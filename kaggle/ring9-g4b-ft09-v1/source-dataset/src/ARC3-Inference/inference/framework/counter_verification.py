"""Evidence primitives for G2 counter discovery and reversible masking.

This module deliberately stops short of assigning purpose.  It compiles visible
rewrite processes that recur across distinct Duck interventions, verifies one
prospective recurrence, and constructs a mask over the observed support.  The
raw grids remain authoritative; masking is always a derived view.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence


MASK_SENTINEL = "<COUNTER_MASKED>"


@dataclass(frozen=True)
class CounterCandidate:
    candidate_id: str
    rewrite: str
    observed_support: tuple[tuple[int, int], ...]
    full_bar_footprint: tuple[tuple[int, int], ...]
    footprint_geometry: str
    source_integer: int
    replacement_integer: int
    witness_evidence_refs: tuple[str, ...]
    witness_transition_ids: tuple[int, ...]
    intervention_keys: tuple[str, ...]
    amount_per_transition: tuple[int, ...]
    status: str = "SCHEDULED_BOOKKEEPING_CANDIDATE"


@dataclass(frozen=True)
class CounterPrediction:
    candidate_id: str
    declared_at_transition: int
    expected_rewrite: str
    expected_amount: int
    evidence_basis: tuple[str, ...]


@dataclass(frozen=True)
class CounterComparison:
    candidate_id: str
    outcome: str
    transition_id: int
    observed_amount: int
    support_cells: tuple[tuple[int, int], ...]
    evidence_ref: str


@dataclass(frozen=True)
class MaskLaw:
    law_id: str
    law_version_id: str
    revision: int
    status: str
    cells: tuple[tuple[int, int], ...]
    rewrite: str
    witness_evidence_refs: tuple[str, ...]
    demonstration_ref: str
    reversibility: str = "RAW_GRID_PRESERVED_MASK_IS_DERIVED_VIEW"


@dataclass(frozen=True)
class CounterBoundary:
    outcome: str
    boundary_kind: str | None
    transition_id: int
    source_before: int | None
    source_after: int | None
    replacement_before: int | None
    replacement_after: int | None
    footprint_size: int
    evidence_ref: str


@dataclass(frozen=True)
class CounterMonitorVerdict:
    disposition: str
    reason: str
    transition_id: int
    hud_changed_cells: tuple[tuple[int, int], ...]
    world_changed_cells: tuple[tuple[int, int], ...]


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _intervention_key(outcome: Mapping[str, Any]) -> str:
    action = outcome.get("action")
    if not isinstance(action, Mapping):
        return "UNKNOWN"
    return _canonical({
        "action": action.get("action"),
        "row": action.get("row"),
        "col": action.get("col"),
    })


def _evidence_ref(item: Mapping[str, Any]) -> str:
    return str(item.get("evidence_id") or item.get("lossless_diff_ref") or "").strip()


def _transition_id(item: Mapping[str, Any]) -> int:
    return int(item.get("transition_id") or 0)


def _rewrite_cells(outcome: Mapping[str, Any]) -> dict[str, list[tuple[int, int]]]:
    grouped: dict[str, list[tuple[int, int]]] = defaultdict(list)
    for cell in outcome.get("changed_cells") or ():
        if not isinstance(cell, Mapping):
            continue
        before, after = cell.get("before"), cell.get("after")
        rewrite = f"{before}->{after}"
        grouped[rewrite].append((int(cell["row"]), int(cell["col"])))
    return grouped


def _pair_values(rewrite: str) -> tuple[int, int] | None:
    try:
        left, right = rewrite.split("->", 1)
        return int(left), int(right)
    except (TypeError, ValueError):
        return None


def _connected_from_seeds(
    allowed: set[tuple[int, int]], seeds: set[tuple[int, int]]
) -> set[tuple[int, int]]:
    found = set(seeds) & allowed
    frontier = list(found)
    while frontier:
        row, col = frontier.pop()
        for cell in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
            if cell in allowed and cell not in found:
                found.add(cell)
                frontier.append(cell)
    return found


def _full_pair_footprint(
    rows: Sequence[Mapping[str, Any]],
    rewrite: str,
    support: tuple[tuple[int, int], ...],
) -> tuple[tuple[tuple[int, int], ...], str]:
    """Recover the stable two-class bar containing the moving rewrite front."""
    pair = _pair_values(rewrite)
    if pair is None or not support:
        return support, "OBSERVED_REWRITE_SUPPORT"
    support_set = set(support)
    support_rows = {row for row, _ in support}
    support_cols = {col for _, col in support}
    geometry = (
        "HORIZONTAL_BAR" if len(support_rows) == 1
        else "VERTICAL_BAR" if len(support_cols) == 1
        else "CONNECTED_TWO_CLASS_REGION"
    )
    inferred: list[set[tuple[int, int]]] = []
    for outcome in rows:
        transitions = outcome.get("site_transitions")
        if not isinstance(transitions, (list, tuple)):
            continue
        values = {
            (int(item["row"]), int(item["col"])): int(item["before"])
            for item in transitions
            if isinstance(item, Mapping) and item.get("before") is not None
        }
        allowed = {cell for cell, value in values.items() if value in pair}
        seeds = support_set & set(values)
        if geometry == "HORIZONTAL_BAR":
            row = next(iter(support_rows))
            allowed = {cell for cell in allowed if cell[0] == row}
        elif geometry == "VERTICAL_BAR":
            col = next(iter(support_cols))
            allowed = {cell for cell in allowed if cell[1] == col}
        component = _connected_from_seeds(allowed, seeds)
        if component:
            inferred.append(component)
    if inferred and all(item == inferred[0] for item in inferred[1:]):
        return tuple(sorted(inferred[0])), geometry
    return support, "OBSERVED_REWRITE_SUPPORT"


def compile_counter_candidates(
    evidence: Iterable[Mapping[str, Any]], *, minimum_witnesses: int = 2
) -> tuple[CounterCandidate, ...]:
    """Compile recurrent visible rewrites without calling them counters.

    Qualification is intentionally structural: the same integer rewrite must
    occur on every fixed-geometry transition in the supplied consecutive
    window, the interventions must differ, and no acted coordinate may lie in
    the observed support.  A later gate still has to explain and demonstrate
    the candidate before a MaskLaw can be issued.
    """
    rows = [dict(item) for item in evidence]
    if len(rows) < max(2, int(minimum_witnesses)):
        return ()
    if any(item.get("shape_before") != item.get("shape_after") for item in rows):
        return ()
    refs = tuple(_evidence_ref(item) for item in rows)
    if any(not ref for ref in refs):
        return ()
    intervention_keys = tuple(_intervention_key(item) for item in rows)
    if len(set(intervention_keys)) < 2:
        return ()

    grouped = [_rewrite_cells(item) for item in rows]
    shared = set(grouped[0])
    for item in grouped[1:]:
        shared.intersection_update(item)

    candidates: list[CounterCandidate] = []
    for rewrite in sorted(shared):
        per_step = [item[rewrite] for item in grouped]
        amounts = tuple(len(cells) for cells in per_step)
        if any(amount <= 0 for amount in amounts):
            continue
        support = tuple(sorted({cell for cells in per_step for cell in cells}))
        acted = {
            (int(site["row"]), int(site["col"]))
            for item in rows
            if isinstance((site := item.get("acted_site")), Mapping)
        }
        if acted.intersection(support):
            continue
        pair = _pair_values(rewrite)
        if pair is None:
            continue
        footprint, geometry = _full_pair_footprint(rows, rewrite, support)
        payload = {
            "rewrite": rewrite,
            "support": support,
            "refs": refs,
            "transitions": tuple(_transition_id(item) for item in rows),
        }
        digest = hashlib.sha256(_canonical(payload).encode()).hexdigest()[:16]
        candidates.append(CounterCandidate(
            candidate_id=f"COUNTER-CANDIDATE-{digest}",
            rewrite=rewrite,
            observed_support=support,
            full_bar_footprint=footprint,
            footprint_geometry=geometry,
            source_integer=pair[0],
            replacement_integer=pair[1],
            witness_evidence_refs=refs,
            witness_transition_ids=tuple(_transition_id(item) for item in rows),
            intervention_keys=intervention_keys,
            amount_per_transition=amounts,
        ))
    return tuple(candidates)


def prediction_for(candidate: CounterCandidate, *, declared_at_transition: int) -> CounterPrediction:
    rates = Counter(candidate.amount_per_transition)
    expected = min(rates, key=lambda value: (-rates[value], value))
    return CounterPrediction(
        candidate_id=candidate.candidate_id,
        declared_at_transition=int(declared_at_transition),
        expected_rewrite=candidate.rewrite,
        expected_amount=int(expected),
        evidence_basis=candidate.witness_evidence_refs,
    )


def compare_counter_prediction(
    prediction: CounterPrediction,
    outcome: Mapping[str, Any],
    *,
    evidence_ref: str,
) -> CounterComparison:
    grouped = _rewrite_cells(outcome)
    cells = tuple(sorted(grouped.get(prediction.expected_rewrite, ())))
    transition_id = _transition_id(outcome)
    if transition_id <= prediction.declared_at_transition:
        verdict = "INDETERMINATE"
    elif len(cells) == prediction.expected_amount:
        verdict = "SUPPORTED"
    else:
        verdict = "CONTRADICTED"
    return CounterComparison(
        candidate_id=prediction.candidate_id,
        outcome=verdict,
        transition_id=transition_id,
        observed_amount=len(cells),
        support_cells=cells,
        evidence_ref=str(evidence_ref),
    )


def mask_law_from_supported(
    candidate: CounterCandidate,
    comparison: CounterComparison,
    *,
    revision: int = 1,
) -> MaskLaw:
    if comparison.candidate_id != candidate.candidate_id or comparison.outcome != "SUPPORTED":
        raise ValueError("MaskLaw requires a supported prospective counter comparison.")
    cells = (
        tuple(sorted(set(candidate.full_bar_footprint) | set(comparison.support_cells)))
        if candidate.footprint_geometry == "OBSERVED_REWRITE_SUPPORT"
        else candidate.full_bar_footprint
    )
    payload = {
        "candidate": asdict(candidate),
        "comparison": asdict(comparison),
        "cells": cells,
        "revision": int(revision),
    }
    digest = hashlib.sha256(_canonical(payload).encode()).hexdigest()[:16]
    return MaskLaw(
        law_id=f"MASK-{candidate.candidate_id.split('-')[-1]}",
        law_version_id=f"MASK-V{int(revision)}-{digest}",
        revision=int(revision),
        status="OBSERVED",
        cells=cells,
        rewrite=candidate.rewrite,
        witness_evidence_refs=candidate.witness_evidence_refs,
        demonstration_ref=comparison.evidence_ref,
    )


def _standing(
    outcome: Mapping[str, Any], candidate: CounterCandidate, side: str
) -> tuple[int, int] | None:
    transitions = outcome.get("site_transitions")
    if not isinstance(transitions, (list, tuple)):
        return None
    field = "before" if side == "before" else "after"
    values = {
        (int(item["row"]), int(item["col"])): item.get(field)
        for item in transitions
        if isinstance(item, Mapping)
    }
    if any(cell not in values or values[cell] is None for cell in candidate.full_bar_footprint):
        return None
    source = sum(
        int(values[cell]) == candidate.source_integer
        for cell in candidate.full_bar_footprint
    )
    replacement = sum(
        int(values[cell]) == candidate.replacement_integer
        for cell in candidate.full_bar_footprint
    )
    return source, replacement


def compare_counter_boundary(
    candidate: CounterCandidate,
    outcome: Mapping[str, Any],
    *,
    evidence_ref: str,
    prior_standing: tuple[int, int] | None,
) -> CounterBoundary:
    """Lock only when counter extrema coincide with game-over or respawn."""
    before = _standing(outcome, candidate, "before")
    after = _standing(outcome, candidate, "after")
    boundary = outcome.get("boundary_event")
    boundary = boundary if isinstance(boundary, Mapping) else {}
    state = str(boundary.get("state") or "").upper()
    game_over = bool(boundary.get("game_over") or boundary.get("done")) or "GAME_OVER" in state
    footprint_size = len(candidate.full_bar_footprint)
    reached_extrema = bool(
        after is not None and after[0] == 0 and after[1] == footprint_size
    )
    respawned = bool(
        prior_standing is not None
        and after is not None
        and prior_standing[0] <= max(candidate.amount_per_transition)
        and after[0] > prior_standing[0]
        and after[1] < prior_standing[1]
    )
    if game_over and reached_extrema:
        verdict, kind = "SUPPORTED", "GAME_OVER_AT_SOURCE_MIN_REPLACEMENT_MAX"
    elif respawned:
        verdict, kind = "SUPPORTED", "RESPAWN_AFTER_SOURCE_MIN_REPLACEMENT_MAX"
    else:
        verdict, kind = "PENDING", None
    return CounterBoundary(
        outcome=verdict,
        boundary_kind=kind,
        transition_id=_transition_id(outcome),
        source_before=None if before is None else before[0],
        source_after=None if after is None else after[0],
        replacement_before=None if before is None else before[1],
        replacement_after=None if after is None else after[1],
        footprint_size=footprint_size,
        evidence_ref=str(evidence_ref),
    )


def counter_standing(
    candidate: CounterCandidate, outcome: Mapping[str, Any]
) -> tuple[int, int] | None:
    return _standing(outcome, candidate, "after")


def monitor_locked_counter(
    candidate: CounterCandidate,
    law: MaskLaw,
    outcome: Mapping[str, Any],
) -> CounterMonitorVerdict:
    """Validate a later transition against a locked counter law."""
    mask = set(law.cells)
    acted = outcome.get("acted_site")
    acted_cell = (
        (int(acted["row"]), int(acted["col"]))
        if isinstance(acted, Mapping) else None
    )
    changed = [item for item in outcome.get("changed_cells") or () if isinstance(item, Mapping)]
    hud_rows = [
        item for item in changed
        if (int(item["row"]), int(item["col"])) in mask
    ]
    world_cells = tuple(sorted(
        (int(item["row"]), int(item["col"]))
        for item in changed
        if (int(item["row"]), int(item["col"])) not in mask
    ))
    hud_cells = tuple(sorted(
        (int(item["row"]), int(item["col"])) for item in hud_rows
    ))
    disposition, reason = "VALID", "LOCKED_COUNTER_TICK"
    if acted_cell in mask:
        disposition, reason = "REOPEN", "COUNTER_DIRECTLY_TARGETED"
    elif not hud_rows:
        disposition, reason = "REOPEN", "LOCKED_COUNTER_UNEXPECTEDLY_HELD"
    else:
        standing_before = _standing(outcome, candidate, "before")
        standing_after = _standing(outcome, candidate, "after")
        respawn = bool(
            standing_before is not None
            and standing_after is not None
            and standing_before[0] == 0
            and standing_before[1] == len(candidate.full_bar_footprint)
            and standing_after[0] > standing_before[0]
            and standing_after[1] < standing_before[1]
        )
        if respawn:
            reason = "LOCKED_COUNTER_RESPAWN"
        else:
            expected = (candidate.source_integer, candidate.replacement_integer)
            arcs = [(int(item["before"]), int(item["after"])) for item in hud_rows]
            if any(arc != expected for arc in arcs):
                disposition, reason = "REOPEN", "COUNTER_ARITHMETIC_CHANGED_OR_ENTANGLED"
            elif len(arcs) not in set(candidate.amount_per_transition):
                disposition, reason = "REOPEN", "COUNTER_RATE_CHANGED"
    return CounterMonitorVerdict(
        disposition=disposition,
        reason=reason,
        transition_id=_transition_id(outcome),
        hud_changed_cells=hud_cells,
        world_changed_cells=world_cells,
    )


def masked_grid(
    grid: Sequence[Sequence[int]], law: MaskLaw
) -> tuple[tuple[int | str, ...], ...]:
    """Return a derived masked view; never mutate or discard the raw grid."""
    hidden = set(law.cells)
    return tuple(
        tuple(MASK_SENTINEL if (row, col) in hidden else int(value) for col, value in enumerate(values))
        for row, values in enumerate(grid)
    )


def trigger_record(
    lossless_outcomes: Iterable[Mapping[str, Any]], footprint: Iterable[tuple[int, int]]
) -> dict[str, Any]:
    """Axiom A1 (v2): the trigger class the whole record supports for the active candidate.

    A transition *ticks* when a footprint cell changes, and is *effective* when any cell
    outside the footprint changes. EVERY_TRANSITION: it ticked on transitions that changed
    nothing else, and never failed to tick. EFFECTIVE_TRANSITIONS_ONLY: it ticked on every
    effective transition and on none that changed nothing else. OPEN: only effective, ticking
    transitions so far, so the record cannot yet tell those two apart. IRREGULAR: anything
    else. The record's class is always an admissible claim, so this check never deadlocks.
    """
    footprint = set(footprint)
    outcomes = list(lossless_outcomes)
    transitions = len(outcomes)
    counts = {
        "effective_transitions_with_tick": 0,
        "effective_transitions_without_tick": 0,
        "null_transitions_with_tick": 0,
        "null_transitions_without_tick": 0,
    }
    for outcome in outcomes:
        cells = [
            (int(item["row"]), int(item["col"]))
            for item in outcome.get("changed_cells") or ()
            if isinstance(item, Mapping)
        ]
        tick = any(cell in footprint for cell in cells)
        effective = any(cell not in footprint for cell in cells)
        key = ("effective" if effective else "null") + (
            "_transitions_with_tick" if tick else "_transitions_without_tick"
        )
        counts[key] += 1
    if counts["effective_transitions_without_tick"] == 0 and counts["null_transitions_without_tick"] == 0:
        trigger = "EVERY_TRANSITION" if counts["null_transitions_with_tick"] else "OPEN"
    elif (
        counts["effective_transitions_without_tick"] == 0
        and counts["null_transitions_with_tick"] == 0
        and counts["effective_transitions_with_tick"] > 0
    ):
        trigger = "EFFECTIVE_TRANSITIONS_ONLY"
    else:
        trigger = "IRREGULAR"
    admissible = (
        ["EVERY_TRANSITION", "EFFECTIVE_TRANSITIONS_ONLY"] if trigger == "OPEN" else [trigger]
    )
    return {
        "class": trigger,
        "admissible_claims": admissible,
        "null_transitions_without_tick": counts["null_transitions_without_tick"],
        "null_transitions_with_tick": counts["null_transitions_with_tick"],
        "effective_transitions_with_tick": counts["effective_transitions_with_tick"],
        "effective_transitions_without_tick": counts["effective_transitions_without_tick"],
        "transition_count": transitions,
    }
