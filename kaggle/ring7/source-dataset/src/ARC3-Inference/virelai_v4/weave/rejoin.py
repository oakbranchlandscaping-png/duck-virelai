"""WO_WEAVE_R2C · DEFORM re-join — thread the swept ground without fusing the figures.

An ADDITIVE POST-PASS over ``weave_window`` output. It threads a DEFORM-terminated
worldline (a swept region that both loses and gains cells, so the cascade could not
license a single verb and re-BIRTHed it each node) back into ONE persistent ### —
by MEASURED cell-overlap, never by size, class, or background.

STRUCTURAL NOTES (mandatory, per Director):
  * ADDITIVE POST-PASS. Does NOT modify ``weave/edge.py`` (the cascade) or
    ``weave/worldline.py`` (the threader) — both are proven and committed. If the
    re-join ever mis-joins, it lifts out cleanly without touching the proven layer.
  * MEASURED overlap only. NO size shortcut, NO class constant, NO is_background.
    The thresholds below are RATIOS (dominance / mutuality), never absolute-size cuts.
  * GUARDS THE R2b FIGURE-COMPLEMENT. A swept ground is threaded; two same-class
    figures that merely pass over each other (mover pass-through) must NEVER fuse —
    that would destroy the fill-bar↔counter reactive complement R2b reads.

THE RULE — a DEFORM-terminated worldline W (last region at node t) re-joins a
successor region R (a BIRTH born at t+1, SAME class) iff ALL hold:
  (1) DOMINANT   overlap / min(|W_last|, |R|) >= THETA_DOM   — most of the smaller persists;
  (2) MUTUAL     overlap / max(|W_last|, |R|) >= THETA_MUT   — neither side is tiny vs the join
                 (rejects a small block transiently sitting on a big region);
  (3) SUSTAINED  R is the UNIQUE successor passing (1)&(2) — if two pass, it is AMBIGUOUS
                 and W is left terminated (never guess a join);
  (4) NOT-A-PASS-THROUGH  R is a BIRTH (it matched nothing in the cascade). A mover
                 CONTINUES via MOVE/GROW/SHRINK and is therefore never a BIRTH candidate —
                 so a figure sliding over the ground is structurally excluded here.

Conservative by design: a MISSED join is an honest residual; a WRONG join is a
corruption. Bias hard toward the former. Deterministic; frozenset arithmetic;
multi-cell-jump robust (no adjacency assumption).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from virelai_v4.weave.worldline import Worldline
from virelai_v4.weave.edge import WeaveEdge, Verb, Anchor
from virelai_v4.weave.transition_signature import transition_signature

# Phase-0 (live vc33): the true swept ground (class-3) persists at ~96% cell-overlap
# every edge; the synthetic mis-join (a small block on a big region) has mutual ~4%.
# The committed synthetic DEFORMs (reflected-L 67%, move+resize 0%) stay below. 0.80
# threads the ground and rejects every mis-join case.
THETA_DOM: float = 0.80
THETA_MUT: float = 0.80


def _overlap(a, b) -> Tuple[float, float]:
    """(dominant, mutual) overlap ratios of two cell-sets: intersection over the
    smaller, and over the larger. (0.0, 0.0) if either is empty."""
    a, b = frozenset(a), frozenset(b)
    if not a or not b:
        return 0.0, 0.0
    inter = len(a & b)
    return inter / min(len(a), len(b)), inter / max(len(a), len(b))


def _merge(w: Worldline, b: Worldline) -> Worldline:
    """W absorbs B: one continuous worldline keeping W's (earlier) id. The bridging
    transition is recorded as a DEFORM edge — the honest verb the re-join spans."""
    # WO-VERB-FROM-TRANSITIONS-01: the bridge has BOTH endpoints, so unlike every
    # residual verb `weave_edge` emits it is signature-computable — and it must be, since
    # `_change_magnitude`'s DEFORM branch exists solely for this edge and now reads the
    # signature rather than dispatching on the verb.
    bridge = WeaveEdge(prev=w.steps[-1][1], now=b.steps[0][1],
                       verb=Verb.DEFORM, anchor=Anchor.NONE, delta=None,
                       signature=transition_signature(w.steps[-1][1], b.steps[0][1]))
    return Worldline(id=w.id, steps=w.steps + b.steps,
                     edges=w.edges + (bridge,) + b.edges)


# ---------------------------------------------------------------------------
# WO-OCCLUSION-01 · THE OCCLUSION WITNESS — an ADDITIVE pass, appended below the
# committed fold. It lifts out cleanly: delete this block and the module's
# behaviour at `cuts=None` is unchanged, which is the structural note at the head
# of this file applied to itself. `edge.py` and `worldline.py` are NOT touched.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OcclusionWitness:
    """The contact event, recorded — not merely a bridge.

    A worldline terminated at ``at_node`` while a region stood on ALL of its cells,
    and its exact cell set resumed at ``resumed_node``. ``covering`` holds the
    single covering region for every interior node, so the witness names WHAT was
    standing on it. **Nothing reads this for meaning** — no role, no seal, no
    attribution. It is recorded because a contact event is evidence; what it means
    is not this rung's to say."""

    terminated_id: int
    successor_id: int
    at_node: int
    resumed_node: int
    covering: Tuple[Tuple[int, Any], ...]      # ((node_index, RegionClay), …)


