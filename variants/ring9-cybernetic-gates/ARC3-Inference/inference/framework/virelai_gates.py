"""Fresh cybernetic gate kernel for Virelai.

The kernel owns the scientific protocol.  Duck may describe and interpret the
evidence, but it cannot skip a required probe, silently change the question, or
close a gate with a label-only answer.

This first slice implements G0 (opaque action affordances) and G1 (ego/direct
influence).  Later gates should extend the same state machine rather than add a
second router.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
from typing import Any, Iterable, Mapping, Sequence

from inference.framework.adaptive_ego_coverage import (
    AdaptiveCoordinateCoverage,
    CoordinateCandidate,
    candidate_digest,
)
from inference.framework.cybernetic_targeting import (
    GateAssessment,
    GoalContract,
    MemoryProduct,
    TargetJournal,
    TargetRegistry,
    TargetRouter,
)
from inference.framework.counter_verification import (
    trigger_record,
    CounterBoundary,
    CounterCandidate,
    CounterComparison,
    CounterPrediction,
    MaskLaw,
    compare_counter_prediction,
    compare_counter_boundary,
    compile_counter_candidates,
    mask_law_from_supported,
    counter_standing,
    prediction_for,
)
from inference.framework.ego_verification import (
    EgoLaw,
    ProspectivePrediction,
    ScopedComparison,
    compare_probe_outcome,
    ego_law_from_interface,
    ego_law_from_supported,
    prediction_from_mapping,
)
from inference.framework.probe_evidence import EVIDENCE_SCHEMA, compact_probe_outcome
from inference.framework.masked_world_state import MaskedStateArchive, grids_from_probe_outcome
from inference.framework.lever_attribution import (
    ATTRIBUTION_CHANNELS,
    COUNTER_ONLY_DISPOSITION,
    LeverAttributionError,
    POSITIVE_DISPOSITIONS,
    LeverEvidenceAccumulator,
    attribute_lever_outcome,
)
from inference.framework.entity_observation import EntityLedger, EntityTransition, ObservationScope
from inference.framework.lever_lifecycle import LifecycleJournal
from inference.framework.g3_inheritance import G2NullInheritance, inherited_total_nulls
from inference.framework.annotation_lane import AnnotationLane
from inference.framework.memory_store import cell_bbox
from inference.framework.life_record import LifeRecord
from inference.framework.carry import CarryLedger
from inference.framework.lever_dossier import (
    LeverDossierAnswer,
    LeverDossierError,
    effect_summary as lever_effect_summary,
    validate_lever_dossier,
)
from inference.framework.g4_reactions import (
    G4ReactionError,
    LeverEffectAnatomy,
    LeverReactionAnswer,
    anatomy_payload,
    compile_effect_anatomy,
    validate_reaction_answer,
)
from inference.framework.g4_orbits import G4OrbitError, LeverOrbitAnswer, validate_orbit_answer
from inference.framework.g4_guided import (
    INTERRUPTED,
    LeverRun,
    is_terminal,
    level_changed,
    restudy_next_life,
)


SCHEMA_VERSION = "virelai-cybernetic-gates-v1"
# Axiom A1 (DOCTRINE_FRICTION_AXIOMS_v1): counters come in many forms; the target is the same.
COUNTER_TARGET = (
    "Find any counter on this board -- a visible process that tracks bookkeeping (actions, "
    "effective moves, time, lives) rather than the world -- label its law, and mask it so lever "
    "data stays pure. You choose the actions. When the controller shows a candidate, explain it "
    "and freeze one prediction about the counter's footprint for an action you choose."
)
ACTION_METADATA_GATE_ID = "G0-ACTION-METADATA"
GATE_ID = "G1-EGO"
COUNTER_GATE_ID = "G2-COUNTER"
COUNTER_BOUNDARY_BATCH_MAX = max(1, int(os.environ.get("VIRELAI_COUNTER_BOUNDARY_BATCH_MAX", "8")))
LEVER_GATE_ID = "G3-LEVERS"
REACTION_GATE_ID = "G4-REACTIONS"
ORBIT_GATE_ID = "G4.2-LEVER-ORBITS"
RELATION_GATE_ID = "G4-B-LEVER-RELATIONS"
LAW_GATE_ID = "G4-C-LEVER-LAW"
G4_GATE_IDS = (REACTION_GATE_ID, ORBIT_GATE_ID, RELATION_GATE_ID, LAW_GATE_ID)


def _phase1_hold_reason(payload: Mapping[str, Any]) -> str | None:
    """Why Phase 2 (G4-B onward) may not open yet, or None when it may.

    Held in ``_effective_target_id``: no gate after G4-A opens while this returns a reason.
    Cross-level work is a separate gate (G9): a level transition closes the level's G4 study.
    """
    if payload.get("pending_lever_entities"):
        return "Phase 1 is incomplete."
    if payload.get("phase1_status") == "CLOSED_BY_LEVEL_BOUNDARY":
        return "the level changed during Phase 1; cross-level work belongs to the G9 gate."
    if not payload.get("lever_entities"):
        return "no lever completed Phase 1 on this level."
    return None


def _lever_class(answer: Any) -> str:
    """Phase-1 classification of a lever from its own consecutive-push orbit.

    Derived only from the orbit stop and period (single-lever data); no
    cross-lever information. Richer typing is a later refinement.
    """
    stop = getattr(answer, "stop_disposition", None)
    period = getattr(answer, "observed_period", None)
    if stop == "OBSERVED_STATE_RECURRENCE":
        if period == 2:
            return "TOGGLE"
        if isinstance(period, int) and period > 2:
            return "CYCLE"
        return "RECURRENT"
    if stop == "NULL_AT_OBSERVED_STATE":
        return "ABSORBING"
    return "UNCLASSIFIED"
_OPAQUE_ACTION = re.compile(r"^ACTION([0-9]+)$")


class GateContractError(ValueError):
    """The proposed operation is not admissible in the current gate state."""


@dataclass(frozen=True)
class ActionAffordance:
    action: str
    requires_coordinates: bool


@dataclass(frozen=True)
class CoverageItem:
    coverage_id: str
    action: str
    row: int | None = None
    col: int | None = None
    probe_kind: str = "SIMPLE_PAIR"
    target_class_id: str | None = None
    target_member_id: str | None = None
    selection_reason: str | None = None
    observed: bool = False
    evidence_id: str | None = None

    def action_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"action": self.action}
        if self.row is not None and self.col is not None:
            payload.update(row=self.row, col=self.col)
        return payload


@dataclass(frozen=True)
class ProbeEnvelope:
    probe_id: str
    gate_id: str
    purpose: str
    question: str
    actions: tuple[dict[str, Any], ...]
    live_alternatives: tuple[str, ...]
    outcome_partition: tuple[str, ...]
    declared_at_transition: int
    admissible_actions: tuple[str, ...] = ()
    target: Mapping[str, Any] | None = None
    pilot_intent: str | None = None
    # G4-A guided actions: Duck's optional free-text statement of what the action is for.
    intent: str | None = None


@dataclass(frozen=True)
class GateAnswer:
    answer_id: str
    answer_kind: str
    subjects: tuple[str, ...]
    mechanism: str
    action_laws: Mapping[str, str]
    conditions: tuple[str, ...]
    constraints: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    novel_prediction: Mapping[str, Any]
    limitations: tuple[str, ...]
    # Lossless machine-readable action-law fields.  The prose law remains the
    # explanatory contract; this record lets the NAV controller consume only
    # displacements Duck actually declared and G1 subsequently demonstrated.
    action_law_specs: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionMetadataAnswer:
    answer_id: str
    action_metadata: tuple[ActionAffordance, ...]
    semantic_claims: tuple[str, ...]
    epistemic_limit: str


@dataclass(frozen=True)
class CounterAnswer:
    answer_id: str
    candidate_id: str
    tracked_variable: str
    mechanism: str
    bookkeeping_reason: str
    conditions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]
    novel_prediction: Mapping[str, Any]
    # Axiom A1 (v2): what makes the counter tick, and it must agree with the whole record.
    trigger: str = "UNSPECIFIED"


@dataclass(frozen=True)
class CounterModel:
    model_id: str
    revision: int
    status: str
    tracked_variable: str
    mechanism: str
    bookkeeping_reason: str
    conditions: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    competing_models: tuple[str, ...]
    falsifier: str
    limitations: tuple[str, ...]
    candidate_id: str
    demonstration_ref: str
    boundary_ref: str
    boundary_kind: str
    tracked_variable_status: str = "DUCK_HYPOTHESIS_NOT_IDENTIFIED_BY_RECURRENCE"
    trigger: str = "UNSPECIFIED"


def _opaque_action_name(value: Any) -> str:
    name = str(value or "").strip().upper()
    match = _OPAQUE_ACTION.fullmatch(name)
    if not match:
        raise GateContractError(
            f"Gated mode accepts opaque ACTION<number> names only; received {value!r}."
        )
    return name


def _action_number(name: str) -> int:
    match = _OPAQUE_ACTION.fullmatch(name)
    assert match is not None
    return int(match.group(1))


def action_affordances(actions: Iterable[Any]) -> tuple[ActionAffordance, ...]:
    """Represent the exact action surface without guessing world-specific effects."""
    unique = {_opaque_action_name(value) for value in actions}
    return tuple(
        ActionAffordance(action=name, requires_coordinates=_action_number(name) == 6)
        for name in sorted(unique, key=_action_number)
    )


def control_archetype_prior(
    affordances: Iterable[ActionAffordance],
) -> dict[str, Any]:
    """Translate the legal action surface into the supplied opening ontology."""
    names = {item.action for item in affordances}
    movement_channels = tuple(name for name in (f"ACTION{number}" for number in range(1, 5)) if name in names)
    has_pointer = "ACTION6" in names
    has_interaction = "ACTION5" in names
    if movement_channels and has_pointer:
        world_type = "HYBRID"
        ego_types = ("EMBODIED_EGO", "POINTER_GOD_MODE")
    elif movement_channels:
        world_type = "NAVIGATION"
        ego_types = ("EMBODIED_EGO",)
    elif has_pointer:
        world_type = "CLICK_GOD_MODE"
        ego_types = ("POINTER_GOD_MODE",)
    else:
        world_type = "UNKNOWN"
        ego_types = ()
    obligations: list[str] = []
    if movement_channels:
        obligations.append(
            "Localize the embodied ego; measure ACTION1-ACTION4 displacement, "
            "refusal, stride, and conditions."
        )
    if has_pointer:
        obligations.append(
            "Treat ACTION6 as Duck's hand; test valid targets, local and remote "
            "effects, and constraints."
        )
    if movement_channels and has_pointer:
        obligations.append(
            "Test whether ACTION6 activates the embodied ego; after an effective "
            "click, retest non-coordinate channels."
        )
    if has_interaction:
        obligations.append(
            "Treat ACTION5 as an extra interaction channel; learn its effect by pairs."
        )
    return {
        "source": "CONTROLLER_SUPPLIED_ACTION_SURFACE_ONTOLOGY",
        "world_type": world_type,
        "ego_types": list(ego_types),
        "movement_channel_candidates": list(movement_channels),
        "pointer_channel": "ACTION6" if has_pointer else None,
        "interaction_channel": "ACTION5" if has_interaction else None,
        "opening_obligations": obligations,
        "epistemic_limit": (
            "The roster supplies only the archetype. Ego identity and all exact action "
            "laws remain to be demonstrated."
        ),
    }


def _coordinate_coverage_item(
    candidate: CoordinateCandidate, *, selection_reason: str
) -> CoverageItem:
    suffix = candidate_digest(candidate)
    return CoverageItem(
        coverage_id=f"SITE-ACTION6-{candidate.class_id}-{candidate.member_id}-{suffix}",
        action="ACTION6",
        row=candidate.anchor[0],
        col=candidate.anchor[1],
        probe_kind="COORDINATE_CLASS",
        target_class_id=candidate.class_id,
        target_member_id=candidate.member_id,
        selection_reason=selection_reason,
    )


def _coverage(
    actions: tuple[ActionAffordance, ...],
    coordinate: AdaptiveCoordinateCoverage,
) -> tuple[CoverageItem, ...]:
    items: list[CoverageItem] = []
    for affordance in actions:
        number = _action_number(affordance.action)
        if number in {0, 6}:
            continue
        for repetition in (1, 2):
            items.append(CoverageItem(f"PAIR-{affordance.action}-{repetition}", affordance.action))
    if any(item.requires_coordinates for item in actions):
        items.extend(
            _coordinate_coverage_item(candidate, selection_reason="CLASS_REPRESENTATIVE")
            for candidate in coordinate.initial_representatives()
        )
    return tuple(items)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


class EgoGateMachine:
    """Deterministic G0/G1 state machine with stable gate identity."""

    def __init__(
        self,
        *,
        valid_actions: Iterable[Any],
        initial_grid: Sequence[Sequence[int]],
        observed_through_step: int = 0,
    ) -> None:
        self._initial_grid = tuple(tuple(int(cell) for cell in row) for row in initial_grid)
        self.affordances = action_affordances(valid_actions)
        self._currently_available = {item.action for item in self.affordances}
        self._coordinate_enabled = any(item.requires_coordinates for item in self.affordances)
        self.coordinate_coverage = AdaptiveCoordinateCoverage(self._initial_grid)
        self._control_archetype = control_archetype_prior(self.affordances)
        self.coverage = (
            ()
            if self._control_archetype["world_type"] == "CLICK_GOD_MODE"
            else _coverage(self.affordances, self.coordinate_coverage)
        )
        self._coverage_signatures: dict[str, str] = {}
        self._coverage_effects: dict[str, bool] = {}
        self.coverage_stop_reason: str | None = None
        self.revision = 1
        self.status = "ACTIVE" if self.coverage else "ANSWER_REQUIRED"
        self.coverage_stop_reason = (
            "ACTION_SURFACE_POINTER_EGO"
            if self._control_archetype["world_type"] == "CLICK_GOD_MODE"
            else None
        )
        self.observed_through_step = max(0, int(observed_through_step))
        self.answer: GateAnswer | None = None
        self.evidence: list[dict[str, Any]] = []
        self._lossless_outcomes: list[dict[str, Any]] = []
        self.reuse_events: list[dict[str, Any]] = []
        self._demonstration_attempted = False
        self.pending_prediction: ProspectivePrediction | None = None
        self.last_comparison: ScopedComparison | None = None
        self.ego_law: EgoLaw | None = None
        self._hybrid_activation_followup_added = False

    @property
    def gate_id(self) -> str:
        return GATE_ID

    def _unobserved(self) -> CoverageItem | None:
        return next(
            (item for item in self.coverage if not item.observed and item.action in self._currently_available),
            None,
        )

    def _settle_coverage(self) -> None:
        """Advance only the opening coverage state; never grade an ego claim."""
        if self._unobserved() is not None:
            self.status = "ACTIVE"
            self.coverage_stop_reason = None
            return
        adaptive = self.coordinate_coverage.next_adaptive() if self._coordinate_enabled else None
        if adaptive is not None and "ACTION6" in self._currently_available:
            candidate, reason = adaptive
            added = _coordinate_coverage_item(candidate, selection_reason=reason)
            if added.coverage_id not in {existing.coverage_id for existing in self.coverage}:
                self.coverage = (*self.coverage, added)
            self.status = "ACTIVE"
            self.coverage_stop_reason = None
            return
        if (
            self._coordinate_enabled
            and self.coordinate_coverage.state == "ACTIVE"
            and "ACTION6" not in self._currently_available
        ):
            self.status = "UNRESOLVED"
            self.coverage_stop_reason = "COORDINATE_ACTION_UNAVAILABLE"
        elif any(self._coverage_effects.values()):
            self.status = "ANSWER_REQUIRED"
            self.coverage_stop_reason = "DISCRIMINATING_EFFECT_OBSERVED"
        else:
            self.status = "UNRESOLVED"
            self.coverage_stop_reason = "REPRESENTATION_GAP_NO_VISIBLE_EFFECT"

    def _add_hybrid_activation_followup(self, after_coverage_id: str) -> None:
        """Retest simple channels after a visibly effective hybrid click."""
        if self._hybrid_activation_followup_added:
            return
        prior = control_archetype_prior(self.affordances)
        if prior["world_type"] != "HYBRID":
            return
        actions = [
            item.action
            for item in self.affordances
            if _action_number(item.action) in {1, 2, 3, 4, 5}
        ]
        followups = tuple(
            CoverageItem(
                coverage_id=f"POST-CLICK-PAIR-{action}-{repetition}",
                action=action,
                probe_kind="HYBRID_POST_CLICK_PAIR",
                selection_reason="TEST_POINTER_ACTIVATION",
            )
            for action in actions
            for repetition in (1, 2)
        )
        if not followups:
            return
        rebuilt: list[CoverageItem] = []
        for candidate in self.coverage:
            rebuilt.append(candidate)
            if candidate.coverage_id == after_coverage_id:
                rebuilt.extend(followups)
        self.coverage = tuple(rebuilt)
        self._hybrid_activation_followup_added = True

    def update_action_metadata(self, valid_actions: Iterable[Any]) -> None:
        """Refresh G0 from the live adapter and extend finite G1 coverage."""
        refreshed = action_affordances(valid_actions)
        refreshed_names = {item.action for item in refreshed}
        known_names = {item.action for item in self.affordances}
        additions = tuple(item for item in refreshed if item.action not in known_names)
        if additions:
            self.affordances = tuple(sorted((*self.affordances, *additions), key=lambda x: _action_number(x.action)))
            self._control_archetype = control_archetype_prior(self.affordances)
            existing_ids = {item.coverage_id for item in self.coverage}
            added_coverage = tuple(
                item for item in _coverage(additions, self.coordinate_coverage)
                if item.coverage_id not in existing_ids
            )
            self.coverage = (*self.coverage, *added_coverage)
            if self.status in {"ANSWER_REQUIRED", "DEMONSTRATION_REQUIRED", "UNRESOLVED", "CLOSED"}:
                self.answer = None
                self.status = "REOPENED"
            if any(item.requires_coordinates for item in additions):
                self._coordinate_enabled = True
        self._currently_available = refreshed_names
        if self.status in {"ACTIVE", "ANSWER_REQUIRED", "REOPENED", "UNRESOLVED"}:
            self._settle_coverage()
        self.revision += 1

    def next_probe(self) -> ProbeEnvelope | None:
        item = self._unobserved()
        if item is not None:
            return ProbeEnvelope(
                probe_id=f"{GATE_ID}:{item.coverage_id}",
                gate_id=GATE_ID,
                purpose="PROBE",
                question=(
                    "Which displayed cells, if any, are directly controlled by this opaque action?"
                    if item.probe_kind in {"SIMPLE_PAIR", "HYBRID_POST_CLICK_PAIR"}
                    else "Does this representative coordinate intervention reveal direct control?"
                ),
                actions=(item.action_payload(),),
                live_alternatives=(
                    (
                        "embodied direct control", "conditional or refused control",
                        "action-correlated environmental change", "no visible effect",
                    )
                    if item.probe_kind in {"SIMPLE_PAIR", "HYBRID_POST_CLICK_PAIR"}
                    else (
                        "pointer or god-mode control", "target-local response",
                        "remote or scheduled change", "no visible effect",
                    )
                ),
                outcome_partition=("changed", "unchanged", "terminal boundary"),
                declared_at_transition=self.observed_through_step,
            )
        if self.status == "DEMONSTRATION_REQUIRED" and self.answer is not None:
            prediction = dict(self.answer.novel_prediction)
            action = _normalize_action_payload(prediction.get("action"))
            return ProbeEnvelope(
                probe_id=f"{GATE_ID}:DEMONSTRATE:{self.answer.answer_id}",
                gate_id=GATE_ID,
                purpose="DEMONSTRATE",
                question="Does the explanatory ego model predict a new transition?",
                actions=(action,),
                live_alternatives=("prediction supported", "prediction contradicted"),
                outcome_partition=("changed", "unchanged", "terminal boundary"),
                declared_at_transition=self.observed_through_step,
            )
        return None

    def validate_probe(self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]) -> ProbeEnvelope:
        expected = self.next_probe()
        if expected is None:
            if self.status == "ANSWER_REQUIRED":
                raise GateContractError("G1 coverage is complete; submit a gate_answer before another action.")
            if self.status == "CLOSED":
                raise GateContractError("G1 is closed; no further G1 probe is admissible.")
            raise GateContractError(f"G1 has no admissible probe while status is {self.status}.")
        if not isinstance(decision, Mapping):
            raise GateContractError("Gated mode requires action(actions, decision={...}) with the current ProbeEnvelope.")
        supplied_actions = tuple(_normalize_action_payload(item) for item in actions)
        checks = {
            "probe_id": expected.probe_id,
            "gate_id": expected.gate_id,
            "purpose": expected.purpose,
            "question": expected.question,
            "live_alternatives": list(expected.live_alternatives),
            "outcome_partition": list(expected.outcome_partition),
        }
        for key, required in checks.items():
            if decision.get(key) != required:
                raise GateContractError(f"ProbeEnvelope mismatch for {key}; expected {required!r}.")
        if _canonical(supplied_actions) != _canonical(expected.actions):
            raise GateContractError(f"Only the next gated probe is admissible: {list(expected.actions)!r}.")
        return expected

    def record_outcome(self, probe: ProbeEnvelope, outcome: Mapping[str, Any]) -> dict[str, Any]:
        expected = self.next_probe()
        if expected is None or probe.probe_id != expected.probe_id:
            raise GateContractError("Outcome does not belong to the current probe.")
        self.observed_through_step = max(
            self.observed_through_step,
            int(outcome.get("transition_id") or outcome.get("action_num") or self.observed_through_step + 1),
        )
        self._lossless_outcomes.append(dict(outcome))
        stored_outcome = (
            compact_probe_outcome(outcome)
            if outcome.get("schema") == EVIDENCE_SCHEMA and "changed_cells" in outcome
            else dict(outcome)
        )
        digest = hashlib.sha256(
            _canonical({"probe_id": probe.probe_id, "outcome": stored_outcome}).encode("utf-8")
        ).hexdigest()[:16]
        evidence_id = f"E-{digest}"
        event = {
            "schema": SCHEMA_VERSION,
            "evidence_id": evidence_id,
            "gate_id": GATE_ID,
            "probe_id": probe.probe_id,
            "outcome": stored_outcome,
        }
        self.evidence.append(event)
        item = self._unobserved()
        if item is not None:
            changed_count = outcome.get("changed_cell_count")
            effect = bool(outcome.get("board_changed")) or (
                isinstance(changed_count, int) and changed_count > 0
            )
            signature_payload = {
                "effect": effect,
                "local": outcome.get("target_local_changed_cell_count"),
                "remote": outcome.get("remote_changed_cell_count"),
                "actions_after": sorted(str(value) for value in outcome.get("available_actions_after", ())),
            }
            self._coverage_signatures[item.coverage_id] = _canonical(signature_payload)
            self._coverage_effects[item.coverage_id] = effect
            if item.target_member_id is not None:
                self.coordinate_coverage.record(item.target_member_id, outcome)
            self.coverage = tuple(
                replace(candidate, observed=True, evidence_id=evidence_id)
                if candidate.coverage_id == item.coverage_id
                else candidate
                for candidate in self.coverage
            )
            if item.probe_kind == "COORDINATE_CLASS" and effect:
                self._add_hybrid_activation_followup(item.coverage_id)
            self._settle_coverage()
        elif self.status == "DEMONSTRATION_REQUIRED":
            if self.pending_prediction is None:
                raise GateContractError("Demonstration has no journaled prospective prediction.")
            self.last_comparison = compare_probe_outcome(self.pending_prediction, outcome)
            if self.last_comparison.outcome == "SUPPORTED":
                assert self.answer is not None
                self.ego_law = ego_law_from_supported(asdict(self.answer), self.last_comparison)
                self.status = "CLOSED"
            elif self.last_comparison.outcome == "CONTRADICTED":
                self.ego_law = None
                self.status = "REOPENED"
            else:
                self.ego_law = None
                self.status = "UNRESOLVED"
            self._demonstration_attempted = True
        # Persist the controller's actual post-observation assessment with the
        # event.  The offline evaluator must not have to reconstruct adaptive
        # coverage or re-run a scoped comparison from weaker prompt-facing data.
        event["gate_status_after"] = self.status
        event["coverage_certificate"] = self.coverage_certificate(include_unknown_members=False)
        if self.last_comparison is not None:
            event["demonstration_comparison"] = asdict(self.last_comparison)
        if self.ego_law is not None:
            event["ego_law"] = asdict(self.ego_law)
        self.revision += 1
        return event

    def current_grid(self) -> tuple[tuple[int, ...], ...]:
        """Reconstruct the latest visible frame from retained G1 transitions."""
        grid = [list(row) for row in self._initial_grid]
        for outcome in self._lossless_outcomes:
            for item in outcome.get("changed_cells") or ():
                if not isinstance(item, Mapping):
                    continue
                row, col = int(item["row"]), int(item["col"])
                after = item.get("after")
                if after is None or not (0 <= row < len(grid) and 0 <= col < len(grid[row])):
                    continue
                grid[row][col] = int(after)
        return tuple(tuple(row) for row in grid)

    def embodied_ego_binding(self) -> tuple[tuple[tuple[int, int], ...], str]:
        """Return Duck's demonstrated ego footprint and its evidence strength."""
        if self._control_archetype["world_type"] == "CLICK_GOD_MODE":
            return (), "POINTER_EGO_HAS_NO_GRID_FOOTPRINT"
        if self.last_comparison is not None and self.last_comparison.after_footprint:
            return tuple(self.last_comparison.after_footprint), "DEMONSTRATED_AFTER_FOOTPRINT"
        if self.pending_prediction is not None and self.pending_prediction.scope.cells:
            return tuple(self.pending_prediction.scope.cells), "DUCK_DECLARED_SCOPE_FALLBACK"
        return (), "EGO_FOOTPRINT_UNAVAILABLE"

    def submit_answer(self, raw: Mapping[str, Any]) -> GateAnswer:
        if self.status not in {"ANSWER_REQUIRED", "REOPENED", "UNRESOLVED"}:
            raise GateContractError(f"A G1 answer is not admissible while status is {self.status}.")
        pointer_exit = self._control_archetype["world_type"] == "CLICK_GOD_MODE"
        if self.status == "UNRESOLVED" and self.coverage_stop_reason is not None:
            raise GateContractError(
                "G1 coverage stopped at a representation gap; no evidence supports an ego-law demonstration."
            )
        answer = _answer_from_mapping(raw, interface_pointer=pointer_exit)
        if pointer_exit:
            normalized_kind = answer.answer_kind.upper().replace("-", "_").replace(" ", "_")
            if normalized_kind not in {"POINTER_GOD_MODE", "CLICK_GOD_MODE", "POINTER_EGO"}:
                raise GateContractError(
                    "Click-only G1 must explain the ego as POINTER_GOD_MODE."
                )
            if set(answer.action_laws) != {"ACTION6"}:
                raise GateContractError(
                    "Click-only G1 must explain ACTION6 as the site-selecting control locus."
                )
            self.answer = answer
            self.pending_prediction = None
            self.last_comparison = None
            self.ego_law = ego_law_from_interface(asdict(answer), prerequisite_ref=ACTION_METADATA_GATE_ID)
            self.status = "CLOSED"
            self.revision += 1
            return answer
        known_evidence = {str(item["evidence_id"]) for item in self.evidence}
        if not answer.evidence_refs or not set(answer.evidence_refs) <= known_evidence:
            raise GateContractError("The answer must cite only observed G1 evidence IDs and cite at least one.")
        available = {item.action for item in self.affordances}
        if not answer.action_laws or not set(answer.action_laws) <= available:
            raise GateContractError("action_laws must explain one or more currently available opaque actions.")
        prediction_action = _normalize_action_payload(answer.novel_prediction.get("action"))
        if prediction_action["action"] not in available:
            raise GateContractError("The novel prediction must use a currently available opaque action.")
        scope = answer.novel_prediction.get("scope")
        novelty = str(answer.novel_prediction.get("novelty") or "").strip()
        because = str(answer.novel_prediction.get("because") or "").strip()
        if not isinstance(scope, Mapping) or not scope:
            raise GateContractError("novel_prediction.scope must name the observable comparison scope.")
        if len(novelty.split()) < 3 or len(because.split()) < 3:
            raise GateContractError(
                "The prediction must say why it follows from the model and what makes this future test novel."
            )
        try:
            self.pending_prediction = prediction_from_mapping({
                "probe_id": f"{GATE_ID}:DEMONSTRATE:{answer.answer_id}",
                "declared_at_transition": self.observed_through_step,
                "action": prediction_action,
                "scope": scope,
                "predicate": answer.novel_prediction.get("predicate"),
                "expected_parameters": answer.novel_prediction.get("expected_parameters", {}),
                "evidence_basis": answer.evidence_refs,
                "falsifier": answer.falsifier,
            })
        except ValueError as exc:
            raise GateContractError(str(exc)) from exc
        self.answer = answer
        self.last_comparison = None
        self.ego_law = None
        self.status = "DEMONSTRATION_REQUIRED"
        self.revision += 1
        return answer

    def record_reuse(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        """Record a later decision's explicit use of the demonstrated ego law."""
        if self.status != "CLOSED" or self.answer is None or self.ego_law is None:
            raise GateContractError("An ego law can be reused only after G1 closes by demonstration.")
        decision_id = str(raw.get("decision_id") or "").strip()
        law_id = str(raw.get("law_id") or "").strip()
        action = _opaque_action_name(raw.get("action"))
        use = str(raw.get("use") or "").strip()
        if not decision_id or law_id != self.ego_law.law_id:
            raise GateContractError("Reuse must name a later decision and the active EgoLaw law_id.")
        if action not in self.answer.action_laws:
            raise GateContractError("Reuse must cite an action law from the closed ego answer.")
        if len(use.split()) < 4:
            raise GateContractError("Reuse must explain how the cited action law enables the later decision.")
        event = {
            "schema": SCHEMA_VERSION,
            "gate_id": GATE_ID,
            "law_id": law_id,
            "law_version_id": self.ego_law.law_version_id,
            "decision_id": decision_id,
            "action": action,
            "use": use,
            "observed_through_step": self.observed_through_step,
        }
        self.reuse_events.append(event)
        self.revision += 1
        return event

    def snapshot(self) -> dict[str, Any]:
        probe = self.next_probe()
        return {
            "schema": SCHEMA_VERSION,
            "gate_id": GATE_ID,
            "gate_kind": "EGO_DIRECT_INFLUENCE",
            "revision": self.revision,
            "status": self.status,
            "question": "What is the ego, and how does each directly controlling action move or alter it?",
            "prerequisites": ["G0-ACTION-METADATA"],
            "action_metadata": [asdict(item) for item in self.affordances],
            "control_archetype_prior": control_archetype_prior(self.affordances),
            "coverage": [asdict(item) for item in self.coverage],
            "coverage_certificate": self.coverage_certificate(include_unknown_members=False),
            "evidence_ids": [item["evidence_id"] for item in self.evidence],
            "answer": asdict(self.answer) if self.answer is not None else None,
            "pending_prediction": (
                asdict(self.pending_prediction) if self.pending_prediction is not None else None
            ),
            "last_comparison": (asdict(self.last_comparison) if self.last_comparison is not None else None),
            "ego_law": asdict(self.ego_law) if self.ego_law is not None else None,
            "next_probe": asdict(probe) if probe is not None else None,
            "next_gate_id": "G2-COUNTER" if self.status == "CLOSED" else None,
            "reuse_events": list(self.reuse_events),
        }

    def coverage_certificate(self, *, include_unknown_members: bool) -> dict[str, Any]:
        simple_rows = []
        for action in sorted(
            {item.action for item in self.coverage if item.probe_kind == "SIMPLE_PAIR"},
            key=_action_number,
        ):
            items = [
                item for item in self.coverage
                if item.probe_kind == "SIMPLE_PAIR" and item.action == action
            ]
            signatures = sorted(
                {
                    self._coverage_signatures[item.coverage_id]
                    for item in items
                    if item.coverage_id in self._coverage_signatures
                }
            )
            simple_rows.append({
                "action": action,
                "required_presses": 2,
                "observed_presses": sum(item.observed for item in items),
                "effect_observed": any(self._coverage_effects.get(item.coverage_id, False) for item in items),
                "outcomes_consistent": len(signatures) <= 1,
            })
        coordinate = (
            {
                "schema": "virelai-g1-coordinate-coverage-v1",
                "state": "DEFERRED_TO_LATER_TARGETS",
                "candidate_count": len(self.coordinate_coverage.candidates),
                "class_count": len(self.coordinate_coverage.classes),
                "tested_count": 0,
                "unknown_count": len(self.coordinate_coverage.candidates),
                "effect_observed": False,
                "class_status_counts": {"DEFERRED": len(self.coordinate_coverage.classes)},
            }
            if self._control_archetype["world_type"] == "CLICK_GOD_MODE"
            else
            self.coordinate_coverage.certificate(include_unknown_members=include_unknown_members)
            if self._coordinate_enabled
            else {
                "schema": "virelai-g1-coordinate-coverage-v1",
                "state": "NOT_APPLICABLE",
                "candidate_count": 0,
                "class_count": 0,
                "tested_count": 0,
                "unknown_count": 0,
                "effect_observed": False,
                "class_status_counts": {},
            }
        )
        activation_rows = []
        for action in sorted(
            {
                item.action
                for item in self.coverage
                if item.probe_kind == "HYBRID_POST_CLICK_PAIR"
            },
            key=_action_number,
        ):
            items = [
                item
                for item in self.coverage
                if item.probe_kind == "HYBRID_POST_CLICK_PAIR" and item.action == action
            ]
            activation_rows.append({
                "action": action,
                "required_presses": 2,
                "observed_presses": sum(item.observed for item in items),
                "effect_observed": any(
                    self._coverage_effects.get(item.coverage_id, False) for item in items
                ),
                "selection_reason": "TEST_POINTER_ACTIVATION",
            })
        simple_effect = any(row["effect_observed"] for row in simple_rows)
        conditional_evidence = any(
            row["observed_presses"] >= 2 and not row["outcomes_consistent"]
            for row in simple_rows
        )
        coordinate_effect = bool(coordinate["effect_observed"])
        if simple_effect and coordinate_effect:
            observed_channels = "MIXED"
        elif simple_effect:
            observed_channels = "NON_COORDINATE_EFFECT"
        elif coordinate_effect:
            observed_channels = "COORDINATE_EFFECT"
        else:
            observed_channels = "NO_VISIBLE_EFFECT"
        live_alternatives: list[str] = []
        if simple_effect:
            live_alternatives.extend(
                ["embodied direct control", "non-coordinate remote or scheduled effect"]
            )
        if coordinate_effect:
            live_alternatives.extend(
                ["pointer or god-mode control", "coordinate-triggered remote or scheduled effect"]
            )
        if conditional_evidence:
            live_alternatives.append("conditional or refused control")
        if not live_alternatives:
            live_alternatives.extend(
                [
                    "control outside the tested states or current representation",
                    "no visible direct effect under tested probes",
                ]
            )
        return {
            "schema": "virelai-g1-coverage-certificate-v1",
            "state": self.status,
            "stop_reason": self.coverage_stop_reason,
            "observed_channels": observed_channels,
            "conditional_evidence": conditional_evidence,
            "live_alternatives": list(dict.fromkeys(live_alternatives)),
            "simple_action_pairs": simple_rows,
            "hybrid_post_click_pairs": activation_rows,
            "coordinate": coordinate,
            "inertness_claim_permitted": False,
            "epistemic_limit": (
                "A negative probe applies only to its action, site, and observed state; "
                "unknown class members remain explicit."
            ),
        }


class CounterGateMachine:
    """G2: discover, explain, and prospectively verify bookkeeping noise."""

    def __init__(
        self,
        *,
        affordances: Sequence[ActionAffordance],
        initial_grid: Sequence[Sequence[int]],
        observed_through_step: int,
        excluded_ego_cells: Sequence[tuple[int, int]] = (),
        ego_binding_source: str = "NOT_APPLICABLE",
    ) -> None:
        self.affordances = tuple(affordances)
        self.initial_grid = tuple(tuple(int(cell) for cell in row) for row in initial_grid)
        self.observed_through_step = int(observed_through_step)
        self.revision = 1
        self.status = "ACTIVE"
        self.stop_reason: str | None = None
        self.evidence: list[dict[str, Any]] = []
        self._lossless_outcomes: list[dict[str, Any]] = []
        self._world_type = control_archetype_prior(self.affordances)["world_type"]
        self._visual_roster = AdaptiveCoordinateCoverage(self.initial_grid)
        self._excluded_ego_cells = frozenset((int(row), int(col)) for row, col in excluded_ego_cells)
        self._ego_binding_source = str(ego_binding_source)
        self._ranked_visual_targets = tuple(
            item
            for item in self._visual_roster.ranked_candidates()
            if not (
                self._world_type in {"NAVIGATION", "HYBRID"}
                and (
                    item.scale == "FIELD"
                    or bool(set(item.cells) & self._excluded_ego_cells)
                )
            )
        )
        self._movement_actions = tuple(
            item.action
            for item in self.affordances
            if _action_number(item.action) in {1, 2, 3, 4, 5}
        )
        self._navigation_steps_for_target = 0
        self._navigation_step_limit = 24
        self._navigation_results: list[dict[str, Any]] = []
        self._probe_actions = self._build_probe_actions()
        self._probe_index = 0
        self._probe_serial = 0
        self._counter_only_action: dict[str, Any] | None = None
        # Counter axiom (DOCTRINE_FRICTION_AXIOMS_v1, A1): in CLICK worlds G2 is a stated
        # target -- find the counter, label its law, mask it -- and Duck chooses the actions.
        self._guided = self._world_type == "CLICK_GOD_MODE"
        self._clicked_cells: set[tuple[int, int]] = set()
        self._rejected_candidates: list[dict[str, Any]] = []
        self._prediction_predicate: str = "COUNTER_REWRITE"
        self.candidate: CounterCandidate | None = None
        self.answer: CounterAnswer | None = None
        self.pending_prediction: CounterPrediction | None = None
        self.last_comparison: CounterComparison | None = None
        self.counter_model: CounterModel | None = None
        self.mask_law: MaskLaw | None = None
        self.boundary_confirmation: CounterBoundary | None = None
        self.boundary_obligation: dict[str, Any] | None = None
        self.search_disposition: dict[str, Any] | None = None
        self._prior_standing: tuple[int, int] | None = None
        self.state_archive: MaskedStateArchive | None = None

    def _build_probe_actions(self) -> tuple[dict[str, Any], ...]:
        if self._world_type == "CLICK_GOD_MODE":
            # Captain click arm: enumerate every visual component once in the
            # shared strict ranking. G2 may pause the sweep to explain and mask
            # a counter; later gates resume the same roster for lever discovery.
            return tuple(
                {"action": "ACTION6", "row": item.anchor[0], "col": item.anchor[1]}
                for item in self._ranked_visual_targets
            )

        if self._world_type in {"NAVIGATION", "HYBRID"} and self._movement_actions:
            # Duck chooses individual piloting actions while the controller
            # binds the next ranked target and owns completion of the list.
            return ()
        self.status = "UNRESOLVED"
        self.stop_reason = "EMBODIED_PILOT_ACTION_UNAVAILABLE"
        return ()

    def _ranked_target(self) -> CoordinateCandidate | None:
        ranked = self._ranked_visual_targets
        if self._probe_index >= len(ranked):
            return None
        return ranked[self._probe_index]

    @staticmethod
    def _target_payload(candidate: CoordinateCandidate) -> dict[str, Any]:
        return {
            "member_id": candidate.member_id,
            "rank": None,
            "anchor": list(candidate.anchor),
            "bbox": list(candidate.bbox),
            "cells": [list(cell) for cell in candidate.cells],
            "integer": candidate.integer,
            "cell_count": candidate.cell_count,
            "shape_family": candidate.shape_family,
        }

    def _current_action(self) -> dict[str, Any] | None:
        if self.status == "DEMONSTRATION_REQUIRED" and self.answer is not None:
            # Duck's own frozen choice: the prediction names the action it will take.
            return dict(self.answer.novel_prediction["action"])
        if (
            self.status in {"DEMONSTRATION_REQUIRED", "BOUNDARY_CONFIRMATION_REQUIRED"}
            and self._counter_only_action is not None
        ):
            return dict(self._counter_only_action)
        if self._guided:
            return None
        if self._probe_index < len(self._probe_actions):
            return self._probe_actions[self._probe_index]
        return None

    def answer_template(self) -> dict[str, Any] | None:
        """Return the exact evidence-bound G2 answer shape Duck must complete."""
        if self.candidate is None:
            return None
        default_action = self._counter_only_action or self._latest_witness_action()
        prediction = prediction_for(self.candidate, declared_at_transition=self.observed_through_step)
        return {
            "answer_id": "G2-COUNTER-EXPLANATION-1",
            "candidate_id": self.candidate.candidate_id,
            "trigger": self.record_trigger()["admissible_claims"][0],
            "tracked_variable": "Explain the visible quantity represented by the exchange.",
            "mechanism": "Explain the two-class rewrite, geometry, rate, and direction of progression.",
            "bookkeeping_reason": (
                "Explain why varied interventions support bookkeeping rather than a target effect."
            ),
            "conditions": [],
            "evidence_refs": list(self.candidate.witness_evidence_refs),
            "competing_models": ["State one evidence-compatible alternative."],
            "falsifier": "State what future observation would refute this counter model.",
            "limitations": ["The consequence at source minimum/replacement maximum is unobserved."],
            "novel_prediction": {
                "action": dict(default_action),
                "scope": {
                    "representation": "CELLS",
                    "cells": [list(cell) for cell in self.candidate.full_bar_footprint],
                },
                "predicate": "COUNTER_REWRITE",
                "expected_parameters": {
                    "rewrite": prediction.expected_rewrite,
                    "amount": prediction.expected_amount,
                },
                "because": "Explain why the observed recurrence predicts this future rewrite.",
                "novelty": "Explain why this is a prospective transition from a later state.",
            },
            "trigger_options": {
                "record": self.record_trigger(),
                "rule": (
                    "State what makes the counter tick. It must agree with the whole record: "
                    "EVERY_TRANSITION, EFFECTIVE_TRANSITIONS_ONLY (only when something else "
                    "changes), or IRREGULAR. When the record is OPEN either simple claim is "
                    "admissible, and a COUNTER_SILENT prediction on an action you expect to change "
                    "nothing would tell them apart."
                ),
            },
            "prediction_options": {
                "action": (
                    "Any one admissible action you choose. The prediction is scored only on the "
                    "counter footprint; changes elsewhere are recorded, not held against it."
                ),
                "predicate": {
                    "COUNTER_REWRITE": "the action will rewrite exactly `amount` footprint cells",
                    "COUNTER_SILENT": (
                        "the action will leave the footprint unchanged (for example, if your "
                        "label says the counter ticks only on effective actions); amount 0"
                    ),
                },
            },
        }

    def _latest_witness_action(self) -> dict[str, Any]:
        assert self.candidate is not None
        refs = set(self.candidate.witness_evidence_refs)
        for outcome in reversed(self._lossless_outcomes):
            action = outcome.get("action")
            if str(outcome.get("evidence_id") or "") in refs and isinstance(action, Mapping):
                return _normalize_action_payload(action)
        return {"action": self.affordances[0].action}

    def record_trigger(self) -> dict[str, Any]:
        """Axiom A1 (v2): the trigger class the whole record supports (``trigger_record``)."""
        assert self.candidate is not None
        return trigger_record(
            self._lossless_outcomes,
            set(self.candidate.full_bar_footprint) | set(self.candidate.observed_support),
        )

    def _trigger_disagreement(self, claim: str, record: Mapping[str, Any]) -> str:
        reasons = []
        if claim == "EVERY_TRANSITION" and record["null_transitions_without_tick"]:
            reasons.append(
                f"{record['null_transitions_without_tick']} transitions changed nothing and did "
                "not tick"
            )
        if claim in {"EVERY_TRANSITION", "EFFECTIVE_TRANSITIONS_ONLY"} and record[
            "effective_transitions_without_tick"
        ]:
            reasons.append(
                f"{record['effective_transitions_without_tick']} transitions changed the world "
                "without a tick"
            )
        if claim == "EFFECTIVE_TRANSITIONS_ONLY" and record["null_transitions_with_tick"]:
            reasons.append(
                f"{record['null_transitions_with_tick']} transitions ticked with no other change"
            )
        return "; ".join(reasons) or f"the record's trigger class is {record['class']}"

    def _purity_violations(self, candidate: CounterCandidate) -> list[str]:
        """Axiom A1 purity: the mask may neither swallow nor leak lever data.

        Every recorded change inside the footprint must follow the counter's own rewrite law
        (or its inverse, a refill), and no witness may have acted directly on the footprint.
        """
        footprint = set(candidate.full_bar_footprint) | set(candidate.observed_support)
        allowed = {
            (candidate.source_integer, candidate.replacement_integer),
            (candidate.replacement_integer, candidate.source_integer),
        }
        witness_refs = set(candidate.witness_evidence_refs)
        violations: list[str] = []
        remote_witness = False
        for outcome in self._lossless_outcomes:
            ref = str(outcome.get("evidence_id") or "")
            for item in outcome.get("changed_cells") or ():
                if not isinstance(item, Mapping):
                    continue
                cell = (int(item["row"]), int(item["col"]))
                if cell in footprint and (int(item["before"]), int(item["after"])) not in allowed:
                    violations.append(
                        f"{ref}: footprint cell {list(cell)} changed "
                        f"{item['before']}->{item['after']}, outside the counter law"
                    )
            if ref in witness_refs:
                acted = outcome.get("acted_site")
                acted_cell = (
                    (int(acted["row"]), int(acted["col"])) if isinstance(acted, Mapping) else None
                )
                if acted_cell is None or acted_cell not in footprint:
                    remote_witness = True
        if not remote_witness:
            # A counter must tick when acted on elsewhere; if every witness targeted the
            # footprint, the rewrite may be the footprint's own response (a lever), not bookkeeping.
            violations.append("every witness acted directly on the footprint; none was remote")
        return violations

    def _rank_prefix_observed(self) -> int:
        count = 0
        for item in self._ranked_visual_targets:
            if not (set(item.cells) & self._clicked_cells):
                break
            count += 1
        return count

    def _click_coverage_complete(self) -> bool:
        return all(set(item.cells) & self._clicked_cells for item in self._ranked_visual_targets)

    def _select_counter_only_action(self, candidate: CounterCandidate) -> dict[str, Any] | None:
        footprint = set(candidate.full_bar_footprint)
        witness_refs = set(candidate.witness_evidence_refs)
        for outcome in reversed(self._lossless_outcomes):
            if str(outcome.get("evidence_id") or "") not in witness_refs:
                continue
            changed = {
                (int(item["row"]), int(item["col"]))
                for item in outcome.get("changed_cells") or ()
                if isinstance(item, Mapping)
            }
            acted = outcome.get("acted_site")
            acted_cell = (
                (int(acted["row"]), int(acted["col"]))
                if isinstance(acted, Mapping) else None
            )
            action = outcome.get("action")
            if (
                changed
                and changed <= footprint
                and acted_cell not in footprint
                and isinstance(action, Mapping)
            ):
                return _normalize_action_payload(action)
        return None

    def next_probe(self) -> ProbeEnvelope | None:
        if self.status == "ACTIVE" and self._world_type in {"NAVIGATION", "HYBRID"}:
            candidate = self._ranked_target()
            if candidate is None:
                return None
            target = self._target_payload(candidate)
            target["rank"] = self._probe_index + 1
            return ProbeEnvelope(
                probe_id=f"{COUNTER_GATE_ID}:PILOT_TO_CONTACT:{self._probe_serial + 1}",
                gate_id=COUNTER_GATE_ID,
                purpose="PILOT_TO_CONTACT",
                question=(
                    "Pilot the demonstrated embodied ego toward the binding ranked object; "
                    "declare whether this step approaches it or deliberately attempts contact."
                ),
                actions=(),
                admissible_actions=self._movement_actions,
                target=target,
                live_alternatives=(
                    "ego advances toward the target",
                    "target responds on contact",
                    "contact is visibly refused",
                    "movement law or route needs revision",
                ),
                outcome_partition=(
                    "approach step", "target response", "refused contact",
                    "boundary event", "pilot budget exhausted",
                ),
                declared_at_transition=self.observed_through_step,
            )
        if self._guided and self.status == "ACTIVE":
            untried = [
                list(item.anchor) for item in self._ranked_visual_targets
                if not (set(item.cells) & self._clicked_cells)
            ]
            return ProbeEnvelope(
                probe_id=f"{COUNTER_GATE_ID}:GUIDED:{self._probe_serial + 1}",
                gate_id=COUNTER_GATE_ID,
                purpose="GUIDED_ACTION",
                question=COUNTER_TARGET,
                actions=(),
                admissible_actions=tuple(sorted({item.action for item in self.affordances})),
                live_alternatives=(
                    "a recurrent bookkeeping rewrite appears",
                    "a target-dependent effect appears",
                    "nothing visible changes",
                ),
                outcome_partition=("recorded",),
                declared_at_transition=self.observed_through_step,
                target={
                    "coverage_rule": (
                        "If no counter appears, G2 closes as not-observed only after every "
                        "ranked visual object has been clicked at least once."
                    ),
                    "untried_object_anchors": untried[:24],
                    "untried_count": len(untried),
                    "rejected_candidates": [
                        item["candidate_id"] for item in self._rejected_candidates
                    ],
                },
            )
        action = self._current_action()
        if action is None:
            return None
        if self.status == "DEMONSTRATION_REQUIRED":
            purpose = "DEMONSTRATE"
            question = "Does the proposed bookkeeping process recur on the next intervention?"
            alternatives = (
                "predicted bookkeeping rewrite recurs",
                "process holds, reverses, or changes rate",
                "target-dependent or causal effect replaces the pattern",
            )
        elif self.status == "BOUNDARY_CONFIRMATION_REQUIRED":
            purpose = "CONFIRM_BOUNDARY"
            question = "What occurs when the source reaches minimum and replacement reaches maximum?"
            alternatives = (
                "game over at counter extrema",
                "counter respawn after extrema",
                "counter continues without boundary consequence",
            )
        elif self.status == "ACTIVE":
            purpose = "PROBE"
            question = "Which visible changes recur independently of the chosen intervention?"
            alternatives = (
                "scheduled bookkeeping candidate",
                "target-dependent causal change",
                "ego or reaction change",
                "no visible change",
            )
        else:
            return None
        actions = (dict(action),)
        if self.status == "BOUNDARY_CONFIRMATION_REQUIRED":
            remaining = int((self.boundary_obligation or {}).get("source_after") or 1)
            batch_size = min(COUNTER_BOUNDARY_BATCH_MAX, max(1, remaining))
            actions = tuple(dict(action) for _ in range(batch_size))
        return ProbeEnvelope(
            probe_id=f"{COUNTER_GATE_ID}:{purpose}:{self._probe_serial + 1}",
            gate_id=COUNTER_GATE_ID,
            purpose=purpose,
            question=question,
            actions=actions,
            live_alternatives=alternatives,
            outcome_partition=("changed", "unchanged", "terminal boundary"),
            declared_at_transition=self.observed_through_step,
        )

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        expected = self.next_probe()
        if expected is None:
            if self.status == "ANSWER_REQUIRED":
                raise GateContractError("G2 has a candidate; submit its explanation before another action.")
            if self.status == "CLOSED":
                raise GateContractError("G2 is closed; no further G2 probe is admissible.")
            raise GateContractError(f"G2 has no admissible probe while status is {self.status}.")
        supplied = tuple(_normalize_action_payload(item) for item in actions)
        if expected.admissible_actions:
            if len(supplied) != 1 or supplied[0]["action"] not in expected.admissible_actions:
                raise GateContractError(
                    "The embodied pilot admits exactly one currently authorized opaque control: "
                    f"{list(expected.admissible_actions)!r}."
                )
            intent = str((decision or {}).get("pilot_intent") or "").strip().upper()
            if intent not in {"APPROACH", "CONTACT_ATTEMPT"}:
                raise GateContractError(
                    "Embodied piloting requires pilot_intent APPROACH or CONTACT_ATTEMPT."
                )
            return replace(expected, actions=supplied, pilot_intent=intent)
        if _canonical(supplied) != _canonical(expected.actions):
            raise GateContractError(f"Only the next gated G2 probe is admissible: {list(expected.actions)!r}.")
        return expected

    def _record_navigation_step(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any], *, evidence_id: str
    ) -> dict[str, Any] | None:
        candidate = self._ranked_target()
        if candidate is None:
            return None
        self._navigation_steps_for_target += 1
        target_cells = set(candidate.cells)
        changed_target_cells = sorted(
            (int(item["row"]), int(item["col"]))
            for item in outcome.get("changed_cells") or ()
            if isinstance(item, Mapping)
            and (int(item["row"]), int(item["col"])) in target_cells
        )
        boundary = outcome.get("boundary_event")
        terminal = isinstance(boundary, Mapping) and any(
            bool(boundary.get(key))
            for key in ("done", "level_completed", "game_over", "run_complete")
        )
        disposition = None
        attribution = None
        if changed_target_cells:
            disposition = "TARGET_RESPONDED"
            attribution = "DIRECT_TARGET_FOOTPRINT_DELTA"
        elif terminal:
            disposition = "BOUNDARY_DURING_TARGET_PURSUIT"
            attribution = "OBSERVED_BOUNDARY"
        elif probe.pilot_intent == "CONTACT_ATTEMPT" and not bool(outcome.get("board_changed")):
            disposition = "REFUSED_CONTACT_REPORTED"
            attribution = "DUCK_DECLARED_CONTACT_WITH_NO_VISIBLE_DELTA"
        elif self._navigation_steps_for_target >= self._navigation_step_limit:
            disposition = "PILOT_BUDGET_EXHAUSTED"
            attribution = "BOUNDED_WITHOUT_CONTACT_EVIDENCE"
        if disposition is None:
            return None
        row = {
            "member_id": candidate.member_id,
            "rank": self._probe_index + 1,
            "disposition": disposition,
            "attribution": attribution,
            "evidence_ref": evidence_id,
            "steps": self._navigation_steps_for_target,
            "changed_target_cells": [list(cell) for cell in changed_target_cells],
            "pilot_intent": probe.pilot_intent,
        }
        self._navigation_results.append(row)
        self._probe_index += 1
        self._navigation_steps_for_target = 0
        return row

    def _candidate_from_recent_suffix(self) -> CounterCandidate | None:
        best: CounterCandidate | None = None
        for start in range(max(0, len(self._lossless_outcomes) - 12), len(self._lossless_outcomes) - 1):
            found = compile_counter_candidates(self._lossless_outcomes[start:])
            for candidate in found:
                if best is None or len(candidate.witness_transition_ids) > len(best.witness_transition_ids):
                    best = candidate
        return best

    def _seal_state_archive(self) -> None:
        assert self.mask_law is not None
        self.state_archive = MaskedStateArchive(self.mask_law)
        for prior in self._lossless_outcomes:
            grids = grids_from_probe_outcome(prior)
            if grids is None:
                continue
            self.state_archive.record_transition(
                evidence_ref=str(prior.get("evidence_id") or ""),
                before=grids[0],
                after=grids[1],
            )

    def _record_supported_counter(self, outcome: Mapping[str, Any], evidence_id: str) -> None:
        assert self.answer is not None
        assert self.candidate is not None
        assert self.last_comparison is not None
        assert self.mask_law is not None
        standing = counter_standing(self.candidate, outcome)
        if standing is not None:
            self._prior_standing = standing
        boundary = compare_counter_boundary(
            self.candidate,
            outcome,
            evidence_ref=evidence_id,
            prior_standing=None,
        )
        self.boundary_confirmation = boundary
        locked = boundary.outcome == "SUPPORTED"
        self.counter_model = CounterModel(
            model_id=f"COUNTER-{self.candidate.candidate_id.split('-')[-1]}",
            revision=1,
            status=(
                "LOCKED_BY_EXTREMUM_BOUNDARY"
                if locked else "LOCKED_AS_MASK_BASELINE"
            ),
            tracked_variable=self.answer.tracked_variable,
            mechanism=self.answer.mechanism,
            bookkeeping_reason=self.answer.bookkeeping_reason,
            conditions=self.answer.conditions,
            evidence_refs=self.answer.evidence_refs,
            competing_models=self.answer.competing_models,
            falsifier=self.answer.falsifier,
            limitations=self.answer.limitations,
            candidate_id=self.candidate.candidate_id,
            demonstration_ref=self.last_comparison.evidence_ref,
            boundary_ref=evidence_id if locked else "",
            boundary_kind=(
                str(boundary.boundary_kind)
                if locked else "NOT_REQUIRED_AFTER_MASK_LOCK"
            ),
            trigger=self.answer.trigger,
        )
        # G2's only downstream job is to provide a stable subtraction mask.
        # Once the prediction succeeds, later counter ticks are deliberately
        # ignored.  They must not revise this product or reopen descendants.
        self.boundary_obligation = None
        self._seal_state_archive()
        # The reversible mask is G2's complete operational product. Productive
        # gates spend no further attention on the counter.
        self.status = "CLOSED"
        self.stop_reason = (
            "COUNTER_LOCKED_BY_MIN_MAX_BOUNDARY"
            if locked else "COUNTER_MASK_READY_BASELINE_LOCKED"
        )

    def _close_without_observed_counter(self, reason: str) -> None:
        self.search_disposition = {
            "status": "COUNTER_NOT_OBSERVED_WITHIN_OPENING",
            "reason": reason,
            "world_type": self._world_type,
            "probe_count": len(self.evidence),
            "evidence_refs": [str(item["evidence_id"]) for item in self.evidence],
            "scope": "BOUNDED_RANKED_OPENING_ONLY",
            "later_monitor_policy": "REOPEN_IF_A_RECURRENT_REMOTE_REWRITE_APPEARS",
            "epistemic_limit": (
                "No recurrent visible bookkeeping process was observed in the bounded opening; "
                "absence outside those actions and states is not claimed."
            ),
        }
        self.status = "CLOSED"
        self.stop_reason = "COUNTER_NOT_OBSERVED_WITHIN_OPENING"

    def monitor_later_transition(self, outcome: Mapping[str, Any]) -> dict[str, Any] | None:
        """Report the stable post-G2 ignore policy without revising knowledge."""
        if self.counter_model is None or self.mask_law is None:
            return None
        return {
            "schema": SCHEMA_VERSION,
            "gate_id": COUNTER_GATE_ID,
            "purpose": "STABLE_COUNTER_BASELINE",
            "policy": "MASK_AND_IGNORE_AFTER_G2",
            "transition_id": int(outcome.get("transition_id") or 0),
            "mask_law_ref": self.mask_law.law_version_id,
        }

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        expected = self.next_probe()
        if expected is None or probe.probe_id != expected.probe_id:
            raise GateContractError("Outcome does not belong to the current G2 probe.")
        self.observed_through_step = max(
            self.observed_through_step,
            int(outcome.get("transition_id") or self.observed_through_step + 1),
        )
        digest = hashlib.sha256(
            _canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()
        ).hexdigest()[:16]
        evidence_id = f"E-{digest}"
        lossless = dict(outcome)
        lossless["evidence_id"] = evidence_id
        self._lossless_outcomes.append(lossless)
        event = {
            "schema": SCHEMA_VERSION,
            "evidence_id": evidence_id,
            "gate_id": COUNTER_GATE_ID,
            "probe_id": probe.probe_id,
            "outcome": compact_probe_outcome(outcome),
        }
        self.evidence.append(event)
        self._probe_serial += 1
        if probe.purpose == "PROBE":
            self._probe_index += 1
        elif probe.purpose == "GUIDED_ACTION" or (self._guided and probe.purpose == "DEMONSTRATE"):
            for item in probe.actions:
                if "row" in item and "col" in item:
                    self._clicked_cells.add((int(item["row"]), int(item["col"])))
            self._probe_index = self._rank_prefix_observed()
        elif probe.purpose == "PILOT_TO_CONTACT":
            navigation_result = self._record_navigation_step(probe, outcome, evidence_id=evidence_id)
            if navigation_result is not None:
                event["navigation_target_result"] = navigation_result

        if self.status == "DEMONSTRATION_REQUIRED":
            assert self.pending_prediction is not None
            assert self.candidate is not None
            comparison = self._grade_counter_prediction(outcome, evidence_id)
            self.last_comparison = comparison
            violations = (
                self._purity_violations(self.candidate)
                if comparison.outcome == "SUPPORTED" else []
            )
            if comparison.outcome == "SUPPORTED" and not violations:
                self.mask_law = mask_law_from_supported(self.candidate, comparison)
                self._record_supported_counter(outcome, evidence_id)
            elif comparison.outcome == "SUPPORTED":
                self._reject_candidate("COUNTER_MASK_IMPURE", violations)
            elif comparison.outcome == "CONTRADICTED":
                self.answer = None
                self.pending_prediction = None
                self.candidate = None
                self.status = (
                    "ACTIVE" if self._guided or self._current_action() is not None
                    else "UNRESOLVED"
                )
                self.stop_reason = "COUNTER_PREDICTION_CONTRADICTED"
            else:
                self.status = "UNRESOLVED"
                self.stop_reason = "COUNTER_PREDICTION_INDETERMINATE"
        elif self.status == "BOUNDARY_CONFIRMATION_REQUIRED":
            assert self.candidate is not None
            boundary = compare_counter_boundary(
                self.candidate,
                outcome,
                evidence_ref=evidence_id,
                prior_standing=self._prior_standing,
            )
            self.boundary_confirmation = boundary
            standing = counter_standing(self.candidate, outcome)
            if standing is not None:
                self._prior_standing = standing
            if boundary.outcome == "SUPPORTED":
                assert self.counter_model is not None
                self.counter_model = replace(
                    self.counter_model,
                    revision=self.counter_model.revision + 1,
                    status="LOCKED_BY_EXTREMUM_BOUNDARY",
                    boundary_ref=evidence_id,
                    boundary_kind=str(boundary.boundary_kind),
                )
                self.boundary_obligation = None
                self.status = "CLOSED"
                self.stop_reason = "COUNTER_LOCKED_BY_MIN_MAX_BOUNDARY"
            else:
                assert self.boundary_obligation is not None
                self.boundary_obligation = {
                    **self.boundary_obligation,
                    "source_after": boundary.source_after,
                    "replacement_after": boundary.replacement_after,
                    "last_evidence_ref": evidence_id,
                }
                self.stop_reason = "RATE_SUPPORTED_AWAITING_MIN_MAX_BOUNDARY"
        else:
            self.candidate = self._candidate_from_recent_suffix()
            if self.candidate is not None and any(
                item["candidate_id"] == self.candidate.candidate_id
                for item in self._rejected_candidates
            ):
                self.candidate = None
            violations = [] if self.candidate is None else self._purity_violations(self.candidate)
            if self.candidate is not None and violations:
                self._reject_candidate("COUNTER_CANDIDATE_IMPURE", violations)
            elif self.candidate is not None:
                self._counter_only_action = self._select_counter_only_action(self.candidate)
                self.status = "ANSWER_REQUIRED"
                self.stop_reason = "RECURRENT_REMOTE_REWRITE_OBSERVED"
            elif self._guided and self._click_coverage_complete():
                self._close_without_observed_counter(
                    "NO_RECURRENT_PROCESS_AFTER_FULL_CLICK_COVERAGE"
                )
            elif self._world_type in {"NAVIGATION", "HYBRID"} and self._ranked_target() is None:
                self._close_without_observed_counter(
                    "NO_RECURRENT_PROCESS_AFTER_COLLISION_SWEEP"
                )
            elif (
                not self._guided
                and self._world_type == "CLICK_GOD_MODE"
                and self._current_action() is None
            ):
                self._close_without_observed_counter(
                    "NO_RECURRENT_PROCESS_IN_BOUNDED_PROBES"
                )
        event["gate_status_after"] = self.status
        if self.candidate is not None:
            event["counter_candidate"] = asdict(self.candidate)
        if self.last_comparison is not None:
            event["counter_comparison"] = asdict(self.last_comparison)
        if self.mask_law is not None:
            event["mask_law"] = asdict(self.mask_law)
        if self.boundary_confirmation is not None:
            event["counter_boundary"] = asdict(self.boundary_confirmation)
        if self.counter_model is not None:
            event["counter_model"] = asdict(self.counter_model)
        if self.boundary_obligation is not None:
            event["boundary_obligation"] = dict(self.boundary_obligation)
        if self.search_disposition is not None:
            event["search_disposition"] = dict(self.search_disposition)
        self.revision += 1
        return event

    def submit_answer(self, raw: Mapping[str, Any]) -> CounterAnswer:
        if self.status != "ANSWER_REQUIRED" or self.candidate is None:
            raise GateContractError(f"A G2 answer is not admissible while status is {self.status}.")
        if not isinstance(raw, Mapping):
            raise GateContractError("G2 gate_answer requires an answer object.")
        required = (
            "answer_id", "candidate_id", "tracked_variable", "mechanism",
            "bookkeeping_reason", "falsifier",
        )
        text = {name: str(raw.get(name) or "").strip() for name in required}
        missing = [name for name, value in text.items() if not value]
        if missing:
            raise GateContractError(f"G2 answer missing explanatory fields: {', '.join(missing)}.")
        if text["candidate_id"] != self.candidate.candidate_id:
            raise GateContractError("G2 answer must explain the active counter candidate.")
        if len(text["tracked_variable"].split()) < 3:
            raise GateContractError("tracked_variable must explain what visible quantity changes.")
        if len(text["mechanism"].split()) < 5 or len(text["bookkeeping_reason"].split()) < 5:
            raise GateContractError("G2 must explain both the visible mechanism and why it is bookkeeping.")
        refs = _strings(raw.get("evidence_refs"), "evidence_refs")
        if set(refs) != set(self.candidate.witness_evidence_refs):
            raise GateContractError("G2 evidence_refs must exactly cite the candidate witnesses.")
        record = self.record_trigger()
        trigger = str(raw.get("trigger") or "").strip().upper()
        if not trigger:
            raise GateContractError(
                "G2 answer requires trigger (what makes the counter tick): one of "
                f"{record['admissible_claims']!r}; the record supports {record['class']}."
            )
        if trigger not in record["admissible_claims"]:
            raise GateContractError(
                f"G2 trigger {trigger} disagrees with the record: "
                f"{self._trigger_disagreement(trigger, record)}. The record supports "
                f"{record['class']} (axiom A1: the label must agree with the whole record)."
            )
        raw_prediction = raw.get("novel_prediction")
        if not isinstance(raw_prediction, Mapping):
            raise GateContractError("G2 answer requires novel_prediction in the supplied template shape.")
        predicted_action = raw_prediction.get("action")
        if not isinstance(predicted_action, Mapping):
            predicted_action = {"action": predicted_action}
        predicted_action = _normalize_action_payload(predicted_action)
        if predicted_action["action"] not in {item.action for item in self.affordances}:
            raise GateContractError(
                "G2 novel_prediction.action must be one currently admissible action: "
                f"{sorted({item.action for item in self.affordances})!r}."
            )
        predicate = str(raw_prediction.get("predicate") or "")
        if predicate not in {"COUNTER_REWRITE", "COUNTER_SILENT"}:
            raise GateContractError(
                "G2 novel_prediction predicate must be COUNTER_REWRITE or COUNTER_SILENT."
            )
        scope = raw_prediction.get("scope")
        scope = scope if isinstance(scope, Mapping) else {}
        scope_cells = _coordinate_cells(
            scope.get("cells"), "novel_prediction.scope.cells"
        )
        if set(scope_cells) != set(self.candidate.full_bar_footprint):
            raise GateContractError("G2 prediction scope must exactly cover the candidate's full footprint.")
        expected_parameters = raw_prediction.get("expected_parameters")
        expected_parameters = expected_parameters if isinstance(expected_parameters, Mapping) else {}
        expected = prediction_for(
            self.candidate, declared_at_transition=self.observed_through_step
        )
        if str(expected_parameters.get("rewrite") or "") != expected.expected_rewrite:
            raise GateContractError("G2 predicted rewrite must match the observed candidate rewrite.")
        try:
            predicted_amount = int(expected_parameters.get("amount"))
        except (TypeError, ValueError) as exc:
            raise GateContractError("G2 predicted amount must be an integer.") from exc
        required_amount = 0 if predicate == "COUNTER_SILENT" else expected.expected_amount
        if predicted_amount != required_amount:
            raise GateContractError(
                "G2 predicted amount must be 0 for COUNTER_SILENT and the recurrent observed "
                "rate for COUNTER_REWRITE."
            )
        because = str(raw_prediction.get("because") or "").strip()
        novelty = str(raw_prediction.get("novelty") or "").strip()
        if len(because.split()) < 5 or len(novelty.split()) < 5:
            raise GateContractError("G2 novel_prediction must explain both its basis and prospectiveness.")
        canonical_prediction = {
            "action": dict(predicted_action),
            "scope": {
                "representation": "CELLS",
                "cells": [list(cell) for cell in sorted(scope_cells)],
            },
            "predicate": predicate,
            "expected_parameters": {
                "rewrite": expected.expected_rewrite,
                "amount": required_amount,
            },
            "because": because,
            "novelty": novelty,
        }
        answer = CounterAnswer(
            answer_id=text["answer_id"],
            candidate_id=text["candidate_id"],
            tracked_variable=text["tracked_variable"],
            mechanism=text["mechanism"],
            bookkeeping_reason=text["bookkeeping_reason"],
            conditions=_strings(raw.get("conditions", []), "conditions", required=False),
            evidence_refs=refs,
            competing_models=_strings(raw.get("competing_models"), "competing_models"),
            falsifier=text["falsifier"],
            limitations=_strings(raw.get("limitations", []), "limitations", required=False),
            novel_prediction=canonical_prediction,
            trigger=trigger,
        )
        self.answer = answer
        self._prediction_predicate = predicate
        self.pending_prediction = replace(expected, expected_amount=required_amount)
        self.status = "DEMONSTRATION_REQUIRED"
        self.stop_reason = None
        self.revision += 1
        return answer

    def _grade_counter_prediction(
        self, outcome: Mapping[str, Any], evidence_id: str
    ) -> CounterComparison:
        assert self.pending_prediction is not None and self.candidate is not None
        comparison = compare_counter_prediction(
            self.pending_prediction, outcome, evidence_ref=evidence_id
        )
        if self._prediction_predicate == "COUNTER_SILENT" and comparison.outcome == "SUPPORTED":
            footprint = set(self.candidate.full_bar_footprint) | set(self.candidate.observed_support)
            touched = [
                item for item in outcome.get("changed_cells") or ()
                if isinstance(item, Mapping)
                and (int(item["row"]), int(item["col"])) in footprint
            ]
            if touched:
                comparison = replace(comparison, outcome="CONTRADICTED", observed_amount=len(touched))
        return comparison

    def _reject_candidate(self, reason: str, violations: Sequence[str]) -> None:
        """A candidate that fails purity is recorded and dropped; the search continues."""
        assert self.candidate is not None
        self._rejected_candidates.append({
            "candidate_id": self.candidate.candidate_id,
            "reason": reason,
            "violations": list(violations)[:12],
        })
        self.candidate = None
        self.answer = None
        self.pending_prediction = None
        self.status = "ACTIVE" if self._guided or self._current_action() is not None else "UNRESOLVED"
        self.stop_reason = reason

    def snapshot(self) -> dict[str, Any]:
        current_target = None
        if self._probe_index < len(self._probe_actions):
            current_target = dict(self._probe_actions[self._probe_index])
        ranked_target = self._ranked_target()
        target_payload = (
            self._target_payload(ranked_target) if ranked_target is not None else None
        )
        if target_payload is not None:
            target_payload["rank"] = self._probe_index + 1
        roster_size = len(self._ranked_visual_targets)
        return {
            "schema": SCHEMA_VERSION,
            "gate_id": COUNTER_GATE_ID,
            "gate_kind": "COUNTER_AND_REVERSIBLE_MASK",
            "revision": self.revision,
            "status": self.status,
            "question": "Which visible process is bookkeeping noise, what does it track, and how can it be reversibly masked?",
            "opening_protocol": {
                "world_type": self._world_type,
                "sweep_arm": (
                    "CLICK_EVERYTHING"
                    if self._world_type == "CLICK_GOD_MODE"
                    else "COLLIDE_WITH_EVERYTHING"
                ),
                "ranking": [
                    "SMALLEST_FOOTPRINT",
                    "LOWEST_INTEGER",
                    "NEAREST_TOP_LEFT_MEMBER",
                    "COORDINATE_TIEBREAK",
                ],
                "enumeration_total": roster_size,
                "enumeration_observed": min(self._probe_index, roster_size),
                "current_target_action": current_target,
                "current_target": target_payload,
                "ego_binding_source": self._ego_binding_source,
                "excluded_ego_cells": [
                    list(cell) for cell in sorted(self._excluded_ego_cells)
                ],
                "excluded_structural_fields": self._world_type in {"NAVIGATION", "HYBRID"},
                "rank_is_semantics": False,
            },
            "navigation_results": list(self._navigation_results),
            "probe_progress": {
                "observed": len(self.evidence),
                "limit": (
                    len(self._probe_actions)
                    if self._world_type == "CLICK_GOD_MODE"
                    else roster_size * self._navigation_step_limit
                ),
            },
            "stop_reason": self.stop_reason,
            "evidence_ids": [item["evidence_id"] for item in self.evidence],
            "candidate": asdict(self.candidate) if self.candidate is not None else None,
            "answer": asdict(self.answer) if self.answer is not None else None,
            "pending_prediction": asdict(self.pending_prediction) if self.pending_prediction is not None else None,
            "last_comparison": asdict(self.last_comparison) if self.last_comparison is not None else None,
            "boundary_confirmation": (
                asdict(self.boundary_confirmation)
                if self.boundary_confirmation is not None else None
            ),
            "boundary_obligation": self.boundary_obligation,
            "search_disposition": self.search_disposition,
            "counter_model": asdict(self.counter_model) if self.counter_model is not None else None,
            "mask_law": asdict(self.mask_law) if self.mask_law is not None else None,
            "state_identity": (
                self.state_archive.snapshot() if self.state_archive is not None else None
            ),
            "next_probe": asdict(self.next_probe()) if self.next_probe() is not None else None,
            "next_gate_id": "G3-LEVERS" if self.status == "CLOSED" else None,
        }

    def sweep_frontier(self) -> dict[str, Any]:
        """Persist the shared object enumeration without counting confirmation detours."""
        candidates = self._ranked_visual_targets
        observed = min(self._probe_index, len(candidates))
        navigation_by_member = {
            str(item["member_id"]): item for item in self._navigation_results
        }
        return {
            "schema": "virelai-ranked-object-frontier-v1",
            "world_type": self._world_type,
            "sweep_arm": (
                "CLICK_EVERYTHING"
                if self._world_type == "CLICK_GOD_MODE"
                else "COLLIDE_WITH_EVERYTHING"
            ),
            "ego_binding_source": self._ego_binding_source,
            "excluded_ego_cells": [
                list(cell) for cell in sorted(self._excluded_ego_cells)
            ],
            "ranking": [
                "SMALLEST_FOOTPRINT",
                "LOWEST_INTEGER",
                "NEAREST_TOP_LEFT_MEMBER",
                "COORDINATE_TIEBREAK",
            ],
            "observed_count": observed,
            "candidate_count": len(candidates),
            "enumeration_complete": observed == len(candidates),
            "candidates": [
                {
                    "rank": rank,
                    "member_id": item.member_id,
                    "anchor": list(item.anchor),
                    "integer": item.integer,
                    "cell_count": item.cell_count,
                    "status": (
                        navigation_by_member[item.member_id]["disposition"]
                        if item.member_id in navigation_by_member
                        else "OBSERVED" if rank <= observed else "UNTRIED"
                    ),
                    "result": navigation_by_member.get(item.member_id),
                }
                for rank, item in enumerate(candidates, start=1)
            ],
        }


