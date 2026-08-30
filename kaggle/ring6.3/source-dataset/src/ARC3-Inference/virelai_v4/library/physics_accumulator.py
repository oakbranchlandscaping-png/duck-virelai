"""
virelai_v4/library/physics_accumulator.py — Per-lever vector-consistency
accumulation (WO-A.2b, Physics Reframe NR-01).

Accumulates each lever's measured operations (perception/operation_measurer)
across observations and writes the agreement statistic into
LibraryObject.causal_agreement — replacing the structural 0% the set
representation could never escape (the changed-cell set marches and never
repeats; the operation is constant).

THE FORMULA (pinned at WO-A.2b §0(e), hand-verified in-gate):
  agreement(v1..vn) = mean over unordered pairs (i,j) of score(vi, vj)
  score(vi, vj) = 1.0                       if cos(vi,vj) > 0.99
                                            and min||/max|| > 0.9
                = max(0, cos * mag_ratio)   otherwise
  Per lever: mean over operation signatures having >= 2 observations.
  GATE-P1 (46,56) — four consistent presses + one true inverse —
  gives C(4,2)/C(5,2) = 0.60 exactly.

Write surface (additive, write-only — A.2b is write-but-not-read):
  - context.physics_vectors[lever_rid]  (new field, PERSIST_LIVES_RESET_LEVEL)
  - context.physics_verdicts[lever_rid] (new field, same tier)
  - LibraryObject.causal_agreement + causal_observation_count via the
    existing setter (semantic_library.py:518,546-547; both unwritten before
    this WO — fill, not collide).
Existing probe-outcome accumulators (probe_confirmation_count, log-score
axes, causes/caused_by) are NOT touched; the captain's predicates read
those, and the floor depends on them.

Saturated presses (no movers) record nothing — GATE-P1 semantics: real
terminal states, excluded from pairwise consistency.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple, TYPE_CHECKING

from virelai_v4.contracts.causal_verdict import CausalVerdict
from virelai_v4.contracts.conserved_transfer import ConservedTransfer
from virelai_v4.library.conserved_transfer_author import author_conserved_transfer
from virelai_v4.library.constants import LEVER_TYPED_THRESHOLD  # WO-E6
from virelai_v4.library.library_roles import LibraryRole, ObservationStatus

# WO-EFFECT-LABEL — the COUNTER is never a lever's world-effect subject: it ticks
# every press, and physics operates on RAW grid deltas, so the tick leaks in. A
# live role read (mirroring cycle_probe's _live_counter_cells, WO-CP1-FIX-B)
# keeps it out of mover-subject resolution; the labeled disregard record itself
# lives on the object (disregarded_live_region_ids), written by the classifier
# path. (EGO deliberately NOT excluded: a lever CAN drive the ego — a teleporter
# — so ego exclusion would discard a real effect. The ego-navigation-noise
# question in NAV worlds is flagged separately, not decided here.)
_NON_EFFECT_ROLES = frozenset({LibraryRole.COUNTER})
from virelai_v4.library.semantic_library import SemanticLibrary
from virelai_v4.perception.operation_measurer import (
    MeasuredOperation,
    measure_operations,
    measure_shape_change,
)

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

logger = logging.getLogger(__name__)

_COS_FENCE = 0.99
_MAG_FENCE = 0.9
_VERDICT_AGREEMENT_BAR = 0.5   # the GATE-P1 GO bar


@dataclass
class LeverPhysics:
    """Accumulated operation evidence for one lever (keyed by region_id)."""
    vectors_by_signature: Dict[Tuple, List[Tuple[float, float]]] = \
        field(default_factory=dict)
    bracket_count: int = 0     # brackets with >= 1 measured operation


def _pair_score(va: Tuple[float, float], vb: Tuple[float, float]) -> float:
    """§0(e) pair score: 1.0 inside the cos/magnitude fences, else
    max(0, cos * magnitude_ratio)."""
    na = math.hypot(*va)
    nb = math.hypot(*vb)
    if na < 1e-9 and nb < 1e-9:
        return 1.0
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    cos = (va[0] * vb[0] + va[1] * vb[1]) / (na * nb)
    mag = min(na, nb) / max(na, nb)
    if cos > _COS_FENCE and mag > _MAG_FENCE:
        return 1.0
    return max(0.0, cos * mag)


def pairwise_agreement(vectors: List[Tuple[float, float]]) -> Optional[float]:
    """Mean pair score over all unordered pairs; None with < 2 vectors."""
    n = len(vectors)
    if n < 2:
        return None
    total, pairs = 0.0, 0
    for i in range(n):
        for j in range(i + 1, n):
            total += _pair_score(vectors[i], vectors[j])
            pairs += 1
    return total / pairs


def lever_agreement(physics: LeverPhysics) -> Optional[float]:
    """Per-lever agreement: mean over signatures with >= 2 observations."""
    per_sig = [pairwise_agreement(vecs)
               for vecs in physics.vectors_by_signature.values()]
    scored = [a for a in per_sig if a is not None]
    if not scored:
        return None
    return sum(scored) / len(scored)


def record_operations(physics: LeverPhysics,
                      operations: List[MeasuredOperation]) -> None:
    """Append one bracket's measured operations into the accumulator."""
    if not operations:
        return                      # saturated press — nothing recorded
    for op in operations:
        physics.vectors_by_signature.setdefault(
            op.signature, []).append(op.vector)
    physics.bracket_count += 1


