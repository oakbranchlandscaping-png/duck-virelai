"""WO-PE-03D: the five-category grader, the verdict sheet, the tables and the exits (interface §4; v2 §7 grader list).

Author: Claude (Alpha build seat), 2026-10-25. Base ``0f2e703``. The key is synthetic (build-seat authored, code tests
only, refused for formal grading). The verdicts below are test inputs, not anyone's judgment of the world. On the base
every test fails: ``inference.paper_evidence`` does not exist.
"""
from __future__ import annotations

import json

import pytest

from pe03_support import (LEVEL1, LEVER_A, LEVER_B, VC33, G50T, item, packet, synthetic_key)
from inference.paper_evidence import claims as c
from inference.paper_evidence import grader, keys, mapping


def _confirmed(packet_, key):
    sheet = mapping.propose(packet_, key)
    for row in sheet["rows"]:
        if row["confirmed"] is None:
            row["confirmed"] = []  # the human confirms: no solver subject is this object
    return sheet


def _setup(items=None):
    key = keys.validate(synthetic_key(items), formal=False)
    pk = packet(VC33)
    return pk, key, _confirmed(pk, key)


def _by_id(pk):
    return {cl["assertion_id"]: cl for cl in pk["claims"]}


def _ruling(report, pk, key, pick):
    """Test verdicts: UNVERIFIABLE for every owed claim, except where ``pick`` names another."""
    sheet = grader.verdict_sheet(pk, key, report)
    claims = _by_id(pk)
    for row in sheet["claims"]:
        row["verdict"], row["satisfies"] = pick(claims[row["assertion_id"]]) or ("UNVERIFIABLE", [])
    return sheet


def test_01_an_unconfirmed_mapping_leaves_the_grade_incomplete():
    pk, key, _ = _setup()
    report = grader.grade(pk, key, mapping.propose(pk, key))
    assert report["unconfirmed_mappings"] == 1 and report["complete"] is False


def test_02_exact_joins_and_accepted_alternatives_are_correct_and_satisfy_their_items():
    pk, key, sheet = _setup()
    report = grader.grade(pk, key, sheet)
    claims = _by_id(pk)
    joined = [r for r in report["claims"] if r["basis"] == "JOINED"]
    assert {(claims[r["assertion_id"]]["predicate"], claims[r["assertion_id"]]["object"]) for r in joined} >= {
        ("ROLE_IS", "LEVER"), ("ROLE_IS", "COUNTER"), ("COUNTER_REWRITE", "7->4"), ("COUNTER_TRIGGER", "EVERY_TRANSITION"),
        ("CONTROL_MODE", "POINTER")}
    assert all(r["grade"] == "CORRECT" and r["satisfies"] for r in joined)
    trigger = next(i for i in key["items"] if i["predicate"] == "COUNTER_TRIGGER")
    assert next(o for o in report["items"] if o["key_id"] == trigger["key_id"])["outcome"] == "SATISFIED"


def test_03_a_single_valued_contradiction_is_wrong_without_a_verdict():
    pk, key, sheet = _setup([item(LEVER_B, "ROLE", "ROLE_IS", "COUNTER")])
    report = grader.grade(pk, key, sheet)
    claims = _by_id(pk)
    wrong = [r for r in report["claims"] if r["grade"] == "WRONG"]
    assert wrong and all(r["basis"] == "CONTRADICTS_KEY" and claims[r["assertion_id"]]["object"] == "LEVER" for r in wrong)
    assert report["items"][0]["outcome"] == "MISSED"


def test_04_outside_the_key_s_coverage_a_proposition_is_unverifiable_by_rule():
    pk, key, sheet = _setup()
    report = grader.grade(pk, key, sheet)
    silent = [r for r in report["claims"] if r["basis"] == "KEY_SILENT"]
    assert silent and {r["grade"] for r in silent} == {"UNVERIFIABLE"}
    claims = _by_id(pk)
    assert all(claims[r["assertion_id"]]["kind"] == "PROPOSITION" for r in silent)


