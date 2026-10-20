"""WO-G4-DOSSIER-B, slice B2: library-selected G4 study — the agenda selects, the gate admits, the controller runs.

Author: Claude (Alpha build seat), 2026-10-18. Design: ``INTERFACE_WO_G4_DOSSIER_B2_v1`` under Sol's rulings 5-7 on
``INTERFACE_WO_G4_DOSSIER_B_v1`` and the plan's Stage 2 exit evidence:

* the earliest incomplete actionable chapter is the selected question (anatomy, then orbit; limits is typed and
  never blocks; relations and law keep the gate's level question);
* Duck chooses only on a turn it already holds (the explanation of a confirmed run), only among the gate's admitted
  candidates; mandatory work keeps priority; a decline, a timeout, a stale choice or completion returns to coverage;
* one subject and question through card, digest, capability, probe, route, execution, receipt and dossier;
* with no choice the ladder is byte-identical to ``0119a74`` (``tests/fixtures/g4_no_choice_golden.json``);
* completing one lever never advances another lever or the level.

The ladder is the ft09 v1 record replayed to G4.1's opening, then driven by the controller on the offline ft09
world (``g4_no_choice_trace.Drive``); Duck's explanations are the record's own answers.
"""
from __future__ import annotations

import json
import pickle
from types import SimpleNamespace

import pytest

from g4_no_choice_trace import GOLDEN, ORBITS, Drive, controller_trace, record_trace
from inference.framework.controller_executor import next_owned_step
from inference.framework.library_agenda import gate_agenda, question_id
from inference.framework.virelai_gates import GateContractError

REACTIONS = "G4-REACTIONS"
LEVERS = ("E0053", "E0054", "E0055", "E0056", "E0057", "E0060", "E0061", "E0062")
_CACHE: dict[str, bytes] = {}


class _Stop(Exception):
    pass


def _qid(gate: str, entity: str) -> str:
    return question_id(1, gate, entity, "EFFECTS" if gate == REACTIONS else "ORBIT")


def _cached(key: str, build) -> Drive:
    if key not in _CACHE:
        _CACHE[key] = pickle.dumps(build())
    return pickle.loads(_CACHE[key])


def _at_anatomy() -> Drive:
    """G4.1 open on the eight ft09 levers, no anatomy answered."""
    return _cached("anatomy", Drive)


def _at_explanation() -> Drive:
    """G4-A: E0053's run is confirmed and Duck holds the turn to explain it; no other lever was run."""
    def build():
        drive = Drive()

        def stop(_drive):
            raise _Stop

        try:
            drive.run(stop)
        except _Stop:
            pass
        return drive

    return _cached("explanation", build)


def _until_duck(drive: Drive, limit: int = 40) -> list:
    """The controller's steps up to Duck's next turn (actions taken, answers submitted)."""
    taken = []
    for _ in range(limit):
        step = next_owned_step(drive.machine)
        if step.owner != "CONTROLLER":
            return taken
        if step.kind == "ANSWER":
            drive.machine.submit_answer(json.loads(json.dumps(step.answer)))
        else:
            taken.append((step, drive.act(step)))
    raise AssertionError("the controller never handed the turn back")


def _events(machine) -> list[tuple[str, str]]:
    return [(row["event"], row["entity_id"]) for row in machine.g4_selection_events]


def _click(machine, entity: str) -> dict:
    return dict(machine._adapters[ORBITS]._interventions[entity])


# ---- 0 · the no-choice golden (a guard on 0119a74; must stay byte-identical) -----------------------------------

def test_b2_00_with_no_choice_the_g4_ladder_is_byte_identical_to_the_golden():
    golden = json.loads(GOLDEN.read_text())
    assert controller_trace() == golden["ft09_controller"]
    assert record_trace() == golden["ft09_record"]


# ---- 1 · the agenda selects the earliest incomplete actionable chapter ------------------------------------------

