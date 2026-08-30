"""
virelai_v4/library/attribution.py — Attribution column updater.

Sets is_attributed and attribution_evidence on every LibraryObject
based on current library state. Called once per frame after role
classification, before action selection.

Import sovereignty: imports from contracts/ and library/semantic_library.py only.
Tier target: file ≤ 120 lines (Green). Function body ≤ 50 lines (Green).

WO-01 LEVER-CATALOG
"""

from __future__ import annotations

import os

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary

# Minimum static confidence required for attribution as STATIC.
_STATIC_CONFIDENCE_THRESHOLD: float = 0.90


def _compute_attribution(obj: LibraryObject) -> tuple[bool, list[str]]:
    """Compute (is_attributed, attribution_evidence) for one object.

    Evaluation order (first match wins):
      1. EGO → attributed
      2. COUNTER → attributed
      3. LEVER → attributed (self-caused)
      4. REACTIVE with non-empty caused_by → attributed
      5. STATIC with confidence ≥ 0.90 → attributed (inert)
      6. Otherwise → unattributed
    """
    role = obj.role

    if role == LibraryRole.EGO:
        return True, ["role=EGO"]

    if role == LibraryRole.COUNTER:
        return True, ["role=COUNTER"]

    if role == LibraryRole.LEVER:
        causes = list(obj.causes)
        return True, [f"role=LEVER, causes={causes}"]

    if role == LibraryRole.REACTIVE and obj.caused_by:
        caused_by = list(obj.caused_by)
        obs_count = obj.causal_observation_count
        return True, [f"caused_by={caused_by}, obs_count={obs_count}"]

    if role == LibraryRole.STATIC and obj.confidence >= _STATIC_CONFIDENCE_THRESHOLD:
        return True, [f"static_conf={obj.confidence:.2f}"]

    return False, []


def update_attribution(library: SemanticLibrary) -> None:
    """Set is_attributed and attribution_evidence on every LibraryObject.

    Called once per frame after role classification, before action selection.
    Attribution is derived from library state at call time — never stale.

    Parameters
    ----------
    library : SemanticLibrary
        The current semantic library. Modified in place.
    """
    for obj in library.objects.values():
        attributed, evidence = _compute_attribution(obj)
        obj.is_attributed = attributed
        obj.attribution_evidence = evidence

    if os.environ.get("VIRELAI_WO02_DIAG") == "1":
        import sys
        for rid, obj in library.objects.items():
            if getattr(obj, 'role', None) is not None:
                _role_str = str(getattr(obj, 'role', 'UNKNOWN'))
                _conf = getattr(obj, 'confidence', 0.0)
                if 'STATIC' in _role_str and _conf >= 0.85:
                    print(f"[WO02-FIX-HYP] ATTR-CHECK rid={rid} role={_role_str} conf={_conf:.2f} attributed={obj.is_attributed}", file=sys.stderr, flush=True)
