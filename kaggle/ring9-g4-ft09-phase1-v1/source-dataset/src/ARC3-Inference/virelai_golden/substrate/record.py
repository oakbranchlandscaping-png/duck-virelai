"""SUBSTRATE · record — the lossless given, whole game, segment-flagged.

Ladder step 5 (record). Canon: 03 §2 the Record — the only persistent thing; R-H — the record
accumulates across lives and carries across levels, never wiped inside a game.

Transcription origin (R-C): virelai_v4/capture/frame_record.py @ oracle-v4 (211 lines, read
whole) — `CaptureRecord` (the frozen per-node given: all layers, state, available_actions,
full_reset, levels_completed, win_levels, guid, game_id) and `FrameRecordLog` (append-only,
monotonic node_index). What it proved: byte-equal `reconstruct` of every delivered layer on
every canary since WO-CC-S1; the record derives nothing.

Carried from origin as ONE field, `action`: v4's `edge` (action id) and `acted_cell` (the
(row, col) a click landed on) together — `(action_id, cell | None)`, or None when the record
cannot see it. A harness recording is action-blind (every line carries the placeholder
`{"id": 0, "data": {}}`; F-0002 closed), so its Nodes carry None and the Record says
`BLIND(n)`. A golden record (G0-06, `adapter.play`) carries the action verbatim from the
emitter and the Record says `LIVE(n)`. Reader at this rung: `render_record_header` (the
per-button count); from Rung 1: the ego read. NOT transcribed: `site`/`cls` (Store-A
lineage), `layered_hash` (its only reader was a diagnostic).

NEW here (labeled, cited): the segment flags. v4 restarted its capture at a level boundary
(measured: run 2's DELIVERY ROSTER counted 133 of 166 nodes — the 33 before the level-up were
discarded). R-H forbids that. `life` and `opens_life` / `opens_level` are derived from the given
fields `state` and `levels_completed` by the two rules stated on them, and from nothing else.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

from virelai_golden.substrate.grid import Grid, as_grid

Layers = Tuple[Tuple[Tuple[int, ...], ...], ...]  # layers → rows → cells; lossless, hashable
Action = Tuple[int, Optional[Tuple[int, int]]]    # (action id, (row, col) for a click else None)

NOT_FINISHED = "NOT_FINISHED"  # the platform's own state string; anything else ends a life


def freeze_layers(frame_layers: Sequence[Sequence[Sequence[int]]]) -> Layers:
    """Deep-freeze a delivery's layer stack. Lossless: every layer, every cell, as ints."""
    return tuple(tuple(tuple(int(c) for c in row) for row in layer) for layer in frame_layers)


@dataclass(frozen=True)
class Node:
    """One turn's given, verbatim, plus its place in the game's segments.

    Given (from the platform, unchanged): index, layers, state, levels_completed, win_levels,
    available_actions, full_reset, guid, game_id.
    Derived (rules in `Record.build`): life, opens_life, opens_level.
    """

    index: int
    layers: Layers
    state: str
    levels_completed: int
    win_levels: int
    available_actions: Tuple[int, ...]
    full_reset: bool
    guid: str
    game_id: str
    action: Optional[Action]  # the press that PRODUCED this node; None = not in the record
    life: int            # 1-based; increments on the node after a life-ending state
    opens_life: bool     # first node of a life (index 0, or follows a non-NOT_FINISHED node)
    opens_level: bool    # levels_completed rose against the previous node

    @property
    def layer_count(self) -> int:
        return len(self.layers)

    @property
    def settled(self) -> Grid:
        """The settled grid of this delivery — the last layer (G1, grid.settled)."""
        return as_grid(self.layers[-1])

    @property
    def ends_life(self) -> bool:
        """The platform said the life is over on this node (GAME_OVER, WIN, …)."""
        return self.state != NOT_FINISHED


@dataclass(frozen=True)
class Record:
    """The whole game, in order. Never truncated at a life or a level (R-H).

    `origin` names what node 0 is. A harness recording's first line is not the game's initial
    frame (F-0002: consistent with the frame after the first press; decided by G0-06's live
    record, which writes the reset frame itself). `action_channel` states, as a positive claim,
    whether the record can see what was pressed.
    """

    game_id: str
    nodes: Tuple[Node, ...]
    origin: str
    action_channel: str
    source: str

    def __len__(self) -> int:
        return len(self.nodes)

    @property
    def lives(self) -> int:
        return self.nodes[-1].life if self.nodes else 0

    @property
    def deaths(self) -> Tuple[int, ...]:
        return tuple(n.index for n in self.nodes if n.ends_life)

    @property
    def level_ups(self) -> Tuple[int, ...]:
        return tuple(n.index for n in self.nodes if n.opens_level)

    @property
    def multi_grid(self) -> Tuple[int, ...]:
        return tuple(n.index for n in self.nodes if n.layer_count > 1)


@dataclass(frozen=True)
class Given:
    """The platform's fields for one turn, before segmenting. What a loader hands `build`."""

    layers: Layers
    state: str
    levels_completed: int
    win_levels: int
    available_actions: Tuple[int, ...]
    full_reset: bool
    guid: str
    game_id: str
    action: Optional[Action] = None


def build(givens: Sequence[Given], *, origin: str, action_channel: str, source: str) -> Record:
    """Segment a sequence of givens into a Record. Two rules, nothing else:

    life rule   — node k opens a new life iff k == 0 or node k−1's state was not NOT_FINISHED.
    level rule  — node k opens a level iff its levels_completed exceeds node k−1's.
    Both read only the given. No size, position, class or content enters.
    """
    if not givens:
        raise ValueError("a Record needs at least one node; an empty recording is an absence")
    nodes = []
    life = 0
    prev = None
    for k, g in enumerate(givens):
        opens_life = prev is None or prev.state != NOT_FINISHED
        if opens_life:
            life += 1
        opens_level = prev is not None and g.levels_completed > prev.levels_completed
        nodes.append(Node(
            index=k, layers=g.layers, state=g.state, levels_completed=g.levels_completed,
            win_levels=g.win_levels, available_actions=g.available_actions,
            full_reset=g.full_reset, guid=g.guid, game_id=g.game_id, action=g.action,
            life=life, opens_life=opens_life, opens_level=opens_level,
        ))
        prev = g
    return Record(
        game_id=givens[0].game_id, nodes=tuple(nodes), origin=origin,
        action_channel=action_channel, source=source,
    )
