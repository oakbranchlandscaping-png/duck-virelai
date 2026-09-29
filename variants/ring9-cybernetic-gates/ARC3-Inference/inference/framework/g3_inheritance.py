"""G3 inherits G2's total nulls (ruling D5, DESIGN_VIRELAI_MEMORY_v2 §5.5).

Author: Claude (Alpha build seat), 2026-09-29. R9-R08 (memory stage M-2).

G2's counter search clicks ranked visual objects before G3 opens. A click that changed **no cell
at all** (no residue anywhere, no counter tick, no boundary) is already a scoped null for the
object it acted on, in the world state of that moment. G3 records it as that object's scoped null,
citing G2's evidence, instead of clicking the object again. Nothing is inferred beyond the record:
an object with any non-null G2 click, or none, is swept by G3 as before.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

INHERITED_ACTOR = "G3_INHERITED_G2_NULL"
BOUNDARY_KEYS = ("done", "level_completed", "game_over", "run_complete")


def _acted_cell(outcome: Mapping[str, Any]) -> tuple[int, int] | None:
    site = outcome.get("acted_site")
    if isinstance(site, Mapping) and "row" in site and "col" in site:
        return int(site["row"]), int(site["col"])
    action = outcome.get("action")
    if isinstance(action, Mapping) and "row" in action and "col" in action:
        return int(action["row"]), int(action["col"])
    return None


def _total_null(outcome: Mapping[str, Any]) -> bool:
    if outcome.get("changed_cells") or int(outcome.get("changed_cell_count") or 0):
        return False
    boundary = outcome.get("boundary_event")
    return not (isinstance(boundary, Mapping) and any(boundary.get(key) for key in BOUNDARY_KEYS))


def inherited_total_nulls(
    frontier: Sequence[Mapping[str, Any]], g2_outcomes: Iterable[Mapping[str, Any]]
) -> dict[str, str]:
    """``member_id -> evidence_id`` of the first G2 total null on each member never seen to respond.

    A member qualifies only if every G2 click that acted on its original cells was a total null.
    """
    owner = {
        (int(cell[0]), int(cell[1])): str(row["member_id"])
        for row in frontier
        for cell in row.get("original_cells") or row.get("cells") or ()
    }
    nulls: dict[str, str] = {}
    responded: set[str] = set()
    for outcome in g2_outcomes:
        member = owner.get(_acted_cell(outcome) or (-1, -1))
        if member is None:
            continue
        if not _total_null(outcome):
            responded.add(member)
        elif outcome.get("evidence_id"):
            nulls.setdefault(member, str(outcome["evidence_id"]))
    return {member: ref for member, ref in nulls.items() if member not in responded}


@dataclass
class G2NullInheritance:
    """The inherited nulls of one G3 roster, applied at the roster head as the sweep reaches them."""

    nulls: dict[str, str]
    count: int = 0

    def apply(self, candidates: Sequence[Mapping[str, Any]], index: int, ledger: Any, journal: Any) -> int:
        """Record each untouched head member G2 saw null; return the first index G3 must click."""
        while index < len(candidates):
            member_id = str(candidates[index]["member_id"])
            evidence_ref = self.nulls.get(member_id)
            entity_id = ledger.entity_for_member(member_id)
            if not evidence_ref or not entity_id or journal.entities[entity_id].state != "UNTOUCHED":
                return index
            journal.attempt(entity_id, evidence_ref=evidence_ref, actor=INHERITED_ACTOR)
            journal.response(entity_id, positive=False, evidence_ref=evidence_ref, actor=INHERITED_ACTOR)
            self.count += 1
            index += 1
        return index


__all__ = ["G2NullInheritance", "INHERITED_ACTOR", "inherited_total_nulls"]
