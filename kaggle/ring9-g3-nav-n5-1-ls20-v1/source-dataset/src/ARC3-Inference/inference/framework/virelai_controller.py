"""Deterministic, replay-only decision controller over admitted Virelai facts.

This module does not act, prompt Duck, or invent semantic evidence.  It turns a
canonical WorldModel into a versioned rule set and one bounded focus record.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
import hashlib
import json
from typing import Any, Iterable

from inference.framework.virelai_world_model import MechanicRule, WorldModel


CONTROLLER_SCHEMA = "virelai-decision-controller-v1"
PHASES = (
    "CONTROL",
    "AUTONOMY",
    "INTERACTIONS",
    "ROLE_DEPTH",
    "PHYSICS_GRAMMAR",
    "WIN_SEARCH",
    "WIN_ANALYSIS",
    "TRANSFER",
    "REPRESENTATION_REPAIR",
)
RULE_STATUSES = frozenset({"CANDIDATE", "OBSERVED", "CONTRADICTED", "SUPERSEDED"})
DECISION_PURPOSES = frozenset(
    {"EXPLORE", "NAVIGATE", "TEST_RULE", "PURSUE_WIN", "RECONFIRM_TRANSFER"}
)
PREDICTION_EXPECTATIONS = frozenset({"CHANGED", "UNCHANGED"})
SCOPE_REPRESENTATIONS = frozenset({"WORLDLINE", "REGION", "CELLS", "VISIBLE_OBSERVATION"})


@dataclass(frozen=True)
class RuleVersion:
    rule_version_id: str
    source_rule_id: str
    family: str
    version: int
    status: str
    level_scope: tuple[int, ...]
    trigger_action: str
    subject_ids: tuple[str, ...]
    affected_ids: tuple[str, ...]
    state_variable_id: str | None
    condition: str
    predicted_transformation: str
    predicted_from: str | None
    predicted_to: str | None
    witness_transition_ids: tuple[int, ...]
    contradiction_transition_ids: tuple[int, ...]
    parent_rule_version_id: str | None = None
    distinction_needed: str | None = None
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class PhaseContract:
    phase: str
    purpose: str
    obligations: tuple[str, ...]
    opening_rule: str
    advance_rule: str
    defer_rule: str
    reopen_rule: str


@dataclass(frozen=True)
class FocusCandidate:
    phase: str
    reason: str
    evidence_transition_ids: tuple[int, ...]
    applicable_rule_version_ids: tuple[str, ...]
    obligation: str


@dataclass(frozen=True)
class FocusState:
    focus_id: str
    phase: str
    status: str
    reason: str
    obligation: str
    evidence_transition_ids: tuple[int, ...]
    applicable_rule_version_ids: tuple[str, ...]
    alternatives: tuple[FocusCandidate, ...]
    deferred_phases: tuple[str, ...]
    model_step: int


@dataclass(frozen=True)
class ControllerSnapshot:
    schema: str
    game_id: str
    model_version: int
    observed_through_step: int
    phase_contracts: tuple[PhaseContract, ...]
    rule_versions: tuple[RuleVersion, ...]
    focus: FocusState


@dataclass(frozen=True)
class ActionSpec:
    action: str
    parameters: tuple[tuple[str, int | str], ...] = ()


@dataclass(frozen=True)
class ScopeSpec:
    representation: str
    identifier: str | None = None
    region: tuple[int, int, int, int] | None = None
    cells: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class PredictionSpec:
    claim_id: str | None
    expected: str
    scope: ScopeSpec
    falsifier: str | None = None


@dataclass(frozen=True)
class FocusProposal:
    question: str
    reason: str
    evidence_transition_ids: tuple[int, ...] = ()


@dataclass(frozen=True)
class DecisionEnvelope:
    decision_id: str
    focus_id: str
    purpose: str
    actions: tuple[ActionSpec, ...]
    prediction: PredictionSpec | None
    proposed_focus: FocusProposal | None
    declared_at_transition: int
    win_reference_id: str | None = None


@dataclass(frozen=True)
class DecisionReceipt:
    decision_id: str
    accepted: bool
    executed_actions: tuple[ActionSpec, ...]
    result: Any = None
    error: str | None = None


@dataclass(frozen=True)
class OutcomeComparison:
    comparison_id: str
    decision_id: str
    transition_id: int
    outcome: str
    scoped_observation: tuple[tuple[str, Any], ...]
    remote_observation: tuple[tuple[str, Any], ...]
    autonomous_observation: tuple[tuple[str, Any], ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class RevisionEvent:
    revision_id: str
    parent_rule_version_id: str | None
    resulting_rule_version_id: str | None
    decision_id: str
    comparison_id: str
    revision_kind: str
    explanation: str


def phase_contracts() -> tuple[PhaseContract, ...]:
    """Operational contracts: each purpose carries a completion obligation."""
    rows = (
        ("CONTROL", "identify what the player can directly control", "name one action-linked controlled subject or preserve control as unknown"),
        ("AUTONOMY", "separate action effects from repeated action-independent change", "record a repeated visible process with witnesses or defer autonomy"),
        ("INTERACTIONS", "identify which action-subject pairs produce visible changes", "record one scoped action/effect rule or preserve the missing interaction"),
        ("ROLE_DEPTH", "resolve the operating details of an admitted interaction", "bind its direction, magnitude, period, endpoint, or an explicit missing field"),
        ("PHYSICS_GRAMMAR", "express admitted mechanics as predictive state transitions", "create a versioned rule with a condition and predicted transformation"),
        ("WIN_SEARCH", "seek a novel state using the admitted grammar", "name the unresolved state distinction that blocks a win prediction"),
        ("WIN_ANALYSIS", "describe the observed win boundary without promoting correlation to cause", "preserve the winning edge, separators, and causal uncertainty"),
        ("TRANSFER", "compare prior-level knowledge with the new level", "name what persisted, changed, and requires reconfirmation"),
        ("REPRESENTATION_REPAIR", "repair a world-model gap that prevents a valid prediction", "name the missing representation and the evidence needed to add it"),
    )
    return tuple(
        PhaseContract(
            phase=phase,
            purpose=purpose,
            obligations=(obligation,),
            opening_rule=f"open when {phase.lower()} is the highest-priority unmet obligation",
            advance_rule=f"advance when the {phase.lower()} obligation is represented by admitted evidence",
            defer_rule="defer when no admissible observation can currently resolve it",
            reopen_rule="reopen on contradiction, level change, or newly admitted distinguishing evidence",
        )
        for phase, purpose, obligation in rows
    )


def compile_rule_versions(model: WorldModel) -> tuple[RuleVersion, ...]:
    """Compile version 1 rules; no confidence floats and no causal promotion."""
    variable_by_owner = {
        variable.owner_id: variable.variable_id for variable in model.state_variables
    }
    rows = []
    for rule in sorted(model.mechanics, key=lambda item: item.rule_id):
        family = _rule_family(rule)
        predicted_from, predicted_to = _state_edge(rule)
        witnesses = tuple(sorted(set(rule.witness_transition_ids)))
        contradictions = tuple(sorted(set(rule.counterexample_transition_ids)))
        condition = rule.condition or "; ".join(rule.preconditions) or "CONDITION_UNRESOLVED"
        limitations = []
        if not rule.subject_ids and not rule.trigger_object_type:
            limitations.append("Trigger subject is unresolved.")
        if condition == "CONDITION_UNRESOLVED":
            limitations.append("Activation condition is unresolved.")
        if family != "DISCRETE_STATE_TRANSITION":
            limitations.append("No discrete before/after state edge is admitted.")
        seed = f"{rule.rule_id}|v1|{family}|{condition}|{rule.transformation}"
        rows.append(RuleVersion(
            rule_version_id="RV-" + hashlib.sha256(seed.encode()).hexdigest()[:12],
            source_rule_id=rule.rule_id,
            family=family,
            version=1,
            status=rule.status,
            level_scope=tuple(sorted(set(rule.levels_observed))),
            trigger_action=rule.trigger_action,
            subject_ids=tuple(sorted(set(rule.subject_ids or (() if rule.trigger_object_type is None else (rule.trigger_object_type,))))),
            affected_ids=tuple(sorted(set(rule.affected_ids))),
            state_variable_id=next((variable_by_owner[item] for item in rule.affected_ids if item in variable_by_owner), None),
            condition=condition,
            predicted_transformation=rule.transformation,
            predicted_from=predicted_from,
            predicted_to=predicted_to,
            witness_transition_ids=witnesses,
            contradiction_transition_ids=contradictions,
            distinction_needed=("exact discrete before/after state" if family != "DISCRETE_STATE_TRANSITION" else None),
            limitations=tuple(limitations),
        ))
    return tuple(rows)


def build_controller_snapshot(model: WorldModel) -> ControllerSnapshot:
    rules = compile_rule_versions(model)
    candidates = _focus_candidates(model, rules)
    chosen = candidates[0]
    alternatives = tuple(candidates[1:3])
    seed = f"{model.game_id}|{model.model_version}|{model.observed_through_step}|{chosen.phase}|{chosen.reason}"
    focus = FocusState(
        focus_id="F-" + hashlib.sha256(seed.encode()).hexdigest()[:12],
        phase=chosen.phase,
        status="OPEN",
        reason=chosen.reason,
        obligation=chosen.obligation,
        evidence_transition_ids=chosen.evidence_transition_ids,
        applicable_rule_version_ids=chosen.applicable_rule_version_ids,
        alternatives=alternatives,
        deferred_phases=tuple(phase for phase in PHASES if phase not in {chosen.phase, *(item.phase for item in alternatives)}),
        model_step=model.observed_through_step,
    )
    snapshot = ControllerSnapshot(
        schema=CONTROLLER_SCHEMA,
        game_id=model.game_id,
        model_version=model.model_version,
        observed_through_step=model.observed_through_step,
        phase_contracts=phase_contracts(),
        rule_versions=rules,
        focus=focus,
    )
    validate_controller_snapshot(snapshot, model)
    return snapshot


def canonical_controller_bytes(snapshot: ControllerSnapshot) -> bytes:
    return (json.dumps(_canonical(snapshot), sort_keys=True, separators=(",", ":")) + "\n").encode()


def decision_envelope_from_dict(
    payload: dict[str, Any], *, actions: Iterable[str | dict[str, Any]], declared_at_transition: int
) -> DecisionEnvelope:
    """Parse one prospective declaration and the exact actions it accompanies."""
    action_specs = tuple(_action_spec(item) for item in actions)
    prediction_payload = payload.get("prediction")
    prediction = None
    if prediction_payload is not None:
        if not isinstance(prediction_payload, dict):
            raise ValueError("prediction must be an object")
        scope_payload = prediction_payload.get("scope")
        if not isinstance(scope_payload, dict):
            raise ValueError("prediction scope must be an object")
        scope = ScopeSpec(
            representation=str(scope_payload.get("representation") or "").upper(),
            identifier=(str(scope_payload["identifier"]) if scope_payload.get("identifier") is not None else None),
            region=(tuple(int(value) for value in scope_payload["region"]) if scope_payload.get("region") is not None else None),
            cells=tuple(tuple(int(value) for value in cell) for cell in scope_payload.get("cells", ())),
        )
        prediction = PredictionSpec(
            claim_id=(str(prediction_payload["claim_id"]) if prediction_payload.get("claim_id") is not None else None),
            expected=str(prediction_payload.get("expected") or "").upper(),
            scope=scope,
            falsifier=(str(prediction_payload["falsifier"]) if prediction_payload.get("falsifier") is not None else None),
        )
    proposal_payload = payload.get("proposed_focus")
    proposal = None
    if proposal_payload is not None:
        if not isinstance(proposal_payload, dict):
            raise ValueError("proposed_focus must be an object")
        proposal = FocusProposal(
            question=str(proposal_payload.get("question") or "").strip(),
            reason=str(proposal_payload.get("reason") or "").strip(),
            evidence_transition_ids=tuple(sorted(set(int(value) for value in proposal_payload.get("evidence_transition_ids", ())))),
        )
    seed_payload = {
        "focus_id": payload.get("focus_id"),
        "purpose": payload.get("purpose"),
        "actions": _canonical(action_specs),
        "prediction": _canonical(prediction),
        "proposal": _canonical(proposal),
        "declared_at_transition": declared_at_transition,
    }
    decision_id = str(payload.get("decision_id") or "D-" + hashlib.sha256(json.dumps(seed_payload, sort_keys=True).encode()).hexdigest()[:12])
    return DecisionEnvelope(
        decision_id=decision_id,
        focus_id=str(payload.get("focus_id") or ""),
        purpose=str(payload.get("purpose") or "").upper(),
        actions=action_specs,
        prediction=prediction,
        proposed_focus=proposal,
        declared_at_transition=max(0, int(declared_at_transition)),
        win_reference_id=(str(payload["win_reference_id"]) if payload.get("win_reference_id") is not None else None),
    )


def validate_decision_envelope(
    envelope: DecisionEnvelope, *, active_focus_id: str, legal_actions: Iterable[str]
) -> None:
    if envelope.focus_id != active_focus_id:
        raise ValueError(f"stale focus; active focus is {active_focus_id}")
    if envelope.purpose not in DECISION_PURPOSES:
        raise ValueError(f"invalid purpose: {envelope.purpose}")
    if not envelope.actions:
        raise ValueError("at least one action is required")
    legal = {str(item).upper() for item in legal_actions}
    illegal = [item.action for item in envelope.actions if item.action.upper() not in legal]
    if illegal:
        raise ValueError(f"illegal action: {illegal[0]}")
    if envelope.purpose in {"TEST_RULE", "RECONFIRM_TRANSFER"}:
        if len(envelope.actions) != 1:
            raise ValueError("prospective tests require exactly one action")
        if envelope.prediction is None:
            raise ValueError("this purpose requires a prospective prediction and scope")
    if envelope.prediction is not None:
        if envelope.prediction.expected not in PREDICTION_EXPECTATIONS and not envelope.prediction.claim_id:
            raise ValueError("mechanic-specific expectations require a referenced claim")
        scope = envelope.prediction.scope
        if scope.representation not in SCOPE_REPRESENTATIONS:
            raise ValueError("invalid prediction scope representation")
        if scope.representation == "WORLDLINE" and not scope.identifier:
            raise ValueError("WORLDLINE scope requires identifier")
        if scope.representation == "REGION" and (scope.region is None or len(scope.region) != 4):
            raise ValueError("REGION scope requires four coordinates")
        if scope.representation == "CELLS" and not scope.cells:
            raise ValueError("CELLS scope requires at least one cell")
    if envelope.purpose == "PURSUE_WIN" and not envelope.win_reference_id:
        raise ValueError("PURSUE_WIN requires a prior win or win-hypothesis reference")
    if envelope.proposed_focus is not None and (
        not envelope.proposed_focus.question or not envelope.proposed_focus.reason
    ):
        raise ValueError("focus proposals require a question and reason")


class ControllerActionBridge:
    """Stage-B atomic gate. The supplied executor is called only after validation."""

    def __init__(self, *, active_focus_id: str, legal_actions: Iterable[str], executor: Any):
        self.active_focus_id = active_focus_id
        self.legal_actions = tuple(legal_actions)
        self.executor = executor
        self.receipts: list[DecisionReceipt] = []
        self._accepted: dict[str, DecisionReceipt] = {}

    def execute(self, envelope: DecisionEnvelope) -> DecisionReceipt:
        if envelope.decision_id in self._accepted:
            return self._accepted[envelope.decision_id]
        try:
            validate_decision_envelope(
                envelope,
                active_focus_id=self.active_focus_id,
                legal_actions=self.legal_actions,
            )
        except ValueError as exc:
            receipt = DecisionReceipt(
                decision_id=envelope.decision_id,
                accepted=False,
                executed_actions=(),
                error=f"{exc}. Use focus_id={self.active_focus_id} and a valid declared purpose.",
            )
            self.receipts.append(receipt)
            return receipt
        result = self.executor(envelope.actions)
        receipt = DecisionReceipt(
            decision_id=envelope.decision_id,
            accepted=True,
            executed_actions=envelope.actions,
            result=result,
        )
        self._accepted[envelope.decision_id] = receipt
        self.receipts.append(receipt)
        return receipt


def compare_outcome(
    envelope: DecisionEnvelope,
    transition: Any,
    *,
    resolved_scope_cells: Iterable[tuple[int, int]] | None = None,
    autonomous_cells: Iterable[tuple[int, int]] = (),
) -> OutcomeComparison:
    """Compare one prospective prediction with its exact resulting transition.

    WORLDLINE scope must be resolved by the identity layer at the pre-action
    boundary.  A missing resolution is explicit and never silently widened.
    """
    transition_id = int(transition.transition_id)
    comparison_id = "OC-" + hashlib.sha256(
        f"{envelope.decision_id}|{transition_id}".encode()
    ).hexdigest()[:12]
    if len(envelope.actions) != 1 or not _action_matches_transition(
        envelope.actions[0], transition
    ):
        return OutcomeComparison(
            comparison_id, envelope.decision_id, transition_id, "UNMATCHED",
            (("reason", "executed transition does not match the declared interaction"),), (), (),
            ("No rule revision is permitted.",),
        )
    if envelope.prediction is None:
        return OutcomeComparison(
            comparison_id, envelope.decision_id, transition_id, "UNMATCHED",
            (("reason", "decision carried no prospective prediction"),), (), (),
            ("No rule revision is permitted.",),
        )
    if getattr(transition, "geometry_changed", False) or any(
        bool(getattr(transition, field, False))
        for field in ("level_completed", "game_over", "run_complete")
    ):
        return OutcomeComparison(
            comparison_id, envelope.decision_id, transition_id, "INDETERMINATE",
            (("reason", "geometry or terminal boundary"),), (), (),
            ("Boundary transitions require separate interpretation.",),
        )
    scope = envelope.prediction.scope
    scope_cells: set[tuple[int, int]] | None
    if scope.representation == "VISIBLE_OBSERVATION":
        scope_cells = None
    elif scope.representation == "CELLS":
        scope_cells = set(scope.cells)
    elif scope.representation == "REGION" and scope.region is not None:
        r0, c0, r1, c1 = scope.region
        scope_cells = {(row, col) for row in range(r0, r1 + 1) for col in range(c0, c1 + 1)}
    elif scope.representation == "WORLDLINE":
        if resolved_scope_cells is None:
            return OutcomeComparison(
                comparison_id, envelope.decision_id, transition_id, "INDETERMINATE",
                (("reason", "worldline identity was not resolved at the pre-action boundary"),), (), (),
                ("Representation gap opened; scope was not widened.",),
            )
        scope_cells = set(resolved_scope_cells)
    else:
        return OutcomeComparison(
            comparison_id, envelope.decision_id, transition_id, "INDETERMINATE",
            (("reason", "scope representation unavailable"),), (), (),
            ("Scope was not widened.",),
        )
    deltas = tuple(getattr(transition, "cell_deltas", ()))
    changed_cells = {(int(item.row), int(item.col)) for item in deltas}
    scoped_changed = changed_cells if scope_cells is None else changed_cells & scope_cells
    remote_changed = set() if scope_cells is None else changed_cells - scope_cells
    autonomous_changed = changed_cells & set(autonomous_cells)
    observed = "CHANGED" if scoped_changed else "UNCHANGED"
    expected = envelope.prediction.expected
    if expected in PREDICTION_EXPECTATIONS:
        outcome = "SUPPORTED" if observed == expected else "CONTRADICTED"
    else:
        outcome = "INDETERMINATE"
    limitations = ["Verdict applies only to the declared scope."]
    if remote_changed:
        limitations.append("Remote changes were observed separately and do not reverse the scoped verdict.")
    if expected not in PREDICTION_EXPECTATIONS:
        limitations.append("Mechanic-specific expectation requires a transformation matcher.")
    return OutcomeComparison(
        comparison_id=comparison_id,
        decision_id=envelope.decision_id,
        transition_id=transition_id,
        outcome=outcome,
        scoped_observation=(("observed", observed), ("changed_cells", tuple(sorted(scoped_changed)))),
        remote_observation=(("changed_cells", tuple(sorted(remote_changed))),),
        autonomous_observation=(("changed_cells", tuple(sorted(autonomous_changed))),),
        limitations=tuple(limitations),
    )


def revise_rule(
    parent: RuleVersion | None,
    envelope: DecisionEnvelope,
    comparison: OutcomeComparison,
) -> tuple[RuleVersion | None, RevisionEvent]:
    """Append one version; the parent object is never mutated or discarded."""
    kind = {
        "SUPPORTED": "SUPPORTED",
        "CONTRADICTED": "CONTRADICTED",
        "INDETERMINATE": "NO_SEMANTIC_CHANGE",
        "UNMATCHED": "NO_SEMANTIC_CHANGE",
    }[comparison.outcome]
    resulting = None
    if parent is not None and kind in {"SUPPORTED", "CONTRADICTED"}:
        witnesses = parent.witness_transition_ids
        contradictions = parent.contradiction_transition_ids
        status = parent.status
        if kind == "SUPPORTED":
            witnesses = tuple(sorted(set((*witnesses, comparison.transition_id))))
        else:
            contradictions = tuple(sorted(set((*contradictions, comparison.transition_id))))
            status = "CONTRADICTED"
        seed = f"{parent.source_rule_id}|v{parent.version + 1}|{comparison.comparison_id}|{kind}"
        resulting = RuleVersion(
            **{
                **asdict(parent),
                "rule_version_id": "RV-" + hashlib.sha256(seed.encode()).hexdigest()[:12],
                "version": parent.version + 1,
                "status": status,
                "witness_transition_ids": witnesses,
                "contradiction_transition_ids": contradictions,
                "parent_rule_version_id": parent.rule_version_id,
            }
        )
    revision_seed = f"{envelope.decision_id}|{comparison.comparison_id}|{kind}"
    revision = RevisionEvent(
        revision_id="RE-" + hashlib.sha256(revision_seed.encode()).hexdigest()[:12],
        parent_rule_version_id=parent.rule_version_id if parent else None,
        resulting_rule_version_id=resulting.rule_version_id if resulting else None,
        decision_id=envelope.decision_id,
        comparison_id=comparison.comparison_id,
        revision_kind=kind,
        explanation=(
            f"{comparison.outcome} against the exact declared scope at transition "
            f"{comparison.transition_id}; parent evidence remains preserved."
        ),
    )
    return resulting, revision


def validate_controller_snapshot(snapshot: ControllerSnapshot, model: WorldModel | None = None) -> None:
    if snapshot.schema != CONTROLLER_SCHEMA:
        raise ValueError("unsupported controller schema")
    if snapshot.focus.phase not in PHASES or len(snapshot.focus.alternatives) > 2:
        raise ValueError("invalid bounded focus")
    if not snapshot.focus.obligation:
        raise ValueError("focus requires an obligation")
    rule_ids = {item.rule_version_id for item in snapshot.rule_versions}
    for rule in snapshot.rule_versions:
        if rule.status not in RULE_STATUSES or rule.version < 1:
            raise ValueError(f"invalid rule version: {rule.rule_version_id}")
        if not rule.witness_transition_ids and rule.status == "OBSERVED":
            raise ValueError(f"observed rule lacks witnesses: {rule.rule_version_id}")
    candidates = (snapshot.focus,) + snapshot.focus.alternatives
    for candidate in candidates:
        missing = set(candidate.applicable_rule_version_ids) - rule_ids
        if missing:
            raise ValueError(f"focus references unknown rules: {sorted(missing)}")
    if model is not None:
        known_evidence = {
            evidence.transition_id for claim in model.claims for evidence in claim.evidence
        } | {item for rule in model.mechanics for item in (*rule.witness_transition_ids, *rule.counterexample_transition_ids)}
        for candidate in candidates:
            missing = set(candidate.evidence_transition_ids) - known_evidence
            if missing:
                raise ValueError(f"focus references unknown evidence: {sorted(missing)}")


def _focus_candidates(model: WorldModel, rules: tuple[RuleVersion, ...]) -> tuple[FocusCandidate, ...]:
    by_level = tuple(rule for rule in rules if model.current_level in rule.level_scope)
    observed = tuple(rule for rule in by_level if rule.status == "OBSERVED")
    discrete = tuple(rule for rule in observed if rule.family == "DISCRETE_STATE_TRANSITION")
    wins_before = tuple(win for win in model.wins if win.completed_level < model.current_level)
    candidates: list[FocusCandidate] = []
    if wins_before:
        win = sorted(wins_before, key=lambda item: (item.completed_level, item.transition_id))[-1]
        candidates.append(_candidate("TRANSFER", "A prior-level win exists and the present level requires a persistence/change comparison.", (win.transition_id,), (), "name what persisted, changed, and requires reconfirmation"))
    current_win = next((win for win in reversed(model.wins) if win.completed_level == model.current_level), None)
    if current_win and model.observed_through_step <= current_win.transition_id + 1:
        candidates.append(_candidate("WIN_ANALYSIS", "A new win boundary has just been observed.", (current_win.transition_id,), (), "preserve the winning edge and causal uncertainty"))
    representation_gaps = tuple(item for item in model.unknowns if any(word in item.lower() for word in ("identity", "representation", "semantic adapter")))
    if representation_gaps and not model.objects:
        candidates.append(_candidate("REPRESENTATION_REPAIR", representation_gaps[0], (), (), "name the missing representation and evidence required"))
    if not observed:
        candidates.append(_candidate("CONTROL", "No observed action-linked mechanic is admitted for the current level.", (), (), "identify a controlled subject or preserve control as unknown"))
    elif not discrete:
        evidence = tuple(sorted({item for rule in observed for item in rule.witness_transition_ids}))
        candidates.append(_candidate("ROLE_DEPTH", "Current-level effects exist but lack an admitted discrete before/after state edge.", evidence, tuple(rule.rule_version_id for rule in observed), "resolve the exact state edge or preserve it as missing"))
    else:
        evidence = tuple(sorted({item for rule in discrete for item in rule.witness_transition_ids}))
        candidates.append(_candidate("PHYSICS_GRAMMAR", "Current-level mechanics support discrete predictive state transitions.", evidence, tuple(rule.rule_version_id for rule in discrete), "maintain versioned conditional predictions"))
    autonomous = tuple(rule for rule in observed if rule.trigger_action == "ANY_OBSERVED_DUCK_ACTION")
    if autonomous:
        candidates.append(_candidate("AUTONOMY", "A repeated visible process is admitted across diverse actions.", tuple(sorted({item for rule in autonomous for item in rule.witness_transition_ids})), tuple(rule.rule_version_id for rule in autonomous), "separate the repeated process from targeted action effects"))
    if not candidates:
        candidates.append(_candidate("WIN_SEARCH", "The admitted grammar has no unresolved earlier phase.", (), tuple(rule.rule_version_id for rule in observed), "name the state distinction blocking a win prediction"))
    priority = {phase: index for index, phase in enumerate(PHASES)}
    # Transfer and a just-observed win override the ordinary epistemic ladder.
    override = {"TRANSFER": -2, "WIN_ANALYSIS": -1}
    candidates.sort(key=lambda item: (override.get(item.phase, priority[item.phase]), item.phase, item.reason))
    deduped = []
    seen = set()
    for item in candidates:
        if item.phase not in seen:
            deduped.append(item)
            seen.add(item.phase)
    return tuple(deduped)


def _candidate(phase: str, reason: str, evidence: Iterable[int], rules: Iterable[str], obligation: str) -> FocusCandidate:
    return FocusCandidate(phase, reason, tuple(sorted(set(evidence))), tuple(sorted(set(rules))), obligation)


def _rule_family(rule: MechanicRule) -> str:
    if _state_edge(rule) != (None, None):
        return "DISCRETE_STATE_TRANSITION"
    return "VISIBLE_TRANSFORMATION"


def _state_edge(rule: MechanicRule) -> tuple[str | None, str | None]:
    for parameter in rule.parameters:
        if parameter.startswith("observed_state_transition="):
            edge = parameter.split("=", 1)[1]
            if "->" in edge:
                left, right = edge.split("->", 1)
                return left.strip() or None, right.strip() or None
    return None, None


def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, dict):
        return {str(key): _canonical(item) for key, item in sorted(value.items(), key=lambda row: str(row[0]))}
    if isinstance(value, (tuple, list)):
        return [_canonical(item) for item in value]
    return value


def _action_spec(value: str | dict[str, Any]) -> ActionSpec:
    if isinstance(value, str):
        action = value.strip().upper()
        parameters: tuple[tuple[str, int | str], ...] = ()
    elif isinstance(value, dict):
        action = str(value.get("action") or "").strip().upper()
        parameters = tuple(
            sorted(
                (str(key), item)
                for key, item in value.items()
                if key != "action" and isinstance(item, (int, str))
            )
        )
    else:
        raise ValueError("actions must be strings or objects")
    if not action:
        raise ValueError("action name is required")
    if action == "MOUSE":
        keys = {key for key, _ in parameters}
        if not {"row", "col"} <= keys:
            raise ValueError("MOUSE requires row and col")
    return ActionSpec(action=action, parameters=parameters)


def _action_matches_transition(action: ActionSpec, transition: Any) -> bool:
    if str(getattr(transition, "actor", "DUCK")).upper() != "DUCK":
        return False
    observed = str(getattr(transition, "action_name", "")).strip().upper()
    action_ids = {"RESET": 0, "UP": 1, "DOWN": 2, "LEFT": 3, "RIGHT": 4, "SPACE": 5, "MOUSE": 6}
    expected_id = action_ids.get(action.action)
    observed_id = getattr(transition, "action_id", None)
    if expected_id is not None and observed_id is not None and int(observed_id) != expected_id:
        return False
    if action.action == "MOUSE":
        params = dict(action.parameters)
        return getattr(transition, "acted_cell", None) == (params.get("row"), params.get("col"))
    return observed in {action.action, f"ACTION{expected_id}"}
