"""G3 after an unresolved G2: the counter exclusion region (WO-RUNTIME-01 §6, Director ruling Q3).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``.

When G2 closes CLOSED_UNRESOLVED while one or more counter candidates survive, G3 has no mask to subtract counter ticks
with (``lever_attribution`` removes counter change only through mask cells), so every tick would read as a remote
response of the clicked object. The ruling:

* the exclusion region R is the union of every plausible candidate's footprint (``full_bar_footprint`` and
  ``observed_support``); plausible means held by G2 on this level and neither contradicted nor rejected;
* every G3 attribution then carries ``COUNTER_UNRESOLVED``;
* evidence entirely inside R cannot certify a lever by itself;
* an object becomes a lever only from evidence outside R, or from in-R evidence that is independently localised:
  (1) spatially attributable to the tested entity (inside its own target cells) **and** (2) predicted by no
  surviving candidate (no candidate's rewrite, ``source → replacement`` or back, covers the change);
* otherwise the row stays inconclusive (``UNRESOLVED_ATTRIBUTION``, G3's existing ambiguity path) with the masking
  reason ``COUNTER_UNRESOLVED_EXCLUSION``. A screened row is never re-scored into a lever: promotion needs a new
  transition that qualifies on its own.

G2 records its candidates through two delegation lines (``note_candidate``, ``note_contradicted``); with no
unresolved G2 nothing here changes an attribution.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from typing import Any, Iterable, Mapping, Sequence

COUNTER_UNRESOLVED = "COUNTER_UNRESOLVED: G2 closed unresolved; counter change is not masked"
EXCLUSION = "COUNTER_UNRESOLVED_EXCLUSION"
POSITIVE = ("LOCAL_LEVER_WITNESS", "REMOTE_LEVER_WITNESS", "LOCAL_AND_REMOTE_LEVER_WITNESS")


# ---- G2's roster -------------------------------------------------------------------------------------------------

def note_candidate(counter: Any, candidate: Any) -> Any:
    """Keep every candidate G2 holds (returned unchanged, so the assignment site stays one line)."""
    if candidate is not None:
        roster = counter.__dict__.setdefault("_candidate_roster", {})
        roster.setdefault(candidate.candidate_id, candidate)
    return candidate


def note_contradicted(counter: Any) -> None:
    if counter.candidate is not None:
        counter.__dict__.setdefault("_contradicted_candidates", set()).add(counter.candidate.candidate_id)


def plausible(counter: Any) -> list[dict[str, Any]]:
    """The candidates G2 held that no recorded transition contradicted and no purity check rejected."""
    dropped = set(getattr(counter, "_contradicted_candidates", set()) or set())
    dropped |= {str(item.get("candidate_id")) for item in getattr(counter, "_rejected_candidates", ()) or ()}
    roster = dict(getattr(counter, "_candidate_roster", {}) or {})
    if counter.candidate is not None:
        roster.setdefault(counter.candidate.candidate_id, counter.candidate)
    return [{"candidate_id": cid, "footprint": sorted({tuple(c) for c in (*item.full_bar_footprint,
                                                                         *item.observed_support)}),
             "source_integer": int(item.source_integer), "replacement_integer": int(item.replacement_integer),
             "candidate": asdict(item)}
            for cid, item in sorted(roster.items()) if cid not in dropped]


# ---- the exclusion --------------------------------------------------------------------------------------------------

class Exclusion:
    def __init__(self, candidates: Iterable[Any]) -> None:
        self.candidates = [_as_row(item) for item in candidates]
        self.region = frozenset(cell for item in self.candidates for cell in item["footprint"])

    def _predicted(self, change: tuple) -> bool:
        row, col, before, after = change
        for item in self.candidates:
            pair = (item["source_integer"], item["replacement_integer"])
            if (row, col) in item["cells"] and (before, after) in (pair, pair[::-1]):
                return True
        return False

    def screen(self, attribution: Any, *, target_cells: Iterable[Any], outcome: Mapping[str, Any]) -> Any:
        """The attribution under Q3: tagged, and stripped of in-region evidence that does not qualify."""
        limitations = tuple(attribution.limitations)
        if not any(item.startswith("COUNTER_UNRESOLVED") for item in limitations):
            limitations = (*limitations, COUNTER_UNRESOLVED)
        if attribution.disposition not in POSITIVE:
            return replace(attribution, limitations=limitations)
        target = {tuple(cell) for cell in target_cells}
        changes = {(int(r), int(c)): (int(r), int(c), b, a) for r, c, b, a in attribution.changed_cells}
        kept = {cell for cell in attribution.residue_cells
                if tuple(cell) not in self.region
                or (tuple(cell) in target and not self._predicted(changes.get(tuple(cell), (*cell, None, None))))}
        if kept == set(map(tuple, attribution.residue_cells)):
            return replace(attribution, limitations=limitations)
        local, remote = sorted(kept & target), sorted(kept - target)
        if not kept:
            return replace(attribution, disposition="UNRESOLVED_ATTRIBUTION", residue_cells=(), local_residue_cells=(),
                           remote_residue_cells=(), limitations=(*limitations, _inseparable(self, attribution)))
        disposition = ("LOCAL_AND_REMOTE_LEVER_WITNESS" if local and remote
                       else "LOCAL_LEVER_WITNESS" if local else "REMOTE_LEVER_WITNESS")
        return replace(attribution, disposition=disposition, residue_cells=tuple(sorted(kept)),
                       local_residue_cells=tuple(local), remote_residue_cells=tuple(remote),
                       limitations=(*limitations, f"{EXCLUSION}: in-region cells excluded as inseparable"))


def _as_row(item: Any) -> dict[str, Any]:
    if isinstance(item, Mapping):
        footprint = [tuple(cell) for cell in item["footprint"]]
        source, replacement = int(item["source_integer"]), int(item["replacement_integer"])
        cid = str(item["candidate_id"])
    else:
        footprint = sorted({tuple(c) for c in (*item.full_bar_footprint, *item.observed_support)})
        source, replacement, cid = int(item.source_integer), int(item.replacement_integer), str(item.candidate_id)
    return {"candidate_id": cid, "footprint": footprint, "cells": frozenset(footprint),
            "source_integer": source, "replacement_integer": replacement}


def _inseparable(exclusion: Exclusion, attribution: Any) -> str:
    ids = ", ".join(item["candidate_id"] for item in exclusion.candidates)
    return (f"{EXCLUSION}: every response cell lies in the counter exclusion region and is not separable from "
            f"candidate(s) {ids}; the row stays inconclusive and is never promoted without new qualifying evidence")


# ---- the machine's view --------------------------------------------------------------------------------------------

def for_machine(machine: Any) -> Exclusion | None:
    """The exclusion when G2 closed CLOSED_UNRESOLVED with surviving candidates; None otherwise."""
    product = machine.target_journal.active_product("G2-COUNTER")
    payload = product.payload if product is not None and isinstance(product.payload, Mapping) else {}
    if payload.get("status") != "UNRESOLVED" or not payload.get("plausible_counter_candidates"):
        return None
    return Exclusion(payload["plausible_counter_candidates"])


def screen_g3(machine: Any, attribution: Any, outcome: Mapping[str, Any], target_cells: Sequence[Any]) -> Any:
    """G3's one delegation line: the attribution unchanged unless G2 closed unresolved with candidates."""
    exclusion = for_machine(machine)
    return attribution if exclusion is None else exclusion.screen(attribution, target_cells=target_cells,
                                                                  outcome=outcome)


def counter_cells(machine: Any) -> frozenset[tuple[int, int]]:
    """The certified mask, the exclusion region and a live candidate's footprint (the board-change key ignores them)."""
    cells: set[tuple[int, int]] = set()
    counter = getattr(machine, "counter", None)
    mask = getattr(counter, "mask_law", None)
    if mask is not None:
        cells |= {tuple(cell) for cell in mask.cells}
    exclusion = for_machine(machine)
    if exclusion is not None:
        cells |= set(exclusion.region)
    candidate = getattr(counter, "candidate", None)
    if candidate is not None:
        cells |= {tuple(c) for c in (*candidate.full_bar_footprint, *candidate.observed_support)}
    return frozenset(cells)


__all__ = ["COUNTER_UNRESOLVED", "EXCLUSION", "Exclusion", "counter_cells", "for_machine", "note_candidate",
           "note_contradicted", "plausible", "screen_g3"]
