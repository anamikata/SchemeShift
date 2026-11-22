import json
from pathlib import Path

from app.compare import compare_rules, exclude_verified_amendment_pair_duplicates
from app.evidence import verify_amendment_pairs, verify_extraction, verify_limited_amendment_link
from app.models import ExtractedRule, RuleExtraction
from app.pdf_extract import ExtractedDocument, ExtractedPage


FIXTURE = Path(__file__).parent.parent.parent / "research" / "gold_pairs" / "pwd_erratum_2025.json"


def _document(pages: list[str]) -> ExtractedDocument:
    extracted = [ExtractedPage(page_number=i, text=text) for i, text in enumerate(pages, start=1)]
    total = sum(len(page.text) for page in extracted)
    return ExtractedDocument(extracted, len(extracted), total, False)


def _rules(records: list[dict]) -> list[ExtractedRule]:
    return [ExtractedRule(**record) for record in records]


def test_pwd_official_erratum_gold_fixture():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    new_doc = _document(fixture["new_document"]["pages"])

    old_extraction = RuleExtraction(
        order_number=fixture["old_document"]["order_number"],
        rules=_rules(fixture["gold_rules"]["old"]),
    )
    amendment = fixture["new_document"]["amendment"]
    new_extraction = RuleExtraction(
        order_number=fixture["new_document"]["order_number"],
        rules=_rules(fixture["gold_rules"]["new"]),
        amendment_effect=amendment["effect"],
        amends_order_number=amendment["amends_order_number"],
        amends_order_quote=amendment["amends_order_quote"],
        amends_order_page=amendment["amends_order_page"],
        amendment_scope_quote=amendment["scope_quote"],
        amendment_scope_page=amendment["scope_page"],
    )

    old_verified = verify_extraction(old_extraction.rules, old_doc)
    new_verified = verify_extraction(new_extraction.rules, new_doc)
    assert all(item.evidence.verified for item in old_verified)
    assert all(item.evidence.verified for item in new_verified)

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)
    assert scope.verified is True

    # The explicit before/after amount corrections are verified independently
    # against the amendment quote and the original uploaded order.
    from app.models import ExtractedAmendmentPair
    amendment_pairs = [
        ExtractedAmendmentPair(
            target="first paragraph amount", old_value=350, old_unit="Crores",
            new_value=350, new_unit="Lakh",
            quote="Government have pleased to correct the amounts mentioned in the first para as Rs. 350 Crores and in the second para as Rs. 689 Crores in the Government Order read above as Rs. 350 Lakh and Rs. 689 Lakh respectively.",
            page=1,
        ),
        ExtractedAmendmentPair(
            target="second paragraph amount", old_value=689, old_unit="Crores",
            new_value=689, new_unit="Lakh",
            quote="Government have pleased to correct the amounts mentioned in the first para as Rs. 350 Crores and in the second para as Rs. 689 Crores in the Government Order read above as Rs. 350 Lakh and Rs. 689 Lakh respectively.",
            page=1,
        ),
    ]
    verified_pairs = verify_amendment_pairs(amendment_pairs, old_doc, new_doc, scope)
    assert len(verified_pairs) == 2
    assert all(pair.verified for pair in verified_pairs)
    assert [(pair.old_value, pair.old_unit, pair.new_value, pair.new_unit) for pair in verified_pairs] == [
        (350, "Crores", 350, "Lakh"), (689, "Crores", 689, "Lakh")
    ]
    assert all(pair.old_document_page == 1 for pair in verified_pairs)

    changes = compare_rules(old_verified, new_verified, scope)
    actual = {item.scope: item for item in changes}
    for expected in fixture["expected_changes"]:
        change = actual[expected["scope"]]
        assert change.change_type == expected["change_type"]
        assert change.old_value == expected["old_value"]
        assert change.new_value == expected["new_value"]
        assert change.old_unit == expected["old_unit"]
        assert change.new_unit == expected["new_unit"]


