"""WO-PE-03B: the pure claim projection of a sealed v11 model (interface §2; interface v2 §7, projection list).

Author: Claude (Alpha build seat), 2026-10-25. Base ``0f2e703``. Fixtures: three sealed canary models
(``fixtures/pe03_canary``, sha256-pinned). On the base every test fails: ``inference.paper_evidence`` does not exist.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import pytest

from pe03_support import G50T, KA59, VC33, WORLDS, claims, model, packet
from inference.paper_evidence import claims as c
from inference.paper_evidence import paper_report, projection, sources_answers
from inference.paper_evidence.context import level_context

ROOT = Path(__file__).resolve().parents[1]
SOLVER_ID = re.compile(r"\b(O-L\d|PV-|EV-|LEVER-|G3-DISCOVERY|E-[0-9a-f]{6})")


def _strings(value, out):
    if isinstance(value, dict):
        for key, item in value.items():
            out.add(key)
            _strings(item, out)
    elif isinstance(value, list):
        for item in value:
            _strings(item, out)
    elif isinstance(value, str):
        out.add(value)
    return out


@pytest.mark.parametrize("world", WORLDS)
def test_01_two_projections_are_byte_identical(world):
    first = projection.evidence_bytes(projection.project(model(world)))
    assert first == projection.evidence_bytes(projection.project(model(world)))
    packet_ = json.loads(first)
    assert packet_["stamp"]["content_sha256"] == model(world)["content_sha256"]
    assert packet_["counts"]["claims"] == len(packet_["claims"]) > 0


@pytest.mark.parametrize("world", WORLDS)
def test_02_every_ref_and_source_id_resolves_in_the_model(world):
    """Refs and source ids name things in the sealed model, or in the model's own describer (pattern ids)."""
    from inference.framework import world_description

    present = _strings(model(world), set()) | _strings(world_description.describe_world(model(world)), set())
    for item in packet(world)["claims"]:
        assert all(ref in present for ref in item["refs"]), item["refs"]
        for key in ("product_id", "provenance_event", "pattern_id"):
            if item["source"].get(key):
                assert item["source"][key] in present, (key, item["source"])


@pytest.mark.parametrize("world", WORLDS)
def test_03_identities_are_full_sha256_and_recompute(world):
    for item in packet(world)["claims"]:
        proposition = {"schema": c.SCHEMA, "game_id": item["game_id"], "level": item["level"], "family": item["family"],
                       "kind": item["kind"], "subject": c.identity_subject(item["subject"]),
                       "predicate": item["predicate"], "object": item["object"], "scope": item["scope"]}
        assert item["claim_key"] == c.sha256(proposition) and len(item["claim_key"]) == 64
        assert item["assertion_id"] == c.sha256({"claim_key": item["claim_key"], "source": item["source"]})


@pytest.mark.parametrize("world", WORLDS)
def test_04_no_solver_id_enters_a_claim_key(world):
    """D16: the subject's identity is a handle plus geometry; solver ids stay in the trace (an unresolved subject,
    which can never join a key, is the only exception and says so)."""
    for item in packet(world)["claims"]:
        identity = json.dumps(c.identity_subject(item["subject"]))
        if not item["subject"]["handle"].startswith("unresolved:"):
            assert not SOLVER_ID.search(identity), identity
        assert "track_id" not in identity and "entity_id" not in identity


def test_05_one_proposition_proposed_and_certified_is_one_key_and_two_assertions():
    by_key = defaultdict(list)
    for item in packet(VC33)["claims"]:
        by_key[item["claim_key"]].append(item)
    shared = [items for items in by_key.values()
              if {i["executor"] for i in items} >= {"CONTROLLER", "SYSTEM"} and items[0]["predicate"] == "ACTION_EFFECT"]
    assert shared, "a controller-proposed action law the gate certified shares one claim_key"
    items = shared[0]
    assert len({i["assertion_id"] for i in items}) == len(items) >= 2


@pytest.mark.parametrize("world", WORLDS)
def test_06_a_gate_derived_product_never_yields_a_law_or_relation(world):
    assert not [i for i in packet(world)["claims"]
                if i["certification"] == "GATE_DERIVED" and i["kind"] == "PROPOSITION"]


def test_07_record_derived_relations_are_record_derived_and_system():
    relations = [i for i in claims(VC33, family="RELATION") if i["executor"] == "SYSTEM"]
    assert relations and {(i["certification"], i["admission"]) for i in relations} == {("RECORD_DERIVED", "NOT_APPLICABLE")}


def test_08_refused_answers_stay_in_the_denominator():
    refused = claims(KA59, executor="DUCK", admission="REFUSED")
    assert refused and all(i["kind"] == "PROPOSITION" and i["field_source"] for i in refused)
    assert claims(VC33, executor="DUCK", admission="ADMITTED") and claims(VC33, executor="DUCK", admission="REFUSED")


def _duck_row(world=VC33):
    m = model(world)
    level = next(level for level in m["levels"] if any(
        r.get("executor") == "DUCK" and r.get("disposition") == "ADMITTED" and r.get("operation") == "ANSWER"
        and r.get("level") == level["level"] for r in m["provenance"]["rows"]))
    ctx = level_context(m, level)
    row = next(r for r in ctx.answer_rows if r["executor"] == "DUCK" and r["disposition"] == "ADMITTED")
    return ctx, json.loads(json.dumps(row))


