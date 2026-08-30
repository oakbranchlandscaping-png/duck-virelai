"""WO_COUPLING_R2_ROLE_REWIRE · coupling-grounded role inference (CHARTER_COUPLING_LAW R2).

infer_roles now CONSUMES ``build_coupling`` — the pair-motion law is the substrate for the
role read, replacing the R1 reactive-complement heuristic. The two confounds that started
this thread are resolved at the mechanism level:

  · COUNTER over-fire (fired on backgrounds) → a COUNTER is now a member of a STABLE coupled
    relay that fires CLICK-INDEPENDENT (moves on presses where it was not the acted member).
    A ``complement_ids`` member (the loose dependent residual) is typed DEPENDENT and
    consciously ignored — never COUNTER, never dropped.
  · LEVER/REACTIVE confounded by global churn → LEVER/REACTIVE now require a STABLE COUPLED
    PAIR that is CLICK-DRIVEN (fires on the presses where a member was clicked), not mere
    co-occurrence with a click. The lever is the pair's acted member; the partner is reactive.

STATIC / EGO-out-of-input / UNKNOWN are unchanged from the R1 role logic.

DERIVED-NOT-STORED, WEAVE-NATIVE: reads only the weave (build_coupling + acted_on); writes
nothing; no Store-A, no LibraryObject, no is_background, no size-prior. Dossier-only, no
dispatch (the dispatch seam is later).
"""

from __future__ import annotations

# WO-COUNTER-EXCHANGE-01 · the compensating line for this rung's new import. `replace`
# and `dataclass` stood as two separate imports of ONE module, two lines apart. Collapsed
# into one — no predicate, no ordering and no name changed, and the ratchet is paid from
# redundancy rather than from a shortened conditional.
from dataclasses import dataclass, replace
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from virelai_v4.weave.edge import Verb
from virelai_v4.weave.action_roster import (acted_on, heart_boundary_edges,
                                            life_boundary_edges)
from virelai_v4.weave.coupling import build_coupling, COUPLE_CORR
from virelai_v4.weave.ego_read import action_bearings, channel_a_witness, ego_basis, ego_parallax, ego_seal
from virelai_v4.weave.ego_field import (
    ego_field_seal, field_basis, field_parallax, field_read,
)
from virelai_v4.weave.exchange_read import exchange_note, exchange_seal
from virelai_v4.weave.ground_read import ground_read
from virelai_v4.weave.nav_target import sealed_egos, with_directional
from virelai_v4.weave.wall_read import wall_read
from virelai_v4.weave.medium import (
    medium_basis, medium_parallax, medium_seal, medium_witnesses,
)
# WO-INFER-ROLES-EXTRACT-01 · re-exported so every existing reference to these three
# resolves unchanged — they moved with the subject that owns them, not away from callers.
from virelai_v4.weave.pair_classify import (          # noqa: F401  (re-export)
    CLICK_DRIVEN_MAX_UNCLICKED_FRAC,
    PairVerdicts,
    _click_driven_split,
    _lever_reactive_candidate,
    classify_pairs,
)
from virelai_v4.weave.lever_witness import (
    no_effect_note, no_effects, witness_basis, witness_parallax, witnessed_levers,
)


# ---------------------------------------------------------------------------
# WO-BAND-SPLIT-01 · TWO BANDS, NAMED CORRECTLY
# ---------------------------------------------------------------------------
#
# Canon has two bands, and this module emitted ONE value from a mixed list.
#
#   BAND 1 — SELF-STATE. Read off the SETTLED RECORD, before any probing: does this
#            object change? {STATIC, REACTIVE}. An observation, not an inference.
#   BAND 2 — THE ROLE, derived from the mechanic stratum: EGO · COUNTER · LEVER ·
#            ENVIRONMENTAL FORCE · REACTIVE-DRIVEN · INERT.
#
# A reader could not tell "never changes" from "we know what it is". That is a category
# error, not a naming disagreement, and it shows: the recolor canary reads STATIC/FIRM=56
# — fifty-six objects whose Band 1 is STATIC and whose Band 2 is genuinely EMPTY, clicked
# once each, coverage nowhere near INERT's exhaustive-interaction bar.
#
# WHAT THIS RUNG DOES: adds Band 1, renames DEPENDENT → REACTIVE-DRIVEN (R-3), retires
# UNKNOWN as a role (R-4 — Band 2 empty is ∅ WITH ITS COVERAGE, never a leaf), and renders
# both bands as the distinct claims they are.
#
# WHAT IT DELIBERATELY DOES NOT DO — the interim, ruled rather than assumed. `STATIC` and
# `REACTIVE` STAY in the Band-2 slot for now. WO-BAND-SPLIT-01 v1 would have vacated them;
# Cowork's halt found that `STATIC` is not merely a misplaced name but a LIVE BELIEF-WRITE
# INPUT — `weave_role_landing` maps it to `LibraryRole.STATIC`, which feeds
# `static_log_score`, which `store_a_role_verdicts` argmaxes over, which IS the integration
# roster's role slot. Vacating it starves that axis of 56 verdicts per life and silently
# moves 56 roster lines. CE ruled: the work order that empties the slot must be the one
# that decides where the evidence goes instead. That is WO-STATIC-VACATION-01, queued.
# Until it lands, these two are Band-2 values marked INTERIM here and in the render, with
# the reason named — visible drift beats invisible drift.

# BAND 1 — self-state. The parent tag, read beneath the mechanic layer.
BAND1_STATIC, BAND1_REACTIVE = "STATIC", "REACTIVE"

# BAND 2 — the role. `UNKNOWN` is retired as a value (R-4): an empty Band 2 is `None`,
# rendered `∅`, and always accompanied by its coverage. It is not a leaf and never a
# sole-terminal answer. `DEPENDENT` is renamed `REACTIVE-DRIVEN` (R-3) — same archetype,
# drifted name. `STATIC`/`REACTIVE` remain here on the interim above.
# WO-INERT-CERTIFICATE-01: INERT joins as an emitted value (R-1, R-5). It is sole-exclusive
# and PROVISIONAL-only at this rung — see `_inert_seal`.
(STATIC, COUNTER, LEVER, REACTIVE, EGO, REACTIVE_DRIVEN, INERT, UNKNOWN) = (
    "STATIC", "COUNTER", "LEVER", "REACTIVE", "EGO", "REACTIVE-DRIVEN", "INERT", "UNKNOWN")
# The two Band-1 names still sitting in the Band-2 slot, named once so the render and the
# tests read the same list rather than each hard-coding it.
# WO-STATIC-VACATION-01: STATIC vacated; REACTIVE alone remains interim.
BAND2_INTERIM_BAND1_NAMES = frozenset({REACTIVE})
FIRM, PROVISIONAL, OUT_OF_INPUT = "FIRM", "PROVISIONAL", "OUT_OF_INPUT"


@dataclass(frozen=True)
class RoleVerdict:
    worldline_id: int
    # BAND 2 — the role. `None` means ∅: no role earned, coverage stated beside it.
    # Kept as `role` rather than renamed to `band2` so the field name does not churn every
    # construction site — including `library/store_a_role_read.py`, a SECOND producer of
    # this type that lies outside this rung's fence. `.band2` below is the reading name.
    role: Optional[str]
    confidence: str
    basis: str           # the human-gradable evidence sentence (cites the coupling)
    # WO-W2-C-01 · where two independent computations of the same fact disagree, the
    # divergence is RECORDED and routed, never silently reconciled
    # (RULING_OBSERVERS_INTEGRATOR_v1 §1). Empty when there is nothing to report.
    parallax: str = ""
    # WO-BAND-SPLIT-01 · Band 1, additive and defaulted so every existing construction
    # site — here and in `store_a_role_read.py` — keeps working untouched. Empty string
    # means "not observed", which is distinct from either tag and must never render as one.
    band1: str = ""
    band1_coverage: int = 0     # steps the self-state was observed over — part of the claim
    # WO-BAND-1-REVISIT-01 · RENAMED FROM `band1_flashes`, because it never measured what
    # that name claimed. It counts SETTLED-STATE REVISITS — steps that returned to a
    # fingerprint the worldline already held. It is not canon §3's transient excursion:
    # this predicate reads `Worldline.steps`, which is built from the VISIBLE LAYER only
    # (`capture/ledger_build.py:49`), and a transient lives in the frames beneath it.
    # Render-only; no predicate consumes it. See `_settled_revisits`.
    band1_revisits: int = 0
    # WO-GROUND-01 · THE GROUND CLAIM, ADDITIVE AND DEFAULTED on `WO-BAND-SPLIT-01`'s
    # precedent — 0 of 14 construction sites here and in `store_a_role_read.py` change,
    # and the Band-2 menu stays closed at six. **It is a FIELD, not a role and not a
    # sub-class in prose**, because `masked_worldlines` must ask *is this ground* of the
    # value: the medium sub-class lives in its basis and every consumer that wants it has
    # to parse text, which is the cost this one does not pay. `False` means "not typed",
    # which is distinct from "typed and refused" — nothing writes the latter, and no
    # consumer may read one as the other. See `weave/ground_read.py` for the predicate.
    ground: bool = False
    ground_basis: str = ""
    # WO-WALL-01 · the same shape one field over. `False` means "not typed"; nothing
    # writes "typed and refused". See `weave/wall_read.py` for the two conjuncts.
    wall: bool = False
    wall_basis: str = ""

    @property
    def band2(self) -> Optional[str]:
        """The role, by its canonical band name. `None` is ∅."""
        return self.role


def _acted_by_press(cuts, node_actions, worldlines):
    """Per press-edge (left→right), the ### acted_on that press (resolved @cut[left], the
    wiring law), keyed by the LEFT node index — the same press index build_coupling uses."""
    ordered = sorted(cuts, key=lambda c: c.node_index)
    nodes = [c.node_index for c in ordered]
    cbi = {c.node_index: c for c in cuts}
    out: Dict[int, Any] = {}
    for left, right in zip(nodes, nodes[1:]):
        aid, target = node_actions[right] if 0 <= right < len(node_actions) else (None, None)
        res = acted_on(right, aid, target, cbi, worldlines) if aid == 6 else None
        out[left] = res.worldline_id if (res is not None and res.status == "RESOLVED") else None
    return out


