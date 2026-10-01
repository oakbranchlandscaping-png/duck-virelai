"""WEAVE · rejoin — two additive, EXACT post-passes that thread a terminated worldline onward.

Canon: 02 §4 identity lives on the worldline; 01 §3 no background — a swept ground is
threaded by MEASURED relations, never by size, class or position. R-H: a death is provisional.
R-M (2026-09-07): deciding which worldline the floor IS is an ego-relative act — the DEFORM
fold is not the weave's to make and lands at Rung 3 (`roles/ground.py`) as an exact predicate
over the sealed ego's exchange. Here a DEFORM is an honest termination.

Transcription origin (R-C): virelai_v4/weave/rejoin.py @ oracle-v4 (348 lines, read whole).
  2. Occlusion witness (WO-OCCLUSION-01/03): an exact cell-set that vanished under a single
     strictly-covering region at EVERY interior node and resumed is one object; the witness
     names what stood on it. No gap constant — full cover at every node is self-limiting.
  3. Return (WO-RETURN-01): a birth whose fingerprint exactly equals a terminated worldline's
     last fingerprint is that worldline returning, at any distance, earliest first.
What it proved: the swept ground threads end-to-end on vc33 and ls20; Y = 26 / 27 — WITH the
origin's pass 1, which this file no longer carries.

═══ RETIRED · pass 1 · F-0003 CLOSED BY R-M ═══ The origin's DEFORM re-join (WO_WEAVE_R2C:
a DEFORM-terminated worldline joins its unique same-class BIRTH successor at t+1 when
|W∩R|/min ≥ 0.80 and |W∩R|/max ≥ 0.80) carried two CHOSEN numbers, labeled F-0003 from G0-04
and transcribed only because the Rung 0 exit was byte-fidelity to v4's LIST 2. The Director
ruled (R-M) that v4 is origin, never oracle, for that decision. The pass is retired from the
production tree at commit d905dff → G3-01; its text survives as a TEST INSTRUMENT
(`tests/oracle/retired_deform_fold.py`) whose only job is to reproduce v4's LIST 2 so the
departure stays measurable. What the number decided, measured on 2026-09-07: on the harness
run 1 (131 cuts) it folded 17 golden worldlines into 2 (16 floor fragments and one Black
76-cell object that deformed once, no ego exchange); on run 2, 3 into 1. Effect here: passes 2
and 3 run on the un-folded worldlines, so the floor arrives at Rung 3 as fragments whose
exact-fingerprint returns (pass 3) are already threaded — the home configuration is ONE
worldline across its revisits.

Kept verbatim: the bridging edge carries Verb.DEFORM for both passes (the origin reports this
as a mismatch and does not fix it; neither does this file — the reader of a bridge verb reads
the signature, which is exact).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from virelai_golden.substrate.ledger import Cut
from virelai_golden.substrate.scan import Region
from virelai_golden.weave.edge import Anchor, WeaveEdge
from virelai_golden.weave.verbs import Verb, transition_signature
from virelai_golden.weave.worldline import Worldline

def _merge(w: Worldline, b: Worldline) -> Worldline:
    """W absorbs B, keeping W's earlier id; the bridge is a DEFORM edge with an exact signature."""
    bridge = WeaveEdge(w.last_region, b.first_region, Verb.DEFORM, Anchor.NONE, None,
                       transition_signature(w.last_region, b.first_region))
    return Worldline(w.id, w.steps + b.steps, w.edges + (bridge,) + b.edges)


def _replace(wls: List[Worldline], old: Worldline, merged: Worldline, absorbed: Worldline) -> List[Worldline]:
    return [merged if x is old else x for x in wls if x is not absorbed]


# ── pass 2 · occlusion witness (exact) ─────────────────────────────────────────────────────

@dataclass(frozen=True)
class OcclusionWitness:
    """A worldline ended at `at_node` under a single region standing on ALL its cells at every
    interior node, and its exact cell set resumed at `resumed_node`. Recorded, never read for
    meaning at this rung."""

    terminated_id: int
    successor_id: int
    at_node: int
    resumed_node: int
    covering: Tuple[Tuple[int, Region], ...]


