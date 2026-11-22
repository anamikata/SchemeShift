from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from .models import AmendmentScopeEvidence, RuleChange, VerifiedRule


def canonical_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).casefold()
    if isinstance(value, str):
        return " ".join(value.casefold().split())
    return str(value).casefold()


def _rule_key(item: VerifiedRule) -> tuple[str, str]:
    return (item.rule.field, (item.rule.scope or "").strip().casefold())


def _group_rules(rules: list[VerifiedRule]) -> dict[tuple[str, str], list[VerifiedRule]]:
    grouped: dict[tuple[str, str], list[VerifiedRule]] = defaultdict(list)
    for item in rules:
        if item.evidence.verified:
            grouped[_rule_key(item)].append(item)
    return grouped


def _explanation_ml(change_type: str) -> str:
    explanations = {
        "modified": "ഈ വ്യവസ്ഥയുടെ മൂല്യമോ നിബന്ധനയോ രണ്ട് രേഖകളിൽ വ്യത്യസ്തമാണ്. ഉറവിട ഉദ്ധരണികൾ പരിശോധിക്കുക.",
        "unchanged": "പരിശോധിച്ച വ്യവസ്ഥയുടെ മൂല്യവും താരതമ്യ രീതിയും രണ്ട് രേഖകളിലും ഒരുപോലെയാണ്.",
        "not_restated_in_new_document": "പഴയ രേഖയിൽ ഈ വ്യവസ്ഥ കണ്ടെത്തി; പുതിയ രേഖയിൽ ആവർത്തിച്ചിട്ടില്ല. ഇതുകൊണ്ട് മാത്രം വ്യവസ്ഥ റദ്ദായെന്ന് പറയാനാവില്ല.",
        "not_found_in_old_document": "പുതിയ രേഖയിൽ ഈ വ്യവസ്ഥ കണ്ടെത്തി; നൽകിയ പഴയ രേഖയിൽ കണ്ടെത്തിയില്ല. ഇത് പുതുതായി ചേർത്തതാണെന്ന് ഇതുകൊണ്ട് മാത്രം ഉറപ്പിക്കാനാവില്ല.",
        "unchanged_by_limited_amendment": "പുതിയ രേഖ പഴയ ഉത്തരവിനെ വ്യക്തമായി ഉദ്ധരിക്കുകയും മാറ്റം പറഞ്ഞ പരിധിയിൽ മാത്രം ആണെന്ന് സ്ഥിരീകരിക്കുകയും ചെയ്യുന്നു. അതിനാൽ ഇവിടെ ആവർത്തിക്കാത്ത ഈ വ്യവസ്ഥ മാറ്റമില്ലാതെ തുടരുന്നതായി കാണിക്കുന്നു.",
        "needs_review": "ഒന്നിലധികം വ്യവസ്ഥകൾ ഒരേ വിഭാഗത്തിൽ കണ്ടെത്തി. സ്വയമേവ താരതമ്യം ചെയ്യാതെ മനുഷ്യ പരിശോധന ആവശ്യമാണ്.",
    }
    return explanations[change_type]