def test_b2_01_the_agenda_selects_the_gates_own_lever_chapter_and_limits_never_blocks():
    from inference.framework import g4_selection

    drive = _at_anatomy()
    machine = drive.machine
    agenda = gate_agenda(machine)
    assert machine.gate_id == REACTIONS and agenda["selected"] == _qid(REACTIONS, "E0053")
    rows = g4_selection.admission_candidates(machine)  # revision 2 (Sol): G4.1 is controller work, never Duck's choice
    assert [row["entity_id"] for row in rows] == list(LEVERS) and rows[0]["head"]
    assert not any(row["selectable"] for row in rows)
    assert not set(agenda["eligible"]) & {_qid(REACTIONS, entity) for entity in LEVERS}
    limits = [q for q in agenda["questions"] if q["kind"] == "LIMITS"]
    assert {q["subject"] for q in limits} == set(LEVERS)
    assert all(q["disposition"] == "OPEN_NOT_ACTIONABLE" and q["gate"] is None for q in limits)
    assert agenda["selected"] not in {q["id"] for q in limits}
    explaining = _at_explanation().machine
    explaining.select_question(_qid(ORBITS, "E0060"), actor="DUCK")
    frozen = pickle.dumps(explaining)
    assert explaining.gate_id == ORBITS and gate_agenda(explaining)["selected"] == _qid(ORBITS, "E0053")
    assert pickle.dumps(explaining) == frozen  # the agenda reads a standing choice and writes nothing
    head = g4_selection.admission_candidates(explaining)[0]
    assert (head["entity_id"], head["status"], head["head"]) == ("E0054", "NOT_STARTED", True)


def test_b2_01_relations_and_law_keep_the_gates_level_question():
    drive = Drive().run()
    assert drive.machine.gate_id == "G4-C-LEVER-LAW"
    assert gate_agenda(drive.machine)["selected"] == question_id(1, "G4-C-LEVER-LAW", "LEVEL-1", "LEVER_LAW")


# ---- 2 · an off-head choice on the turn Duck already holds ------------------------------------------------------

def test_b2_02_duck_chooses_an_off_head_lever_and_one_question_threads_probe_execution_and_receipt():
    drive = _at_explanation()
    machine = drive.machine
    chosen = _qid(ORBITS, "E0057")
    transitions = len(machine.transition_index)
    selection = machine.select_question(chosen, actor="DUCK")
    assert (selection["entity_id"], selection["is_head"], selection["gate_id"]) == ("E0057", False, ORBITS)
    assert len(machine.transition_index) == transitions  # choosing consumes no experiment
    assert gate_agenda(machine)["selected"] == _qid(ORBITS, "E0053")  # the explanation owed comes first
    drive.duck_turn(None)  # Duck explains E0053 on the same turn
    assert gate_agenda(machine)["selected"] == chosen
    capability = machine.next_probe_capability()
    assert capability["question_id"] == chosen and capability["target"]["question_id"] == chosen
    assert capability["target"]["selected_by"] == "DUCK" and capability["target"]["selected_entity"] == "E0057"
    taken = _until_duck(drive)
    assert taken and all(step.action == _click(machine, "E0057") for step, _ in taken)
    assert all(chosen in step.reason for step, _ in taken)
    for (step, receipt), row in zip(taken, machine.transition_index[-len(taken):]):
        assert receipt["probe_id"].startswith("G4.2-LEVER-ORBITS:GUIDED:SEL:E0057:L1P1:R1:")
        assert row["probe_id"] == receipt["probe_id"] and row["evidence_id"] == receipt["evidence_id"]
    events = machine._adapters[ORBITS]._events[-len(taken):]
    assert all(event["question_id"] == chosen and event["lever_entity_id"] == "E0057" for event in events)
    assert _events(machine) == [("ADMITTED", "E0057"), ("FINISHED", "E0057")]  # completion ends the choice
    assert gate_agenda(machine)["selected"] == chosen  # Duck now explains the chosen run
    drive.duck_turn(None)
    step = next_owned_step(machine)
    assert step.action == _click(machine, "E0054") and step.reason == "G4-A: run E0054 (NOT_STARTED)"
    assert ":SEL:" not in drive.act(step)["probe_id"]  # coverage resumes at the head, unchanged