def _full_covers(cells, cut) -> List[Any]:
    """Every SINGLE region at this cut whose cells are a SUPERSET of ``cells``.

    **A union of regions does not qualify and this is deliberate** — it is the
    audit's own rule, kept. "Several regions between them happen to cover these
    cells" is a different claim from "this region was standing on it", and only the
    second is a contact event.

    **STRICT superset, and the strictness is load-bearing.** A region whose cells
    EQUAL ``cells`` is the object itself, present and visible — not something
    standing on it. A non-strict test admits that case, and it admitted it in the
    first build of this rung: an interior node where the object was plainly visible
    counted as covered, which let a second, later reappearance qualify and
    manufactured an ambiguity out of nothing. Exact and strict: no ratio, no
    tolerance."""
    return [r for r in cut.regions if cells < r.cells]


def _witnesses_for(w: Worldline, wls, cuts, order, node_of) -> List[OcclusionWitness]:
    """Every qualifying reappearance of ``w``'s exact cell set, earliest first.

    Three requirements, all exact — no threshold, no ratio, no tolerance, and NO GAP
    CONSTANT. The gap needs no bound because full coverage must hold at EVERY
    interior node; the requirement is self-limiting, and a tuned constant would be a
    measurement smuggled into the predicate."""
    t = w.steps[-1][0]
    wr = w.steps[-1][1]
    if t not in order:
        return []
    lo = order.index(t)
    out: List[OcclusionWitness] = []
    for b in sorted(wls, key=lambda x: (x.first_node, x.id)):
        if b is w or b.first_node <= t or b.first_node not in order:
            continue
        # (1) EXACT cell set and class — not overlap-equivalence
        if b.first_region.class_id != wr.class_id or b.first_region.cells != wr.cells:
            continue
        interior = order[lo + 1:order.index(b.first_node)]
        if not interior:
            continue           # no interval to occlude — not a witness, not a "yes"
        covering = []
        for n in interior:
            # (2) FULL cover by (3) a SINGLE region, at EVERY interior node
            covers = _full_covers(wr.cells, node_of[n])
            if not covers:
                break
            # deterministic pick, the weave's own visual order — ties never guessed
            covering.append((n, min(covers, key=lambda r: (r.cell_count, r.class_id,
                                                           r.anchor))))
        else:
            out.append(OcclusionWitness(terminated_id=w.id, successor_id=b.id,
                                        at_node=t, resumed_node=b.first_node,
                                        covering=tuple(covering)))
    return out


