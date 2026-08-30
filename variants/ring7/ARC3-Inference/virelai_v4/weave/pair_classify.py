"""WO-INFER-ROLES-EXTRACT-01 · PAIR CLASSIFICATION, LIFTED WHOLE.

A PRECONDITION EXTRACTION, NOT A FEATURE. Its value is entirely in what it makes
buildable: the ruled next rung is a two-pass `infer_roles`, so witnesses compute against
the FULL `COUNTER` set instead of the `marginal_counters` that held 2 of 5 on the primary
canary's stored life. `infer_roles` measured **161 executable lines — RED (151-250)** at
anchor `5fbbb31`, and the ratchet forbids restructuring a RED function. This buys the room.

MEASURED UNDER THE DIRECTOR'S STANDING AMENDMENT (2026-08-08): tier and ratchet
measurements count EXECUTABLE lines only — docstrings are excluded at both function and
file grain, because the caps bound the complexity a reader must hold in their head, and a
docstring reduces that. Prose here is therefore free, and it is spent on provenance.

**NOTHING IN THIS MODULE IS NEW.** Every executable line is `infer_roles`' own, lifted
verbatim from `weave/role_read.py` at that anchor:

    CLICK_DRIVEN_MAX_UNCLICKED_FRAC   role_read.py:34-38
    _lever_reactive_candidate         role_read.py:605-654
    _click_driven_split               role_read.py:657-671
    the two-pass discriminator        role_read.py:771-863

No predicate, threshold, verdict or ordering changed. **The proof is not that the tests
pass — it is that the rendered dossier is byte-identical on both stored canaries**, pinned
by `tests/weave/test_infer_roles_extract.py`.

THE SUBJECT, named so the extraction is by responsibility rather than by line count: given
the stable pairs and the three channels, decide which pairs license a LEVER↔REACTIVE
relation and which are autonomous relays whose members are COUNTER — and record, never
drop, the candidacies channel exclusivity denied. The four symbols above are that one
subject; they moved together because they are used by nothing else.

`role_read` re-exports all three moved symbols, so every existing reference resolves
unchanged and no caller outside this module had to learn a new import.

Pure and stdlib-only over the channels it is handed. Writes no belief, reads no library,
and types nothing: it returns the four maps and `infer_roles`' ladder does the typing.
"""

from __future__ import annotations

from typing import Any, Dict, List, NamedTuple, Tuple


class PairVerdicts(NamedTuple):
    """The four maps the ladder reads. `excluded_lever` is the denial record — a LEVER
    candidacy refused by channel exclusivity, reported on the counter's own verdict rather
    than dropped (`RULING_OBSERVERS_INTEGRATOR_v1` §1)."""
    counter_of: Dict[int, Any]
    lever_of: Dict[int, List[Tuple[int, Any]]]
    reactive_of: Dict[int, List[Tuple[int, Any]]]
    excluded_lever: Dict[int, Any]


# A stable pair is CLICK-DRIVEN (LEVER↔REACTIVE) only if it essentially never fires without
# a click — i.e. its unclicked-active presses are at most this fraction of its active presses.
# A pair that fires click-INDEPENDENT on more than this is autonomous → COUNTER (this is what
# stops an often-clicked counter, like vc33's fuel-bar, from being mislabeled a LEVER).
CLICK_DRIVEN_MAX_UNCLICKED_FRAC = 0.15


# ---- WO-LEVER-SUBTREE-05 · magnitude channel + multi-cause reactive objects --
#
# Two confirmed defects in the click-driven-vs-autonomous discriminator, found by direct
# read against real ground truth (WO_LEVER_SUBTREE_04_RETURN proved the pairing layer
# correct; this rung is entirely downstream of it, in infer_roles itself):
#
#   Defect 1 — wrong channel. The discriminator built its active/unclicked press sets
#   from `matrix`, the SIGNED cell-count-delta channel. A reactor that responds by moving
#   (MOVE verb) rather than resizing has a signed delta of exactly zero on every press
#   even though it visibly reacts — the identical blind spot `_corr` had one layer down,
#   now confirmed present here, in different code, unaffected by that fix.
#
#   Defect 2 — single-cause storage. `lever_of`/`reactive_of` held one (partner, pair)
#   tuple per worldline, plain-assigned, not appended. A worldline that is a genuine,
#   confirmed reactor to TWO real levers (or a lever with multiple confirmed reactors)
#   had its earlier-processed relationship silently overwritten by the last one seen —
#   not the discriminator failing to notice a second cause, but nowhere to record it even
#   when everything upstream correctly found one.
#
#   Consequence of fixing Defect 2 — the same evidence-gated exclusion this WO's own
#   precedent (WO_LEVER_SUBTREE_04_RETURN §B.2, refinement 2) already proved one layer
#   down: a reactive object confirmed to respond to TWO real levers will, evaluated one
#   pair at a time, see the OTHER lever's clicks as "unclicked" noise against whichever
#   pair is being scored — inflating past CLICK_DRIVEN_MAX_UNCLICKED_FRAC for a pair that
#   is, in fact, entirely click-driven once the other lever's own confirmed effect is
#   accounted for. Ported up via the identical two-pass, evidence-gated shape: pass 1
#   classifies every pair with no cross-pair knowledge (channel-fixed only) to discover
#   which (lever, reactive) relationships already have independent standing evidence;
#   pass 2 re-scores every pair, excluding from its own unclicked set only presses
#   already explained by a DIFFERENT, pass-1-confirmed lever for the SAME reactive
#   member — never merely because someone else was clicked, exactly the discipline that
#   kept the coupling-layer fix from over-promoting (WO_LEVER_SUBTREE_04_RETURN's own
#   first, too-broad attempt at this exact pattern, caught by its regression floor).