def _clicks_by_wl(cuts, node_actions, worldlines) -> Dict[int, set]:
    """Which nodes clicked each ### (resolved against cut[t-1], the wiring law)."""
    cbi = {c.node_index: c for c in cuts}
    clicked: Dict[int, set] = {}
    for c in cuts:
        t = c.node_index
        aid, target = node_actions[t] if 0 <= t < len(node_actions) else (None, None)
        res = acted_on(t, aid, target, cbi, worldlines)
        if res.status == "RESOLVED":
            clicked.setdefault(res.worldline_id, set()).add(t)
    return clicked


# ---- WO-BAND-SPLIT-01 · THE BAND-1 PREDICATE ---------------------------------
#
# Canon §1: "does this object change?" — pure, belief-free, off the SETTLED RECORD.
#
# WHY NOT `churned`. It was the obvious candidate and this rung's premise check rejected
# it, deliberately. `churned` reads `PanelRow.changed_presses > 0`: a count of PRESSES on
# which the frame changed, computed over the press series and sourced from the magnitude
# channel — i.e. arriving through `build_coupling`, from the MECHANIC stratum. Two
# consequences, both disqualifying:
#
#   1. It cannot express canon §3's ANIMATION LAW. A transient excursion that settles back
#      registers as two changed presses, so a flash would flip Band 1 — which canon
#      forbids outright: "a flash is recorded BESIDE the tag, never merged into it."
#   2. It would derive the PARENT tag from the CHILD stratum, inverting the very band
#      ordering this split exists to establish. Band 1 sits beneath the mechanic layer;
#      reading it through the coupling panel makes it an inference wearing an
#      observation's name.
#
# So Band 1 reads the worldline's OWN step record — the settled sighting fingerprints,
# available directly on `Worldline.steps`, beneath every rung above it. No coupling, no
# marginal, no panel, no belief.

def _settled_revisits(fps: List[Any]) -> int:
    """How many steps returned to a fingerprint this worldline had already held.

    A COUNT, NOT A CLASSIFICATION. It decides nothing — no predicate reads it, and Band 1
    is computed without it. It exists so a reader can tell an object cycling among a few
    states apart from one marching monotonically through many, which the tag alone cannot
    say. Extracted rather than inlined (THE INTERLEAVING BAN) so the tag's rule stays one
    line and this stays separable.
    """
    seen, revisits = set(), 0
    for fp in fps:
        if fp in seen:
            revisits += 1
        seen.add(fp)
    return revisits


def _band1_self_state(wl) -> Tuple[str, int, int]:
    """(band1, coverage, settled-state revisits) for one worldline, from its record alone.

    Canon §1: *does this object change?* The fingerprint is the visual object's own
    identity — `(class_id, cells)`, exactly the pair `SPEC_SIGHTING_LEDGER` makes the atom
    of a sighting. **A worldline whose steps are all one fingerprint never changed:
    BAND1_STATIC. Otherwise BAND1_REACTIVE.** No exemption, no skip, no lookahead.

    WO-BAND-1-REVISIT-01 · WHAT WAS REMOVED, AND WHY IT WAS WRONG.
    This carried a flash exemption: a step differing from its predecessor whose successor
    returned to that predecessor was called a transient, dropped from the distinctness
    test, and counted separately. On an ALTERNATING sequence the exemption consumed the
    whole run — `i += 2` ate each excursion *and* its return — so

        A → B → A → B → A → B → A     7 steps; the object MOVES on every one
        →  ('STATIC', 7, 3)

    **Band 1 inverted on exactly the class of object it exists to describe.** Band 1 prunes
    the assertable role menu (`STATIC → {LEVER(remote), INERT}`), so an oscillator was
    pruned to *inert or remote lever* before any role was considered. Measured on a real
    worldline: a piece stepping away from a home cell and back, 16 distinct anchors,
    constant class and cell-count, read STATIC with 14 "flashes" (`WO_READ_A_01_RETURN` §4).

    WHY THE EXEMPTION CANNOT BE REPAIRED HERE, stated so a future chamber finds the reason
    rather than the absence. Canon §3's animation law is real and the platform really has
    transients: `ARC_3_Official` §2.3.1 — *"the agent receives a frame or frame sequence;
    frame sequences allow for non-interactive animations between player turns."* Those
    frames ARE captured — `capture/frame_record.py` is lossless over every layer. But
    `capture/ledger_build.py:49` takes `log.reconstruct(node)[-1]`, **the visible layer**,
    and the ledger this predicate reads is built from that alone. So a transient never
    reaches `Worldline.steps`, and no predicate over `Worldline.steps` can see one.
    **The law is implementable — over the capture, not over this input.** That is a
    capture/ledger rung and it is outside this fence. Until it lands, a settle-back
    observed here is a settled-state revisit and nothing more, which is what the returned
    count is now named for.

    COVERAGE IS PART OF THE CLAIM. STATIC over three observed steps is not STATIC over a
    hundred, and the returned count travels with the tag into the render — the same
    discipline the two marginal seals already carry. A single-step worldline has nothing to
    compare and returns coverage 1 with no tag at all: `("", 1, 0)`. An absent observation
    must never render as either tag.
    """
    steps = getattr(wl, "steps", ()) or ()
    if len(steps) < 2:
        return "", len(steps), 0

    fps = [(r.class_id, r.cells) for (_n, r) in steps]
    band1 = BAND1_STATIC if len(set(fps)) == 1 else BAND1_REACTIVE
    return band1, len(steps), _settled_revisits(fps)


# ---- WO-W2-C-01 · COUNTER from the marginal ----------------------------------
#
# THE SEAL IS A ∀-WITNESS, NOT A CUTOFF. `AMENDMENT_PROBE_STRATEGY_v1` Clause B:
# "Resolution is never a confidence score crossing a threshold. No threshold constant,
# no dwell-time parameter, no hysteresis band exists anywhere in the descent trigger."
# So the discriminator here is not "independence is high enough" — it is exhaustion over
# a recorded set, the universal half of `NESTED_TAXONOMY_SPEC_v5` §4's ∃/∀ law ("the
# claim holds of the whole only if it holds of every member; one counter-witness kills
# it"), the same shape §6 already ratifies for INERT ("assertable from tried-everything
# quiet"):
#
#   COUNTER seals iff, over a NON-EMPTY set of presses where an action fired and did NOT
#   target this worldline, it moved on EVERY one — AND that set, together with the presses
#   that did target it, covers every press the worldline was LIVE for (the coverage
#   certificate, see `_marginal_counter_seal`). Channel-exclusion applies first: a
#   worldline already explained by a measured coupling is channel (c), not channel (b).
#
#   WO-W2-C-01b: the certificate's denominator is the worldline's OWN live window
#   (`PanelRow.live_presses`), not the global one. C-01 measured a re-minted worldline
#   against a window it did not exist in and blocked witnesses that were complete over
#   every press their subject could have moved on. Ruled at C-01a; the denominator is
#   carried by the marginal stratum that owns it, and received here.
#
# That is `FOUNDATIONAL_ARCHETYPES_v2` §2's defining observable stated as a predicate:
# "it ticks because time passed or actions were spent — not because of WHICH action."
# Three properties make it a seal rather than a threshold:
#   * There is no constant to choose. 1.0 is the boundary of the rate's domain, not a
#     cutoff inside it; "every" is not "enough". Exact, too: `_action_marginal` computes
#     `moved / n` by integer division-to-float, and IEEE-754 gives `n/n == 1.0` exactly
#     and `a/b < 1.0` strictly for a < b — so the equality IS the integer predicate
#     `moved == n`, not a tolerance.
#   * One counter-witness kills it — the bucket-drain law at this rung.
#   * The non-empty requirement is not a dwell time. ∀ over ∅ is vacuously true, so
#     excluding the empty set is a logical guard; an abstention (-1.0) types nothing.
# Coverage is reported, never converted into confidence: the denominator travels in the
# basis so a reader sees how much the ∀ ranged over ("confidence is coverage").

def _marginal_counter_seal(row) -> bool:
    """The ∀-witness over the un-targeted press set, PLUS a coverage certificate.

    Exhaustion, not magnitude — and exhaustion over the worldline's OWN observed window,
    not a sliver of it. The second conjunct (`untargeted + targeted == live_presses`) says
    every press this worldline was live for also fired an action, so the ∀ ranges over its
    entire life rather than a fragment. Without it, a worldline in a window where only ONE
    press carried an action seals on that single press — mere co-occurrence with a click
    wearing a quantifier, i.e. exactly the global-churn confound this module exists to kill
    (the committed `test_t5_cooccurring_churner_not_lever_or_reactive` is that constraint,
    and it caught this seal's first form; see WO-W2-C-01's return §0.4).

    WO-W2-C-01b — the denominator is `live_presses`, the worldline's own live window,
    received from the marginal stratum that owns it. C-01 compared against the GLOBAL
    window and so measured a re-minted worldline against presses it did not exist in,
    blocking witnesses that were complete over every press their subject could have moved
    on. Ruled at C-01a. Nothing else in the seal moved.

    This is a coverage certificate, not a dwell time: no constant is chosen, nothing is
    tuned, and the quantity compared against is the subject's own live window. It is
    `FOUNDATIONAL_ARCHETYPES_v2` §6's ratified shape for INERT — "assertable from
    tried-everything quiet" — applied to ticking instead of quiet, and it inherits §6's
    honesty too: the verdict is coverage-bounded and reopens when coverage changes.

    The cost, stated rather than hidden: one press the worldline was live for that carried
    no producing action voids the seal. That is deliberately conservative — it can only
    ever type FEWER counters than the bare ∀-witness, never more."""
    covered = (row.untargeted_presses + row.targeted_presses) == row.live_presses
    return row.untargeted_presses > 0 and row.action_independence == 1.0 and covered


