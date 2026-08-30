"""WO-COLLIDE-GOLDEN-01 · WALK THERE ON PURPOSE — the golden collide drive.

The embodied analogue of the click sweep: where CLICK clicks each eligible object once,
NAV must walk the ego into each one. The skeleton — **select, detect arrival, step** — is
PORTED from `strategy/collide_sweep.py`'s rung-2 drive and
`strategy/tier3_nav._compute_navigation_action_for_target`. **All four of its inputs are
re-pointed to the weave**, and one of them could not be ported at all.

════════════════════════════════════════════════════════════════════════════════════════
WHAT WAS RE-POINTED, AND WHAT THE LEGACY DRIVE READS INSTEAD

  the target   `coverage_sweep`'s NAV candidate list, from the weave's own FIRM verdicts
               — not `library.objects` filtered by `LibraryRole` and `is_background`.
  the ego      a worldline whose Band-2 verdict is `EGO`, and `steps[-1][1].cells` is its
               LIVE footprint — not `header.ego_body_cells` translated from spawn by a
               centroid delta.
  arrival      **a TRANSFER** — see below. Not a footprint overlap against a REMEMBERED
               footprint, which is what legacy compares. WO-REACHABLE-01: the PLANNED side
               of the same event is a live overlap (`reachable.overlaps`), and the two are
               one claim seen from before and after.
  the step     `EgoMap.observed`, measured from the record — not the inline
               `1=UP, 2=DOWN, 3=LEFT, 4=RIGHT` the legacy stepper carries in its body.
               **`observed`, not `bearings`** — WO-EGO-OBSERVED-01 §0.1: the seal's ∀ is
               for a permanent role claim, and a plan re-derived every frame is a ∃.

**The legacy drive is untouched and still wired behind its own env flag.** This is a
parallel implementation, not a patch.

════════════════════════════════════════════════════════════════════════════════════════
ARRIVAL IS A TRANSFER, NOT AN OVERLAP — and this is a STRUCTURAL incompatibility rather
than an epistemic one, the campaign's first.

Legacy asks `bool(frozenset(ego_cells) & frozenset(target_cells))`. **`provenance.
cell_owners` RAISES when a cell is owned twice**: the weave's cuts are a disjoint
partition, so two worldlines can NEVER share a cell and that test is identically false at
every node, for every pair, by construction. Legacy can ask it only because
`library.objects[rid].cells` is spawn-frozen — it compares a moving ego against a
remembered footprint.

**In a partition, contact is a HANDOVER.** The ego has reached the target when, on that
edge, it gained cells whose giver is the target worldline — cell-exact, and the action
that produced the node is attributed to it. `provenance.OwnerEdge.exchanges` is
`(cell, giver, receiver)` by worldline id and has computed exactly this all along.

**THE HONEST CONSEQUENCE, STATED RATHER THAN DISCOVERED:** an object the ego cannot
displace yields no transfer, so it never registers as reached and its frame budget
expires. **Legacy's overlap test has the same failure mode** — it also requires the ego
to occupy ground the target held. *A thing you cannot move is a thing you have not
touched, as far as the record can say.*

════════════════════════════════════════════════════════════════════════════════════════
THE STEPPER — the dominant-axis skeleton, with the table removed

Legacy: dominant axis → `1 if delta_row < 0 else 2` → stuck-perpendicular at
`stuck_count >= 3` → clamp to legal → `0` (RESET) when nothing is playable.

Here: dominant axis → **an action ANY of whose observed bearings has, on that axis, the
sign that closes the gap** → the other axis when the first offers none → nothing when
neither does. **The perpendicular fallback is structural rather than counted** — it fires
when the dominant axis has no observed answer, not after three of anything, so legacy's
one tuned constant does not come with the shape.

**AN ACTION WITH NO OBSERVED BEARING IS NOT AVAILABLE TO THIS STEPPER.** No completion, no
canonical cardinal, no symmetric inference. `stride_probe._commit_action_dirs` fills
unobserved cardinals from `canonical_at_stride`; nothing here does, and a test forbids it.

**Position is read here and that is not a prior.** Navigation is inherently positional —
this module computes a direction to walk, and classifies nothing. The campaign's ban on
size and position priors is a ban on deciding what a thing IS from where it is or how big
it is; no verdict is produced anywhere in this file.

Pure and stdlib-only. Reads the weave it is handed and the drive state on the context;
emits an ACTION ID, never a `GameAction` — the caller owns the platform type. Writes no
belief, and never reaches `land_weave_roles`.
"""

from __future__ import annotations

from dataclasses import dataclass

from typing import (Any, Dict, FrozenSet, Iterable, List, NamedTuple, Optional, Sequence,
                    Tuple)

from virelai_v4.capture.clay import master_object_list
from virelai_v4.capture.ledger_build import regions_at
from virelai_v4.weave.collide_plan import _next_press, _reach_state, _unreachable, walked_out
# WO-ARRIVE-01 · on its own line, and the committed one above is byte-identical.
# `test_ego_set`'s fence pins that line as evidence the search is untouched, and a fence
# that rejects a widening is working — the name arrives beside it rather than inside it.
from virelai_v4.weave.collide_plan import fresh_body, owner_ids, standing_on
from virelai_v4.weave.collide_tags import Bearing, Cell, Site, _region_at_last, blocking_tags
from virelai_v4.weave.ego_read import action_bearings
from virelai_v4.weave.ground_read import ground_block, ground_worldlines
from virelai_v4.weave.provenance import owner_edge
from virelai_v4.weave.action_roster import (heart_boundary_edges,
                                            life_boundary_edges)
from virelai_v4.weave.role_read import COUNTER, EGO, FIRM, verdict_egos


# WO-PROBE-RECORD-01 · the three meanings `_pass_over` already carried as trailing
# comments, made into values. NAMES, NOT SCORES: nothing is ranked, nothing is compared,
# and no verdict reads them. They exist so a retirement can say WHICH retirement it was —
# the distinction this module could not make while its record was one untagged set.
ARRIVED: str = "ARRIVED"          # the transfer happened
# WO-NO-PREDICTION-01 · **`UNREACHABLE` NOW HAS NO PRODUCER, AND THAT IS RATIFIED RATHER
# THAN OVERLOOKED.** Its one emitter was `drive_step`'s reachability gate, and the gate was
# a prediction. The name, `_pass_over`'s branch and `coverage_state`'s read all STAY —
# correct and dormant — so an evidence-fed producer can fill it without re-deriving the
# state. **No such producer is invented here.** `STUCK`'s bound is the honest candidate and
# it is not chartered; v3.5's was `_UNREACHABLE_THRESH = 5`, a tuned constant, and its
# record cleared only at a level transition. Neither ports.
UNREACHABLE: str = "UNREACHABLE"  # DORMANT — reserved for evidence, emitted by nothing
# WO-CURSOR-AND-STUCK-01 · THE THIRD NEGATIVE FACT, AND IT IS NOT THE OTHER TWO.
# **Stuck is about the POSITION; unreachable is about the WORLD.** More presses at one
# anchor than there are actions to try means every direction has had at least one
# attempt and this place has yielded nothing — it says NOTHING about whether the target
# can be reached from somewhere else, and the target stays on the list. v3.5 collapsed
# exactly these two: `stuck_detector`'s BFS_STAGNATION carried `suggested_action =
# "MARK_UNREACHABLE"`, and `nav_atlas.unreachable_targets` was then filtered silently
# and forever. A NAME, not a number; no verdict reads it.
STUCK: str = "STUCK"              # the position yielded nothing — not a claim about the world

# WO-BLOCKER-TAG-01 · THE THIRD COVERAGE STATE, AND IT IS THE DEFAULT. `ARRIVED` and
# `UNREACHABLE` double as the two recorded states; `UNTRIED` is what a candidate is when
# neither set holds it. **A budget expiry maps here and not to a third record** — twelve
# frames running out is *I ran out*, not *I cannot*, and making it a verdict is the
# press-tally mistake `_unreachable`'s docstring already names four prior instances of.
UNTRIED: str = "UNTRIED"          # never attempted, or attempted and left inconclusive

# The ordinal comparison, and it is the whole gradient. `reach` returns a path that is
# SHORTEST IN PRESSES, so its length is presses-remaining. Fewer is closer. There is no
# distance here and there must never be one: a rate, a speed or a magnitude would each be
# a metric in disguise, and this campaign has paid for every metric it reached for.
CLOSER: str = "CLOSER"
STALLED: str = "STALLED"
RECEDING: str = "RECEDING"
OPENING: str = "OPENING"          # fewer than two measurements — nothing to compare yet


class DriveStep(NamedTuple):
    """One frame's decision, with everything a reader needs to grade it on the replay."""
    ego: int
    target: int
    action: Any
    bearing: Bearing
    basis: str
    # WO-PROBE-RECORD-01 · defaulted, so every existing construction site is unchanged
    remaining: Optional[int] = None   # presses to arrival, from the search already run
    progress: str = OPENING           # this frame against the last, ordinally


def bearing_map(ego_map) -> Dict[Any, FrozenSet[Bearing]]:
    """`{action: every distinct bearing it was seen to produce}` — the projection
    `WO_NAV_MINE_00_RETURN` §4 said was a comprehension. OBSERVED ONLY: an action never
    pressed, or pressed with no translation, has no entry and is therefore never emitted.

    **IT READS `observed`, NOT `bearings` — `WO_EGO_OBSERVED_01` §0.1.** The seal's
    `bearings` is filtered by a ∀ (*every press of this button agreed*) because a
    permanent role claim must be. **A plan is not a claim.** This map answers *if I press
    it, where do I probably end up* — re-derived every frame, feeding a loop that re-plans
    on the next observation — and gating it on the ∀ discarded well-observed bearings
    that a single disagreeing press had killed. A closed loop does not need certainty.

    **The seal is untouched.** `ego_read.bearings` and `ego_read.ego_seal` are exactly
    what they were; this reads a field beside them."""
    if ego_map is None:
        return {}
    return {o.action: o.bearings for o in ego_map.observed}


def driving_worldline(verdicts) -> Optional[int]:
    """The worldline this drive steers, or `None` when none is typed `EGO`.

    **MULTI-EGO IS THE RATIFIED DEFAULT** (`RULING_EGO_WORLDLINE_v1`) and this drive can
    steer one body at a time, so a selection is unavoidable. The rule is the LOWEST
    worldline id — deterministic, and the same first-appearance ordering
    `build_weave_sweep_list` already uses. It is a convention, not a judgement: nothing
    here claims the lowest-numbered ego is the better one, and a rung that needs to steer
    a chosen body must say which and why."""
    egos = sorted(wid for wid, rv in verdicts.items() if rv.role == EGO)
    return egos[0] if egos else None


def arrived(edge, egos, target_wid: int) -> bool:
    """Did the BODY take cells from the target on this edge? That is contact, in a
    partition where nothing can overlap. Direction matters: the ego GAINING from the
    target is arrival; the ego giving to it is the target moving over the ego.

    **`egos` IS A SET — `RULING_EGO_WORLDLINE_v1` §4, applied.** *"All downstream
    consumers must accept a set of ego worldlines. Any code or contract assuming one ego
    is stale as of this ruling."* This took one id and was stale by that ruling; the body
    is several worldlines and a transfer to ANY of them is the body arriving. Nothing new
    is computed — `provenance.owner_edge` already records the receiver of every cell whose
    owner changed, and the single-id form discarded all but one of them.

    A caller wanting the old single-id question asks it by passing a one-member set."""
    return any(giver == target_wid and receiver in egos
               for (_cell, giver, receiver) in edge.exchanges)


def _aim(worldline) -> Optional[Cell]:
    """The point this drive steers by: the footprint's TOP-LEFT ANCHOR, live.

    **`_centroid` RETIRED HERE — WO-REACHABLE-01 §1.3, on the ratified anchor ruling**
    (`DESIGN_PHILOSOPHY_v1_apr2026.md:191` / `_v2.md:183`, cited from the archived source
    because the governing copy no longer carries the clause — see the return's §8.1):
    *"Ego displacement must be computed from direct grid localization … Centroid is a trap
    — use top-left bounding box anchor."*

    THREE REASONS, and the first two were already measured in this repository:

      1. **A mean is not a position.** `WO-CAMPAIGN3-PHASE2-05-STEP0-FINDINGS` measured a
         3×3 body at top-left `(32,21)` whose centroid `(33,22)` anchored a slice that
         missed every cell of the body. For a hollow or L-shaped footprint the centroid
         need not lie inside the object at all.
      2. **A mean is not an integer**, and a half-integer cannot lie on a lattice of
         integer strides. `PHASE_1_V3_5_MINING_INVENTORY:1149` recorded the V3.5 finding
         as *"np.min is always integer and always stride-clean"* — the lattice argument,
         written before there was a lattice to argue about.
      3. **It drifts against the record that renders it.** `WO_EGO_OBSERVED_01_RETURN`
         §7.2 found the note printing a gap of `(+8,+16)` between anchors `(26,3)` and
         `(34,20)`, whose true difference is `(+8,+17)` — the centroid showing through a
         field labelled `anchor`, by exactly the half-extent difference of the two
         footprints. **The same quantity now decides and renders, so it cannot drift.**

    `RegionClay.anchor` is `(min row, min col)`, computed at `from_cells`, and it carries
    the `(-1, -1)` sentinel for an empty cell set — which is why this returns `None` there
    instead: a coordinate that is not a coordinate is what the legacy sentinel was, and
    `WO_COLLIDE_GOLDEN_01` already removed one of those from this module."""
    region = _region_at_last(worldline)
    return None if not region.cells else region.anchor


