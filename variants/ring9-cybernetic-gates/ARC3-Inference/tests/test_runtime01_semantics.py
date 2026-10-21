"""WO-RUNTIME-01 revision 3: workflow settlement is kept apart from knowledge certification.

Author: Claude (Alpha build seat), 2026-10-21. Base ``73f13d1``, on the parked revision-2 tree. Sol's build directive
for revision 3, §7: a G4 product with a closed chapter advances the ladder (``SETTLED_WITH_GAPS``) without making the
gate, or the closed subject, look certified; its knowledge fields hold supported facts only; downstream gates route
over observed geometry and carry it as unresolved; every closure keeps its cause, epistemic class and revisit policy.

Fixtures: the vc33 carry-v7 record (levers E0004 and E0005), driven as live, and the ft09 v1 record at G4-B
(``test_g4b_relations.start_g4b``). On revision 2 the closed lever's anatomy stayed among the anatomies, G4.2 read
``phase1_status`` ``COMPLETE``, the census counted ``PARTIAL`` as certified and a closure kept no class.
"""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

import pytest

import dossier_fixtures as fx
from runtime01_support import VC33, controller_answers, drive_to, scheduling_scenarios
from inference.framework.record_replay import load_record, replay

G41, G42, G4B, G4C = "G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"
EFFECTS = "Q:L1:G4-REACTIONS:{}:EFFECTS"
ORBIT = "Q:L1:G4.2-LEVER-ORBITS:{}:ORBIT"
FIXTURES = Path(__file__).parent / "fixtures"


def _close(machine, question, reason="CLOCK_BUDGET_SPENT", cause="TURN_CLOCK"):
    from inference.framework import gate_closure

    return gate_closure.close_question(machine, question, reason, ["E-OUTCOME-1"], cause)


def _g41_partial():
    """G4.1 with E0004's chapter closed (the turn clock spent its budget) and E0005 answered by the controller."""
    machine = drive_to(G41)
    _close(machine, EFFECTS.format("E0004"))
    controller_answers(machine, G41)
    return machine


def _at(steps):
    machine = replay(load_record(VC33), max_steps=steps, measure=False).machine
    machine.annotations.oriented = True
    return machine


def _payload(machine, gate):
    return machine.target_journal.active_product(gate).payload


def _wm():
    from inference.framework import world_model_v2 as wm

    return wm


def _refused(model):
    wm = _wm()
    model["content_sha256"] = wm.content_sha256(model)
    with pytest.raises(wm.WorldModelV2Error):
        wm.read_world_model(model)


# ---- 1-4 · settled with gaps, never certified ----------------------------------------------------------------------

def test_01_one_answered_and_one_closed_chapter_is_settled_with_gaps_and_partial():
    payload = _payload(_g41_partial(), G41)
    assert (payload["settlement_status"], payload["knowledge_status"], payload["status"]) == (
        "SETTLED_WITH_GAPS", "PARTIAL", "PARTIAL")
    assert (payload["answered_entities"], payload["closed_entities"], payload["pending_entities"]) == (
        ["E0005"], ["E0004"], [])
    assert [row["entity_id"] for row in payload["unresolved_lever_chapters"]] == ["E0004"]


def test_02_a_partial_gate_is_absent_from_the_certified_gates():
    from inference.framework import library_agenda

    machine = _g41_partial()
    model = fx.compiled(machine, persist_reason="RUN_END")
    rows = {row["gate_id"]: row for row in fx.open_level(model)["certified"]["gates"]}
    assert rows[G41]["disposition"] == "PARTIAL"
    assert rows[G41]["subjects"] == {"answered": 1, "closed": 1, "pending": 0}
    assert G41 not in {gate for gate, row in rows.items() if row["disposition"] == "CERTIFIED"}
    agreement = library_agenda.census_agreement(library_agenda.gate_agenda(machine), model)
    assert "certified_gates" not in agreement and "partial_gates" not in agreement  # agenda and census agree


def test_03_and_04_the_answered_subject_stays_certified_and_the_closed_one_closed():
    model = fx.compiled(_g41_partial(), persist_reason="RUN_END")
    answered, closed = fx.chapter(model, "E0005", "anatomy"), fx.chapter(model, "E0004", "anatomy")
    assert (answered["status"], answered["basis"], answered["source"]) == ("COMPLETE", "PRODUCT_CERTIFIED", "PRODUCT_CONTENT")
    assert (closed["status"], closed["basis"]) == ("CLOSED_UNRESOLVED", "CHAPTER_CLOSED_UNRESOLVED")
    (item,) = [row for row in closed["open"] if row["kind"] == "CHAPTER_CLOSED"]
    assert (item["cause"], item["closure_class"], item["revisit_policy"]) == (
        "TURN_CLOCK", "RESOURCE_LIMIT", "NEW_LIFE_OR_MATERIAL_EVIDENCE")