# WO-LOCAL-LEVER-01 · the mirror of the seal above, on the other channel.
#
# `SPEC_PIXEL_ARITHMETIC_v1` §3 names four answers to "what does this worldline's
# arithmetic key on": WHICH action, THAT ANY action, ANOTHER worldline's arithmetic, or
# nothing. The seal above reads the second. `lever_of` reads the third. **The FIRST had
# no reader at all** — `role_read` emitted LEVER only from `lever_of`, populated only from
# click-driven stable PAIRS, so a lever whose effect lands on its own cells had no remote
# partner and therefore no path to a verdict. Not a threshold problem; there was no branch.
#
# `FOUNDATIONAL_ARCHETYPES_v2`, quoted by `coupling.py`'s own marginal header: "A clock
# reads independence ~1 (it moves whoever was targeted). A lever reads independence ~0 and
# dependence ~1. The pair is what separates them — neither reading alone does." This seal
# reads that pair.

# The FIRM bar. Deliberately NOT a new constant: this is `role_read`'s own existing
# evidentiary bar for "confidently, repeatedly, deliberately targeted" (the LEVER branch's
# `conf = FIRM if len(wl_clicks) >= 2`), which `weave/repeated_contact.py` also cites
# rather than re-deriving. Two observations IS thin, and this WO's return says so plainly;
# inventing a higher floor here would be a tuned constant with no evidence behind it, which
# is the worse error. Confidence follows coverage — below the bar the verdict is
# PROVISIONAL, never withheld and never over-claimed.
LOCAL_LEVER_FIRM_PRESSES: int = 2


def _marginal_local_lever_seal(row) -> bool:
    """The ∀-witness over the TARGETED press set, plus the same coverage certificate.

    Deliberately the exact mirror of `_marginal_counter_seal` — same shape, same
    certificate, same conservatism — because the two are one distinction read from two
    sides, and a witness built to a different standard than its twin would make the
    comparison meaningless.

      · ∀ over targeted: `action_dependence == 1.0` — moved on EVERY press that hit it.
      · ∀ over un-targeted: `action_independence == 0.0` — moved on NONE that did not.
      · `targeted_presses > 0` — the mirror of the seal's `untargeted_presses > 0`.
      · the same coverage certificate: every press this worldline was live for also fired
        an action, so the ∀ ranges over its whole life rather than a fragment.

    `-1.0` IS NOT ZERO, and both conjuncts depend on it. `_action_marginal` returns -1.0
    for an empty denominator, so a worldline with no un-targeted presses reads
    `independence == -1.0` and fails this seal — correctly: "never moved when untouched"
    is unclaimable about a worldline that was never untouched. The same holds for
    dependence. A measured 0.0 and an absent reading must never be conflated; that
    conflation is the exact defect WO-MARGINAL-CHANNEL-01 was chartered to fix.

    WHAT THIS WITNESS DOES NOT ESTABLISH, stated rather than closed by naming: the marginal
    is CORRELATIONAL. `depend == 1.0` says the object changed on every press that targeted
    it — not that the click CAUSED the change rather than merely accompanying it. The
    archetype is causal; this evidence is not. A worldline that happens to change on a
    schedule that coincides with its own click pattern would satisfy this seal. The
    coverage certificate and the ∀-over-un-targeted conjunct together make that coincidence
    expensive, not impossible."""
    covered = (row.untargeted_presses + row.targeted_presses) == row.live_presses
    return (row.targeted_presses > 0
            and row.action_dependence == 1.0
            and row.action_independence == 0.0
            and covered)


# ---- WO-INERT-CERTIFICATE-01 · THE HONEST NULL --------------------------------
#
# `INERT` is one of the six ratified archetypes and no code path emitted it. After
# WO-STATIC-VACATION-01 the 56 quiet worldlines on the recolor canary read `B2:∅` — honest
# and incomplete. Canon has a name for a worldline that does nothing and causes nothing.
#
# THE PRICE, and it is the whole rung (`FOUNDATIONAL_ARCHETYPES_v2` §6): "the observable is
# as much about the COVERAGE as the silence: inert is never assertable from quiet alone; it
# is assertable from TRIED-EVERYTHING quiet." So the deliverable is the CERTIFICATE, not the
# verdict. Most worldlines will not qualify, and that is the correct outcome — the rung
# turns an undifferentiated `∅` into either `INERT` with its evidence, or `∅` with a stated
# reason it is not yet `INERT`.
#
# WHAT THE RECORD CAN AND CANNOT SUPPORT — answered before building to it, because a
# certificate claiming exhaustiveness the record cannot back is the mythology failure in the
# one place canon most warns against it:
#
#   * ONLY ACTION6 IS AIMABLE. `action_roster.resolve_action` returns NON_TARGETED for any
#     action without a target cell, so directionals cannot be "tried AT" a worldline at all.
#     The set of action CLASSES aimable at one worldline has size ONE. Canon's "every
#     applicable action tried at it" therefore cannot mean an enumeration over aimable
#     classes — there is only one.
#   * BUT THE OFFERED SET IS ENUMERABLE. `NodeCut.available_actions` carries what the
#     platform offered, and it is populated and world-specific (one canary offers a click
#     only; another offers directionals and NO click at all). So the honest enumeration is:
#     of the actions this world OFFERED, which fired while this worldline was live — and,
#     separately, how many were AIMED at it.
#   * REPETITION IS A COUNT, NOT AN EXHAUSTION. Two clicks is not "tried everything", and no
#     amount of clicking at one cell proves the object was probed exhaustively.
#
# CONSEQUENCE, STATED RATHER THAN ENGINEERED AROUND: **`INERT` is PROVISIONAL, always, at
# this rung.** The class enumeration is real; the interaction exhaustion is not. A FIRM
# `INERT` would claim a coverage the record cannot produce. When the taxonomy grows a real
# probe-progression for the STATIC branch, the bar can rise and the confidence with it.
#
# `INERT` IS SOLE-EXCLUSIVE (canon §2, §6) — it co-exists with no other Band-2 value, which
# is why the seal sits at the BOTTOM of the ladder: everything above it is an earned
# archetype, and reaching this branch already means none was earned.
#
# `INERT` IS REOPENABLE. "A coverage-bounded verdict, never permanent — a black swan reopens
# it without ceremony." The certificate is a RECORD OF WHAT WAS TRIED, so a later, wider
# enumeration voids it. There is deliberately NO LATCH: nothing here is remembered across
# calls, and a press that moves the worldline kills the seal on the next read.

# The non-vacuity bar for aimed presses. NOT a new constant: this is `role_read`'s own
# existing bar for "confidently, repeatedly, deliberately targeted"
# (`LOCAL_LEVER_FIRM_PRESSES`), reused rather than minted. It guards vacuity — ∀ over ∅ is
# vacuously true — and does NOT claim exhaustion; see the PROVISIONAL note above.
INERT_MIN_AIMED_PRESSES: int = LOCAL_LEVER_FIRM_PRESSES


def _interaction_certificate(row, wl_clicks, offered, fired_while_live) -> Dict[str, Any]:
    """What was tried at and around this worldline — the record canon prices INERT against.

    Returns the evidence, never a verdict. It is built for EVERY Band-2 `∅`, whether or not
    the seal fires, because "not yet enough evidence" and "evidence of nothing" are
    different claims and an undifferentiated `∅` cannot tell them apart.

      aimed          — presses that targeted this worldline (ACTION6 resolved to it)
      offered        — the action ids this world offered, from `NodeCut.available_actions`
      exercised      — those offered ids that actually fired during its live window
      missing        — offered minus exercised: the named gap, so a reader sees what a
                       wider enumeration would have to cover before INERT could firm
      covered        — the same coverage certificate the other two seals use: every press
                       it was live for also fired an action, so the ∀ ranges over its whole
                       life rather than a fragment
    """
    return {
        "aimed": row.targeted_presses,
        "clicks": len(wl_clicks or ()),
        "offered": tuple(sorted(offered)),
        "exercised": tuple(sorted(fired_while_live)),
        "missing": tuple(sorted(set(offered) - set(fired_while_live))),
        "covered": (row.untargeted_presses + row.targeted_presses) == row.live_presses,
        "live": row.live_presses,
    }


def _inert_seal(row, band1: str, cert: Dict[str, Any], causes_nothing: bool) -> bool:
    """The ∀-witness for INERT, mirroring `_marginal_counter_seal` and
    `_marginal_local_lever_seal` rather than inventing a third standard — the three are one
    taxonomy read from three sides, and a witness built to a different bar makes them
    incomparable.

    The conjuncts, from `FOUNDATIONAL_ARCHETYPES_v2` §6:

      · BAND 1 IS STATIC. The STATIC parent prunes the assertable menu to
        {LEVER(remote), INERT}; a worldline that changes cannot be inert. Band 1 is READ,
        never re-derived — it is an observation off the settled record and re-deriving it
        here would be the band inversion WO-BAND-SPLIT-01 exists to prevent.
      · NO ATTRIBUTED EFFECT. It caused nothing elsewhere. **This is the sharpest
        false-positive risk in the whole seal**: a REMOTE LEVER is STATIC and silent about
        itself while causing everything, and canon's cross-branch case says it is not inert.
      · MOVED ON NOTHING. `action_dependence == 0.0` (never moved when aimed at) AND
        `action_independence == 0.0` (never moved when anything else fired). Exact, for the
        same IEEE-754 reason the counter seal's `== 1.0` is exact.
      · EVERY OFFERED ACTION EXERCISED during its live window — the real enumeration, over
        what the world offered rather than over an invented set.
      · NON-VACUITY: at least `INERT_MIN_AIMED_PRESSES` presses actually aimed at it. ∀ over
        ∅ is vacuously true, and `-1.0` is an ABSENT reading, never a measured 0.0.
      · The shared coverage certificate.
    """
    if band1 != BAND1_STATIC or not causes_nothing:
        return False
    if cert["aimed"] < INERT_MIN_AIMED_PRESSES or cert["missing"]:
        return False
    if not cert["covered"]:
        return False
    # BOTH denominators must be non-empty, and this is the seal's own non-vacuity rule
    # rather than an accident of the equality below. The counter seal requires
    # `untargeted > 0`; the local-lever seal requires `targeted > 0`; INERT claims silence
    # across BOTH populations, so it requires both. A worldline aimed at on every single
    # press was never observed while something ELSE was acted on — it has not been "tried
    # everything", however quiet it was.
    if row.targeted_presses <= 0 or row.untargeted_presses <= 0:
        return False
    # -1.0 is an ABSENT reading, never a measured 0.0. The guard above already excludes it;
    # the exact equalities below would reject it anyway, and both are kept deliberately —
    # the guard states the rule, the equality enforces it.
    return row.action_dependence == 0.0 and row.action_independence == 0.0


