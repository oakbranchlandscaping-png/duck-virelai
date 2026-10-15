"""WO-PE-01 fail-first tests: the provenance journal and its six capture points.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v1_2026-10-14``;
rulings ``RULINGS_PAPER_EVIDENCE_v1_2026-10-14`` D1-D4 and the two carried defects.

Every submitted probe, answer, G3 choice and note produces one ADMISSION row (refusals included); every admitted
probe that reaches the environment produces an EXECUTION row; a G3 handoff nobody takes is an OPPORTUNITY /
NOT_ATTEMPTED row. Answers keep the submitted payload, the effective payload and who supplied each field. The
journal is deterministic and hash chained, and a reader detects every kind of damage. Nothing here reads
transcript prose.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME, Frame, write_runtime_state
from inference.agent.tool_agent import ToolAgent

STEP_PAYLOAD = {"executed": True, "action_num": 1, "transition_id": 1, "level": 1,
                "valid_actions": ["ACTION1", "ACTION2"], "board_changed": True}
REACHABILITY = {
    "schema": "virelai-nav-reachability-certificate-v1", "target_version": 1, "status": "PRESUMED_UNREACHABLE",
    "reachable_stands": [[1, 1]], "refused_edges": [[[1, 1], "ACTION1"]], "closest_stand": [1, 1], "remaining_gap": 3,
    "contact_surface_count": 0, "open_frontier_edge_count": 0, "inertness_claim_permitted": False,
    "reopen_conditions": ["new stood anchor", "previously refused edge yields", "target geometry or identity changes",
                          "ego footprint, bearing map, or action surface changes", "terrain or level state changes"],
    "evidence_refs": ["E-FLOOR", "E-WALL"],
}
EXPLANATION = ("Every mapped floor stand was tried and none touches this object, so it is released; that is not "
               "inertness, and a new stand reopens it.")


def _prov():
    from inference.framework import audit_journal

    return audit_journal


def _path(state_path: Path, suffix: str) -> Path:
    return state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", suffix))


def _journal(state_path: Path) -> list[dict]:
    read = _prov().read_journal(_path(state_path, "_provenance.jsonl"))
    assert read.status in {"OPEN", "SEALED"}, read.failure
    return read.rows


def _rows(state_path: Path, operation: str, *, event: str | None = None) -> list[dict]:
    return [row for row in _journal(state_path) if row["operation"] == operation and event in (None, row["event"])]


def _bridge(tmp_path: Path, *, enabled: bool = True):
    state_path = tmp_path / f"gated_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(state_path, current_frame=Frame(grid=((0, 1), (0, 0)), step=0, level=1), history=[])
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      provenance_enabled=enabled)
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["ACTION1", "ACTION2"]
    return agent, state_path


def _stdout(result) -> dict:
    return json.loads(json.loads(result.content)["stdout"])


def _reachability_machine():
    from test_g3_scheduler import machine_for

    machine = machine_for(["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO")
    adapter = machine._adapters["G3-LEVERS"]
    target = machine.next_probe_capability()["target"]
    adapter._pending_reachability = {**REACHABILITY, "target_entity_id": target["entity_id"],
                                     "target_member_id": target["member_id"]}
    return machine, adapter, target


# ---- 1, 2, 11 · Duck probes ------------------------------------------------------------------------------------

def test_an_admitted_duck_probe_is_admitted_executed_and_joined_to_envelope_evidence_and_transition(tmp_path):
    from test_gated_python_bridge import _capability

    agent, state_path = _bridge(tmp_path)
    agent._step_env_callback = lambda payload: dict(STEP_PAYLOAD)
    capability = _capability(agent, state_path)
    code = f"action({capability['actions']!r}, decision={{'probe_token': {capability['probe_token']!r}}})"
    assert agent._run_python_tool(state_path, {"code": code}).step_executed

    admission, execution = _rows(state_path, "PROBE")
    assert (admission["event"], admission["disposition"], admission["executor"]) == ("ADMISSION", "ADMITTED", "DUCK")
    issued = agent._gate_machine._issued_capabilities[capability["probe_token"]]
    assert admission["submitted"] == {"actions": capability["actions"], "decision": {
        "probe_token": f"CAPABILITY:{issued['probe_id']}:R{issued['gate_revision']}"}}  # the capability, not its HMAC
    assert admission["gate_id"] == "G1-EGO" and admission["at_transition"] == 0 and admission["reason"] is None
    assert (execution["event"], execution["disposition"]) == ("EXECUTION", "EXECUTED")
    envelope = json.loads(_path(state_path, "_probe_envelopes.jsonl").read_text().splitlines()[-1])
    event = json.loads(_path(state_path, "_gate_events.jsonl").read_text().splitlines()[-1])
    row = agent._gate_machine.transition_index[-1]
    assert admission["refs"]["probe_id"] == execution["refs"]["probe_id"] == envelope["probe_id"] == event["probe_id"]
    assert execution["refs"]["evidence_id"] == event["evidence_id"] == row["evidence_id"]
    assert execution["refs"]["executed_transition"] == row["transition_id"] == 1


def test_a_refused_duck_probe_keeps_the_exact_action_and_the_gates_reason(tmp_path):
    from test_gated_python_bridge import _capability

    agent, state_path = _bridge(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or dict(STEP_PAYLOAD)
    capability = _capability(agent, state_path)
    wrong = agent._run_python_tool(
        state_path, {"code": f"action(['ACTION2'], decision={{'probe_token': {capability['probe_token']!r}}})"})
    assert not wrong.step_executed and calls == []

    (refused,) = _rows(state_path, "PROBE")
    assert (refused["event"], refused["disposition"], refused["executor"]) == ("ADMISSION", "REFUSED", "DUCK")
    assert refused["submitted"]["actions"] == [{"action": "ACTION2"}]  # as it crosses the tool boundary
    assert refused["reason"]["code"] == "GATE_CONTRACT" and refused["reason"]["text"] in wrong.content
    assert refused["refs"]["probe_id"] is None


def test_a_duck_action_refused_before_the_gate_is_still_one_refused_admission(tmp_path):
    """The repair block: a rejected gate answer in the same tool call blocks the action before any gate check."""
    agent, state_path = _bridge(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    code = "result = virelai('gate_answer', answer={})\naction(['ACTION1'])"
    agent._run_python_tool(state_path, {"code": code})
    assert calls == []
    (refused,) = _rows(state_path, "PROBE")
    assert refused["disposition"] == "REFUSED" and refused["reason"]["code"] == "ACTION_CONTRACT"
    assert refused["submitted"]["actions"] == [{"action": "ACTION1"}]


# ---- 3, 4 · controller probes -----------------------------------------------------------------------------------

class _ControllerRun:
    """The production agent on the continuation world, controller-only, the way ``solver.play`` drives it."""

    def __init__(self, tmp_path: Path, monkeypatch, *, enabled: bool = True, turns: int = 30) -> None:
        from test_memory_m2 import Run

        run = Run(tmp_path, monkeypatch)
        agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                          controller_executor_enabled=True, provenance_enabled=enabled)
        monkeypatch.setattr(agent, "_ensure_session", lambda _path: None)
        monkeypatch.setattr(agent, "_chat_completion", run._model)
        agent._controller.g3_choice_handoff = False
        run.agent = agent
        run.until_duck(limit=turns)
        self.run, self.agent, self.state_path, self.dir = run, agent, run.state_path, tmp_path


@pytest.fixture(scope="module")
def controller_run(tmp_path_factory):
    patch = pytest.MonkeyPatch()
    yield _ControllerRun(tmp_path_factory.mktemp("prov_a"), patch)
    patch.undo()


def test_every_controller_action_is_an_admitted_and_executed_controller_probe(controller_run):
    rows = _rows(controller_run.state_path, "PROBE")
    admitted = [r for r in rows if r["event"] == "ADMISSION"]
    executed = [r for r in rows if r["event"] == "EXECUTION"]
    assert len(admitted) == len(executed) == len(controller_run.run.env_calls) > 0
    assert {(r["executor"], r["disposition"]) for r in admitted} == {("CONTROLLER", "ADMITTED")}
    assert {r["disposition"] for r in executed} == {"EXECUTED"}
    assert [r["refs"]["probe_id"] for r in admitted] == [r["refs"]["probe_id"] for r in executed]
    assert [r["submitted"]["actions"] for r in admitted] == [call["actions"] for call in controller_run.run.env_calls]


def test_a_refused_controller_probe_is_a_refused_controller_admission(tmp_path):
    from test_gated_python_bridge import _capability
    from inference.agent.controller_turn import _controller_action

    agent, state_path = _bridge(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or dict(STEP_PAYLOAD)
    machine = agent._ensure_gate_machine(state_path)
    _capability(agent, state_path)
    step = SimpleNamespace(probe_token="P-not-the-current-token", decision={}, action={"action": "ACTION1"},
                           gate_id=machine.gate_id, reason="test")
    result = _controller_action(agent, state_path, machine, step, 0, 1, tmp_path / "log.txt")
    assert not result.step_executed and calls == []
    (refused,) = _rows(state_path, "PROBE")
    assert (refused["executor"], refused["event"], refused["disposition"]) == ("CONTROLLER", "ADMISSION", "REFUSED")
    assert refused["submitted"] == {"actions": [{"action": "ACTION1"}],
                                    "decision": {"probe_token": "CAPABILITY:NOT_ISSUED"}}
    assert refused["reason"]["code"] == "GATE_CONTRACT" and refused["reason"]["text"]


# ---- 5, 6, 7 · answers ------------------------------------------------------------------------------------------

def test_an_admitted_duck_answer_keeps_its_raw_and_effective_payloads_and_who_wrote_each_field(tmp_path):
    agent, state_path = _bridge(tmp_path)
    machine, _adapter, target = _reachability_machine()
    agent._gate_machine = machine
    template = machine.gate_view()["answer_template"]
    submitted = {key: value for key, value in template.items() if key not in {"evidence_refs", "conclusion"}}
    submitted["explanation"] = EXPLANATION
    reply = agent._run_python_tool(state_path, {"code": f"result = virelai('gate_answer', answer={submitted!r})"})
    assert reply.interaction_kind == "GATE_TRANSITION"  # accepted (the reply itself exceeds the tool output cap)

    (row,) = _rows(state_path, "ANSWER")
    assert (row["executor"], row["event"], row["disposition"]) == ("DUCK", "ADMISSION", "ADMITTED")
    assert row["submitted"] == json.loads(json.dumps(submitted)) and "evidence_refs" not in row["submitted"]
    assert row["effective"]["evidence_refs"] == template["evidence_refs"]
    assert row["effective"]["conclusion"] == "PRESUMED_UNREACHABLE"
    sources = row["field_sources"]
    assert sources["explanation"] == "SUBMITTER"
    assert sources["evidence_refs"] == sources["conclusion"] == "CONTROLLER_FILLED"
    assert sources["target_member_id"] == "SUBMITTER_CONFIRMED_BY_CONTROLLER"
    assert row["refs"]["answer_id"] and row["refs"]["subject"] == target["entity_id"]


def test_a_refused_duck_answer_is_recorded_with_its_payload_and_reason(tmp_path):
    agent, state_path = _bridge(tmp_path)
    reply = agent._run_python_tool(state_path, {"code": "result = virelai('gate_answer', answer={'x': 1})"})
    assert reply.interaction_kind == "CONTRACT_REPAIR"
    (row,) = _rows(state_path, "ANSWER")
    assert (row["executor"], row["disposition"], row["gate_id"]) == ("DUCK", "REFUSED", "G0-ACTION-METADATA")
    assert row["submitted"] == {"x": 1} and row["effective"] == {"x": 1}
    assert row["reason"] == {"code": "GATE_CONTRACT", "text": reply.repair_error}
    assert not _path(state_path, "_gate_answers.jsonl").exists()


def test_controller_answers_are_recorded_admitted_and_refused(tmp_path):
    from inference.agent.controller_turn import _controller_answer

    agent, state_path = _bridge(tmp_path)
    machine = agent._ensure_gate_machine(state_path)
    good = {"answer_id": "G0-controller", "semantic_claims": [],
            "action_metadata": [{"action": a.action, "requires_coordinates": a.requires_coordinates}
                                for a in machine.ego.affordances],
            "epistemic_limit": "Action effects remain unknown until they are observed through probes."}
    bad = SimpleNamespace(answer={"answer_id": ""}, refusal_key=("G0", 0, None), reason="bad")
    _controller_answer(agent, state_path, machine, bad, tmp_path / "log.txt")
    _controller_answer(agent, state_path, machine, SimpleNamespace(answer=good, refusal_key=("G0", 0, 1), reason="ok"),
                       tmp_path / "log.txt")
    refused, admitted = _rows(state_path, "ANSWER")
    assert (refused["executor"], refused["disposition"], refused["reason"]["code"]) == (
        "CONTROLLER", "REFUSED", "GATE_CONTRACT")
    assert (admitted["executor"], admitted["disposition"], admitted["refs"]["answer_id"]) == (
        "CONTROLLER", "ADMITTED", "G0-controller")
    assert set(admitted["field_sources"].values()) == {"SUBMITTER"}


# ---- 8, 9 · G3 choices ------------------------------------------------------------------------------------------

def test_admitted_and_refused_g3_choices_are_selection_admissions(tmp_path):
    from inference.framework.library_agenda import gate_agenda
    from test_g3_directed_click import _at

    result, _ = _at("carry_v7", 3)
    agent, state_path = _bridge(tmp_path)
    agent._gate_machine = result.machine
    chosen = gate_agenda(result.machine)["eligible"][1]
    for question in (chosen, "Q:L1:G3-LEVERS:E9999:IS_LEVER"):
        agent._run_python_tool(state_path, {"code": f"result = virelai('next_probe', question_id={question!r})"})
    rows = _rows(state_path, "G3_SELECTION")
    assert [(r["event"], r["disposition"], r["executor"], r["refs"]["question_id"]) for r in rows] == [
        ("ADMISSION", "ADMITTED", "DUCK", chosen), ("ADMISSION", "REFUSED", "DUCK", "Q:L1:G3-LEVERS:E9999:IS_LEVER")]
    assert rows[1]["reason"] == {"code": "G3_EVENT", "text": "the question names no row this G3 roster serves now"}
    assert rows[0]["refs"]["source_event"]["event"] == "ADMITTED" and rows[0]["submitted"] == {"question_id": chosen}


def test_a_g3_choice_refused_before_selection_is_still_recorded(tmp_path):
    """The active gate is not G3: the machine raises before any selection event exists."""
    agent, state_path = _bridge(tmp_path)
    reply = agent._run_python_tool(
        state_path, {"code": "result = virelai('next_probe', question_id='Q:L1:G3-LEVERS:E0001:IS_LEVER')"})
    assert _stdout(reply)["error"].startswith("G3 choice not admissible")
    (row,) = _rows(state_path, "G3_SELECTION")
    assert (row["event"], row["disposition"], row["reason"]["code"]) == ("ADMISSION", "REFUSED", "GATE_CONTRACT")
    assert row["submitted"] == {"question_id": "Q:L1:G3-LEVERS:E0001:IS_LEVER"}


def _live_session(tmp_path: Path, model, *, enabled: bool = True):
    from inference.framework.solver import HarnessSolver, _HarnessGameSession
    from test_g3_directed_click import _Ft09Game

    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True, provenance_enabled=enabled)
    agent._ensure_session = lambda _path: None
    game = _Ft09Game()
    state_path = tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}"
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=agent, game_index=0, pass_index=0, state_path=state_path,
        transcript_path=tmp_path / "t.txt", analysis_html_relpath="a.html", stop_event=threading.Event(),
        viewer_data_path=tmp_path / "v.json")
    agent._chat_completion = lambda messages, **kw: model(agent, session, solver)
    return session, agent, state_path


def test_a_g3_handoff_nobody_takes_is_an_offered_then_not_attempted_opportunity(tmp_path):
    from inference.agent.tool_agent import _ChatCompletionResult

    def model(agent, session, solver):
        agent._yield_seconds = 0.0
        solver.max_actions_per_game = session.action_count + 1
        return _ChatCompletionResult(message={"role": "assistant", "content": "Weighing the rows."})

    session, agent, state_path = _live_session(tmp_path, model)
    session.play()
    rows = _rows(state_path, "G3_SELECTION")
    assert [(r["event"], r["disposition"], r["executor"]) for r in rows] == [
        ("OPPORTUNITY", "OFFERED", "CONTROLLER"), ("OPPORTUNITY", "NOT_ATTEMPTED", "DUCK")]
    assert [r["refs"]["source_event"]["event"] for r in rows] == ["HANDOFF", "COVERAGE_RESUMED"]
    assert _prov().read_journal(_path(state_path, "_provenance.jsonl")).status == "SEALED"


# ---- 10 · notes -------------------------------------------------------------------------------------------------

def test_accepted_and_refused_note_submissions_are_annotation_rows(tmp_path):
    agent, state_path = _bridge(tmp_path)
    good = [{"subject": "WORLD", "kind": "HUNCH", "text": "The top band may count down."}]
    agent._run_python_tool(state_path, {"code": f"result = virelai('annotate', notes={good!r})"})
    agent._run_python_tool(state_path, {"code": "result = virelai('annotate', notes=[])"})
    accepted, refused = _rows(state_path, "ANNOTATION")
    assert (accepted["event"], accepted["disposition"], accepted["executor"]) == ("ADMISSION", "UNCERTIFIED", "DUCK")
    assert accepted["submitted"] == good and accepted["refs"]["note_ids"] == ["N0001"]
    assert (refused["disposition"], refused["reason"]["code"], refused["submitted"]) == (
        "REFUSED", "ANNOTATION_INVALID", [])


# ---- 12, 13, 14 · identity, determinism, integrity --------------------------------------------------------------

def _refuse_twice(tmp_path: Path) -> list[dict]:
    agent, state_path = _bridge(tmp_path)
    for _ in range(2):
        agent._run_python_tool(state_path, {"code": "result = virelai('gate_answer', answer={})"})
    return _rows(state_path, "ANSWER")


def test_repeated_identical_submissions_get_distinct_stable_ids(tmp_path):
    first = _refuse_twice(tmp_path / "a")
    again = _refuse_twice(tmp_path / "b")
    assert [r["submitted"] for r in first] == [{}, {}] and first[0]["at_transition"] == first[1]["at_transition"]
    assert first[0]["seq"] != first[1]["seq"] and first[0]["event_id"] != first[1]["event_id"]
    assert [r["event_id"] for r in first] == [r["event_id"] for r in again]


@pytest.fixture(scope="module")
def controller_twin(tmp_path_factory):
    patch = pytest.MonkeyPatch()
    yield _ControllerRun(tmp_path_factory.mktemp("prov_b"), patch)
    patch.undo()


def test_an_identical_deterministic_replay_writes_a_byte_identical_journal(controller_run, controller_twin):
    first = _path(controller_run.state_path, "_provenance.jsonl").read_bytes()
    second = _path(controller_twin.state_path, "_provenance.jsonl").read_bytes()
    assert first and first == second
    assert b"wall" not in first and str(controller_run.dir).encode() not in first


def _sealed_copy(run, tmp_path: Path) -> Path:
    source = _path(run.state_path, "_provenance.jsonl")
    copy_path = tmp_path / "journal.jsonl"
    copy_path.write_bytes(source.read_bytes())
    journal = _prov().ProvenanceJournal.open(copy_path, run_stem="ft09", game_id="ft09")
    assert journal.seal()
    return copy_path


@pytest.mark.parametrize(("damage", "code"), [
    ("missing", "SEQUENCE_GAP"), ("duplicated", "DUPLICATE_SEQUENCE"), ("reordered", "SEQUENCE_REORDERED"),
    ("modified", "HASH_MISMATCH"), ("truncated", "TRUNCATED_TAIL")])
def test_every_kind_of_journal_damage_is_detected_and_the_verified_prefix_returned(
        controller_run, tmp_path, damage, code):
    path = _sealed_copy(controller_run, tmp_path)
    prov = _prov()
    assert prov.read_journal(path).status == "SEALED"
    lines = path.read_bytes().split(b"\n")[:-1]
    if damage == "missing":
        del lines[3]
    elif damage == "duplicated":
        lines.insert(4, lines[3])
    elif damage == "reordered":
        lines[3], lines[4] = lines[4], lines[3]
    elif damage == "modified":
        row = json.loads(lines[3])
        row["executor"] = "DUCK" if row["executor"] != "DUCK" else "CONTROLLER"
        lines[3] = prov.canonical(row)
    data = b"\n".join(lines) + b"\n"
    if damage == "truncated":
        data = data[: len(data) - len(lines[-1]) // 2 - 1]
    path.write_bytes(data)
    read = prov.read_journal(path)
    assert read.status == "CORRUPT" and read.failure["code"] == code
    verified = {"duplicated": 4, "truncated": len(lines) - 1}.get(damage, 3)
    assert len(read.rows) == verified and read.rows == prov.read_journal(path).rows


def test_a_journal_whose_tail_and_seal_are_lost_reads_open_never_sealed(controller_run, tmp_path):
    path = _sealed_copy(controller_run, tmp_path)
    lines = path.read_bytes().split(b"\n")[:-1]
    path.write_bytes(b"\n".join(lines[:-3]) + b"\n")
    read = _prov().read_journal(path)
    assert read.status == "OPEN" and len(read.rows) == len(lines) - 3


# ---- 15 · pending G3 events at every handled end ----------------------------------------------------------------

PENDING = {"schema": "virelai-g3-selection-event-v1", "event": "HANDOFF", "question_id": None, "entity_id": None,
           "actor": "CONTROLLER", "reason": "a genuine G3 choice was offered to Duck", "phase": "CLICK", "level": 1,
           "life": 1, "at_transition": 0, "gate_revision": 0}


@pytest.mark.parametrize("ending", ["planned_stop", "controlled_stop", "budget_stop", "crash"])
def test_a_pending_g3_event_survives_every_handled_end(tmp_path, ending):
    from inference.agent.tool_agent import AnalyzerTurnResult

    def turn(agent, session, solver, state_path):
        machine = agent._ensure_gate_machine(state_path)
        machine.g3_selection_events.append(dict(PENDING))  # noted, never flushed by a probe or a turn
        if ending == "crash":
            raise RuntimeError("boom")
        if ending == "budget_stop":
            solver.max_actions_per_game = 0
            return AnalyzerTurnResult(step_executed=False, yielded_control=True)
        return AnalyzerTurnResult(step_executed=False, **{ending: "test end"})

    session, agent, state_path = _live_session(tmp_path, lambda *a: None)
    agent._current_valid_actions = ["ACTION6"]
    agent.analyze = lambda *args, **kwargs: turn(agent, session, session.solver, state_path)
    session.play()
    events = [json.loads(line) for line in _path(state_path, "_g3_selection_events.jsonl").read_text().splitlines()]
    assert events == [PENDING]
    read = _prov().read_journal(_path(state_path, "_provenance.jsonl"))
    assert read.status == "SEALED"
    assert [(r["operation"], r["event"], r["disposition"]) for r in read.rows] == [
        ("G3_SELECTION", "OPPORTUNITY", "OFFERED")]


# ---- 16 · the lifecycle actor -----------------------------------------------------------------------------------

@pytest.mark.parametrize("executor", ["CONTROLLER", "DUCK"])
def test_a_reachability_release_records_its_real_executor(tmp_path, executor):
    from inference.agent.controller_turn import _controller_answer

    agent, state_path = _bridge(tmp_path)
    machine, adapter, target = _reachability_machine()
    agent._gate_machine = machine
    answer = {**machine.gate_view()["answer_template"], "explanation": EXPLANATION}
    if executor == "CONTROLLER":
        _controller_answer(agent, state_path, machine, SimpleNamespace(
            answer=answer, refusal_key=("G3", 0, None), reason="semantic reuse"), tmp_path / "log.txt")
    else:
        agent._run_python_tool(state_path, {"code": f"result = virelai('gate_answer', answer={answer!r})"})
    events = adapter.lifecycle_journal.entities[target["entity_id"]].events
    assert events[-1].to_state == "PRESUMED_UNREACHABLE" and events[-1].actor == executor
    (row,) = _rows(state_path, "ANSWER")
    assert (row["executor"], row["disposition"]) == (executor, "ADMITTED")


# ---- 17, 18 · failure and the disabled path --------------------------------------------------------------------

@pytest.fixture(scope="module")
def failing_run(tmp_path_factory):
    patch = pytest.MonkeyPatch()
    from inference.framework import audit_journal

    def broken(self, row):
        raise OSError("disk full")

    patch.setattr(audit_journal.ProvenanceJournal, "_write", broken)
    try:
        run = _ControllerRun(tmp_path_factory.mktemp("prov_fail"), patch)
    finally:
        patch.undo()  # the broken writer must not leak into later tests in this module
    yield run


def test_a_journal_write_failure_changes_no_action_and_stops_nothing(controller_run, failing_run):
    assert failing_run.run.env_calls == controller_run.run.env_calls
    assert failing_run.agent._provenance.failed == "OSError: disk full"
    assert not _path(failing_run.state_path, "_provenance.jsonl").exists()


def test_a_journal_write_failure_is_a_structured_observer_warning(tmp_path, monkeypatch):
    from inference.agent.tool_agent import AnalyzerTurnResult
    from inference.framework import audit_journal

    monkeypatch.setattr(audit_journal.ProvenanceJournal, "_write",
                        lambda self, row: (_ for _ in ()).throw(OSError("disk full")))
    session, agent, state_path = _live_session(tmp_path, lambda *a: None)
    agent._current_valid_actions = ["ACTION6"]

    def turn(*_args, **_kwargs):
        agent._ensure_gate_machine(state_path).g3_selection_events.append(dict(PENDING))
        return AnalyzerTurnResult(step_executed=False, planned_stop="test end")

    agent.analyze = turn
    session.play()
    folder = tmp_path / "virelai" / session.solver._run_stem("fixture", 0)
    warnings = [json.loads(line) for line in (folder / "observer_warnings.jsonl").read_text().splitlines()]
    assert [w["detail"] for w in warnings if w["event"] == "PROVENANCE_WRITE_FAILED"] == ["OSError: disk full"]


@pytest.fixture(scope="module")
def disabled_run(tmp_path_factory):
    patch = pytest.MonkeyPatch()
    yield _ControllerRun(tmp_path_factory.mktemp("prov_off"), patch, enabled=False)
    patch.undo()


def test_with_capture_disabled_nothing_is_journaled_and_every_other_artifact_is_identical(controller_run, disabled_run):
    assert disabled_run.run.env_calls == controller_run.run.env_calls
    assert not _path(disabled_run.state_path, "_provenance.jsonl").exists()
    for suffix in ("_gate_answers.jsonl", "_gate_events.jsonl", "_probe_outcomes.jsonl",
                   "_probe_frames.jsonl", "_g3_target_ledger.json", "_g3_selection_events.jsonl"):
        off, on = _path(disabled_run.state_path, suffix), _path(controller_run.state_path, suffix)
        assert off.exists() == on.exists(), suffix
        assert not on.exists() or off.read_bytes() == on.read_bytes(), suffix
    # envelopes carry the capability token, an HMAC under a per-game random secret: equal apart from it
    envelopes = [[{k: v for k, v in json.loads(line).items() if k != "probe_token"}
                  for line in _path(run.state_path, "_probe_envelopes.jsonl").read_text().splitlines()]
                 for run in (disabled_run, controller_run)]
    assert envelopes[0] == envelopes[1]
    strip = lambda rows: [{k: v for k, v in r.items() if k != "wall_seconds"} for r in rows]  # noqa: E731
    ledgers = [strip(json.loads(line) for line in _path(run.state_path, "_turn_ledger.jsonl").read_text().splitlines())
               for run in (disabled_run, controller_run)]
    assert ledgers[0] == ledgers[1]


# =================================================================================================================
# WO-PE-01 revision 2 (Sol's review, 2026-10-14): fail-first against revision 1.
# R2-J · executions join to their exact admission · R2-S · the reader validates the whole row contract ·
# R2-O · provenance is sealed only after final G3 handling.
# Forged journals are built here, from the published row formula, so the reader is tested independently of the
# writer.
# =================================================================================================================

import hashlib  # noqa: E402

R2_SCHEMA = "virelai-provenance-v1"
R2_RUN = {"run_stem": "fixture_p0", "game_id": "fixture"}
R2_REF_KEYS = ("question_id", "subject", "probe_id", "answer_id", "evidence_id", "executed_transition", "note_ids",
               "source_event", "admission_event_id")
R2_BODY_KEYS = ("level", "life", "gate_id", "at_transition", "executor", "operation", "event", "disposition",
                "submitted", "effective", "field_sources", "refs", "reason")


def _r2_sha(value) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
    return hashlib.sha256(raw.encode("ascii")).hexdigest()


def _r2_content(operation: str, event: str, disposition: str, *, executor: str = "CONTROLLER", level: int = 1,
                life: int = 1, gate: str = "G1-EGO", reason: dict | None = None, **refs) -> dict:
    return {"level": level, "life": life, "gate_id": gate, "at_transition": 0, "executor": executor,
            "operation": operation, "event": event, "disposition": disposition, "submitted": None, "effective": None,
            "field_sources": None, "refs": {key: refs.get(key) for key in R2_REF_KEYS}, "reason": reason}


def _r2_forge(path: Path, contents: list[dict], *, seal: bool = True, edit=None, seal_edit=None) -> list[dict]:
    """Write a hash-consistent journal: every id and hash recomputed after any ``edit``."""
    rows, head = [], "0" * 64
    for seq, content in enumerate(contents, start=1):
        run = content.pop("_run", R2_RUN)
        body = {key: content[key] for key in R2_BODY_KEYS}
        row = {"schema": R2_SCHEMA, "record": "EVENT", "seq": seq, "run": run, **body,
               "event_id": "PV-" + _r2_sha({"run": run, "seq": seq, "content": body})[:16],
               "previous_event_hash": head}
        if edit is not None:
            edit(seq, row)
        row["event_hash"] = _r2_sha({k: v for k, v in row.items() if k != "event_hash"})
        rows.append(row)
        head = row["event_hash"]
    lines = [row for row in rows]
    if seal:
        sealed = {"schema": R2_SCHEMA, "record": "SEAL", "seq": len(rows) + 1, "run": R2_RUN,
                  "previous_event_hash": head, "event_count": len(rows), "head_hash": head}  # revision 3: the run
        if seal_edit is not None:
            seal_edit(sealed)
        sealed["event_hash"] = _r2_sha({k: v for k, v in sealed.items() if k != "event_hash"})
        lines.append(sealed)
    path.write_bytes(b"".join(
        json.dumps(r, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode() + b"\n" for r in lines))
    return rows


def _r2_event_id(seq: int, content: dict, run: dict = R2_RUN) -> str:
    return "PV-" + _r2_sha({"run": run, "seq": seq, "content": {k: content[k] for k in R2_BODY_KEYS}})[:16]


def _r2_admission(life: int, probe: str = "P-0007") -> dict:
    return _r2_content("PROBE", "ADMISSION", "ADMITTED", life=life, probe_id=probe)


def _r2_execution(life: int, admission_event_id, probe: str = "P-0007", *, executed: bool = True) -> dict:
    if executed:
        return _r2_content("PROBE", "EXECUTION", "EXECUTED", life=life, probe_id=probe, evidence_id=f"E-{life}",
                           executed_transition=life, admission_event_id=admission_event_id)
    return _r2_content("PROBE", "EXECUTION", "NOT_ATTEMPTED", life=life, probe_id=probe,
                       admission_event_id=admission_event_id,
                       reason={"code": "NOT_EXECUTED", "text": "the environment did not execute the action"})


# ---- R2-J · executions join to the exact admission -------------------------------------------------------------

def test_r2_one_probe_id_admitted_in_two_lives_joins_each_execution_to_its_own_admission(tmp_path):
    first = _r2_admission(1)
    first_id = _r2_event_id(1, first)
    second = _r2_admission(2)
    second_id = _r2_event_id(3, second)
    contents = [first, _r2_execution(1, first_id), second, _r2_execution(2, second_id)]
    rows = _r2_forge(tmp_path / "j.jsonl", [dict(c) for c in contents])
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "SEALED", read.failure
    assert read.joins == {rows[1]["event_id"]: first_id, rows[3]["event_id"]: second_id}


def test_r2_an_execution_pointing_at_the_older_admission_is_a_mismatch(tmp_path):
    older = _r2_admission(1)  # admitted in life 1, never executed
    older_id = _r2_event_id(1, older)
    contents = [older, _r2_admission(2), _r2_execution(2, older_id)]
    _r2_forge(tmp_path / "j.jsonl", contents)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "ADMISSION_MISMATCH" and read.failure["line"] == 3
    assert len(read.rows) == 2


def test_r2_an_execution_with_no_admission_reference_is_missing_its_admission(tmp_path):
    contents = [_r2_admission(1), _r2_execution(1, None)]
    _r2_forge(tmp_path / "j.jsonl", contents)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "ADMISSION_MISSING" and len(read.rows) == 1


def test_r2_two_executions_cannot_consume_one_admission(tmp_path):
    admission = _r2_admission(1)
    admission_id = _r2_event_id(1, admission)
    contents = [admission, _r2_execution(1, admission_id), _r2_execution(1, admission_id)]
    _r2_forge(tmp_path / "j.jsonl", contents)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "ADMISSION_ALREADY_CONSUMED"
    assert len(read.rows) == 2


def test_r2_a_not_attempted_execution_is_joined_to_its_exact_admission(tmp_path):
    """Captured: Duck's admitted probe that the environment does not execute."""
    from test_gated_python_bridge import _capability

    agent, state_path = _bridge(tmp_path)
    agent._step_env_callback = lambda payload: {"executed": False, "error": "the environment refused the step"}
    capability = _capability(agent, state_path)
    code = f"action({capability['actions']!r}, decision={{'probe_token': {capability['probe_token']!r}}})"
    agent._run_python_tool(state_path, {"code": code})
    admission, execution = _rows(state_path, "PROBE")
    assert (admission["disposition"], execution["event"], execution["disposition"]) == (
        "ADMITTED", "EXECUTION", "NOT_ATTEMPTED")
    assert execution["refs"]["admission_event_id"] == admission["event_id"]
    for key in ("level", "life", "gate_id", "executor"):
        assert execution[key] == admission[key], key
    read = _prov().read_journal(_path(state_path, "_provenance.jsonl"))
    assert read.joins == {execution["event_id"]: admission["event_id"]}


