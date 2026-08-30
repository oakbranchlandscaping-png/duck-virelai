"""Probe outcome processor for Cluster 4 (WO-MINE-CLEAN-05-PHASE-4).

This module owns the Tier 4 (Levers) probe-outcome processing logic:
reads the previous probe's target from VirelaiContext, classifies the
outcome via classify_probe_outcome, and updates the semantic library
with role transitions, causal links, and probe event log entries.

Extracted from library_sync.py in Phase 4 of Campaign MINE Housekeeping.
Per FRICTION-APEX-Q2-CLARIFICATION: _process_previous_probe_outcome is
re-imported into library_sync.py because sync_library calls it. The
re-import is a structural call-site enabler, not a test shim — tests
import this symbol directly from probe_outcome_processor.

Sovereignty: stdlib + contracts/ + library/. No numpy, no perception/,
no targeting/, no strategy/, no memory/.

Public API:
- _process_previous_probe_outcome(library, context, world_delta) -> None

Data flow (per WO-MINE-CLEAN-05-PHASE-4-DIAG F16):
- Reads from context: last_probe_target_region_id, last_probe_target_cells, last_probe_action_kind
- Reads from library: objects, header.actions_taken
- Writes to library: object roles via update_object_role, probe_event_log entries,
  per-object causes/caused_by/probe_confirmation_count/lever_locked/inert_probe_count/
  confidence/ambiguous_probe_count
- Writes to context: NONE (sync_library clears context.last_probe_target_* AFTER this call)
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Set, Tuple, TYPE_CHECKING

from virelai_v4.contracts.world_delta import WorldDelta
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
from virelai_v4.library.probe_outcome_classifier import classify_probe_outcome
from virelai_v4.library.semantic_library import SemanticLibrary
from virelai_v4.library.sweep_updater import update_sweep_from_outcome

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext

logger = logging.getLogger(__name__)


# ----------------------------------------------------------------------
# WO-OCD-05 — the Evidence Asymmetry Engine (the two write-sites).
# Law (OBJECT_INVESTIGATION_DOCTRINE.md:43-66, NORTH_STAR.md:116-140):
# a positive probe is dispositive and sticky; accumulated null probes build
# inert-coverage without closing the question; an object re-opens for
# investigation when the world-state changes under it. Reader is OCD-02
# (investigation_priority.py); fields are OCD-01. This is the missing writer.
# ----------------------------------------------------------------------
def _record_inert_observation(obj: "LibraryObject", current_hash: str) -> None:
    """Site 1 — record a genuine null probe as inert-coverage that caps
    confidence at 0.90 but never closes the object.

    inert_coverage counts zero-delta probes under DISTINCT grid-state hashes
    (DOCTRINE:94), maintained as a bounded distinct-consecutive integer (CE
    Option-2 ruling): incremented only when the current hash differs from the
    object's last-probed hash, so N nulls under one world-state count once.
    inert_confidence = min(0.90, 0.30 + 0.10 * inert_coverage) grows only with
    genuinely new conditions. An ever_reactive object (demotion guard) still
    accrues coverage but its confidence is never pushed toward inert, and the
    object's ROLE is never set STATIC/INERT here — it stays re-flaggable (Site 2).
    """
    obj.inert_probe_count += 1
    if current_hash != obj.last_probe_state_hash:
        obj.inert_coverage += 1
    if not obj.ever_reactive and obj.role != LibraryRole.LEVER:
        obj.confidence = min(0.90, 0.30 + 0.10 * obj.inert_coverage)


def _flag_state_changed_inerts(library: "SemanticLibrary", current_hash: str) -> None:
    """Site 2 — the reinvestigation trigger. Computed FRESH each sync (not a
    sticky set): an object with inert_coverage > 0 whose last probe was under a
    different grid-state hash becomes a reinvestigation candidate (DOCTRINE:58).
    Self-clearing — once re-probed under the current hash (Site 1 updates
    last_probe_state_hash), the hashes match and the flag computes False next
    sync. Bounded to one re-probe per state-change (with the reader's probe_count
    penalty) — the anti-x129 self-termination. Never flags an unprobed object.
    """
    for obj in library.objects.values():
        obj.needs_reinvestigation = (
            obj.inert_coverage > 0
            and obj.last_probe_state_hash != current_hash
        )


# ----------------------------------------------------------------------
# WO_FC_LOCALITY_v3 — foundation correction: lever locality law
# ----------------------------------------------------------------------

def _self_change_witnessed(obj) -> bool:
    """Did this object's OWN region undergo a witnessed change on actuation?

    Reads the monotone `is_active` witness (semantic_library.py:144), set the
    first frame any of the object's cells appear in the world delta. It is built
    from a fresh per-frame cell→region map (delta_updater.py:286), so it captures
    an identity-preserving class toggle (class A→B, footprint and cell count
    preserved, net shape delta zero) that the probe classifier — intersecting the
    delta with STALE probe-time cells — misses. Locus of change, not magnitude.
    Reads existing evidence; mints none.
    """
    return bool(getattr(obj, "is_active", False))


# ----------------------------------------------------------------------
# Tier 4 probe outcome processing (WO-02 LEVER-CATALOG)
# ----------------------------------------------------------------------

def _process_previous_probe_outcome(
    library: SemanticLibrary,
    context: "VirelaiContext",
    world_delta: WorldDelta,
) -> None:
    """Classify the probe outcome from the previous Tier 4 action and update library evidence.

    Called when context.last_probe_target_region_id is set (i.e. the previous action
    was a Tier 4 probe). Classifies the world delta using classify_probe_outcome
    (library/probe_outcome_classifier.py) and applies the appropriate evidence
    update to the probed LibraryObject.

    Outcome → library update table:
        LEVER_LOCAL_SELF   — role = LEVER, causes += [self], probe_confirmation_count++, lever_locked = True
        LEVER_LOCAL_REMOTE — role = LEVER, causes += [self] + affected, affected.caused_by += [self],
                             probe_confirmation_count++, lever_locked = True
        LEVER_REMOTE_ONLY  — role = LEVER, causes += affected, affected.caused_by += [self],
                             probe_confirmation_count++, lever_locked = True
        NO_EFFECT          — inert_probe_count++; if >= 3 and not LEVER, nudge static_confidence
        AMBIGUOUS          — ambiguous_probe_count++

    Parameters
    ----------
    library : SemanticLibrary
        Mutated in place.
    context : VirelaiContext
        Provides last_probe_target_region_id and last_probe_target_cells.
    world_delta : WorldDelta
        Canonical per-frame delta (from context.world_delta). Contains world_cells
        (productive signal) and ego_cells (ego displacement stream).
    """
    # Read from canonical WorldDelta
    world_delta_cells: Set[Tuple[int, int]] = set(world_delta.world_cells)
    ego_displacement_cells: Set[Tuple[int, int]] = set(world_delta.ego_cells)

    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        _world_type = type(world_delta_cells).__name__
        _world_len = len(world_delta_cells) if hasattr(world_delta_cells, '__len__') else -1
        _ego_type = type(ego_displacement_cells).__name__
        _ego_len = len(ego_displacement_cells) if hasattr(ego_displacement_cells, '__len__') else -1
        _sample = list(world_delta_cells)[:3] if _world_len > 0 else []
        print(f"[WO02-DIAG2] PROBE-DELTA-IN world_type={_world_type} world_len={_world_len} ego_type={_ego_type} ego_len={_ego_len} world_sample={_sample}", file=sys.stderr, flush=True)
    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        print(f"[WO02-DIAG] PROBE-PROCESS action={library.header.actions_taken} probed_rid={context.last_probe_target_region_id} kind={context.last_probe_action_kind}", file=sys.stderr, flush=True)
    region_id = context.last_probe_target_region_id
    probed_cells = set(context.last_probe_target_cells) if context.last_probe_target_cells else set()

    # Graceful skip: region no longer in library
    if region_id not in library.objects:
        logger.warning(
            "[PROBE-OUTCOME] Probed region %d no longer in library — skipping outcome processing",
            region_id,
        )
        library.probe_event_log.append({
            "region_id": region_id,
            "outcome": "SKIPPED",
            "notes": "region not in library at outcome frame",
        })
        return

    outcome = classify_probe_outcome(
        probed_region_id=region_id,
        probed_region_cells=probed_cells,
        world_delta=world_delta,
        library_at_probe=library,
    )
    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        print(f"[WO02-DIAG] PROBE-OUTCOME action={library.header.actions_taken} rid={outcome.probed_region_id} outcome={outcome.outcome} self={outcome.self_cells_changed} other={outcome.other_reactive_cells_changed} affected={outcome.affected_region_ids}", file=sys.stderr, flush=True)

    obj = library.objects[region_id]

    # WO-EFFECT-LABEL: accumulate the consciously-disregarded live/HUD regions
    # (the counter tick, observed and labeled) onto the probed object — recorded
    # for the lever's full description, never attributed as a causal effect.
    if outcome.disregarded_region_ids:
        obj.disregarded_live_region_ids = tuple(sorted(
            set(obj.disregarded_live_region_ids)
            | set(outcome.disregarded_region_ids)
        ))

    # WO-OCD-05 — the current grid-state hash for THIS frame. Captured before the
    # outcome branches so Site 1 can compare it against the object's PRIOR
    # last_probe_state_hash before that field is overwritten below.
    _current_state_hash = ""
    if context is not None and context.state_tracker is not None:
        _current_state_hash = getattr(context.state_tracker, "_last_signature", "") or ""

    if outcome.outcome in ("LEVER_LOCAL_SELF", "LEVER_LOCAL_REMOTE", "LEVER_REMOTE_ONLY"):
        # WO-OCD-05 demotion-guard latch: a confirmed positive/causal outcome
        # latches ever_reactive permanently; a later null never clears it, so an
        # object that responded once is never pushed toward inert.
        obj.ever_reactive = True
        # Promote probed object to LEVER
        try:
            library.update_object_role(region_id, LibraryRole.LEVER, 1.0)
        except (ValueError, KeyError):
            pass  # Already LEVER or illegal transition — acceptable

        # Update causes list
        if outcome.outcome == "LEVER_LOCAL_SELF":
            # Self-cause only
            obj.causes = tuple(sorted(set(obj.causes) | {region_id}))

        elif outcome.outcome == "LEVER_LOCAL_REMOTE":
            # Self + affected
            obj.causes = tuple(sorted(set(obj.causes) | {region_id} | set(outcome.affected_region_ids)))
            for affected_id in outcome.affected_region_ids:
                affected_obj = library.objects.get(affected_id)
                if affected_obj is not None:
                    affected_obj.caused_by = tuple(sorted(set(affected_obj.caused_by) | {region_id}))

        elif outcome.outcome == "LEVER_REMOTE_ONLY":
            # Affected only (no self-cause)
            obj.causes = tuple(sorted(set(obj.causes) | set(outcome.affected_region_ids)))
            for affected_id in outcome.affected_region_ids:
                affected_obj = library.objects.get(affected_id)
                if affected_obj is not None:
                    affected_obj.caused_by = tuple(sorted(set(affected_obj.caused_by) | {region_id}))

        obj.probe_confirmation_count += 1
        obj.lever_locked = True

        # WO-D4: route the locality determination into the lever_locality field
        # (the CLICK writer). No counter touched; exactly one assignment
        # (floor-safe, §0.1). Per-world-type single-writer contract (CE ruling):
        # the CLICK writer asserts its lane at the point of write — a write from a
        # non-CLICK lane surfaces (logged) and is suppressed, never silent.
        #
        # WO_FC_LOCALITY_v3 (floor repair): locality derives from the LOCUS of
        # witnessed change, not its net magnitude. Self witnessed — by this
        # probe's outcome (self_cells_changed) OR the monotone is_active history —
        # → LOCAL; no self witness while driving change elsewhere → REMOTE. This
        # repairs the identity-preserving toggle (LEVER_REMOTE_ONLY yet is_active)
        # that the stale-cells probe read as REMOTE. No new vocabulary.
        _locality = ("LOCAL" if (outcome.self_cells_changed or _self_change_witnessed(obj))
                     else "REMOTE")
        if library.header.world_type == "CLICK":
            obj.lever_locality = _locality
        else:
            logger.warning(
                "lever_locality CLICK-lane write attempted under world_type=%s "
                "(region %d) — per-world-type contract violation, suppressed",
                library.header.world_type, region_id,
            )

        # WO-BLUEPRINT-07: BBA Layer One accumulator hook (secondary site).
        # WO-BLUEPRINT-08-TWO-THRESHOLD damping (Apex ratified May 22, 2026
        # per Section 2 v1.3 amendment): LEVER_LOCAL outcomes pass
        # confidence=0.7 rather than 1.0. The damping ensures a single
        # LEVER_LOCAL outcome crosses LEVER_LOCKED_THRESHOLD (0.6) but
        # does NOT cross LEVER_TYPED_THRESHOLD (0.95). The captain then
        # dispatches the cycle_probe to type the lever; cycle_probe
        # terminal commits at confidence=1.0 (un-damped) push the
        # log-score above the HIGH threshold and the walk advances.
        #
        # Math check: delta = log(0.7/0.3) ≈ 0.847. Starting from neutral
        # prior (log_score=0.0), post-increment log_score ≈ 0.847.
        # sigmoid(0.847) ≈ 0.700 — crosses 0.6 (LOW) ✓, below 0.95 (HIGH) ✓.
        #
        # Runs alongside the existing `lever_locked = True` write and
        # the `update_object_role(..., LEVER, 1.0)` write above.
        # Categorical substrate unchanged during Sub-Phase 3 coexistence.
        accumulate_role_evidence(obj, LibraryRole.LEVER, 0.7)

    elif outcome.outcome == "NO_EFFECT":
        # WO-OCD-05 Site 1 — a genuine null probe is NOT dispositive. This
        # interposes on the old premature-close (was: inert_probe_count>=3 →
        # confidence 0.90): accumulate inert-coverage over DISTINCT grid hashes
        # and cap confidence at 0.90, but NEVER set role=STATIC/INERT and never
        # demote an ever_reactive object. region-not-found is excluded upstream
        # (processor SKIPPED early-return, plus outcome.notes here defensively).
        if not getattr(outcome, "notes", ""):
            _record_inert_observation(obj, _current_state_hash)

    elif outcome.outcome == "AMBIGUOUS":
        obj.ambiguous_probe_count += 1

    # Update per-object investigation dossier summary (WO-OCD-01).
    # These fields index into library.probe_event_log for fast ranker/router
    # access. The library-wide log (below) remains the canonical event stream.
    # needs_reinvestigation is intentionally NOT written here — WO-OCD-05
    # (Evidence Asymmetry Engine) is its write site; declared in WO-OCD-01
    # so WO-OCD-02 (Ranker Upgrade) can read it without ordering dependency.
    obj.last_probe_frame = library.header.actions_taken
    obj.last_probe_outcome = outcome.outcome
    # WO-OCD-05: overwrite with THIS frame's hash — the same value Site 1
    # compared the prior hash against above (order matters: compare, then store).
    obj.last_probe_state_hash = _current_state_hash
    obj.probe_count += 1

    # Record in event log
    library.probe_event_log.append({
        "region_id": region_id,
        "outcome": outcome.outcome,
        "affected_region_ids": list(outcome.affected_region_ids),
        "notes": outcome.notes,
    })

    logger.debug(
        "[PROBE-OUTCOME] Region %d: %s (affected=%s)",
        region_id, outcome.outcome, outcome.affected_region_ids,
    )

    # Update sweep consecutive_inerts / reactive_found (WO-04).
    # Called after the outcome handler so the same ProbeOutcome informs both
    # attribution (above) and sweep termination tracking.
    if context is not None:
        update_sweep_from_outcome(
            context=context,
            probed_region_id=region_id,
            outcome=outcome,
        )
