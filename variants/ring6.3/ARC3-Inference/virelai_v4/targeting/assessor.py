"""
virelai_v4/targeting/assessor.py — Six-Tier Targeting Assessor.

Pure function: assess_target_state(library) → TargetState.
Zero side effects. Zero mutations. SemanticLibrary is the sole input.

The assessor grades the library's current belief state against the six-tier
priority chain and returns a frozen snapshot describing what is known, what
is unresolved, and which tier is currently the active focus.

Six tiers:
    1  WORLD_TYPE_EGO   — World type classification and ego identification
    2  LIFE_COUNTER     — Life counter / budget meter identification
    3  REACTIVE_CELLS     — Lever / active cell discovery
    4  LEVERS     — Lever behavioral type (TOGGLE / CYCLE / DIRECTIONAL)
    5  LEVER_TYPING   — Target / reactive cell identification
    6  CAUSAL_LINKS     — Lever → target causal link mapping

Tier 4 reads ``LibraryObject.lever_mechanism`` (Phase 3 cycle probe verdict)
per WO-CAMPAIGN3-PHASE3-04 post-canary surgical update (May 5, 2026); GREEN
when all LEVER objects are typed; AMBER when typing in progress or pending.

Tier 6 remains a placeholder: causal link mapping infrastructure arrives in
Phase 4 Combination Search.

Import sovereignty: imports from library/ (read-only) and stdlib only.
No imports from perception/, strategy/, memory/, or contracts/.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.nested_read import derived_role
from virelai_v4.library.semantic_library import SemanticLibrary

# WO_CAPTAIN_READS_TAPE D4: the three axis-backed CHILD roles the census proved
# one-sided-write-prone (EGO/COUNTER/LEVER) are graded off the DERIVED read
# (`derived_role`), not the Store-B categorical — so a categorical written
# without its axis, or one whose axis was wiped, no longer moves a tier. The
# STATIC/REACTIVE tag membership and the UNKNOWN/absence reads stay on the
# recorded fields: they are the Band-1 tag and the §4 vocabulary residue, not
# convergeable child roles, and routing them through the derived read would
# change tier semantics (a fence, not a swap).
_EGO = LibraryRole.EGO.value
_COUNTER = LibraryRole.COUNTER.value
_LEVER = LibraryRole.LEVER.value


# ---------------------------------------------------------------------------
# Calibration constants — tuned against live games
# ---------------------------------------------------------------------------

TIER1_EGO_CONFIDENCE:          float = 0.65
TIER2_COUNTER_CONFIDENCE:      float = 0.6
TIER2_CANDIDATE_RATIO:         float = 0.60  # WO-C5-02: action_independence_ratio AMBER threshold
TIER3_LEVER_CONFIDENCE:        float = 0.5
TIER3_UNKNOWN_RATIO_THRESHOLD: float = 0.3
TIER5_TARGET_CONFIDENCE:       float = 0.5

# World types that do not require an embodied ego (God Mode)
_NO_EGO_WORLD_TYPES = frozenset({"CLICK", "GLOBAL"})

# Fraction of total cells below which an unknown object is a counter candidate (legacy fallback)
_COUNTER_CANDIDATE_FRACTION = 0.05


# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

class TierStatus(Enum):
    RED   = "RED"
    AMBER = "AMBER"
    GREEN = "GREEN"


@dataclass(frozen=True)
class TierAssessment:
    tier:         int         # 1–6
    name:         str         # e.g. "WORLD_TYPE_EGO"
    status:       TierStatus  # RED / AMBER / GREEN
    gap:          str         # Human-readable description of what is missing
    confidence:   float       # 0.0–1.0 aggregate confidence for this tier
    object_count: int         # Objects relevant to this tier


@dataclass(frozen=True)
class TargetState:
    tiers:          tuple       # All 6 TierAssessments, always present
    current_tier:   int         # Lowest-numbered non-GREEN tier (0 if all GREEN)
    current_focus:  str         # Human-readable focus description
    overall_status: TierStatus  # Worst status across all tiers
    ready_to_act:   bool        # True only when all 6 tiers are GREEN


# ---------------------------------------------------------------------------
# Tier 1 — World Type + Ego
# ---------------------------------------------------------------------------

def _assess_world_type_ego(library: SemanticLibrary) -> TierAssessment:
    """Tier 1: world type classification and ego identification."""
    world_type = library.header.world_type
    egos = [o for o in library.objects.values() if derived_role(o) == _EGO]
    has_live_action = any(
        sa.status == "LIVE" for sa in library.sdk_actions.values()
    )

    ego_confirmed = any(e.confidence >= TIER1_EGO_CONFIDENCE for e in egos)
    no_ego_needed = world_type in _NO_EGO_WORLD_TYPES

    # GREEN: world type known AND ego confirmed (or not needed)
    if world_type != "UNKNOWN" and (ego_confirmed or no_ego_needed):
        return TierAssessment(
            tier=1, name="WORLD_TYPE_EGO", status=TierStatus.GREEN,
            gap="", confidence=1.0, object_count=len(egos),
        )

    # RED: world type unknown, no ego candidates, no live action evidence
    if world_type == "UNKNOWN" and not egos and not has_live_action:
        return TierAssessment(
            tier=1, name="WORLD_TYPE_EGO", status=TierStatus.RED,
            gap="No world type established", confidence=0.0, object_count=0,
        )

    # AMBER: partial evidence
    if egos:
        conf = sum(e.confidence for e in egos) / len(egos)
        gap = (
            "Ego candidate exists but unconfirmed"
            if world_type == "UNKNOWN"
            else "World type confirmed, no confident ego identified"
        )
    else:
        conf = 0.3   # live action evidence only
        gap = "No ego identified" if world_type != "UNKNOWN" else "No world type established"

    return TierAssessment(
        tier=1, name="WORLD_TYPE_EGO", status=TierStatus.AMBER,
        gap=gap, confidence=conf, object_count=len(egos),
    )


# ---------------------------------------------------------------------------
# Tier 2 — Life Counter
# ---------------------------------------------------------------------------

def _assess_life_counter(library: SemanticLibrary) -> TierAssessment:
    """Tier 2: life counter / budget meter identification."""
    counters = [o for o in library.objects.values() if derived_role(o) == _COUNTER]

    if counters:
        best_conf = max(c.confidence for c in counters)
        if best_conf >= TIER2_COUNTER_CONFIDENCE:
            return TierAssessment(
                tier=2, name="LIFE_COUNTER", status=TierStatus.GREEN,
                gap="", confidence=best_conf, object_count=len(counters),
            )
        # Counter exists but confidence too low
        return TierAssessment(
            tier=2, name="LIFE_COUNTER", status=TierStatus.AMBER,
            gap="Counter candidate at low confidence",
            confidence=best_conf, object_count=len(counters),
        )

    # WO-C5-02: Action independence ratio — primary AMBER signal.
    # Objects with ratio >= 0.60 change on most actions → strong LC candidate.
    # Requires at least 5 observations (same guard as the classifier).
    # Excludes confirmed EGO objects (EGO also changes often but is not an LC).
    ratio_candidates = [
        o for o in library.objects.values()
        if derived_role(o) not in (_EGO, _COUNTER)
        and o.actions_observed >= 5
        and o.action_independence_ratio >= TIER2_CANDIDATE_RATIO
    ]
    if ratio_candidates:
        best_ratio = max(o.action_independence_ratio for o in ratio_candidates)
        return TierAssessment(
            tier=2, name="LIFE_COUNTER", status=TierStatus.AMBER,
            gap="Counter candidate detected (high action independence ratio)",
            confidence=best_ratio, object_count=len(ratio_candidates),
        )

    # Legacy fallback: small UNKNOWN objects that changed are counter candidates.
    # Fires only when the ratio signal is not yet available (< 5 observations).
    grid_cells = library.header.grid_rows * library.header.grid_cols
    threshold = max(1, int(_COUNTER_CANDIDATE_FRACTION * grid_cells))
    legacy_candidates = [
        o for o in library.objects.values()
        if o.role == LibraryRole.UNKNOWN
        and o.change_count > 0
        and o.cell_count <= threshold
    ]
    if legacy_candidates:
        return TierAssessment(
            tier=2, name="LIFE_COUNTER", status=TierStatus.AMBER,
            gap="Counter candidate at low confidence",
            confidence=0.0, object_count=0,
        )

    return TierAssessment(
        tier=2, name="LIFE_COUNTER", status=TierStatus.RED,
        gap="No life counter identified", confidence=0.0, object_count=0,
    )


# ---------------------------------------------------------------------------
# Tier 3 — Active Cells / Levers
# ---------------------------------------------------------------------------

def _assess_active_cells(library: SemanticLibrary) -> TierAssessment:
    """Tier 3: reactive / active cell discovery (WO-RM-01/WO-RM-04).

    REACTIVE objects are objects observed to change in the world delta.
    STATIC objects are confirmed non-changing arena objects.
    LEVER is reserved for Tier 4 when causal direction is established.

    GREEN: all arena objects (non-EGO, non-COUNTER, non-BACKGROUND) classified
           as REACTIVE or STATIC, each with confidence >= 0.70.
    AMBER: all arena objects are REACTIVE, STATIC, or UNKNOWN, with <= 2 UNKNOWN
           remaining AND at least one high-confidence REACTIVE exists.
    RED:   no REACTIVE objects discovered.
    """
    reactives = [o for o in library.objects.values() if o.role == LibraryRole.REACTIVE]

    if not reactives:
        return TierAssessment(
            tier=3, name="REACTIVE_CELLS", status=TierStatus.RED,
            gap="No reactive objects discovered", confidence=0.0, object_count=0,
        )

    avg_conf = sum(r.confidence for r in reactives) / len(reactives)

    avg_conf  = sum(r.confidence for r in reactives) / len(reactives)
    high_conf = any(r.confidence >= TIER3_LEVER_CONFIDENCE for r in reactives)

    # Arena objects: non-EGO, non-COUNTER, non-BACKGROUND (WO-RM-04).
    # Roles that count as "classified" for Tier 3 — LEVER/TARGET/SIGNAL are higher-
    # resolution refinements of REACTIVE, not unknowns.
    _classified = frozenset({
        LibraryRole.REACTIVE, LibraryRole.STATIC,
        LibraryRole.LEVER, LibraryRole.TARGET, LibraryRole.SIGNAL,
    })
    arena_objects = [
        o for o in library.objects.values()
        if derived_role(o) not in (_EGO, _COUNTER)
        and not o.is_background
    ]

    # GREEN: every arena object is classified (no UNKNOWNs) AND high-confidence
    # REACTIVE anchor exists.
    if arena_objects and high_conf and all(
        o.role in _classified for o in arena_objects
    ):
        return TierAssessment(
            tier=3, name="REACTIVE_CELLS", status=TierStatus.GREEN,
            gap="", confidence=avg_conf, object_count=len(reactives),
        )

    # AMBER: arena mix is only classified + UNKNOWN with few UNKNOWNs left
    unknown_arena = [o for o in arena_objects if o.role == LibraryRole.UNKNOWN]
    if (
        high_conf
        and all(o.role in _classified | {LibraryRole.UNKNOWN} for o in arena_objects)
        and len(unknown_arena) <= 2
    ):
        gap = (
            f"{len(unknown_arena)} arena object(s) still UNKNOWN"
            if unknown_arena
            else "Reactive objects found — confidence below threshold"
        )
        return TierAssessment(
            tier=3, name="REACTIVE_CELLS", status=TierStatus.AMBER,
            gap=gap, confidence=avg_conf, object_count=len(reactives),
        )

    return TierAssessment(
        tier=3, name="REACTIVE_CELLS", status=TierStatus.AMBER,
        gap="Reactive objects found but many objects unclassified",
        confidence=avg_conf, object_count=len(reactives),
    )


# ---------------------------------------------------------------------------
# Tier 4 — Lever Behavioral Typing
# ---------------------------------------------------------------------------

def _assess_lever_typing(library: SemanticLibrary) -> TierAssessment:
    """Tier 4: lever behavioral type (TOGGLE/CYCLE/DIRECTIONAL/SATURATED/UNKNOWN).

    Reads Phase 3 cycle probe verdict from ``LibraryObject.lever_mechanism``.
    Wired at WO-CAMPAIGN3-PHASE3-04 post-canary surgical update (May 5, 2026)
    per investigation §6 Recommendation 1; closes FINDING-PHASE3-DIRECTIVE-
    PLACEHOLDER (assessor was unaware of Phase 3 substrate).

    Tier verdict (WO-E7: "characterized" = type-known OR condition-known):
      - No LEVER objects → RED ("No levers to type")
      - All LEVER objects characterized (lever_mechanism not None OR saturated) → GREEN
      - Mixed verdicts (some characterized; some pending) → AMBER ("typing in progress")
      - All LEVER objects uncharacterized → AMBER ("typing pending")
    """
    levers = [o for o in library.objects.values() if derived_role(o) == _LEVER]

    if not levers:
        return TierAssessment(
            tier=4, name="LEVERS", status=TierStatus.RED,
            gap="No levers to type", confidence=0.0, object_count=0,
        )

    # WO-E7 (type/condition de-collapse): a saturated lever's type field no
    # longer reads SATURATED (saturation is on obj.saturated). It is still
    # CHARACTERIZED — its condition is known — so it counts toward Tier-4 via
    # the condition axis, not a spurious type. Without this OR, de-collapsing
    # the producer would flip a saturated lever typed->untyped and regress
    # Tier-4 GREEN->AMBER (the §0.3 guard).
    typed = [o for o in levers
             if o.lever_mechanism is not None or getattr(o, "saturated", False)]
    n_typed = len(typed)
    n_total = len(levers)

    if n_typed == n_total:
        return TierAssessment(
            tier=4, name="LEVERS", status=TierStatus.GREEN,
            gap=f"Lever typing active; {n_typed}/{n_total} levers typed",
            confidence=1.0, object_count=n_total,
        )

    if n_typed > 0:
        return TierAssessment(
            tier=4, name="LEVERS", status=TierStatus.AMBER,
            gap=f"Lever typing in progress; {n_typed}/{n_total} levers typed",
            confidence=n_typed / n_total, object_count=n_total,
        )

    # n_typed == 0: cycle probe should be firing
    return TierAssessment(
        tier=4, name="LEVERS", status=TierStatus.AMBER,
        gap=f"Lever typing pending; 0/{n_total} levers typed (cycle probe should be active)",
        confidence=0.0, object_count=n_total,
    )


# ---------------------------------------------------------------------------
# Tier 5 — Reactive Cells
# ---------------------------------------------------------------------------

def _saturated_lever_observation_gap(library: SemanticLibrary) -> Optional[str]:
    """Observation-status summary across saturated levers, for the tier-5
    ``gap`` DESCRIPTION only (WO-A.3-TIER5-GAP-ENRICHMENT, NR-01 A.3).

    Returns None when no saturated levers exist (caller keeps its default
    gap). Reads ``observation_status`` (substrate-written by A.2c-Core).

    Action-neutral by construction: ``gap`` flows only into the descriptive
    ``focus`` / ``current_focus`` fields (rendered + logged), never into the
    routing decision, which is computed from ``status`` / ``current_tier`` /
    ``ready_to_act`` (verified §0 P0.8). This helper does NOT read or modify
    any ``status``. Saturation is detected via the ``saturated`` bool or the
    ``lever_mechanism`` field's name — WITHOUT importing the LeverMechanism
    enum (assessor import sovereignty: library/ + stdlib only, no contracts/).
    """
    def _is_saturated(o) -> bool:
        if getattr(o, "saturated", False):
            return True
        mech = getattr(o, "lever_mechanism", None)
        return mech is not None and getattr(mech, "name", "") == "SATURATED"

    levers = [o for o in library.objects.values()
              if derived_role(o) == _LEVER and _is_saturated(o)]
    if not levers:
        return None

    counts = {"OBSERVED_RIGID": 0, "NOT_OBSERVED": 0, "OBSERVED_NON_RIGID": 0}
    for lev in levers:
        name = getattr(lev.observation_status, "name", "NOT_OBSERVED")
        counts[name] = counts.get(name, 0) + 1
    total = len(levers)
    return (
        f"{counts['OBSERVED_RIGID']}/{total} saturated levers OBSERVED_RIGID "
        f"(verdict pending §4.3); {counts['NOT_OBSERVED']}/{total} NOT_OBSERVED; "
        f"{counts['OBSERVED_NON_RIGID']}/{total} OBSERVED_NON_RIGID"
    )


def _assess_reactive_cells(library: SemanticLibrary) -> TierAssessment:
    """Tier 5: target / reactive cell identification.

    Reads ``LibraryRole.REACTIVE`` (Phase 2 substrate-honest field) in
    addition to ``LibraryRole.TARGET`` (legacy causal-link role). Updated
    at WO-CAMPAIGN3-PHASE3-04 post-canary surgical update (May 5, 2026)
    per investigation §6 Recommendation 1; closes FINDING-DEC-23
    (assessor used pre-amendment naming, surfaced "No reactive cells
    identified" despite REACTIVE objects existing in the library).

    Tier verdict ordering:
      - No REACTIVE, TARGET, or LEVER objects → RED ("No reactive cells identified")
      - TARGET objects with high confidence + LEVER objects → GREEN (causal link substrate)
      - REACTIVE or TARGET objects exist but no causal link substrate → AMBER
    """
    reactive = [o for o in library.objects.values() if o.role == LibraryRole.REACTIVE]
    targets  = [o for o in library.objects.values() if o.role == LibraryRole.TARGET]
    levers   = [o for o in library.objects.values() if derived_role(o) == _LEVER]

    if not reactive and not targets and not levers:
        return TierAssessment(
            tier=5, name="LEVER_TYPING", status=TierStatus.RED,
            gap="No reactive cells identified", confidence=0.0, object_count=0,
        )

    avg_conf = sum(t.confidence for t in targets) / len(targets) if targets else 0.0

    if targets and any(t.confidence >= TIER5_TARGET_CONFIDENCE for t in targets) and levers:
        return TierAssessment(
            tier=5, name="LEVER_TYPING", status=TierStatus.GREEN,
            gap="", confidence=avg_conf, object_count=len(targets),
        )

    if reactive and not targets:
        # Phase 2 contact reactivity surfaced REACTIVE objects; causal link
        # substrate (TARGET role) not yet wired (Phase 4 territory).
        avg_reactive_conf = sum(o.confidence for o in reactive) / len(reactive)
        return TierAssessment(
            tier=5, name="LEVER_TYPING", status=TierStatus.AMBER,
            gap=(_saturated_lever_observation_gap(library)
                 or f"{len(reactive)} REACTIVE cells identified; "
                    f"causal link substrate pending"),
            confidence=avg_reactive_conf, object_count=len(reactive),
        )

    gap = _saturated_lever_observation_gap(library) or (
        "Reactive cells at low confidence" if targets
        else "No reactive cells identified"
    )
    return TierAssessment(
        tier=5, name="LEVER_TYPING", status=TierStatus.AMBER,
        gap=gap, confidence=avg_conf, object_count=len(targets),
    )


# ---------------------------------------------------------------------------
# Tier 6 — Causal Links (placeholder)
# ---------------------------------------------------------------------------

def _assess_causal_links(library: SemanticLibrary) -> TierAssessment:
    """Tier 6: lever → target causal link mapping.

    Placeholder — causal link builder arrives in Campaign 6.
    Reports AMBER when preconditions met (LEVER + TARGET), RED otherwise.
    """
    levers  = [o for o in library.objects.values() if derived_role(o) == _LEVER]
    targets = [o for o in library.objects.values() if o.role == LibraryRole.TARGET]

    if not levers or not targets:
        return TierAssessment(
            tier=6, name="CAUSAL_LINKS", status=TierStatus.RED,
            gap="Insufficient objects for causal mapping",
            confidence=0.0, object_count=0,
        )

    return TierAssessment(
        tier=6, name="CAUSAL_LINKS", status=TierStatus.AMBER,
        gap="Causal link mapping not yet implemented",
        confidence=0.0, object_count=0,
    )


# ---------------------------------------------------------------------------
# Public API — pure assessment function
# ---------------------------------------------------------------------------

def assess_target_state(library: SemanticLibrary) -> TargetState:
    """Grade the library's belief state against the six-tier priority chain.

    Pure function: reads SemanticLibrary, returns frozen TargetState.
    Zero side effects. Zero mutations.
    """
    tier1 = _assess_world_type_ego(library)
    tier2 = _assess_life_counter(library)
    tier3 = _assess_active_cells(library)
    tier4 = _assess_lever_typing(library)
    tier5 = _assess_reactive_cells(library)
    tier6 = _assess_causal_links(library)

    tiers: Tuple[TierAssessment, ...] = (tier1, tier2, tier3, tier4, tier5, tier6)

    # current_tier: lowest-numbered non-GREEN tier (0 if all GREEN)
    current_tier = 0
    for t in tiers:
        if t.status != TierStatus.GREEN:
            current_tier = t.tier
            break

    current_focus = (
        "All tiers GREEN — ready to act"
        if current_tier == 0
        else tiers[current_tier - 1].gap
    )

    if any(t.status == TierStatus.RED for t in tiers):
        overall_status = TierStatus.RED
    elif any(t.status == TierStatus.AMBER for t in tiers):
        overall_status = TierStatus.AMBER
    else:
        overall_status = TierStatus.GREEN

    ready_to_act = all(t.status == TierStatus.GREEN for t in tiers)

    return TargetState(
        tiers=tiers,
        current_tier=current_tier,
        current_focus=current_focus,
        overall_status=overall_status,
        ready_to_act=ready_to_act,
    )


__all__ = [
    "TierStatus",
    "TierAssessment",
    "TargetState",
    "assess_target_state",
    "TIER1_EGO_CONFIDENCE",
    "TIER2_COUNTER_CONFIDENCE",
    "TIER2_CANDIDATE_RATIO",
    "TIER3_LEVER_CONFIDENCE",
    "TIER3_UNKNOWN_RATIO_THRESHOLD",
    "TIER5_TARGET_CONFIDENCE",
]
