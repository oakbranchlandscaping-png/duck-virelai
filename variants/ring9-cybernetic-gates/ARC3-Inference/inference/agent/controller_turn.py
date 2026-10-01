"""The controller's turn: execute a computable step without calling the model (memory law M8).

Author: Claude (Alpha build seat), 2026-09-29. R9-R08 (DESIGN_VIRELAI_MEMORY_v2 §5.5, stage M-2).

``ToolAgent.analyze`` calls ``run_controller_turn`` before it builds a prompt. When the gate machine
says the controller owns the step (``controller_executor.next_owned_step``), this module takes it:
gate answers rendered from certified state, then **exactly one** bound action through the same
recording path Duck's actions use (``_gate_probe_begin`` / ``_gate_probe_record``), with
``executor: CONTROLLER`` on the envelope, the answer record and the turn-ledger row. It returns
the analyzer's usual result, so the solver loop reads the new frame and asks again: one frame in,
one action out. No plan is queued.

When Duck owns the step, it returns ``None`` and ``analyze`` proceeds with a model turn. If the
controller stopped for a reason (a stop-and-wake condition, a refused answer), Duck's prompt
carries a one-paragraph handoff saying what the controller did and why it stopped.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CONTROLLER = "CONTROLLER"  # the executor label; the gate logic lives in controller_executor
MAX_ANSWERS_PER_TURN = 16


@dataclass
class ControllerSession:
    enabled: bool = False
    refused: set[tuple[str, int, int | None]] = field(default_factory=set)
    wake: str | None = None
    handoff: str = ""
    actions: int = 0
    answers: int = 0
    last_raw: dict[str, Any] = field(default_factory=dict)  # the last step payload (budgets)
    rerun: dict[str, Any] | None = None  # an extra run Duck asked for (D3)

    def take_handoff(self) -> str:
        text, self.handoff = self.handoff, ""
        return text

    def hand_to_duck(self, reason: str) -> None:
        if self.actions or self.answers:
            self.handoff = (
                f"CONTROLLER HANDOFF: the controller has taken {self.actions} actions and "
                f"{self.answers} gate answers without a model call. It hands this step to you "
                f"because {reason}. The card below is current."
            )


def run_controller_turn(
    agent: Any, state_path: Path, action_num: int, analysis_step: int | None, analyzer_log: Path,
) -> Any | None:
    """Take the controller's step, or return None to let Duck take it."""
    session: ControllerSession = agent._controller
    if not session.enabled or agent._step_env_callback is None:
        return None
    from inference.framework.controller_executor import ANSWER, DUCK, ladder_end, next_owned_step

    machine = agent._ensure_gate_machine(state_path)
    end = ladder_end(machine)
    if end is not None:
        return _planned_stop(agent, end, analyzer_log)
    if session.wake is not None and not _takes_duck_choice(machine):
        session.hand_to_duck(session.wake)
        session.wake = None
        return None
    for _ in range(MAX_ANSWERS_PER_TURN):
        step = next_owned_step(machine, refused=session.refused, rerun=session.rerun)
        if step.owner == DUCK:
            session.hand_to_duck(step.reason)
            return None
        if step.kind == ANSWER:
            _controller_answer(agent, state_path, machine, step, analyzer_log)
            continue
        try:
            return _controller_action(agent, state_path, machine, step, action_num, analysis_step, analyzer_log)
        finally:
            agent._step_env_callback = None
            agent._virelai_query_callback = None
            agent._current_valid_actions = []
    return None


def _takes_duck_choice(machine: Any) -> bool:
    """G4-B and G4-C: the next action is Duck's own frozen prediction, so a wake waits until it is taken."""
    from inference.framework.controller_executor import PREDICTION_GATES

    return machine.gate_id in PREDICTION_GATES and machine.next_probe_capability() is not None


def _planned_stop(agent: Any, reason: str, analyzer_log: Path) -> Any:
    """The controller owns the end (R9-I02): stop the game cleanly, with no model call."""
    from inference.agent.tool_agent import AnalyzerTurnResult

    _log(analyzer_log, f"planned stop: {reason}")
    agent._step_env_callback = None
    agent._virelai_query_callback = None
    return AnalyzerTurnResult(step_executed=False, planned_stop=reason)


def _log(analyzer_log: Path, text: str) -> None:
    from inference.agent.tool_agent import _append_transcript_section

    _append_transcript_section(analyzer_log, "CONTROLLER", text)


