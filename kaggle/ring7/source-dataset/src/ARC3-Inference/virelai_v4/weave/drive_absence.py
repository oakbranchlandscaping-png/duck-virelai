"""WO-GROUND-01 · `drive_absence`, EXTRACTED — the last render inside the decision module.

**A MOVE, NOT A REWRITE. THE BODY IS BYTE-IDENTICAL** to what stood at
`collide_drive.py:1504-1607` at anchor `0f46b56`, and `test_absence_truth.py`'s pin
proves it rather than this sentence. No predicate, no threshold, no sentence and no
ordering changed; only the module the function lives in.

**WHY IT MOVED, AND WHY NOW.** `collide_drive.py` is the decision module and this is a
RENDERER — it takes no decision and its own docstring says so. `WO_GROUND_MINE_00 §9.6`
and every return since has carried *the owed `drive_absence` extraction, 48 lines, the
last render inside the decision module* as an open item. `WO-GROUND-01` added a second
render to that module (the ground block, which went to `ground_read.py` rather than
here), so the file crossed its gate and the ratchet came due. **This is the compensating
extraction, and it is net-BETTER rather than net-zero.**

**THE IMPORT RUNS ONE WAY AND THERE IS NO CYCLE.** This module imports eleven names from
`collide_drive`; `collide_drive` imports NOTHING from here and does not re-export the
name. A bottom-of-module re-export would have kept the old import path working and would
have been a genuine cycle hazard — importing this module first would find `collide_drive`
half-initialised. **The import path changed instead, visibly, at every call site.**

Pure rendering. Recomputes from the same helpers the decision used, so the account and
the act cannot drift — the property the body's own docstring names and the reason every
helper below is imported rather than reimplemented.
"""

from __future__ import annotations

from typing import Any, Sequence, Tuple

from virelai_v4.weave.collide_drive import (_aim, _axis_order, _boundaries, _closers,
                                            _map_str, _next_target, _offered_cause,
                                            _unmeasured_str, _unreachable, UNTRIED,
                                            bearing_map, coverage_state,
                                            driving_worldline)
from virelai_v4.weave.ego_read import action_bearings
from virelai_v4.weave.role_read import verdict_egos

__all__ = ["drive_absence"]


def _gap_str(by_id, ego: int, target: int) -> str:
    """The gap the drive was closing, from the same `_aim` the decision used, beside the
    two anchors it is the difference of.

    **WO-ARRIVE-01 · MOVED HERE FROM `collide_drive`, BODY UNCHANGED.** Its only caller is
    this module's absence note; it renders a string and reads no belief, and the drive was
    carrying it while this rung added to the drive. `WO-GROUND-01` set the precedent when
    `drive_absence` itself left: **the import path changes visibly at the call site and
    nothing is re-exported**, so `collide_drive` still imports nothing from here and there
    is no cycle. This pays the rung's ratchet — eleven lines out against five in.

    **THE MISMATCH `WO_EGO_OBSERVED_01_RETURN` §7.2 FOUND IS CLOSED HERE, AND BY DELETION
    RATHER THAN BY REPAIR.** That note printed `(+8,+16)` between anchors `(26,3)` and
    `(34,20)` — a difference of `(+8,+17)` — because the gap came from `_centroid` and the
    anchors came from `RegionClay.anchor`, two quantities separated by the half-extent
    difference of the two footprints. The label was not wrong; **the field beside it was
    the wrong number.** With one quantity there is nothing left to disagree, and no
    rounding is applied because there is nothing fractional to round."""
    e, t = by_id.get(ego), by_id.get(target)
    if e is None or t is None:
        return "gap: unreadable — a worldline left the window"
    ea, ta = _aim(e), _aim(t)
    if ea is None or ta is None:
        return "gap: unreadable — an empty footprint"
    d = (ta[0] - ea[0], ta[1] - ea[1])
    axes = "row then col" if _axis_order(d) == [0, 1] else "col then row"
    return (f"gap (dr,dc)=({d[0]:+d},{d[1]:+d}) "
            f"from anchor {ea} to {ta}; axes tried {axes}")


