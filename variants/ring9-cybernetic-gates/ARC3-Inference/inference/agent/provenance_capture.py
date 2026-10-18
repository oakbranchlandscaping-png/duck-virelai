"""WO-PE-01: the six capture points of the provenance journal, on the agent side.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v2``.

Each function turns the facts a call site already holds into one audit row of ``inference.framework.audit_journal``:
Duck's and the controller's probes (admitted, refused, executed, not attempted), their answers (submitted and
effective payloads, and who supplied each field), G3 choices (translated from the G3 selection events) and
notes. Nothing here changes what a gate admits or what is executed. Recording never raises: a failure (a write
error, or a payload that is not strict JSON) marks the journal failed, and the solver reports it as
``PROVENANCE_WRITE_FAILED`` when the session closes.

A probe's admission row is its operation anchor: the pending probe keeps that row's ``event_id``, and its execution
row names it in ``refs.admission_event_id`` and carries the admission's context (level, life, gate and the
transition before the decision). The transition the probe produced is ``refs.executed_transition``.

The journal lives on the ``ToolAgent`` (``_provenance``), never on the gate machine. Capture is off unless the
agent was built with ``provenance_enabled=True``; while it is disabled, every function here returns at once.
"""
from __future__ import annotations

import functools
from pathlib import Path
from typing import Any, Callable, Mapping

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
from inference.framework import audit_journal as pv

LEVER_GATE_ID = "G3-LEVERS"


def _enabled(agent: Any) -> bool:
    return bool(getattr(agent, "_provenance_enabled", False))


def _run_stem(state_path: Path) -> str:
    suffix = f"_{RUNTIME_STATE_FILENAME}"
    name = Path(state_path).name
    return name[: -len(suffix)] if name.endswith(suffix) else Path(state_path).stem


def journal_path(state_path: Path) -> Path:
    """WO-PE-02: where a run's journal lives, beside its other sidecars. Pure: it touches no file."""
    return Path(state_path).with_name(f"{_run_stem(state_path)}_provenance.jsonl")


def journal(agent: Any, state_path: Path) -> pv.ProvenanceJournal | None:
    """The agent's journal, opened beside the other sidecars on first use."""
    if not _enabled(agent):
        return None
    existing = getattr(agent, "_provenance", None)
    if existing is not None:
        return existing
    stem = _run_stem(state_path)
    path = journal_path(state_path)
    game_id = stem.rsplit("_p", 1)[0] if "_p" in stem else stem
    try:
        opened = pv.ProvenanceJournal.open(path, run_stem=stem, game_id=game_id)
    except Exception as exc:  # noqa: BLE001 - an unreadable journal is a failed journal, never a crash
        opened = pv.ProvenanceJournal(path, {"run_stem": stem, "game_id": game_id})
        opened._fail(f"{type(exc).__name__}: {exc}")
    agent._provenance = opened
    return opened


def portable(machine: Any, submitted: Any) -> Any:
    """The submitted payload with a capability token replaced by the capability it names.

    A probe token is an HMAC under a per-game random secret, deliberately unforgeable and so different on every
    run. The journal records which issued capability was presented (its probe and gate revision), or that the
    token was not one the gate issued; never the secret-derived bytes. Nothing else is changed."""
    if not isinstance(submitted, Mapping) or not isinstance(submitted.get("decision"), Mapping):
        return submitted
    decision = dict(submitted["decision"])
    if "probe_token" in decision:
        issued = (getattr(machine, "_issued_capabilities", None) or {}).get(str(decision["probe_token"] or "").strip())
        decision["probe_token"] = (f"CAPABILITY:{issued['probe_id']}:R{issued['gate_revision']}" if issued
                                   else "CAPABILITY:NOT_ISSUED")
    return {**submitted, "decision": decision}


def context(machine: Any) -> dict[str, Any]:
    """Where a decision is taken: the level, life and gate, and the transition before it."""
    lives = getattr(machine, "lives", None)
    return {"level": getattr(lives, "level", None), "life": getattr(lives, "life", None),
            "gate_id": getattr(machine, "gate_id", None),
            "at_transition": getattr(machine, "observed_through_step", None)}


def _sync(record: pv.ProvenanceJournal, machine: Any) -> None:
    events = list(getattr(machine, "g3_selection_events", None) or ())
    while record.g3_cursor < len(events) and not record.failed:
        record.append(pv.translate_g3_event(events[record.g3_cursor], LEVER_GATE_ID))
        record.g3_cursor += 1
    g4 = list(getattr(machine, "g4_selection_events", None) or ())  # WO-G4-DOSSIER-B (B2)
    while record.g4_cursor < len(g4) and not record.failed:
        record.append(pv.translate_g4_event(g4[record.g4_cursor]))
        record.g4_cursor += 1


