"""An offline ft09 world continued from the live v2 record, for memory stage M-2 (R9-R08).

Author: Claude (Alpha build seat), 2026-09-29.

The world starts from the v2 record's initial grid and follows the one law the record shows: a
click on any 6x6 tile the record saw respond toggles it between its two recorded colours, and each
such click ticks the bottom bar two cells (12->11, from the right). Every other click changes
nothing, which is what the record shows for the 54 objects G2 clicked. That continuation is a
hypothesis about ft09, not a fact: tiles the live run never reached are assumed inert.

Since R9-R12 the world can be built from the live memory-v1 record (``V1_RECORD``), which reached
all eight tiles, and it carries the law that run observed (L-1): the click that spends the bar's
last cells ends the life (``bar_empty``); the harness then resets the board.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from inference.framework.record_replay import decode_grid, load_record, lossless_outcome

V2_RECORD = Path(__file__).parent / "fixtures" / "ft09_kaggle_v2_record.json.gz"
V1_RECORD = Path(__file__).parent / "fixtures" / "ft09_kaggle_memory_v1_record.json.gz"
BAR_ROW, BAR, BAR_SPENT = 63, 12, 11


class Ft09World:
    def __init__(self, record: dict[str, Any] | None = None) -> None:
        record = record or load_record(V2_RECORD)
        self.grid = decode_grid(record["initial_grid"])
        self.valid_actions = list(record.get("valid_actions") or ["ACTION6"])
        self.tiles: dict[tuple[int, int, int, int], tuple[int, int]] = {}
        for step in record["steps"]:
            if step.get("kind") == "RESET":
                continue
            cells = [(r, c, b, a) for r, c, b, a in step["changed"] if r != BAR_ROW]
            if cells:
                rows, cols = [r for r, *_ in cells], [c for _, c, *_ in cells]
                self.tiles[(min(rows), min(cols), max(rows), max(cols))] = tuple(sorted({cells[0][2], cells[0][3]}))
        self.transition_id = 0

    def bar_empty(self) -> bool:
        return all(value != BAR for value in self.grid[BAR_ROW])

    def _tile_at(self, row: int, col: int) -> tuple[int, int, int, int] | None:
        return next((box for box in self.tiles if box[0] <= row <= box[2] and box[1] <= col <= box[3]), None)

    def changes(self, action: dict[str, Any]) -> list[list[int]]:
        box = self._tile_at(int(action["row"]), int(action["col"]))
        if box is None:
            return []
        low, high = self.tiles[box]
        before = self.grid[box[0]][box[1]]
        after = low if before == high else high
        changed = [[r, c, before, after] for r in range(box[0], box[2] + 1) for c in range(box[1], box[3] + 1)]
        spare = sorted(c for c in range(len(self.grid[BAR_ROW])) if self.grid[BAR_ROW][c] == BAR)[-2:]
        return changed + [[BAR_ROW, c, BAR, BAR_SPENT] for c in spare]

    def step(self, action: dict[str, Any]) -> dict[str, Any]:
        """Apply one action; return the lossless outcome a run records."""
        self.transition_id += 1
        self.grid, outcome = lossless_outcome(self.grid, self.transition_id, action, self.changes(action))
        return outcome


__all__ = ["Ft09World", "V1_RECORD", "V2_RECORD"]
