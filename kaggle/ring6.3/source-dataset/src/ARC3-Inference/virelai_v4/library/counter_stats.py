"""Counter stats updater for Cluster 5 (WO-MINE-CLEAN-05-PHASE-5).

This module owns the per-frame computation of LC rate and budget estimates
for confirmed COUNTER objects. Reads object pixel counts and actions
observed; writes lc_rate (pixels per action) and lc_budget_est (estimated
actions remaining before LC reaches zero).

Extracted from library_sync.py in Phase 5 of Campaign MINE Housekeeping —
the campaign closer for WO-05.

WO-XLEVEL-LOOP-01 adds the rate-confirmation write (LOOP-00 verdict (a)):
the live-grid drain measurement — delta-free, therefore HUD-mask-immune —
is the behavioral re-confirmation of counter-hood, the counter analogue of
the lever's cycle probe. On L2 the persisted HUD mask suppresses the
world-delta evidence Rule A needs (the LOOP-00 asymmetry), so the inherited
role=COUNTER (02b, the suspicion) is confirmed HERE from the measured drain,
raising obj.confidence past TIER2_COUNTER_CONFIDENCE so Tier 2 GREENs, the
captain turns on, and the lever loop runs on L2 as it does on L1.

F4+ note (stored-confidence-ratchet, §0(c) verified): the max() write is
evidence-gated and re-asserted each frame (raise only WHILE lc_rate < 0
with sufficient observations). lc_rate is a cumulative average anchored at
the spawn count, so a draining counter stays negative within the level; at
a new life current==initial drives the rate to 0 and the gate simply stops
asserting (no revoke needed — role/confidence persist across lives by
Groundhog-Day design); at the LEVEL boundary the 02a rebuild zeroes
confidence, so the ratchet's scope is bounded to one level and the §12
re-confirmation stays structural. On L1 the write is a no-op (Rule A has
already set 0.70-0.90 before counter_stats sees a COUNTER role).

Sovereignty: stdlib + library/. No numpy, no contracts/, no perception/,
no targeting/, no strategy/, no memory/.

Public API:
- _update_counter_stats(library) -> None
"""

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import SemanticLibrary


# ----------------------------------------------------------------------
# WO-XLEVEL-LOOP-01 — rate-confirmation thresholds (LOOP-00 verdict (a)).
# ----------------------------------------------------------------------

# Sustained-drain evidence gate: at least this many observed actions with a
# negative cumulative rate before the measurement confirms counter-hood.
# Mirrors Rule A's observation-depth guard (_COUNTER_MIN_OBSERVATIONS = 5).
RATE_CONFIRM_MIN_OBSERVATIONS: int = 5

# Confirmation confidence: clears TIER2_COUNTER_CONFIDENCE (0.6 — the Tier-2
# GREEN read, assessor.py:142-147) and engages the confirmed-COUNTER
# terminal-skip (classification_pass.py:140, >= 0.70) at exactly the
# designed "confirmed COUNTER" semantics. Matches Rule A's confidence floor.
RATE_CONFIRM_CONFIDENCE: float = 0.70


# ----------------------------------------------------------------------
# Counter stats update (WO-C5-02)
# ----------------------------------------------------------------------

def _update_counter_stats(library: SemanticLibrary) -> None:
    """Compute lc_rate and lc_budget_est for all confirmed COUNTER objects.

    Called after _classify_objects so newly promoted COUNTER objects are covered.
    Only runs when initial_cell_count > 0 and actions_observed > 0 (avoids
    division by zero and spurious rates on freshly classified objects).

    lc_rate:       pixels changed per action (negative = draining, positive = filling).
    lc_budget_est: estimated actions remaining before LC reaches zero.
                   Set to -1 when rate >= 0 (filling/static) or when current count = 0.

    WO-XLEVEL-LOOP-01: a sustained measured drain (lc_rate < 0 over >=
    RATE_CONFIRM_MIN_OBSERVATIONS actions) confirms counter-hood —
    obj.confidence ratchets to RATE_CONFIRM_CONFIDENCE. One write, no other
    field; evidence-gated, re-asserted each frame. See module docstring.
    """
    for obj in library.objects.values():
        if obj.role != LibraryRole.COUNTER:
            continue
        if obj.initial_cell_count <= 0 or obj.actions_observed <= 0:
            continue
        obj.lc_rate = (obj.current_cell_count - obj.initial_cell_count) / obj.actions_observed
        if obj.lc_rate < 0.0 and obj.current_cell_count > 0:
            obj.lc_budget_est = int(obj.current_cell_count / abs(obj.lc_rate))
        else:
            obj.lc_budget_est = -1
        # WO-XLEVEL-LOOP-01 — rate -> confidence confirmation (the one write).
        if (obj.lc_rate < 0.0
                and obj.actions_observed >= RATE_CONFIRM_MIN_OBSERVATIONS):
            obj.confidence = max(obj.confidence, RATE_CONFIRM_CONFIDENCE)
