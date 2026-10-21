"""Every Duck turn ends in exactly one typed outcome, and a failed one is bounded (WO-RUNTIME-01).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Interface: ``INTERFACE_WO_RUNTIME_01_v3_2026-10-20``
with the Director's rulings Q1–Q5 and Sol's rulings of 2026-10-20 (``MODEL_REQUEST_FAILED`` in the clock class; the
scripted-state fixtures; no runtime switch), as reconciled by ``IMPLEMENTATION_INTERFACE_WO_RUNTIME_01``.

``ToolAgent.analyze`` runs the turn unchanged and passes its raw result here (``settle``). The raw signals (a fatal
failure, a controlled stop, a retryable request failure, the yield reason) stay on the result exactly as they were;
``settle`` adds ``turn_outcome`` and ``recovery_reason`` and, for a failed Duck turn:

* charges the selected question's consecutive budget for its failure class (HARD 2, CLOCK 4; Director ruling Q1),
  reset by any executed action, accepted answer, gate transition or changed masked board;
* writes the audit row ``TURN OUTCOME`` (the authoritative record) and the turn-ledger row (operational evidence);
* leaves one recovery token for the controller's next turn, consumed before any prompt is built
  (``recovery_consume``). No recovery path adds a model request to the failed turn.

The other helpers here are the turn's own bounds: the request cap (ruling D), the commit turn after a clock expiry
(Q1), the attempted-action repair (a refused action is never read-only), and Duck's explicit decline (Q5).
"""
from __future__ import annotations

import dataclasses
import hashlib
import time
from typing import Any, Mapping

import requests

ACTION_EXECUTED, GATE_PROGRESS, EXPLICIT_DECLINE = "ACTION_EXECUTED", "GATE_PROGRESS", "EXPLICIT_DECLINE"
RECOVERABLE_NO_ACTION, TERMINAL, UNRECOVERABLE = "RECOVERABLE_NO_ACTION", "TERMINAL", "UNRECOVERABLE"
OUTCOMES = (ACTION_EXECUTED, GATE_PROGRESS, EXPLICIT_DECLINE, RECOVERABLE_NO_ACTION, TERMINAL, UNRECOVERABLE)
RECOVERABLE = frozenset({RECOVERABLE_NO_ACTION, EXPLICIT_DECLINE})
HARD, CLOCK, CONTROLLER = "HARD", "CLOCK", "CONTROLLER"
CONTROLLER_TURN = "CONTROLLER_TURN"  # the marker of a settled controller turn that executed nothing (not typed)
REASON_CLASS = {
    "TURN_CLOCK": CLOCK, "MODEL_TIMEOUT": CLOCK, "MODEL_REQUEST_FAILED": CLOCK,
    "READ_ONLY_REPEAT": HARD, "NO_TOOL_CALL": HARD, "MALFORMED_ACTION": HARD, "ACTION_REFUSED": HARD,
    "STALE_CHOICE": HARD, "SUBJECT_INADMISSIBLE": HARD, "PYTHON_ERROR": HARD, "CONTRACT_REPAIR_EXHAUSTED": HARD,
    "ROUTE_RETRY_EXHAUSTED": HARD, "CONTEXT_OVERFLOW": HARD, "TOOL_STEP_LIMIT": HARD,
    "NO_LEGAL_CONTROLLER_MOVE": CONTROLLER, "DECLINED": None,
}
BUDGETS = {HARD: 2, CLOCK: 4}  # Director ruling Q1: consecutive failed turns per question, counted per class
FREE_PLAY = "FREE_PLAY"
PLAY_GATE = "PLAY-NORMAL"
_STOPS = (("no_progress_tool_loop", "READ_ONLY_REPEAT"), ("contract_repair_loop", "CONTRACT_REPAIR_EXHAUSTED"),
          ("g3_route_retry_exhausted", "ROUTE_RETRY_EXHAUSTED"), ("g3_semantic_retry_exhausted", "CONTRACT_REPAIR_EXHAUSTED"))
_MALFORMED = ("accepts opaque ACTION", "requires integer row and col", "decision accepts only", "missing an `action`",
              "expects a string", "legacy MOUSE", "requires at least one action", "is empty", "must be a string or",
              "Python syntax error", "decline takes exactly")