def test_b2_03_the_card_the_digest_and_the_capability_name_the_chosen_question(tmp_path):
    from test_g3_directed_click import _surfaces

    drive = _at_explanation()
    machine = drive.machine
    drive.duck_turn(None)
    card, digest, capability = _surfaces(tmp_path / "head", machine)
    head = _qid(ORBITS, "E0054")
    assert card["question_id"] == digest["goal"]["question_id"] == capability["question_id"] == head
    chosen = _qid(ORBITS, "E0060")
    machine.select_question(chosen, actor="DUCK")
    card, digest, capability = _surfaces(tmp_path / "chosen", machine)
    assert card["question_id"] == digest["goal"]["question_id"] == capability["question_id"] == chosen
    assert digest["goal"]["gate_id"] == ORBITS and capability["target"]["question_id"] == chosen
    assert any("virelai('next_probe'" in rule for rule in machine.gate_view()["rules"])  # the card says how


# ---- 3 · admission is the gate's: refusals are recorded once ----------------------------------------------------

def test_b2_04_inadmissible_choices_are_refused_once_with_their_reason():
    drive = _at_explanation()
    machine = drive.machine
    with pytest.raises(GateContractError, match="G4 choice not admissible: the question names no lever"):
        machine.select_question(_qid(ORBITS, "E9999"), actor="DUCK")
    with pytest.raises(GateContractError, match="names no lever"):
        machine.select_question(_qid(ORBITS, "E0053"), actor="DUCK")  # its run is confirmed: not a candidate
    drive.duck_turn(None)
    drive.act(next_owned_step(machine))  # E0054's run is under way
    with pytest.raises(GateContractError, match="owes its run endpoint first"):
        machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
    end = Drive().run().machine
    with pytest.raises(GateContractError, match="the active gate is G4-C-LEVER-LAW"):
        end.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
    assert [row["event"] for row in machine.g4_selection_events] == ["REFUSED", "REFUSED", "REFUSED"]
    assert [row["event"] for row in end.g4_selection_events] == ["REFUSED"]
    assert getattr(machine._adapters[ORBITS], "_g4_selection", None) is None


def test_b2_04_a_g3_question_keeps_the_g3_refusal_and_a_g4_question_never_reaches_g3():
    machine = _at_explanation().machine
    with pytest.raises(GateContractError, match="G3 choice not admissible: the active gate is G4.2-LEVER-ORBITS"):
        machine.select_question("Q:L1:G3-LEVERS:E0053:IS_LEVER", actor="DUCK")
    assert machine.g3_selection_events == [] and machine.g4_selection_events == []


# ---- 4 · fallback: stale choices and completion return to coverage ---------------------------------------------

def test_b2_05_a_boundary_that_cuts_the_chosen_run_ends_the_choice_and_coverage_resumes():
    from inference.framework.record_replay import lossless_outcome, record_like_live

    drive = _at_explanation()
    machine = drive.machine
    machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
    drive.duck_turn(None)
    step = next_owned_step(machine)
    assert step.action == _click(machine, "E0057")
    probe = machine.validate_probe({"probe_token": step.probe_token}, [step.action])
    drive.world.transition_id += 1
    boundary = {"game_over": True, "level_before": 1, "level_after": 1, "state": "GAME_OVER"}
    drive.world.grid, outcome = lossless_outcome(drive.world.grid, drive.world.transition_id, step.action,
                                                 drive.world.changes(step.action), boundary)
    record_like_live(machine, probe, outcome, drive.world.valid_actions)
    machine.next_probe_capability()  # the gate's own state-advancing call settles the choice
    assert _events(machine) == [("ADMITTED", "E0057"), ("STALE", "E0057")]
    assert getattr(machine._adapters[ORBITS], "_g4_selection", None) is None
    capability = machine.next_probe_capability()
    assert capability is None or "question_id" not in (capability.get("target") or {})


