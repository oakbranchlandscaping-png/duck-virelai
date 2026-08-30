"""WO-COLLIDE-EXTRACT-01 · THE PLAN LAYER, LIFTED OUT OF THE DRIVE — VERBATIM.

**A MOVE, NOT A REFACTOR.** Every function below is byte-identical to the body it had in
`collide_drive.py` at `c61eb04`. `_reach_state` still runs ONE search and returns the
boolean beside the ordinal and the path; `_needs_plan` still has exactly three clauses;
`_next_press` still keeps `None` and `()` apart and still filters by the offer. **Any
change to what these compute would have made the extraction non-neutral, and the oracle
would have said so.**

**WHY IT LEFT.** See `collide_tags`. Seven returns recommended the split; the eighth
deferral would have been *while adding a rarity pass, a sort key and a novelty test to
the same file*.

**THIS MODULE SITS ABOVE `collide_tags`, AND THE DEPENDENCY IS REAL RATHER THAN
INCIDENTAL.** `_needs_plan`'s first re-plan trigger is *the board changed* — the
comparison against `blocking_tags`'s output that `drive_step` runs at its head. The plan
consumes what the tag layer produces, so importing `_region_at_last` downward follows the
data dependency rather than crossing it.

Stdlib plus `weave.reachable` and `weave.collide_tags` only.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Optional, Sequence, Tuple

from virelai_v4.weave.collide_tags import Bearing, Site, _region_at_last
from virelai_v4.weave.reachable import reach
# WO-ARRIVE-01 · on its own line, and the committed one above is byte-identical.
# `test_ego_set` pins that line as the evidence the search is untouched — a fence that
# rejects a widening is working, so the predicate arrives beside it rather than inside it.
from virelai_v4.weave.reachable import overlaps
# WO-EGO-FRESH-01 · the settled frame's regions. On its own line, beside the two above,
# for the reason WO-ARRIVE-01 recorded: a fence that rejects a widening is working.
from virelai_v4.capture.ledger_build import regions_at


def _walk(worldline) -> Tuple[Bearing, ...]:
    """This worldline's per-step ANCHOR DISPLACEMENT across its trail."""
    st = worldline.steps
    return tuple((st[i + 1][1].anchor[0] - st[i][1].anchor[0],
                  st[i + 1][1].anchor[1] - st[i][1].anchor[1])
                 for i in range(len(st) - 1))


def _co_moves(a, b) -> bool:
    """Do these two worldlines move as ONE BODY across the window?

    **THE LICENCE IS MEASURED CO-MOTION, AND IT IS NOT "BOTH ARE SEALED EGO."**
    `RULING_EGO_WORLDLINE_v1` §4 says the ego is a SET; it does not say the set is one
    body, and unioning cell sets asserts one. The condition is verifiable from
    `Worldline.steps` alone: the same node range, and the same displacement at every step.

    **IT IS DISPLACEMENT, NOT ANCHOR — `WO_EGO_BODY_01 §1` said anchor and the record says
    otherwise.** Measured on the graded roster: the two ego worldlines have identical node
    ranges and identical per-step displacements, and a CONSTANT anchor offset between them
    — never an identical anchor. Two parts of one avatar sit in different places and move
    together; requiring equal anchors would have excluded both members and silently left
    the body a single worldline.

    Fewer than two steps cannot demonstrate co-motion, and that is an honest absence
    rather than a threshold — there is no displacement to compare."""
    na = tuple(n for n, _r in a.steps)
    nb = tuple(n for n, _r in b.steps)
    if na != nb or len(na) < 2:
        return False
    return _walk(a) == _walk(b)


def body_cells(by_id, ego: int, egos: Sequence[int] = ()):
    """`(cells, excluded_ids)` — the ONE producer of the body's footprint.

    The union of the last-node cells of every member of `egos` that co-moves with the
    elected worldline, which is always itself a member. A sealed ego that does not move in
    lockstep is NOT part of this body and is returned in `excluded_ids` so the exclusion is
    reported rather than silent.

    **NO FALLBACK BRANCH, BY CONSTRUCTION.** With an empty or single `egos` the loop never
    unions anything and the result is the elected footprint — the union of one set is that
    set. There is no special case to get wrong."""
    base = by_id.get(ego)
    if base is None:
        return frozenset(), ()
    cells = frozenset(_region_at_last(base).cells)
    excluded = []
    for wid in egos:
        other = by_id.get(wid)
        if wid == ego or other is None:
            continue
        if _co_moves(base, other):
            cells = cells | frozenset(_region_at_last(other).cells)
        else:
            excluded.append(wid)
    return cells, tuple(excluded)


