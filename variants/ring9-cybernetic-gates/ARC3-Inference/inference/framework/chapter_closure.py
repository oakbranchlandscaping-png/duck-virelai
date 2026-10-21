"""One G4.1 or G4.2 lever chapter closed CLOSED_UNRESOLVED (WO-RUNTIME-01 revisions 2 and 3).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. The Director authorized a narrowly scoped per-lever
unresolved state for G4.1 (``G4-REACTIONS``, the effect anatomy) and G4.2 (``G4.2-LEVER-ORBITS``, the orbit study):

* only the selected lever chapter closes; its row stores the question, entity, reason, level, life, the recovery
  events that spent it and the chapter's evidence references;
* the gate skips that chapter in every later scheduling read (the adapters' one-line delegations to ``closed``) and
  keeps studying every other lever;
* the gate is settled when every lever is answered (or, in G4.2, released by a boundary) or closed; it then emits its
  ordinary product with the closure contract of ``chapter_semantics`` (revision 3): ``settlement_status``
  ``SETTLED_WITH_GAPS`` apart from ``knowledge_status`` ``PARTIAL`` or ``UNRESOLVED``; supported facts only in the
  knowledge fields; explicit ``unresolved_lever_chapters`` rows, each with its cause, epistemic closure class and
  revisit policy; and the source of every subject's geometry;
* downstream gates route over the observed geometry of a closed G4.1 chapter (``region_rows``) and carry it as
  ``ANATOMY_UNRESOLVED``; G4-C certifies no law whose levers' chapters are unresolved (``prerequisites_present``);
* the lever's dossier chapter renders ``CLOSED_UNRESOLVED`` / ``CHAPTER_CLOSED_UNRESOLVED`` with its closure class,
  never certified; the gate is never counted certified (``PARTIAL`` or ``CLOSED_UNRESOLVED`` in the census).

Scope: the closures live on the gate adapter, which is LEVEL-tier state (``life_record``): a level change rebuilds the
adapters, so a closure never outlives its chapter's level. A product emitted without a closure is byte-identical to
the base's (``with_rows`` and ``identity`` add nothing then).
"""
from __future__ import annotations

from typing import Any, Mapping

REACTIONS, ORBITS = "G4-REACTIONS", "G4.2-LEVER-ORBITS"
CHAPTERS = {REACTIONS: "EFFECTS", ORBITS: "ORBIT"}
ROWS = "unresolved_lever_chapters"


def closed(adapter: Any) -> dict[str, dict[str, Any]]:
    """The adapter's closed chapters by entity (empty: the base behaviour)."""
    return adapter.__dict__.get("_closed_chapters") or {}


def is_closed(adapter: Any, entity_id: str) -> bool:
    return str(entity_id) in closed(adapter)


def _answered(gate: str, adapter: Any, entity_id: str) -> bool:
    return entity_id in adapter._answers  # an interrupted (released) G4.2 lever is still open, so it may close


def _evidence(gate: str, adapter: Any, entity_id: str) -> list[str]:
    if gate == REACTIONS:
        return sorted(adapter._anatomies[entity_id].support_evidence_refs)
    return sorted({step.evidence_ref for run in adapter._runs.get(entity_id, []) for step in run.orbit.steps
                   if getattr(step, "evidence_ref", None)})


