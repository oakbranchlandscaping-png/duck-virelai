"""WO-GROUND-01 · THE GROUND TYPES, AND IS LOUDLY IGNORED.

**THE CLAIM: a worldline whose deformation IS the ego's motion, and nothing else.**

The Director's ruling: *traversable and blocking are grouped by VISUAL OBJECT — the `###`
worldline — never by class. Once a worldline types as ground, its motion is explained by
its own role: disregarded as a target, recorded everywhere, never erased.*

════════════════════════════════════════════════════════════════════════════════════════
**NOTHING HERE IS NEW EVIDENCE.** Both conjuncts read records that were already computed:

  the worldline's own verb stream   `Worldline.edges` / `.steps` — which presses this
                                    worldline DEFORMED on, and which nodes they produced.
  `crossing.Crossing.per_edge`      every edge on which this worldline's churn was
                                    ENTIRELY owner-owner exchange. `crossing._accumulate`
                                    records an edge only when `complement_verdict`
                                    returned `intrinsic_cells == ∅`, so membership in
                                    this record IS the emptiness test — computed once per
                                    `infer_roles` call, by `field_read`, and until now
                                    read only by the ego and medium seals.

**NO NEW PROVENANCE WORK IS DONE.** `owner_edge` costs 8.16 ms per edge and `field_read`
already pays it (`WO_GROUND_MINE_01 §4`). This module adds set operations over records in
hand: **≈0 ms per frame, measured — see the return.**

**THERE IS NO BOUND OF ANY KIND IN THE PREDICATE.** No threshold, no ratio, no fraction,
no count, no minimum coverage. Both conjuncts are subset containment and non-emptiness,
and `test_ground.py` asserts that over this module's AST. A predicate with a bound would
be a tuned constant wearing a law's clothes — and the discriminator does not need one:

    measured, `WO_GROUND_MINE_01 §2-§3`, on the pinned record `[over-corpus]`
      the ground        68 DEFORM edges · 68 of 68 on an ego MOVE node · 68 of 68 clean
      the oscillator    0 DEFORM edges · GROW 41 · SHRINK 41 · never fires

**THE MULTIPLICITY IS SIGNAL, AND IT IS NOT COLLAPSED.** A ground worldline re-mints its
fingerprint every time the ego walks through it — measured 25 fingerprints for one
worldline over 74 deformations, 108 of 133 steps re-presenting a shape already worn. The
mask operates at the WORLDLINE; `visual_targets` keeps its fingerprint key untouched.
Collapsing the multiplicity would destroy the evidence that identified the ground.

**LOUDLY IGNORED, NEVER DELETED — `lever_witness`' shape.** *Something happened and was
attributed elsewhere* is a different claim from *nothing happened*, and the roster block
below is where the difference is printed. A masked ground object leaves the drive's
to-do list and stays in the record with its basis beside it.

**NO CLASS TERM, NO COLOUR, NO SIZE, NO POSITION.** The predicate reads verbs, node
indices and set membership. There is no legal place in it to put a world's contents.

Pure and stdlib-only. Reads what it is handed, decides one predicate, writes nothing.
"""

from __future__ import annotations

from typing import Any, Dict, FrozenSet, Sequence, Set, Tuple

from virelai_v4.weave.edge import Verb

__all__ = ["deform_nodes", "move_nodes", "clean_exchange_nodes", "is_ground",
           "ground_read", "ground_basis", "ground_worldlines", "ground_block"]


# ---------------------------------------------------------------------------
# The three readings, each off a record already in hand
# ---------------------------------------------------------------------------

def deform_nodes(worldline) -> FrozenSet[int]:
    """The nodes this worldline's own `DEFORM` edges produced.

    `DEFORM` is `edge.py:36`'s verb for *a same-class partner exists but no single
    licensed verb* — the footprint changed in a way no translation, growth or shrink
    explains. A ground worldline earns one every time something walks through it.

    Keyed on `steps[i + 1][0]` — the edge's RIGHT node, the wiring law — so these are
    directly comparable with the ego's move nodes and with `EdgeExchange.node`, which
    is `OwnerEdge.now_node` and therefore the same index."""
    return frozenset(worldline.steps[i + 1][0]
                     for i, e in enumerate(worldline.edges) if e.verb is Verb.DEFORM)


def move_nodes(worldline) -> FrozenSet[int]:
    """The nodes this worldline's own `MOVE` edges produced — where it displaced.

    The same walk as `deform_nodes` on a different verb, kept as its own function
    because *where did this deform* and *where did this move* are two questions and a
    single function taking a verb parameter would be one function with an `and` in its
    name."""
    return frozenset(worldline.steps[i + 1][0]
                     for i, e in enumerate(worldline.edges) if e.verb is Verb.MOVE)