def _target_registry() -> TargetRegistry:
    registry = TargetRegistry()
    registry.register(GoalContract(
        goal_id="G0-ACTION-SURFACE-v1",
        target_id=ACTION_METADATA_GATE_ID,
        question="Which opaque actions are currently available, and which require coordinates?",
        desired_knowledge=("opaque action identities", "parameter requirements"),
        prerequisites=(),
        admissible_probe_kinds=(),
        completion_predicate=(
            "Exact action surface acknowledged without world-specific effect claims; "
            "the supplied control archetype is carried into G1."
        ),
        memory_product_type="ActionSurface",
    ))
    registry.register(GoalContract(
        goal_id="G1-EGO-v1",
        target_id=GATE_ID,
        question="Where and how does Duck directly influence the world?",
        desired_knowledge=("control mode", "controlled subject or locus", "opaque action laws"),
        prerequisites=(ACTION_METADATA_GATE_ID,),
        admissible_probe_kinds=(
            "consecutive simple-action pair",
            "representative coordinate intervention",
            "post-click activation pair in hybrid worlds",
            "prospective ego-law demonstration",
        ),
        completion_predicate=(
            "Archetype-specific sufficient explanation: interface-grounded pointer law for "
            "click-only worlds; demonstrated control law for embodied branches."
        ),
        memory_product_type="EgoLaw",
    ))
    registry.register(GoalContract(
        goal_id="G2-COUNTER-v1",
        target_id=COUNTER_GATE_ID,
        question=(
            "Which visible process is bookkeeping noise, what does it track, "
            "and how can it be reversibly masked?"
        ),
        desired_knowledge=(
            "recurrent visible process",
            "tracked visible variable",
            "bookkeeping explanation",
            "reversible mask scope",
        ),
        prerequisites=(GATE_ID,),
        admissible_probe_kinds=(
            "any action Duck chooses (CLICK worlds: stated target)",
            "varied intervention recurrence probe (embodied worlds)",
            "prospective footprint-scoped counter prediction",
        ),
        completion_predicate=(
            "Axiom A1: find, label, mask. Duck explains an evidence-bound recurrent bookkeeping "
            "process; the mask passes purity on the record (every footprint change follows the "
            "counter law, no witness acted on the footprint); a later transition supports one "
            "frozen footprint-scoped prediction on an action Duck chose; the mask becomes a stable "
            "ignored baseline. Or the complete coverage records that no counter was observed, "
            "without claiming global absence."
        ),
        memory_product_type="CounterGateProduct",
    ))
    registry.register(GoalContract(
        goal_id="G3-LEVER-INVENTORY-v1",
        target_id=LEVER_GATE_ID,
        question=(
            "Which contacted or clicked visual objects produce an attributed local or remote "
            "world change after ego and counter subtraction?"
        ),
        desired_knowledge=(
            "enumeration-complete interaction coverage",
            "attributed positive lever witnesses",
            "local versus remote effect scope",
            "unresolved and bounded-negative attempts",
        ),
        prerequisites=(COUNTER_GATE_ID,),
        admissible_probe_kinds=(
            "ranked click interaction",
            "embodied approach or contact attempt",
            "prospective lever-witness demonstration",
        ),
        completion_predicate=(
            "The inherited ranked frontier is exhausted without early stopping; every positive "
            "lever claim has an attributed ego/counter-masked witness and a later prospective "
            "demonstration. Null attempts remain scoped observations rather than inertness claims."
        ),
        memory_product_type="LeverInventory",
    ))
    registry.register(GoalContract(
        goal_id="G4-LEVER-REACTIONS-v1",
        target_id=REACTION_GATE_ID,
        question=(
            "For each confirmed lever, which subjects or regions changed and what exact "
            "visible transformation occurred?"
        ),
        desired_knowledge=(
            "G3-bound lever identity and intervention",
            "complete counter-masked effect anatomy",
            "local and remote affected regions",
            "exact observed integer transformations",
            "human mechanism explanation",
        ),
        prerequisites=(LEVER_GATE_ID,),
        admissible_probe_kinds=(),
        completion_predicate=(
            "Every G3-ready lever has a complete effect-channel partition and Duck explains "
            "each affected region and exact observed rewrite. Deeper reaction-law questions "
            "remain explicitly open for subsequent G4 slices."
        ),
        memory_product_type="LeverEffectAnatomySet",
    ))
    registry.register(GoalContract(
        goal_id="G4A-GUIDED-LEVER-STUDY-v1",
        target_id=ORBIT_GATE_ID,
        question=(
            "What does pressing each confirmed lever repeatedly do, up to a confirmed endpoint "
            "or recurrence?"
        ),
        desired_knowledge=(
            "complete counter-masked state sequence of a consecutive same-click run",
            "first observed null or exact recurrence, with its period",
            "confirmation: a second null, or one more full retraced cycle",
            "single-lever class from the lever's own run",
            "human explanation bounded to the observed run",
        ),
        prerequisites=(REACTION_GATE_ID,),
        admissible_probe_kinds=("any one valid action chosen by Duck (guided target)",),
        completion_predicate=(
            "Stated target, Duck-executed: every lever has a confirmed or diverged run read from "
            "Duck's own consecutive presses, plus an accepted explanation. Boundary-interrupted "
            "levers are released; a level change closes the level's study (G9 owns transfer). "
            "The controller never selects Duck's next action."
        ),
        memory_product_type="LeverOrbitSet",
    ))
    # G4.3-LEVER-LIMITS is retired (Director ruling 2026-09-27). Persistence and reversal are
    # Duck-frozen predictions in G4-B (R9-R12); G4-C tests the description (R9-R13, g4c_gate.py).
    from inference.framework.g4c_gate import later_contracts

    for contract in later_contracts():
        registry.register(contract)
    return registry


