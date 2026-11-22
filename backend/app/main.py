from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Annotated

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .ai_extract import extract_rules_with_gemini
from .compare import compare_rules, exclude_verified_amendment_pair_duplicates
from .evaluate import apply_diff_uncertainty, carry_forward_limited_amendment_rules, evaluate_profile
from .evidence import verify_amendment_pairs, verify_extraction, verify_limited_amendment_link
from .models import AnalysisResponse, ApplicantProfile, DocumentSummary
from .pdf_extract import extract_pdf_pages
from .settings import settings

app = FastAPI(
    title="SchemeShift API",
    description="Evidence-backed comparison of government order versions.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str | bool]:
    return {
        "status": "ok",
        "gemini_configured": bool(settings.gemini_api_key),
        "model": settings.gemini_model,
    }


def _summary(extraction, verified_rules, *, filename: str, source_bytes: bytes, pdf_document) -> DocumentSummary:
    verified_count = sum(1 for item in verified_rules if item.evidence.verified)
    return DocumentSummary(
        title=extraction.document_title,
        order_number=extraction.order_number,
        order_date=extraction.order_date,
        source_filename=filename,
        source_sha256=hashlib.sha256(source_bytes).hexdigest(),
        page_count=pdf_document.page_count,
        processed_page_count=len(pdf_document.pages),
        extracted_rule_count=len(extraction.rules),
        verified_rule_count=verified_count,
        rejected_rule_count=len(extraction.rules) - verified_count,
        coverage_notes=extraction.coverage_notes,
    )


async def _read_pdf(file: UploadFile) -> tuple[bytes, object]:
    if file.content_type not in {"application/pdf", "application/octet-stream"} and not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=415, detail=f"{file.filename or 'Uploaded file'} is not a PDF.")
    max_bytes = settings.max_upload_mb * 1024 * 1024
    # Read at most one byte beyond the limit so a very large upload is not
    # copied fully into application memory before being rejected.
    data = await file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"Each PDF must be smaller than {settings.max_upload_mb} MB.")
    try:
        document = extract_pdf_pages(data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if document.likely_scanned:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Text extraction found very little readable text in {file.filename or 'the PDF'}. "
                "It may be scanned or low quality. Use a searchable PDF or paste the relevant text; OCR fallback is not enabled in this MVP."
            ),
        )
    return data, document


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_documents(
    old_document: Annotated[UploadFile, File(description="Older government order or scheme guideline PDF")],
    new_document: Annotated[UploadFile, File(description="Newer amendment, revision, or guideline PDF")],
    applicant_profile: Annotated[str | None, Form()] = None,
) -> AnalysisResponse:
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="Gemini API key is not configured on the server yet.")

    old_bytes, old_pdf = await _read_pdf(old_document)
    new_bytes, new_pdf = await _read_pdf(new_document)

    profile = None
    if applicant_profile:
        try:
            profile = ApplicantProfile.model_validate(json.loads(applicant_profile))
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Applicant profile is invalid: {exc}") from exc

    try:
        old_extraction, new_extraction = await asyncio.gather(
            asyncio.to_thread(extract_rules_with_gemini, old_pdf, old_document.filename or "older-order.pdf"),
            asyncio.to_thread(extract_rules_with_gemini, new_pdf, new_document.filename or "newer-order.pdf"),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI extraction failed: {exc}") from exc

    old_verified = verify_extraction(old_extraction.rules, old_pdf)
    new_verified = verify_extraction(new_extraction.rules, new_pdf)
    amendment_scope = verify_limited_amendment_link(old_extraction, new_extraction, old_pdf, new_pdf)
    changes = compare_rules(old_verified, new_verified, amendment_scope)
    amendment_pairs = verify_amendment_pairs(
        new_extraction.amendment_pairs, old_pdf, new_pdf, amendment_scope
    )
    changes = exclude_verified_amendment_pair_duplicates(changes, amendment_pairs)

    warnings: list[str] = [
        "This report compares only the two uploaded documents. Referenced parent orders not uploaded may contain continuing conditions.",
        "A condition missing from one document is not automatically treated as repealed or newly introduced.",
        "Profile results cover only evidence-verified, explicit conditions that the current rule engine understands.",
        "This is not an official government eligibility decision. Confirm the latest applicable orders with the issuing department.",
    ]
    for label, document in (("Older document", old_pdf), ("Newer document", new_pdf)):
        if document.page_count > len(document.pages):
            warnings.append(
                f"{label}: only the first {len(document.pages)} of {document.page_count} pages were processed in this prototype."
            )

    if new_extraction.amendment_effect == "specific_changes_only" and not amendment_scope.verified:
        warnings.append(
            "The newer document appears to describe a limited amendment, but its parent-order link and scope quotation could not both be verified. Conditions not repeated in the newer document remain unknown."
        )
    rejected = sum(1 for item in old_verified + new_verified if not item.evidence.verified)
    if rejected:
        warnings.append(f"{rejected} AI-extracted rule(s) failed quotation/value verification and were excluded from comparison and profile evaluation.")
    rejected_pairs = sum(1 for item in amendment_pairs if not item.verified)
    if rejected_pairs:
        warnings.append(f"{rejected_pairs} extracted amendment pair(s) failed independent source verification and are shown as unverified.")
    if not amendment_pairs and amendment_scope.verified:
        warnings.append("The amendment scope is verified, but no explicit before-and-after correction pairs were extracted. Review the source quotation manually.")
    if not changes:
        warnings.append("No comparable evidence-verified rules were found in both documents.")

    effective_new_rules = carry_forward_limited_amendment_rules(
        old_verified, new_verified, changes, amendment_scope
    )
    old_assessment, new_assessment = apply_diff_uncertainty(
        evaluate_profile(old_verified, profile),
        evaluate_profile(effective_new_rules, profile),
        changes,
    )

    return AnalysisResponse(
        old_document=_summary(
            old_extraction, old_verified,
            filename=old_document.filename or "older-order.pdf",
            source_bytes=old_bytes,
            pdf_document=old_pdf,
        ),
        new_document=_summary(
            new_extraction, new_verified,
            filename=new_document.filename or "newer-order.pdf",
            source_bytes=new_bytes,
            pdf_document=new_pdf,
        ),
        old_rules=old_verified,
        new_rules=new_verified,
        changes=changes,
        old_assessment=old_assessment,
        new_assessment=new_assessment,
        amendment_scope=amendment_scope,
        amendment_pairs=amendment_pairs,
        warnings=warnings,
    )