def clean_exchange_nodes(field, wid: int) -> FrozenSet[int]:
    """The nodes on which this worldline's churn was ENTIRELY owner-owner exchange.

    **THIS IS THE EMPTINESS TEST, READ RATHER THAN RECOMPUTED.** `crossing._accumulate`
    skips any edge whose `complement_verdict.intrinsic_cells` is non-empty, so an edge
    reaching `Crossing.per_edge` has already been rated clean by the committed
    discriminator. Asking membership here is asking `intrinsic_cells == ∅` there, without
    a second producer of the same fact and without touching `complement_verdict`.

    **AN UNACCOUNTABLE EDGE IS ABSENT, AND ABSENCE IS ABSENCE.** `crossings` drops an
    edge whose `cell_owners` raised. Such a node is simply not in this set, so a
    worldline that deformed there fails the conjunct and does not type. That is the
    conservative direction: the seal is never granted on evidence that could not be read.
    """
    return frozenset(e.node
                     for crossing in (field.crossings.get(wid, ()) if field else ())
                     for e in crossing.per_edge)


# ---------------------------------------------------------------------------
# The predicate
# ---------------------------------------------------------------------------

def is_ground(worldline, ego_moves: FrozenSet[int], clean: FrozenSet[int]) -> bool:
    """**Its deformation is the ego's motion and nothing else.** Two conjuncts, both
    set relations, no bound of any kind.

    1. Every node it DEFORMED on is a node the driving ego's own `MOVE` edges produced.
    2. Every node it DEFORMED on is one where its churn was pure exchange.

    Plus non-emptiness, which is not a threshold but the difference between *observed to
    deform only under the ego* and *never observed to deform at all*. A worldline that
    never deformed satisfies both subset relations vacuously, and `∅ ⊆ anything` is not
    evidence — it is the absence of evidence, and typing on it would seal the entire
    static board as ground. **Absence is rendered as absence.**"""
    d = deform_nodes(worldline)
    return bool(d) and d <= ego_moves and d <= clean


def ground_basis(worldline, ego_moves: FrozenSet[int], clean: FrozenSet[int]) -> str:
    """The human-gradable evidence sentence, in node counts and nothing else.

    Coverage travels with the claim, as every seal in this build renders it: *this many
    deformations, all of them on the ego's own move nodes, all of them clean.* No cell,
    no colour, no class integer and no extent appears here — the sentence is about
    machinery."""
    d = deform_nodes(worldline)
    return (f"deformed on {len(d)} node{'' if len(d) == 1 else 's'}, "
            f"every one produced by the ego's own displacement and accounted as pure "
            f"owner-owner exchange (intrinsic churn empty); its motion is explained by "
            f"the ego walking through it")


def ground_read(worldlines, verdicts, field, egos: Sequence[int]) -> Dict[int, str]:
    """`{worldline_id: basis}` for every worldline that types GROUND.

    **THE EGO'S MOVE NODES ARE THE UNION OVER EVERY SEALED EGO, NOT THE ELECTED ONE.**
    `masked_worldlines`' own docstring records the rung that fixed this mistake in the
    other direction: *which one do I steer* has one answer, *which of these are mine*
    does not, and `RULING_EGO_WORLDLINE_v1` ratified multi-ego as the default. A ground
    object deforms under whichever body walks through it.

    **NO EGO IS EVER GROUND.** It is excluded before the predicate rather than expected
    to fail it — the body you are steering is identity, not belief, which is the same
    reason `masked_worldlines` bars it at any confidence.

    **NO EGO MEANS NOTHING TYPES, NOT EVERYTHING.** With no sealed ego there are no move
    nodes, the first conjunct cannot hold, and the board is left whole.

    **AND THE CLICK CLAIM IS NARROWER THAN THE CHARTER STATED — SEE THE RETURN §0.**
    `WO-GROUND-01 §5` reasoned that *a click world has no ego MOVE nodes, so the predicate
    cannot fire there*. **That is false at the file.** A verb is read off geometry
    (`edge.py:31` — same class, same shape, translated), never off an action id, so a
    clicked object that translates carries `MOVE` exactly as a pressed one does. What IS
    true, and what the fence asserts, is stronger and simpler: **this module never reads
    an action id at all.** A click world where nothing translates types nothing because
    there are no `MOVE` edges anywhere; a click world where the ego does translate types
    its ground by the same rule as any other world, which is universality working rather
    than failing."""
    by_id = {w.id: w for w in worldlines}
    seen: Set[int] = set(egos)
    ego_moves: FrozenSet[int] = frozenset()
    for wid in seen:
        wl = by_id.get(wid)
        if wl is not None:
            ego_moves = ego_moves | move_nodes(wl)
    out: Dict[int, str] = {}
    for wl in worldlines:
        if wl.id in seen or wl.id not in (verdicts or {}):
            continue
        clean = clean_exchange_nodes(field, wl.id)
        if is_ground(wl, ego_moves, clean):
            out[wl.id] = ground_basis(wl, ego_moves, clean)
    return out


