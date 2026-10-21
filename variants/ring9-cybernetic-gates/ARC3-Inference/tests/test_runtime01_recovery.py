"""WO-RUNTIME-01 §3–§5: the controller consumes every recovery before the next prompt; budgets close only the selected
question or gate; the ladder is never abandoned.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. On the base no recovery exists: a failed Duck turn in
normal play wakes Duck again (or ends the game), and an exhausted gate rests the whole level.
"""
from __future__ import annotations

import requests

from runtime01_support import PlayRun, Script, journal_rows
from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import PLAY_GATE_ID

LS20 = "tests/fixtures/ls20_kaggle_unified_v1_record.json.gz"
VC33 = "tests/fixtures/vc33_kaggle_carry_v7_record.json.gz"
TIMEOUT = requests.ReadTimeout("read timed out")
INSPECT = "print(current_frame.step)"


def _machine(path: str, steps: int):
    return replay(load_record(path), max_steps=steps, measure=False).machine


# ---- normal play: one controller frontier action per failed Duck turn -----------------------------------------

def test_a_failed_duck_turn_in_normal_play_gets_exactly_one_controller_action(tmp_path, monkeypatch):
    """Interface 11-14, 19-20 / WO 9-10, 15, 37."""
    run = PlayRun(tmp_path, monkeypatch, Script([TIMEOUT]))
    run.to_play()
    before = len(run.env_calls)
    failed = run.turn()
    assert failed.turn_outcome == "RECOVERABLE_NO_ACTION" and len(run.env_calls) == before
    assert len(run.script.requests) == 1
    recovered = run.turn()  # the next controller turn, before any prompt is built
    assert recovered.step_executed and recovered.turn_outcome == "ACTION_EXECUTED"
    assert len(run.env_calls) == before + 1 and len(run.script.requests) == 1  # no prompt, no model call
    envelope = run.rows("_probe_envelopes.jsonl")[-1]
    assert envelope["executor"] == "CONTROLLER" and envelope["gate_id"] == PLAY_GATE_ID
    assert envelope["target"]["receipt"] == "FREE_PLAY"
    ledger = run.rows("_turn_ledger.jsonl")
    duck, controller = ledger[-2], ledger[-1]
    assert duck["executor"] == "DUCK" and duck["turn_outcome"] == "RECOVERABLE_NO_ACTION"  # the failure stays visible
    assert controller["executor"] == "CONTROLLER" and controller["recovery"] == "CONTROLLER_ACTION"
    assert controller["question_id"] == "FREE_PLAY"
    assert run.agent._controller.recovery is None  # consumed once
    third = run.turn()  # Duck owns the next step again: control is not transferred
    assert len(run.script.requests) == 2 and third.turn_outcome == "RECOVERABLE_NO_ACTION"


def test_the_frontier_action_is_legal_untried_deterministic_and_never_ducks_choice(tmp_path, monkeypatch):
    """WO 10-12, 37: the same state gives the same action; it was never tried from this board; Duck is not named."""
    actions = []
    for attempt in range(2):
        run = PlayRun(tmp_path / str(attempt), monkeypatch, Script([TIMEOUT]))
        run.to_play()
        run.turn()
        run.turn()
        actions.append(run.env_calls[-1]["actions"][0])
        rows = [row for row in journal_rows(run.state_path) if row["operation"] == "TURN"]
        recovery = rows[-1]
        assert recovery["event"] == "RECOVERY" and recovery["disposition"] == "CONTROLLER_ACTION"
        assert recovery["executor"] == "CONTROLLER" and recovery["refs"]["question_id"] == "FREE_PLAY"
    assert actions[0] == actions[1]


def test_audit_v3_links_the_failure_its_recovery_and_the_execution(tmp_path, monkeypatch):
    """WO 29: question and ownership, failed turn, reason, decision, controller admission and execution."""
    run = PlayRun(tmp_path, monkeypatch, Script([TIMEOUT]))
    run.to_play()
    run.turn()
    run.turn()
    rows = journal_rows(run.state_path)
    by_id = {row["event_id"]: row for row in rows}
    outcome = next(row for row in rows if (row["operation"], row["event"]) == ("TURN", "OUTCOME"))
    recovery = next(row for row in rows if (row["operation"], row["event"]) == ("TURN", "RECOVERY"))
    assert outcome["executor"] == "DUCK" and outcome["disposition"] == "RECOVERABLE_NO_ACTION"
    assert outcome["reason"]["code"] in {"MODEL_TIMEOUT", "TURN_CLOCK"}
    assert outcome["refs"]["question_id"] == "FREE_PLAY"
    assert recovery["submitted"]["turn_event_id"] == outcome["event_id"]
    admission = by_id[recovery["submitted"]["resulting_event_id"]]
    assert (admission["operation"], admission["event"], admission["executor"]) == ("PROBE", "ADMISSION", "CONTROLLER")
    execution = next(row for row in rows if row["refs"]["admission_event_id"] == admission["event_id"])
    assert execution["disposition"] == "EXECUTED"


