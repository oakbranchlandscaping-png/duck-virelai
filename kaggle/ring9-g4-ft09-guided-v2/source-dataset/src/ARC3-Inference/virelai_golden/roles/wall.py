"""ROLES · wall — what refuses the ego: the object standing where a refused press would have put it.

Canon: 02 §6.3 WALL (v1.2) — "a refused transition on a single-fingerprint worldline. A sealed
embodied ego, on a press whose bearing is already known from its own kinematics, is HELD
against this worldline — the delta the ego's kinematic law predicts does not occur, and the
worldline is the object at the predicted landing. The refusal set is built only from ego
MOVE/HELD edges and is unioned over every sealed ego, egos excluded. The worldline holds ONE
fingerprint across its coverage: a blocker that changes is not a wall." Band 1 STATIC.
Position: with GROUND, after the ego seals, before the lever hunt. R-I: a typed WALL is not a
walk-to target — the refusal that typed it is the contact; "the ground never becomes a wall".
R-M: GROUND is typed first and its members are excluded before the predicate (the fold is what
makes "never a wall" a construction rather than a measurement).

Transcription origin (R-C): virelai_v4/weave/wall_read.py @ oracle-v4 (111 lines, read whole)
— the two conjuncts (a blocking tag; ONE fingerprint), egos unioned then excluded, "a record,
never a generalisation: the key is the fingerprint, no class term"; virelai_v4/weave/
collide_tags.py:95-140 `blocking_tags`, `_landing` (the footprint translated by the known
bearing; integer, exact, no centroid). What it proved: two worldlines typed WALL on 21/21 and
20/21 records, every WALL an ex-∅, no sealed ego types WALL, the ground never a wall
(WO_WALL_01_RETURN_v1). The refusal record itself is golden's `EgoMap.transitions.refused`
(G1-01): (site, action) HELD, minus every (site, action) that ever passed — ∀, provisional.

CORRECTED FROM THE ORACLE (labeled): v4 resolved the landing from the ego's region at the
window's LAST node and the holders from the LAST cut (`_region_at_last`, `_holders(cuts)`) —
a footprint and a board from a different time than the press. Here the landing is the member's
own region at the refused press's LEFT node and the holder is the owner of each landing cell
at that same node (the wiring law: a press resolves against the frame it was made from). The
bearing is the member's ∀-agreed bearing for that action (`EgoMap.bearings`); a refusal under
an action with no agreed bearing is UNASKABLE and counted, never guessed.

Typed silence: a HELD press at a (site, action) that also passed is not a refusal — it is a
state-dependent hold (the corpus has them: ls20's A3 at home while the bar refills), reported
as the WALL+LEVER / driven-constraint question the subtree seed names. A landing off the
board is the edge of the world, not a worldline; counted. A tagged worldline holding more than
one fingerprint is reported as a changing blocker, typed elsewhere. `medium.py` (v4's
pre-R-I "the ground a mover moves through", a REACTIVE-DRIVEN sub-class under a menu closed
at six) is NOT transcribed: R-I made it GROUND, and G3-01 typed it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional, Sequence, Tuple

from virelai_golden.roles.ego_body import EgoMap, body_action_series, life_boundaries
from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.record import Record
from virelai_golden.substrate.scan import Cell
from virelai_golden.weave.provenance import cell_owners, worldline_owner_index
from virelai_golden.weave.verbs import Verb
from virelai_golden.weave.worldline import Worldline


@dataclass(frozen=True)
class Refusal:
    member: int                # the ego member held
    left: int                  # the node the press was made from
    right: int
    action: int
    bearing: Optional[Tuple[int, int]]   # the member's agreed bearing, or None (unaskable)
    landing: FrozenSet[Cell]   # predicted cells minus the member's own; empty if unaskable
    holders: Dict[int, int]    # worldline id → landing cells it stood on (off-board cells absent)


@dataclass(frozen=True)
class WallVerdict:
    wid: int
    refusals: Tuple[Refusal, ...]
    basis: str
    parallax: str


@dataclass(frozen=True)
class WallRead:
    verdicts: Dict[int, WallVerdict]
    refusals: Tuple[Refusal, ...]
    typed: str
    holds_that_passed: int     # HELD presses at a (site, action) that also passed — not refusals
    unaskable: int             # refusals under an action with no agreed bearing
    off_board: int             # landing cells outside the grid, summed over refusals
    on_ground: int             # landing cells on a GROUND member, summed over refusals
    changing_blockers: Tuple[int, ...]   # tagged worldlines holding > 1 fingerprint (not WALL)


def fingerprints(wl: Worldline) -> int:
    return len({r.fingerprint for _, r in wl.steps})


def refusals_of(wl: Worldline, m: EgoMap, window: Sequence[Cut], action_at: Sequence[Optional[int]],
                boundaries: FrozenSet[int], index) -> Tuple[List[Refusal], int]:
    """Every refused press of one ego member, resolved at the press; and the held-but-passed count."""
    by_node = {c.node: c for c in window}
    bearing = {b.action: b.bearing for b in m.bearings}
    shape = window[0].shape if window else (0, 0)
    out: List[Refusal] = []
    passed = 0
    for i, e in enumerate(wl.edges):
        left, right = wl.steps[i][0], wl.steps[i + 1][0]
        if right in boundaries:
            continue
        aid = action_at[right] if 0 <= right < len(action_at) else None
        if aid is None or e.verb is Verb.MOVE:
            continue
        region = wl.steps[i][1]
        if (region.anchor, aid) not in m.transitions.refused:
            passed += 1   # HELD here, but this (site, action) passed elsewhere: state-dependent
            continue
        b = bearing.get(aid)
        if b is None:
            out.append(Refusal(wl.id, left, right, aid, None, frozenset(), {}))
            continue
        landing = frozenset((r + b[0], c + b[1]) for r, c in region.cells) - region.cells
        owners = cell_owners(by_node[left], index)
        holders: Dict[int, int] = {}
        for cell in landing:
            if 0 <= cell[0] < shape[0] and 0 <= cell[1] < shape[1]:
                o = owners.get(cell)
                if o is not None:
                    holders[o] = holders.get(o, 0) + 1
        out.append(Refusal(wl.id, left, right, aid, b, landing, holders))
    return out, passed


def infer_walls(record: Record, window: Sequence[Cut], worldlines: Sequence[Worldline],
                maps: Dict[int, EgoMap], ego: FrozenSet[int], ground: FrozenSet[int],
                boundaries: Optional[FrozenSet[int]] = None) -> WallRead:
    if record.action_channel.startswith("BLIND"):
        return WallRead({}, (), "WALL unmeasured: action-blind record, no ego can seal", 0, 0, 0, 0, ())
    if not ego:
        return WallRead({}, (), "WALL unaskable: no EGO(BODY) sealed (R-I: ego-relative, embodied worlds only)",
                        0, 0, 0, 0, ())
    by_id = {w.id: w for w in worldlines}
    index = worldline_owner_index(worldlines)
    action_at = body_action_series(record)
    boundaries = life_boundaries(record) if boundaries is None else boundaries
    all_ref: List[Refusal] = []
    passed = 0
    for m in sorted(ego):
        if m in maps and m in by_id:
            rs, p = refusals_of(by_id[m], maps[m], window, action_at, boundaries, index)
            all_ref.extend(rs)
            passed += p
    unaskable = sum(1 for r in all_ref if r.bearing is None)
    off_board = sum(len(r.landing) - sum(r.holders.values()) for r in all_ref if r.bearing is not None)
    on_ground = sum(n for r in all_ref for w, n in r.holders.items() if w in ground)
    tagged: Dict[int, List[Refusal]] = {}
    for r in all_ref:
        for w in r.holders:
            if w in ego or w in ground:
                continue  # no ego is a wall; the ground never becomes a wall (R-I, R-M)
            tagged.setdefault(w, []).append(r)
    verdicts: Dict[int, WallVerdict] = {}
    changing: List[int] = []
    for w, rs in sorted(tagged.items()):
        n_fp = fingerprints(by_id[w])
        if n_fp != 1:
            changing.append(w)
            continue
        acts = sorted({r.action for r in rs})
        cells = sum(r.holders[w] for r in rs)
        basis = (f"stood where the ego would have landed on {len(rs)} refused press(es) under "
                 f"{', '.join(f'A{a}' for a in acts)} ({cells} landing cell(s)); held ONE fingerprint across "
                 f"all {len(by_id[w].steps)} step(s) → WALL")
        parallax = ("Band 1 STATIC by construction; not a walk-to target — the refusal is the contact (R-I); "
                    "not INERT (refusing is behaviour); WALL+LEVER only on an exogenous effect, never on the refusal")
        verdicts[w] = WallVerdict(w, tuple(rs), basis, parallax)
    typed = (f"WALL asked over {len(all_ref)} refusal(s) of {len(ego)} ego member(s): {unaskable} unaskable "
             f"(no agreed bearing), {passed} hold(s) at a (site, action) that also passed — state-dependent, "
             f"not refusals; {off_board} landing cell(s) off the board; {on_ground} on GROUND")
    return WallRead(verdicts, tuple(all_ref), typed, passed, unaskable, off_board, on_ground, tuple(changing))
