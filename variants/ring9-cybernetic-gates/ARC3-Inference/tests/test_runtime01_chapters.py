"""WO-RUNTIME-01 revision 2: one G4.1 or G4.2 lever chapter closes CLOSED_UNRESOLVED; the others go on.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Director rulings 1 and 2 of revision 2: a per-lever
unresolved state for G4.1 and G4.2 (close only the selected chapter, store its row, never offer it again, keep
studying every other lever, settle with a partial product the downstream gates read, render the dossier chapter
CLOSED_UNRESOLVED); D22 and D-2 close the exact selected question inside the stuck gate and never an upstream one.

Fixture: the vc33 carry-v7 record (two levers, E0004 and E0005), driven as live. On the base none of this exists: a
G4 chapter question could not be closed (revision 1 recorded ``CHAPTER_CLOSE_NOT_REPRESENTABLE`` every time its
budget was spent, the loop Sol stopped), and a G4 stall escalated to G3.
"""
from __future__ import annotations

import copy

from runtime01_support import VC33, controller_answers, drive_to, journal_rows
from inference.framework.record_replay import load_record, replay

G3, G41, G42, G4B = "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS"
EFFECTS = "Q:L1:G4-REACTIONS:{}:EFFECTS"
ORBIT = "Q:L1:G4.2-LEVER-ORBITS:{}:ORBIT"


def _g42(steps: int):
    return replay(load_record(VC33), max_steps=steps, measure=False).machine


def _close(machine, question, reason="HARD_BUDGET_SPENT", history=("E-OUTCOME-1", "E-OUTCOME-2")):
    from inference.framework import gate_closure

    return gate_closure.close_question(machine, question, reason, list(history))


def _g3_state(machine):
    g3 = machine._adapters[G3]
    product = machine.target_journal.active_product(G3)
    return ({entity: item.state for entity, item in g3.lifecycle_journal.entities.items()},
            None if product is None else (product.product_id, product.revision))


def _agent(machine, *, provenance=False):
    from inference.agent.tool_agent import ToolAgent

    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True, provenance_enabled=provenance)
    agent._gate_machine = machine
    return agent


# ---- G4.1 ----------------------------------------------------------------------------------------------------------

def test_one_g41_lever_chapter_closes_while_the_other_levers_continue():
    machine = drive_to(G41)
    reactions = machine._adapters[G41]
    assert reactions._current_entity() == "E0004" and reactions._ordered_entities == ("E0004", "E0005")
    assert not reactions._answers
    closure = _close(machine, EFFECTS.format("E0004"))
    assert (closure.status, closure.scope, closure.gate_id, closure.subject) == ("CLOSED", "CHAPTER", G41, "E0004")
    assert machine.gate_id == G41 and reactions._current_entity() == "E0005"  # the other lever is still studied
    assert controller_answers(machine, G41) == 1  # E0005 is answered as before
    assert list(reactions._answers) == ["E0005"] and machine.gate_id == G42  # settled: answered or closed


def test_a_g41_partial_product_keeps_every_result_and_names_the_closed_chapter():
    machine = drive_to(G41)
    _close(machine, EFFECTS.format("E0004"))
    controller_answers(machine, G41)
    payload = machine.target_journal.active_product(G41).payload
    assert payload["status"] == "PARTIAL" and payload["lever_entities"] == ["E0004", "E0005"]
    # revision 3: the knowledge fields hold supported facts only; the closed lever's geometry is observed geometry
    assert [item["entity_id"] for item in payload["anatomies"]] == ["E0005"]
    assert [item["entity_id"] for item in payload["observed_geometry"]] == ["E0004"]
    assert [item["entity_id"] for item in payload["answers"]] == ["E0005"]  # the successful result kept
    (row,) = payload["unresolved_lever_chapters"]
    assert {key: row[key] for key in ("gate_id", "chapter", "entity_id", "question_id", "reason", "level", "life")} == {
        "gate_id": G41, "chapter": "EFFECTS", "entity_id": "E0004", "question_id": EFFECTS.format("E0004"),
        "reason": "HARD_BUDGET_SPENT", "level": 1, "life": 1}
    assert row["recovery_event_ids"] == ["E-OUTCOME-1", "E-OUTCOME-2"] and row["evidence_refs"]