def test_05_every_audit_is_graded_as_an_audit_and_never_satisfies_an_item():
    pk, key, sheet = _setup()
    report = grader.grade(pk, key, sheet)
    claims = _by_id(pk)
    audits = [r for r in report["claims"] if claims[r["assertion_id"]]["kind"] == "AUDIT"]
    assert audits and {(r["grade"], r["basis"]) for r in audits} == {("CORRECT", "MODEL_SUPPORTED")}
    assert not any(r["satisfies"] for r in audits)


def test_06_in_coverage_claims_need_a_verdict_and_the_sheet_lists_exactly_them():
    pk, key, sheet = _setup()
    report = grader.grade(pk, key, sheet)
    owed = [r["assertion_id"] for r in report["claims"] if r["grade"] is None]
    assert owed and report["owed_verdicts"] == len(owed) and report["complete"] is False
    worksheet = grader.verdict_sheet(pk, key, report)
    assert [row["assertion_id"] for row in worksheet["claims"]] == owed
    assert all(row["verdict"] is None and row["key_items_in_reach"] for row in worksheet["claims"])


def test_07_human_verdicts_complete_the_grade_with_all_five_categories():
    pk, key, sheet = _setup()
    first = grader.grade(pk, key, sheet)
    locality = next(i for i in key["items"] if i["predicate"] == "EFFECT_LOCALITY")

    def pick(claim):
        if claim["predicate"] == "EFFECT_LOCALITY" and claim["subject"]["handle"] == "c9@32,60":
            return "WRONG", []
        if claim["predicate"] == "MECHANISM" and claim["subject"]["handle"] == "c9@24,60":
            return "INVENTED", []
        return None

    verdicts = _ruling(first, pk, key, pick)
    report = grader.grade(pk, key, sheet, verdicts)
    assert report["complete"] is True and report["owed_verdicts"] == 0
    assert set(report["tables"]["propositions"]) == {"CORRECT", "WRONG", "UNVERIFIABLE", "INVENTED"}
    outcomes = {o["key_id"]: o["outcome"] for o in report["items"]}
    assert outcomes[locality["key_id"]] == "MISSED"
    assert set(outcomes.values()) == {"SATISFIED", "MISSED", "NOT_COVERED"}
    missed_optional = [o for o in report["items"] if o["outcome"] == "MISSED" and not o["required"]]
    assert not missed_optional  # MISSED is only ever a required item


def test_08_a_human_may_rule_a_claim_correct_and_name_the_item_it_satisfies():
    pk, key, sheet = _setup()
    win = next(i for i in key["items"] if i["predicate"] == "WIN_CONDITION")
    first = grader.grade(pk, key, sheet)
    verdicts = _ruling(first, pk, key, lambda cl: ("CORRECT", [win["key_id"]]) if cl["predicate"] == "LEVEL_CLEARED_BY" else None)
    report = grader.grade(pk, key, sheet, verdicts)
    assert next(o for o in report["items"] if o["key_id"] == win["key_id"])["outcome"] == "SATISFIED"


def test_09_a_gap_is_never_invented():
    pk, key, sheet = _setup()
    gap = next(cl for cl in pk["claims"] if cl["family"] == "GAP")
    first = grader.grade(pk, key, sheet)
    verdicts = _ruling(first, pk, key, lambda cl: None)
    verdicts["claims"].append({"assertion_id": gap["assertion_id"], "verdict": "INVENTED", "satisfies": []})
    report = grader.grade(pk, key, sheet, verdicts)
    assert next(r for r in report["claims"] if r["assertion_id"] == gap["assertion_id"])["grade"] != "INVENTED"


def test_10_tables_cover_every_dimension_and_keep_propositions_and_audits_apart():
    pk, key, sheet = _setup()
    report = grader.grade(pk, key, sheet)
    rows = report["tables"]["by_level_family_kind_executor_admission_certification_grade"]
    assert sum(row[-1] for row in rows) == len(pk["claims"])
    assert {row[2] for row in rows} == {"PROPOSITION", "AUDIT"}
    assert sum(report["tables"]["propositions"].values()) == pk["counts"]["propositions"]
    assert sum(report["tables"]["proposition_bases"].values()) == pk["counts"]["propositions"]
    assert report["tables"]["proposition_bases"]["KEY_SILENT"] > 0
    assert sum(report["tables"]["audits"].values()) == pk["counts"]["audits"]
    assert report["tables"]["provenance_sealed"] is True


