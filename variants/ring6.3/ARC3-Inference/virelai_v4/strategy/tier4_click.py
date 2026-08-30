"""Tier 4 CLICK action selector.

Owns the Tier 4 CLICK exploration strategy: drives the CLICK sweep (WO-04)
by delegating to select_click_sweep_probe and emitting one ACTION6 per
frame at the next probe coordinate. Records probe target on context.

Extracted from action_selector.py in WO-CLEAN-06-PHASE-3 as part of the
Tier 4 CLICK cluster decomposition. Final phase of the WO-CLEAN-06 campaign.

Sovereignty: stdlib + arcengine + library/ (type only) + strategy/ siblings.
No numpy, no contracts/, no perception/, no targeting/, no memory/.

Public API:
- _select_tier4_click_action(library, context) -> GameAction
"""

from __future__ import annotations

import logging
import os
import sys
from typing import TYPE_CHECKING

from arcengine import GameAction

from virelai_v4.library.region_geometry import representative_coordinate
from virelai_v4.library.semantic_library import SemanticLibrary

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# Captain primitive (WO-OCD-CAPTAIN-IMPLEMENTATION Step 2)
# ----------------------------------------------------------------------

def emit_click_at_region(
    context: "VirelaiContext",
    library: SemanticLibrary,
    region_id: int,
) -> GameAction:
    """Emit ACTION6 at the centroid of the named region's cells.

    Captain primitive — direct emit, no sweep state machine.
    Separate from _select_tier4_click_action (which drives the legacy
    sweep) so the captain can call it without triggering the sweep's
    K-eviction logic. The captain's dispatch table at
    virelai_v4/captain.py routes (tier=4, probe_type="click") here.

    Coordinate selection uses region_geometry.representative_coordinate,
    which guarantees the returned (row, col) is in the cell set
    (handles irregular shapes where the geometric centroid would fall
    in empty space).
    """
    obj = library.objects[region_id]
    row, col = representative_coordinate(set(obj.cells))
    action = GameAction.ACTION6
    action.set_data({"x": col, "y": row})
    return action


# ----------------------------------------------------------------------
# Tier 4 CLICK action selector
# ----------------------------------------------------------------------

def tier4_click_tool(
    library: SemanticLibrary,
    context: "VirelaiContext",
) -> GameAction:
    """Tier 4 CLICK probe strategy: drive the CLICK sweep (WO-04).

    SOV-02 Step 2: renamed from `_select_tier4_click_action` to
    `tier4_click_tool`.  Backward-compat alias preserved below.

    Library-read: iterates library.objects to find the next unprobed region
    via select_click_sweep_probe.

    Delegates to select_click_sweep_probe (strategy/click_sweep.py) which
    maintains sweep state on context. Emits one ACTION6 per frame at the
    next probe coordinate. When the sweep is complete (list exhausted or
    K consecutive inerts), emits fallback ACTION6 at (0, 0) so the assessor
    can advance the directive.

    Records on context:
        last_probe_target_region_id  — region_id of probed object, or None on completion
        last_probe_target_cells      — frozenset of spawn-frame cells, or None on completion
        last_probe_action_kind       — "CLICK"

    Parameters
    ----------
    library : SemanticLibrary
        Current semantic library (read-only for this function).
    context : VirelaiContext
        Context object mutated to record probe target and sweep state.

    Returns
    -------
    GameAction.ACTION6 with coordinates set.
    """
    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        print(
            f"[WO02-DIAG] T4-CLICK-ENTRY action={library.header.actions_taken} "
            f"sweep_idx={context.sweep_index} sweep_len={len(context.sweep_list)} "
            f"consecutive_inerts={context.sweep_consecutive_inerts} directive=TIER4",
            file=sys.stderr, flush=True,
        )

    # WO-SOV-03 Category B (site 4): captain_is_active retired.
    # Under single-actor architecture the captain owns all CLICK probe dispatch
    # via DISPATCH_TABLE. The legacy sweep body is unconditionally dead —
    # always skip. Dead code below (probe = select_click_sweep_probe ...)
    # deferred to SP8 for removal.
    #
    # WO-STEP-01 §2: the old gated stub emitted a SILENT ACTION6 at (0,0) —
    # the vc33 budget-burn's true emitting line (FRICTION-CYCLEPROBE-ORPHAN
    # H3, corrected: the stub, not the dead sweep-complete fallback below).
    # Retired to the typed-gap discipline: deterministic frame-keyed coords,
    # one logged notice, emitter "typed_gap" — never a silent inert corner.
    from virelai_v4.strategy.typed_gap_action import gap_click_coords, emit_typed_gap_warning
    _frame = getattr(context, "prev_grid", None)
    _rows = library.header.grid_rows if library.header.grid_rows > 0 else 64
    _cols = library.header.grid_cols if library.header.grid_cols > 0 else 64
    _x, _y = gap_click_coords(_frame, _rows, _cols)
    # WO-LOGGING-CARDINALITY: dedupe + tally (replaces per-action flood).
    emit_typed_gap_warning(library.header.world_type, "TIER4_LEGACY_GATED")
    context.last_probe_target_region_id = None
    context.last_probe_target_cells = None
    context.last_probe_action_kind = None
    context.last_emitter_path = "typed_gap"
    action = GameAction.ACTION6
    action.set_data({"x": int(_x), "y": int(_y)})
    return action


# SOV-02 Step 2: backward-compat alias — test sites that import
# `_select_tier4_click_action` by name (test_cycle_probe_invocation.py
# lines 1148, 1321) continue to work without changes.
_select_tier4_click_action = tier4_click_tool


