"""The G4-C gate: test the description with one new prediction; certify the law set (R9-R13).

Author: Claude (Alpha build seat), 2026-09-30.

Director rulings (2026-09-30, BUILD_PLAN_G4_CLICK_COMPLETION_v11):
- G4-C is its own thin gate after G4-B. Duck freezes one new prediction drawn from its accepted
  description and names the relations it relies on; the controller takes it.
- SUPPORTED: the gate emits the ``LeverReactionLawSet`` and the level's CLICK G4 is closed.
- CONTRADICTED: G4-B reopens. The contradicted prediction joins G4-B's record, the description is
  withdrawn, and Duck tests more and revises it; G4-C then asks for a new test again.
- New means an untested action and board: no graded prediction (G4-B or G4-C) has taken this action
  from the current counter-masked board.

G4-C reuses G4-B's lever regions, grading and outcome record (``LeverRelationsTarget.take``), so one
record holds every graded transition of the level.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any, Mapping, Sequence

from inference.framework.cybernetic_targeting import GateAssessment, GoalContract, MemoryProduct
from inference.framework.g4_relations import (
    CONTRADICTED, LAW_KIND, SUPPORTED, G4RelationError, Prediction, masked_address, validate_prediction,
)
from inference.framework.g4b_gate import LEVERS_ON_CARD, LeverRelationsTarget, relations_contract
from inference.framework.virelai_gates import (
    LAW_GATE_ID,
    RELATION_GATE_ID,
    GateContractError,
    ProbeEnvelope,
    _canonical,
    _normalize_action_payload,
)

PRODUCT_TYPE = "LeverReactionLawSet"
CLAIM_CHARS = 90  # a relation's claim on the card (axiom A6); the whole claim by virelai('relations')


def law_contract() -> GoalContract:
    return GoalContract(
        goal_id="G4C-LEVER-LAW-v1",
        target_id=LAW_GATE_ID,
        question="Does the description of the lever set predict a case it has not seen?",
        desired_knowledge=(
            "one new prediction drawn from the accepted description, frozen before its test",
            "an action no graded prediction has taken from the current counter-masked board",
            "a supported law set, or a reopened G4-B",
        ),
        prerequisites=(RELATION_GATE_ID,),
        admissible_probe_kinds=("the one action of Duck's frozen law prediction, taken by the controller",),
        completion_predicate=(
            "Stated target: a new prediction drawn from the accepted G4-B description is SUPPORTED; the "
            "LeverReactionLawSet is emitted. A contradiction reopens G4-B."
        ),
        memory_product_type=PRODUCT_TYPE,
    )


def later_contracts() -> tuple[GoalContract, ...]:
    """The G4 gates after G4-A, in ladder order (registered by ``CyberneticGateMachine``)."""
    return relations_contract(), law_contract()


def later_adapters(machine: Any) -> dict[str, Any]:
    return {RELATION_GATE_ID: LeverRelationsTarget(machine), LAW_GATE_ID: LeverLawTarget(machine)}


class LeverLawTarget:
    TARGET = (
        "Test your description of the lever set. Freeze one new prediction drawn from it: an action "
        "or target-bound contact procedure no graded prediction has tested from the current board, "
        "what it will do to every lever's region and to the rest of the board, and the relation "
        "numbers it relies on. The controller executes it and grades only its activation transition. "
        "Supported: the lever law set is certified. Contradicted: G4-B reopens, and you test "
        "more and revise the description."
    )
    DONE_WHEN = (
        "One new prediction drawn from the accepted description is SUPPORTED. A contradicted one stays "
        "on the record and reopens G4-B."
    )
    RULES = (
        f"Freeze it with virelai('gate_answer', answer={{...}}) using the {LAW_KIND} template; from_relations lists the relation numbers shown under subject.relations.",
        "New means untested: an action already graded from this same masked board is refused. Levers left out of expected are predicted UNCHANGED.",
        "You never take a G4-C action yourself; the controller takes the frozen one.",
    )

    def __init__(self, machine: Any) -> None:
        self.machine = machine
        self.revision = 1
        self._tests: list[Prediction] = []
        self._pending: Prediction | None = None
        self._certified: Prediction | None = None
        self._level_closed: dict[str, Any] | None = None
        self._events: list[dict[str, Any]] = []
        self._unresolved: str | None = None  # R9-R24 D21: Duck's per-level budget was spent

    @property
    def _relations(self) -> LeverRelationsTarget:
        return self.machine._adapters[RELATION_GATE_ID]

    def _description(self) -> Any:
        answer = self._relations._answer
        if answer is None:
            raise GateContractError("G4-C opens only on an accepted G4-B description.")
        return answer

    def _closed(self) -> bool:
        return self._certified is not None or self._level_closed is not None or self._unresolved is not None

    def close_unresolved(self, reason: str) -> None:
        """D21 (ruling G-4): Duck's budget is spent; no reopening, a declared end with what is certified."""
        if not self._closed():
            self._unresolved, self._pending = reason, None
            self.revision += 1
            self._emit_product()

    # ---- gate protocol -----------------------------------------------------------------------

    def assess(self) -> GateAssessment:
        if self._closed():
            disposition, unmet = "SATISFIED", ()
        elif self._pending is not None:
            disposition, unmet = "PROBE_REQUIRED", (f"the controller takes {self._pending.prediction_id}",)
        else:
            disposition, unmet = "ANSWER_REQUIRED", ("freeze one new prediction drawn from your description",)
        return GateAssessment(
            target_id=LAW_GATE_ID, revision=self.revision, disposition=disposition,
            evidence_refs=tuple(event["evidence_id"] for event in self._events),
            unmet_requirements=unmet, explanation=self.TARGET,
        )

    def next_probe(self) -> ProbeEnvelope | None:
        if self._pending is None or self._closed():
            return None
        nav = str(self._pending.action.get("kind") or "").upper() == "NAV"
        return ProbeEnvelope(
            probe_id=f"{LAW_GATE_ID}:{self._pending.prediction_id}",
            gate_id=LAW_GATE_ID,
            purpose="NAV_PREDICTION_TEST" if nav else "PREDICTION_TEST",
            question=self._pending.because,
            actions=() if nav else (dict(self._pending.action),),
            live_alternatives=("SUPPORTED", "CONTRADICTED"),
            outcome_partition=("graded",),
            declared_at_transition=self._pending.declared_at_transition,
            admissible_actions=(tuple(sorted(
                item.action for item in self.machine.ego.affordances
                if item.action in self.machine.ego._currently_available and item.action != "ACTION6"
            )) if nav else ()),
            target={"prediction_id": self._pending.prediction_id,
                    "entity_id": self._pending.acted_lever,
                    "intervention": dict(self._pending.action)},
        )

    def validate_probe(self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]) -> ProbeEnvelope:
        raise GateContractError(
            f"G4-C takes an action only through a frozen {LAW_KIND}; the controller takes it."
        )

    def submit_answer(self, raw: Mapping[str, Any]) -> Prediction:
        if self._closed():
            raise GateContractError("G4-C is closed; no further answers are taken.")
        if self._pending is not None:
            raise GateContractError(f"{self._pending.prediction_id} is frozen and not yet taken; the controller takes it next.")
        try:
            prediction = self._freeze(raw)
        except G4RelationError as exc:
            raise GateContractError(f"G4-C answer rejected: {exc}") from exc
        self._pending = prediction
        self._tests.append(prediction)
        self.revision += 1
        return prediction

    def _freeze(self, raw: Mapping[str, Any]) -> Prediction:
        relations = self._description().relations
        drawn = raw.get("from_relations")
        if not isinstance(drawn, (list, tuple)) or not drawn or not all(isinstance(item, int) and not isinstance(item, bool) for item in drawn):
            raise G4RelationError("from_relations must be a non-empty list of relation numbers")
        if any(item < 0 or item >= len(relations) for item in drawn):
            raise G4RelationError(f"from_relations must be numbers from 0 to {len(relations) - 1}")
        raw_action = raw.get("action")
        if isinstance(raw_action, Mapping) and str(raw_action.get("kind") or "").upper() == "NAV":
            action = dict(raw_action)
            region = next((item for item in self._relations._regions
                           if item.entity_id == str(action.get("entity_id") or "")), None)
            if region is None or _canonical(region.click) != _canonical(action):
                raise G4RelationError("NAV action must exactly match a listed target-bound intervention")
        else:
            try:
                action = _normalize_action_payload(raw_action)
            except GateContractError as exc:
                raise G4RelationError(f"action: {exc}") from exc
        grid = self._relations._grid()
        if grid is not None:
            before = masked_address(grid, self.machine.counter.mask_law)
            tested = self._relations._record.tested(action, before) or self._relations.tested_from_record(action, before)
            if tested:
                raise G4RelationError(
                    f"this action was already graded from this same board ({tested[0]}); a new "
                    "prediction needs an action or board no graded prediction has tested"
                )
        prediction = validate_prediction(
            raw, self._relations._regions, prediction_id=f"L{len(self._tests) + 1}",
            declared_at_transition=self.machine.observed_through_step, action=action, kind=LAW_KIND,
        )
        prediction.from_relations = list(drawn)
        return prediction

    def record_outcome(self, probe: ProbeEnvelope, outcome: Mapping[str, Any]) -> dict[str, Any]:
        pending = self._pending
        if probe.gate_id != LAW_GATE_ID or pending is None:
            raise GateContractError("Outcome does not belong to a frozen G4-C prediction.")
        if probe.intent and probe.intent.startswith("NAV:APPROACH:"):
            import hashlib
            from inference.framework.probe_evidence import compact_probe_outcome
            evidence_id = "E-" + hashlib.sha256(_canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()).hexdigest()[:16]
            baseline = self.machine.apply_counter_baseline({**dict(outcome), "evidence_id": evidence_id})
            boundary = outcome.get("boundary_event")
            state = dict(boundary) if isinstance(boundary, Mapping) else None
            from inference.framework.g4_guided import level_changed
            closed = bool(level_changed(state))
            if closed and self._level_closed is None:
                self._level_closed = {"evidence_ref": evidence_id, "level_before": state.get("level_before"),
                                      "level_after": state.get("level_after")}
                self._emit_product()
            event = {"schema": "virelai-cybernetic-gate-v1", "evidence_id": evidence_id,
                     "gate_id": probe.gate_id, "probe_id": probe.probe_id,
                     "action": dict(outcome.get("action") or {}),
                     "prediction": {"prediction_id": pending.prediction_id, "status": "ROUTING"},
                     "nav_phase": "APPROACH", "graded": False,
                     "outcome": compact_probe_outcome(outcome), "counter_baseline": baseline,
                     "level_boundary": None if not closed else dict(self._level_closed)}
            self.revision += 1
            self._events.append(event)
            return event
        event = self._relations.take(pending, probe, outcome)
        self._pending = None
        self.revision += 1
        self._events.append(event)
        if event["level_boundary"] is not None:
            self._level_closed = event["level_boundary"]
        if pending.status == SUPPORTED:
            self._certified = pending
        if self._closed():
            self._emit_product()
        elif pending.status == CONTRADICTED:  # on the same level: the description is withdrawn, G4-B continues
            self._relations.reopen(pending)
            self.machine.target_journal.invalidate(RELATION_GATE_ID, include_self=True)
        return event

    def _emit_product(self) -> None:
        answer = self._relations._answer  # None only when G4-B itself closed UNRESOLVED (D21)
        certified = self._certified
        identity = {"test": None if certified is None else certified.evidence_ref,
                    "level_closed": None if self._level_closed is None else self._level_closed["evidence_ref"]}
        self.machine.target_journal.put(MemoryProduct(
            product_id="G4-LAW-" + hashlib.sha256(_canonical(identity).encode()).hexdigest()[:16],
            product_type=PRODUCT_TYPE,
            target_id=LAW_GATE_ID,
            revision=self.revision,
            payload={
                "scope": "G4C_LEVER_REACTION_LAW",
                "status": "COMPLETE" if certified is not None else "UNRESOLVED" if self._unresolved else "CLOSED_BY_LEVEL_BOUNDARY",
                "unresolved_reason": self._unresolved,
                "lever_entities": list(self._relations._levers()),
                "description": None if answer is None else answer.description,
                "relations": [] if answer is None else [dict(item) for item in answer.relations],
                "open_conditions": [] if answer is None else list(answer.open_conditions),
                "law_test": None if certified is None else asdict(certified),
                "tests": [asdict(item) for item in self._tests],
                "level_boundary": None if self._level_closed is None else dict(self._level_closed),
                "epistemic_limit": (
                    "A law set is a description that predicted one untested case; it holds for the "
                    "boards tested on this level, not universally."
                ),
                "digest_lines": [
                    f"law: {0 if answer is None else len(answer.relations)} relations · new test "
                    f"{'SUPPORTED' if certified is not None else 'UNRESOLVED (Duck budget spent)' if self._unresolved else 'cut off by a level change'} · "
                    f"{len(self._tests)} tests, {len(self._relations._reopened)} reopenings of G4-B",
                ],
            },
            dependencies=(RELATION_GATE_ID,),
        ))

    # ---- views -------------------------------------------------------------------------------

    def _template(self) -> dict[str, Any]:
        rows = self._relations._lever_rows()
        example = rows[0] if rows else {"entity_id": "<entity_id>", "click": {}}
        return {
            "answer_kind": LAW_KIND,
            "from_relations": [0],
            "action": dict(example["click"]),
            "expected": {example["entity_id"]: "STEPS"},
            "elsewhere": "NO_CHANGE",
            "because": "Say which relation predicts this outcome, and why this board has not been tested.",
        }

    def compact_gate_view(self) -> dict[str, Any]:
        assessment = self.assess()
        closed = self._closed()
        answer = self._relations._answer
        last = next((item for item in reversed(self._tests) if item.graded), None)
        return {
            "schema": "virelai-g4c-target-card-v1",
            "gate_id": LAW_GATE_ID,
            "revision": self.revision,
            "status": assessment.disposition,
            "goal_card": self.machine.target_registry.get(LAW_GATE_ID).goal_card(status=assessment.disposition),
            "target": self.TARGET,
            "done_when": self.DONE_WHEN,
            "rules": list(self.RULES),
            "unmet_requirements": list(assessment.unmet_requirements),
            "subject": {  # R9-R24: what Duck acts on first; the description also stands in the world model
                "levers": [{key: row[key] for key in ("entity_id", "click", "class", "state_now")}
                           for row in self._relations._lever_rows()[:LEVERS_ON_CARD]],
                "relations": [] if answer is None else [
                    {"number": index, "levers": item["levers"], "claim": item["claim"][:CLAIM_CHARS]}
                    for index, item in enumerate(answer.relations)
                ],
                "last_test": None if last is None else last.compact(),
                "description": None if answer is None else answer.description,
            },
            "progress": {"tests": len(self._tests), "reopenings": len(self._relations._reopened)},
            "next_operation": (
                "WAIT_FOR_NEXT_SLICE" if closed
                else "CONTROLLER_TAKES_PREDICTION" if self._pending is not None
                else "SUBMIT_GATE_ANSWER"
            ),
            "answer_template": None if closed or self._pending is not None else self._template(),
            "expand": [{"label": "full prediction ledger", "query": "virelai('relations')"}],
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "schema": "virelai-g4c-gate-v1", "gate_id": LAW_GATE_ID, "revision": self.revision,
            "status": self.assess().disposition, "tests": [asdict(item) for item in self._tests],
            "events": list(self._events),
        }


__all__ = ["LeverLawTarget", "PRODUCT_TYPE", "law_contract", "later_adapters", "later_contracts"]