def test_r2_every_captured_execution_names_its_own_admission(tmp_path, controller_run):
    from test_gated_python_bridge import _capability

    agent, state_path = _bridge(tmp_path)
    agent._step_env_callback = lambda payload: dict(STEP_PAYLOAD)
    capability = _capability(agent, state_path)
    code = f"action({capability['actions']!r}, decision={{'probe_token': {capability['probe_token']!r}}})"
    agent._run_python_tool(state_path, {"code": code})
    for path in (state_path, controller_run.state_path):
        latest, joined = None, 0
        for row in _rows(path, "PROBE"):
            if row["event"] == "ADMISSION":
                latest = row
                continue
            assert row["refs"]["admission_event_id"] == latest["event_id"]
            joined += 1
        assert joined and len(_prov().read_journal(_path(path, "_provenance.jsonl")).joins) == joined


# ---- R2-S · the reader validates the whole row contract ---------------------------------------------------------

def test_r2_a_forged_event_id_is_detected_even_with_every_hash_recomputed(tmp_path):
    def forge(seq, row):
        if seq == 2:
            row["event_id"] = "PV-" + "0" * 16

    admission = _r2_admission(1)
    _r2_forge(tmp_path / "j.jsonl", [admission, _r2_execution(1, _r2_event_id(1, admission))], edit=forge)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "EVENT_ID_MISMATCH" and len(read.rows) == 1