def _write_observation_status(library_obj, new_status: ObservationStatus) -> None:
    """Monotonic-promotion status write (WO-A2c-Core §1.2).

    Status does NOT downgrade: once OBSERVED_RIGID is written, a later
    OBSERVED_NON_RIGID does not overwrite it (falsification of the rigid
    model on a later press is its own observation, counted separately).
    Call ONLY from the classified press paths (3 and 4). The 'no write'
    paths (1a no-probe, 1b life-start, 2 region-absent) leave existing
    status intact by NOT calling this helper — preserving prior-life
    observations and honoring loss-of-subject ≠ falsification.
    """
    if library_obj.observation_status == ObservationStatus.OBSERVED_RIGID:
        return  # monotonic: no downgrade
    library_obj.observation_status = new_status


def _revise_saturation_on_observed_delta(obj) -> None:
    """WO-E6 revision route — discovery, not composition.

    A press that produced an observable delta (rigid motion or a real non-rigid
    change) is direct evidence the lever is NOT saturated: saturation is, by
    definition, a press that changed nothing (the cycle-probe ZERO_DELTA
    terminal). So when such a delta lands on a lever that was marked saturated,
    clear obj.saturated — the lever un-saturated, discovered from the recorded
    delta during the captain's normal per-lever B3 round-robin. The captain
    composed nothing; it pressed the least-observed lever and the world (changed
    by its work on other levers) answered.

    Keys on obj.saturated ONLY — the same field the display B2 reads
    (dossier.py:208). Does NOT write lever_mechanism: the type/condition
    de-collapse (SATURATED still living in the type field) is WO-E7, sequenced
    after this. Idempotent; a no-op when the lever was not saturated."""
    if getattr(obj, "saturated", False):
        obj.saturated = False


def _confirmed_translation(physics: LeverPhysics,
                           agreement: Optional[float]) -> bool:
    """DIRECTIONAL_DISPLACEMENT requires agreement above the GO bar and
    every recorded operation to be an actual displacement (nonzero)."""
    if agreement is None or agreement <= _VERDICT_AGREEMENT_BAR:
        return False
    return all(math.hypot(*v) >= 1.0
               for vecs in physics.vectors_by_signature.values()
               for v in vecs)


def _overlap_argmax(
    before_cells: FrozenSet[Tuple[int, int]],
    library: SemanticLibrary,
    exclude_rid: Optional[int],
    skip_background: bool,
) -> Optional[int]:
    """Raw cell-intersection argmax over library regions; ties broken by lowest
    region_id (deterministic), requiring at least one overlapping cell. Skips
    the pressed lever and, when skip_background, any region the agent has
    observed to be background (is_background — earned upstream from the
    universal ignore_score channels, defeasible). Returns None when no eligible
    region overlaps."""
    best_rid: Optional[int] = None
    best_overlap = 0
    for rid in sorted(library.objects.keys()):
        if rid == exclude_rid:
            continue
        obj = library.objects[rid]
        if skip_background and obj.is_background:
            continue
        if obj.role in _NON_EFFECT_ROLES:   # WO-EFFECT-CLEAN: no COUNTER/EGO subject
            continue
        cells = obj.cells
        if not cells:
            continue
        overlap = len(before_cells & cells)
        if overlap > best_overlap:
            best_overlap = overlap
            best_rid = rid
    return best_rid