_STALE = ("stale", "no longer", "superseded", "not issued", "expired")


# ---- the budgets ---------------------------------------------------------------------------------------------------

class Budgets:
    """Consecutive failed Duck turns per (level, life, gate, question), counted per class; progress resets them."""

    def __init__(self) -> None:
        self._rows: dict[tuple, dict[str, Any]] = {}

    @staticmethod
    def _scope(machine: Any) -> tuple:
        lives = getattr(machine, "lives", None)
        return (getattr(lives, "level", None), getattr(lives, "life", None), getattr(machine, "gate_id", None))

    def _row(self, machine: Any, question: str | None) -> dict[str, Any]:
        return self._rows.setdefault((*self._scope(machine), question),
                                     {HARD: [], CLOCK: [], "commit": False, "board": None})

    def fail(self, machine: Any, question: str | None, reason: str, *, event_id: str | None = None,
             board: str | None = None) -> bool:
        """Charge one failure; True when its class's budget is now spent."""
        kind = REASON_CLASS.get(reason)
        if kind not in BUDGETS:
            return False
        row = self._row(machine, question)
        if board is not None and row["board"] is not None and board != row["board"]:
            self.progress(machine, "BOARD_CHANGED")
            row = self._row(machine, question)
        row["board"] = board if board is not None else row["board"]
        row[kind].append(event_id)
        return len(row[kind]) >= BUDGETS[kind]

    def progress(self, machine: Any, _kind: str) -> None:
        """Any executed action, accepted answer, gate transition or changed board on this level and life resets every
        count (the audit's rule 4 reads the same resets from the journal)."""
        scope = self._scope(machine)[:2]
        for key in [key for key in self._rows if key[:2] == scope]:
            del self._rows[key]

    def counts(self, machine: Any, question: str | None) -> dict[str, int]:
        row = self._rows.get((*self._scope(machine), question)) or {HARD: [], CLOCK: []}
        return {HARD: len(row[HARD]), CLOCK: len(row[CLOCK])}

    def history(self, machine: Any, question: str | None, kind: str) -> list[str]:
        row = self._rows.get((*self._scope(machine), question)) or {}
        return [item for item in row.get(kind) or () if item]

    def set_commit(self, machine: Any, question: str | None) -> None:
        self._row(machine, question)["commit"] = True

    def commit_due(self, machine: Any, question: str | None) -> bool:
        row = self._rows.get((*self._scope(machine), question))
        return bool(row and row["commit"])


def budgets(agent: Any) -> Budgets:
    found = getattr(agent, "_recovery_budgets", None)
    if found is None:
        found = agent._recovery_budgets = Budgets()
    return found


# ---- the turn's start and its bounds -------------------------------------------------------------------------------

def selected_question(machine: Any) -> str | None:
    if machine is None:
        return None
    if machine.gate_id == PLAY_GATE:
        return FREE_PLAY
    try:
        from inference.framework.library_agenda import selected_question as agenda_question

        return agenda_question(machine)
    except Exception:  # noqa: BLE001 - a view failure never costs the turn its record
        return None


def board_key(machine: Any) -> str | None:
    """The masked board, excluding certified and candidate counter cells (Q1's "materially changed board")."""
    if machine is None:
        return None
    try:
        from inference.framework.card_builder import _current_grid
        from inference.framework.counter_exclusion import counter_cells

        grid = _current_grid(machine)
        if grid is None:
            return None
        hidden = counter_cells(machine)
        rows = [[-1 if (r, c) in hidden else int(v) for c, v in enumerate(row)] for r, row in enumerate(grid)]
        return hashlib.sha256(repr(rows).encode()).hexdigest()[:16]
    except Exception:  # noqa: BLE001
        return None