def test_r2_a_different_run_mid_journal_is_detected(tmp_path):
    intruder = {**_r2_content("ANSWER", "ADMISSION", "ADMITTED", answer_id="A-1"), "field_sources": {},
                "_run": {"run_stem": "other_p0", "game_id": "other"}}
    contents = [_r2_admission(1), intruder]
    _r2_forge(tmp_path / "j.jsonl", contents)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "RUN_MISMATCH" and len(read.rows) == 1


def test_r2_an_event_whose_record_is_not_event_is_schema_invalid(tmp_path):
    def forge(seq, row):
        if seq == 1:
            row["record"] = "NOTE"

    _r2_forge(tmp_path / "j.jsonl", [_r2_admission(1)], edit=forge)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "SCHEMA_INVALID" and read.rows == []
    assert "record" in read.failure["detail"]


def test_r2_a_seal_with_the_wrong_schema_is_rejected_even_with_its_hash_recomputed(tmp_path):
    def forge(seal):
        seal["schema"] = "virelai-provenance-v0"

    _r2_forge(tmp_path / "j.jsonl", [_r2_admission(1)], seal_edit=forge)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "SCHEMA_INVALID" and len(read.rows) == 1


@pytest.mark.parametrize("bad", [object(), {1, 2}, {1: "integer key"}], ids=["object", "set", "integer-key"])
def test_r2_an_unsupported_submitted_object_fails_the_journal_and_is_never_stringified(tmp_path, bad):
    prov = _prov()
    with pytest.raises((TypeError, ValueError)):
        prov.canonical({"submitted": bad})
    journal = prov.ProvenanceJournal.open(tmp_path / "j.jsonl", run_stem="fixture_p0", game_id="fixture")
    content = {**_r2_content("ANSWER", "ADMISSION", "REFUSED", reason={"code": "GATE_CONTRACT", "text": "no"}),
               "submitted": {"payload": bad}, "field_sources": {}}
    assert journal.append(content) is None
    assert journal.failed and not (tmp_path / "j.jsonl").exists()