def _axis_order(delta: Tuple[float, float]) -> List[int]:
    """Dominant axis first, then the other — the ported skeleton's ordering, extracted so
    the DECISION and the note's account of it read the same function. A note that
    re-derives which axis was tried can drift from the axis that actually was."""
    return [0, 1] if abs(delta[0]) >= abs(delta[1]) else [1, 0]


def _qualifies(bearings: Iterable[Bearing], axis: int, sign: int) -> bool:
    """**∃, and the whole rung is in this word.** Has this button EVER gone the way that
    closes this axis? One witness is enough and no second question is asked — not how
    often, not how usually, not compared with what else it did.

    No count appears here and none is reachable: `ActionObserved.bearings` is a SET, so
    *how many times* is structurally unavailable at this seam. A majority rule cannot be
    written against it, which is the ban enforced by shape rather than by review."""
    return any(b[axis] * sign > 0 for b in bearings)


def _closing(bearings: Iterable[Bearing], axis: int, sign: int) -> Bearing:
    """WHICH of the chosen action's observed bearings the step reports as its own.

    A CONVENTION, DELIBERATELY NOT A STATISTIC. The obvious alternative — report the one
    seen most often — is a modal bearing, which is a threshold wearing a statistic and is
    forbidden. This takes the lowest-sorted bearing among those that close the axis: fully
    determined by the record, computed without consulting any tally, and honest about what
    it is. The step's `basis` renders it, so a reader grading the replay sees a bearing the
    record actually contains."""
    return sorted(b for b in bearings if b[axis] * sign > 0)[0]


def _unrefused(actions: Iterable[Any], site, refused) -> Tuple[Any, ...]:
    """Those actions the record has NOT already refused from THIS site, order preserved.

    **TIER 1, PORTED FROM `nav_executor.py:409`** — *"skip BFS-planned actions that are known
    blocked edges at the current position. Prevents issuing the exact same (position, action)
    pair that already produced zero movement."* The prior architecture ran this filter over
    its held plan; here it runs over the stepper's candidates, which is the same filter at
    the seam that was missing it.

    **THE KEY IS `(site, action)` AND BOTH HALVES ARE LOAD-BEARING.** A refusal is a fact
    about a press made from one cell. The same button from a different cell is untested, and
    treating it as refused would be the class-level generalisation `_record_blocked_wall`
    made and this build forbids — `WO_NAV_LOOP_MINE_00_RETURN` §3 grades that column
    do-not-port by name.

    **ABSENCE IS ABSENCE, AT BOTH INPUTS.** No site, or no record, excludes nothing — an
    exclusion keyed on a site nobody supplied would be keyed on nothing, and a caller that
    holds no record is not asserting that nothing is refused."""
    if site is None or not refused:
        return tuple(actions)
    return tuple(a for a in actions if (site, a) not in refused)


def _pairs(bmap: Dict[Any, FrozenSet[Bearing]], actions: Iterable[Any]
           ) -> Tuple[Tuple[Any, Bearing], ...]:
    """Every `(action, bearing)` the record offers for these actions, deterministically.

    **THE SHAPE IS `reachable._expansions`', VERBATIM, AND THAT IS DELIBERATE.** Actions
    ascending by `str`, each action's OBSERVED bearings ascending. **An action seen to
    produce more than one bearing contributes each of them**, because the ∃ the map became
    is a claim that the button has gone each of those ways.

    **AND THAT IS WHY THIS IS A PAIR LIST RATHER THAN A BEARING LOOKUP.**
    `WO-PAIR-AND-BODY-01` retired `_bearing_of` for reading THE lowest bearing out of the
    map: *"right whenever an action had one bearing and wrong exactly when the ∃ map held
    more than one — which is what `WO_EGO_OBSERVED_01` built on purpose."* **My first draft
    of this rung reintroduced exactly that defect and `test_pair_and_body`'s fence caught
    it.** Working over pairs means a multi-bearing action is tested and reported per
    bearing, never collapsed — so the value that decides is the value the note renders.

    No tally is consulted and none exists: `ActionObserved.bearings` is a set."""
    return tuple((a, b) for a in sorted(actions, key=str)
                 for b in sorted(bmap.get(a) or ()))


def _orthogonal_to(bmap: Dict[Any, FrozenSet[Bearing]], against: Bearing,
                   actions: Iterable[Any]) -> Tuple[Tuple[Any, Bearing], ...]:
    """Those `(action, bearing)` pairs whose bearing is ORTHOGONAL to `against`.

    **TIER 2, AND THE PORT'S SHARPEST EDGE — THE TABLE DID NOT COME WITH IT.** Both ancestors
    read the perpendicular action out of a literal: `nav_executor.py:259`'s
    `_PERP_MAP` mapping, and the legacy layer's branch on the action id at
    `strategy/tier3_nav.py:111`. **Both assert which button is which axis, which is a
    No-null-class breach and is illegal here.**

    **Perpendicular is a relation between two MEASURED bearings.** Their dot product vanishes
    or it does not. Nothing is named, nothing is assumed, and an action the record has never
    seen move the ego contributes no pair rather than a guess — which is why the direction
    table could never have been written from this record in the first place.

    **A BEARING THAT VANISHES ENTIRELY IS NOT A SIDESTEP.** Its dot product with everything
    is zero; a button observed to move the ego nowhere is excluded rather than admitted on a
    technicality."""
    return tuple((a, b) for a, b in _pairs(bmap, actions)
                 if (b[0] or b[1]) and b[0] * against[0] + b[1] * against[1] == 0)


def _toward(delta: Tuple[float, float], bmap: Dict[Any, FrozenSet[Bearing]],
            offered: Sequence[Any], site=None,
            refused: FrozenSet[Any] = frozenset()
            ) -> Optional[Tuple[Any, Bearing, Any]]:
    """`(action, bearing, stepped_off)` — the press to make, or `None` when the record offers
    none — **and it no longer presses into what this site has already refused.**

    **THE THIRD ELEMENT IS WHAT THE NOTE RENDERS, AND IT EXISTS SO THE NOTE CANNOT DRIFT.**
    `stepped_off` is the refused action tier 2 moved off, or `None` for tiers 1 and 3. The
    first draft let the renderer RE-DERIVE the sidestep from the two records, and it claimed
    one on a tier-3 rotation — because the rotated action happened to be orthogonal to
    something refused here. **A note that states a tier the stepper did not take is a
    renderer stating a falsehood**, which this campaign has already had to remove once.
    `_closing`'s discipline, applied here: **the same value decides and renders.**

    **THE RED, IN THE DIRECTOR'S WORDS:** *the solver wastes motions into a wall and then
    wanders.* Measured on the constructed board: the ego stands where action 4 was refused,
    the record still holds 4's observed bearing from elsewhere, the target lies beyond — and
    this function returned 4, every frame, until the budget expired.

    **THE ROOT WAS NOT IGNORANCE, IT WAS PLUMBING.** The refusal set is bound in `drive_step`
    and threaded into `reach`, which excludes it at expansion. It never reached here. **The
    component holding the record was the one returning nothing; the one actually pressing
    was blind to it** — `WO_NAV_LOOP_MINE_00_RETURN` §4b pinned that at file:line, and this
    signature is the whole of the fix.

    ════════════════════════════════════════════════════════════════════════════════════
    THREE TIERS, PORTED IN ORDER FROM `execution/nav_executor.py`'s WALK

      **1 · Do not re-press a refusal** (`:409`). Candidates are filtered by `_unrefused`
        before any axis is considered. The dominant-axis walk below is otherwise UNCHANGED.

      **2 · Move off the refused axis** (`:662`). When every action that would close the gap
        is refused here, take one whose OBSERVED bearing is orthogonal to the refused one's —
        preferring one not itself refused here, which is the prior architecture's own
        condition: *"only inject if the perpendicular action is not itself a known blocked
        edge at this position."*

      **3 · Rotate the offered set** (`:415`). When neither is available, take any offered
        action the record holds a bearing for and this site has not refused, rather than
        recomputing the same direction from the same gap. The prior architecture cycled all
        four and called it *"exploration mode"* — **when there is no route, the useful act is
        to learn the board, not to shove at it.**

    **AND WHEN EVERY OFFERED ACTION IS REFUSED HERE, THIS RETURNS `None`.** Pressing anyway
    would be the wall this rung exists to stop, dressed as persistence.

    ════════════════════════════════════════════════════════════════════════════════════
    WHAT DID NOT PORT

    **The direction tables.** `_PERP_MAP` and the legacy `if action_id in {1, 2}` both assert
    which button is which axis. `_orthogonal_to` computes the relation from the record.

    **The counts.** `_UNREACHABLE_THRESH = 5` and `stuck_count >= 3` are tuned constants; the
    trigger here is an observation already in hand — *this press, from this site, was
    refused* — available the same frame it is needed.

    **THE OFFERED FILTER IS LOAD-BEARING AND `_closers` DELIBERATELY LACKS IT** — that
    difference is `WO_DRIVE_ABSENCE_01`'s three-way diagnostic split, and it survives this
    rung unchanged. Every tier below is filtered by it.

    **ABSENCE IS ABSENCE.** No site or no record restores the anchor's behaviour exactly:
    `_unrefused` excludes nothing, tier 2 never fires because tier 1 never empties, and the
    walk is the one it always was. Asserted."""
    offers = [a for a in bmap if a in offered]
    live = _unrefused(offers, site, refused)
    held = tuple(a for a in offers if a not in live)      # refused HERE, and only here
    for axis in _axis_order(delta):
        want = delta[axis]
        if want == 0:
            continue
        sign = 1 if want > 0 else -1
        able = sorted((a for a in live if _qualifies(bmap[a], axis, sign)), key=str)
        if able:
            return able[0], _closing(bmap[able[0]], axis, sign), None
        # TIER 2 · every action that would close this axis is refused HERE — step off it.
        for blocked in sorted((a for a in held if _qualifies(bmap[a], axis, sign)), key=str):
            side = _orthogonal_to(bmap, _closing(bmap[blocked], axis, sign), live)
            if side:
                return side[0][0], side[0][1], blocked
    # TIER 3 · nothing closes the gap and nothing sidesteps. **GATED ON A REFUSAL BEING IN
    # PLAY**, because a frame with nothing refused here is not an obstruction: the anchor
    # emitted nothing and stated why (`WO-DRIVE-ABSENCE-01`), and that contract is untouched.
    # Rotating there would replace a stated absence with a press, which is a different rung.
    if held:
        rest = _pairs(bmap, live)
        if rest:
            return rest[0][0], rest[0][1], None
    return None


# WO-ROLE-MASK-01 · THE ROLES WHOSE OBJECTS ARE NOT TARGETS — A CLOSED LIST OF TWO, AND
# THE THIRD IS HALTED.
#
# Director's ruling: *the counter mask is learned and then applied to the target list; once
# we know what the counter is, all the visual objects of the counter are no longer targeted.
# Same with the floor. Other than that, all objects should be targeted. And the wall should
# be a target — the counter will be a target until we learn to mask it.*
#
# **THIS IS NOT THE BARRING THIS CAMPAIGN DELETED.** `_barred_sites` removed candidates for
# what they had been typed as BEFORE any press — a prediction about reachability, and the
# same error as the gate that stood beside it. This removes them for what they ARE: a HUD
# is not a probe subject. **The difference is the seal**: nothing is masked until the weave
# has sealed it, and a counter is a legitimate target on every frame before that.
#
# **NAMED INDIVIDUALLY, NEVER A PREDICATE OVER THE ARCHETYPE TABLE.** A rule of the form
# *typed roles are not targets* would take `LEVER` — and reaching a lever is the objective
# on an embodied world, where the CLICK arm excludes a known one because re-clicking is
# waste. `INERT` stays a target too: the wall is what the region will be learned from, and
# it is learned by going rather than by filtering. `REACTIVE-DRIVEN` that is not the floor
# is a thing a lever moves, and worth touching.
#
# **FIRM, AND THE BAR IS UNIFORM.** `coverage_sweep._is_excluded` gates its own exclusion on
# `confidence == FIRM` and its docstring refuses to lower the bar per role, because *a
# per-role bar would make this filter's own rule depend on which role it is reading.* The
# same reasoning holds here and the same bar is used.
#
# **THE MEDIUM IS ABSENT FROM THIS LIST AND THAT IS A HALT, NOT AN OMISSION — see the
# return's §2.** The floor is `REACTIVE-DRIVEN`'s sub-class, and `RoleVerdict` carries no
# sub-class field: `role_read._attach_medium` writes the archetype and puts the medium's
# evidence in `basis`, a prose string — *"the menu stays closed at six … the sub-class lives
# in the basis."* `_medium_of` is computed at `role_read.py:1153` and discarded. So the
# floor cannot be masked from a verdict as verdicts are shaped, and masking `REACTIVE-DRIVEN`
# whole would take the things a lever moves — which the ruling says must stay targets.
# **Deriving it here would make a third caller of `medium_witnesses` and a second producer
# of the medium fact. The verdict's shape is CE's ruling to make.**
_MASKED_ROLES = (COUNTER,)


