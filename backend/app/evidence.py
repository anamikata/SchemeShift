from __future__ import annotations

import re
import unicodedata
from typing import Any

from .models import AmendmentScopeEvidence, EvidenceCheck, ExtractedRule, RuleExtraction, VerifiedRule
from .pdf_extract import ExtractedDocument


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value or "")
    value = value.replace("\u00a0", " ").replace("\u200b", "")
    return re.sub(r"\s+", " ", value).strip().casefold()


def _normalize_citation_quote(value: str) -> str:
    """Normalize citation quotes when PDF layout extraction splits a hyphenated token.

    pypdf's layout mode can insert a line break after a hyphen (for example,
    ``11-08-\n2025``). Treating that layout break as a literal space makes an
    otherwise exact citation quotation fail verification.
    """
    normalized = normalize_text(value)
    return re.sub(r"(?<=\d)-\s+(?=\d)", "-", normalized)


def _ascii_digits(value: str) -> str:
    """Normalize Malayalam numerals so evidence checks can compare them safely."""
    malayalam_digits = "൦൧൨൩൪൫൬൭൮൯"
    return value.translate(str.maketrans({digit: str(index) for index, digit in enumerate(malayalam_digits)}))


def _number_tokens(value: Any) -> set[str]:
    """Return canonical numeric tokens, including Indian comma-grouped figures."""
    if isinstance(value, bool) or value is None:
        return set()
    if isinstance(value, (int, float)):
        raw = str(value)
    elif isinstance(value, list):
        tokens: set[str] = set()
        for item in value:
            tokens |= _number_tokens(item)
        return tokens
    else:
        raw = str(value)

    raw = _ascii_digits(raw)
    # Treat commas as grouping separators (₹6,00,000 -> 600000). Preserve
    # decimal points so values such as 60.5 remain distinct from 605.
    found = re.findall(r"(?<![\w])\d[\d,]*(?:\.\d+)?", raw)
    normalized: set[str] = set()
    for token in found:
        compact = token.replace(",", "")
        try:
            number = float(compact)
            canonical = str(int(number)) if number.is_integer() else format(number, ".12g")
        except ValueError:
            canonical = compact
        normalized.add(canonical)
    return normalized


def value_appears_in_quote(value: Any, quote: str) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        # Boolean values are interpretations; the source quote itself is the evidence.
        return True
    if isinstance(value, (int, float)):
        tokens = _number_tokens(value)
        quote_tokens = _number_tokens(quote)
        return bool(tokens) and tokens.issubset(quote_tokens)
    if isinstance(value, list):
        if not value:
            return False
        return all(value_appears_in_quote(item, quote) for item in value)
    normalized_value = normalize_text(str(value))
    normalized_quote = normalize_text(quote)
    return bool(normalized_value) and normalized_value in normalized_quote


def numeric_operator_supported(field: str, operator: str, quote: str) -> bool:
    """Conservatively check whether numeric comparison wording supports the operator."""
    numeric_fields = {
        "max_age_years",
        "max_annual_family_income_inr",
        "min_marks_percent",
        "university_rank_max",
    }
    if field not in numeric_fields:
        return True

    text = normalize_text(quote)
    patterns = {
        "<": r"\b(below|under|less than|younger than)\b|താഴെ|കുറവായ|ൽ താഴെ",
        "<=": r"\b(up to|at most|not more than|no more than|not exceed|not exceeding|does not exceed|maximum)\b|\btop\s+\d|വരെ|കവിയരുത്|കൂടരുത്|അധികമാകരുത്",
        ">": r"\b(above|over|more than|greater than|exceeding)\b|മുകളിൽ|കൂടുതൽ|അധികം",
        ">=": r"\b(at least|minimum|not less than|no less than)\b|കുറഞ്ഞത്|കുറയാതെ",
    }
    pattern = patterns.get(operator)
    if pattern is None:
        return False
    return re.search(pattern, text) is not None