def test_r2_a_nonfinite_submitted_value_fails_open_and_reports_later(tmp_path):
    from inference.agent.provenance_capture import close_session

    code = "result = virelai('annotate', notes=[{'subject': 'WORLD', 'kind': 'HUNCH', 'text': float('nan')}])"
    replies = []
    for enabled in (True, False):
        agent, state_path = _bridge(tmp_path / str(enabled), enabled=enabled)
        replies.append(agent._run_python_tool(state_path, {"code": code}).content)
        if enabled:
            on_agent, on_state = agent, state_path
    assert replies[0] == replies[1]  # the game sees exactly what it saw without capture
    assert on_agent._provenance.failed.startswith("ValueError")
    journal_path = _path(on_state, "_provenance.jsonl")
    assert not journal_path.exists() or b"NaN" not in journal_path.read_bytes()
    assert [event for event, _detail in close_session(on_agent, on_state)] == ["PROVENANCE_WRITE_FAILED"]


# ---- R2-O · finalization order ----------------------------------------------------------------------------------

def test_r2_an_event_made_during_final_g3_handling_is_journaled_before_the_seal(tmp_path):
    from inference.agent.tool_agent import AnalyzerTurnResult

    final = {**PENDING, "event": "COVERAGE_RESUMED", "reason": "made while the open G3 outcome was recorded"}
    session, agent, state_path = _live_session(tmp_path, lambda *a: None)
    agent._current_valid_actions = ["ACTION6"]
    agent.analyze = lambda *args, **kwargs: (agent._ensure_gate_machine(state_path),
                                              AnalyzerTurnResult(step_executed=False, planned_stop="end"))[1]
    calls = []

    def traced(name, original, side_effect=None):
        def call(*args, **kwargs):
            calls.append(name)
            if side_effect is not None:
                side_effect()
            return original(*args, **kwargs)
        return call

    session._record_open_g3_outcome = traced(
        "record_open_g3_outcome", session._record_open_g3_outcome,
        lambda: agent._gate_machine.g3_selection_events.append(dict(final)))
    session._close_provenance = traced("seal_provenance", session._close_provenance)
    session._finish_if_needed = traced("finish_if_needed", session._finish_if_needed)
    session._write_l2a_world_model = traced("write_final_model", session._write_l2a_world_model)
    session.play()
    assert calls == ["record_open_g3_outcome", "seal_provenance", "finish_if_needed", "write_final_model"]
    read = _prov().read_journal(_path(state_path, "_provenance.jsonl"))
    assert read.status == "SEALED"
    assert [(r["event"], r["disposition"], r["refs"]["source_event"]["event"]) for r in read.rows] == [
        ("OPPORTUNITY", "NOT_ATTEMPTED", "COVERAGE_RESUMED")]


