"""
virelai_v4/contracts/world_delta.py — Canonical per-frame WorldDelta contract.

WO-02-ARCH LEVER-CATALOG · WO-W1-01 (cell_transitions, the canonical catalog)

Computed once at the top of sync_library, consumed by every downstream system.
Replaces all ad-hoc _compute_world_delta calls.

Import sovereignty: imports only dataclasses and typing. Nothing else.

WO-W1-01a: the concrete `TotalCellTransitions`/`RestrictedCellView` views that
populate `cell_transitions`/`world_transitions` were relocated to
`library/cell_transition_view.py` — a contract declares shapes, it does not
implement lazy views. This module now only widens the field annotations to
`Mapping`; `library/world_delta_computer.py` constructs the concrete views and
injects them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import FrozenSet, Mapping, Optional, Tuple

CellCoord = Tuple[int, int]
ClassTransition = Tuple[int, int]  # (old_class, new_class)


@dataclass(frozen=True)
class WorldDelta:
    """
    Canonical per-frame delta, computed once at the top of sync_library,
    consumed by every downstream system. Replaces all ad-hoc delta computations.

    Invariants:
        raw_cells = ego_cells ∪ hud_cells ∪ world_cells
        ego_cells, hud_cells, world_cells are disjoint
        world_cells is the productive signal for causal reasoning
    """
    # Cell sets (the three-stream split)
    raw_cells: FrozenSet[CellCoord]
    ego_cells: FrozenSet[CellCoord]
    hud_cells: FrozenSet[CellCoord]
    world_cells: FrozenSet[CellCoord]

    # SUPERSEDED (WO-W1-01 §2.3) — retiring when its sole reader,
    # diagnostics/dossier.py:1526 (`_delta_attribution`), migrates to read
    # `cell_transitions` restricted to `world_cells` directly, in a later W1
    # rung. Populated at the one builder call site in world_delta_computer.py
    # as a read-only narrowing over `cell_transitions` (one store beneath it,
    # not a second independently-populated loop); any direct/legacy
    # construction (every existing call site that passes `world_transitions=`
    # explicitly, predating this WO) is untouched and keeps working exactly
    # as before. Annotation widened Dict -> Mapping (WO-W1-01 §2.2) — a
    # strict widening, not a contract change: every prior caller already
    # passed a `dict`, which is already a `Mapping`.
    world_transitions: Mapping[CellCoord, ClassTransition] = field(default_factory=dict)

    # WO-W1-01 — the canonical total catalog (SPEC_DELTA_LEDGER §2): every
    # cell in the grid, HELD included, privileging nothing. Defaults to an
    # empty dict for legacy/direct construction sites that predate this field
    # and never populate it — it has no consumer yet (WO-W1-01 §3 wires
    # none). `library/world_delta_computer.py` populates it as a
    # `TotalCellTransitions` view (see `library/cell_transition_view.py`,
    # WO-W1-01a) over the frame's own two grids.
    cell_transitions: Mapping[CellCoord, ClassTransition] = field(default_factory=dict)

    # Frame provenance
    frame_action: int = -1
    prev_frame_hash: Optional[int] = None
    curr_frame_hash: Optional[int] = None

    # WO-W1b-03 — RULING_OBSERVERS_INTEGRATOR_v1 Clause A: the canonical
    # record grows to carry the same frame-identity facts the observer
    # (cybernetic/frame_delta.py's FrameDelta) already carries, so a future
    # consumer-of-record can read step/action_id here instead of from the
    # observer. Defaults preserve every legacy/direct construction site that
    # predates this field and never populates it (annotation/field addition
    # only — no other change to this contract).
    step: int = -1
    action_id: int = -1

    # WO-W2-B-01 — SPEC_DELTA_LEDGER_v1 §2's ledger form ("cells grouped by
    # (from, to)"), materialized canonical-side. RULING_OBSERVERS_INTEGRATOR_v1
    # Clause A: the index lives on the record, not the observer — the observer
    # (cybernetic/frame_delta.py's class_transitions) keeps computing
    # independently and becomes this field's parallax grading surface, per
    # Clause B. Values are member cells, not counts: a count is always
    # derivable (len(cells)) but identity is not recoverable from a count once
    # discarded, and no constraint yet forces that cut — retained per ruling.
    # Additive: defaults to an empty dict for every legacy/direct construction
    # site that predates this field and never populates it.
    transition_index: Mapping[ClassTransition, FrozenSet[CellCoord]] = field(default_factory=dict)

    @property
    def raw_count(self) -> int:
        return len(self.raw_cells)

    @property
    def world_count(self) -> int:
        return len(self.world_cells)

    @property
    def is_world_empty(self) -> bool:
        return len(self.world_cells) == 0
