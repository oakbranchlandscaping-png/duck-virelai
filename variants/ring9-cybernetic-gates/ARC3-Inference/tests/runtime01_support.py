"""Shared fixtures for the WO-RUNTIME-01 tests: scripted models, a guarded agent, and the ft09 world in normal play.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Interface: ``INTERFACE_WO_RUNTIME_01_v3_2026-10-20``
and ``IMPLEMENTATION_INTERFACE_WO_RUNTIME_01_v1/v2``. Nothing here is production code; the tests drive the production
``ToolAgent``, controller turn and gate machine exactly as ``solver.play`` does.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Sequence

from ft09_world import Ft09World
from inference.agent.runtime_state import RUNTIME_STATE_FILENAME, Frame, HistoryEntry, write_runtime_state
from inference.agent.tool_agent import ToolAgent, _ChatCompletionResult, _ToolDispatchResult

FIXTURES = Path(__file__).parent / "fixtures"
STOP_CALLS = FIXTURES / "runtime01_public_stop_calls.json"
TOOL = [{"type": "function", "function": {"name": "python", "description": "fixture",
                                         "parameters": {"type": "object", "properties": {}}}}]


def tool_call(code: str, index: int) -> _ChatCompletionResult:
    return _ChatCompletionResult(
        message={"role": "assistant", "content": None, "tool_calls": [{
            "id": f"call-{index}", "type": "function",
            "function": {"name": "python", "arguments": json.dumps({"code": code})}}]},
        finish_reason="tool_calls", model_id="fixture-model")


def prose(index: int) -> _ChatCompletionResult:
    return _ChatCompletionResult(message={"role": "assistant", "content": f"thinking {index}"},
                                 finish_reason="stop", model_id="fixture-model")


class Script:
    """A scripted model: each request returns the next item (a code string, a result, or an exception)."""

    def __init__(self, items: Sequence[Any]) -> None:
        self.items = list(items)
        self.requests: list[list[dict]] = []
        self.kwargs: list[dict] = []

    def __call__(self, messages, **kwargs):
        self.requests.append(json.loads(json.dumps(messages, default=str)))
        self.kwargs.append(dict(kwargs))
        item = self.items[min(len(self.requests) - 1, len(self.items) - 1)]
        if isinstance(item, BaseException):
            raise item
        if callable(item) and not isinstance(item, str):
            return item(len(self.requests) - 1)
        if isinstance(item, _ChatCompletionResult):
            return item
        return tool_call(str(item), len(self.requests) - 1)

    def user_texts(self, request: int = -1) -> list[str]:
        return [str(m.get("content")) for m in self.requests[request] if m.get("role") == "user"]


def guarded_agent(tmp_path: Path, monkeypatch, script: Script, *, dispatch: Callable | None = None,
                  provenance: bool = False) -> tuple[ToolAgent, Path]:
    """The production agent with the card, controller and network replaced by fixtures (the circuit-breaker
    pattern of ``test_tool_agent_no_tool_circuit_breaker``); the turn's own loop, guards and settlement are real."""
    state_path = tmp_path / f"tool_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(state_path, current_frame=Frame(grid=((0, 0), (0, 0)), step=0, level=1), history=[])
    agent = ToolAgent(model="fixture-model", provider="openai", base_url="https://fixture.invalid/v1",
                      api_key="fixture", virelai_gates_enabled=True, provenance_enabled=provenance)
    monkeypatch.setattr(agent, "_ensure_session", lambda _path: None)
    monkeypatch.setattr(agent, "_tools", lambda _path: TOOL)
    monkeypatch.setattr(agent, "_automatic_virelai_update", lambda *args, **kwargs: "")
    monkeypatch.setattr(agent, "_controller_focus_update", lambda: "")
    monkeypatch.setattr(agent, "_gate_context_update", lambda _path: "GATE CARD expand: virelai('library')")
    monkeypatch.setattr(agent, "_build_user_prompt", lambda *args, **kwargs: "probe")
    monkeypatch.setattr(agent, "_build_user_message", lambda prompt, _frame: {"role": "user", "content": prompt})
    monkeypatch.setattr(agent, "_controller_no_legal_move", lambda _path: "")
    monkeypatch.setattr(agent, "_ensure_gate_machine", lambda _path: None)
    monkeypatch.setattr(agent, "_chat_completion", script)
    if dispatch is not None:
        monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    return agent, state_path


def read_only(_path, _name, _arguments) -> _ToolDispatchResult:
    return _ToolDispatchResult('{"returncode": 0, "stdout": "observed"}')


def refused(code: str, text: str) -> Callable:
    def dispatch(_path, _name, _arguments) -> _ToolDispatchResult:
        return _ToolDispatchResult(json.dumps({"error": f"RuntimeError: {text}"}), interaction_kind="ACTION_REFUSED",
                                   repair_signature=code, repair_error=text)
    return dispatch


def ledger_rows(state_path: Path) -> list[dict]:
    path = state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_turn_ledger.jsonl"))
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def journal_rows(state_path: Path) -> list[dict]:
    path = state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_provenance.jsonl"))
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