def unit_appears_in_quote(unit: str | None, quote: str) -> bool:
    if not unit:
        return True
    unit_text = normalize_text(unit)
    quote_text = normalize_text(quote)
    unit_groups = (
        ("lakh", ("lakh", "lac", "lakhs", "ലക്ഷം")),
        ("crore", ("crore", "crores", "cr", "കോടി")),
        ("percent", ("%", "percent", "per cent", "ശതമാനം")),
        ("currency", ("inr", "rupee", "rupees", "₹", "rs.", "rs ", "രൂപ")),
        ("year", ("year", "years", "yr", "yrs", "വർഷം", "വയസ്സ്", "വയസ്സിൽ", "വയസ്")),
        ("month", ("month", "months", "മാസം")),
    )
    recognized = False
    for _name, aliases in unit_groups:
        if any(alias in unit_text for alias in aliases):
            recognized = True
            if not any(alias in quote_text for alias in aliases):
                return False
    # For uncommon units, require an exact textual match instead of trusting the model.
    return recognized or unit_text in quote_text


def boolean_value_supported(field: str, value: Any, quote: str) -> bool:
    """Require explicit wording for the polarity of boolean condition fields."""
    if not isinstance(value, bool):
        return True
    text = normalize_text(quote)
    patterns = {
        "requires_full_time": {
            True: r"full[ -]?time|regular research|മുഴുവൻ സമയ|പൂർണ്ണ സമയ|സ്ഥിരം ഗവേഷണ",
            False: r"part[ -]?time.{0,40}(eligible|allowed|permitted)|full[ -]?time.{0,30}(not required|not mandatory)|പാർട്ട് ടൈം.{0,30}(അനുവദി|അർഹ)",
        },
        "other_fellowship_prohibited": {
            True: r"shall not (?:receive|draw|avail).{0,45}(other|another).{0,25}fellowship|not eligible.{0,50}(other|another).{0,25}fellowship|മറ്റൊരു ഫെല്ലോഷിപ്പ്.{0,35}(ലഭിക്കരുത്|അനുവദനീയമല്ല)",
            False: r"may (?:also )?receive.{0,40}(other|another).{0,25}fellowship|permitted to receive.{0,40}fellowship|മറ്റൊരു ഫെല്ലോഷിപ്പ്.{0,35}(ലഭിക്കാം|അനുവദനീയമാണ്)",
        },
        "one_child_per_family": {
            True: r"one child.{0,30}family|only one child|single child.{0,30}family|ഒരു കുട്ടി.{0,30}കുടുംബം|ഒരു കുട്ടിക്ക് മാത്രം",
            False: r"more than one child.{0,30}(eligible|may apply)|all eligible children.{0,30}apply|ഒന്നിലധികം കുട്ടികൾ.{0,30}(അപേക്ഷിക്കാം|അർഹ)",
        },
        "scholarship_one_time": {
            True: r"only once|one time only|once only|not more than once|ഒരിക്കൽ മാത്രം|ഒരു തവണ മാത്രം",
            False: r"more than once|multiple times|may be availed again|ഒന്നിലധികം തവണ|വീണ്ടും ലഭിക്കാം",
        },
    }
    field_patterns = patterns.get(field)
    if not field_patterns:
        return True
    return re.search(field_patterns[value], text) is not None


def verify_rule(rule: ExtractedRule, document: ExtractedDocument) -> VerifiedRule:
    page = next((p for p in document.pages if p.page_number == rule.page), None)
    if page is None:
        check = EvidenceCheck(
            verified=False,
            quote_found=False,
            value_supported=False,
            operator_supported=False,
            unit_supported=False,
            reason=f"Page {rule.page} does not exist in the uploaded document.",
        )
        return VerifiedRule(rule=rule, evidence=check)

    quote_found = normalize_text(rule.quote) in normalize_text(page.text)
    value_supported = value_appears_in_quote(rule.value, rule.quote) and boolean_value_supported(rule.field, rule.value, rule.quote)
    operator_supported = numeric_operator_supported(rule.field, rule.operator, rule.quote)
    unit_supported = unit_appears_in_quote(rule.unit, rule.quote)
    verified = quote_found and value_supported and operator_supported and unit_supported

    if not quote_found:
        reason = "The supplied quotation was not found verbatim on the stated page after whitespace normalization."
    elif not value_supported:
        reason = "The extracted value is not supported by the quotation."
    elif not operator_supported:
        reason = "The quote does not clearly support the extracted numeric comparison operator; manual review is required."
    elif not unit_supported:
        reason = "The extracted unit was not found in the source quotation; manual review is required."
    else:
        reason = "The quotation, extracted value, and supported comparison wording were found on the stated source page."

    return VerifiedRule(
        rule=rule,
        evidence=EvidenceCheck(
            verified=verified,
            quote_found=quote_found,
            value_supported=value_supported,
            operator_supported=operator_supported,
            unit_supported=unit_supported,
            reason=reason,
        ),
    )