def _owners(worldlines) -> Dict[Any, Any]:
    """`{fingerprint: the worldline that IS this object}` — **THE ONE PRODUCER OF OBJECT
    IDENTITY, AND BOTH THE CHECK-OFF AND THE SELECTION ASK IT.**

    A worldline's trail holds one fingerprint per node and every one of them is a moment of
    the SAME object, so each maps here to the worldline itself. That is the whole answer to
    *which thing is this queue entry* — asked of the record, not of an anchor.

    **WO-SEEK-THE-SMALLEST-01 · IT REPLACES A COORDINATE COMPARISON WITH AN IDENTITY.**
    `collide_drive._standing_at` asked whether some worldline's CURRENT footprint anchors
    at the entry's FIRST-APPEARANCE site. For a still object the two coincide; for an object
    that has moved or deformed they never do again, and **nothing in a life makes a dead
    anchor current** — so every entry but the newest was unresolvable for the rest of the
    run, silently. Measured live: the drive offered list position eight, passing over 2
    through 7. This map has an entry for every moment of every object the weave bound.

    **A FINGERPRINT TWO WORLDLINES SHARE RESOLVES TO THE LATER ONE, AND THAT IS STATED
    RATHER THAN GUARDED.** It can only happen where two objects held the identical cell set
    at some node, which the partition forbids at any ONE node; across nodes it is a rebirth,
    and `WO-RETURN-01` already rules those into one worldline. A tie-break here would be a
    second identity rule competing with that one.

    **AN OBJECT NO WORLDLINE OWNS IS ABSENT FROM THIS MAP, AND THAT IS ABSENCE.** Both
    callers skip such an entry rather than inventing a holder for it."""
    owners: Dict[Any, Any] = {}
    for w in worldlines:
        for _node, region in w.steps:
            owners[region.fingerprint] = w
    return owners


def owner_ids(worldlines) -> Dict[Any, int]:
    """`{fingerprint: worldline id}` — `_owners` for the caller that steers rather than
    measures.

    The drive steps toward a WORLDLINE: `_aim`, `arrived` and `_reach_state` all read a
    region off one. The selection therefore needs the id and nothing else, and taking only
    the id here keeps the whole worldline out of the drive's hands."""
    return {fp: w.id for fp, w in _owners(worldlines).items()}


def _last_seen(worldlines) -> Dict[Any, Any]:
    """`{fingerprint: the cells that object last held}` — **WHERE IT WAS, NOT WHERE IT
    WAS MINTED.**

    **THIS IS THE LOOKUP EVERY ARRIVAL TEST SO FAR HAS DONE WITHOUT, AND THE REASON THEY
    FAILED.** A queue entry carries `(class integer, cells)` frozen at the moment the
    fingerprint was minted, and an anchor from its FIRST appearance. Neither tracks where
    the object is now. **A covered object is absent from the settled frame** — the body is
    standing on it, so nothing of it is visible to be found — and its worldline is the only
    record that says where it was when it was last seen. `WO_ARRIVAL_AUDIT_01` measured the
    alternative: a remembered fingerprint fired **0 times** on the record the Director
    named and 131 times against one stale oversized key on another. The worldline's last
    step is neither stale nor oversized: it is one node old at most and it is the object.

    **EVERY MOMENT OF A DEFORMING OBJECT POINTS AT THE SAME PLACE.** A worldline's trail
    holds a fingerprint per node; each is its own queue entry, and each maps here to the
    ONE cell set that worldline last held. So an object that deformed under contact ticks
    off every moment of itself at once rather than one per pass — which is the *forty
    entries over fifteen sites* `WO_DECLARE_INTENT_01` §0.1 measured, answered without a
    ruling about keying.

    **BUILT ON `_owners`, WHICH IS WHERE THE IDENTITY RULE LIVES** — one producer, two
    readings. This one takes the cells; `owner_ids` takes the id."""
    return {fp: _region_at_last(w).cells for fp, w in _owners(worldlines).items()}