def begin_duck_turn(agent: Any, state_path: Any) -> None:
    """Called once a Duck turn begins (the controller handed it over): what the turn is for and how it is bounded."""
    machine = getattr(agent, "_gate_machine", None)
    _controller_progress(agent, machine)
    question = selected_question(machine)
    commit = budgets(agent).commit_due(machine, question)
    session = getattr(agent, "_controller", None)
    owned = str(getattr(session, "owned_because", "") or "")
    agent._duck_turn = {"question_id": question, "owned_because": owned, "commit": commit, "board": board_key(machine),
                        "gate_id": getattr(machine, "gate_id", None), "refusals": 0, "declined": None,
                        "timeouts": [], "saved_limit": None, "started": time.monotonic(),
                        "choice": "choose one with" in owned}
    agent._last_request_error = None
    agent._last_dispatch = None
    if commit:  # Q1: the commit turn corrects its first read-only call at once
        agent._duck_turn["saved_limit"] = agent._max_read_only_without_progress
        agent._max_read_only_without_progress = 1


def _controller_progress(agent: Any, machine: Any) -> None:
    """An answer the controller had accepted since the last turn resets the counts too (Q1: any accepted answer)."""
    session = getattr(agent, "_controller", None)
    answers = int(getattr(session, "answers", 0) or 0)
    if answers != int(getattr(agent, "_recovery_answers_seen", 0) or 0):
        agent._recovery_answers_seen = answers
        budgets(agent).progress(machine, "ANSWER_ACCEPTED")


def request_cap(agent: Any, upstream: float | None, turn_started_at: float) -> float | None:
    """Ruling D: a request may wait no longer than the turn's remaining allowance (nor the world's)."""
    yield_seconds = getattr(agent, "_yield_seconds", None)
    cap, source = upstream, "UPSTREAM"
    if yield_seconds is not None:
        remaining = max(0.1, float(yield_seconds) - (time.monotonic() - turn_started_at))
        if upstream is None or remaining < float(upstream):
            cap, source = remaining, "TURN"
    agent._request_cap_source = source
    turn = getattr(agent, "_duck_turn", None)
    if turn is not None and cap is not None:
        turn["timeouts"].append(round(float(cap), 3))
    return cap


def commit_sections(agent: Any, *sections: str) -> tuple[str, ...]:
    """Q1: after a clock expiry the next prompt on the question permits only act, answer or decline."""
    turn = getattr(agent, "_duck_turn", None)
    if not turn or not turn["commit"]:
        return sections
    from inference.agent.prompts import commit_turn_prompt

    machine = getattr(agent, "_gate_machine", None)
    capability = machine.next_probe_capability() if machine is not None else None
    view = machine.gate_view() if machine is not None else {}
    return ("", "", commit_turn_prompt(question_id=turn["question_id"], capability=capability,
                                       template=view.get("answer_template")), "")


# ---- attempted actions and the decline -----------------------------------------------------------------------------

def refusal_code(text: str) -> str:
    lowered = str(text).lower()
    if any(item.lower() in lowered for item in _MALFORMED):
        return "MALFORMED_ACTION"
    if any(item in lowered for item in _STALE):
        return "STALE_CHOICE"
    if "inadmissible" in lowered or "not admissible" in lowered:
        return "SUBJECT_INADMISSIBLE"
    return "ACTION_REFUSED"


def watch_refusals(agent: Any, handler: Any) -> Any:
    """Duck's action handler, noting a refused attempt (the audit refusal row is the gate's, written as before)."""
    def watched(actions: Any, decision: Any = None) -> Any:
        try:
            return handler(actions, decision)
        except BaseException as exc:
            agent._turn_refusal = f"{type(exc).__name__}: {exc}"
            raise
    return watched


def dispatch(agent: Any, result: Any, executed: bool) -> Any:
    """The python dispatch, typed: an accepted decline is DECLINE (Q5); a dispatch whose action was refused is an
    attempt, ACTION_REFUSED, never an observation."""
    declined, agent._turn_declined = getattr(agent, "_turn_declined", False), False
    refusal, agent._turn_refusal = getattr(agent, "_turn_refusal", None), None
    if declined:
        return dataclasses.replace(result, interaction_kind="DECLINE")
    if refusal is None or executed or result.interaction_kind != "OBSERVATION":
        return result
    return dataclasses.replace(result, interaction_kind="ACTION_REFUSED", repair_signature=refusal_code(refusal),
                               repair_error=refusal)