def test_frontier_exhaustion_stops_cleanly_with_its_proof(tmp_path, monkeypatch):
    """WO 13 / Q4: FREE_PLAY_FRONTIER_EXHAUSTED only with every legal action proven tried or barred."""
    from inference.framework import free_play_frontier

    run = PlayRun(tmp_path, monkeypatch, Script([TIMEOUT]))
    run.to_play()
    machine = run.agent._gate_machine
    frontier = free_play_frontier.for_machine(machine)
    signature = frontier.signature(machine)
    for key in frontier.legal(machine):
        frontier.mark_tried(signature, key, transition_id=0)  # scripted state: every legal action tried here
    run.turn()
    result = run.turn()
    assert result.planned_stop.startswith("FREE_PLAY_FRONTIER_EXHAUSTED")
    rows = journal_rows(run.state_path)
    stop = next(row for row in rows if row["event"] == "RECOVERY")
    assert stop["disposition"] == "NO_CONTROLLER_ACTION"
    assert stop["reason"]["code"] == "FREE_PLAY_FRONTIER_EXHAUSTED"
    proof = stop["submitted"]["proof"]
    assert proof["signature"] == signature and proof["legal"] and all(item["tried"] or item["barred"]
                                                                       for item in proof["legal"])


def test_frontier_exhaustion_is_refused_while_one_legal_action_lacks_proof(tmp_path, monkeypatch):
    from inference.framework import free_play_frontier

    run = PlayRun(tmp_path, monkeypatch, Script([TIMEOUT]))
    run.to_play()
    machine = run.agent._gate_machine
    frontier = free_play_frontier.for_machine(machine)
    signature = frontier.signature(machine)
    legal = sorted(frontier.legal(machine), key=str)
    for key in legal[:-1]:
        frontier.mark_tried(signature, key, transition_id=0)
    run.turn()
    result = run.turn()
    assert not result.planned_stop and result.step_executed  # the one unproven action is taken instead


# ---- gates: the controller head first, then the class budgets --------------------------------------------------

def test_a_controller_owned_gate_head_resumes_before_any_prompt(tmp_path, monkeypatch):
    """WO 15 / interface 8: after a failed G3 choice turn the controller takes the coverage head."""
    run = PlayRun(tmp_path, monkeypatch, Script([TIMEOUT]))
    run.agent._controller.g3_choice_handoff = True
    run.until_duck()
    assert run.agent._gate_machine.gate_id == "G3-LEVERS"
    before = len(run.env_calls)
    calls = len(run.script.requests)
    run.turn()  # the next turn: consumed recovery, controller head
    assert len(run.env_calls) == before + 1 and len(run.script.requests) == calls
    assert run.agent._gate_machine.gate_id == "G3-LEVERS"  # the gate and its mandatory work stay
    recovery = [row for row in journal_rows(run.state_path) if row["event"] == "RECOVERY"][-1]
    assert recovery["disposition"] == "CONTROLLER_ACTION"


def test_hard_budget_two_closes_only_the_selected_gate_question(tmp_path, monkeypatch):
    """WO 16, 19 / Q1: two consecutive HARD failures on G1's question close G1 alone; G2 is still built."""
    from inference.agent import recovery_consume, turn_recovery

    machine = _machine(LS20, 8)
    question = "Q:L1:G1-EGO:LEVEL-1:CONTROL_LOCUS"
    budgets = turn_recovery.Budgets()
    assert budgets.fail(machine, question, "READ_ONLY_REPEAT") is False
    assert budgets.fail(machine, question, "READ_ONLY_REPEAT") is True
    closure = recovery_consume.close_selected(machine, question, "HARD_BUDGET_SPENT")
    assert closure.status == "CLOSED" and closure.scope == "GATE" and closure.gate_id == "G1-EGO"
    product = machine.target_journal.active_product("G1-EGO")
    assert product.payload["status"] == "UNRESOLVED" and product.payload["unresolved_reason"]
    assert machine.gate_id == "G2-COUNTER"  # the ladder continued
    assert machine._counter_prepared_from_ego is True  # G1's close still prepared G2's input
    assert machine._adapters[PLAY_GATE_ID].forced is None


