from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings

client = TestClient(app)


def test_health_endpoint_does_not_expose_secret():
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["gemini_configured"] is bool(settings.gemini_api_key)
    assert "api_key" not in body


def test_analyze_requires_server_configured_api_key():
    if settings.gemini_api_key:
        return
    response = client.post(
        "/api/analyze",
        files={
            "old_document": ("old.pdf", b"%PDF-1.4", "application/pdf"),
            "new_document": ("new.pdf", b"%PDF-1.4", "application/pdf"),
        },
    )
    assert response.status_code == 503
    assert "API key is not configured" in response.json()["detail"]


def test_analyze_returns_traceable_diff_and_local_profile_assessment(monkeypatch):
    import hashlib
    from io import BytesIO
    from types import SimpleNamespace

    from app import main
    from app.models import ExtractedRule, RuleExtraction
    from app.pdf_extract import ExtractedDocument, ExtractedPage

    fake_old_bytes = b"old-public-order-pdf-bytes"
    fake_new_bytes = b"new-public-order-pdf-bytes"
    old_quote = "Annual family income shall not exceed Rs. 5 lakh per annum."
    new_quote = "Annual family income shall not exceed Rs. 6 lakh per annum."

    old_doc = ExtractedDocument(
        pages=[ExtractedPage(1, old_quote + " Additional policy text for extraction coverage.")],
        page_count=1,
        text_character_count=100,
        likely_scanned=False,
    )
    new_doc = ExtractedDocument(
        pages=[ExtractedPage(1, new_quote + " Additional revised policy text for extraction coverage.")],
        page_count=1,
        text_character_count=100,
        likely_scanned=False,
    )

    async def fake_read_pdf(file):
        return (fake_old_bytes, old_doc) if file.filename == "old.pdf" else (fake_new_bytes, new_doc)

    def fake_extract_rules(document, filename):
        quote = old_quote if filename == "old.pdf" else new_quote
        value = 5 if filename == "old.pdf" else 6
        return RuleExtraction(
            document_title="Test scholarship order",
            order_number="TEST/1",
            order_date="2025-01-01",
            rules=[ExtractedRule(
                field="max_annual_family_income_inr",
                operator="<=",
                value=value,
                unit="lakh INR",
                quote=quote,
                page=1,
                explanation_en="Annual income limit for applicants.",
                explanation_ml="അപേക്ഷകരുടെ വാർഷിക വരുമാന പരിധി.",
            )],
        )

    monkeypatch.setattr(main, "settings", SimpleNamespace(
        gemini_api_key="test-key",
        gemini_model="test-model",
        max_upload_mb=18,
        allowed_origins=(),
    ))
    monkeypatch.setattr(main, "_read_pdf", fake_read_pdf)
    monkeypatch.setattr(main, "extract_rules_with_gemini", fake_extract_rules)

    response = client.post(
        "/api/analyze",
        files={
            "old_document": ("old.pdf", BytesIO(b"placeholder"), "application/pdf"),
            "new_document": ("new.pdf", BytesIO(b"placeholder"), "application/pdf"),
        },
        data={
            "applicant_profile": '{"annual_family_income_inr": 550000}',
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["changes"][0]["change_type"] == "modified"
    assert body["changes"][0]["old_value"] == 5
    assert body["changes"][0]["new_value"] == 6
    assert body["changes"][0]["explanation_ml"]
    assert body["amendment_scope"]["verified"] is False
    assert body["amendment_scope"]["effect"] == "unclear"
    assert body["old_assessment"]["outcome"] == "fails_extracted_conditions"
    assert body["new_assessment"]["outcome"] == "meets_extracted_conditions"
    assert body["old_document"]["source_sha256"] == hashlib.sha256(fake_old_bytes).hexdigest()
    assert body["new_document"]["source_sha256"] == hashlib.sha256(fake_new_bytes).hexdigest()


def test_oversized_pdf_is_rejected_before_full_read(monkeypatch):
    import asyncio
    from io import BytesIO
    from types import SimpleNamespace

    from fastapi import HTTPException
    from starlette.datastructures import Headers, UploadFile
    from app import main

    monkeypatch.setattr(main, "settings", SimpleNamespace(max_upload_mb=1))
    upload = UploadFile(
        filename="large.pdf",
        file=BytesIO(b"x" * (1024 * 1024 + 1)),
        headers=Headers({"content-type": "application/pdf"}),
    )
    try:
        asyncio.run(main._read_pdf(upload))
        assert False, "Expected the size limit to reject the file"
    except HTTPException as exc:
        assert exc.status_code == 413
        assert "smaller than 1 MB" in exc.detail


def test_analyze_runs_real_pdf_text_extraction_with_mocked_ai(monkeypatch):
    """Exercise multipart upload and pypdf extraction using synthetic local PDFs.

    Gemini is mocked deliberately: this verifies the real PDF ingestion and
    evidence pipeline, not live model accuracy or any official source document.
    """
    from pathlib import Path
    from types import SimpleNamespace

    from app import main
    from app.models import ExtractedRule, RuleExtraction

    fixture_dir = Path(__file__).parent / "fixtures"
    old_bytes = (fixture_dir / "old_policy_sample.pdf").read_bytes()
    new_bytes = (fixture_dir / "new_policy_sample.pdf").read_bytes()

    old_quote = "Annual family income shall not exceed Rs. 5 lakh per annum."
    new_quote = "Annual family income shall not exceed Rs. 6 lakh per annum."

    def fake_extract_rules(document, filename):
        is_old = filename == "old_policy_sample.pdf"
        quote = old_quote if is_old else new_quote
        value = 5 if is_old else 6
        return RuleExtraction(
            document_title="Synthetic Example Overseas Scholarship",
            order_number="SYNTHETIC-TEST-ONLY",
            order_date="2025-01-01",
            rules=[ExtractedRule(
                field="max_annual_family_income_inr",
                operator="<=",
                value=value,
                unit="lakh INR",
                quote=quote,
                page=1,
                explanation_en="Annual family income ceiling.",
                explanation_ml="വാർഷിക കുടുംബ വരുമാന പരിധി.",
            )],
        )

    monkeypatch.setattr(main, "settings", SimpleNamespace(
        gemini_api_key="test-key",
        gemini_model="test-model",
        max_upload_mb=18,
        allowed_origins=(),
    ))
    monkeypatch.setattr(main, "extract_rules_with_gemini", fake_extract_rules)

    response = client.post(
        "/api/analyze",
        files={
            "old_document": ("old_policy_sample.pdf", old_bytes, "application/pdf"),
            "new_document": ("new_policy_sample.pdf", new_bytes, "application/pdf"),
        },
        data={"applicant_profile": '{"annual_family_income_inr": 550000}'},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["old_document"]["page_count"] == 1
    assert body["new_document"]["page_count"] == 1
    assert body["old_document"]["verified_rule_count"] == 1
    assert body["new_document"]["verified_rule_count"] == 1
    assert body["changes"][0]["change_type"] == "modified"
    assert body["changes"][0]["old_value"] == 5
    assert body["changes"][0]["new_value"] == 6
    assert body["old_assessment"]["outcome"] == "fails_extracted_conditions"
    assert body["new_assessment"]["outcome"] == "meets_extracted_conditions"
