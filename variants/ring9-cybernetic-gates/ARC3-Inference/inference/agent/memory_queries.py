"""Gated memory queries: Duck's one pull interface, the read views, and the UNCERTIFIED lane.

Author: Claude (Alpha build seat), 2026-09-29. R9-R09 (DESIGN_VIRELAI_MEMORY_v2 §5.4, stage M-3).

``virelai('memory', kind=…, id=…, offset=…, limit=…)`` is the one pull interface over
``MemoryStore``. The older read views (``gate_audit``, ``inventory``, ``entity``, ``reaction``,
``orbit``, ``evidence``, and G4-B's ``relations`` since R9-R12) are kept as aliases and moved here unchanged from
``tool_agent.py``. ``virelai('orient', notes=[…])`` and ``virelai('annotate', notes=[…])`` write
Duck's notes to the UNCERTIFIED lane, persisted as ``{stem}_annotations.jsonl``.
``virelai('rerun', id=ENTITY, presses=N)`` asks the controller for an extra G4-A run (D3, R9-R10).
``virelai('library', kind=…)`` pages the validated semantic library (WO-L2a library view, 2026-10-11).
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
from inference.framework.annotation_lane import AnnotationError, orientation_due, submit_notes
from inference.framework.memory_store import MemoryStore

VIEWS = {
    "gate_audit": lambda m, p: m.gate_audit_view(offset=p.get("offset", 0), limit=p.get("limit", 20)),
    "inventory": lambda m, p: m.inventory_view(offset=p.get("offset", 0), limit=p.get("limit", 10)),
    "entity": lambda m, p: m.entity_view(
        str(p.get("id") or ""), offset=p.get("offset", 0), limit=p.get("limit", 128)
    ),
    "reaction": lambda m, p: m.reaction_view(str(p.get("id") or "")),
    "orbit": lambda m, p: m.orbit_view(str(p.get("id") or "")),
    "relations": lambda m, p: m.relations_view(),
    "evidence": lambda m, p: m.evidence_view(p.get("id", "")),
}
ORIENTATION_REFUSAL = (
    "The orientation turn is due: read world_model and submit virelai('orient', notes=[...]) "
    "before any action or gate answer."
)


def _reply(operation: str, data: Any, error: str | None = None, truncated: bool = False) -> dict[str, Any]:
    """The error comes first, so the tool-output limit never cuts it off (R9-R14, F1)."""
    return {"schema": "virelai-query-v1", "operation": operation, "error": error, "data": data, "truncated": truncated}


def _refused_state(machine: Any) -> dict[str, Any]:
    """With a refusal, the state it needs, not the whole card (virelai('gate') returns that)."""
    view = machine.gate_view()
    return {"gate_id": machine.gate_id, "status": view.get("status"), "next_operation": view.get("next_operation"),
            "card": "virelai('gate')"}


def _library_query(machine: Any, parameters: dict[str, Any]) -> dict[str, Any]:
    """``virelai('library', kind=…, id=…, reason=…, subject=…, level=…, part=…, offset=…, limit=…)``, and the
    event filters ``transition``, ``from_transition``, ``to_transition``, ``object``, ``verb`` and
    ``include_folded`` (WO-DESC-B): one bounded page of the validated live library; ``next`` names the call for the
    rest, with every active filter.
    A census or lookup failure is the reply's error, never a crash."""
    from inference.framework.library_view import library_page, live_model

    keys = ("id", "reason", "subject", "level", "part", "offset", "limit",
            "transition", "from_transition", "to_transition", "object", "verb", "include_folded")  # WO-DESC-B
    options = {key: parameters[key] for key in keys if key in parameters}
    try:
        data = library_page(live_model(machine), str(parameters.get("kind") or "levels"), **options)
    except Exception as exc:  # noqa: BLE001 - reported to Duck with its type; the gate state is untouched
        return _reply("library", None, f"{type(exc).__name__}: {exc}")
    return _reply("library", data, truncated=bool(data.get("truncated")))


