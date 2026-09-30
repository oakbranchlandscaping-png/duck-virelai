"""The G4-B gate: how the levers affect each other, one frozen prediction at a time (R9-R12).

Author: Claude (Alpha build seat), 2026-09-29. The logic is in ``g4_relations``; this module is
the gate adapter the ``CyberneticGateMachine`` registers after G4-A.

Ownership (DESIGN_VIRELAI_MEMORY_v2 §5.5: "G4-B relations and predictions: Duck"): Duck freezes
each prediction and writes the final description; the controller takes each frozen action and
the gate grades it. G4-B opens only when G4-A is COMPLETE (the Phase-1 hold in
``CyberneticGateMachine._effective_target_id``). It supersedes the retired G4.3 adapter:
persistence and reversal are now predictions Duck may freeze, as the G4.3 retirement note said.
"""
from __future__ import annotations

import hashlib
from dataclasses import asdict
from typing import Any, Mapping, Sequence

from inference.framework.cybernetic_targeting import GateAssessment, GoalContract, MemoryProduct
from inference.framework.g4_guided import is_terminal, level_changed
from inference.framework.g4_relations import (
    PREDICTION_KIND,
    RELATIONS_KIND,
    G4RelationError,
    OutcomeRecord,
    Prediction,
    RelationsAnswer,
    coverage,
    grade,
    lever_regions,
    masked_address,
    masked_changes,
    validate_prediction,
    validate_relations_answer,
)
from inference.framework.masked_world_state import grids_from_probe_outcome
from inference.framework.probe_evidence import compact_probe_outcome
from inference.framework.virelai_gates import (
    ORBIT_GATE_ID,
    REACTION_GATE_ID,
    RELATION_GATE_ID,
    SCHEMA_VERSION,
    GateContractError,
    ProbeEnvelope,
    _canonical,
    _normalize_action_payload,
)

PRODUCT_TYPE = "LeverRelationSet"
LEDGER_ON_CARD = 3
LEVERS_ON_CARD = 6  # axiom A6: the card stays flat in the number of levers; the rest by virelai('relations')


def relations_contract() -> GoalContract:
    return GoalContract(
        goal_id="G4B-LEVER-RELATIONS-v1",
        target_id=RELATION_GATE_ID,
        question="How do the levers affect each other?",
        desired_knowledge=(
            "a prediction frozen before each test, graded on the counter-masked board",
            "every lever pressed in at least one graded prediction",
            "relations resting only on supported predictions",
            "contradictions and split outcomes kept on the record",
            "a plain-language description of the lever set",
        ),
        prerequisites=(ORBIT_GATE_ID,),
        admissible_probe_kinds=("the one action of Duck's frozen prediction, taken by the controller",),
        completion_predicate=(
            "Stated target: every lever is the pressed lever of at least one graded prediction, and "
            "Duck's plain-language description is accepted with every relation citing supported "
            "predictions. Contradicted predictions and missing conditions stay on the record."
        ),
        memory_product_type=PRODUCT_TYPE,
    )