def _occlusion_pass(worldlines, cuts):
    """Join witnessed pairs. Returns ``(worldlines, witnesses)``.

    Iterates to quiet like the fold above, so an object occluded repeatedly threads
    end-to-end. The earlier id wins, via the same `_merge` the committed pass uses —
    which means the bridge carries `Verb.DEFORM` whatever the true terminating verb
    was. That mismatch is REPORTED by this rung and ruled by CE; it is not fixed
    here, because `coupling.py`'s DEFORM branch depends on the edge existing.

    **ONE CODE PATH — WO-OCCLUSION-03.** `WO-OCCLUSION-01` built two variants,
    EARLIEST and REFUSE, because `WO-OCCLUSION-01 §2` expected `:105`'s uniqueness
    discipline to have something to arbitrate. It does not, and the reason is
    structural rather than sampled: a second, later reappearance must cross the
    first one's node where the object is PRESENT, and presence and strict cover are
    mutually exclusive because regions are a disjoint partition. The mirror case is
    closed by the same argument. Both orientations are pinned as tests.

    The variants were therefore the same function, and CE accepted the proof, so the
    branch is gone. A contested successor cannot arise; were the proof ever wrong,
    the second claimant would find its successor already absorbed and skip — safe by
    construction, not by a guard."""
    wls = list(worldlines)
    seen: List[OcclusionWitness] = []
    changed = True
    while changed:
        changed = False
        order = [c.node_index for c in cuts]
        node_of = {c.node_index: c for c in cuts}
        for w in sorted(wls, key=lambda x: (x.steps[-1][0], x.id)):
            cands = _witnesses_for(w, wls, cuts, order, node_of)
            if not cands:
                continue
            wit = cands[0]     # the earliest, and provably the only, candidate
            succ = [x for x in wls if x.id == wit.successor_id]
            if not succ:
                continue
            seen.append(wit)
            merged = _merge(w, succ[0])
            wls = [merged if x is w else x for x in wls if x is not succ[0]]
            changed = True
            break
    return wls, seen


def occlusion_witnesses(worldlines, cuts) -> List[OcclusionWitness]:
    """The witnesses only, joining nothing — for measurement and for tests."""
    order = [c.node_index for c in cuts]
    node_of = {c.node_index: c for c in cuts}
    out: List[OcclusionWitness] = []
    for w in worldlines:
        out.extend(_witnesses_for(w, worldlines, cuts, order, node_of))
    return out


# ---------------------------------------------------------------------------
# WO-RETURN-01 · A DEATH IS PROVISIONAL — a SECOND additive pass, appended below
# the occlusion block on the same terms. It lifts out cleanly: delete this block
# and the module's behaviour is the committed one. `edge.py` and `worldline.py`
# are NOT touched, and neither is the overlap fold's `t + 1` guard.
# ---------------------------------------------------------------------------

def _last_fingerprint(w: Worldline):
    """The `(class_id, cells)` this worldline wore when it ended."""
    return (w.steps[-1][1].class_id, w.steps[-1][1].cells)


def _first_fingerprint(w: Worldline):
    """The `(class_id, cells)` a worldline was born wearing."""
    return (w.first_region.class_id, w.first_region.cells)


def _earliest_return(w: Worldline, wls) -> Optional[Worldline]:
    """The EARLIEST birth whose fingerprint exactly matches `w`'s last — or `None`.

    **THE DIRECTOR'S RULE, AND IT IS ONE COMPARISON.** A death is provisional; a birth
    whose fingerprint exactly matches a terminated worldline's last fingerprint is that
    worldline returning, **at any distance**. No window, no bound, no tolerance, no gap
    constant — `test_return.py` asserts that over this module's AST.

    **EARLIEST-FIRST IS AN ORDERING, NOT A TIE-BREAK — and it is what dissolves the
    ambiguity `WO_RETURN_AUDIT_00` Q2/Q3 measured.** Twenty of twenty-two terminations
    had more than one candidate and twenty births were claimed by up to nine
    terminations; **every one of those was a CHAIN read as a fan.** `###004` matched
    twenty-one births because it returned twenty-one times, and `###043` matched the
    remaining twenty. Join the earliest, and each later match belongs to the later link.
    The same discipline `witnessed_levers` uses: an existential claim is satisfied by its
    earliest evidence.

    **THE SUCCESSOR STARTS STRICTLY AFTER THIS WORLDLINE ENDS**, so the merged trail is
    strictly increasing in node order and **the joined worldline can never hold two
    regions at one node.** That is `WO-RETURN-01 §6`'s named corruption risk, closed by
    construction rather than by a check."""
    fp = _last_fingerprint(w)
    t = w.steps[-1][0]
    cands = [b for b in wls
             if b is not w and b.first_node > t and _first_fingerprint(b) == fp]
    if not cands:
        return None
    return min(cands, key=lambda b: (b.first_node, b.id))