def _certificate_str(cert: Dict[str, Any]) -> str:
    """The certificate as one readable clause, rendered whether or not the seal fired.

    A worldline that fails the bar must say WHY — which is the difference between a rung
    that made the gap legible and one that merely stayed quiet about it."""
    off = ",".join(str(a) for a in cert["offered"]) or "—"
    exd = ",".join(str(a) for a in cert["exercised"]) or "—"
    miss = ",".join(str(a) for a in cert["missing"])
    parts = [f"aimed {cert['aimed']}× (bar {INERT_MIN_AIMED_PRESSES})",
             f"actions offered [{off}] exercised [{exd}]"]
    if miss:
        parts.append(f"NEVER TRIED [{miss}]")
    parts.append(f"coverage {'complete' if cert['covered'] else 'PARTIAL'} "
                 f"over {cert['live']} live presses")
    return "coverage: " + " · ".join(parts)


def _counter_evidence(wid, row, pair, in_proxy: bool):
    """(basis, parallax) for a COUNTER verdict. Both computations are reported; where
    they disagree the divergence is named and NEITHER is dropped."""
    sealed = _marginal_counter_seal(row)
    parts = []
    if sealed:
        parts.append(f"marginal: moved on ALL {row.untargeted_presses} fired presses that "
                     f"did not target it — every press it was live for "
                     f"(∀-witness + full live-window coverage, {row.live_presses} live) → schedule-autonomous")
    if pair is not None:
        other = pair.wid_b if pair.wid_a == wid else pair.wid_a
        parts.append(f"pair: click-independent stable relay w/ ###{other:03d} "
                     f"(k={pair.ratio_k:+.2f}, corr={pair.corr:+.2f})")
    basis = " · ".join(parts) + " → COUNTER"

    if sealed and pair is not None:
        parallax = "marginal and pair agree"
    elif sealed:
        parallax = ("marginal sealed, pair did not — no STABLE click-independent relay "
                    "names this worldline; counter_of is populated only from report.pairs, "
                    "so a clock with no partner (or only an unstable one) is invisible to it")
    else:
        parallax = (f"pair sealed, marginal did not (indep={row.action_independence:.3f} "
                    f"over {row.untargeted_presses} un-targeted presses; coverage "
                    f"{row.untargeted_presses + row.targeted_presses} of "
                    f"{row.live_presses} live presses) — recorded, not reconciled")
    if in_proxy:
        parallax += ("; the complement proxy said REACTIVE-DRIVEN — the measured verdict stands, "
                     "the proxy is participants−coupled_members and not §5's fitted dependence")
    return basis, parallax


# ---- WO-W2-C-02 · the lever states its prediction ----------------------------
#
# SPEC_MECHANIC_LAYER_v1 §7, verbatim: "Every committed mechanic carries a forward
# prediction: given one member's next delta, the relation predicts the others' (for a
# conserved pair, the negation; in general, THE FITTED DEPENDENCE). ... A mechanic that
# cannot state its prediction is not admissible."
#
# §7 names the fitted dependence as the prediction's own content, so a stable fitted ratio
# IS admissible evidence — what was missing was the STATEMENT. The retired basis said
# "couples k=+1.00 on click": a description of presses already observed, carrying no claim
# about an unobserved one and no death condition. §7 requires both.
#
# DIRECTION MATTERS AND IS NOT THE ROLE'S. `_ratio_k` fits `d(wid_a) ≈ k · d(wid_b)`
# (coupling.py: `a = ids[i]`, `b = ids[i + 1:]`, `k = _ratio_k(da, db)`), and the elected
# lever may be EITHER member. So the prediction is stated in the pair's own (a, b) terms,
# where it is unambiguous, rather than as "lever → partner", which would silently invert
# on half the pairs.
#
# THE SECOND DEATH CLAUSE IS EARNED FROM THE CODE, NOT ADDED FOR RHETORIC.
# `_ratio_stability` computes the per-press ratio only `if b[i] != 0` — over presses where
# wid_b moved, and it needs at least two or it returns inf. The fit therefore never ranged
# over presses where wid_a moves while wid_b holds. Such a press is an unobserved regime,
# and §7's "descends to a finer statement" is exactly what it would force.

def _lever_prediction(p) -> str:
    """§7's forward prediction for one coupled pair, with its death condition."""
    return (f"PREDICTS d(###{p.wid_a:03d}) = {p.ratio_k:+.2f}·d(###{p.wid_b:03d}) on the "
            f"next press (fitted across the {p.active_presses} presses where either moved; "
            f"the per-press ratio held over those where ###{p.wid_b:03d} moved) · "
            f"DIES on the first press whose joint delta contradicts it, or on a press where "
            f"###{p.wid_a:03d} moves while ###{p.wid_b:03d} holds — a regime the fit never "
            f"ranged over")


def _counter_exclusion_note(wid, excluded_lever) -> str:
    """The parallax suffix recording a LEVER candidacy denied by channel exclusivity.
    Empty when this worldline was never elected. The denial is REPORTED, never dropped
    (RULING_OBSERVERS_INTEGRATOR_v1 §1)."""
    if wid not in excluded_lever:
        return ""
    reactive, p = excluded_lever[wid]
    return (f"; also the elected acted member of a click-driven stable pair with "
            f"###{reactive:03d} (k={p.ratio_k:+.2f}, corr={p.corr:+.2f}) — LEVER candidacy "
            f"excluded by channel exclusivity, and the pair licenses no REACTIVE without "
            f"an admitted cause")


def _local_lever_exclusion_note(wid, excluded_counter) -> str:
    """The mirror suffix: a COUNTER verdict this worldline's own marginal displaced.

    WO-LOCAL-LEVER-01. Three worldlines on the recolor canary reach the COUNTER branch
    through the pair path's "click-independent stable relay" while their own marginal reads
    `depend == 1.0` — direct evidence they are NOT click-independent. The relay reached that
    conclusion without ever consulting the marginal, and the measured ∀-witness outranks it.

    **But the disagreement is real and travels with the verdict rather than being reconciled
    away** (RULING_OBSERVERS_INTEGRATOR_v1 §1), exactly as `_counter_exclusion_note` does for
    the denial running the other way. A reader must be able to see that two computations
    disagreed, and which one was taken."""
    if wid not in excluded_counter:
        return ""
    p = excluded_counter[wid]
    return (f"; also a member of a stable relay the pair path read as click-INDEPENDENT "
            f"(k={p.ratio_k:+.2f}, corr={p.corr:+.2f}) — COUNTER displaced by this "
            f"worldline's own marginal, which measured it moving on every press that "
            f"targeted it; the pair read never consulted the marginal")






# ---- WO-LEVER-WITNESS-01 · THE RATCHET, PAID -------------------------------------
#
# `infer_roles` was 171 body lines at this rung's anchor — already RED (151-250). The
# witness branch added 8, which the ratchet forbids without compensating extraction
# net-zero-or-better by exit. These three are that compensation. Each is a single
# responsibility lifted whole, byte-neutral in output, and each is separately testable —
# extraction the tier system was asking for, not padding to clear a number.

def _offered_and_fired(cuts, node_actions):
    """`(offered_action_classes, {node_index: action_id or None})` — the world's OWN offer
    and what actually fired at each node. Read from `NodeCut.available_actions`, the
    platform's offer rather than an invented menu; keyed by node so a worldline's live
    window can be intersected against it without re-walking the cuts per worldline."""
    offered = {a for c in cuts for a in (c.available_actions or ())}
    fired = {c.node_index: (node_actions[c.node_index][0]
                            if 0 <= c.node_index < len(node_actions) else None)
             for c in cuts}
    return offered, fired


def _certificate_for(wl, row, wl_clicks, offered, fired_by_node):
    """The interaction certificate for ONE worldline, over ITS live window — the offered
    classes intersected with what fired while it existed. "Not yet enough evidence" and
    "evidence of nothing" are different claims, and the certificate is what tells them
    apart."""
    live_nodes = {n for (n, _r) in wl.steps}
    fired_live = {a for n, a in fired_by_node.items()
                  if n in live_nodes and a is not None}
    return _interaction_certificate(row, wl_clicks, offered, fired_live)


def _lever_pair_basis(causes) -> str:
    """The pair-based LEVER's evidence sentence. WO-LEVER-SUBTREE-05 Defect 2: a lever may
    have MORE than one confirmed reactive partner; every one is named, none silently
    dropped. The single-partner wording is byte-for-byte what it has always been — a test
    pins it — and the multi-partner branch is the additive case."""
    if len(causes) == 1:
        reactive, p = causes[0]
        return (f"acted member of click-driven stable pair; partner ###{reactive:03d} "
                f"couples k={p.ratio_k:+.2f} on click → LEVER · {_lever_prediction(p)}")
    partners = ", ".join(f"###{r:03d} (k={p.ratio_k:+.2f})" for r, p in causes)
    predictions = " | ".join(_lever_prediction(p) for _, p in causes)
    return (f"acted member of click-driven stable pairs with {len(causes)} "
            f"confirmed reactive partners: {partners} → LEVER · {predictions}")


# ---- WO-INFER-ROLES-EXTRACT-01 · THE LADDER, LIFTED WHOLE --------------------------
#
# A PRECONDITION EXTRACTION. `infer_roles` measured 161 EXECUTABLE lines at anchor
# `5fbbb31` — RED (151-250) under the Director's standing amendment that tier measurements
# count executable lines only, docstrings excluded at both grains. The ruled next rung is a
# two-pass `infer_roles`, and the ratchet forbids restructuring a RED function. This is the
# second of two extractions that buy the room; `weave/pair_classify.py` is the first.
#
# THE LADDER IS NOT SPLIT. Its branch order is preserved verbatim — every guard, every
# evidence sentence, every `continue` in the original is a `return` here and nothing else
# changed. §1 of the WO forbids beginning the two-pass, and moving a body whole is not
# beginning it: no witness call moved, no branch was reordered, no predicate was touched.
#
# `continue` became `return` because the loop body became a function; a branch that typed a
# worldline and stopped now types it and returns it. The fall-through ∅ is the final
# `return`. A worldline the ladder declines to type returns `None`, and the caller records
# nothing for it — exactly what `continue` past the end did.


