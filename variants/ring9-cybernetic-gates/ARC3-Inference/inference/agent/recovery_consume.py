"""The controller's side of a recovery: consumed at the head of the next controller turn (WO-RUNTIME-01 §4–§5).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Interface v3 §1–§5 with the Director's rulings Q1–Q5.

``turn_recovery.settle`` leaves one token after a failed or declined Duck turn. ``consume`` takes it before any prompt
is built (``controller_turn.run_controller_turn`` calls it first):

* in ``PLAY-NORMAL``: one deterministic frontier action (ruling A, ``free_play_frontier``) through the ordinary
  ``PLAY-NORMAL`` capability, recorded as the controller's (``FREE_PLAY``), or a clean stop with its proof when the
  frontier is exhausted (Q4);
* in a gate: when the question's budget is spent, or Duck declined it, only that question or gate closes
  ``CLOSED_UNRESOLVED`` (``gate_closure``) and the ladder continues; otherwise the ordinary controller turn runs and
  ``resolve`` records whether the controller took the gate's head or Duck is woken again.

D22 (``no_legal_move``) and D-2 (``stalled``) are the same bounded recovery on the controller's side (Q2): neither
rests the level. Every decision is one audit row (v3: ``TURN RECOVERY``, ``GATE CLOSE``, ``GATE RECOVERY_CHECK``).
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.agent import provenance_capture, repair_obligation

PLAY_GATE, G0 = "PLAY-NORMAL", "G0-ACTION-METADATA"
NO_LEGAL_MOVE_TURNS = 2  # Q2: D22 closes after two consecutive no-move turns
_CLOSE_REASON = {"HARD": "HARD_BUDGET_SPENT", "CLOCK": "CLOCK_BUDGET_SPENT"}


# ---- the audit rows ------------------------------------------------------------------------------------------------

def _where(machine: Any) -> dict[str, Any]:
    return provenance_capture.context(machine)


def _row(machine: Any, executor: str, operation: str, event: str, disposition: str, code: str, text: str, *,
         question: str | None, subject: str | None = None, submitted: Any = None, gate: str | None = None) -> dict:
    where = _where(machine)
    if gate is not None:
        where["gate_id"] = gate
    return provenance_capture.row(where, executor, operation, event, disposition, submitted=submitted,
                                  reason={"code": code, "text": str(text)[:240] or code},
                                  question_id=question, subject=subject)


def record_outcome(agent: Any, state_path: Any, machine: Any, turn: Mapping[str, Any], outcome: str,
                   reason: str) -> str | None:
    """The failed or declined Duck turn: ``TURN OUTCOME`` (Duck's), with the refusal it cites, if any."""
    detail = str(getattr(agent, "_last_turn_detail", "") or reason)
    row = _row(machine, "DUCK", "TURN", "OUTCOME", outcome, reason, detail, question=turn.get("question_id"),
               gate=turn.get("gate_id"),
               submitted={"owned_because": turn.get("owned_because") or None, "commit_turn": bool(turn.get("commit")),
                          "refusal_event_id": provenance_capture.last_refusal(agent)})
    written = provenance_capture.audit(agent, state_path, machine, row)
    return None if written is None else written["event_id"]


def _recovery(agent: Any, state_path: Any, machine: Any, token: Mapping[str, Any], disposition: str, *,
              resulting: str | None = None, code: str | None = None, proof: Any = None) -> str | None:
    submitted = {"turn_event_id": token.get("outcome_event_id"), "resulting_event_id": resulting}
    if proof is not None:
        submitted["proof"] = proof
    row = _row(machine, "CONTROLLER", "TURN", "RECOVERY", disposition, code or str(token.get("reason")),
               f"{disposition} after {token.get('reason')}", question=token.get("question_id"),
               gate=token.get("gate_id"), submitted=submitted)
    written = provenance_capture.audit(agent, state_path, machine, row)
    return None if written is None else written["event_id"]


def _close_row(agent: Any, state_path: Any, machine: Any, closure: Any, code: str, question: str | None,
               history: list, kind: str | None) -> str | None:
    budget = {"HARD": 2, "CLOCK": 4}.get(kind or "")
    row = _row(machine, "CONTROLLER", "GATE", "CLOSE", "CLOSED_UNRESOLVED", code,
               f"{closure.scope} {closure.subject or closure.gate_id} closes unresolved: {code}", question=question,
               subject=closure.subject, gate=closure.gate_id,
               submitted={"scope": closure.scope, "class": kind, "budget": budget, "history": [h for h in history if h],
                          "cascaded": list(closure.cascaded)})
    written = provenance_capture.audit(agent, state_path, machine, row)
    return None if written is None else written["event_id"]


def budget_closed(agent: Any, state_path: Any, machine: Any, gate: str) -> str | None:
    """Q5: a D21 close of G4-B or G4-C (Duck's per-level budget spent) is journalled as the controller's GATE CLOSE."""
    from inference.framework.gate_closure import Closure

    if agent is None:
        return None
    return _close_row(agent, state_path, machine, Closure("CLOSED", "GATE", gate), "DUCK_BUDGET_SPENT", None, [], None)


# ---- closing the selected question ---------------------------------------------------------------------------------

def close_selected(machine: Any, question: str | None, reason: str, history: tuple | list = (),
                   cause: str | None = None) -> Any:
    """Close only the selected question (a gate, a G3 entity or a G4.1/G4.2 lever chapter) CLOSED_UNRESOLVED; the
    ladder continues (Q1, Q2, Q5; revision 2 ruling 1)."""
    from inference.framework import gate_closure

    return gate_closure.close_question(machine, question, reason, history, cause)


def _close(agent: Any, state_path: Any, machine: Any, token: Mapping[str, Any]) -> None:
    code = ("DECLINED" if token.get("decline") else "NO_LEGAL_CONTROLLER_MOVE"
            if token.get("reason") == "NO_LEGAL_CONTROLLER_MOVE" else _CLOSE_REASON.get(str(token.get("class")), "HARD_BUDGET_SPENT"))
    cause = code if token.get("decline") or code == "NO_LEGAL_CONTROLLER_MOVE" else str(token.get("reason") or code)
    history, kind = list(token.get("history") or ()), None if token.get("decline") else token.get("class")
    if code == "NO_LEGAL_CONTROLLER_MOVE":  # WO-RUNTIME-01A: a D22 close cites its recovery checks (rule 5), classless
        history, kind = _d22_checks(agent, state_path, machine), None
        if history is None:
            return  # the gate has a legal move after all: nothing is checked, nothing closes; ``resolve`` records
    closure = close_selected(machine, token.get("question_id"), code, history, cause)
    if closure.status == "CLOSED":
        repair_obligation.discharge(agent)  # WO-RUNTIME-01A: a closed question owes no answer
        close_id = _close_row(agent, state_path, machine, closure, code, token.get("question_id"), history, kind)
        _recovery(agent, state_path, machine, token, "CLOSED_UNRESOLVED", resulting=close_id, code=code)
    else:
        return  # nothing to close (already closed or gone): the ordinary turn decides, ``resolve`` records it
    agent._controller.pending = None


def _d22_checks(agent: Any, state_path: Any, machine: Any) -> list | None:
    """WO-RUNTIME-01A: the ``RECOVERY_CHECK`` rows a watchdog close cites: the session's pending no-move checks of this
    gate, level and life; with none pending, one fresh check of the board now; ``None`` when a legal move exists (no
    check is fabricated). The Duck ``OUTCOME`` is never cited: its ``RECOVERY`` names the close."""
    session, where = agent._controller, _where(machine)
    record = provenance_capture.journal(agent, state_path)
    rows = record.chain.v3.rows if record is not None else {}
    scope = (where["gate_id"], where["level"], where["life"])
    pending = [item for item in getattr(session, "no_move", ()) or () if item in rows
               and (rows[item]["gate_id"], rows[item]["level"], rows[item]["life"]) == scope]
    session.no_move = []
    if pending:
        return pending
    status = machine.legal_move_status()
    if status.get("legal", True):
        return None
    check = _row(machine, "CONTROLLER", "GATE", "RECOVERY_CHECK", "NO_LEGAL_MOVE", "NO_LEGAL_CONTROLLER_MOVE",
                 str(status.get("reason") or "no probe, no acceptable answer and no declared end"), question=None)
    written = provenance_capture.audit(agent, state_path, machine, check)
    return [] if written is None else [written["event_id"]]


# ---- consumption ---------------------------------------------------------------------------------------------------

def consume(agent: Any, state_path: Any, machine: Any, analyzer_log: Any, action_num: int,
            analysis_step: int | None) -> Any | None:
    """Take the recovery token before any prompt: a frontier action or stop in play, a close in a gate, or nothing
    (the ordinary controller turn follows and ``resolve`` records what it did)."""
    session = agent._controller
    token, session.recovery = getattr(session, "recovery", None), None
    if token is None:
        return None
    session.pending = token
    if machine.gate_id == PLAY_GATE:
        return _free_play(agent, state_path, machine, analyzer_log, action_num, analysis_step, token)
    if token.get("decline") or token.get("exhausted") or token.get("reason") == "NO_LEGAL_CONTROLLER_MOVE":
        _close(agent, state_path, machine, token)
    return None


def _free_play(agent: Any, state_path: Any, machine: Any, analyzer_log: Any, action_num: int,
               analysis_step: int | None, token: Mapping[str, Any]) -> Any:
    from inference.agent import controller_turn
    from inference.framework import free_play_frontier
    from inference.framework.controller_executor import ACTION, CONTROLLER, OwnedStep

    frontier = free_play_frontier.for_machine(machine)
    choice = frontier.choose(machine)
    if choice is None:  # Q4: exhausted with its proof (or, with nothing legal at all, no move to make)
        proof = frontier.proof(machine)
        code = "FREE_PLAY_FRONTIER_EXHAUSTED" if proof["complete"] else "NO_LEGAL_CONTROLLER_MOVE"
        _recovery(agent, state_path, machine, token, "NO_CONTROLLER_ACTION", code=code, proof=proof)
        agent._controller.pending = None
        return controller_turn._planned_stop(agent, f"{code}: every legal action on this masked board is tried or "
                                                    "barred" if proof["complete"] else f"{code}: no legal action on "
                                                    "this board", analyzer_log)
    capability = machine.next_probe_capability() or {}
    step = OwnedStep(CONTROLLER, PLAY_GATE, f"free-play frontier after {token.get('reason')} (ruling A)", ACTION,
                     action=dict(choice.action), probe_token=str(capability.get("probe_token") or ""),
                     decision={"intent": f"FREE_PLAY frontier: untried {list(choice.key)}"})
    try:
        return controller_turn._controller_action(agent, state_path, machine, step, action_num, analysis_step,
                                                  analyzer_log)
    finally:
        agent._step_env_callback = None
        agent._virelai_query_callback = None
        agent._current_valid_actions = []


def duck_owns_next(agent: Any, state_path: Any, machine: Any, event_id: str | None, turn: Mapping[str, Any],
                   reason: str) -> None:
    """With no controller executor in the session, the recovery is resolved at once: Duck is woken again."""
    if event_id is not None:
        _recovery(agent, state_path, machine, {"outcome_event_id": event_id, "question_id": turn.get("question_id"),
                                               "gate_id": turn.get("gate_id"), "reason": reason}, "DUCK_REWOKEN")


def resolve(agent: Any, state_path: Any, result: Any) -> None:
    """After the controller turn: record how a pending recovery was resolved (a controller action, or Duck again)."""
    session = agent._controller
    token = getattr(session, "pending", None)
    if token is None:
        return
    machine = getattr(agent, "_gate_machine", None)
    if result is not None and getattr(result, "step_executed", False):
        _recovery(agent, state_path, machine, token, "CONTROLLER_ACTION",
                  resulting=provenance_capture.last_admission(agent, "CONTROLLER"))
    elif result is None:
        _recovery(agent, state_path, machine, token, "DUCK_REWOKEN")
    elif getattr(result, "planned_stop", ""):
        _recovery(agent, state_path, machine, token, "NO_CONTROLLER_ACTION", code="PLANNED_STOP")
    else:
        return  # the controller's action was refused: the recovery stays pending for the next turn
    session.pending = None


def ledger_fields(agent: Any, probe_id: str | None = None) -> dict[str, Any]:
    """The controller row's recovery fields (turn ledger v2) while it resolves a pending recovery."""
    token = getattr(agent._controller, "pending", None)
    if token is None:
        return {}
    return {"recovery": "CONTROLLER_ACTION", "resumed_by": "CONTROLLER", "question_id": token.get("question_id"),
            "recovery_of": token.get("outcome_event_id"), "recovery_reason": token.get("reason"),
            "next_probe_id": probe_id}


# ---- D22 and D-2, inside ruling B ----------------------------------------------------------------------------------

def _closed_note(agent: Any, state_path: Any, machine: Any, code: str, history: list) -> str:
    from inference.agent import turn_recovery

    from inference.framework.gate_closure import close_stuck_gate
    from inference.framework.play_gate import rest_in_play

    gate, question = machine.gate_id, turn_recovery.selected_question(machine)
    closure = close_stuck_gate(machine, question, code, history)  # r2: the exact question, the gate's head, the gate
    if closure.status == "CLOSED":
        repair_obligation.discharge(agent)  # WO-RUNTIME-01A: a closed question owes no answer
        _close_row(agent, state_path, machine, closure, code, question, history, None)
        return f"{gate}: {code}; {closure.scope.lower()} {closure.subject or closure.gate_id} closed CLOSED_UNRESOLVED; " \
               f"the ladder continues at {machine.gate_id}"
    if gate != G0 or machine.target_journal.active_product(G0) is not None:
        return f"{gate}: {code}; nothing closable for {question}: no rest, the controller's ordinary turn decides"
    note = f"{G0}: {code}; no action surface, so no downstream gate is constructible: normal play (the last resort)"
    row = _row(machine, "CONTROLLER", "GATE", "LAST_RESORT", "NORMAL_PLAY_ENTERED", "NO_CONSTRUCTIBLE_GATE", note,
               question=question, gate=G0, submitted={"history": [h for h in history if h], "trigger": code})
    provenance_capture.audit(agent, state_path, machine, row)  # typed and audited (r2 ruling 2.5)
    rest_in_play(machine, note)
    return note


def no_legal_move(agent: Any, state_path: Any, machine: Any) -> str | None:
    """Q2 (D22): two consecutive turns with no legal controller move close only the current question or gate."""
    session = agent._controller
    status = machine.legal_move_status()
    if status.get("legal", True) or machine.gate_id == PLAY_GATE:
        session.no_move = []
        return None
    check = _row(machine, "CONTROLLER", "GATE", "RECOVERY_CHECK", "NO_LEGAL_MOVE", "NO_LEGAL_CONTROLLER_MOVE",
                 str(status.get("reason") or "no probe, no acceptable answer and no declared end"),
                 question=None)
    written = provenance_capture.audit(agent, state_path, machine, check)
    session.no_move = [*getattr(session, "no_move", []), None if written is None else written["event_id"]]
    if len(session.no_move) < NO_LEGAL_MOVE_TURNS:
        return None
    history, session.no_move = session.no_move, []
    return _closed_note(agent, state_path, machine, "NO_LEGAL_CONTROLLER_MOVE", history)


def stalled(agent: Any, state_path: Any, machine: Any) -> str | None:
    """Q2 (D-2): three controller turns that executed nothing close only the refused step's question."""
    from inference.agent.controller_turn import MAX_STALLED_CONTROLLER_TURNS

    session = agent._controller
    if session.stalled < MAX_STALLED_CONTROLLER_TURNS or machine.gate_id == PLAY_GATE:
        return None
    check = _row(machine, "CONTROLLER", "GATE", "RECOVERY_CHECK", "CONTROLLER_STALLED", "CONTROLLER_STALLED",
                 str(session.wake or "the controller executed no action"), question=None)
    written = provenance_capture.audit(agent, state_path, machine, check)
    session.stalled, session.wake = 0, None
    return _closed_note(agent, state_path, machine, "CONTROLLER_STALLED",
                        [None if written is None else written["event_id"]])


__all__ = ["budget_closed", "close_selected", "consume", "ledger_fields", "no_legal_move", "record_outcome",
           "resolve", "stalled"]
