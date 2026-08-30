"""
virelai_v4/library/observation_enrichment.py — Per-object CellHistory enrichment.

Transplanted from V3.5 observer/knife/observation_enrichment.py (WO-SYNTH-01a).
V4 changes:
  - Imports updated to V4 paths.
  - is_toggle imported at module level from virelai_v4.cybernetic.cell_history
    (was a lazy import inside _compute_object_metrics in V3.5).

Public API:
    enrich_inventory_from_cell_history(inventory, cell_history, total_actions)
        -> SemanticInventory

Import sovereignty: virelai_v4.library.semantic_object, virelai_v4.perception.cell_history,
and stdlib only.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Tuple

from virelai_v4.library.semantic_object import (
    ObjectFunction,
    SemanticInventory,
    SemanticObject,
)
from virelai_v4.cybernetic.cell_history import is_toggle as _is_toggle


def enrich_inventory_from_cell_history(
    inventory: SemanticInventory,
    cell_history: Dict[Tuple[int, int], Any],
    total_actions: int,
) -> SemanticInventory:
    """Enrich each SemanticObject with per-object CellHistory evidence.

    For each object, looks up CellHistory entries for that object's specific
    cells and computes per-object metrics: cells_changed, total_changes,
    toggle confirmation.  Boosts role_confidence for ACTIVE and REACTIVE
    objects with observation evidence.  Also updates ObjectFunction
    evidence_count when CellHistory depth exceeds probe-based count.

    Args:
        inventory:    Already-built SemanticInventory with objects and functions.
        cell_history: {(row, col): CellHistory} from state["cell_history"].
        total_actions: Total actions this life (for inert depth calculation).

    Returns:
        New SemanticInventory with enriched objects and functions.
    """
    if not cell_history:
        return inventory

    object_metrics: Dict[Tuple[int, int], _ObjectMetrics] = {}
    enriched_objects = []

    for obj in inventory.objects:
        metrics = _compute_object_metrics(obj, cell_history)
        object_metrics[(obj.class_id, obj.region_id)] = metrics

        new_confidence = _adjust_confidence(obj, metrics)
        if new_confidence != obj.role_confidence:
            enriched_objects.append(replace(obj, role_confidence=new_confidence))
        else:
            enriched_objects.append(obj)

    enriched_functions = []
    for fn in inventory.functions:
        new_fn = _enrich_function(fn, object_metrics)
        enriched_functions.append(new_fn)

    return SemanticInventory(
        cycle_id=inventory.cycle_id,
        grid_shape=inventory.grid_shape,
        objects=tuple(enriched_objects),
        functions=tuple(enriched_functions),
    )


class _ObjectMetrics:
    """Per-object CellHistory metrics. Internal helper, not exported."""
    __slots__ = ("cells_observed", "cells_changed", "total_changes", "any_toggle")

    def __init__(
        self,
        cells_observed: int = 0,
        cells_changed: int = 0,
        total_changes: int = 0,
        any_toggle: bool = False,
    ):
        self.cells_observed = cells_observed
        self.cells_changed = cells_changed
        self.total_changes = total_changes
        self.any_toggle = any_toggle


def _compute_object_metrics(
    obj: SemanticObject,
    cell_history: Dict[Tuple[int, int], Any],
) -> _ObjectMetrics:
    """Compute CellHistory metrics for a single object's cells."""
    if not obj.cells:
        return _ObjectMetrics()

    cells_observed = 0
    cells_changed = 0
    total_changes = 0
    any_toggle = False

    for coord in obj.cells:
        ch = cell_history.get(coord)
        if ch is not None:
            cells_observed += 1
            cc = getattr(ch, "change_count", 0)
            total_changes += cc
            if cc > 0:
                cells_changed += 1
            if not any_toggle and len(getattr(ch, "transitions", [])) >= 2:
                if _is_toggle(ch):
                    any_toggle = True

    return _ObjectMetrics(
        cells_observed=cells_observed,
        cells_changed=cells_changed,
        total_changes=total_changes,
        any_toggle=any_toggle,
    )


def _adjust_confidence(obj: SemanticObject, metrics: _ObjectMetrics) -> float:
    """Compute adjusted role_confidence from per-object CellHistory evidence.

    Rules:
        ACTIVE with cells_changed > 0 and total_changes >= 3:
            boost = min(0.15, total_changes / 100.0)
            new_confidence = min(0.95, role_confidence + boost)

        REACTIVE with cells_changed > 0:
            boost = min(0.10, cells_changed / max(obj.area, 1))
            new_confidence = min(0.90, role_confidence + boost)

        All others: no change.
    """
    if metrics.cells_changed == 0:
        return obj.role_confidence

    if obj.state_role == "ACTIVE" and metrics.total_changes >= 3:
        boost = min(0.15, metrics.total_changes / 100.0)
        return min(0.95, obj.role_confidence + boost)

    if obj.state_role == "REACTIVE" and metrics.cells_changed > 0:
        boost = min(0.10, metrics.cells_changed / max(obj.area, 1))
        return min(0.90, obj.role_confidence + boost)

    return obj.role_confidence


def _enrich_function(
    fn: ObjectFunction,
    object_metrics: Dict[Tuple[int, int], _ObjectMetrics],
) -> ObjectFunction:
    """Update ObjectFunction evidence_count from per-object CellHistory depth."""
    if fn.verb not in ("click", "contact"):
        return fn

    key = (fn.subject_class_id, fn.subject_region_id)
    metrics = object_metrics.get(key)

    if metrics is None:
        for (cid, rid), m in object_metrics.items():
            if cid == fn.subject_class_id and m.total_changes > 0:
                metrics = m
                break

    if metrics is None or metrics.total_changes <= fn.evidence_count:
        return fn

    return ObjectFunction(
        subject_class_id=fn.subject_class_id,
        verb=fn.verb,
        object_class_id=fn.object_class_id,
        evidence_count=max(fn.evidence_count, metrics.total_changes),
        confidence=fn.confidence,
        target_class_ids=fn.target_class_ids,
        affected_cells=fn.affected_cells,
        subject_region_id=fn.subject_region_id,
        direction=fn.direction,
        effect_locality=fn.effect_locality,
        target_region_ids=fn.target_region_ids,
    )


__all__ = ["enrich_inventory_from_cell_history"]
