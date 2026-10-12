"""The level's board, rebuilt and verified from its own record (G3 reset continuity).

Author: Claude (Alpha build seat), 2026-10-11. DIAGNOSTIC_G3_LEDGER_FRAME_SYNC_v1 option A, ruled by Sol: G2 starts
from the latest observed board, including any reset, and G3's entity ledger threads the resets since that seed
alongside G2's outcomes. The machine's ``transition_index`` keeps every transition (probes, free play and harness
RESETs) with its sparse changed cells ``[row, col, before, after]``. This module replays those rows over the
level-entry board, in transition order, and **checks every recorded ``before`` against the rebuilt board**. A row
that contradicts the board, or a transition recorded twice, is a broken record: it raises ``BrokenBoardRecord``,
which names the transition, and nothing is rebuilt past it. A gap in the level's transition ids is a missing
row and is rejected the same way. Callers report it; nobody resynchronises around it.

Pure functions; no machine state. Called once per level (G2's seed, G3's ledger build), never per action.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

Board = tuple[tuple[int, ...], ...]


class BrokenBoardRecord(ValueError):
    """The level's record cannot rebuild the board: the named transition contradicts it, repeats or is missing."""

    def __init__(self, transition_id: int, message: str) -> None:
        super().__init__(message)
        self.transition_id = int(transition_id)


def _level_rows(rows: Iterable[Mapping[str, Any]], entry: int) -> list[Mapping[str, Any]]:
    """The level's rows in order. A transition id is the game's history length (every executed action, RESET
    included), so a level's executed transitions run contiguously from ``entry + 1``: a repeated id or a gap is
    a broken record. An omission after the last recorded transition cannot be seen here (H2's record check)."""
    ordered = sorted((row for row in rows if int(row.get("transition_id") or 0) > entry),
                     key=lambda row: int(row["transition_id"]))
    expected = int(entry) + 1
    for row in ordered:
        transition = int(row["transition_id"])
        if transition < expected:
            raise BrokenBoardRecord(transition, f"transition {transition} is recorded twice")
        if transition > expected:
            raise BrokenBoardRecord(expected, f"transition {expected} is missing from the level record "
                                              f"(the recorded ids jump to {transition})")
        expected = transition + 1
    return ordered


def _apply(board: list[list[int]], row: Mapping[str, Any]) -> None:
    transition = int(row["transition_id"])
    for cell in row.get("changed") or ():
        r, c, before, after = (int(cell[0]), int(cell[1]), cell[2], cell[3])
        if not (0 <= r < len(board) and 0 <= c < len(board[r])):
            raise BrokenBoardRecord(transition, f"transition {transition} changes cell ({r}, {c}) outside the board")
        if before is None or after is None or int(before) != board[r][c]:
            raise BrokenBoardRecord(
                transition, f"transition {transition} records cell ({r}, {c}) as {before} before, "
                            f"but the board holds {board[r][c]}")
        board[r][c] = int(after)


def _frozen(board: Sequence[Sequence[int]]) -> Board:
    return tuple(tuple(int(cell) for cell in row) for row in board)


def board_through(entry_board: Sequence[Sequence[int]], rows: Iterable[Mapping[str, Any]], *, entry: int,
                  through: int | None = None) -> Board:
    """The verified board after ``through`` (default: the latest recorded transition of the level)."""
    board = [list(map(int, row)) for row in entry_board]
    for row in _level_rows(rows, entry):
        if through is not None and int(row["transition_id"]) > through:
            break
        _apply(board, row)
    return _frozen(board)


def latest_transition(rows: Iterable[Mapping[str, Any]], *, entry: int) -> int:
    """The last transition the level has recorded (the level's entry when it has none)."""
    return max((int(row.get("transition_id") or 0) for row in rows if int(row.get("transition_id") or 0) > entry),
               default=int(entry))


def _total_outcome(before: Board, after: Board, row: Mapping[str, Any]) -> dict[str, Any]:
    """A RESET as the lossless outcome ``EntityLedger.observe_reset`` reads: every cell's before and after."""
    shape = [len(before), len(before[0]) if before else 0]
    return {
        "schema": "virelai-probe-outcome-v1", "transition_id": int(row["transition_id"]),
        "probe_id": None, "evidence_id": row.get("evidence_id"), "action": {"action": "RESET"},
        "acted_site": None, "boundary": {"state": "NOT_FINISHED", "actor": "SYSTEM_RESET", "reset": True},
        "shape_before": shape, "shape_after": shape,
        "site_transitions": [{"row": r, "col": c, "before": before[r][c], "after": after[r][c]}
                             for r in range(shape[0]) for c in range(shape[1])],
        "changed_cells": [{"row": r, "col": c, "before": before[r][c], "after": after[r][c]}
                          for r in range(shape[0]) for c in range(shape[1]) if before[r][c] != after[r][c]],
        "source": "LEVEL_RECORD_RECONSTRUCTION",
    }


def reset_frames(entry_board: Sequence[Sequence[int]], rows: Iterable[Mapping[str, Any]], *, entry: int,
                 since: int) -> list[dict[str, Any]]:
    """Every RESET after ``since``, in transition order, each as a verified full before-and-after outcome.

    The whole level is rebuilt from its entry so each reset's before-board is checked too; a broken record
    anywhere up to the last reset raises ``BrokenBoardRecord``.
    """
    board = [list(map(int, row)) for row in entry_board]
    frames: list[dict[str, Any]] = []
    for row in _level_rows(rows, entry):
        is_reset = str(row.get("kind") or "") == "RESET"
        before = _frozen(board) if is_reset else None
        _apply(board, row)
        if is_reset and int(row["transition_id"]) > since:
            frames.append(_total_outcome(before, _frozen(board), row))
    return frames


__all__ = ["BrokenBoardRecord", "board_through", "latest_transition", "reset_frames"]