def compare_rules(
    old_rules: list[VerifiedRule],
    new_rules: list[VerifiedRule],
    amendment_scope: AmendmentScopeEvidence | None = None,
) -> list[RuleChange]:
    """Compare only evidence-verified rules; avoid silently overwriting duplicates.

    Missing clauses are never interpreted as repealed or newly introduced.
    Multiple same-field/same-scope rules are surfaced for human review because
    automatic one-to-one matching may pair the wrong thresholds or subgroups.
    """
    old_map = _group_rules(old_rules)
    new_map = _group_rules(new_rules)
    keys = sorted(set(old_map) | set(new_map))
    changes: list[RuleChange] = []
    # A scope statement is not enough by itself: require at least one
    # independently verified old/new rule pair that actually changed.
    has_verified_change = any(
        len(old_map.get(key, [])) == 1
        and len(new_map.get(key, [])) == 1
        and (
            canonical_value(old_map[key][0].rule.value) != canonical_value(new_map[key][0].rule.value)
            or old_map[key][0].rule.operator != new_map[key][0].rule.operator
            or canonical_value(old_map[key][0].rule.unit or "") != canonical_value(new_map[key][0].rule.unit or "")
        )
        for key in keys
    )
    scope_can_carry_forward = bool(amendment_scope and amendment_scope.verified and has_verified_change)

    for key in keys:
        old_items = old_map.get(key, [])
        new_items = new_map.get(key, [])
        field, scope = key

        if any(item.rule.status != "explicit" for item in old_items + new_items):
            changes.append(
                RuleChange(
                    field=field,
                    scope=scope or None,
                    change_type="needs_review",
                    old_value=[item.rule.value for item in old_items] or None,
                    new_value=[item.rule.value for item in new_items] or None,
                    old_quote="\n\n".join(item.rule.quote for item in old_items) or None,
                    new_quote="\n\n".join(item.rule.quote for item in new_items) or None,
                    old_pages=[item.rule.page for item in old_items],
                    new_pages=[item.rule.page for item in new_items],
                    explanation="At least one extracted condition is marked conditional or ambiguous. It is not automatically compared as a definitive rule.",
                    explanation_ml="കുറഞ്ഞത് ഒരു വ്യവസ്ഥയെങ്കിലും നിബന്ധനാപരമോ അവ്യക്തമോ ആണ്. അതിനെ നിർണായകമായ വ്യവസ്ഥയായി സ്വയമേവ താരതമ്യം ചെയ്യുന്നില്ല.",
                )
            )
            continue

        if len(old_items) > 1 or len(new_items) > 1:
            old_values = [item.rule.value for item in old_items]
            new_values = [item.rule.value for item in new_items]
            old_quotes = "\n\n".join(item.rule.quote for item in old_items) or None
            new_quotes = "\n\n".join(item.rule.quote for item in new_items) or None
            changes.append(
                RuleChange(
                    field=field,
                    scope=scope or None,
                    change_type="needs_review",
                    old_value=old_values or None,
                    new_value=new_values or None,
                    old_quote=old_quotes,
                    new_quote=new_quotes,
                    old_pages=[item.rule.page for item in old_items],
                    new_pages=[item.rule.page for item in new_items],
                    explanation="Multiple verified rules share this field and scope. They are shown together for manual matching rather than being paired automatically.",
                    explanation_ml=_explanation_ml("needs_review"),
                )
            )
            continue

        old = old_items[0] if old_items else None
        new = new_items[0] if new_items else None

        if old and new:
            same = (
                canonical_value(old.rule.value) == canonical_value(new.rule.value)
                and old.rule.operator == new.rule.operator
                and canonical_value(old.rule.unit or "") == canonical_value(new.rule.unit or "")
            )
            changes.append(
                RuleChange(
                    field=field,
                    scope=scope or None,
                    change_type="unchanged" if same else "modified",
                    old_value=old.rule.value,
                    new_value=new.rule.value,
                    old_unit=old.rule.unit,
                    new_unit=new.rule.unit,
                    old_quote=old.rule.quote,
                    new_quote=new.rule.quote,
                    old_pages=[old.rule.page],
                    new_pages=[new.rule.page],
                    explanation=(
                        "The verified condition has the same value and operator in both documents."
                        if same
                        else "The verified condition differs in value, operator, or unit; review the quoted clauses."
                    ),
                    explanation_ml=_explanation_ml("unchanged" if same else "modified"),
                )
            )
        elif old:
            if scope_can_carry_forward:
                changes.append(
                    RuleChange(
                        field=field,
                        scope=scope or None,
                        change_type="unchanged_by_limited_amendment",
                        old_value=old.rule.value,
                        new_value=old.rule.value,
                        old_unit=old.rule.unit,
                        new_unit=old.rule.unit,
                        old_quote=old.rule.quote,
                        new_quote=amendment_scope.scope_quote,
                        old_pages=[old.rule.page],
                        new_pages=[amendment_scope.scope_page] if amendment_scope.scope_page else [],
                        explanation="This condition is not repeated in the amendment, but the newer document explicitly cites the uploaded older order and says it is modified only to the stated extent. The condition is therefore treated as unchanged by this limited amendment, not independently re-extracted from the amendment.",
                        explanation_ml=_explanation_ml("unchanged_by_limited_amendment"),
                    )
                )
            else:
                changes.append(
                    RuleChange(
                        field=field,
                        scope=scope or None,
                        change_type="not_restated_in_new_document",
                        old_value=old.rule.value,
                        old_unit=old.rule.unit,
                        old_quote=old.rule.quote,
                        old_pages=[old.rule.page],
                        explanation="This condition was found in the older document but not in the newer document. It may continue through a parent order; absence alone does not prove repeal.",
                        explanation_ml=_explanation_ml("not_restated_in_new_document"),
                    )
                )
        elif new:
            changes.append(
                RuleChange(
                    field=field,
                    scope=scope or None,
                    change_type="not_found_in_old_document",
                    new_value=new.rule.value,
                    new_unit=new.rule.unit,
                    new_quote=new.rule.quote,
                    new_pages=[new.rule.page],
                    explanation="This condition was found in the newer document but not in the older document supplied. It may be newly introduced, or the older PDF may not contain the relevant parent clause.",
                    explanation_ml=_explanation_ml("not_found_in_old_document"),
                )
            )

    return changes


def exclude_verified_amendment_pair_duplicates(changes, amendment_pairs):
    """Avoid presenting an explicitly verified correction as an unrelated new rule.

    The dedicated amendment-pair panel carries the before/after relationship and
    source evidence. Remove only generic 'not found in old' rows whose exact new
    quotation is already represented by a verified pair; leave all other rules
    and uncertainty classifications untouched.
    """
    verified_quotes = {
        canonical_value(pair.quote)
        for pair in amendment_pairs
        if pair.verified and pair.quote
    }
    if not verified_quotes:
        return changes
    return [
        change for change in changes
        if not (
            change.change_type == "not_found_in_old_document"
            and change.new_quote
            and canonical_value(change.new_quote) in verified_quotes
        )
    ]
