from app.compare import compare_rules
from app.evaluate import evaluate_profile
from app.evidence import verify_rule
from app.models import ApplicantProfile, ExtractedRule, VerifiedRule, EvidenceCheck
from app.pdf_extract import ExtractedDocument, ExtractedPage


def make_doc(text: str) -> ExtractedDocument:
    return ExtractedDocument(
        pages=[ExtractedPage(page_number=1, text=text)],
        page_count=1,
        text_character_count=len(text),
        likely_scanned=False,
    )


def vr(field: str, value, quote: str, *, scope: str | None = None, unit: str | None = None, operator: str = "<=") -> VerifiedRule:
    rule = ExtractedRule(
        field=field,
        operator=operator,
        value=value,
        unit=unit,
        scope=scope,
        quote=quote,
        page=1,
        status="explicit",
    )
    return VerifiedRule(
        rule=rule,
        evidence=EvidenceCheck(verified=True, quote_found=True, value_supported=True, reason="test"),
    )


def test_verification_requires_quote_value_operator_and_unit():
    quote = "Annual family income should not exceed Rs. 6 lakh per annum."
    document = make_doc(quote)
    good = ExtractedRule(
        field="max_annual_family_income_inr",
        operator="<=",
        value=6,
        unit="lakh INR",
        quote=quote,
        page=1,
    )
    assert verify_rule(good, document).evidence.verified is True

    wrong_value = good.model_copy(update={"value": 8})
    assert verify_rule(wrong_value, document).evidence.verified is False

    wrong_operator = good.model_copy(update={"operator": "<"})
    assert verify_rule(wrong_operator, document).evidence.operator_supported is False

    wrong_unit = good.model_copy(update={"unit": "crore INR"})
    assert verify_rule(wrong_unit, document).evidence.unit_supported is False


def test_strict_age_limit_is_not_made_inclusive():
    quote = "Applicants must be below 40 years of age."
    document = make_doc(quote)
    rule = ExtractedRule(
        field="max_age_years",
        operator="<",
        value=40,
        unit="years",
        quote=quote,
        page=1,
    )
    verified = verify_rule(rule, document)
    assert verified.evidence.verified is True

    at_boundary = evaluate_profile(
        [VerifiedRule(rule=rule, evidence=verified.evidence)],
        ApplicantProfile(age_years=40),
    )
    assert at_boundary.outcome == "fails_extracted_conditions"


def test_absence_is_not_treated_as_repeal():
    old = [vr("max_age_years", 40, "Age limit up to 40 years.")]
    new = [vr("max_annual_family_income_inr", 600000, "Income up to 600000 rupees.")]
    changes = compare_rules(old, new)
    types = {change.field: change.change_type for change in changes}
    assert types["max_age_years"] == "not_restated_in_new_document"
    old_age_change = next(change for change in changes if change.field == "max_age_years")
    assert old_age_change.old_pages == [1]
    assert old_age_change.new_pages == []
    assert types["max_annual_family_income_inr"] == "not_found_in_old_document"