def verify_extraction(rules: list[ExtractedRule], document: ExtractedDocument) -> list[VerifiedRule]:
    return [verify_rule(rule, document) for rule in rules]


def _normalized_order_id(value: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").casefold())


_ORDER_IDENTIFIER_RE = re.compile(
    r"G\s*\.?\s*O\s*\.?\s*\(\s*[^)]{1,12}\s*\)\s*No\.?\s*"
    r"[\w.-]+\s*/\s*\d{4}\s*/\s*[\w.-]+",
    re.IGNORECASE,
)


def _header_order_id(document: ExtractedDocument) -> str | None:
    """Read the first Government Order identifier from the supplied old PDF header."""
    if not document.pages:
        return None
    header_text = (document.pages[0].text or "")[:2000]
    match = _ORDER_IDENTIFIER_RE.search(header_text)
    return _normalized_order_id(match.group(0)) if match else None


def _explicit_parent_reference_pages(order_id: str, document: ExtractedDocument) -> list[int]:
    """Find pages where the order ID is explicitly cited as a read/referred order."""
    normalized_id = _normalized_order_id(order_id)
    if not normalized_id:
        return []
    pages: list[int] = []
    for page in document.pages:
        for referenced_id, _start, _end in _explicit_order_references(page.text):
            if referenced_id == normalized_id:
                pages.append(page.page_number)
                break
    return pages


def _explicit_order_references(text: str) -> list[tuple[str, int, int]]:
    normalized_text = normalize_text(text)
    references = []
    for match in _ORDER_IDENTIFIER_RE.finditer(normalized_text):
        prefix = normalized_text[max(0, match.start() - 120):match.start()]
        if re.search(r"\b(?:read|vide|refer(?:red)?|cited)\b.{0,80}$", prefix):
            references.append((_normalized_order_id(match.group(0)), match.start(), match.end()))
    return references


def _resolved_order_before_generic_reference(page_text: str, quote: str) -> str | None:
    normalized_text = normalize_text(page_text)
    normalized_quote = normalize_text(quote)
    if not normalized_quote:
        return None
    quote_position = normalized_text.find(normalized_quote)
    if quote_position < 0:
        return None
    preceding = [
        reference_id
        for reference_id, _start, end in _explicit_order_references(page_text)
        if end <= quote_position
    ]
    return preceding[-1] if preceding else None


def verify_limited_amendment_link(
    old_extraction: RuleExtraction,
    new_extraction: RuleExtraction,
    old_document: ExtractedDocument,
    new_document: ExtractedDocument,
) -> AmendmentScopeEvidence:
    """Verify that a newer document explicitly limits changes to a cited parent order.

    The AI's classification is never trusted alone. The supplied older PDF's
    first-page order identifier must match a literal parent citation in the newer
    PDF. A generic "read above" reference is accepted only when it can be resolved
    to that independent, page-level citation. The scope quote must also occur on
    its stated page and contain an explicit limited-effect phrase.
    """
    effect = new_extraction.amendment_effect
    result = AmendmentScopeEvidence(
        verified=False,
        effect=effect,
        referenced_order_number=new_extraction.amends_order_number,
        scope_quote=new_extraction.amendment_scope_quote,
        scope_page=new_extraction.amendment_scope_page,
        reason="The newer document does not contain a verifiable limited-scope amendment link to the uploaded older order.",
    )
    if effect != "specific_changes_only":
        return result

    old_id = _normalized_order_id(old_extraction.order_number)
    header_id = _header_order_id(old_document)
    cited_id = _normalized_order_id(new_extraction.amends_order_number)
    if not old_id or header_id != old_id:
        result.reason = "The older document's extracted order number does not match an order identifier in its first-page header."
        return result
    if cited_id and cited_id != old_id:
        result.reason = "The order number cited by the newer document does not match the uploaded older document's extracted order number."
        return result

    matching_reference_pages = _explicit_parent_reference_pages(old_extraction.order_number, new_document)
    if not matching_reference_pages:
        result.reason = "The newer document does not explicitly cite the uploaded older order; a generic 'read above' reference alone is insufficient."
        return result

    if new_extraction.amends_order_page is not None:
        reference_page = next((p for p in new_document.pages if p.page_number == new_extraction.amends_order_page), None)
        if reference_page is None or reference_page.page_number not in matching_reference_pages:
            result.reason = "The explicit parent-order citation was not found on the stated page of the newer document."
            return result
    elif len(matching_reference_pages) == 1:
        reference_page = next((p for p in new_document.pages if p.page_number == matching_reference_pages[0]), None)
    else:
        result.reason = "The explicit parent-order citation appears on multiple pages and no page was identified."
        return result

    scope_page = next((p for p in new_document.pages if p.page_number == new_extraction.amendment_scope_page), None)
    reference_quote = new_extraction.amends_order_quote or ""
    scope_quote = new_extraction.amendment_scope_quote or ""

    if reference_quote and _normalize_citation_quote(reference_quote) not in _normalize_citation_quote(reference_page.text):
        result.reason = "The extracted parent-order quotation could not be verified on the cited page of the newer document."
        return result
    if reference_quote and _normalized_order_id(old_extraction.order_number) not in _normalized_order_id(reference_quote):
        # A page-verified generic phrase is usable only because the same page
        # independently contains the direct parent citation matched above.
        generic_reference = re.search(
            r"\b(?:government\s+)?order\s+read\s+above\b|\bread\s+above\b",
            normalize_text(reference_quote),
        )
        if not generic_reference or reference_page.page_number not in matching_reference_pages:
            result.reason = "The parent-order quotation is neither a direct order citation nor a resolvable 'read above' reference."
            return result
        resolved_id = _resolved_order_before_generic_reference(reference_page.text, reference_quote)
        if resolved_id != old_id:
            result.reason = "The generic 'read above' reference is ambiguous or resolves to a different cited order."
            return result
    elif not reference_quote and not cited_id:
        all_referenced_ids = {
            reference_id
            for page in new_document.pages
            for reference_id, _start, _end in _explicit_order_references(page.text)
        }
        if all_referenced_ids != {old_id}:
            result.reason = "The explicit parent-order reference is ambiguous because no citation quotation or order number was extracted."
            return result
    if scope_page is None or not scope_quote or normalize_text(scope_quote) not in normalize_text(scope_page.text):
        result.reason = "The limited-scope quotation could not be verified on the stated page of the newer document."
        return result

    scope_text = normalize_text(scope_quote)
    limited_phrases = (
        "stands modified to this extent only",
        "modified to this extent only",
        "modified to the extent stated above only",
        "to this extent only",
        "ഈ പരിധിയിൽ മാത്രം ഭേദഗതി",
    )
    if not any(phrase in scope_text for phrase in limited_phrases):
        result.reason = "The verified scope quotation does not contain a recognized explicit limited-effect phrase."
        return result

    result.verified = True
    result.referenced_order_number = old_extraction.order_number
    result.reason = "The newer document explicitly cites the uploaded older order and verifies that it is modified only to the stated extent."
    return result


def _canonical_number(value: Any) -> str | None:
    tokens = _number_tokens(value)
    return next(iter(tokens)) if len(tokens) == 1 else None


def _find_amount_evidence(value: Any, unit: str, document: ExtractedDocument) -> tuple[int, str] | None:
    """Find a source-page excerpt containing the exact numeric value and its unit."""
    target = _canonical_number(value)
    if target is None or not unit:
        return None
    for page in document.pages:
        text = _ascii_digits(page.text or "")
        for match in re.finditer(r"(?<![\w])\d[\d,]*(?:\.\d+)?(?![\w])", text):
            if _canonical_number(match.group(0)) != target:
                continue
            # Keep the unit close to the number; a unit elsewhere on the page is not enough.
            window = text[match.end():match.end() + 48]
            if not unit_appears_in_quote(unit, window):
                continue
            start = max(0, match.start() - 90)
            end = min(len(text), match.end() + 90)
            excerpt = text[start:end].strip()
            return page.page_number, excerpt
    return None


_AMOUNT_MENTION_RE = re.compile(
    r"(?<![\w])(?P<value>[0-9൦-൯][0-9,൦-൯]*(?:\.[0-9]+)?)(?![\w])\s*"
    r"(?P<unit>crores?|cr\.?|lakhs?|lacs?|percent|per\s+cent|%|"
    r"rupees?|inr|rs\.?|₹|ലക്ഷം|കോടി|ശതമാനം|രൂപ)",
    re.IGNORECASE,
)
_ORDINALS = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth")
_TARGET_ANCHOR_RE = re.compile(
    r"\b(?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"\d+(?:st|nd|rd|th)?)\s+(?:para(?:graph)?|clause)\b|"
    r"\b(?:para(?:graph)?|clause)\s+(?P<ordinal_after>first|second|third|fourth|fifth|"
    r"sixth|seventh|eighth|ninth|tenth|\d+(?:st|nd|rd|th)?)\b",
    re.IGNORECASE,
)