def masked_worldlines(verdicts) -> FrozenSet[int]:
    """Every worldline whose visual objects are not targets — the ego, and each sealed
    member of `_MASKED_ROLES`.

    **EVERY `EGO`, NOT THE ONE WE DRIVE — WO-EGO-MASK-ALL-01, AND THIS CORRECTS
    `WO-ROLE-MASK-01`.** This line read `driving_worldline(verdicts)`, which returns the
    LOWEST id among the worldlines typed `EGO`. **That is the right function for a different
    question.** *Which one do I steer* has exactly one answer and always will; *which of
    these are mine* does not, and `RULING_EGO_WORLDLINE_v1` ratified multi-ego as the
    default. The seal honours that — `role_read`'s ladder types per worldline and elects
    nothing, so any number may carry `EGO` in one window — and the bar did not.

    **THE COST WAS MEASURED ON THE BOARD.** An avatar built from two visual objects that
    move as one types as two `EGO` worldlines; the old bar took the elected half and left
    the other's whole trail in the queue. **The ego was targeting itself, at positions it
    had already left.** The same defect appears wherever a world carries more than one
    avatar, which the ruling says is the default rather than the exception.

    **NO ELECTION HERE, AND THAT IS STRUCTURAL.** A tie-break in the bar would re-introduce
    the single-ego assumption the ruling retired. `driving_worldline` keeps its election and
    the stepper is untouched: the two questions now have two functions, which is what they
    always needed.

    **THE EGO IS BARRED AT ANY CONFIDENCE.** `infer_roles` emits no FIRM `EGO`
    (`_is_excluded`'s docstring records the clause it left structurally correct and inert
    for the same reason), and barring the body you are steering is identity, not belief.
    The counter half keeps the uniform `FIRM` bar, untouched.

    **NO VERDICTS MEANS NOTHING IS MASKED, NOT EVERYTHING.** Absence rendered as absence:
    a board the weave has not read yet is a board where every object is a target.

    **WO-GROUND-01 · THE GROUND IS BARRED, AND IT IS READ FROM THE FIELD RATHER THAN THE
    ROLE.** `rv.ground` is a defaulted field, not a seventh Band-2 answer — the menu is
    closed at six and this rung does not open it. The bar carries no confidence clause
    because the claim carries no confidence: the predicate is two set relations over
    records already in hand, and a worldline either deformed only under the ego or it did
    not. **Nothing is masked before it types** — `ground` defaults `False`, so a board the
    ladder has not typed yet bars nothing, which is the counter's own discipline restated.

    **BARRED FROM THE LIST, NOT FROM THE RECORD.** `ground_read.ground_block` prints every
    visual object this line removes, with its basis. A mask that made them vanish would be
    deletion wearing a disregard's clothes."""
    if not verdicts:
        return frozenset()
    return ground_worldlines(verdicts) | frozenset(
        wid for wid, rv in verdicts.items()
        if rv.role == EGO or (rv.role in _MASKED_ROLES and rv.confidence == FIRM))


def _own_footprints(worldlines, ego) -> FrozenSet[Any]:
    """**THE BARRED WORLDLINES' OWN VISUAL OBJECTS, AND NOTHING ELSE IS BARRED.**

    **WO-ROLE-MASK-01 · THE PARAMETER WIDENED FROM ONE ID TO A SET; THE RULE DID NOT
    CHANGE.** It read `ego: Optional[int]` and barred the driving worldline's own entries.
    It now accepts an id, an iterable of ids, or `None`, and bars the entries of each — the
    `(node, cells)` pairing, the trail-wide match and the discriminator below are all
    exactly as they were, and the one-id case is byte-identical. **The work order listed
    this function as out of scope while its own §0.3 named it as the template the mask is
    built on; widening the parameter is the smallest reading that makes both true, and CE
    can reverse it in one line.**

    **WHY THE TRAIL AND NOT THE ANCHOR, FOR A COUNTER ESPECIALLY.** A draining counter mints
    a new fingerprint at a new anchor every tick, and each enters the queue at its own first
    appearance. Only a trail-wide `(node, cells)` match removes all of them; barring the
    current anchor would remove one moment of forty.

    Director's ruling: *the ego should not target its own visual objects, yes. After that
    everything should be a valid target, then we must learn what is reachable.*

    **WHAT THIS REPLACED, AND BOTH RULES WERE CE'S OWN.** `_barred_sites` inverted
    `build_weave_sweep_list`'s exclusion and walked **every step** of every excluded
    worldline, barring each anchor. Its docstring called that *"the safe direction."* It is
    not: a thing typed `COUNTER` is exactly a thing we may have typed wrong, and refusing
    to go near it is reasoning ahead of evidence — **the same error the reachability gate
    made, in the filter standing beside it.**

    **AND THE MEASURED MECHANISM IS NOT THE ONE IT WAS BLAMED ON.** Barring was by
    ANCHOR, so a huge medium's top-left corner barely moves and it barred **one** site.
    What swept the board was a small MOVER — a ticking counter, and **the ego itself**.
    Measured at `a3aa5c8` on a five-object board: the counter barred five sites, the ego
    barred five, the medium one, and **three of five real objects were invisible to
    navigation — none of them the thing that barred it.**

    **THE BAR IS BY FINGERPRINT, NOT BY SITE, AND THE DOOR IS WHY.** Three readings of the
    ruling were measured. Barring the ego's CURRENT anchor leaves its whole past trail as
    candidates — the ego targeting where it used to be, which is precisely *its own visual
    objects*. Barring the ego's TRAIL OF SITES fixes that and **deletes any real object
    standing where the ego once stood** — including, on the discriminating fixture, a
    newborn object appearing at the ego's start cell. That is the door of
    `WO_BLOCKER_TAG_01`'s reopening case, and the site reading loses it.

    **A fingerprint is the ego's or it is not.** An entry the ego's own worldline held is
    the ego; an entry that merely shares a place with one is a different object and is a
    target. `(class_id, cells)` is the immortal key `WO_VISUAL_TARGETS_01` already keys the
    master list on, so this is a lookup, not a derivation.

    **THE KEY IS `(node, cells)`, AND BOTH HALVES ARE LOAD-BEARING.**
    `test_visual_targets`'s AST guard bans the attribute `class_id` inside this derivation,
    because filtering BY CLASS is the model every prior generation built. Half the immortal
    fingerprint would be a legitimate read and **the fence cannot tell the two apart, so it
    is obeyed rather than widened** — this rung carries no ruling that supersedes it.

    Cells ALONE are not enough, and the discriminator caught it: an object appearing later
    at the ego's exact former footprint would be barred, which is the door case this rule
    exists to keep. **Pairing the cells with the NODE makes it exact.** A cut is a DISJOINT
    partition, so at node *n* the region holding the ego's cells IS the ego — and an object
    whose own first appearance is at a different node is a different object, however its
    footprint coincides. No class is named and nothing is over-barred.

    The one case that still bars is an object of the ego's OWN class at the ego's OWN cells
    at a node the ego was there — which is not another object at all: the immortal
    fingerprint makes it one entry with the ego's.

    Absence is absence: no ego, or an ego absent from the window, bars nothing."""
    if ego is None:
        return frozenset()
    ids = {ego} if isinstance(ego, int) else set(ego)
    return _footprints_of(worldlines, ids)


def _footprints_of(worldlines, ids) -> FrozenSet[Any]:
    """**THE ONE JOIN FROM WORLDLINES TO VISUAL OBJECTS**, and both readers of it now
    share this line rather than each spelling it.

    `(node, cells)` per step: a worldline's identity claim, expressed in the coordinates a
    `FingerprintEntry`'s trail can be tested against. **A cut is a DISJOINT partition, so
    at node *n* the region holding those cells IS that worldline** — the join is exact and
    needs no class, no anchor and no proximity.

    **WO-TARGET-THE-OBJECT-01 · EXTRACTED, NOT ADDED.** `_own_footprints` held these two
    lines and the novelty band needs the same ones. Two spellings of one join is how the
    mask and the band drift apart, and R-2's *masking is by worldline, targeting is by
    visual object* is exactly the sentence that makes this the seam."""
    return frozenset((n, r.cells)
                     for w in worldlines if w.id in ids for (n, r) in w.steps)


def _newborn_footprints(worldlines) -> FrozenSet[Any]:
    """**THE VISUAL OBJECTS OF EVERY WORLDLINE BORN INSIDE THIS WINDOW.** R-3's top band.

    **THE BIRTH IS READ FROM `first_node`, NOT FROM A VERB.** `WO_PLANNER_MINE_00_RETURN`
    Q4.3 established `Verb.BIRTH` is discarded — it seeds a builder and never reaches
    `worldline.verbs` — so the appearance is read positionally, and the rule for what
    counts is `re_join`'s own, ported rather than invented: **`first_node > win_start`,
    because a window-seed is not a birth.** A worldline present at the window's first node
    may have existed for a thousand frames; only one that starts later APPEARED.

    **AND THE BAND IS A WORLDLINE FACT JOINED TO OBJECTS BY `_footprints_of`** — the same
    join the mask uses, which is what the charter's P2 asked to be named. **Not a set
    difference over the master list**: that attributes by adjacency, and the master list
    only grows, so *appeared since the last frame* has no clean reading at a read-time
    view.

    Absence is absence: an empty window, or one where every worldline is a seed, has no
    newborn band — which renders as every candidate sorting on footprint alone."""
    if not worldlines:
        return frozenset()
    win_start = min(w.first_node for w in worldlines)
    return _footprints_of(worldlines,
                          {w.id for w in worldlines if w.first_node > win_start})


@dataclass(frozen=True)
class Target:
    """**ONE VISUAL OBJECT ON THE DRIVE'S TO-DO LIST: WHAT IT IS, AND WHERE TO STEER.**

    `key` is the immortal fingerprint `(class integer, cells)` — **the identity, and the
    only thing coverage is keyed on.** `site` is that object's NW corner at its first
    appearance — **a reference point for navigation and nothing more.**

    **WO-TARGET-THE-OBJECT-01 · R-1 · THE TWO WERE ONE VALUE AND THAT CONFLATED OBJECTS.**
    The queue was a tuple of anchors and the derivation deduped on them, so *two distinct
    visual objects whose corners coincide* were one target. The Director's ruling:
    **the NW corner is a simple reference point for navigation; an anchor should be a
    visual object's cell-site footprint.** A bar at eighty-two cells and the same bar at
    eighty are two objects, and collapsing them because their corners agree is the
    worldline error one stratum down — an identity claim standing in for a fact.

    **AND THE SITE KEY WAS SOLVING A PROBLEM THE MASK NOW SOLVES AT THE SOURCE.** It
    existed so a draining counter could not mint forty entries; `masked_worldlines` removes
    them by role, by worldline, before the ranking ever sees them. The dedup was still
    collapsing distinct targets on top of that — paying for a fix it no longer needed.

    **THE COST, STATED RATHER THAN DISCOVERED:** two objects sharing an anchor are now two
    pursuits, and the second arrives the moment it is offered. **That is correct** — each
    is a distinct thing the drive has or has not worked, and a checkoff that ticks an
    object nobody went to is the false coverage this record exists to prevent.

    **THE HOME IS THE FENCE'S, NOT THE MERITS'.** The coherent placement is
    `collide_tags.py`, beside the `Site` alias this record supersedes, and moving it there
    pays four lines of this rung's ratchet — measured, not guessed. **That file is outside
    this rung's fence**, whose closing line is *anything else in `git status` — HALT*, so
    it stays here and the ratchet stays unpaid. **One line of CE's ruling moves it.**"""

    key: Tuple[int, Any]
    site: Site


