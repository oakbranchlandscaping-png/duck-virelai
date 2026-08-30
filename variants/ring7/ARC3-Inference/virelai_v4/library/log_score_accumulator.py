"""
virelai_v4/library/log_score_accumulator.py — BBA Layer One accumulator.

Translates role classifier verdicts (and probe-confirmed evidence) into
per-slot log-score axis increments. Lives as a sibling module to
`library_sync.py` rather than inside it; the audit's tier rule permitted
either placement, but `library_sync.py` already imports from
`classification_pass.py`, `probe_outcome_processor.py`, and adjacent
modules — placing the accumulator there and importing it back into those
three call-sites would produce a circular-import surface. The sibling
module avoids that risk.

Per BBA Layer One coexistence audit:
  - §3.4 — saturation-preserving accumulator constraint: the accumulator
    must fire on every terminal cycle_probe `lever_mechanism` commit
    (CYCLE, TOGGLE, DIRECTIONAL, GLOBAL, ONE_SHOT, GATED, SATURATED,
    UNKNOWN), not only on cycles.
  - §4.5 — primary extension target is the classifier verdict consumer
    at `library/classification_pass.py:_classify_objects`, not
    `library.update_object_role`. The secondary writers
    (`contact_reactivity_integration.py:370`, the cycle_probe
    `lever_mechanism` writers) bypass `update_object_role`; attaching
    the hook there would silently miss them.
  - §4.6 — the hook is purely additive. All existing categorical writes
    (`obj.role`, `obj.confidence`, `obj.lever_locked`,
    `obj.lever_mechanism`) are preserved during Sub-Phase 3 coexistence.

FM 6 mitigation: no module-level mutable state. The role→axis lookup
table is a `MappingProxyType` (immutable). The function holds no caches,
counters, or shared lists across calls.

FM 7 mitigation: the function signature accepts only `(slot, role,
confidence)`. No lifecycle field (`game_state`, `full_reset`, level,
life) is read. Inspection-based tests in
`tests/library/test_log_score_accumulator.py` pin both properties.

Import sovereignty: stdlib + `library.library_roles` + `library.semantic_library`.
No imports from `library_sync`, `classification_pass`,
`probe_outcome_processor`, `cycle_probe`, or any module outside `library/`.

Filed under WO-BLUEPRINT-07 (May 22, 2026).
"""

from __future__ import annotations

import logging
import math
from types import MappingProxyType

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import LibraryObject

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Role → BBA axis mapping (immutable lookup)
# ---------------------------------------------------------------------------
#
# Six BBA Layer One axes per Blueprint Section 2.6.1:
#     static, reactive, ego, counter, lever, gate
#
# Five of the nine LibraryRole values map to a corresponding axis. The other
# four — TARGET, SIGNAL, INERT, UNKNOWN — are not part of the BBA six-axis
# taxonomy: TARGET is a Section 4+ concept, SIGNAL is HUD-adjacent, INERT is the
# STATIC-branch role-null, and UNKNOWN is absence of evidence. The accumulator
# no-ops for all four — LOUDLY as of WO-A3-01 (see the WARNING at the `.get`
# miss). (Prior text read "five of eight" and named three; the enum has nine
# members and INERT was the unnamed fourth — the count-next-to-the-code debt.)
#
# The `gate` axis is not yet wired (Sub-Phase 4+ work per the Captain's
# category priority structure) — no LibraryRole maps to it today; it
# remains at the neutral prior until later sub-phases.
_ROLE_TO_AXIS: "MappingProxyType[LibraryRole, str]" = MappingProxyType({
    LibraryRole.EGO:      "ego_log_score",
    LibraryRole.LEVER:    "lever_log_score",
    LibraryRole.REACTIVE: "reactive_log_score",
    LibraryRole.COUNTER:  "counter_log_score",
    LibraryRole.STATIC:   "static_log_score",
})


# Numerical clamp for confidence at the boundaries. logit(0) and logit(1)
# are infinite; clamping to (eps, 1 - eps) keeps the increment finite
# while preserving the high-confidence-saturates-axis behavior the audit
# §3.4 anchor requires.
_CLAMP_EPS: float = 1e-6


# ---------------------------------------------------------------------------
# accumulate_role_evidence — the single public entry point
# ---------------------------------------------------------------------------

