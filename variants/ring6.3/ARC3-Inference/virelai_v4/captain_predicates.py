"""
Captain predicates — extracted from captain.py in WO-SOV-02 (May 26, 2026).

WO-SOV-03 (May 26, 2026): `captain_is_active` retired. Under single-actor
architecture (WO-SOV-01), the captain is the sole gameplay actor. The
Strangler-Fig coexistence predicate is vacuous and has been removed.

Only `captain_preconditions_met` remains as the Tier 1+2 GREEN gate.
It is re-exported from captain.py for backward compat.

Load-time circular dependency note:
    captain.py → captain_predicates.py  (safe)
    action_selector.py imports captain_preconditions_met via captain.py
"""
from __future__ import annotations

from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import SemanticLibrary
    from virelai_v4.targeting.assessor import TargetState


def captain_preconditions_met(target_state: Optional["TargetState"]) -> bool:
    """Returns True when Tiers 1 and 2 are GREEN.

    Preserved from V4 per WO-BLUEPRINT-06 §1 ("captain coexists with
    the legacy `_dispatch_action` routing tree through Sub-Phase 5").
    The Tier 1+2 GREEN gate is the V4 expression of "foundation must
    be established before object-list sub-library work" — Blueprint
    encodes the same logic as per-attribute prerequisite predicates
    on sub-library opening; this external gate retires in Sub-Phase 5
    when the prerequisite-predicate-on-foundation pattern lands.

    Architectural lesson (corrected, May 15, 2026 — pre-Blueprint):

        A tier's gate precondition is the set of tiers that supply the
        captain with the information it needs to INTERPRET its
        observations — not the set of tiers whose targets the captain
        is expected to ADDRESS. Gate preconditions are supply-side,
        not demand-side.

    For Tier 4 Coverage (the captain's Form B walk over the Object List):
      - Needs world type → Tier 1 precondition
      - Needs counter location (HUD mask) → Tier 2 precondition
      - Does NOT need pre-existing knowledge of which regions are
        reactive — that's what the walk DISCOVERS

    NOTE — name collision (now resolved): this reads
    target_state.tiers[i].status (the assessor's GREEN/AMBER/RED
    determination). The Migration Path G.1 Risk 1 name collision
    between target_state.current_tier (assessor's field, retained for
    field card display) and the captain's cursor field (renamed to
    captain_cursor, then retired in WO-BLUEPRINT-06 Step 6) is now
    resolved by the rename.

    Lazy import of TierStatus to keep this module sandbox-importable.
    """
    if target_state is None:
        return False
    from virelai_v4.targeting.assessor import TierStatus
    return all(
        target_state.tiers[i].status == TierStatus.GREEN
        for i in (0,)  # Tier 1 (world_type + action list) only.
        # WO-E04 (Campaign E, Director-authorized re-order): Tier 2 (life
        # counter) intentionally NOT required. The counter is never identified
        # pre-sweep (E02), which deadlocked the captain. Relaxing to Tier 1 lets
        # the first-touch walk run and leaves the counter to be deduced by the
        # walk. E03 (H1 clear): nothing inside the walk requires the counter
        # identified, so this single-site relax does not fan out.
    )


# WO-SOV-03 (May 26, 2026): captain_is_active removed.
# The Strangler-Fig routing predicate that guarded legacy emitters
# during coexistence is vacuous under single-actor architecture.
# Retirement closes FM 9 (Split Solver Sovereignty) → MITIGATED.
# Strangler-Fig Routing Predicate Tests (five cases) verified vacuity
# before deletion (test_captain_form_b.py::TestCaptainIsActiveRoutingPredicate).