def test_11_an_excluded_level_grades_nothing_and_its_items_say_why():
    pk = packet(VC33)
    raw = synthetic_key([item(LEVER_A, "ROLE", "ROLE_IS", "LEVER"), item(LEVER_A, "ROLE", "ROLE_IS", "LEVER", level=2)],
                        levels=(1, 2))
    raw["construction"]["entry_frames"]["2"] = "e" * 64
    key = keys.validate(raw, formal=False)
    report = grader.grade(pk, key, _confirmed(pk, key))
    assert report["excluded_levels"] == {"2": "ENTRY_FRAME_MISMATCH"}
    assert [o["outcome"] for o in report["items"]] == ["SATISFIED", "EXCLUDED"]
    claims = _by_id(pk)
    assert not [r for r in report["claims"] if claims[r["assertion_id"]]["level"] == 2]


def test_12_the_grade_is_deterministic():
    pk, key, sheet = _setup()
    first = grader.verdict_sheet(pk, key, grader.grade(pk, key, sheet))
    verdicts = {**first, "claims": [{**row, "verdict": "UNVERIFIABLE"} for row in first["claims"]]}
    one = c.sha256(grader.grade(pk, key, sheet, verdicts))
    assert one == c.sha256(grader.grade(packet(VC33), key, _confirmed(packet(VC33), key), verdicts))


def test_13_sheets_bound_to_another_packet_or_key_are_refused():
    pk, key, sheet = _setup()
    with pytest.raises(ValueError):
        grader.grade(pk, key, {**sheet, "packet": "0" * 64})
    with pytest.raises(ValueError):
        grader.grade(pk, key, sheet, {"packet": pk["stamp"]["content_sha256"], "key": "0" * 64, "claims": []})


def test_14_an_open_journal_world_is_graded_and_its_tables_say_so():
    pk = packet(G50T)
    raw = synthetic_key([item(LEVEL1, "CONDITION", "WIN_CONDITION", "synthetic")])
    raw.update(game_id=pk["stamp"]["game_id"])
    raw["construction"]["entry_frames"] = {"1": pk["stamp"]["entry_frames"]["1"]}
    key = keys.validate(raw, formal=False)
    report = grader.grade(pk, key, _confirmed(pk, key))
    assert report["tables"]["provenance_sealed"] is False and report["claims"]


def test_15_the_cli_exits_3_then_4_then_0_and_writes_the_graded_report(tmp_path):
    import tools.paper_grade as tool
    from inference.paper_evidence import projection

    evidence = tmp_path / "paper_evidence.json"
    evidence.write_bytes(projection.evidence_bytes(packet(VC33)))
    key_path = tmp_path / "key.json"
    key_path.write_text(json.dumps(synthetic_key()))
    out = tmp_path / "grade"
    assert tool.main([str(evidence), str(key_path), "--dir", str(out)]) == 2  # a synthetic key is refused formally
    args = [str(evidence), str(key_path), "--dir", str(out), "--synthetic"]
    assert tool.main(args) == 3
    sheet = json.loads((out / "mapping_sheet.json").read_text())
    for row in sheet["rows"]:
        row["confirmed"] = row["confirmed"] if row["confirmed"] is not None else []
    (out / "mapping_sheet.json").write_text(json.dumps(sheet))
    assert tool.main(args) == 4
    worksheet = json.loads((out / "verdict_sheet.json").read_text())
    for row in worksheet["claims"]:
        row["verdict"] = "UNVERIFIABLE"
    (out / "verdict_sheet.json").write_text(json.dumps(worksheet))
    assert tool.main(args) == 0
    report = json.loads((out / "grade_report.json").read_text())
    assert report["complete"] is True
    assert "**CORRECT**" in (out / "paper_report.md").read_text()