def selection_event_count(machine: Any) -> int:
    """How many G3 and G4 choice events the machine holds (a refusal either selector recorded is not re-recorded)."""
    return sum(len(getattr(machine, name, None) or ()) for name in ("g3_selection_events", "g4_selection_events"))


def _append(agent: Any, state_path: Path, machine: Any, content: Mapping[str, Any]) -> dict[str, Any] | None:
    record = journal(agent, state_path)
    if record is None:
        return None
    try:
        if machine is not None:
            _sync(record, machine)
        return record.append(content)
    except Exception as exc:  # noqa: BLE001 - recording never costs the game an action
        record._fail(f"{type(exc).__name__}: {exc}")
        return None


def _record_failure(agent: Any, state_path: Path, exc: BaseException) -> None:
    try:
        record = journal(agent, state_path)
        if record is not None:
            record._fail(f"{type(exc).__name__}: {exc}")
    except Exception:  # noqa: BLE001
        pass


def _guarded(capture: Callable[..., Any]) -> Callable[..., Any]:
    """A capture point that fails open: building a row (strict JSON, references) never raises into gameplay."""
    @functools.wraps(capture)
    def guarded(agent: Any, state_path: Path, *args: Any, **kwargs: Any) -> Any:
        try:
            return capture(agent, state_path, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            _record_failure(agent, state_path, exc)
            return None
    return guarded


def _guarded_trace(method: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(method)
    def guarded(trace: "AnswerTrace", *args: Any, **kwargs: Any) -> Any:
        try:
            return method(trace, *args, **kwargs)
        except Exception as exc:  # noqa: BLE001
            _record_failure(trace.agent, trace.state_path, exc)
            return None
    return guarded


def sync(agent: Any, state_path: Path, machine: Any) -> None:
    """Translate every G3 selection event not yet journaled."""
    record = journal(agent, state_path)
    if record is None or machine is None:
        return
    try:
        _sync(record, machine)
    except Exception as exc:  # noqa: BLE001
        record._fail(f"{type(exc).__name__}: {exc}")


def _row(where: Mapping[str, Any], executor: str, operation: str, event: str, disposition: str, *,
         submitted: Any = None, effective: Any = None, sources: Any = None, reason: Any = None,
         **refs: Any) -> dict[str, Any]:
    return {**where, "executor": executor, "operation": operation, "event": event, "disposition": disposition,
            "submitted": submitted, "effective": effective, "field_sources": sources,
            "refs": pv.make_refs(**refs), "reason": reason}


# ---- probes -----------------------------------------------------------------------------------------------------

@_guarded
def probe_refused(agent: Any, state_path: Path, machine: Any, where: Mapping[str, Any], executor: str,
                  submitted: Any, code: str, text: str) -> None:
    if not _enabled(agent):
        return
    agent._provenance_admissions = getattr(agent, "_provenance_admissions", 0) + 1
    _append(agent, state_path, machine, _row(where, executor, "PROBE", "ADMISSION", "REFUSED",
                                             submitted=portable(machine, submitted),
                                             reason={"code": code, "text": str(text)}))


@_guarded
def probe_admitted(agent: Any, state_path: Path, machine: Any, where: Mapping[str, Any], executor: str,
                   submitted: Any, probe: Any) -> None:
    if not _enabled(agent):
        return
    agent._provenance_admissions = getattr(agent, "_provenance_admissions", 0) + 1
    agent._provenance_pending = {"probe_id": probe.probe_id, "executor": executor, "where": dict(where),
                                 "admission_event_id": None}
    row = _append(agent, state_path, machine, _row(where, executor, "PROBE", "ADMISSION", "ADMITTED",
                                                   submitted=portable(machine, submitted), probe_id=probe.probe_id))
    agent._provenance_pending["admission_event_id"] = row["event_id"] if row else None


@_guarded
def probe_executed(agent: Any, state_path: Path, machine: Any, probe: Any, gate_event: Mapping[str, Any]) -> None:
    """The execution of the pending admitted probe, joined to its exact admission row."""
    pending = getattr(agent, "_provenance_pending", None) if _enabled(agent) else None
    if pending is None:
        return
    agent._provenance_pending = None
    evidence = gate_event.get("evidence_id") if isinstance(gate_event, Mapping) else None
    transition = next((row.get("transition_id") for row in reversed(getattr(machine, "transition_index", ()) or ())
                       if row.get("evidence_id") == evidence), None)
    _append(agent, state_path, machine, _row(
        pending["where"], pending["executor"], "PROBE", "EXECUTION", "EXECUTED", probe_id=probe.probe_id,
        evidence_id=evidence, executed_transition=transition, admission_event_id=pending["admission_event_id"]))


@_guarded
def probe_not_attempted(agent: Any, state_path: Path, machine: Any, code: str, text: str) -> None:
    """An admitted probe that the environment did not execute, or whose execution raised."""
    pending = getattr(agent, "_provenance_pending", None) if _enabled(agent) else None
    if pending is None:
        return
    agent._provenance_pending = None
    _append(agent, state_path, machine, _row(
        pending["where"], pending["executor"], "PROBE", "EXECUTION", "NOT_ATTEMPTED", probe_id=pending["probe_id"],
        admission_event_id=pending["admission_event_id"], reason={"code": code, "text": str(text)}))


def duck_action(agent: Any, state_path: Path, handler: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap Duck's gated ``action()``: a refusal before the gate, a terminal no-op and an admitted probe that never
    executes become rows too. The handler's result and exceptions pass through unchanged."""
    if not _enabled(agent):
        return handler

    def wrapped(actions: Any, decision: Any = None) -> Any:
        mark = getattr(agent, "_provenance_admissions", 0)
        machine = getattr(agent, "_gate_machine", None)
        where = context(machine)
        try:
            result = handler(actions, decision)
        except BaseException as exc:
            _after_duck_action(agent, state_path, actions, decision, mark, where, exc=exc)
            raise
        _after_duck_action(agent, state_path, actions, decision, mark, where, result=result)
        return result

    return wrapped


def _after_duck_action(agent: Any, state_path: Path, actions: Any, decision: Any, mark: int,
                       where: Mapping[str, Any], *, exc: BaseException | None = None, result: Any = None) -> None:
    machine = getattr(agent, "_gate_machine", None)
    if getattr(agent, "_provenance_pending", None) is not None:
        detail = f"{type(exc).__name__}: {exc}" if exc is not None else _not_executed_detail(result)
        probe_not_attempted(agent, state_path, machine, "EXECUTION_ERROR" if exc is not None else "NOT_EXECUTED",
                            detail)
        return
    if getattr(agent, "_provenance_admissions", 0) != mark:
        return  # the gate's own admission row is already written
    payload = (result or {}).get("action_result") if isinstance(result, Mapping) else None
    if exc is not None:
        code, text = "ACTION_CONTRACT", str(exc)
    elif isinstance(payload, Mapping) and str(payload.get("stop_reason") or "").startswith("previous_"):
        code, text = "TERMINAL_STATE", str(payload.get("stop_detail") or payload.get("stop_reason"))
    else:
        return
    probe_refused(agent, state_path, machine, where, "DUCK", {"actions": actions, "decision": decision}, code, text)


def _not_executed_detail(result: Any) -> str:
    payload = (result or {}).get("action_result") if isinstance(result, Mapping) else None
    detail = (payload or {}).get("error") if isinstance(payload, Mapping) else None
    return str(detail or "the environment did not execute the action")


# ---- answers ----------------------------------------------------------------------------------------------------

class AnswerTrace:
    """One gate-answer submission: prepare (fill certified fields) and submit, keeping both payloads."""

    def __init__(self, agent: Any, state_path: Path, machine: Any, executor: str, raw: Any, submitted: Any) -> None:
        self.agent, self.state_path, self.machine, self.executor = agent, state_path, machine, executor
        self.raw, self.submitted, self.effective = raw, submitted, None
        self.where = context(machine) if _enabled(agent) else {}
        self.notes: list[Any] = []

    def submit(self) -> Any:
        """The gate's own decision, unchanged. With capture on, ``prepare_answer`` then ``submit_prepared`` (the same
        composition as ``submit_answer``), keeping the effective payload; with capture off, the call is exactly the
        one before WO-PE-01, plus the real executor for G3's lifecycle when the controller submits."""
        if not _enabled(self.agent):
            if self.executor == "DUCK":
                return self.machine.submit_answer(self.submitted)
            return self.machine.submit_answer(self.submitted, executor=self.executor)
        self.effective = self.machine.prepare_answer(self.submitted)
        return self.machine.submit_prepared(self.effective, executor=self.executor)

    def _sources(self, admitted: bool) -> dict[str, str]:
        from inference.framework.card_builder import CERTIFIED, CERTIFIED_TEMPLATE_FIELDS

        certified = CERTIFIED_TEMPLATE_FIELDS.get(str(self.where.get("gate_id")), ())
        return pv.field_sources(pv.normalized(self.submitted), pv.normalized(self.effective), certified,
                                admitted=admitted, marker=CERTIFIED)

    def _subject(self) -> Any:
        effective = self.effective if isinstance(self.effective, Mapping) else {}
        return effective.get("target_entity_id") or effective.get("entity_id") or effective.get("lever_entity_id")

    @_guarded_trace
    def refused(self, exc: BaseException) -> None:
        if not _enabled(self.agent):
            return
        from inference.agent.memory_queries import ORIENTATION_REFUSAL
        from inference.framework.annotation_lane import AnnotationError

        text = str(exc)
        code = ("ANNOTATION_INVALID" if isinstance(exc, AnnotationError)
                else "ORIENTATION_DUE" if text == ORIENTATION_REFUSAL else "GATE_CONTRACT")
        effective = self.effective if isinstance(self.effective, Mapping) else {}
        _append(self.agent, self.state_path, self.machine, _row(
            self.where, self.executor, "ANSWER", "ADMISSION", "REFUSED", submitted=self.raw,
            effective=self.effective, sources=self._sources(False), reason={"code": code, "text": text},
            answer_id=effective.get("answer_id"), subject=self._subject()))
        if code == "ANNOTATION_INVALID" and isinstance(self.raw, Mapping):
            _append(self.agent, self.state_path, self.machine, _row(
                self.where, self.executor, "ANNOTATION", "ADMISSION", "REFUSED",
                submitted=self.raw.get("annotations"), reason={"code": code, "text": text}))

    @_guarded_trace
    def admitted(self, answer: Any) -> None:
        if not _enabled(self.agent):
            return
        answer_id = getattr(answer, "answer_id", None) or getattr(answer, "prediction_id", None)
        _append(self.agent, self.state_path, self.machine, _row(
            self.where, self.executor, "ANSWER", "ADMISSION", "ADMITTED", submitted=self.raw,
            effective=self.effective, sources=self._sources(True), answer_id=answer_id, subject=self._subject()))
        if self.notes and isinstance(self.raw, Mapping):
            _append(self.agent, self.state_path, self.machine, _row(
                self.where, self.executor, "ANNOTATION", "ADMISSION", "UNCERTIFIED",
                submitted=self.raw.get("annotations"), note_ids=[note.note_id for note in self.notes]))


# ---- notes and G3 choices ---------------------------------------------------------------------------------------

@_guarded
def notes(agent: Any, state_path: Path, machine: Any, where: Mapping[str, Any], raw: Any, *,
          stored: list[Any] | None = None, refusal: BaseException | None = None) -> None:
    if not _enabled(agent):
        return
    if refusal is not None:
        _append(agent, state_path, machine, _row(where, "DUCK", "ANNOTATION", "ADMISSION", "REFUSED", submitted=raw,
                                                 reason={"code": "ANNOTATION_INVALID", "text": str(refusal)}))
        return
    _append(agent, state_path, machine, _row(where, "DUCK", "ANNOTATION", "ADMISSION", "UNCERTIFIED", submitted=raw,
                                             note_ids=[note.note_id for note in stored or ()]))


@_guarded
def g3_choice_refused_early(agent: Any, state_path: Path, machine: Any, where: Mapping[str, Any],
                            question_id: str, events_before: int, refusal: BaseException) -> None:
    """A G3 choice the machine refused before ``g3_selection.select`` wrote any event (the gate is not G3)."""
    if not _enabled(agent) or selection_event_count(machine) != events_before:
        return
    _append(agent, state_path, machine, _row(
        where, "DUCK", "G3_SELECTION", "ADMISSION", "REFUSED", submitted={"question_id": question_id},
        question_id=question_id, reason={"code": "GATE_CONTRACT", "text": str(refusal)}))


# ---- session close ----------------------------------------------------------------------------------------------

def close_session(agent: Any, state_path: Path) -> list[tuple[str, str]]:
    """At every handled end: write pending G3 selection events, journal them, close an admitted probe that never
    executed, and seal. Returns the observer warnings to record; never raises."""
    warnings: list[tuple[str, str]] = []
    machine = getattr(agent, "_gate_machine", None)
    if machine is not None and getattr(machine, "g3_selection_events", None) is not None:
        try:
            from inference.agent.gate_artifacts import flush_g3_selection_events

            flush_g3_selection_events(Path(state_path), machine)
        except Exception as exc:  # noqa: BLE001
            warnings.append(("G3_SELECTION_FLUSH_FAILED", f"{type(exc).__name__}: {exc}"))
    record = journal(agent, state_path)
    if record is None:
        return warnings
    sync(agent, state_path, machine)
    probe_not_attempted(agent, state_path, machine, "EXECUTION_ERROR", "the session closed before it executed")
    record.seal()
    if record.failed and not record.warned:
        record.warned = True
        warnings.append(("PROVENANCE_WRITE_FAILED", record.failed))
    return warnings


__all__ = [
    "AnswerTrace", "close_session", "context", "portable", "duck_action", "g3_choice_refused_early", "journal",
    "journal_path", "notes",
    "probe_admitted", "probe_executed", "probe_not_attempted", "probe_refused", "selection_event_count", "sync",
]