def visual_targets(cuts, worldlines, ego: Optional[int] = None) -> Tuple[Target, ...]:
    """**THE DRIVE'S TO-DO LIST: THE BOARD'S VISUAL OBJECTS, AS SITES.**

    Director's ruling: *targets should be VISUAL OBJECTS, not worldlines. A visual object
    is an objective fact that will not change, only grow. Worldlines may shift as we learn
    more about the world.* A fingerprint `(class_id, cells)` is immortal once seen; a
    worldline id is a claim about identity that `weave_window` renumbers by first
    appearance **within the window**, so the same object carries different ids in
    successive windows and a checkoff keyed on one ticks off whatever now holds that
    number.

    **THE KEY IS THE FINGERPRINT. THE PARAGRAPH BELOW SAYS "SITE" AND IS THE SECOND STALE
    CLAIM IN THIS DOCSTRING — CORRECTED BY WO-DECLARE-INTENT-01.** `_next_target` returns
    `t.key`, `drive_step` stores it in `collide_drive_target_site`, and `_pass_over` adds
    THAT to the coverage record: `(class integer, cells)`, not the anchor.
    `WO-TARGET-THE-OBJECT-01` made that change knowingly and recorded in `_pass_over` that
    *"the field still spells itself `..._target_site`; what it holds is the object's
    immortal key"* — but this paragraph, which states the superseded ruling, was left
    standing.

    **AND THE DIFFERENCE IS MEASURABLE, NOT COSMETIC.** Under fingerprint keying, an
    object that deforms mints a new entry per node and each needs its OWN pursuit; under
    the site rule the paragraph describes, one attempt would cover them all. Measured on
    the graded record `[over-corpus]`: **40 entries over 15 distinct sites — 2.7 per site,
    one site holding 16.** That is a standing question for CE, and this function's
    behaviour is untouched by the rung that found it.

    [SUPERSEDED — kept as the record of what was ruled and when.]
    `WO_BLOCKED_MINE_00_RETURN` Q4 found all six of v3.5's target structures keyed on
    `(row, col)` and none on an object; Q7d found the fingerprint-to-subject question
    unmet in every generation. The ruling: **attempting one entry attempts every entry
    sharing its site.** The ego occupies a footprint and contacts whatever holds those
    cells, so two fingerprints at one anchor are one subject at two moments.

    Not the fingerprint, because an object that recolours or resizes **under contact**
    mints a new one the instant it is touched — a fingerprint-keyed checkoff would tick
    nothing and the list would grow faster than it could be worked. Not the worldline,
    because that is the claim the ruling replaces.

    **THE COST, STATED RATHER THAN DISCOVERED:** an object that MOVES presents at two
    sites and attempting it at one does not tick the other. That is correct — contact at
    a place is what the arrival test measures, and a moved object at a new place is a new
    opportunity for contact.

    **ORDER: `_order_key`'S RANKING — SEE THAT FUNCTION, WHICH IS THE ONE AUTHORITY.**
    *Newly-appeared, then smallest footprint, then lowest class integer, then first
    appearance*, ascending throughout.

    **THIS PARAGRAPH SAID "first appearance, and nothing else … no rarity, no size" AND
    WAS STALE FROM THE RUNG AFTER IT WAS WRITTEN — CORRECTED BY WO-DECLARE-INTENT-01.**
    `WO-VISUAL-TARGETS-01` wrote it truthfully; `WO-RANK-AUDIT-00`/R-3 then added
    `_order_key` and the sort at the foot of this function, and the prose was never
    brought along. **A charter was written from it**: `WO_DECLARE_INTENT_01 §2` read this
    paragraph, concluded the coverage roster's `ranked:` footer was advertising a removed
    ranking, and asked for the FOOTER to be corrected. The footer is accurate; this was
    the stale text. Prose exceeding evidence, inside the function whose behaviour it
    describes — the failure mode this project names first.

    **NO CAP, AND THAT PART WAS AND REMAINS TRUE.** Truncation is v3.5's silent eight.

    A READ-TIME VIEW, NEVER A SECOND ACCUMULATOR — `clay`'s own rule for this primitive.
    The list is re-derived from the cached cuts; what accumulates is the coverage record,
    which is why a checkoff survives a window and a rebuild.

    **WO-OPEN-THE-BOARD-01 · THE BOARD IS OPEN. THE ONLY BAR IS THE EGO'S OWN.** See
    `_own_entries`. Every other visual object on the board is a candidate, whatever it has
    been typed as and whoever has stood on its site — *"then we must learn what is
    reachable"*, which is a thing learned by going, not by filtering.

    **`included` IS GONE — WO-NAV-CLEANUP-01, ON CE'S RULING.** `WO-OPEN-THE-BOARD-01`
    stopped this function consuming the sweep's FIRM-`COUNTER`/`LEVER`/`EGO` filter and
    kept the parameter so the removal would be visible rather than silent, leaving the
    ruling to CE. The ruling is made: **a parameter that reads as live and is not is the
    same residue as a symbol nothing calls**, and it had begun to mislead — the caller's
    own comment still claimed the filter *"is the same call and cannot weaken"* while its
    result was being discarded.

    **THE FILTER IS UNTOUCHED.** `build_weave_sweep_list` still governs the CLICK arm
    through `select_weave_sweep_probe`; what this rung removes from the NAV arm is a
    per-frame computation whose result went nowhere. **The exclusion this function does
    perform is unchanged and is its own**: the ego's own visual objects, and nothing
    else."""
    own = _own_footprints(worldlines, ego)
    born = _newborn_footprints(worldlines)
    ranked = []
    for entry in master_object_list(cuts).entries:
        if any((a.node_index, entry.fingerprint[1]) in own for a in entry.trail):
            continue
        novel = any((a.node_index, entry.fingerprint[1]) in born for a in entry.trail)
        ranked.append((_order_key(entry, novel),
                       Target(entry.fingerprint, entry.trail[0].anchor)))
    ranked.sort(key=lambda pair: pair[0])
    return tuple(t for _k, t in ranked)


def _order_key(entry, novel: bool) -> Tuple[int, int, int, int]:
    """**R-3's ranking, as one lexicographic tuple over integers already on the record.**

    `(newly-appeared, footprint, class integer, first appearance)` — ascending throughout,
    and every term is a value the entry already carries. **No derivation, no weight, no
    score, no demotion, no rarity, no distance, no cap.**

    **THE DIRECTOR'S REASON IS THE ONE THAT GOES HERE:** *small rare things are usually
    important, so we start there.* **And it is not this build's invention.** v3.5 ran
    largest-first, recorded that it found nothing on a world it probed, reversed to
    smallest-first and recorded an unlock the old order had missed — falsified in one
    direction and confirmed in the other, in two code sites under a law of its own.
    `WO_RANK_AUDIT_00_RETURN` §5.1 has the citations. **PORT default: the burden of proof
    now sits on any other direction.**

    **THE NOVELTY BAND IS FIRST BECAUSE APPEARING IS ITSELF THE EVIDENCE.** A thing the
    world just produced is the freshest unexplained fact on the board; a thing that has
    been sitting there since the window opened will still be there next frame.

    **THE CLASS INTEGER IS A TIE-BREAK OF CONVENIENCE AND IS RULED AS ONE.** It is a fact
    about the harness's encoding, not about the object — it earns its place by being
    deterministic and carrying no threshold, and it says nothing else.
    `WO_RANK_AUDIT_00_RETURN` §2 put that distinction in front of CE before the ruling,
    and R-3 took it knowingly. It is read off `fingerprint[0]` — the recorded value — and
    **not off the attribute this module bans by name**, because filtering BY class is the
    model every prior generation built and the ban on that spelling stays.

    **AND THE BOTTOM OF THE KEY IS A TOTAL ORDER, NOT AN ARTEFACT.** Entries tying on all
    four terms cannot exist — two distinct fingerprints differ in class or in cells — but
    even the sort's stability rests on `collapse_fingerprints` returning
    `(class_id, sorted(cells))` ascending, **a documented total order over the entries.**
    That is the exact hazard `WO_RANK_AUDIT_00_RETURN` §5.2 measured in a prior generation,
    where an equal-scoring population fell through a stable sort to whatever order the
    scanner happened to emit. **Here there is nothing to fall through to.**"""
    return (0 if novel else 1, entry.cell_count, entry.fingerprint[0],
            entry.trail[0].node_index)


def coverage_state(context, key) -> str:
    """`ARRIVED`, `UNREACHABLE` or `UNTRIED` for one candidate — the three states the
    drive held in one set.

    **WO-TARGET-THE-OBJECT-01 · THE ARGUMENT IS THE VISUAL OBJECT'S KEY, NOT ITS ANCHOR.**
    R-1: coverage is a record of which OBJECTS have been worked. Two objects at one corner
    are two records, and an object that moves carries its own record with it.

    The order encodes the asymmetry: **`ARRIVED` is existential and permanent** (the ego
    stood on ground that target held, and nothing later unsays it), **`UNREACHABLE` is
    universal and provisional**, and **`UNTRIED` is the default and the only honest answer
    for a target whose budget ran out.** Lever, medium, ego, the medium's sub-class, the
    blocked transition — and now this. Only coverage claims take a ∀.

    **WO-NO-PREDICTION-01 · THE SECOND BRANCH IS NOW DEAD, DELIBERATELY.** Nothing writes
    `collide_drive_unreachable` any more: the ∀ it read was a deduction over the bearings
    observed so far, which is a prediction and not a coverage claim. **The branch stays so
    an evidence-fed producer needs no new state**, and until one is chartered this function
    returns `ARRIVED` or `UNTRIED`. **A dormant branch that says why it is dormant is
    honest; a deleted state that quietly stops being reachable is not.**"""
    if key in context.collide_drive_reached:
        return ARRIVED
    if key in context.collide_drive_unreachable:
        return UNREACHABLE
    return UNTRIED


def _standing_at(by_id, site: Site, ego: int) -> Optional[int]:
    """The worldline whose CURRENT footprint anchors at this site, or `None`.

    **WO-SEEK-THE-SMALLEST-01 · OFF THE DECISION PATH. NOTHING IN THE DRIVE CALLS THIS.**
    It was `_next_target`'s resolution and it assumed a static board: a candidate resolved
    only if some worldline's CURRENT anchor equalled the entry's FIRST-APPEARANCE anchor,
    and **nothing in a life makes a dead anchor current again**, so an entry that was not
    the object's newest moment was unresolvable for the rest of the run — silently, because
    a miss is a `None` the walk steps over. Selection now resolves by identity through
    `collide_plan.owner_ids`.

    **IT IS KEPT BECAUSE TWO COMMITTED DIAGNOSTICS MEASURE THE RULE IT IMPLEMENTS** —
    `_trace/ground_ab_00.py` and `_trace/ground_regression_00.py` both import it to ask
    what the anchor rule resolves to. Deleting it would take the instrument that reads the
    defect out with the defect. **Moving it to the diagnostics is owed and is CE's** — a
    re-pointing rung, not this one.

    **THE SITE IS THE TARGET; THE WORLDLINE IS ONLY HOW THE STEPPER REACHES IT.** The
    drive steps toward a footprint, and `_aim`, `arrived` and `_reach_state` all read one
    off a `Worldline` — so a site with nothing standing on it in this window cannot be
    pursued. **That is absence, not a skip:** the site is left on the list, uncontacted,
    and becomes pursuable again the moment something holds it.

    THE EGO EXCLUDES ITSELF, BY IDENTITY, HERE — the local guard `WO_SWEEP_FORK_01` put
    at the drive, kept beside the fingerprint bar in `_own_footprints` rather than replaced
    by it. **WO-NAV-CLEANUP-01 · this line said `_barred`, which does not exist.**
    `WO-OPEN-THE-BOARD-01` renamed `_barred_sites` and corrected the paragraph that
    DISCUSSES the replacement while missing this one — a phantom citation a reader or a
    work order would follow to nothing.
    Neither resolves the FIRM-`EGO` question, which stays open one stratum up."""
    for wid in sorted(by_id):
        if wid == ego:
            continue
        if _region_at_last(by_id[wid]).anchor == site:
            return wid
    return None