def test_b2_05_a_declined_turn_changes_nothing_the_controller_would_do():
    """Decline or timeout: Duck explains without choosing; the next step is exactly the no-choice head."""
    golden = json.loads(GOLDEN.read_text())["ft09_controller"]["steps"]
    drive = _at_explanation()
    drive.duck_turn(None)
    step = next_owned_step(drive.machine)
    receipt = drive.act(step)
    first = next(row for row in golden if row.get("reason") == "G4-A: run E0054 (NOT_STARTED)")
    assert (step.reason, receipt["probe_id"], receipt["evidence_id"]) == (
        first["reason"], first["probe_id"], first["evidence_id"])
    assert drive.machine.g4_selection_events == []


# ---- 5 · isolation, and the dossier names the subject and question ----------------------------------------------

def test_b2_06_completing_the_chosen_lever_advances_no_other_lever_or_level_and_its_dossier_cites_the_run():
    import dossier_fixtures as fx

    drive = _at_explanation()
    machine = drive.machine
    drive.duck_turn(None)
    before = fx.compiled(machine, persist_reason="LEVEL_ADVANCE")
    machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
    taken = _until_duck(drive)
    drive.duck_turn(None)  # Duck explains E0057
    after = fx.compiled(machine, persist_reason="LEVEL_ADVANCE")
    statuses = {e: machine._adapters[ORBITS]._lever_status(e) for e in LEVERS}
    assert statuses["E0057"] == "EXPLAINED" and statuses["E0053"] == "EXPLAINED"
    assert all(statuses[e] == "NOT_STARTED" for e in LEVERS if e not in ("E0053", "E0057"))
    assert int(machine.lives.level) == 1 and len(after["levels"]) == len(before["levels"])
    old, new = fx.open_level(before)["lever_dossiers"], fx.open_level(after)["lever_dossiers"]

    def stated(chapter):  # what a chapter states; the aggregate product's ref and the latest sighting move on
        facts = dict(chapter["facts"] or {})
        facts.pop("appearance", None)
        return chapter["status"], chapter["basis"], facts, chapter["open"]

    for entity in LEVERS:
        if entity == "E0057":
            continue
        for name in ("identity", "anatomy", "orbit", "relations", "law_tests"):
            assert stated(new[entity]["chapters"][name]) == stated(old[entity]["chapters"][name]), (entity, name)
    orbit = new["E0057"]["chapters"]["orbit"]
    assert old["E0057"]["chapters"]["orbit"]["status"] == "NOT_BUILT" and orbit["status"] != "NOT_BUILT"
    assert {receipt["evidence_id"] for _, receipt in taken} <= set(orbit["evidence_refs"])
    assert new["E0057"]["subject"]["entity_id"] == "E0057"  # the question's subject; its kind is this chapter


# ---- 6 · G4.1: an anatomy choice reorders answers and changes no product ----------------------------------------

def test_b2_07_g41_is_controller_work_a_duck_choice_is_refused_and_coverage_answers_in_order():
    """Revision 2 (Sol, blocker 1): G4.1 has no Duck probe turn. Its anatomy questions stay on the agenda with the
    controller's head selected; a choice is refused (recorded once), changes nothing, and the product is the golden's."""
    golden = {row["target_id"]: row for row in json.loads(GOLDEN.read_text())["ft09_controller"]["products"]}
    drive = _at_anatomy()
    machine = drive.machine
    def state():  # the G4.1 gate's own state (its machine reference aside)
        return pickle.dumps({k: v for k, v in vars(machine._adapters[REACTIONS]).items() if k != "machine"})

    frozen = state()
    with pytest.raises(GateContractError, match="G4 choice not admissible: G4.1 anatomy is controller work"):
        machine.select_question(_qid(REACTIONS, "E0060"), actor="DUCK")
    assert _events(machine) == [("REFUSED", None)] and state() == frozen
    assert gate_agenda(machine)["selected"] == _qid(REACTIONS, "E0053")
    answered = []
    while machine.gate_id == REACTIONS:
        step = next_owned_step(machine)
        answered.append(step.answer["entity_id"])
        machine.submit_answer(json.loads(json.dumps(step.answer)))
    assert answered == list(LEVERS)  # the controller's coverage order
    product = machine.target_journal.active_product(REACTIONS)
    assert product.product_id == golden[REACTIONS]["product_id"]


