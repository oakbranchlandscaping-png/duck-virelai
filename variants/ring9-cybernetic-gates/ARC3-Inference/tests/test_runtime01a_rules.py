"""WO-RUNTIME-01A: the repair obligation, the D22 close's citations, and the forgeries the audit and model refuse.

Author: Claude (Alpha build seat), 2026-10-22. Base ``8b47c73``. Interface: ``INTERFACE_WO_RUNTIME_01A_v1_2026-10-22``.

The fast half of the slice (the canary reproductions are ``test_runtime01a_reproductions``):

* §4.1, the obligation: an executed action under an open repair obligation is progress, never a stop; a close
  discharges the obligation of the question it closes (on the base: the stop is raised, the obligation survives);
* §4.2, the D22 close cites its recovery checks (on the base: the analyzer-watchdog close cites nothing and the journal
  fails with rule 5);
* §4.3, the forgeries, every hash recomputed: refused (on the base, five of them are accepted).
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from runtime01_support import Script, guarded_agent
from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
from inference.agent.tool_agent import AnalyzerTurnResult, ToolAgent, _ToolDispatchResult
from inference.framework import audit_journal as aj
from inference.framework.record_replay import load_record, replay
from inference.framework.solver import _turn_ends_game

FIXTURES = Path(__file__).parent / "fixtures"
VC33 = "tests/fixtures/vc33_kaggle_carry_v7_record.json.gz"
LS20 = "tests/fixtures/ls20_kaggle_unified_v1_record.json.gz"
ORBIT = "Q:L1:G4.2-LEVER-ORBITS:{}:ORBIT"
REJECTED = _ToolDispatchResult('{"error": "G3 dossier answers require target_member_id."}',
                               interaction_kind="CONTRACT_REPAIR", repair_signature="g3-dossier-target",
                               repair_error="G3 dossier answers require target_member_id.")
EXECUTED = _ToolDispatchResult('{"executed": true}', step_executed=True)
INSPECTED = _ToolDispatchResult('{"returncode": 0, "stdout": "observed"}')
RUN = SimpleNamespace(solver_note=None, state="playing")


def _dispatching(*results):
    queue = list(results)

    def dispatch(_path, _name, _arguments):
        return queue.pop(0) if len(queue) > 1 else queue[0]
    return dispatch


# ---- §4.1 · the repair obligation --------------------------------------------------------------------------------

def test_01_an_open_obligation_stops_only_a_dispatch_that_neither_repairs_transitions_nor_executes():
    from inference.agent import repair_obligation

    agent = SimpleNamespace(_contract_repair_required=True, _contract_repair_signatures={"s"})
    assert repair_obligation.stops_turn(agent, INSPECTED)
    assert not repair_obligation.stops_turn(agent, EXECUTED)
    assert not repair_obligation.stops_turn(agent, REJECTED)
    assert not repair_obligation.stops_turn(agent, _ToolDispatchResult("{}", interaction_kind="GATE_TRANSITION"))
    repair_obligation.discharge(agent)
    assert agent._contract_repair_required is False and agent._contract_repair_signatures == set()
    assert not repair_obligation.stops_turn(agent, INSPECTED)


def test_02_ka59_a_rejected_answer_then_an_executed_action_is_progress_and_never_ends_the_game(tmp_path, monkeypatch):
    """ka59 step 40, at the analyzer: the refused answer, the repair prompt, then the executed probe (base: the
    ``contract_repair_loop`` stop on an ACTION_EXECUTED turn, which ``_turn_ends_game`` ends the game on)."""
    agent, state = guarded_agent(tmp_path, monkeypatch, Script(["virelai('gate_answer', answer={})", "action()"]),
                                 dispatch=_dispatching(REJECTED, EXECUTED))
    result = agent.analyze(state, 1)
    assert result.step_executed and result.turn_outcome == "ACTION_EXECUTED"
    assert result.controlled_stop == ""
    assert _turn_ends_game(result, RUN) is False
    assert agent._contract_repair_required is False  # the progress path discharged the obligation


def test_03_dc22_and_sc25_a_carried_obligation_then_an_executed_action_is_progress(tmp_path, monkeypatch):
    """dc22 step 162 and sc25 step 125: the obligation carried from the previous turn, then an executed press."""
    agent, state = guarded_agent(tmp_path, monkeypatch, Script(["action()"]), dispatch=_dispatching(EXECUTED))
    agent._contract_repair_required = True  # carried: no action, level or gate change since the rejection
    agent._sync_no_progress_tool_guard = lambda _path: None  # the scope is unchanged (the base check would agree)
    result = agent.analyze(state, 1)
    assert result.turn_outcome == "ACTION_EXECUTED" and result.controlled_stop == ""
    assert _turn_ends_game(result, RUN) is False


def test_04_an_inspection_under_the_obligation_is_still_the_typed_bounded_failure(tmp_path, monkeypatch):
    """The repair path is unchanged: an inspection instead of the correction ends the turn RECOVERABLE."""
    agent, state = guarded_agent(tmp_path, monkeypatch, Script(["virelai('gate_answer', answer={})", "print(1)"]),
                                 dispatch=_dispatching(REJECTED, INSPECTED))
    result = agent.analyze(state, 1)
    assert (result.turn_outcome, result.recovery_reason) == ("RECOVERABLE_NO_ACTION", "CONTRACT_REPAIR_EXHAUSTED")
    assert result.controlled_stop.startswith("contract_repair_loop") and not _turn_ends_game(result, RUN)


def test_05_a_close_discharges_the_obligation_so_the_next_question_is_never_charged(tmp_path, monkeypatch):
    """dc22's E0010 then E0011: the HARD budget closes the chapter; an inspection on the next turn is an ordinary
    read-only call, never ``CONTRACT_REPAIR_EXHAUSTED`` charged to the next lever (base: it is)."""
    from inference.agent import recovery_consume

    machine = replay(load_record(VC33), max_steps=20, measure=False).machine
    machine.annotations.oriented = True
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True)
    agent._gate_machine = machine
    agent._contract_repair_required, agent._contract_repair_signatures = True, {"rejected"}
    token = {"outcome_event_id": None, "question_id": ORBIT.format("E0004"), "gate_id": machine.gate_id,
             "reason": "CONTRACT_REPAIR_EXHAUSTED", "class": "HARD", "exhausted": True, "decline": False,
             "history": ["PV-a", "PV-b"]}
    agent._controller.recovery = token
    recovery_consume.consume(agent, tmp_path / f"x_{RUNTIME_STATE_FILENAME}", machine, tmp_path / "a.txt", 20, None)
    from inference.framework import chapter_closure

    assert chapter_closure.is_closed(machine._adapters["G4.2-LEVER-ORBITS"], "E0004")
    assert agent._contract_repair_required is False and agent._contract_repair_signatures == set()


# ---- §4.2 · the D22 close cites its recovery checks --------------------------------------------------------------

def _d22(tmp_path, *, legal_at_consume=False, pending=True):
    """ls20 at G2 with no legal move (the canary's G2 dead end): the controller's check, Duck's watchdog outcome, then
    the consuming turn."""
    from inference.agent import recovery_consume, turn_recovery

    machine = replay(load_record(LS20), max_steps=10, measure=False).machine
    assert machine.gate_id == "G2-COUNTER"
    machine.annotations.oriented = True
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True, provenance_enabled=True)
    agent._gate_machine = machine
    agent._ensure_gate_machine = lambda _path: machine
    state = tmp_path / f"w_{RUNTIME_STATE_FILENAME}"
    real = machine.legal_move_status
    legal = {"value": False}
    machine.legal_move_status = lambda: {**real(), "legal": legal["value"],
                                         "reason": "WAIT_FOR_REPRESENTATION_OR_NEW_ACTION offers no probe, answer or end"}
    if pending:
        recovery_consume.no_legal_move(agent, state, machine)  # the controller turn's first check (1 of 2)
    turn_recovery.begin_duck_turn(agent, state)
    turn_recovery.settle(agent, AnalyzerTurnResult(step_executed=False, fatal_failure="controller_no_legal_move: "
                                                   "the gate offers no probe, answer or end"), state)
    legal["value"] = legal_at_consume
    recovery_consume.consume(agent, state, machine, tmp_path / "a.txt", 8, None)
    return agent, machine, _journal_rows(state)


def _journal_rows(state: Path) -> list[dict]:
    from inference.agent.provenance_capture import journal_path

    path = journal_path(state)
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def _kinds(rows):
    return [(row["operation"], row["event"], row["disposition"]) for row in rows]


def test_06_a_d22_close_after_the_watchdog_cites_the_controllers_pending_check(tmp_path):
    agent, machine, rows = _d22(tmp_path)
    assert agent._provenance.failed == ""  # base: JournalFault ... rule 5
    by_id = {row["event_id"]: row for row in rows}
    check, outcome, close, recovery = rows[-4:]
    assert _kinds([check, outcome, close, recovery]) == [
        ("GATE", "RECOVERY_CHECK", "NO_LEGAL_MOVE"), ("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION"),
        ("GATE", "CLOSE", "CLOSED_UNRESOLVED"), ("TURN", "RECOVERY", "CLOSED_UNRESOLVED")]
    assert close["reason"]["code"] == "NO_LEGAL_CONTROLLER_MOVE" and close["submitted"]["class"] is None
    assert close["submitted"]["history"] == [check["event_id"]]  # the check, never the Duck outcome
    assert all(by_id[item]["event"] == "RECOVERY_CHECK" for item in close["submitted"]["history"])
    assert recovery["submitted"] == {"turn_event_id": outcome["event_id"], "resulting_event_id": close["event_id"]}
    assert agent._controller.no_move == []


def test_07_with_no_pending_check_the_close_writes_one_fresh_check_and_cites_it(tmp_path):
    agent, _machine, rows = _d22(tmp_path, pending=False)
    assert agent._provenance.failed == ""
    outcome, check, close, recovery = rows[-4:]
    assert _kinds([outcome, check, close]) == [("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION"),
                                               ("GATE", "RECOVERY_CHECK", "NO_LEGAL_MOVE"),
                                               ("GATE", "CLOSE", "CLOSED_UNRESOLVED")]
    assert close["submitted"]["history"] == [check["event_id"]]


def test_08_with_a_legal_move_at_consumption_nothing_is_fabricated_and_nothing_closes(tmp_path):
    agent, machine, rows = _d22(tmp_path, legal_at_consume=True, pending=False)
    assert agent._provenance.failed == ""
    assert not [row for row in rows if row["event"] in ("CLOSE", "RECOVERY_CHECK")]
    assert machine.gate_id == "G2-COUNTER" and machine.target_journal.active_product("G2-COUNTER") is None
    assert agent._controller.pending is not None  # the ordinary turn decides; ``resolve`` records it


# ---- §4.3 · the forgeries, every hash recomputed -----------------------------------------------------------------

RUN_ID = {"run_stem": "w_p0", "game_id": "w"}
Q = "Q:L1:G2-COUNTER:LEVEL-1:COUNTER"


def _body(op, event, disposition, executor, code=None, *, gate="G2-COUNTER", q=None, subject=None, submitted=None,
          level=1, life=1):
    return {"level": level, "life": life, "gate_id": gate, "at_transition": 5, "executor": executor,
            "operation": op, "event": event, "disposition": disposition, "submitted": submitted, "effective": None,
            "field_sources": None, "refs": aj.make_refs(question_id=q, subject=subject),
            "reason": None if code is None else {"code": code, "text": code}}


def _chain(bodies):
    """Rows with their hashes, event ids and seal recomputed: the forger's journal."""
    rows, head = [], aj.GENESIS
    for seq, body in enumerate(bodies, start=1):
        body = {key: aj.normalized(body.get(key)) for key in aj.BODY_KEYS}
        run = aj.normalized(RUN_ID)
        row = {"schema": aj.SCHEMA, "record": "EVENT", "seq": seq, "run": run, **body,
               "event_id": aj.event_id(run, seq, body), "previous_event_hash": head}
        row["event_hash"] = aj._hashed(row)
        head = row["event_hash"]
        rows.append(row)
    seal = aj._seal_row(len(rows) + 1, RUN_ID, head, len(rows), head, aj.SCHEMA)
    return rows, b"".join(aj._dumps(row) + b"\n" for row in [*rows, seal])


def _id(bodies, index):
    return _chain(bodies[: index + 1])[0][index]["event_id"]


def _read(bodies):
    return aj.read_journal_bytes(_chain(bodies)[1])


def _close(history, *, code="HARD_BUDGET_SPENT", kind="HARD", **where):
    budget = {"HARD": 2, "CLOCK": 4}.get(kind)
    return _body("GATE", "CLOSE", "CLOSED_UNRESOLVED", "CONTROLLER", code, q=where.pop("q", Q),
                 submitted={"scope": "GATE", "class": kind, "budget": budget, "history": history, "cascaded": []},
                 **where)


def _recovery(outcome, close, code="HARD_BUDGET_SPENT", q=Q):
    return _body("TURN", "RECOVERY", "CLOSED_UNRESOLVED", "CONTROLLER", code, q=q,
                 submitted={"turn_event_id": outcome, "resulting_event_id": close})


def _budget_prefix():
    bodies = [_body("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION", "DUCK", "CONTRACT_REPAIR_EXHAUSTED", q=Q)]
    bodies.append(_body("TURN", "RECOVERY", "DUCK_REWOKEN", "CONTROLLER", "CONTRACT_REPAIR_EXHAUSTED", q=Q,
                        submitted={"turn_event_id": _id(bodies, 0), "resulting_event_id": None}))
    bodies.append(_body("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION", "DUCK", "CONTRACT_REPAIR_EXHAUSTED", q=Q))
    return bodies, (_id(bodies, 0), _id(bodies, 2))


def _d22_prefix():
    bodies = [_body("GATE", "RECOVERY_CHECK", "NO_LEGAL_MOVE", "CONTROLLER", "NO_LEGAL_CONTROLLER_MOVE"),
              _body("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION", "DUCK", "NO_LEGAL_CONTROLLER_MOVE", q=Q)]
    return bodies, (_id(bodies, 0), _id(bodies, 1))


def _with_close_and_recovery(prefix, outcome, close_body, code):
    bodies = [*prefix, close_body]
    bodies.append(_recovery(outcome, _id(bodies, len(bodies) - 1), code))
    return bodies


def test_09_the_legitimate_closes_still_read_sealed():
    prefix, (first, second) = _budget_prefix()
    assert _read(_with_close_and_recovery(prefix, second, _close([first, second]), "HARD_BUDGET_SPENT")).status \
        == "SEALED"
    prefix, (check, outcome) = _d22_prefix()
    d22 = _close([check], code="NO_LEGAL_CONTROLLER_MOVE", kind=None)
    assert _read(_with_close_and_recovery(prefix, outcome, d22, "NO_LEGAL_CONTROLLER_MOVE")).status == "SEALED"


def _refused(bodies, needle):
    read = _read(bodies)
    assert read.status == "CORRUPT", f"accepted: {needle}"
    assert needle in read.failure["detail"], read.failure


def test_10_a_d22_close_citing_a_forbidden_outcome_reference_is_refused():
    prefix, (check, outcome) = _d22_prefix()
    forged = _close([check, outcome], code="NO_LEGAL_CONTROLLER_MOVE", kind=None)
    _refused(_with_close_and_recovery(prefix, outcome, forged, "NO_LEGAL_CONTROLLER_MOVE"), "rule 5")


@pytest.mark.parametrize("where", [{"level": 2}, {"life": 2}, {"gate": "G3-LEVERS"}],
                         ids=["level", "life", "gate"])
def test_11_a_close_naming_the_wrong_level_life_or_gate_is_refused(where):
    prefix, (check, outcome) = _d22_prefix()
    forged = _close([check], code="NO_LEGAL_CONTROLLER_MOVE", kind=None, **where)
    _refused(_with_close_and_recovery(prefix, outcome, forged, "NO_LEGAL_CONTROLLER_MOVE"), "rule 5")


def test_12_a_close_naming_the_wrong_question_is_refused():
    prefix, (check, outcome) = _d22_prefix()
    forged = _close([check], code="NO_LEGAL_CONTROLLER_MOVE", kind=None, q="Q:L1:G2-COUNTER:LEVEL-1:OTHER")
    _refused(_with_close_and_recovery(prefix, outcome, forged, "NO_LEGAL_CONTROLLER_MOVE"), "rule 2")


@pytest.mark.parametrize("code,kind", [("CLOCK_BUDGET_SPENT", "HARD"), ("NO_LEGAL_CONTROLLER_MOVE", "HARD")])
def test_13_a_cause_that_does_not_match_its_closure_class_is_refused(code, kind):
    prefix, (first, second) = _budget_prefix()
    _refused(_with_close_and_recovery(prefix, second, _close([first, second], code=code, kind=kind), code), "rule 5")


def test_14_a_recovery_without_its_outcome_is_refused():
    bodies = [_body("TURN", "RECOVERY", "CONTROLLER_ACTION", "CONTROLLER", "TURN_CLOCK", q=Q,
                    submitted={"turn_event_id": "PV-0000000000000000", "resulting_event_id": None})]
    _refused(bodies, "rule 2")


def test_15_a_budget_close_whose_outcome_another_recovery_resolved_is_refused():
    prefix, (first, second) = _budget_prefix()
    bodies = [*prefix, _close([first, second])]
    bodies.append(_body("TURN", "RECOVERY", "DUCK_REWOKEN", "CONTROLLER", "CONTRACT_REPAIR_EXHAUSTED", q=Q,
                        submitted={"turn_event_id": second, "resulting_event_id": None}))
    _refused(bodies, "rule 2")


def test_16_two_closes_consuming_the_same_exhaustion_are_refused():
    prefix, (first, second) = _budget_prefix()
    bodies = [*prefix, _close([first, second]), _close([first, second])]
    bodies.append(_recovery(second, _id(bodies, 3)))
    _refused(bodies, "rule 4")


def test_17_a_certified_gate_row_derived_only_from_a_repair_failure_is_refused():
    import dossier_fixtures as fx
    from inference.framework import gate_closure, world_model_v2 as wm

    machine = replay(load_record(LS20), max_steps=10, measure=False).machine
    gate_closure.close_gate(machine, "G2-COUNTER", "HARD_BUDGET_SPENT")  # a repair budget closed the gate
    model = fx.compiled(machine, persist_reason="RUN_END")
    rows = {row["gate_id"]: row for row in fx.open_level(model)["certified"]["gates"]}
    assert rows["G2-COUNTER"]["disposition"] == "CLOSED_UNRESOLVED"
    wm.read_world_model(model)  # the honest model reads
    forged = copy.deepcopy(model)
    for row in fx.open_level(forged)["certified"]["gates"]:
        if row["gate_id"] == "G2-COUNTER":
            row["disposition"] = "CERTIFIED"
    forged["content_sha256"] = wm.content_sha256(forged)
    with pytest.raises(wm.WorldModelV2Error, match="UNRESOLVED"):
        wm.read_world_model(forged)


def test_18_a_final_model_claiming_complete_with_an_open_journal_is_refused(tmp_path):
    import dossier_provenance_fixtures as dp
    from inference.framework import provenance_chapter as pc
    from inference.framework import world_model_v2 as wm

    path = tmp_path / dp.SIDECAR
    journal = aj.ProvenanceJournal.open(path, run_stem=dp.RUN["run_stem"], game_id=dp.RUN["game_id"])
    journal.append(dp.execution(journal.append(dp.admission("CONTROLLER", 1)), dp.EVIDENCE, dp.TRANSITION))
    unsealed = dp.model("RUN_END")
    chapter = pc.h2(unsealed, data=path.read_bytes(), sidecar=dp.SIDECAR, capture="ENABLED", answer_records=None)
    assert (chapter["integrity"], chapter["completeness"]) == ("OPEN", "INCOMPLETE")
    with pytest.raises(wm.WorldModelV2Error, match="completeness"):
        wm.seal({**unsealed, "provenance": {**chapter, "completeness": "COMPLETE", "reasons": [],
                                            "completeness_scope": "RUN"}})


# ---- guards: real canary closes still read; the frozen v2 reader is unchanged ------------------------------------

def _canary_journals() -> dict:
    return json.loads(gzip.decompress((FIXTURES / "runtime01a_canary_journals.json.gz").read_bytes()))["journals"]


@pytest.mark.parametrize("name", sorted(_canary_journals()))
def test_19_the_sealed_canary_journals_still_read_sealed_under_the_tightened_rules(name):
    entry = _canary_journals()[name]
    data = entry["text"].encode()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    read = aj.read_journal_bytes(data)
    assert read.status == "SEALED", read.failure
    assert sum(1 for row in read.rows if (row["operation"], row["event"]) == ("GATE", "CLOSE")) > 0
    assert aj.read_journal_v2_bytes(data).status == "CORRUPT"  # the frozen v2 reader still refuses v3 rows