def _next_target(context, candidates: Sequence[Target], ego: int,
                 by_id) -> Tuple[Optional[Any], Optional[int]]:
    """The next VISUAL OBJECT's key, and the worldline that IS it.

    **WO-SEEK-THE-SMALLEST-01 · RE-DERIVED EVERY FRAME, FROM THE BOARD AS IT IS NOW.**
    The Director's rule: *hit a target, the objects are re-ranked, the next target is
    sought.* Three lines say it whole — take the candidates `visual_targets` produced this
    frame, drop everything the coverage record says is not `UNTRIED`, take the first that
    resolves. **A target on the board and not checked off is a candidate. There are no
    passes.**

    **THE CURSOR IS GONE, AND IT IS WHAT THE CANARY CAUGHT.** `collide_drive_offered`
    carried a set across frames and emptied only at a pass boundary, so a candidate a stale
    window had hidden stayed hidden until the pass ended. Measured live: after the cluster
    retired, the drive offered list position EIGHT — positions 2 through 7 passed over,
    including the one-cell object the Director was watching for at position 3. **Two
    targets in a 136-press life.** The cursor was ported from `click_traversal`'s full-pass
    rule, which is correct on a board that does not change; this one changes, and that is
    the premise of the campaign.

    **RESOLUTION IS BY IDENTITY, NOT BY A FROZEN ANCHOR.** `_standing_at` asked whether some
    worldline's CURRENT anchor equalled this entry's FIRST-APPEARANCE anchor — see that
    function, which is now off the decision path. `owner_ids` answers *which worldline IS
    this object* from the trail the weave already bound. An entry no worldline owns is
    skipped for THIS frame and stays on the list, uncontacted: there is no region to steer
    toward, and that is absence rather than a verdict.

    **THE EGO IS EXCLUDED BY IDENTITY, HERE, AS IT WAS BEFORE.** `_own_footprints` already
    bars the ego's own entries at the queue's derivation; this is the local guard
    `WO_SWEEP_FORK_01` put at the drive, kept rather than replaced.

    **NO RANKING, AND `_order_key` IS UNTOUCHED.** The order is the list's own — newly
    appeared, then smallest footprint, then lowest class, then first appearance. v3.5
    re-sorted on `(attempt_count ASC, distance ASC)`; the distance is a metric this build
    bans by name and the counter is the permanent demotion CE withdrew. **What changed is
    that selection stopped carrying state, not what the order is.**"""
    owners = owner_ids(by_id.values())
    for t in candidates:
        if coverage_state(context, t.key) != UNTRIED:
            continue
        wid = owners.get(t.key)
        if wid is not None and wid != ego:
            return t.key, wid
    return None, None


def _spent(context, unmoved: Optional[bool],
           offered: Sequence[Any]) -> Optional[str]:
    """Has this pursuit spent itself, and by WHICH of the two facts? `None` if not.

    **THE BOUND IS THE SIZE OF THE OFFERED SET AND IT IS NOT A CHOSEN NUMBER.** More
    unmoved observations at one place than there are actions to try means every direction
    has had at least one attempt and the position has yielded nothing. On a world offering
    four it is four; on a world offering three it is three. **Derived per frame, from the
    frame** — `available_actions` off the cut, never inferred from the bearing map.

    **WO-STUCK-IS-POSITIONAL-01 · IT COUNTED FRAMES, NOT STILLNESS, AND THE CAUSE WAS TWO
    CONSTANTS ALIASING.** This compared the ego's anchor against the previous frame's and
    reset when it changed — which is the rule as ruled. But the anchor came from
    `_aim(by_id[ego])`, read out of `context.weave_sweep_worldlines`, and
    `coverage_sweep.refresh_weave_roles` rebuilds that **only when its cadence is due**.
    Between refreshes the SAME worldline object is read, so the anchor is identical **by
    construction, whatever the ego did.** The recompute interval is one greater than the
    offered-action count on the embodied board, so the counter reached its bound on the
    last frame before the window would have refreshed — and **every pursuit died at exactly
    that number, never one more, never the budget, with nothing ever reached.** Measured at
    `8de275a`: an ego moving on every press, released as `STUCK` at press five.

    **THE FIX IS FRESHNESS, AND IT IS THE CAMPAIGN'S OWN LAW.** A press counts toward
    stillness only when it is measured against a NEW observation. Re-reading one window is
    **not evidence that the ego stayed put** — it is no evidence at all, and absence of
    evidence is not evidence of absence. `observed` is `(node_index, anchor)`: the node
    makes a re-read recognisable, the anchor is what stillness is about.

    **WHAT THIS COSTS, STATED RATHER THAN DISCOVERED.** Stillness can now only be
    established once per window refresh, so `STUCK` requires `len(offered)` refreshes of an
    unmoved ego. **The frame budget will therefore fire first on most pursuits, and that is
    correct**: `STUCK` means *this place defeated me*, which should be rare, and the budget
    means *I have spent enough here*, which should be common. **It also means the budget is
    now the binding bound and plans longer than it still cannot complete — the next
    constant to fall, and not this rung's.**

    **ABSENCE IS ABSENCE.** No observation, no anchor within it, or no offered set is
    answered with `None` rather than a stuck report — twice over now, since a stale re-read
    is itself an absence of new evidence.

    ORDER: budget first, because it was here first and is the wider net; stuck second, so a
    pursuit that is both is reported as the older fact. **Neither is a verdict.**"""
    if unmoved is None:
        return None
    if not unmoved:
        context.collide_drive_unmoved_reads = 0
        return None
    context.collide_drive_unmoved_reads += 1
    if offered and context.collide_drive_unmoved_reads > len(offered):
        return STUCK
    return None


def _unmoved(context, by_id, ego) -> Optional[bool]:
    """Is the ego's KNOWN footprint still on a FRESH frame? `None` when there is nothing
    to ask with.

    **STILLNESS IS PRESENCE, NOT POSITION — WO-BUDGET-OUT-01.** `WO_TWO_RESULTS_01` asked
    for a per-press reading of the ego's POSITION and Cowork halted: position needs
    identity, identity is a path through a window (`worldline.weave_window`), and one
    refresh costs ~6098 ms against ~10 ms for a fresh frame. **Presence needs no identity.**
    The ego's `RegionClay.fingerprint` is known from the cached window; `regions_at`
    scans ONE fresh frame and the question is only whether that exact fingerprint is
    still among them. `RegionClay`'s own docstring names that pair as the identity, and
    it is the same key `still_bridge` and `worldline_binding` build on. **The pair is
    read through the property and never spelled here**, so the drive names no world term
    — `test_collide_drive`'s fence bans one, rightly.

    **IT FAILS SAFE, BY CONSTRUCTION.** The fingerprint is up to one refresh stale and the
    frame is fresh, so occlusion, deformation, death or any staleness reads as ABSENT —
    *it moved* — and the caller RESETS the count. **Absence can only ever make `STUCK`
    harder to reach, never easier**, which is the only direction this build accepts. No
    threshold arbitrates it.

    **THE ONE FALSE POSITIVE, NAMED RATHER THAN DEFENDED AGAINST.** Another object of the
    SAME KIND occupying the ego's exact former cell set would read as present. Under a
    disjoint partition that is an exact coincidence — every cell, same class, same frame —
    and the defence against a coincidence would be a tuned number, which costs more than
    it buys. It is named here and nowhere guarded.

    **THE LOG IS ALREADY IN HAND.** `context.frame_record_log` is appended once per press
    at `virelai.py:360`, inside `choose_action` and ABOVE the sweep call — so the last
    record is THIS frame. No seam is widened and no argument is added.

    An absent log, an absent ego or an empty log is an absent PREMISE: `None`, which
    counts nothing and resets nothing. Absence rendered as absence."""
    w = by_id.get(ego)
    log = getattr(context, "frame_record_log", None)
    if w is None or log is None or not len(log):
        return None
    known = _region_at_last(w).fingerprint
    return any(g.fingerprint == known
               for g in regions_at(log, log.records[-1].node_index))


def _arrival(context, cuts, worldlines, egos) -> None:
    """Retire the held target if the ego took cells from it across the last edge.

    **EXTRACTED, NOT ADDED** — this rung's ratchet. The six lines stood inline in
    `drive_step`, which sat 13 lines from the bound while this rung added to its
    neighbourhood. The `except` is the committed one: `owner_edge` raises on a window it
    cannot bridge, and an arrival that cannot be read is not an arrival."""
    held = context.collide_drive_target
    if held is None or len(cuts) < 2:
        return
    try:
        if arrived(owner_edge(cuts[-2], cuts[-1], worldlines), egos, held):
            _pass_over(context, held, ARRIVED)          # reached — the transfer happened
    except Exception:
        pass


def _pass_over(context, target: int, outcome: str) -> None:
    """Retire a target from the queue and reset the frame budget.

    **EXTRACTED, NOT ADDED.** The three lines stood inline at two sites already — the
    arrival branch and the budget-expiry branch — and WO-REACHABLE-01 needs a third. One
    name for *this target leaves the queue* keeps the three reasons distinguishable at
    their call sites while the mechanism stays single.

    **WO-VISUAL-TARGETS-01 · WHAT IS RECORDED IS NOT THE WORLDLINE.** That is the whole
    checkoff change: the coverage record does not renumber. `collide_drive_outcome` still
    names the worldline, because it is a reading for the Director rather than a coverage
    claim.

    **WO-TARGET-THE-OBJECT-01 · AND WHAT IT RECORDS IS THE VISUAL OBJECT, NOT ITS CORNER.**
    R-1. The field still spells itself `..._target_site`; **what it holds is the object's
    immortal key.** Renaming it touches `collide_plan`, which this rung's fence does not
    open, so the name is left for CE and the return declares it. **The value is right and
    the label is one word short** — recorded here rather than left for a reader to trip on.

    A pursuit carrying no target records no coverage — **absence rendered as absence.** It
    cannot arise from `drive_step`, which sets both together; it can arise from a caller
    that sets the target directly, and silently adding `None` to the coverage record
    would tick off an object that does not exist."""
    key = context.collide_drive_target_site
    if key is not None and outcome == ARRIVED:
        context.collide_drive_reached.add(key)
    elif key is not None and outcome == UNREACHABLE:
        context.collide_drive_unreachable.add(key)
    # WO-COVERAGE-ROSTER-01 · **PURSUED, AND IT DID NOT ARRIVE** — written here and only
    # here, in the three lines that name the outcome, so the record and the retirement
    # cannot drift apart. Every non-arrival is one: the budget expiring, the anchor bound,
    # and the dormant verdict alike. **It is not the negation of `reached`** — a site can
    # be in both, and TOUCHED wins at the render rather than by a retraction here.
    if key is not None and outcome != ARRIVED:
        context.collide_drive_not_reached.add(key)
    context.collide_drive_outcome = (target, outcome)
    context.collide_drive_target = None
    context.collide_drive_target_site = None
    _release(context)


def _release(context) -> None:
    """Every reading that belongs to ONE PURSUIT, cleared — and to nothing else.

    **WO-SEEK-THE-SMALLEST-01 · EXTRACTED, NOT ADDED, AND THE EXTRACTION IS THE POINT.**
    A pursuit now ends two ways: it RETIRES with an outcome, or it YIELDS because the
    re-derived ranking named something better. The second writes no coverage — a yielded
    target is neither reached nor failed, it is deferred, and recording it would put a
    `NOT REACHED` against an object nothing was concluded about. **What the two share is
    exactly this reset**, and one name for it is what stops them drifting: a yield that
    forgot the plan would walk the old route toward the new target.

    `_pass_over` clears the target fields above this call because a retirement leaves the
    slot empty; a yield refills it on the same frame and must not.

    WO-HOLD-THE-PATH-01 · the plan belongs to the pursuit and leaves with it. A path
    outliving its target is the staleness the held plan is otherwise accused of.

    WO-CURSOR-AND-STUCK-01 · the anchor-press count belongs to the PURSUIT, not the life.
    A fresh target gets a fresh set of attempts from wherever the ego stands; the
    OBSERVATION itself is left alone, so a pursuit beginning where the last one ended is
    still measured against the same reading."""
    context.collide_drive_frames = 0
    context.collide_drive_trail = ()
    context.collide_drive_path = ()
    context.collide_drive_path_for = None
    context.collide_drive_walked_out = False
    context.collide_drive_unmoved_reads = 0


def step_progress(trail: Sequence[int]) -> str:
    """This frame's presses-remaining against the last, ORDINALLY. Fewer is closer.

    Two measurements are needed before anything can be said; with fewer the answer is
    `OPENING` rather than an invented zero."""
    if len(trail) < 2:
        return OPENING
    if trail[-1] < trail[-2]:
        return CLOSER
    return STALLED if trail[-1] == trail[-2] else RECEDING