def _no_effect_suffix(wid, no_effect_of) -> str:
    """WO-REMOTE-WITNESS-01 · the recorded tick, appended to the verdict it explains.

    A worldline that was probed, produced motion, and had every mover attributed to a
    sealed counter reads `∅`/`INERT` exactly like one that was never probed at all. That
    is the honest-null discipline failing one field over: the two are different claims and
    the render must separate them. Extracted rather than inlined (THE INTERLEAVING BAN) so
    the ladder gains no branch."""
    n = no_effect_of.get(wid)
    return (" · " + no_effect_note(n)) if n is not None else ""


class _LadderContext(NamedTuple):
    """Everything the ladder reads, assembled once. A bag, deliberately: the alternative is
    a fifteen-parameter signature, and the ladder genuinely does consult fifteen pieces of
    evidence. `excluded_counter` is the one member it MUTATES — the counter-slot denial it
    records for a displaced verdict, which is why it is a dict rather than a value."""
    report: Any
    worldlines: Any
    clicked: Any
    complement: Any
    has_directional: bool
    offered: Any
    fired_by_node: Any
    counter_of: Any
    lever_of: Any
    reactive_of: Any
    excluded_lever: Any
    excluded_counter: Any
    marginal_local_levers: Any
    lever_witnesses: Any
    no_effect_of: Any
    ego_of: Any
    field_of: Any


def _rv_band1_of(_wl):
    """Band 1 for the INERT seal, READ from the same predicate the attach pass uses —
    never re-derived here. Re-deriving would be the band inversion WO-BAND-SPLIT-01
    exists to prevent, and would let the two disagree."""
    return _band1_self_state(_wl)[0]


def _inert_or_empty(wl, ctx: "_LadderContext", row, wl_clicks, churned):
    """The honest-null tail — INERT with its certificate, or `∅` with its coverage.

    WO-EGO-01 · EXTRACTED WHOLE, verbatim, because `_type_worldline` closed the last rung
    at 80 of 80 and this rung must add a branch. THE INTERLEAVING BAN: extract, then call.
    Not one predicate, threshold or string moved in the lift — the proof is that the
    byte-identity pin's render is unchanged by it.

    Reaching here already means no archetype was earned, which is what makes it the right
    home for a sole-exclusive verdict."""
    (report, worldlines, clicked, complement, has_directional, _offered, _fired_by_node,
     counter_of, lever_of, reactive_of, excluded_lever, excluded_counter,
     marginal_local_levers, lever_witnesses, no_effect_of, _ego_of,
     _field_of) = ctx
    wid = wl.id
    # UNKNOWN — insufficient/ambiguous; NOT LEVER/REACTIVE without a stable coupled pair
    # (this is the global-churn confound fix: co-occurrence alone is never enough).
    # INERT / BAND 2 ∅ — WO-INERT-CERTIFICATE-01.
    #
    # Reaching this branch already means no archetype was earned, which is exactly what
    # makes it the right home for a SOLE-EXCLUSIVE verdict: nothing above it fired.
    # The certificate is built for EVERY worldline that gets here, seal or no seal —
    # "not yet enough evidence" and "evidence of nothing" are different claims and an
    # undifferentiated ∅ cannot tell them apart.
    _cert = _certificate_for(wl, row, wl_clicks, _offered, _fired_by_node)
    # "caused nothing elsewhere" — the cross-branch guard. A REMOTE LEVER is STATIC and
    # silent about itself while causing everything, and canon says it is not inert.
    # WO-LEVER-WITNESS-01 · a WITNESSED lever caused something elsewhere, so it is not
    # causing nothing. Added to the conjunct rather than left to the ladder's order:
    # the branch above already `continue`s before reaching here, so this is redundant
    # TODAY and deliberately so — `causes_nothing` is a statement about the world, and
    # a reordering that made INERT reachable first must not silently re-absorb a
    # worldline whose effect was observed. Exclusivity by construction, not by branch
    # order, is this module's own repeated lesson.
    _causes_nothing = (wid not in lever_of and wid not in reactive_of
                       and wid not in counter_of and wid not in complement
                       and wid not in lever_witnesses)

    if _inert_seal(row, _rv_band1_of(wl), _cert, _causes_nothing):
        return RoleVerdict(wid, INERT, PROVISIONAL,
            f"no self-delta, no attributed effect, moved on NO press aimed or "
            f"otherwise → INERT · {_certificate_str(_cert)}"
            f"{_no_effect_suffix(wid, no_effect_of)}",
            "PROVISIONAL by construction: the offered action classes were all "
            "exercised, but repetition is a count and not an exhaustion — no aimed-press "
            "total proves the object was probed exhaustively. Reopens without ceremony "
            "on any press that moves it or any wider enumeration.")

    # BAND 2 ∅ — R-4: "UNKNOWN stops being a role." An empty Band 2 is not a verdict
    # and never a leaf; it is the honest absence of one, and it renders WITH ITS
    # COVERAGE so a reader can tell "nothing observed yet" from "nothing there".
    return RoleVerdict(wid, None, PROVISIONAL,
        f"{'churns' if churned else 'no churn'}, no stable coupling / clean signal → "
        f"Band 2 ∅ (no role earned over {row.live_presses} live presses) · "
        f"{_certificate_str(_cert)}{_no_effect_suffix(wid, no_effect_of)}")



