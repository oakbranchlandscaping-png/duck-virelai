"""
virelai_v4/library/library_roles.py — LibraryRole enum and translation table.

Transplanted from V3.5 observer/knife/library_roles.py.
Imports adapted to V4 paths.

The SemanticLibrary uses a simplified 8-role vocabulary that consolidates
the V3.5 14-member ObjectRole enum into decision-relevant categories.

    LibraryRole     ObjectRole(s)
    ───────────     ─────────────
    EGO             AGENT
    LEVER           CONTROL  (Tier 4: causal direction confirmed)
    REACTIVE        (new — observed to change in world delta; no causal direction yet)
    TARGET          EFFECT
    SIGNAL          SIGNAL_CANDIDATE, HUD_ACTIVE, HUD_ELEMENT, HUD_OTHER, INDICATOR
    COUNTER         LIFE_COUNTER, COUNTER
    STATIC          OBSTACLE, INERT, FLOOR, FILLER
    UNKNOWN         UNKNOWN (and any unmapped value)

Import sovereignty: imports only stdlib.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional


class LibraryRole(str, Enum):
    """Simplified role vocabulary for the SemanticLibrary."""
    EGO      = "EGO"
    LEVER    = "LEVER"
    REACTIVE = "REACTIVE"
    TARGET   = "TARGET"
    SIGNAL   = "SIGNAL"
    COUNTER  = "COUNTER"
    STATIC   = "STATIC"
    # DD gap-2: INERT is the STATIC-branch role-null — "no role," held at static's
    # coverage-bounded skepticism, re-openable (revoked if the object later shows
    # efficacy, e.g. becomes a remote lever). Distinct from STATIC, which is the
    # Band-1 self-state tag, not a role. Landed here; the derived assignment lives
    # in diagnostics/store_a_readout._tag_then_role (the captain-store read).
    INERT    = "INERT"
    UNKNOWN  = "UNKNOWN"


class ObservationStatus(str, Enum):
    """Per-lever physics-observation status (WO-A2c-Core, NR-01 Layer 1).

    PORT-AS-IS in shape from V3.5's CONFIRMED/PARTIAL/FALSIFIED outcome
    triple (falsification/prediction_comparator.py): a three-state
    categorization with a first-class middle state. The vocabulary is
    V4 physics-observation, not causal-verdict.

    This is the substrate representation A.3's NO_AGREEMENT_TYPE_PENDING
    will read: the captain maps NOT_OBSERVED and OBSERVED_NON_RIGID to
    "I do not yet know" and gates tier-6 closure on OBSERVED_RIGID alone.

    Layer 2 (deferred to A.4) will add OBSERVED_BOUNDARY once NR-01 §4.3's
    boundary criterion is earned. It is deliberately ABSENT here — this WO
    binds to no unfiled contract content (§0 P0.4, Amendment Landing
    Status Pre-Check).
    """
    NOT_OBSERVED       = "NOT_OBSERVED"        # default; never pressed in any life
    OBSERVED_RIGID     = "OBSERVED_RIGID"      # rigid model fit (P4 conservation passed)
    OBSERVED_NON_RIGID = "OBSERVED_NON_RIGID"  # rigid model rejected — honest "my model failed here"

    @classmethod
    def from_object_role(cls, role: Optional[object]) -> "LibraryRole":
        """Translate an ObjectRole enum value to a LibraryRole.

        Accepts ObjectRole, string, or None. Never raises — unknown or
        unmapped input returns UNKNOWN.
        """
        if role is None:
            return cls.UNKNOWN
        key = str(role.value) if hasattr(role, "value") else str(role)
        return _TRANSLATION_TABLE.get(key, cls.UNKNOWN)


# Translation table: ObjectRole string values → LibraryRole
# Covers all 14 ObjectRole members including legacy values.
_TRANSLATION_TABLE = {
    "AGENT":            LibraryRole.EGO,
    "CONTROL":          LibraryRole.LEVER,
    "EFFECT":           LibraryRole.TARGET,
    "LIFE_COUNTER":     LibraryRole.COUNTER,
    "OBSTACLE":         LibraryRole.STATIC,
    "INERT":            LibraryRole.STATIC,
    "SIGNAL_CANDIDATE": LibraryRole.SIGNAL,
    "HUD_ACTIVE":       LibraryRole.SIGNAL,
    "UNKNOWN":          LibraryRole.UNKNOWN,
    # Legacy values (no longer assigned by classifier but kept for compat)
    "COUNTER":          LibraryRole.COUNTER,
    "INDICATOR":        LibraryRole.SIGNAL,
    "HUD_ELEMENT":      LibraryRole.SIGNAL,
    "FLOOR":            LibraryRole.STATIC,
    "FILLER":           LibraryRole.STATIC,
    "HUD_OTHER":        LibraryRole.SIGNAL,
}


__all__ = ["LibraryRole"]
