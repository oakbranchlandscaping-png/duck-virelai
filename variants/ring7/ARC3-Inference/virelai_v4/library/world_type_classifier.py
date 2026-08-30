"""
virelai_v4/library/world_type_classifier.py — World type classification.

Reads accumulated action evidence from the SemanticLibrary and classifies
the world type (NAV / CLICK / GLOBAL) from three evidence channels:

  Channel 1: Action availability pattern
             Which SDK action IDs exist in the library?
  Channel 2: Directional consistency (NAV confirmation)
             Do ACTION1-4 produce consistent deltas across all four?
  Channel 3: ACTION6 exclusivity (CLICK confirmation)
             Is ACTION6 LIVE while directionals are absent or all NOOP?

Returns a (world_type, ego_mode, confidence) tuple. The caller writes the
result into library.header via the confidence ratchet in library_sync.

Import sovereignty: library/ and stdlib only.
No imports from contracts/, targeting/, perception/, memory/, strategy/.
Pure function: reads library state, returns tuple, mutates nothing.
"""

from __future__ import annotations

from virelai_v4.library.semantic_library import SemanticLibrary

# ---------------------------------------------------------------------------
# Calibration constants
# ---------------------------------------------------------------------------

_DIRECTIONAL_IDS = frozenset({1, 2, 3, 4})

# Minimum total test_count across all SDK actions before classification runs.
# Below this threshold the evidence is too sparse to commit.
_MIN_TOTAL_TESTS: int = 3

# Minimum confidence required to return a classification rather than UNKNOWN.
_CONFIDENCE_THRESHOLD: float = 0.4

# NAV directional consistency: max_delta / min_delta must not exceed this.
_CONSISTENCY_RATIO: float = 2.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_world_type(
    library: SemanticLibrary,
) -> tuple[str, str, float]:
    """Classify world type from accumulated action evidence.

    Returns (world_type, ego_mode, confidence) where:
        world_type : "NAV", "CLICK", "GLOBAL", or "UNKNOWN"
        ego_mode   : "EMBODIED", "GOD_MODE", "GLOBAL", or "UNKNOWN"
        confidence : float 0.0–1.0

    The caller (library_sync) applies the confidence ratchet and writes the
    result into library.header. This function is read-only.
    """
    sdk = library.sdk_actions

    # Minimum evidence gate: wait for at least 3 total action tests
    total_tests = sum(s.test_count for s in sdk.values())
    if total_tests < _MIN_TOTAL_TESTS:
        return ("UNKNOWN", "UNKNOWN", 0.0)

    available_ids = set(sdk.keys())
    dir_ids  = available_ids & _DIRECTIONAL_IDS
    has_a5   = 5 in available_ids
    has_a6   = 6 in available_ids
    a6_entry = sdk.get(6)
    a6_tested = has_a6 and a6_entry is not None and a6_entry.test_count > 0

    nav_conf    = 0.0
    click_conf  = 0.0
    global_conf = 0.0

    # --- Channel 1: Action availability pattern ---
    if dir_ids and not has_a6:
        # Directionals only — classic NAV
        nav_conf += 0.4
    elif has_a6 and not dir_ids:
        # ACTION6 only — classic CLICK (nearly unambiguous)
        click_conf += 0.5
    elif dir_ids and a6_tested:
        # Both directionals AND ACTION6 tested — HYBRID signal, lean CLICK
        click_conf += 0.2
    elif dir_ids and not a6_tested:
        # Directionals available, ACTION6 present but untested — lean NAV
        nav_conf += 0.3
    elif has_a5 and not dir_ids and not has_a6:
        # ACTION5 only — GLOBAL
        global_conf += 0.5

    # --- Channel 2: Directional consistency (NAV confirmation) ---
    if dir_ids:
        live_dirs = [
            sdk[aid] for aid in dir_ids
            if aid in sdk and sdk[aid].status == "LIVE" and sdk[aid].delta_cells > 0
        ]
        if len(live_dirs) >= 2:
            deltas = [s.delta_cells for s in live_dirs]
            if min(deltas) > 0 and max(deltas) / min(deltas) <= _CONSISTENCY_RATIO:
                nav_conf += 0.3 if len(live_dirs) >= 4 else 0.1

    # --- Channel 3: ACTION6 exclusivity (CLICK confirmation) ---
    if has_a6 and a6_entry is not None and a6_entry.status == "LIVE":
        if not dir_ids:
            # No directionals in available_actions at all
            click_conf += 0.3
        else:
            all_dir_noop = all(
                aid in sdk and sdk[aid].status == "NOOP"
                for aid in dir_ids
            )
            any_dir_live = any(
                aid in sdk and sdk[aid].status == "LIVE"
                for aid in dir_ids
            )
            if all_dir_noop:
                click_conf += 0.3   # directionals confirmed ineffective
            elif any_dir_live:
                click_conf += 0.1   # both effective — weaker CLICK signal

    # --- Select highest-confidence classification ---
    best_conf = max(nav_conf, click_conf, global_conf)
    if best_conf < _CONFIDENCE_THRESHOLD:
        return ("UNKNOWN", "UNKNOWN", 0.0)

    if nav_conf >= click_conf and nav_conf >= global_conf:
        return ("NAV", "EMBODIED", nav_conf)
    elif click_conf >= global_conf:
        return ("CLICK", "GOD_MODE", click_conf)
    else:
        return ("GLOBAL", "GLOBAL", global_conf)