def _full_covers(cells: frozenset, cut: Cut) -> List[Region]:
    """Single regions whose cells are a STRICT superset — equality is the object itself."""
    return [r for r in cut.regions if cells < r.cells]


def _witnesses_for(w: Worldline, wls: Sequence[Worldline], order: List[int],
                   node_of: Dict[int, Cut]) -> List[OcclusionWitness]:
    t, wr = w.last_node, w.last_region
    if t not in order:
        return []
    lo = order.index(t)
    out: List[OcclusionWitness] = []
    for b in sorted(wls, key=lambda x: (x.first_node, x.id)):
        if b is w or b.first_node <= t or b.first_node not in order:
            continue
        if b.first_region.value != wr.value or b.first_region.cells != wr.cells:
            continue
        interior = order[lo + 1:order.index(b.first_node)]
        if not interior:
            continue
        covering: List[Tuple[int, Region]] = []
        for n in interior:
            covers = _full_covers(wr.cells, node_of[n])
            if not covers:
                break
            covering.append((n, min(covers, key=lambda r: (r.area, r.value, r.anchor))))
        else:
            out.append(OcclusionWitness(w.id, b.id, t, b.first_node, tuple(covering)))
    return out


def _occlusion_pass(wls: List[Worldline], cuts: Sequence[Cut]) -> Tuple[List[Worldline], List[OcclusionWitness]]:
    order = [c.node for c in cuts]
    node_of = {c.node: c for c in cuts}
    seen: List[OcclusionWitness] = []
    changed = True
    while changed:
        changed = False
        for w in sorted(wls, key=lambda x: (x.last_node, x.id)):
            cands = _witnesses_for(w, wls, order, node_of)
            if not cands:
                continue
            wit = cands[0]
            succ = [x for x in wls if x.id == wit.successor_id]
            if not succ:
                continue
            seen.append(wit)
            wls = _replace(wls, w, _merge(w, succ[0]), succ[0])
            changed = True
            break
    return wls, seen


def occlusion_witnesses(wls: Sequence[Worldline], cuts: Sequence[Cut]) -> List[OcclusionWitness]:
    """The witnesses only, joining nothing."""
    order = [c.node for c in cuts]
    node_of = {c.node: c for c in cuts}
    out: List[OcclusionWitness] = []
    for w in wls:
        out.extend(_witnesses_for(w, wls, order, node_of))
    return out


# ── pass 3 · return (exact) ─────────────────────────────────────────────────────────────────

def _earliest_return(w: Worldline, wls: Sequence[Worldline]) -> Optional[Worldline]:
    fp = w.last_region.fingerprint
    cands = [b for b in wls if b is not w and b.first_node > w.last_node
             and b.first_region.fingerprint == fp]
    return min(cands, key=lambda b: (b.first_node, b.id)) if cands else None


def _return_pass(wls: List[Worldline]) -> List[Worldline]:
    changed = True
    while changed:
        changed = False
        for w in sorted(wls, key=lambda x: (x.last_node, x.id)):
            succ = _earliest_return(w, wls)
            if succ is None:
                continue
            wls = _replace(wls, w, _merge(w, succ), succ)
            changed = True
            break
    return wls


def merge(w: Worldline, b: Worldline) -> Worldline:
    """W absorbs B (B's every step later than W's last), keeping W's earlier id. The one merge
    primitive of the tree; `roles/ground.py` folds with it under R-M."""
    return _merge(w, b)


def re_join(worldlines: Sequence[Worldline], cuts: Sequence[Cut]) -> List[Worldline]:
    """The two exact passes, in the origin's order: occlusion witness, then return.
    `cuts` is required here (v4 gated both on it; every golden caller has the cuts)."""
    wls = list(worldlines)
    if not wls:
        return wls
    wls, _ = _occlusion_pass(wls, cuts)
    return _return_pass(wls)
