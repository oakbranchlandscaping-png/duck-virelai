"""
virelai_v4/library/cycle_probe_invocation.py — cycle probe invocation layer.

WO-CAMPAIGN3-PHASE3-02-RESUMPTION Step 1 (May 5, 2026): integration helpers
for select_action's cycle probe pre-Tier gate. Phase Sovereignty preserved
(cycle probe domain owns its lever queue + state initialization logic);
module split from ``library/cycle_probe.py`` to keep both files within
Yellow tier per Constitution §2 (Ratchet Rule).

Module Sovereignty rationale:
    - ``library/cycle_probe.py`` is the cycle probe substrate (state machine,
      classification primitive, activation harness). It contains the V3.5
      port + V4 per-frame state machine refactor.
    - ``library/cycle_probe_invocation.py`` is the integration layer
      (lever queue, state initialization, mode + coordinate selection).
      Helpers here adapt the substrate to ``select_action``'s call signature.

The split honors:
    - Constitution §2 Ratchet Rule (cycle_probe.py would have crossed Yellow
      → Red without the split; surfaced at Step 1 implementation).
    - Step 0 Recommendation 6 spirit (Phase Sovereignty: cycle probe domain
      owns invocation logic; not select_action).
    - Single Responsibility (substrate vs invocation are distinct concerns).

Exports:
    _has_unprobed_lever          — predicate gate for cycle probe section
    _select_next_unprobed_lever  — deterministic next-lever selection
    _initialize_cycle_probe_state — CycleProbeState constructor (mode + coord)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

from virelai_v4.contracts.lever_mechanism import (
    ActivationMode,
    CycleProbeState,
)

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary


def _has_unprobed_lever(library: "SemanticLibrary") -> bool:
    """Return True if any LibraryObject has role==LEVER and lever_mechanism is None.

    Predicate for select_action's cycle probe pre-Tier gate. When True and
    no probe is currently active, the integration site initializes a probe
    for the next unprobed lever. When False, the cycle probe section falls
    through immediately (no levers remaining to probe; dispatch routing
    handles the verdicts).

    Per WO-PHASE3-02-RESUMPTION Step 0 Recommendation 4: implicit lever
    queue via library iteration; no new ``context.cycle_probe_queue`` field.
    Sequential probing is sufficient for Phase 3.
    """
    from virelai_v4.library.semantic_library import LibraryRole

    return any(
        obj.role == LibraryRole.LEVER and obj.lever_mechanism is None
        for obj in library.objects.values()
    )


def _select_next_unprobed_lever(
    library: "SemanticLibrary",
    context: "VirelaiContext",
) -> Optional["LibraryObject"]:
    """Return next unprobed LEVER object via deterministic ``region_id`` ordering.

    Per WO-PHASE3-02-RESUMPTION Step 0 Recommendation 4: deterministic
    ordering enables reproducible replays — Groundhog Day discipline. The
    library iteration produces a stable selection across lives within a
    level (LibraryObject.region_id is set at spawn and immutable per
    library convention).

    Returns None when no unprobed lever exists; caller should gate via
    ``_has_unprobed_lever`` first.

    The ``context`` parameter is reserved for future selection-priority
    refinement (e.g., NavLeverCandidate.confidence as tiebreaker once
    cross-referenced); currently unused but accepted for forward-compat
    with the integration site's call signature.
    """
    from virelai_v4.library.semantic_library import LibraryRole

    unprobed = [
        obj for obj in library.objects.values()
        if obj.role == LibraryRole.LEVER and obj.lever_mechanism is None
    ]
    if not unprobed:
        return None
    return min(unprobed, key=lambda o: o.region_id)


def _initialize_cycle_probe_state(
    target_obj: "LibraryObject",
    context: "VirelaiContext",
    library: "SemanticLibrary",
    spawn_frame: np.ndarray,
) -> CycleProbeState:
    """Construct initial CycleProbeState for ``target_obj``.

    Mode selection:
        - ``library.header.world_type == "CLICK"`` → ``ActivationMode.CLICK``
        - ``library.header.world_type == "NAV"``   → ``ActivationMode.NAV_OCCUPANCY``
        - other (unclassified or unexpected) → ``ActivationMode.CLICK`` fallback
          (CLICK is the safer default; NAV_OCCUPANCY requires BFS substrate).

    Coordinate selection:
        - NAV worlds: prefer matching ``NavLeverCandidate.coordinate`` when
          a candidate falls within ``target_obj.cells`` (precise activation
          point per Phase 2 contact reactivity); else centroid of cells.
        - CLICK worlds: centroid of cells (any pixel of the object triggers
          a CLICK).

    Per WO-PHASE3-02-RESUMPTION Step 0 Recommendation 4 + Step 1 spec.

    The ``spawn_frame`` parameter is appended to ``accumulated_frames`` as
    the iteration-0 baseline observation; subsequent activation iterations
    append post-activation frames per the state machine contract at
    ``library/cycle_probe.py::_run_cycle_probe_step_impl:265-266``.
    """
    # WO-CP1-FIX-B: empty-cells target guard. A typing target with no geometry
    # cannot be aimed at — the old silent (0,0) centroid fallback burned the
    # K=20 cap clicking a corner pixel (WO-DIAG-CP1: 27/50 actions → GAME_OVER).
    # Typed refusal: log the gap, return None; the captain falls through to the
    # legacy/typed-gap dispatch. Never (0,0).
    _guard_cells = getattr(target_obj, "cells", None)
    if not _guard_cells:
        logger.warning(
            "[TYPED_GAP] cycle-probe target rid=%s has no geometry (cells "
            "empty) — typing REFUSED; (0,0) fallback retired (WO-CP1-FIX-B)",
            getattr(target_obj, "region_id", None),
        )
        return None

    world_type = library.header.world_type
    if world_type == "NAV":
        mode = ActivationMode.NAV_OCCUPANCY
    elif world_type == "CLICK":
        mode = ActivationMode.CLICK
    else:
        # Unclassified or unexpected world type — fall back to CLICK.
        mode = ActivationMode.CLICK

    # Coordinate selection: prefer NavLeverCandidate.coordinate for NAV
    # worlds (precise lever kernel coordinate per Phase 2); centroid as
    # fallback (works for CLICK worlds and NAV worlds without matching
    # candidate).
    target_coord: Optional[Tuple[int, int]] = None
    cells = getattr(target_obj, "cells", None)

    if mode == ActivationMode.NAV_OCCUPANCY and cells:
        nav_atlas = getattr(context, "nav_atlas", None)
        if nav_atlas is not None:
            candidates = getattr(nav_atlas, "nav_lever_candidates", None) or []
            for cand in candidates:
                cand_coord = getattr(cand, "coordinate", None)
                if cand_coord is not None and cand_coord in cells:
                    target_coord = (int(cand_coord[0]), int(cand_coord[1]))
                    break

    if target_coord is None and cells:
        # Centroid fallback (deterministic via int rounding).
        rows = [int(r) for r, _ in cells]
        cols = [int(c) for _, c in cells]
        target_coord = (
            int(round(sum(rows) / len(rows))),
            int(round(sum(cols) / len(cols))),
        )

    if target_coord is None:
        # Defense-in-depth: object with no cells should not exist per
        # LibraryObject invariant; fall back to (0, 0) to avoid crash.
        target_coord = (0, 0)

    region_id = int(getattr(target_obj, "region_id", 0))

    # WO-OCD-CYCLE-PROBE-VARIABLE-K (May 15, 2026): seed state_hashes
    # with the spawn-frame's HUD-masked hash. The cycle probe's per-press
    # cycle detection compares each post-press hash against this list;
    # state_hashes[0] is the spawn baseline (pre any press). The
    # consecutive_press_count defaults to 0 via the dataclass default.
    #
    # Session reset semantic: every captain dispatch of a target lever
    # flows through this initializer, which produces a fresh state. So
    # consecutive_press_count and state_hashes reset on every:
    #   - Groundhog Day life advance (PER_LIFE_SCRATCHPAD reset)
    #   - Reinvestigation trigger that re-initializes the cycle probe
    #   - Captain re-entry at the lever for any other reason
    # This preserves Groundhog Day determinism: same lever in same
    # starting state gets the same K=20 spam budget per session.
    from virelai_v4.library.cycle_probe import (
        _hud_masked_state_hash,
        _live_counter_cells,
    )
    lc_region = None
    arr = getattr(context, "action_reality_report", None)
    if arr is not None:
        lc_region = getattr(arr, "life_counter_region", None)
    # WO-CP1-FIX-B: the spawn hash must use the SAME live-region masking as the
    # per-press hashes (extra_cells = COUNTER slots), or the chain mismatches.
    spawn_hash = _hud_masked_state_hash(
        np.asarray(spawn_frame, dtype=np.int32),
        getattr(context, "hud_mask", None),
        lc_region,
        extra_cells=_live_counter_cells(library),
    )

    return CycleProbeState(
        target_lever_coord=target_coord,
        target_object_region_id=region_id,
        iteration=0,
        accumulated_frames=[np.asarray(spawn_frame, dtype=np.int32).copy()],
        mode=mode,
        nav_path=None,
        nav_path_index=0,
        nav_in_reset=False,
        consecutive_press_count=0,
        state_hashes=[spawn_hash],
    )


__all__ = [
    "_has_unprobed_lever",
    "_select_next_unprobed_lever",
    "_initialize_cycle_probe_state",
]