def test_05_a_g42_phase_with_a_closed_orbit_chapter_is_never_complete():
    machine = _at(24)
    _close(machine, ORBIT.format("E0005"))
    payload = _payload(machine, G42)
    assert payload["phase1_status"] == "SETTLED_WITH_GAPS" and payload["settlement_status"] == "SETTLED_WITH_GAPS"
    assert machine.gate_id == G4B  # the ladder still advances


# ---- 6-9 · supported facts only; downstream carries the gap ----------------------------------------------------------

def test_06_a_closed_g41_anatomy_is_never_promoted_from_g3_geometry():
    machine = _g41_partial()
    payload = _payload(machine, G41)
    assert [item["entity_id"] for item in payload["anatomies"]] == ["E0005"]
    (geometry,) = payload["observed_geometry"]
    assert (geometry["entity_id"], geometry["geometry_source"], geometry["anatomy_status"]) == (
        "E0004", "GATE_OBSERVED_GEOMETRY", "ANATOMY_UNRESOLVED")
    assert payload["geometry_sources"] == {"E0004": "GATE_OBSERVED_GEOMETRY", "E0005": "ACCEPTED_ANSWER"}
    assert "E0004" not in machine._adapters[G41]._answers  # the controller can rebuild the region; it never answers it
    model = fx.compiled(machine, persist_reason="RUN_END")
    assert fx.chapter(model, "E0004", "anatomy")["status"] == "CLOSED_UNRESOLVED"


def test_07_downstream_routing_uses_observed_geometry_and_keeps_its_unresolved_source():
    machine = _g41_partial()
    study = machine._adapters[G42]
    study._seed()
    assert study._ordered_entities == ("E0004", "E0005")  # G4.2 may study the lever whose anatomy is unresolved
    for entity in ("E0004", "E0005"):
        _close(machine, ORBIT.format(entity))
    orbits = _payload(machine, G42)
    assert orbits["anatomy_status"] == {"E0004": "ANATOMY_UNRESOLVED"}  # carried wherever it is studied
    assert machine.gate_id == G4B
    relations = machine._adapters[G4B]
    assert relations._levers() == ("E0004", "E0005")  # the observed geometry routes G4-B's regions
    relations.close_unresolved("DUCK_BUDGET_SPENT")
    product = _payload(machine, G4B)
    assert product["region_sources"] == {"E0004": "GATE_OBSERVED_GEOMETRY", "E0005": "ACCEPTED_ANSWER"}


def test_08_g4b_never_invents_a_missing_orbit():
    machine = _at(24)
    _close(machine, ORBIT.format("E0005"))
    relations = machine._adapters[G4B]
    relations._levers()  # seeds the regions
    regions = {region.entity_id: region for region in relations._regions}
    assert regions["E0004"].steps and regions["E0004"].lever_class is not None
    assert regions["E0005"].steps == () and regions["E0005"].lever_class is None  # nothing inferred
    relations.close_unresolved("DUCK_BUDGET_SPENT")
    assert _payload(machine, G4B)["orbit_sources"] == {"E0004": "ACCEPTED_ANSWER", "E0005": "UNRESOLVED_PLACEHOLDER"}


def test_09_g4c_certifies_no_law_whose_prerequisite_subject_is_unresolved():
    from test_g4b_relations import _take, start_g4b
    from test_g4c_law import _described, _law

    machine, world = start_g4b()
    _described(machine, world)
    study = machine._adapters[G42]
    # scripted state: E0055's G4.2 chapter closed unresolved (this record answered every chapter)
    study.__dict__.setdefault("_closed_chapters", {})["E0055"] = {"entity_id": "E0055"}
    _law(machine, "E0055")
    _take(machine, world)
    law = machine._adapters[G4C]
    assert law._tests[-1].status == "SUPPORTED" and law._certified is None  # graded, but certifies nothing
    assert machine.gate_id == G4C and machine.target_journal.active_product(G4C) is None
    _law(machine, "E0056", relations=[0])  # relation 0 names E0053 and E0054; E0056 is supported
    _take(machine, world)
    assert law._certified is not None and _payload(machine, G4C)["status"] == "COMPLETE"