def test_duplicate_same_scope_rules_require_manual_review():
    old = [
        vr("max_annual_family_income_inr", 5, "Income up to Rs. 5 lakh.", unit="lakh INR"),
        vr("max_annual_family_income_inr", 6, "Income up to Rs. 6 lakh.", unit="lakh INR"),
    ]
    new = [vr("max_annual_family_income_inr", 7, "Income up to Rs. 7 lakh.", unit="lakh INR")]
    changes = compare_rules(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "needs_review"
    assert changes[0].old_value == [5, 6]


def test_numeric_rule_evaluation_converts_lakh_to_rupees():
    rules = [
        vr("max_age_years", 40, "Age limit up to 40 years.", unit="years", operator="<="),
        vr("max_annual_family_income_inr", 6, "Annual family income up to Rs. 6 lakh.", unit="lakh INR", operator="<="),
    ]
    profile = ApplicantProfile(age_years=22, annual_family_income_inr=450000)
    result = evaluate_profile(rules, profile)
    assert result.outcome == "meets_extracted_conditions"

    ineligible = ApplicantProfile(age_years=42, annual_family_income_inr=450000)
    result2 = evaluate_profile(rules, ineligible)
    assert result2.outcome == "fails_extracted_conditions"


def test_unknown_operator_never_returns_eligible():
    rule = vr("max_age_years", 40, "Age limit up to 40 years.", operator="stated")
    result = evaluate_profile([rule], ApplicantProfile(age_years=22))
    assert result.outcome == "insufficient_evidence"



def test_indian_grouped_rupee_value_matches_canonical_number():
    from app.evidence import _number_tokens

    assert _number_tokens(600000) == _number_tokens("₹6,00,000")
    assert _number_tokens(35000000) == _number_tokens("₹3,50,00,000")


def test_malayalam_numeric_rule_evidence_is_supported():
    quote = "അപേക്ഷകർക്ക് ൪൦ വയസ്സിൽ താഴെയായിരിക്കണം."
    document = make_doc(quote)
    rule = ExtractedRule(
        field="max_age_years",
        operator="<",
        value=40,
        unit="വയസ്സ്",
        quote=quote,
        page=1,
    )
    verified = verify_rule(rule, document)
    assert verified.evidence.verified is True


def test_malayalam_lakh_unit_is_converted_for_local_profile_evaluation():
    quote = "വാർഷിക കുടുംബ വരുമാനം ൬ ലക്ഷം രൂപയിൽ കവിയരുത്."
    document = make_doc(quote)
    rule = ExtractedRule(
        field="max_annual_family_income_inr",
        operator="<=",
        value=6,
        unit="ലക്ഷം രൂപ",
        quote=quote,
        page=1,
    )
    verified = verify_rule(rule, document)
    assert verified.evidence.verified is True
    result = evaluate_profile(
        [verified],
        ApplicantProfile(annual_family_income_inr=650000),
    )
    assert result.outcome == "fails_extracted_conditions"



def test_conditional_rule_is_not_auto_compared_as_a_definitive_change():
    old = [
        vr("max_age_years", 40, "Applicants should be below 40 years of age.")
    ]
    conditional_rule = ExtractedRule(
        field="max_age_years",
        operator="<",
        value=35,
        unit="years",
        scope=None,
        status="conditional",
        quote="The age limit may be relaxed to below 35 years in special cases.",
        page=1,
    )
    from app.models import EvidenceCheck
    new = [VerifiedRule(
        rule=conditional_rule,
        evidence=EvidenceCheck(verified=True, quote_found=True, value_supported=True, reason="test"),
    )]
    changes = compare_rules(old, new)
    assert len(changes) == 1
    assert changes[0].change_type == "needs_review"
    assert changes[0].explanation_ml



def test_boolean_rule_polarity_must_be_supported_by_quote():
    from app.evidence import boolean_value_supported

    assert boolean_value_supported(
        "other_fellowship_prohibited", True,
        "Candidates shall not receive another fellowship during the programme.",
    )
    assert not boolean_value_supported(
        "other_fellowship_prohibited", True,
        "Candidates may also receive another fellowship during the programme.",
    )
    assert boolean_value_supported(
        "other_fellowship_prohibited", False,
        "Candidates may also receive another fellowship during the programme.",
    )


def test_not_restated_or_not_found_conditions_force_incomplete_profile_result():
    from app.evaluate import apply_diff_uncertainty
    from app.models import EligibilityCheck, RuleChange

    old_assessment = EligibilityCheck(
        outcome="meets_extracted_conditions", passed=["age: passed"]
    )
    new_assessment = EligibilityCheck(
        outcome="meets_extracted_conditions", passed=["income: passed"]
    )
    changes = [
        RuleChange(
            field="max_age_years",
            change_type="not_restated_in_new_document",
            old_value=40, old_quote="Below 40 years", old_pages=[1],
            explanation="Not repeated in the amendment.",
        ),
        RuleChange(
            field="max_annual_family_income_inr",
            change_type="not_found_in_old_document",
            new_value=6, new_quote="Income up to 6 lakh", new_pages=[2],
            explanation="Not present in the older upload.",
        ),
    ]

    old_result, new_result = apply_diff_uncertainty(old_assessment, new_assessment, changes)
    assert old_result.outcome == "insufficient_evidence"
    assert new_result.outcome == "insufficient_evidence"
    assert any("max_annual_family_income_inr" in item for item in old_result.unknown)
    assert any("max_age_years" in item for item in new_result.unknown)


def test_explicit_failure_remains_failure_even_if_other_conditions_are_unknown():
    from app.evaluate import apply_diff_uncertainty
    from app.models import EligibilityCheck, RuleChange

    old_assessment = EligibilityCheck(outcome="fails_extracted_conditions", failed=["age failed"])
    new_assessment = EligibilityCheck(outcome="meets_extracted_conditions", passed=["income passed"])
    change = RuleChange(
        field="max_age_years",
        change_type="not_restated_in_new_document",
        old_value=40, old_pages=[1],
        explanation="Not restated.",
    )
    old_result, new_result = apply_diff_uncertainty(old_assessment, new_assessment, [change])
    assert old_result.outcome == "fails_extracted_conditions"
    assert new_result.outcome == "insufficient_evidence"


def test_limited_amendment_scope_requires_verified_parent_and_scope_quotes():
    from app.evidence import verify_limited_amendment_link
    from app.models import RuleExtraction

    old_id = "G.O.(Rt)No.1217/2025/PWD"
    old_text = f"Government of Kerala {old_id} dated 11-08-2025. Sanction amount Rs. 260 Lakhs."
    new_reference = "Read G.O.(Rt)No.1217/2025/PWD dated 11-08-2025."
    scope_quote = "The Government Order read above stands modified to this extent only."
    new_text = f"{new_reference} {scope_quote}"
    old_doc = make_doc(old_text)
    new_doc = make_doc(new_text)
    old_extraction = RuleExtraction(order_number=old_id)
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number=old_id,
        amends_order_quote=new_reference,
        amends_order_page=1,
        amendment_scope_quote=scope_quote,
        amendment_scope_page=1,
    )

    proof = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)
    assert proof.verified is True
    assert proof.scope_page == 1

    mismatched_parent = new_extraction.model_copy(update={"amends_order_number": "G.O.(Rt)No.999/2025/PWD"})
    rejected = verify_limited_amendment_link(old_extraction, mismatched_parent, old_doc, new_doc)
    assert rejected.verified is False

    unquoted_scope = new_extraction.model_copy(update={"amendment_scope_quote": "The entire order stands replaced."})
    rejected_scope = verify_limited_amendment_link(old_extraction, unquoted_scope, old_doc, new_doc)
    assert rejected_scope.verified is False