class LeverRelationsTarget:
    TARGET = (
        "Find out how the levers affect each other. For each test, freeze a prediction: the one "
        "action to take, and what it will do to every lever's region (UNCHANGED, STEPS as the lever's "
        "own press does, or CHANGES) and to the rest of the board. The controller takes the action and "
        "grades your prediction on the counter-masked board. Press every lever in at least one "
        "prediction, then describe the lever set in plain language."
    )
    DONE_WHEN = (
        "Every lever has been pressed in a graded prediction, and your description is accepted: every "
        "relation you claim cites supported predictions that pressed or named its levers. Contradicted "
        "predictions stay on the record; two different outcomes of one action from the same masked "
        "board are a missing condition you must list."
    )
    RULES = (
        "Freeze a prediction with virelai('gate_answer', answer={...}) using the LEVER_PREDICTION template. One prediction at a time; you never take G4-B actions yourself.",
        "Levers you leave out of expected are predicted UNCHANGED. elsewhere is every cell outside the lever regions.",
        "A lever's state (S0, S1, ...) names which of its recorded region contents it shows now; the counter is masked.",
        "Test relations the single-lever runs cannot show: a lever pressed after another changed, a press that undoes one, whether a lever's effect depends on another's state.",
        "When every lever has been pressed in a graded prediction, submit the LEVER_RELATIONS description; you may freeze more predictions first to support a relation.",
    )

    def __init__(self, machine: Any) -> None:
        self.machine = machine
        self.revision = 1
        self._regions: tuple = ()
        self._predictions: list[Prediction] = []
        self._pending: Prediction | None = None
        self._record = OutcomeRecord()
        self._answer: RelationsAnswer | None = None
        self._events: list[dict[str, Any]] = []
        self._level_closed: dict[str, Any] | None = None

    # ---- state -------------------------------------------------------------------------------

    def _seed(self) -> None:
        if self._regions:
            return
        reactions = self.machine.target_journal.active_product(REACTION_GATE_ID)
        orbits = self.machine.target_journal.active_product(ORBIT_GATE_ID)
        if reactions is None or orbits is None:
            raise GateContractError("G4-B opens only after G4.1 and G4-A have emitted their products.")
        try:
            self._regions = lever_regions(
                reactions.payload.get("anatomies") or (), orbits.payload.get("orbits") or (),
                orbits.payload.get("lever_classes") or {},
            )
        except G4RelationError as exc:
            raise GateContractError(f"G4-B cannot open: {exc}") from exc

    def _levers(self) -> tuple[str, ...]:
        self._seed()
        return tuple(region.entity_id for region in self._regions)

    def _grid(self) -> list[list[int]] | None:
        from inference.framework.card_builder import _current_grid

        return _current_grid(self.machine)

    def _closed(self) -> bool:
        return self._answer is not None or self._level_closed is not None

    # ---- gate protocol -----------------------------------------------------------------------

    def assess(self) -> GateAssessment:
        _acted, missing = coverage(self._predictions, self._levers())
        if self._closed():
            disposition, unmet = "SATISFIED", ()
        elif self._pending is not None:
            disposition, unmet = "PROBE_REQUIRED", (f"the controller takes {self._pending.prediction_id}",)
        elif missing:
            disposition, unmet = "ANSWER_REQUIRED", (f"freeze a prediction that presses: {', '.join(missing)}",)
        else:
            disposition, unmet = "ANSWER_REQUIRED", ("describe the lever set (LEVER_RELATIONS)",)
        return GateAssessment(
            target_id=RELATION_GATE_ID, revision=self.revision, disposition=disposition,
            evidence_refs=tuple(event["evidence_id"] for event in self._events),
            unmet_requirements=unmet, explanation=self.TARGET,
        )

    def next_probe(self) -> ProbeEnvelope | None:
        if self._pending is None or self._closed():
            return None
        return ProbeEnvelope(
            probe_id=f"{RELATION_GATE_ID}:{self._pending.prediction_id}",
            gate_id=RELATION_GATE_ID,
            purpose="PREDICTION_TEST",
            question=self._pending.because,
            actions=(dict(self._pending.action),),
            live_alternatives=("SUPPORTED", "CONTRADICTED"),
            outcome_partition=("graded",),
            declared_at_transition=self._pending.declared_at_transition,
            target={"prediction_id": self._pending.prediction_id},
        )

    def validate_probe(self, decision: Mapping[str, Any] | None, actions: Sequence[Mapping[str, Any]]) -> ProbeEnvelope:
        raise GateContractError(
            "G4-B takes an action only through a frozen prediction: submit virelai('gate_answer', "
            f"answer={{'answer_kind': '{PREDICTION_KIND}', ...}}) and the controller takes it."
        )

    def record_outcome(self, probe: ProbeEnvelope, outcome: Mapping[str, Any]) -> dict[str, Any]:
        pending = self._pending
        if probe.gate_id != RELATION_GATE_ID or pending is None:
            raise GateContractError("Outcome does not belong to a frozen G4-B prediction.")
        grids = grids_from_probe_outcome(outcome)
        if grids is None:
            raise GateContractError("G4-B requires lossless full-grid site transitions.")
        evidence_id = "E-" + hashlib.sha256(_canonical({"probe_id": probe.probe_id, "outcome": outcome}).encode()).hexdigest()[:16]
        counter_baseline = self.machine.apply_counter_baseline({**dict(outcome), "evidence_id": evidence_id})
        law = self.machine.counter.mask_law
        before, after = grids
        try:
            grade(pending, self._regions, masked_changes(before, after, law),
                  evidence_ref=evidence_id, transition_id=int(outcome.get("transition_id") or 0))
        except G4RelationError as exc:
            raise GateContractError(f"G4-B grading refused: {exc}") from exc
        condition = self._record.note(pending.action, masked_address(before, law), masked_address(after, law), evidence_id)
        self._pending = None
        self.revision += 1
        boundary = outcome.get("boundary_event")
        state = dict(boundary) if isinstance(boundary, Mapping) else None
        event = {
            "schema": SCHEMA_VERSION, "evidence_id": evidence_id, "gate_id": RELATION_GATE_ID,
            "probe_id": probe.probe_id, "action": dict(pending.action),
            "prediction": asdict(pending), "missing_condition": condition,
            "outcome": compact_probe_outcome(outcome), "counter_baseline": counter_baseline,
        }
        self._events.append(event)
        if is_terminal(state) and level_changed(state) and self._level_closed is None:
            self._level_closed = {"evidence_ref": evidence_id, "level_before": state.get("level_before"),
                                  "level_after": state.get("level_after")}
            self._emit_product()
        return event

    def submit_answer(self, raw: Mapping[str, Any]) -> Prediction | RelationsAnswer:
        if self._closed():
            raise GateContractError("G4-B is closed; no further answers are taken.")
        kind = str(raw.get("answer_kind") or "").strip().upper()
        try:
            if kind == PREDICTION_KIND:
                return self._freeze(raw)
            if kind == RELATIONS_KIND:
                self._answer = validate_relations_answer(raw, self._predictions, self._levers(), self._record.conditions)
                self.revision += 1
                self._emit_product()
                return self._answer
        except G4RelationError as exc:
            raise GateContractError(f"G4-B answer rejected: {exc}") from exc
        raise GateContractError(f"G4-B answer_kind must be {PREDICTION_KIND} or {RELATIONS_KIND}.")

    def _freeze(self, raw: Mapping[str, Any]) -> Prediction:
        if self._pending is not None:
            raise G4RelationError(f"{self._pending.prediction_id} is frozen and not yet taken; the controller takes it next")
        try:
            action = _normalize_action_payload(raw.get("action"))
        except GateContractError as exc:
            raise G4RelationError(f"action: {exc}") from exc
        available = {item.action for item in self.machine.ego.affordances if item.action in self.machine.ego._currently_available}
        if action.get("action") not in available:
            raise G4RelationError(f"action must be one of the available actions {sorted(available)}")
        self._pending = validate_prediction(
            raw, self._regions, prediction_id=f"P{len(self._predictions) + 1}",
            declared_at_transition=self.machine.observed_through_step, action=action,
        )
        self._predictions.append(self._pending)
        self.revision += 1
        return self._pending

    def _emit_product(self) -> None:
        acted, missing = coverage(self._predictions, self._levers())
        identity = {"answer": None if self._answer is None else self._answer.answer_id,
                    "level_closed": None if self._level_closed is None else self._level_closed["evidence_ref"]}
        self.machine.target_journal.put(MemoryProduct(
            product_id="G4-RELATIONS-" + hashlib.sha256(_canonical(identity).encode()).hexdigest()[:16],
            product_type=PRODUCT_TYPE,
            target_id=RELATION_GATE_ID,
            revision=self.revision,
            payload={
                "scope": "G4B_LEVERS_TOGETHER",
                "status": "COMPLETE" if self._answer is not None else "CLOSED_BY_LEVEL_BOUNDARY",
                "lever_entities": list(self._levers()),
                "pressed_levers": acted,
                "unpressed_levers": missing,
                "predictions": [asdict(item) for item in self._predictions],
                "missing_conditions": [dict(item) for item in self._record.conditions],
                "answer": None if self._answer is None else asdict(self._answer),
                "level_boundary": None if self._level_closed is None else dict(self._level_closed),
                "epistemic_limit": (
                    "Relations are claims about the graded transitions they cite, from the boards "
                    "those predictions were made on; they are not universal laws."
                ),
                "digest_lines": self._digest_lines(acted),
            },
            dependencies=(ORBIT_GATE_ID,),
        ))

    def _digest_lines(self, acted: Sequence[str]) -> list[str]:
        graded = [item for item in self._predictions if item.graded]
        supported = sum(1 for item in graded if item.status == "SUPPORTED")
        line = (f"relations: {supported}/{len(graded)} predictions supported · {len(acted)} levers pressed · "
                f"{len(self._record.conditions)} missing conditions")
        lines = [line]
        if self._answer is not None:
            lines.append(f"described: {self._answer.description[:240]}")
        return lines

    # ---- views -------------------------------------------------------------------------------

    def _lever_rows(self) -> list[dict[str, Any]]:
        """Every lever, unpressed first (the card shows the first LEVERS_ON_CARD)."""
        grid = self._grid()
        _acted, missing = coverage(self._predictions, self._levers())
        rows = [
            {"entity_id": region.entity_id, "click": dict(region.click), "bbox": region.bbox(),
             "class": region.lever_class, "state_now": None if grid is None else region.state_label(grid),
             "pressed": region.entity_id not in missing}
            for region in self._regions
        ]
        return sorted(rows, key=lambda row: row["pressed"])

    def _templates(self, missing: Sequence[str]) -> dict[str, Any]:
        example = next((region for region in self._regions if region.entity_id in missing), self._regions[0])
        prediction = {
            "answer_kind": PREDICTION_KIND,
            "action": dict(example.click),
            "expected": {example.entity_id: "STEPS"},
            "elsewhere": "NO_CHANGE",
            "because": "State the relation this test checks and why you expect this outcome.",
        }
        relations = {
            "answer_kind": RELATIONS_KIND,
            "description": "Describe the lever set in plain language: what each lever does, and how they affect each other.",
            "relations": [{"levers": ["<entity_id>", "<entity_id>"], "claim": "One relation, stated for the boards tested.",
                           "prediction_refs": ["<a SUPPORTED prediction_id>"]}],
            "open_conditions": [item["condition_id"] for item in self._record.conditions],
            "competing_models": ["One model still compatible with every graded prediction."],
            "falsifier": "A later graded outcome that would contradict this description.",
            "limitations": ["Relations hold for the boards the cited predictions were made on."],
        }
        return {"prediction": prediction, "relations": relations}

    def compact_gate_view(self) -> dict[str, Any]:
        assessment = self.assess()
        acted, missing = coverage(self._predictions, self._levers())
        graded = [item for item in self._predictions if item.graded]
        templates = self._templates(missing)
        closed = self._closed()
        view: dict[str, Any] = {
            "schema": "virelai-g4b-target-card-v1",
            "gate_id": RELATION_GATE_ID,
            "revision": self.revision,
            "status": assessment.disposition,
            "goal_card": self.machine.target_registry.get(RELATION_GATE_ID).goal_card(status=assessment.disposition),
            "target": self.TARGET,
            "done_when": self.DONE_WHEN,
            "rules": list(self.RULES),
            "unmet_requirements": list(assessment.unmet_requirements),
            "subject": {
                "levers": self._lever_rows()[:LEVERS_ON_CARD],
                "levers_not_shown": max(0, len(self._levers()) - LEVERS_ON_CARD),
                "last_graded": None if not graded else graded[-1].compact(),
            },
            "progress": {
                "pressed_levers": len(acted), "total_levers": len(self._levers()), "unpressed": missing,
                "predictions": {"supported": sum(1 for item in graded if item.status == "SUPPORTED"),
                                "contradicted": sum(1 for item in graded if item.status == "CONTRADICTED")},
                "recent": [item.compact() for item in graded[-LEDGER_ON_CARD:]],
                "missing_conditions": [item["condition_id"] for item in self._record.conditions],
            },
            "next_operation": (
                "WAIT_FOR_NEXT_SLICE" if closed
                else "CONTROLLER_TAKES_PREDICTION" if self._pending is not None
                else "SUBMIT_GATE_ANSWER"
            ),
            "answer_template": None if closed or self._pending is not None else (
                templates["prediction"] if missing else templates["relations"]
            ),
            "expand": [{"label": "full prediction ledger", "query": "virelai('relations')"}],
        }
        if not closed and self._pending is None and not missing:
            view["answer_template_note"] = (
                "Every lever has been pressed. Submit the LEVER_RELATIONS description, or freeze "
                f"another prediction (answer_kind {PREDICTION_KIND}) to support a relation first."
            )
        return view

    def relations_view(self) -> dict[str, Any]:
        return {
            "schema": "virelai-g4b-ledger-v1",
            "gate_id": RELATION_GATE_ID,
            "levers": self._lever_rows(),
            "predictions": [asdict(item) for item in self._predictions],
            "missing_conditions": [dict(item) for item in self._record.conditions],
            "answer": None if self._answer is None else asdict(self._answer),
        }

    def snapshot(self) -> dict[str, Any]:
        return {**self.relations_view(), "revision": self.revision, "status": self.assess().disposition,
                "events": list(self._events), "unmet_requirements": list(self.assess().unmet_requirements)}


__all__ = ["LeverRelationsTarget", "PRODUCT_TYPE", "RELATION_GATE_ID", "relations_contract"]