def _couple(world, acted: str, also: str) -> None:
    """The offline world, scripted: pressing ``acted`` also steps ``also``'s tile in the same transition."""
    from ft09_world import BAR_ROW
    from test_g4b_relations import TILES, _click

    plain = world.changes

    def changes(action):
        if (int(action["row"]), int(action["col"])) != TILES[acted]:
            return plain(action)
        return [cell for cell in plain(_click(also)) if cell[0] != BAR_ROW] + plain(action)

    world.changes = changes


def test_09b_g4c_certifies_no_law_an_unresolved_lever_took_part_in():
    """r3.1 (Sol): a lever whose region the graded transition changed is a prerequisite, named or not."""
    from types import SimpleNamespace

    from test_g4b_relations import _take, start_g4b
    from test_g4c_law import _described, _law
    from inference.framework import chapter_semantics as S

    machine, world = start_g4b()
    _described(machine, world)
    # 1. lever B (E0055) closed: its G4.2 chapter, scripted as in test 9
    machine._adapters[G42].__dict__.setdefault("_closed_chapters", {})["E0055"] = {"entity_id": "E0055"}
    # the contract, whatever the prediction named: an observed participant is a prerequisite
    graded = SimpleNamespace(acted_lever="E0056", named=["E0056"], from_relations=[],
                             observed={"E0056": "STEPS", "E0055": "CHANGES", "E0053": "UNCHANGED"})
    assert not S.prerequisites_present(machine, graded)
    graded.observed["E0055"] = "UNCHANGED"
    assert S.prerequisites_present(machine, graded)
    # 2-3. a law over lever A (E0056) on a transition that changes both A's and B's regions
    plain = world.changes
    _couple(world, "E0056", "E0055")
    _law(machine, "E0056", {"E0056": "STEPS", "E0055": "STEPS"})
    _take(machine, world)
    law = machine._adapters[G4C]
    test = law._tests[-1]
    # 4. the observation is SUPPORTED, and B took part in it
    assert test.status == "SUPPORTED" and test.observed["E0055"] != "UNCHANGED"
    # 5. no law is certified: B is an unresolved observed participant
    assert law._certified is None and machine.target_journal.active_product(G4C) is None
    assert machine.gate_id == G4C
    # 6. once only A's supported region changes, the law certifies
    world.changes = plain
    _law(machine, "E0056")
    _take(machine, world)
    assert law._tests[-1].observed["E0055"] == "UNCHANGED"
    assert law._certified is not None and _payload(machine, G4C)["status"] == "COMPLETE"


# ---- 10-11 · forgeries ---------------------------------------------------------------------------------------------

def test_10_a_forged_whole_gate_certification_is_refused_after_resealing():
    model = fx.compiled(_g41_partial(), persist_reason="RUN_END")
    _wm().read_world_model(model)
    forged = copy.deepcopy(model)
    for row in fx.open_level(forged)["certified"]["gates"]:
        if row["gate_id"] == G41:
            for key in ("settlement_status", "knowledge_status", "subjects"):
                row.pop(key)
            row["disposition"] = "CERTIFIED"
    _refused(forged)


def test_11_a_forged_completed_subject_is_refused_after_resealing_every_hash():
    from inference.framework import product_content as pc

    model = fx.compiled(_g41_partial(), persist_reason="RUN_END")
    level = fx.open_level(model)
    pid = next(pid for pid, entry in level["product_content"].items() if entry["gate_id"] == G41)
    entry = level["product_content"][pid]
    forged_payload = copy.deepcopy(entry["payload"])
    forged_payload["answered_entities"] = ["E0004", "E0005"]  # E0004 claimed answered, with no answer
    forged_payload["closed_entities"], forged_payload["unresolved_lever_chapters"] = [], []
    forged_payload["knowledge_status"] = forged_payload["status"] = "PARTIAL"
    entry["payload"] = forged_payload
    entry["digest"] = pc._digested({key: entry[key] for key in ("gate_id", "product_type", "revision", "dependencies")},
                                   forged_payload)
    level["receipts"]["products"][pid]["payload_sha256"] = pc.legacy_payload_sha256(forged_payload)
    _refused(model)
    chapter = copy.deepcopy(fx.compiled(_g41_partial(), persist_reason="RUN_END"))
    fx.chapter(chapter, "E0004", "anatomy").update(status="COMPLETE", basis="PRODUCT_CERTIFIED")
    _refused(chapter)


