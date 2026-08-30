"""WO-WALL-01 · WHAT STOPS THE EGO AND DOES NOT CHANGE.

**THE SEAL.** A worldline seals `WALL` when it carries a blocking tag and holds ONE
fingerprint. Two conjuncts, both counts, no bound of any kind.

**IT MEASURES NOTHING NEW.** `blocking_tags` already lifts a refusal to the fingerprint of
the object standing where the ego's footprint would have landed — the Director's own
ruling, implemented at `collide_tags.py:95`. This module reads it and asks one further
question of the worldline that owns the tag. `blocking_tags`, `_landing` and `_holders`
are untouched.

**WHY ONE FINGERPRINT IS THE DISCRIMINATOR, MEASURED BEFORE IT WAS BUILT.**
`WO_COUNTER_MINE_01` split the tagged population over twenty-one records and found no
middle:

    one fingerprint, tagged across the whole life   ###020 · ###016 · ###009   never crossed
    many fingerprints, tagged in fragments          ###019 (6-10 of them)      crossed on 21/21

Frames cannot separate them — an owner that re-mints every few nodes accumulates tagged
frames exactly as an unchanging one does. **What separates them is how many fingerprints
the owner spent doing it**, and it is the same discriminator that typed the ground read
from the other side: *the floor re-mints when the ego walks through it; a wall does not.*
Corpus-wide, 64 owners carried exactly one tagged fingerprint and 57 carried more.

**THE EGO SET, NOT THE DRIVING TONE.** `blocking_tags` compares each candidate against
`_region_at_last(ego)` — ONE tone's footprint at the window's last node — so the other
sealed tone tags itself as a blocker, and an earlier footprint of the driving tone does
too. `WO_WALL_MINE_00` §5.1 measured **24 such tags on 9 of 21 records**. Every worldline
in `verdict_egos` is excluded here, which is what `RULING_EGO_WORLDLINE_v1` §4 requires
and what a single `ego: int` parameter structurally cannot express.

**WORLD SCOPE, APPLIED BEFORE THE TESTS FOUND IT** (`WO-COUNTER-EXCHANGE-02`'s lesson).
This predicate needs no scope flag because it is **structurally inert off a directional
world**: `Transitions.refused` is built only from an ego worldline's own MOVE/HELD edges
(`ego_read.py:277-286`), and `blocking_tags` returns `frozenset()` on an empty refusal set
by its own guard (`collide_tags.py:127`). A world with no sealed ego has no refusal record
at all, so the seal cannot fire there — not because a flag forbids it, but because there
is nothing to read. Stated and proved rather than gated: adding a `has_directional` term
here would be a line asserting a doubt the record has already settled.

**A RECORD, NEVER A GENERALISATION.** The key is the fingerprint and the verdict is the
worldline's. There is no class term in this module, no perimeter, no footprint size and no
position — a wall is the thing standing where the ego would have landed, and nothing else.

**ONE DEBT, INHERITED AND RECORDED.** `bearing_map` is imported inside the function body
rather than at module scope. `role_read` imports this module and `collide_drive` imports
`role_read` (`collide_drive.py:93`), so a module-level import would close a cycle. The
projection is `{action: bearings}` over `EgoMap.observed` and its honest home is
`weave/ego_read.py` beside the field it reads — the same debt `collide_tags` recorded for
`_region_at_last` and the three type aliases, and it should move with them. **Deferred
rather than duplicated**: one producer of the fact, and the cycle stated instead of a
second copy that could drift.

Pure and stdlib-only beyond the two weave reads. Writes no belief and masks nothing.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Sequence

from virelai_v4.weave.collide_tags import blocking_tags


def fingerprints(worldline) -> FrozenSet:
    """Every distinct `(class_id, cells)` this worldline held across its trail.

    The immortal identity, counted. A worldline that never changed footprint or class
    carries exactly one; one that re-minted carries as many as it minted."""
    return frozenset((r.class_id, r.cells) for (_node, r) in worldline.steps)


def wall_read(worldlines, cuts, ego_of, egos: Sequence[int]) -> Dict[int, str]:
    """`{worldline_id: basis}` for every worldline that seals WALL.

    The tags of EVERY sealed ego are unioned before any exclusion, so a blocker refusing
    only the second tone is seen; then every sealed ego is removed, so neither tone can
    seal on itself. Absence of a sealed ego, of cuts, or of a measured map yields `{}` —
    **absence, not an assertion that nothing blocks.**"""
    from virelai_v4.weave.collide_drive import bearing_map      # cycle; see the header
    if not egos or not cuts:
        return {}
    by_id = {w.id: w for w in worldlines}
    owner: Dict[FrozenSet, int] = {}
    for w in worldlines:
        for fp in fingerprints(w):
            owner.setdefault(fp, w.id)
    tagged = set()
    for e in egos:
        m = ego_of.get(e)
        if m is None or e not in by_id:
            continue
        tagged |= blocking_tags(cuts, by_id, e, bearing_map(m), m.transitions.refused)
    out: Dict[int, str] = {}
    for fp in tagged:
        wid = owner.get(fp)
        if wid is None or wid in egos:
            continue
        held = fingerprints(by_id[wid])
        if len(held) == 1:
            out[wid] = (f"refused the ego and held ONE fingerprint across all "
                        f"{len(by_id[wid].steps)} node(s) it was present → WALL")
    return out


def wall_worldlines(verdicts) -> FrozenSet[int]:
    """Every worldline whose verdict carries the wall field, ascending.

    Placed here rather than in a consumer for the reason `verdict_egos`' docstring gives:
    the producer of a fact owns the reader of it, so two readers cannot disagree."""
    return frozenset(wid for wid, rv in verdicts.items()
                     if getattr(rv, "wall", False))