def drive_step(context, cuts, node_actions, worldlines, verdicts,
               candidates: Sequence[int]) -> Optional[DriveStep]:
    """One frame of the drive: register arrival, choose a target, step toward it.

    Returns the step, or `None` when there is nothing to do — no ego typed, no measured
    map, no target left, or no measured bearing that closes the gap. **Every `None` is a
    stated absence the caller renders; none of them is an error.**

    ARRIVAL IS TESTED ON EXACTLY ONE EDGE — the two most recent cuts. `crossings()` walks
    the whole window and materialises `cell_owners` per node, which is the O(life²) cost
    `coverage_sweep`'s cadence gate exists to avoid; one `owner_edge` is 1/N of it and is
    the whole test.

    Non-fatal by construction, as `crossing.py` is: `cell_owners` RAISES on a cut that is
    not a disjoint partition, and **a drive must never be taken down by an accounting
    invariant it only consults.** An unaccountable edge registers no arrival — absence,
    not an exception."""
    ego = driving_worldline(verdicts)
    if ego is None:
        return None
    by_id = {w.id: w for w in worldlines}
    # WO-BLOCKED-RECORD-01 · the same call, BOUND rather than consumed inline. `bmap` and
    # the refusal record are two readings of ONE `EgoMap`, and reading it twice would be a
    # second read of the same window that could disagree with the first.
    ego_map = action_bearings(worldlines, node_actions,
                              _boundaries(cuts, node_actions, worldlines,
                                          verdicts)).get(ego)
    bmap = bearing_map(ego_map)
    if not bmap or ego not in by_id:
        return None
    # Reached only when `bmap` is non-empty, which requires `ego_map` — so this needs no
    # guard of its own, and adding one would state a doubt the line above has settled.
    refused = ego_map.transitions.refused
    # WO-BLOCKER-TAG-01 · THE BOARD CHANGED, SO EVERY REFUSAL REOPENS. `unreachable` is a
    # ∀ over the transitions refused so far, and the tags are what those refusals are
    # ABOUT. When the set of blocking fingerprints differs from the one the standing
    # verdicts were formed under, something that could have opened a path has happened —
    # a blocker moved, recoloured, grew, shrank, arrived or went — and every provisional
    # verdict is voided WHOLE. **No dependency graph and no per-target bookkeeping**: one
    # comparison, erring toward re-trying, which is the safe direction for a claim that is
    # never proven. `reached` is untouched, because it is existential and permanent.
    tags = blocking_tags(cuts, by_id, ego, bmap, refused)
    # WO-HOLD-THE-PATH-01 · BOUND, because it is now read twice: it voids the unreachable
    # verdicts below and it is the first of the held plan's three re-plan triggers.
    board_changed = tags != context.collide_drive_blockers
    if board_changed:
        context.collide_drive_unreachable = set()
        context.collide_drive_blockers = tags

    _arrival(context, cuts, worldlines, verdict_egos(verdicts))

    # WO-SEEK-THE-SMALLEST-01 · **SELECTION RE-DERIVES WHEN A PURSUIT ENDS, AND THE
    # TRIGGER IS THE EMPTY SLOT.** The Director's rule: *when a target is hit, the visual
    # objects are re-ranked and the next target is sought.* The cursor and its pass boundary
    # are still gone — a target passed over on one selection is a full candidate on the
    # next, and nothing about selection survives a frame.
    #
    # **AMENDMENT · THE HELD TARGET IS NOT PREEMPTED, AND THE MEASUREMENT IS WHY.** This
    # rung first re-ranked EVERY frame — a strictly stronger rule than the one ruled — and
    # `instruments/seek_01.py` measured what that costs: **125 of 173 holds lasted exactly
    # ONE frame.** `_order_key`'s first term is novelty, a board that mints objects mints
    # new firsts continuously, and every yield calls `_release`, which takes the plan with
    # it. **A pursuit that never survives a frame can never walk a route:** `_needs_plan`
    # re-plans every frame, `collide_drive_trail` never gets two readings, and
    # `step_progress` never leaves `OPENING`. Re-ranking at the hit is the ruled rule and it
    # needs no hysteresis, no minimum hold and no constant — the slot emptying IS the event.
    if context.collide_drive_target is None:
        # WO-VISUAL-TARGETS-01 · a coverage key and the worldline that IS it, set together.
        # **WO-TARGET-THE-OBJECT-01 · the key is the VISUAL OBJECT's, not a corner.**
        key, wid = _next_target(context, candidates, ego, by_id)
        context.collide_drive_target_site, context.collide_drive_target = key, wid
    elif context.collide_drive_target_site is not None:
        # **THE HELD KEY IS RE-RESOLVED, NOT RE-RANKED — AND THAT IS NOT PREEMPTION.**
        # `weave_window` renumbers worldline ids by first appearance WITHIN the window, so
        # the id held across a refresh can name a DIFFERENT object while the coverage key
        # still names the right one: `_arrival` would then test the transfer against the
        # wrong worldline and `_reach_state` would aim at its cells. The key is immortal and
        # the id is not. **The target does not change here** — only the id the same key
        # resolves to, through the same `owner_ids` selection uses. An id that resolves to
        # nothing this frame is left alone rather than cleared: absence is not a correction.
        # **It is separable from the amendment and CE can delete these three lines without
        # touching anything else.**
        _held = owner_ids(by_id.values()).get(context.collide_drive_target_site)
        if _held is not None:
            context.collide_drive_target = _held
    # WO-ARRIVE-01 · **THE QUEUE, NOT THE HELD TARGET — AND ALL OF IT, ON THIS FRAME.**
    #
    # `WO_ARRIVE_AUDIT_02` measured the defect and **none of it is the predicate.** The
    # state test already existed and is exact; it was asked of ONE already-selected target,
    # so a body covering three cluster members could check off at most one — **plurality
    # THREE on 120 of 120 covering frames, one slot, `Optional[int]`.** The other two stayed
    # `UNTRIED`, were re-offered on a later pass, and the cursor never left the cluster.
    #
    # **IT IS A RECORD, NOT A RETIREMENT, AND THAT IS THE WHOLE ECONOMY OF THE CHANGE.**
    # `collide_drive_reached` is existential and permanent; `coverage_state` reads it and
    # returns `ARRIVED`; `_unoffered` drops those from `untried`. Marking the covered set
    # here IS the cursor advancing past the cluster — no per-target bookkeeping, no second
    # queue, nothing to un-latch. And re-adding a key the set already holds is a no-op,
    # which is why a cadence re-reading one window is harmless HERE and phantom-fires for
    # the EVENT test: `WO_ARRIVE_AUDIT_02` measured that test firing 25 times for 21
    # arrivals, and a set cannot do that.
    #
    # **BELOW `_next_target`, DELIBERATELY — THE RETIREMENT PATH IS NOT TOUCHED.** Above it,
    # the held pursuit's own key would already read `ARRIVED` when `_unoffered` ran, the
    # pursuit would never form, and `WO-ALREADY-THERE-01`'s committed retirement — the
    # `path == ()` limb below, which asks `overlaps` of the same two sets through
    # `_reach_state` — would have nothing to retire. Measured: three of that rung's REDs
    # went red. Here the held target is selected and retires exactly as it does at the
    # anchor, and its siblings leave the queue beside it. Event and state stay two readings
    # of one fact, un-reconciled — `RULING_OBSERVERS_INTEGRATOR_v1` §1.
    # WO-EGO-FRESH-01 · **THE BODY IS READ FROM THE SETTLED FRAME, ONCE, BEFORE ANYTHING
    # IS ASKED OF IT.** One producer; the readers take it rather than each deriving its
    # own. `None` is NOT LOCATED — absence and ambiguity are the same answer — and the
    # frame says so on its own line rather than presenting the cached footprint as current.
    _fresh = fresh_body(by_id, ego, verdict_egos(verdicts),
                        getattr(context, "frame_record_log", None))
    context.collide_drive_reached |= standing_on(by_id, worldlines, ego,
                                                 verdict_egos(verdicts), candidates,
                                                 None if _fresh is None else _fresh[0])
    target = context.collide_drive_target
    if target is None or target not in by_id:
        return None
    # WO-EGO-FRESH-01 · **THE HELD PURSUIT RETIRES ON ITS OWN RECORD.** The line above marks
    # every queued object the body covers; if the held one is among them the pursuit is
    # over, and leaving it held would be the drive walking toward a place it has already
    # recorded arriving at. `_pass_over` is the committed retirement, untouched — this is a
    # third call site for it, not a fourth mechanism.
    if context.collide_drive_target_site in context.collide_drive_reached:
        _pass_over(context, target, ARRIVED)
        return None

    # WO-NO-PREDICTION-01 · THE REACHABILITY GATE IS DELETED, AND THIS IS A PORT.
    #
    # These three lines stood here:
    #
    #     if unreach:
    #         _pass_over(context, target, UNREACHABLE)   # off the lattice — before a press
    #         return None
    #
    # **THE DIRECTOR'S RULING: the reachability gate should not exist until proven. Trying
    # to predict what we can reach prevents us from getting there.** CE had ruled
    # *everything is touchable until a press proves otherwise* and then built a gate that
    # refused a target BEFORE any press, on arithmetic: no combination of the bearings
    # observed SO FAR, avoiding the transitions refused SO FAR, lands this footprint. That
    # reads *proven unreachable*; it means **my current model cannot find a route** — and
    # the refusal forecloses its own evidence, because being refused is what stops the ego
    # going somewhere new to learn the bearing that would have found one. Measured at
    # `48047df` on one window: **one observed bearing, and three of four candidate sites
    # retired with `frames=0` and `anchor_presses=0` — not one button pressed at any.**
    #
    # **AND THE GATE IS THIS ARCHITECTURE'S INVENTION, NOT ITS INHERITANCE.** v3.5 had
    # BOTH halves and kept them apart: `nav_atlas.nav_bfs_stride` returned `None` for *no
    # route found* and `nav_executor._plan_bfs_path` simply tried the next candidate — the
    # target stayed in `target_candidates` on every later replan — while
    # `nav_atlas.unreachable_targets` was written from ONE place, gated on `if moved: ...
    # else: _consec_blocked += 1`, which is presses that happened and changed nothing. v4
    # fused a planner's failure with an evidentiary record. **`PORT default, INVENT
    # justified`: the gate is the invention and it failed the way that discipline
    # predicts.** v3.5 had even found this failure mode once and fixed it — its
    # `blocked_classes` mode assumes unknown classes passable, *"the preferred mode for
    # early-game states where walkable_classes is sparse"*, a whitelist swapped for a
    # blacklist for exactly this reason. `reach`'s observed-bearing lattice is a whitelist.
    #
    # **WHAT DID NOT PORT, per CE's release:** v3.5's `_UNREACHABLE_THRESH = 5` is a tuned
    # constant, and its `unreachable_targets` cleared only at a level transition — permanent
    # within a level, the demotion defect this campaign has now rejected twice.
    #
    # **`reach`'s `None` is now the absence of a PLAN, which is what it always measured.**
    # The pursuit proceeds: `_next_press` returns `None` on an empty plan and the frame
    # falls through to `_toward`, whose basis line has said *"the search refused"* since
    # WO-HOLD-THE-PATH-01 — a branch that was written, wired and unreachable, because the
    # retirement returned two lines above it. The stuck rule and the budget are what make
    # this affordable and they are BELOW here, so an unreachable target now costs
    # `len(offered)` presses at one anchor instead of a verdict.
    #
    # **THE BLOCKED RECORD IS UNTOUCHED.** `refused` is still threaded into `reach` and
    # still avoided at expansion — a refusal is a MEASUREMENT and stays. What went is
    # `None` becoming a claim about the target.
    _no_verdict, remaining, path = _reach_state(by_id, ego, target, bmap, cuts, refused, verdict_egos(verdicts))

    # WO-ALREADY-THERE-01 · **STANDING ON IT IS ARRIVING, AND `()` IS NOT `None`.**
    # `reachable.py:199` returns `()` the instant `overlaps(ego_cells, (0,0), target_cells)`
    # holds — the BODY on a cell the target holds, which is arrival as a STATE. `None` is
    # *no combination lands this footprint* and must still fall through to the fallback;
    # `WO_LATTICE_MINE_00_RETURN` §7 found `cycle_probe.py:723` collapsing the two with
    # `if path is None or len(path) == 0`, so the empty tuple is tested distinctly here.
    #
    # **ABOVE THE INCREMENT, WHERE `_arrival` ALSO SITS.** An arrival by state counts its
    # presses exactly as an arrival by transfer does. Nothing new is computed: `path` was
    # bound two lines up and reaches `_next_press` uncollapsed below.
    if path == ():
        _pass_over(context, target, ARRIVED)
        return None
    context.collide_drive_frames += 1
    offered = tuple(cuts[-1].available_actions) if cuts else ()
    # WO-BUDGET-OUT-01 · PRESENCE ON A FRESH FRAME, NOT AN ANCHOR OFF A CACHED ONE.
    # `WO-STUCK-IS-POSITIONAL-01` keyed this on `(cuts[-1].node_index, anchor)` so a
    # re-read of one window was distinguishable from a fresh look — correct, and it made
    # stillness observable at most once per refresh, which put `STUCK` ~25 presses away
    # while the budget cut at 12. The budget is gone and the input is fresh every press.
    ending = _spent(context, _unmoved(context, by_id, ego),
                    offered) or (UNREACHABLE if walked_out(context) and _no_verdict else None)
    if ending is not None:
        _pass_over(context, target, ending)   # STUCK or UNREACHABLE — the note says which
        return None
    # The trail holds MEASURED ordinals only. A frame whose premises were absent adds
    # nothing rather than a placeholder, so absence stays absence and the comparison
    # below is always between two real readings.
    if remaining is not None:
        context.collide_drive_trail = tuple(context.collide_drive_trail) + (remaining,)

    ego_a, tgt_a = _aim(by_id[ego]), _aim(by_id[target])
    if ego_a is None or tgt_a is None:
        return None
    # WO-HOLD-THE-PATH-01 · THE PLAN FIRST, THE HILL-CLIMBER AS THE FALLBACK IT ALWAYS WAS.
    # `_toward` reads the raw signed gap with no memory of the previous frame, no knowledge
    # of walls and none of the lattice; it reverses whenever the ego overshoots a component
    # by a stride. It is correct at what it does and it was being used as the primary.
    pressed = _next_press(context, path, board_changed, offered)
    if pressed is not None:
        action, bearing = pressed
        source = (f"FROM THE HELD PATH ({len(context.collide_drive_path)} press"
                  f"{'' if len(context.collide_drive_path) == 1 else 'es'} left of the plan "
                  f"the search returned)")
    else:
        # WO-OBSTRUCTION-01 · THE RECORD REACHES THE ACTUATOR. `refused` was bound at the
        # head of this function and threaded into `reach`; the fallback — which made every
        # press of the measured run — could not see it. `ego_a` is the ego's live anchor and
        # is the site every refusal is keyed on, so both arguments were already in hand.
        chosen = _toward((tgt_a[0] - ego_a[0], tgt_a[1] - ego_a[1]), bmap, offered,
                         ego_a, refused)
        if chosen is None:
            return None
        action, bearing, stepped_off = chosen
        source = ("FROM THE FALLBACK STEPPER (no plan holds — the search refused, or its "
                  "next press was not offered this frame)" + _sidestep_str(
                      offered, ego_a, refused, action, stepped_off))
    return DriveStep(
        ego=ego, target=target, action=action, bearing=bearing,
        remaining=remaining, progress=step_progress(context.collide_drive_trail),
        basis=(f"ego ###{ego:03d} → ###{target:03d}: action {action} measured to bear "
               f"({bearing[0]:+d},{bearing[1]:+d}) {source} — frame "
               f"{context.collide_drive_frames}, "
               f"{len(context.collide_drive_reached)} reached, "
               f"{len(context.collide_drive_unreachable)} unreachable"
               # WO-EGO-FRESH-01 · a frame the settled grid could not answer for is SAID,
               # never silently substituted. The cached footprint is still read — the
               # ruling's fallback — and the reader can tell which one happened.
               + ("" if _fresh is not None else " · POSITION NOT FRESH")))


