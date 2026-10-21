"""The normal-play frontier: one legal, untried action after an unproductive Duck turn (WO-RUNTIME-01 §4, ruling A).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. A port of Ring 7's ``cybernetic/state_tracker.py``
(``virelai_v4``, sha256 ``fdc91f38...79ef``): the legal set of a board signature, ``untried = legal - tried`` (an
invalid action recorded from the board counts as tried, so it mints no frontier), and ``order_untried``'s
diversity-first order (the least globally tried target first, then ``(action_id, str(target))`` as the determinism
floor). Ring 7's re-home plan (``plan_to_frontier``) is **not** ported: an exhausted board stops cleanly with its proof
(Director ruling Q4), and there is no graph routing toward another board in this slice.

Ring 9 binding:

* **signature** — R-8's key: ``masked_address(grid, machine.counter.mask_law)`` (the raw address with no mask law);
* **edge key** — ``(ACTION<n>, None)`` for a simple action; ``(ACTION6, anchor)`` for a click, where the anchor is
  the minimum cell of the 4-connected same-integer component the click lands in (the visual-object definition of
  ``adaptive_ego_coverage._components``);
* **legal** — computed for the current board when asked (Q4: currently legal): ``PlayTarget._available()``, with
  ACTION6 expanded into one key per component (in NAVIGATION and HYBRID worlds, G2's filter: no FIELD-scale component
  and no ego cell);
* **tried** — derived incrementally from the level's record tier (``machine.transition_index``: every transition of
  the level, gate probes included), replayed over the level-entry board; no hook in ``record_outcome`` and no second
  writable store, only a cursor; level-scoped, rebuilt on a new level or mask law;
* **barred** — R-8's same-board no-effect memory (``PlayTarget._noops``), shown in the proof.

Exactly one action per call; no plan and no queue.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Sequence

Key = tuple[str, Any]


@dataclass(frozen=True)
class Choice:
    key: Key
    action: dict[str, Any]
    signature: str


def _target_token(target: Any) -> str:
    return "" if target is None else str(target)


def order_untried(keys: Iterable[Key], tried: Mapping[str, Iterable[Key]]) -> list[Key]:
    """Ring 7 ``order_untried``: least globally tried target first, then ``(action_id, str(target))``."""
    counts: dict[Any, int] = {}
    for edges in tried.values():
        for key in edges:
            counts[key[1]] = counts.get(key[1], 0) + 1
    return sorted(keys, key=lambda key: (counts.get(key[1], 0), key[0], _target_token(key[1])))


def untried(legal: Iterable[Key], tried: Iterable[Key]) -> set[Key]:
    return set(legal) - set(tried)


def component(board: Sequence[Sequence[int]], row: int, col: int) -> tuple[tuple[int, int], ...]:
    """The 4-connected same-integer component holding (row, col), sorted (empty off the board)."""
    if not (0 <= row < len(board) and 0 <= col < len(board[row])):
        return ()
    value, seen, todo = int(board[row][col]), {(row, col)}, [(row, col)]
    while todo:
        r, c = todo.pop()
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if (nr, nc) not in seen and 0 <= nr < len(board) and 0 <= nc < len(board[nr]) \
                    and int(board[nr][nc]) == value:
                seen.add((nr, nc))
                todo.append((nr, nc))
    return tuple(sorted(seen))


def edge_key(action: Mapping[str, Any], board: Sequence[Sequence[int]]) -> Key:
    name = str(action.get("action") or "")
    if "row" not in action or "col" not in action:
        return (name, None)
    cells = component(board, int(action["row"]), int(action["col"]))
    return (name, cells[0] if cells else (int(action["row"]), int(action["col"])))


class Frontier:
    """Level-scoped frontier state, refreshed from the machine's record on every use."""

    def __init__(self) -> None:
        self.scope: tuple | None = None
        self.cursor = 0
        self.board: list[list[int]] | None = None
        self.tried_edges: dict[str, set[Key]] = {}
        self.tried_at: dict[tuple[str, Key], list[int]] = {}
        self.legal_cache: dict[tuple, frozenset[Key]] = {}
        self.broken: str | None = None  # a broken level record stops the tried derivation where it broke

    def _law(self, machine: Any) -> Any:
        return getattr(getattr(machine, "counter", None), "mask_law", None)

    def _sig(self, machine: Any, board: Sequence[Sequence[int]]) -> str:
        from inference.framework.g4_relations import masked_address

        return masked_address([list(row) for row in board], self._law(machine))

    def refresh(self, machine: Any) -> None:
        from inference.framework.level_board import BrokenBoardRecord, _apply, _level_rows

        law = self._law(machine)
        scope = (id(machine), int(machine.lives.level), int(machine.carry.entry),
                 None if law is None else law.law_version_id)
        if scope != self.scope:
            self.__init__()
            self.scope = scope
            self.board = [list(map(int, row)) for row in machine.ego._initial_grid]
        try:  # what was tried before a break stays proven (each edge cites its transition); nothing after it is read
            rows = _level_rows(machine.transition_index, int(machine.carry.entry))
            for row in rows[self.cursor:]:
                action = row.get("action") or {}
                if action.get("action"):
                    site = row.get("acted_site") or {}
                    key = edge_key({**action, **site}, self.board)
                    self.mark_tried(self._sig(machine, self.board), key, transition_id=int(row["transition_id"]))
                _apply(self.board, row)
                self.cursor += 1
        except BrokenBoardRecord as exc:
            self.broken = str(exc)

    def mark_tried(self, signature: str, key: Key, *, transition_id: int) -> None:
        self.tried_edges.setdefault(signature, set()).add(tuple(key))
        cited = self.tried_at.setdefault((signature, tuple(key)), [])
        if int(transition_id) not in cited:
            cited.append(int(transition_id))

    def _current(self, machine: Any) -> list[list[int]]:
        from inference.framework.card_builder import _current_grid

        grid = _current_grid(machine)
        return [list(map(int, row)) for row in (grid if grid is not None else self.board or [])]

    def signature(self, machine: Any) -> str:
        self.refresh(machine)  # the level scope first, so marks made against this signature survive
        return self._sig(machine, self._current(machine))

    def legal(self, machine: Any) -> frozenset[Key]:
        from inference.framework.adaptive_ego_coverage import AdaptiveCoordinateCoverage
        from inference.framework.virelai_gates import PLAY_GATE_ID, control_archetype_prior

        self.refresh(machine)
        board = self._current(machine)
        available = tuple(machine._adapters[PLAY_GATE_ID]._available())
        cache_key = (repr(board), available)
        if cache_key not in self.legal_cache:
            keys = {(name, None) for name in available if name != "ACTION6"}
            if "ACTION6" in available:
                world = control_archetype_prior(machine.ego.affordances)["world_type"]
                ego = set(getattr(machine.counter, "_excluded_ego_cells", ()) or ())
                for item in AdaptiveCoordinateCoverage(board).ranked_candidates():
                    if world in {"NAVIGATION", "HYBRID"} and (item.scale == "FIELD" or set(item.cells) & ego):
                        continue
                    keys.add(("ACTION6", tuple(item.anchor)))
            self.legal_cache[cache_key] = frozenset(keys)
        return self.legal_cache[cache_key]

    def _barred(self, machine: Any, signature: str, key: Key, board: Sequence[Sequence[int]]) -> list[int]:
        from inference.framework.virelai_gates import PLAY_GATE_ID, _canonical

        noops = machine._adapters[PLAY_GATE_ID]._noops
        action = self._action(key)
        return list(noops.get(_canonical([action, signature]), ()))

    @staticmethod
    def _action(key: Key) -> dict[str, Any]:
        name, target = key
        return {"action": name} if target is None else {"action": name, "row": int(target[0]), "col": int(target[1])}

    def choose(self, machine: Any) -> Choice | None:
        """Exactly one untried legal action on this board (deterministic, diversity-first), or None (exhausted)."""
        self.refresh(machine)
        board = self._current(machine)
        signature = self._sig(machine, board)
        tried = self.tried_edges.get(signature, set())
        open_keys = [key for key in untried(self.legal(machine), tried)
                     if not self._barred(machine, signature, key, board)]
        if not open_keys:
            return None
        key = order_untried(open_keys, self.tried_edges)[0]
        return Choice(key=key, action=self._action(key), signature=signature)

    def proof(self, machine: Any) -> dict[str, Any]:
        """Q4: every currently legal action on this exact masked board, each tried here or barred by R-8."""
        self.refresh(machine)
        board = self._current(machine)
        signature = self._sig(machine, board)
        rows = []
        for key in sorted(self.legal(machine), key=lambda k: (k[0], _target_token(k[1]))):
            rows.append({"key": [key[0], None if key[1] is None else list(key[1])],
                         "tried": list(self.tried_at.get((signature, key), [])),
                         "barred": self._barred(machine, signature, key, board)})
        return {"signature": signature, "legal": rows, "broken_record": self.broken,
                "complete": bool(rows) and all(row["tried"] or row["barred"] for row in rows)}


def for_machine(machine: Any) -> Frontier:
    frontier = getattr(machine, "_free_play_frontier", None)
    if frontier is None:
        frontier = Frontier()
        machine._free_play_frontier = frontier
    return frontier


__all__ = ["Choice", "Frontier", "component", "edge_key", "for_machine", "order_untried", "untried"]