def _return_pass(worldlines) -> List[Worldline]:
    """Join every termination to its earliest exact-fingerprint return.

    **ITERATES TO QUIET**, like both passes above, so an object buried and revealed
    repeatedly threads end-to-end into ONE worldline rather than a run of pairs —
    measured at twenty-one links in one chain on one record.

    **THE EARLIER ID WINS**, via the same `_merge` the committed passes use. That is
    what retires the queue defect without touching the queue: `_merge` prepends the
    original's steps, so the rejoined worldline's `first_node` is the ORIGINAL's — it is
    a window seed again, `_newborn_footprints` (`collide_drive.py:593`) reads
    `first_node > win_start` and no longer flags it, and `_order_key`'s novelty term
    stops promoting it. **`_newborn_footprints` and `_order_key` are untouched; the
    defect disappears as a consequence of the identity rule.**

    **THE OCCLUSION WITNESS IS RETAINED AND NOT MERGED.** It runs first and keeps its
    own record: it answers *why it vanished*, naming the covering region. This answers
    *is it the same object*. `WO_RETURN_AUDIT_00` Q6 measured the two populations as
    disjoint on one record — complementary readings, both kept, neither reconciled."""
    wls: List[Worldline] = list(worldlines)
    changed = True
    while changed:
        changed = False
        for w in sorted(wls, key=lambda x: (x.steps[-1][0], x.id)):
            succ = _earliest_return(w, wls)
            if succ is None:
                continue
            merged = _merge(w, succ)
            wls = [merged if x is w else x for x in wls if x is not succ]
            changed = True
            break
    return wls


def re_join(worldlines, theta_dom: float = THETA_DOM,
            theta_mut: float = THETA_MUT, cuts=None) -> List[Worldline]:
    """Re-join DEFORM-terminated worldlines to their unique dominant-sustained
    same-class BIRTH successors. Additive: returns a new worldline list; the proven
    threader's output is the input. Iterates so a ground swept across many nodes
    threads into one ### end-to-end. First-appearance numbering preserved (the
    earlier id wins; absorbed ids are retired).

    WO-OCCLUSION-01 · **``cuts`` DEFAULTS TO ``None`` AND THAT IS THE FIDELITY GATE.**
    Without cuts this function cannot see occupancy, so the occlusion pass cannot run
    and every existing caller is byte-identical to the committed behaviour — not by
    assertion but by construction. A caller opts in by handing over the window's cuts;
    nothing else changes."""
    wls: List[Worldline] = list(worldlines)
    if not wls:
        return wls
    win_start = min(wl.first_node for wl in wls)

    changed = True
    while changed:
        changed = False
        for w in sorted(wls, key=lambda x: (x.steps[-1][0], x.id)):
            t = w.steps[-1][0]
            wr = w.steps[-1][1]
            cands = []
            for b in wls:
                if b is w:
                    continue
                if b.first_node != t + 1:          # (4) successor born at t+1
                    continue
                if b.first_node <= win_start:      # (4) a window-seed is not a birth
                    continue
                if len(b.steps) < 1 or b.first_region.class_id != wr.class_id:
                    continue
                dom, mut = _overlap(wr.cells, b.first_region.cells)
                if dom >= theta_dom and mut >= theta_mut:   # (1) dominant, (2) mutual
                    cands.append(b)
            if len(cands) == 1:                    # (3) sustained = unique successor
                merged = _merge(w, cands[0])
                wls = [merged if x is w else x for x in wls if x is not cands[0]]
                changed = True
                break
            # len(cands) > 1 -> AMBIGUOUS: leave terminated, never guess a join.
    if cuts is not None:
        wls, _w = _occlusion_pass(wls, cuts)
        # WO-RETURN-01 · the identity rule, LAST — after the evidence-bearing pass, so a
        # join the occlusion witness can explain is made by the witness and carries its
        # record. What reaches here is what no witness could account for.
        #
        # **INSIDE THE `cuts` GATE, AND THAT IS NOT ARBITRARY.** This pass needs no cuts
        # — it reads fingerprints alone — and a first draft ran it unconditionally.
        # `test_occlusion`'s two REDs caught that immediately: `re_join` WITHOUT cuts is
        # required to be byte-identical to the committed fold, which this module's own
        # docstring calls the fidelity gate, *"not by assertion but by construction."*
        # **A caller opts into every additive pass by handing over the window's cuts, or
        # into none of them.** One gate, both passes, nothing else changes.
        wls = _return_pass(wls)
    return wls