def _canonical_unit(unit: str) -> str:
    normalized = normalize_text(unit).rstrip(".")
    if normalized in {"crore", "crores", "cr"}:
        return "crore"
    if normalized in {"lakh", "lakhs", "lac", "lacs"}:
        return "lakh"
    if normalized in {"percent", "per cent", "%", "ശതമാനം"}:
        return "percent"
    if normalized in {"rupee", "rupees", "inr", "rs", "₹", "രൂപ"}:
        return "currency"
    if normalized == "ലക്ഷം":
        return "lakh"
    if normalized == "കോടി":
        return "crore"
    return normalized


def _amount_mentions(quote: str) -> list[tuple[str, str, int, int]]:
    text = _ascii_digits(unicodedata.normalize("NFC", quote or ""))
    return [
        (_canonical_number(match.group("value")) or "", _canonical_unit(match.group("unit")), match.start(), match.end())
        for match in _AMOUNT_MENTION_RE.finditer(text)
    ]


def _target_ordinal(value: str) -> str | None:
    normalized = normalize_text(value)
    match = _TARGET_ANCHOR_RE.search(normalized)
    if not match:
        return None
    token = match.group("ordinal") or match.group("ordinal_after")
    token = token.removesuffix("st").removesuffix("nd").removesuffix("rd").removesuffix("th")
    if token.isdigit():
        number = int(token)
        return _ORDINALS[number - 1] if 1 <= number <= len(_ORDINALS) else str(number)
    return token


