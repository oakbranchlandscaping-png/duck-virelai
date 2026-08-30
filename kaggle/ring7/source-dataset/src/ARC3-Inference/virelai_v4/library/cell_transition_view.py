"""
virelai_v4/library/cell_transition_view.py — the canonical total cell-transition
view and its narrowing (SPEC_DELTA_LEDGER §2/§9).

WO-W1-01a — relocated verbatim from `contracts/world_delta.py` (WO-W1-01a §1: a
mechanical move, no logic change). Moved because `contracts/` declares shapes and
does not implement lazy views — two concrete, behavior-bearing classes living in
the contract module was a phase-sovereignty inversion. The contract now declares
only `cell_transitions`/`world_transitions` as `Mapping` (typing-only); this module
implements the two concrete views and `world_delta_computer.py` constructs and
injects them.

Two Mapping-conforming, lazy, grid-backed views:

  TotalCellTransitions — the total catalog: every cell, HELD included,
      privileging nothing (SPEC_DELTA_LEDGER §2 property 3).
  RestrictedCellView   — a read-only narrowing of any such Mapping to a key
      subset. This is what `world_transitions` is derived from in
      `world_delta_computer.py`: "one store, one derived view, its single
      reader untouched by construction."

Neither view stores a copy of grid contents — both keep only the two grid
references and compute `(a, b)` on demand, so materializing them costs nothing
beyond the frame's own retained grids (SPEC_DELTA_LEDGER §9's "derived-but-
retained view" fork, taken here rather than delta-primary storage).
"""
from __future__ import annotations

from typing import Any, FrozenSet, Iterator, Mapping, Optional, Tuple

from virelai_v4.contracts.world_delta import CellCoord, ClassTransition


class TotalCellTransitions(Mapping[CellCoord, ClassTransition]):
    """The canonical, convention-free `(a -> b)` view over one frame-pair.

    Total by construction: every `(row, col)` in the grid answers a
    transition, HELD (`a == b`) exactly as readily as CHANGED (SPEC_DELTA_LEDGER
    §1) — this view privileges nothing (§2 property 3) and asserts nothing
    above the transition (§8 — no object, no verb, no appear/clear/recolor
    typing; that reading is a derived rung above this one).

    Lazy and grid-backed, never accumulated: holds only the two grid
    references handed to it at construction — one frame-transition's worth —
    and computes each `(a, b)` from them on lookup or iteration. `[]`,
    `.get()`, `in`, `len()`, iteration, and `.items()` all behave exactly as
    if every cell were stored (the binding constraint on this rung) — this is
    the `Mapping` contract itself, not an approximation of it.

    Empty (zero keys, still `Mapping`-conforming) when either grid is absent,
    or the two grids differ in shape — the honest absence, never an invented
    value (the same discipline WO-W1-01's §0.4 diagnostic asked for on the
    no-prior-grid path).

    K-2-DEFERRED (ratified, not built here): a future transition-keyed index
    — cells grouped by `(a, b)`, giving net-per-integer counts without
    inversion — can be built later by one pass over this view's `.items()`.
    That is the one full traversal such an index would need; it is not
    materialized here. It ships with its first customer, in a later WO.
    """

    __slots__ = ("_prev", "_curr", "_shape")

    def __init__(self, prev_grid: Optional[Any], curr_grid: Optional[Any]) -> None:
        self._prev = prev_grid
        self._curr = curr_grid
        shape: Optional[Tuple[int, int]] = None
        if prev_grid is not None and curr_grid is not None:
            try:
                if tuple(prev_grid.shape[:2]) == tuple(curr_grid.shape[:2]):
                    shape = (int(prev_grid.shape[0]), int(prev_grid.shape[1]))
            except Exception:
                shape = None
        self._shape = shape

    def __getitem__(self, key: CellCoord) -> ClassTransition:
        if self._shape is None:
            raise KeyError(key)
        r, c = key
        rows, cols = self._shape
        if not (0 <= r < rows and 0 <= c < cols):
            raise KeyError(key)
        try:
            return (int(self._prev[r, c]), int(self._curr[r, c]))
        except Exception as exc:
            raise KeyError(key) from exc

    def __iter__(self) -> Iterator[CellCoord]:
        if self._shape is None:
            return
        rows, cols = self._shape
        for r in range(rows):
            for c in range(cols):
                yield (r, c)

    def __len__(self) -> int:
        if self._shape is None:
            return 0
        rows, cols = self._shape
        return rows * cols


class RestrictedCellView(Mapping[CellCoord, ClassTransition]):
    """A read-only narrowing of a total-transitions `Mapping` to a key subset.

    What `world_transitions` becomes at the one builder call site in
    `world_delta_computer.py`: identical observable content to the
    independently-populated dict it replaces, but sourced from the one
    `cell_transitions` store beneath it — no second per-cell loop, no second
    field minted.
    """

    __slots__ = ("_source", "_keys")

    def __init__(
        self,
        source: Mapping[CellCoord, ClassTransition],
        keys: Any,
    ) -> None:
        self._source = source
        self._keys: FrozenSet[CellCoord] = frozenset(keys)

    def __getitem__(self, key: CellCoord) -> ClassTransition:
        if key not in self._keys:
            raise KeyError(key)
        return self._source[key]

    def __iter__(self) -> Iterator[CellCoord]:
        return iter(self._keys)

    def __len__(self) -> int:
        return len(self._keys)
