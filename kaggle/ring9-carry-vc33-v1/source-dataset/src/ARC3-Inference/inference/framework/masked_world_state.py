"""Counter-masked delta partition and retroactive world-state identity.

Raw integer grids remain the record.  A locked MaskLaw supplies a quotient view:
counter cells become an address token, HUD-only changes disappear from world
delta, and every retained frame is re-addressed under the same mask.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Mapping, Sequence

from inference.framework.counter_verification import MASK_SENTINEL, MaskLaw


Cell = tuple[int, int]
Grid = tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class DeltaPartition:
    raw_cells: frozenset[Cell]
    hud_cells: frozenset[Cell]
    world_cells: frozenset[Cell]

    @property
    def is_hud_only(self) -> bool:
        return bool(self.raw_cells) and not self.world_cells

    @property
    def world_changed(self) -> bool:
        return bool(self.world_cells)


@dataclass(frozen=True)
class ArchivedState:
    node_id: int
    raw_address: str
    world_address: str
    raw_grid: Grid


@dataclass(frozen=True)
class ArchivedTransition:
    evidence_ref: str
    before_node: int
    after_node: int
    delta: DeltaPartition


def _canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()


def _grid(grid: Sequence[Sequence[int]]) -> Grid:
    return tuple(tuple(int(value) for value in row) for row in grid)


def raw_address(grid: Sequence[Sequence[int]]) -> str:
    normalized = _grid(grid)
    return hashlib.sha256(_canonical(normalized)).hexdigest()[:16]


def world_address(grid: Sequence[Sequence[int]], law: MaskLaw) -> str:
    normalized = _grid(grid)
    hidden = set(law.cells)
    view = tuple(
        tuple(MASK_SENTINEL if (row, col) in hidden else value for col, value in enumerate(values))
        for row, values in enumerate(normalized)
    )
    return hashlib.sha256(_canonical(view)).hexdigest()[:16]


def partition_delta(
    before: Sequence[Sequence[int]],
    after: Sequence[Sequence[int]],
    law: MaskLaw,
) -> DeltaPartition:
    left, right = _grid(before), _grid(after)
    if tuple(map(len, left)) != tuple(map(len, right)) or len(left) != len(right):
        raise ValueError("Delta partition requires fixed grid geometry.")
    raw = frozenset(
        (row, col)
        for row, values in enumerate(left)
        for col, value in enumerate(values)
        if value != right[row][col]
    )
    mask = frozenset(law.cells)
    hud = raw & mask
    world = raw - mask
    if raw != hud | world or hud & world:
        raise AssertionError("raw delta must partition exactly into HUD and world cells")
    return DeltaPartition(raw_cells=raw, hud_cells=hud, world_cells=world)


class MaskedStateArchive:
    """Append raw states, then derive masked addresses and world deltas."""

    def __init__(self, law: MaskLaw) -> None:
        self.law = law
        self.states: list[ArchivedState] = []
        self.transitions: list[ArchivedTransition] = []

    def _append_state(self, grid: Sequence[Sequence[int]]) -> int:
        normalized = _grid(grid)
        node_id = len(self.states)
        self.states.append(ArchivedState(
            node_id=node_id,
            raw_address=raw_address(normalized),
            world_address=world_address(normalized, self.law),
            raw_grid=normalized,
        ))
        return node_id

    def record_transition(
        self,
        *,
        evidence_ref: str,
        before: Sequence[Sequence[int]],
        after: Sequence[Sequence[int]],
    ) -> ArchivedTransition:
        left = _grid(before)
        if self.states and self.states[-1].raw_grid == left:
            before_node = self.states[-1].node_id
        else:
            before_node = self._append_state(left)
        after_node = self._append_state(after)
        transition = ArchivedTransition(
            evidence_ref=str(evidence_ref),
            before_node=before_node,
            after_node=after_node,
            delta=partition_delta(left, after, self.law),
        )
        self.transitions.append(transition)
        return transition

    def snapshot(self) -> dict[str, Any]:
        visits: dict[str, list[int]] = {}
        for state in self.states:
            visits.setdefault(state.world_address, []).append(state.node_id)
        return {
            "schema": "virelai-masked-state-archive-v1",
            "mask_law_version_id": self.law.law_version_id,
            "raw_state_count": len({item.raw_address for item in self.states}),
            "world_state_count": len(visits),
            "world_revisit_count": sum(len(nodes) - 1 for nodes in visits.values()),
            "hud_only_transition_count": sum(item.delta.is_hud_only for item in self.transitions),
            "world_change_transition_count": sum(item.delta.world_changed for item in self.transitions),
            "visits": dict(sorted(visits.items())),
            "transitions": [
                {
                    **asdict(item),
                    "delta": {
                        "raw_cells": sorted(item.delta.raw_cells),
                        "hud_cells": sorted(item.delta.hud_cells),
                        "world_cells": sorted(item.delta.world_cells),
                        "is_hud_only": item.delta.is_hud_only,
                        "world_changed": item.delta.world_changed,
                    },
                }
                for item in self.transitions
            ],
        }


def grids_from_probe_outcome(
    outcome: Mapping[str, Any]
) -> tuple[Grid, Grid] | None:
    shape = outcome.get("shape_before")
    transitions = outcome.get("site_transitions")
    if (
        not isinstance(shape, (list, tuple))
        or len(shape) != 2
        or not isinstance(transitions, (list, tuple))
    ):
        return None
    rows, cols = int(shape[0]), int(shape[1])
    before = [[0 for _ in range(cols)] for _ in range(rows)]
    after = [[0 for _ in range(cols)] for _ in range(rows)]
    seen: set[Cell] = set()
    for item in transitions:
        if not isinstance(item, Mapping):
            return None
        row, col = int(item["row"]), int(item["col"])
        if not (0 <= row < rows and 0 <= col < cols):
            return None
        before[row][col] = int(item["before"])
        after[row][col] = int(item["after"])
        seen.add((row, col))
    if len(seen) != rows * cols:
        return None
    return _grid(before), _grid(after)