class _ActionSurfaceTarget:
    """G0 adapter: preserve the proven checkpoint behind the generic router."""

    def __init__(self, machine: "CyberneticGateMachine") -> None:
        self.machine = machine
        self.answer: ActionMetadataAnswer | None = None
        self.revision = 1

    @property
    def status(self) -> str:
        return self.assess().disposition

    def assess(self) -> GateAssessment:
        return GateAssessment(
            target_id=ACTION_METADATA_GATE_ID,
            revision=self.revision,
            disposition="ANSWER_REQUIRED" if self.answer is None else "SATISFIED",
            unmet_requirements=("exact opaque ActionSurface answer",) if self.answer is None else (),
            explanation=(
                "Duck must acknowledge the current opaque action surface before any probe."
                if self.answer is None
                else "The current opaque action surface is represented without semantic claims."
            ),
        )

    def next_probe(self) -> ProbeEnvelope | None:
        return None

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        del decision, actions
        raise GateContractError(
            "G0 action metadata is unanswered; submit gate_answer before any environment action."
        )

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        del probe, outcome
        raise GateContractError("G0 admits no environment action.")

    def submit_answer(self, raw: Mapping[str, Any]) -> ActionMetadataAnswer:
        if not isinstance(raw, Mapping):
            raise GateContractError("G0 gate_answer requires an answer object.")
        answer_id = str(raw.get("answer_id") or "").strip()
        if not answer_id:
            raise GateContractError("G0 answer_id is required.")
        supplied_raw = raw.get("action_metadata")
        if not isinstance(supplied_raw, (list, tuple)):
            raise GateContractError("G0 action_metadata must list every displayed action affordance.")
        supplied: list[ActionAffordance] = []
        for item in supplied_raw:
            if not isinstance(item, Mapping):
                raise GateContractError("Each G0 action_metadata entry must be an object.")
            name = _opaque_action_name(item.get("action"))
            required = item.get("requires_coordinates")
            if not isinstance(required, bool):
                raise GateContractError("requires_coordinates must be a boolean supplied by the interface.")
            supplied.append(ActionAffordance(name, required))
        supplied_tuple = tuple(sorted(supplied, key=lambda item: _action_number(item.action)))
        if supplied_tuple != self.machine.ego.affordances:
            raise GateContractError(
                "G0 action_metadata must exactly match the current opaque action surface and parameter requirements."
            )
        semantic_claims = _strings(raw.get("semantic_claims", []), "semantic_claims", required=False)
        if semantic_claims:
            raise GateContractError("G0 cannot assign semantic effects to action numbers before probing.")
        epistemic_limit = str(raw.get("epistemic_limit") or "").strip()
        if len(epistemic_limit.split()) < 5:
            raise GateContractError(
                "G0 epistemic_limit must state that action effects remain unknown until observed."
            )
        answer = ActionMetadataAnswer(
            answer_id=answer_id,
            action_metadata=supplied_tuple,
            semantic_claims=semantic_claims,
            epistemic_limit=epistemic_limit,
        )
        self.answer = answer
        self.revision += 1
        self.machine.target_journal.put(MemoryProduct(
            product_id=answer.answer_id,
            product_type="ActionSurface",
            target_id=ACTION_METADATA_GATE_ID,
            revision=self.revision,
            payload=asdict(answer),
        ))
        return answer

    def invalidate(self) -> None:
        self.answer = None
        self.revision += 1
        self.machine.target_journal.invalidate(ACTION_METADATA_GATE_ID, include_self=True)

    def snapshot(self) -> dict[str, Any]:
        contract = self.machine.target_registry.get(ACTION_METADATA_GATE_ID)
        return {
            "schema": SCHEMA_VERSION,
            "gate_id": ACTION_METADATA_GATE_ID,
            "gate_kind": "ACTION_METADATA",
            "revision": self.revision,
            "status": self.status,
            "question": contract.question,
            "goal_card": contract.goal_card(status=self.status),
            "action_metadata": [asdict(item) for item in self.machine.ego.affordances],
            "control_archetype_prior": control_archetype_prior(
                self.machine.ego.affordances
            ),
            "answer_requirements": {
                "answer_id": "non-empty",
                "action_metadata": "exact copy of the current action metadata",
                "semantic_claims": "must be empty before probing",
                "epistemic_limit": "state that effects remain unknown until observed",
            },
            "next_probe": None,
            "next_gate_id": GATE_ID,
        }


class _EgoTarget:
    """Adapter for the existing G1 implementation; G1 behavior is hardened later."""

    def __init__(self, machine: "CyberneticGateMachine") -> None:
        self.machine = machine

    @property
    def status(self) -> str:
        return self.assess().disposition

    def assess(self) -> GateAssessment:
        status = "SATISFIED" if self.machine.ego.status == "CLOSED" else self.machine.ego.status
        unmet: tuple[str, ...]
        if status in {"ACTIVE", "REOPENED"}:
            unmet = ("complete discriminating ego probes",)
        elif status == "ANSWER_REQUIRED":
            if self.machine.ego._control_archetype["world_type"] == "CLICK_GOD_MODE":
                unmet = (
                    "explain the pointer ego, coordinate-locus movement, and G1 scope boundary",
                )
            else:
                unmet = ("submit evidence-bound ego explanation and prospective prediction",)
        elif status == "DEMONSTRATION_REQUIRED":
            unmet = ("execute and support the prospective ego prediction",)
        elif status == "UNRESOLVED":
            if self.machine.ego.coverage_stop_reason is not None:
                unmet = (
                    "obtain a discriminating observation or improve the available representation",
                )
            else:
                unmet = ("repair the unresolved demonstration scope or boundary and resubmit",)
        else:
            unmet = ()
        return GateAssessment(
            target_id=GATE_ID,
            revision=self.machine.ego.revision,
            disposition=status,
            evidence_refs=tuple(str(item["evidence_id"]) for item in self.machine.ego.evidence),
            unmet_requirements=unmet,
            explanation=(
                "G1 closes as soon as its archetype-specific ego question is sufficiently answered."
            ),
        )

    def next_probe(self) -> ProbeEnvelope | None:
        return self.machine.ego.next_probe()

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        return self.machine.ego.validate_probe(decision, actions)

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        event = self.machine.ego.record_outcome(probe, outcome)
        self._sync_product()
        return event

    def submit_answer(self, raw: Mapping[str, Any]) -> GateAnswer:
        answer = self.machine.ego.submit_answer(raw)
        self._sync_product()
        return answer

    def _sync_product(self) -> None:
        law = self.machine.ego.ego_law
        if self.machine.ego.status == "CLOSED" and law is not None:
            self.machine._prepare_counter_from_ego()
            self.machine.target_journal.put(MemoryProduct(
                product_id=law.law_id,
                product_type="EgoLaw",
                target_id=GATE_ID,
                revision=self.machine.ego.revision,
                payload=asdict(law),
                dependencies=(ACTION_METADATA_GATE_ID,),
            ))
        elif self.machine.ego.status in {"REOPENED", "UNRESOLVED"}:
            self.machine.target_journal.invalidate(GATE_ID, include_self=True)

    def snapshot(self) -> dict[str, Any]:
        snapshot = self.machine.ego.snapshot()
        contract = self.machine.target_registry.get(GATE_ID)
        snapshot["goal_card"] = contract.goal_card(status=self.status)
        snapshot["completed_gates"] = self.machine.completed_gate_rows()
        return snapshot


