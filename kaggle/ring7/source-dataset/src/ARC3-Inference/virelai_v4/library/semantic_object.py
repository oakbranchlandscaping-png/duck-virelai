"""
virelai_v4/library/semantic_object.py — Semantic Inventory data structures.

Transplanted as-is from V3.5 observer/knife/semantic_object.py.
Imports adapted to V4 paths. No logic changes.

V3.5-era intermediate representation used by the role classifier and
downstream systems. Coexists with V4 LibraryObject until later campaigns
retire these types.

Import sovereignty: imports only stdlib.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple


# ── ClassEvidence ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ClassEvidence:
    """Evidence summary for a single class_id, consumed by confidence computation.

    Populated by inventory_builder from Tier 1 evidence sources available
    in the state dict at inventory build time. Passed to classify_role()
    and classify_state_role() to replace hardcoded confidence constants.
    """
    lever_confidence:       float = 0.0
    observation_depth:      int   = 0
    states_observed:        int   = 0
    contact_count:          int   = 0
    effect_pixel_count:     int   = 0
    regime_confidence:      float = 0.5
    all_profiled:           bool  = False
    cell_observation_depth: int   = 0
    cell_inert_depth:       int   = 0
    cell_toggle_confirmed:  bool  = False


# ── ObjectRole ───────────────────────────────────────────────────────────────

class ObjectRole(str, Enum):
    """Semantic role hypothesis for one pixel-class object.

    Assigned by role_classifier.classify_role() via an 11-rule priority
    chain. The string value equals the enum name for readable rendering.
    """
    AGENT            = "AGENT"
    CONTROL          = "CONTROL"
    EFFECT           = "EFFECT"
    LIFE_COUNTER     = "LIFE_COUNTER"
    OBSTACLE         = "OBSTACLE"
    INERT            = "INERT"
    SIGNAL_CANDIDATE = "SIGNAL_CANDIDATE"
    HUD_ACTIVE       = "HUD_ACTIVE"
    UNKNOWN          = "UNKNOWN"
    # Legacy values kept for enum compatibility — no longer assigned
    COUNTER     = "COUNTER"
    INDICATOR   = "INDICATOR"
    HUD_ELEMENT = "HUD_ELEMENT"
    FLOOR       = "FLOOR"
    FILLER      = "FILLER"
    HUD_OTHER   = "HUD_OTHER"


# ── SemanticObject ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SemanticObject:
    """One visible object: a Region annotated with a role hypothesis."""
    class_id:        int
    region_id:       int
    role:            ObjectRole
    role_confidence: float
    area:            int
    coverage:        float
    centroid:        Tuple[float, float]
    bbox:            Tuple[int, int, int, int]
    is_hud:          bool
    compactness:     float
    num_components:  int
    state_role:      str = "UNKNOWN"
    cells:           FrozenSet[Tuple[int, int]] = frozenset()
    layer:           str = "FOREGROUND"
    lc_rate:         Optional[float] = None
    lc_initial:      Optional[int]   = None
    lc_budget_est:   Optional[int]   = None


# ── ObjectFunction ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ObjectFunction:
    """One observed causal verb: subject acts on (optional) object."""
    subject_class_id:  int
    verb:              str
    object_class_id:   Optional[int]
    evidence_count:    int
    confidence:        float
    target_class_ids:  Tuple[int, ...] = ()
    affected_cells:    int = 0
    subject_region_id: Optional[int] = None
    direction:         Optional[str] = None
    effect_locality:   Optional[str] = None
    target_region_ids: Tuple[int, ...] = ()


# ── SemanticInventory ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SemanticInventory:
    """Full semantic inventory: all objects (nouns) and functions (verbs)."""
    cycle_id:   str
    grid_shape: Tuple[int, int]
    objects:    Tuple[SemanticObject, ...]
    functions:  Tuple[ObjectFunction, ...]

    def objects_by_role(self, role: ObjectRole) -> List[SemanticObject]:
        """All SemanticObjects with the given role."""
        return [o for o in self.objects if o.role == role]

    def role_map(self) -> Dict[int, ObjectRole]:
        """Map class_id → role. Highest-confidence wins on ties."""
        best: Dict[int, Tuple[float, ObjectRole]] = {}
        for obj in self.objects:
            prev = best.get(obj.class_id)
            if prev is None or obj.role_confidence > prev[0]:
                best[obj.class_id] = (obj.role_confidence, obj.role)
        return {cid: v[1] for cid, v in best.items()}

    def agent_coverage(self) -> float:
        """Fraction of grid area occupied by AGENT-role objects."""
        grid_area = self.grid_shape[0] * self.grid_shape[1]
        if grid_area == 0:
            return 0.0
        total = sum(o.area for o in self.objects if o.role == ObjectRole.AGENT)
        return total / grid_area


__all__ = [
    "ClassEvidence",
    "ObjectRole",
    "SemanticObject",
    "ObjectFunction",
    "SemanticInventory",
]