def action_refusal(agent: Any, dispatch: Any) -> tuple[str | None, str | None]:
    """(halt reason, repair prompt): one concise repair for the first refusal in a turn, the end at the second."""
    from inference.agent.prompts import action_repair_prompt

    turn = getattr(agent, "_duck_turn", None) or {}
    turn["refusals"] = int(turn.get("refusals") or 0) + 1
    code = str(dispatch.repair_signature or "ACTION_REFUSED")
    if turn["refusals"] >= 2:
        return f"action_refused:{code}: {dispatch.repair_error}", None
    return None, action_repair_prompt(error=str(dispatch.repair_error), question_id=turn.get("question_id"))


def decline(agent: Any, machine: Any, parameters: Mapping[str, Any]) -> dict[str, Any]:
    """Q5: ``virelai('decline', question_id=...)`` for the selected Duck-owned question only; no answer, no claim.
    An accepted decline marks the dispatch (``dispatch``: DECLINE)."""
    turn = getattr(agent, "_duck_turn", None)
    current = None if turn is None else turn["question_id"]
    error = None
    if set(parameters) != {"question_id"}:
        error = "decline takes exactly question_id; it carries no answer or claim."
    elif turn is None or machine is None or machine.gate_id == "G0-ACTION-METADATA":
        error = "No Duck-owned question is selected now; nothing can be declined."
    elif str(parameters.get("question_id") or "") != str(current):
        error = f"Only the selected question can be declined (this id is stale or different): {current}."
    if error is not None:
        agent._turn_refusal = f"DeclineRefused: {error}"
        return {"schema": "virelai-query-v1", "operation": "decline", "data": None, "error": error,
                "truncated": False}
    turn["declined"], agent._turn_declined = current, True
    effect = ("one controller frontier action follows" if current == FREE_PLAY
              else "the question closes CLOSED_UNRESOLVED and the ladder continues")
    return {"schema": "virelai-query-v1", "operation": "decline", "error": None, "truncated": False,
            "data": {"declined": current, "effect": effect, "answer": None}}


# ---- classification and settlement ---------------------------------------------------------------------------------

def classify(agent: Any, result: Any) -> tuple[str, str]:
    """(outcome, reason) for one analyzer result, from the raw signals it and the agent carry."""
    if result is None:
        return UNRECOVERABLE, "ANALYZER_EXCEPTION"
    yielded = str(getattr(result, "yield_reason", "") or "")
    if result.planned_stop:
        return TERMINAL, "PLANNED_STOP"
    if yielded == "stop_requested":
        return TERMINAL, "STOP_REQUESTED"
    if result.step_executed:
        return ACTION_EXECUTED, ""
    if yielded == "declined":
        return EXPLICIT_DECLINE, "DECLINED"
    if yielded == "gate_transition" or getattr(agent, "_gate_transitioned_this_turn", False):
        return GATE_PROGRESS, ""
    return RECOVERABLE_NO_ACTION, _failure_reason(agent, result, yielded)


def _failure_reason(agent: Any, result: Any, yielded: str) -> str:
    fatal = str(result.fatal_failure or "")
    if fatal:
        return ("NO_TOOL_CALL" if fatal.startswith("provider_tool_call_incompatible")
                else "NO_LEGAL_CONTROLLER_MOVE" if fatal.startswith("controller_no_legal_move") else "CONTEXT_OVERFLOW")
    if result.retryable_failure:
        error = getattr(agent, "_last_request_error", None)
        if isinstance(error, requests.Timeout):
            return "TURN_CLOCK" if getattr(agent, "_request_cap_source", "") == "TURN" else "MODEL_TIMEOUT"
        return "MODEL_REQUEST_FAILED"
    stop = str(result.controlled_stop or "")
    if stop.startswith("action_refused:"):
        return stop.split(":", 2)[1]
    for prefix, reason in _STOPS:
        if stop.startswith(prefix):
            return "PYTHON_ERROR" if reason == "READ_ONLY_REPEAT" and _last_call_raised(agent) else reason
    if yielded == "turn_time_budget":
        return "TURN_CLOCK"
    return "TOOL_STEP_LIMIT"