def test_pwd_erratum_resolves_generic_read_above_to_explicit_parent_citation():
    """The generic operative reference is resolved through the literal Read line on page 1."""
    from app.evidence import verify_amendment_pairs
    from app.models import ExtractedAmendmentPair

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    new_doc = _document(fixture["new_document"]["pages"] + ["Second page contains no amendment clauses."])
    old_extraction = RuleExtraction(
        order_number="G.O.(Rt) No.1217/2025/PWD",
        order_date="2025-08-11",
        rules=[],
    )
    scope_quote = "The Government Order read above stands modified to this extent only."
    pair_quote = (
        "Government have pleased to correct the amounts mentioned in the first para as Rs. 350 Crores "
        "and in the second para as Rs. 689 Crores in the Government Order read above as Rs. 350 Lakh "
        "and Rs. 689 Lakh respectively."
    )
    new_extraction = RuleExtraction(
        order_number="G.O.(Rt) No.1247/2025/PWD",
        rules=[],  # This erratum has corrections, not general eligibility conditions.
        amendment_effect="specific_changes_only",
        amends_order_number=None,
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=scope_quote,
        amendment_scope_page=1,
        amendment_pairs=[
            ExtractedAmendmentPair(
                target="first paragraph amount", old_value=350, old_unit="Crores",
                new_value=350, new_unit="Lakh", quote=pair_quote, page=1,
            ),
            ExtractedAmendmentPair(
                target="second paragraph amount", old_value=689, old_unit="Crores",
                new_value=689, new_unit="Lakh", quote=pair_quote, page=1,
            ),
        ],
    )

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)
    verified_pairs = verify_amendment_pairs(new_extraction.amendment_pairs, old_doc, new_doc, scope)

    assert scope.verified is True
    assert scope.scope_page == 1
    assert scope.referenced_order_number == "G.O.(Rt) No.1217/2025/PWD"
    assert all(pair.verified for pair in verified_pairs)
    assert [(pair.old_value, pair.old_unit, pair.new_value, pair.new_unit) for pair in verified_pairs] == [
        (350, "Crores", 350, "Lakh"), (689, "Crores", 689, "Lakh")
    ]
    assert new_doc.page_count == old_doc.page_count == 2
    assert new_extraction.rules == []


def test_pwd_real_pdf_layout_wrapped_parent_citation_quote_verifies():
    """Match the citation quote to the exact pypdf layout text from the real PDF."""
    old_id = "G.O.(Rt)No.1217/2025/PWD"
    old_doc = _document([f"G.O.(Rt)No.1217/2025/PWD Dated,Thiruvananthapuram, 11-08-2025", "page 2"])
    # Exact relevant page-one text extracted by pypdf layout mode from
    # govtorder2108202511_25_32.pdf: the date is split after the final hyphen.
    new_page = (
        "G.O.(Rt)No.1247/2025/PWD   Dated,Thiruvananthapuram, 14-08-2025\n"
        "Read  G.O.(Rt)No.1217/2025/PWD            Dated,Thiruvananthapuram,  11-08-\n"
        "      2025\n"
        "ORDER\n"
        "The Government Order read above stands modified to this extent only."
    )
    new_doc = _document([new_page, "page 2"])
    scope_quote = "The Government Order read above stands modified to this extent only."
    extraction = RuleExtraction(
        order_number="G.O.(Rt)No.1247/2025/PWD",
        amendment_effect="specific_changes_only",
        amends_order_quote=(
            "Read G.O.(Rt)No.1217/2025/PWD Dated,Thiruvananthapuram, 11-08-2025"
        ),
        amends_order_page=1,
        amendment_scope_quote=scope_quote,
        amendment_scope_page=1,
    )

    scope = verify_limited_amendment_link(
        RuleExtraction(order_number=old_id), extraction, old_doc, new_doc
    )

    assert scope.verified is True
    assert scope.referenced_order_number == old_id


def test_pwd_erratum_rejects_wrong_parent_even_when_read_above_is_quoted():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    new_doc = _document(fixture["new_document"]["pages"])
    amendment = fixture["new_document"]["amendment"]
    old_extraction = RuleExtraction(order_number=fixture["old_document"]["order_number"])
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number="G.O.(Rt) No.999/2025/PWD",
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=amendment["scope_quote"],
        amendment_scope_page=1,
    )

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)

    assert scope.verified is False
    assert "does not match" in scope.reason


def test_pwd_erratum_does_not_match_new_citation_to_wrong_older_document_header():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(["G.O.(Rt) No.999/2025/PWD. This is a different uploaded order."])
    new_doc = _document(fixture["new_document"]["pages"])
    old_extraction = RuleExtraction(order_number="G.O.(Rt) No.999/2025/PWD")
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number=None,
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=fixture["new_document"]["amendment"]["scope_quote"],
        amendment_scope_page=1,
    )

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)

    assert scope.verified is False
    assert "does not explicitly cite the uploaded older order" in scope.reason