def _sidestep_str(offered, site, refused, chosen, stepped_off) -> str:
    """**THE DECISION, GRADED WITHOUT LEAVING THE LINE.** Names what this site has refused,
    and — when the chosen press is not one of the refused closers — the orthogonality that
    licensed it.

    **A READING, NOT A SECOND DERIVATION.** It re-reads the same two records the choice was
    made from and states what they hold; it takes no decision and no branch of the stepper
    depends on it. The refusal count is rendered on EVERY fallback press, not only on a
    sidestep, because `WO_NAV_LOOP_MINE_00_RETURN` §6 could not answer whether the record was
    populated at all — **a rung that consumes a record must expose it.**"""
    here = sorted((a for a in offered
                   if site is not None and (site, a) in (refused or ())), key=str)
    what = f"[{', '.join(str(a) for a in here)}]" if here else "(nothing refused here)"
    step = "" if stepped_off is None else (
        f" · SIDESTEP: {stepped_off} is refused here, so action {chosen} was taken on the "
        f"orthogonal bearing the record holds for it")
    return f" · refused here: {len(here)} {what}{step}"


def probe_record(context) -> str:
    """The pursuit, in one line: subject, the presses-remaining trail, and the
    last retirement by name.

    A READING, NOT A VERDICT. No seal consumes it and no belief is written from it; it
    exists so the Director grades a pursuit rather than a frame. Every absence states
    itself — no target, no measurement, no retirement yet are three different lines, and
    none of them is rendered as a zero."""
    target = context.collide_drive_target
    trail = tuple(context.collide_drive_trail)
    out = context.collide_drive_outcome
    last = (f"last: ###{out[0]:03d} {out[1]}" if out else "last: none retired yet")
    if target is None:
        return f"PROBE | no target held · {last}"
    if not trail:
        return f"PROBE | ###{target:03d} · presses-remaining: not measured yet · {last}"
    walk = " → ".join(str(n) for n in trail)
    return (f"PROBE | ###{target:03d} · presses-remaining {walk} · "
            f"{step_progress(trail)} · {last}")


def _consistent_str(ego_map) -> str:
    """The ∀ subset: actions with one agreed bearing, each with its coverage. `presses` is
    part of the claim (`ActionBearing`'s own docstring) and travels with it.

    **UNCHANGED — this is the line the note has always carried**, lifted out under its own
    name so the clean/contaminated distinction stays legible at a glance beside what
    WO-OBSERVED-RENDER-01 adds."""
    return " · ".join(f"{b.action}→({b.bearing[0]:+d},{b.bearing[1]:+d})×{b.presses}"
                      for b in ego_map.bearings)


def _planned_from_str(ego_map) -> str:
    """**THE ∃ SET, WHICH IS WHAT THE PLANNER ACTUALLY PLANS FROM.**

    `bearing_map` reads `EgoMap.observed`, unfiltered, and `reach` expands over every pair
    it holds — so every plan this drive has ever built came from THIS record. Until
    WO-OBSERVED-RENDER-01 nothing in the tree printed it. The note named which actions were
    contaminated (`consistency died: 1`) and never what they were contaminated WITH, so a
    second bearing could be a collapsed animation or a teleport and the reading was the
    same either way.

    **NO COUNT, AND THE TYPE IS WHY.** `ActionObserved` holds `bearings: FrozenSet` and its
    own docstring states the reason: *storing a set rather than a list makes how often
    structurally unavailable to every reader, so a majority rule, a modal bearing, or any
    other threshold wearing a statistic cannot be written against this field.* `×n` beside
    a ∀ claim is its coverage; there is no such number here and this renderer does not
    invent one.

    **IT RENDERS AND RULES NOTHING.** No filter, no dedup, no *this one looks like a
    teleport*. The values are the deliverable and the next rung is where they are read.

    **THE LENGTH IS BOUNDED BY THE BOARD, NOT BY A CAP.** One entry per action that ever
    moved, each carrying its distinct deltas — so the segment grows with the offered set
    and with how many ways a button has been seen to go, both facts about the world rather
    than choices. A cap would be the tuned constant this campaign has spent four rungs
    removing. The compact form keeps a four-action board inside one continuation, and
    `test_the_planned_from_segment_stays_bounded` measures it rather than asserting it."""
    return " · ".join(
        f"{o.action}→" + "/".join(f"({b[0]:+d},{b[1]:+d})" for b in sorted(o.bearings))
        for o in ego_map.observed)


def _boundaries(cuts, node_actions, worldlines, verdicts) -> FrozenSet[int]:
    """Every edge whose evidence is disregarded — the harness-marked life boundary, and the
    heart boundary it does not mark.

    **WO-HEART-DISREGARD-01 · ONE PRODUCER, TWO PREDICATES.** `action_roster` owns both and
    shares their atoms; this is the union, derived once so the drive's two readers cannot
    disagree about what a boundary is. The sealed-`COUNTER` set is read off the verdicts
    this seam already holds — `role_read` computes the same set from the panel nineteen
    lines before it calls `action_bearings`, so both sides of the tree name the same thing
    without a second producer of the seal.

    The coupling report is rebuilt here because the drive is not handed one. That is a pass
    over the window's edges, the same order of work `blocking_tags` already does per frame,
    and the alternative — threading a report through the caller — would put a `coupling`
    import in `coverage_sweep`'s seam for a diagnostic the drive can derive itself."""
    from virelai_v4.weave.coupling import build_coupling
    sealed = {wid for wid, rv in (verdicts or {}).items()
              if rv.role == COUNTER and rv.confidence == FIRM}
    if not sealed or not cuts:
        return life_boundary_edges(cuts)
    try:
        report = build_coupling(worldlines, cuts, node_actions)
    except Exception:
        return life_boundary_edges(cuts)        # a report that cannot be built disregards nothing
    return life_boundary_edges(cuts) | heart_boundary_edges(cuts, report, sealed,
                                                        worldlines)


def _map_str(ego_map) -> str:
    """The map, in two halves: what agreed, and what the planner may plan from.

    **`none` NOW MEANS NOTHING WAS OBSERVED, NOT *NOTHING AGREED* — WO-OBSERVED-RENDER-01
    AND THIS IS THE DEFECT IT CLOSES.** The guard read `if ego_map is None or not
    ego_map.bearings: return "none"`, so a map whose every action had been seen to move —
    but never twice the same way — printed `none` while `reach` was busy planning from it.
    **The note said the ego had no bearings at the exact moment it had too many.**

    Absence is rendered as absence at each half: no map at all is `none`; a map with no
    agreed bearing says so; a map with nothing observed says that instead of collapsing
    into the other."""
    if ego_map is None:
        return "none"
    agreed = _consistent_str(ego_map)
    planned = _planned_from_str(ego_map)
    if not agreed and not planned:
        return "none"
    return (f"{agreed or 'no action agreed with itself'}"
            f" ‖ planned from: {planned or 'nothing observed'}")


def _unmeasured_str(ego_map) -> str:
    """The actions that WERE observed and still produced no usable bearing, split the way
    `EgoMap` already splits them — `still` (pressed, no translation) and `inconsistent`
    (more than one bearing, so the ∀ died).

    **THE OFFERED SET IS IN SCOPE AGAIN AS OF WO-ABSENCE-TRUTH-01** — the caller now
    passes `cuts` and `_offered_cause` reads `NodeCut.available_actions` from the frame.
    This function is unchanged and still answers a DIFFERENT question, which is why it
    stands: an action the platform offered but nobody pressed explains nothing, while an
    action that WAS pressed and produced no bearing is exactly why the map is short. The
    paragraph that stood here said the offered set could not be reached from this seam;
    that was true of the call site, never of the data, and the call site was the defect."""
    if ego_map is None:
        return ""
    parts = []
    if ego_map.still:
        parts.append("observed but never moved it: "
                     + ", ".join(str(a) for a in ego_map.still))
    if ego_map.inconsistent:
        parts.append("observed with more than one bearing (consistency died): "
                     + ", ".join(str(a) for a in ego_map.inconsistent))
    return " · ".join(parts)


def _closers(delta: Tuple[float, float], bmap: Dict[Any, FrozenSet[Bearing]]) -> Tuple[Any, ...]:
    """The observed actions that WOULD close the gap on some axis if they were offered.

    **THIS IS THE DIAGNOSTIC SPLIT THE RUNG EXISTS FOR.** `_toward` filters candidates by
    `a in offered`; this asks the same sign question with that filter removed. So:

      * empty  → the map genuinely has nothing pointing the right way. **The map is short**
                 — the ego seal needs only two DISTINGUISHABLE bearings, so a worldline can
                 type `EGO` on a two-entry map and be unable to steer in four directions.
      * non-empty → the map HAS an answer and it was not available this frame. **The cause
                 is the offered set**, which is not in scope at this seam (see
                 `_unmeasured_str`) — and that is a THIRD cause, distinct from both a short
                 map and a diagonal gap whose fallback found nothing."""
    out = []
    for axis in _axis_order(delta):
        want = delta[axis]
        if want == 0:
            continue
        sign = 1 if want > 0 else -1
        out.extend(a for a, bs in bmap.items() if _qualifies(bs, axis, sign))
    return tuple(sorted(set(out), key=str))


def _offered_cause(closers: Sequence[Any], cuts) -> str:
    """The third cause, SPLIT BY WHAT THE FRAME ACTUALLY HELD — WO-ABSENCE-TRUTH-01.

    **THE LINE THIS REPLACES WAS FALSE ON A LIVE BOARD, AND IT WAS BELIEVED.** It read
    *THE MAP HAS AN ANSWER AND IT WAS NOT AVAILABLE … which actions the platform OFFERED
    this frame is not in scope at this seam* — a conclusion about availability, stated
    beside an admission that availability had not been looked at. On the embodied replay
    every action was offered on every frame and the note named three of them unavailable.
    CE read it, reasoned from it, and concluded the drive was blocked on the offered set.
    **A note that reports a cause it cannot measure is worse than silence, because it gets
    believed.**

    The offered set is not out of scope and never was — `NodeCut.available_actions` is on
    the cut, `drive_step` reads it on the line that chooses the action, and this seam had
    simply never been handed the cuts. Three answers, and each says which it is:

      * **NOT OFFERED** — measured, from the same cut the stepper read. The map had an
        answer and the platform did not offer it. This is what the old line asserted, and
        it is now asserted only when it is true.
      * **OFFERED** — measured, and it is a FINDING rather than an explanation: a closing
        action was available and the step still did not happen, so the refusal came from
        somewhere this seam does not look. **Named, not guessed at.**
      * **NOT MEASURED** — no cuts reached this call. The absence is stated as an absence
        and no claim about availability is made, which is what the old line should have
        said on its own evidence.

    No constant, no table, no inference from `EgoMap`: availability is read from the frame
    or it is not reported."""
    names = ", ".join(str(a) for a in closers)
    if not cuts:
        return (f"THE MAP HAS AN ANSWER AND THIS SEAM DID NOT SEE THE OFFERED SET: {names} "
                f"would close it. Whether the platform offered them this frame was NOT "
                f"MEASURED here — no cut reached this call — and no claim about "
                f"availability is made")
    offered = tuple(cuts[-1].available_actions)
    if not set(closers) & set(offered):
        return (f"THE MAP HAS AN ANSWER AND IT WAS NOT OFFERED: {names} would close it, "
                f"and the platform offered {', '.join(str(a) for a in offered) or 'nothing'} "
                f"this frame — measured from the cut, not inferred")
    return (f"THE MAP HAS AN ANSWER AND IT WAS OFFERED: {names} would close it and the "
            f"platform offered {', '.join(str(a) for a in offered)} this frame. **The "
            f"step was refused for a reason this seam did not measure** — the drive "
            f"returned before the stepper ran, or the target was retired and this note "
            f"describes the next one. Stated as a gap in the record, not as a cause")


