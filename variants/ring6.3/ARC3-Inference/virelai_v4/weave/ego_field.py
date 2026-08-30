"""WO-EGO-02 · THE FIGURE, THE GROUND IT CROSSES, AND WHICH BUTTON MOVED IT.

THE RULE, in the Director's words:

    Press a direction. What moved? Was it the counter? If not, it is the world's
    response — and an ego is the case where that response depends on WHICH button.
    And just as there must be two counters, for every ego there is a `+1` background
    it must move across.

Act, observe, subtract the known noise, name what remains. **The same rule that closed the
lever, with the attribution changed from *pressed here* to *pressed this button*.**

The account this reads is `crossing.py`'s and is deliberately not recomputed here. That
module answers *who exchanged ground with whom, under which button*; this one answers *and
which of the two was the figure* — the question a complement verdict structurally cannot.

════════════════════════════════════════════════════════════════════════════════════════
THE SEAL — three conjuncts, and every one of them is structural rather than tuned:

    1. A CROSSING. There is a partner `p` with which this worldline exchanges cells over
       at least one edge, with NO intrinsic churn on those edges. Nothing appeared from
       nowhere and nothing vanished — every cell that moved changed hands between two
       worldlines that both persist. **That is the `+1` background, and `partners` names
       it.**

    2. THE EXCHANGE DEPENDS ON WHICH BUTTON. There are two observed actions under which
       this worldline gained DIFFERENT cells from that same partner. A figure crossing a
       ground takes ground from ahead of it, and "ahead" is what the button selects.

    3. THIS ONE IS DISPLACED AND THE PARTNER IS NOT. Across the window the candidate's own
       footprint occupies MORE THAN ONE distinct `RegionClay.anchor`; the partner's
       occupies exactly one. **This is the whole of the tie-break** — see below.

**CONJUNCT 2 IS `SPEC_PIXEL_ARITHMETIC_v1` §3's channel law on the exchange stratum**,
exactly as `ego_read`'s is on the bearing stratum: a worldline whose exchange is the same
whatever you press keys on THAT-ANY action — channel (b), a schedule — not on WHICH
action, channel (a). It is a set inequality, not a rate; no constant appears in this
module and a test forbids one.

WHY CONJUNCT 3 EXISTS, and it is the one thing the first build got wrong. **The exchange
record is symmetric by construction**: every cell the figure gains from the ground is a
cell the ground loses to the figure, so conjuncts 1 and 2 are satisfied identically by
BOTH endpoints and the ground typed `EGO` alongside the figure. The asymmetry is not in
the exchange and never was — *a relation is symmetric; a role is not, and the asymmetry
always comes from outside the relation.* CE ruled it DISPLACEMENT: **the figure translates
across the window; the ground re-mints in place.**

  · MEASURED FROM `RegionClay.anchor` OVER THE WORLDLINE'S OWN `steps` — NOT from the
    `MOVE` verb. A `MOVE` requires `_translation`, which requires an identical normalised
    shape, so a figure that changes shape as it crosses produces no `MOVE` at all. Reading
    the anchor series directly is what lets this rung reach the case `ego_read` cannot.
  · `RegionClay.anchor` is `(min row, min col)` of the cell-set — the top-left of the
    bounding box, computed by `clay._anchor`. It is NOT necessarily an occupied cell, and
    an empty cell-set yields the `(-1, -1)` sentinel. That is all it claims to be, and it
    is enough: a footprint re-minting in place holds its top-left; one crossing the board
    does not.
  · **MORE THAN ONE DISTINCT ANCHOR — NO MINIMUM COUNT.** Two is displacement and so is
    twenty. A minimum would be this module's first threshold and there is not one.
  · **WHEN THE PARTNER IS ALSO DISPLACED, NEITHER TYPES FROM THIS CROSSING.** Two figures
    passing through each other are two figures; neither is a ground, so neither crossing
    carries the evidence this seal requires, and the pair is passed over in silence rather
    than resolved by size, class, or position. If one of them is an ego it must earn the
    tag from a different partner or from the bearing read below.

**AND IT DIVERGES FROM `ego_read` ON THE SINGLE-ACTION CASE, DELIBERATELY.** `ego_read`
seals coverage-bounded on one observed action, because one button can still be *consistent*.
Here one button cannot be *distinguished from another*, so conjunct 2 is unsatisfiable and
the seal refuses. **The two modules answer different questions and may disagree; where they
do, the disagreement is recorded and NOT reconciled** (`RULING_OBSERVERS_INTEGRATOR_v1`).

WHY THE CROSSING IS A CONJUNCT AND NOT MERE CORROBORATION — settled from the ratified
layer law rather than from preference. `RULING_BELIEF_HOME_LAYERS_v1` §4 establishes that
**the embodied world has a true logical background where the click world has none.**
Requiring a crossing therefore admits the embodied ego and **structurally excludes the
click worlds**, which have no ground to cross. Making it corroboration instead would leave
the click-world exposure open by a second route, which §9.6 forbids.

Pure and stdlib-only. Reads the crossing account and the worldlines it is handed; computes
nothing else, writes nothing, and decides nothing about any other tag.
"""

