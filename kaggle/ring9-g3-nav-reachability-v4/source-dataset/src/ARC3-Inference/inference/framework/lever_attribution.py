"""Scoped G3 lever attribution after ego and counter identification.

This module ports the two-channel witness law from the golden solver without
importing its controller policy.  POINTER attribution is resolved at the
pre-action site.  BODY attribution requires an observed contact line or a
scoped refused-contact report.  A positive residue proves a lever witness;
silence never proves inertness and never retracts an earlier witness.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


ATTRIBUTION_CHANNELS = frozenset({"POINTER", "BODY"})
POSITIVE_DISPOSITIONS = frozenset({
    "LOCAL_LEVER_WITNESS",
    "REMOTE_LEVER_WITNESS",
    "LOCAL_AND_REMOTE_LEVER_WITNESS",
})
AMBIGUOUS_DISPOSITIONS = frozenset({"AMBIGUOUS_EGO_MASKED"})
COUNTER_ONLY_DISPOSITION = "COUNTER_ONLY_RESPONSE"


class LeverAttributionError(ValueError):
    """The outcome lacks the lossless or scoped evidence needed by G3."""


Cell = tuple[int, int]
Change = tuple[int, int, int | None, int | None]


@dataclass(frozen=True)
class LeverAttribution:
    attribution_id: str
    evidence_ref: str
    transition_id: int
    channel: str
    target_member_id: str
    contact_attributed: bool
    attribution_basis: str
    disposition: str
    changed_cells: tuple[Change, ...]
    counter_masked_cells: tuple[Cell, ...]
    ego_motion_cells: tuple[Cell, ...]
    ego_confounded_cells: tuple[Cell, ...]
    ground_exchange_cells: tuple[Cell, ...]
    residue_cells: tuple[Cell, ...]
    local_residue_cells: tuple[Cell, ...]
    remote_residue_cells: tuple[Cell, ...]
    boundary_state: str | None
    inertness_claim_permitted: bool
    limitations: tuple[str, ...]

    @property
    def positive(self) -> bool:
        return self.disposition in POSITIVE_DISPOSITIONS


@dataclass(frozen=True)
class LeverWitness:
    witness_id: str
    target_member_id: str
    evidence_ref: str
    transition_id: int
    channel: str
    locality: str
    local_residue_cells: tuple[Cell, ...]
    remote_residue_cells: tuple[Cell, ...]


@dataclass(frozen=True)
class LeverRecord:
    target_member_id: str
    status: str
    local_witnesses: tuple[LeverWitness, ...]
    remote_witnesses: tuple[LeverWitness, ...]
    null_evidence_refs: tuple[str, ...]
    counter_only_evidence_refs: tuple[str, ...]
    unresolved_evidence_refs: tuple[str, ...]
    inertness_claim_permitted: bool = False


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def _cells(values: Iterable[Any], *, field: str) -> frozenset[Cell]:
    cells: set[Cell] = set()
    for value in values:
        if isinstance(value, Mapping):
            if "row" not in value or "col" not in value:
                raise LeverAttributionError(f"{field} entries require row and col")
            cells.add((int(value["row"]), int(value["col"])))
        elif isinstance(value, (list, tuple)) and len(value) == 2:
            cells.add((int(value[0]), int(value[1])))
        else:
            raise LeverAttributionError(f"{field} entries must be [row, col] or coordinate objects")
    return frozenset(cells)


def _changes(outcome: Mapping[str, Any]) -> tuple[Change, ...]:
    raw = outcome.get("changed_cells")
    if not isinstance(raw, (list, tuple)):
        raise LeverAttributionError(
            "G3 attribution requires lossless changed_cells; previews or counts are insufficient"
        )
    changes: list[Change] = []
    for item in raw:
        if not isinstance(item, Mapping) or "row" not in item or "col" not in item:
            raise LeverAttributionError("changed_cells entries require row and col")
        changes.append((
            int(item["row"]),
            int(item["col"]),
            None if item.get("before") is None else int(item["before"]),
            None if item.get("after") is None else int(item["after"]),
        ))
    return tuple(sorted(changes))


def _acted_cell(outcome: Mapping[str, Any]) -> Cell | None:
    acted = outcome.get("acted_site")
    if not isinstance(acted, Mapping):
        return None
    if "row" not in acted or "col" not in acted:
        return None
    return int(acted["row"]), int(acted["col"])


def _boundary_state(outcome: Mapping[str, Any]) -> str | None:
    boundary = outcome.get("boundary_event")
    if not isinstance(boundary, Mapping):
        return None
    terminal = any(
        bool(boundary.get(key))
        for key in ("done", "level_completed", "game_over", "run_complete")
    )
    if not terminal:
        return None
    return str(boundary.get("state") or "OBSERVED_BOUNDARY")


def attribute_lever_outcome(
    outcome: Mapping[str, Any],
    *,
    evidence_ref: str,
    channel: str,
    target_member_id: str,
    target_cells: Iterable[Any],
    counter_mask_cells: Iterable[Any],
    ego_motion_cells: Iterable[Any],
    ego_confounded_cells: Iterable[Any] = (),
    ground_exchange_cells: Iterable[Any] = (),
    body_contact_cells: Iterable[Any] = (),
    pre_action_owner_member_id: str | None = None,
    refused_contact: bool = False,
    target_is_counter: bool = False,
) -> LeverAttribution:
    """Attribute one transition without assigning a mechanism to its residue.

    ``target_cells`` is the resolved target footprint relevant to this press.
    ``ego_motion_cells`` is the ego's own expected vacated/entered footprint.
    Target-owned cells are retained even when the ego enters them, because an
    object disappearing or changing on contact is a local response.  Ordinary
    ground exchange must be supplied separately and is always subtracted.
    """
    normalized_channel = str(channel or "").strip().upper()
    if normalized_channel not in ATTRIBUTION_CHANNELS:
        raise LeverAttributionError(f"unsupported attribution channel: {channel!r}")
    member_id = str(target_member_id or "").strip()
    if not member_id:
        raise LeverAttributionError("target_member_id is required")
    evidence = str(evidence_ref or "").strip()
    if not evidence:
        raise LeverAttributionError("evidence_ref is required")

    changes = _changes(outcome)
    changed = frozenset((row, col) for row, col, _, _ in changes)
    target = _cells(target_cells, field="target_cells")
    counter = changed & _cells(counter_mask_cells, field="counter_mask_cells")
    raw_ego = changed & _cells(ego_motion_cells, field="ego_motion_cells")
    confounded = changed & _cells(ego_confounded_cells, field="ego_confounded_cells")
    # Preserve target-owned contact cells as possible local response instead
    # of erasing them as generic ego translation.
    ego = raw_ego - target
    ground = (
        changed & _cells(ground_exchange_cells, field="ground_exchange_cells")
    ) - target
    contact_line = _cells(body_contact_cells, field="body_contact_cells") & target

    if normalized_channel == "POINTER":
        acted = _acted_cell(outcome)
        contact_attributed = (
            acted is not None
            and acted in target
            and str(pre_action_owner_member_id or "") == member_id
        )
        basis = (
            "PRE_ACTION_POINTER_OWNER"
            if contact_attributed else "POINTER_OWNER_UNRESOLVED"
        )
    else:
        contact_attributed = bool(contact_line) or bool(refused_contact)
        if contact_line:
            basis = "BODY_CONTACT_LINE"
        elif refused_contact:
            basis = "SCOPED_REFUSED_BODY_CONTACT"
        else:
            basis = "BODY_CONTACT_UNRESOLVED"

    residue = changed - counter - ego - ground
    local = residue & target
    remote = residue - target
    boundary_state = _boundary_state(outcome)
    limitations: list[str] = []

    if boundary_state is not None:
        disposition = "BOUNDARY_EVENT_DEFERRED"
        limitations.append(
            "Boundary transitions are retained for G4 reaction typing and do not prove a G3 lever."
        )
    elif changed and changed == counter and (target_is_counter or not contact_attributed):
        disposition = COUNTER_ONLY_DISPOSITION
        limitations.append(
            "All observed change was contained in the sealed counter footprint. This tested "
            "interaction produced no visible lever residue after bookkeeping subtraction; "
            "it does not establish inertness."
        )
    elif confounded and not (residue - confounded):
        disposition = "AMBIGUOUS_EGO_MASKED"
        limitations.append(
            "Changed ego cells could be self-motion or remotely driven; G3 will not call them null."
        )
    elif not contact_attributed:
        disposition = "UNRESOLVED_ATTRIBUTION"
        limitations.append(
            "A visible residue without resolved pointer ownership or body contact is not a lever witness."
        )
    elif local and remote:
        disposition = "LOCAL_AND_REMOTE_LEVER_WITNESS"
    elif local:
        disposition = "LOCAL_LEVER_WITNESS"
    elif remote:
        disposition = "REMOTE_LEVER_WITNESS"
    else:
        disposition = "SCOPED_NULL_RESPONSE"
        limitations.append(
            "This press produced no non-excluded residue; it does not establish inertness."
        )

    transition_id = int(outcome.get("transition_id") or 0)
    seed = {
        "evidence_ref": evidence,
        "transition_id": transition_id,
        "channel": normalized_channel,
        "target_member_id": member_id,
        "disposition": disposition,
        "residue": sorted(residue),
    }
    attribution_id = "ATTR-" + hashlib.sha256(_canonical(seed).encode()).hexdigest()[:16]
    return LeverAttribution(
        attribution_id=attribution_id,
        evidence_ref=evidence,
        transition_id=transition_id,
        channel=normalized_channel,
        target_member_id=member_id,
        contact_attributed=contact_attributed,
        attribution_basis=basis,
        disposition=disposition,
        changed_cells=changes,
        counter_masked_cells=tuple(sorted(counter)),
        ego_motion_cells=tuple(sorted(ego)),
        ego_confounded_cells=tuple(sorted(confounded)),
        ground_exchange_cells=tuple(sorted(ground)),
        residue_cells=tuple(sorted(residue)),
        local_residue_cells=tuple(sorted(local)),
        remote_residue_cells=tuple(sorted(remote)),
        boundary_state=boundary_state,
        inertness_claim_permitted=False,
        limitations=tuple(limitations),
    )


def witness_from_attribution(attribution: LeverAttribution) -> LeverWitness | None:
    """Create an existential witness only from a positively attributed residue."""
    if not attribution.positive:
        return None
    locality = {
        "LOCAL_LEVER_WITNESS": "LOCAL",
        "REMOTE_LEVER_WITNESS": "REMOTE",
        "LOCAL_AND_REMOTE_LEVER_WITNESS": "LOCAL_AND_REMOTE",
    }[attribution.disposition]
    return LeverWitness(
        witness_id="LEVER-" + attribution.attribution_id.split("-", 1)[-1],
        target_member_id=attribution.target_member_id,
        evidence_ref=attribution.evidence_ref,
        transition_id=attribution.transition_id,
        channel=attribution.channel,
        locality=locality,
        local_residue_cells=attribution.local_residue_cells,
        remote_residue_cells=attribution.remote_residue_cells,
    )


class LeverEvidenceAccumulator:
    """Append-only G3 evidence; later silence cannot retract a witness."""

    def __init__(self) -> None:
        self._attributions: dict[str, list[LeverAttribution]] = {}
        self._witnesses: dict[str, list[LeverWitness]] = {}

    def record(self, attribution: LeverAttribution) -> LeverRecord:
        member_id = attribution.target_member_id
        self._attributions.setdefault(member_id, []).append(attribution)
        witness = witness_from_attribution(attribution)
        if witness is not None:
            self._witnesses.setdefault(member_id, []).append(witness)
        return self.record_for(member_id)

    def record_for(self, target_member_id: str) -> LeverRecord:
        member_id = str(target_member_id)
        attributions = self._attributions.get(member_id, [])
        witnesses = self._witnesses.get(member_id, [])
        local = tuple(
            item for item in witnesses if item.locality in {"LOCAL", "LOCAL_AND_REMOTE"}
        )
        remote = tuple(
            item for item in witnesses if item.locality in {"REMOTE", "LOCAL_AND_REMOTE"}
        )
        if local and remote:
            status = "LEVER_LOCAL_AND_REMOTE"
        elif local:
            status = "LEVER_LOCAL"
        elif remote:
            status = "LEVER_REMOTE"
        elif attributions:
            status = "NO_POSITIVE_WITNESS_YET"
        else:
            status = "UNTRIED"
        return LeverRecord(
            target_member_id=member_id,
            status=status,
            local_witnesses=local,
            remote_witnesses=remote,
            null_evidence_refs=tuple(
                item.evidence_ref
                for item in attributions
                if item.disposition == "SCOPED_NULL_RESPONSE"
            ),
            counter_only_evidence_refs=tuple(
                item.evidence_ref
                for item in attributions
                if item.disposition == COUNTER_ONLY_DISPOSITION
            ),
            unresolved_evidence_refs=tuple(
                item.evidence_ref
                for item in attributions
                if item.disposition in {
                    "UNRESOLVED_ATTRIBUTION", "BOUNDARY_EVENT_DEFERRED"
                }
            ),
            inertness_claim_permitted=False,
        )

    def snapshot(self) -> dict[str, Any]:
        members = sorted(set(self._attributions) | set(self._witnesses))
        return {
            "schema": "virelai-g3-lever-evidence-v1",
            "records": [asdict(self.record_for(member)) for member in members],
        }
