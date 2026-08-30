"""
virelai_v4/contracts/lever_effect.py — LeverEffect: durable per-lever
per-subject-region measured effect record (WO-EFFECT-STORE-RIGID, WO1).

Populated by physics_accumulator's Path 4 when a rigid-press measurement
resolves to a library subject region (before-cell overlap). Mirrors
MeasuredOperation's discipline: frozen, immutable, no library access.

Per CE ruling (June 10): a typed dataclass in its own module — NOT a thin
Dict[region_id, vector]. LibraryObject holds a Tuple[LeverEffect, ...] as
durable library belief (distinct from the runtime context.physics_vectors
store, which resets at the level boundary).

DURABILITY NOTE (WO1 §0.5.3 finding): stored as a field on LibraryObject, a
LeverEffect inherits LibraryObject lifecycle — it accumulates across lives
within a level (the library persists per Groundhog-Day life) and is rebuilt
fresh on level advance (library/substrate/level_advance.py snapshot+rescan+
discard). That is PERSIST_LIVES_RESET_LEVEL semantics, which matches NR-01
per-world physics (each level measures its own physics). It is NOT "survives
level advance"; see the build report finding.

VECTOR TYPE (WO1 drift correction): the measurer emits an area-weighted mean
displacement rounded to 4 decimals — `Tuple[float, float]`
(operation_measurer.py:48, :117). The WO recommended Tuple[int, int]; file
truth is float, so vector is typed float here to avoid a lossy cast. Rigid
displacements are near-integer; the render rounds for display.

SCHEMA RESERVED FOR WO3 (non-rigid grade): magnitude, direction,
boundary, shape_descriptor. Not initialized in WO1; operation_kind carries
"RIGID" now and admits "NON_RIGID" later without a schema break.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class LeverEffect:
    """One (lever -> subject region) measured effect observation cluster.

    subject_region_id : library region_id of the affected object.
    vector            : (d_row, d_col) centroid displacement for a RIGID
                        translation (measurer truth, float; near-integer).
                        None for a non-rigid effect.
    observation_count : number of merged observations of this (subject, kind).
    operation_kind    : "RIGID" (WO1, rigid translation) or "NON_RIGID"
                        (WO3, shape/volume change).
    cell_count_delta  : WO3 — net foreground cell change for a NON_RIGID effect
                        (+grew / -shrank). None for a rigid effect.
    conserved_transfer_member : WO-C3 — membership flag: True when this
                        per-subject entry participates in the lever's
                        ConservedTransfer relation. A REFERENCE into the
                        relation (the relation is keyed on the lever and holds
                        the members / conserved quantity / boundary); this entry
                        NEVER carries the relation itself (ruling b / §3).
    """
    subject_region_id: int
    vector: Optional[Tuple[float, float]] = None
    observation_count: int = 1
    operation_kind: str = "RIGID"
    cell_count_delta: Optional[int] = None
    conserved_transfer_member: bool = False


__all__ = ["LeverEffect"]