def _lever_reactive_candidate(p, clicked_active, press_left, acted_press):
    """Which member of a pair WOULD be the lever if this pair is click-driven — determined
    purely from which member is at the click end of the pair's own active presses, which
    does not depend on the confound-exclusion applied to the unclicked set below (the two
    questions — who is the cause, and is the evidence strong enough — are separable).
    Returns (lever, reactive) or None if there is no clicked-active press to determine one
    from (such a pair can never be click-driven regardless of its unclicked set)."""
    if not clicked_active:
        return None
    a, b = p.wid_a, p.wid_b
    lever = p.acted_member if p.acted_member in (a, b) else \
        acted_press.get(press_left[clicked_active[0]])
    if lever not in (a, b):
        lever = a
    reactive = b if lever == a else a
    return lever, reactive


def _click_driven_split(a, b, magnitude, press_left, acted_press, confound_levers=frozenset()):
    """(active, clicked_active, unclicked_active) for pair (a, b), reading the MAGNITUDE
    channel (verb-agnostic; WO-LEVER-SUBTREE-05 Defect 1) rather than the signed
    cell-count-delta channel `matrix`, which is exactly zero for a MOVE/RECOLOR-verb
    reactor regardless of how visibly it reacts. `confound_levers` (WO-LEVER-SUBTREE-05
    Defect 2's consequence) excludes from `unclicked_active` any press already explained
    by a DIFFERENT, independently-confirmed lever for this same reactive member — passed
    in only by the second of two passes in `infer_roles`, empty (a no-op) on the first."""
    active = [i for i in range(len(press_left))
              if magnitude[a][i] != 0 or magnitude[b][i] != 0]
    clicked_active = [i for i in active if acted_press.get(press_left[i]) in (a, b)]
    unclicked_active = [i for i in active
                         if acted_press.get(press_left[i]) not in (a, b)
                         and acted_press.get(press_left[i]) not in confound_levers]
    return active, clicked_active, unclicked_active