def test_pwd_erratum_requires_scope_language_on_claimed_page():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    source_page = fixture["new_document"]["pages"][0]
    scope_clause = fixture["new_document"]["amendment"]["scope_quote"]
    # Simulate an amendment page that contains the parent citation and correction
    # but omits the scope sentence; no scope may be inferred from the title.
    no_scope_page = source_page.replace(f" {scope_clause}", "")
    new_doc = _document([no_scope_page, "The claimed scope quotation is not on this page."])
    old_extraction = RuleExtraction(order_number=fixture["old_document"]["order_number"])
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number=None,
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=scope_clause,
        amendment_scope_page=2,
    )

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)

    assert scope.verified is False
    assert "limited-scope quotation" in scope.reason


def test_pwd_erratum_rejects_generic_reference_without_literal_parent_citation():
    from app.models import ExtractedAmendmentPair
    from app.evidence import verify_amendment_pairs

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    quote = fixture["new_document"]["pages"][0]
    # Keep the operative phrase and corrections, but remove the direct Read
    # citation line. A generic reference cannot identify which order was uploaded.
    quote_without_parent = quote.replace("Read G.O.(Rt)No.1217/2025/PWD Dated,Thiruvananthapuram, 11-08-2025. ", "")
    new_doc = _document([quote_without_parent])
    scope_quote = fixture["new_document"]["amendment"]["scope_quote"]
    old_extraction = RuleExtraction(order_number=fixture["old_document"]["order_number"])
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number=None,
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=scope_quote,
        amendment_scope_page=1,
        amendment_pairs=[ExtractedAmendmentPair(
            target="first paragraph amount", old_value=350, old_unit="Crores",
            new_value=350, new_unit="Lakh",
            quote="Government have pleased to correct the amounts mentioned in the first para as Rs. 350 Crores "
            "and in the second para as Rs. 689 Crores in the Government Order read above as Rs. 350 Lakh "
            "and Rs. 689 Lakh respectively.",
            page=1,
        )],
    )

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)
    pair = verify_amendment_pairs(new_extraction.amendment_pairs, old_doc, new_doc, scope)[0]

    assert scope.verified is False
    assert "generic 'read above' reference alone is insufficient" in scope.reason
    assert pair.verified is False
    assert scope.reason in pair.reason


def test_pwd_erratum_rejects_ambiguous_read_above_after_multiple_parent_citations():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    page = fixture["new_document"]["pages"][0]
    # A second explicit parent citation becomes the nearest antecedent for
    # "Government Order read above"; the verifier must not guess which one.
    page = page.replace(
        "Government have pleased to correct",
        "Read G.O.(Rt)No.999/2025/PWD. Government have pleased to correct",
    )
    new_doc = _document([page])
    amendment = fixture["new_document"]["amendment"]
    old_extraction = RuleExtraction(order_number=fixture["old_document"]["order_number"])
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number=None,
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=amendment["scope_quote"],
        amendment_scope_page=1,
    )

    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)

    assert scope.verified is False
    assert "ambiguous or resolves to a different cited order" in scope.reason


def test_pwd_erratum_rejects_cross_paired_amounts_after_parent_resolution():
    from app.evidence import verify_amendment_pairs
    from app.models import ExtractedAmendmentPair

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    new_doc = _document(fixture["new_document"]["pages"] + ["Second page."])
    amendment = fixture["new_document"]["amendment"]
    pair_quote = (
        "Government have pleased to correct the amounts mentioned in the first para as Rs. 350 Crores "
        "and in the second para as Rs. 689 Crores in the Government Order read above as Rs. 350 Lakh "
        "and Rs. 689 Lakh respectively."
    )
    old_extraction = RuleExtraction(order_number=fixture["old_document"]["order_number"])
    new_extraction = RuleExtraction(
        amendment_effect="specific_changes_only",
        amends_order_number=None,
        amends_order_quote="Government Order read above",
        amends_order_page=1,
        amendment_scope_quote=amendment["scope_quote"],
        amendment_scope_page=1,
    )
    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)
    pairs = [
        ExtractedAmendmentPair(
            target="first paragraph amount", old_value=350, old_unit="Crores",
            new_value=689, new_unit="Lakh", quote=pair_quote, page=1,
        ),
        ExtractedAmendmentPair(
            target="second paragraph amount", old_value=689, old_unit="Crores",
            new_value=350, new_unit="Lakh", quote=pair_quote, page=1,
        ),
    ]

    verified_pairs = verify_amendment_pairs(pairs, old_doc, new_doc, scope)

    assert scope.verified is True
    assert all(not pair.verified for pair in verified_pairs)
    assert all("unambiguously associated" in pair.reason for pair in verified_pairs)


