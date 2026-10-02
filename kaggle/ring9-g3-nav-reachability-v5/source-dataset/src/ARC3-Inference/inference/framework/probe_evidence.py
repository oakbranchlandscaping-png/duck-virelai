"""Production-shaped before/action/after evidence for cybernetic probes.

The compiler reports integer-grid observations.  It does not assign semantic
roles such as ego, counter, lever, wall, or goal.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence

from inference.agent.runtime_state import Frame, frame_to_payload


EVIDENCE_SCHEMA = "virelai-probe-outcome-v1"


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def frame_ref(frame: Frame | None) -> str | None:
    if frame is None:
        return None
    digest = hashlib.sha256(_canonical(frame_to_payload(frame)).encode("utf-8")).hexdigest()[:20]
    return f"F-{digest}"


def _value(grid: Sequence[Sequence[int]], row: int, col: int) -> int | None:
    if row < 0 or row >= len(grid) or col < 0 or col >= len(grid[row]):
        return None
    return int(grid[row][col])


def _changed_cells(
    before: Sequence[Sequence[int]], after: Sequence[Sequence[int]]
) -> list[dict[str, Any]]:
    height = max(len(before), len(after))
    width = max(
        max((len(row) for row in before), default=0),
        max((len(row) for row in after), default=0),
    )
    changed: list[dict[str, Any]] = []
    for row in range(height):
        for col in range(width):
            old = _value(before, row, col)
            new = _value(after, row, col)
            if old != new:
                changed.append({"row": row, "col": col, "before": old, "after": new})
    return changed


def _site_transitions(
    before: Sequence[Sequence[int]], after: Sequence[Sequence[int]]
) -> list[dict[str, Any]] | None:
    """Return the total fixed-geometry site ledger, including held cells.

    A changed-cell diff cannot verify an overlapping translation because cells
    in the overlap may retain their integer.  Geometry changes have no total
    site correspondence and are represented as typed absence.
    """
    before_shape = (len(before), tuple(len(row) for row in before))
    after_shape = (len(after), tuple(len(row) for row in after))
    if before_shape != after_shape:
        return None
    return [
        {
            "row": row,
            "col": col,
            "before": int(before[row][col]),
            "after": int(after[row][col]),
            "outcome": (
                "HELD" if int(before[row][col]) == int(after[row][col]) else "CHANGED"
            ),
        }
        for row in range(len(before))
        for col in range(len(before[row]))
    ]


def _bbox(cells: Iterable[Mapping[str, Any]]) -> dict[str, int] | None:
    points = [(int(item["row"]), int(item["col"])) for item in cells]
    if not points:
        return None
    rows = [row for row, _ in points]
    cols = [col for _, col in points]
    return {
        "min_row": min(rows),
        "min_col": min(cols),
        "max_row": max(rows),
        "max_col": max(cols),
    }


def _transition_key(before: int | None, after: int | None) -> str:
    left = "MISSING" if before is None else str(before)
    right = "MISSING" if after is None else str(after)
    return f"{left}->{right}"


def _transition_counts(cells: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    counts = Counter(_transition_key(item.get("before"), item.get("after")) for item in cells)
    return dict(sorted(counts.items()))


def _connected_scope(
    grid: Sequence[Sequence[int]], row: int, col: int
) -> set[tuple[int, int]] | None:
    seed = _value(grid, row, col)
    if seed is None:
        return None
    seen = {(row, col)}
    frontier = [(row, col)]
    while frontier:
        current_row, current_col = frontier.pop()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            neighbor = current_row + dr, current_col + dc
            if neighbor in seen:
                continue
            if _value(grid, *neighbor) == seed:
                seen.add(neighbor)
                frontier.append(neighbor)
    return seen


def _changed_regions(cells: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_point = {(int(item["row"]), int(item["col"])): item for item in cells}
    remaining = set(by_point)
    regions: list[dict[str, Any]] = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        component = {seed}
        frontier = [seed]
        while frontier:
            row, col = frontier.pop()
            for point in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if point in remaining:
                    remaining.remove(point)
                    component.add(point)
                    frontier.append(point)
        region_cells = [by_point[point] for point in sorted(component)]
        regions.append({
            "size": len(region_cells),
            "bbox": _bbox(region_cells),
            "integer_transition_counts": _transition_counts(region_cells),
        })
    return sorted(
        regions,
        key=lambda item: (
            item["bbox"]["min_row"], item["bbox"]["min_col"], item["size"]
        ),
    )


def compile_probe_outcome(
    *,
    probe_id: str,
    transition_id: int,
    action: Mapping[str, Any],
    before_frame: Frame | None,
    after_frame: Frame | None,
    available_actions_before: Sequence[str],
    available_actions_after: Sequence[str],
    callback_payload: Mapping[str, Any],
) -> dict[str, Any]:
    limitations: list[str] = []
    before_grid = before_frame.grid if before_frame is not None else ()
    after_grid = after_frame.grid if after_frame is not None else ()
    if before_frame is None:
        limitations.append("before frame unavailable")
    if after_frame is None:
        limitations.append("after frame unavailable")

    changed = _changed_cells(before_grid, after_grid)
    site_transitions = _site_transitions(before_grid, after_grid)
    computed_board_changed = bool(changed)
    reported_board_changed = bool(callback_payload.get("board_changed"))
    if computed_board_changed != reported_board_changed:
        limitations.append("callback board_changed disagrees with captured frames")

    shape_before = list(before_frame.shape) if before_frame is not None else None
    shape_after = list(after_frame.shape) if after_frame is not None else None
    if shape_before != shape_after:
        limitations.append("grid shape changed across the transition")

    acted_site = None
    target_scope = None
    local_changes: list[dict[str, Any]] | None = None
    remote_changes: list[dict[str, Any]] | None = None
    if isinstance(action.get("row"), int) and isinstance(action.get("col"), int):
        row, col = int(action["row"]), int(action["col"])
        acted_site = {"row": row, "col": col}
        scope = _connected_scope(before_grid, row, col)
        if scope is None:
            limitations.append("acted site is outside the captured before frame")
        else:
            scope_cells = [{"row": r, "col": c} for r, c in sorted(scope)]
            target_scope = {
                "kind": "BEFORE_EQUAL_INTEGER_COMPONENT",
                "cell_count": len(scope),
                "bbox": _bbox(scope_cells),
            }
            local_changes = [
                item for item in changed if (int(item["row"]), int(item["col"])) in scope
            ]
            remote_changes = [
                item for item in changed if (int(item["row"]), int(item["col"])) not in scope
            ]
    else:
        limitations.append("non-coordinate action has no acted-site scope; local/remote split unavailable")

    diff_digest = hashlib.sha256(
        _canonical({"probe_id": probe_id, "changed_cells": changed}).encode("utf-8")
    ).hexdigest()[:20]
    return {
        "schema": EVIDENCE_SCHEMA,
        "probe_id": probe_id,
        "transition_id": int(transition_id),
        "before_frame_ref": frame_ref(before_frame),
        "after_frame_ref": frame_ref(after_frame),
        "lossless_diff_ref": f"D-{diff_digest}",
        "action": dict(action),
        "acted_site": acted_site,
        "shape_before": shape_before,
        "shape_after": shape_after,
        "board_changed": computed_board_changed,
        "reported_board_changed": reported_board_changed,
        "changed_cell_count": len(changed),
        "changed_cells": changed,
        "changed_bbox": _bbox(changed),
        "integer_transition_counts": _transition_counts(changed),
        "changed_region_summaries": _changed_regions(changed),
        "site_transition_coverage": (
            "TOTAL" if site_transitions is not None else "UNDEFINED_ACROSS_GEOMETRY_CHANGE"
        ),
        "site_transitions": site_transitions,
        "target_scope": target_scope,
        "target_local_changed_cell_count": None if local_changes is None else len(local_changes),
        "target_local_changes": local_changes,
        "remote_changed_cell_count": None if remote_changes is None else len(remote_changes),
        "remote_changes": remote_changes,
        "unscoped_changed_cell_count": len(changed) if target_scope is None else 0,
        "available_actions_before": list(available_actions_before),
        "available_actions_after": list(available_actions_after),
        "boundary_event": {
            "state": callback_payload.get("state"),
            "done": bool(callback_payload.get("done")),
            "level_completed": bool(callback_payload.get("level_completed")),
            "game_over": bool(callback_payload.get("game_over")),
            "run_complete": bool(callback_payload.get("run_complete")),
            "level_before": before_frame.level if before_frame is not None else None,
            "level_after": after_frame.level if after_frame is not None else callback_payload.get("level"),
        },
        "limitations": limitations,
    }


def compact_probe_outcome(outcome: Mapping[str, Any], *, preview_limit: int = 12) -> dict[str, Any]:
    compact = dict(outcome)
    changed = list(compact.pop("changed_cells", []) or [])
    site_transitions = compact.pop("site_transitions", None)
    local = compact.pop("target_local_changes", None)
    remote = compact.pop("remote_changes", None)
    compact["changed_cells_preview"] = changed[:preview_limit]
    compact["changed_cells_truncated"] = len(changed) > preview_limit
    compact["site_transitions_omitted"] = (
        None if site_transitions is None else len(site_transitions)
    )
    compact["target_local_changes_preview"] = (
        None if local is None else list(local)[:preview_limit]
    )
    compact["remote_changes_preview"] = (
        None if remote is None else list(remote)[:preview_limit]
    )
    return compact


def frame_archive_rows(before_frame: Frame | None, after_frame: Frame | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role, frame in (("before", before_frame), ("after", after_frame)):
        if frame is None:
            continue
        rows.append({
            "schema": "virelai-probe-frame-v1",
            "role": role,
            "frame_ref": frame_ref(frame),
            "frame": frame_to_payload(frame),
        })
    return rows
