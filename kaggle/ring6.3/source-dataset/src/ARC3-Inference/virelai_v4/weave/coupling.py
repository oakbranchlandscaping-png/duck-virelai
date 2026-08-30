"""WO_COUPLING_R1_DETECTOR · the ###-grain pair-motion coupling detector (CHARTER_COUPLING_LAW R1).

The deliverable is the PAIR MOTION LAW, not a background label. For a woven window this
module builds the PRESS-INDEXED, per-### signed-delta matrix (store the event, not the
class marginal), then reads coupled pairs off it with a MULTI-CRITERION PANEL — none of
whose criteria is trusted alone — and DERIVES the complement as the dependent/residual
member (the one outside the tight relay). The complement is described, never labeled
"background", never dropped: it is tagged, consciously ignored.

WEAVE-NATIVE, DERIVED-NOT-STORED: reads only committed weave (region_at cell counts +
acted_on); writes nothing to any object; pure Python math (no numpy/scipy). No Store-A,
no LibraryObject, no background flag, no size-prior — size appears ONLY as a reported
tie-break column (``size_rank``), never as a classify gate. R1 is the DETECTOR: it does
not rewire role inference (that is R2).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from virelai_v4.weave.worldline import region_at
from virelai_v4.weave.action_roster import acted_on
from virelai_v4.weave.edge import Verb

# thresholds — stated, not magic
MIN_ACTIVE = 4          # a pair needs this many presses where either member moves
CAND_CORR = 0.6         # |corr| above this makes a pair a coupling CANDIDATE
COUPLE_CORR = 0.85      # |corr| above this (AND a stable ratio) makes it COUPLED
RATIO_STABLE_MAX = 0.3  # per-press ratio std/|mean| below this = stable ratio


@dataclass(frozen=True)
class CoupledPair:
    wid_a: int
    wid_b: int
    corr: float
    ratio_k: float
    ratio_stable: bool
    active_presses: int
    acted_member: Optional[int]     # the member acted_on during the pair's presses (feeds R2)


@dataclass(frozen=True)
class PanelRow:
    wid: int
    best_corr: float                # strongest |corr| with any other ### (coupling — fires)
    ratio_stability: float          # best-partner ratio stability (lower = tighter)
    active_presses: int
    size_rank: int                  # TIE-BREAK COLUMN ONLY — never a classify gate
    form_stability: float           # mean jaccard vs prev step (abstains on figure/ground)
    churn_depth: float              # mean fractional churn (abstains on figure/ground)
    # WO-W2-A-01 · THE ACTION-RELATION MARGINAL (SPEC_MECHANIC_LAYER_v1 §2's second
    # stratum). Unlike the three appearance marginals above, these two do not abstain
    # on figure/ground: they are measured against the action stream, not the shape.
    # -1.0 is ABSTENTION (an empty denominator), never a reading of 0.0.
    action_independence: float = -1.0   # moved / could-have-moved, on UN-targeted presses
    action_dependence: float = -1.0     # moved / could-have-moved, on TARGETED presses
    untargeted_presses: int = 0         # the independence denominator
    targeted_presses: int = 0           # the dependence denominator
    # WO-W2-C-01b — presses this worldline was LIVE for, whether or not an action fired.
    # The window its own rates range over, carried so a consumer can certify coverage
    # without reconstructing liveness beneath this layer (SPEC_MECHANIC_LAYER_v1 §2: the
    # marginal stratum owns its denominators; §8: downward opacity).
    live_presses: int = 0
    # WO-W2-B-02' — the MAGNITUDE channel's counterpart of `active_presses`. That column
    # counts presses where the worldline RESIZED; this one counts presses where the frame
    # CHANGED. They differ by exactly the count-invariant verbs (RECOLOR, MOVE, and a
    # constant-count re_join bridge). Additive: `active_presses` keeps its meaning and its
    # value, so every vc33 reading that depends on it is unmoved.
    changed_presses: int = 0


@dataclass(frozen=True)
class CouplingReport:
    presses: Tuple[int, ...]                 # left-node index of each press-edge
    matrix: Dict[int, Tuple[float, ...]]     # wid -> SIGNED count delta per press
    pairs: Tuple[CoupledPair, ...]
    complement_ids: Tuple[int, ...]
    panel: Dict[int, PanelRow]
    # WO-W2-B-02' · the second channel. Co-indexed with `matrix` press-for-press and built
    # in the same walk (`_build_channels`). Non-negative by construction: it is a set
    # cardinality, so it CANNOT carry the relay's sign and no fit may read it.
    magnitude: Dict[int, Tuple[float, ...]] = field(default_factory=dict)
    # WO-EGO-02 · THE THIRD CHANNEL, and it was already computed. `action_by_press[i]` is
    # the raw action id that produced press `i` — built in the same walk as `presses` and
    # co-indexed with every `matrix`/`magnitude` row by construction. It was a local,
    # handed once to `_action_marginal` and dropped at the return, so a consumer wanting
    # to partition the magnitude matrix BY BUTTON had to re-derive it through a node join
    # against `node_actions`. Exposing it changes no computation and no other field: this
    # is the same list, returned instead of discarded.
    #
    # `None` where no action fired — the honest absence, never a zero.
    action_by_press: Tuple[Optional[int], ...] = ()


# ---- pure-python signal math (no numpy/scipy) -------------------------------

def _corr(a: List[float], b: List[float]) -> Tuple[float, int]:
    """Pearson over the presses where EITHER member moves; (corr, active_count)."""
    idx = [i for i in range(len(a)) if a[i] != 0 or b[i] != 0]
    if len(idx) < 3:
        return 0.0, len(idx)
    xa = [a[i] for i in idx]
    xb = [b[i] for i in idx]
    ma = sum(xa) / len(xa)
    mb = sum(xb) / len(xb)
    num = sum((xa[i] - ma) * (xb[i] - mb) for i in range(len(xa)))
    da = sum((v - ma) ** 2 for v in xa) ** 0.5
    db = sum((v - mb) ** 2 for v in xb) ** 0.5
    if da == 0 or db == 0:
        return 0.0, len(idx)
    return num / (da * db), len(idx)


def _ratio_k(a: List[float], b: List[float]) -> float:
    """Least-squares k for dA ≈ k·dB."""
    sbb = sum(v * v for v in b)
    if sbb == 0:
        return 0.0
    return sum(a[i] * b[i] for i in range(len(a))) / sbb


def _ratio_stability(a: List[float], b: List[float]) -> float:
    """std/|mean| of the per-press ratio a/b over presses where b moves. Low = stable."""
    r = [a[i] / b[i] for i in range(len(a)) if b[i] != 0]
    if len(r) < 2:
        return float("inf")
    m = sum(r) / len(r)
    sd = (sum((x - m) ** 2 for x in r) / len(r)) ** 0.5
    return sd / (abs(m) + 1e-9)


# ---- the detector -----------------------------------------------------------

def _cc(wl, node_index: int) -> int:
    r = region_at(wl, node_index)
    return r.cell_count if r is not None else 0


# ---- WO-W2-B-02′ · TWO CHANNELS ----------------------------------------------
#
# SPEC_MECHANIC_LAYER_v1 §3: "per press, per individuated worldline, signed delta — one
# row of a matrix." A row, not a scalar. `cell_count` is invariant under STILL, RECOLOR
# and MOVE — three of the five continue-verbs — so the count-difference row alone records
# zero for a worldline translating across the whole board.
#
# No single number can be both non-zero whenever the frame changed and sign-preserving on
# a conserved relay: the two verbs that carry motion invisibly are exactly the two with no
# legal sign. RECOLOR's `delta` is a pair of nominal class labels — arithmetic on colour
# identity, which the information wall forbids outright. MOVE's is a bearing, withheld by
# AMENDMENT_BUILD_LADDER_v3 Clause D until MEC-1/MEC-3. So: two channels.
#
#   SIGNED     `now.cell_count - prev.cell_count` — today's quantity, byte-for-byte. Note
#              this needs NO verb table: the count difference is verb-agnostic and correct
#              on all nine. Sign was never the verb-dependent part. It is computed by the
#              unchanged `_cc` expression below so the relay's k = -1.00 is preserved by
#              CONSTRUCTION, not by tuning. Every fit reads this channel and only this one.
#   MAGNITUDE  the class-labelled change size — non-negative, non-zero whenever the frame
#              changed. Only `role_read`'s churn test reads it.
#
# THE DEFORM BRANCH IS NOT OPTIONAL. `re_join._merge` (rejoin.py:62-63) manufactures a
# `Verb.DEFORM` edge with both endpoints present that `weave_edge` never emits, and splices
# it into `Worldline.edges`; every production read goes through `re_join`. WO-W2-B-02 had
# no DEFORM branch, fell through to its MOVE catch-all, and destroyed a -0.949 correlation.
# There is no catch-all here: an unhandled verb raises, because a default is what shipped
# the regression.

_MAGNITUDE_BY_VERB = (Verb.STILL, Verb.RECOLOR, Verb.MOVE,
                      Verb.GROW, Verb.SHRINK, Verb.DEFORM)


def _change_magnitude(edge) -> float:
    """Cells whose CLASS LABEL changed across one edge — the cardinality of the symmetric
    difference of the class-labelled cell sets, {(cell, class_id)}.

    The labelling is what makes it total. A plain cell symmetric difference is 0 under
    RECOLOR (same footprint ⇒ empty difference), reproducing `cell_count`'s blindness
    sideways. Labelling by the region's class makes a recoloured cell differ from itself.

    WO-VERB-FROM-TRANSITIONS-01 — READ FROM THE SIGNATURE, NOT DISPATCHED ON THE VERB.
    This docstring specified the object ("the symmetric difference of the class-labelled
    cell sets") and then declined to build it ("Closed form, so no set is built"), computing
    the cardinality through six per-verb branches instead. `edge.py::TransitionSignature`
    is now that object, and this function reads it.

    Why that matters and is not cosmetic: the GROW branch returned
    `now.cell_count - prev.cell_count`, which is the right answer ONLY BECAUSE the verb
    asserted now ⊇ prev. The magnitude was therefore only as sound as the naming — a
    mis-assigned verb produced a silently wrong number with no way to notice. Since
    WO-MARGINAL-CHANNEL-01 the magnitude channel is what the action marginal reads, so that
    unsoundness sat directly under the role layer. Reading the signature makes the quantity
    a function of what the cells did rather than of what the pair was called; the chain runs
    arithmetic -> verb -> magnitude instead of geometry -> verb -> arithmetic.

    The closed form is preserved exactly, and `tests/weave/test_verb_from_transitions.py`
    pins the equivalence on all six verbs against a verbatim transcription of the branches
    below — the port's own correctness proof.

    One-endpoint edges keep their pre-port answers: a residual verb has no two-sided
    signature (structurally, not incidentally), so it is answered from its single endpoint's
    count. NO CATCH-ALL survives the port: a two-endpoint edge with no signature raises,
    naming itself. A default is what shipped WO-W2-B-02's regression."""
    prev, now = edge.prev, edge.now
    if prev is None and now is None:
        return 0.0                                   # nothing to measure, honestly
    if prev is None:
        return float(now.cell_count)                 # appeared
    if now is None:
        return float(prev.cell_count)                # vanished
    sig = getattr(edge, "signature", None)
    if sig is None:
        raise ValueError(
            f"_change_magnitude: two-endpoint edge (verb {getattr(edge, 'verb', None)!r}) "
            f"carries no transition signature. Every such edge is signature-computable and "
            f"must be constructed with one — a catch-all default is what shipped "
            f"WO-W2-B-02's regression.")
    return float(sig.magnitude)


def _edge_index(wl) -> Dict[Tuple[int, int], Any]:
    """(left_node, right_node) -> the WeaveEdge spanning that step transition.
    `Worldline.edges[i]` spans `steps[i] -> steps[i+1]` (worldline.py:34), an invariant
    `re_join._merge` preserves by splicing exactly one bridge edge per join."""
    n = min(len(wl.edges), len(wl.steps) - 1)
    return {(wl.steps[i][0], wl.steps[i + 1][0]): wl.edges[i] for i in range(n)}


def _press_magnitude(wl, eidx, left: int, right: int) -> float:
    """One press, one worldline, the magnitude channel. Where the weave threaded an edge,
    measure the class change it typed; where it did not — before a birth, after a death, a
    terminated thread — the presence difference IS the change, and its size is its
    magnitude."""
    e = eidx.get((left, right))
    if e is not None:
        return _change_magnitude(e)
    return float(abs(_cc(wl, right) - _cc(wl, left)))


def _build_channels(ids, by_id, nodes):
    """Both rows, per worldline, from ONE walk of ONE press series — so the two channels
    cannot drift out of co-index. Returns (signed, magnitude).

    The signed row is the pre-existing expression, character for character: this rung adds
    a channel, it does not touch the one every fit reads."""
    matrix: Dict[int, Tuple[float, ...]] = {}
    magnitude: Dict[int, Tuple[float, ...]] = {}
    for wid in ids:
        wl = by_id[wid]
        eidx = _edge_index(wl)
        sig, mag = [], []
        for left, right in zip(nodes, nodes[1:]):
            sig.append(float(_cc(wl, right) - _cc(wl, left)))
            mag.append(_press_magnitude(wl, eidx, left, right))
        matrix[wid] = tuple(sig)
        magnitude[wid] = tuple(mag)
    return matrix, magnitude


# ---- WO-W2-B-D1 · the instrument (env-gated; measures, decides nothing) ------
#
# WO-W2-B-02 replaced this module's per-press quantity and was reverted: one press on
# one worldline went 0 -> non-zero, large enough to destroy a -0.949 correlation. That
# build's own return proved the replacement is arithmetically IDENTICAL to `_cc`'s
# difference on STILL / GROW / SHRINK and on the no-edge fallback — so on a trail
# measured as pure GROW/SHRINK the two should not have differed at all. The property
# and the run disagree, and which branch actually fired is unknown.
#
# This emits, per worldline per press, the verb the weave typed beside ALL THREE
# candidate quantities, so the branch is read off the record rather than reasoned about.
# It computes no new belief and feeds nothing: `_bd1_dump` returns None.

def _bd1_line(wl, eidx, left: int, right: int) -> str:
    """One press, one worldline: the typed verb and the three candidate quantities.
    `sym_diff` / `now_cells` are -1 exactly when there is no edge to read them from —
    an honest absence marker, never a value."""
    e = eidx.get((left, right))
    verb, sym_diff, now_cells = "NO_EDGE", -1, -1
    if e is not None:
        verb = e.verb.name
        prev, now = e.prev, e.now
        if prev is not None and now is not None:
            sym_diff = len(frozenset(prev.cells) ^ frozenset(now.cells))
            now_cells = now.cell_count
    cc_delta = _cc(wl, right) - _cc(wl, left)
    return (f"[W2-BD1] wid={wl.id} press={left}-{right} verb={verb} "
            f"cc_delta={cc_delta} sym_diff={sym_diff} now_cells={now_cells}")


def _bd1_dump(ids, by_id, nodes) -> None:
    """Emit one line per (worldline, press) to stderr, flushed — the
    VIRELAI_WO02_DIAG pattern (`library_sync.py:344`). Never stdout: the canary's own
    artifact is unperturbed. Edge lookup is the committed contract, `Worldline.edges[i]`
    spans `steps[i] -> steps[i+1]` (worldline.py:34)."""
    import sys
    for wid in ids:
        wl = by_id[wid]
        n = min(len(wl.edges), len(wl.steps) - 1)
        eidx = {(wl.steps[i][0], wl.steps[i + 1][0]): wl.edges[i] for i in range(n)}
        for left, right in zip(nodes, nodes[1:]):
            print(_bd1_line(wl, eidx, left, right), file=sys.stderr, flush=True)


# ---- WO-W2-A-01 · the action-relation marginal --------------------------------
#
# SPEC_MECHANIC_LAYER_v1 §2 names two strata. Couplings answer "does this worldline's
# arithmetic key on ANOTHER worldline's arithmetic". The marginals answer the other two
# channels of SPEC_PIXEL_ARITHMETIC_v1 §3 — "on WHICH action" and "on THAT ANY action
# occurred" — and the mechanic layer had no representative for either: its three
# existing marginals (size_rank, form_stability, churn_depth) are appearance readings
# that abstain by design. The action-relation measurement lived only at
# `library/counter_stats.py:83`, on Store-A, divided by a spawn-frozen
# `initial_cell_count`, behind `if obj.role != COUNTER: continue` — able to confirm a
# counter, never to discover one. This derives it where §2 says it belongs, from data
# `build_coupling` already holds.
#
# THE DEFINITION. For one worldline w over the press series, partition the presses:
#   FIRED      — `node_actions[right]` yielded `aid is not None`. Channel (b): THAT an
#                action occurred. `aid is None` means exactly one thing — no producing
#                action (the root node) — never "an action we could not read".
#   LIVE       — w is present at either endpoint of the press. A press w could not have
#                moved on is not evidence about w either way, so it leaves both rates.
#   TARGETED   — a FIRED ∧ LIVE press whose resolved acted-on worldline IS w. Channel
#                (a): WHICH action — carried, on a click world, by the target cell.
# Then, over disjoint sets whose union is FIRED ∧ LIVE:
#   action_independence(w) = moved / |FIRED ∧ LIVE ∧ ¬TARGETED|
#   action_dependence(w)   = moved / |FIRED ∧ LIVE ∧  TARGETED|
# where `moved` counts presses with `matrix[w][i] != 0`. Both are rates in [0,1]; an
# empty denominator ABSTAINS as -1.0, never 0.0, because 0.0 is a claim.
#
# A clock reads independence ~1 (it moves whoever was targeted). A lever reads
# independence ~0 and dependence ~1. An inert worldline reads 0 on both. The pair is
# what separates them — neither reading alone does. Derived per call, never stored
# (§8), and consumed by nothing: reading it is rung C.

def _action_marginal(wl, deltas, nodes, action_by_press, acted_by_press):
    """(independence, dependence, n_untargeted, n_targeted, n_live) for one worldline.

    Takes `nodes` rather than the press list so the right-hand node of each press is
    read from the window, never inferred as `left + 1` — cut node_indices are not
    guaranteed contiguous, and inferring adjacency is how index-space bugs start.

    WO-W2-C-01b: the LIVE test is evaluated FIRST and counted, so `n_live` is the whole
    window this worldline could have moved in — independent of whether an action fired.
    Both tests are conjunctive filters, so the order carries no meaning for the four
    rates; only the new counter needs it. Liveness is read from a set built once from
    `wl.steps` (which holds exactly the nodes where the worldline is present) rather than
    by calling `region_at` per press: `region_at` is a linear scan of `steps`, so the set
    form is O(|steps|) once plus O(1) per press instead of O(|steps|) twice per press —
    strictly cheaper than what it replaces, not merely cheap enough to add a counter."""
    live_nodes = {n for (n, _region) in wl.steps}
    untgt_n = untgt_moved = tgt_n = tgt_moved = live_n = 0
    for i, (left, right) in enumerate(zip(nodes, nodes[1:])):
        if left not in live_nodes and right not in live_nodes:
            continue                                       # not LIVE
        live_n += 1
        if action_by_press[i] is None:                     # not FIRED
            continue
        moved = deltas[i] != 0
        if acted_by_press[i] == wl.id:
            tgt_n += 1
            tgt_moved += 1 if moved else 0
        else:
            untgt_n += 1
            untgt_moved += 1 if moved else 0
    indep = (untgt_moved / untgt_n) if untgt_n else -1.0
    depend = (tgt_moved / tgt_n) if tgt_n else -1.0
    return indep, depend, untgt_n, tgt_n, live_n


def build_coupling(worldlines, cuts, node_actions) -> CouplingReport:
    ordered = sorted(cuts, key=lambda c: c.node_index)
    nodes = [c.node_index for c in ordered]
    cbi = {c.node_index: c for c in cuts}
    ids = [w.id for w in worldlines]
    by_id = {w.id: w for w in worldlines}

    # D-A · the press-indexed signed-delta MATRIX (store the event) --------------
    presses: List[int] = []            # left-node index of each edge
    acted_by_press: List[Optional[int]] = []
    # WO-W2-A-01 · channel (b): the raw action id per press, or None for "no producing
    # action". Additive — `acted_by_press` keeps its meaning (the RESOLVED target ###,
    # click-lane only) and its type. `aid` is dense over EVERY action type at the one
    # production intake (`ledger_build.load_node_actions_from_log`, its own docstring:
    # "a directional's (action_id, None) reaches the weave here"), so the `aid == 6`
    # guard below is about RESOLVABILITY — acted_on needs a target cell — never about
    # whether a press can be seen at all.
    action_by_press: List[Optional[int]] = []
    for left, right in zip(nodes, nodes[1:]):
        presses.append(left)
        aid, target = node_actions[right] if 0 <= right < len(node_actions) else (None, None)
        action_by_press.append(aid)
        res = acted_on(right, aid, target, cbi, worldlines) if aid == 6 else None
        acted_by_press.append(res.worldline_id if (res is not None and res.status == "RESOLVED") else None)

    matrix, magnitude = _build_channels(ids, by_id, nodes)

    # WO-W2-B-D1 · WHICH BRANCH FIRED — env-gated diagnostic, additive.
    # Reads only what is already computed above; writes nothing; returns nothing;
    # changes no value any production path consumes. Off unless VIRELAI_W2_BD1=1.
    try:
        import os
        if os.environ.get("VIRELAI_W2_BD1") == "1":
            _bd1_dump(ids, by_id, nodes)
    except Exception:
        pass

    # D-B · the multi-criterion PANEL (pairs) ------------------------------------
    pairs: List[CoupledPair] = []
    best_partner: Dict[int, Tuple[float, float]] = {wid: (0.0, float("inf")) for wid in ids}
    coupled_members: set = set()
    participants: set = set()
    for i, a in enumerate(ids):
        da = list(matrix[a])
        for b in ids[i + 1:]:
            db = list(matrix[b])
            corr, active = _corr(da, db)
            if active < MIN_ACTIVE or abs(corr) <= CAND_CORR:
                continue
            k = _ratio_k(da, db)
            stab = _ratio_stability(da, db)
            stable = stab < RATIO_STABLE_MAX
            coupled = abs(corr) > COUPLE_CORR and stable
            acted_member = _acted_member(a, b, presses, acted_by_press, da, db)
            pairs.append(CoupledPair(a, b, corr, k, stable, active, acted_member))
            participants.update((a, b))
            if coupled:
                coupled_members.update((a, b))
            for m, o in ((a, b), (b, a)):
                if abs(corr) > abs(best_partner[m][0]):
                    best_partner[m] = (corr, stab)

    # WO-LEVER-SUBTREE-04 · fallback promotion pass, additive — runs ONLY for worldlines
    # `_corr` can never see. `_self_invariant(matrix[a])` is exactly the condition under
    # which `da == 0` fires unconditionally for every possible partner (proven exhaustively
    # against real ground truth, WO_LEVER_SUBTREE_03_RETURN §B.2) — so no worldline that
    # reaches this pass could have formed a pair above, by construction, not by a guard that
    # could drift out of sync with the primary path. `_corr`, its call site, and every
    # existing threshold above are untouched.
    #
    # TWO PASSES, evidence-gated, not a blanket exclusion: the real fixture round-robins
    # clicks across several self-invariant candidates in a life (found RED-first: 7 of
    # them here, only 2 of which are genuine remote levers) — blanket-excluding every OTHER
    # candidate's presses from `a`'s off-target set (tried first) starves the denominator
    # and lets ANY partner through at strength=1.0, which is not a test anymore. Pass 1 runs
    # the promotion test with only the same-candidate settle-back exclusion (no cross-
    # candidate knowledge yet) to find which (candidate, partner) relationships have their
    # OWN independent evidence. Pass 2 re-scores each candidate against each partner,
    # excluding a press from the off-target set only when a *different* candidate that pass
    # 1 already confirmed causes that same partner to change is the one acting on that press
    # (plus its own settle-back echo) — i.e. only when there is independent evidence the
    # change is explained by someone else, never merely because someone else was clicked.
    self_invariant_ids = {wid for wid in ids if _self_invariant(matrix[wid])}
    pass1_confirmed: Dict[Tuple[int, int], bool] = {}
    for a in self_invariant_ids:
        for b in ids:
            if b == a:
                continue
            raw = _attributed_exogenous_effect(a, b, presses, acted_by_press, magnitude[b])
            pass1_confirmed[(a, b)] = raw is not None

    for a in self_invariant_ids:
        for b in ids:
            if b == a:
                continue
            confound_ids = {c for c in self_invariant_ids
                             if c != a and pass1_confirmed.get((c, b))}
            strength = _attributed_exogenous_effect(
                a, b, presses, acted_by_press, magnitude[b], confound_ids)
            if strength is None:
                continue
            active_presses = sum(1 for m in magnitude[b] if m != 0)
            pairs.append(CoupledPair(a, b, strength, 0.0, True, active_presses, a))
            participants.update((a, b))
            coupled_members.update((a, b))
            if strength > abs(best_partner[a][0]):
                best_partner[a] = (strength, 0.0)
            if strength > abs(best_partner[b][0]):
                best_partner[b] = (strength, 0.0)

    # D-C · the DERIVED complement (dependent/residual = participant outside a tight relay).
    #   Size is NOT used to elect — only participation-minus-tight-relay. (Tie-break: the
    #   looser best-partner ratio, then smaller size_rank, purely to order a genuine tie.)
    complement = sorted(participants - coupled_members,
                        key=lambda w: (-best_partner[w][1],))
    complement_ids = tuple(complement)

    # per-### PANEL rows (calibration: which criteria fire vs abstain) ------------
    meansize = {w.id: (sum(_cc(w, n) for n in nodes) / max(1, len(nodes))) for w in worldlines}
    size_rank = {wid: r + 1 for r, wid in enumerate(sorted(ids, key=lambda w: -meansize[w]))}
    panel: Dict[int, PanelRow] = {}
    for wid in ids:
        corr0, stab0 = best_partner[wid]
        # WO-MARGINAL-CHANNEL-01: the marginal reads the MAGNITUDE row, not the signed
        # one. `_action_marginal` uses its `deltas` argument for exactly one thing —
        # `moved = deltas[i] != 0`, a boolean — and `cell_count` is invariant under
        # STILL, RECOLOR and MOVE (this module's own header). Handed the signed row, a
        # worldline that recolors or translates in place read `moved=False` on every
        # press of its life, so `action_dependence` could only ever answer "no" for it.
        # `magnitude` is built in the same walk of the same press series
        # (`_build_channels`), co-indexed by construction. The fits below keep the
        # signed row — `_corr`/`_ratio_k`/`_ratio_stability` need the sign, because a
        # conserved transfer is one member's loss against another's gain and a
        # magnitude row cannot express that opposition. Only this boolean did not.
        indep, depend, n_untgt, n_tgt, n_live = _action_marginal(
            by_id[wid], magnitude[wid], nodes, action_by_press, acted_by_press)
        panel[wid] = PanelRow(
            wid=wid,
            best_corr=abs(corr0),
            ratio_stability=stab0,
            active_presses=sum(1 for d in matrix[wid] if d != 0),
            size_rank=size_rank[wid],
            form_stability=_form_stability(by_id[wid], nodes),
            churn_depth=_churn_depth(by_id[wid], nodes, matrix[wid], presses),
            action_independence=indep,
            action_dependence=depend,
            untargeted_presses=n_untgt,
            targeted_presses=n_tgt,
            live_presses=n_live,
            changed_presses=sum(1 for m in magnitude[wid] if m != 0),
        )

    return CouplingReport(tuple(presses), matrix, tuple(pairs), complement_ids, panel,
                          magnitude, tuple(action_by_press))


def _acted_member(a, b, presses, acted_by_press, da, db) -> Optional[int]:
    """Which member (if any) was acted_on during this pair's active presses."""
    count = {a: 0, b: 0}
    for i in range(len(presses)):
        if da[i] == 0 and db[i] == 0:
            continue
        m = acted_by_press[i]
        if m in count:
            count[m] += 1
    if count[a] == 0 and count[b] == 0:
        return None
    return a if count[a] >= count[b] else b


# ---- WO-LEVER-SUBTREE-04 · the remote-lever promotion path (additive fallback) ---------
#
# WO_LEVER_SUBTREE_02_RETURN / WO_LEVER_SUBTREE_03_RETURN, exhaustively, on real ground
# truth: a genuine remote lever has zero variance in its own signed (cell-count-delta) row,
# in every life, under every partner — `_corr`'s `da == 0` bail (`:101`) excludes it from
# EVERY possible CoupledPair, unconditionally, by construction. This is not a tuning gap:
# FOUNDATIONAL_ARCHETYPES_v2 §3 already rules a remote lever's self-delta is IRRELEVANT to
# its lever-ness, and `_corr` requires exactly the one thing doctrine says doesn't matter.
#
# The fix is additive, not a repair of `_corr`: a second, independent promotion path, run
# ONLY for worldlines the existing test can never see. `_self_invariant` identifies the
# candidate set; `_attributed_exogenous_effect` is the actual test — does a click on this
# worldline specifically predict a change on another, using the click-attribution channel
# (`acted_by_press`) already proven correct against real ground truth in
# WO_LEVER_SUBTREE_03_RETURN §B.1, and the MAGNITUDE channel (`_change_magnitude` /
# `CouplingReport.magnitude`) for "did the partner change" — the general, verb-agnostic
# change signal that WO_LEVER_SUBTREE_02_RETURN §B.2 already found is computed every press
# and never read by the correlation decision. Reading it here, for exactly the case it was
# built for, closes that gap without touching the signed-channel path at all.

def _self_invariant(row) -> bool:
    """True iff a worldline's own signed (cell-count-delta) row never leaves zero — the
    exact, exhaustively-confirmed condition under which `_corr` can never form a pair for
    it (`da == 0` unconditionally, for every possible partner). Real ground truth showed
    this exactly, not approximately, for both confirmed levers (WO_LEVER_SUBTREE_03_RETURN
    §A.2: `changed_presses=0` too, not just the signed channel) — an exact-zero test is
    what the evidence supports; a tolerance/epsilon would be an unjustified extra magic
    number this WO's own discipline forbids inventing without cause."""
    return all(v == 0.0 for v in row)


def _attributed_exogenous_effect(a, b, presses, acted_by_press, magnitude_b,
                                  confound_ids=frozenset()) -> Optional[float]:
    """The promotion test for a self-invariant candidate lever `a` against partner `b`:
    does `b` change reliably when `a` is the click target, and rarely otherwise?

    Returns a strength in [-1, 1] (on-target change rate minus off-target change rate) on
    promotion, `None` otherwise. Two gates, both reusing EXISTING ratified constants rather
    than inventing new ones:
      - `MIN_ACTIVE` (already the pair-formation floor elsewhere in this module) as the
        minimum number of recorded `a`-targeted presses — too few clicks is not evidence.
      - `COUPLE_CORR` (already the bar the signed-channel path itself requires for a pair
        to be COUPLED, not just a CANDIDATE) as the bar for `on_rate - off_rate` — the two
        statistics are on the same [-1, 1] scale, so reusing the one constant is principled,
        not a coincidence of convenience.

    ONE-PRESS SETTLE-BACK EXCLUSION, found RED-first against real data, not assumed up
    front: this WO's real fixture shows a reactor (e.g. `###010`, life 1) GROW by exactly
    the reaction's cell count on the press `a` is clicked, then SHRINK back to baseline on
    the very NEXT press, unconditionally — confirmed directly (`region_at`: cc 848→956 on
    the click, 956→848 the press after, regardless of what is clicked next). A naive
    off-target scan counts that settle-back frame as "changed while untargeted" and
    penalizes a genuine lever for its own reaction's second half. The press immediately
    following an `a`-targeted press is excluded from the off-target set for exactly this
    reason — it is not independent evidence, it is the same reaction's echo. This is a
    minimal, data-forced exclusion (one adjacency rule), not a tuned window: it removes
    exactly the frames the real evidence showed are mechanically entangled with an
    on-target press, nothing more.

    CROSS-LEVER CONFOUND EXCLUSION, also found RED-first, and evidence-gated rather than a
    blanket rule: the real fixture round-robins clicks across several self-invariant
    candidates in a life (7 here, only 2 of them genuine remote levers) — a press that is
    off-target for `a` can still be *on*-target for a *different* candidate `c`, and `c`'s
    own genuine reaction can land on a worldline `b` that also happens to be `a`'s partner.
    Confirmed directly: `###005`'s off-target scan against `###009` was picking up press
    index 6, which is `###004`'s own click (a different self-invariant candidate), where
    `###009` genuinely shrinks 368→240 (`region_at`) — a real, evidenced effect of
    `###004`'s click, not noise, and not evidence against `###005`'s specificity. (This
    does not contradict `WO_LEVER_SUBTREE_03_RETURN` §A.3's press-6→7 cell attribution,
    which used the *destination* node's region and so only ever captures GROW, never
    SHRINK — the same 128 cells that vacate `###009` there were re-attributed to a growing
    neighbour; the magnitude channel used here, unlike that whole-frame ownership pass, is
    symmetric to grow/shrink by construction.)

    Blanket-excluding every OTHER self-invariant candidate's presses (tried first, found
    wrong RED-first) starves the off-target denominator to near-empty and lets ANY partner
    through at strength≈1.0 — not a test anymore. `confound_ids` is deliberately narrower:
    the caller passes only the OTHER candidates that a separate pass has *already*
    independently confirmed cause `b` to change (their own on/off rates clear the same bar
    this function applies) — so a press is excluded from `a`'s off-target set only when
    there is standing evidence someone else explains it, never merely because someone else
    was clicked. A press in `confound_ids` (that candidate's own click) or immediately
    following one (that candidate's own settle-back echo) is excluded, mirroring the rule
    already applied to `a`'s own click above.

    ABSTENTION ON AN EMPTY OFF-TARGET SET, found by the existing regression floor, not
    assumed up front: a candidate `a` that happens to be the ONLY thing ever clicked in a
    window has zero untargeted presses once its own click and every confound is excluded —
    defaulting `off_rate` to 0.0 in that case turns absence of counter-evidence into
    confirming evidence (any partner that merely changes on `a`'s clicks, including a
    worldline that changes on EVERY press regardless of what is clicked, would promote at
    strength=1.0). `NESTED_TAXONOMY_SPEC_v5` §4's ∃/∀ law and this module's own sibling
    marginal (`_action_marginal`, which abstains at -1.0 over an empty un-targeted set)
    already settle this: ∀ over an empty set is vacuously true, so it is a logical guard,
    not a tuned threshold — an empty off-target set abstains (`None`), it does not default
    to a maximal strength.

    Confirmed against real ground truth (`WO_LEVER_SUBTREE_03_RETURN` §A.2/A.3, re-verified
    here after all exclusions): both real levers show on_rate=1.0 (9/9 and 9/9 targeted
    presses, `b` changed every time), off_rate=0.0 over a genuinely non-empty eligible
    untargeted set (0 of it showed a coincidental change once settle-back echoes and
    confirmed cross-lever confounds are excluded) — strength=1.0, comfortably clearing
    `COUPLE_CORR` with margin to spare, not a threshold tuned to just barely admit the
    known-good case.
    """
    targeted_idx = [i for i in range(len(presses)) if acted_by_press[i] == a]
    if len(targeted_idx) < MIN_ACTIVE:
        return None
    untargeted_idx = [i for i in range(len(presses))
                       if acted_by_press[i] != a
                       and acted_by_press[i] not in confound_ids
                       and not (i > 0 and acted_by_press[i - 1] == a)
                       and not (i > 0 and acted_by_press[i - 1] in confound_ids)]
    if not untargeted_idx:
        return None
    on_target = sum(1 for i in targeted_idx if magnitude_b[i] != 0)
    on_rate = on_target / len(targeted_idx)
    off_target = sum(1 for i in untargeted_idx if magnitude_b[i] != 0)
    off_rate = off_target / len(untargeted_idx)
    strength = on_rate - off_rate
    if strength > COUPLE_CORR:
        return strength
    return None


def _form_stability(wl, nodes) -> float:
    """Mean jaccard(region@n, region@n-1) across the ###'s presence. High = shape barely
    changes → this criterion ABSTAINS on figure/ground (it cannot separate figure/ground)."""
    js: List[float] = []
    for left, right in zip(nodes, nodes[1:]):
        ra = region_at(wl, left)
        rb = region_at(wl, right)
        if ra is None or rb is None:
            continue
        A, B = set(ra.cells), set(rb.cells)
        js.append(len(A & B) / len(A | B) if (A | B) else 1.0)
    return sum(js) / len(js) if js else 1.0


def _churn_depth(wl, nodes, deltas, presses) -> float:
    """Mean |signed delta| / cell_count over active presses. Low = shallow churn → abstains."""
    vals = []
    for i, left in enumerate(presses):
        cc = _cc(wl, left)
        if cc > 0 and deltas[i] != 0:
            vals.append(abs(deltas[i]) / cc)
    return sum(vals) / len(vals) if vals else 0.0


# ---- render (human-gradable; beside the footprint + roles blocks) -----------

def render_coupling_block(report: CouplingReport, worldlines) -> str:
    cls = {w.id: w.first_region.class_id for w in worldlines}
    lines: List[str] = [
        "COUPLING (weave-native · pair-motion law · derived-not-stored · size = tie-break only)"]
    if report.pairs:
        lines.append("  pairs (### a ~ ### b · corr · k · stable? · acted):")
        for p in sorted(report.pairs, key=lambda q: -abs(q.corr)):
            tag = " COUPLED" if (abs(p.corr) > COUPLE_CORR and p.ratio_stable) else ""
            acted = f" · acted=###{p.acted_member:03d}" if p.acted_member is not None else ""
            lines.append(
                f"    ###{p.wid_a:03d}(c{cls.get(p.wid_a,'?')}) ~ ###{p.wid_b:03d}(c{cls.get(p.wid_b,'?')}): "
                f"corr={p.corr:+.3f} k={p.ratio_k:+.2f} stable={p.ratio_stable} "
                f"active={p.active_presses}{acted}{tag}")
    else:
        lines.append("  pairs: none above threshold")
    lines.append("  panel (per-### · which criteria fire vs abstain):")
    lines.append("    ### (class) | best|corr| | ratio-stab | active | size-rank | form-stab | churn"
                 " | indep | depend | (untgt/tgt of live)")
    for wid in sorted(report.panel):
        r = report.panel[wid]
        stab = "inf" if r.ratio_stability == float("inf") else f"{r.ratio_stability:.3f}"
        ind = "  -  " if r.action_independence < 0 else f"{r.action_independence:.3f}"
        dep = "  -  " if r.action_dependence < 0 else f"{r.action_dependence:.3f}"
        lines.append(
            f"    ###{wid:03d}(c{cls.get(wid,'?')}) | {r.best_corr:.3f} | {stab} | {r.active_presses:3d} | "
            f"{r.size_rank:2d} | {r.form_stability:.3f} | {r.churn_depth:.3f} | "
            f"{ind} | {dep} | ({r.untargeted_presses}/{r.targeted_presses} of {r.live_presses} live)")
    if report.complement_ids:
        for wid in report.complement_ids:
            lines.append(f"  complement: ###{wid:03d}(c{cls.get(wid,'?')}) = dependent/residual member "
                         f"(loosest independent coupling) — consciously ignored, NOT dropped")
    else:
        lines.append("  complement: none derived (no loose residual outside a tight relay)")
    return "\n".join(lines)