def _resolve_subject(
    before_cells: FrozenSet[Tuple[int, int]],
    library: SemanticLibrary,
    exclude_rid: Optional[int],
    prefer_figure: bool = True,
) -> Optional[int]:
    """Resolve a moved cluster to the library region it displaced, by before-
    cell overlap (WO-EFFECT-STORE-RIGID, WO1; figure-over-ground WO-C4).

    PORT-WITH-MODIFICATIONS of V3.5's overlap-similarity primitive
    (attribution_engine.try_confirm Jaccard, IPA-LEVER-EFFECT-RUNG-WO1): here
    the use-case is "which of N library objects did this cluster move," so the
    score is raw cell-intersection argmax (not Jaccard-vs-one-mask), requiring
    at least one overlapping cell, ties broken by lowest region_id
    (deterministic). The pressed lever is excluded as a self-attribution guard.

    WO-C4 — figure over described ground: when prefer_figure, run the overlap
    argmax among non-background candidates first; the background (is_background)
    is selected only when no non-background region overlaps at all — recorded
    and attributable, never mistaken for the actor, never silently dropped. The
    only signal read is is_background; no class identity, no threshold here.

    Returns None when no library region overlaps — surfaced by the caller, NOT
    silently dropped. NOTE: library.cells is spawn-frozen, so overlap is most
    reliable on a subject's first (pre-displacement) observation; this is the
    Director-verified addressing surface (see IPA finding)."""
    if not before_cells:
        return None
    if prefer_figure:
        figure = _overlap_argmax(
            before_cells, library, exclude_rid, skip_background=True)
        if figure is not None:
            return figure
    return _overlap_argmax(
        before_cells, library, exclude_rid, skip_background=False)


def _gather_seam_deltas(library: SemanticLibrary, lever_rid: int):
    """Read the lever's recorded non-rigid deltas, splitting functional
    endpoints from the boundary side by the already-attributed is_background
    label (WO-C3 §4 iii). READ-ONLY over attribution — it does not re-attribute
    (Fold 2). Returns (functional_deltas, complement_or_None)."""
    obj = library.objects.get(lever_rid)
    functional: Dict[int, int] = {}
    complement = 0
    have_complement = False
    if obj is None:
        return functional, None
    for e in obj.lever_effects:
        delta = getattr(e, "cell_count_delta", None)
        if delta is None:
            continue
        subj = library.objects.get(e.subject_region_id)
        if subj is not None and getattr(subj, "is_background", False):
            complement += delta
            have_complement = True
        else:
            functional[e.subject_region_id] = delta
    return functional, (complement if have_complement else None)


def _forward_predicts(prior_candidate: ConservedTransfer,
                      current_deltas: Dict[int, int]) -> bool:
    """The forward, out-of-sample, EXACT-VALUE gate (§4 ii): a candidate licensed
    from a prior press must predict THIS press's complementary member's exact
    signed delta. For each ordered member pair, the prior relation predicts the
    partner's delta as -current[member]; license only when that exact value is
    the partner's measured delta this press. Not directional, not same-press."""
    members = prior_candidate.member_subject_ids
    if len(members) < 2:
        return False
    for a in members:
        if a not in current_deltas:
            return False
    for a in members:
        predicted = prior_candidate.predict_complement_delta(a, current_deltas[a])
        partners = [m for m in members if m != a]
        if not any(current_deltas[p] == predicted for p in partners):
            return False
    return True


def _author_conserved_transfer_at_seam(
    library: SemanticLibrary, context: "VirelaiContext", lever_rid: int,
) -> None:
    """WO-C3 seam: author the conserved-transfer candidate from measured deltas
    and LICENSE it only when a prior press's candidate out-predicts THIS press
    (forward gate; a single press never licenses — no same-press fit). On
    license, the Substrate writes the relation (single writer, Fold 4).

    global_functional_conserves is NOT stipulated here (left False): no live
    Descent fires from an unmeasured premise. The author's Descent path is
    armed and exercised by tests that supply the measured global signal; arming
    it on the live canary awaits the global-conservation measurement (flagged)."""
    functional, complement = _gather_seam_deltas(library, lever_rid)
    if not functional:
        return
    candidate = author_conserved_transfer(
        lever_rid, functional,
        complement_candidate=complement,
        global_functional_conserves=False,
        holdout=None,
    )
    prior = context.conserved_transfer_candidates.get(lever_rid)
    if candidate is not None and prior is not None:
        prior_candidate, _prior_deltas = prior
        if _forward_predicts(prior_candidate, functional):
            library.record_conserved_transfer(lever_rid, candidate)
    if candidate is not None:
        context.conserved_transfer_candidates[lever_rid] = (candidate, dict(functional))


