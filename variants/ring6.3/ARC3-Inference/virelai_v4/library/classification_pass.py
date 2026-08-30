"""virelai_v4/library/classification_pass.py — Classification pass over the semantic library.

Relocated from library/library_sync.py (WO-MINE-CLEAN-05-PHASE-3).
This module contains the classification pass — the constructs that read
accumulated cellular and behavioral evidence and assign or update each
LibraryObject's role classification.

Single Responsibility: read SemanticLibrary + CellHistory + total actions;
write per-object role classifications via library.update_object_role(...).
Does not populate from spawn, does not process deltas, does not handle
probe outcomes, does not derive HUD masks.

Import sovereignty: library/, perception/, stdlib only.
No imports from contracts/, targeting/, strategy/, memory/. No numpy.

Public surface:
    MIN_CLASSIFY_ACTIONS — calibration constant exposed for tests
    _ObjectRegionProxy   — adapter wrapping LibraryObject for classify_role
    _build_cell_evidence — accumulated-evidence wrapper around build_cell_evidence
    _partition_ego_from_active — EGO classification via displacement coherence
    _classify_objects    — main classification pass
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

from virelai_v4.library.cell_evidence_builder import build_cell_evidence
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
from virelai_v4.library.counter_march import maybe_open_counter_sublabel  # WO-E14 D1
from virelai_v4.library.role_classifier import CellEvidence, classify_role
from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary
from virelai_v4.cybernetic.cell_history import CellHistory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Classification threshold
# ---------------------------------------------------------------------------

MIN_CLASSIFY_ACTIONS = 3
# Minimum total actions observed before any object is classified.
# Calibration parameter — tuned against live games.


# ---------------------------------------------------------------------------
# Region proxy — adapts LibraryObject fields for classify_role
# ---------------------------------------------------------------------------

class _ObjectRegionProxy:
    """Minimal Region proxy for classify_role. Adapts LibraryObject fields.

    classify_role reads .value (class_id), .area (cell_count), and .cells.
    Only these three fields are provided.
    """
    __slots__ = ("value", "area", "cells")

    def __init__(self, obj: LibraryObject) -> None:
        self.value = obj.class_id
        self.area  = obj.cell_count
        self.cells = obj.cells


# ---------------------------------------------------------------------------
# CellEvidence adapter (WO-RM-03: body extracted to cell_evidence_builder.py)
# ---------------------------------------------------------------------------

def _build_cell_evidence(
    obj: LibraryObject,
    cell_history: Optional[Dict[Tuple[int, int], CellHistory]],
    library: SemanticLibrary,
    total_actions: int,
) -> Optional[CellEvidence]:
    """Delegate to cell_evidence_builder.build_cell_evidence (extracted WO-RM-03)."""
    return build_cell_evidence(obj, cell_history, library, total_actions)


# ---------------------------------------------------------------------------
# WO-RM-03: Ego partition — classify EGO from displacement coherence
# ---------------------------------------------------------------------------

def _partition_ego_from_active(
    library: SemanticLibrary,
    ego_body_cells: frozenset,
    ego_value_set: set,
) -> None:
    """Partition the active population by displacement coherence.

    Objects where is_active=True AND cells overlap ego_body_cells
    AND class_id in ego_value_set are classified EGO at confidence 0.90.
    All other active objects remain REACTIVE (or their current role).

    Called after _update_active_static, before general role classifier.
    Silently skips illegal transitions (COUNTER is terminal; already-EGO is idempotent).
    """
    if not ego_body_cells or not ego_value_set:
        return  # ego not yet detected — nothing to partition
    for obj in library.objects.values():
        if not obj.is_active:
            continue
        if obj.role == LibraryRole.EGO:
            continue  # already EGO — idempotent, no re-assignment
        if bool(obj.cells & ego_body_cells) and obj.class_id in ego_value_set:
            try:
                library.update_object_role(obj.region_id, LibraryRole.EGO, confidence=0.90)
                # WO_SWEEP_EGO_BIND D1a: feed the Store-A ego axis through the
                # existing setter so the captain-store render (render_read →
                # implied_role, which argmaxes the log-score axes, NOT obj.role)
                # derives EGO — matching the categorical role just written, with
                # no derivation-layer edit. Fires once per object: already-EGO
                # objects are skipped above (idempotent), so the axis is not
                # re-accumulated across frames. Confidence mirrors the 0.90
                # categorical assignment (no invented number).
                accumulate_role_evidence(obj, LibraryRole.EGO, 0.90)
            except ValueError:
                pass  # COUNTER or other terminal role — leave unchanged
    # (partition complete — EGO objects assigned by displacement coherence)


# ---------------------------------------------------------------------------
# Classification pass
# ---------------------------------------------------------------------------

def _classify_objects(
    library: SemanticLibrary,
    cell_history: Optional[Dict[Tuple[int, int], CellHistory]],
    total_actions: int,
) -> None:
    """Assign evidence-based roles to library objects.

    Called at the end of Mode B after the change_count update loop.
    Skips objects already classified with high confidence (>= 0.7).
    Catches ValueError from illegal role transitions — logs and continues.
    Does NOT run in Mode A (spawn) or Mode C (Groundhog Day skip).
    """
    grid_area = library.header.grid_rows * library.header.grid_cols

    for obj in library.objects.values():
        # WO-RM-03: EGO is terminal — skip regardless of ego_confirmed flag.
        # Partition assigns EGO before _classify_objects runs; the ego_confirmed
        # flag is set later in the same sync frame. Both paths are covered here.
        if obj.role == LibraryRole.EGO:
            continue
        # WO-C5-02: confirmed COUNTER is terminal — skip re-classification.
        # action_independence_ratio is the classification signal; once an object
        # is confirmed COUNTER it should not be demoted by a transient low-ratio frame.
        if obj.role == LibraryRole.COUNTER and obj.confidence >= 0.70:
            continue
        # WO-02 LEVER-CATALOG demotion guard: lever_locked objects stay LEVER forever.
        # Set True when probe evidence promotes a region to LEVER via _process_previous_probe_outcome.
        if getattr(obj, "lever_locked", False):
            continue
        # High-confidence non-UNKNOWN objects are already classified — skip.
        # WO-RM-04-FIX-2: REACTIVE is excluded from this gate so that a life counter
        # misclassified REACTIVE by Pre-B (which fires at active_frame_count=2, before
        # Rule A accumulates its required 5 observations) can be re-evaluated and promoted
        # to COUNTER once actions_observed >= _COUNTER_MIN_OBSERVATIONS.
        # WO-EA-01-PHASE-1 (F4+ Variant A): STATIC is also excluded — observation-count-
        # based STATIC entry (Rule 5 at total_actions=20) can fire before cell-evidence
        # accumulates. Without this exclusion, late pip transitions (e.g., ls20's class-8
        # within-level lives-remaining cluster) cannot reach Pre-A and the object is locked
        # at STATIC despite confirmed cell-layer change_count accumulation.
        if obj.role not in (LibraryRole.UNKNOWN, LibraryRole.REACTIVE, LibraryRole.STATIC) and obj.confidence >= 0.7:
            continue

        evidence = _build_cell_evidence(obj, cell_history, library, total_actions)
        if evidence is None:
            continue

        proxy = _ObjectRegionProxy(obj)
        new_role, new_conf = classify_role(
            region=proxy,
            grid_area=grid_area,
            hud_class_ids=set(),
            type_map=None,       # Evidence-first: type_map not available here
            cell_evidence=evidence,
            region_current_role=obj.role,   # WO-C5-02: EGO exemption inside classifier
            is_active=obj.is_active,
            active_frame_count=obj.active_frame_count,
            total_actions=total_actions,
            ignore_score=obj.ignore_score,
            cell_count_history=obj.cell_count_history,  # WO-E09-v2 D2: march recognizer input
        )

        # WO-BLUEPRINT-07: BBA Layer One accumulator hook (primary site).
        # Per coexistence audit §4.5: the role classifier's verdict is the
        # cleanest evidence emitter to feed the per-axis log-scores. The
        # hook fires BEFORE any categorical-write skip below, so even
        # UNKNOWN/unchanged-role frames contribute evidence to the axes
        # (the accumulator no-ops on UNKNOWN / non-BBA-axis roles by
        # design — see library/log_score_accumulator.py). The existing
        # categorical writes (`obj.confidence`, `update_object_role`)
        # remain unchanged during Sub-Phase 3 coexistence.
        accumulate_role_evidence(obj, new_role, new_conf)

        # WO-E14 D1: open the COUNTER sub-label under the (reactive) role when the
        # accumulated counter belief crosses CONFIRMATION_THRESHOLD. Additive —
        # does not touch obj.role / obj.confidence (the ratchet below is untouched).
        maybe_open_counter_sublabel(obj)

        if new_role == LibraryRole.UNKNOWN:
            continue   # Classifier says insufficient evidence — no change

        if new_role == obj.role:
            if new_conf > obj.confidence:
                obj.confidence = new_conf
            continue

        # WO-EA-01-PHASE-1 (F4+ Variant A): cell-evidence override for STATIC → REACTIVE.
        # V3.5 principle: any non-zero cell-layer change_count → REACTIVE wins. V4's
        # stored-confidence ratchet would otherwise lose the comparison (STATIC's
        # confidence climbs with total_actions; REACTIVE's confidence at low change_count
        # is below STATIC's by Life 5). The override translates V3.5's fresh-classification
        # principle to V4's stored-state architecture for this specific transition.
        cell_evidence_override = (
            obj.role == LibraryRole.STATIC
            and new_role == LibraryRole.REACTIVE
            and evidence is not None
            and evidence.change_count > 0
        )

        # Different role — apply only when new evidence is stronger,
        # OR when the F4+ cell-evidence override applies (STATIC → REACTIVE).
        if new_conf > obj.confidence or cell_evidence_override:
            try:
                library.update_object_role(obj.region_id, new_role, new_conf)
            except ValueError as exc:
                # WO-CAMPAIGN3-PHASE3-04 post-second-canary surgical update
                # (May 5, 2026): demoted from logger.warning to logger.debug
                # per Director's framing "cells can be levers and reactive."
                # Trace 3 finding: substrate fights itself; transition graph
                # correctly preserves LEVER classification (per Phase 2 contact
                # reactivity attribution); role_classifier evaluates each frame
                # and proposes REACTIVE (per cell-change evidence); transition
                # graph blocks LEVER → REACTIVE per
                # ``library/semantic_library.py:279``; ValueError is the
                # expected substrate-honest enforcement. The blocked-transition
                # event is logging noise around correct behavior; demoted to
                # debug-level so it doesn't flood canary terminals at runtime
                # while remaining diagnosable when DEBUG logging is enabled.
                logger.debug(
                    "Illegal role transition blocked for region %d: "
                    "%s → %s — %s",
                    obj.region_id, obj.role.value, new_role.value, exc,
                )