def _pair_is_associated_within_quote(pair, quote: str) -> bool:
    """Require a source-local, unambiguous association between each old/new amount."""
    mentions = _amount_mentions(quote)
    expected_old = (_canonical_number(pair.old_value), _canonical_unit(pair.old_unit))
    expected_new = (_canonical_number(pair.new_value), _canonical_unit(pair.new_unit))
    target_ordinal = _target_ordinal(pair.target)
    text = _ascii_digits(unicodedata.normalize("NFC", quote or "")).casefold()

    # A single correction is accepted only when the quotation contains exactly
    # one old and one corrected amount, in that order, with correction wording
    # between them. Extra amounts make this shape ambiguous.
    if len(mentions) == 2:
        old, new = mentions
        bridge = text[old[3]:new[2]]
        correction_wording = re.search(
            r"\b(?:correct(?:ed|s|ing)?|revis(?:e|ed|es|ing)|amend(?:ed|s|ing)?|"
            r"substitut(?:e|ed|es|ing)|chang(?:e|ed|es|ing)|read\s+as)\b",
            bridge,
        )
        anchors = [
            (match.group("ordinal") or match.group("ordinal_after"), match.start())
            for match in _TARGET_ANCHOR_RE.finditer(text)
        ]
        if anchors and target_ordinal:
            anchor_tokens = [
                _target_ordinal(f"{ordinal} paragraph")
                for ordinal, _position in anchors
            ]
            if target_ordinal not in anchor_tokens:
                return False
        return (
            correction_wording is not None
            and (old[0], old[1]) == expected_old
            and (new[0], new[1]) == expected_new
        )

    # Multiple corrections need an explicit ordered mapping. The old side must
    # identify each target paragraph/clause, the corrected side must have the
    # same number of amounts, and "respectively" must connect those sequences.
    delimiter = re.search(r"\bread\s+above\s+as\b", text)
    respectively = re.search(r"\brespectively\b", text)
    if not delimiter or not respectively or respectively.start() < delimiter.end():
        return False
    old_mentions = [item for item in mentions if item[2] < delimiter.start()]
    new_mentions = [item for item in mentions if delimiter.end() <= item[2] < respectively.start()]
    if len(old_mentions) < 2 or len(old_mentions) != len(new_mentions):
        return False

    anchors = list(_TARGET_ANCHOR_RE.finditer(text[:delimiter.start()]))
    if len(anchors) != len(old_mentions) or not target_ordinal:
        return False
    mapped_old: list[tuple[str, str, str]] = []
    for index, anchor in enumerate(anchors):
        ordinal = anchor.group("ordinal") or anchor.group("ordinal_after")
        canonical_ordinal = _target_ordinal(f"{ordinal} paragraph")
        if canonical_ordinal is None:
            return False
        mapped_old.append((canonical_ordinal, old_mentions[index][0], old_mentions[index][1]))

    return any(
        ordinal == target_ordinal
        and (old_value, old_unit) == expected_old
        and (new_mentions[index][0], new_mentions[index][1]) == expected_new
        for index, (ordinal, old_value, old_unit) in enumerate(mapped_old)
    )


