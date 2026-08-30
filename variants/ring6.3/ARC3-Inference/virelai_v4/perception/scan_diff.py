"""
virelai_v4/perception/scan_diff.py — Correspondence primitive (WO-A.2a).

Transplanted from V3.5 discovery/census/multi_scan.py:549-777.
Includes: RegionDelta, ScanDiff, diff_scans().

This is the delta tool deliberately excluded by grid_scan.py:6
"for a later campaign" — the Physics Reframe (NR-01) is that campaign.

Algorithm and thresholds preserved unchanged from V3.5:
  Pass 1 — same-value cell-set overlap matching, greedy largest-ratio-first,
           minimum overlap ratio 0.3 (vs min area).
  Pass 2 — minimal-displacement assignment for fully displaced objects:
           same value, area within 30%, centroid distance < grid_diagonal/4,
           greedy closest-first.
Preserved V3.5 quirks (transplant fidelity, not endorsement):
  - "transformed" deltas are appended to regions_grew (V3.5 behavior).
  - Pass 2 runs per-value, after Pass 1 for that value.

diff_scans is a PURE FUNCTION over two GridScans. It writes no belief,
touches no library, mutates neither input. The frame is truth; this
measures how the truth moved.

Import sovereignty: imports only from perception.grid_scan and stdlib.
Not wired to any live path (wiring is A.2b).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from virelai_v4.perception.grid_scan import GridScan, Region, ValueSummary

# V3.5 thresholds — preserved unchanged (retuning is out of scope / INVENT).
_PASS1_MIN_OVERLAP_RATIO = 0.3
_PASS2_MAX_AREA_RATIO = 0.30
_PASS2_DIAG_DIVISOR = 4


# ---------------------------------------------------------------------------
# Dataclasses — transplanted identically from V3.5 (multi_scan.py:549-583)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RegionDelta:
    """What happened to a specific region between two grid states."""
    region_id_before: Optional[int]
    region_id_after: Optional[int]
    value: int
    area_before: int
    area_after: int
    centroid_before: Optional[Tuple[float, float]]
    centroid_after: Optional[Tuple[float, float]]
    displacement: float
    delta_type: str


@dataclass
class ScanDiff:
    """
    Difference between two GridScans.

    Fields:
        regions_stable:      Regions that didn't change.
        regions_moved:       Regions that moved (centroid shifted).
        regions_grew:        Regions that gained area (incl. "transformed").
        regions_shrank:      Regions that lost area.
        regions_appeared:    New regions (not in scan_before).
        regions_disappeared: Gone regions (not in scan_after).
        value_deltas:        {value: (count_before, count_after)}.
        border_changes:      Value pairs whose border length changed.
    """
    regions_stable: List[RegionDelta] = field(default_factory=list)
    regions_moved: List[RegionDelta] = field(default_factory=list)
    regions_grew: List[RegionDelta] = field(default_factory=list)
    regions_shrank: List[RegionDelta] = field(default_factory=list)
    regions_appeared: List[RegionDelta] = field(default_factory=list)
    regions_disappeared: List[RegionDelta] = field(default_factory=list)
    value_deltas: Dict[int, Tuple[int, int]] = field(default_factory=dict)
    border_changes: List[Tuple[int, int, int, int]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Pass 1 — overlap matching (multi_scan.py:600-658, unchanged)
# ---------------------------------------------------------------------------

def _classify_pass1(disp: float, area_b: int, area_a: int) -> str:
    """V3.5 delta-type classification, unchanged."""
    if disp < 0.5 and abs(area_a - area_b) <= 1:
        return "stable"
    if disp >= 1.0 and abs(area_a - area_b) / max(area_b, 1) < 0.15:
        return "moved"
    if area_a > area_b:
        return "grew"
    if area_a < area_b:
        return "shrank"
    return "transformed"


def _append_delta(diff: ScanDiff, delta: RegionDelta) -> None:
    """Route a matched delta to its ScanDiff bucket (V3.5 routing,
    including the transformed->regions_grew quirk)."""
    bucket = {
        "stable": diff.regions_stable,
        "moved": diff.regions_moved,
        "grew": diff.regions_grew,
        "shrank": diff.regions_shrank,
    }.get(delta.delta_type, diff.regions_grew)
    bucket.append(delta)


def _pass1_overlap_match(
    diff: ScanDiff,
    val: int,
    regs_b: List[Region],
    regs_a: List[Region],
    matched_before: Set[int],
    matched_after: Set[int],
) -> None:
    """Greedy largest-overlap-ratio-first matching for one value."""
    matches = []
    for rb in regs_b:
        for ra in regs_a:
            if ra.region_id in matched_after:
                continue
            overlap = len(rb.cells & ra.cells)
            if overlap > 0:
                min_area = min(rb.area, ra.area)
                ratio = overlap / min_area if min_area > 0 else 0
                matches.append((ratio, rb, ra))

    matches.sort(key=lambda x: x[0], reverse=True)

    for ratio, rb, ra in matches:
        if rb.region_id in matched_before or ra.region_id in matched_after:
            continue
        if ratio < _PASS1_MIN_OVERLAP_RATIO:
            continue

        matched_before.add(rb.region_id)
        matched_after.add(ra.region_id)

        disp = (
            (ra.centroid[0] - rb.centroid[0]) ** 2
            + (ra.centroid[1] - rb.centroid[1]) ** 2
        ) ** 0.5
        dtype = _classify_pass1(disp, rb.area, ra.area)
        _append_delta(diff, RegionDelta(
            region_id_before=rb.region_id,
            region_id_after=ra.region_id,
            value=val,
            area_before=rb.area,
            area_after=ra.area,
            centroid_before=rb.centroid,
            centroid_after=ra.centroid,
            displacement=disp,
            delta_type=dtype,
        ))


# ---------------------------------------------------------------------------
# Pass 2 — minimal-displacement assignment (multi_scan.py:672-727, unchanged)
# ---------------------------------------------------------------------------

def _pass2_proximity_match(
    diff: ScanDiff,
    val: int,
    regs_b: List[Region],
    regs_a: List[Region],
    matched_before: Set[int],
    matched_after: Set[int],
    grid_shape: Tuple[int, int],
) -> None:
    """Catch movers displaced to non-overlapping positions: same value,
    area within 30%, centroid distance < grid_diagonal/4, closest-first."""
    unmatched_b = [rb for rb in regs_b if rb.region_id not in matched_before]
    unmatched_a = [ra for ra in regs_a if ra.region_id not in matched_after]
    if not (unmatched_b and unmatched_a):
        return

    diag = (grid_shape[0] ** 2 + grid_shape[1] ** 2) ** 0.5
    prox_matches = []
    for rb in unmatched_b:
        for ra in unmatched_a:
            if ra.region_id in matched_after:
                continue
            if rb.area > 0:
                area_ratio = abs(ra.area - rb.area) / rb.area
            else:
                area_ratio = 1.0
            if area_ratio > _PASS2_MAX_AREA_RATIO:
                continue
            disp = (
                (ra.centroid[0] - rb.centroid[0]) ** 2
                + (ra.centroid[1] - rb.centroid[1]) ** 2
            ) ** 0.5
            if disp > diag / _PASS2_DIAG_DIVISOR:
                continue
            prox_matches.append((disp, rb, ra))

    prox_matches.sort(key=lambda x: x[0])

    for disp, rb, ra in prox_matches:
        if rb.region_id in matched_before or ra.region_id in matched_after:
            continue
        matched_before.add(rb.region_id)
        matched_after.add(ra.region_id)
        dtype = "moved" if disp >= 1.0 else "stable"
        delta = RegionDelta(
            region_id_before=rb.region_id,
            region_id_after=ra.region_id,
            value=val,
            area_before=rb.area,
            area_after=ra.area,
            centroid_before=rb.centroid,
            centroid_after=ra.centroid,
            displacement=disp,
            delta_type=dtype,
        )
        if dtype == "moved":
            diff.regions_moved.append(delta)
        else:
            diff.regions_stable.append(delta)


# ---------------------------------------------------------------------------
# Unmatched residue — appeared / disappeared (multi_scan.py:729-757)
# ---------------------------------------------------------------------------

def _collect_unmatched(
    diff: ScanDiff,
    val: int,
    regs_b: List[Region],
    regs_a: List[Region],
    matched_before: Set[int],
    matched_after: Set[int],
) -> None:
    for rb in regs_b:
        if rb.region_id not in matched_before:
            diff.regions_disappeared.append(RegionDelta(
                region_id_before=rb.region_id, region_id_after=None,
                value=val, area_before=rb.area, area_after=0,
                centroid_before=rb.centroid, centroid_after=None,
                displacement=0.0, delta_type="disappeared",
            ))
    for ra in regs_a:
        if ra.region_id not in matched_after:
            diff.regions_appeared.append(RegionDelta(
                region_id_before=None, region_id_after=ra.region_id,
                value=val, area_before=0, area_after=ra.area,
                centroid_before=None, centroid_after=ra.centroid,
                displacement=0.0, delta_type="appeared",
            ))


# ---------------------------------------------------------------------------
# Orchestrator (multi_scan.py:587-777, decomposed; behavior unchanged)
# ---------------------------------------------------------------------------

def diff_scans(scan_before: GridScan, scan_after: GridScan) -> ScanDiff:
    """
    Compute structured difference between two grid scans.

    Strategy: match regions by value and spatial overlap (Pass 1, minimum
    overlap ratio 0.3 of the smaller area), then by proximity + area for
    fully displaced movers (Pass 2). Pure function: no side effects on
    either scan, the library, or any Slot.

    Returns:
        ScanDiff describing what changed structurally.
    """
    diff = ScanDiff()
    matched_before: Set[int] = set()
    matched_after: Set[int] = set()

    for val in set(scan_before.unique_values) | set(scan_after.unique_values):
        regs_b = scan_before.regions_by_value.get(val, [])
        regs_a = scan_after.regions_by_value.get(val, [])
        _pass1_overlap_match(diff, val, regs_b, regs_a,
                             matched_before, matched_after)
        _pass2_proximity_match(diff, val, regs_b, regs_a,
                               matched_before, matched_after,
                               scan_before.grid_shape)
        _collect_unmatched(diff, val, regs_b, regs_a,
                           matched_before, matched_after)

    # Value deltas
    _EMPTY = ValueSummary(0, 0, 0, 0.0, True, (0, 0, 0, 0))
    for val in set(scan_before.unique_values) | set(scan_after.unique_values):
        cb = scan_before.value_summaries.get(val, _EMPTY).total_cells
        ca = scan_after.value_summaries.get(val, _EMPTY).total_cells
        if cb != ca:
            diff.value_deltas[val] = (cb, ca)

    # Border changes
    borders_b = {(b.value_a, b.value_b): b.length for b in scan_before.borders}
    borders_a = {(b.value_a, b.value_b): b.length for b in scan_after.borders}
    for pair in set(borders_b) | set(borders_a):
        lb, la = borders_b.get(pair, 0), borders_a.get(pair, 0)
        if lb != la:
            diff.border_changes.append((pair[0], pair[1], lb, la))

    return diff


__all__ = ["RegionDelta", "ScanDiff", "diff_scans"]
