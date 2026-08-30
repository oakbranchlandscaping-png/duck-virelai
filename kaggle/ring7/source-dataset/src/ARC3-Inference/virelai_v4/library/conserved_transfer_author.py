"""
virelai_v4/library/conserved_transfer_author.py — author the ConservedTransfer
relation from measured deltas (WO-C3 §4, ruling c + CE's licensing conditions).

Pure, read-only, library-tier. Computes WHETHER a conserved-transfer relation is
licensed and, if so, its members / conserved quantity / boundary complement —
all DERIVED from measured deltas, never stipulated. The Substrate
(semantic_library.record_conserved_transfer) is the single writer; this module
only decides and constructs.

Licensing (HL-4, no free parameter):
  (i)   Conservation — integer-exact, no epsilon. A relation is licensed only
        when the functional-side deltas net EXACTLY (loss == gain), or a single
        functional endpoint nets EXACTLY against a measured boundary complement.
  (ii)  Out-prediction — forward, out-of-sample, exact-value. When a held-out
        press is supplied, the candidate must predict that press's complementary
        member's EXACT signed delta; mismatch → not licensed.
  (iii) Membership — measured (reads is_background to separate functional
        endpoints from the boundary side; it does NOT re-attribute — Fold 2),
        boundary recorded as a conserved complement quantity, never
        class-3-as-partner. If closing requires a missing endpoint → Descent.

Game-free: no class literal, no color, no tuned threshold. The only belief read
is the already-attributed subject set and the is_background label.
"""

from __future__ import annotations

from typing import Dict, Mapping, Optional, Tuple

from virelai_v4.contracts.conserved_transfer import (
    ConservedComplement,
    ConservedTransfer,
    DescentRequired,
)


def author_conserved_transfer(
    lever_region_id: int,
    functional_deltas: Mapping[int, int],
    *,
    complement_candidate: Optional[int] = None,
    global_functional_conserves: bool = False,
    holdout: Optional[Tuple[int, int, int]] = None,
) -> Optional[ConservedTransfer]:
    """Decide and construct the conserved-transfer relation, or None / Descent.

    Args:
      lever_region_id: the lever the relation is keyed to.
      functional_deltas: {subject_id: signed integer delta} for this lever's
        NON-background (functional) endpoints this press — measured, the
        background side excluded by the caller via is_background.
      complement_candidate: the measured boundary-side signed magnitude (the
        background swing's functional portion), when present. Used only for the
        class-0-against-boundary shape.
      global_functional_conserves: measured fact that the functional total is
        conserved globally this level. Distinguishes "honestly uncoupled" from
        "a class-0 endpoint is missing" (the Descent trigger).
      holdout: (member_id, member_delta, measured_complement_delta) from a
        held-out press, for the forward exact-value out-prediction gate (§4 ii).
        None when no held-out press is available yet (no license is emitted for
        the grade flip until the forward check has passed — see the seam).

    Returns the licensed ConservedTransfer, or None when no relation is licensed.
    Raises DescentRequired when closing the conservation needs a Slot to doubt
    its own boundary.
    """
    nonzero = {sid: d for sid, d in functional_deltas.items() if d != 0}

    candidate = _form_candidate(
        lever_region_id, nonzero, complement_candidate,
        global_functional_conserves)
    if candidate is None:
        return None

    # (ii) forward, out-of-sample, exact-value gate.
    if holdout is not None:
        member_id, member_delta, measured_complement = holdout
        predicted = candidate.predict_complement_delta(member_id, member_delta)
        if predicted is None or predicted != measured_complement:
            return None      # the coupled model failed to out-predict — no license

    return candidate


def _form_candidate(
    lever_region_id: int,
    nonzero: Dict[int, int],
    complement_candidate: Optional[int],
    global_functional_conserves: bool,
) -> Optional[ConservedTransfer]:
    """Construct the integer-exact candidate from measured deltas, or signal
    Descent / None. No epsilon: equality is exact integer arithmetic."""
    if not nonzero:
        return None

    total = sum(nonzero.values())

    # Shape A — class-0-to-class-0: the functional endpoints net to zero exactly.
    if len(nonzero) >= 2 and total == 0:
        gross = sum(d for d in nonzero.values() if d > 0)
        return ConservedTransfer(
            lever_region_id=lever_region_id,
            member_subject_ids=tuple(sorted(nonzero.keys())),
            conserved_quantity=gross,
            complement=None,
        )

    # Shape B — class-0-against-the-boundary: a single functional endpoint nets
    # EXACTLY against a measured boundary complement. The complement is a
    # conserved QUANTITY typed by behavior, never class-3-the-partner.
    if len(nonzero) == 1:
        (member_id, d), = nonzero.items()
        if complement_candidate is not None and complement_candidate == -d:
            return ConservedTransfer(
                lever_region_id=lever_region_id,
                member_subject_ids=(member_id,),
                conserved_quantity=abs(d),
                complement=ConservedComplement(quantity=-d, boundary_kind="divider"),
            )
        # No matching boundary complement. If the functional total is measured to
        # conserve globally, the closing endpoint exists but is not recorded here
        # — a Slot must be re-read to expose it. Descent, not a silent couple.
        if global_functional_conserves:
            raise DescentRequired(
                f"lever {lever_region_id}: functional endpoint {member_id} "
                f"(Δ={d}) does not net against any recorded endpoint or measured "
                f"boundary complement, yet the functional total conserves "
                f"globally — closing requires re-individuating a Slot to expose "
                f"the missing endpoint. Reserved Descent Operator; escalate.")
        return None

    # Functional endpoints present but do not net exactly. If they are measured
    # to conserve globally, an endpoint is missing → Descent; else honestly
    # uncoupled (the conservation is conditional, partitioned not averaged).
    if global_functional_conserves and total != 0:
        raise DescentRequired(
            f"lever {lever_region_id}: recorded functional endpoints "
            f"{sorted(nonzero)} net to {total} (≠0) but the functional total "
            f"conserves globally — a Slot boundary must be re-read to close. "
            f"Reserved Descent Operator; escalate.")
    return None


__all__ = ["author_conserved_transfer"]