def verify_amendment_pairs(
    pairs,
    old_document: ExtractedDocument,
    new_document: ExtractedDocument,
    amendment_scope: AmendmentScopeEvidence,
):
    """Verify explicit before/after pairs against both PDFs and the verified scope link.

    The AI's pair is accepted only if its quote exists on the cited amendment
    page, the old and corrected amounts are explicitly associated within that
    quote, the old amount/unit occurs in the uploaded older document, and the
    parent-order/limited-scope link is verified.
    """
    from .models import VerifiedAmendmentPair

    verified_pairs = []
    for pair in pairs:
        new_page = next((p for p in new_document.pages if p.page_number == pair.page), None)
        quote_found = bool(new_page and normalize_text(pair.quote) in normalize_text(new_page.text))
        old_value_in_quote = value_appears_in_quote(pair.old_value, pair.quote)
        new_value_in_quote = value_appears_in_quote(pair.new_value, pair.quote)
        old_unit_in_quote = unit_appears_in_quote(pair.old_unit, pair.quote)
        new_unit_in_quote = unit_appears_in_quote(pair.new_unit, pair.quote)
        associated_in_quote = _pair_is_associated_within_quote(pair, pair.quote)
        old_evidence = _find_amount_evidence(pair.old_value, pair.old_unit, old_document)

        scope_reason = (
            f"Parent-order reference and limited amendment scope are not verified: {amendment_scope.reason}"
            if amendment_scope
            else "No verified parent-order reference and limited amendment scope are available."
        )
        checks = [
            (bool(amendment_scope and amendment_scope.verified), scope_reason),
            (quote_found, "The amendment quotation was not found on the stated page."),
            (old_value_in_quote and old_unit_in_quote, "The original amount or unit is not supported by the amendment quotation."),
            (new_value_in_quote and new_unit_in_quote, "The corrected amount or unit is not supported by the amendment quotation."),
            (associated_in_quote, "The original and corrected amounts are not unambiguously associated with this target in the amendment quotation."),
            (old_evidence is not None, "The original amount and unit could not be located together in the uploaded older document."),
        ]
        failed = [message for passed, message in checks if not passed]
        verified = not failed
        verified_pairs.append(
            VerifiedAmendmentPair(
                target=pair.target,
                old_value=pair.old_value,
                old_unit=pair.old_unit,
                new_value=pair.new_value,
                new_unit=pair.new_unit,
                quote=pair.quote,
                page=pair.page,
                old_document_quote=old_evidence[1] if old_evidence else None,
                old_document_page=old_evidence[0] if old_evidence else None,
                verified=verified,
                reason=(
                    "The explicit correction is supported by the amendment quotation, the original amount appears in the uploaded older order, and the limited amendment link is verified."
                    if verified else " ".join(failed)
                ),
            )
        )
    return verified_pairs