# ---- 7 · Duck's tool, the durable log and the audit journal -----------------------------------------------------

def _bridge(tmp_path, machine):
    from test_provenance_capture import _bridge as bridge

    agent, state_path = bridge(tmp_path)
    agent._gate_machine = machine
    return agent, state_path


def test_b2_08_duck_chooses_through_the_tool_and_every_event_reaches_disk_and_the_audit_journal(tmp_path):
    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
    from test_provenance_capture import _rows

    machine = _at_explanation().machine
    agent, state_path = _bridge(tmp_path, machine)
    chosen, missing = _qid(ORBITS, "E0056"), _qid(ORBITS, "E9999")
    reply = agent._run_python_tool(state_path, {"code": f"result = virelai('next_probe', question_id={chosen!r})"})
    shown = json.loads(json.loads(reply.content)["stdout"])
    assert shown["error"] is None and shown["data"]["target"]["question_id"] == chosen  # the probe binds the choice
    assert shown["data"]["question_id"] == _qid(ORBITS, "E0053")  # the explanation owed this turn still comes first
    refused = agent._run_python_tool(state_path, {"code": f"result = virelai('next_probe', question_id={missing!r})"})
    assert json.loads(json.loads(refused.content)["stdout"])["error"].startswith("G4 choice not admissible")
    path = state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_g4_selection_events.jsonl"))
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [(row["event"], row["question_id"]) for row in rows] == [("ADMITTED", chosen), ("REFUSED", missing)]
    assert all(row["schema"] == "virelai-g4-selection-event-v1" and row["gate_id"] == ORBITS for row in rows)
    audit = _rows(state_path, "G4_SELECTION")
    assert [(r["event"], r["disposition"], r["gate_id"], r["refs"]["question_id"]) for r in audit] == [
        ("ADMISSION", "ADMITTED", ORBITS, chosen), ("ADMISSION", "REFUSED", ORBITS, missing)]
    assert _rows(state_path, "G3_SELECTION") == []


def test_b2_10_the_tool_refuses_a_g41_choice_instead_of_admitting_it_and_reporting_no_probe(tmp_path):
    """Sol's blocker 1, fail-first: revision 1 recorded an admitted G4.1 choice, then replied "No probe is admissible
    now." Revision 2 refuses it: no admission, no bound choice, and the reply names why and the current question."""
    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME

    machine = _at_anatomy().machine
    agent, state_path = _bridge(tmp_path, machine)
    question = _qid(REACTIONS, "E0060")
    reply = agent._run_python_tool(state_path, {"code": f"result = virelai('next_probe', question_id={question!r})"})
    shown = json.loads(json.loads(reply.content)["stdout"])
    assert shown["error"].startswith("G4 choice not admissible: G4.1 anatomy is controller work")
    assert shown["data"]["question_id"] == _qid(REACTIONS, "E0053")  # the controller's head stays selected
    assert getattr(machine._adapters[REACTIONS], "_g4_selection", None) is None
    path = state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_g4_selection_events.jsonl"))
    assert [json.loads(line)["event"] for line in path.read_text().splitlines()] == ["REFUSED"]


