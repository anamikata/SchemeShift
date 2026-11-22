from __future__ import annotations

from typing import Any

from .models import AmendmentScopeEvidence, ApplicantProfile, EligibilityCheck, RuleChange, VerifiedRule


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("₹", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _as_values(value: Any) -> list[str] | None:
    if isinstance(value, list):
        return [str(item).strip().casefold() for item in value]
    if isinstance(value, str):
        # Only split obvious delimiter-separated lists. Do not guess from prose.
        if ";" in value:
            return [part.strip().casefold() for part in value.split(";") if part.strip()]
        return [value.strip().casefold()] if value.strip() else None
    return None


def _canonical_degree_level(value: Any) -> str:
    """Normalize only reviewed, unambiguous degree-level labels.

    Do not use substring or fuzzy matching here: eligibility categories must not
    be inferred from loosely similar wording. Unknown labels remain exact text.
    """
    normalized = " ".join(str(value).strip().casefold().replace(".", "").split())
    aliases = {
        "pg": "postgraduate",
        "post graduate": "postgraduate",
        "postgraduate": "postgraduate",
        "postgraduate degree": "postgraduate",
        "postgraduate degree programmes": "postgraduate",
        "masters": "postgraduate",
        "master's": "postgraduate",
        "phd": "phd",
        "research": "phd",
        "research phd": "phd",
        "research (phd) programmes": "phd",
        "doctoral": "phd",
        "doctoral programmes": "phd",
    }
    return aliases.get(normalized, normalized)


def _apply_numeric_operator(actual: float, threshold: float, operator: str) -> bool | None:
    if operator == "<":
        return actual < threshold
    if operator == "<=":
        return actual <= threshold
    if operator == ">":
        return actual > threshold
    if operator == ">=":
        return actual >= threshold
    return None


def _evaluate_one(field: str, value: Any, profile: ApplicantProfile, unit: str | None = None, operator: str = "stated") -> tuple[str, str]:
    """Return (pass|fail|unknown, user-facing explanation)."""
    if field == "max_age_years":
        limit = _as_number(value)
        if profile.age_years is None or limit is None:
            return "unknown", "Age or a parseable age limit is missing."
        passed = _apply_numeric_operator(profile.age_years, limit, operator)
        if passed is None:
            return "unknown", "The extracted age comparison operator is not supported by the evaluator."
        return ("pass", f"Age {profile.age_years:g} satisfies the quoted age condition ({operator} {limit:g} years).") if passed else ("fail", f"Age {profile.age_years:g} does not satisfy the quoted age condition ({operator} {limit:g} years).")

    if field == "max_annual_family_income_inr":
        limit = _as_number(value)
        unit_text = (unit or "").casefold()
        if limit is not None and ("lakh" in unit_text or "ലക്ഷം" in unit_text):
            limit *= 100_000
        elif limit is not None and ("crore" in unit_text or "കോടി" in unit_text):
            limit *= 10_000_000
        if profile.annual_family_income_inr is None or limit is None:
            return "unknown", "Annual family income or a parseable income limit is missing."
        passed = _apply_numeric_operator(profile.annual_family_income_inr, limit, operator)
        if passed is None:
            return "unknown", "The extracted income comparison operator is not supported by the evaluator."
        return ("pass", "Annual family income satisfies the quoted income condition.") if passed else ("fail", "Annual family income does not satisfy the quoted income condition.")

    if field == "min_marks_percent":
        minimum = _as_number(value)
        if profile.marks_percent is None or minimum is None:
            return "unknown", "Marks percentage or a parseable minimum is missing."
        passed = _apply_numeric_operator(profile.marks_percent, minimum, operator)
        if passed is None:
            return "unknown", "The extracted marks comparison operator is not supported by the evaluator."
        return ("pass", "Marks percentage satisfies the quoted marks condition.") if passed else ("fail", "Marks percentage does not satisfy the quoted marks condition.")

    if field == "university_rank_max":
        maximum = _as_number(value)
        if profile.university_rank is None or maximum is None:
            return "unknown", "University rank or a parseable ranking limit is missing."
        passed = _apply_numeric_operator(float(profile.university_rank), maximum, operator)
        if passed is None:
            return "unknown", "The extracted ranking comparison operator is not supported by the evaluator."
        return ("pass", "University rank satisfies the quoted ranking condition.") if passed else ("fail", "University rank does not satisfy the quoted ranking condition.")

    if field in {"eligible_communities", "excluded_communities"}:
        allowed = _as_values(value)
        if profile.community is None or allowed is None:
            return "unknown", "Applicant community or a structured community list is missing."
        member = profile.community.strip().casefold() in allowed
        if field == "eligible_communities":
            return ("pass", "Applicant community appears in the stated eligible list.") if member else ("fail", "Applicant community is not in the stated eligible list.")
        return ("fail", "Applicant community appears in the stated excluded list.") if member else ("pass", "Applicant community is not in the stated excluded list.")

    if field == "eligible_degree_levels":
        allowed = _as_values(value)
        if profile.degree_level is None or allowed is None:
            return "unknown", "Degree level or a structured list of eligible levels is missing."
        applicant_level = _canonical_degree_level(profile.degree_level)
        allowed_levels = {_canonical_degree_level(item) for item in allowed}
        passed = applicant_level in allowed_levels
        return ("pass", "Degree level is included in the stated list.") if passed else ("fail", "Degree level is not included in the stated list.")

    if field == "eligible_disciplines":
        allowed = _as_values(value)
        if profile.discipline is None or allowed is None:
            return "unknown", "Discipline or a structured list of eligible disciplines is missing."
        passed = profile.discipline.strip().casefold() in allowed
        return ("pass", "Discipline is included in the stated list.") if passed else ("fail", "Discipline is not included in the stated list.")

    if field == "requires_full_time":
        if profile.full_time_research is None:
            return "unknown", "Full-time/part-time status was not supplied."
        required = bool(value)
        passed = profile.full_time_research if required else True
        return ("pass", "Full-time requirement is satisfied.") if passed else ("fail", "The document requires full-time study, but the profile is not full-time.")

    if field == "other_fellowship_prohibited":
        if profile.currently_receives_other_fellowship is None:
            return "unknown", "Whether another fellowship is being received was not supplied."
        prohibited = bool(value)
        passed = not (prohibited and profile.currently_receives_other_fellowship)
        return ("pass", "No conflicting fellowship is reported.") if passed else ("fail", "The document prohibits another fellowship, but the profile reports one.")

    if field == "one_child_per_family":
        if profile.is_only_applicant_child_from_family is None:
            return "unknown", "Family-level applicant status was not supplied."
        passed = profile.is_only_applicant_child_from_family if bool(value) else True
        return ("pass", "The one-applicant-per-family condition is satisfied.") if passed else ("fail", "The one-applicant-per-family condition is not satisfied.")

    if field == "scholarship_one_time":
        if profile.previously_received_same_scheme is None:
            return "unknown", "Previous receipt of this scheme was not supplied."
        passed = not (bool(value) and profile.previously_received_same_scheme)
        return ("pass", "The one-time restriction is satisfied.") if passed else ("fail", "The profile indicates this scheme was previously received.")

    return "unknown", "This field is displayed for review but is not yet evaluated automatically."


def evaluate_profile(rules: list[VerifiedRule], profile: ApplicantProfile | None) -> EligibilityCheck:
    if profile is None:
        return EligibilityCheck(outcome="not_evaluated", unknown=["No applicant profile was provided."])

    passed: list[str] = []
    failed: list[str] = []
    unknown: list[str] = []

    for item in rules:
        if not item.evidence.verified:
            continue
        if item.rule.status != "explicit":
            unknown.append(f"{item.rule.field}: condition is {item.rule.status} and requires review.")
            continue
        result, reason = _evaluate_one(item.rule.field, item.rule.value, profile, item.rule.unit, item.rule.operator)
        message = f"{item.rule.field}: {reason}"
        if result == "pass":
            passed.append(message)
        elif result == "fail":
            failed.append(message)
        else:
            unknown.append(message)

    if failed:
        outcome = "fails_extracted_conditions"
    elif unknown or not passed:
        outcome = "insufficient_evidence"
    else:
        outcome = "meets_extracted_conditions"

    return EligibilityCheck(outcome=outcome, passed=passed, failed=failed, unknown=unknown)


def apply_diff_uncertainty(
    old_assessment: EligibilityCheck,
    new_assessment: EligibilityCheck,
    changes: list[RuleChange],
) -> tuple[EligibilityCheck, EligibilityCheck]:
    """Prevent a partial amendment from looking like a complete eligibility decision.

    A condition found in only one supplied document is not automatically repealed
    or newly introduced. The other document's profile result must therefore carry
    an explicit unknown when the continuing status cannot be established.
    """
    for change in changes:
        if change.change_type == "not_restated_in_new_document":
            new_assessment.unknown.append(
                f"{change.field}: this condition appears in the older supplied document but is not restated in the newer document; its continuing status requires the parent order or human review."
            )
        elif change.change_type == "not_found_in_old_document":
            old_assessment.unknown.append(
                f"{change.field}: this condition appears in the newer supplied document but was not found in the older document; its prior status requires the parent order or human review."
            )
        elif change.change_type == "needs_review":
            note = (
                f"{change.field}: the comparison is ambiguous or has multiple same-scope rules; "
                "manual review is required before relying on this condition."
            )
            if change.old_pages:
                old_assessment.unknown.append(note)
            if change.new_pages:
                new_assessment.unknown.append(note)

    for assessment in (old_assessment, new_assessment):
        if assessment.unknown and assessment.outcome != "fails_extracted_conditions":
            assessment.outcome = "insufficient_evidence"

    return old_assessment, new_assessment


def carry_forward_limited_amendment_rules(
    old_rules: list[VerifiedRule],
    new_rules: list[VerifiedRule],
    changes: list[RuleChange],
    amendment_scope: AmendmentScopeEvidence | None,
) -> list[VerifiedRule]:
    """Build the effective rule set for a verified, explicitly limited erratum.

    Only old rules labelled unchanged_by_limited_amendment are carried forward.
    This does not run for incomplete or unverified amendment links.
    """
    if not amendment_scope or not amendment_scope.verified:
        return list(new_rules)

    inherited_keys = {
        (change.field, (change.scope or "").strip().casefold())
        for change in changes
        if change.change_type == "unchanged_by_limited_amendment"
    }
    existing_keys = {
        (item.rule.field, (item.rule.scope or "").strip().casefold())
        for item in new_rules
    }
    inherited = [
        item for item in old_rules
        if (item.rule.field, (item.rule.scope or "").strip().casefold()) in inherited_keys
        and (item.rule.field, (item.rule.scope or "").strip().casefold()) not in existing_keys
        and item.evidence.verified
        and item.rule.status == "explicit"
    ]
    return list(new_rules) + inherited