def _type_worldline(wl, ctx: "_LadderContext"):
    """One worldline's Band-2 verdict, or `None` if the ladder declines to type it.

    The branch order IS the taxonomy's exclusivity and is preserved exactly as it stood in
    `infer_roles`. See the block comment above for what moved and what did not."""
    (report, worldlines, clicked, complement, has_directional, _offered, _fired_by_node,
     counter_of, lever_of, reactive_of, excluded_lever, excluded_counter,
     marginal_local_levers, lever_witnesses, no_effect_of, ego_of,
     field_of) = ctx
    rv_band1_of = _rv_band1_of
    wid = wl.id
    verbs = wl.verbs
    wl_clicks = clicked.get(wid, set())
    # WO-W2-C-01: churn is read from the mechanic layer's OWN reading, not by
    # reaching past it into the raw matrix. `panel` is keyed by the same
    # `worldlines` this loop walks (coupling.py builds it over `ids`), so the
    # lookup is total by construction. Retires one SPEC_MECHANIC_LAYER §8 reach.
    row = report.panel[wid]
    # WO-W2-B-02' — churn is the MAGNITUDE channel's count, not the signed one.
    # `active_presses` counts presses where the worldline RESIZED; `cell_count` is
    # invariant under RECOLOR and MOVE, so on a world of movers that column reads 0
    # for the most active object on the board and this line called it motionless.
    # `changed_presses` counts presses where the FRAME changed. Still read from the
    # panel — the mechanic layer's own reading — never by reaching past it into a
    # raw channel (SPEC_MECHANIC_LAYER_v1 §8, the reach WO-W2-C-01 retired).
    churned = row.changed_presses > 0
    moves = any(vb is Verb.MOVE for vb in verbs)

    # COUNTER — MEASURED, and measured verdicts come first. Two independent
    # computations of one fact: the marginal's ∀-witness and the pair path's stable
    # relay. Either seals; both are reported; neither overrides the other.
    # CHANNEL EXCLUSION, before the marginal is read at all. SPEC_PIXEL_ARITHMETIC_v1
    # §3's four answers are EXCLUSIVE — "four answers, because §2 guarantees no fifth
    # channel". A worldline already explained by a measured coupling is explained by
    # channel (c), another worldline's arithmetic; re-reading it as channel (b) would
    # type the dependent member of a click-driven pair as schedule-autonomous. This
    # is the lawful-progression exclusion discipline, not a tuning knob.
    #
    # WO-LEVER-SUBTREE-05 — a THIRD defect, self-discovered mid-build (not named in
    # the WO's own §0), found only by testing this build against real data: the
    # exclusion above was applied to the MARGINAL half of this condition only. A
    # worldline can genuinely participate in BOTH an autonomous pair (e.g. ###009's
    # own click-independent seesaw with ###010, a real, separate mechanic) AND a
    # click-driven one (###009 also confirmed caused by ###004/###005's clicks) —
    # `counter_of` is populated from the FIRST pair encountered per worldline
    # regardless of which channel it belongs to, so `pair is not None` fired
    # unconditionally and silently overrode a correct LEVER/REACTIVE verdict this
    # very build produces. This is not a new policy call: it is applying the SAME
    # already-ratified "channel exclusivity BY CONSTRUCTION, not by branch order"
    # principle stated immediately above to the disjunct that was missed, factored
    # from `(A and not E) or B` to `(A or B) and not E` — the marginal's own COUNTER
    # is still checked first, so `test_t2_measured_verdict_...` and
    # `test_t3_counter_sealed_worldline_...` (which rely on `excluded_lever`, never
    # on this path) are unaffected; only a worldline BOTH `pair is not None` AND
    # `explained_by_coupling` changes behavior, and no committed fixture exercised
    # that combination before this WO's own build could produce it.
    explained_by_coupling = wid in lever_of or wid in reactive_of
    pair = counter_of.get(wid)
    # WO-LOCAL-LEVER-01 · the local-lever seal excludes the COUNTER path, by the same
    # by-construction discipline the lever candidacy exclusion above already uses. This
    # guard is what makes the fix reachable at all: three worldlines on the recolor
    # canary arrive here with `pair is not None` from the autonomous relay while their
    # own marginal reads depend=1.00, so a LEVER branch added merely BELOW this one
    # could never fire for them. The denial is recorded on the verdict it displaces,
    # never dropped silently — the same treatment `excluded_lever` already gets.
    if wid in marginal_local_levers and pair is not None:
        excluded_counter[wid] = pair
    # WO-COUNTER-EXCLUDE-01 · A VACUOUS ∀ MAY NOT SEAL. The marginal disjunct — and ONLY
    # that disjunct; the pair relay is a different computation and is not in scope — is
    # denied to a worldline carrying a MEASURED channel-(a) witness. On a directional
    # world `acted_by_press` is empty by construction (`coupling.py:394` resolves a
    # target only where `aid == 6`), so TARGETED is ∅, every press is un-targeted, and a
    # mover with no null press reads `action_independence == 1.0`: the ∀ ranges over a
    # set from which the only presses that could have refuted it were structurally
    # absent. `role_read.py:980` already records this as a known cost and defers the
    # ordering question one stratum up; this is that ruling, landed. §3's four answers
    # are exclusive, so a worldline observed to move under more than one button in more
    # than one bearing keys on WHICH action and cannot also key on THAT ANY action. By
    # construction, not by branch order — the same discipline WO-W2-C-02 ratified.
    # WO-COUNTER-EXCHANGE-01 · A CLOCK TRADES WITH ITS DISPLAY. The PAIR disjunct — and
    # only that disjunct; the marginal arm carries WO-COUNTER-EXCLUDE-01's channel-(a)
    # term and is not touched — now requires a measured exchange witness: some single
    # counterparty GROWs on every SHRINK edge it spanned. The pair finder is NOT retuned;
    # `abs(corr)`, the stability rule and every constant in `coupling.py` stand exactly as
    # they were. What changes is that correlation alone no longer seals, because a lever
    # correlates with its effect too and only a clock SHRINKS BY WHAT ITS DISPLAY GREW.
    # `WO_COUNTER_MINE_01` measured the alternative — recurrence read at the CELL — and it
    # ranks the ground the ego walks across first on this board. Read at the VERB the ego
    # cannot be a counterparty at all, because its GROW/SHRINK count is 0/0 on every
    # record. See `weave/exchange_read.py` for the quantifier and its derived scope.
    #
    # WO-COUNTER-EXCHANGE-02 · AND IT IS SCOPED TO THE EVIDENCE THAT PRODUCED IT. The
    # 0/0 measurement is a fact about a WALKING ego on DIRECTIONAL records — not a law
    # about every world. On a click world the acted worldline is named by a target cell
    # and never has to translate, so a legitimate counter there may have a partner that
    # never grows; `test_t1` and `test_t9` are both such worlds and both were wrongly
    # unsealed by the unscoped conjunct. `has_directional` is the ladder's own already-
    # computed flag (`role_read.py:1076`) — no new constant, no new measurement — and
    # gating on it applies the discriminator exactly where its evidence was gathered.
    # Every record in `live_runs/` is directional, so the 21-record measurement is not
    # given back by one verdict: 51 counters before this scope, 51 after.
    if (((_marginal_counter_seal(row) and not channel_a_witness(ego_of.get(wid)))
            or (pair is not None and (not has_directional or exchange_seal(field_of, worldlines, wid))))
            and not explained_by_coupling and wid not in marginal_local_levers):
        basis, plx = _counter_evidence(wid, row, pair, wid in complement)
        plx += _counter_exclusion_note(wid, excluded_lever) + exchange_note(field_of, worldlines, wid, pair)
        return RoleVerdict(wid, COUNTER, FIRM, basis, plx)

    # LEVER — acted member of a click-driven stable pair(s). WO-LEVER-SUBTREE-05
    # Defect 2: a lever may have MORE than one confirmed reactive partner; every one
    # is named, none silently dropped. The single-partner case is worded identically
    # to before this fix (byte-for-byte) — this is additive, not a reformat.
    if wid in lever_of:
        conf = FIRM if len(wl_clicks) >= 2 else PROVISIONAL
        return RoleVerdict(wid, LEVER, conf,
                                    _lever_pair_basis(lever_of[wid]))

    # LEVER (LOCAL) — WO-LOCAL-LEVER-01. The acted worldline IS the effect: it changed
    # on every press that targeted it and on none that did not, so its arithmetic keys
    # on WHICH action (SPEC_PIXEL_ARITHMETIC_v1 §3's first answer) with no remote
    # partner to couple to. Placed BELOW the pair-based LEVER deliberately: a worldline
    # with a confirmed remote partner has the richer evidence and keeps that verdict;
    # this branch types the levers the pair path structurally cannot see.
    if wid in marginal_local_levers:
        conf = (FIRM if row.targeted_presses >= LOCAL_LEVER_FIRM_PRESSES
                else PROVISIONAL)
        basis = (f"changed on ALL {row.targeted_presses} presses targeting it and NONE "
                 f"of {row.untargeted_presses} that did not, over its whole live window "
                 f"({row.live_presses} presses) → LEVER (acts on itself; no remote "
                 f"partner)")
        plx = _local_lever_exclusion_note(wid, excluded_counter)
        return RoleVerdict(wid, LEVER, conf, basis, plx)

    # LEVER (WITNESSED) — WO-LEVER-WITNESS-01. `LEVER` is EXISTENTIAL: one press on it
    # that produced a remote effect earns the tag, and no later null press unearns it.
    # The two branches above are rate-shaped and the live trace measured both of the
    # primary canary's real levers being rejected by one at `COUPLE_CORR` — 0.800 and
    # 0.816 — for reasons that are not threshold problems (a saturation burst counted
    # as failure; a co-lever polluting an off-target rate). A rate is the shape of a
    # ∀-claim, and lever-ness is not a ∀-claim.
    #
    # PLACED HERE, BELOW BOTH, DELIBERATELY — the same reasoning that puts the local
    # seal below the pair path. A worldline with a confirmed stable partner has the
    # richer evidence and keeps that verdict; this branch types only the levers the
    # rate paths structurally cannot reach. Additive: nothing above it changes.
    #
    # Channel exclusivity is applied at the SOURCE (`exclude=marginal_counters` where
    # the witnesses are computed), not by this branch's position — by construction,
    # not by branch order, which is the discipline WO-W2-C-02 ratified.
    if wid in lever_witnesses:
        _w = lever_witnesses[wid]
        return RoleVerdict(wid, LEVER, PROVISIONAL,
                                    witness_basis(_w), witness_parallax(_w))

    # REACTIVE — partner of a click-driven stable pair(s). Same Defect 2 fix: a
    # reactive object may be confirmed caused by MORE than one real lever.
    if wid in reactive_of:
        causes = reactive_of[wid]
        if len(causes) == 1:
            lever, p = causes[0]
            basis = (f"couples in stable ratio (k={p.ratio_k:+.2f}) to clicks on lever "
                     f"###{lever:03d} → REACTIVE · {_lever_prediction(p)}")
        else:
            levers = ", ".join(f"###{l:03d} (k={p.ratio_k:+.2f})" for l, p in causes)
            predictions = " | ".join(_lever_prediction(p) for _, p in causes)
            basis = (f"couples in stable ratio to clicks on {len(causes)} confirmed "
                     f"levers: {levers} → REACTIVE · {predictions}")
        return RoleVerdict(wid, REACTIVE, PROVISIONAL, basis)

    # DEPENDENT — the complement PROXY, and it applies only where no measured
    # verdict exists. `complement_ids` is `participants − coupled_members`, not
    # SPEC_MECHANIC_LAYER §5's fitted dependence; checked first (as it was), it
    # buried a measured verdict. Demoted, not deleted.
    if wid in complement:
        return RoleVerdict(wid, REACTIVE_DRIVEN, PROVISIONAL,
            "reactive-driven: dependent/residual member of a coupling (loosest "
            "independent) — consciously ignored, not dropped",
            f"proxy verdict only; the marginal did not seal "
            f"(indep={row.action_independence:.3f} over "
            f"{row.untargeted_presses} un-targeted presses; coverage "
            f"{row.untargeted_presses + row.targeted_presses} of "
            f"{row.live_presses} live presses)")

    # STATIC — VACATED FROM BAND 2 by WO-STATIC-VACATION-01.
    #
    # The branch that stood here read `if wl_clicks and not churned` and emitted
    # `STATIC/FIRM` into the ROLE slot. "Never changes" is self-state — Band 1 — and it
    # is now observed for every worldline off the settled record, so carrying it here
    # was the same category error one field over. `weave_role_landing` reads Band 1 for
    # this fact now; see that module's `_WEAVE_BAND1_TO_LIBRARY_ROLE`.
    #
    # WHAT THESE WORLDLINES INHERIT, stated because a removed branch always hands its
    # subjects to whatever sits below: the EGO branch needs `moves`, and a worldline
    # that never changed has no MOVE verb by construction, so it cannot be captured
    # there. They fall through to `B2:∅` WITH THEIR COVERAGE — which is the honest
    # answer, and the whole point: `∅` is not INERT, and single-click coverage is
    # nowhere near INERT's exhaustive-interaction bar.
    #
    # REACTIVE is NOT vacated with it. Its repoint would add 10 `reactive_log_score`
    # landings on the live canary — to the exact ten worldlines that are COUNTER and
    # LEVER — saturating an axis beside an already-saturated `counter_log_score`, where
    # `store_a_role_read`'s `_AXES` order and strict `>` flip the roster line
    # COUNTER → REACTIVE. Measured, not feared (WO_STATIC_VACATION_01_RETURN_v1).
    # It stays †-marked until the weave has its own belief home.

    # EGO — WO-EGO-01. `RULING_EGO_WORLDLINE_v1`: ego is any worldline that moves as the
    # direct result of an action button. Multi-ego by definition — no election, no
    # uniqueness, no tie-break; every qualifying worldline carries the tag.
    #
    # PLACED HERE DELIBERATELY, BELOW EVERY MEASURED VERDICT. This rung types the ego; it
    # does not re-rank the ladder. Sitting here, the branch can only claim worldlines that
    # would otherwise fall to OUT_OF_INPUT, INERT or ∅ — so no measured verdict is
    # displaced and the click worlds cannot move. **That conservatism has a known cost and
    # it is reported rather than hidden**: on a directional world the marginal COUNTER seal
    # fires on a perfectly consistent mover, because with no ACTION6 every press is
    # un-targeted and the ego moved on all of them. A mover with no null press is therefore
    # claimed by COUNTER before reaching here. Whether a measured action→bearing map
    # outranks a marginal that never consulted the action id is an ordering question one
    # stratum above this rung — see this WO's return; it is NOT settled by this placement.
    # WO-EGO-02 · THE FIELD READ FIRST — it rests on the exchange record, which is what the
    # embodied board actually shows, and it carries the ground BY NAME. The own-stream
    # bearing read stays below it, unmodified and still able to seal on its own evidence.
    #
    # AND THE GROUND DOES NOT TYPE WITH THE FIGURE. The exchange record is symmetric by
    # construction, so a crossing and its action-dependence are satisfied identically by
    # BOTH endpoints; the first build typed the background alongside the ego. The
    # asymmetry is displacement — this one's footprint occupied more than one anchor
    # across the window and its partner's occupied exactly one — and it is measured from
    # `RegionClay.anchor` rather than from a `MOVE` verb precisely so a figure that
    # changes shape as it crosses still carries it.
    if ego_field_seal(field_of, wid):
        _agrees = wid in ego_of and ego_seal(ego_of[wid])
        return RoleVerdict(wid, EGO, PROVISIONAL,
                           field_basis(field_of, wid),
                           field_parallax(field_of, wid, _agrees))

    if wid in ego_of and ego_seal(ego_of[wid]):
        return RoleVerdict(wid, EGO, PROVISIONAL,
                           ego_basis(ego_of[wid]), ego_parallax(ego_of[wid]))

    # EGO (OUT-OF-INPUT) — a mover in a click-only world has no directional evidence to
    # be covariant with. Unchanged; `has_directional` is NOT consulted by the branch above.
    if moves and not has_directional:
        return RoleVerdict(wid, None, OUT_OF_INPUT,
            "mover but no directional input (click-only world) → EGO out-of-input; "
            "Band 2 ∅ (R-4: UNKNOWN is not a role)")

    return _inert_or_empty(wl, ctx, row, wl_clicks, churned)


