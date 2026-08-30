"""virelai_v4/library/affordance_belief.py — Affordance Layer Entry A belief enums.

Per Library Blueprint Section 5.2.1 (The Affordance Layer — Entry A,
Declared Action Set). Filed under WO-LGTD-02 Phase 1 of the Library-Grounded
Tool Dispatch Campaign.

Declares:
  - DeclarativeBelief: platform-authoritative DECLARED/ABSENT state per frame.
  - OperationalBelief: four-state operational evidence enum.
  - ACTION_NAME_MAP: canonical int → name mapping for action IDs 0-7.
  - SEMANTIC_ROLE_MAP: canonical int → role mapping for action IDs 0-7.

Persistence taxonomy per Section 5.2.1 (and WO-LGTD-01a tier-name correction):
  declarative_belief: PERSIST_LIVES_AND_LEVELS — platform-authoritative,
    refreshes every frame from FrameData.available_actions.
  operational_belief: PERSIST_LIVES_RESET_LEVEL — per-level operational
    evidence. Reset at level advance to discharge GAP-7 region-regeneration
    hazard (closed by WO-LGTD-01).

The four-state OperationalBelief collapses ACKNOWLEDGED_INERT and
ZERO_DELTA_SILENT into INERT for v1.0 per WO Section 4.3.2 and Section 9
honest-framing deferral. The cosmetic-vs-causal distinction waits for v1.1
amendment.

Import sovereignty: stdlib only. No imports from other virelai_v4 modules.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict


# ---------------------------------------------------------------------------
# DeclarativeBelief — Entry A: declarative axis
# ---------------------------------------------------------------------------

class DeclarativeBelief(Enum):
    """Whether the platform declared this action on the current frame.

    DECLARED — action_id appears in FrameData.available_actions.
    ABSENT   — action_id does not appear in FrameData.available_actions.

    Per Section 5.2.1: declarative_belief refreshes every frame from
    FrameData. Platform-authoritative. The substrate writes; the captain
    reads.
    """
    DECLARED = "DECLARED"
    ABSENT = "ABSENT"


# ---------------------------------------------------------------------------
# OperationalBelief — Entry A: operational axis (v1.0 four-state collapse)
# ---------------------------------------------------------------------------

class OperationalBelief(Enum):
    """Whether attempting this action has produced effects across observations.

    UNTESTED                — no probe attempt has produced an outcome.
    INERT                   — attempts produced no delta. Collapses both
                              ACKNOWLEDGED_INERT and ZERO_DELTA_SILENT until
                              v1.1 amendment specifies the cosmetic-vs-causal
                              distinction (WO Section 9 deferral).
    EFFECTIVE_CONDITIONAL   — at least one attempt was effective; some prior
                              attempts were not. Effective contingent on
                              state.
    EFFECTIVE_UNCONDITIONAL — all attempts were effective. Action reliably
                              produces a delta when dispatched.

    Per Section 5.2.1 (operational axis) and WO-LGTD-01a Section 7.3
    (tier-name correction): operational_belief is per-level — survives
    life retry, resets at level advance.
    """
    UNTESTED = "UNTESTED"
    INERT = "INERT"
    EFFECTIVE_CONDITIONAL = "EFFECTIVE_CONDITIONAL"
    EFFECTIVE_UNCONDITIONAL = "EFFECTIVE_UNCONDITIONAL"


# ---------------------------------------------------------------------------
# Canonical action-id maps
# ---------------------------------------------------------------------------

ACTION_NAME_MAP: Dict[int, str] = {
    0: "RESET",
    1: "ACTION1",
    2: "ACTION2",
    3: "ACTION3",
    4: "ACTION4",
    5: "ACTION5",
    6: "ACTION6",
    7: "ACTION7",
}
"""Canonical mapping from integer action_id to its symbolic name.

Per Section 5.2.1: each SDKAction's `action_name` is populated at first
declaration from this map. Populated by the substrate in WO-LGTD-02 Phase
4; defaults to empty string in Phase 1 (the schema extension phase).
"""


SEMANTIC_ROLE_MAP: Dict[int, str] = {
    0: "reset",
    1: "directional-up",
    2: "directional-down",
    3: "directional-left",
    4: "directional-right",
    5: "interact",
    6: "coordinate",
    7: "undo",
}
"""Canonical mapping from integer action_id to its documented semantic role.

Per Section 5.2.1 and the ARC-AGI-3 platform documentation. Each SDKAction's
`semantic_role` is populated at first declaration from this map. Populated
by the substrate in WO-LGTD-02 Phase 4; defaults to empty string in Phase 1.
"""


__all__ = [
    "DeclarativeBelief",
    "OperationalBelief",
    "ACTION_NAME_MAP",
    "SEMANTIC_ROLE_MAP",
]
