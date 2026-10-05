"""The level's own record, read back: boards, lever states and lever effects (R9-R24, D18 and D19).

Author: Claude (Alpha build seat), 2026-10-04. RULING_G4_CONTROLLER_FIRST_v2_2026-10-04 (Director-ruled).

Every transition of a level is a lossless sparse row in the machine's record (``transition_index``,
R9-R06; tagged with its life and level, R9-R16). Walking those rows backward from the current board
gives every board the level has shown, exactly. From those boards this module reads what the
controller can certify without a model call:

- D18 · each lever region's states: every distinct content the region has shown on this level, in
  first-seen order (S0, S1, ...). The card used to name a state only when a press rewrote the whole
  region, which never happened on vc33 level 3 (v7: 1,947 of 1,947 ``state_now`` read UNRECORDED);
- D19 · each recorded lever press: which lever regions it changed, whether it changed anything
  else outside the counter mask, and the masked boards before and after. G-2: an observed
  transition is evidence, whatever prediction preceded it.

A transition that ended a life or the level is not evidence about the levers (R9-R16) and is skipped
as a press; its cells still rebuild the boards. Pure functions: nothing here changes the machine.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from inference.framework.g4_relations import UNCHANGED, masked_address, masked_changes

TERMINAL_STATES = ("GAME_OVER", "WIN", "RESET")


@dataclass(frozen=True)
class Press:
    """One recorded press of a lever on this level, read from the boards (D19)."""

    transition_id: int
    evidence_ref: str
    lever: str
    action: dict[str, Any]
    changed_levers: tuple[str, ...]
    elsewhere: bool
    before_address: str
    after_address: str

    @property
    def null(self) -> bool:
        return not self.changed_levers and not self.elsewhere


def level_rows(machine: Any) -> list[dict[str, Any]]:
    level = machine.lives.level
    return [row for row in machine.transition_index if row.get("level") == level]


def level_boards(machine: Any) -> list[tuple[dict[str, Any], list[list[int]], list[list[int]]]]:
    """(row, board before, board after) for every row of this level, rebuilt backward from now."""
    from inference.framework.card_builder import _current_grid

    grid = _current_grid(machine)
    if grid is None:
        return []
    boards = []
    after = [list(row) for row in grid]
    for row in reversed(level_rows(machine)):
        before = [list(line) for line in after]
        for r, c, old, _new in row.get("changed") or ():
            if old is not None:
                before[r][c] = old
        boards.append((row, before, after))
        after = before
    boards.reverse()
    return boards


def region_histories(regions: Sequence[Any], boards: Sequence[tuple], grid: Sequence[Sequence[int]] | None) -> dict[str, tuple]:
    """D18: every distinct content each region has shown on this level, first seen first."""
    seen: dict[str, list[tuple[int, ...]]] = {region.entity_id: [] for region in regions}
    shown = [boards[0][1]] if boards else []
    shown += [after for _row, _before, after in boards]
    if grid is not None:
        shown.append(grid)
    for board in shown:
        for region in regions:
            content = tuple(board[r][c] for r, c in region.cells)
            if content not in seen[region.entity_id]:
                seen[region.entity_id].append(content)
    return {key: tuple(value) for key, value in seen.items()}


def _lever_objects(machine: Any, regions: Sequence[Any]) -> dict[str, set[tuple[int, int]]]:
    """Each lever's own object cells (the G3 entity ledger), where a click presses it."""
    ledger = machine._adapters["G3-LEVERS"]._ensure_entity_ledger()
    return {region.entity_id: {tuple(cell) for cell in ledger.cells_for(region.entity_id)} for region in regions}


def _acted_lever(regions: Sequence[Any], objects: Mapping[str, set], action: Mapping[str, Any]) -> str | None:
    """The lever a click pressed: its recorded click site, or a cell of its own object.

    Never a cell of its effect region: a click on another object inside the area a lever moves is
    not a press of that lever.
    """
    site = (action.get("row"), action.get("col"))
    for region in regions:
        click = region.click or {}
        if (click.get("row"), click.get("col")) == site and click.get("action") == action.get("action"):
            return region.entity_id
    return next((region.entity_id for region in regions if site in objects.get(region.entity_id, ())), None)


def presses(machine: Any, regions: Sequence[Any], boards: Sequence[tuple] | None = None) -> list[Press]:
    """D19: every non-terminal press of a lever on this level, with what it changed."""
    law = machine.counter.mask_law
    inside = {cell for region in regions for cell in region.cells}
    objects = _lever_objects(machine, regions)
    found = []
    for row, before, after in boards if boards is not None else level_boards(machine):
        if row.get("kind") == "RESET" or row.get("boundary_state") in TERMINAL_STATES:
            continue
        lever = _acted_lever(regions, objects, row.get("action") or {})
        if lever is None:
            continue
        changed = masked_changes(before, after, law)
        found.append(Press(
            transition_id=int(row["transition_id"]),
            evidence_ref=str(row.get("evidence_id") or f"T{row['transition_id']}"),
            lever=lever,
            action=dict(row.get("action") or {}),
            changed_levers=tuple(region.entity_id for region in regions if region.observe(changed) != UNCHANGED),
            elsewhere=any(cell not in inside for cell in changed),
            before_address=masked_address(before, law),
            after_address=masked_address(after, law),
        ))
    return found


def split_outcomes(found: Sequence[Press]) -> list[dict[str, Any]]:
    """The same press from the same masked board with different outcomes: a missing condition."""
    rows: dict[tuple, dict[str, list[str]]] = {}
    for press in found:
        key = (press.lever, press.before_address)
        rows.setdefault(key, {}).setdefault(press.after_address, []).append(press.evidence_ref)
    return [
        {"lever": lever, "before_address": before, "outcomes": outcomes,
         "reading": "the same press from the same masked board had different outcomes: a condition is missing"}
        for (lever, before), outcomes in rows.items() if len(outcomes) > 1
    ]


__all__ = ["Press", "level_boards", "level_rows", "presses", "region_histories", "split_outcomes"]