def _attach_medium(verdicts, medium_of):
    """WO-MEDIUM-01 · the medium sub-class, attached after the ladder rather than inside it.

    **THE MENU STAYS CLOSED AT SIX.** The role written is `REACTIVE-DRIVEN` — the
    passively-reactive archetype — and the sub-class lives in the basis, which names the
    movers and what this worldline's own stream did where they crossed it.

    **IT REACHES EXACTLY TWO KINDS OF VERDICT and this guard is the fence:** `∅` (no role
    earned — where the embodied ground falls today, because a constant-extent medium has no
    magnitude variance and `_corr` cannot see it, so it never enters `complement_ids`), and
    an existing `REACTIVE-DRIVEN`, where the complement proxy already reached the right
    archetype from the wrong evidence and the measured basis is the refinement. Every other
    role is returned untouched.

    The displaced proxy basis is RECORDED on the parallax, never dropped — two readings of
    one archetype, and the weaker one says so rather than vanishing."""
    out: Dict[int, RoleVerdict] = {}
    for wid, rv in verdicts.items():
        ws = medium_of.get(wid)
        if not medium_seal(ws) or rv.role not in (None, REACTIVE_DRIVEN):
            out[wid] = rv
            continue
        plx = medium_parallax(ws)
        if rv.role == REACTIVE_DRIVEN:
            plx += f"; the complement proxy also reached this archetype — {rv.basis}"
        out[wid] = replace(rv, role=REACTIVE_DRIVEN, confidence=PROVISIONAL,
                           basis=medium_basis(ws), parallax=plx)
    return out


def verdict_egos(verdicts) -> Tuple[int, ...]:
    """Every worldline whose VERDICT is `EGO`, ascending — the set
    `RULING_EGO_WORLDLINE_v1` §4 requires every downstream consumer to accept.

    **IT LIVES HERE BECAUSE THIS MODULE OWNS VERDICTS, AND BECAUSE THE NAME IT REPLACES
    WAS A COLLISION.** `WO-CONTACT-LINE-01` added a `sealed_egos(verdicts)` to
    `weave/contact_line.py` while `weave/nav_target.py:73` already exported a
    `sealed_egos(worldlines, ego_of, field)` — a DIFFERENT fact, computed before any
    verdict exists and, in its own words, *"deliberately the wider set."* Two functions,
    one name, one package, opposite sides of the seal. The older name keeps its meaning;
    this one says what it is.

    Placing it here also breaks an import cycle: `contact_line` imports `collide_drive`,
    so `collide_drive` could not import back. Both import `role_read` already."""
    return tuple(sorted(wid for wid, rv in verdicts.items() if rv.role == EGO))


def infer_roles(worldlines, cuts, node_actions) -> Dict[int, RoleVerdict]:
    report = build_coupling(worldlines, cuts, node_actions)
    magnitude = report.magnitude
    press_left = list(report.presses)                 # left-node index per press position
    acted_press = _acted_by_press(cuts, node_actions, worldlines)
    complement = set(report.complement_ids)
    clicked = _clicks_by_wl(cuts, node_actions, worldlines)
    has_directional = any((aid not in (None, 6)) for (aid, _t) in node_actions)
    # WO-INERT-CERTIFICATE-01 · the world's OWN offered action set, and what fired.
    # Read from `NodeCut.available_actions` — the platform's offer, not an invented
    # menu. `_fired_by_node` keys by node so a worldline's live window can be
    # intersected against it without re-walking the cuts per worldline.
    _offered, _fired_by_node = _offered_and_fired(cuts, node_actions)

    # classify each STABLE coupled pair: autonomous (COUNTER-family) vs click-driven (LEVER↔REACTIVE)
    # WO-W2-C-02 · channel exclusivity, BY CONSTRUCTION rather than by branch order.
    # SPEC_PIXEL_ARITHMETIC_v1 §3's four answers are exclusive ("four answers, because §2
    # guarantees no fifth channel"). A worldline the marginal seals as schedule-autonomous
    # (channel b) is not a cause (channel a), so it never enters LEVER candidacy — not
    # merely "the COUNTER branch happens to run first", which left the pair panel free to
    # elect it and, before this rung, did.
    marginal_counters = {w.id for w in worldlines
                         if _marginal_counter_seal(report.panel[w.id])}
    # WO-LEVER-WITNESS-01 · the ∃-witnesses, computed HERE — beside `marginal_counters` and
    # before any pair is classified — so channel exclusivity reaches the witness path by
    # construction rather than by the ladder's order. Pure read over the same per-press
    # magnitude and click-attribution channels the pair path already uses; adds no
    # measurement of its own and changes no verdict above it.
    #
    # WO-REMOTE-WITNESS-01 · the sealed set is passed to BOTH filters, and they are not
    # the same question. `exclude` keeps a sealed counter out of CANDIDACY (it is not a
    # cause); `disregard` keeps a sealed counter's tick out of EVIDENCE (its motion is
    # explained by its own role). They filter opposite sides of the press and happen to
    # take the same argument here; a rung that widens one must decide the other on its
    # own merits. `no_effects` records the presses where every mover was disregarded —
    # the tick observed and attributed, never silently subtracted.
    # WO-EGO-01 · the action→bearing map, learned per worldline from the verb stream and
    # the action stream. Observed entries only — nothing completed, no direction assumed.
    # WO-RESPAWN-DISREGARD-01 · the boundary set, derived once from the cuts this
    # function already holds. A death's displacement is not evidence about a button.
    # WO-HEART-DISREGARD-01 · the SECOND boundary, and the harness marks nothing at it.
    # `marginal_counters` is nineteen lines above and `report` above that, so the seal
    # this predicate needs already exists here — the audit's cycle risk did not apply.
    ego_of = action_bearings(
        worldlines, node_actions,
        life_boundary_edges(cuts) | heart_boundary_edges(cuts, report, marginal_counters, worldlines))
    # WO-EGO-02 · the SECOND ego observer, and the one the record actually supports.
    # `ego_of` reads a worldline's OWN bearing stream and needs a MOVE verb; this reads the
    # exchange record — who it took ground from, under which button — and needs none. The
    # evidence was already computed by `provenance.complement_verdict` and consumed only by
    # a renderer. Both are kept: they answer different questions and their disagreement is
    # recorded rather than reconciled (RULING_OBSERVERS_INTEGRATOR_v1). The account and the
    # displacement fact travel TOGETHER in one value, because the tie-break is a statement
    # about TWO worldlines — the candidate and its partner — and a per-worldline lookup
    # cannot answer it alone.
    field_of = field_read(worldlines, cuts, node_actions)
    # WO-NAV-TARGET-LAND-01 · the directional lane's subject, at the only position that
    # has one. ADDITIVE: fills `acted_press` only where the click lane left `None`, and
    # visits no press carrying a target cell — so a click world's mapping is unchanged.
    acted_press = with_directional(acted_press, cuts, node_actions, worldlines,
                                   ego_of, field_of)
    _sealed = frozenset(marginal_counters)
    # WO-NAV-TARGET-LAND-01 · the medium's motion is explained by its own role, so it is
    # DISREGARDED as evidence — the other side of the mask the `:1063-1069` comment
    # reserved. It stays out of `exclude`: the ego does take that ground, the attribution
    # is correct, and the medium remains the RECORDED subject of a medium-only press.
    _disregard = (_sealed | frozenset(medium_witnesses(worldlines, field_of))
                  | sealed_egos(worldlines, ego_of, field_of))
    lever_witnesses = witnessed_levers(magnitude, press_left, acted_press,
                                       exclude=_sealed, disregard=_disregard)
    lever_no_effects = no_effects(magnitude, press_left, acted_press,
                                  exclude=_sealed, disregard=_disregard)
    # WO-LOCAL-LEVER-01 · the same exclusion discipline, applied to the other channel and
    # computed at the same point — BEFORE any pair is classified, so it is exclusion BY
    # CONSTRUCTION rather than by branch order. That distinction is not stylistic: the
    # comment above records that "the COUNTER branch happens to run first" already failed
    # once, leaving the pair panel free to elect a worldline it should never have seen.
    #
    # THE COLLISION THIS RESOLVES. Three worldlines on the recolor canary type COUNTER/FIRM
    # through the pair path, described as a "click-independent stable relay" — while their
    # own marginal reads depend=1.00, which is direct evidence they are NOT click
    # independent. The pair path concluded otherwise because it never consulted the
    # marginal. A branch added merely AFTER the COUNTER branch could not fire for them.
    #
    # A worldline sealed as a local lever keys on WHICH action (channel a); the autonomous
    # relay claims it keys on THAT ANY action (channel b). §3's four answers are exclusive,
    # so it cannot be both, and the measured ∀-witness outranks a pair-inferred relay that
    # was read without the marginal. The pair-based COUNTER path is NOT removed — it stays
    # correct for genuine counters, which by construction cannot satisfy this seal (a
    # counter's independence is 1.0, a local lever's is 0.0; no row satisfies both).
    marginal_local_levers = {w.id for w in worldlines
                             if _marginal_local_lever_seal(report.panel[w.id])}
    excluded_counter: Dict[int, Any] = {}  # wid -> the pair whose counter slot it was denied
    stable_pairs = [p for p in report.pairs
                     if p.ratio_stable and abs(p.corr) > COUPLE_CORR]

    # WO-INFER-ROLES-EXTRACT-01 · the two-pass pair discriminator, extracted whole to
    # `weave/pair_classify.py`. Lifted verbatim — no predicate, threshold, verdict or
    # ordering changed; the proof is the byte-identity pin, not the test suite.
    counter_of, lever_of, reactive_of, excluded_lever = classify_pairs(
        stable_pairs, magnitude, press_left, acted_press, marginal_counters)



    _ladder = _LadderContext(
        report=report, worldlines=worldlines, clicked=clicked, complement=complement,
        has_directional=has_directional, offered=_offered, fired_by_node=_fired_by_node,
        counter_of=counter_of, lever_of=lever_of, reactive_of=reactive_of,
        excluded_lever=excluded_lever, excluded_counter=excluded_counter,
        marginal_local_levers=marginal_local_levers, lever_witnesses=lever_witnesses,
        no_effect_of=lever_no_effects, ego_of=ego_of, field_of=field_of)
    verdicts: Dict[int, RoleVerdict] = {}
    for wl in worldlines:
        _rv = _type_worldline(wl, _ladder)
        if _rv is not None:
            verdicts[wl.id] = _rv

    # ---- WO-MEDIUM-01 · refine REACTIVE-DRIVEN with the medium sub-class ---------
    #
    # A PASS, NOT A BRANCH, and the distinction is the whole of its safety. The ladder is
    # untouched — no branch moved, none was added, `_type_worldline` is byte-identical —
    # and this pass may only reach a verdict that earned NO role (`∅`) or one the
    # complement PROXY already called REACTIVE-DRIVEN. It cannot displace a measured
    # verdict, by construction rather than by position, which is the conservatism the ego
    # rung established and `WO_EGO_03` halted for want of one branch over.
    _medium_of = medium_witnesses(worldlines, field_of)
    verdicts = _attach_medium(verdicts, _medium_of)

    # ---- WO-BAND-SPLIT-01 · attach BAND 1 to every verdict ----------------------
    #
    # One pass, after the Band-2 ladder, deliberately: Band 1 is INDEPENDENT of the role.
    # It is read off the worldline's own settled record and cannot be influenced by which
    # branch typed it — computing it here rather than inside eight construction sites makes
    # that independence structural, and makes the coverage TOTAL by construction (every
    # verdict gets a band, or none does, and the loop below proves which).
    #
    # `dataclasses.replace` rather than mutation: `RoleVerdict` is frozen and stays frozen.
    by_id = {w.id: w for w in worldlines}
    for wid, rv in list(verdicts.items()):
        wl = by_id.get(wid)
        if wl is None:
            continue                      # honest: no worldline, no self-state to observe
        b1, cov, revisits = _band1_self_state(wl)
        verdicts[wid] = replace(rv, band1=b1, band1_coverage=cov, band1_revisits=revisits)

    # ---- WO-GROUND-01 · attach the GROUND claim, after the ladder -----------------
    #
    # **A PASS, NOT A BRANCH — `_attach_medium`'s shape, and for the same reason.** The
    # ladder is untouched and `_type_worldline` is byte-identical. The claim is orthogonal
    # to the role: it says *this worldline's deformation is the ego's motion*, which no
    # Band-2 answer states and none of them contradicts, so it is attached beside the role
    # rather than competing for it.
    #
    # **IT MUST RUN AFTER THE LADDER, AND THAT IS STRUCTURAL RATHER THAN STYLISTIC.** The
    # predicate needs the sealed egos, and the egos are what the ladder produces. Reading
    # them before they exist would be a cycle; reading them here is a second pass over a
    # finished map, exactly as Band 1 is.
    #
    # **NO NEW MEASUREMENT.** `field_of` is already in hand — `crossing.Crossing.per_edge`
    # carries the clean-exchange edges and the verb streams carry the rest, so this pass
    # does set arithmetic over records `field_read` already paid 8.16 ms/edge to build.
    for wid, basis in ground_read(worldlines, verdicts, field_of,
                                  verdict_egos(verdicts)).items():
        verdicts[wid] = replace(verdicts[wid], ground=True, ground_basis=basis)

    # WO-WALL-01 · A PASS, NOT A BRANCH, on `ground`'s precedent one field over: the Band-2
    # ladder is byte-identical and no construction site moved. It reads `blocking_tags` —
    # already the Director's ruled site → object → tag chain — and asks one further
    # question of the OWNER: did it hold one fingerprint while refusing. THE EGO SET, not
    # the driving tone: `WO_WALL_MINE_00` §5.1 measured 24 tags owned by a sealed ego on 9
    # of 21 records, because `blocking_tags` compares against one tone's last footprint.
    # NOTHING IS MASKED HERE — `masked_worldlines` is untouched, by charter: the ego
    # learning it cannot enter something is a fact to record, and whether that retires it
    # as a target is a separate ruling.
    for wid, basis in wall_read(worldlines, cuts, ego_of, verdict_egos(verdicts)).items():
        verdicts[wid] = replace(verdicts[wid], wall=True, wall_basis=basis)

    return verdicts


