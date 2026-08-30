"""WO_WEAVE_ACTION_ON_NODE · resolve the captain's action to the ### it acted on.

A raw click is a coordinate; the roster wants the OBJECT. Because every cell has an
owner (owner-provenance, committed), a click ``(row, col)`` resolves to the ### whose
footprint contains that cell — so the roster records "acted on ###007", not a bare
coordinate. The footprint we already carry is what makes the resolution exact.

STRUCTURAL NOTES:
  * A READING over the committed owner map (`provenance.cell_owners`). It does NOT
    change threading (`edge.py`/`worldline.py`/`provenance.py` untouched).
  * Game-free, no is_background, no size shortcut, no snapping.
  * An UNOWNED click reads EMPTY — honestly a miss, never snapped to a nearest ###
    (a snap would be a lie the downstream role layer would trip over).
  * SCOPE: records WHICH ### was acted on. It does NOT say what the ### IS — no
    LEVER/REACTIVE/STATIC/archetype labelling (that is the downstream role layer).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, FrozenSet, Optional, Tuple

from virelai_v4.weave.provenance import cell_owners, worldline_owner_index

Cell = Tuple[int, int]

RESOLVED = "RESOLVED"          # target cell owned by a ###
EMPTY = "EMPTY"               # targeted OUT-OF-BOUNDS coord (in-bounds always resolves under totality)
NON_TARGETED = "NON_TARGETED"  # directional / no-coordinate action
OUT_OF_WINDOW = "OUT_OF_WINDOW"  # the pre-action node t-1 is not in the woven window (a wiring error to surface)


@dataclass(frozen=True)
class ActionResolution:
    action_id: Any
    target_cell: Optional[Cell]
    worldline_id: Optional[int]   # the ### acted on, or None
    status: str                   # RESOLVED / EMPTY / NON_TARGETED


def resolve_action(action_id: Any, target_cell: Optional[Cell],
                   cut, worldlines) -> ActionResolution:
    """Resolve a node's action to the ### it acted on, using ``cut``'s owner map.

    ``target_cell`` None (a directional / non-targeted action) → NON_TARGETED.
    A targeted cell owned by a ### → RESOLVED with that ### id. A targeted cell in
    unowned space → EMPTY (never snapped). Resolves against the given ``cut`` (the
    frame recorded with the action)."""
    if target_cell is None:
        return ActionResolution(action_id, None, None, NON_TARGETED)
    owners = cell_owners(cut, worldline_owner_index(worldlines))
    wid = owners.get((int(target_cell[0]), int(target_cell[1])))
    if wid is None:
        return ActionResolution(action_id, tuple(target_cell), None, EMPTY)
    return ActionResolution(action_id, tuple(target_cell), wid, RESOLVED)


def action_node_indices(frame_index: int) -> Tuple[int, int]:
    """The index rule (SPEC_WEAVE §5.2): a sidecar action with ``frame_index k``
    produces node ``t = k`` and was issued from the pre-action node ``t-1 = k-1``
    (the frame the captain observed). Node 0 is the spawn — no producing action."""
    return (frame_index, frame_index - 1)


def life_boundary_edges(cuts) -> FrozenSet[int]:
    """**THE RIGHT-HAND NODE OF EVERY EDGE THAT CROSSES A LIFE BOUNDARY.**

    WO-RESPAWN-DISREGARD-01. A respawn's displacement is real and **it is not evidence
    about a button**: the ego did not walk to spawn, it died. `weave/ego_read.py` reads
    each edge for a bearing and for a `(site, action)` transition; an edge in this set
    contributes to neither, while the worldline still spans it. **The continuity is the
    Director's ruling — the respawn IS the same worldline, and severing it would destroy
    the Groundhog Day principle the next campaign stands on.**

    **THE TEST IS DERIVED FROM WHAT EACH SIGNAL MEANS, NOT CHOSEN BETWEEN.** `full_reset`
    marks the frame the game RESET, so the boundary edge ARRIVES there. `GAME_OVER` marks
    the frame the life ENDED, so the boundary edge DEPARTS from there. **One edge, two
    ends** — and `virelai.py`'s own note records, verified on a real multi-life recording,
    that some cuts carry `full_reset=False`, which is why both signals must be read and
    why neither alone is enough.

    **MEASURED, BECAUSE REASONING ABOUT NODE INDICES HAS COST THIS CAMPAIGN TWICE.** Four
    candidate tests were run against a constructed pair — a death edge that must be
    disregarded and the first walk after it that must be kept — under three stampings
    (`full_reset` on the arrival node, `GAME_OVER` on the pre node, and both):

        RIGHT node is a boundary          clean · MISSES the death · clean
        is_boundary_pre(right)            MISSES · clean · KILLS a legitimate walk
        EITHER endpoint is a boundary     KILLS · clean · KILLS
        full_reset(right) OR GAME_OVER(left)      clean · clean · clean

    **`is_boundary_pre` below is NOT reusable here and that is not a defect in it.** It ORs
    both signals on ONE node because its question is *was this action issued from a
    boundary* — an action-shaped question. This one is edge-shaped, and asking the
    node-shaped predicate of an edge over-flags the first legitimate press after a
    respawn. **Two questions, two predicates, one home** — they share this module and the
    two atomic reads below, so the boundary logic has one place rather than a fifth copy.

    Returns the RIGHT node's index for each crossing edge, so a reader holding
    `worldline.steps` tests `steps[i + 1][0] in boundaries`. Absence is absence: no cuts,
    or a window with no boundary, yields the empty set and nothing is disregarded."""
    if not cuts:
        return frozenset()
    by = {c.node_index: c for c in cuts}
    out = set()
    for c in cuts:
        prev = by.get(c.node_index - 1)
        if _reset_at(c) or (prev is not None and _game_over_at(prev)):
            out.add(c.node_index)
    return frozenset(out)


def heart_boundary_edges(cuts, report, sealed, worldlines) -> FrozenSet[int]:
    """**THE RIGHT-HAND NODE OF EVERY EDGE ON WHICH A SEALED COUNTER REVERSED WHILE
    SOMETHING MOVED** — a life boundary the harness does not mark.

    WO-HEART-DISREGARD-01. `life_boundary_edges` above closes the boundary the platform
    flags. This world has another inside a life: a fuel bar drains, a heart is spent, the
    ego is returned to spawn — **and no `full_reset` and no `GAME_OVER` accompany it.**
    Constructed proof, not argument: on such an edge the predicate above does not fire, the
    teleport's displacement enters `observed` as a bearing, and `passable` takes the cell
    the ego departed from, where the subtraction in `_transitions` then makes a genuine
    refusal there unconstructible for the rest of the life.

    **A REVERSAL, NOT A MAXIMUM, AND THAT IS WHY IT COSTS NO CONSTANT.** The Director's
    words are *the bar is empty, then all of a sudden it is full again* — and *empty* and
    *full* are LEVELS, which `CouplingReport` does not carry. It carries `matrix`:
    `wid -> SIGNED count delta per press`, built as `_cc(wl, right) - _cc(wl, left)`. **A
    drain is a run of negatives and a refill is a positive**, so the same event read as a
    sign change against the press before needs no range, no threshold and no magnitude. A
    level-phrased reading would have needed a maximum, and **a range the solver does not
    have is a threshold waiting to be invented.**

    **THE CONJUNCTION IS REQUIRED AND IT IS NOT CAUTION.** The embodied canary seals
    several `COUNTER` worldlines that are small static objects clustered at one place —
    the Director reads them as a door's flash, and the counter seal is *ticks on every
    press, independent of which action*, which a door that answers every attempt satisfies.
    **So the sealed set is itself noisy**, and a reversal alone would call a flash a heart
    loss. Requiring that something was displaced on the same press means **a flashing
    object reversing while everything stands still fires nothing.**

    **WHAT THE CONJUNCTION DOES NOT BUY, STATED RATHER THAN DISCOVERED.** It cannot
    separate a heart loss from a legitimate walk that happens to coincide with a sealed
    counter's reversal — both have a displacement on the press. **That direction destroys a
    true observation**, and it is bounded only by how rare a reversal is. The narrower
    protection this predicate does give is that an UNSEALED worldline's reversal fires
    nothing at all.

    **THE JOIN IS EXACT AND IT IS BY NODE INDEX.** `build_coupling` walks
    `zip(nodes, nodes[1:])` and appends the LEFT node as `presses[j]`, building `matrix`,
    `magnitude` and `action_by_press` in the same walk — so press `j` spans
    `nodes[j] -> nodes[j+1]` and every channel is co-indexed press-for-press by
    construction. This returns the RIGHT node, `nodes[j + 1]`, which is the convention
    `life_boundary_edges` already uses and the index `_observe` already tests
    (`wl.steps[i + 1][0] in boundaries`). **`WO-RESPAWN-DISREGARD-01`'s halt was about
    exactly this class of off-by-one, so the join is read off the producer rather than
    assumed.**

    Absence is absence: no report, no sealed counter, or a window with no reversal yields
    the empty set and nothing is disregarded."""
    if report is None or not sealed or not cuts:
        return frozenset()
    nodes = [c.node_index for c in sorted(cuts, key=lambda c: c.node_index)]
    out = set()
    for wid in sealed:
        series = report.matrix.get(wid) or ()
        for j in range(1, len(series)):
            if not (series[j] > 0 and series[j - 1] < 0) or j + 1 >= len(nodes):
                continue
            if _displaced_at(worldlines, nodes[j], wid):
                out.add(nodes[j + 1])
    return frozenset(out)


def _displaced_at(worldlines, left_node: int, reverser) -> bool:
    """Did any worldline OTHER than the reversing counter move across the edge leaving
    `left_node`?

    **DISPLACEMENT, NOT SIZE, AND THE FIRST DRAFT GOT THIS WRONG.** It read the report's
    `magnitude` channel — a set-cardinality change — and the reversing counter's own refill
    satisfied it, so the conjunction was vacuous and a flashing object reversing while
    everything stood still fired anyway. **The charter's own case caught it.** A cell count
    is not a position: a body that moves without changing size registers nothing there, and
    the counter that just refilled registers the most.

    So the test is the edge's own `delta`, which is what displacement means, read off the
    worldline rather than off a channel. **The reverser is excluded by identity** — a
    counter is not evidence that the world moved something else."""
    for wl in worldlines or ():
        if wl.id == reverser:
            continue
        for i, e in enumerate(wl.edges):
            if wl.steps[i][0] == left_node and getattr(e, "delta", None):
                return True
    return False


def _reset_at(cut) -> bool:
    """The frame the game RESET — the boundary edge arrives here."""
    return bool(getattr(cut, "full_reset", False))


def _game_over_at(cut) -> bool:
    """The frame the life ENDED — the boundary edge departs from here."""
    return getattr(cut, "state", "") == "GAME_OVER"


def is_boundary_pre(cut_by_idx, node_t: int) -> bool:
    """True when the pre-action node ``t-1`` is a life boundary — a `full_reset` cut
    or a `GAME_OVER` state. The wiring flags (does not resolve) such actions
    (SPEC_WEAVE §5.2 / honest-open)."""
    cut = cut_by_idx.get(node_t - 1)
    if cut is None:
        return False
    return _reset_at(cut) or _game_over_at(cut)


def acted_on(node_t: int, action_id: Any, target_cell: Optional[Cell],
             cut_by_idx, worldlines) -> ActionResolution:
    """THE WIRING LAW (SPEC_WEAVE §5.3): resolve the action that produced node ``t``
    against ``cut[t-1]`` — the pre-click frame the captain observed, NOT the action's
    own (post-action) node ``t`` where the clicked object may already have moved. The
    woven window MUST contain ``t-1``; if it does not, return ``OUT_OF_WINDOW`` (a
    wiring error to surface, never a silent mis-resolve). Uses ABSOLUTE node_index
    lookup, never a window offset. A node with no targeted action (e.g. the spawn) is
    NON_TARGETED regardless of window."""
    if target_cell is None:
        return ActionResolution(action_id, None, None, NON_TARGETED)
    cut = cut_by_idx.get(node_t - 1)
    if cut is None:
        return ActionResolution(action_id, target_cell, None, OUT_OF_WINDOW)
    return resolve_action(action_id, target_cell, cut, worldlines)


def format_resolution(node_index: int, res: ActionResolution) -> str:
    if res.status is NON_TARGETED or res.status == NON_TARGETED:
        return f"node {node_index}: non-targeted action {res.action_id}"
    if res.status == OUT_OF_WINDOW:
        return f"node {node_index}: action {res.action_id} → t-1 out-of-window (widen window to resolve)"
    r, c = res.target_cell
    if res.status == RESOLVED:
        return f"node {node_index}: action {res.action_id} @({r},{c}) → acted on ###{res.worldline_id:03d}"
    return f"node {node_index}: action {res.action_id} @({r},{c}) → acted on EMPTY (out-of-bounds)"