# ---- 12-13 · why a chapter closed ----------------------------------------------------------------------------------

def test_12_every_closure_reason_maps_to_exactly_one_closure_class():
    from inference.agent import turn_recovery
    from inference.framework import audit_v3_rules, chapter_semantics as S

    causes = {reason for reason, kind in turn_recovery.REASON_CLASS.items() if kind is not None or reason == "DECLINED"}
    causes |= {"HARD_BUDGET_SPENT", "CLOCK_BUDGET_SPENT", "DUCK_BUDGET_SPENT", "UPSTREAM_UNRESOLVED",
               "NO_LEGAL_CONTROLLER_MOVE", "CONTROLLER_STALLED", "DECLINED"}
    assert causes <= audit_v3_rules.REASON_CODES | {"DECLINED"}
    for cause in causes:
        typed = S.closure_type(cause)
        assert typed["closure_class"] in S.CLASSES and typed["revisit_policy"] == S.REVISIT[typed["closure_class"]]
    assert set(S.CAUSE_CLASS.values()) == set(S.CLASSES)  # every class is reachable, each cause has one
    assert {S.closure_type(c)["closure_class"] for c in ("TURN_CLOCK", "MODEL_TIMEOUT", "MODEL_REQUEST_FAILED")} == {
        "RESOURCE_LIMIT"}
    assert {S.closure_type(c)["closure_class"] for c in ("MALFORMED_ACTION", "NO_TOOL_CALL", "PYTHON_ERROR")} == {
        "INTERFACE_FAILURE"}
    assert S.closure_type("DECLINED")["revisit_policy"] == "NEW_LIFE"
    with pytest.raises(ValueError):
        S.closure_type("SOMETHING_UNTYPED")


def test_13_a_resource_failure_and_an_evidence_failure_render_differently():
    from inference.framework import chapter_semantics as S
    from inference.framework.world_description import dossier_digest_lines

    rows = {cause: {"question_id": "q", "reason": "r", **S.closure_type(cause)}
            for cause in ("TURN_CLOCK", "EVIDENCE_INCONCLUSIVE")}
    resource, evidence = S.closure_text(rows["TURN_CLOCK"]), S.closure_text(rows["EVIDENCE_INCONCLUSIVE"])
    assert resource != evidence and "nothing is shown about the mechanics" in resource
    assert "nothing is shown" not in evidence and "inconclusive" in evidence
    model = fx.compiled(_g41_partial(), persist_reason="RUN_END")
    line = dossier_digest_lines(fx.open_level(model), "E0004")[-1]
    assert "anatomy X CHAPTER_CLOSED_UNRESOLVED/RESOURCE_LIMIT" in line
    from inference.framework.card_builder import world_model_digest

    digest = [text for text in world_model_digest(_g41_partial()) if text.startswith(f"[{G41}]")]
    assert digest[0].startswith(f"[{G41}] settled with gaps (PARTIAL)") and "RESOURCE_LIMIT" in digest[0]


# ---- 14-17 · what must not change ----------------------------------------------------------------------------------

def test_14_a_product_with_no_closure_is_the_base_payload_unchanged():
    from inference.framework import chapter_closure

    machine = drive_to(G41)
    reactions = machine._adapters[G41]
    controller_answers(machine, G41)
    payload = _payload(machine, G41)
    assert set(payload) == {"scope", "lever_entities", "anatomies", "answers", "open_questions"}  # the base keys only
    assert chapter_closure.with_rows(reactions, payload) is payload
    orbits = _at(24)._adapters[G42]
    assert chapter_closure.with_rows(orbits, {"x": 1}) == {"x": 1}


def test_15_revision_2_scheduling_and_action_traces_are_byte_identical():
    expected = json.loads((FIXTURES / "runtime01_r2_scheduling_trace.json").read_text())
    assert json.loads(json.dumps(scheduling_scenarios(), sort_keys=True)) == expected


def test_16_the_frozen_v10_model_still_reads_unchanged():
    raw = gzip.decompress((FIXTURES / "world_model_v10_frozen.json.gz").read_bytes())
    model = json.loads(raw)
    _wm().validate_v10(model)
    assert _wm().read_world_model(model)["schema"] == "virelai-world-model-v10"
    assert _wm()._canonical(model) == raw
