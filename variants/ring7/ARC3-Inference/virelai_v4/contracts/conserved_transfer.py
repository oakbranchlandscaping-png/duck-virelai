"""
virelai_v4/contracts/conserved_transfer.py — ConservedTransfer: the lever-keyed
conserved-transfer relation (WO-C3, Campaign C exit rung).

The verb Campaign C authors: a conserved quantity transferred across the
figure/ground boundary by a lever, with the participating class-0 endpoints as
MEMBERS. The Slots are participants, not the definition (ruling a). The relation
is authored from measured deltas at the record_lever_effect seam, never
stipulated (ruling c / §4).

DISCIPLINE FENCES baked into the contract so they cannot leak back in:

  * Single relation per coupled unit. The relation holds {members, conserved
    quantity, boundary complement}. Per-subject LeverEffect entries carry only a
    membership flag (conserved_transfer_member) — never the relation itself
    (ruling b / §3).

  * Boundary complement, NOT class-3-as-partner [Fold 3 / §4(iii)]. When the
    conservation closes a class-0 endpoint against the boundary (rather than a
    second class-0 endpoint), the other side is recorded as a ConservedComplement
    — a conserved QUANTITY typed by behavior ("divider"), NEVER the background
    class designated as the actor. class-3-as-partner is the figure/ground
    assertion the cells do not license (C4 made it 'potential_background',
    candidacy not verdict); this contract must not hard-assert it one layer down.

  * Integer-exact [§4(i)]. conserved_quantity is an integer cell count. The grid
    is deterministic and admits no epsilon; a relation that does not net exactly
    is not asserted (the author returns None, entries stay uncoupled).

  * Descent reserved [ruling d / §4(iii)]. DescentRequired is raised — never
    swallowed into a silent couple — when closing the conservation would require
    a Slot to doubt its own boundary (re-read / split / merge to expose a missing
    endpoint). That is the reserved Descent Operator: escalate to Apex.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass(frozen=True)
class ConservedComplement:
    """The non-functional side of a conserved transfer, recorded as a conserved
    QUANTITY typed by its behavior — never as class-3-the-partner.

    quantity      : the conserved magnitude crossing the boundary (signed; the
                    complement of the functional member's delta).
    boundary_kind : a behavioral type for the boundary crossed (e.g. "divider"),
                    NOT a class id / color. The relation conserves a quantity; it
                    does not designate the background as the actor.
    """
    quantity: int
    boundary_kind: str = "divider"


@dataclass(frozen=True)
class ConservedTransfer:
    """A lever-keyed conserved-transfer relation, authored from measured deltas.

    lever_region_id    : the lever this relation is keyed to.
    member_subject_ids : the participating (non-background) endpoints — the
                         conserved quantity's members, derived from measured
                         deltas, not picked.
    conserved_quantity : integer-exact conserved magnitude (gross transfer).
    complement         : the boundary side when the conservation closes
                         class-0-against-the-boundary (ConservedComplement);
                         None when it closes class-0-to-class-0 (members alone
                         net to zero).
    """
    lever_region_id: int
    member_subject_ids: Tuple[int, ...]
    conserved_quantity: int
    complement: Optional[ConservedComplement] = None

    def predict_complement_delta(self, member_id: int,
                                 member_delta: int) -> Optional[int]:
        """Forward, exact-value out-prediction [§4(ii)]: given a member's signed
        delta, predict its conserved partner's EXACT signed delta. Conservation
        means the partner absorbs the negation, so the predicted value is
        -member_delta — a specific signed magnitude, not a direction. Returns
        None when member_id is not a member of this relation (the uncoupled
        model has no partner to predict and fails by silence)."""
        if member_id not in self.member_subject_ids:
            return None
        return -member_delta


class DescentRequired(Exception):
    """Raised when closing the conservation requires a Slot to doubt its own
    boundary — a class-0 Slot must be re-read, split, or merged to expose a
    missing endpoint [ruling d / §4(iii)]. The reserved Descent Operator: a
    campaign-level result, escalated to Apex, never engineered past with an
    epsilon or a silent couple."""


__all__ = [
    "ConservedComplement",
    "ConservedTransfer",
    "DescentRequired",
]