class _CounterTarget:
    def __init__(self, machine: "CyberneticGateMachine") -> None:
        self.machine = machine

    @property
    def counter(self) -> CounterGateMachine:
        return self.machine.counter

    def _sync_step(self) -> None:
        self.counter.observed_through_step = max(
            self.counter.observed_through_step, self.machine.ego.observed_through_step
        )

    def assess(self) -> GateAssessment:
        self._sync_step()
        status = "SATISFIED" if self.counter.status == "CLOSED" else self.counter.status
        unmet = {
            "ACTIVE": (
                ("find a counter: act as you choose; the controller detects recurrent "
                 "bookkeeping rewrites and checks purity")
                if self.counter._guided else "complete bounded recurrence probes",
            ),
            "ANSWER_REQUIRED": ("explain what the candidate tracks and why it is bookkeeping",),
            "DEMONSTRATION_REQUIRED": ("execute the prospective counter-law demonstration",),
            "BOUNDARY_CONFIRMATION_REQUIRED": (
                "observe game-over or respawn at source minimum and replacement maximum",
            ),
            "UNRESOLVED": ("repair or extend the counter representation",),
        }.get(status, ())
        return GateAssessment(
            target_id=COUNTER_GATE_ID,
            revision=self.counter.revision,
            disposition=status,
            evidence_refs=tuple(item["evidence_id"] for item in self.counter.evidence),
            unmet_requirements=unmet,
            explanation=(
                "G2 closes after a supported recurrent process receives a reversible mask; "
                "its extremum consequence remains a background obligation, or "
                "after the complete bounded opening records that no counter was observed."
            ),
        )

    def next_probe(self) -> ProbeEnvelope | None:
        self._sync_step()
        return self.counter.next_probe()

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        return self.counter.validate_probe(decision, actions)

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        event = self.counter.record_outcome(probe, outcome)
        self._sync_product()
        return event

    def submit_answer(self, raw: Mapping[str, Any]) -> CounterAnswer:
        return self.counter.submit_answer(raw)

    def _sync_product(self) -> None:
        if self.counter.status == "CLOSED" and (
            (
                self.counter.counter_model is not None
                and self.counter.mask_law is not None
            )
            or self.counter.search_disposition is not None
        ):
            product_kind = (
                "COUNTER_MODEL_AND_MASK"
                if self.counter.counter_model is not None
                else "COUNTER_NOT_OBSERVED"
            )
            product_id = (
                self.counter.counter_model.model_id
                if self.counter.counter_model is not None
                else f"COUNTER-SEARCH-{self.counter.revision}"
            )
            derived_period_actions = None
            if self.counter.candidate is not None:
                rates = set(self.counter.candidate.amount_per_transition)
                footprint_size = len(self.counter.candidate.full_bar_footprint)
                if len(rates) == 1:
                    rate = next(iter(rates))
                    if rate > 0 and footprint_size % rate == 0:
                        derived_period_actions = footprint_size // rate
            self.machine.target_journal.put(MemoryProduct(
                product_id=product_id,
                product_type="CounterGateProduct",
                target_id=COUNTER_GATE_ID,
                revision=self.counter.revision,
                payload={
                    "product_kind": product_kind,
                    "counter_model": (
                        asdict(self.counter.counter_model)
                        if self.counter.counter_model is not None else None
                    ),
                    "mask_law": (
                        asdict(self.counter.mask_law)
                        if self.counter.mask_law is not None else None
                    ),
                    "boundary_obligation": self.counter.boundary_obligation,
                    "search_disposition": self.counter.search_disposition,
                    "derived_period_actions": derived_period_actions,
                    "ranked_object_frontier": self.counter.sweep_frontier(),
                    "state_identity": (
                        self.counter.state_archive.snapshot()
                        if self.counter.state_archive is not None else None
                    ),
                },
                dependencies=(GATE_ID,),
            ))

    def snapshot(self) -> dict[str, Any]:
        snapshot = self.counter.snapshot()
        contract = self.machine.target_registry.get(COUNTER_GATE_ID)
        snapshot["goal_card"] = contract.goal_card(status=self.assess().disposition)
        snapshot["completed_gates"] = self.machine.completed_gate_rows()
        return snapshot


