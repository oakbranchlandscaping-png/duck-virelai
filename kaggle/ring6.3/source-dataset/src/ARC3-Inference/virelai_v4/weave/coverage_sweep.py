"""virelai_v4/weave/coverage_sweep.py — WO-WEAVE-SWEEP-01 Phase 1.

The weave-sourced coverage sweep: an additive, weave-native replacement for the
question the legacy captain's `FIRST_TOUCH_PROBE` dispatch can no longer safely
answer (WO_CONFIRM_ACTIONS_ATTEMPTED_GAP_RETURN_v1 root-caused the write-gap;
WO-WEAVE-SWEEP-01 Phase 0 audited the safe build path around it).

WHAT THIS IS. Repeats contact across delta-showing worldlines — never fixating
on one — until the weave's OWN role inference (`weave/role_read.py`, already
correctly identifying COUNTER and LEVER from real, repeated evidence) reports a
FIRM lever coupling. That is the point: a coupling cannot be legitimately
asserted from a single observation, so this module's job is to keep contact
going long enough for real confidence to emerge, not to force an early verdict.

WO-LEVER-SUBTREE-06: on a FIRM lever verdict, the sweep no longer completes
immediately — it hands off to a mechanism-typing detour
(`_advance_mechanism_probe`) that repeat-clicks the lever's own site and
classifies each confirmed reactive partner's fingerprint sequence
(`weave/mechanism_classify.py`) before the sweep finally completes. See that
function's docstring for why: a self-invariant remote lever has nothing of its
own left to classify once it's confirmed LEVER — the partner is where the
pattern is.

WHAT THIS IS NOT. Not a fix to `captain.py`, `targeting/dispatch_registry.py`,
`strategy/tier4_click.py`, `strategy/typed_gap_action.py`, or
`strategy/click_sweep.py` — none of those five files is imported, modified, or
otherwise touched by this module. Per RULING_GOLDEN_RUN_v1, this severs a feed:
the legacy captain simply isn't asked the question on a frame this module owns.
`click_sweep.py` is a template for SHAPE only (build-list-then-drain-with-
per-frame-state-advance, K-consecutive-inerts backstop) — its exclusion source
(`obj.role in (LibraryRole.EGO, LibraryRole.COUNTER)` off `library.objects`) is
NOT ported; this module's exclusion source is the weave's own FIRM role
verdicts instead (see `_is_excluded` below).

READ-ONLY BOUNDARY (WO-WEAVE-SWEEP-01 Phase 0 §0.3 — BINDING, not advisory).
`compute_current_weave_roles` calls ONLY the read-only prefix of the landing
chain that `Virelai._land_weave_roles` also uses:
`ledger_from_capture` -> `weave_window`/`re_join` -> `infer_roles`. It NEVER
calls `land_weave_roles` (the belief-accumulating step) or
`Virelai._land_weave_roles` itself — that step is confirmed, in its own
docstring, non-idempotent across overlapping windows ("`accumulate_role_evidence`
is pure addition (no dedupe)"), and calling it more than once per life would
double-count evidence. This module's read-only prefix mirrors the existing
precedent `Virelai._render_lineage` (virelai.py:1701-1734) already uses for the
identical reason — a pure read that must not inherit the landing's side effects.

CADENCE (WO-WEAVE-SWEEP-01 Phase 0 §0.2 — BINDING). `ledger_from_capture`
rescans the ENTIRE capture log, unconditionally, on every call (it is not
incremental) — that is the real cost driver, not `weave_window`/`re_join`.
Recomputing role verdicts every action would be O(life_length^2) over a life.
This module is throttled to recompute at most once every
`WEAVE_SWEEP_RECOMPUTE_INTERVAL` actions (fixed-interval, not event-triggered —
see the WO Phase 1 return for the reasoning); the per-frame CONTACT itself
(picking the next candidate and emitting a click) is cheap and happens every
eligible frame regardless of the recompute cadence.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from virelai_v4.capture.ledger_build import (
    ledger_from_capture,
    load_node_actions_from_log,
)
from virelai_v4.weave.mechanism_classify import (
    MECHANISM_PROBE_MAX_PRESSES,
    UNKNOWN as MECHANISM_UNKNOWN,
    classify_mechanism,
)
from virelai_v4.weave.contact_line import contact_note
from virelai_v4.weave.declare_intent import before_step, intent_note
from virelai_v4.weave.rejoin import re_join
from virelai_v4.weave.role_read import COUNTER, EGO, FIRM, LEVER, RoleVerdict, infer_roles
from virelai_v4.weave.worldline import Worldline, weave_window

# Recompute cadence — see module docstring "CADENCE" and the Phase 1 WO return.
WEAVE_SWEEP_RECOMPUTE_INTERVAL = 5

# Backstop termination only — the primary termination is a FIRM LEVER verdict
# (see `firm_lever_present`). Ported constant SHAPE from click_sweep.py's
# CLICK_SWEEP_K_CONSECUTIVE_INERTS (value re-chosen independently, not copied,
# since this module's cadence and candidate pool differ from the template's).
WEAVE_SWEEP_K_CONSECUTIVE_INERTS = 8


def _life_start_boundary(cuts) -> int:
    """Duplicated, verbatim in logic, from `Virelai._current_life_start`
    (virelai.py:1736-1769) — a pure `@staticmethod` over `cuts` with no other
    dependency on the `Virelai` instance. Duplicated rather than imported to
    avoid a circular import (virelai.py imports this module for wiring); see
    the WO Phase 1 return for why this is a deliberate, cited duplication and
    not a silent fork. Confirmed safe to call mid-life — WO-WEAVE-SWEEP-01
    Phase 0 §0.3 new finding #2. Any future change to the source's boundary
    logic must be mirrored here by hand; there is no single source of truth
    across the import boundary.
    """
    start = cuts[0].node_index if cuts else 0
    for c in cuts[:-1]:   # exclude this life's own terminal — it starts no new life
        if bool(getattr(c, "full_reset", False)) or getattr(c, "state", "") == "GAME_OVER":
            start = c.node_index + 1
    return start


def compute_current_weave_state(log):
    """`(cuts, node_actions, worldlines, verdicts)` for the current, still-open life.

    **ADDITIVE — `compute_current_weave_roles` below is unchanged and now delegates here**,
    so every existing consumer keeps its exact two-tuple. The collide drive
    (`weave/collide_drive.py`) needs the CUTS, to take one `owner_edge` across the two most
    recent of them, and the ACTION SERIES, to read the ego's measured bearings — both were
    computed on this path all along and discarded at the return. Same read-only prefix,
    same windowing, no second `ledger_from_capture`."""
    if log is None or len(log) == 0:
        return [], [], [], {}
    cuts_full = ledger_from_capture(log)
    if not cuts_full:
        return [], [], [], {}
    lo = _life_start_boundary(cuts_full)
    cuts = [c for c in cuts_full if c.node_index >= lo]
    if not cuts:
        return [], [], [], {}
    node_actions = load_node_actions_from_log(log)
    worldlines = re_join(weave_window(cuts), cuts=cuts)
    verdicts = infer_roles(worldlines, cuts, node_actions)
    return cuts, node_actions, worldlines, verdicts


def compute_current_weave_roles(
    log,
) -> Tuple[List[Worldline], Dict[int, RoleVerdict]]:
    """Read-only role-verdict read for the current, still-open life.

    Windowed to the current life only (mirroring `_land_weave_roles`'s own
    windowing discipline, via the duplicated `_life_start_boundary` above), so
    a worldline from a prior life within the same level's accumulated log
    cannot leak into this life's sweep. Returns `([], {})` on an empty or
    absent log, or when the current life's window has no cuts yet.

    Pure: never mutates `log`, never writes belief, never calls
    `land_weave_roles`. Safe to call every recompute tick.
    """
    _cuts, _na, worldlines, verdicts = compute_current_weave_state(log)
    return worldlines, verdicts


def _is_excluded(wid: int, verdicts: Dict[int, RoleVerdict]) -> bool:
    """A worldline is excluded from the sweep once the weave's OWN role read
    reports it FIRM-confidence COUNTER, LEVER or EGO — a real, evidence-backed
    verdict, never a provisional or single-observation read. This is the
    weave-native replacement for click_sweep.py's
    `obj.role in (LibraryRole.EGO, LibraryRole.COUNTER)` filter — re-grounded
    on `infer_roles` output instead of `library.objects`/`LibraryRole`, per
    the WO's design (no library.objects read anywhere in this module).

    WO-SWEEP-FORK-01 · EGO WAS EXCLUDED FROM THIS FILTER ON A PREMISE THIS
    CAMPAIGN RETIRED. The line that stood here read:

        "EGO is not excluded here: `infer_roles` only ever emits EGO as
         `UNKNOWN/OUT_OF_INPUT` (role_read.py has no firm-EGO branch in the
         current click-world-scoped role set), so there is nothing to exclude
         under that name at this module's confidence bar."

    That was true when written. `role_read` now emits `EGO` from two branches
    — the own-stream bearing read (WO-EGO-01) and the exchange-record field
    read (WO-EGO-02) — and on an embodied world it types the agent's own
    avatar. **A captain that sweeps its own avatar as a probe candidate is
    probing itself.**

    **AND ADDING EGO HERE DOES NOT YET STOP THAT, WHICH IS THIS RUNG'S
    FINDING.** Both branches emit `PROVISIONAL`, and no code path in `weave/`
    constructs an `EGO` verdict at `FIRM`. So this clause is structurally
    correct and currently INERT: it will exclude an ego the moment the ego
    seal earns a FIRM tier, and until then the avatar remains a candidate at
    this module's unchanged confidence bar. The bar is deliberately NOT
    lowered for EGO — a per-role bar would make this filter's own rule
    depend on which role it is reading, and that is a design question one
    stratum up. Reported rather than patched.
    """
    rv = verdicts.get(wid)
    return rv is not None and rv.role in (COUNTER, LEVER, EGO) and rv.confidence == FIRM


def build_weave_sweep_list(
    worldlines: List[Worldline], verdicts: Dict[int, RoleVerdict]
) -> List[int]:
    """Ordered worldline ids eligible for contact — every worldline not yet
    firmly typed COUNTER/LEVER. Ordering: worldline id ascending (weave_window's
    own first-appearance numbering) — deterministic; no salience fallback is
    ported from click_sweep.py's `_v35_salience_score` (a v1 simplification,
    stated here rather than silently omitted — see the Phase 1 WO return)."""
    return sorted(wl.id for wl in worldlines if not _is_excluded(wl.id, verdicts))


def refresh_weave_roles(context, log) -> bool:
    """The CADENCE gate and the refresh it guards, together — **extracted from
    `Virelai._maybe_weave_sweep_action` by WO-SWEEP-FORK-01**, which added lines
    to a file already in tier violation and owed the ratchet a compensating
    extraction. It belongs here on its own merits: the throttle exists because
    `ledger_from_capture` rescans the whole log every call (see this module's
    CADENCE section), and the rule and the read it protects were split across
    the import boundary with only a docstring holding them together.

    Returns whether a recompute actually happened. Mutates only the sweep's own
    scratch on `context` — never belief, and never `land_weave_roles`.
    """
    due = (
        context.weave_sweep_last_recompute_step is None
        or context.weave_sweep_worldlines is None
        or (context.step_count - context.weave_sweep_last_recompute_step)
        >= WEAVE_SWEEP_RECOMPUTE_INTERVAL
    )
    if not due:
        return False
    cuts, node_actions, worldlines, verdicts = compute_current_weave_state(log)
    context.weave_sweep_cuts = cuts
    context.weave_sweep_node_actions = node_actions
    context.weave_sweep_worldlines = worldlines
    context.weave_sweep_verdicts = verdicts
    context.weave_sweep_last_recompute_step = context.step_count
    # A fresh read invalidates any candidate list built off the stale one —
    # force select_weave_sweep_probe to rebuild.
    context.weave_sweep_list = []
    context.weave_sweep_index = 0
    return True


def advance_sweep_state(context, grid_changed: bool, log, emitting: bool) -> None:
    """The sweep's per-frame state advance, both arms: attribute the previous probe's
    outcome to the inerts backstop **only on an arm that emits one**, then refresh the
    cached read if the cadence is due.

    **Extracted from `Virelai._maybe_weave_sweep_action` by WO-COLLIDE-GOLDEN-01**, which
    added lines to a file already in deep tier violation and owed the ratchet a
    compensating extraction. It belongs here on its own merits — both halves are this
    module's own state and its own cadence rule, and the caller was only holding them in
    the right order and the `emitting` distinction in a comment.

    `emitting=False` is the NAV arm: `record_weave_sweep_outcome` advances the
    K-consecutive-inerts backstop toward termination, and **a frame that emits no probe
    has no outcome to attribute** — running it there would walk the sweep to completion on
    evidence it never gathered."""
    if emitting:
        record_weave_sweep_outcome(context, grid_changed)
    refresh_weave_roles(context, log)


def _unpaired(context, cuts) -> Tuple[Any, ...]:
    """The offered actions this life has not yet pressed MORE THAN ONCE, in a deterministic
    order — **the opening phase's whole state, derived, with no flag and no constant.**

    **WHY "MORE THAN ONCE" IS THE CONDITION AND NOT A TUNED NUMBER.** `EgoMap.bearings` is a
    ∀ — an action's bearing survives only `if len(set(v)) == 1`, *every press of this button
    agreed*. **With one press that quantifier is vacuous: an observation cannot disagree
    with itself.** The second press is the first frame at which the ∀ means anything. So the
    pair is not a sample size chosen for confidence; it is **the minimum cardinality at which
    the record's own reproducibility test is non-vacuous**, and the only integers in this
    derivation are `0` and `1`.

    **THE PRIOR ART, AND IT IS THE SAME NUMBER FOR THE SAME REASON.**
    `discovery/rover_gambit/gambit.py:19` — *"Exactly two executor calls per action in the
    probe set. Total steps consumed: 2 × len(action_set)."* One press is a delta; two presses
    of one button is a REPRODUCIBLE delta, which is what separates the ego's motion from the
    world's. **The cost falls out of the offered set; it is never written down.**

    **THE OFFERED SET IS ASKED FRESH EVERY FRAME, AND THAT SETTLES THE MID-PHASE CHANGE.**
    An action the platform stops offering stops blocking completion — it is absent, and
    absence is not a completed pair. An action newly offered is unpaired and the phase
    continues. **Neither case needs a rule of its own**, which is the reason the phase holds
    a press count rather than a target count.

    Absence is absence: no cached window, or a window offering nothing, yields no phase."""
    if not cuts:
        return ()
    pressed = getattr(context, "nav_opening_presses", None) or {}
    return tuple(sorted((a for a in cuts[-1].available_actions if pressed.get(a, 0) <= 1),
                        key=str))


def _opening_action(context, unpaired: Tuple[Any, ...]):
    """The one action the phase presses this frame — **the pair it started, or the next one.**

    **CONSECUTIVE PAIRS, NOT AN INTERLEAVE, AND THE PRIOR ART IS EXPLICIT.**
    `gambit.py:118` walks `for action_id in sorted(action_set):` and calls the executor twice
    inside that body — **both presses of one button, back to back.** Interleaving would be a
    different experiment: the world may move between two presses of the same action, and a
    pair straddling that is not a reproduction. Finishing a started pair before opening a new
    one is what makes the second press a test of the first."""
    if not unpaired:
        return None
    pressed = getattr(context, "nav_opening_presses", None) or {}
    started = tuple(a for a in unpaired if pressed.get(a, 0) > 0)
    return (started or unpaired)[0]


def _opening_note(action, ordinal: int, unpaired: Tuple[Any, ...]) -> str:
    """The phase, stating itself in the note the arm already renders.

    Names the action, which press of its pair this is, and **every action still unpaired** —
    the list rather than a remaining count, because a count is a number the reader then has
    to divide and a list is the thing itself."""
    return (f"weave sweep · NAV · OPENING PHASE — action {action}, press {ordinal} of its "
            f"pair. Still unpaired: {', '.join(str(a) for a in unpaired)} "
            f"({len(unpaired)} of the offered set). **Nothing is claimed about what this "
            f"button does** — the weave threads the press and the seals read it.")


def nav_drive_step(context):
    """WO-COLLIDE-GOLDEN-01 · `(step_or_None, note_if_it_changed)` for the NAV arm.

    **This function is the NAV arm's sole note writer, and now its only one.** This
    paragraph said `note_nav_sweep` was *"left in place for its own callers"*. **It had
    none** — `WO_NAV_SWEEP_00_RETURN` §4.1 swept the tree by symbol and found the pair
    reachable from nothing, while this sentence and one in `virelai.py` each asserted a
    caller the other was assumed to hold. Both were true until this signature carried the
    note out, and neither was corrected when it did. **The pair is deleted by
    WO-NAV-CLEANUP-01** — see the block where it stood, below `select_weave_sweep_probe`'s
    neighbours — and the reason it could not simply be left dormant is that it rendered
    the RED this campaign closed.

    **The candidate list is `build_weave_sweep_list`'s — there is no second selector.** The
    drive excludes only the driving worldline, at the drive, by identity (see
    `collide_drive._next_target` for why that is local and does not resolve the FIRM-`EGO`
    question). `select_weave_sweep_probe` and `record_weave_sweep_outcome` remain
    unreached on this arm, for the two reasons `WO_SWEEP_FORK_01` §3 gave: one advances a
    candidate index and can enter a click campaign, the other advances a termination
    backstop on an outcome that was never observed. **A directional step is not a probe
    outcome and must not feed either.**"""
    from virelai_v4.weave.collide_drive import (DriveStep, drive_step, driving_worldline,
                                                masked_worldlines, probe_record,
                                                visual_targets)
    # WO-GROUND-01 · `drive_absence` moved out of the decision module — the owed
    # extraction, paying this rung's ratchet. The body is byte-identical; only the path
    # changed, and it changed visibly here rather than through a re-export.
    from virelai_v4.weave.drive_absence import drive_absence
    worldlines = context.weave_sweep_worldlines or []
    verdicts = context.weave_sweep_verdicts or {}
    cuts = context.weave_sweep_cuts or []
    node_actions = context.weave_sweep_node_actions or []
    # WO-OPENING-PHASE-01 · THE EGO FINDS ITSELF BEFORE IT GOES ANYWHERE.
    #
    # **THE FIRST CLAUSE OF THE DIRECTOR'S SENTENCE, AND IT HAD NEVER BEEN BUILT.** At the
    # anchor this arm consulted the drive on the opening frame of every life, and the drive
    # returned `None` with the note *"no worldline types EGO — nothing to steer"*. That is a
    # starvation loop stated in one line: nothing had moved the ego deliberately, so no
    # worldline typed `EGO`, so the bearing map was empty, so `reach` had no lattice, so the
    # drive fell back — and the fallback's presses are not an experiment.
    #
    # **THE PHASE IS THE PORT; THE DETECTOR IS NOT.** `WO_THE_WHOLE_LOOP_MINE_00_RETURN` §4
    # traced the Opening Rover Gambit — baseline isolation, then two presses per action,
    # then a stride and a signed direction per action, and **navigation did not begin until
    # that model existed.** What ports is the PHASE: a deliberate, bounded opening whose cost
    # falls out of the offered set. `WO_EGO_MINE_00_RETURN`'s do-not-port judgement on the
    # prior detector — pooled centroid, direction prior, symmetric completion — stands whole.
    #
    # **THE PROBE PRESSES. THE WEAVE THREADS. THE SEALS TYPE.** Nothing here reads a role,
    # writes a role, or computes an ego; `ego_seal` and `ego_field_seal` are untouched and
    # finally have deliberate motion to observe. `ego_seal` needs ONE witnessed press, so the
    # first press that moves the body types it — the pair is for the ∀ above that, not for
    # the seal.
    #
    # **AND IT IS INSIDE THE CLICK GATE BY CONSTRUCTION**, not by a test: this function has
    # exactly one caller and it sits under `virelai.py`'s `if _world != "CLICK"`.
    _unpaired_now = _unpaired(context, cuts)
    _opening = _opening_action(context, _unpaired_now)
    if _opening is not None:
        _pressed = dict(getattr(context, "nav_opening_presses", None) or {})
        _ordinal = _pressed.get(_opening, 0) + 1
        _pressed[_opening] = _ordinal
        context.nav_opening_presses = _pressed
        _onote = _opening_note(_opening, _ordinal, _unpaired_now)
        _ochanged = _onote != context.weave_sweep_nav_note
        context.weave_sweep_nav_note = _onote
        # **EVERY FIELD THAT DOES NOT APPLY IS ABSENT, NOT ZEROED.** There is no ego to name,
        # no target to name, and — this is the load-bearing one — **no bearing**, because a
        # bearing here would be a claim about what the button does and the phase makes none.
        # `(0, 0)` would say *it moved nothing*, which is exactly the assertion §4 forbids.
        return DriveStep(ego=None, target=None, action=_opening, bearing=None,
                         basis=_onote), (_onote if _ochanged else None)
    # WO-VISUAL-TARGETS-01 · THE CANDIDATES ARE THE BOARD'S VISUAL OBJECTS, AS SITES.
    # The derivation lives in `collide_drive` and not here because this module cannot be
    # imported without scipy, and a rung whose logic no test can execute is a rung graded
    # on reading. Cost: one pass over the cached window's regions per frame.
    #
    # **WO-NAV-CLEANUP-01 · THE `included` ARGUMENT IS GONE, AND `build_weave_sweep_list`
    # IS NOT CALLED HERE ANY MORE.** This comment said the sweep's FIRM-COUNTER/LEVER/EGO
    # filter *"is the same call and cannot weaken"* — but `WO-OPEN-THE-BOARD-01` stopped
    # `visual_targets` consuming the set, and from that rung on the call computed a list,
    # passed it, and had it ignored. **The filter is untouched and still governs the CLICK
    # arm through `select_weave_sweep_probe`**; what is removed is a per-frame computation
    # whose result was discarded, and a parameter that read as live and was not.
    # **WO-ROLE-MASK-01 · THE QUEUE IS MASKED BY ROLE, AND THIS IS THE ONE LINE IT COSTS.**
    # `driving_worldline` was the belief-to-queue channel one argument wide: a role verdict
    # in, the id whose footprints are barred out. `masked_worldlines` is that channel for
    # the closed list — the ego, and every worldline the weave has SEALED `COUNTER`. Nothing
    # is masked before a seal exists, and a counter is a legitimate target until it types.
    #
    # **THE MASK MUST BE APPLIED WHERE THE QUEUE IS DERIVED, WHICH IS HERE.** Applying it
    # inside `drive_step` would leave this derivation unmasked and make two queues; applying
    # it in the roster alone would grade a list the drive never worked. This rung's fence
    # named `collide_drive.py` and `tests/` — **the one line in this file is declared in the
    # return's §4**, because the alternative sites are all worse.
    candidates = visual_targets(cuts, worldlines, masked_worldlines(verdicts))
    # WO-CONTACT-LINE-01 · **THE HELD TARGET IS READ BEFORE THE STEP, AND THAT ORDER IS
    # THE WHOLE CORRECTNESS OF THE LINE.** `drive_step` -> `_arrival` -> `_pass_over`
    # clears `collide_drive_target` on arrival, so reading it afterwards would render
    # `none` on exactly the presses the line exists to show. Read once, before.
    _held_at_press = context.collide_drive_target
    # WO-DECLARE-INTENT-01 · the three readings a retirement destroys, bound for one press.
    _before = before_step(context)
    step = drive_step(context, cuts, node_actions, worldlines, verdicts, candidates)
    # The render is extracted whole into `weave/contact_line.py`; this is the call.
    _contact = contact_note(cuts, worldlines, verdicts, _held_at_press)
    # **WO-NAV-CLEANUP-01 · THE PURSUIT RECORD IS READ AT LAST.** `probe_record` has been
    # computed from `collide_drive_trail` every frame since `WO-PROBE-RECORD-01` and
    # rendered by nothing for eighteen rungs — the record was right and the wiring never
    # happened. It joins the note the arm already renders rather than gaining a channel of
    # its own, because a second logging path is a second thing to keep honest.
    #
    # **THE CADENCE IS UNCHANGED, AND THAT WAS MEASURED RATHER THAN ASSUMED.** The
    # on-change rule below is what `WO-DRIVE-ABSENCE-01` installed to stop a stable absence
    # printing every frame, and the concern is live. But `step.basis` already carries the
    # frame counter, so on a frame that emits, the note ALREADY changed — appending here
    # adds a line to a line that was printing, not a new line. On a frame that does not
    # emit, the early `return None`s in `drive_step` come BEFORE the trail is appended, so
    # a genuine absence leaves `probe_record` frozen and the note stays stable. The one
    # case that prints per frame is a pursuit whose fallback refuses every frame — and
    # there the value that changes is the presses-remaining trail stalling, which is the
    # pursuit failing in public and is bounded by the frame budget.
    if step is not None:
        note = f"{step.basis} · {probe_record(context)}"
    else:
        # WO-ABSENCE-TRUTH-01 · THE SIXTH ARGUMENT, TWO RUNGS LATE. `drive_absence` has
        # accepted `cuts` since WO-REACHABLE-01 and this call has passed five, so the
        # note has been computing its cause with `cuts=()`: the unreachability cause
        # could never fire, and the offered-set cause was an INFERENCE stated as a
        # measurement. `drive_step` on the line above is handed the same `cuts` and
        # always has been — the account and the act now read one board.
        #
        # **WO-NAV-CLEANUP-01 · THE CONDITIONAL BECAME A STATEMENT, AND THE SPELLING OF
        # THIS CALL IS DELIBERATE.** `test_absence_truth`'s guard pins this call's source
        # text so the sixth argument cannot be dropped again. Folding the pursuit record
        # into a conditional expression broke that literal, and Python 3.11 forbids the
        # newline inside an f-string that would have restored it. **The guard is not
        # re-graded to fit this rung** — a fence that rejects an addition is working, and
        # the branch is written to satisfy it while keeping the absence call LAZY, which a
        # bound temporary above the branch would not have done.
        absent = drive_absence(context, node_actions, worldlines, verdicts, candidates,
                               cuts)
        note = f"{absent} · {probe_record(context)}"
    # WO-CONTACT-LINE-01 · joined to the note the arm ALREADY emits, on BOTH branches.
    # Both, because the drive emitted a step on 0 of 130 presses offline — attaching to
    # the step branch alone would render the line on none of them, and §GRADED-ON asks
    # for a line on every press.
    note = f"{note} · {_contact}"
    # WO-DECLARE-INTENT-01 · the declaration and the walk, on the channel the arm already
    # has. Empty on every press that neither forms the list nor retires a pursuit.
    note = note + intent_note(context, cuts, worldlines, verdicts, node_actions,
                              candidates, _before)
    changed = note != context.weave_sweep_nav_note
    context.weave_sweep_nav_note = note
    return step, (note if changed else None)


# WO-NAV-CLEANUP-01 · `note_nav_sweep` AND `nav_sweep_note` ARE DELETED, AND THE REASON IS
# NOT THAT THEY WERE UNUSED.
#
# `nav_sweep_note` returned, verbatim: *"NO ACTION EMITTED: the navigation primitive that
# would drive the ego to a selected target is not built (collide_sweep is coverage policy
# only). The frame falls through to legacy dispatch"* — **the exact RED
# `WO-COLLIDE-GOLDEN-01` was chartered to close.** The primitive is built and `nav_drive_step`
# emits on this arm every frame. A renderer that states a falsehood is not dormant; it is
# wrong, and `UNREACHABLE`'s dormancy — a state kept because a future PRODUCER needs it —
# is not a precedent for keeping it.
#
# `note_nav_sweep` was its only caller and had none of its own. **Two documents said
# otherwise**: this module's `nav_drive_step` docstring (*"left in place for its own
# callers"*) and `virelai.py`'s NAV seam (*"retained for the frames the drive is not
# reached at all"*). Both were true before `WO-COLLIDE-GOLDEN-01` carried the note out
# through `nav_drive_step`'s return, and neither was corrected when it did. Both are
# corrected by this rung — `WO_NAV_SWEEP_00_RETURN` §4.1.
#
# **The stated-absence itself is not lost.** `drive_absence` states the NAV arm's absence
# with the cause read off the board, which is what these two approximated from a candidate
# list; `nav_drive_step`'s `else` branch has called it since `WO-ABSENCE-TRUTH-01`.


def firm_lever_present(verdicts: Dict[int, RoleVerdict]) -> bool:
    """The sweep's PRIMARY termination condition, per the Director's explicit
    design: at least one worldline reads LEVER with a FIRM, evidence-backed
    coupling verdict — not merely 'clicked once'. `RoleVerdict.confidence`
    only reaches FIRM for a LEVER when `len(wl_clicks) >= 2`
    (role_read.py:`infer_roles`'s LEVER branch: `FIRM if len(wl_clicks) >= 2
    else PROVISIONAL`) — i.e. by construction, this can never fire off a
    single click; repeated contact is structurally required to satisfy it."""
    return any(rv.role == LEVER and rv.confidence == FIRM for rv in verdicts.values())


def record_weave_sweep_outcome(context, grid_changed: bool) -> None:
    """Update the K-consecutive-inerts backstop counter. Call once per frame
    the sweep is active, fed the SAME `grid_changed` signal
    `Virelai.choose_action` already computes ("Derive grid_changed from
    FrameDelta") — introduces no new delta computation. `grid_changed` reflects
    whether the frame just observed (i.e., the outcome of the PREVIOUS action)
    changed the board; feeding it here before selecting the next probe
    correctly attributes the prior click's outcome to the counter."""
    if grid_changed:
        context.weave_sweep_consecutive_inerts = 0
    else:
        context.weave_sweep_consecutive_inerts += 1


_PARTNER_ID_RE = re.compile(r"###(\d{3})")


def _confirmed_partners_of(
    lever_wid: int, verdicts: Dict[int, RoleVerdict]
) -> Tuple[int, ...]:
    """Every worldline id this LEVER's own verdict basis names as a confirmed
    reactive partner. `RoleVerdict.basis` is role_read.py's own documented
    "human-gradable evidence sentence (cites the coupling)" (role_read.py's
    RoleVerdict docstring) — reading the ###NNN ids it already cites, rather
    than re-deriving confirmation independently here, avoids duplicating
    infer_roles' Defect-1/Defect-2-fixed collective-bootstrap logic
    (WO_LEVER_SUBTREE_05_RETURN) a second time in a different module. Sorted
    ascending, deterministic, deduped. Empty if `lever_wid` isn't LEVER."""
    rv = verdicts.get(lever_wid)
    if rv is None or rv.role != LEVER:
        return ()
    # role_read.py's LEVER basis text names the lever itself repeatedly too
    # (each "PREDICTS d(###<lever>) = ... " clause) — exclude lever_wid from
    # the extracted set so it is never mistaken for its own partner.
    ids = {int(m) for m in _PARTNER_ID_RE.findall(rv.basis)}
    ids.discard(lever_wid)
    return tuple(sorted(ids))


def _start_mechanism_probe(context, verdicts: Dict[int, RoleVerdict]) -> None:
    """Entered exactly once per life, the first time `firm_lever_present`
    fires. Queues every FIRM lever as of THIS moment, ascending by id
    (deterministic, no salience heuristic — same convention
    `build_weave_sweep_list` already uses). The confirmed-partner set for
    each lever is fixed here, from this one verdicts snapshot, and is not
    re-derived as the probe campaign advances — role verdicts are not
    expected to change meaningfully over the probe's own short, bounded
    burst, and re-deriving them mid-campaign would risk a partner list that
    shifts under a campaign already in progress."""
    levers = sorted(
        wid for wid, rv in verdicts.items() if rv.role == LEVER and rv.confidence == FIRM
    )
    context.mechanism_probe_started = True
    context.mechanism_probe_lever_queue = levers
    context.mechanism_probe_results = {lv: {} for lv in levers}
    _advance_to_next_lever(context, verdicts)


def _requeue_newly_firm_levers(context, verdicts: Dict[int, RoleVerdict]) -> None:
    """WO-LEVER-SUBTREE-08: called only from `_advance_to_next_lever`, only at
    the instant the lever queue is found empty — never mid-dive. `_start_
    mechanism_probe` queues every FIRM lever as of its own one-time snapshot
    (by design — see that function's docstring on why re-deriving mid-campaign
    is unsafe); this is the campaign's one safe re-check point instead: the
    prior lever's dive has already fully finished (or exhausted its press
    budget) by the time `_advance_to_next_lever` is ever called, so there is
    no in-progress `mechanism_probe_pending_partners`/`mechanism_probe_
    fingerprints` state this can disturb (WO-08 Part A.5). `context.
    mechanism_probe_results` already holds a key for every lever ever queued
    (seeded in `_start_mechanism_probe`, added here for anything newly
    queued) — so "not already a key" is the correct, monotonic test for
    genuinely new, never scanning the same lever back in twice."""
    newly_firm = sorted(
        wid for wid, rv in verdicts.items()
        if rv.role == LEVER and rv.confidence == FIRM
        and wid not in context.mechanism_probe_results
    )
    if not newly_firm:
        return
    context.mechanism_probe_lever_queue.extend(newly_firm)
    for wid in newly_firm:
        context.mechanism_probe_results[wid] = {}


def _advance_to_next_lever(context, verdicts: Dict[int, RoleVerdict]) -> None:
    """Pop the next queued lever and reset the per-lever probe scratch state.
    Sets `context.mechanism_probe_current_lever` to None once the queue is
    exhausted — the caller's signal that the whole campaign is done.

    WO-LEVER-SUBTREE-08: before treating an empty queue as campaign-complete,
    `_requeue_newly_firm_levers` gets one look at whether any lever has gone
    FIRM since the queue was last built or checked — see that function's own
    docstring for why this is safe here and nowhere else in the campaign."""
    context.mechanism_probe_fingerprints = {}
    context.mechanism_probe_press_count = 0
    if not context.mechanism_probe_lever_queue:
        _requeue_newly_firm_levers(context, verdicts)
    if not context.mechanism_probe_lever_queue:
        context.mechanism_probe_current_lever = None
        context.mechanism_probe_pending_partners = set()
        return
    lever_wid = context.mechanism_probe_lever_queue.pop(0)
    context.mechanism_probe_current_lever = lever_wid
    context.mechanism_probe_pending_partners = set(_confirmed_partners_of(lever_wid, verdicts))


def _advance_mechanism_probe(
    context, log, verdicts: Dict[int, RoleVerdict]
) -> Optional[Tuple[int, Worldline]]:
    """WO-LEVER-SUBTREE-06's mechanism-typing mode, entered at the exact point
    `select_weave_sweep_probe`'s Termination 1 used to complete the sweep
    immediately. Per the WO's ruled correction, a self-invariant remote lever
    has nothing of its own to classify — this repeat-clicks the lever's own
    site instead, recording each confirmed reactive PARTNER's fingerprint
    every press, until every partner classifies or
    `MECHANISM_PROBE_MAX_PRESSES` is spent, one lever at a time, then moves to
    the next queued lever. Only once every lever queued at mode-entry has been
    walked does `context.weave_sweep_complete` finally get set — this REPLACES
    the sweep's remaining broad-candidate contact, it does not run alongside
    it, matching the original Termination 1's own "this is the primary,
    terminal condition" semantics.

    FRESH READ EVERY PRESS, DELIBERATELY, DESPITE THE MODULE'S OWN CADENCE
    DISCIPLINE (see module docstring "CADENCE"). That discipline exists
    because `ledger_from_capture` rescans the whole log every call, and doing
    that every action across a WHOLE life is the O(life_length^2) cost this
    module was built to avoid. This function's own full-recompute-per-press
    cost is bounded instead: at most `MECHANISM_PROBE_MAX_PRESSES` extra
    recomputes per queued lever, a small, fixed burst at the tail of one life,
    not a per-action cost across the life's whole length — the failure mode
    the throttle guards against does not apply here."""
    if not context.mechanism_probe_started:
        _start_mechanism_probe(context, verdicts)

    if context.mechanism_probe_current_lever is None:
        context.weave_sweep_complete = True
        return None

    worldlines, _fresh_verdicts = compute_current_weave_roles(log)
    by_id = {wl.id: wl for wl in worldlines}

    for pid in list(context.mechanism_probe_pending_partners):
        wl = by_id.get(pid)
        if wl is None:
            continue  # window edge -- try again next press, not a crash
        region = wl.steps[-1][1]
        seq = context.mechanism_probe_fingerprints.setdefault(pid, [])
        seq.append((region.class_id, region.cells))
        verdict_str = classify_mechanism(seq)
        if verdict_str != MECHANISM_UNKNOWN:
            context.mechanism_probe_results[context.mechanism_probe_current_lever][pid] = (
                verdict_str
            )
            context.mechanism_probe_pending_partners.discard(pid)

    context.mechanism_probe_press_count += 1
    budget_spent = context.mechanism_probe_press_count >= MECHANISM_PROBE_MAX_PRESSES
    if not context.mechanism_probe_pending_partners or budget_spent:
        for pid in context.mechanism_probe_pending_partners:
            # Budget exhausted with this partner still unclassified -- an
            # honest UNKNOWN, never a forced guess.
            context.mechanism_probe_results[context.mechanism_probe_current_lever][pid] = (
                MECHANISM_UNKNOWN
            )
        _advance_to_next_lever(context, verdicts)
        if context.mechanism_probe_current_lever is None:
            context.weave_sweep_complete = True
            return None

    lever_wid = context.mechanism_probe_current_lever
    lever_wl = by_id.get(lever_wid)
    if lever_wl is None:
        return None  # window edge -- skip this press, retry next call
    return (lever_wid, lever_wl)


def select_weave_sweep_probe(
    context,
    worldlines: List[Worldline],
    verdicts: Dict[int, RoleVerdict],
    log=None,
) -> Optional[Tuple[int, Worldline]]:
    """Return `(worldline_id, worldline)` for the next contact, or `None` if
    the sweep should terminate THIS call (also sets
    `context.weave_sweep_complete = True` when it does). Per-frame
    state-advance shape ported from `click_sweep.py`'s
    `select_click_sweep_probe`: checks termination first, rebuilds the
    candidate list when empty, advances an index, records visited state. Does
    NOT mutate belief. Does NOT set `context.last_emitter_path` — that is the
    caller's job (WO-WEAVE-SWEEP-01 Phase 1 §0.2.5), because only the caller
    knows whether it is about to actually emit the returned probe as an action
    this frame.

    `log` (WO-LEVER-SUBTREE-06): the caller's frame_record_log, threaded
    through so the mechanism-probe detour (Termination 1, below) can do its
    own fresh per-press reads. `None` is accepted for pre-existing callers
    that never reach mechanism-probe mode (e.g. a synthetic test with no firm
    lever) — `_advance_mechanism_probe` is the only code path that reads it,
    and it is only reached once a firm lever has actually appeared."""
    # Termination 1 (primary, Director-specified): a firm LEVER verdict
    # exists. WO-LEVER-SUBTREE-06: this no longer completes the sweep
    # immediately -- it hands off to the mechanism-typing detour, which is
    # itself what eventually sets weave_sweep_complete once every queued
    # lever's confirmed partners have classified or exhausted their budget.
    if firm_lever_present(verdicts) or context.mechanism_probe_started:
        return _advance_mechanism_probe(context, log, verdicts)

    # Termination 2 (backstop, ported from the template).
    if context.weave_sweep_consecutive_inerts >= WEAVE_SWEEP_K_CONSECUTIVE_INERTS:
        context.weave_sweep_complete = True
        return None

    if not context.weave_sweep_list:
        context.weave_sweep_list = build_weave_sweep_list(worldlines, verdicts)
        context.weave_sweep_index = 0

    if context.weave_sweep_index >= len(context.weave_sweep_list):
        # This generation of the list is exhausted. Rebuild once in case the
        # candidate pool has changed since it was built (new worldline
        # appeared, or an exclusion lapsed — it cannot: exclusion is
        # monotonic in practice since roles do not un-firm, but the rebuild
        # is defensive and cheap — it is a pure-python sort over already-
        # computed verdicts, not a re-read).
        context.weave_sweep_list = build_weave_sweep_list(worldlines, verdicts)
        context.weave_sweep_index = 0
        if not context.weave_sweep_list:
            context.weave_sweep_complete = True
            return None

    wid = context.weave_sweep_list[context.weave_sweep_index]
    context.weave_sweep_index += 1
    context.weave_sweep_probed.add(wid)

    wl = next((w for w in worldlines if w.id == wid), None)
    if wl is None:
        # Worldline id from a stale candidate list no longer present in the
        # current read (window edge, re_join fold) — skip silently, try the
        # next candidate this same call. Matches click_sweep.py's own
        # "region disappeared from library" recursion; bounded by list length
        # since each recursive call advances the index.
        return select_weave_sweep_probe(context, worldlines, verdicts, log)

    return (wid, wl)


__all__ = [
    "WEAVE_SWEEP_RECOMPUTE_INTERVAL",
    "WEAVE_SWEEP_K_CONSECUTIVE_INERTS",
    "compute_current_weave_roles",
    "build_weave_sweep_list",
    "advance_sweep_state",
    "compute_current_weave_state",
    "nav_drive_step",
    "refresh_weave_roles",
    "firm_lever_present",
    "record_weave_sweep_outcome",
    "select_weave_sweep_probe",
]