def fresh_body(by_id, ego: int, egos: Sequence[int], log):
    """`(cells, anchor)` READ FROM THE SETTLED CURRENT FRAME, or `None` — not located.

    **THE BODY'S POSITION IS THE ONE PROPOSITION THE DRIVE HELD WITHOUT EVIDENCE.**
    `body_cells` above reads `_region_at_last`, which comes from a window rebuilt on a
    cadence, so on most presses it answers where the body WAS. `RULING_EGO_POSITION_v1`:
    *a cached anchor is not weak evidence of the current position, it is NO evidence of
    it.* Graded on one life: the body covered three queued objects on seventeen presses,
    fifty-one pairs were available, and the record took one.

    **LOCATION BY RIGID CONGRUENCE, AND RIGIDITY IS ALREADY MEASURED.** `_co_moves` above
    licenses the body on identical per-step displacements and a CONSTANT anchor offset
    between members. That constancy is the certificate: each member's `shape` is sought
    among the settled frame's regions, and **every member must be found, at its known
    offset, or nothing is.** One congruent region is a common coincidence; a multi-part
    rigid assembly at a fixed internal offset is not.

    **IT LOCATES; IT DOES NOT IDENTIFY.** `regions_at`'s own docstring: *"answers a
    question about PRESENCE, never about identity: identity is a path through a window and
    cannot be had at this price."* This returns a PLACE. It never asserts that the located
    regions ARE these worldlines, and a caller that reads it as identity has misread it.

    **ABSENCE AND AMBIGUITY ARE THE SAME ANSWER, AND THERE IS NO TIE-BREAK.** Zero matches
    — deformed, occluded, merged with a neighbour, ended — and two or more both answer
    `None`. Nearest-to-last-known is a distance metric this build bans by name and is a
    prediction besides. **No prior generation abstains here**: `nav_atlas
    .find_ego_anchor_position` takes `positions[0]`, which its own docstring concedes is
    the top-left only *"for a contiguous cluster"*. Abstention is this rung's invention and
    it is declared. Measured over the corpus: ambiguity never occurred, in 3734 of 3734.

    **THE ANCHOR IS THE ELECTED MEMBER'S, NEVER THE UNION'S** — `WO_EGO_BODY_01` §3's R2,
    unchanged on that axis. `reach` uses cells and anchor COUPLED: it translates the cells
    by its search offset and builds the refusal key as `ego_anchor + offset`. Only the
    MOMENT the anchor describes changes here, never which member it comes from.

    **THE QUANTIFIER, STATED.** Requiring every member is a ∀, and it is lawful because the
    claim is provisional and per-frame: it is re-asked next press and dies without ceremony
    on one missing member. No permanent claim here takes a ∀.

    An absent log, an absent ego, or an empty log is an absent PREMISE and answers `None` —
    absence rendered as absence, and the caller then reads the cached body and says so."""
    base = by_id.get(ego)
    if base is None or log is None or not len(log):
        return None
    er = _region_at_last(base)
    members = [ego] + [w for w in egos
                       if w != ego and w in by_id and _co_moves(base, by_id[w])]
    want, offs = {}, {}
    for m in members:
        rm = _region_at_last(by_id[m])
        want[m] = rm.shape
        offs[m] = (rm.anchor[0] - er.anchor[0], rm.anchor[1] - er.anchor[1])
    if any(want[m] is None for m in members):
        return None
    seen = {}
    for g in regions_at(log, log.records[-1].node_index):
        seen.setdefault(g.shape, []).append(g)
    found = []
    for g in seen.get(want[ego], ()):
        parts = [g]
        for m in members:
            if m == ego:
                continue
            dr, dc = offs[m]
            site = (g.anchor[0] + dr, g.anchor[1] + dc)
            h = next((h for h in seen.get(want[m], ()) if h.anchor == site), None)
            if h is None:
                parts = None
                break
            parts.append(h)
        if parts is not None:
            found.append(parts)
    if len(found) != 1:
        return None
    cells = frozenset()
    for part in found[0]:
        cells = cells | frozenset(part.cells)
    return cells, found[0][0].anchor


