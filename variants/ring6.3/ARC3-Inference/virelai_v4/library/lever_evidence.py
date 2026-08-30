"""
virelai_v4/library/lever_evidence.py — Evidence recording for Tier 3 lever probing.

On the frame AFTER a Tier 3 CLICK probe (detected by last_probe_target being set),
process the HUD-masked world delta to record lever evidence on the probed object.

Four cases:
  Case 1: nonzero delta, probed object's cells changed → LOCAL lever.
  Case 2: nonzero delta, only other objects changed → REMOTE lever.
  Case 3: both → LOCAL on probed, REMOTE effects on others.
  Case 4: zero delta → increment inert_probe_count, do NOT reclassify.

Confidence accumulation:
  - First positive observation → 0.60
  - Each additional positive observation → +0.10 (cap 0.95)
  - Zero deltas → no change to confidence, just increment inert_probe_count

After recording, clear last_probe_target (consume the intent→observation link).

Import sovereignty: imports from contracts/, perception/, and stdlib only.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Dict, Optional, Set, Tuple

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext
    from virelai_v4.contracts.world_delta import WorldDelta
    from virelai_v4.library.semantic_library import SemanticLibrary

logger = logging.getLogger(__name__)


def record_lever_evidence(
    context: VirelaiContext,
    library: SemanticLibrary,
    world_delta: WorldDelta,
) -> None:
    """Process a Tier 3 probe's world delta and record lever evidence.

    Called in library_sync on the frame AFTER a probe (detected by last_probe_target).
    Reads last_probe_target, last_probe_coord from context (cleared after).
    Reads world_delta.world_cells — already filtered of ego_cells and hud_cells
    at WorldDelta construction time.
    Updates library.objects[region_id].lever_* fields in place.
    Clears context.last_probe_target and context.last_probe_coord.

    WO-PHASE4-02 (canonicalization): consumes the canonical WorldDelta
    artifact instead of the raw FrameDelta. The previous FrameDelta path was
    not actually HUD-masked in V4's live path because compute_frame_delta is
    called without hud_mask — see OTA-05. WorldDelta is the source of truth.

    Parameters
    ----------
    context : VirelaiContext
        Carries last_probe_target, last_probe_coord (set by action_selector).
    library : SemanticLibrary
        Contains objects. lever_* fields mutated in place.
    world_delta : WorldDelta
        The canonical world delta on this frame. world_cells is the
        productive signal — already filtered of ego_cells and hud_cells.
    """
    if context.last_probe_target is None:
        # No probe happened last frame — nothing to record
        return

    probe_target_id = context.last_probe_target
    probed_object = library.objects.get(probe_target_id)

    if probed_object is None:
        logger.warning(f"Probe target region_id={probe_target_id} not in library. Skipping evidence recording.")
        context.last_probe_target = None
        context.last_probe_coord = None
        return

    # Extract world delta cells (already filtered of ego/hud at WorldDelta construction)
    world_delta_cells: Set[Tuple[int, int]] = set(world_delta.world_cells)

    if not world_delta_cells:
        # Case 4: zero delta (after HUD mask)
        probed_object.inert_probe_count += 1
        logger.debug(
            f"Probe target region_id={probe_target_id}: zero delta. "
            f"inert_probe_count now {probed_object.inert_probe_count}."
        )
        context.last_probe_target = None
        context.last_probe_coord = None
        return

    # Nonzero delta: attribute changed cells to objects
    # Iterate through all objects and check which cells changed
    attribution: Dict[int, Set[Tuple[int, int]]] = {}
    for obj in library.objects.values():
        affected_cells = obj.cells & world_delta_cells
        if affected_cells:
            attribution[obj.region_id] = affected_cells

    # Determine probed object's changed cells
    probed_changed = attribution.get(probe_target_id, set())
    other_changed_ids = {rid for rid in attribution.keys() if rid != probe_target_id}

    world_type = library.header.world_type
    if probed_changed and not other_changed_ids:
        # Case 1: LOCAL lever (only probed object changed)
        _record_local_lever(probed_object, probed_changed, world_type)
        logger.debug(
            f"Probe target region_id={probe_target_id}: LOCAL lever. "
            f"Changed cells: {len(probed_changed)}, confidence now {probed_object.lever_confidence}."
        )
    elif not probed_changed and other_changed_ids:
        # Case 2: REMOTE lever (only other objects changed)
        _record_remote_lever(probed_object, other_changed_ids, world_type)
        logger.debug(
            f"Probe target region_id={probe_target_id}: REMOTE lever. "
            f"Affected region_ids: {other_changed_ids}, confidence now {probed_object.lever_confidence}."
        )
    elif probed_changed and other_changed_ids:
        # Case 3: LOCAL on probed (primary), plus side effects on others
        # The probed object is classified as LOCAL (it changed when probed).
        # We record the other affected objects in lever_effect_region_ids.
        _record_local_lever(probed_object, probed_changed, world_type)
        # Record the other region_ids as side effects (without overwriting locality)
        if probed_object.lever_effect_region_ids is None:
            probed_object.lever_effect_region_ids = []
        probed_object.lever_effect_region_ids.extend(other_changed_ids)
        logger.debug(
            f"Probe target region_id={probe_target_id}: LOCAL + REMOTE side effects. "
            f"Local changed {len(probed_changed)}, remote affected {len(other_changed_ids)} objects. "
            f"Confidence now {probed_object.lever_confidence}."
        )

    # Clear the probe intent marker
    context.last_probe_target = None
    context.last_probe_coord = None


def _record_local_lever(obj, changed_cells: Set[Tuple[int, int]],
                        world_type: str) -> None:
    """Update lever evidence for a LOCAL lever (probed object's cells changed).

    WO-D4: lever_locality is single-writer-per-world-type. record_lever_evidence
    is the NAV writer; it asserts its lane at the point of write — a write
    attempted under a non-NAV world_type surfaces (logged) and is suppressed,
    never a silent cross-lane write (CE ruling)."""
    if world_type == "NAV":
        obj.lever_locality = "LOCAL"
    else:
        logger.warning(
            "lever_locality NAV-lane write attempted under world_type=%s "
            "(region %s) — per-world-type contract violation, suppressed",
            world_type, getattr(obj, "region_id", "?"),
        )
    if obj.lever_effect_cells is None:
        obj.lever_effect_cells = set()
    obj.lever_effect_cells |= changed_cells

    # Increment confidence: first positive → 0.60, each additional → +0.10, cap 0.95
    if obj.lever_confidence == 0.0:
        obj.lever_confidence = 0.60
    else:
        obj.lever_confidence = min(0.95, obj.lever_confidence + 0.10)


def _record_remote_lever(obj, other_region_ids: set, world_type: str) -> None:
    """Update lever evidence for a REMOTE lever (probed object affects others).

    WO-D4: NAV-lane write of lever_locality (single-writer-per-world-type);
    asserts its lane at the point of write (CE ruling)."""
    if world_type == "NAV":
        obj.lever_locality = "REMOTE"
    else:
        logger.warning(
            "lever_locality NAV-lane write attempted under world_type=%s "
            "(region %s) — per-world-type contract violation, suppressed",
            world_type, getattr(obj, "region_id", "?"),
        )
    if obj.lever_effect_region_ids is None:
        obj.lever_effect_region_ids = []

    # Union the new region_ids into the existing list
    existing = set(obj.lever_effect_region_ids)
    existing |= other_region_ids
    obj.lever_effect_region_ids = list(existing)

    # Increment confidence: first positive → 0.60, each additional → +0.10, cap 0.95
    if obj.lever_confidence == 0.0:
        obj.lever_confidence = 0.60
    else:
        obj.lever_confidence = min(0.95, obj.lever_confidence + 0.10)