def test_pwd_erratum_pair_quote_must_be_on_its_claimed_page():
    from app.evidence import verify_amendment_pairs
    from app.models import AmendmentScopeEvidence, ExtractedAmendmentPair

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    new_doc = _document(fixture["new_document"]["pages"] + ["Second page has no correction quotation."])
    quote = (
        "Government have pleased to correct the amounts mentioned in the first para as Rs. 350 Crores "
        "and in the second para as Rs. 689 Crores in the Government Order read above as Rs. 350 Lakh "
        "and Rs. 689 Lakh respectively."
    )
    scope = AmendmentScopeEvidence(verified=True, effect="specific_changes_only", reason="verified")
    pair = ExtractedAmendmentPair(
        target="first paragraph amount", old_value=350, old_unit="Crores",
        new_value=350, new_unit="Lakh", quote=quote, page=2,
    )

    result = verify_amendment_pairs([pair], old_doc, new_doc, scope)

    assert result[0].verified is False
    assert "not found on the stated page" in result[0].reason


def test_pwd_gold_fixture_cannot_use_limited_scope_if_parent_reference_is_wrong():
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    new_doc = _document(fixture["new_document"]["pages"])
    old_extraction = RuleExtraction(
        order_number=fixture["old_document"]["order_number"],
        rules=_rules(fixture["gold_rules"]["old"]),
    )
    amendment = fixture["new_document"]["amendment"]
    new_extraction = RuleExtraction(
        order_number=fixture["new_document"]["order_number"],
        rules=_rules(fixture["gold_rules"]["new"]),
        amendment_effect=amendment["effect"],
        amends_order_number="G.O.(Rt)No.999/2025/PWD",
        amends_order_quote=amendment["amends_order_quote"],
        amends_order_page=amendment["amends_order_page"],
        amendment_scope_quote=amendment["scope_quote"],
        amendment_scope_page=amendment["scope_page"],
    )
    scope = verify_limited_amendment_link(old_extraction, new_extraction, old_doc, new_doc)
    assert scope.verified is False

    changes = compare_rules(
        verify_extraction(old_extraction.rules, old_doc),
        verify_extraction(new_extraction.rules, new_doc),
        scope,
    )
    final_amount = next(item for item in changes if item.scope == "final revised sanction amount")
    assert final_amount.change_type == "not_restated_in_new_document"


def test_amendment_pair_rejected_when_original_amount_is_not_in_old_document():
    from app.evidence import verify_amendment_pairs
    from app.models import AmendmentScopeEvidence, ExtractedAmendmentPair

    old_doc = _document(["Administrative sanction for Rs. 260 Lakhs."])
    new_doc = _document(["The amount as Rs. 350 Crores is corrected as Rs. 350 Lakh. The order stands modified to this extent only."])
    scope = AmendmentScopeEvidence(
        verified=True, effect="specific_changes_only", referenced_order_number="G.O.1",
        scope_quote="The order stands modified to this extent only.", scope_page=1, reason="verified",
    )
    pair = ExtractedAmendmentPair(
        target="first paragraph amount", old_value=350, old_unit="Crores",
        new_value=350, new_unit="Lakh",
        quote="The amount as Rs. 350 Crores is corrected as Rs. 350 Lakh.", page=1,
    )
    result = verify_amendment_pairs([pair], old_doc, new_doc, scope)
    assert result[0].verified is False
    assert "older document" in result[0].reason


def test_amendment_pair_rejected_without_verified_limited_scope():
    from app.evidence import verify_amendment_pairs
    from app.models import AmendmentScopeEvidence, ExtractedAmendmentPair

    old_doc = _document(["Administrative sanction for Rs. 350 Crores."])
    new_doc = _document(["The amount as Rs. 350 Crores is corrected as Rs. 350 Lakh."])
    scope = AmendmentScopeEvidence(verified=False, reason="scope not verified")
    pair = ExtractedAmendmentPair(
        target="amount", old_value=350, old_unit="Crores", new_value=350,
        new_unit="Lakh", quote="The amount as Rs. 350 Crores is corrected as Rs. 350 Lakh.", page=1,
    )
    result = verify_amendment_pairs([pair], old_doc, new_doc, scope)
    assert result[0].verified is False
    assert "limited amendment scope" in result[0].reason


