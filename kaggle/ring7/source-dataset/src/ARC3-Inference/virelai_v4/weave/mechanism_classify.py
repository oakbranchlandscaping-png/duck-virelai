"""virelai_v4/weave/mechanism_classify.py — WO-LEVER-SUBTREE-06.

Pure classification of a reactive partner's fingerprint sequence into one of the
mechanism categories the legacy ``library/cycle_probe.py`` algorithm (V3.5,
``cycle_probe.py:181-287``, "concept-only port source, confirmed pre-flipbook,
never touched" per this WO's own charter) already names: TOGGLE, CYCLE,
DIRECTIONAL, SATURATED, UNKNOWN.

WHY THIS PORTS THE CONCEPT, NOT THE FUNCTION (WO-LEVER-SUBTREE-06 §0's ruled
correction). ``cycle_probe.py`` classifies the LEVER'S OWN pixel trajectory — it
watches the lever itself toggle/cycle/drift when clicked. That premise fits a
lever that visibly changes on its own click. Our two confirmed real levers
(``###004``/``###005``, see ``AUDIT_LEVER_SUBTREE_CAMPAIGN_v1``) are the
opposite: static, remote, self-invariant by definition (WO-LEVER-SUBTREE-03/04's
own confirmed premise — a ``_self_invariant`` worldline never changes itself,
full stop). There is nothing on the lever's own side to classify. What the
subtree seed (``FOUNDATIONAL_ARCHETYPES_v2`` §3, "effect quality, bearing, and
magnitude") and the real data both call for is classifying the REACTIVE
PARTNER's pattern instead — same four live categories, same recurrence logic,
pointed at the object that actually has a pattern to show.

FINGERPRINT, ALREADY A NAMED CONCEPT. ``RegionClay``'s own docstring
(``capture/clay.py``) states: "the identity is the fingerprint
``(class_id, cells)``". This module does not invent a new notion of object
identity — it reuses the one this codebase already names, one snapshot per
targeted press.

WHAT'S PORTED, PRECISELY, FROM ``cycle_probe.py:181-287``
(``_classify_transition``):
  - Non-adjacent equality (distance >= 2) closes a recurrence; distance == 2
    -> TOGGLE, distance > 2 -> CYCLE. Scan order preserved: outer loop over
    press index ascending, inner loop over the earlier index ascending, first
    match wins — the earliest press at which ANY recurrence closes is the one
    reported (``cycle_probe.py:261``, ``for j in range(0, i - 1)``).

WHAT'S DELIBERATELY CHANGED, PER THIS WO'S EXPLICIT RULING:
  - SATURATED requires TWO CONSECUTIVE non-responses
    (``fp[i-2] == fp[i-1] == fp[i]``), not the legacy's one
    (``toggle_states[i] == toggle_states[i-1]``, a single press). The WO names
    this explicitly: "the legacy code's single-press saturation call is
    exactly the kind of premature, one-observation verdict this project has
    corrected everywhere else it's found it."

WHAT'S ADAPTED, NOT PORTED (no per-pixel toggle/drift split exists at the
object-fingerprint level the way it does over a raw pixel array):
  - DIRECTIONAL is read off ``cell_count`` monotonicity across the whole
    observed run when no recurrence and no saturation was found — the same
    "drift" concept cycle_probe.py's ``drift_pixel_count`` names, re-grounded
    on a scalar this codebase already treats as pixel-level ground
    (``SPEC_PIXEL_ARITHMETIC_v1``), since a frozenset-valued fingerprint has no
    per-pixel direction vector of its own to read.
  - UNKNOWN is the fallback when neither pattern confirms within the observed
    run — covers both of cycle_probe.py's two UNKNOWN branches (no
    toggle-and-no-drift; toggle-but-no-cycle-within-budget) under one name,
    since this module has no toggle/drift pixel split to keep them apart by.
"""

from __future__ import annotations

from typing import FrozenSet, Sequence, Tuple

# A fingerprint is one worldline's (class_id, cells) snapshot at one press —
# the identity RegionClay's own docstring already names. Two fingerprints are
# equal iff both fields match exactly (frozenset equality on cells is exact
# cell-position equality, per "the frame is truth").
Fingerprint = Tuple[int, FrozenSet[Tuple[int, int]]]

TOGGLE = "TOGGLE"
CYCLE = "CYCLE"
DIRECTIONAL = "DIRECTIONAL"
SATURATED = "SATURATED"
UNKNOWN = "UNKNOWN"

# Independently chosen for this context — this module never imports
# library/cycle_probe.py (RULING_GOLDEN_RUN_v1's feed-severing discipline), so
# this is not a shared constant, just the same considered value. Cites
# cycle_probe.py's own `_PROBE_CAP = 20` as the precedent this number matches:
# the legacy system's own observation budget for exactly this recurrence
# question, re-chosen here rather than copied.
MECHANISM_PROBE_MAX_PRESSES = 20


def classify_mechanism(fingerprints: Sequence[Fingerprint]) -> str:
    """Classify an ordered fingerprint sequence — one snapshot per targeted
    press, in order, ``fingerprints[0]`` being the partner's state BEFORE the
    first targeted press — into TOGGLE / CYCLE / DIRECTIONAL / SATURATED /
    UNKNOWN.

    Needs at least 2 entries to say anything; returns UNKNOWN below that — an
    honest "not yet knowable" from insufficient observation, never a guess."""
    n = len(fingerprints)
    if n < 2:
        return UNKNOWN

    for i in range(1, n):
        # Two-consecutive-non-response saturation (this WO's ruled
        # strengthening of the legacy single-press test) — needs i >= 2 so
        # both fp[i-1]==fp[i-2] (the first non-response) and fp[i]==fp[i-1]
        # (the second, consecutive one) are in range.
        if i >= 2 and fingerprints[i] == fingerprints[i - 1] == fingerprints[i - 2]:
            return SATURATED

        # Non-adjacent recurrence scan, ported verbatim in shape from
        # cycle_probe.py:261 (j ascending from 0 to i-2, first match wins).
        for j in range(0, i - 1):
            if fingerprints[i] == fingerprints[j]:
                distance = i - j
                return TOGGLE if distance == 2 else CYCLE

    # No recurrence, no saturation within the observed run. DIRECTIONAL iff
    # the cell_count trajectory drifted monotonically the whole way (isolated
    # single-press pauses tolerated, matching the legacy filter-to-nonzero-
    # diffs-before-checking-sign pattern); otherwise UNKNOWN.
    counts = [len(fp[1]) for fp in fingerprints]
    diffs = [b - a for a, b in zip(counts, counts[1:])]
    nonzero = [d for d in diffs if d != 0]
    if nonzero and (all(d > 0 for d in nonzero) or all(d < 0 for d in nonzero)):
        return DIRECTIONAL
    return UNKNOWN


__all__ = [
    "Fingerprint",
    "TOGGLE",
    "CYCLE",
    "DIRECTIONAL",
    "SATURATED",
    "UNKNOWN",
    "MECHANISM_PROBE_MAX_PRESSES",
    "classify_mechanism",
]
