import json
from pathlib import Path


def test_obc_policy_snapshot_is_not_mislabelled_as_direct_amendment_pair():
    fixture_path = (
        Path(__file__).parents[2]
        / "research"
        / "candidate_pairs"
        / "obc_overseas_2024_snapshot_vs_2026_revised.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    assert fixture["classification"] == (
        "official_policy_snapshot_comparison_not_verified_direct_parent_amendment_pair"
    )
    assert fixture["older_source"]["document"] == "G.O.(Rt) No.10/2024/BCDD"
    assert fixture["newer_source"]["document"] == "G.O.(Rt) No.6/2026/BCDD"
    assert "2014 eligibility conditions" in " ".join(fixture["not_yet_safe_to_infer"])

    ranking = next(
        item for item in fixture["safe_comparison_findings"]
        if item["field"] == "university_ranking_eligibility_ceiling"
    )
    assert "600" in ranking["older_snapshot"]
    assert "300" in ranking["newer_rule"]
    assert "not_a_direct_parent_clause_diff" in ranking["confidence"]

    # The reusable fixture must contain only policy text, never beneficiary rows.
    assert "beneficiaries" not in fixture
    assert all("name" not in key.lower() for key in fixture.keys())


def test_obc_candidate_preserves_the_batch_cutoff_vs_scheme_ceiling_distinction():
    fixture_path = (
        Path(__file__).parents[2]
        / "research"
        / "candidate_pairs"
        / "obc_overseas_2024_snapshot_vs_2026_revised.json"
    )
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))

    older = fixture["older_source"]["relevant_quotes"][0]["text"]
    newer = fixture["newer_source"]["relevant_quotes"][1]["text"]
    ranking = next(
        item for item in fixture["safe_comparison_findings"]
        if item["field"] == "university_ranking_eligibility_ceiling"
    )

    assert "up to rank 600" in older
    assert "ranked within the top 300" in newer
    assert "for that specific batch" in ranking["important_caveat"]
    assert fixture["classification"].endswith("not_verified_direct_parent_amendment_pair")