def test_cross_paired_pwd_amounts_are_rejected():
    from app.evidence import verify_amendment_pairs
    from app.models import AmendmentScopeEvidence, ExtractedAmendmentPair

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    old_doc = _document(fixture["old_document"]["pages"])
    quote = fixture["new_document"]["pages"][0].split(" The Government Order read above stands modified")[0]
    new_doc = _document([quote])
    scope = AmendmentScopeEvidence(verified=True, effect="specific_changes_only", reason="verified")
    pairs = [
        ExtractedAmendmentPair(
            target="first paragraph amount", old_value=350, old_unit="Crores",
            new_value=689, new_unit="Lakh", quote=quote, page=1,
        ),
        ExtractedAmendmentPair(
            target="second paragraph amount", old_value=689, old_unit="Crores",
            new_value=350, new_unit="Lakh", quote=quote, page=1,
        ),
    ]

    result = verify_amendment_pairs(pairs, old_doc, new_doc, scope)

    assert all(not pair.verified for pair in result)
    assert all("unambiguously associated" in pair.reason for pair in result)


def test_amount_mentioned_elsewhere_in_quote_does_not_validate_wrong_target_pair():
    from app.evidence import verify_amendment_pairs
    from app.models import AmendmentScopeEvidence, ExtractedAmendmentPair

    old_doc = _document(["The second paragraph amount is Rs. 689 Crores."])
    # The extra amount is context only; it is not the amount corrected in the
    # first paragraph. A component-only check would wrongly accept this pair.
    quote = (
        "The amount mentioned in the first para as Rs. 350 Crores is corrected "
        "as Rs. 350 Lakh. A separate Rs. 689 Crores figure is cited."
    )
    new_doc = _document([quote])
    scope = AmendmentScopeEvidence(verified=True, effect="specific_changes_only", reason="verified")
    pair = ExtractedAmendmentPair(
        target="first paragraph amount", old_value=689, old_unit="Crores",
        new_value=350, new_unit="Lakh", quote=quote, page=1,
    )

    result = verify_amendment_pairs([pair], old_doc, new_doc, scope)

    assert result[0].verified is False
    assert "unambiguously associated" in result[0].reason


def test_ambiguous_multiple_correction_wording_remains_unverified():
    from app.evidence import verify_amendment_pairs
    from app.models import AmendmentScopeEvidence, ExtractedAmendmentPair

    old_doc = _document(["The first paragraph amount is Rs. 350 Crores. The second is Rs. 689 Crores."])
    # Synthetic ambiguous wording: there is no "respectively" to map the two
    # old amounts to the two corrected amounts.
    quote = "Amounts 350 Crores and 689 Crores were corrected to 350 Lakh and 689 Lakh."
    new_doc = _document([quote])
    scope = AmendmentScopeEvidence(verified=True, effect="specific_changes_only", reason="verified")
    pair = ExtractedAmendmentPair(
        target="first paragraph amount", old_value=350, old_unit="Crores",
        new_value=350, new_unit="Lakh", quote=quote, page=1,
    )

    result = verify_amendment_pairs([pair], old_doc, new_doc, scope)

    assert result[0].verified is False
    assert "unambiguously associated" in result[0].reason


def test_verified_amendment_pair_suppresses_only_duplicate_generic_not_found_row():
    from app.models import RuleChange, VerifiedAmendmentPair

    quote = "The amount as Rs. 350 Crores is corrected as Rs. 350 Lakh."
    pair = VerifiedAmendmentPair(
        target="first paragraph amount", old_value=350, old_unit="Crores",
        new_value=350, new_unit="Lakh", quote=quote, page=1,
        verified=True, reason="verified",
    )
    duplicate = RuleChange(
        field="other", change_type="not_found_in_old_document", new_value="Rs. 350 Lakh",
        new_quote=quote, new_pages=[1], explanation="duplicate generic row",
    )
    unrelated = RuleChange(
        field="other", change_type="not_found_in_old_document", new_value="60%",
        new_quote="Minimum qualification is 60%.", new_pages=[2], explanation="unrelated",
    )
    unchanged = RuleChange(
        field="other", change_type="not_restated_in_new_document", old_value="legacy",
        old_quote="An unrelated old condition.", old_pages=[2], explanation="preserve",
    )
    result = exclude_verified_amendment_pair_duplicates([duplicate, unrelated, unchanged], [pair])
    assert result == [unrelated, unchanged]