def run_physics_measurement(
    library: SemanticLibrary,
    context: "VirelaiContext",
    prev_grid,
    grid,
) -> None:
    """The A.2b substrate hook. Called from sync_library inside the probe-
    outcome block (after _process_previous_probe_outcome, before the
    last_probe_target_* clears). Fences:
      - fires only when last_probe_target_region_id is set (same gate as
        the probe-outcome observer; cleared by reset_for_new_level, so a
        post-advance bracket can never fire — structural fence);
      - skips when prev_grid is None (life start);
      - skips when the probed region is not in the library.
    Write-only: nothing reads physics_vectors/verdicts or causal_agreement
    yet. The behavioral payoff is A.3.
    """
    lever_rid = context.last_probe_target_region_id
    # Path 1a (no probe) / 1b (life-start, no prior): NO status write —
    # 1b preserves any OBSERVED_RIGID earned in a prior Groundhog-Day life.
    if lever_rid is None or prev_grid is None:
        return
    # Path 2 (region absent): loss of subject, not falsification — NO write.
    if lever_rid not in library.objects:
        return
    obj = library.objects[lever_rid]
    operations = measure_operations(prev_grid, grid)
    # Path 3: press observed, no rigid mover fit. Distinguish a SILENT press
    # (nothing changed — saturated / no-op / HUD-only) from a real non-rigid
    # change, BEFORE any status write. An empty delta is a halt, not an
    # observation: record the silence, write no OBSERVED_NON_RIGID, attribute
    # no effect. (ZERO_DELTA_SILENT — halts are information.)
    if not operations:
        shape = measure_shape_change(prev_grid, grid)
        if shape is None:
            # Silent press: nothing changed. No status write, no effect.
            # WO-E6 (loop guard): if this is a TYPED lever, the silent press is
            # a B3 effect-probe that found nothing — count it so the least-
            # observed round-robin de-prioritizes a genuinely-saturated lever
            # (else effort stays 0 forever -> re-probed every frame). §0.3:
            # observation_count is NOT touched on a null press, so this is the
            # only place a null re-probe registers. Discovery — counts what was
            # observed (silence), composes nothing.
            if obj.sigmoid_confidence("lever") >= LEVER_TYPED_THRESHOLD:
                obj.effect_null_presses += 1
            return
        # Real non-rigid change: cells moved but no area-conserving rigid mover.
        _write_observation_status(obj, ObservationStatus.OBSERVED_NON_RIGID)
        # WO-E6 (revision route): an observed delta is proof the lever is not
        # saturated. If it was marked saturated, it un-saturated — discovery.
        _revise_saturation_on_observed_delta(obj)
        # WO-EFFECT-NONRIGID (WO3): characterize the non-rigid change so it
        # accumulates a LeverEffect entry — closing the substrate gap that left
        # the captain's least-observed predicate seeing 0 entries for non-rigid
        # levers (perpetually targeting them, never rotating). Descriptive only;
        # no verb label. Unlike the rigid path, the pressed lever is NOT excluded
        # from subject resolution (exclude_rid=None): a non-rigid self-toggle
        # changing its own cells is a real, characterizable effect.
        subject_rid = _resolve_subject(
            shape.changed_cells, library, exclude_rid=None,
            prefer_figure=True)
        if subject_rid is not None:
            library.record_lever_effect(
                lever_rid=lever_rid,
                subject_region_id=subject_rid,
                operation_kind="NON_RIGID",
                cell_count_delta=shape.net_cell_change,
            )
        # WO-C3: author/license the conserved-transfer relation from the lever's
        # measured non-rigid deltas (Substrate writes on license — single writer).
        _author_conserved_transfer_at_seam(library, context, lever_rid)
        return
    # Path 4: press observed, rigid model fit → OBSERVED_RIGID.
    physics = context.physics_vectors.setdefault(lever_rid, LeverPhysics())
    record_operations(physics, operations)
    # WO-E6 (revision route): a rigid delta is observed motion — proof the
    # lever is not saturated. If it was marked saturated, it un-saturated
    # (discovery from the recorded delta). Keys on obj.saturated; no
    # lever_mechanism write (the de-collapse is WO-E7).
    _revise_saturation_on_observed_delta(obj)
    # WO-EFFECT-STORE-RIGID (WO1): resolve each moved cluster to the library
    # region it displaced and record the durable per-subject effect. ADDITIVE —
    # the existing agreement / verdict / status writes below are unchanged.
    for operation in operations:
        subject_rid = _resolve_subject(
            operation.before_cells, library, exclude_rid=lever_rid,
            prefer_figure=True)
        if subject_rid is None:
            logger.debug(
                "lever %s: moved cluster %s overlapped no library region; "
                "effect not attributed", lever_rid, operation.signature)
            continue
        library.record_lever_effect(
            lever_rid=lever_rid,
            subject_region_id=subject_rid,
            vector=operation.vector,
            operation_kind="RIGID",
        )
    agreement = lever_agreement(physics)
    if agreement is not None:
        library.update_object_behavior(
            lever_rid,
            causal_agreement=agreement,
            causal_observation_count=physics.bracket_count,
        )
    if _confirmed_translation(physics, agreement):
        context.physics_verdicts[lever_rid] = \
            CausalVerdict.DIRECTIONAL_DISPLACEMENT.name
    # Status write + clean count are the LAST mutations on this path.
    _write_observation_status(obj, ObservationStatus.OBSERVED_RIGID)
    obj.rigid_observation_count += 1


__all__ = [
    "LeverPhysics",
    "pairwise_agreement",
    "lever_agreement",
    "record_operations",
    "run_physics_measurement",
    "ObservationStatus",
]