# =================================================================================================================
# WO-PE-01 revision 3 (Sol's final amendment, 2026-10-14): the seal names its run. Fail-first against revision 2.
# =================================================================================================================

R3_RUN = {"run_stem": "fixture_p0", "game_id": "fixture"}


def _r3_open(path: Path, run: dict = R3_RUN):
    return _prov().ProvenanceJournal.open(path, run_stem=run["run_stem"], game_id=run["game_id"])


def test_r3_an_empty_sealed_journal_names_its_run_and_reads_sealed(tmp_path):
    journal = _r3_open(tmp_path / "j.jsonl")
    assert journal.seal()
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "SEALED" and read.rows == [] and read.failure is None
    assert read.seal.get("run") == R3_RUN  # an empty journal's identity comes from its seal
    assert getattr(read, "run", None) == R3_RUN


def test_r3_an_open_journal_cannot_be_reopened_as_another_run_even_with_no_new_event(tmp_path):
    path = tmp_path / "j.jsonl"
    first = _r3_open(path)
    assert first.append(_r2_admission(1)) is not None  # one event, never sealed: the journal is OPEN
    before = path.read_bytes()
    intruder = _r3_open(path, {"run_stem": "other_p0", "game_id": "other"})
    assert intruder.failed and "run" in intruder.failed  # failed at open, before any event is offered
    assert intruder.seal() is False and path.read_bytes() == before
    assert _prov().read_journal(path).status == "OPEN"
    same = _r3_open(path)  # the journal's own run may still continue and seal it
    assert not same.failed and same.seal() and _prov().read_journal(path).status == "SEALED"