def classify_pairs(stable_pairs, magnitude, press_left, acted_press,
                   marginal_counters) -> PairVerdicts:
    """The two-pass discriminator — PASS 1's collective bootstrap, then PASS 2's final
    classification with the confound exclusion — lifted whole. Every comment below is the
    original's; see the module docstring for provenance and the byte-identity proof."""
    excluded_lever: Dict[int, Any] = {}  # wid -> the pair whose lever slot it was denied

    counter_of: Dict[int, Any] = {}       # wid -> the pair it counters in
    lever_of: Dict[int, List[Tuple[int, Any]]] = {}      # lever wid -> [(reactive wid, pair), ...]
    reactive_of: Dict[int, List[Tuple[int, Any]]] = {}   # reactive wid -> [(lever wid, pair), ...]


    # PASS 1 — COLLECTIVE bootstrap, channel-fixed (Defect 1). Found necessary by direct
    # testing against real data, not assumed: a naive per-pair bootstrap (does THIS one
    # candidate, alone, explain the reactive object well enough?) cannot break a genuinely
    # SYMMETRIC multi-cause case — when a reactive object is confirmed caused by two real
    # levers in exactly equal measure (the real `vc33` fixture's ###009: 9 of its 18
    # active presses explained by ###004's clicks, 9 by ###005's, 0 unattributed to
    # either), NEITHER candidate alone clears the tolerance, so nothing ever seeds
    # `confirmed_levers_of` and the confound exclusion below never activates for anyone.
    # `WO_LEVER_SUBTREE_04_RETURN`'s own port of this shape into `coupling.py` avoided
    # this only because that fixture's round-robin click order happened to let one
    # candidate's settle-back exclusion accidentally absorb the other's clicks too — a
    # scheduling coincidence, not a property this discriminator can rely on.
    #
    # The fix: test every reactive object's FULL candidate SET collectively. Does the
    # UNION of clicks from every candidate lever paired with this reactive object explain
    # (at least 1 - CLICK_DRIVEN_MAX_UNCLICKED_FRAC of) its own active presses? A genuine
    # multi-cause reactor is fully explained by the union of its causes even though no
    # single cause explains it alone. With exactly one candidate this reduces to the
    # identical single-pair test the discriminator always ran — byte-identical behavior
    # for every existing single-lever fixture (B.4 case 4).
    candidates_by_reactive: Dict[int, List[Tuple[int, Any]]] = {}
    for p in stable_pairs:
        a, b = p.wid_a, p.wid_b
        _active, clicked_active, _unclicked = _click_driven_split(
            a, b, magnitude, press_left, acted_press)
        candidate = _lever_reactive_candidate(p, clicked_active, press_left, acted_press)
        if candidate is None:
            continue
        lever, reactive = candidate
        if lever in marginal_counters:
            continue  # schedule-autonomous never enters candidacy at all
        candidates_by_reactive.setdefault(reactive, []).append((lever, p))

    confirmed_levers_of: Dict[int, set] = {}   # reactive wid -> {lever wids confirmed for it}
    for reactive, causes in candidates_by_reactive.items():
        active_r = [i for i in range(len(press_left)) if magnitude[reactive][i] != 0]
        lever_ids = {lever for lever, _p in causes}
        # settle-back: a press right after ANY candidate's own click is the same
        # mechanically-entangled echo WO_LEVER_SUBTREE_04_RETURN found in coupling.py's
        # own promotion path, applied per member of this reactive object's candidate set.
        unexplained = [i for i in active_r
                       if acted_press.get(press_left[i]) not in lever_ids
                       and not (i > 0 and acted_press.get(press_left[i - 1]) in lever_ids)]
        tol = max(1, int(CLICK_DRIVEN_MAX_UNCLICKED_FRAC * len(active_r))) if active_r else 0
        if len(unexplained) <= tol:
            confirmed_levers_of[reactive] = set(lever_ids)

    # PASS 2 — final classification. Same channel and same lever/reactive identity (that
    # determination never depended on the unclicked set), but `unclicked_active` now
    # excludes presses already explained by a DIFFERENT, pass-1-confirmed lever for this
    # same reactive member (Defect 2's consequence, WO_LEVER_SUBTREE_04_RETURN §B.2's
    # precedent ported up) — never merely because someone else was clicked.
    for p in stable_pairs:
        a, b = p.wid_a, p.wid_b
        active, clicked_active, _unclicked_naive = _click_driven_split(
            a, b, magnitude, press_left, acted_press)
        candidate = _lever_reactive_candidate(p, clicked_active, press_left, acted_press)
        if candidate is None:
            # no clicked-active press at all: never click-driven, same as before.
            counter_of.setdefault(a, p)
            counter_of.setdefault(b, p)
            continue
        lever, reactive = candidate
        confound = confirmed_levers_of.get(reactive, set()) - {lever}
        _active2, clicked_active2, unclicked_active = _click_driven_split(
            a, b, magnitude, press_left, acted_press, confound_levers=confound)
        tol = max(1, int(CLICK_DRIVEN_MAX_UNCLICKED_FRAC * len(active))) if active else 0
        if clicked_active2 and len(unclicked_active) <= tol:
            # CLICK-DRIVEN: fires only when a member is clicked (not click-independent),
            # once presses independently explained by another confirmed lever are set
            # aside. The acted member is the lever, its partner the reactive.
            if lever in marginal_counters:
                # The acted member is schedule-autonomous. The pair licenses no lever, and
                # therefore no reactive either — a partner cannot be the effect of a cause
                # that was never admitted. Recorded on the counter's own verdict, never
                # dropped silently.
                excluded_lever[lever] = (reactive, p)
                continue
            lever_of.setdefault(lever, []).append((reactive, p))
            reactive_of.setdefault(reactive, []).append((lever, p))
        else:
            # AUTONOMOUS / click-independent stable relay: both members are COUNTER
            counter_of.setdefault(a, p)
            counter_of.setdefault(b, p)

    return PairVerdicts(counter_of, lever_of, reactive_of, excluded_lever)