def _band1_str(rv: RoleVerdict) -> str:
    """``B1:TAG(n)`` — the self-state with its coverage, which is part of the claim.

    STATIC over three observed steps is not STATIC over a hundred, so the denominator
    travels with the tag exactly as the two marginal seals' bases already do.

    WO-BAND-1-REVISIT-01: the appended count is `+Nrevisit` — steps that returned to a
    fingerprint the worldline already held. It was `+Nflash` and it never measured a flash:
    a transient lives in the frame layers beneath the visible one, which the ledger this
    reads does not carry.

    RENDERED FOR REACTIVE ONLY, AND THAT IS NOT COSMETIC. A STATIC worldline has exactly
    one fingerprint, so its revisit count is `coverage - 1` BY CONSTRUCTION — it carries no
    information the coverage does not already carry, and printing it on every STATIC line
    would be decoration that reads as evidence. The count answers one question and only for
    a changer: does this object CYCLE among a few states, or MARCH through many. The field
    still carries the number for any reader that wants it; the render states it where it
    can mean something. (`_multi_member_flag`'s "appends ONLY when it fires" discipline.)

    ``B1:—`` when the self-state was not observable (a single-step worldline has nothing to
    compare). An absent observation must never render as either tag."""
    if not rv.band1:
        return f"B1:—({rv.band1_coverage})"
    flash = (f" +{rv.band1_revisits}revisit"
             if (rv.band1 == BAND1_REACTIVE and rv.band1_revisits) else "")
    return f"B1:{rv.band1}({rv.band1_coverage}){flash}"


def _band2_str(rv: RoleVerdict) -> str:
    """``B2:ROLE`` — the role, or ``B2:∅`` where none was earned (R-4).

    An interim Band-1 name still occupying this slot is MARKED, not silently passed
    through: `STATIC` and `REACTIVE` are self-state, not roles, and they sit here only
    until WO-STATIC-VACATION-01 decides where their belief evidence goes instead. Marking
    them is the difference between a known interim and a quiet category error — the second
    is what this rung exists to end."""
    if rv.band2 is None:
        return "B2:∅"
    mark = "†" if rv.band2 in BAND2_INTERIM_BAND1_NAMES else ""
    return f"B2:{rv.band2}{mark}"


def render_roles_block(verdicts: Dict[int, RoleVerdict], worldlines) -> str:
    """The human-gradable ROLE block, grouped FIRM → PROVISIONAL → OUT_OF_INPUT.
    Coupling-grounded; derived-not-stored; dossier-only (no dispatch).

    WO-BAND-SPLIT-01 — TWO BANDS, RENDERED SEPARATELY. Band 1 is self-state read off the
    settled record before any probing; Band 2 is the role derived from the mechanic
    stratum. They are different claims with different evidence and different oracles, and a
    grader who cannot tell them apart cannot grade either."""
    from collections import Counter
    cls = {w.id: w.first_region.class_id for w in worldlines}
    rank = {FIRM: 0, PROVISIONAL: 1, OUT_OF_INPUT: 2}
    lines: List[str] = ["ROLE INFERENCE (two bands · B1 self-state off the settled record · "
                        "B2 role from the mechanic stratum · derived-not-stored · dossier-only)"]
    interim = sorted({rv.band2 for rv in verdicts.values()
                      if rv.band2 in BAND2_INTERIM_BAND1_NAMES})
    if interim:
        lines.append(f"  † {', '.join(interim)} is Band-1 self-state still occupying the "
                     f"Band-2 slot. STATIC was vacated by WO-STATIC-VACATION-01; REACTIVE "
                     f"was not, because repointing it lands reactive evidence on every "
                     f"changing worldline and flips COUNTER→REACTIVE in the roster's "
                     f"argmax. It waits on the weave's own belief home.")
    for wid, rv in sorted(verdicts.items(), key=lambda kv: (rank.get(kv[1].confidence, 3), kv[0])):
        lines.append(f"  ###{wid:03d} c{cls.get(wid, '?')} · {_band1_str(rv)} · "
                     f"{_band2_str(rv)}/{rv.confidence} — {rv.basis}")
        if rv.parallax:
            # WO-W2-C-01 — the divergence travels with the verdict, never reconciled.
            lines.append(f"        ⟂ {rv.parallax}")
    dist = Counter(f"{rv.band2 if rv.band2 is not None else '∅'}/{rv.confidence}"
                   for rv in verdicts.values())
    lines.append("  summary (B2): " + ", ".join(f"{k}={n}" for k, n in sorted(dist.items())))
    b1dist = Counter(rv.band1 or "—" for rv in verdicts.values())
    lines.append("  summary (B1): " + ", ".join(f"{k}={n}" for k, n in sorted(b1dist.items())))
    return "\n".join(lines)