def test_explicit_limited_erratum_scope_preserves_unrepeated_condition():
    from app.compare import compare_rules
    from app.models import AmendmentScopeEvidence

    original = [
        vr("other", 350, "estimated amount of Rs. 350 Crores", scope="previous sanction", unit="Crores", operator="stated"),
        vr("other", 689, "Rs. 689 Crores under the H/A", scope="revised sanction request", unit="Crores", operator="stated"),
        vr("other", 260, "for an amount of Rs 260 Lakhs", scope="final revised sanction", unit="Lakhs", operator="stated"),
    ]
    erratum = [
        vr("other", 350, "Rs. 350 Crores ... as Rs. 350 Lakh", scope="previous sanction", unit="Lakh", operator="stated"),
        vr("other", 689, "Rs. 689 Crores ... as Rs. 689 Lakh", scope="revised sanction request", unit="Lakh", operator="stated"),
    ]
    proof = AmendmentScopeEvidence(
        verified=True,
        effect="specific_changes_only",
        referenced_order_number="G.O.(Rt)No.1217/2025/PWD",
        scope_quote="The Government Order read above stands modified to this extent only.",
        scope_page=1,
        reason="Verified source link and limited scope.",
    )

    changes = compare_rules(original, erratum, proof)
    by_scope = {item.scope: item for item in changes}
    assert by_scope["previous sanction"].change_type == "modified"
    assert by_scope["revised sanction request"].change_type == "modified"
    assert by_scope["final revised sanction"].change_type == "unchanged_by_limited_amendment"
    assert by_scope["final revised sanction"].new_value == 260


def test_unverified_limited_scope_does_not_promote_missing_rule_to_unchanged():
    from app.compare import compare_rules
    from app.models import AmendmentScopeEvidence

    old = [vr("other", 260, "Rs. 260 Lakhs", scope="final sanction", unit="Lakhs", operator="stated")]
    proof = AmendmentScopeEvidence(
        verified=False,
        effect="specific_changes_only",
        scope_quote="The Government Order stands modified to this extent only.",
        scope_page=1,
        reason="Parent link not verified.",
    )
    changes = compare_rules(old, [], proof)
    assert changes[0].change_type == "not_restated_in_new_document"