# ---------------------------------------------------------------------------
# WO-COVERAGE-ROSTER-01 · THE COVERAGE ROSTER — every object, touched or not reached
#
# **IT LIVES HERE AND NOT IN THE DOSSIER, AND A FENCE DECIDED THAT.** It was written into
# `diagnostics/integration_roster.py` first — beside the three lists the Director already
# reads, which is where the charter put it. `test_roster_sever`'s import fence rejected it:
# that module may import `virelai_v4.capture.clay` **and nothing else**, so the diagnostic
# runs where the SDK and scipy are absent and so a `library/` read cannot creep back in
# through the renderer. The addition was reverted rather than the fence widened — a fence
# that rejects an addition is working — and the roster moved to the module that already
# owns `visual_targets` and `probe_record`, which keeps ONE producer of the queue.
#
# **THE COST, STATED:** the colour-name palette is that module's, so the roster names the
# raw `class_id` — the value the solver actually holds. `weave/` has no legal place for a
# render palette, and moving one here to buy a nicer line would be the firewall leaking in
# the direction that looks harmless.
# ---------------------------------------------------------------------------

TOUCHED = "TOUCHED"
NOT_REACHED = "NOT REACHED"
NEVER_ATTEMPTED = "NEVER ATTEMPTED"


def _source(context):
    """`(cuts, worldlines, verdicts, reached, not_reached, unreachable)` — **ONE LIFE'S
    RECORD, CHOSEN ONCE.**

    **WO-ROSTER-HOLD-01 · LIVE FIRST, AND ATOMICALLY.** Three paths end a run and only one
    of them clears anything:

      * **GAME_OVER** — `reset_for_new_life` fires from `choose_action` and empties every
        `PER_LIFE_SCRATCHPAD` field, so at `cleanup()` the live side is gone and the hold,
        captured immediately before that call, is the life's record.
      * **WIN** — no reset runs; the live fields are intact and are this life's.
      * **the harness stopping** (life cap, scorecard, budget, a terminated env) — likewise.

    Preferring the HOLD would be wrong on the last two, and worse with lives: a run whose
    second life ends by budget would render its FIRST life's roster while the second's sat
    in the live fields. Preferring LIVE is right on all three, because the only thing that
    empties the live side is the event that fills the hold.

    **AND THE CHOICE IS MADE ONCE, NOT PER FIELD — THIS RUNG'S OWN GUARD CAUGHT THAT.** A
    per-field fallback reads each name live-or-held independently, so a life that reached
    NOTHING has a legitimately empty `reached` and would have borrowed the previous life's,
    rendering `TOUCHED` for a site this life never touched while its failures came from the
    live side. **A roster is one life's record, not a mixture**, so the discriminator is
    asked once — of the window, which is what a life having run at all means — and every
    value comes from the same side of it.

    **ABSENCE SURVIVES.** Both sides empty is still both empty; the roster says *no queue*
    rather than inventing one. This narrows when that line appears; it does not remove it."""
    if getattr(context, "weave_sweep_cuts", None):
        return (context.weave_sweep_cuts,
                getattr(context, "weave_sweep_worldlines", None),
                getattr(context, "weave_sweep_verdicts", None),
                getattr(context, "collide_drive_reached", None),
                getattr(context, "collide_drive_not_reached", None),
                getattr(context, "collide_drive_unreachable", None))
    return (getattr(context, "coverage_hold_cuts", None),
            getattr(context, "coverage_hold_worldlines", None),
            getattr(context, "coverage_hold_verdicts", None),
            getattr(context, "coverage_hold_reached", None),
            getattr(context, "coverage_hold_not_reached", None),
            getattr(context, "coverage_hold_unreachable", None))


def _disposition(key, reached, not_reached) -> str:
    """One visual object's disposition, and **the precedence is the whole rule.**

    An object can be in BOTH records: worked, exhausted, and touched on a later pass. The
    arrival is existential and permanent; the failure is a thing that happened; neither
    retracts the other. So the READING resolves it, by precedence, rather than the drive
    editing its own history at the moment of arrival. **The same shape as `Transitions`'
    passable-wins: structural, with nothing to un-latch.**

    `UNREACHABLE` is not returned. It has no producer — `WO-NO-PREDICTION-01` left the
    state dormant deliberately and **the region rung is the producer it waits for.** It is
    rendered as an empty class rather than omitted: *nothing was proven unreachable* and
    *this solver cannot say* are different statements, and only the first is true."""
    if key in reached:
        return TOUCHED
    if key in not_reached:
        return NOT_REACHED
    return NEVER_ATTEMPTED


def _queued(context) -> Tuple[Target, ...]:
    """The queue, re-derived from the drive's own cached window — **`visual_targets`
    ITSELF, not a second walk of the master list.**

    A roster that computed its own queue could reconcile perfectly against a population
    the drive never worked. `weave_sweep_cuts` / `_worldlines` / `_verdicts` are what the
    drive was handed on its last frame, so this is the same call with the same inputs.

    **THE COST, STATED RATHER THAN DISCOVERED:** it is the LAST cached window, so an
    object that appeared and left earlier in the life is not in it. A divergence of that
    kind surfaces as a reconciliation failure, which is why the sum is asserted rather
    than trusted."""
    cuts, worldlines, verdicts, _r, _n, _u = _source(context)
    if not cuts:
        return ()
    # WO-ROLE-MASK-01 · the roster grades the queue the drive worked, so it masks by the
    # same call. `masked_worldlines` subsumes `driving_worldline` — the ego is one of the
    # ids it returns — and reading the role channel twice would be two producers of one
    # subtraction.
    return visual_targets(cuts, worldlines or [], masked_worldlines(verdicts or {}))


def coverage_roster(context) -> str:
    """**EVERY VISUAL OBJECT THE DRIVE WAS OFFERED, AND WHAT BECAME OF IT.**

    The Director's statement of the probe: *a list of visual objects; each has a cell-site
    footprint; that footprint becomes the target; we try to get to every target cell site,
    and we either get there and observe what happened, or we learn it is not reachable.*
    Four of the five were built — the list is `visual_targets`, the site is the key, the
    lattice is `reach`, arrival is `arrived`. **This is the fifth: the record of what was
    ATTEMPTED**, which had nowhere to be written and therefore nowhere to be read. On a
    click world the action list is that proof; on an embodied world the Director was
    watching a replay and inferring intent.

    **PER LIFE, AND THE HEADER SAYS SO.** Every field read here is `PER_LIFE_SCRATCHPAD`,
    so a run of several lives yields a roster per life. That is correct — the board changes
    across lives — and it is stated rather than left for a reader to assume cumulative.

    **IT REPORTS THE QUEUE AS DERIVED AND CORRECTS NOTHING** — no dedup, no filter, no
    shortening. If the queue is wrong, showing that is the job.

    **A READING, NOT A VERDICT**, exactly as `probe_record` is: no seal consumes it, no
    belief is written from it, and every absence states itself."""
    _cuts, _w, _v, _reached, _failed, _unreach = _source(context)
    queue = _queued(context)
    reached, failed, unreach = set(_reached or ()), set(_failed or ()), set(_unreach or ())
    out = ["########## COVERAGE ROSTER · THIS LIFE ONLY ##########"]
    if not queue:
        out.append("  no queue — the drive was handed no cached window this life, so there "
                   "is no list to grade. Absence, not an empty board.")
        out.append("########## END COVERAGE ROSTER ##########")
        return "\n".join(out)
    tally = {TOUCHED: 0, NOT_REACHED: 0, NEVER_ATTEMPTED: 0}
    # WO-TARGET-THE-OBJECT-01 · the position is printed because **the order IS the rung**,
    # and it is produced with `range` rather than the obvious builtin: `test_probe_record`'s
    # whole-module metric fence bans the substring `rate`, which `enumerate` contains.
    # **The fence is obeyed rather than widened** — this rung carries no ruling over it, and
    # it is the eighth false positive of that class this campaign has absorbed rather than
    # relaxed.
    for n in range(len(queue)):
        t = queue[n]
        state = _disposition(t.key, reached, failed)
        tally[state] += 1
        cells = len(t.key[1])
        extent = f"{cells} cell{'' if cells == 1 else 's'}"
        late = "  (reached on a later pass)" if state == TOUCHED and t.key in failed else ""
        out.append(f"  #{n}  {t.site}  class {t.key[0]}  {extent}  →  {state}{late}")
    out.append("")
    out.append(f"  TOUCHED         {tally[TOUCHED]}")
    out.append(f"  NOT REACHED     {tally[NOT_REACHED]}")
    out.append(f"  NEVER ATTEMPTED {tally[NEVER_ATTEMPTED]}")
    # **STATED EMPTY, NOT OMITTED — AND THE PARENTHETICAL WAS STALE, CORRECTED HERE BY
    # WO-GROUND-01.** It read *"dormant — no producer until the region is built"*, which
    # was true when written and stopped being true at `WO-OUT-OF-REACH-01`: `_pass_over`
    # writes `UNREACHABLE` when a walked-out plan ends with no verdict, and that limb
    # fires. A zero here is now an observation about this life, not an absent producer —
    # the opposite reading from the one the old text invited.
    out.append(f"  UNREACHABLE     {len(unreach & {t.key for t in queue})}   "
               f"(a producer exists since WO-OUT-OF-REACH-01; zero is an observation)")
    out.append(f"  queued          {len(queue)}   "
               f"(ranked: newly-appeared, then smallest footprint, then lowest class)")
    # WO-GROUND-01 · **LOUDLY IGNORED.** What the ground mask took out of the queue is
    # printed here with its basis, because `_queued` is the same derivation the drive
    # worked and masking alone would delete these from the record as well as the list.
    out.extend(ground_block(_cuts, _w, _v, masked_worldlines(_v or {})))
    out.append("########## END COVERAGE ROSTER ##########")
    return "\n".join(out)


def coverage_reconciles(context) -> bool:
    """**queued == touched + not-reached + never-attempted.** Asserted, not eyeballed.

    Every queued site takes exactly one disposition, so the three classes partition the
    queue and their sum is its size. **A failure here is a finding about the LIST, not a
    rendering bug** — it would mean the queue re-derived at render time is not the
    population the drive worked, and that outranks the roster."""
    queue = _queued(context)
    _c, _w, _v, _reached, _failed, _u = _source(context)
    reached, failed = set(_reached or ()), set(_failed or ())
    # **WRITTEN AS A PARTITION, AND A FENCE IS WHY IT IS THE BETTER CHECK.** This read
    # `sum(seen.count(k) for k in (...)) == len(queue)`; `test_collide_drive`'s whole-module
    # ban on `.count(` — *no statistic reaches the ∃ seam* — rejected it. The ban is right
    # even though this tally feeds no belief, and the rewrite is stronger than what it
    # replaced: sizes summing could be satisfied by a double-count plus an omission, and
    # asserting the UNION as well cannot be.
    by_state = {TOUCHED: set(), NOT_REACHED: set(), NEVER_ATTEMPTED: set()}
    for t in queue:
        by_state[_disposition(t.key, reached, failed)].add(t.key)
    covered = set()
    for members in by_state.values():
        covered |= members
    return sum(len(m) for m in by_state.values()) == len(queue) == len(covered)


__all__ = [
    "STUCK",
    "probe_record", "step_progress", "coverage_roster", "coverage_reconciles",
    "TOUCHED", "NOT_REACHED", "NEVER_ATTEMPTED",
    "ARRIVED", "UNREACHABLE",
    "CLOSER", "STALLED", "RECEDING", "OPENING",
    "DriveStep",
    "arrived",
    "bearing_map",
    "drive_step",
    "driving_worldline",
]
