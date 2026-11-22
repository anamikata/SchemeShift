from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

RuleStatus = Literal["explicit", "conditional", "ambiguous"]
RuleOperator = Literal["<", "<=", ">", ">=", "in", "not_in", "required", "prohibited", "stated"]

SUPPORTED_FIELDS = {
    "max_age_years",
    "max_annual_family_income_inr",
    "min_marks_percent",
    "eligible_communities",
    "excluded_communities",
    "university_rank_max",
    "eligible_degree_levels",
    "eligible_disciplines",
    "requires_full_time",
    "other_fellowship_prohibited",
    "one_child_per_family",
    "scholarship_one_time",
    "monthly_fellowship_inr",
    "max_fellowship_years",
    "beneficiary_limit",
    "application_deadline",
    "required_documents",
    "other",
}


class ExtractedRule(BaseModel):
    """One rule extracted from a government document, with source evidence."""

    field: str = Field(description="A normalized field name from the supported field vocabulary.")
    operator: RuleOperator = Field(description="Use the exact comparison operator supported by the wording; preserve strict versus inclusive limits.")
    value: Any = Field(description="The value exactly supported by the quote. Do not calculate or infer it.")
    unit: str | None = None
    scope: str | None = Field(default=None, description="Who or what the condition applies to, if explicitly stated.")
    status: RuleStatus = "explicit"
    quote: str = Field(description="A verbatim quotation copied from the source page, preserving the original language.")
    page: int = Field(ge=1, description="1-based page number in the uploaded PDF.")
    explanation_en: str | None = None
    explanation_ml: str | None = None

    @field_validator("field")
    @classmethod
    def validate_field(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in SUPPORTED_FIELDS:
            return "other"
        return normalized


class ExtractedAmendmentPair(BaseModel):
    """An explicit before/after correction stated by an amendment or erratum."""

    target: str = Field(description="The explicitly identified target, such as first paragraph amount.")
    old_value: Any = Field(description="Original numeric value only; do not include its unit or currency label.")
    old_unit: str = Field(description="Original unit exactly as stated, such as Crores.")
    new_value: Any = Field(description="Corrected numeric value only; do not include its unit or currency label.")
    new_unit: str = Field(description="Corrected unit exactly as stated, such as Lakh.")
    quote: str = Field(description="Verbatim quotation from the amendment that explicitly states both old and corrected values.")
    page: int = Field(ge=1, description="1-based page number containing the amendment quotation.")


class VerifiedAmendmentPair(BaseModel):
    target: str
    old_value: Any
    old_unit: str
    new_value: Any
    new_unit: str
    quote: str
    page: int
    old_document_quote: str | None = None
    old_document_page: int | None = None
    verified: bool = False
    reason: str


class RuleExtraction(BaseModel):
    document_title: str | None = None
    order_number: str | None = None
    order_date: str | None = None
    rules: list[ExtractedRule] = Field(default_factory=list)
    amendment_pairs: list[ExtractedAmendmentPair] = Field(default_factory=list)
    coverage_notes: list[str] = Field(default_factory=list)
    # Amendment metadata is only advisory until the backend verifies both quotes
    # against the uploaded pages and confirms the referenced parent order.
    amendment_effect: Literal["specific_changes_only", "full_replacement", "unclear", "not_amendment"] = "unclear"
    amends_order_number: str | None = None
    amends_order_quote: str | None = None
    amends_order_page: int | None = Field(default=None, ge=1)
    amendment_scope_quote: str | None = None
    amendment_scope_page: int | None = Field(default=None, ge=1)


class AmendmentScopeEvidence(BaseModel):
    verified: bool = False
    effect: Literal["specific_changes_only", "full_replacement", "unclear", "not_amendment"] = "unclear"
    referenced_order_number: str | None = None
    scope_quote: str | None = None
    scope_page: int | None = None
    reason: str


class ApplicantProfile(BaseModel):
    age_years: float | None = Field(default=None, ge=0, le=120)
    annual_family_income_inr: float | None = Field(default=None, ge=0)
    marks_percent: float | None = Field(default=None, ge=0, le=100)
    community: str | None = None
    university_rank: int | None = Field(default=None, ge=1)
    degree_level: str | None = None
    discipline: str | None = None
    full_time_research: bool | None = None
    currently_receives_other_fellowship: bool | None = None
    is_only_applicant_child_from_family: bool | None = None
    previously_received_same_scheme: bool | None = None


class EvidenceCheck(BaseModel):
    verified: bool
    quote_found: bool
    value_supported: bool
    operator_supported: bool = True
    unit_supported: bool = True
    reason: str


class VerifiedRule(BaseModel):
    rule: ExtractedRule
    evidence: EvidenceCheck


class RuleChange(BaseModel):
    field: str
    scope: str | None = None
    change_type: Literal[
        "modified",
        "unchanged",
        "not_restated_in_new_document",
        "not_found_in_old_document",
        "unchanged_by_limited_amendment",
        "needs_review",
    ]
    old_value: Any = None
    new_value: Any = None
    old_unit: str | None = None
    new_unit: str | None = None
    old_quote: str | None = None
    new_quote: str | None = None
    old_pages: list[int] = Field(default_factory=list)
    new_pages: list[int] = Field(default_factory=list)
    explanation: str
    explanation_ml: str | None = None


class EligibilityCheck(BaseModel):
    outcome: Literal["meets_extracted_conditions", "fails_extracted_conditions", "insufficient_evidence", "not_evaluated"]
    passed: list[str] = Field(default_factory=list)
    failed: list[str] = Field(default_factory=list)
    unknown: list[str] = Field(default_factory=list)
    disclaimer: str = "This is an evidence-based comparison aid, not an official eligibility decision."


class DocumentSummary(BaseModel):
    title: str | None = None
    order_number: str | None = None
    order_date: str | None = None
    source_filename: str
    source_sha256: str
    page_count: int
    processed_page_count: int
    extracted_rule_count: int
    verified_rule_count: int
    rejected_rule_count: int
    coverage_notes: list[str] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    old_document: DocumentSummary
    new_document: DocumentSummary
    old_rules: list[VerifiedRule]
    new_rules: list[VerifiedRule]
    changes: list[RuleChange]
    old_assessment: EligibilityCheck
    new_assessment: EligibilityCheck
    amendment_scope: AmendmentScopeEvidence | None = None
    amendment_pairs: list[VerifiedAmendmentPair] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