def test_r3_a_seal_carrying_a_different_run_is_rejected_with_its_hash_recomputed(tmp_path):
    def forge(seal):
        seal["run"] = {"run_stem": "other_p0", "game_id": "other"}

    _r2_forge(tmp_path / "j.jsonl", [_r2_admission(1)], seal_edit=forge)
    read = _prov().read_journal(tmp_path / "j.jsonl")
    assert read.status == "CORRUPT" and read.failure["code"] == "RUN_MISMATCH" and len(read.rows) == 1


def test_r3_identical_empty_runs_write_byte_identical_seals_that_carry_the_run(tmp_path):
    seals = []
    for name, run in (("a", R3_RUN), ("b", R3_RUN), ("c", {"run_stem": "other_p0", "game_id": "other"})):
        journal = _r3_open(tmp_path / name / "j.jsonl", run)
        assert journal.seal()
        seals.append((tmp_path / name / "j.jsonl").read_bytes())
    assert seals[0] == seals[1]
    assert b'"run":{"game_id":"fixture","run_stem":"fixture_p0"}' in seals[0]
    assert seals[2] != seals[0]  # the seal hash covers the run


def test_r3_the_seal_writer_runs_the_full_seal_validator_before_writing(tmp_path, monkeypatch):
    prov = _prov()
    calls = []
    original = prov._Chain.check_seal

    def spy(self, row):
        calls.append(("check_seal", dict(row)))
        return original(self, row)

    def write(self, row):
        calls.append(("write", row.get("record")))
        return writer(self, row)

    writer = prov.ProvenanceJournal._write
    monkeypatch.setattr(prov._Chain, "check_seal", spy)
    monkeypatch.setattr(prov.ProvenanceJournal, "_write", write)
    journal = _r3_open(tmp_path / "good.jsonl")
    assert journal.seal()
    assert [name for name, _ in calls] == ["check_seal", "write"] and calls[0][1]["record"] == "SEAL"
    calls.clear()
    broken = _r3_open(tmp_path / "bad.jsonl", {"run_stem": "", "game_id": "fixture"})  # an invalid run identity
    assert broken.seal() is False and broken.failed and not (tmp_path / "bad.jsonl").exists()
    assert [name for name, _ in calls] == ["check_seal"]