from __future__ import annotations

from typing import Any, Dict, NamedTuple, Optional, Tuple

from virelai_v4.weave.crossing import Crossing, crossings

Cell = Tuple[int, int]


class FieldRead(NamedTuple):
    """The crossing account plus the displacement fact each verdict needs beside it.

    Carried together because conjunct 3 is a statement about TWO worldlines — the
    candidate and its partner — and a per-worldline lookup cannot answer it alone."""
    crossings: Dict[int, Tuple[Crossing, ...]]
    displaced: Dict[int, bool]


def anchor_walk(worldline) -> Tuple[Cell, ...]:
    """The worldline's own `RegionClay.anchor` at each of its steps, in node order."""
    return tuple(region.anchor for (_node_index, region) in worldline.steps)


def displacement(worldlines) -> Dict[int, bool]:
    """`{worldline_id: occupied more than one distinct anchor across the window}`.

    No minimum count and no distance: a footprint that held its top-left is not displaced
    and every footprint that did not is. Absence of a worldline from the map is not
    possible — every worldline has at least one step."""
    return {wl.id: len(set(anchor_walk(wl))) > 1 for wl in worldlines}


def field_read(worldlines, cuts, node_actions) -> FieldRead:
    """The whole account this rung reads, assembled once per `infer_roles` call."""
    return FieldRead(crossings=crossings(worldlines, cuts, node_actions),
                     displaced=displacement(worldlines))


def _deciding(field: FieldRead, wid: int) -> Optional[Crossing]:
    """The first crossing satisfying ALL THREE conjuncts, or `None`.

    Conjunct 1 holds by construction — `crossing.py` records only clean exchanges — so
    what is tested here is 2 (the gained set differs by button) and 3 (this one moved and
    the partner did not)."""
    if not field.displaced.get(wid):
        return None
    for c in field.crossings.get(wid) or ():
        if field.displaced.get(c.partner):
            continue                     # two figures crossing; neither is a ground
        sets = list(c.gained_by_action.values())
        if len(sets) > 1 and any(s != sets[0] for s in sets[1:]):
            return c
    return None


def ego_field_seal(field: FieldRead, wid: int) -> bool:
    """All three conjuncts, over any one partner. No threshold, no fraction, no tolerance.

    A crossing whose gained-set is identical under every observed button keys on THAT-ANY
    action and is a schedule, not an ego. With one observed action the comparison has no
    second term and the seal refuses — see this module's header on the deliberate
    divergence from `ego_read` there."""
    return _deciding(field, wid) is not None


def field_basis(field: FieldRead, wid: int) -> str:
    """The verdict's evidence sentence — the ground, the buttons, and what each took."""
    c = _deciding(field, wid)
    if c is None:
        return "no action-dependent crossing over a stationary ground"
    per = " · ".join(f"{a}→{len(g)} cells" for a, g in c.gained_by_action.items())
    return (f"crosses ###{c.partner:03d} — {c.edges} clean exchange"
            f"{'' if c.edges == 1 else 's'}, no intrinsic churn — and took DIFFERENT "
            f"ground under different buttons: {per}; its own footprint occupied more than "
            f"one anchor across the window where ###{c.partner:03d}'s occupied exactly one "
            f"→ EGO (the response depends on which button; the ground it moves across is "
            f"named, not assumed)")


def field_parallax(field: FieldRead, wid: int,
                   ego_read_agrees: Optional[bool] = None) -> str:
    """What the claim does not establish, plus any divergence from the other observer.

    `RULING_OBSERVERS_INTEGRATOR_v1`: where two independent computations of one fact
    disagree, the divergence travels with the verdict and is never silently reconciled."""
    c = _deciding(field, wid)
    extra = ""
    if ego_read_agrees is False:
        extra = ("; ⟂ the own-stream bearing read does NOT seal this worldline — it needs a "
                 "MOVE verb with a translation delta, which a figure that changes shape as "
                 "it crosses never produces. Two observers, two questions, divergence "
                 "recorded and not reconciled")
    n = len(c.gained_by_action) if c else 0
    return (f"coverage: {n} button{'' if n == 1 else 's'} observed on the deciding crossing. "
            f"The ground is the partner the exchange named — no size, no class and no "
            f"position decided it, only that its footprint held ONE anchor while this one "
            f"did not. An action never pressed has no entry and is never inferred from "
            f"another{extra}")