def standing_on(by_id, worldlines, ego: int, egos: Sequence[int],
                candidates: Sequence[Any], body=None) -> FrozenSet[Any]:
    """**EVERY QUEUED OBJECT THE BODY IS STANDING ON. PLURAL, AND ALL OF THEM AT ONCE.**

    The predicate is `reachable.overlaps` — integer cells, integer offset, set membership,
    no distance and nothing that could be tuned — asked of the same two sets
    `_reach_state` hands `reach` on the line below: the body from `body_cells`, and the
    object's cells from its worldline. **Nothing new is computed and nothing is searched.**
    `reach` answers this same question first and then walks a lattice; this asks only the
    question, of the whole queue instead of one already-selected target.

    **THE OFFSET IS `(0, 0)` BECAUSE BOTH SETS ARE ALREADY IN THE GRID'S FRAME.** `reach`
    translates by the offset it has accumulated while searching; there is no search here
    and so no translation. It is not a bearing and it is not a default that could be tuned
    into one — it is the absence of one.

    **THE BODY IS THE SET, NOT THE ELECTED TONE.** `RULING_EGO_WORLDLINE_v1` §4, through
    `body_cells`, which is the ONE producer of the body's footprint and unions only the
    members `_co_moves` licenses. A cluster member lying across the seam of a two-tone body
    is covered by the union and by neither tone alone.

    **AN OBJECT NO WORLDLINE OWNS IS NOT CHECKED OFF.** Its fingerprint is absent from
    `_last_seen` and it is skipped — absence rendered as absence. Marking it would mean
    reading `key[1]`, the mint-frozen cells, which is exactly the stale read this function
    exists to replace.

    **THE ONE UNTESTED CASE, NAMED RATHER THAN DEFENDED AGAINST — WO-ARRIVE-01 §5.**
    An object that MOVED after the node it was last seen at could be marked reached while
    the body stands where it used to be. No threshold guards it; a tolerance would cost
    more than it buys.

    **AND THE EXCLUSION THE CHARTER OFFERED IS VACUOUS, WHICH IS WHY IT IS NOT BUILT.**
    §5 named one: *the object being present ELSEWHERE in the same fresh frame.* It can
    discriminate nothing. `provenance.cell_owners` RAISES on a cell owned twice, so the
    cuts are a disjoint partition and **two worldlines can never share a cell at one node**
    — a body therefore cannot overlap an object that is PRESENT on that frame, at all.
    Every mark this function makes is already an object absent from the settled frame.
    Measured over the corpus: **2925 marked pairs, of which 0 have their object present at
    that node.** An exclusion that removes nothing is not a cheap guard; it is a second
    consumer of the current frame bought for no discrimination.

    **SO THE RESIDUAL RISK IS THE IDENTITY QUESTION AND NOTHING ELSE.** An object absent
    here is absent because the body covers it, or because it left and its worldline did not
    follow it. The second is `WO_SWEEP_01`'s confirmed rebirth — a buried object returning
    under a new id — which `WO-RETURN-01` rejoins and does not close. **That is
    architecture, above the drive, and it is CE's.**"""
    # WO-EGO-FRESH-01 · **THE BODY IS HANDED IN WHEN THE FRAME COULD ANSWER FOR IT.**
    # `drive_step` produces it once per press from `fresh_body` and hands it to its
    # readers; `None` means NOT LOCATED and the cached footprint is read instead, which is
    # the ruling's §5 fallback and is not a silent one — the caller renders it.
    if body is None:
        body, _excluded = body_cells(by_id, ego, egos)
    if not body:
        return frozenset()
    seen = _last_seen(worldlines)
    return frozenset(t.key for t in candidates
                     if t.key in seen and overlaps(body, (0, 0), seen[t.key]))


def walked_out(context) -> bool:
    """Did a NON-EMPTY plan reach zero during this pursuit — a route WALKED to its end?

    **THE FACT IS RECORDED AT THE POP, AND THAT IS THE WHOLE POINT.**
    `WO_BUDGET_MINE_00_RETURN` Q1 traced `collide_drive_path` end to end and found the
    distinction visible nowhere: `_needs_plan` reads the exhausted plan and the very next
    statement overwrites it, so *the route ended* and *there was never a route* arrive at
    that line as the same empty tuple. `WO_TWO_RESULTS_01 §2.3` chartered recording it
    there, before the overwrite — but there it still needs a guard to tell the two apart,
    and a guard can be got wrong.

    **AT THE POP THEY CANNOT BE CONFUSED: a pop cannot happen on an empty plan.** The
    only line that can set this fact is the one that consumes the last press of a plan
    that had presses. An empty plan re-planning to empty never reaches it, and neither
    does a plan whose next press the platform did not offer — `_next_press` returns
    before the pop. The distinction is STRUCTURAL rather than tested.

    **IT IS NOT A COUNT AND IT IS NOT A VERDICT.** It says only that the ego finished
    walking a route it had. What that licenses is the drive's to decide, and only in
    combination with a search that still refuses — which is `WO-NO-PREDICTION-01`'s line:
    before an attempt, no-route-found is a PREDICTION; after a route has been walked to
    its end, it is a MEASUREMENT.

    `getattr` rather than a bare read, because a caller may hand this a context object
    that predates the field — an absent field is *no route walked*, which is the honest
    answer and not an error."""
    return bool(getattr(context, "collide_drive_walked_out", False))