def test_b2_11_the_derived_question_of_the_dossier_chapter_is_the_selection_and_every_cited_receipt():
    """Sol's ruling: no question_id is stored in the dossier. The question is derived from level, gate, entity and
    chapter; it equals the admitted selection, every selected run receipt and the completed chapter's question.
    Revision 3: proven on the saved v8 artifact by the canonical validator (``lever_dossier_selection``), from the
    persisted audit rows and receipt index; the live receipts carry the same question."""
    from inference.framework import lever_dossier_selection as sel
    from test_g4_selection_persisted import _translated, chosen_run, journal_bytes, sealed_unvalidated

    machine, unsealed = chosen_run()
    model = sealed_unvalidated(unsealed, journal_bytes(_translated(machine)))
    level = next(item for item in model["levels"] if item["state"] == "OPEN")
    chapter = level["lever_dossiers"]["E0057"]["chapters"]["orbit"]
    derived = sel.dossier_question(level["level"], "E0057", "orbit")
    admitted = next(row for row in machine.g4_selection_events if row["event"] == "ADMITTED")
    receipts = [event for event in machine._adapters[ORBITS]._events if event.get("question_id")]
    assert derived == question_id(1, ORBITS, "E0057", "ORBIT") == admitted["question_id"]
    assert chapter["status"] == "COMPLETE" and {r["evidence_id"] for r in receipts} == set(chapter["evidence_refs"])
    assert all(r["question_id"] == derived for r in receipts)
    assert sel.problems(model) == [] and _wm_read(model)["schema"] == "virelai-world-model-v10"


def test_b2_12_a_new_choice_replacing_a_standing_one_ends_it_on_the_record():
    """Revision 3: one open choice per gate. Re-choosing before the run begins closes the first choice (STALE), so
    every FINISHED selection pairs with exactly one earlier ADMITTED one."""
    drive = _at_explanation()
    machine = drive.machine
    machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
    second = machine.select_question(_qid(ORBITS, "E0060"), actor="DUCK")
    assert second["admission"] == 2
    assert _events(machine) == [("ADMITTED", "E0057"), ("STALE", "E0057"), ("ADMITTED", "E0060")]
    assert machine.g4_selection_events[1]["reason"] == "a new choice replaced it before its run began"


def _wm_read(model):
    from inference.framework.world_model_v2 import read_world_model

    return read_world_model(model)


# ---- 8 · the NAV route takes the chosen lever --------------------------------------------------------------------

def test_b2_09_the_nav_route_plans_for_the_chosen_lever():
    from inference.framework import controller_executor, g4_selection

    planned = []
    levers = [{"entity_id": "A", "status": "NOT_STARTED", "click": {"kind": "NAV"}},
              {"entity_id": "B", "status": "NOT_STARTED", "click": {"kind": "NAV"}}]
    adapter = SimpleNamespace(
        _g4_selection={"question_id": "Q:L1:G4.2-LEVER-ORBITS:B:ORBIT", "entity_id": "B", "level": 1, "life": 1,
                       "gate_id": ORBITS, "actor": "DUCK", "runs_at_admission": 0, "admitted_status": "NOT_STARTED"},
        _ordered_entities=("A", "B"), _answers={}, _completed={}, _interruptions={}, _runs={}, _active_run=None,
        _level_closed=None, _lever_status=lambda e: "NOT_STARTED", _studying=lambda: True,
        planned_nav_step=lambda e: planned.append(e) or SimpleNamespace(intent="APPROACH", action="ACTION1"))
    machine = SimpleNamespace(gate_id=ORBITS, lives=SimpleNamespace(level=1, life=1), _adapters={ORBITS: adapter},
                              next_probe_capability=lambda: {"probe_token": "T", "target": {"levers": levers}},
                              gate_view=lambda: {})
    lever, status = controller_executor._orbit_lever(machine, levers)
    assert (lever["entity_id"], status) == ("B", "NOT_STARTED") and g4_selection.chosen(machine)["entity_id"] == "B"
    step = controller_executor._nav_orbit_step(machine, machine.next_probe_capability(), None)
    assert planned == ["B"] and step.decision == {"intent": "NAV:APPROACH:B"}
    assert "Q:L1:G4.2-LEVER-ORBITS:B:ORBIT" in step.reason
