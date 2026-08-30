"""virelai_v4/library/probe_outcome_classifier.py — Probe outcome classification.

Relocated from `strategy/` (WO-MINE-CLEAN-04, originally introduced under
WO-01 LEVER-CATALOG). This function classifies the result of a probe action
against the current semantic library state, producing a ProbeOutcome contract.

Import sovereignty: contracts/, library/, stdlib only.
No imports from targeting/, strategy/, perception/, memory/.

FINDING-DEC-14: this function was previously in strategy/ despite being
library-tier reasoning, which created the library↔strategy module-top
import cycle. Its natural home is library/.
"""

from __future__ import annotations

from typing import Set, Tuple

from virelai_v4.contracts.probe_types import ProbeOutcome
from virelai_v4.contracts.world_delta import WorldDelta
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import SemanticLibrary

# WO-EFFECT-LABEL — roles whose changes are OBSERVED and LABELED but consciously
# DISREGARDED as lever effects (not silently masked). The COUNTER ticks every
# press, and the frozen hud_mask (built once at first COUNTER detection, never
# recomputed) under-covers it, so its cells leak into world_cells; a live role
# read (mirroring cycle_probe's _live_counter_cells, WO-CP1-FIX-B) labels them
# and routes them to disregarded_region_ids — recorded, not erased. (EGO is NOT
# disregarded here: its cells are already subtracted from world_cells upstream,
# and a lever CAN legitimately drive the ego — a teleporter — so ego is a
# separate, flagged decision, not folded into this counter cleanup.)
_NON_EFFECT_ROLES = frozenset({LibraryRole.COUNTER})


def classify_probe_outcome(
    probed_region_id: int,
    probed_region_cells: Set[Tuple[int, int]],
    world_delta: WorldDelta,
    library_at_probe: SemanticLibrary,
) -> ProbeOutcome:
    """Classify a single probe's world delta into a ProbeOutcome.

    Given the world delta immediately after a single probe, determine the
    causal role of the probed object.

    Parameters
    ----------
    probed_region_id : int
        Region ID of the object that was probed.
    probed_region_cells : Set[Tuple[int, int]]
        (row, col) cells belonging to the probed object at probe time.
    world_delta : WorldDelta
        Canonical per-frame delta (from context.world_delta — WO-02-ARCH).
        world_delta.world_cells contains the productive signal (HUD/ego filtered).
        world_delta.ego_cells contains ego displacement cells.
    library_at_probe : SemanticLibrary
        The semantic library at the moment of probing (read-only).

    Returns
    -------
    ProbeOutcome
        Frozen dataclass describing the probe result.
    """
    # Read from canonical WorldDelta
    world_delta_cells: Set[Tuple[int, int]] = set(world_delta.world_cells)
    ego_displacement_cells: Set[Tuple[int, int]] = set(world_delta.ego_cells)

    # Guard: probed region must exist in library
    if probed_region_id not in library_at_probe.objects:
        return ProbeOutcome(
            outcome="NO_EFFECT",
            probed_region_id=probed_region_id,
            notes="probed region not found in library",
        )

    # AMBIGUOUS: non-empty world delta but entirely masked by ego displacement
    if world_delta_cells and not (world_delta_cells - ego_displacement_cells):
        return ProbeOutcome(
            outcome="AMBIGUOUS",
            probed_region_id=probed_region_id,
            notes="probe outcome masked by ego occupancy; re-probe after ego moves",
        )

    # Subtract ego displacement to get clean world delta
    world_delta_non_ego: Set[Tuple[int, int]] = world_delta_cells - ego_displacement_cells

    # Self-reference: probed object's own cells in the non-ego delta
    self_cells_changed: bool = bool(probed_region_cells & world_delta_non_ego)

    # Remote effect: cells in delta that are NOT in the probed object
    other_cells: Set[Tuple[int, int]] = world_delta_non_ego - probed_region_cells

    # WO-EFFECT-LABEL — active labeling + conscious disregard (NOT a silent mask).
    # Every OTHER region whose cells changed is LABELED by role and partitioned:
    #   - EFFECT subjects: regions the lever genuinely drives (non-live roles).
    #   - DISREGARDED: live/HUD regions (the COUNTER) that ticked but are
    #     consciously excluded from effect attribution. The change is OBSERVED and
    #     RECORDED here (disregarded_ids), attributed to its role — not erased.
    touched = [
        region
        for region in library_at_probe.objects.values()
        if region.region_id != probed_region_id
        and bool(set(region.cells) & other_cells)
    ]
    affected_ids = sorted(
        r.region_id for r in touched if r.role not in _NON_EFFECT_ROLES
    )
    disregarded_ids = sorted(
        r.region_id for r in touched if r.role in _NON_EFFECT_ROLES
    )
    other_reactive_cells_changed: bool = bool(affected_ids)
    _dis_note = (
        f"; disregarded live/HUD regions {disregarded_ids} (counter tick, non-effect)"
        if disregarded_ids else ""
    )

    # Outcome matrix — the OUTCOME is driven by genuine EFFECT regions only; a
    # press that merely ticked the counter is NO_EFFECT with the tick recorded.
    if self_cells_changed and other_reactive_cells_changed:
        return ProbeOutcome(
            outcome="LEVER_LOCAL_REMOTE",
            probed_region_id=probed_region_id,
            affected_region_ids=affected_ids,
            disregarded_region_ids=disregarded_ids,
            self_cells_changed=True,
            other_reactive_cells_changed=True,
            notes=f"local+remote{_dis_note}",
        )
    if self_cells_changed:
        return ProbeOutcome(
            outcome="LEVER_LOCAL_SELF",
            probed_region_id=probed_region_id,
            affected_region_ids=[],
            disregarded_region_ids=disregarded_ids,
            self_cells_changed=True,
            other_reactive_cells_changed=False,
            notes=f"local self{_dis_note}",
        )
    if other_reactive_cells_changed:
        return ProbeOutcome(
            outcome="LEVER_REMOTE_ONLY",
            probed_region_id=probed_region_id,
            affected_region_ids=affected_ids,
            disregarded_region_ids=disregarded_ids,
            self_cells_changed=False,
            other_reactive_cells_changed=True,
            notes=f"remote only{_dis_note}",
        )
    # No genuine effect. If the only change was a disregarded counter tick, that
    # is recorded (labeled) — the press did nothing but tick the counter.
    return ProbeOutcome(
        outcome="NO_EFFECT",
        probed_region_id=probed_region_id,
        disregarded_region_ids=disregarded_ids,
        notes=f"no effect{_dis_note}",
    )
