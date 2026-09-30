"""Joint pixel arithmetic for one action-attributed control.

The lever residue has already subtracted ego, ground, and sealed counter cells.
This module keeps each press intact and asks what transformation the remaining
pixels underwent together.  It names no role and infers no purpose.
"""
from __future__ import annotations

from collections import Counter
from statistics import median
from typing import Any, Sequence


def _components(cells: Sequence[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    groups = []
    while remaining:
        seed = min(remaining)
        remaining.remove(seed)
        group, frontier = {seed}, [seed]
        while frontier:
            row, col = frontier.pop()
            for neighbor in ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    group.add(neighbor)
                    frontier.append(neighbor)
        groups.append(group)
    return groups


def _component_record(before: Any, after: Any, cells: set[tuple[int, int]], step: int) -> dict[str, Any]:
    rows, cols = [cell[0] for cell in cells], [cell[1] for cell in cells]
    before_values = {int(before[cell]) for cell in cells}
    after_values = {int(after[cell]) for cell in cells}
    return {
        "step": step,
        "bbox": [min(rows), min(cols), max(rows), max(cols)],
        "height": max(rows) - min(rows) + 1,
        "width": max(cols) - min(cols) + 1,
        "cells": len(cells),
        "before_class": next(iter(before_values)) if len(before_values) == 1 else None,
        "after_class": next(iter(after_values)) if len(after_values) == 1 else None,
    }


def _decompose(components: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    by_geometry: dict[tuple[int, int, int], list[dict[str, Any]]] = {}
    for row in components:
        by_geometry.setdefault((row["height"], row["width"], row["cells"]), []).append(row)
    out = []
    for geometry, rows in sorted(by_geometry.items()):
        per_step = Counter(row["step"] for row in rows)
        uniform = all(row["before_class"] is not None and row["after_class"] is not None for row in rows)
        rewrites = Counter((row["before_class"], row["after_class"]) for row in rows if uniform)
        ordered = sorted(rows, key=lambda row: (row["step"], row["bbox"]))
        bearings = []
        if all(count == 1 for count in per_step.values()) and len(ordered) > 1:
            for left, right in zip(ordered, ordered[1:]):
                if right["step"] == left["step"] + 1:
                    bearings.append((
                        right["bbox"][0] - left["bbox"][0],
                        right["bbox"][1] - left["bbox"][1],
                    ))
        stable_bearing = bearings[0] if bearings and len(set(bearings)) == 1 else None
        if stable_bearing not in (None, (0, 0)) and len(set(rewrites)) == 1:
            kind = "DIRECTIONAL_REWRITE_FRONT"
        elif max(per_step.values(), default=0) > 1 and uniform:
            kind = "COORDINATED_TILE_RECOLOR"
        elif uniform:
            kind = "UNIFORM_COMPONENT_REWRITE_GROUP"
        else:
            kind = "NONUNIFORM_COMPONENT_CHANGE_GROUP"
        out.append({
            "kind": kind,
            "component_shape": [geometry[0], geometry[1]],
            "component_cells": geometry[2],
            "components_observed": len(rows),
            "presses_observed": len(per_step),
            "components_per_press": {
                "min": min(per_step.values()),
                "median": median(per_step.values()),
                "max": max(per_step.values()),
            },
            "class_rewrites": [
                {"before_class": left, "after_class": right, "observations": count}
                for (left, right), count in sorted(rewrites.items())
            ],
            "bearing": list(stable_bearing) if stable_bearing is not None else None,
            "example_bboxes": [row["bbox"] for row in ordered[:6]],
        })
    return out


def _rewrite(before: Any, after: Any, cells: Sequence[tuple[int, int]]) -> dict[str, Any]:
    arcs: Counter[tuple[int, int]] = Counter()
    before_mass: Counter[int] = Counter()
    after_mass: Counter[int] = Counter()
    for row, col in cells:
        left, right = int(before[row, col]), int(after[row, col])
        before_mass[left] += 1
        after_mass[right] += 1
        if left != right:
            arcs[(left, right)] += 1
    return {
        "changed_cells": sum(arcs.values()),
        "class_multiset_conserved": before_mass == after_mass,
        "rewrites": [
            {"before_class": left, "after_class": right, "cells": count}
            for (left, right), count in sorted(arcs.items())
        ],
        "signed_class_delta": [
            [class_id, after_mass[class_id] - before_mass[class_id]]
            for class_id in sorted(set(before_mass) | set(after_mass))
            if after_mass[class_id] != before_mass[class_id]
        ],
    }


def _period(states: Sequence[tuple[int, ...]]) -> int | None:
    # Two complete periods are required. A single return remains untyped.
    for period in range(2, len(states) // 2 + 1):
        if all(states[index] == states[index - period] for index in range(period, len(states))):
            return period
    return None


def compile_joint_transformation(
    record: Any,
    presses: Sequence[Any],
    actor: int,
    *,
    component_boxes: Sequence[Sequence[int]] = (),
) -> dict[str, Any] | None:
    selected = [press for press in presses if actor in press.attributed and press.residue]
    if len(selected) < 2:
        return None
    support = sorted({cell for press in selected for cell in press.residue})
    if not support:
        return None
    observations = []
    component_observations = []
    fingerprints = []
    first = selected[0]
    fingerprints.append(tuple(int(record.nodes[first.left].settled[cell]) for cell in support))
    for press in selected:
        before = record.nodes[press.left].settled
        after = record.nodes[press.right].settled
        arithmetic = _rewrite(before, after, sorted(press.residue))
        component_observations.extend(
            _component_record(before, after, component, press.right)
            for component in _components(sorted(press.residue))
        )
        observations.append({
            "left_node": press.left,
            "right_node": press.right,
            "action_id": press.action,
            "affected_cells": len(press.residue),
            **arithmetic,
        })
        fingerprints.append(tuple(int(after[cell]) for cell in support))
    nonempty = [row for row in observations if row["changed_cells"]]
    if len(nonempty) < 2:
        return None
    conserved = all(row["class_multiset_conserved"] for row in nonempty)
    rewrite_tables = {
        tuple((arc["before_class"], arc["after_class"], arc["cells"]) for arc in row["rewrites"])
        for row in nonempty
    }
    common_rewrites = nonempty[0]["rewrites"] if len(rewrite_tables) == 1 else []
    signed_tables = {
        tuple(tuple(item) for item in row["signed_class_delta"])
        for row in nonempty
    }
    functional_substitution = bool(common_rewrites) and all(
        len({arc["after_class"] for arc in common_rewrites if arc["before_class"] == before}) == 1
        for before in {arc["before_class"] for arc in common_rewrites}
    )
    if conserved:
        kind = "COORDINATED_CLASS_PERMUTATION"
    elif len(rewrite_tables) == 1 and functional_substitution:
        kind = "COORDINATED_FIXED_CLASS_SUBSTITUTION"
    elif len(rewrite_tables) == 1:
        kind = "COORDINATED_REPEATED_CLASS_REWRITE"
    else:
        kind = "COORDINATED_CLASS_REWRITE"
    counts = [row["changed_cells"] for row in nonempty]
    boxes = sorted({tuple(int(value) for value in box) for box in component_boxes if len(box) == 4})
    return {
        "schema": "virelai-joint-transformation-v1",
        "kind": kind,
        "status": "OBSERVED_REPEATEDLY",
        "actor_worldline_id": actor,
        "witness_steps": [row["right_node"] for row in nonempty],
        "witness_count": len(nonempty),
        "support_union_cells": len(support),
        "changed_cells_per_press": {
            "min": min(counts), "median": median(counts), "max": max(counts),
        },
        "component_boxes": [list(box) for box in boxes],
        "component_count": len(boxes),
        "class_multiset_conserved_each_press": conserved,
        "rewrite_table_repeats_exactly": len(rewrite_tables) == 1,
        "rewrite_is_functional_substitution": functional_substitution,
        "common_class_rewrites": common_rewrites,
        "common_signed_class_delta": (
            [list(item) for item in next(iter(signed_tables))]
            if len(signed_tables) == 1 else []
        ),
        "period": _period(fingerprints),
        "press_arithmetic": observations,
        "decomposition": _decompose(component_observations),
        "limitations": (
            "Channels co-occur on presses attributed to the same control. "
            "This establishes one joint visible transformation, not its purpose or win relevance."
        ),
    }


__all__ = ["compile_joint_transformation"]