def accumulate_role_evidence(
    slot: LibraryObject,
    role: LibraryRole,
    confidence: float,
) -> None:
    """Translate one classifier verdict (or probe-confirmed evidence) into
    a log-odds increment on the Slot's corresponding BBA axis.

    The increment is the Bayesian log-odds delta from the neutral prior:

        delta = log(p / (1 - p))     where  p = clamp(confidence, eps, 1-eps)

    For confidence == 0.5, delta is 0 (no evidence). For high confidence,
    delta is large and positive — a single call from the cycle_probe
    saturation site (confidence 1.0) drives the axis above
    CONFIRMATION_THRESHOLD per the audit §3.4 anchor requirement.

    Roles outside the BBA six-axis taxonomy (TARGET, SIGNAL, INERT, UNKNOWN)
    produce no increment; the function no-ops — LOUDLY (WO-A3-01: a WARNING
    naming the role, the dropped confidence, and the slot). This preserves the
    substrate's neutral state during the classifier's insufficient-evidence
    frames without hiding that evidence was dropped.

    Args:
        slot: The LibraryObject to mutate. The corresponding
              `<axis>_log_score` field is incremented in place.
        role: The LibraryRole verdict (from classify_role) or evidence
              tag (from probe outcome / cycle_probe terminal commit).
        confidence: Scalar in [0.0, 1.0]. The classifier's confidence in
              the role assignment, or 1.0 for direct probe confirmation.

    Returns:
        None. The Slot is mutated in place.
    """
    axis = _ROLE_TO_AXIS.get(role)
    if axis is None:
        # WO-A3-01 — THE LOUD DOOR. The discard stays lawful: a role with no
        # BBA axis (TARGET, SIGNAL, INERT, UNKNOWN) still writes nothing, so the
        # neutral prior is preserved. What dies is the SILENCE. A normalizer that
        # drops evidence without a word is the door-swallowing pattern — it made
        # `landed=0` legible only by accident, months late. Now it says so.
        #
        # Per the A3 ruling, this is per-role in intent though uniform in code:
        #   TARGET  — a real _confidence_target value is being dropped; a category
        #             error upstream (role_classifier), a pending-register item.
        #   SIGNAL  — a 0.40 sentinel; declared non-evidential, lossless to drop.
        #   INERT   — never reaches here today (NO-CALLER-FOUND at 92fa8a0);
        #             the header's "five of eight" miscounts the nine-member enum.
        #   UNKNOWN — absence of evidence; lawful to drop, but not silently.
        _logger.warning(
            "accumulate_role_evidence: role %s has no BBA axis; dropping "
            "confidence %.4f for slot region_id=%s. Discard is lawful "
            "(neutral prior preserved); the silence is not.",
            getattr(role, "value", role),
            confidence,
            getattr(slot, "region_id", "?"),
        )
        return

    # Clamp to avoid logit(0) = -inf and logit(1) = +inf. The clamp
    # preserves monotonicity (higher confidence → larger delta) and
    # ensures one call from confidence==1.0 produces a finite, large
    # increment (logit(1 - 1e-6) ≈ 13.8) sufficient to drive
    # sigmoid_confidence above CONFIRMATION_THRESHOLD on a single
    # observation — the audit §3.4 anchor constraint.
    p = max(_CLAMP_EPS, min(1.0 - _CLAMP_EPS, confidence))
    delta = math.log(p / (1.0 - p))

    current = getattr(slot, axis)
    setattr(slot, axis, current + delta)


def _retire_static_on_reactive_witness(slot) -> None:
    """DD gap-3a: retire the static self-state conjecture on the reactive witness.

    NESTED_TAXONOMY_SPEC §3: `static` is a falsifiable ∀-conjecture ("its own
    pixels have never changed"); the first observed self-delta — the reactive
    witness (the black swan) — falsifies it forever. This sets
    `static_log_score = -inf`, which `sigmoid_confidence` maps to 0.0
    (semantic_library.py:356-357).

    Single responsibility — the NEGATIVE pole only. It does NOT write
    `reactive_log_score`: the positive seal (`reactive = +inf`) is gap-3b,
    deferred behind the gap-2 overload split, because `reactive_log_score` is the
    axis `implied_role` argmaxes for the Band-2 role and `+inf` there poisons the
    role read (a LOCAL lever/counter/ego would derive REACTIVE). `static` is NOT
    overloaded, so a `-inf` there is side-effect-free on the role derivation — a
    `-inf` axis never wins the raw-argmax maximum; it can only stop masking the
    true role beneath a static corpse.

    Idempotent: re-setting `-inf` is a no-op. Witness-gated by the caller (fires
    at the first-active-frame block in delta_updater.py — a genuine observed
    self-delta, per §3 "earned by observation alone"), never by absence-of-change.
    """
    slot.static_log_score = float("-inf")


__all__ = ["accumulate_role_evidence", "_retire_static_on_reactive_witness"]
