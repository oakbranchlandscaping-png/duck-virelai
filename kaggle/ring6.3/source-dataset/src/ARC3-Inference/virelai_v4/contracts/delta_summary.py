"""
virelai_v4/contracts/delta_summary.py — Per-Slot DeltaSummary record.

Per Blueprint Section 2.4.4 specification — the per-Slot view of a
FrameDelta. Each Slot's ProbeEvent stores a DeltaSummary describing
what happened to that Slot's cells (and surrounding world cells)
during the probe.

Per WO-00 A.3 inheritance evidence:
    The substrate's per-frame whole-grid FrameDelta (already in V4 at
    virelai_v4/cybernetic/frame_delta.py) is the raw observation.
    DeltaSummary is the per-Slot perspective computed by the substrate
    from the global FrameDelta plus the Slot's current_segment.cells
    and the GridScan's regions_by_id.

The mapping per WO-00 A.3:
    DeltaSummary.changed_cells = FrameDelta.changed_cells ∩ slot.cells
                                  (or world_cells - slot.cells for remote)
    DeltaSummary.delta_magnitude = len(DeltaSummary.changed_cells)
    DeltaSummary.affected_region_ids = regions whose cells overlap the delta
    DeltaSummary.is_self_delta = bool(FrameDelta.changed_cells ∩ slot.cells)
    DeltaSummary.is_remote_delta = bool(FrameDelta.changed_cells - slot.cells - hud)
    DeltaSummary.is_lc_only = (FrameDelta.world_changed == 0)

Filed under WO-BLUEPRINT-04, May 19, 2026.
INVENT anchor: #4 family — ProbeEvent dataclass dependency.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple


@dataclass(frozen=True)
class DeltaSummary:
    """The per-Slot view of a FrameDelta per Blueprint Section 2.4.4.

    Computed by substrate hygiene from the global FrameDelta plus the
    Slot's current_segment.cells and the GridScan's region map. Used as
    the `delta_observed` field on ProbeEvent records.

    Fields:
        changed_cells: The cells (from the Slot's perspective) that
            changed this frame. May include self-cells, remote cells,
            or both depending on is_self_delta / is_remote_delta.

        delta_magnitude: Number of cells that changed.

        affected_region_ids: Region IDs whose cells overlap the delta.
            Used by BBA Layer Two for cross-Slot causal attribution
            (Section 4+ deferred work).

        is_self_delta: True if this Slot's own cells changed.

        is_remote_delta: True if cells outside this Slot (and outside
            the HUD/LC region) changed.

        is_lc_only: True if all changes were within the HUD/LC region —
            the FrameDelta.world_changed == 0 case. Used as a filter
            flag so HUD-only deltas don't trigger Slot-level evidence
            updates.
    """
    changed_cells: FrozenSet[Tuple[int, int]]
    delta_magnitude: int
    affected_region_ids: FrozenSet[int]
    is_self_delta: bool
    is_remote_delta: bool
    is_lc_only: bool