def test_09_a_controller_filled_field_is_never_duck_s():
    ctx, row = _duck_row()
    field = next(f for f in sorted(row["field_sources"]) if f in ("mechanism_explanation", "falsifier", "observed_period")
                 and row["submitted"].get(f))
    row["field_sources"][field] = "CONTROLLER_FILLED"
    row.setdefault("effective", dict(row["submitted"]))
    ctx.answer_rows = [row]
    found = [i for i in sources_answers.answer_claims(ctx) if i["source"]["field"] == field]
    assert found and {(i["executor"], i["field_source"]) for i in found} == {("CONTROLLER", "CONTROLLER_FILLED")}


def test_10_an_unparseable_refusal_is_one_open_gap_audit():
    ctx, row = _duck_row()
    row.update({"disposition": "REFUSED", "submitted": "not a payload", "reason": {"code": "GATE_CONTRACT"}})
    ctx.answer_rows = [row]
    (only,) = list(sources_answers.answer_claims(ctx))
    assert (only["family"], only["kind"], only["predicate"], only["status"], only["admission"]) == (
        "GAP", "AUDIT", "UNPARSEABLE_ANSWER", "OPEN", "REFUSED")


def test_11_models_that_cannot_be_formal_are_refused_with_a_typed_reason():
    v4 = json.loads((ROOT / "tests/fixtures/world_model_v4_frozen.json").read_text())
    with pytest.raises(projection.ProjectionRefused) as refused:
        projection.project(v4)
    assert refused.value.code == "PRODUCT_CONTENT_UNAVAILABLE"
    with pytest.raises(projection.ProjectionRefused) as refused:
        projection.project({**model(KA59), "schema": "virelai-world-model-v10"})
    assert refused.value.code in ("SCHEMA_NOT_V11",)
    tampered = model(KA59)
    tampered["levels"][0]["gaps"] = tampered["levels"][0]["gaps"][1:]
    with pytest.raises(projection.ProjectionRefused) as refused:
        projection.project(tampered)
    assert refused.value.code == "MODEL_INVALID"


def test_12_an_open_journal_is_measured_output_never_refused():
    stamp = packet(G50T)["stamp"]
    assert (stamp["integrity"], stamp["completeness"], stamp["provenance_sealed"]) == ("OPEN", "INCOMPLETE", False)
    assert packet(G50T)["claims"]
    assert "not sealed and complete" in paper_report.render(packet(G50T))


@pytest.mark.parametrize("world", WORLDS)
def test_13_scoped_nulls_are_conditions_never_inert_roles(world):
    nulls = claims(world, predicate="NO_OBSERVED_EFFECT")
    assert all(i["family"] == "CONDITION" for i in nulls)
    assert not [i for i in packet(world)["claims"] if i["object"] == "INERT"]
    certified = sum(len(level["certified"]["scoped_nulls"]) for level in model(world)["levels"])
    assert len([i for i in nulls if i["executor"] == "CONTROLLER" and i["admission"] == "NOT_APPLICABLE"]) == certified


def test_14_a_pattern_with_two_explanation_statuses_is_two_assertions_of_one_proposition():
    by_pattern = defaultdict(list)
    for item in claims(VC33, family="TRANSFORMATION"):
        by_pattern[item["source"]["pattern_id"]].append(item)
    mixed = [items for items in by_pattern.values() if len(items) > 1]
    assert mixed
    for items in mixed:
        assert len({i["claim_key"] for i in items}) == 1 and len({i["status"] for i in items}) == len(items)


def test_15_a_composite_lever_is_the_union_of_its_members():
    coupled = claims(VC33, predicate="COUPLED_WITH")
    assert coupled
    for item in coupled:
        assert "+" in item["subject"]["handle"] and item["subject"]["geometry"]["frame"] == "ENTRY"
        assert len(item["subject"]["trace"]["members"]) == 2


def test_16_every_level_of_every_world_is_stamped_with_its_entry_frame():
    for world in WORLDS:
        frames = packet(world)["stamp"]["entry_frames"]
        assert frames == {str(l["level"]): l["entry"]["board_sha256"] for l in model(world)["levels"]}


def test_17_entry_geometry_carries_the_entry_board_hash_and_later_objects_do_not():
    for item in claims(VC33, family="ROLE"):
        geometry = item["subject"]["geometry"]
        if geometry and geometry["frame"] == "ENTRY":
            assert geometry["board_sha256"] == packet(VC33)["stamp"]["entry_frames"][str(item["level"])]
        elif geometry and geometry["frame"].startswith("T"):
            assert geometry["board_sha256"] is None


def test_18_no_runtime_module_imports_the_paper_evidence_package():
    for folder in ("inference/agent", "inference/framework", "inference/utils", "inference/tools"):
        for path in (ROOT / folder).rglob("*.py"):
            assert "paper_evidence" not in path.read_text(), path


def test_19_the_report_has_the_six_sections_for_every_level():
    text = paper_report.render(packet(VC33))
    for level in (1, 2, 3):
        block = text.split(f"## Level {level}")[1].split("## Level")[0]
        for name in ("Self", "Time", "Response", "Players", "Model", "Value", "What the model does not know"):
            assert f"### {name}" in block
    assert "[duck, refused]" in text and "[certified]" in text
