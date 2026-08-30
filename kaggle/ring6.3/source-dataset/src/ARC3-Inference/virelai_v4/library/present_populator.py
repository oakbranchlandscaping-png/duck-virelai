"""virelai_v4/library/present_populator.py — add-only present-object population.

WO-LAYER1-01 v2. Below the weave, at the visual-object layer. A visual object is
the exact pair ``(class_id, cells)`` — the ``RegionClay`` fingerprint the master
list dedups on (``capture/clay.py``). Each Mode-B frame, any present visual
object whose fingerprint is not already a slot is ADDED as a new slot.

ADD-ONLY, by ruling: this module never removes, retires, or relocates a slot. A
slot whose visual object is no longer present (it changed — moved / recolored /
resized, so its fingerprint is gone) is left in place, so the captain's
accumulated dossier survives for the Layer-2 belief-home rung to absorb into the
``###``. Retirement is a later rung.

NO MATCH RULE, NO CORRESPONDENCE, NO WEAVE. "Present" == fingerprint in the
current scan. This module never compares to the previous frame, never calls
``weave_edge``, never classifies birth-vs-mover — under the exact definition
those are the weave's compression verbs, meaningless at this layer.

Single responsibility: given the current frame's ``GridScan``, add slots for
present fingerprints not already present. It does not classify behaviour, does
not process deltas (that is ``_update_from_delta``, which runs after this).

Import sovereignty: contracts/library/perception only (mirrors spawn_populator).
"""

from __future__ import annotations

import logging
from typing import Dict, Iterable, Set, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary
from virelai_v4.library.spawn_populator import (
    _layer_for_region,
    _position_label,
    _shape_label,
)
from virelai_v4.perception.grid_scan import GridScan

logger = logging.getLogger(__name__)

Fingerprint = Tuple[int, "frozenset"]


def _existing_fingerprints(library: SemanticLibrary) -> Set[Fingerprint]:
    """The exact ``(class_id, cells)`` set the roster already holds."""
    return {(o.class_id, o.cells) for o in library.objects.values()}


def _refresh_count_like(library: SemanticLibrary, classes: Iterable[int]) -> None:
    """Recompute ``count_like`` over the grown roster for the affected classes.

    ``count_like`` = (# slots sharing this class) - 1. Same semantics as
    ``spawn_populator._compute_count_like``, but computed over ``library.objects``
    (the grown roster) rather than a single scan, so same-class slots are not
    left stale after an add. Only classes that gained a slot this frame are
    touched; on a frame with no adds this function is never called (byte-identical
    behaviour is preserved for the no-add case)."""
    for class_id in set(classes):
        members = [o for o in library.objects.values() if o.class_id == class_id]
        n = len(members) - 1
        for o in members:
            o.count_like = n


def populate_present_objects(library: SemanticLibrary, grid_scan: GridScan) -> int:
    """Add a slot for every present visual object not already a slot. Add-only.

    Membership is by FINGERPRINT ``(class_id, cells)``, never by ``region_id``.
    A slot lingering from a moved-away object has a different fingerprint than the
    object's new footprint, so the new footprint correctly adds — that is the
    add-only + exact-ontology behaviour, not a bug.

    Returns the number of slots added.
    """
    existing = _existing_fingerprints(library)
    rows, cols = grid_scan.grid_shape
    background_value = grid_scan.background_value

    # Fresh non-colliding key: a within-level LABEL (provenance only), never an
    # identity claim (AMENDMENT_RULING_LIB1 §2). Monotone above every current key.
    next_key = (max(library.objects.keys()) + 1) if library.objects else 0

    added = 0
    affected_classes: Set[int] = set()
    for region in grid_scan.regions:
        fingerprint: Fingerprint = (region.value, region.cells)
        if fingerprint in existing:
            continue  # already a slot — idempotent on a static object
        obj = LibraryObject(
            region_id=next_key,
            class_id=region.value,
            cells=region.cells,
            cell_count=region.area,
            shape_desc=_shape_label(region.bbox, region.area, region.bbox_area),
            zone="",
            position_desc=_position_label(region.centroid, rows, cols),
            layer=_layer_for_region(region, background_value),
            count_like=0,  # refreshed over the grown roster below
            role=LibraryRole.UNKNOWN,
            confidence=0.0,
            # previous_class_signature defaults to None -> revoke-safe, exactly
            # like a spawn slot (first Mode-B pass initializes, never revokes).
            initial_cell_count=region.area,
            current_cell_count=region.area,
        )
        library.add_object(obj)
        existing.add(fingerprint)
        affected_classes.add(region.value)
        next_key += 1
        added += 1

    if added:
        _refresh_count_like(library, affected_classes)
    return added