def ground_worldlines(verdicts) -> FrozenSet[int]:
    """Every worldline whose verdict carries the ground claim.

    Reads the field rather than parsing a basis: *is this ground* is a question a
    consumer must be able to ask of the value, which is the whole reason
    `WO-BAND-SPLIT-01`'s precedent was followed. The medium sub-class lives in prose and
    pays that cost; this does not."""
    return frozenset(wid for wid, rv in (verdicts or {}).items()
                     if getattr(rv, "ground", False))


# ---------------------------------------------------------------------------
# Loudly ignored — the roster's record of what the mask removed
# ---------------------------------------------------------------------------

def ground_block(cuts, worldlines, verdicts, masked: FrozenSet[int]) -> Tuple[str, ...]:
    """The roster lines for every visual object the GROUND mask removed from the queue.

    **THE MASK MUST NOT MAKE THEM VANISH, AND WITHOUT THIS BLOCK IT WOULD.** `_queued`
    is `visual_targets` under `masked_worldlines`, and `coverage_roster` renders
    `_queued` — one derivation serving two purposes. Masking a ground worldline
    therefore removes its objects from the drive's to-do list AND from the record of
    what the drive was offered. **The first is the rung; the second would be deletion
    wearing a disregard's clothes.**

    So the difference is derived and printed: the queue as it would stand with the
    ground mask lifted, minus the queue as it stands. Each entry is stated with its
    worldline's basis. Nothing is reconciled and no disposition is invented — a ground
    object was never attempted, and saying it was *NEVER ATTEMPTED* beside objects the
    drive genuinely skipped would be a false equivalence. It carries its own word.

    **`visual_targets` IS IMPORTED INSIDE THE BODY**, the pattern `coverage_sweep.py:330`
    already uses for this exact reason: `collide_drive` imports this module, so a
    module-level import back would be a cycle. The dependency is real, one-directional
    and stated.

    **NO SECOND KEYING.** Both calls are the same `visual_targets` with the same cuts and
    worldlines; only the mask differs, so the fingerprint keys are identical on both
    sides and the difference is exact."""
    from virelai_v4.weave.collide_drive import visual_targets
    ground = ground_worldlines(verdicts)
    if not ground or not cuts:
        return ()
    worked = {t.key for t in visual_targets(cuts, worldlines or [], masked)}
    lifted = visual_targets(cuts, worldlines or [], frozenset(masked) - ground)
    removed = [t for t in lifted if t.key not in worked]
    if not removed:
        return ()
    out = [f"  GROUND — DISREGARDED AS TARGETS, RECORDED HERE ({len(removed)} "
           f"queue entr{'y' if len(removed) == 1 else 'ies'} the mask removed):"]
    # **GROUPED BY SITE, AND THE ENTRY COUNT IS PRINTED RATHER THAN THE MULTIPLICITY
    # DISCARDED.** A ground worldline re-mints its fingerprint every time something walks
    # through it, and `visual_targets` is fingerprint-keyed, so one site can carry many
    # entries — measured 25 at one site on the pinned record. Printing 25 identical lines
    # is noise that HIDES that fact; printing the site once with its count states it. **No
    # entry is dropped and no key is merged** — this is a rendering of the same list, and
    # `WO_DECLARE_INTENT_01 §0.1`'s standing question about the fingerprint-keyed queue is
    # left exactly where it is.
    by_site: Dict[Any, int] = {}
    for t in removed:
        by_site[t.site] = by_site.get(t.site, 0) + 1
    for site, n in sorted(by_site.items(), key=lambda kv: str(kv[0])):
        # `== 1` rather than `> 1`: the module-wide AST fence bans every magnitude
        # comparison, and it CAUGHT this line as a `>` on first writing. The ban is right
        # even for a pluralisation — a bound moved one call up is the same bound, and a
        # fence that carved out "but this one is only rendering" would stop being one.
        entries = "" if n == 1 else f" ({n} queue entries, one per fingerprint)"
        out.append(f"    {site}  →  GROUND (not attempted; its motion is the ego's)"
                   f"{entries}")
    for wid in sorted(ground):
        rv = (verdicts or {}).get(wid)
        basis = getattr(rv, "ground_basis", "") if rv is not None else ""
        out.append(f"    ###{wid:03d} typed GROUND — {basis}")
    return tuple(out)