def test_clock_budget_four_and_a_hard_failure_count_separately():
    """WO 17 / Q1: separate consecutive counters per class."""
    from inference.agent import turn_recovery

    machine = _machine(LS20, 8)
    question = "Q:L1:G1-EGO:LEVEL-1:CONTROL_LOCUS"
    budgets = turn_recovery.Budgets()
    assert [budgets.fail(machine, question, reason) for reason in
            ("TURN_CLOCK", "READ_ONLY_REPEAT", "TURN_CLOCK", "MODEL_TIMEOUT")] == [False, False, False, False]
    assert budgets.fail(machine, question, "TURN_CLOCK") is True  # the fourth clock-class failure


def test_progress_resets_both_counters():
    """WO 18 / Q1: an executed action, accepted answer, gate transition or changed masked board resets both."""
    from inference.agent import turn_recovery

    machine = _machine(LS20, 8)
    question = "Q:L1:G1-EGO:LEVEL-1:CONTROL_LOCUS"
    for progress in ("ACTION_EXECUTED", "GATE_PROGRESS", "BOARD_CHANGED"):
        budgets = turn_recovery.Budgets()
        budgets.fail(machine, question, "READ_ONLY_REPEAT")
        budgets.fail(machine, question, "TURN_CLOCK")
        budgets.progress(machine, progress)
        assert budgets.counts(machine, question) == {"HARD": 0, "CLOCK": 0}


def test_g3_entity_closure_closes_one_entity_only(tmp_path):
    """WO §5: a one-entity G3 closure leaves every other entity as it was, and coverage moves on."""
    from inference.agent import recovery_consume

    machine = _machine(VC33, 8)
    assert machine.gate_id == "G3-LEVERS"
    g3 = machine._adapters["G3-LEVERS"]
    journal = g3.lifecycle_journal
    before = {entity: state.state for entity, state in journal.entities.items()}
    entity = next(iter(sorted(e for e, s in before.items() if s in {"UNTOUCHED", "ATTEMPTED"})))
    question = f"Q:L1:G3-LEVERS:{entity}:IS_LEVER"
    closure = recovery_consume.close_selected(machine, question, "HARD_BUDGET_SPENT")
    assert closure.status == "CLOSED" and closure.scope == "ENTITY"
    after = {e: s.state for e, s in journal.entities.items()}
    assert after[entity] == "BUDGET_STOPPED"
    assert {e: s for e, s in after.items() if e != entity} == {e: s for e, s in before.items() if e != entity}
    assert machine.gate_id == "G3-LEVERS"  # the gate itself stays open: only the entity closed


def test_g4_2_unresolved_close_reaches_g4_b():
    """WO 20: the phase-one hold lets a gate-level unresolved G4.2 close through."""
    from inference.framework import gate_closure

    machine = _machine(VC33, 20)
    gate_closure.close_gate(machine, "G4.2-LEVER-ORBITS", "HARD_BUDGET_SPENT")
    payload = machine.target_journal.active_product("G4.2-LEVER-ORBITS").payload
    # r3: phase one is settled with gaps (workflow), apart from the knowledge, which is unresolved
    assert (payload["phase1_status"], payload["settlement_status"]) == ("SETTLED_WITH_GAPS", "SETTLED_WITH_GAPS")
    assert (payload["knowledge_status"], payload["status"], payload["answered_entities"]) == ("UNRESOLVED", "UNRESOLVED", [])
    assert {row["closure_class"] for row in payload["unresolved_lever_chapters"]} == {"INTERFACE_FAILURE"}
    assert machine.gate_id == "G4-B-LEVER-RELATIONS"


def test_cascade_only_where_the_downstream_gate_cannot_be_built():
    """Q3 cascade rule: a G3 closure with no G4-ready lever cannot build G4.1, so G4.1 onward close
    UPSTREAM_UNRESOLVED and the level reaches normal play through the router, never a forced rest."""
    from inference.framework import gate_closure

    machine = _machine(LS20, 12)
    assert machine.gate_id == "G3-LEVERS"
    gate_closure.close_gate(machine, "G3-LEVERS", "HARD_BUDGET_SPENT")
    for gate in ("G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"):
        payload = machine.target_journal.active_product(gate).payload
        status = payload.get("status") or payload.get("phase1_status")
        assert status == "UNRESOLVED" and "UPSTREAM_UNRESOLVED" in str(payload.get("unresolved_reason"))
    assert machine.gate_id == PLAY_GATE_ID and machine._adapters[PLAY_GATE_ID].forced is None


