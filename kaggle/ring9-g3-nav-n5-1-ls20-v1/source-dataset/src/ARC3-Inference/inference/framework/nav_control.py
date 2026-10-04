"""Compile the embodied controller's route bearings from verified G1 evidence.

No action number receives a semantic direction.  A bearing enters this map
only when G1 retained a structured displacement and the supported prospective
demonstration observed that same displacement.

Author: Sol (Alpha build seat), 2026-10-01.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from inference.framework.masked_world_state import grids_from_probe_outcome


@dataclass(frozen=True)
class NavControlMap:
    bearings: tuple[tuple[str, tuple[int, int]], ...]
    evidence_refs: tuple[tuple[str, str], ...]
    unresolved_actions: tuple[str, ...]
    ego_shape: tuple[tuple[int, int], ...]

    def bearing_map(self) -> dict[str, tuple[int, int]]:
        return dict(self.bearings)


def _shape(cells):
    cells = tuple(sorted(tuple(map(int, cell)) for cell in cells))
    if not cells:
        return ()
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple((r-r0, c-c0) for r, c in cells)


def _pattern(grid, cells):
    r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
    return tuple(sorted((r-r0, c-c0, int(grid[r][c])) for r, c in cells))


def _occurrences(grid, pattern):
    if not grid or not pattern:
        return ()
    height, width = len(grid), len(grid[0])
    max_r = max(r for r, _, _ in pattern)
    max_c = max(c for _, c, _ in pattern)
    found = []
    for ar in range(height-max_r):
        for ac in range(width-max_c):
            if all(int(grid[ar+r][ac+c]) == value for r, c, value in pattern):
                found.append((ar, ac))
    return tuple(found)


def _observed_delta(outcome, pattern):
    grids = grids_from_probe_outcome(outcome)
    if grids is None:
        return None
    before, after = grids
    left, right = _occurrences(before, pattern), _occurrences(after, pattern)
    changed = {(int(x["row"]), int(x["col"])) for x in outcome.get("changed_cells", ())
               if isinstance(x, Mapping)}
    candidates = []
    shape = {(r, c) for r, c, _ in pattern}
    for p in left:
        for q in right:
            delta = (q[0]-p[0], q[1]-p[1])
            if delta == (0, 0):
                continue
            occupied = {(p[0]+r, p[1]+c) for r, c in shape} | {(q[0]+r, q[1]+c) for r, c in shape}
            if changed & occupied:
                candidates.append(delta)
    return candidates[0] if candidates and len(set(candidates)) == 1 else None


def compile_nav_control_map(ego: Any) -> NavControlMap:
    answer = getattr(ego, "answer", None)
    comparison = getattr(ego, "last_comparison", None)
    specs: Mapping[str, Mapping[str, Any]] = getattr(answer, "action_law_specs", {}) or {}
    available = tuple(sorted(item.action for item in getattr(ego, "affordances", ())
                             if item.action in getattr(ego, "_currently_available", set())))
    bearings: dict[str, tuple[int, int]] = {}
    refs: dict[str, str] = {}
    demonstrated_action = None
    demonstrated_delta = None
    if comparison is not None and getattr(comparison, "outcome", None) == "SUPPORTED":
        pending = getattr(ego, "pending_prediction", None)
        demonstrated_action = getattr(getattr(pending, "action", None), "action", None)
        demonstrated_delta = getattr(comparison, "observed_translation", None)
    for action, spec in specs.items():
        raw = spec.get("displacement")
        if not isinstance(raw, (list, tuple)) or len(raw) != 2:
            continue
        delta = (int(raw[0]), int(raw[1]))
        # The prospective demonstration directly certifies one law. Other laws
        # remain unresolved until their own structured evidence is added.
        if action == demonstrated_action and delta == demonstrated_delta and delta != (0, 0):
            bearings[action] = delta
            refs[action] = str(getattr(comparison, "comparison_id", ""))
    footprint, _ = ego.embodied_ego_binding()
    # Mine the paired opening probes themselves.  We search for the exact
    # demonstrated multi-integer ego pattern before and after each transition;
    # a bearing is admitted only when the translation is unique in that frame.
    current = ego.current_grid()
    pattern = _pattern(current, footprint) if footprint else ()
    for index, outcome in enumerate(getattr(ego, "_lossless_outcomes", ())):
        raw_action = outcome.get("action") or {}
        action = str(raw_action.get("action") if isinstance(raw_action, Mapping) else raw_action).upper()
        if action not in available or action in bearings:
            continue
        delta = _observed_delta(outcome, pattern)
        if delta is not None:
            bearings[action] = delta
            evidence = next((row for row in getattr(ego, "evidence", ())
                             if row.get("probe_id") == outcome.get("probe_id")), None)
            refs[action] = str((evidence or {}).get("evidence_id") or f"G1-OUTCOME-{index+1}")
    return NavControlMap(tuple(sorted(bearings.items())), tuple(sorted(refs.items())),
                         tuple(action for action in available if action not in bearings), _shape(footprint))


__all__ = ["NavControlMap", "compile_nav_control_map"]
