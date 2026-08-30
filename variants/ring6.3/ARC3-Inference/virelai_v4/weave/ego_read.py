"""WO-EGO-01 · THE ACTION→BEARING MAP, LEARNED FROM THE RECORD AND NOTHING ELSE.

CANON: **ego is action-covariance, nothing else.** `RULING_EGO_WORLDLINE_v1` — *ego is any
worldline that moves as the direct result of an action button; multi-ego by definition,
determined at the worldline level, never by footprint.*

THE OBSERVABLE, stated over evidence the weave already holds:

    ∀ presses of action `a`, this worldline's bearing is the same        (consistency)
    and it does not move the SAME way under every observed action        (covariance)

**SELF-CONTAINED — IT NEVER ASKS WHICH BUTTON IS "UP".** Only that a button is consistent
and that buttons are distinguishable. That is the whole difference from the prior art.
`library/ego_detector.py` hardcodes `_EXPECTED_DIRECTION = {1:(-1,0), 2:(1,0), …}` and
DISCARDS any observation whose sign disagrees, so a world with a different control scheme
produces **silence rather than a counterexample** — the detector cannot fail loudly, it
simply finds no ego. This rule detects that world. It is strictly stronger and it needs no
table (`WO_EGO_MINE_00_RETURN` §3.1).

**NOTHING IS COMPLETED.** Legacy's `stride_probe._commit_action_dirs` fills unobserved
cardinals from a canonical table scaled by the observed stride, and hands them downstream
indistinguishable from observed entries. An action never pressed has NO entry here — not a
zero, not a guess, not an inference from its opposite. Absence is rendered as absence
(§3.2 of the same return).

THE SECOND CONJUNCT IS THE RATIFIED CHANNEL LAW, NOT AN INVENTED RULE.
`SPEC_PIXEL_ARITHMETIC_v1` §3 names four exclusive answers to "what does this worldline's
arithmetic key on": WHICH action, THAT-ANY action, another worldline's arithmetic, or
nothing. **A worldline whose bearing is identical under every observed action keys on
THAT-ANY action — a schedule, channel (b) — not on WHICH action, channel (a).** It is
therefore not an ego, and the exclusion is by construction rather than by a bar. With a
single observed action the question is unaskable and the claim travels coverage-bounded
instead, exactly as the two marginal seals carry their denominators.

THE KEYING, and it is this rung's one indexing risk — resolved by node, never by index.
`Worldline.edges[i]` spans `steps[i][0] → steps[i+1][0]` and `len(edges) == len(steps)-1`,
an invariant `rejoin._merge` preserves by inserting a bridge edge. **The edge series is NOT
index-parallel to the dense press series** — a worldline born late, or absent at a node,
has fewer edges than there are presses. So the action is read at the edge's RIGHT node,
`node_actions[steps[i+1][0]]`, which is `action_roster.action_node_indices`' stated index
rule and the same convention `role_read._acted_by_press` uses: *a record for node t carries
the action that produced t*. The re-join bridge is a `DEFORM` with `delta=None` and can
never masquerade as a bearing.

A NULL PRESS IS AN OBSERVATION, NOT AN ABSENCE. A press under which this worldline did not
translate is recorded on the map and **cannot retract an accumulated bearing** — the lesson
the lever campaign paid six rungs for, and the one thing legacy's ego path already gets
right (its `detect_ego` returns empty on a null frame and the caller's ratchet preserves
prior state). It is kept distinct from a press never made.

════════════════════════════════════════════════════════════════════════════════════════
AND THE NULL PRESS NOW KEEPS THE SITE IT WAS MADE FROM — WO-BLOCKED-RECORD-01.

*Action 2 did not move it* is a fact about a button. **Action 2 does not move it FROM
HERE** is a fact about the world, and it is the one a search can use. The site was in
scope the whole time: this module reads the action at `steps[i + 1][0]` and the ego stood
at `steps[i][1]` when the button went down. **One index, and the wall becomes learnable.**

`Transitions` is that record, and it is not a second opinion about anything this module
already decided — `bearings`, `still`, `inconsistent` and `observed` are byte-identical,
and every seal built on them is untouched. It is a fifth field, on the precedent
`WO_EGO_OBSERVED_01` set: the evidence was being computed and thrown away.

Pure and stdlib-only. Reads the verb stream and the action stream it is handed; computes
nothing else, writes nothing, and decides nothing about any other tag.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, NamedTuple, Optional, Sequence, Tuple

from virelai_v4.weave.edge import Verb

Bearing = Tuple[int, int]
Site = Tuple[int, int]
Transition = Tuple[Site, Any]           # (the anchor pressed FROM, the action pressed)


class ActionBearing(NamedTuple):
    """One observed action and the single bearing it produced, with its coverage.

    `presses` is how many translations were observed under this action — part of the
    claim, never converted into a score. Confidence is coverage."""
    action: Any
    bearing: Bearing
    presses: int


class ActionObserved(NamedTuple):
    """Every DISTINCT bearing one action was seen to produce, and nothing else.

    **NO COUNT LIVES HERE, AND THAT IS THE POINT.** `ActionBearing` carries `presses`
    because a ∀ claim must travel with its coverage. This record answers a different
    question — *has this button EVER gone that way* — which is a ∃ and takes no number at
    all. Storing a set rather than a list makes *how often* structurally unavailable to
    every reader, so a majority rule, a modal bearing, or any other threshold wearing a
    statistic **cannot be written against this field**. The ban is enforced by the shape,
    not by a reviewer."""
    action: Any
    bearings: FrozenSet[Bearing]


# THE FRAME PROVES NON-MOTION, AND ONLY THESE TWO VERBS PROVE IT. `edge.Verb` defines
# STILL as *same footprint, same class* and RECOLOR as *same footprint, class changed* —
# both are the frame saying THE SAME CELLS, which is the whole content of *it did not
# move*. Every other verb the `still` list absorbs fails to establish it: GROW and SHRINK
# change the footprint and may move the anchor with it; DEFORM has no licensed verb at
# all, and the re-join BRIDGE is a synthetic DEFORM spanning a discontinuity, so reading
# a refusal from one would state that the ego held a site it demonstrably left; BIRTH and
# DEATH have an absent endpoint and therefore no site to key on.
#
# **`still` IS NOT NARROWED — IT IS UNTOUCHED.** This is a SECOND, stricter reading of
# the same edges, and the two answer different questions: `still` asks *did this press
# produce a bearing* (and a non-bearing is any of nine verbs); the record asks *did this
# press leave the ego where it was* (and only two verbs answer yes). A refusal is a
# positive claim that prunes a search — the safe direction for it is to under-record,
# which is the same reasoning `reachable`'s header gives for its permissive bound.
_HELD = frozenset({Verb.STILL, Verb.RECOLOR})

# WO-NAV-CLEANUP-01 · THE THREE STATE NAMES AND `transition_state` ARE RETIRED, AND THE
# RECORD THEY NAMED IS UNTOUCHED.
#
# They were built so *a reader and a test can say which of the three they mean*. **No
# reader ever came.** `WO_NAV_SWEEP_00_RETURN` §2 swept every reference in the tree: the
# function had one production reader — none — and the two names it returned were read by
# nothing but itself. The consumer that exists reads `Transitions.refused` as a SET, at
# `reach`'s expansion, and never asks the three-way question.
#
# **WHAT STAYS, AND WHY THIS IS NOT A WEAKENING.** `Transitions` keeps both frozensets and
# both docstrings; `passable` remains live and acts by SUBTRACTION at `_transitions`'
# construction — the reopening is structural and nothing about it moves here. The third
# state is still rendered as absence, which is what a `(site, action)` in neither set has
# always been. **A vocabulary for a question nothing asks is not a spare part.**
#
# **RULING EXTENDED BY ONE SYMBOL, DECLARED RATHER THAN TAKEN.** CE named `transition_state`,
# `PASSABLE` and `REFUSED`. `UNTRIED` is the third name of the same three-line block and
# `transition_state`'s only other reader; retiring two thirds of a vocabulary and leaving
# the last third would be residue created by the rung that came to remove it. **This is
# `ego_read.UNTRIED` only** — `collide_drive.UNTRIED` is a different constant, live, and
# untouched.


class Transitions(NamedTuple):
    """Which `(site, action)` presses moved the ego, and which held it where it was.

    **THE ASYMMETRY IS THE WHOLE TYPE, AND IT IS THIS BUILD'S FIFTH INSTANCE.**

        `passable` is EXISTENTIAL and permanent — *I moved from here under this button,
        once.* A later press that fails says the world changed, not that the press never
        succeeded. Nothing subtracts from it.

        `refused` is UNIVERSAL and provisional — *every press I have made from this site
        under this button held me.* It is `INERT` for a transition: never proven, only
        unfalsified so far, coverage-bounded, and **killed outright by one press that
        moves.** Lever, medium, ego and the medium's sub-class carry the same shape.

    **PASSABLE-WINS IS STRUCTURAL, NOT PROCEDURAL.** `_transitions` subtracts `passable`
    from the refusals before constructing, so the reopening has no un-latching step to
    forget, no flag to clear and no trigger to fire. **A success does not retract a
    refusal; it makes the refusal unconstructible.** That is why this record needs no
    world-state identifier: `PassabilityMap.update_world_state` reaches for one because it
    CACHES across frames, and this record is rebuilt from the window's own edges every
    time `action_bearings` runs.

    ABSENCE IS RENDERED AS ABSENCE, AND IT IS THE THIRD STATE. A `(site, action)` in
    neither set was never pressed. It is `UNTRIED`, it is distinguishable from both, and
    a search must enter it — *everything is touchable until proven otherwise* is exactly
    the rule that a two-state map cannot state."""
    passable: FrozenSet[Transition]
    refused: FrozenSet[Transition]


NO_TRANSITIONS = Transitions(passable=frozenset(), refused=frozenset())


class EgoMap(NamedTuple):
    """Everything the record says about one worldline's response to the action buttons.

    `bearings`      — observed actions and their agreed bearing, ascending. OBSERVED ONLY.
    `still`         — actions under which a press produced no translation. An observation,
                      recorded so it is distinguishable from a press never made.
    `inconsistent`  — actions that produced more than one bearing. One disagreement is
                      enough to kill the consistency conjunct, which is a ∀.
    `observed`      — every action that ever produced a translation with EVERY distinct
                      bearing it produced, unfiltered, **including the actions that also
                      appear in `inconsistent`.** See below.

    **TWO QUESTIONS, ONE ∀ — `WO_EGO_OBSERVED_01` §0.1.** The SEAL asks whether this
    worldline's response depends on WHICH button. That is a permanent role claim, so it is
    a ∀: one counterexample kills it, and `bearings` is the filtered evidence it stands on.
    A PLAN asks where a button probably goes. That is re-derived every frame and feeds a
    loop that re-plans on the next observation, so it is a ∃, and gating it on the ∀ built
    for the role claim is a category error.

    `_observe` computed the ∃ evidence all along and threw it away — `seen[a]` held every
    bearing for every action and only the consistent ones survived. `observed` is that
    record kept rather than discarded. **It is additive: `bearings`, `still` and
    `inconsistent` are byte-identical to what they were, and so is every seal built on
    them.**

    ABSENCE IS STILL RENDERED AS ABSENCE. `observed` holds only actions that produced a
    translation. An action pressed with no motion appears in `still` and NOT here; an
    action never pressed appears in neither.

    `transitions`   — the same presses keyed on the SITE they were made from, so *action
                      2 did not move it* becomes *action 2 does not move it FROM here*.
                      See `Transitions`. **ADDITIVE, on the precedent `observed` set:
                      `bearings`, `still` and `inconsistent` are byte-identical to what
                      they were, every seal built on them is untouched, and the field is
                      defaulted so every existing construction site keeps working.**
    """
    bearings: Tuple[ActionBearing, ...]
    still: Tuple[Any, ...]
    inconsistent: Tuple[Any, ...]
    observed: Tuple[ActionObserved, ...] = ()
    transitions: Transitions = NO_TRANSITIONS


def _action_at(node_actions: Sequence[Any], node_index: int) -> Optional[Any]:
    """The action that PRODUCED `node_index`, or `None` if there is none to read.

    The wiring law, applied at the edge's right node. Out-of-range is `None` rather than
    an error: a window may legitimately end before the action series does."""
    if not (0 <= node_index < len(node_actions)):
        return None
    aid, _target = node_actions[node_index]
    return aid


def _observed(seen: Dict[Any, List[Bearing]]) -> Tuple[ActionObserved, ...]:
    """The ∃ record: every action that moved this worldline, with every distinct bearing
    it was seen to produce. Same ordering key as `bearings` and `inconsistent`, so the
    three read in one order.

    **EXTRACTED RATHER THAN INTERLEAVED.** `_observe`'s single responsibility is walking
    the edges into `seen`; folding that record a third way is a second thing, so it is a
    second function that `_observe` calls."""
    return tuple(ActionObserved(action=a, bearings=frozenset(v))
                 for a, v in sorted(seen.items(), key=lambda kv: str(kv[0])))


def _transitions(wl, node_actions, boundaries=frozenset()) -> Transitions:
    """The presses this worldline was present for, keyed on the SITE THEY WERE MADE FROM.

    **THE SITE IS ONE INDEX AWAY FROM THE ACTION, AND IT WAS BEING DISCARDED.** `_observe`
    reads the action at the edge's RIGHT node — `steps[i + 1][0]`, the wiring law — while
    the ego's footprint BEFORE that press is `steps[i][1]`, in scope on the same
    iteration. `WO_BLOCKED_MINE_00_RETURN` found V1 and V3 both keying this record on a
    rounded centroid (`phase_handlers.py:4389`) and flagged it as the one line not to
    port. **There is no centroid here to round:** `RegionClay.anchor` is `min(row),
    min(col)` over the cell set (`capture/clay.py:_anchor`) — geometry, integer, exact.

    **A SEPARATE WALK, DELIBERATELY.** `_observe`'s single responsibility is folding the
    edges into `seen`; sorting the same edges by site is a second thing, so it is a second
    function that `_observe` calls — the same extraction `_observed` made, and the ratchet
    rule that new logic is never interleaved into an existing body.

    A worldline whose region holds no cells anchors at the `(-1, -1)` sentinel
    `_anchor` returns; a refusal keyed there is inert rather than special-cased, because
    no in-bounds search ever generates that site."""
    passable, refused = set(), set()
    for i, e in enumerate(wl.edges):
        # WO-RESPAWN-DISREGARD-01 · **A DEATH IS NOT EVIDENCE ABOUT A BUTTON.** An edge
        # that crosses a life boundary carries a real displacement the ego did not walk:
        # it died, and the world put it back at spawn. Constructed proof, not argument —
        # one such edge EMPTIES this action's consistent bearing, adds a permanent member
        # to the existential set the planner draws from, and (worst, and never checked
        # until `WO_RESPAWN_AUDIT_00`) writes the cell it died FROM into `passable`, where
        # the subtraction below then makes a genuine refusal there unconstructible.
        #
        # **DISREGARDED, NOT SEVERED.** The worldline still spans the boundary — the
        # Director's ruling, and Groundhog Day depends on it. What stops is the READING of
        # this edge as evidence. `continue` rather than a branch into `refused`: the press
        # is evidence that the button moves the ego out of that cell AND evidence that it
        # does not. **Absence, not a refusal.**
        if wl.steps[i + 1][0] in boundaries:
            continue
        aid = _action_at(node_actions, wl.steps[i + 1][0])
        if aid is None:
            continue                                    # no action to attribute it to
        site = wl.steps[i][1].anchor                    # where it stood BEFORE the press
        if e.verb is Verb.MOVE and e.delta is not None:
            passable.add((site, aid))
        elif e.verb in _HELD:
            refused.add((site, aid))                    # the frame: the same cells
    return Transitions(passable=frozenset(passable),
                       refused=frozenset(refused) - frozenset(passable))


def _observe(wl, node_actions, boundaries=frozenset()) -> EgoMap:
    """One worldline's action→bearing record, read from its own verb stream.

    Walks the edges rather than the presses, because the edges are what carry a bearing
    and what the worldline was actually present for."""
    seen: Dict[Any, List[Bearing]] = {}
    still: List[Any] = []
    for i, e in enumerate(wl.edges):
        # WO-RESPAWN-DISREGARD-01 · **A DEATH IS NOT EVIDENCE ABOUT A BUTTON.** An edge
        # that crosses a life boundary carries a real displacement the ego did not walk:
        # it died, and the world put it back at spawn. Constructed proof, not argument —
        # one such edge EMPTIES this action's consistent bearing, adds a permanent member
        # to the existential set the planner draws from, and (worst, and never checked
        # until `WO_RESPAWN_AUDIT_00`) writes the cell it died FROM into `passable`, where
        # the subtraction below then makes a genuine refusal there unconstructible.
        #
        # **DISREGARDED, NOT SEVERED.** The worldline still spans the boundary — the
        # Director's ruling, and Groundhog Day depends on it. What stops is the READING of
        # this edge as evidence. `continue` rather than a branch into `refused`: the press
        # is evidence that the button moves the ego out of that cell AND evidence that it
        # does not. **Absence, not a refusal.**
        if wl.steps[i + 1][0] in boundaries:
            continue
        aid = _action_at(node_actions, wl.steps[i + 1][0])
        if aid is None:
            continue                                    # no action to attribute it to
        if e.verb is Verb.MOVE and e.delta is not None:
            seen.setdefault(aid, []).append(tuple(e.delta))
        else:
            still.append(aid)                           # observed, and not a bearing
    bearings = tuple(
        ActionBearing(action=a, bearing=v[0], presses=len(v))
        for a, v in sorted(seen.items(), key=lambda kv: str(kv[0]))
        if len(set(v)) == 1)
    inconsistent = tuple(
        a for a, v in sorted(seen.items(), key=lambda kv: str(kv[0])) if len(set(v)) > 1)
    return EgoMap(bearings=bearings,
                  still=tuple(sorted(set(still), key=str)),
                  inconsistent=inconsistent,
                  observed=_observed(seen),
                  transitions=_transitions(wl, node_actions, boundaries))


def action_bearings(worldlines, node_actions,
                    boundaries=frozenset()) -> Dict[int, EgoMap]:
    """`{worldline_id: EgoMap}` for every worldline that produced at least one
    observation — a translation or a null press — under some action.

    A worldline with nothing to say is absent from the mapping rather than present with an
    empty record, so a caller cannot mistake "never observed" for "observed and silent".

    **THE EMPTINESS TEST NEEDED NO CHANGE WHEN `observed` ARRIVED, AND THAT IS PROVED
    RATHER THAN ASSUMED.** `observed` is non-empty exactly when `seen` is, and every
    action in `seen` produced at least one bearing, so it landed in `bearings` or in
    `inconsistent`. The three-way test therefore already covers the fourth field.

    **AND IT NEEDED NO CHANGE WHEN `transitions` ARRIVED EITHER, ON THE SAME PROOF.** A
    non-empty `passable` requires a MOVE carrying a delta, which put its action in `seen`
    and therefore into `bearings` or `inconsistent`; a non-empty `refused` requires an
    edge that is not that MOVE, which appended to `still`. **Neither side can be non-empty
    while all three tested fields are empty**, so the test covers the fifth field too —
    proved, not assumed, because assuming it is how a field arrives that nobody reaches."""
    out: Dict[int, EgoMap] = {}
    for wl in worldlines:
        m = _observe(wl, node_actions, boundaries)
        if m.bearings or m.still or m.inconsistent:
            out[wl.id] = m
    return out


def ego_witness(m: EgoMap):
    """The press that earned the seal: an action, and one bearing it produced.

    Deterministic and cited rather than implied — `observed` is already ordered by action
    and the bearings are ordered here, so two readers name the same witness. `None` when
    nothing ever moved this worldline under any button."""
    for ao in m.observed:
        for b in sorted(ao.bearings):
            return ao.action, b
    return None


def ego_seal(m: EgoMap) -> bool:
    """ONE WITNESSED PRESS, AND IT STICKS.

        1. EXISTENTIAL. At least one press moved this worldline in a direction the button
           it was pressed under produced. That is the witness, and it is permanent.
        2. THE CHANNEL LAW, UNCHANGED. If more than one action was observed and they all
           produced the same single bearing, the response keys on THAT-ANY action — a
           schedule, channel (b), not an ego (`SPEC_PIXEL_ARITHMETIC_v1` §3). With one
           observed action the comparison has no second term and travels
           coverage-bounded, exactly as `WO_EGO_01` §3.1 ruled.

    **WHAT CHANGED, AND WHY IT IS NOT A TOLERANCE.** Conjunct 1 was a forall over presses
    -- every action that moved it had to produce exactly one bearing, so ONE disagreeing
    press killed a worldline the record showed moving under three other buttons. That is
    the wrong quantifier for a permanent claim, not a bar set too high, and no fraction
    would have fixed it. `lever_witness` reached the same conclusion for the lever after
    four rungs of trying to tune a rate: *a null press is not a witness, and a non-witness
    cannot subtract from an existential.* The medium reached it too. The ego was the last
    of the three still carrying a forall.

    **HOW IT DIES, AND IT IS NOT SILENCE.** The seal is retracted only if the observation
    that earned it is shown misattributed -- the witness itself withdrawn. A later press
    that moved it nowhere says it was BLOCKED; a later press with a different bearing says
    the button does more than one thing. Neither says it is not the avatar, and there is
    no arithmetic here for either to subtract through.

    Reads `observed`, not `bearings`: `bearings` is the forall-filtered evidence and an
    existential must not be gated on the filter built for the claim it replaces. No
    threshold, no fraction, no tolerance, no decay."""
    if not m.observed:
        return False                                    # nothing ever moved it
    if len(m.observed) > 1 and len({b for ao in m.observed for b in ao.bearings}) == 1:
        return False                                    # channel (b): keys on ANY action
    return True


def channel_a_witness(m) -> bool:
    """MORE THAN ONE ACTION OBSERVED TO MOVE IT, AND MORE THAN ONE BEARING AMONG THEM.

    `SPEC_PIXEL_ARITHMETIC_v1` §3's four answers are EXCLUSIVE. This reads the FIRST —
    the response keys on WHICH action — from the same `observed` set `ego_seal` reads,
    and it is the exact complement of that seal's conjunct 2 *within* the case that
    conjunct is about. Conjunct 2 declines a map with more than one observed action and
    ONE shared bearing, because a single bearing under every button is channel (b), THAT
    ANY action. Given more than one observed action, "not one distinct bearing" and "more
    than one distinct bearing" are the same statement — `observed` never carries an entry
    with no bearing (`_observed` is built from a non-empty `seen` list) — so this is that
    complement stated positively, computed nowhere else and derived from nothing new.

    **WHY IT LIVES BESIDE `ego_seal` AND NOT AT THE CONSUMER.** The two predicates read
    one record and answer one question from opposite sides; a second reader of `observed`
    in another module is how two readings of one map begin to disagree.

    **IT IS NOT A THRESHOLD.** `> 1` is the boundary between "one" and "many", not a
    cutoff chosen inside a range — the same integer comparison `ego_seal` already makes
    on the same set, five lines up. There is no rate here, nothing is divided, and a map
    with a single observed action returns `False` because the question is unaskable, not
    because it scored too low (`WO_EGO_01` §3.1's coverage-bounded case, preserved).

    `None` — a worldline with no map at all — is `False` for the same reason: absence of
    an observation is not an observation."""
    if m is None or len(m.observed) <= 1:
        return False
    return len({b for ao in m.observed for b in ao.bearings}) > 1


def _map_str(m: EgoMap) -> str:
    return " · ".join(f"{b.action}→({b.bearing[0]:+d},{b.bearing[1]:+d})×{b.presses}"
                      for b in m.bearings)


def ego_basis(m: EgoMap) -> str:
    """The verdict's evidence sentence, and it names the WITNESS.

    The lever and the medium both cite the observation that earned them; the ego cited a
    summary of a filter instead. It cites the press now, and states the permanence and
    the death condition with it so a reader grades the claim without leaving the line."""
    w = ego_witness(m)
    if w is None:
        return "no press moved it under any button"
    action, bearing = w
    n = len(m.observed)
    still = (f"; {len(m.still)} action(s) also observed still "
             f"({', '.join(str(a) for a in m.still)})") if m.still else ""
    return (f"moves as the direct result of an action button: WITNESSED under action "
            f"{action}, which moved it by ({bearing[0]:+d},{bearing[1]:+d}) — {n} action"
            f"{'' if n == 1 else 's'} observed to move it — {_map_str(m)}{still} → EGO "
            f"(EXISTENTIAL: one witnessed press earns it and no later press unearns it; "
            f"a still press says blocked, not not-the-avatar)")


def ego_parallax(m: EgoMap) -> str:
    """What the map does NOT establish, stated where the verdict renders it."""
    if len(m.bearings) == 1:
        return ("coverage-bounded: ONE action observed, so distinguishability is unaskable "
                "— the claim is that this button moves it consistently, not that other "
                "buttons move it differently. Reopens as wider coverage arrives; actions "
                "never pressed have no entry and are not inferred from this one")
    return ("the map holds only what was pressed — an action absent here was never "
            "observed, not observed-and-zero, and is never completed from its opposite")
