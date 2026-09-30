"""Gated memory queries: Duck's one pull interface, the read views, and the UNCERTIFIED lane.

Author: Claude (Alpha build seat), 2026-09-29. R9-R09 (DESIGN_VIRELAI_MEMORY_v2 §5.4, stage M-3).

``virelai('memory', kind=…, id=…, offset=…, limit=…)`` is the one pull interface over
``MemoryStore``. The older read views (``gate_audit``, ``inventory``, ``entity``, ``reaction``,
``orbit``, ``evidence``, and G4-B's ``relations`` since R9-R12) are kept as aliases and moved here unchanged from
``tool_agent.py``. ``virelai('orient', notes=[…])`` and ``virelai('annotate', notes=[…])`` write
Duck's notes to the UNCERTIFIED lane, persisted as ``{stem}_annotations.jsonl``.
``virelai('rerun', id=ENTITY, presses=N)`` asks the controller for an extra G4-A run (D3, R9-R10).
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
    return {"schema": "virelai-query-v1", "operation": operation, "data": data, "error": error, "truncated": truncated}


def gated_memory_query(
    agent: Any, state_path: Path, machine: Any, operation: str, parameters: dict[str, Any]
) -> dict[str, Any] | None:
    """Answer a memory or view operation; None if the operation is not one of these."""
    from inference.framework.virelai_gates import GateContractError

    if operation in VIEWS:
        try:
            data = VIEWS[operation](machine, parameters)
        except GateContractError as exc:
            return _reply(operation, agent._binding_gate_payload(machine), str(exc))
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
    if operation in {"orient", "annotate"}:
        return _submit(agent, state_path, machine, operation, parameters.get("notes"))
    if operation == "rerun":
        from inference.agent.controller_turn import request_rerun

        refusal = request_rerun(agent, machine, parameters)
        return _reply(operation, agent._binding_gate_payload(machine), refusal)
    return None


def _submit(agent: Any, state_path: Path, machine: Any, operation: str, raw: Any) -> dict[str, Any]:
    source = "ORIENTATION" if operation == "orient" else "ANNOTATION"
    try:
        notes = submit_notes(machine, raw, source=source)
    except AnnotationError as exc:
        return _reply(operation, agent._binding_gate_payload(machine), str(exc))
    record_notes(state_path, notes)
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