def test_verified_limited_amendment_carries_forward_omitted_rules_into_new_profile_check():
    from app.evaluate import carry_forward_limited_amendment_rules, evaluate_profile
    from app.models import AmendmentScopeEvidence, RuleChange

    old_age = vr("max_age_years", 40, "Applicants must be below 40 years of age.", scope="general age condition", unit="years", operator="<")
    new_income = vr("max_annual_family_income_inr", 6, "Annual family income shall not exceed Rs. 6 lakh.", scope="income ceiling", unit="lakh INR", operator="<=")
    changes = [
        RuleChange(
            field="max_age_years",
            scope="general age condition",
            change_type="unchanged_by_limited_amendment",
            old_value=40,
            new_value=40,
            old_unit="years",
            new_unit="years",
            explanation="The limited amendment leaves this condition unchanged.",
        ),
        RuleChange(
            field="max_annual_family_income_inr",
            scope="income ceiling",
            change_type="modified",
            old_value=5,
            new_value=6,
            old_unit="lakh INR",
            new_unit="lakh INR",
            explanation="Income ceiling changed.",
        ),
    ]
    proof = AmendmentScopeEvidence(
        verified=True,
        effect="specific_changes_only",
        referenced_order_number="G.O.(Rt)No.1/2025/TEST",
        scope_quote="The order stands modified to this extent only.",
        scope_page=1,
        reason="Verified.",
    )
    effective = carry_forward_limited_amendment_rules([old_age], [new_income], changes, proof)
    assert len(effective) == 2
    result = evaluate_profile(effective, ApplicantProfile(age_years=45, annual_family_income_inr=500000))
    assert result.outcome == "fails_extracted_conditions"
    assert any("max_age_years" in line for line in result.failed)


def test_unverified_amendment_never_carries_forward_rules_for_new_assessment():
    from app.evaluate import carry_forward_limited_amendment_rules
    from app.models import AmendmentScopeEvidence, RuleChange

    old_rule = vr("max_age_years", 40, "Applicants must be below 40 years of age.", scope="age", unit="years", operator="<")
    proof = AmendmentScopeEvidence(verified=False, effect="specific_changes_only", reason="Not verified.")
    changes = [RuleChange(field="max_age_years", scope="age", change_type="unchanged_by_limited_amendment", explanation="Test")]
    assert carry_forward_limited_amendment_rules([old_rule], [], changes, proof) == []


def test_limited_scope_quote_alone_cannot_carry_forward_without_verified_change_pair():
    from app.compare import compare_rules
    from app.models import AmendmentScopeEvidence

    old = [vr("max_age_years", 40, "Applicants must be below 40 years of age.", scope="age", unit="years", operator="<")]
    new = [vr("other", "some unrelated note", "Some unrelated administrative note.", scope="note", operator="stated")]
    proof = AmendmentScopeEvidence(
        verified=True,
        effect="specific_changes_only",
        referenced_order_number="G.O.(Rt)No.1/2025/TEST",
        scope_quote="The order stands modified to this extent only.",
        scope_page=1,
        reason="The parent and scope quotes were verified.",
    )
    changes = compare_rules(old, new, proof)
    age_change = next(item for item in changes if item.field == "max_age_years")
    assert age_change.change_type == "not_restated_in_new_document"


def test_degree_level_pg_matches_explicit_postgraduate_label():
    rule = vr(
        "eligible_degree_levels",
        ["Postgraduate Degree programmes"],
        "Eligible levels include Postgraduate Degree programmes.",
        operator="in",
    )
    result = evaluate_profile([rule], ApplicantProfile(degree_level="PG"))
    assert result.outcome == "meets_extracted_conditions"


def test_degree_level_phd_matches_explicit_research_label():
    rule = vr(
        "eligible_degree_levels",
        ["Research (PhD) programmes"],
        "Eligible levels include Research (PhD) programmes.",
        operator="in",
    )
    result = evaluate_profile([rule], ApplicantProfile(degree_level="Ph.D"))
    assert result.outcome == "meets_extracted_conditions"


def test_degree_level_unknown_label_is_not_fuzzy_matched():
    rule = vr(
        "eligible_degree_levels",
        ["Postgraduate Degree programmes"],
        "Eligible levels include Postgraduate Degree programmes.",
        operator="in",
    )
    result = evaluate_profile([rule], ApplicantProfile(degree_level="postgraduate diploma"))
    assert result.outcome == "fails_extracted_conditions"
