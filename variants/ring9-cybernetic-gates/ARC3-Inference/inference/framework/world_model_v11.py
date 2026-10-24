"""World model v11: the rules a gate closed CLOSED_UNRESOLVED adds (WO-RUNTIME-01 §10, Director ruling B).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. ``world_model_v2`` dispatches here, so its own
version logic stays one line per rule.

What v11 adds over v10, and nothing else:

* the provenance chapter is ``virelai-provenance-chapter-v3`` (audit v1, v2 or v3 rows: the recovery vocabulary);
  ``provenance_chapter.validate_chapter`` holds that rule;
* a census gate row may be ``CLOSED_UNRESOLVED`` — the gate's product exists, states ``status: UNRESOLVED`` and its
  ``unresolved_reason``, and certifies nothing: no EGO or COUNTER role cites it;
* (revision 2) a G4.1 or G4.2 gate row may be ``PARTIAL`` — its product states ``status: PARTIAL`` and carries
  explicit ``unresolved_lever_chapters`` rows beside the answered levers (``chapter_closure``);
* (revision 3) such a row also states the product's ``settlement_status``, ``knowledge_status`` and subject counts,
  agrees with the stored product (``chapter_semantics.gate_problems``: never CERTIFIED), and the product keeps the
  settlement/knowledge contract (``chapter_semantics.payload_problems``);
* (WO-RUNTIME-01A) a gate row whose stored product states ``status: UNRESOLVED`` with its ``unresolved_reason`` is
  ``CLOSED_UNRESOLVED``, never ``CERTIFIED``: a repair failure certifies nothing (the gate-level twin of revision 3's
  chapter rule).

A model below v11 holds no ``CLOSED_UNRESOLVED`` or ``PARTIAL`` gate row (a relabelled v11 artifact is refused by the
frozen readers, as WIN-01 r2 refuses a relabelled episode).
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.framework.chapter_semantics import gate_problems

CLOSED_UNRESOLVED, PARTIAL = "CLOSED_UNRESOLVED", "PARTIAL"
GATE_DISPOSITIONS = frozenset({"NOT_STARTED", "NOT_REACHED", "IN_PROGRESS", "CERTIFIED", "RECORD_MISMATCH",
                               CLOSED_UNRESOLVED, PARTIAL})
PARTIAL_GATES = frozenset({"G4-REACTIONS", "G4.2-LEVER-ORBITS"})
UNRESOLVED_ROLE_GATES = {"G1-EGO": "EGO", "G2-COUNTER": "COUNTER"}


def unresolved(product: Any) -> bool:
    """A gate product closed CLOSED_UNRESOLVED (``gate_closure``, or G4-B/G4-C's own ``close_unresolved``)."""
    payload = getattr(product, "payload", None)
    return isinstance(payload, Mapping) and payload.get("status") == "UNRESOLVED" \
        and bool(payload.get("unresolved_reason"))


def disposition(product: Any) -> str:
    """The census disposition of a gate holding an active product."""
    payload = getattr(product, "payload", None)
    partial = isinstance(payload, Mapping) and payload.get("status") == PARTIAL
    return CLOSED_UNRESOLVED if unresolved(product) else PARTIAL if partial else "CERTIFIED"


def gate_fields(product: Any) -> dict[str, Any]:
    """The census gate row's disposition and, for a product with closed chapters (revision 3), its settlement and
    knowledge status and subject counts: a PARTIAL gate is never a certified gate."""
    from inference.framework.chapter_semantics import gate_row

    return gate_row(getattr(product, "payload", None), disposition(product))


def _gate_rows(level: Any) -> list:
    certified = level.get("certified") if isinstance(level, Mapping) else None
    gates = certified.get("gates") if isinstance(certified, Mapping) else None
    return [row for row in gates or () if isinstance(row, Mapping)]


def _closed_rows_certified(level: Any, rows: list) -> list[str]:
    """01A: a CERTIFIED gate row whose stored product was closed CLOSED_UNRESOLVED (a repair failure, not knowledge)."""
    content = level.get("product_content") or {}
    payloads = {row.get("gate_id"): (content.get(row.get("product_id")) or {}).get("payload") for row in rows
                if row.get("disposition") == "CERTIFIED" and isinstance(content.get(row.get("product_id")), Mapping)}
    return [f"level {level.get('level')}: {gate} is CERTIFIED, but its product is UNRESOLVED "
            f"({payload.get('unresolved_reason')}): a closed gate certifies nothing"
            for gate, payload in sorted(payloads.items())
            if isinstance(payload, Mapping) and payload.get("status") == "UNRESOLVED"
            and payload.get("unresolved_reason")]


def problems(levels: Any, *, current: bool) -> list[str]:
    """v11 (``current``): the disposition vocabulary and no certifying role on a closed gate; below v11: no
    ``CLOSED_UNRESOLVED`` row at all."""
    found: list[str] = []
    for level in levels or ():
        rows = _gate_rows(level)
        closed = {row.get("gate_id"): row for row in rows if row.get("disposition") == CLOSED_UNRESOLVED}
        partial = {row.get("gate_id"): row for row in rows if row.get("disposition") == PARTIAL}
        if not current:
            found.extend(f"level {level.get('level')}: {gate} is {row['disposition']}, which only v11 holds"
                         for gate, row in sorted({**closed, **partial}.items()))
            continue
        found.extend(f"level {level.get('level')}: {gate} cannot be PARTIAL (only G4.1 and G4.2 close per chapter)"
                     for gate, row in sorted(partial.items()) if gate not in PARTIAL_GATES or not row.get("product_id"))
        found.extend(f"level {level.get('level')}: gate {row.get('gate_id')} has unknown disposition "
                     f"{row.get('disposition')!r}" for row in rows if row.get("disposition") not in GATE_DISPOSITIONS)
        found.extend(f"level {level.get('level')}: CLOSED_UNRESOLVED {gate} names no product"
                     for gate, row in sorted(closed.items()) if not row.get("product_id"))
        found.extend(gate_problems(level))  # revision 3: the row agrees with its product's settlement and knowledge
        found.extend(_closed_rows_certified(level, rows))  # WO-RUNTIME-01A
        for role in (level.get("certified") or {}).get("roles") or ():
            gate = role.get("gate_id")
            if gate in closed and UNRESOLVED_ROLE_GATES.get(gate) == role.get("role"):
                found.append(f"level {level.get('level')}: {role.get('role')} cites {gate}, closed CLOSED_UNRESOLVED")
    return found


__all__ = ["CLOSED_UNRESOLVED", "GATE_DISPOSITIONS", "PARTIAL", "disposition", "gate_fields", "problems", "unresolved"]