def drive_absence(context, node_actions, worldlines, verdicts,
                  candidates: Sequence[int], cuts: Sequence[Any] = ()) -> str:
    """WHY no step was produced — **the facts it refused on, not the conclusion.**

    The line that stood here said *"no MEASURED bearing closes the gap"* and withheld its
    evidence: it named neither the bearings the ego had nor the gap being closed, and TWO
    different causes print it identically — a partial map (the ego seal needs only two
    distinguishable bearings, so a two-entry map types an `EGO` and cannot steer in four
    directions) and a diagonal gap whose perpendicular fallback also found nothing. **Those
    need different rungs and the log could not tell them apart.**

    Every other seal in this build renders absence with its reason — `INERT`'s certificate
    names what was tried and what is missing, the marginals abstain at `-1.0` rather than
    `0.0`, the medium's basis names its mover. This one rendered a verdict without a
    record.

    **NO DECISION IS TAKEN HERE.** It recomputes from the same helpers the decision used —
    `_centroid`, `_axis_order`, `bearing_map` — so the account and the act cannot drift.

    **THE FOURTH CAUSE — WO-REACHABLE-01 — IS STATED FIRST**, because the RED showed the
    third one lying about it: an off-lattice target whose map held bearings of the right
    SIGN printed *THE MAP HAS AN ANSWER AND IT WAS NOT AVAILABLE*, and the map had no
    answer that ever lands. Unreachability is the stronger claim and it preempts.

    `cuts` IS OPTIONAL AND ITS ABSENCE IS RENDERED AS ABSENCE. The reachability read needs
    the grid shape, which lives on `NodeCut`; the production caller
    (`coverage_sweep.nav_drive_step`) does not pass `cuts`, so the fourth cause is
    authored and cannot reach the live log until one argument is added there — a line
    outside this rung's fence. **The BEHAVIOUR lands regardless**: `drive_step` has `cuts`
    and retires an unreachable target before a press either way. It is the REASON that
    cannot travel, and this is the same one-parameter gap `WO_DRIVE_ABSENCE_01_RETURN`
    §4.1 recorded for the offered set — now load-bearing for a second reason.

    ONE CONFLATION IT INHERITS AND CANNOT FIX AT THIS SEAM: when a target is retired —
    reached, unreachable, or budget-expired — `drive_step` has already cleared it, so this
    reports the NEXT target rather than the pass-over. Distinguishing them needs a context
    field, and the context is not in this rung's fence. **WO-REACHABLE-01 makes this fire
    on frame 1 rather than frame 13, so an existing defect became far more visible without
    becoming worse.** The passed-over count is printed on every line, so a reader watching
    it tick sees the pass-over on the line before."""
    ego = driving_worldline(verdicts)
    if ego is None:
        typed = ", ".join(f"###{w:03d}={verdicts[w].role}" for w in sorted(verdicts))
        return (f"weave sweep · NAV · no worldline types EGO — nothing to steer. "
                f"verdicts in hand: {typed or 'none'}")

    ego_map = action_bearings(worldlines, node_actions,
                              _boundaries(cuts, node_actions, worldlines,
                                          verdicts)).get(ego)
    if not bearing_map(ego_map):
        extra = _unmeasured_str(ego_map)
        return (f"weave sweep · NAV · ego ###{ego:03d} has NO measured action→bearing map "
                f"— no press has yet been observed to move it, and nothing is assumed"
                + (f". {extra}" if extra else ""))

    # HOISTED EIGHT LINES by WO-VISUAL-TARGETS-01 — `_next_target` resolves a site to the
    # worldline standing on it and needs this map to do so. The comprehension is pure and
    # this function takes no decision; the alternative was a second identical dict.
    by_id = {w.id: w for w in worldlines}
    target = context.collide_drive_target
    if target is None:
        _key, target = _next_target(context, candidates, ego, by_id)
    if target is None:
        return (f"weave sweep · NAV · ego ###{ego:03d} — every candidate site reached, "
                f"unreachable, or held by nothing this window "
                f"({len(context.collide_drive_reached)} reached, "
                f"{len(context.collide_drive_unreachable)} unreachable, "
                f"{sum(1 for t in candidates if coverage_state(context, t.key) == UNTRIED)} "
                f"untried, of {len(candidates)} visual objects); drive complete")

    unmeasured = _unmeasured_str(ego_map)
    e, t = by_id.get(ego), by_id.get(target)
    closers: Tuple[Any, ...] = ()
    if e is not None and t is not None:
        ea, ta = _aim(e), _aim(t)
        if ea is not None and ta is not None:
            closers = _closers((ta[0] - ea[0], ta[1] - ea[1]), bearing_map(ego_map))
    if _unreachable(by_id, ego, target, bearing_map(ego_map), cuts,
                    ego_map.transitions.refused, verdict_egos(verdicts)):
        # WO-NO-PREDICTION-01 · **RE-VOICED FROM A VERDICT TO A PLAN'S ABSENCE.** The
        # sentence began *"THE TARGET IS NOT REACHABLE…"*, which is the reading that made
        # the gate feel like a measurement. The arithmetic is unchanged; what it licenses
        # is not. **No route found is not cannot be reached**, and the pursuit CONTINUES —
        # this note now explains a frame the fallback stepper is steering, not a target
        # that has been retired.
        cause = ("NO ROUTE WAS FOUND UNDER WHAT HAS BEEN OBSERVED: no combination of the "
                 "bearings seen so far, avoiding the transitions refused so far, puts this "
                 "footprint on a cell this target holds. **That is the absence of a PLAN, "
                 "not a claim about the target** — the pursuit continues on the fallback "
                 "stepper and ends only on arrival, the anchor bound, or the budget. A "
                 "newly observed bearing voids it, and so does one press that moves")
    elif closers:
        cause = _offered_cause(closers, cuts)
    else:
        cause = ("THE MAP IS SHORT: no measured bearing points the right way on either "
                 "axis. The ego seal needs only two distinguishable bearings, so a "
                 "worldline can type EGO on a map too partial to steer with")
    return (f"weave sweep · NAV · ego ###{ego:03d} → ###{target:03d}: NO ACTION — "
            f"{cause}. {_gap_str(by_id, ego, target)}\n"
            f"    map: {_map_str(ego_map)}"
            + (f" · {unmeasured}" if unmeasured else "")
            + f" · frame {context.collide_drive_frames} · "
              f"{len(context.collide_drive_reached)} reached, "
              f"{len(context.collide_drive_unreachable)} unreachable")