class _LeverTarget:
    """G3 entry adapter: preserve G2's frontier while attribution is added."""

    def __init__(self, machine: "CyberneticGateMachine") -> None:
        self.machine = machine
        self.revision = 1
        self.evidence = LeverEvidenceAccumulator()
        self._dossier_answers: dict[str, LeverDossierAnswer] = {}
        self._inventory_answer: GateAnswer | None = None
        self._bounded_coverage_answer: GateAnswer | None = None
        self._bounded_ambiguities: dict[str, dict[str, Any]] = {}
        self._pending_confirmation: dict[str, Any] | None = None
        self._pending_dossier: dict[str, str] | None = None
        self._confirmation_records: list[dict[str, Any]] = []
        self._deferred_observations: list[dict[str, Any]] = []
        self.entity_ledger: EntityLedger | None = None
        self.lifecycle_journal: LifecycleJournal | None = None
        self._observed_transition_ids: set[int] = set()
        self._probe_serial = 0
        self._target_index = 0
        self._navigation_steps = 0
        self._navigation_limit = 24
        self._nav_refused: set[tuple[tuple[int, int], str]] = set()
        self._nav_route_evidence: list[str] = []
        self._last_nav_plan: Any | None = None
        self._phase = "CLICK" if self._world_type in {"CLICK_GOD_MODE", "HYBRID"} else "NAV"
        self._complete_reason: str | None = None
        self._eligible_frontier: tuple[dict[str, Any], ...] | None = None
        self._excluded_frontier: tuple[dict[str, Any], ...] | None = None
        self._frontier_mask_version: str | None = None
        self._inheritance: G2NullInheritance | None = None

    @property
    def _world_type(self) -> str:
        return control_archetype_prior(self.machine.ego.affordances)["world_type"]

    def _roster_after_inherited_nulls(self) -> tuple[dict[str, Any], ...]:
        """Ruling D5: a roster head G2 already clicked to a total null is recorded, not re-clicked.

        Safe before the pending checks: a pending confirmation or dossier holds a head that is no
        longer UNTOUCHED, and the inheritance stops at any such head.
        """
        candidates = self._ensure_frontier()
        if self._phase != "CLICK" or not self.machine.protocol["g3_inherits_g2_nulls"]:
            return candidates
        if self._inheritance is None:
            nulls = inherited_total_nulls(candidates, self.machine.counter._lossless_outcomes)
            self._inheritance = G2NullInheritance(nulls)
        self._target_index = self._inheritance.apply(
            candidates, self._target_index, self._ensure_entity_ledger(), self.lifecycle_journal
        )
        return candidates

    def _close_scoped_null_entities(self) -> None:
        """Close only entities whose complete sweep produced scoped null evidence."""
        journal = self.lifecycle_journal
        if journal is None:
            return
        for entity_id, entity in journal.entities.items():
            if entity.state != "NO_RESPONSE_YET":
                continue
            evidence_ref = entity.events[-1].evidence_ref if entity.events else "G3-ENUMERATION-COMPLETE"
            journal.close(entity_id, evidence_ref=evidence_ref)

    def _bound_ambiguity(
        self,
        *,
        member_id: str,
        entity_id: str,
        evidence_ref: str,
        disposition: str,
        reason: str,
        terminal_state: str = "AMBIGUOUS",
    ) -> dict[str, Any]:
        """Record why the current target has no distinct admissible next probe."""
        journal = self.lifecycle_journal
        assert journal is not None
        lifecycle = journal.entities[entity_id]
        if terminal_state == "BUDGET_STOPPED" and lifecycle.state != "BUDGET_STOPPED":
            journal.transition(
                entity_id,
                "BUDGET_STOPPED",
                evidence_ref=evidence_ref,
                actor="G3_ROUTER",
                reason=reason,
            )
        record = {
            "schema": "virelai-g3-bounded-ambiguity-v1",
            "target_member_id": member_id,
            "entity_id": entity_id,
            "evidence_ref": evidence_ref,
            "disposition": disposition,
            "terminal_state": terminal_state,
            "reason": reason,
            "inertness_claim_permitted": False,
            "retry_condition": (
                "a reset/rebind, newly available action, newly appearing object, or other "
                "controller-identifiable discriminating condition"
            ),
        }
        self._bounded_ambiguities[entity_id] = record
        return record

    def _ensure_frontier(self) -> tuple[dict[str, Any], ...]:
        """Compile G3's eligible roster from G2's frozen ranking and total mask."""
        mask = self.machine.counter.mask_law
        mask_cells = frozenset(() if mask is None else mask.cells)
        mask_version = None if mask is None else mask.law_version_id
        if self._eligible_frontier is not None:
            if self._frontier_mask_version != mask_version:
                raise GateContractError(
                    "G3 frontier mask version changed after compilation; reopen from G2."
                )
            return self._eligible_frontier
        evidence_refs = tuple(
            dict.fromkeys(
                (() if mask is None else mask.witness_evidence_refs)
                + (() if mask is None else (mask.demonstration_ref,))
            )
        )
        eligible: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for source_rank, candidate in enumerate(
            self.machine.counter._ranked_visual_targets, start=1
        ):
            cells = frozenset(candidate.cells)
            overlap = cells & mask_cells
            base = {
                "source_rank": source_rank,
                "member_id": candidate.member_id,
                "integer": candidate.integer,
                "original_cells": tuple(candidate.cells),
                "original_anchor": tuple(candidate.anchor),
                "original_bbox": tuple(candidate.bbox),
                "original_cell_count": candidate.cell_count,
                "shape_family": candidate.shape_family,
            }
            if cells and cells <= mask_cells:
                excluded.append({
                    **base,
                    "disposition": "COUNTER_ROLE_EXCLUDED",
                    "mask_law_version_id": mask_version,
                    "evidence_refs": evidence_refs,
                })
                continue
            projected = tuple(sorted(cells - mask_cells))
            relation = "PARTIAL_COUNTER_OVERLAP" if overlap else "DISJOINT_FROM_COUNTER"
            rows = [row for row, _ in projected]
            cols = [col for _, col in projected]
            eligible.append({
                **base,
                "eligible_rank": len(eligible) + 1,
                "mask_relation": relation,
                "cells": projected,
                "anchor": min(projected),
                "bbox": (min(rows), min(cols), max(rows), max(cols)),
                "cell_count": len(projected),
                "candidate": candidate,
            })
        self._eligible_frontier = tuple(eligible)
        self._excluded_frontier = tuple(excluded)
        self._frontier_mask_version = mask_version
        return self._eligible_frontier

    def _frontier_snapshot(self) -> dict[str, Any]:
        eligible = self._ensure_frontier()
        excluded = self._excluded_frontier or ()

        def public(row: Mapping[str, Any]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in row.items():
                if key == "candidate":
                    continue
                if key in {"cells", "original_cells"}:
                    result[key] = [list(cell) for cell in value]
                elif key in {
                    "anchor", "bbox", "original_anchor", "original_bbox",
                    "evidence_refs",
                }:
                    result[key] = list(value)
                else:
                    result[key] = value
            return result

        original_count = len(self.machine.counter._ranked_visual_targets)
        return {
            "schema": "virelai-g3-mask-filtered-frontier-v1",
            "world_type": self._world_type,
            "sweep_arm": (
                "CLICK_EVERY_ELIGIBLE_OBJECT"
                if self._world_type == "CLICK_GOD_MODE"
                else "COLLIDE_WITH_EVERY_ELIGIBLE_OBJECT"
            ),
            "mask_law_version_id": self._frontier_mask_version,
            "original_candidate_count": original_count,
            "candidate_count": len(eligible),
            "excluded_candidate_count": len(excluded),
            "accounting_complete": original_count == len(eligible) + len(excluded),
            "candidates": [public(row) for row in eligible],
            "excluded_candidates": [public(row) for row in excluded],
        }

    def _compact_confirmation_record(self, record: Mapping[str, Any]) -> dict[str, Any]:
        """Keep confirmation facts in the prompt while leaving geometry queryable."""
        compact = {
            key: value
            for key, value in record.items()
            if key not in {
                "predicted_local_cells", "predicted_remote_cells", "frozen_target"
            }
        }
        target = dict(record.get("frozen_target") or {})
        target_cells = list(target.pop("cells", []) or [])
        if target:
            compact["frozen_target"] = target
        compact["frozen_target_summary"] = {
            "cell_count": len(target_cells),
            "bbox": cell_bbox(target_cells),
            "detail_query": (
                "virelai('entity', id=%r, offset=0, limit=128)"
                % str(record.get("entity_id") or "")
            ),
        }
        for field in ("predicted_local_cells", "predicted_remote_cells"):
            cells = list(record.get(field) or [])
            compact[field.removesuffix("_cells") + "_summary"] = {
                "cell_count": len(cells),
                "bbox": cell_bbox(cells),
                "evidence_query": (
                    "virelai('evidence', id=%r)"
                    % str(record.get("witness_evidence_ref") or "")
                ),
            }
        compact["geometry_delivery"] = "FOCUSED_EVIDENCE_QUERY"
        return compact

    def _compact_frontier_snapshot(self) -> dict[str, Any]:
        """Project the complete frontier to bounded roster rows for Duck.

        The persistent snapshot retains every cell.  The automatic turn only
        needs identity, order, geometry summaries, mask accounting, and
        retrieval handles; exact geometry remains available through the
        entity query for the binding subject.
        """
        full = self._frontier_snapshot()
        ledger = self._ensure_entity_ledger()

        def compact_row(row: Mapping[str, Any]) -> dict[str, Any]:
            result = {
                key: value
                for key, value in row.items()
                if key not in {"cells", "original_cells"}
            }
            result["cells_omitted"] = int(row.get("cell_count") or 0)
            result["original_cells_omitted"] = int(
                row.get("original_cell_count") or 0
            )
            entity_id = str(
                row.get("entity_id")
                or ledger.entity_for_member(str(row.get("member_id") or ""))
                or ""
            )
            result["entity_id"] = entity_id
            result["detail_query"] = "virelai('entity', id=%r, offset=0, limit=128)" % entity_id
            return result

        return {
            **{
                key: value
                for key, value in full.items()
                if key not in {"candidates", "excluded_candidates"}
            },
            "schema": "virelai-g3-mask-filtered-frontier-v1",
            "view": "COMPACT_ROSTER",
            "candidates": [compact_row(row) for row in full["candidates"]],
            "excluded_candidates": [
                compact_row(row) for row in full["excluded_candidates"]
            ],
            "full_geometry_delivery": "FOCUSED_ENTITY_QUERY",
        }

    def _ensure_entity_ledger(self) -> EntityLedger:
        if self.entity_ledger is not None:
            return self.entity_ledger
        mask = self.machine.counter.mask_law
        eligible = self._ensure_frontier()
        ledger = EntityLedger(
            self.machine.counter.initial_grid,
            ignored_cells=() if mask is None else mask.cells,
            mask_law_version_id=None if mask is None else mask.law_version_id,
        )
        ledger.bind_members({
            "member_id": row["member_id"],
            "integer": row["integer"],
            "cells": row["cells"],
        } for row in eligible)
        ego_cells, _ego_binding_source = self.machine.ego.embodied_ego_binding()
        if ego_cells:
            ledger.bind_role_cells("EGO", ego_cells)
        for outcome in self.machine.counter._lossless_outcomes:
            transition_id = int(outcome.get("transition_id") or 0)
            if transition_id in self._observed_transition_ids:
                continue
            ledger.observe(outcome)
            self._observed_transition_ids.add(transition_id)
        self.entity_ledger = ledger
        self.lifecycle_journal = LifecycleJournal(ledger.entities)
        return ledger

    def observe_transition(self, outcome: Mapping[str, Any]) -> EntityTransition:
        ledger = self._ensure_entity_ledger()
        transition_id = int(outcome.get("transition_id") or 0)
        if transition_id in self._observed_transition_ids:
            return ledger.transitions[-1]
        transition = ledger.observe(outcome)
        self._observed_transition_ids.add(transition_id)
        return transition

    def observe_reset(self, outcome: Mapping[str, Any]) -> EntityTransition:
        """Port the light-weave site-only RESET back-edge into G3."""
        ledger = self._ensure_entity_ledger()
        transition_id = int(outcome.get("transition_id") or 0)
        if transition_id in self._observed_transition_ids:
            return ledger._transitions_by_id[transition_id]
        transition = ledger.observe_reset(outcome)
        self._observed_transition_ids.add(transition_id)
        return transition

    def observation_scope(
        self,
        outcome: Mapping[str, Any],
        *,
        target_member_id: str | None = None,
        target_entity_id: str | None = None,
        ego_entity_ids: Iterable[str] = (),
        ground_entity_ids: Iterable[str] = (),
    ) -> ObservationScope:
        ledger = self._ensure_entity_ledger()
        mask = self.machine.counter.mask_law
        action = outcome.get("action")
        action_name = str(action.get("action") or "").upper() if isinstance(action, Mapping) else ""
        movement_action = _action_number(action_name) in {1, 2, 3, 4, 5}
        world_type = control_archetype_prior(self.machine.ego.affordances)["world_type"]
        authorized_ego_motion = world_type in {"NAVIGATION", "HYBRID"} and movement_action
        bound_ego = tuple(ego_entity_ids) or ledger.role_entities("EGO")
        bound_ground = tuple(ground_entity_ids) or ledger.role_entities("GROUND")
        scope = ledger.scope(
            outcome,
            target_member_id=target_member_id,
            target_entity_id=target_entity_id,
            ego_entity_ids=bound_ego,
            ground_entity_ids=bound_ground,
            counter_mask_cells=() if mask is None else mask.cells,
            expected_ego_motion=authorized_ego_motion,
        )
        self._observed_transition_ids.add(int(outcome.get("transition_id") or 0))
        return scope

    def _counter_product(self) -> MemoryProduct:
        product = self.machine.target_journal.active_product(COUNTER_GATE_ID)
        if product is None:
            raise GateContractError("G3 cannot open before G2 emits CounterGateProduct.")
        return product

    def assess(self) -> GateAssessment:
        self._counter_product()
        product = self.machine.target_journal.active_product(LEVER_GATE_ID)
        if product is not None:
            disposition = "SATISFIED"
            unmet = ()
        elif self._bounded_coverage_answer is not None:
            disposition = "UNRESOLVED"
            unmet = (
                "new discriminating evidence is required for the explicitly bounded entities",
            )
        elif self._pending_dossier is not None:
            disposition = "ANSWER_REQUIRED"
            unmet = ("explain the confirmed lever before advancing the roster",)
        elif self._complete_reason:
            disposition = "ANSWER_REQUIRED"
            unmet = ("submit the evidence-bound LeverInventory",)
        else:
            disposition = "ACTIVE"
            unmet = ("enumerate the inherited frontier through the world-type scheduler",)
        return GateAssessment(
            target_id=LEVER_GATE_ID,
            revision=self.revision,
            disposition=disposition,
            evidence_refs=(),
            unmet_requirements=unmet,
            explanation=(
                "G3 inherits G2's exact object frontier and mask. It must enumerate every "
                "remaining object and may type a lever only from an attributed positive residue. "
                "A target with no distinct admissible follow-up is recorded as bounded ambiguity "
                "so it cannot monopolize the sweep or become a false inertness claim."
            ),
        )

    def next_probe(self) -> ProbeEnvelope | None:
        self._counter_product()
        ledger = self._ensure_entity_ledger()
        candidates = self._roster_after_inherited_nulls()
        if self._pending_dossier is not None:
            return None
        if self._pending_confirmation is not None:
            pending = self._pending_confirmation
            target = dict(pending["target"])
            target["confirmation_of"] = pending["witness_evidence_ref"]
            target["prediction"] = {
                "local_cells": [list(cell) for cell in pending["local_cells"]],
                "remote_cells": [list(cell) for cell in pending["remote_cells"]],
            }
            if pending["phase"] == "CLICK":
                return ProbeEnvelope(
                    probe_id=pending["probe_id"],
                    gate_id=LEVER_GATE_ID,
                    purpose="CONFIRM_LEVER_WITNESS",
                    question="Repeat the witnessed intervention once to confirm its scoped residue.",
                    actions=(dict(pending["action"]),),
                    live_alternatives=("prediction supported", "prediction contradicted", "boundary deferred"),
                    outcome_partition=("supported", "contradicted", "boundary event"),
                    declared_at_transition=pending["declared_at_transition"],
                    target=target,
                )
            return ProbeEnvelope(
                probe_id=pending["probe_id"],
                gate_id=LEVER_GATE_ID,
                purpose="CONFIRM_LEVER_WITNESS",
                question="Repeat the witnessed contact attempt once to confirm its scoped residue.",
                actions=(),
                live_alternatives=("prediction supported", "prediction contradicted", "boundary deferred"),
                outcome_partition=("supported", "contradicted", "boundary event"),
                declared_at_transition=pending["declared_at_transition"],
                admissible_actions=tuple(
                    item.action for item in self.machine.ego.affordances
                    if _action_number(item.action) in {1, 2, 3, 4, 5}
                ),
                target=target,
            )
        if self._phase == "CLICK" and self._target_index >= len(candidates):
            if self._world_type == "HYBRID":
                self._phase = "NAV"
                self._target_index = 0
                self._navigation_steps = 0
            else:
                self._close_scoped_null_entities()
                self._complete_reason = "CLICK_ENUMERATION_COMPLETE"
                return None
        if self._phase == "NAV" and self._target_index >= len(candidates):
            self._close_scoped_null_entities()
            self._complete_reason = "NAV_ENUMERATION_COMPLETE"
            return None
        frontier_item = candidates[self._target_index]
        entity_id = ledger.entity_for_member(frontier_item["member_id"])
        target = {
            "rank": self._target_index + 1,
            "eligible_rank": frontier_item["eligible_rank"],
            "source_rank": frontier_item["source_rank"],
            "member_id": frontier_item["member_id"],
            "entity_id": entity_id,
            "anchor": list(frontier_item["anchor"]),
            "bbox": list(frontier_item["bbox"]),
            "cells": [list(cell) for cell in frontier_item["cells"]],
            "integer": frontier_item["integer"],
            "cell_count": frontier_item["cell_count"],
            "shape_family": frontier_item["shape_family"],
            "mask_relation": frontier_item["mask_relation"],
        }
        if self._phase == "CLICK":
            return ProbeEnvelope(
                probe_id=f"{LEVER_GATE_ID}:CLICK:{self._target_index + 1}",
                gate_id=LEVER_GATE_ID,
                purpose="RANKED_CLICK_TARGET",
                question="Does clicking this ranked entity produce an attributable local or remote response?",
                actions=({
                    "action": "ACTION6",
                    "row": frontier_item["anchor"][0],
                    "col": frontier_item["anchor"][1],
                },),
                live_alternatives=("local target response", "remote response", "counter-only change", "no visible response", "ambiguous ego effect"),
                outcome_partition=("changed", "unchanged", "boundary event"),
                declared_at_transition=self.machine.observed_through_step,
                target=target,
            )
        return ProbeEnvelope(
            probe_id=f"{LEVER_GATE_ID}:NAV:{self._target_index + 1}:{self._navigation_steps + 1}",
            gate_id=LEVER_GATE_ID,
            purpose="PILOT_TO_LEVER_CONTACT",
            question="Pilot the demonstrated ego toward the ranked entity; declare approach or contact attempt.",
            actions=(),
            live_alternatives=("approach continues", "target responds on contact", "contact refused", "boundary during pursuit", "pilot budget exhausted"),
            outcome_partition=("approach", "contact response", "refused contact", "boundary event", "budget exhausted"),
            declared_at_transition=self.machine.observed_through_step,
            admissible_actions=tuple(item.action for item in self.machine.ego.affordances if _action_number(item.action) in {1, 2, 3, 4, 5}),
            target=target,
        )

    def planned_nav_step(self, target: Mapping[str, Any]) -> Any | None:
        """Return the controller's next evidence-bounded route/contact step."""
        if self._phase != "NAV":
            return None
        from inference.framework.nav_control import compile_nav_control_map
        from inference.framework.nav_route import NavLattice, plan_contact

        control = compile_nav_control_map(self.machine.ego)
        bearings = control.bearing_map()
        if not bearings:
            return None
        ledger = self._ensure_entity_ledger()
        ego_ids = ledger.role_entities("EGO")
        sightings = [ledger.entities[item].current for item in ego_ids if item in ledger.entities]
        sightings = [item for item in sightings if item is not None and item.cells]
        if not sightings:
            return None
        cells = tuple(sorted({cell for sighting in sightings for cell in sighting.cells}))
        anchor = min(cells)
        shape = frozenset((r-anchor[0], c-anchor[1]) for r, c in cells)
        stands = set()
        for entity_id in ego_ids:
            for sighting in ledger.entities[entity_id].sightings:
                if sighting.cells:
                    stands.add(min(sighting.cells))
        grid = ledger._grid
        lattice = NavLattice(anchor, shape, bearings, frozenset(stands),
                             frozenset(self._nav_refused), (len(grid), len(grid[0])))
        target_entity = str(target.get("entity_id") or "")
        target_cells = target.get("cells") or ()
        hypothesis = ledger.entities.get(target_entity)
        if hypothesis is not None and hypothesis.current is not None:
            target_cells = hypothesis.current.cells
        self._last_nav_plan = plan_contact(lattice, target_entity, target_cells)
        return self._last_nav_plan

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        expected = self.next_probe()
        if expected is None:
            raise GateContractError("G3 enumeration is complete; no further target probe is admissible.")
        supplied = tuple(_normalize_action_payload(item) for item in actions)
        if expected.admissible_actions:
            if len(supplied) != 1 or supplied[0]["action"] not in expected.admissible_actions:
                raise GateContractError(
                    "G3 embodied piloting admits one current movement action: "
                    f"{list(expected.admissible_actions)!r}."
                )
            intent = str((decision or {}).get("pilot_intent") or "").strip().upper()
            if intent not in {"APPROACH", "CONTACT_ATTEMPT"}:
                raise GateContractError("G3 embodied piloting requires pilot_intent APPROACH or CONTACT_ATTEMPT.")
            return replace(expected, actions=supplied, pilot_intent=intent)
        if _canonical(supplied) != _canonical(expected.actions):
            raise GateContractError(f"Only the current ranked G3 target action is admissible: {list(expected.actions)!r}.")
        return expected

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        target_index_before = self._target_index
        expected = self.next_probe()
        if expected is None or probe.probe_id != expected.probe_id:
            raise GateContractError("Outcome does not belong to the current G3 probe.")
        ledger = self._ensure_entity_ledger()
        evidence_id = "E-" + hashlib.sha256(
            _canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()
        ).hexdigest()[:16]
        lossless = dict(outcome)
        lossless["evidence_id"] = evidence_id
        is_confirmation = probe.purpose == "CONFIRM_LEVER_WITNESS"
        target_member_id = str((probe.target or {}).get("member_id") or "")
        entity_id = ledger.entity_for_member(target_member_id)
        journal = self.lifecycle_journal
        assert journal is not None
        entity_id = entity_id or str((probe.target or {}).get("entity_id") or "")
        if entity_id and not is_confirmation and journal.entities[entity_id].state in {
            "UNTOUCHED", "AMBIGUOUS", "NO_RESPONSE_YET"
        }:
            journal.attempt(entity_id, evidence_ref=evidence_id)
        changed = {
            (int(item["row"]), int(item["col"]))
            for item in outcome.get("changed_cells") or ()
            if isinstance(item, Mapping)
        }
        target_cells = {
            (int(cell[0]), int(cell[1]))
            for cell in (probe.target or {}).get("cells", ())
            if isinstance(cell, (list, tuple)) and len(cell) == 2
        }
        target_changed = bool(target_cells & changed)
        terminal = any(
            bool((outcome.get("boundary_event") or {}).get(key))
            for key in ("done", "level_completed", "game_over", "run_complete")
        ) if isinstance(outcome.get("boundary_event"), Mapping) else False
        event: dict[str, Any] = {
            "schema": SCHEMA_VERSION,
            "evidence_id": evidence_id,
            "gate_id": LEVER_GATE_ID,
            "probe_id": probe.probe_id,
            "target": dict(probe.target or {}),
            "outcome": compact_probe_outcome(outcome),
        }
        action = probe.actions[0] if probe.actions else outcome.get("action")
        if isinstance(action, Mapping) and "row" in action and "col" in action:
            lossless.setdefault("acted_site", {
                "row": int(action["row"]), "col": int(action["col"]),
            })
        scope = self.observation_scope(
            lossless,
            target_member_id=target_member_id,
            target_entity_id=entity_id,
        )
        if (
            self._phase == "NAV" and probe.pilot_intent == "CONTACT_ATTEMPT"
            and not target_changed and not scope.ego_expected_cells
            and not scope.ground_exchange_cells
        ):
            # This is the production refused-contact observation: the predicted
            # contact press yielded no target, ego, or ground residue after the
            # counter was partitioned away.
            lossless["refused_contact"] = True
            if isinstance(action, Mapping):
                action_name = str(action.get("action") or "")
                ego_ids = ledger.role_entities("EGO")
                anchors = [ledger.entities[item].current.anchor for item in ego_ids
                           if ledger.entities[item].current is not None]
                if anchors and action_name:
                    self._nav_refused.add((min(anchors), action_name))
        pending = self._pending_confirmation
        if is_confirmation and pending is not None:
            frozen_cells = tuple(
                (int(cell[0]), int(cell[1]))
                for cell in pending["target"].get("cells", ())
            )
            scope = replace(
                scope,
                target_cells=frozen_cells,
                pre_action_owner_entity_id=pending.get("pre_action_owner_entity_id"),
            )
        channel = "POINTER" if self._phase == "CLICK" else "BODY"
        try:
            attribution = attribute_lever_outcome(
                lossless,
                evidence_ref=evidence_id,
                channel=channel,
                target_member_id=target_member_id,
                target_cells=scope.target_cells,
                counter_mask_cells=(
                    ()
                    if self.machine.counter.mask_law is None
                    else self.machine.counter.mask_law.cells
                ),
                ego_motion_cells=scope.ego_expected_cells,
                ego_confounded_cells=scope.ego_confounded_cells,
                ground_exchange_cells=scope.ground_exchange_cells,
                body_contact_cells=scope.body_contact_cells,
                pre_action_owner_member_id=(
                    target_member_id
                    if scope.pre_action_owner_entity_id == entity_id else None
                ),
                refused_contact=bool(lossless.get("refused_contact")),
                target_is_counter=(
                    bool(scope.target_cells)
                    and self.machine.counter.mask_law is not None
                    and set(scope.target_cells)
                    <= set(self.machine.counter.mask_law.cells)
                ),
            )
        except LeverAttributionError as exc:
            raise GateContractError(f"G3 attribution requires lossless scoped evidence: {exc}") from exc
        record = self.evidence.record(attribution)
        event["attribution"] = asdict(attribution)
        event["dossier"] = asdict(record)
        if self._phase == "NAV" and probe.pilot_intent == "CONTACT_ATTEMPT" and entity_id:
            from inference.framework.nav_intervention import ContactEpoch, ContactProcedure
            procedure = ContactProcedure.create(
                target_entity_id=entity_id, ego_entity_ids=ledger.role_entities("EGO"),
                target_cells=scope.target_cells,
                allowed_actions=tuple(sorted(
                    item.action for item in self.machine.ego.affordances
                    if _action_number(item.action) in {1, 2, 3, 4}
                )), level=self.machine.lives.level, life=self.machine.lives.life,
            )
            plan = self._last_nav_plan
            stand = getattr(plan, "stand", None)
            ego_after = {
                cell for ego_id in ledger.role_entities("EGO")
                if ego_id in ledger.entities and ledger.entities[ego_id].current is not None
                for cell in ledger.entities[ego_id].current.cells
            }
            contact_outcome = (
                "BOUNDARY" if attribution.boundary_state else
                "REFUSED" if lossless.get("refused_contact") else
                "ENTERED" if ego_after & set(scope.target_cells) else
                "DISPLACED" if plan is not None and ego_after and min(ego_after) != plan.stand else
                "TRANSFORMED" if attribution.positive else "UNRESOLVED"
            )
            epoch = ContactEpoch.create(
                procedure=procedure, route_evidence_refs=tuple(self._nav_route_evidence),
                contact_evidence_ref=evidence_id,
                final_action=str((action or {}).get("action") if isinstance(action, Mapping) else action),
                stand=stand, outcome=contact_outcome,
            )
            event["contact_epoch"] = epoch.snapshot()
        counter_baseline = self.machine.apply_counter_baseline(lossless)
        event["counter_baseline"] = counter_baseline
        ambiguity_bounded = False
        if is_confirmation:
            pending = self._pending_confirmation
            predicted_local = set(pending["local_cells"]) if pending else set()
            predicted_remote = set(pending["remote_cells"]) if pending else set()
            local_supported = bool(set(attribution.local_residue_cells) & predicted_local)
            remote_supported = bool(set(attribution.remote_residue_cells) & predicted_remote)
            confirmation_supported = attribution.positive and (
                local_supported or remote_supported
            )
            confirmation_record = {
                "witness_evidence_ref": pending["witness_evidence_ref"] if pending else None,
                "confirmation_evidence_ref": evidence_id,
                "target_member_id": target_member_id,
                "entity_id": entity_id,
                "declared_at_transition": (
                    int(pending["declared_at_transition"]) if pending else None
                ),
                "graded_at_transition": int(outcome.get("transition_id") or 0),
                "frozen_target": dict(pending["target"]) if pending else {},
                "predicted_local_cells": (
                    [list(cell) for cell in pending["local_cells"]] if pending else []
                ),
                "predicted_remote_cells": (
                    [list(cell) for cell in pending["remote_cells"]] if pending else []
                ),
                "status": (
                    "SUPPORTED" if confirmation_supported
                    else "BOUNDARY_DEFERRED" if attribution.boundary_state
                    else "CONTRADICTED"
                ),
            }
            event["confirmation"] = confirmation_record
            self._confirmation_records.append(dict(confirmation_record))
            advance_target = True
            if entity_id and confirmation_supported:
                witness = next(
                    item for item in self.evidence._witnesses.get(target_member_id, ())
                    if item.evidence_ref == pending["witness_evidence_ref"]
                )
                journal.witness(entity_id, witness_ref=witness.witness_id)
                journal.close(entity_id, evidence_ref=evidence_id)
                if journal.entities[entity_id].answer_refs:
                    journal.ready_for_g4(entity_id, evidence_ref=evidence_id)
                else:
                    witness_attribution = next(
                        item
                        for item in self.evidence._attributions.get(target_member_id, ())
                        if item.evidence_ref == pending["witness_evidence_ref"]
                    )
                    intervention: dict[str, Any]
                    if pending["phase"] == "NAV":
                        from inference.framework.nav_intervention import ContactProcedure
                        procedure = ContactProcedure.create(
                            target_entity_id=entity_id,
                            ego_entity_ids=ledger.role_entities("EGO"),
                            target_cells=pending["target"].get("cells", ()),
                            allowed_actions=tuple(sorted(
                                item.action for item in self.machine.ego.affordances
                                if _action_number(item.action) in {1, 2, 3, 4}
                            )),
                            level=self.machine.lives.level,
                            life=self.machine.lives.life,
                        )
                        intervention = {
                            **procedure.intervention.payload(),
                            "final_action": dict(pending["action"] or {}),
                            "target_cells": [list(cell) for cell in procedure.target_cells],
                        }
                    else:
                        intervention = dict(pending["action"] or {})
                    self._pending_dossier = {
                        "target_member_id": target_member_id,
                        "entity_id": entity_id,
                        "witness_evidence_ref": pending["witness_evidence_ref"],
                        "confirmation_evidence_ref": evidence_id,
                        "intervention": intervention,
                        "effect_summary": lever_effect_summary(
                            witness_attribution,
                            witness_evidence_ref=pending["witness_evidence_ref"],
                        ),
                    }
                    advance_target = False
            elif entity_id and attribution.boundary_state:
                journal.transition(
                    entity_id, "AMBIGUOUS", evidence_ref=evidence_id,
                    actor="G3_CONFIRMATION", reason="confirmation interrupted by boundary",
                )
                self._deferred_observations.append({
                    "target_gate": "G4-REACTIONS",
                    "evidence_ref": evidence_id,
                    "transition_id": int(outcome.get("transition_id") or 0),
                    "target_member_id": target_member_id,
                    "entity_id": entity_id,
                    "observation": "LEVER_CONFIRMATION_INTERRUPTED_BY_BOUNDARY",
                    "confirmation": dict(confirmation_record),
                    "epistemic_limit": (
                        "The boundary interrupted confirmation; the target remains retryable."
                    ),
                })
                advance_target = False
            elif entity_id:
                journal.transition(
                    entity_id, "AMBIGUOUS", evidence_ref=evidence_id,
                    actor="G3_CONFIRMATION", reason="prospective witness contradicted",
                )
            self._pending_confirmation = None
            if advance_target:
                self._target_index += 1
            self._navigation_steps = 0
        else:
            if entity_id and attribution.boundary_state:
                journal.transition(
                    entity_id, "AMBIGUOUS", evidence_ref=evidence_id,
                    actor="G3_ATTRIBUTOR", reason="target attempt interrupted by boundary",
                )
                self._deferred_observations.append({
                    "target_gate": "G4-REACTIONS",
                    "evidence_ref": evidence_id,
                    "transition_id": int(outcome.get("transition_id") or 0),
                    "target_member_id": target_member_id,
                    "entity_id": entity_id,
                    "observation": "LEVER_TARGET_ATTEMPT_INTERRUPTED_BY_BOUNDARY",
                    "epistemic_limit": "The interrupted target remains at the head of the G3 roster.",
                })
            elif entity_id and attribution.positive:
                journal.response(entity_id, positive=True, evidence_ref=evidence_id)
                self._pending_confirmation = {
                    "probe_id": f"{LEVER_GATE_ID}:CONFIRM:{target_member_id}:{evidence_id}",
                    "phase": self._phase,
                    "target": dict(probe.target or {}),
                    "action": dict(probe.actions[0]) if probe.actions else None,
                    "target_member_id": target_member_id,
                    "entity_id": entity_id,
                    "pre_action_owner_entity_id": scope.pre_action_owner_entity_id,
                    "witness_evidence_ref": evidence_id,
                    "declared_at_transition": int(outcome.get("transition_id") or 0),
                    "local_cells": tuple(attribution.local_residue_cells),
                    "remote_cells": tuple(attribution.remote_residue_cells),
                }
            elif entity_id and attribution.disposition in {
                "SCOPED_NULL_RESPONSE", COUNTER_ONLY_DISPOSITION
            }:
                journal.response(entity_id, positive=False, evidence_ref=evidence_id)
            elif entity_id and attribution.disposition in {"AMBIGUOUS_EGO_MASKED", "UNRESOLVED_ATTRIBUTION"}:
                journal.transition(
                    entity_id,
                    "AMBIGUOUS",
                    evidence_ref=evidence_id,
                    actor="G3_ATTRIBUTOR",
                    reason=attribution.disposition,
                )
                if self._phase == "CLICK":
                    event["bounded_ambiguity"] = self._bound_ambiguity(
                        member_id=target_member_id,
                        entity_id=entity_id,
                        evidence_ref=evidence_id,
                        disposition=attribution.disposition,
                        reason=(
                            "The metadata admits only the same direct coordinate click for this "
                            "frozen target. Repeating it supplies no distinct controller-owned "
                            "probe unless a reset, rebind, or new action changes the condition."
                        ),
                    )
                    ambiguity_bounded = True
        boundary_interrupted = bool(attribution.boundary_state)
        if not is_confirmation and entity_id and self._phase == "NAV":
            self._navigation_steps += 1
            self._nav_route_evidence.append(evidence_id)
            if boundary_interrupted:
                self._navigation_steps = 0
            elif target_changed and self._pending_confirmation is None:
                if attribution.disposition in {
                    "AMBIGUOUS_EGO_MASKED", "UNRESOLVED_ATTRIBUTION"
                }:
                    event["bounded_ambiguity"] = self._bound_ambiguity(
                        member_id=target_member_id,
                        entity_id=entity_id,
                        evidence_ref=evidence_id,
                        disposition=attribution.disposition,
                        reason=(
                            "The contact attempt changed the target state without resolving "
                            "causal ownership; the frozen attempt is recorded rather than repeated."
                        ),
                    )
                self._target_index += 1
                self._navigation_steps = 0
            elif (
                probe.pilot_intent == "CONTACT_ATTEMPT"
                and attribution.disposition in {"SCOPED_NULL_RESPONSE", COUNTER_ONLY_DISPOSITION}
                and self._pending_confirmation is None
            ):
                # A completed footprint contact with no world residue is the
                # target's scoped null result.  It closes this G3 attempt; the
                # route length is irrelevant to the epistemic verdict.
                self._target_index += 1
                self._navigation_steps = 0
            elif terminal and self._pending_confirmation is None:
                if attribution.disposition in {
                    "AMBIGUOUS_EGO_MASKED", "UNRESOLVED_ATTRIBUTION"
                }:
                    event["bounded_ambiguity"] = self._bound_ambiguity(
                        member_id=target_member_id,
                        entity_id=entity_id,
                        evidence_ref=evidence_id,
                        disposition=attribution.disposition,
                        terminal_state="AMBIGUOUS",
                        reason="The embodied contact pursuit was interrupted by a terminal boundary.",
                    )
                self._target_index += 1
                self._navigation_steps = 0
        elif (
            not is_confirmation and self._phase == "CLICK"
            and self._pending_confirmation is None and not boundary_interrupted
            and (
                ambiguity_bounded
                or attribution.disposition not in {
                    "AMBIGUOUS_EGO_MASKED", "UNRESOLVED_ATTRIBUTION"
                }
            )
        ):
            self._target_index += 1
        event["scheduler"] = {
            "phase": self._phase,
            "target_index": self._target_index,
            "navigation_steps": self._navigation_steps,
            "entity_id": entity_id,
            "target_changed": target_changed,
            "route_evidence_refs": list(self._nav_route_evidence),
        }
        if self._target_index != target_index_before:
            self._nav_route_evidence.clear()
            self._last_nav_plan = None
        self.revision += 1
        return event

    def submit_answer(self, raw: Mapping[str, Any]) -> GateAnswer | LeverDossierAnswer:
        answer_kind = str(raw.get("answer_kind") or "").strip().upper()
        if answer_kind == "LEVER_INVENTORY" or "lever_entities" in raw:
            return self._submit_inventory(raw)
        member_id = str(raw.get("target_member_id") or "").strip()
        if not member_id:
            raise GateContractError("G3 dossier answers require target_member_id.")
        if self._pending_dossier is None:
            raise GateContractError(
                "G3 accepts a lever dossier only after a prospectively supported confirmation."
            )
        if member_id != self._pending_dossier["target_member_id"]:
            raise GateContractError("G3 requires the confirmed current lever's dossier before any other answer.")
        explanation = str(raw.get("explanation") or raw.get("mechanism") or "").strip()
        required_refs = (
            self._pending_dossier["witness_evidence_ref"],
            self._pending_dossier["confirmation_evidence_ref"],
        )
        answer_id = str(raw.get("answer_id") or "G3-ANSWER-" + hashlib.sha256(
            _canonical({"member": member_id, "evidence": required_refs, "explanation": explanation}).encode()
        ).hexdigest()[:16])
        try:
            answer = validate_lever_dossier(
                raw,
                answer_id=answer_id,
                target_member_id=member_id,
                expected_intervention=self._pending_dossier["intervention"],
                expected_effect_summary=self._pending_dossier["effect_summary"],
                required_evidence_refs=required_refs,
            )
        except LeverDossierError as exc:
            raise GateContractError(f"G3 dossier rejected: {exc}") from exc
        self._dossier_answers[member_id] = answer
        entity_id = self._ensure_entity_ledger().entity_for_member(member_id)
        if entity_id and self.lifecycle_journal is not None:
            self.lifecycle_journal.answer(entity_id, answer_ref=answer_id)
            lifecycle = self.lifecycle_journal.entities[entity_id]
            if lifecycle.state == "G3-CLOSED" and lifecycle.witness_refs:
                self.lifecycle_journal.ready_for_g4(
                    entity_id, evidence_ref=required_refs[-1]
                )
        self._pending_dossier = None
        self._target_index += 1
        self._navigation_steps = 0
        self._nav_route_evidence.clear()
        self._last_nav_plan = None
        self.revision += 1
        return answer

    def _submit_inventory(self, raw: Mapping[str, Any]) -> GateAnswer:
        if self._complete_reason is None or self._pending_confirmation is not None:
            raise GateContractError("G3 inventory requires a completed probe roster with no pending confirmation.")
        if self._inventory_answer is not None or self._bounded_coverage_answer is not None:
            raise GateContractError(
                "G3 aggregate answer is already accepted; do not resubmit it. "
                "Follow the gate's next_operation."
            )
        ledger = self._ensure_entity_ledger()
        journal = self.lifecycle_journal
        assert journal is not None
        ranked = self._ensure_frontier()
        expected_entities = {
            ledger.entity_for_member(str(item["member_id"])) for item in ranked
        }
        expected_entities.discard(None)
        unbounded = {
            entity_id: journal.entities[entity_id].state
            for entity_id in sorted(expected_entities)
            if journal.entities[entity_id].state not in {
                "G3-CLOSED", "G4-READY", "AMBIGUOUS", "BUDGET_STOPPED"
            }
            or (
                journal.entities[entity_id].state in {"AMBIGUOUS", "BUDGET_STOPPED"}
                and entity_id not in self._bounded_ambiguities
            )
        }
        if unbounded:
            raise GateContractError(
                f"G3 coverage cannot be reported with unbounded probe results: {unbounded!r}."
            )
        lever_entities = _strings(raw.get("lever_entities", []), "lever_entities", required=False)
        clean_null_entities = _strings(
            raw.get("clean_null_entities", []), "clean_null_entities", required=False
        )
        ambiguous_entities = _strings(
            raw.get("ambiguous_entities", []), "ambiguous_entities", required=False
        )
        witnessed = {
            entity_id for entity_id in expected_entities
            if journal.entities[entity_id].state == "G4-READY"
        }
        clean_null = {
            entity_id for entity_id in expected_entities
            if journal.entities[entity_id].state == "G3-CLOSED"
            and not journal.entities[entity_id].witness_refs
        }
        ambiguous = {
            entity_id for entity_id in expected_entities
            if journal.entities[entity_id].state in {"AMBIGUOUS", "BUDGET_STOPPED"}
        }
        if set(lever_entities) != witnessed:
            raise GateContractError(
                "lever_entities must exactly match the witnessed, explained G4-ready entities."
            )
        if set(clean_null_entities) != clean_null:
            raise GateContractError(
                "clean_null_entities must exactly match entities closed by scoped null evidence."
            )
        if set(ambiguous_entities) != ambiguous:
            raise GateContractError(
                "ambiguous_entities must exactly match explicitly bounded unresolved entities."
            )
        if not witnessed and not ambiguous:
            raise GateContractError(
                "The completed interaction record contains no witnessed lever; G3 remains unanswered "
                "and the probe roster, contact execution, or attribution must be repaired."
            )
        explanation = str(raw.get("explanation") or raw.get("mechanism") or "").strip()
        evidence_refs = _strings(raw.get("evidence_refs"), "evidence_refs")
        competing = _strings(raw.get("competing_models"), "competing_models")
        falsifier = str(raw.get("falsifier") or "").strip()
        if not explanation or not evidence_refs or not competing or not falsifier:
            raise GateContractError(
                "LeverInventory requires explanation, evidence_refs, competing_models, and falsifier."
            )
        required_refs = {
            ref
            for entity_id in witnessed
            for ref in journal.entities[entity_id].witness_refs
        } | {
            journal.entities[entity_id].events[-1].evidence_ref
            for entity_id in clean_null
            if journal.entities[entity_id].events
        } | {
            self._bounded_ambiguities[entity_id]["evidence_ref"]
            for entity_id in ambiguous
        }
        known_refs = {
            item.evidence_ref
            for member_id in self.evidence._attributions
            for item in self.evidence._attributions[member_id]
        } | required_refs
        if set(evidence_refs) != required_refs or not set(evidence_refs) <= known_refs:
            raise GateContractError(
                "G3 inventory evidence_refs must exactly cover positive witnesses, scoped nulls, "
                "and bounded ambiguities."
            )
        answer_id = str(raw.get("answer_id") or "G3-INVENTORY-" + hashlib.sha256(
            _canonical({"entities": lever_entities, "evidence": evidence_refs}).encode()
        ).hexdigest()[:16])
        answer_kind = "G3_BOUNDED_COVERAGE_REPORT" if ambiguous else "LEVER_INVENTORY"
        answer = GateAnswer(
            answer_id=answer_id,
            answer_kind=answer_kind,
            subjects=(
                tuple(lever_entities + clean_null_entities + ambiguous_entities)
                if ambiguous else lever_entities
            ),
            mechanism=explanation,
            action_laws={"probe_protocol": str(self._complete_reason)},
            conditions=_strings(raw.get("conditions", []), "conditions", required=False),
            constraints=_strings(raw.get("limitations", []), "limitations", required=False),
            evidence_refs=evidence_refs,
            competing_models=competing,
            falsifier=falsifier,
            novel_prediction={
                "lever_entities": list(lever_entities),
                "clean_null_entities": list(clean_null_entities),
                "ambiguous_entities": list(ambiguous_entities),
            },
            limitations=_strings(raw.get("limitations", []), "limitations", required=False),
        )
        if ambiguous:
            self._bounded_coverage_answer = answer
            self.revision += 1
            return answer
        self._inventory_answer = answer
        self.machine.target_journal.put(MemoryProduct(
            product_id=answer_id,
            product_type="LeverInventory",
            target_id=LEVER_GATE_ID,
            revision=self.revision,
            payload={
                "answer": asdict(answer),
                "probe_protocol": self._complete_reason,
                "lever_entities": list(lever_entities),
                "clean_null_entities": list(clean_null_entities),
                "ambiguous_entities": [],
                "ranked_target_count": len(ranked),
                "frontier_accounting": self._frontier_snapshot(),
                "lifecycle_journal": journal.snapshot(),
            },
            dependencies=(COUNTER_GATE_ID,),
        ))
        self.revision += 1
        return answer

    def snapshot(self) -> dict[str, Any]:
        product = self._counter_product()
        payload = dict(product.payload)
        counter_model = payload.get("counter_model") or {}
        boundary_ref = str(counter_model.get("boundary_ref") or "")
        boundary_outcome = next(
            (
                row
                for row in reversed(self.machine.counter._lossless_outcomes)
                if str(row.get("evidence_id") or "") == boundary_ref
            ),
            None,
        )
        changed_outside_mask = None
        transition_id = None
        if isinstance(boundary_outcome, Mapping):
            mask_cells = (
                set(self.machine.counter.mask_law.cells)
                if self.machine.counter.mask_law else set()
            )
            changed_outside_mask = sum(
                1
                for item in boundary_outcome.get("changed_cells") or ()
                if isinstance(item, Mapping)
                and (int(item["row"]), int(item["col"])) not in mask_cells
            )
            transition_id = int(boundary_outcome.get("transition_id") or 0)
        contract = self.machine.target_registry.get(LEVER_GATE_ID)
        return {
            "schema": SCHEMA_VERSION,
            "gate_id": LEVER_GATE_ID,
            "revision": self.revision,
            "status": self.assess().disposition,
            "goal_card": contract.goal_card(status=self.assess().disposition),
            "source_frontier": payload.get("ranked_object_frontier"),
            "inherited_frontier": self._frontier_snapshot(),
            "counter_model_ref": counter_model.get("model_id"),
            "mask_law_ref": (payload.get("mask_law") or {}).get("law_version_id"),
            "counter_period_actions": payload.get("derived_period_actions"),
            "attribution_contract": {
                "schema": "virelai-g3-lever-attribution-contract-v1",
                "channels": sorted(ATTRIBUTION_CHANNELS),
                "positive_dispositions": sorted(POSITIVE_DISPOSITIONS),
                "subtractions": [
                    "COUNTER_MASK",
                    "EGO_SELF_MOTION",
                    "ORDINARY_GROUND_EXCHANGE",
                ],
                "null_policy": "SCOPED_NULL_RESPONSE_NEVER_PROVES_INERTNESS",
                "boundary_policy": "DEFER_TO_G4_REACTIONS",
                "observation_scope_schema": "virelai-g3-observation-scope-v1",
                "entity_ledger_schema": "virelai-g3-entity-ledger-v1",
                "ego_confounded_policy": "AMBIGUOUS_EGO_MASKED",
                "evidence": self.evidence.snapshot(),
                "dossier_answers": [
                    asdict(answer) for _, answer in sorted(self._dossier_answers.items())
                ],
                "inventory_answer": (
                    asdict(self._inventory_answer) if self._inventory_answer is not None else None
                ),
                "bounded_coverage_answer": (
                    asdict(self._bounded_coverage_answer)
                    if self._bounded_coverage_answer is not None else None
                ),
                "confirmation_records": list(self._confirmation_records),
                "bounded_ambiguities": [
                    dict(item) for _, item in sorted(self._bounded_ambiguities.items())
                ],
            },
            "entity_ledger": self._ensure_entity_ledger().snapshot(),
            "lifecycle_journal": self.lifecycle_journal.snapshot(),
            "scheduler": {
                "phase": self._phase,
                "target_index": self._target_index,
                "navigation_steps": self._navigation_steps,
                "navigation_limit": self._navigation_limit,
                "complete_reason": self._complete_reason,
                "pending_confirmation": (
                    {
                        "probe_id": self._pending_confirmation["probe_id"],
                        "target_member_id": self._pending_confirmation["target_member_id"],
                        "witness_evidence_ref": self._pending_confirmation["witness_evidence_ref"],
                        "declared_at_transition": self._pending_confirmation["declared_at_transition"],
                    }
                    if self._pending_confirmation is not None else None
                ),
                "pending_dossier": dict(self._pending_dossier) if self._pending_dossier else None,
            },
            "deferred_observations": self._deferred_observations + ([{
                "target_gate": "G4-REACTIONS",
                "evidence_ref": boundary_ref,
                "transition_id": transition_id,
                "observation": "COUNTER_EXTREMUM_TRANSITION_HAS_NON_COUNTER_CHANGES",
                "changed_cell_count_outside_counter_mask": changed_outside_mask,
                "epistemic_limit": (
                    "Retain for later conditional-reaction typing; G3 does not assign its cause."
                ),
            }] if boundary_ref and changed_outside_mask else []),
            "answer_template": ({
                "answer_kind": "LEVER_DOSSIER",
                "target_member_id": self._pending_dossier["target_member_id"],
                "explanation": "Explain what this intervention changed and why it is a lever.",
                "intervention": dict(self._pending_dossier["intervention"]),
                "effect_summary": dict(self._pending_dossier["effect_summary"]),
                "evidence_refs": [
                    self._pending_dossier["witness_evidence_ref"],
                    self._pending_dossier["confirmation_evidence_ref"],
                ],
                "competing_models": ["state the strongest remaining alternative"],
                "falsifier": "state what later observation would refute this lever claim",
            } if self._pending_dossier is not None else {
                "answer_kind": "LEVER_INVENTORY",
                "lever_entities": [
                    entity_id for entity_id, item in sorted(self.lifecycle_journal.entities.items())
                    if item.state == "G4-READY"
                ],
                "clean_null_entities": [
                    entity_id for entity_id, item in sorted(self.lifecycle_journal.entities.items())
                    if item.state == "G3-CLOSED" and not item.witness_refs
                ],
                "ambiguous_entities": sorted(self._bounded_ambiguities),
                "explanation": "Explain which probed objects are levers and what changed.",
                "evidence_refs": sorted({
                    ref
                    for entity_id, item in self.lifecycle_journal.entities.items()
                    for ref in (
                        item.witness_refs
                        if item.state == "G4-READY"
                        else [item.events[-1].evidence_ref]
                        if item.state == "G3-CLOSED" and item.events
                        else [self._bounded_ambiguities[entity_id]["evidence_ref"]]
                        if entity_id in self._bounded_ambiguities
                        else []
                    )
                }),
                "competing_models": ["state the strongest remaining alternative"],
                "falsifier": "state what later observation would refute this inventory",
            } if (
                self._complete_reason
                and self._inventory_answer is None
                and self._bounded_coverage_answer is None
            ) else None),
            "next_operation": (
                "SUBMIT_GATE_ANSWER" if self._pending_dossier is not None
                else "QUERY_NEXT_G3_TARGET" if self._complete_reason is None
                else "SUBMIT_GATE_ANSWER" if (
                    self._inventory_answer is None
                    and self._bounded_coverage_answer is None
                )
                else "WAIT_FOR_DISCRIMINATING_EVIDENCE"
                if self._bounded_coverage_answer is not None
                else "WAIT_FOR_NEXT_TARGET"
            ),
            "unmet_requirements": list(self.assess().unmet_requirements),
        }


    def compact_gate_view(self) -> dict[str, Any]:
        """Return bounded model context while snapshot() retains full evidence."""
        if self._complete_reason is not None and self._pending_dossier is None:
            return self._completion_gate_view()
        return self._working_gate_view()

    def _working_gate_view(self) -> dict[str, Any]:
        """Return the compact in-progress G3 workspace view."""
        snapshot = self.snapshot()
        ledger = self._ensure_entity_ledger()
        journal = self.lifecycle_journal
        assert journal is not None
        # The ledger deliberately retains transient worldline hypotheses for
        # evaluation.  The model needs the ranked frontier and established
        # roles, not every component created by a reset or large remote delta.
        relevant_entity_ids = set(ledger.member_to_entity.values())
        relevant_entity_ids.update(
            entity_id
            for entity_ids in ledger.role_bindings.values()
            for entity_id in entity_ids
        )
        if self._pending_confirmation is not None:
            member_id = str(self._pending_confirmation.get("target_member_id") or "")
            entity_id = ledger.member_to_entity.get(member_id)
            if entity_id:
                relevant_entity_ids.add(entity_id)
        compact_entities: dict[str, Any] = {}
        for entity_id in sorted(relevant_entity_ids):
            entity = ledger.entities[entity_id]
            current = entity.current
            cells = () if current is None else current.cells
            compact_entities[entity_id] = {
                "status": entity.status,
                "version": entity.version,
                "member_ids": sorted(entity.member_ids),
                "ambiguity_refs": list(entity.ambiguity_refs),
                "sighting_count": len(entity.sightings),
                "current": (
                    None
                    if current is None
                    else {
                        "transition_id": current.transition_id,
                        "integer": current.integer,
                        "cell_count": len(cells),
                        "bbox": cell_bbox(cells),
                        "relation": current.relation,
                        "evidence_ref": current.evidence_ref,
                    }
                ),
            }
        lifecycle_entities = {
            entity_id: {
                "state": item.state,
                "witness_refs": list(item.witness_refs),
                "answer_refs": list(item.answer_refs),
                "law_version_ids": list(item.law_version_ids),
                "event_count": len(item.events),
                "last_event": asdict(item.events[-1]) if item.events else None,
            }
            for entity_id, item in sorted(journal.entities.items())
            if entity_id in relevant_entity_ids
        }
        attribution = dict(snapshot["attribution_contract"])
        evidence = attribution.get("evidence") or {}
        attribution["evidence"] = {
            "schema": evidence.get("schema"),
            "record_count": len(evidence.get("records") or ()),
            "record_refs": [
                row.get("evidence_id")
                for row in (evidence.get("records") or ())[-8:]
                if isinstance(row, Mapping)
            ],
        }
        attribution["dossier_answers"] = [
            {
                "answer_id": answer.get("answer_id"),
                "answer_kind": answer.get("answer_kind"),
                "target_member_id": answer.get("target_member_id"),
                "evidence_refs": answer.get("evidence_refs"),
                "intervention": answer.get("intervention"),
                "effect_summary": answer.get("effect_summary"),
                "competing_models": answer.get("competing_models"),
            }
            for answer in attribution.get("dossier_answers") or ()
            if isinstance(answer, Mapping)
        ]
        attribution["confirmation_records"] = [
            self._compact_confirmation_record(record)
            for record in attribution.get("confirmation_records") or ()
            if isinstance(record, Mapping)
        ]
        view = dict(snapshot)
        view["inherited_frontier"] = self._compact_frontier_snapshot()
        view["attribution_contract"] = attribution
        view["entity_ledger"] = {
            "schema": "virelai-g3-entity-ledger-compact-v1",
            "entity_count": len(ledger.entities),
            "listed_entity_count": len(compact_entities),
            "omitted_transient_entity_count": len(ledger.entities) - len(compact_entities),
            "member_bindings": dict(sorted(ledger.member_to_entity.items())),
            "role_bindings": {
                role: sorted(entity_ids)
                for role, entity_ids in sorted(ledger.role_bindings.items())
            },
            "entities": compact_entities,
            "transition_count": len(ledger.transitions),
            "limitations": list(dict.fromkeys(ledger.limitations)),
            "detail_query": "virelai('entity', id=entity_id, offset=0, limit=128)",
        }
        lifecycle_snapshot = journal.snapshot()
        view["lifecycle_journal"] = {
            "schema": lifecycle_snapshot["schema"],
            "entity_count": lifecycle_snapshot["entity_count"],
            "listed_entity_count": len(lifecycle_entities),
            "omitted_transient_entity_count": (
                lifecycle_snapshot["entity_count"] - len(lifecycle_entities)
            ),
            "state_counts": lifecycle_snapshot["state_counts"],
            "entities": lifecycle_entities,
        }
        return self._bound_working_card(view)

    # Axiom A6 (DOCTRINE_FRICTION_AXIOMS_v2): the card is bounded regardless of world size.
    CARD_WINDOW_AHEAD = 6
    CARD_NOTABLE_LIMIT = 8
    NOTABLE_STATES = frozenset({"WITNESSED", "RESPONDED", "AMBIGUOUS", "G4-READY", "REOPENED"})

    def _card_entity_ids(self) -> tuple[list[str], set[str]]:
        """Entities the card must carry: the scheduler window, notable states, pending, roles."""
        ledger = self._ensure_entity_ledger()
        journal = self.lifecycle_journal
        assert journal is not None
        frontier = self._ensure_frontier()
        start = min(self._target_index, len(frontier))
        window = [
            ledger.entity_for_member(str(row["member_id"])) or ""
            for row in frontier[start:start + self.CARD_WINDOW_AHEAD]
        ]
        notable = [
            entity_id for entity_id, item in sorted(journal.entities.items())
            if item.state in self.NOTABLE_STATES
        ][: self.CARD_NOTABLE_LIMIT]
        keep = {item for item in window + notable if item}
        keep.update(
            entity_id
            for entity_ids in ledger.role_bindings.values()
            for entity_id in entity_ids
        )
        for pending in (self._pending_confirmation, self._pending_dossier):
            if pending is not None:
                entity_id = ledger.entity_for_member(str(pending.get("target_member_id") or ""))
                if entity_id:
                    keep.add(entity_id)
        return [item for item in window if item], keep

    def _bound_working_card(self, view: dict[str, Any]) -> dict[str, Any]:
        """Window the roster, ledger and journal; everything else is a paged query away."""
        window_ids, keep = self._card_entity_ids()
        frontier = dict(view["inherited_frontier"])
        rows = list(frontier.get("candidates") or ())
        shown = [row for row in rows if str(row.get("entity_id") or "") in keep]
        frontier.update({
            "view": "WINDOWED_ROSTER",
            "candidates": shown,
            "candidates_omitted": len(rows) - len(shown),
            "window": {
                "scheduler_position": self._target_index,
                "ahead": self.CARD_WINDOW_AHEAD,
                "entity_ids": window_ids,
            },
            "roster_query": "virelai('inventory', offset=0, limit=10)",
        })
        view["inherited_frontier"] = frontier
        source = view.get("source_frontier")
        if isinstance(source, Mapping):
            view["source_frontier"] = {
                key: value for key, value in source.items() if key != "candidates"
            }
            view["source_frontier"]["candidates_omitted"] = len(source.get("candidates") or ())
        ledger_view = dict(view["entity_ledger"])
        entities = {
            key: value for key, value in ledger_view["entities"].items() if key in keep
        }
        ledger_view["entities"] = entities
        ledger_view["listed_entity_count"] = len(entities)
        ledger_view["member_bindings"] = {
            member: entity for member, entity in ledger_view["member_bindings"].items()
            if entity in keep
        }
        ledger_view["omitted_entity_count"] = ledger_view["entity_count"] - len(entities)
        view["entity_ledger"] = ledger_view
        journal_view = dict(view["lifecycle_journal"])
        listed = {
            key: value for key, value in journal_view["entities"].items() if key in keep
        }
        journal_view["entities"] = listed
        journal_view["listed_entity_count"] = len(listed)
        journal_view["omitted_entity_count"] = journal_view["entity_count"] - len(listed)
        journal_view["detail_query"] = "virelai('inventory', offset=0, limit=10)"
        view["lifecycle_journal"] = journal_view
        view["card_bound"] = {
            "axiom": "A6",
            "rule": (
                "This card shows the scheduler window, notable entities and roles. The full "
                "roster, ledger and journal are one paged query away; nothing is discarded."
            ),
        }
        return view

    def _completion_gate_view(self) -> dict[str, Any]:
        """Render the exhausted G3 roster as an index into the durable ledger.

        Enumeration completion changes Duck's immediate task from inspecting a
        roster to reporting or carrying its partition.  Re-sending the working
        frontier, entity ledger, lifecycle journal, and attribution archive at
        that point duplicates the store and grows with every attempted object.
        This card retains the conclusion, qualification, and stable expansion
        handles while ``snapshot()`` remains the lossless evaluation surface.
        """
        snapshot = self.snapshot()
        ledger = self._ensure_entity_ledger()
        journal = self.lifecycle_journal
        assert journal is not None
        frontier = self._ensure_frontier()
        display_limit = 8

        confirmed: list[dict[str, Any]] = []
        clean_null: list[dict[str, Any]] = []
        bounded: list[dict[str, Any]] = []
        unresolved: list[dict[str, Any]] = []
        for row in frontier:
            member_id = str(row["member_id"])
            entity_id = ledger.entity_for_member(member_id)
            lifecycle = journal.entities.get(str(entity_id or ""))
            state = None if lifecycle is None else lifecycle.state
            base = {
                "eligible_rank": int(row["eligible_rank"]),
                "source_rank": int(row["source_rank"]),
                "target_member_id": member_id,
                "entity_id": entity_id,
                "state": state,
                "detail_query": (
                    "virelai('entity', id=%r, offset=0, limit=128)"
                    % str(entity_id or "")
                ),
            }
            dossier = self._dossier_answers.get(member_id)
            if state == "G4-READY" and dossier is not None:
                confirmed.append({
                    **base,
                    "intervention": dict(dossier.intervention),
                    "effect_summary": dict(dossier.effect_summary),
                    "evidence_refs": list(dossier.evidence_refs),
                })
            elif state == "G3-CLOSED" and lifecycle is not None:
                clean_null.append({
                    **base,
                    "evidence_ref": (
                        lifecycle.events[-1].evidence_ref
                        if lifecycle.events else None
                    ),
                    "scope": "OBSERVED_INTERACTION_IN_RECORDED_STATE",
                    "inertness_claim_permitted": False,
                })
            elif entity_id in self._bounded_ambiguities:
                ambiguity = self._bounded_ambiguities[entity_id]
                bounded.append({
                    **base,
                    "evidence_ref": ambiguity.get("evidence_ref"),
                    "disposition": ambiguity.get("disposition"),
                    "terminal_state": ambiguity.get("terminal_state"),
                    "retry_condition": ambiguity.get("retry_condition"),
                    "inertness_claim_permitted": False,
                })
            else:
                unresolved.append(base)

        def bounded_section(rows: list[dict[str, Any]]) -> dict[str, Any]:
            return {
                "total": len(rows),
                "listed": rows[:display_limit],
                "omitted": max(0, len(rows) - display_limit),
            }

        answer = self._inventory_answer or self._bounded_coverage_answer
        completion_kind = (
            "CLEAN_INVENTORY"
            if self._inventory_answer is not None
            else "BOUNDED_COVERAGE"
            if self._bounded_coverage_answer is not None
            else "AWAITING_INVENTORY_ANSWER"
        )
        excluded = self._excluded_frontier or ()
        card = {
            "schema": "virelai-g3-completion-card-v1",
            "gate_id": LEVER_GATE_ID,
            "revision": self.revision,
            "status": self.assess().disposition,
            "goal_card": snapshot["goal_card"],
            "completion": {
                "kind": completion_kind,
                "sweep_arm": (
                    "CLICK_EVERY_ELIGIBLE_OBJECT"
                    if self._world_type == "CLICK_GOD_MODE"
                    else "COLLIDE_WITH_EVERY_ELIGIBLE_OBJECT"
                ),
                "reason": self._complete_reason,
                "mask_law_ref": snapshot.get("mask_law_ref"),
                "original_candidate_count": len(frontier) + len(excluded),
                "eligible_candidate_count": len(frontier),
                "counter_excluded_count": len(excluded),
                "accounted_candidate_count": (
                    len(confirmed) + len(clean_null) + len(bounded) + len(unresolved)
                ),
                "accounting_complete": (
                    len(frontier)
                    == len(confirmed) + len(clean_null) + len(bounded) + len(unresolved)
                ),
            },
            "confirmed_levers": bounded_section(confirmed),
            "scoped_nulls": bounded_section(clean_null),
            "bounded_unknowns": bounded_section(bounded),
            "unresolved_entities": bounded_section(unresolved),
            "accepted_answer": (
                None if answer is None else {
                    "answer_id": answer.answer_id,
                    "answer_kind": answer.answer_kind,
                    "evidence_ref_count": len(answer.evidence_refs),
                }
            ),
            "epistemic_limits": [
                "Scoped nulls do not prove inertness outside the tested action and state.",
                "Bounded unknowns remain unresolved and reopen when their retry condition occurs.",
                "G3 locates response witnesses; detailed reaction laws belong to G4.",
            ],
            "expand": [
                {
                    "label": "complete G3 inventory",
                    "query": "virelai('inventory', offset=0, limit=10)",
                },
                {
                    "label": "one entity",
                    "query": "virelai('entity', id=entity_id, offset=0, limit=128)",
                },
                {
                    "label": "one evidence record",
                    "query": "virelai('evidence', id=evidence_id)",
                },
            ],
            "answer_template": snapshot.get("answer_template"),
            "next_operation": snapshot.get("next_operation"),
            "unmet_requirements": snapshot.get("unmet_requirements", []),
        }
        return card

    def inventory_view(self, *, offset: int = 0, limit: int = 10) -> dict[str, Any]:
        """Return one bounded page of the complete G3 roster partition."""
        offset = max(0, int(offset))
        limit = max(1, min(25, int(limit)))
        ledger = self._ensure_entity_ledger()
        journal = self.lifecycle_journal
        assert journal is not None
        rows: list[dict[str, Any]] = []
        for item in self._ensure_frontier():
            member_id = str(item["member_id"])
            entity_id = ledger.entity_for_member(member_id)
            lifecycle = journal.entities.get(str(entity_id or ""))
            dossier = self._dossier_answers.get(member_id)
            ambiguity = self._bounded_ambiguities.get(str(entity_id or ""))
            if lifecycle is not None and lifecycle.state == "G4-READY":
                disposition = "CONFIRMED_LEVER"
            elif lifecycle is not None and lifecycle.state == "G3-CLOSED":
                disposition = "SCOPED_NULL"
            elif ambiguity is not None:
                disposition = "BOUNDED_UNKNOWN"
            else:
                disposition = "UNRESOLVED"
            evidence_refs = []
            if dossier is not None:
                evidence_refs.extend(dossier.evidence_refs)
            elif ambiguity is not None and ambiguity.get("evidence_ref"):
                evidence_refs.append(str(ambiguity["evidence_ref"]))
            elif lifecycle is not None and lifecycle.events:
                evidence_refs.append(lifecycle.events[-1].evidence_ref)
            rows.append({
                "kind": "ELIGIBLE_TARGET",
                "eligible_rank": int(item["eligible_rank"]),
                "source_rank": int(item["source_rank"]),
                "target_member_id": member_id,
                "entity_id": entity_id,
                "disposition": disposition,
                "lifecycle_state": None if lifecycle is None else lifecycle.state,
                "evidence_refs": list(dict.fromkeys(evidence_refs)),
                "retry_condition": (
                    None if ambiguity is None else ambiguity.get("retry_condition")
                ),
                "inertness_claim_permitted": False,
                "detail_query": (
                    "virelai('entity', id=%r, offset=0, limit=128)"
                    % str(entity_id or "")
                ),
            })
        for item in self._excluded_frontier or ():
            rows.append({
                "kind": "ROLE_EXCLUSION",
                "source_rank": int(item["source_rank"]),
                "target_member_id": str(item["member_id"]),
                "disposition": str(item["disposition"]),
                "mask_law_version_id": item.get("mask_law_version_id"),
                "evidence_refs": list(item.get("evidence_refs") or ()),
            })
        page = rows[offset:offset + limit]
        next_offset = offset + len(page)
        return {
            "schema": "virelai-g3-inventory-view-v1",
            "gate_id": LEVER_GATE_ID,
            "page": {
                "offset": offset,
                "limit": limit,
                "returned": len(page),
                "total": len(rows),
                "next_offset": next_offset if next_offset < len(rows) else None,
            },
            "items": page,
            "truncated": next_offset < len(rows),
            "full_store": "CyberneticGateMachine.snapshot()",
        }

    def entity_view(self, entity_id: str, *, offset: int = 0, limit: int = 128) -> dict[str, Any]:
        ledger = self._ensure_entity_ledger()
        requested = str(entity_id or "").strip()
        if requested not in ledger.entities:
            raise GateContractError(f"Unknown G3 entity_id {requested!r}.")
        offset = max(0, int(offset))
        limit = max(1, min(256, int(limit)))
        entity = ledger.entities[requested]
        current = entity.current
        cells = list(current.cells) if current is not None else []
        return {
            "schema": "virelai-g3-entity-detail-v1",
            "entity_id": requested,
            "status": entity.status,
            "version": entity.version,
            "member_ids": sorted(entity.member_ids),
            "ambiguity_refs": list(entity.ambiguity_refs),
            "current": (
                None
                if current is None
                else {
                    "transition_id": current.transition_id,
                    "integer": current.integer,
                    "relation": current.relation,
                    "evidence_ref": current.evidence_ref,
                    "cell_count": len(cells),
                    "bbox": cell_bbox(cells),
                    "cells_page": [list(cell) for cell in cells[offset:offset + limit]],
                    "page": {"offset": offset, "limit": limit, "total": len(cells)},
                }
            ),
            "sightings": [
                {
                    "transition_id": sighting.transition_id,
                    "frame": sighting.frame,
                    "integer": sighting.integer,
                    "cell_count": len(sighting.cells),
                    "bbox": cell_bbox(sighting.cells),
                    "relation": sighting.relation,
                    "evidence_ref": sighting.evidence_ref,
                }
                for sighting in entity.sightings[-8:]
            ],
        }


class _ReactionTarget:
    """G4.0/G4.1: bind proven levers and explain their exact effect anatomy."""

    def __init__(self, machine: "CyberneticGateMachine") -> None:
        self.machine = machine
        self.revision = 1
        self._anatomies: dict[str, LeverEffectAnatomy] = {}
        self._answers: dict[str, LeverReactionAnswer] = {}
        self._ordered_entities: tuple[str, ...] = ()

    def _lever_product(self) -> MemoryProduct:
        product = self.machine.target_journal.active_product(LEVER_GATE_ID)
        if product is None:
            raise GateContractError("G4 cannot open before G3 emits LeverInventory.")
        return product

    def _seed(self) -> None:
        if self._ordered_entities:
            return
        product = self._lever_product()
        entities = tuple(str(item) for item in product.payload.get("lever_entities") or ())
        if not entities:
            raise GateContractError("G4 requires at least one G3-ready lever entity.")
        if set(entities) & set(product.payload.get("clean_null_entities") or ()):
            raise GateContractError("G3 scoped-null entities cannot enter G4.")

        g3: _LeverTarget = self.machine._adapters[LEVER_GATE_ID]
        ledger = g3._ensure_entity_ledger()
        journal = g3.lifecycle_journal
        assert journal is not None
        mask = self.machine.counter.mask_law
        anatomies: dict[str, LeverEffectAnatomy] = {}
        for entity_id in entities:
            lifecycle = journal.entities.get(entity_id)
            if lifecycle is None or lifecycle.state != "G4-READY":
                raise GateContractError(f"G4 subject {entity_id!r} is not G4-ready in the G3 lifecycle.")
            members = sorted(
                member_id for member_id, bound_entity in ledger.member_to_entity.items()
                if bound_entity == entity_id and member_id in g3._dossier_answers
            )
            if len(members) != 1:
                raise GateContractError(
                    f"G4 requires exactly one accepted G3 dossier binding for {entity_id!r}."
                )
            member_id = members[0]
            dossier = g3._dossier_answers[member_id]
            confirmations = [
                item for item in g3._confirmation_records
                if str(item.get("entity_id") or "") == entity_id
                and str(item.get("target_member_id") or "") == member_id
                and str(item.get("status") or "").upper() == "SUPPORTED"
            ]
            if not confirmations:
                raise GateContractError(f"G4 cannot find a supported G3 confirmation for {entity_id!r}.")
            witness_evidence_ref = str(confirmations[-1].get("witness_evidence_ref") or "")
            attributions = [
                item for item in g3.evidence._attributions.get(member_id, ())
                if item.positive and item.evidence_ref == witness_evidence_ref
            ]
            if not attributions:
                raise GateContractError(f"G4 cannot find the positive G3 witness for {entity_id!r}.")
            attribution = attributions[0]
            confirmation_ref = str(confirmations[-1].get("confirmation_evidence_ref") or "")
            try:
                anatomies[entity_id] = compile_effect_anatomy(
                    attribution,
                    entity_id=entity_id,
                    intervention=dossier.intervention,
                    confirmation_evidence_ref=confirmation_ref,
                    dossier_answer_ref=dossier.answer_id,
                    mask_law_version_id=None if mask is None else mask.law_version_id,
                )
            except G4ReactionError as exc:
                raise GateContractError(f"G4 anatomy rejected for {entity_id}: {exc}") from exc
        self._ordered_entities = entities
        self._anatomies = anatomies

    def _current_entity(self) -> str | None:
        self._seed()
        return next((item for item in self._ordered_entities if item not in self._answers), None)

    def assess(self) -> GateAssessment:
        self._seed()
        product = self.machine.target_journal.active_product(REACTION_GATE_ID)
        current = self._current_entity()
        if product is not None:
            disposition = "SATISFIED"
            unmet: tuple[str, ...] = ()
        else:
            disposition = "ANSWER_REQUIRED"
            unmet = (
                f"explain the complete effect anatomy for {current}",
            ) if current is not None else ("emit the G4 anatomy product",)
        return GateAssessment(
            target_id=REACTION_GATE_ID,
            revision=self.revision,
            disposition=disposition,
            evidence_refs=tuple(
                ref for entity_id in self._ordered_entities
                for ref in (
                    self._anatomies[entity_id].witness_evidence_ref,
                    self._anatomies[entity_id].confirmation_evidence_ref,
                )
            ),
            unmet_requirements=unmet,
            explanation=(
                "G4 binds only G3-ready levers. This slice asks Duck to explain every exact "
                "counter-masked effect channel; repetition and deeper mechanism questions remain open."
            ),
        )

    def next_probe(self) -> None:
        self._seed()
        return None

    def validate_probe(self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]) -> None:
        raise GateContractError("G4 effect anatomy uses accepted G3 evidence and requires a gate answer, not an action.")

    def record_outcome(self, probe: ProbeEnvelope, outcome: Mapping[str, Any]) -> dict[str, Any]:
        raise GateContractError("G4 effect anatomy does not admit a new probe in this slice.")

    def submit_answer(self, raw: Mapping[str, Any]) -> LeverReactionAnswer:
        current = self._current_entity()
        if current is None:
            raise GateContractError("G4 effect-anatomy answers are already complete.")
        try:
            answer = validate_reaction_answer(raw, self._anatomies[current])
        except G4ReactionError as exc:
            raise GateContractError(f"G4 reaction answer rejected: {exc}") from exc
        self._answers[current] = answer
        self.revision += 1
        if len(self._answers) == len(self._ordered_entities):
            product_id = "G4-ANATOMY-" + hashlib.sha256(_canonical({
                "entities": self._ordered_entities,
                "answers": [self._answers[item].answer_id for item in self._ordered_entities],
            }).encode()).hexdigest()[:16]
            self.machine.target_journal.put(MemoryProduct(
                product_id=product_id,
                product_type="LeverEffectAnatomySet",
                target_id=REACTION_GATE_ID,
                revision=self.revision,
                payload={
                    "scope": "G4.0_BINDING_AND_G4.1_EFFECT_ANATOMY",
                    "lever_entities": list(self._ordered_entities),
                    "anatomies": [anatomy_payload(self._anatomies[item]) for item in self._ordered_entities],
                    "answers": [asdict(self._answers[item]) for item in self._ordered_entities],
                    "open_questions": list(self._anatomies[self._ordered_entities[0]].open_questions),
                },
                dependencies=(LEVER_GATE_ID,),
            ))
        return answer

    def reaction_view(self, entity_id: str) -> dict[str, Any]:
        self._seed()
        requested = str(entity_id or "").strip()
        if requested not in self._anatomies:
            raise GateContractError(f"Unknown G4 lever entity_id {requested!r}.")
        return {
            "schema": "virelai-g4-reaction-detail-v1",
            "gate_id": REACTION_GATE_ID,
            "anatomy": anatomy_payload(self._anatomies[requested]),
            "accepted_answer": (
                None if requested not in self._answers else asdict(self._answers[requested])
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        self._seed()
        contract = self.machine.target_registry.get(REACTION_GATE_ID)
        assessment = self.assess()
        return {
            "schema": "virelai-g4-reaction-gate-v1",
            "gate_id": REACTION_GATE_ID,
            "revision": self.revision,
            "status": assessment.disposition,
            "goal_card": contract.goal_card(status=assessment.disposition),
            "lever_entities": list(self._ordered_entities),
            "excluded_g3_scoped_null_entities": list(
                self._lever_product().payload.get("clean_null_entities") or ()
            ),
            "anatomies": [anatomy_payload(self._anatomies[item]) for item in self._ordered_entities],
            "answers": [asdict(self._answers[item]) for item in self._ordered_entities if item in self._answers],
            "open_questions": list(self._anatomies[self._ordered_entities[0]].open_questions),
            "unmet_requirements": list(assessment.unmet_requirements),
        }

    def compact_gate_view(self) -> dict[str, Any]:
        snapshot = self.snapshot()
        current = self._current_entity()
        accepted = [
            {"entity_id": item, "answer_id": self._answers[item].answer_id}
            for item in self._ordered_entities if item in self._answers
        ]
        view = {
            "schema": "virelai-g4-reaction-card-v1",
            "gate_id": REACTION_GATE_ID,
            "revision": self.revision,
            "status": self.assess().disposition,
            "goal_card": snapshot["goal_card"],
            "subject_accounting": {
                "g3_ready_lever_count": len(self._ordered_entities),
                "accepted_count": len(self._answers),
                "remaining_count": len(self._ordered_entities) - len(self._answers),
                "excluded_scoped_null_count": len(snapshot["excluded_g3_scoped_null_entities"]),
                "entities": list(self._ordered_entities),
            },
            "accepted_answers": accepted,
            "open_questions": snapshot["open_questions"],
            "next_operation": "WAIT_FOR_NEXT_G4_SLICE" if current is None else "SUBMIT_GATE_ANSWER",
            "unmet_requirements": snapshot["unmet_requirements"],
        }
        if current is not None:
            anatomy = self._anatomies[current]
            compact = anatomy_payload(anatomy, include_cells=False)
            channels = compact["channels"]
            rewrite_phrases = [
                f"{before}->{after}"
                for channel in anatomy.channels
                for before, after, _count in channel.integer_transitions
            ]
            view["current_lever"] = compact
            view["answer_template"] = {
                "answer_kind": "LEVER_EFFECT_ANATOMY",
                "entity_id": anatomy.entity_id,
                "intervention": dict(anatomy.intervention),
                "effect_channels": channels,
                "mechanism_explanation": (
                    f"Name {anatomy.entity_id}, every channel id, its affected local or remote region, "
                    f"and these exact rewrites: {', '.join(rewrite_phrases)}."
                ),
                "evidence_refs": [anatomy.witness_evidence_ref, anatomy.confirmation_evidence_ref],
                "record_refs": [anatomy.dossier_answer_ref, anatomy.anatomy_id],
                "competing_models": ["State one alternative compatible with this single witnessed transition."],
                "falsifier": "State a later observation that would refute this effect description.",
                "limitations": list(anatomy.limitations),
            }
            view["expand"] = [{
                "label": "full effect geometry",
                "query": f"virelai('reaction', id={current!r})",
            }]
        else:
            view["answer_template"] = None
            view["expand"] = [
                {"label": item, "query": f"virelai('reaction', id={item!r})"}
                for item in self._ordered_entities
            ]
        return view


class _LeverStudyTarget:
    """G4-A guided lever study (replaces the scripted G4.2 driver; Claude, 2026-09-27).

    Director ruling 2026-09-27: G4 becomes stated targets. The card states the target and the
    closure test; Duck chooses every action. The controller records each action, reads lever
    runs out of Duck's own presses (``g4_guided.LeverRun``), and checks the record. It never
    selects Duck's next move. The gate id, product type and Phase-1 payload fields are kept so
    the S1 hold and the boundary-release semantics (8cfb782) carry over unchanged.
    """

    TARGET = (
        "For every lever listed below, find out what activating it repeatedly does. Press the "
        "listed CLICK intervention, or repeat the listed NAV body-contact procedure, with no "
        "other lever activation in between, until the "
        "counter-masked board stops changing or returns to an earlier state. Then confirm that "
        "endpoint: one more press that also changes nothing, or one more full cycle that retraces "
        "the recorded states. Explain each lever once its run is confirmed."
    )
    DONE_WHEN = (
        "Every lever has a confirmed (or diverged) run and an accepted explanation. A lever whose "
        "run was cut off by a boundary is recorded as interrupted and released. A level change "
        "closes this level's study; cross-level work is G9."
    )
    RULES = (
        "Any action may be taken, in any order. With the controller executor (D3), it presses each lever to its endpoint and you explain each confirmed run; ask for an extra run with virelai('rerun', id=ENTITY_ID, presses=N).",
        "An activation counts only if it is the exact listed click or the terminal contact of the listed NAV procedure; NAV approach actions do not count.",
        "Any other action, a reset, or a boundary ends an unconfirmed run; start it again when "
        "you are ready. Ended runs stay on the record as evidence.",
        "The counter is masked: only non-counter changes count as the board changing.",
        "Explain a lever with virelai('gate_answer', answer={...}) once its run is CONFIRMED or "
        "DIVERGED; the answer template for that lever is on this card.",
    )

    def __init__(self, machine: "CyberneticGateMachine") -> None:
        self.machine = machine
        self.revision = 1
        self._ordered_entities: tuple[str, ...] = ()
        self._interventions: dict[str, dict[str, Any]] = {}
        self._active_run: LeverRun | None = None
        self._runs: dict[str, list[LeverRun]] = {}
        self._completed: dict[str, LeverRun] = {}
        self._answers: dict[str, LeverOrbitAnswer] = {}
        self._events: list[dict[str, Any]] = []
        self._action_count = 0
        # Levers whose run a boundary cut off: released from pending, still re-studiable.
        self._interruptions: dict[str, dict[str, Any]] = {}
        # Set once a level transition occurs; closes this level's G4 study (G9 owns transfer).
        self._level_closed: dict[str, Any] | None = None
        self._life_restudies: dict[str, int] = {}  # D4: same-level deaths per lever

    def _reaction_product(self) -> MemoryProduct:
        product = self.machine.target_journal.active_product(REACTION_GATE_ID)
        if product is None:
            raise GateContractError("G4-A cannot open before G4.1 emits LeverEffectAnatomySet.")
        return product

    def _seed(self) -> None:
        if self._ordered_entities:
            return
        product = self._reaction_product()
        interventions: dict[str, dict[str, Any]] = {}
        order: list[str] = []
        for raw in product.payload.get("anatomies") or ():
            if not isinstance(raw, Mapping):
                raise GateContractError("G4-A requires structured G4.1 anatomy rows.")
            entity_id = str(raw.get("entity_id") or "").strip()
            intervention = raw.get("intervention")
            if not entity_id or not isinstance(intervention, Mapping) or not intervention:
                raise GateContractError("Each G4-A lever needs an entity and bound intervention.")
            order.append(entity_id)
            if str(intervention.get("kind") or "").upper() == "NAV":
                if str(intervention.get("entity_id") or "") != entity_id or not intervention.get("procedure_id"):
                    raise GateContractError("A NAV intervention must bind its lever entity and procedure id.")
                interventions[entity_id] = dict(intervention)
            else:
                interventions[entity_id] = _normalize_action_payload(intervention)
        if not order:
            raise GateContractError("G4-A requires at least one confirmed lever.")
        self._ordered_entities = tuple(order)
        self._interventions = interventions

    # ---- state -------------------------------------------------------------------------

    def _pending(self) -> tuple[str, ...]:
        self._seed()
        if self._level_closed is not None:
            return ()
        return tuple(
            item for item in self._ordered_entities
            if item not in self._answers and item not in self._interruptions
        )

    def _awaiting_answer(self) -> tuple[str, ...]:
        return tuple(
            item for item in self._ordered_entities
            if item in self._completed and item not in self._answers
        )

    def _lever_for_action(self, action: Mapping[str, Any]) -> str | None:
        normalized = _canonical(_normalize_action_payload(action))
        for entity_id in self._ordered_entities:
            if _canonical(self._interventions[entity_id]) == normalized:
                return entity_id
        return None

    def planned_nav_step(self, entity_id: str) -> Any | None:
        self._seed()
        intervention = self._interventions.get(str(entity_id), {})
        if str(intervention.get("kind") or "").upper() != "NAV":
            return None
        g3 = self.machine._adapters[LEVER_GATE_ID]
        ledger = g3._ensure_entity_ledger()
        entity = ledger.entities.get(str(entity_id))
        cells = tuple(intervention.get("target_cells") or ())
        if entity is not None and entity.current is not None:
            cells = entity.current.cells
        return g3.planned_nav_step({"entity_id": entity_id, "cells": cells})

    def _lever_status(self, entity_id: str) -> str:
        if entity_id in self._answers:
            return "EXPLAINED"
        if entity_id in self._completed:
            return f"{self._completed[entity_id].status}_AWAITING_EXPLANATION"
        if self._active_run is not None and self._active_run.entity_id == entity_id:
            return self._active_run.status
        if entity_id in self._interruptions:
            return "INTERRUPTED_RELEASED"
        return "NOT_STARTED" if not self._runs.get(entity_id) else "RUN_ENDED_RESTART_NEEDED"

    def _studying(self) -> bool:
        """Duck still has lever runs to perform on this level."""
        if self._level_closed is not None:
            return False
        return any(
            item not in self._completed and item not in self._interruptions
            for item in self._ordered_entities
        )

    # ---- gate protocol -----------------------------------------------------------------

    def assess(self) -> GateAssessment:
        self._seed()
        product = self.machine.target_journal.active_product(ORBIT_GATE_ID)
        pending = self._pending()
        awaiting = self._awaiting_answer()
        if not pending:
            disposition = "SATISFIED" if product is not None else "ANSWER_REQUIRED"
            unmet: tuple[str, ...] = () if product is not None else ("emit the G4-A product",)
        elif self._studying():
            disposition = "PROBE_REQUIRED"
            unmet = tuple(
                f"{item}: {self._lever_status(item)}" for item in pending
            )
        else:
            disposition = "ANSWER_REQUIRED"
            unmet = tuple(f"explain the confirmed run for {item}" for item in awaiting)
        refs = tuple(event["evidence_id"] for event in self._events)
        return GateAssessment(
            target_id=ORBIT_GATE_ID,
            revision=self.revision,
            disposition=disposition,
            evidence_refs=refs,
            unmet_requirements=unmet,
            explanation=self.TARGET,
        )

    def next_probe(self) -> ProbeEnvelope | None:
        self._seed()
        if not self._studying():
            return None
        admissible = tuple(sorted(
            item.action for item in self.machine.ego.affordances
            if item.action in self.machine.ego._currently_available
        ))
        if not admissible:
            return None
        return ProbeEnvelope(
            probe_id=f"{ORBIT_GATE_ID}:GUIDED:{self._action_count + 1}",
            gate_id=ORBIT_GATE_ID,
            purpose="GUIDED_ACTION",
            question=self.TARGET,
            actions=(),
            live_alternatives=("run continues", "run stops", "endpoint confirmed", "run ended"),
            outcome_partition=("recorded",),
            declared_at_transition=self.machine.observed_through_step,
            admissible_actions=admissible,
            target={
                "levers": [
                    {"entity_id": item, "click": dict(self._interventions[item]),
                     "status": self._lever_status(item)}
                    for item in self._ordered_entities
                ],
            },
        )

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        raise GateContractError(
            "G4-A has no action to take now: every lever run on this level is confirmed, "
            "interrupted, or the level closed. Submit the explanations the card asks for."
        )

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        if probe.gate_id != ORBIT_GATE_ID or probe.purpose != "GUIDED_ACTION":
            raise GateContractError("Outcome does not belong to the G4-A guided study.")
        grids = grids_from_probe_outcome(outcome)
        if grids is None:
            raise GateContractError("G4-A requires lossless full-grid site transitions.")
        self._seed()
        action = dict(probe.actions[0]) if probe.actions else dict(outcome.get("action") or {})
        evidence_id = "E-" + hashlib.sha256(
            _canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()
        ).hexdigest()[:16]
        lossless = dict(outcome)
        lossless["evidence_id"] = evidence_id
        ledger = self.machine._adapters[LEVER_GATE_ID]._ensure_entity_ledger()
        entities_before = set(ledger.entities)
        counter_baseline = self.machine.apply_counter_baseline(lossless)
        entities_after = set(ledger.entities)
        boundary = outcome.get("boundary_event")
        boundary_state = dict(boundary) if isinstance(boundary, Mapping) else None
        transition_id = int(outcome.get("transition_id") or 0)
        self._action_count += 1

        nav_entity = None
        if probe.intent and probe.intent.startswith("NAV:"):
            parts = probe.intent.split(":", 2)
            nav_entity = parts[2] if len(parts) == 3 else None
            if len(parts) >= 2 and parts[1] == "APPROACH":
                self.revision += 1
                event = {
                    "schema": SCHEMA_VERSION, "evidence_id": evidence_id,
                    "gate_id": ORBIT_GATE_ID, "probe_id": probe.probe_id,
                    "action": action, "lever_entity_id": nav_entity,
                    "decision_intent": probe.intent, "outcome": compact_probe_outcome(outcome),
                    "run": {"kind": "NAV_APPROACH", "orbit_advanced": False},
                    "counter_baseline": counter_baseline,
                    "new_visual_entity_ids": sorted(entities_after - entities_before),
                }
                self._events.append(event)
                if is_terminal(boundary_state):
                    self._record_boundary(evidence_id, boundary_state)
                return event

        lever = nav_entity or self._lever_for_action(action)
        run_event = self._route_action(
            lever, action, evidence_id, transition_id, grids, boundary_state
        )
        self.revision += 1
        event = {
            "schema": SCHEMA_VERSION,
            "evidence_id": evidence_id,
            "gate_id": ORBIT_GATE_ID,
            "probe_id": probe.probe_id,
            "action": action,
            "lever_entity_id": lever,
            "decision_intent": probe.intent,
            "outcome": compact_probe_outcome(outcome),
            "run": run_event,
            "counter_baseline": counter_baseline,
            "new_visual_entity_ids": sorted(entities_after - entities_before),
        }
        self._events.append(event)
        if is_terminal(boundary_state):
            self._record_boundary(evidence_id, boundary_state)
        return event

    def _route_action(
        self,
        lever: str | None,
        action: Mapping[str, Any],
        evidence_id: str,
        transition_id: int,
        grids: tuple[Any, Any],
        boundary_state: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        active = self._active_run
        before, after = grids
        if lever is None or lever in self._completed or lever in self._answers:
            if active is not None:
                active.end("another action was taken")
                self._active_run = None
            return {
                "kind": "OTHER_ACTION" if lever is None else "PRESS_AFTER_CONFIRMED_RUN",
                "ended_run": None if active is None else active.run_id,
            }
        ended = None
        if active is not None and (
            active.entity_id != lever or not active.continues_from(before)
        ):
            active.end(
                "another lever was pressed" if active.entity_id != lever
                else "the board changed between presses (for example a reset)"
            )
            ended = active.run_id
            active = None
        if active is None:
            runs = self._runs.setdefault(lever, [])
            active = LeverRun(
                run_id=f"{lever}-R{len(runs) + 1}",
                entity_id=lever,
                intervention=self._interventions[lever],
                mask_law=self.machine.counter.mask_law,
            )
            runs.append(active)
            self._active_run = active
        try:
            result = active.record(
                evidence_ref=evidence_id,
                transition_id=transition_id,
                before=before,
                after=after,
                boundary_state=boundary_state,
            )
        except G4OrbitError as exc:
            raise GateContractError(f"G4-A run rejected: {exc}") from exc
        if not active.open:
            self._active_run = None
        if active.complete:
            self._completed[lever] = active
            self._interruptions.pop(lever, None)
        elif active.status == INTERRUPTED and not restudy_next_life(self._life_restudies, lever, boundary_state):
            self._interruptions[lever] = {
                "entity_id": lever,
                "run_id": active.run_id,
                "evidence_ref": evidence_id,
                "boundary_state": dict(boundary_state or {}),
                "level_transition": level_changed(boundary_state),
                "run": active.snapshot(),
                "resolution": (
                    "deferred to the cross-level gate (G9)" if level_changed(boundary_state)
                    else "released from pending; Duck may re-study it on this level"
                ),
            }
        return {"kind": "LEVER_PRESS", "run_id": active.run_id, "ended_run": ended, **result}

    def _record_boundary(self, evidence_id: str, boundary_state: Mapping[str, Any] | None) -> None:
        if self._active_run is not None:
            self._active_run.end("boundary")
            self._active_run = None
        if level_changed(boundary_state) and self._level_closed is None:
            state = dict(boundary_state or {})
            self._level_closed = {
                "evidence_ref": evidence_id,
                "level_before": state.get("level_before"),
                "level_after": state.get("level_after"),
            }
        self.revision += 1
        self._emit_orbit_product()

    def _emit_orbit_product(self) -> None:
        completed = tuple(item for item in self._ordered_entities if item in self._answers)
        interrupted = tuple(
            item for item in self._ordered_entities
            if item in self._interruptions and item not in self._answers
        )
        pending = self._pending()
        unstudied = () if self._level_closed is None else tuple(
            item for item in self._ordered_entities
            if item not in self._answers and item not in self._interruptions
        )
        identity: dict[str, Any] = {
            "entities": completed,
            "answers": [self._answers[item].answer_id for item in completed],
        }
        if interrupted:
            identity["interrupted"] = interrupted
        if self._level_closed is not None:
            identity["level_closed"] = self._level_closed.get("evidence_ref")
        product_id = "G4-ORBITS-" + hashlib.sha256(
            _canonical(identity).encode()
        ).hexdigest()[:16]
        phase1_status = (
            "CLOSED_BY_LEVEL_BOUNDARY" if self._level_closed is not None
            else "IN_PROGRESS" if pending else "COMPLETE"
        )
        self.machine.target_journal.put(MemoryProduct(
            product_id=product_id,
            product_type="LeverOrbitSet",
            target_id=ORBIT_GATE_ID,
            revision=self.revision,
            payload={
                "scope": "G4A_GUIDED_SINGLE_LEVER_STUDY",
                "lever_entities": list(completed),
                "pending_lever_entities": list(pending),
                "interrupted_lever_entities": list(interrupted),
                "unstudied_lever_entities": list(unstudied),
                "interruptions": [self._interruptions[item] for item in interrupted],
                "phase1_status": phase1_status,
                "level_boundary": None if self._level_closed is None else dict(self._level_closed),
                "orbits": [
                    {**self._completed[item].orbit.snapshot(),
                     "run_id": self._completed[item].run_id,
                     "run_status": self._completed[item].status,
                     "confirmation": list(self._completed[item].confirmation)}
                    for item in completed
                ],
                "answers": [asdict(self._answers[item]) for item in completed],
                "lever_classes": {item: self._completed[item].lever_class() for item in completed},
                "life_restudies": dict(self._life_restudies),
                "action_count": self._action_count,
                "epistemic_limit": (
                    "Confirmed endpoints and recurrences are state-scoped observations, not "
                    "universal laws. Interrupted levers were cut off by a boundary and are "
                    "neither classified nor pending."
                ),
            },
            dependencies=(REACTION_GATE_ID,),
        ))

    def submit_answer(self, raw: Mapping[str, Any]) -> LeverOrbitAnswer:
        self._seed()
        entity_id = str(raw.get("entity_id") or "").strip()
        if entity_id not in self._ordered_entities:
            raise GateContractError(f"Unknown G4-A lever entity_id {entity_id!r}.")
        if entity_id in self._answers:
            raise GateContractError(f"{entity_id} is already explained.")
        run = self._completed.get(entity_id)
        if run is None:
            raise GateContractError(
                f"{entity_id} has no confirmed run yet ({self._lever_status(entity_id)}); "
                "finish its run before explaining it."
            )
        try:
            answer = validate_orbit_answer(raw, run.orbit)
        except G4OrbitError as exc:
            raise GateContractError(f"G4-A answer rejected: {exc}") from exc
        self._answers[entity_id] = answer
        self.revision += 1
        self._emit_orbit_product()
        return answer

    def orbit_view(self, entity_id: str) -> dict[str, Any]:
        self._seed()
        requested = str(entity_id or "").strip()
        if requested not in self._ordered_entities:
            raise GateContractError(f"Unknown G4-A lever entity_id {requested!r}.")
        return {
            "schema": "virelai-g4a-lever-detail-v1",
            "gate_id": ORBIT_GATE_ID,
            "entity_id": requested,
            "click": dict(self._interventions[requested]),
            "status": self._lever_status(requested),
            "runs": [run.snapshot() for run in self._runs.get(requested, [])],
            "accepted_answer": (
                None if requested not in self._answers else asdict(self._answers[requested])
            ),
        }

    def snapshot(self) -> dict[str, Any]:
        self._seed()
        return {
            "schema": "virelai-g4a-guided-gate-v1",
            "gate_id": ORBIT_GATE_ID,
            "revision": self.revision,
            "status": self.assess().disposition,
            "lever_entities": list(self._ordered_entities),
            "runs": {
                item: [run.snapshot() for run in self._runs.get(item, [])]
                for item in self._ordered_entities
            },
            "answers": [
                asdict(self._answers[item]) for item in self._ordered_entities
                if item in self._answers
            ],
            "events": list(self._events),
            "interruptions": [
                self._interruptions[item] for item in self._ordered_entities
                if item in self._interruptions
            ],
            "level_boundary": None if self._level_closed is None else dict(self._level_closed),
            "unmet_requirements": list(self.assess().unmet_requirements),
        }

    def _answer_template(self, entity_id: str) -> dict[str, Any]:
        run = self._completed[entity_id]
        orbit = run.orbit
        last = orbit.steps[-1]
        return {
            "answer_kind": "LEVER_ORBIT_OBSERVATION",
            "entity_id": entity_id,
            "intervention": dict(orbit.intervention),
            "stop_disposition": orbit.stop_disposition,
            "state_sequence": list(orbit.state_sequence),
            "recurrence_to_state_index": last.recurrence_to_state_index,
            "observed_period": last.observed_period,
            "mechanism_explanation": (
                "Explain what repeated pressing did across this run, why it stopped, and what "
                "the confirmation showed."
            ),
            "evidence_refs": [item.evidence_ref for item in orbit.steps],
            "competing_models": ["State one model still compatible with this finite run."],
            "falsifier": "State a later observation that would contradict this description.",
            "limitations": ["This is an observed state-scoped run, not a universal law."],
        }

    def compact_gate_view(self) -> dict[str, Any]:
        contract = self.machine.target_registry.get(ORBIT_GATE_ID)
        assessment = self.assess()
        self._seed()
        awaiting = self._awaiting_answer()
        view: dict[str, Any] = {
            "schema": "virelai-g4a-target-card-v1",
            "gate_id": ORBIT_GATE_ID,
            "revision": self.revision,
            "status": assessment.disposition,
            "goal_card": contract.goal_card(status=assessment.disposition),
            "target": self.TARGET,
            "done_when": self.DONE_WHEN,
            "rules": list(self.RULES),
            "levers": [
                {
                    "entity_id": item,
                    "click": dict(self._interventions[item]),
                    "status": self._lever_status(item),
                    "class": (
                        self._completed[item].lever_class() if item in self._completed else None
                    ),
                }
                for item in self._ordered_entities
            ],
            "progress": {
                "explained_count": len(self._answers),
                "total_count": len(self._ordered_entities),
                "actions_taken": self._action_count,
            },
            "unmet_requirements": list(assessment.unmet_requirements),
            "next_operation": (
                "G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9"
                if self._level_closed is not None and not awaiting
                else "QUERY_NEXT_PROBE" if self._studying()
                else "SUBMIT_GATE_ANSWER" if awaiting
                else "WAIT_FOR_NEXT_G4_SLICE"
            ),
        }
        if self._active_run is not None:
            run = self._active_run
            view["active_run"] = {
                "run_id": run.run_id,
                "entity_id": run.entity_id,
                "status": run.status,
                "presses": len(run.orbit.steps) + len(run.confirmation),
                "confirmation_required": run.confirmation_required,
                "confirmation_done": len(run.confirmation),
            }
        if awaiting:
            # Bounded so the binding card stays inside the gate-context budget on many-lever
            # worlds; the remaining templates appear as earlier ones are answered.
            view["answer_templates"] = [self._answer_template(item) for item in awaiting[:3]]
            if len(awaiting) > 3:
                view["more_levers_awaiting_explanation"] = list(awaiting[3:])
        view["answer_template"] = (
            None if not awaiting else self._answer_template(awaiting[0])
        )
        if self._interruptions:
            view["interrupted_levers"] = [
                {
                    "entity_id": item["entity_id"],
                    "level_transition": item["level_transition"],
                    "resolution": item["resolution"],
                }
                for item in self._interruptions.values()
            ]
        if self._level_closed is not None:
            view["level_boundary"] = dict(self._level_closed)
            view["rules"] = [
                "The level changed, so G4 study for the previous level is closed. Cross-level "
                "transfer is the separate G9 gate, which is not built. No lever runs remain; "
                "explain any confirmed run still listed, otherwise no gated operation is available."
            ]
        view["expand"] = [{
            "label": "full lever record",
            "query": "virelai('orbit', id='<lever entity_id>')",
        }]
        return view


class CyberneticGateMachine:
    """Stable bridge facade over registry-selected target adapters."""

    def __init__(
        self,
        *,
        valid_actions: Iterable[Any],
        initial_grid: Sequence[Sequence[int]],
        observed_through_step: int = 0,
        g3_inherits_g2_nulls: bool = True,
    ) -> None:
        # The recording protocol, stamped on every probe envelope so a record replays under the
        # protocol it was made with (ruling D5 changed G3's sweep in R9-R08).
        self.protocol = {"g3_inherits_g2_nulls": bool(g3_inherits_g2_nulls)}
        self._build_level(valid_actions, initial_grid, observed_through_step)
        self.lives = LifeRecord()  # lives, levels and the high-water transition (R9-R16)
        self.levels: list[dict[str, Any]] = []  # each finished level's frozen model (R9-R17)
        self._capability_secret = secrets.token_bytes(32)
        self._consumed_capabilities: set[str] = set()
        # The record tier's in-memory index (DESIGN_VIRELAI_MEMORY_v1 §5.1): one sparse, lossless
        # row per recorded transition, whatever gate recorded it. Read by MemoryStore only.
        self.transition_index: list[dict[str, Any]] = []

    def _build_level(self, valid_actions: Iterable[Any], grid: Sequence[Sequence[int]], step: int, prior: Any = None) -> None:
        """Every LEVEL-tier field, fresh (R9-R17); ``prior``'s levers become this level's carry predictions (R9-R18)."""
        self.carry = CarryLedger(prior, grid, step)
        self.annotations = AnnotationLane()  # Duck's UNCERTIFIED notes (D6); never read by a gate
        self.ego = EgoGateMachine(valid_actions=valid_actions, initial_grid=grid, observed_through_step=step)
        self.counter = CounterGateMachine(affordances=self.ego.affordances, initial_grid=grid, observed_through_step=step)
        self.target_registry = _target_registry()
        self.target_journal = TargetJournal(self.target_registry)
        self.target_router = TargetRouter(self.target_registry, self.target_journal)
        self._g0 = _ActionSurfaceTarget(self)
        from inference.framework.g4c_gate import later_adapters

        self._adapters = {
            ACTION_METADATA_GATE_ID: self._g0, GATE_ID: _EgoTarget(self), COUNTER_GATE_ID: _CounterTarget(self),
            LEVER_GATE_ID: _LeverTarget(self), REACTION_GATE_ID: _ReactionTarget(self),
            ORBIT_GATE_ID: _LeverStudyTarget(self), **later_adapters(self),
        }
        self._issued_capabilities: dict[str, dict[str, Any]] = {}
        self._counter_prepared_from_ego = False

    def _advance_level(self, outcome: Mapping[str, Any]) -> None:
        """The level ended: freeze its model, then start the ladder on the next level's board (R9-R17).

        Without a lossless after-board the ladder cannot restart, and ``ladder_end`` stops the run as before.
        """
        grids = grids_from_probe_outcome(outcome)
        if grids is None:
            return
        from inference.framework.level_model import freeze_level

        self.levels.append(freeze_level(self, outcome))
        actions = outcome.get("available_actions_after") or [item.action for item in self.ego.affordances]
        self._build_level(actions, grids[1], int(outcome.get("transition_id") or 0), self.levels[-1])

    def _prepare_counter_from_ego(self) -> None:
        """Start G2 from Duck's demonstrated post-G1 world and ego binding."""
        if self._counter_prepared_from_ego:
            return
        ego_cells, binding_source = self.ego.embodied_ego_binding()
        self.counter = CounterGateMachine(
            affordances=self.ego.affordances,
            initial_grid=self.ego.current_grid(),
            observed_through_step=self.ego.observed_through_step,
            excluded_ego_cells=ego_cells,
            ego_binding_source=binding_source,
        )
        self._counter_prepared_from_ego = True

    @property
    def g0_answer(self) -> ActionMetadataAnswer | None:
        return self._g0.answer

    @property
    def g0_revision(self) -> int:
        return self._g0.revision

    def _effective_target_id(self) -> str:
        picked = self.target_router.current_or_last().target_id
        orbit = self.target_journal.active_product(ORBIT_GATE_ID)
        if orbit is not None and _phase1_hold_reason(orbit.payload) is not None:
            order = [contract.target_id for contract in self.target_registry.ordered()]
            if (picked in order and ORBIT_GATE_ID in order
                    and order.index(picked) > order.index(ORBIT_GATE_ID)):
                # Phase 1 is not complete on this level (a lever is pending, or the level
                # changed mid-study). Stay in G4.2; no Phase-2 gate opens (two-phase study).
                return ORBIT_GATE_ID
        return picked

    def _active_adapter(self) -> Any:
        return self._adapters[self._effective_target_id()]

    @property
    def gate_id(self) -> str:
        return self._effective_target_id()

    @property
    def status(self) -> str:
        return self.assessment().disposition

    def assessment(self) -> GateAssessment:
        return self._active_adapter().assess()

    @property
    def observed_through_step(self) -> int:
        """The last transition any gate recorded (R9-R14: G3 onward advance it too, F2)."""
        return max(self.ego.observed_through_step, self.counter.observed_through_step, self.lives.high_step)

    def next_probe(self) -> ProbeEnvelope | None:
        return self._active_adapter().next_probe()

    def _probe_capability_token(self, probe: ProbeEnvelope) -> tuple[str, str]:
        fingerprint = _canonical({
            "gate_id": probe.gate_id,
            "gate_revision": self.assessment().revision,
            "probe": asdict(probe),
        })
        digest = hmac.new(
            self._capability_secret, fingerprint.encode("utf-8"), hashlib.sha256
        ).digest()[:18]
        token = "P1_" + base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return token, fingerprint

    def next_probe_capability(self) -> dict[str, Any] | None:
        probe = self.next_probe()
        if probe is None:
            return None
        token, fingerprint = self._probe_capability_token(probe)
        self._issued_capabilities.setdefault(token, {
            "fingerprint": fingerprint,
            "probe_id": probe.probe_id,
            "gate_id": probe.gate_id,
            "gate_revision": self.assessment().revision,
        })
        capability = {
            "probe_token": token,
            "gate_id": probe.gate_id,
            "gate_revision": self.assessment().revision,
            "purpose": probe.purpose,
            "question": probe.question,
            "actions": [dict(item) for item in probe.actions],
            "live_alternatives": list(probe.live_alternatives),
            "outcome_partition": list(probe.outcome_partition),
            "declared_at_transition": probe.declared_at_transition,
        }
        if probe.admissible_actions and probe.purpose == "GUIDED_ACTION":
            capability["admissible_actions"] = list(probe.admissible_actions)
            capability["optional_decision_field"] = {
                "intent": "one short sentence: what this action is for"
            }
            capability["instruction"] = (
                "You choose this action. Pick any one admissible action (ACTION6 needs row and "
                "col) that advances the target; the controller records and audits it."
            )
        elif probe.admissible_actions:
            capability["admissible_actions"] = list(probe.admissible_actions)
            capability["required_decision_field"] = {
                "pilot_intent": ["APPROACH", "CONTACT_ATTEMPT"]
            }
        if probe.target is not None:
            capability["target"] = dict(probe.target)
        return capability

    def validate_probe(
        self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]
    ) -> ProbeEnvelope:
        probe = self.next_probe()
        if probe is None:
            return self._active_adapter().validate_probe(decision, actions)
        if not isinstance(decision, Mapping):
            raise GateContractError(
                "Query virelai('next_probe'), then call action(actions, decision={'probe_token': token})."
            )
        guided = probe.purpose in {"GUIDED_ACTION", "NAV_PREDICTION_TEST"} and bool(probe.admissible_actions)
        allowed_decision_fields = {"probe_token"}
        if guided:
            allowed_decision_fields.add("intent")
        elif probe.admissible_actions:
            allowed_decision_fields.add("pilot_intent")
        unexpected = set(decision) - allowed_decision_fields
        if unexpected:
            if guided:
                raise GateContractError(
                    "A guided action decision accepts only probe_token and an optional intent."
                )
            if probe.admissible_actions:
                raise GateContractError(
                    "Embodied pilot decision accepts only probe_token and pilot_intent; "
                    "do not copy the full probe envelope."
                )
            raise GateContractError(
                "Gated action decision accepts only probe_token; do not copy the full probe envelope."
            )
        token = str(decision.get("probe_token") or "").strip()
        if not token:
            raise GateContractError(
                "probe_token is required; query virelai('next_probe') for the current capability."
            )
        issued = self._issued_capabilities.get(token)
        if issued is None:
            raise GateContractError("Unknown probe_token; query virelai('next_probe') and use its token.")
        if token in self._consumed_capabilities:
            raise GateContractError("This probe_token has already been used and cannot be replayed.")
        expected_token, fingerprint = self._probe_capability_token(probe)
        if token != expected_token or issued.get("fingerprint") != fingerprint:
            raise GateContractError(
                "Stale probe_token; the gate or required probe changed. Query virelai('next_probe') again."
            )
        supplied_actions = tuple(_normalize_action_payload(item) for item in actions)
        admitted_probe = probe
        if guided:
            if len(supplied_actions) != 1 or supplied_actions[0]["action"] not in probe.admissible_actions:
                raise GateContractError(
                    "A guided action is exactly one action from: "
                    f"{list(probe.admissible_actions)!r}."
                )
            intent = str(decision.get("intent") or "").strip()[:240] or None
            admitted_probe = replace(probe, actions=supplied_actions, intent=intent)
        elif probe.admissible_actions:
            if len(supplied_actions) != 1 or supplied_actions[0]["action"] not in probe.admissible_actions:
                raise GateContractError(
                    "The embodied pilot admits one action from: "
                    f"{list(probe.admissible_actions)!r}."
                )
            pilot_intent = str(decision.get("pilot_intent") or "").strip().upper()
            if pilot_intent not in {"APPROACH", "CONTACT_ATTEMPT"}:
                raise GateContractError(
                    "Embodied piloting requires pilot_intent APPROACH or CONTACT_ATTEMPT."
                )
            admitted_probe = replace(
                probe, actions=supplied_actions, pilot_intent=pilot_intent
            )
        elif _canonical(supplied_actions) != _canonical(probe.actions):
            raise GateContractError(
                f"The capability admits only its exact actions: {list(probe.actions)!r}."
            )
        self._consumed_capabilities.add(token)
        return admitted_probe

    def record_outcome(
        self, probe: ProbeEnvelope, outcome: Mapping[str, Any]
    ) -> dict[str, Any]:
        event = self._active_adapter().record_outcome(probe, outcome)
        from inference.framework.memory_store import transition_index_row

        self.transition_index.append(self.lives.tag(transition_index_row(probe, outcome, event), outcome))
        mask = self.counter.mask_law if self.target_journal.active_product(COUNTER_GATE_ID) is not None else None
        self.carry.observe(outcome, None if mask is None else mask.cells)
        if level_changed(outcome.get("boundary_event") if isinstance(outcome.get("boundary_event"), Mapping) else None):
            self._advance_level(outcome)
        return event

    def apply_counter_baseline(self, outcome: Mapping[str, Any]) -> dict[str, Any] | None:
        """Apply G2 as a stable mask and ignore later counter behavior.

        Later transitions still enter the entity ledger so new world objects
        remain visible to G3/G4.  They never update the G2 product, open a
        boundary obligation, or invalidate downstream knowledge.
        """
        product = self.target_journal.active_product(COUNTER_GATE_ID)
        if product is None:
            return None
        self._adapters[LEVER_GATE_ID].observe_transition(outcome)
        mask = self.counter.mask_law
        return {
            "schema": SCHEMA_VERSION,
            "gate_id": COUNTER_GATE_ID,
            "purpose": "STABLE_COUNTER_BASELINE",
            "policy": "MASK_AND_IGNORE_AFTER_G2",
            "transition_id": int(outcome.get("transition_id") or 0),
            "mask_law_ref": None if mask is None else mask.law_version_id,
        }

    def observe_system_reset(self, outcome: Mapping[str, Any]) -> EntityTransition | dict[str, Any] | None:
        """A reset ends a life: one row from G0 on (R9-R16, D2); G3's ledger sees it once G2 is certified."""
        row = self.lives.reset(outcome, self.gate_id)
        if row is None:
            return None
        self.transition_index.append(row)
        if self.target_journal.active_product(COUNTER_GATE_ID) is None:
            return row
        return self._adapters[LEVER_GATE_ID].observe_reset(outcome)

    def g3_observation_scope(
        self,
        outcome: Mapping[str, Any],
        *,
        target_member_id: str | None = None,
        target_entity_id: str | None = None,
        ego_entity_ids: Iterable[str] = (),
        ground_entity_ids: Iterable[str] = (),
    ) -> ObservationScope:
        """Derive a production-shaped G3 scope without assigning a mechanism."""
        return self._adapters[LEVER_GATE_ID].observation_scope(
            outcome,
            target_member_id=target_member_id,
            target_entity_id=target_entity_id,
            ego_entity_ids=ego_entity_ids,
            ground_entity_ids=ground_entity_ids,
        )

    def update_action_metadata(self, valid_actions: Iterable[Any]) -> None:
        before = tuple(self.ego.affordances)
        self.ego.update_action_metadata(valid_actions)
        if tuple(self.ego.affordances) != before:
            self._g0.invalidate()
            self._counter_prepared_from_ego = False
            self.counter = CounterGateMachine(
                affordances=self.ego.affordances,
                initial_grid=self.ego._initial_grid,
                observed_through_step=self.observed_through_step,
            )

    def submit_answer(
        self, raw: Mapping[str, Any]
    ) -> ActionMetadataAnswer | GateAnswer | CounterAnswer:
        from inference.framework.card_builder import fill_certified_fields

        return self._active_adapter().submit_answer(fill_certified_fields(self, raw))

    def record_reuse(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        if self.target_journal.active_product(ACTION_METADATA_GATE_ID) is None:
            raise GateContractError("G0 must close before a later law can be reused.")
        return self.ego.record_reuse(raw)

    def completed_gate_rows(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for contract in self.target_registry.ordered():
            product = self.target_journal.active_product(contract.target_id)
            if product is None:
                continue
            rows.append({
                "gate_id": contract.target_id,
                "revision": product.revision,
                "answer": dict(product.payload),
                "product_id": product.product_id,
                "product_type": product.product_type,
            })
        return rows

    def legal_move_status(self) -> dict[str, Any]:
        """Axiom A2 (DOCTRINE_FRICTION_AXIOMS_v1): every gate state admits a move or declares an end.

        Legal means an admissible probe is offered, or an answer is asked for with a template
        to fill, or the gate declares a terminal/waiting state that asks nothing of Duck. The two
        illegal signatures are the ones three live runs deadlocked on: an answer demanded with no
        template (ft09 G2, 2026-09-27), and a probe demanded with none offered (vc33 G4.2,
        2026-09-27; ls20 G2, 2026-09-22).
        """
        view = self.gate_view()
        operation = str(view.get("next_operation") or "")
        base = {
            "gate_id": self.gate_id,
            "status": view.get("status"),
            "next_operation": operation,
        }
        if self.next_probe_capability() is not None:
            return {**base, "legal": True, "move": "PROBE"}
        if operation == "SUBMIT_GATE_ANSWER":
            has_template = view.get("answer_template") is not None or bool(
                view.get("answer_templates")
            )
            if "answer_template" in view and not has_template:
                return {
                    **base, "legal": False,
                    "reason": "an answer is demanded but the card supplies no answer template",
                }
            return {**base, "legal": True, "move": "ANSWER"}
        if operation in {"QUERY_NEXT_PROBE", "QUERY_NEXT_G3_TARGET"}:
            return {
                **base, "legal": False,
                "reason": "a probe is demanded but no admissible probe is offered",
            }
        return {**base, "legal": True, "move": "DECLARED_STATE"}

    def gate_view(self) -> dict[str, Any]:
        contract = self.target_registry.get(self._effective_target_id())
        assessment = self.assessment()
        if contract.target_id in G4_GATE_IDS:
            return self._adapters[contract.target_id].compact_gate_view()
        if contract.target_id == ACTION_METADATA_GATE_ID:
            metadata = [asdict(item) for item in self.ego.affordances]
            return {
                "schema": SCHEMA_VERSION,
                "gate_id": contract.target_id,
                "revision": assessment.revision,
                "status": assessment.disposition,
                "goal_card": contract.goal_card(status=assessment.disposition),
                "action_metadata": metadata,
                "control_archetype_prior": control_archetype_prior(
                    self.ego.affordances
                ),
                "answer_template": {
                    "answer_id": "G0-...",
                    "action_metadata": metadata,
                    "semantic_claims": [],
                    "epistemic_limit": "State that effects remain unknown until observed.",
                },
                "next_operation": "SUBMIT_GATE_ANSWER",
            }
        if contract.target_id == COUNTER_GATE_ID:
            snapshot = self.counter.snapshot()
            if assessment.disposition == "ANSWER_REQUIRED":
                next_operation = "SUBMIT_GATE_ANSWER"
            elif assessment.disposition == "SATISFIED":
                next_operation = "WAIT_FOR_NEXT_TARGET"
            elif self.counter.next_probe() is not None:
                next_operation = "QUERY_NEXT_PROBE"
            else:
                next_operation = "WAIT_FOR_REPRESENTATION_OR_NEW_ACTION"
            view = {
                "schema": SCHEMA_VERSION,
                "gate_id": COUNTER_GATE_ID,
                "revision": assessment.revision,
                "status": assessment.disposition,
                "goal_card": contract.goal_card(status=assessment.disposition),
                "opening_protocol": snapshot["opening_protocol"],
                "progress": snapshot["probe_progress"],
                **({
                    "target": COUNTER_TARGET,
                    "done_when": (
                        "A candidate's law and mask pass purity on the record (every footprint "
                        "change follows the counter law; no witness acted on the footprint) and "
                        "one frozen footprint-scoped prediction is supported. If no counter "
                        "appears, G2 closes as not-observed once every ranked visual object has "
                        "been clicked at least once."
                    ),
                    "rejected_candidates": list(self.counter._rejected_candidates),
                } if self.counter._guided else {}),
                "stop_reason": snapshot["stop_reason"],
                "unmet_requirements": list(assessment.unmet_requirements),
                "next_operation": next_operation,
            }
            if self.counter.candidate is not None:
                view["candidate"] = asdict(self.counter.candidate)
                view["record_trigger"] = self.counter.record_trigger()
            if assessment.disposition == "ANSWER_REQUIRED":
                view["answer_contract"] = {
                    "required_explanation": [
                        "answer_id", "candidate_id", "tracked_variable", "mechanism",
                        "bookkeeping_reason", "evidence_refs", "competing_models", "falsifier",
                        "novel_prediction",
                    ],
                    "evidence_refs": "exactly the active candidate witness evidence ids",
                    "closure_basis": "FUTURE RECURRENCE DEMONSTRATION",
                    "next_target": "G2-COUNTER-BOUNDARY",
                }
                view["answer_template"] = self.counter.answer_template()
                view["answer_template_note"] = (
                    "Replace the example prose. Keep the candidate, evidence refs, full footprint "
                    "and rewrite. Choose the prediction's action yourself (any admissible action) "
                    "and its predicate: COUNTER_REWRITE with the recurrent amount, or "
                    "COUNTER_SILENT with amount 0. It is scored only on the counter footprint."
                )
            if self.counter.pending_prediction is not None:
                view["pending_prediction"] = asdict(self.counter.pending_prediction)
            if self.counter.counter_model is not None and self.counter.mask_law is not None:
                view["counter_model_ref"] = self.counter.counter_model.model_id
                view["mask_law_ref"] = self.counter.mask_law.law_version_id
            if self.counter.boundary_obligation is not None:
                view["boundary_obligation"] = dict(self.counter.boundary_obligation)
            if self.counter.search_disposition is not None:
                view["search_disposition"] = dict(self.counter.search_disposition)
            return view
        if contract.target_id == LEVER_GATE_ID:
            return self._adapters[LEVER_GATE_ID].compact_gate_view()
        observed = sum(1 for item in self.ego.coverage if item.observed)
        coverage_gap = (
            assessment.disposition == "UNRESOLVED"
            and self.ego.coverage_stop_reason is not None
        )
        if coverage_gap:
            next_operation = "WAIT_FOR_REPRESENTATION_OR_NEW_ACTION"
        elif assessment.disposition in {"ANSWER_REQUIRED", "REOPENED", "UNRESOLVED"} and self.next_probe() is None:
            next_operation = "SUBMIT_GATE_ANSWER"
        elif assessment.disposition == "SATISFIED":
            next_operation = "WAIT_FOR_NEXT_TARGET"
        else:
            next_operation = "QUERY_NEXT_PROBE"
        view = {
            "schema": SCHEMA_VERSION,
            "gate_id": contract.target_id,
            "revision": assessment.revision,
            "status": assessment.disposition,
            "goal_card": contract.goal_card(status=assessment.disposition),
            "control_archetype_prior": control_archetype_prior(
                self.ego.affordances
            ),
            "progress": {
                "coverage_observed": observed,
                "coverage_total": len(self.ego.coverage),
                "evidence_count": len(self.ego.evidence),
            },
            "coverage_certificate": self.ego.coverage_certificate(
                include_unknown_members=False
            ),
            "unmet_requirements": list(assessment.unmet_requirements),
            "next_operation": next_operation,
        }
        if self.ego.last_comparison is not None:
            comparison = self.ego.last_comparison
            view["demonstration_verdict"] = {
                "outcome": comparison.outcome,
                "predicate": comparison.predicate,
                "comparison_id": comparison.comparison_id,
                "scoped_changed_cell_count": len(comparison.scoped_changes),
                "remote_changed_cell_count": len(comparison.remote_changes),
                "limitations": list(comparison.limitations),
                "observed_form": comparison.observed_form,
                "observed_recolor": comparison.observed_recolor,
                "observed_translation": comparison.observed_translation,
                "before_footprint": list(comparison.before_footprint),
                "after_footprint": list(comparison.after_footprint),
            }
        if self.ego.ego_law is not None:
            view["ego_law_ref"] = {
                "law_id": self.ego.ego_law.law_id,
                "law_version_id": self.ego.ego_law.law_version_id,
                "revision": self.ego.ego_law.revision,
            }
        if next_operation == "SUBMIT_GATE_ANSWER":
            pointer_exit = (
                self.ego._control_archetype["world_type"] == "CLICK_GOD_MODE"
            )
            available_actions = [item.action for item in self.ego.affordances]
            evidence_refs = (
                [ACTION_METADATA_GATE_ID]
                if pointer_exit
                else [str(item["evidence_id"]) for item in self.ego.evidence]
            )
            view["answer_contract"] = {
                "required_explanation": [
                    "answer_id", "answer_kind", "subjects", "mechanism", "action_laws",
                    "evidence_refs", "competing_models", "falsifier",
                ],
                "closure_basis": (
                    "G0 ACTION_SURFACE INTERFACE AXIOM"
                    if pointer_exit
                    else "OBSERVED G1 TRANSITIONS"
                ),
                "evidence_refs": evidence_refs,
                "next_target": "G2-COUNTER",
            }
            view["answer_template"] = {
                "answer_id": "G1-1" if pointer_exit else "G1-EGO-EXPLANATION-1",
                "answer_kind": (
                    "POINTER_GOD_MODE" if pointer_exit else "EMBODIED_EGO"
                ),
                "subjects": [
                    "pointer locus" if pointer_exit else "directly controlled subject or locus"
                ],
                "mechanism": (
                    "ACTION6 selects the pointer locus coordinate."
                    if pointer_exit
                    else "Explain what the ego is and how control affects it."
                ),
                "action_laws": {
                    action: (
                        "selects the supplied grid coordinate"
                        if pointer_exit
                        else "Describe its observed transformation."
                    )
                    for action in available_actions
                },
                "conditions": [],
                "constraints": [],
                "evidence_refs": evidence_refs,
                "competing_models": [
                    "visible embodied ego"
                    if pointer_exit
                    else "State one evidence-compatible alternative."
                ],
                "falsifier": (
                    "ACTION6 stops accepting coordinates"
                    if pointer_exit
                    else "State what future observation would refute this model."
                ),
                "limitations": [],
            }
            if pointer_exit:
                # The template already carries every required pointer field;
                # avoid duplicating it in the compact automatic gate context.
                view["answer_contract"].pop("required_explanation", None)
                view["answer_contract"].pop("evidence_refs", None)
                view["answer_contract"].pop("next_target", None)
                for optional in ("conditions", "constraints", "limitations"):
                    view["answer_template"].pop(optional, None)
            if not pointer_exit:
                demonstration_action = available_actions[0] if available_actions else "ACTION1"
                view["answer_contract"].update({
                    "novel_prediction": {
                        "action": {"action": demonstration_action},
                        "scope": {"representation": [
                            "VISIBLE_OBSERVATION", "CELLS", "REGION",
                            "ACTED_COMPONENT", "WORLDLINE",
                        ]},
                        "predicate": [
                            "NO_CHANGE", "ANY_CHANGE", "EXACT_CELL_DELTA", "STILL",
                            "RECOLOR", "PURE_TRANSLATION", "GROW", "SHRINK", "DEFORM",
                            "PATTERN_TRANSLATION",
                        ],
                        "expected_parameters": (
                            "EXACT_CELL_DELTA requires changes. Form predicates require exact "
                            "before_footprint, after_footprint, before_integer, after_integer, and "
                            "recolor; PURE_TRANSLATION also requires displacement. "
                            "PATTERN_TRANSLATION verifies a multi-integer footprint and requires "
                            "before_footprint, after_footprint, and displacement but no integer ids."
                        ),
                        "because": "why the prediction follows from the proposed ego law",
                        "novelty": "why this is a future discriminating state",
                    },
                })
                view["answer_template"]["novel_prediction"] = {
                    "action": {"action": demonstration_action},
                    "scope": {
                        "representation": "CELLS",
                        "cells": [[0, 0]],
                    },
                    "predicate": "PATTERN_TRANSLATION",
                    "expected_parameters": {
                        "before_footprint": [[0, 0]],
                        "after_footprint": [[0, 1]],
                        "displacement": [0, 1],
                    },
                    "because": "Explain why the observed ego law predicts this exact future motion.",
                    "novelty": "Explain why this test occurs from a later, untested grid state.",
                }
                view["answer_template_note"] = (
                    "Replace the example footprint, displacement, and prose with the observed subject. "
                    "Keep the nested object and list shapes exactly as shown."
                )
        return view

    def gate_audit_view(self, *, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        offset = max(0, int(offset))
        limit = max(1, min(50, int(limit)))
        snapshot = self.snapshot()
        coverage = list(snapshot.pop("coverage", []))
        snapshot.pop("coverage_certificate", None)
        snapshot.pop("control_archetype_prior", None)
        evidence_ids = list(snapshot.pop("evidence_ids", []))
        reuse_events = list(snapshot.pop("reuse_events", []))
        unknown = (
            list(self.ego.coordinate_coverage.unknown_candidates())
            if self.ego._coordinate_enabled
            else []
        )
        return {
            "schema": SCHEMA_VERSION,
            "gate": snapshot,
            "page": {"offset": offset, "limit": limit},
            "coverage_total": len(coverage),
            "coverage": coverage[offset:offset + limit],
            "evidence_total": len(evidence_ids),
            "evidence_ids": evidence_ids[offset:offset + limit],
            "reuse_total": len(reuse_events),
            "reuse_events": reuse_events[offset:offset + limit],
            "coordinate_unknown_total": len(unknown),
            "coordinate_unknown_members": [
                asdict(item) for item in unknown[offset:offset + limit]
            ],
        }

    def entity_view(self, entity_id: str, *, offset: int = 0, limit: int = 128) -> dict[str, Any]:
        if self.gate_id not in {LEVER_GATE_ID, *G4_GATE_IDS}:
            raise GateContractError("entity detail queries open at G3 and remain available in G4.")
        return self._adapters[LEVER_GATE_ID].entity_view(entity_id, offset=offset, limit=limit)

    def inventory_view(self, *, offset: int = 0, limit: int = 10) -> dict[str, Any]:
        if self.gate_id not in {LEVER_GATE_ID, *G4_GATE_IDS}:
            raise GateContractError("inventory detail queries open at G3 and remain available in G4.")
        return self._adapters[LEVER_GATE_ID].inventory_view(offset=offset, limit=limit)

    def reaction_view(self, entity_id: str) -> dict[str, Any]:
        if self.gate_id not in G4_GATE_IDS:
            raise GateContractError("reaction detail queries open at G4.")
        return self._adapters[REACTION_GATE_ID].reaction_view(entity_id)

    def orbit_view(self, entity_id: str) -> dict[str, Any]:
        if self.gate_id not in {ORBIT_GATE_ID, RELATION_GATE_ID, LAW_GATE_ID}:
            raise GateContractError("orbit detail queries open at G4.2.")
        return self._adapters[ORBIT_GATE_ID].orbit_view(entity_id)

    def relations_view(self) -> dict[str, Any]:
        if self.gate_id not in {RELATION_GATE_ID, LAW_GATE_ID}:
            raise GateContractError("the G4-B prediction ledger opens at G4-B.")
        return self._adapters[RELATION_GATE_ID].relations_view()

    def evidence_view(self, evidence_id: str) -> dict[str, Any]:
        requested = str(evidence_id or "").strip()
        if not requested:
            raise GateContractError("evidence query requires a non-empty evidence_id.")
        events = (*self.ego.evidence, *self.counter.evidence)
        event = next(
            (item for item in events if str(item.get("evidence_id")) == requested), None
        )
        if event is not None:
            return {
                "schema": SCHEMA_VERSION,
                "evidence_id": requested,
                "gate_id": event.get("gate_id"),
                "probe_id": event.get("probe_id"),
                "observation": event.get("outcome"),
            }
        lever = self._adapters[LEVER_GATE_ID]
        for attributions in lever.evidence._attributions.values():
            for attribution in attributions:
                if str(attribution.evidence_ref) == requested:
                    return {
                        "schema": SCHEMA_VERSION,
                        "evidence_id": requested,
                        "gate_id": LEVER_GATE_ID,
                        "probe_id": (
                            f"{LEVER_GATE_ID}:EVIDENCE:{attribution.transition_id}"
                        ),
                        "observation": asdict(attribution),
                    }
        raise GateContractError(f"Unknown gate evidence_id {requested!r}.")

    def snapshot(self) -> dict[str, Any]:
        return self._active_adapter().snapshot()


def _normalize_action_payload(raw: Any) -> dict[str, Any]:
    if isinstance(raw, str):
        raw = {"action": raw}
    if not isinstance(raw, Mapping):
        raise GateContractError("Each probe action must be an action object.")
    name = _opaque_action_name(raw.get("action"))
    payload: dict[str, Any] = {"action": name}
    if _action_number(name) == 6:
        if isinstance(raw.get("row"), bool) or isinstance(raw.get("col"), bool):
            raise GateContractError("ACTION6 row and col must be integers.")
        if not isinstance(raw.get("row"), int) or not isinstance(raw.get("col"), int):
            raise GateContractError("ACTION6 requires integer row and col.")
        payload.update(row=int(raw["row"]), col=int(raw["col"]))
    elif "row" in raw or "col" in raw:
        raise GateContractError(f"{name} does not accept coordinates in the current metadata.")
    return payload


def _strings(raw: Any, field: str, *, required: bool = True) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        raise GateContractError(f"{field} must be a list of strings.")
    values = tuple(str(value).strip() for value in raw if str(value).strip())
    if required and not values:
        raise GateContractError(f"{field} must not be empty.")
    return values


def _coordinate_cells(raw: Any, field: str) -> tuple[tuple[int, int], ...]:
    if not isinstance(raw, (list, tuple)) or not raw:
        raise GateContractError(f"{field} must be a non-empty list of [row, col] cells.")
    cells: list[tuple[int, int]] = []
    for item in raw:
        if not isinstance(item, (list, tuple)) or len(item) != 2:
            raise GateContractError(f"{field} must contain only [row, col] cells.")
        row, col = item
        if isinstance(row, bool) or isinstance(col, bool):
            raise GateContractError(f"{field} coordinates must be integers.")
        try:
            cells.append((int(row), int(col)))
        except (TypeError, ValueError) as exc:
            raise GateContractError(f"{field} coordinates must be integers.") from exc
    if len(set(cells)) != len(cells):
        raise GateContractError(f"{field} must not contain duplicate cells.")
    return tuple(cells)


def _explanatory_text(raw: Any) -> str:
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, Mapping):
        preferred = (
            "law", "description", "effect", "transformation", "mechanism",
            "subject", "name", "role",
        )
        parts = [str(raw[key]).strip() for key in preferred if str(raw.get(key) or "").strip()]
        if parts:
            return "; ".join(dict.fromkeys(parts))
        return _canonical(raw)
    return str(raw or "").strip()


def _normalize_subjects(raw: Any) -> tuple[str, ...]:
    if not isinstance(raw, (list, tuple)):
        raise GateContractError("subjects must be a list of explanatory strings or objects.")
    values = tuple(_explanatory_text(value) for value in raw if _explanatory_text(value))
    if not values:
        raise GateContractError("subjects must not be empty.")
    return values


def _normalize_action_laws(raw: Any) -> dict[str, str]:
    rows: Iterable[tuple[Any, Any]]
    if isinstance(raw, Mapping):
        rows = raw.items()
    elif isinstance(raw, (list, tuple)):
        normalized_rows = []
        for item in raw:
            if not isinstance(item, Mapping) or not item.get("action"):
                raise GateContractError(
                    "Each action_laws list item must contain action plus an explanatory law/effect."
                )
            value = next(
                (item.get(key) for key in ("law", "description", "effect", "transformation", "mechanism")
                 if item.get(key) is not None),
                {key: value for key, value in item.items() if key != "action"},
            )
            normalized_rows.append((item["action"], value))
        rows = normalized_rows
    else:
        raise GateContractError(
            "action_laws must be an object keyed by opaque action, or a list of objects with action and law."
        )
    laws = {_opaque_action_name(key): _explanatory_text(value) for key, value in rows}
    if not laws or any(len(value.split()) < 3 for value in laws.values()):
        raise GateContractError(
            "Each action law must describe an observed transformation in at least three words."
        )
    return laws


def _normalize_action_law_specs(raw: Any) -> dict[str, dict[str, Any]]:
    """Retain structured law fields without trying to infer motion from prose."""
    if not isinstance(raw, (list, tuple)):
        return {}
    specs: dict[str, dict[str, Any]] = {}
    for item in raw:
        if not isinstance(item, Mapping) or not item.get("action"):
            continue
        action = _opaque_action_name(item["action"])
        spec = {str(key): value for key, value in item.items() if key != "action"}
        displacement = spec.get("displacement")
        if isinstance(displacement, Mapping) and {"row", "col"} <= set(displacement):
            spec["displacement"] = [int(displacement["row"]), int(displacement["col"])]
        specs[action] = spec
    return specs


def _normalize_novel_prediction(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise GateContractError("novel_prediction must describe a new testable transition.")
    prediction = dict(raw)
    if not isinstance(prediction.get("scope"), Mapping):
        representation = prediction.pop("scope.representation", None)
        if representation is not None:
            scope = {"representation": representation}
            for name in ("cells", "region", "identifier"):
                dotted = f"scope.{name}"
                if dotted in prediction:
                    scope[name] = prediction.pop(dotted)
            prediction["scope"] = scope
        elif isinstance(prediction.get("scope"), str):
            prediction["scope"] = {"representation": prediction["scope"]}
    expected = prediction.get("expected_parameters")
    if isinstance(expected, Mapping):
        expected = dict(expected)
        displacement = expected.get("displacement")
        if isinstance(displacement, Mapping) and {"row", "col"} <= set(displacement):
            expected["displacement"] = [displacement["row"], displacement["col"]]
        prediction["expected_parameters"] = expected
    return prediction


def _answer_from_mapping(
    raw: Mapping[str, Any], *, interface_pointer: bool = False
) -> GateAnswer:
    if not isinstance(raw, Mapping):
        raise GateContractError("gate_answer requires an answer object.")
    required_text = ("answer_id", "answer_kind", "mechanism", "falsifier")
    text = {field: str(raw.get(field) or "").strip() for field in required_text}
    missing = [field for field, value in text.items() if not value]
    if missing:
        raise GateContractError(f"GateAnswer missing explanatory fields: {', '.join(missing)}.")
    if len(text["mechanism"].split()) < 4:
        raise GateContractError("mechanism must explain what the ego is and how control changes it; a label is insufficient.")
    laws = _normalize_action_laws(raw.get("action_laws"))
    law_specs = _normalize_action_law_specs(raw.get("action_laws"))
    prediction = raw.get("novel_prediction", {})
    if not interface_pointer:
        prediction = _normalize_novel_prediction(prediction)
    if interface_pointer and not isinstance(prediction, Mapping):
        prediction = {}
    return GateAnswer(
        answer_id=text["answer_id"],
        answer_kind=text["answer_kind"],
        subjects=_normalize_subjects(raw.get("subjects")),
        mechanism=text["mechanism"],
        action_laws=laws,
        conditions=_strings(raw.get("conditions", []), "conditions", required=False),
        constraints=_strings(raw.get("constraints", []), "constraints", required=False),
        evidence_refs=(
            (ACTION_METADATA_GATE_ID,)
            if interface_pointer
            else _strings(raw.get("evidence_refs"), "evidence_refs")
        ),
        competing_models=_strings(raw.get("competing_models"), "competing_models"),
        falsifier=text["falsifier"],
        novel_prediction=dict(prediction),
        limitations=_strings(raw.get("limitations", []), "limitations", required=False),
        action_law_specs=law_specs,
    )


__all__ = [
    "ActionAffordance",
    "ActionMetadataAnswer",
    "ACTION_METADATA_GATE_ID",
    "CoverageItem",
    "CyberneticGateMachine",
    "EgoGateMachine",
    "GateAnswer",
    "GateContractError",
    "ProbeEnvelope",
    "SCHEMA_VERSION",
    "action_affordances",
]
