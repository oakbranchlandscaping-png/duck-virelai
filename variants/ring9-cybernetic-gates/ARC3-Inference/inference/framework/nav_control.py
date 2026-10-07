"""Compile embodied route bearings from observed cell-site flow.

A visual object is represented by its complete set of observed cell sites. G1
may ask Duck to describe that object, but route control never depends on Duck
serialising every site or direction into prose. Exact component translations
in the paired opening probes identify the demonstrated ego family, its complete
footprint, and the opaque action-to-displacement map.

Author: Sol (Alpha build seat), 2026-10-06.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.masked_world_state import grids_from_probe_outcome


Cell = tuple[int, int]
Signature = tuple[int, tuple[Cell, ...]]


@dataclass(frozen=True)
class NavControlMap:
    bearings: tuple[tuple[str, tuple[int, int]], ...]
    evidence_refs: tuple[tuple[str, str], ...]
    unresolved_actions: tuple[str, ...]
    ego_shape: tuple[Cell, ...]
    ego_cells: tuple[Cell, ...] = ()
    binding_source: str = "EGO_FOOTPRINT_UNAVAILABLE"

    def bearing_map(self) -> dict[str, tuple[int, int]]:
        return dict(self.bearings)


@dataclass(frozen=True)
class _MovedComponent:
    integer: int
    before: tuple[Cell, ...]
    after: tuple[Cell, ...]
    delta: Cell

    @property
    def signature(self) -> Signature:
        return self.integer, _shape(self.before)


def _shape(cells: Iterable[Cell]) -> tuple[Cell, ...]:
    cells = tuple(sorted((int(row), int(col)) for row, col in cells))
    if not cells:
        return ()
    row0 = min(row for row, _ in cells)
    col0 = min(col for _, col in cells)
    return tuple((row - row0, col - col0) for row, col in cells)


def _components(grid: Sequence[Sequence[int]]) -> dict[int, tuple[tuple[Cell, ...], ...]]:
    """Return every four-connected same-integer component as cell sites."""
    height = len(grid)
    seen: set[Cell] = set()
    found: dict[int, list[tuple[Cell, ...]]] = defaultdict(list)
    for row, values in enumerate(grid):
        for col, raw in enumerate(values):
            seed = (row, col)
            if seed in seen:
                continue
            integer = int(raw)
            cells = {seed}
            seen.add(seed)
            frontier = [seed]
            while frontier:
                here_row, here_col = frontier.pop()
                for there_row, there_col in (
                    (here_row - 1, here_col), (here_row + 1, here_col),
                    (here_row, here_col - 1), (here_row, here_col + 1),
                ):
                    there = (there_row, there_col)
                    if (
                        0 <= there_row < height
                        and 0 <= there_col < len(grid[there_row])
                        and there not in seen
                        and int(grid[there_row][there_col]) == integer
                    ):
                        seen.add(there)
                        cells.add(there)
                        frontier.append(there)
            found[integer].append(tuple(sorted(cells)))
    return {integer: tuple(rows) for integer, rows in found.items()}


def _translated(left: tuple[Cell, ...], right: tuple[Cell, ...]) -> Cell | None:
    if len(left) != len(right) or _shape(left) != _shape(right):
        return None
    delta = (right[0][0] - left[0][0], right[0][1] - left[0][1])
    if delta == (0, 0):
        return None
    moved = {(row + delta[0], col + delta[1]) for row, col in left}
    return delta if moved == set(right) else None


def _moved_components(outcome: Mapping[str, Any]) -> tuple[_MovedComponent, ...]:
    grids = grids_from_probe_outcome(outcome)
    if grids is None:
        return ()
    before, after = grids
    changed = {
        (int(item["row"]), int(item["col"]))
        for item in outcome.get("changed_cells") or ()
        if isinstance(item, Mapping) and "row" in item and "col" in item
    }
    before_components = _components(before)
    after_components = _components(after)
    candidates: list[_MovedComponent] = []
    for integer, left_rows in before_components.items():
        for left in left_rows:
            for right in after_components.get(integer, ()):
                delta = _translated(left, right)
                if delta is None or not (changed & (set(left) | set(right))):
                    continue
                candidates.append(_MovedComponent(integer, left, right, delta))
    # Do not invent a correspondence when duplicate equal-shape components make
    # either end ambiguous. A later paired probe can still establish it.
    left_counts = Counter((item.integer, item.before) for item in candidates)
    right_counts = Counter((item.integer, item.after) for item in candidates)
    return tuple(
        item for item in candidates
        if left_counts[(item.integer, item.before)] == 1
        and right_counts[(item.integer, item.after)] == 1
    )


def _action_name(outcome: Mapping[str, Any]) -> str:
    raw = outcome.get("action") or {}
    return str(raw.get("action") if isinstance(raw, Mapping) else raw).upper()


def _evidence_ref(ego: Any, outcome: Mapping[str, Any], index: int) -> str:
    evidence = next(
        (row for row in getattr(ego, "evidence", ()) if row.get("probe_id") == outcome.get("probe_id")),
        None,
    )
    return str((evidence or {}).get("evidence_id") or f"G1-OUTCOME-{index + 1}")


def _demonstrated_family(ego: Any, rows: Sequence[Mapping[str, Any]]) -> Counter[Signature]:
    comparison = getattr(ego, "last_comparison", None)
    if comparison is None or getattr(comparison, "outcome", None) != "SUPPORTED":
        return Counter()
    raw_delta = getattr(comparison, "observed_translation", None)
    if raw_delta is None:
        return Counter()
    delta = tuple(map(int, raw_delta))
    anchors = set(tuple(map(int, cell)) for cell in getattr(comparison, "after_footprint", ()) or ())
    pending = getattr(ego, "pending_prediction", None)
    action = str(getattr(getattr(pending, "action", None), "action", "")).upper()
    for outcome in reversed(rows):
        if _action_name(outcome) != action:
            continue
        moved = tuple(item for item in _moved_components(outcome) if item.delta == delta)
        if not moved:
            continue
        # Duck may name only representative sites. They select the translated
        # component family; the controller retains every site in those components.
        selected = (
            tuple(item for item in moved if anchors & set(item.after))
            if anchors else moved
        )
        if not selected or (
            anchors and not anchors <= {cell for item in selected for cell in item.after}
        ):
            continue
        return Counter(item.signature for item in selected)
    return Counter()


def _matching_group(
    outcome: Mapping[str, Any], family: Counter[Signature]
) -> tuple[Cell, tuple[_MovedComponent, ...]] | None:
    by_delta: dict[Cell, list[_MovedComponent]] = defaultdict(list)
    for item in _moved_components(outcome):
        by_delta[item.delta].append(item)
    matches: list[tuple[Cell, tuple[_MovedComponent, ...]]] = []
    for delta, items in by_delta.items():
        remaining = Counter(family)
        chosen: list[_MovedComponent] = []
        for item in items:
            if remaining[item.signature] > 0:
                remaining[item.signature] -= 1
                chosen.append(item)
        if not +remaining:
            matches.append((delta, tuple(chosen)))
    return matches[0] if len(matches) == 1 else None


def compile_nav_control_map(ego: Any) -> NavControlMap:
    """Recover opaque bearings and the complete ego site set from paired G1 probes."""
    rows = tuple(getattr(ego, "_lossless_outcomes", ()) or ())
    available = tuple(sorted(
        item.action for item in getattr(ego, "affordances", ())
        if item.action in getattr(ego, "_currently_available", set())
    ))
    comparison = getattr(ego, "last_comparison", None)
    cache_key = (
        int(getattr(ego, "revision", 0)),
        len(rows),
        str(getattr(comparison, "comparison_id", "")),
        available,
    )
    cached = getattr(ego, "_nav_control_cache", None)
    if cached is not None and cached[0] == cache_key:
        return cached[1]
    family = _demonstrated_family(ego, rows)
    observations: dict[str, list[tuple[Cell, tuple[_MovedComponent, ...], str]]] = defaultdict(list)
    for index, outcome in enumerate(rows):
        match = _matching_group(outcome, family) if family else None
        action = _action_name(outcome)
        if match is not None and action in available:
            observations[action].append((match[0], match[1], _evidence_ref(ego, outcome, index)))

    bearings: dict[str, Cell] = {}
    refs: dict[str, str] = {}
    latest_cells: tuple[Cell, ...] = ()
    latest_index = -1
    pending = getattr(ego, "pending_prediction", None)
    demonstrated_action = str(getattr(getattr(pending, "action", None), "action", "")).upper()
    supported = comparison is not None and getattr(comparison, "outcome", None) == "SUPPORTED"
    # Preserve a genuinely structured, prospectively supported G1 law. This is
    # an additional direct evidence channel; prose action descriptions are not.
    answer = getattr(ego, "answer", None)
    specs: Mapping[str, Mapping[str, Any]] = getattr(answer, "action_law_specs", {}) or {}
    demonstrated_delta = getattr(comparison, "observed_translation", None) if supported else None
    for action, spec in specs.items():
        raw = spec.get("displacement")
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            continue
        delta = (int(raw[0]), int(raw[1]))
        if action == demonstrated_action and delta == demonstrated_delta and delta != (0, 0):
            bearings[action] = delta
            refs[action] = str(getattr(comparison, "comparison_id", ""))
    for action, seen in observations.items():
        deltas = {delta for delta, _items, _ref in seen}
        # Paired opening probes certify ordinary bearings. The prospective
        # comparison itself certifies its demonstrated action.
        if len(deltas) != 1 or (len(seen) < 2 and not (supported and action == demonstrated_action)):
            continue
        bearings[action] = next(iter(deltas))
        refs[action] = seen[-1][2]
        for index, outcome in enumerate(rows):
            if _action_name(outcome) != action:
                continue
            match = _matching_group(outcome, family)
            if match is not None and index >= latest_index:
                latest_index = index
                latest_cells = tuple(sorted(cell for item in match[1] for cell in item.after))

    result = NavControlMap(
        tuple(sorted(bearings.items())),
        tuple(sorted(refs.items())),
        tuple(action for action in available if action not in bearings),
        _shape(latest_cells),
        latest_cells,
        "DETERMINISTIC_CELL_SITE_TRANSLATION" if latest_cells else "EGO_FOOTPRINT_UNAVAILABLE",
    )
    try:
        setattr(ego, "_nav_control_cache", (cache_key, result))
    except (AttributeError, TypeError):
        pass
    return result


__all__ = ["NavControlMap", "compile_nav_control_map"]
