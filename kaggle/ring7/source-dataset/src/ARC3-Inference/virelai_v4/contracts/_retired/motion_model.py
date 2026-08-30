"""
contracts/motion_model.py — WO-FORGE-06-L2: MotionModelArtifact

Describes the ego's motion mechanics assembled from gambit raw_deltas + CUD
AgentStructure.  Zero additional probes required — all signals exist in memory.

Authoritative source for:
  - Navigation:            step_vectors → BFS action costs / direction
  - Collision detection:   collision_dirs → impassable directions at spawn
  - Lever access planning: replacement_mask_size → ego-vs-world delta separation
  - Kernel-aware planning: kernel_type → graph construction strategy

Kernel type taxonomy:
  FLIP_TRANSLATION  Entire footprint teleports by stride.  Old position fully
                    restored, new position fully overwritten.  Replacement mask
                    = two disjoint, equal-size blocks.  LS20 uses this.
  CRAWLER           Footprint shifts by < footprint_width.  Old and new
                    positions overlap.  Replacement mask = thin edge band.
  TELEPORT          Old and new positions are non-adjacent (distance >> stride).
  UNKNOWN           No template matched.

Persisted across Groundhog Day lives via state["motion_model"].

Virelai Research Lab · WO-FORGE-06-L2 · March 2026
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Tuple


@dataclass(frozen=True)
class MotionModelArtifact:
    """Empirically assembled ego motion model.

    Assembled by discovery.physics.motion_model_assembler.assemble_motion_model()
    from CUD AgentStructure + gambit raw_deltas.  Frozen — immutable once built.
    """

    # -----------------------------------------------------------------------
    # From CUD AgentStructure
    # -----------------------------------------------------------------------

    kernel_type: str
    """Motion kernel topology: FLIP_TRANSLATION | CRAWLER | TELEPORT | UNKNOWN."""

    footprint_height: int
    """Bounding-box height of the ego footprint in pixels."""

    footprint_width: int
    """Bounding-box width of the ego footprint in pixels."""

    footprint_pixel_count: int
    """Total pixels in the ego body (may be < height × width for irregular shapes)."""

    step_vectors: Dict[int, Tuple[int, int]]
    """Per-action integer stride vectors: {action_id: (delta_row, delta_col)}.

    Derived from CUD action_translation_map.  Blocked or NOOP actions map to
    (0, 0).  Example for LS20: {1: (-5,0), 2: (5,0), 3: (0,-5), 4: (0,5), 5: (0,0)}.
    """

    stride: int
    """Maximum absolute displacement across all non-zero step_vectors.

    Derived field: max(max(|dr|, |dc|) for (dr,dc) in step_vectors.values()
                      if (dr,dc) != (0,0)).
    LS20: 5.
    """

    # -----------------------------------------------------------------------
    # From gambit raw_deltas
    # -----------------------------------------------------------------------

    replacement_mask_size: int
    """Average total pixels changed per successful directional move.

    Includes both departing cells (ego vacated) and arriving cells (ego
    occupied).  HUD pixels excluded.  LS20: ~50 (25 departing + 25 arriving).
    Layer 3 uses this as the threshold: delta > replacement_mask_size → lever
    activation.
    """

    departing_cell_count: int
    """Average pixels restored to floor when ego leaves a position.  LS20: ~25."""

    arriving_cell_count: int
    """Average pixels overwritten when ego enters a position.  LS20: ~25."""

    collision_dirs: FrozenSet[int]
    """Action IDs that produced zero displacement at spawn (blocked directions).

    LS20: frozenset({2}) — DOWN is wall-blocked at spawn.
    """

    # -----------------------------------------------------------------------
    # Derived fields
    # -----------------------------------------------------------------------

    successful_move_dirs: FrozenSet[int]
    """Action IDs that produced successful displacement at spawn.

    Complement of collision_dirs (excluding NOOP actions like action 5).
    LS20: frozenset({1, 3, 4}).
    """

    confidence: float
    """Assembly confidence [0.0, 1.0].

    From CUD layout_coherence if available; falls back to 0.8 when ≥ 2
    successful dirs observed.  Used by downstream consumers to gate usage.
    """