def test_g2_in_a_navigation_world_after_an_unresolved_g1_is_built_not_cascaded():
    from inference.framework import gate_closure

    machine = _machine(LS20, 8)
    gate_closure.close_gate(machine, "G1-EGO", "HARD_BUDGET_SPENT")
    assert machine.gate_id == "G2-COUNTER"
    assert machine.target_journal.active_product("G2-COUNTER") is None


# ---- D22 and D-2 inside ruling B ------------------------------------------------------------------------------

def test_d22_no_legal_move_closes_the_gate_after_two_turns_and_never_rests(monkeypatch):
    """WO 21: two consecutive no-move turns close only the current gate; the next constructible gate opens."""
    from inference.agent import recovery_consume

    machine = _machine(LS20, 10)
    agent = _bare_agent(machine)
    monkeypatch.setattr(machine, "legal_move_status",
                        lambda: {"gate_id": machine.gate_id, "legal": False, "reason": "scripted dead end"})
    assert recovery_consume.no_legal_move(agent, None, machine) is None
    assert machine.gate_id == "G2-COUNTER"
    note = recovery_consume.no_legal_move(agent, None, machine)
    assert note and "NO_LEGAL_CONTROLLER_MOVE" in note
    assert machine.target_journal.active_product("G2-COUNTER").payload["status"] == "UNRESOLVED"
    assert machine.gate_id == "G3-LEVERS" and machine._adapters[PLAY_GATE_ID].forced is None


def test_d2_a_stalled_controller_closes_the_refused_question_and_never_rests():
    """WO 22: three stalled controller turns close the selected question; nothing sets the forced rest."""
    from inference.agent import recovery_consume

    machine = _machine(VC33, 8)
    agent = _bare_agent(machine)
    agent._controller.stalled = 3
    agent._controller.wake = "the gate refused the controller's action: scripted"
    note = recovery_consume.stalled(agent, None, machine)
    assert note and "CONTROLLER_STALLED" in note and "closed CLOSED_UNRESOLVED" in note
    # the selected question (E0004's dossier) has nothing to close and no unsettled head remains, so its gate closes;
    # nothing here can build G4.1, so the router (never the forced rest) reaches normal play: ruling B and Q2
    assert machine.target_journal.active_product("G3-LEVERS").payload["status"] == "UNRESOLVED"
    assert machine._adapters[PLAY_GATE_ID].forced is None
    assert agent._controller.stalled == 0


def test_no_production_path_calls_the_forced_rest():
    """WO 30 (interface): PLAY-NORMAL is entered only by the router."""
    import inspect

    from inference.agent import controller_turn
    from inference.framework import solver

    assert "rest_in_play(" not in inspect.getsource(controller_turn)
    assert "rest_in_play(" not in inspect.getsource(solver)


def _bare_agent(machine):
    from inference.agent.tool_agent import ToolAgent

    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True)
    agent._gate_machine = machine
    return agent


def test_a_d21_budget_close_of_g4b_is_journalled_as_the_controllers_gate_close(tmp_path):
    """Q5: a G4-B or G4-C close on Duck's spent per-level budget (D21) is a GATE CLOSE row, reason DUCK_BUDGET_SPENT."""
    from inference.agent.controller_turn import duck_turn_allowed
    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
    from inference.agent.tool_agent import ToolAgent
    from tests.test_r9_r24_g4_controller_first import RELATIONS, _drive_v7

    machine = _drive_v7().machine
    assert machine.gate_id == RELATIONS
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True, provenance_enabled=True)
    agent._gate_machine = machine
    state_path = tmp_path / f"vc33_{RUNTIME_STATE_FILENAME}"
    turns = 0
    while duck_turn_allowed(machine, tmp_path / "log.txt", agent, state_path):
        turns += 1
    closes = [row for row in journal_rows(state_path) if (row["operation"], row["event"]) == ("GATE", "CLOSE")]
    assert turns >= 1 and len(closes) == 1
    (close,) = closes
    assert (close["executor"], close["disposition"], close["gate_id"]) == ("CONTROLLER", "CLOSED_UNRESOLVED", RELATIONS)
    assert close["reason"]["code"] == "DUCK_BUDGET_SPENT" and close["submitted"]["scope"] == "GATE"
    assert machine.target_journal.active_product(RELATIONS).payload["status"] == "UNRESOLVED"