def _unreachable(by_id, ego: int, target: int, bmap, cuts, refused=frozenset(),
                 egos: Sequence[int] = ()) -> bool:
    """Can no combination of the observed bearings put the ego's footprint on this target?

    **IT RENDERS NO VERDICT ANY MORE — WO-NAV-CLEANUP-01.** `WO-NO-PREDICTION-01` deleted
    the gate that retired a target on this answer, on the Director's ruling that *trying to
    predict what we can reach prevents us from getting there*. Its only caller is now
    `drive_absence`, which uses it to EXPLAIN a frame that emitted nothing. The paragraph
    below described the deleted design in the present tense and is kept as the record of
    what it was.

    **[HISTORICAL] THE FIRST VERDICT OF UNREACHABILITY IN THIS REPOSITORY DERIVED RATHER
    THAN COUNTED.**
    Every other one is a press tally — `plan.py`'s 5, `tier3_nav`'s 3, `collide_sweep`'s 12
    and this module's own 12 — and `collide_sweep.py:183` writes the word *unreachable* in
    a comment for a conclusion drawn purely from a budget expiring.

    Returns `False`, not `True`, when there is nothing to judge on — no cuts, a worldline
    that left the window. **An absent premise is not a refusal**, and answering `True` here
    would retire a target on the strength of a missing grid shape."""
    e, t = by_id.get(ego), by_id.get(target)
    if e is None or t is None or not cuts:
        return False
    return _reach_state(by_id, ego, target, bmap, cuts, refused, egos)[0]


def _reach_state(by_id, ego: int, target: int, bmap, cuts, refused=frozenset(),
                 egos: Sequence[int] = ()):
    """`(unreachable, presses-remaining, path)` from ONE search.

    **WO-NAV-CLEANUP-01 · this line named two values and the function returns three.**
    `WO-HOLD-THE-PATH-01` added the path, recorded it in the paragraphs below, and left
    the headline naming what it used to return — so a reader taking the first line at its
    word unpacks two.

    **The ordinal is kept, not computed.** `reach` was already called here every frame
    and its whole path was collapsed by `is None`; this returns the same boolean beside
    the length that was being discarded, so no second search runs and no call is added.

    `()` — already touching — has length 0 and is NOT `None`. The caller keeps testing
    the boolean, exactly as `reachable`s own docstring insists. An absent premise yields
    `(False, None, None)`: not a refusal, no ordinal to report, and no plan to hold.

    **WO-HOLD-THE-PATH-01 · AND NOW THE PATH ITSELF, WHICH WAS BEING DISCARDED ON THIS
    FUNCTION'S LAST LINE.** The paragraph above records rescuing the ORDINAL from the same
    call and left the sequence behind — the seventeenth instance of this campaign's
    recurring defect, and the only one this chamber introduced itself. `reach` returns the
    action sequence that puts the ego's footprint on the target: blocker-aware,
    lattice-correct, and avoiding every refused transition. The drive then re-derived a
    greedy step from the raw signed gap, frame after frame, with no memory of the last one.

    **THE ORDINAL IS STILL `len(path)` AND IS STILL METRIC-FREE.** Nothing is computed from
    the sequence here; it is returned beside the two values that were already returned, and
    no second search runs.

    **`refused` DEFAULTS TO EMPTY AND IS THREADED, NOT DERIVED HERE** — WO-BLOCKED-RECORD-01.
    The record belongs to the ego's own `EgoMap`; re-deriving it at this seam would make a
    second producer of the same fact, which is how the account and the act drift. The
    ordinal it returns is still `len(path)` and is still metric-free; a search that avoids
    refused transitions returns a LONGER path when it must route around one, and that is
    the honest number of presses remaining rather than the number a wall would have
    granted."""
    e, t = by_id.get(ego), by_id.get(target)
    if e is None or t is None or not cuts:
        return False, None, None
    er, tr = _region_at_last(e), _region_at_last(t)
    # WO-EGO-BODY-01 · **THE BODY'S CELLS, AND DELIBERATELY THE ELECTED TONE'S ANCHOR.**
    # `reach` uses these two for entirely separate things — read at `reachable.py`: the
    # cells go to `overlaps`/`within`, always translated by the accumulated offset, while
    # the anchor is used at exactly one line, `site = (ego_anchor[0] + dr, ...)`, to build
    # the REFUSAL LOOKUP KEY.
    #
    # `Transitions` is built per worldline in `ego_read._transitions`, keyed on the site
    # each press was made FROM — the elected tone's anchor frame. Handing `reach` the
    # union's anchor would shift every site it computes out of that frame, and every
    # refusal lookup would silently miss: the ego would re-press known walls and
    # WO-OBSTRUCTION-01 would be undone. **That is `WO_EGO_BODY_01 §3`'s R2, and the
    # answer is that the anchor must NOT move.** The footprint is what was wrong.
    body, _excluded = body_cells(by_id, ego, egos)
    path = reach(body, er.anchor, tr.cells, bmap, cuts[-1].grid_shape, refused)
    return (path is None), (None if path is None else len(path)), path


