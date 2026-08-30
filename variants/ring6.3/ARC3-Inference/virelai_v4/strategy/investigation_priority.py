"""
virelai_v4/strategy/investigation_priority.py — Unattributed object priority ranker.

Provides rank_unattributed_objects(), which returns all objects where
is_attributed is False, sorted by investigation priority descending.

Key design note from V3.5 Mining Inquiry:
    REACTIVE-unattributed objects are higher-priority lever candidates than
    STATIC-unattributed objects of the same size, because the oracle tells us
    which objects changed but not what caused them to change. A REACTIVE object
    that lacks a confirmed cause is a prime Tier 4 probe candidate.

Import sovereignty: imports from contracts/ and library/ only.
No imports from perception/ or targeting/.
Tier target: file ≤ 500 lines (Green). Function body ≤ 80 lines (Green).

WO-01 LEVER-CATALOG
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import LibraryObject, SemanticLibrary


# ---------------------------------------------------------------------------
# Factor helpers
# ---------------------------------------------------------------------------

def _size_factor(cell_count: int) -> float:
    """Prefer small objects — they are cheaper to probe and easier to attribute."""
    if cell_count <= 10:
        return 1.0
    if cell_count <= 100:
        return 0.7
    if cell_count <= 500:
        return 0.3
    return 0.1


def _rarity_factor(class_id: int, class_total_cells: Dict[int, int], total_grid_cells: int) -> float:
    """Prefer rare pixel classes — common classes are usually background."""
    if total_grid_cells <= 0:
        return 1.0
    class_cells = class_total_cells.get(class_id, 0)
    return 1.0 - (class_cells / total_grid_cells)


def _isolation_factor(obj: LibraryObject, library: SemanticLibrary) -> float:
    """Prefer isolated objects — adjacent large same-class objects dilute signal.

    Returns 0.7 if any bounding-box-adjacent object of a DIFFERENT class has
    ≥ 10× this object's cell count; 1.0 otherwise.
    """
    if not obj.cells:
        return 1.0

    min_r = min(r for r, _ in obj.cells)
    max_r = max(r for r, _ in obj.cells)
    min_c = min(c for _, c in obj.cells)
    max_c = max(c for _, c in obj.cells)

    # Expand bounding box by 1 cell in all directions
    adjacent_box = (min_r - 1, max_r + 1, min_c - 1, max_c + 1)
    threshold = obj.cell_count * 10

    for other in library.objects.values():
        if other.region_id == obj.region_id:
            continue
        if other.class_id == obj.class_id:
            continue
        if other.cell_count < threshold:
            continue
        # Check if other object overlaps the expanded bounding box
        for r, c in other.cells:
            if (adjacent_box[0] <= r <= adjacent_box[1] and
                    adjacent_box[2] <= c <= adjacent_box[3]):
                return 0.7
    return 1.0


def _reactivity_boost(obj: LibraryObject) -> float:
    """REACTIVE-unattributed objects get a 1.3× boost over STATIC objects.

    Core lesson from V3.5: observed activity means something is happening;
    the cause is just unconfirmed. These are prime Tier 4 probe candidates.
    """
    return 1.3 if obj.role == LibraryRole.REACTIVE else 1.0


# ---------------------------------------------------------------------------
# Public ranker
# ---------------------------------------------------------------------------

def rank_unattributed_objects(library: SemanticLibrary) -> List[Tuple[int, float]]:
    """Return (region_id, priority_score) tuples sorted by priority descending.

    Includes only objects where is_attributed is False.
    Excludes BACKGROUND-tagged objects (is_background == True).

    Priority formula:
        score = size_factor × rarity_factor × isolation_factor × reactivity_boost

    The reactivity_boost (1.3 for REACTIVE, 1.0 otherwise) ensures that
    unattributed REACTIVE objects rank above unattributed STATIC objects of
    equal size and rarity.
    """
    # Compute class totals and total grid cell count across all objects
    class_total: Dict[int, int] = {}
    total_grid_cells: int = 0
    for obj in library.objects.values():
        class_total[obj.class_id] = class_total.get(obj.class_id, 0) + obj.cell_count
        total_grid_cells += obj.cell_count

    candidates: List[Tuple[float, int]] = []
    for obj in library.objects.values():
        # Exclude attributed objects
        if obj.is_attributed:
            continue
        # Exclude background-tagged objects
        if getattr(obj, "is_background", False):
            continue

        sf  = _size_factor(obj.cell_count)
        rf  = _rarity_factor(obj.class_id, class_total, total_grid_cells)
        iso = _isolation_factor(obj, library)
        rb  = _reactivity_boost(obj)

        # WO-OCD-02 — investigation-status inputs (read WO-OCD-01 fields)
        # Both default to unit multipliers when fields are at sentinels,
        # so pre-WO-OCD-01 LibraryObjects produce bit-identical scores.
        recency_multiplier = 1.5 if obj.needs_reinvestigation else 1.0
        probe_penalty = 1.0 / (1.0 + 0.5 * obj.probe_count)

        score = sf * rf * iso * rb * recency_multiplier * probe_penalty
        candidates.append((score, obj.region_id))

    # Sort: highest score first; tiebreak by lowest region_id (determinism)
    candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    return [(rid, score) for score, rid in candidates]


# ----------------------------------------------------------------------
# Investigation predicates and ranking
# (migrated from action_selector.py in WO-CLEAN-06-PHASE-1A)
# ----------------------------------------------------------------------


def _is_uninvestigated(obj: "LibraryObject") -> bool:  # type: ignore[name-defined]
    """Return True if this object still needs investigation.

    Excluded: EGO, COUNTER (terminal roles), background-tagged objects,
    and objects already confirmed REACTIVE or STATIC at high confidence.
    """
    if obj.role in (LibraryRole.EGO, LibraryRole.COUNTER):
        return False
    if getattr(obj, "is_background", False):
        return False
    if obj.role in (LibraryRole.REACTIVE, LibraryRole.STATIC) and obj.confidence >= 0.70:
        return False
    return True


def _rank_investigation_targets(library: SemanticLibrary) -> List[int]:
    """Return region_ids sorted descending by investigation priority.

    Scoring (combined = cell_score * 0.7 + rarity_score * 0.3):
        cell_score   = 1.0 / obj.cell_count   — smaller objects score higher
        rarity_score = 1.0 / class_total_cells — rarer pixel classes score higher

    Filters to uninvestigated objects only (_is_uninvestigated predicate).
    Returns an empty list when no uninvestigated objects remain (Tier 3 complete).
    """
    # Compute total cells per class across all library objects
    class_total: Dict[int, int] = {}
    for obj in library.objects.values():
        class_total[obj.class_id] = class_total.get(obj.class_id, 0) + obj.cell_count

    candidates: List[Tuple[float, int]] = []
    for obj in library.objects.values():
        if not _is_uninvestigated(obj):
            continue
        cell_score   = 1.0 / max(obj.cell_count, 1)
        rarity_score = 1.0 / max(class_total.get(obj.class_id, 1), 1)
        # WO-OCD-02 — investigation-status inputs (read WO-OCD-01 fields)
        # Multipliers compose around the existing weighted-sum substructure,
        # preserving the DEBT-LC-03 formula difference vs Tier 4 ranker.
        # Both default to unit multipliers when fields are at sentinels.
        recency_multiplier = 1.5 if obj.needs_reinvestigation else 1.0
        probe_penalty = 1.0 / (1.0 + 0.5 * obj.probe_count)
        score = (cell_score * 0.7 + rarity_score * 0.3) * recency_multiplier * probe_penalty
        candidates.append((score, obj.region_id))

    # Primary sort: highest score first. Secondary tiebreak: lowest region_id first
    # (deterministic; preserves "smallest region_id" semantics when scores are equal).
    candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    return [rid for _, rid in candidates]


# ----------------------------------------------------------------------
# Tier 4 enforcement gate (WO-OCD-06)
# ----------------------------------------------------------------------


def investigation_coverage_complete(library: SemanticLibrary) -> bool:
    """Tier 4 enforcement gate per Object Investigation Doctrine Principle 1.

    Returns True if every object eligible for deliberate probing has
    ``probe_count >= 1``. This is the predicate that gates the cycle probe
    section in ``action_selector.select_action`` — cycle probe (Tier 5
    typing) fires only after Tier 4 closes through exhaustive investigation.

    Filter convention mirrors ``_is_uninvestigated`` (lines 151-163):
    excludes EGO, COUNTER, ``is_background == True``, and high-confidence
    ambient-classified REACTIVE/STATIC (confidence >= 0.70). Every object
    the Tier 3 ranker would not pick for deliberate probing is treated as
    "covered for gate purposes" regardless of probe_count — gate symmetry
    with the ranker prevents the deadlock empirically observed in
    WO-OCD-06's canary (FRICTION-OCD-03).

    WO-OCD-06 — Layer 4 Tier Enforcement Gate.
    WO-OCD-06.5 — Filter amendment for ranker-gate parity (FRICTION-OCD-03
    closure).
    """
    # WO-OCD-06 Step 5 patch — Mac pytest surfaced 5 failures in tests
    # exercising the library-is-None defensive path. The wrapped function
    # (_maybe_run_cycle_probe_section) handles this case at its own entry,
    # but the new outer gate runs before that defense. Returning False
    # keeps the gate closed when no library exists — coverage can't be
    # complete if there's no library — and lets the action selector fall
    # through to tier routing, which has its own None-handling at every
    # downstream callsite.
    if library is None:
        return False
    for obj in library.objects.values():
        if obj.role in (LibraryRole.EGO, LibraryRole.COUNTER):
            continue
        if getattr(obj, "is_background", False):
            continue
        # WO-OCD-06.5 — ambient-classified REACTIVE/STATIC objects at high
        # confidence are not eligible for deliberate probing (filtered out
        # by _is_uninvestigated at lines 151-163). Treat them as "covered
        # for gate purposes" regardless of probe_count. Without this
        # exclusion, the gate deadlocks when any such object reaches
        # conf >= 0.70 without being deliberately probed — empirically
        # observed on vc33 (FRICTION-OCD-03, WO-OCD-06 canary May 12).
        if obj.role in (LibraryRole.REACTIVE, LibraryRole.STATIC) and obj.confidence >= 0.70:
            continue
        if obj.probe_count == 0:
            return False
    return True