def close(machine: Any, gate: str, entity_id: str, *, question_id: str | None, reason: str,
          history: tuple | list = (), cause: str | None = None) -> str:
    """Close one lever chapter: ``CLOSED``, or ``NOTHING_TO_CLOSE`` (unknown, answered or already closed)."""
    adapter = machine._adapters[gate]
    adapter._seed()
    if entity_id not in adapter._ordered_entities or _answered(gate, adapter, entity_id) or is_closed(adapter, entity_id):
        return "NOTHING_TO_CLOSE"
    if gate == ORBITS:
        _release_run(adapter, entity_id)
    from inference.framework import chapter_semantics as S
    from inference.framework.library_agenda import question_id as qid

    level, life = int(machine.lives.level), int(machine.lives.life)
    row = {"gate_id": gate, "chapter": CHAPTERS[gate], "entity_id": entity_id,
           "question_id": question_id or qid(level, gate, entity_id, CHAPTERS[gate]), "reason": str(reason),
           "level": level, "life": life, "at_transition": int(machine.observed_through_step),
           "recovery_event_ids": [str(item) for item in history if item], "evidence_refs": _evidence(gate, adapter, entity_id),
           **S.closure_type(cause or reason)}  # revision 3: the exact cause, its epistemic class, its revisit policy
    adapter.__dict__.setdefault("_closed_chapters", {})[entity_id] = row
    adapter.revision += 1
    _settle(gate, adapter)
    return "CLOSED"


def _release_run(adapter: Any, entity_id: str) -> None:
    """A run of the closed lever ends (its evidence stays on the record); a standing choice of it ends too."""
    run = adapter._active_run
    if run is not None and run.entity_id == entity_id:
        run.end("the lever chapter closed CLOSED_UNRESOLVED")
        adapter._active_run = None
    selection = getattr(adapter, "_g4_selection", None)
    if selection is not None and selection.get("entity_id") == entity_id:
        from inference.framework import g4_selection

        g4_selection.settle(adapter)


def _settle(gate: str, adapter: Any) -> None:
    """Emit the gate's ordinary product once it is settled (G4.1), or as G4-A does after an answer (G4.2)."""
    if gate == REACTIONS:
        if adapter._current_entity() is None:
            adapter._emit_anatomy_product()
    elif adapter._answers or not adapter._pending():
        adapter._emit_orbit_product()


def close_open(machine: Any, gate: str, reason: str) -> list[str]:
    """Every open chapter of the gate, in order (the gate-level close of a seeded G4.1 or G4.2)."""
    adapter = machine._adapters[gate]
    adapter._seed()
    return [entity for entity in adapter._ordered_entities
            if close(machine, gate, entity, question_id=None, reason=reason, cause=reason) == "CLOSED"]


def upstream_closed(machine: Any) -> dict[str, dict[str, Any]]:
    """The G4.1 chapters closed on this level, by lever (what G4.2, G4-B and G4-C must carry as unresolved)."""
    adapter = (getattr(machine, "_adapters", None) or {}).get(REACTIONS)
    return {} if adapter is None else closed(adapter)


def rows(adapter: Any) -> list[dict[str, Any]]:
    return [dict(closed(adapter)[entity]) for entity in adapter._ordered_entities if entity in closed(adapter)]


def identity(adapter: Any, base: dict[str, Any]) -> dict[str, Any]:
    """A product's identity: unchanged without closures; with them, the closed chapters join it."""
    found = rows(adapter)
    return base if not found else {**base, "closed_chapters": [row["entity_id"] for row in found]}


def with_rows(adapter: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """The product payload: byte-identical without closures. With them (revision 3), workflow settlement and
    knowledge are separate: ``settlement_status`` says whether the scheduler may advance, ``knowledge_status`` what
    is supported; the knowledge fields hold supported facts only, the closure rows stand apart, and every subject's
    geometry names its source (``chapter_semantics``)."""
    from inference.framework import chapter_semantics as S

    return S.settle_payload(REACTIONS if hasattr(adapter, "_anatomies") else ORBITS, adapter, payload, rows(adapter))


def closed_in(payload: Mapping[str, Any] | None, entity_id: str) -> bool:
    """A stored product closes this lever's chapter (the dossier compiler and validator read this)."""
    return any(row.get("entity_id") == entity_id for row in (payload or {}).get(ROWS) or ())


__all__ = ["CHAPTERS", "ROWS", "close", "close_open", "closed", "closed_in", "identity", "is_closed", "rows",
           "upstream_closed", "with_rows"]