def _last_call_raised(agent: Any) -> bool:
    dispatch = getattr(agent, "_last_dispatch", None)
    return dispatch is not None and '"error"' in str(getattr(dispatch, "content", ""))


def recoverable(result: Any) -> bool:
    return getattr(result, "turn_outcome", "") in RECOVERABLE


def settle(agent: Any, result: Any, state_path: Any) -> Any:
    """Type the turn; for a Duck turn, charge its budget, record it and leave the recovery token."""
    turn, agent._duck_turn = getattr(agent, "_duck_turn", None), None
    outcome, reason = classify(agent, result)  # an analyzer exception (None) is UNRECOVERABLE, ANALYZER_EXCEPTION
    machine = getattr(agent, "_gate_machine", None)
    if outcome in (ACTION_EXECUTED, GATE_PROGRESS):
        budgets(agent).progress(machine, outcome)
    if turn is not None:
        _settle_duck(agent, state_path, machine, turn, outcome, reason)
    else:
        _controller_progress(agent, machine)
        if outcome == RECOVERABLE_NO_ACTION:  # a controller turn that executed nothing is not a Duck turn
            outcome, reason = "", CONTROLLER_TURN
    if result is None:  # recorded above; the analyzer's contract is unchanged (None: the harness raises, as before)
        return None
    return dataclasses.replace(result, turn_outcome=outcome, recovery_reason=reason)


def _settle_duck(agent: Any, state_path: Any, machine: Any, turn: dict, outcome: str, reason: str) -> None:
    if turn["saved_limit"] is not None:
        agent._max_read_only_without_progress = turn["saved_limit"]
    question, kind = turn["question_id"], REASON_CLASS.get(reason)
    event_id, exhausted = None, False
    if outcome in RECOVERABLE:
        from inference.agent import recovery_consume

        event_id = recovery_consume.record_outcome(agent, state_path, machine, turn, outcome, reason)
        if outcome == RECOVERABLE_NO_ACTION and not turn["choice"]:
            exhausted = budgets(agent).fail(machine, question, reason, event_id=event_id, board=turn["board"])
        if reason == "TURN_CLOCK":
            budgets(agent).set_commit(machine, question)
        if not getattr(agent._controller, "enabled", False):  # no controller to consume it: Duck owns the next turn
            recovery_consume.duck_owns_next(agent, state_path, machine, event_id, turn, reason)
        agent._controller.recovery = {
            "outcome_event_id": event_id, "question_id": question, "gate_id": turn["gate_id"], "reason": reason,
            "class": kind, "exhausted": exhausted, "decline": outcome == EXPLICIT_DECLINE,
            "history": [event_id] if outcome == EXPLICIT_DECLINE else budgets(agent).history(machine, question, kind),
        }
    counts = budgets(agent).counts(machine, question)
    _finish_ledger(agent, {
        "question_id": question, "owned_because": turn["owned_because"], "turn_outcome": outcome,
        "recovery_reason": reason, "failure_class": kind,
        "recovery_count": counts.get(kind, 0) if kind in BUDGETS else 0, "budget_exhausted": exhausted,
        "commit_turn": turn["commit"], "request_timeouts": list(turn["timeouts"]),
        "turn_clock_seconds": getattr(agent, "_yield_seconds", None), "turn_clock_expired": reason == "TURN_CLOCK",
        "next_executor": "CONTROLLER" if outcome in RECOVERABLE else None, "recovery_event_id": event_id})


def _finish_ledger(agent: Any, fields: Mapping[str, Any]) -> None:
    pending, agent._pending_ledger = getattr(agent, "_pending_ledger", None), None
    if pending is not None:
        ledger, base = pending
        ledger.finish(**base, **fields)


__all__ = ["ACTION_EXECUTED", "BUDGETS", "Budgets", "EXPLICIT_DECLINE", "GATE_PROGRESS", "OUTCOMES", "REASON_CLASS",
           "RECOVERABLE", "RECOVERABLE_NO_ACTION", "TERMINAL", "UNRECOVERABLE", "action_refusal", "begin_duck_turn",
           "board_key", "budgets", "classify", "commit_sections", "decline", "dispatch", "recoverable",
           "refusal_code", "request_cap", "selected_question", "settle", "watch_refusals"]