def _chosen_probe(agent: Any, state_path: Path, machine: Any, question_id: str) -> dict[str, Any]:
    """``virelai('next_probe', question_id=Q)`` (WO-G3-DIRECTED; G4.1 and G4-A since WO-G4-DOSSIER-B B2): admit Duck's
    choice in the gate its question names, then return the freshly bound capability. A refusal is the reply's
    error, with the current question; the coverage head is unchanged."""
    from inference.framework.library_agenda import selected_question
    from inference.framework.virelai_gates import GateContractError

    from inference.agent import provenance_capture
    from inference.agent.gate_artifacts import flush_g3_selection_events

    where, before = provenance_capture.context(machine), provenance_capture.selection_event_count(machine)
    try:
        machine.select_question(question_id, actor="DUCK")
    except GateContractError as exc:
        provenance_capture.g3_choice_refused_early(agent, state_path, machine, where, question_id, before, exc)
        return _reply("next_probe", {**_refused_state(machine), "question_id": selected_question(machine)}, str(exc))
    finally:
        flush_g3_selection_events(state_path, machine)
        provenance_capture.sync(agent, state_path, machine)  # WO-PE-01: the choice event, translated
    capability = machine.next_probe_capability()
    return _reply("next_probe", capability, None if capability is not None else "No probe is admissible now.")


def gated_memory_query(
    agent: Any, state_path: Path, machine: Any, operation: str, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    """Answer a memory or view operation; None if the operation is not one of these."""
    from inference.framework.virelai_gates import GateContractError

    if operation in VIEWS:
        try:
            data = VIEWS[operation](machine, parameters)
        except GateContractError as exc:
            return _reply(operation, _refused_state(machine), str(exc))
        return _reply(operation, data, truncated=bool(operation == "inventory" and data.get("truncated")))
    if operation == "memory":
        try:
            data = MemoryStore(machine).query(
                str(parameters.get("kind") or ""),
                **{key: value for key, value in parameters.items() if key != "kind"},
            )
        except (ValueError, TypeError, GateContractError) as exc:
            return _reply(operation, None, str(exc))
        return _reply(operation, data, None if data is not None else "Nothing is recorded under that key.")
    if operation == "library":
        return _library_query(machine, parameters)
    if operation == "next_probe" and parameters.get("question_id"):
        return _chosen_probe(agent, state_path, machine, str(parameters["question_id"]))
    if operation in {"orient", "annotate"}:
        return _submit(agent, state_path, machine, operation, parameters.get("notes"))
    if operation == "rerun":
        from inference.agent.controller_turn import request_rerun

        refusal = request_rerun(agent, machine, parameters)
        return _reply(operation, _refused_state(machine) if refusal else agent._binding_gate_payload(machine), refusal)
    return None


def _submit(agent: Any, state_path: Path, machine: Any, operation: str, raw: Any) -> dict[str, Any]:
    from inference.agent import provenance_capture

    source = "ORIENTATION" if operation == "orient" else "ANNOTATION"
    where = provenance_capture.context(machine)
    try:
        notes = submit_notes(machine, raw, source=source)
    except AnnotationError as exc:
        provenance_capture.notes(agent, state_path, machine, where, raw, refusal=exc)  # WO-PE-01
        return _reply(operation, _refused_state(machine), str(exc))
    record_notes(state_path, notes)
    provenance_capture.notes(agent, state_path, machine, where, raw, stored=notes)
    if source == "ORIENTATION":
        agent._gate_transitioned_this_turn = True
    return _reply(operation, agent._binding_gate_payload(machine))


def record_notes(state_path: Path, notes: list[Any]) -> None:
    path = state_path.with_name(
        state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_annotations.jsonl")
    )
    with path.open("a", encoding="utf-8") as handle:
        for note in notes:
            handle.write(json.dumps({"schema": "virelai-annotation-v1", "label": "UNCERTIFIED", **asdict(note)},
                                    sort_keys=True) + "\n")


def orientation_refusal(machine: Any) -> str | None:
    """While the orientation turn is due, actions and gate answers wait for it."""
    return ORIENTATION_REFUSAL if machine is not None and orientation_due(machine) else None


__all__ = ["gated_memory_query", "orientation_refusal", "record_notes"]
