"""
virelai_v4/library/priority_aggregation.py — cross-slot priority aggregation.

WO-LGTD-AGG (north-star §3.1, supersedes the closed LGTD-01 number). The
Library-resident PURE READ that orders the captain's open questions by
uncertainty-reduction value, replacing _form_b_walk's positional
sorted(region_id) order. Per-slot eligibility (axis/completion reads, the §4.3
foundation guard) is unchanged and lives with the caller; this module only
scores and orders the candidates the caller found eligible.

Inheritance: V3.5 falsification/probe_scorer.py uncertainty scorer —
role_weight x (1 - confidence) with UNKNOWN > INERT > REACTIVE > ACTIVE >
LIFE_COUNTER — ported WITH MODIFICATIONS onto the BBA axes as
role_weight x (1 - |sigmoid(axis) - threshold|). The walk integration is the
INVENT (the WO-PREFERENCE-GRADIENT read-shape the Blueprint names).

Extensibility: the score is a composable factor product (_role_weight x
_uncertainty). WO-PREFERENCE-GRADIENT later EXTENDS the factor set with the
deepening gradient (novel-state-seeking); add factors, do not rewrite.

Pure: no side effects, no library writes, deterministic (stable region_id
tiebreak). Imports: stdlib + contracts + library siblings only.
"""

from __future__ import annotations

from typing import List, Optional, Tuple, TYPE_CHECKING

from virelai_v4.contracts.attribute_type import AttributeType
from virelai_v4.library.constants import (
    LEVER_LOCKED_THRESHOLD,
    LEVER_TYPED_THRESHOLD,
)
from virelai_v4.library.library_roles import LibraryRole

if TYPE_CHECKING:
    from virelai_v4.library.semantic_library import LibraryObject

# V3.5 probe_scorer._CATEGORY_WEIGHT, mapped onto LibraryRole (INERT->STATIC,
# ACTIVE->LEVER; EGO/COUNTER are 0.0 — §4.3 excludes them upstream anyway).
ROLE_WEIGHTS = {
    LibraryRole.UNKNOWN: 10.0,
    LibraryRole.STATIC: 5.0,
    LibraryRole.REACTIVE: 1.5,
    LibraryRole.LEVER: 1.0,
    LibraryRole.TARGET: 1.0,
    LibraryRole.SIGNAL: 1.0,
    LibraryRole.EGO: 0.0,
    LibraryRole.COUNTER: 0.0,
}

# The axis threshold each open question is working toward.
_ATTR_THRESHOLD = {
    AttributeType.CYCLE_PERIOD_DETECTION_PROBE: LEVER_TYPED_THRESHOLD,  # typing -> 0.95
    AttributeType.FIRST_TOUCH_PROBE: LEVER_LOCKED_THRESHOLD,            # discovery -> 0.6
}


def score_open_question(slot: "LibraryObject", attribute_type: AttributeType) -> float:
    """role_weight x uncertainty for one open (slot x attribute).

    uncertainty = 1 - |sigmoid(lever axis) - threshold(attribute)| — highest
    when the belief sits farthest from resolving the attribute's question.
    Pure; deterministic."""
    weight = ROLE_WEIGHTS.get(slot.role, 1.0)
    threshold = _ATTR_THRESHOLD.get(attribute_type, LEVER_LOCKED_THRESHOLD)
    uncertainty = 1.0 - abs(slot.sigmoid_confidence("lever") - threshold)
    return weight * uncertainty


def order_candidates(
    candidates: List[Tuple["LibraryObject", AttributeType, int]],
) -> List[Tuple["LibraryObject", AttributeType, int]]:
    """Order eligible (slot, attribute, region_id) candidates by descending
    score, region_id-ascending tiebreak. Pure; stable; deterministic."""
    return sorted(
        candidates,
        key=lambda c: (-score_open_question(c[0], c[1]), c[2]),
    )


def top_candidate(
    candidates: List[Tuple["LibraryObject", AttributeType, int]],
) -> Optional[Tuple["LibraryObject", AttributeType, int]]:
    ordered = order_candidates(candidates)
    return ordered[0] if ordered else None