class PlayRun:
    """The production agent on the ft09 world, driven the way ``solver.play`` drives it (``test_memory_m2``'s Run),
    with a scripted model. ``to_play`` carries the level to normal play the way the base's D-3 rest did, so a
    reproduction starts from the exported stops' state: the ladder rested and Duck owning a FREE_PLAY turn."""

    def __init__(self, tmp_path: Path, monkeypatch, script: Script, *, provenance: bool = True) -> None:
        self.world = Ft09World()
        self.state_path = tmp_path / f"ft09_{RUNTIME_STATE_FILENAME}"
        self.history: list[HistoryEntry] = []
        self.env_calls: list[dict] = []
        self.script = script
        write_runtime_state(self.state_path, current_frame=self._frame(), history=[])
        self.agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                               controller_executor_enabled=True, provenance_enabled=provenance)
        monkeypatch.setattr(self.agent, "_ensure_session", lambda _path: None)
        monkeypatch.setattr(self.agent, "_chat_completion", script)
        self.agent._controller.g3_choice_handoff = False

    def _frame(self) -> Frame:
        return Frame(grid=tuple(tuple(row) for row in self.world.grid), step=self.world.transition_id, level=1)

    def step_env(self, payload: dict) -> dict:
        self.env_calls.append(payload)
        outcome = self.world.step(payload["actions"][0])
        self.history.append(HistoryEntry(action="ACTION6", frame=self._frame()))
        write_runtime_state(self.state_path, current_frame=self._frame(), history=self.history)
        return {"executed": True, "action_num": self.world.transition_id, "transition_id": self.world.transition_id,
                "level": 1, "state": "NOT_FINISHED", "valid_actions": ["ACTION6"],
                "board_changed": bool(outcome["changed_cells"]), "done": False, "level_completed": False,
                "game_over": False}

    def turn(self):
        return self.agent.analyze(self.state_path, self.world.transition_id, valid_actions=["ACTION6"],
                                  step_env=self.step_env, analysis_step=self.world.transition_id + 1)

    def until_duck(self, limit: int = 400) -> int:
        turns = 0
        while not self.script.requests and turns < limit:
            self.turn()
            turns += 1
        return turns

    def to_play(self) -> None:
        """Run the controller to its first Duck-owned step (no model call), then rest the level in normal play: the
        base's D-3 state at every public stop."""
        from inference.agent.controller_turn import run_controller_turn
        from inference.framework.play_gate import rest_in_play

        log = self.state_path.with_name(f"{self.state_path.stem}_analyzer.txt")
        while True:
            self.agent._current_valid_actions = ["ACTION6"]
            self.agent._ensure_gate_machine(self.state_path)
            self.agent._step_env_callback = self.step_env
            if run_controller_turn(self.agent, self.state_path, self.world.transition_id, None, log) is None:
                break
        self.agent._controller.handoff = ""
        machine = self.agent._gate_machine
        machine.annotations.oriented = True  # scripted state: Duck's orientation turn is behind it, as in the stops
        rest_in_play(machine, "scripted state: the level rested in normal play (D-3)")

    def _duck_owned(self) -> bool:
        from inference.framework.controller_executor import DUCK, next_owned_step

        return next_owned_step(self.agent._gate_machine).owner == DUCK

    def live_token(self) -> str:
        capability = self.agent._gate_machine.next_probe_capability() or {}
        return str(capability.get("probe_token") or "")

    def rows(self, suffix: str) -> list[dict]:
        path = self.state_path.with_name(self.state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", suffix))
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


VC33 = "tests/fixtures/vc33_kaggle_carry_v7_record.json.gz"


def drive_to(stop_gate: str, path: str = VC33) -> Any:
    """The saved record as live (``test_r9_r24``'s driver), stopping the moment ``stop_gate`` opens, before its own
    answers: the controller and the recorded answers carry every earlier gate."""
    from inference.framework.controller_executor import next_owned_step
    from inference.framework.record_replay import (_answer_index, click_world_machine, decode_grid, load_record,
                                                   lossless_outcome, merge_recorded_answer, record_like_live,
                                                   record_protocol)

    record = load_record(path)
    grid = decode_grid(record["initial_grid"])
    machine = click_world_machine(grid, record["valid_actions"], **record_protocol(record))
    pending: dict[str, list] = {}
    for answer in record["answers"]:
        pending.setdefault(answer["gate_id"], []).append(answer)

    def answers() -> None:
        while machine.gate_id != stop_gate:
            owned = next_owned_step(machine)
            if owned.owner == "CONTROLLER" and owned.kind == "ANSWER":
                machine.submit_answer(json.loads(json.dumps(owned.answer)))
                continue
            view = machine.gate_view()
            template, queue = view.get("answer_template") or {}, pending.get(machine.gate_id) or []
            due = view.get("status") == "ANSWER_REQUIRED" or view.get("next_operation") == "SUBMIT_GATE_ANSWER"
            ready = template.get("entity_id") and any(item.get("entity_id") == template["entity_id"] for item in queue)
            if template and (ready or (due and owned.owner == "DUCK" and queue)):
                machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
                continue
            return

    for step in record["steps"]:
        answers()
        if machine.gate_id == stop_gate:
            return machine
        capability = machine.next_probe_capability()
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
        grid, outcome = lossless_outcome(grid, step["transition_id"], step["action"], step["changed"], step.get("boundary"))
        record_like_live(machine, probe, outcome, record["valid_actions"])
    raise AssertionError(f"the record never opens {stop_gate}")


def controller_answers(machine: Any, gate: str) -> int:
    """Let the controller answer ``gate`` as far as it can (G4.1's anatomy is controller work)."""
    from inference.framework.controller_executor import next_owned_step

    count = 0
    while machine.gate_id == gate:
        owned = next_owned_step(machine)
        if not (owned.owner == "CONTROLLER" and owned.kind == "ANSWER"):
            break
        machine.submit_answer(json.loads(json.dumps(owned.answer)))
        count += 1
    return count


# ---- WO-RUNTIME-01 revision 3: the scheduling trace revision 2 fixed (``runtime01_r2_scheduling_trace.json``) -------

def scheduling_trace(machine: Any) -> dict[str, Any]:
    """What the scheduler decides now, with no capability token (tokens are per-session secrets): the gate, the
    agenda's selected question and every G4 chapter's disposition, the controller's next step and action, and the
    G4.2 lever order, pending set and statuses."""
    from inference.framework import library_agenda
    from inference.framework.controller_executor import next_owned_step

    agenda = library_agenda.gate_agenda(machine)
    step = next_owned_step(machine)
    study = machine._adapters.get("G4.2-LEVER-ORBITS")
    seeded = study is not None and bool(study._ordered_entities)
    return {"gate": machine.gate_id, "selected": agenda["selected"], "eligible": agenda["eligible"],
            "g4": {q["id"]: q["disposition"] for q in agenda["questions"]
                   if q["gate"] in ("G4-REACTIONS", "G4.2-LEVER-ORBITS")},
            "step": {"owner": step.owner, "kind": step.kind, "gate": step.gate_id, "reason": step.reason,
                     "action": json.loads(json.dumps(step.action, sort_keys=True, default=str)),
                     "answer": json.loads(json.dumps(step.answer, sort_keys=True, default=str))},
            "g42": None if not seeded else {"order": list(study._ordered_entities), "pending": list(study._pending()),
                                            "status": {e: study._lever_status(e) for e in study._ordered_entities}}}


def scheduling_scenarios() -> dict[str, list[dict[str, Any]]]:
    """The revision-2 closure scenarios, traced at every step (the same calls in revisions 2 and 3)."""
    from inference.agent import recovery_consume
    from inference.agent.tool_agent import ToolAgent
    from inference.framework import gate_closure
    from inference.framework.record_replay import load_record, replay

    def agent(machine):
        found = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                          controller_executor_enabled=True)
        found._gate_machine = machine
        return found

    def at(steps):
        machine = replay(load_record(VC33), max_steps=steps, measure=False).machine
        machine.annotations.oriented = True
        return machine

    out: dict[str, list[dict[str, Any]]] = {}
    machine = drive_to("G4-REACTIONS")
    trace = [scheduling_trace(machine)]
    gate_closure.close_question(machine, "Q:L1:G4-REACTIONS:E0004:EFFECTS", "HARD_BUDGET_SPENT", ["E-1", "E-2"])
    trace.append(scheduling_trace(machine))
    controller_answers(machine, "G4-REACTIONS")
    machine.annotations.oriented = True
    trace.append(scheduling_trace(machine))
    out["g41_close_then_continue"] = trace
    machine = at(20)
    trace = [scheduling_trace(machine)]
    gate_closure.close_question(machine, "Q:L1:G4.2-LEVER-ORBITS:E0004:ORBIT", "HARD_BUDGET_SPENT", ["E-1", "E-2"])
    trace.append(scheduling_trace(machine))
    out["g42_close_awaiting"] = trace
    machine = at(24)
    gate_closure.close_question(machine, "Q:L1:G4.2-LEVER-ORBITS:E0005:ORBIT", "CLOCK_BUDGET_SPENT", ["E-1"])
    out["g42_close_last_then_g4b"] = [scheduling_trace(machine)]
    machine = at(20)
    found = agent(machine)
    real = machine.legal_move_status
    machine.legal_move_status = lambda: {**real(), "legal": False, "reason": "scripted dead end"}
    recovery_consume.no_legal_move(found, None, machine)
    recovery_consume.no_legal_move(found, None, machine)
    machine.legal_move_status = real
    out["d22_g42"] = [scheduling_trace(machine)]
    machine = replay(load_record(VC33), max_steps=8, measure=False).machine
    found = agent(machine)
    found._controller.stalled = 3
    recovery_consume.stalled(found, None, machine)
    out["d2_g3"] = [scheduling_trace(machine)]
    return out