def _controller_answer(agent: Any, state_path: Path, machine: Any, step: Any, analyzer_log: Path) -> None:
    from inference.framework.virelai_gates import GateContractError

    session: ControllerSession = agent._controller
    gate_id = machine.gate_id
    try:
        answer = machine.submit_answer(json.loads(json.dumps(step.answer)))
    except GateContractError as exc:
        session.refused.add(step.refusal_key)
        _log(analyzer_log, f"{gate_id} refused the controller's answer: {exc}")
        return
    agent._record_gate_answer(state_path, machine, gate_id, answer, executor=CONTROLLER)
    session.answers += 1
    _log(analyzer_log, f"answered {gate_id} ({step.reason}); gate now {machine.gate_id}")


def _controller_action(
    agent: Any, state_path: Path, machine: Any, step: Any,
    action_num: int, analysis_step: int | None, analyzer_log: Path,
) -> Any:
    from inference.agent.tool_agent import AnalyzerTurnResult
    from inference.agent.turn_ledger import TurnLedger
    from inference.framework.controller_executor import wake_reason, wake_signals

    session: ControllerSession = agent._controller
    ledger = TurnLedger(
        _ledger_path(state_path), analysis_step=analysis_step, action_num=action_num,
        executor=CONTROLLER, gate_before=machine.gate_id, sections={},
    )
    before = wake_signals(machine, session.last_raw)
    rerun_press = bool(session.rerun) and step.gate_id == "G4.2-LEVER-ORBITS"
    try:
        probe, before_frame, actions_before = agent._gate_probe_begin(
            state_path, machine, {"probe_token": step.probe_token}, [step.action], executor=CONTROLLER,
        )
    except Exception as exc:  # a refused probe is a stop condition, never a crash
        session.wake = f"the gate refused the controller's action: {exc}"
        ledger.finish(gate_after=machine.gate_id, step_executed=False, outcome="controller_refused")
        return AnalyzerTurnResult(step_executed=False)
    raw = agent._step_env_callback({"actions": [step.action], "decision": asdict(probe), "actor": CONTROLLER})
    raw = raw if isinstance(raw, dict) else {}
    event = None
    if raw.get("executed"):
        event = agent._gate_probe_record(
            state_path, machine, probe, [step.action], raw, before_frame, actions_before,
        )
    result = agent._apply_step_result(raw, event)
    executed = bool(result.get("executed"))
    session.actions += int(executed)
    session.last_raw = dict(raw)
    session.wake = (
        wake_reason(machine, event, raw, before) if executed
        else f"the environment did not execute the controller's action ({raw.get('error') or 'no detail'})"
    )
    if rerun_press:
        session.rerun["left"] -= 1
        if session.rerun["left"] <= 0:
            session.wake = session.wake or f"the extra run of {session.rerun['entity_id']} you asked for is done"
            session.rerun = None
    _log(analyzer_log, (
        f"{step.gate_id}: {step.reason}: {json.dumps(step.action, sort_keys=True)}; "
        f"executed={executed}; gate now {machine.gate_id}"
        + (f"; stopping: {session.wake}" if session.wake else "")
    ))
    ledger.finish(gate_after=machine.gate_id, step_executed=executed, outcome="controller_step")
    return AnalyzerTurnResult(step_executed=executed)


def request_rerun(agent: Any, machine: Any, parameters: dict[str, Any]) -> str | None:
    """D3: Duck asks the controller for an extra run of one G4-A lever; None if accepted."""
    from inference.framework.controller_executor import MAX_RERUN_PRESSES, ORBITS

    session: ControllerSession = agent._controller
    if not session.enabled:
        return "The controller executor is off in this run; press the lever yourself."
    if machine.gate_id != ORBITS:
        return f"An extra run is a G4-A request; the gate is {machine.gate_id}."
    entity = str(parameters.get("id") or "").strip()
    capability = machine.next_probe_capability() or {}
    lever = next((item for item in (capability.get("target") or {}).get("levers") or ()
                  if item.get("entity_id") == entity), None)
    if lever is None:
        return f"{entity!r} is not a G4-A lever the controller can press now."
    try:
        presses = int(parameters.get("presses") or 1)
    except (TypeError, ValueError):
        presses = 0
    if not 1 <= presses <= MAX_RERUN_PRESSES:
        return f"presses must be 1 to {MAX_RERUN_PRESSES}."
    session.rerun = {"entity_id": entity, "click": dict(lever["click"]), "left": presses}
    agent._gate_transitioned_this_turn = True
    return None


def _ledger_path(state_path: Path) -> Path:
    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME

    suffix = f"_{RUNTIME_STATE_FILENAME}"
    stem = state_path.name[: -len(suffix)] if state_path.name.endswith(suffix) else state_path.stem
    return state_path.with_name(f"{stem}_turn_ledger.jsonl")


__all__ = ["ControllerSession", "request_rerun", "run_controller_turn"]