def test_downstream_g42_studies_every_lever_the_partial_g41_product_carries():
    machine = drive_to(G41)
    _close(machine, EFFECTS.format("E0004"))
    controller_answers(machine, G41)
    study = machine._adapters[G42]
    study._seed()
    assert study._ordered_entities == ("E0004", "E0005")  # the anatomy of the closed chapter is still evidence
    assert study._pending() == ("E0004", "E0005")


# ---- G4.2 ----------------------------------------------------------------------------------------------------------

def test_one_g42_lever_chapter_closes_while_the_other_orbits_continue():
    machine = _g42(20)
    study = machine._adapters[G42]
    assert "E0004" in study._completed and not study._answers  # E0004's run awaits its explanation
    closure = _close(machine, ORBIT.format("E0004"))
    assert (closure.status, closure.scope, closure.subject) == ("CLOSED", "CHAPTER", "E0004")
    assert study._lever_status("E0004") == "CLOSED_UNRESOLVED" and study._awaiting_answer() == ()
    assert study._pending() == ("E0005",) and study._studying()  # E0005's orbit goes on
    capability = machine.next_probe_capability()
    statuses = {row["entity_id"]: row["status"] for row in capability["target"]["levers"]}
    assert statuses == {"E0004": "CLOSED_UNRESOLVED", "E0005": "NOT_STARTED"}
    from inference.framework.controller_executor import next_owned_step

    machine.annotations.oriented = True  # scripted state: Duck's orientation turn is behind it
    step = next_owned_step(machine)
    assert step.owner == "CONTROLLER" and "E0005" in step.reason  # the controller runs the other lever


def test_a_g42_partial_product_keeps_the_answered_orbit_and_g4b_reads_it():
    machine = _g42(24)
    study = machine._adapters[G42]
    assert list(study._answers) == ["E0004"] and study._pending() == ("E0005",)
    _close(machine, ORBIT.format("E0005"))
    payload = machine.target_journal.active_product(G42).payload
    assert payload["status"] == "PARTIAL" and payload["phase1_status"] == "SETTLED_WITH_GAPS"  # r3: never COMPLETE
    assert payload["lever_entities"] == ["E0004"] and [o["entity_id"] for o in payload["orbits"]] == ["E0004"]
    assert [row["entity_id"] for row in payload["unresolved_lever_chapters"]] == ["E0005"]
    assert machine.gate_id == G4B  # the hold released: the ladder continues
    relations = machine._adapters[G4B]
    assert relations._levers() == ("E0004", "E0005")  # G4-B uses every anatomy and the orbit that exists
    region = {item.entity_id: item for item in relations._regions}
    assert region["E0004"].steps and not region["E0005"].steps


# ---- never offered again -------------------------------------------------------------------------------------------

def test_a_closed_chapter_is_never_offered_again_and_a_second_close_is_a_no_op():
    from inference.agent import recovery_consume
    from inference.framework import library_agenda
    from inference.framework.virelai_gates import GateContractError

    machine = _g42(20)
    question = ORBIT.format("E0004")
    assert library_agenda.selected_question(machine) == question  # the explanation it owes was the selection
    token = {"question_id": question, "class": "HARD", "history": [], "exhausted": True, "reason": "READ_ONLY_REPEAT",
             "outcome_event_id": None, "gate_id": G42}
    agent = _agent(machine)
    agent._controller.pending = dict(token)
    recovery_consume._close(agent, None, machine, token)  # Duck's HARD budget spent on this chapter
    agenda = library_agenda.gate_agenda(machine)
    row = next(q for q in agenda["questions"] if q["id"] == question)
    assert row["disposition"] == "CLOSED_UNRESOLVED" and agenda["selected"] != question
    assert question not in agenda["eligible"]
    assert _close(machine, question).status == "NOTHING_TO_CLOSE"  # no loop: once closed, nothing more to do
    template = {"answer_kind": "LEVER_ORBIT_OBSERVATION", "entity_id": "E0004"}
    try:
        machine._adapters[G42].submit_answer(template)
        raise AssertionError("an answer to a closed chapter was accepted")
    except GateContractError as exc:
        assert "closed CLOSED_UNRESOLVED" in str(exc)


# ---- D22 and D-2: the exact chapter, never upstream ---------------------------------------------------------------