def _needs_plan(context, site: Optional[Site], board_changed: bool) -> bool:
    """THE THREE RE-PLAN TRIGGERS, AND THERE ARE NO OTHERS — WO-HOLD-THE-PATH-01 §2.

      * **the board changed** — `blocking_tags` differs from the set the standing verdicts
        were formed under. Already computed at `drive_step`'s head, already voiding the
        unreachable set: this is a SECOND CONSUMER OF AN EXISTING SIGNAL, not a new one.
      * **the target changed** — the plan was computed for another place.
      * **the path is exhausted** — including the frame a pursuit begins, when there is
        no plan yet, and every frame `reach` refuses (an empty plan re-plans to empty).

    **NO STEP COUNT, NO STALENESS TIMER, NO PER-FRAME VALIDITY CHECK.** A fourth clause
    would be a tuned parameter, and this build has paid for every one it reached for.

    THE GAP, STATED RATHER THAN DISCOVERED: a board change that does not alter the
    blocking fingerprints — a target that moves without being a blocker — leaves the plan
    stale. It then fails to arrive, exhausts, and re-plans on the third trigger. **One
    wasted pursuit, bounded by the budget, and no timer is introduced to pre-empt it.**"""
    return (board_changed
            or site != context.collide_drive_path_for
            or not context.collide_drive_path)


def _next_press(context, path, board_changed: bool,
                offered: Sequence[Any]) -> Optional[Tuple[Any, Bearing]]:
    """One action off the held plan, re-planned first if any trigger fired.

    **`None` FROM `reach` AND `()` FROM `reach` ARE NOT CONFLATED.** `None` is *no
    combination lands this footprint*; `()` is *already touching*. Both yield an empty
    held plan and both fall through to the fallback — but they arrive there by different
    doors, and `WO_LATTICE_MINE_00_RETURN` §7 found `cycle_probe.py:723` collapsing exactly
    these two with `if path is None or len(path) == 0`. The distinction is preserved at the
    line that stores, not re-derived here.

    **THE OFFERED FILTER IS LOAD-BEARING AND SURVIVES.** A plan whose next action the
    platform did not offer this frame is NOT consumed and NOT discarded: the frame falls
    back, the plan waits. Emitting an unoffered action would be a regression the stepper's
    own filter has always prevented."""
    site = context.collide_drive_target_site
    if _needs_plan(context, site, board_changed):
        context.collide_drive_path = () if path is None else tuple(path)
        context.collide_drive_path_for = site
    held = context.collide_drive_path
    if not held:
        return None
    # WO-PAIR-AND-BODY-01 · THE BEARING COMES FROM THE PLAN. `reach` now returns the
    # `(action, bearing)` pairs it expanded, so the vector the note prints is the vector
    # the search computed the offset with. `_bearing_of` re-read the LOWEST bearing from
    # the map and RETIRED with this line: it was right whenever an action had one bearing
    # and wrong exactly when the ∃ map held more than one — which is what
    # `WO_EGO_OBSERVED_01` built on purpose. **No completion is possible now by
    # construction**: a bearing that is not in the plan cannot be reported.
    action, bearing = held[0]
    if action not in offered:
        return None
    context.collide_drive_path = held[1:]
    # WO-OUT-OF-REACH-01 · **THE ROUTE ENDED, RECORDED AT THE ONLY LINE THAT KNOWS IT.**
    # `held` was non-empty three lines up or we returned; if what remains is empty, this
    # press was a plan's LAST. See `walked_out` for why the pop and not `_needs_plan`.
    if not context.collide_drive_path:
        context.collide_drive_walked_out = True
    return action, bearing


__all__ = ["_needs_plan", "_next_press", "_reach_state", "_unreachable",
           "fresh_body", "owner_ids", "standing_on", "walked_out"]