def test_d22_closes_the_exact_current_g4_chapter_with_one_gate_close_row_and_never_a_g3_entity(tmp_path, monkeypatch):
    from inference.agent import recovery_consume
    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME

    machine = _g42(20)
    before = _g3_state(machine)
    agent = _agent(machine, provenance=True)
    state_path = tmp_path / f"vc33_{RUNTIME_STATE_FILENAME}"
    monkeypatch.setattr(machine, "legal_move_status",
                        lambda: {"gate_id": machine.gate_id, "legal": False, "reason": "scripted dead end"})
    assert recovery_consume.no_legal_move(agent, state_path, machine) is None
    note = recovery_consume.no_legal_move(agent, state_path, machine)
    assert "chapter E0004 closed CLOSED_UNRESOLVED" in note
    assert _g3_state(machine) == before  # the upstream gate is untouched
    closes = [row for row in journal_rows(state_path) if (row["operation"], row["event"]) == ("GATE", "CLOSE")]
    assert len(closes) == 1
    (close,) = closes
    assert close["submitted"]["scope"] == "CHAPTER" and close["refs"]["subject"] == "E0004"
    assert close["refs"]["question_id"] == ORBIT.format("E0004") and close["gate_id"] == G42
    assert close["reason"]["code"] == "NO_LEGAL_CONTROLLER_MOVE" and len(close["submitted"]["history"]) == 2


def test_d2_closes_the_exact_current_g4_chapter_and_never_a_g3_entity():
    from inference.agent import recovery_consume

    machine = _g42(20)
    before = _g3_state(machine)
    agent = _agent(machine)
    agent._controller.stalled = 3
    note = recovery_consume.stalled(agent, None, machine)
    assert "chapter E0004 closed CLOSED_UNRESOLVED" in note
    assert machine._adapters[G42]._lever_status("E0004") == "CLOSED_UNRESOLVED"
    assert _g3_state(machine) == before and machine._adapters["PLAY-NORMAL"].forced is None


def test_a_g4_stall_with_nothing_selected_closes_its_own_head_never_g3(monkeypatch):
    from inference.framework import gate_closure, library_agenda

    machine = _g42(18)
    before = _g3_state(machine)
    monkeypatch.setattr(library_agenda, "selected_question", lambda _machine: None)
    closure = gate_closure.close_stuck_gate(machine, None, "CONTROLLER_STALLED", ["E-CHECK-1"])
    assert (closure.status, closure.scope, closure.gate_id) == ("CLOSED", "CHAPTER", G42)
    assert closure.subject in ("E0004", "E0005") and _g3_state(machine) == before


# ---- the dossier and the census -------------------------------------------------------------------------------------

def test_dossiers_distinguish_completed_and_closed_chapters_and_the_census_says_partial():
    import dossier_fixtures as fx

    machine = drive_to(G41)
    _close(machine, EFFECTS.format("E0004"))
    controller_answers(machine, G41)
    model = fx.compiled(machine, persist_reason="RUN_END")  # sealed: every v11 and dossier rule is checked
    closed, completed = fx.chapter(model, "E0004", "anatomy"), fx.chapter(model, "E0005", "anatomy")
    assert (closed["status"], closed["basis"]) == ("CLOSED_UNRESOLVED", "CHAPTER_CLOSED_UNRESOLVED")
    assert (completed["status"], completed["basis"]) == ("COMPLETE", "PRODUCT_CERTIFIED")
    assert closed["answer_ref"] is None and closed["source"] == "GATE_RETAINED"
    gates = {row["gate_id"]: row["disposition"] for row in fx.open_level(model)["certified"]["gates"]}
    assert gates[G41] == "PARTIAL"
    forged = copy.deepcopy(model)
    fx.chapter(forged, "E0004", "anatomy").update(status="COMPLETE", basis="PRODUCT_CERTIFIED")
    from inference.framework import world_model_v2 as wm

    forged["content_sha256"] = wm.content_sha256(forged)
    try:
        wm.read_world_model(forged)
        raise AssertionError("a closed chapter relabelled COMPLETE was accepted")
    except wm.WorldModelV2Error:
        pass


def test_a_partial_gate_is_v11_only():
    import dossier_fixtures as fx
    from inference.framework import world_model_v2 as wm

    machine = drive_to(G41)
    _close(machine, EFFECTS.format("E0004"))
    controller_answers(machine, G41)
    model = fx.compiled(machine, persist_reason="RUN_END")
    for schema in (wm.V10_SCHEMA, wm.V9_SCHEMA):
        forged = dict(model, schema=schema)
        forged["content_sha256"] = wm.content_sha256(forged)
        try:
            wm.read_world_model(forged)
            raise AssertionError(f"a {schema} label on a PARTIAL model was accepted")
        except wm.WorldModelV2Error:
            pass
