from __future__ import annotations

from dataclasses import asdict
import json

import pytest

from inference.framework.virelai_gates import (
    CyberneticGateMachine,
    EgoGateMachine,
    GateContractError,
    action_affordances,
    control_archetype_prior,
)
from inference.agent.runtime_state import Frame, RUNTIME_STATE_FILENAME, write_runtime_state
from inference.framework.probe_evidence import compile_probe_outcome


FRAME0 = ((0, 0, 0), (0, 5, 0), (0, 0, 0))


def test_g0_is_an_explicit_blocking_checkpoint_before_g1():
    machine = CyberneticGateMachine(
        valid_actions=["ACTION1", "ACTION6"], initial_grid=FRAME0
    )
    snapshot = machine.snapshot()
    assert snapshot["gate_id"] == "G0-ACTION-METADATA"
    assert snapshot["status"] == "ANSWER_REQUIRED"
    assert snapshot["next_probe"] is None
    with pytest.raises(GateContractError, match="G0 action metadata is unanswered"):
        machine.validate_probe(None, [{"action": "ACTION1"}])

    answer = machine.submit_answer({
        "answer_id": "G0-A1",
        "action_metadata": [
            {"action": "ACTION1", "requires_coordinates": False},
            {"action": "ACTION6", "requires_coordinates": True},
        ],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until they are observed through controlled probes.",
    })
    assert answer.answer_id == "G0-A1"
    assert machine.snapshot()["gate_id"] == "G1-EGO"
    assert machine.snapshot()["completed_gates"][0]["gate_id"] == "G0-ACTION-METADATA"


def test_g0_rejects_semantic_guess_and_inexact_metadata():
    machine = CyberneticGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    with pytest.raises(GateContractError, match="exactly match"):
        machine.submit_answer({
            "answer_id": "bad-list", "action_metadata": [], "semantic_claims": [],
            "epistemic_limit": "Effects remain unknown until direct observation supplies evidence.",
        })
    with pytest.raises(GateContractError, match="cannot assign semantic effects"):
        machine.submit_answer({
            "answer_id": "bad-semantics",
            "action_metadata": [{"action": "ACTION1", "requires_coordinates": False}],
            "semantic_claims": ["ACTION1 means up"],
            "epistemic_limit": "Effects remain unknown until direct observation supplies evidence.",
        })


def test_changed_action_surface_relocks_g0_and_invalidates_descendants():
    machine = CyberneticGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    machine.submit_answer({
        "answer_id": "G0-original",
        "action_metadata": [{"action": "ACTION1", "requires_coordinates": False}],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until direct observation supplies evidence.",
    })
    assert machine.gate_id == "G1-EGO"
    assert machine.target_journal.active_product("G0-ACTION-METADATA") is not None

    machine.update_action_metadata(["ACTION1", "ACTION2"])

    snapshot = machine.snapshot()
    assert machine.gate_id == "G0-ACTION-METADATA"
    assert machine.g0_answer is None
    assert machine.target_journal.active_product("G0-ACTION-METADATA") is None
    assert snapshot["action_metadata"] == [
        {"action": "ACTION1", "requires_coordinates": False},
        {"action": "ACTION2", "requires_coordinates": False},
    ]
    assert snapshot["goal_card"]["goal_id"] == "G0-ACTION-SURFACE-v1"
    assert machine.assessment().disposition == "ANSWER_REQUIRED"
    assert machine.assessment().unmet_requirements == ("exact opaque ActionSurface answer",)


def _decision(machine: EgoGateMachine) -> dict:
    probe = machine.next_probe()
    assert probe is not None
    data = asdict(probe)
    data.pop("actions")
    data.pop("declared_at_transition")
    data["live_alternatives"] = list(data["live_alternatives"])
    data["outcome_partition"] = list(data["outcome_partition"])
    return data


def _execute_next(machine: EgoGateMachine, *, changed: bool = True) -> str:
    probe = machine.next_probe()
    assert probe is not None
    validated = machine.validate_probe(_decision(machine), list(probe.actions))
    transition_id = machine.observed_through_step + 1
    if machine.status == "DEMONSTRATION_REQUIRED":
        after = ((0, 0, 0), (0, 6, 0), (0, 0, 0)) if changed else FRAME0
        outcome = compile_probe_outcome(
            probe_id=probe.probe_id,
            transition_id=transition_id,
            action=probe.actions[0],
            before_frame=Frame(grid=FRAME0, step=transition_id - 1, level=1),
            after_frame=Frame(grid=after, step=transition_id, level=1),
            available_actions_before=[item.action for item in machine.affordances],
            available_actions_after=[item.action for item in machine.affordances],
            callback_payload={"board_changed": changed, "state": "PLAYING"},
        )
    else:
        outcome = {"transition_id": transition_id, "board_changed": changed}
    event = machine.record_outcome(validated, outcome)
    return event["evidence_id"]


def _routed_g1_machine(actions=("ACTION1",), frame=FRAME0) -> CyberneticGateMachine:
    machine = CyberneticGateMachine(valid_actions=actions, initial_grid=frame)
    machine.submit_answer({
        "answer_id": "G0-capability",
        "action_metadata": [
            {"action": item.action, "requires_coordinates": item.requires_coordinates}
            for item in machine.ego.affordances
        ],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until direct observation supplies evidence.",
    })
    return machine


def test_routed_g1_requires_issued_token_only():
    machine = _routed_g1_machine()
    with pytest.raises(GateContractError, match="next_probe"):
        machine.validate_probe(None, [{"action": "ACTION1"}])
    with pytest.raises(GateContractError, match="Unknown probe_token"):
        machine.validate_probe({"probe_token": "P1_invented"}, [{"action": "ACTION1"}])
    capability = machine.next_probe_capability()
    with pytest.raises(GateContractError, match="accepts only probe_token"):
        machine.validate_probe(
            {"probe_token": capability["probe_token"], "purpose": "PROBE"},
            capability["actions"],
        )


def test_changed_gate_revision_makes_issued_probe_token_stale():
    machine = _routed_g1_machine()
    capability = machine.next_probe_capability()
    machine.ego.update_action_metadata(["ACTION1", "ACTION2"])
    with pytest.raises(GateContractError, match="Stale probe_token"):
        machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )


def test_coordinate_capability_rejects_wrong_site_without_consuming_token():
    machine = _routed_g1_machine(actions=("ACTION1", "ACTION6"))
    for transition_id in (1, 2):
        opening = machine.next_probe_capability()
        accepted = machine.validate_probe(
            {"probe_token": opening["probe_token"]}, opening["actions"]
        )
        machine.record_outcome(
            accepted, {"transition_id": transition_id, "board_changed": True}
        )
    capability = machine.next_probe_capability()
    expected = capability["actions"][0]
    wrong = {"action": "ACTION6", "row": expected["row"] + 1, "col": expected["col"]}
    with pytest.raises(GateContractError, match="exact actions"):
        machine.validate_probe({"probe_token": capability["probe_token"]}, [wrong])
    validated = machine.validate_probe(
        {"probe_token": capability["probe_token"]}, capability["actions"]
    )
    assert "SITE-ACTION6-TC" in validated.probe_id


def test_compact_gate_view_stays_bounded_when_coordinate_coverage_is_large():
    grid = tuple(tuple((row + col) % 2 for col in range(20)) for row in range(20))
    machine = _routed_g1_machine(actions=("ACTION6",), frame=grid)
    certificate = machine.ego.coverage_certificate(include_unknown_members=False)
    assert certificate["coordinate"]["candidate_count"] == 400
    assert len(machine.ego.coverage) == 0
    assert certificate["coordinate"]["class_count"] == 2
    assert certificate["coordinate"]["state"] == "DEFERRED_TO_LATER_TARGETS"
    rendered = json.dumps(machine.gate_view(), sort_keys=True)
    assert len(rendered) / 4 < 700
    assert "coverage_id" not in rendered


def test_g0_exposes_only_opaque_metadata_without_action_semantics():
    affordances = action_affordances(["ACTION6", "ACTION2", "ACTION1"])
    assert [(a.action, a.requires_coordinates) for a in affordances] == [
        ("ACTION1", False), ("ACTION2", False), ("ACTION6", True)
    ]
    with pytest.raises(GateContractError, match="opaque"):
        action_affordances(["LEFT"])


@pytest.mark.parametrize(
    ("actions", "world_type", "ego_types"),
    [
        (("ACTION6",), "CLICK_GOD_MODE", ["POINTER_GOD_MODE"]),
        (("ACTION1", "ACTION4"), "NAVIGATION", ["EMBODIED_EGO"]),
        (
            ("ACTION1", "ACTION5", "ACTION6"),
            "HYBRID",
            ["EMBODIED_EGO", "POINTER_GOD_MODE"],
        ),
        (("ACTION5",), "UNKNOWN", []),
    ],
)
def test_action_surface_supplies_opening_control_archetype(
    actions, world_type, ego_types
):
    prior = control_archetype_prior(action_affordances(actions))
    assert prior["world_type"] == world_type
    assert prior["ego_types"] == ego_types
    assert "remain to be demonstrated" in prior["epistemic_limit"]


def test_gate_view_delivers_hybrid_activation_and_action5_obligations():
    machine = CyberneticGateMachine(
        valid_actions=["ACTION1", "ACTION5", "ACTION6"], initial_grid=FRAME0
    )
    prior = machine.gate_view()["control_archetype_prior"]
    assert prior["world_type"] == "HYBRID"
    assert prior["interaction_channel"] == "ACTION5"
    assert any("activates" in item for item in prior["opening_obligations"])


def test_click_only_g1_requires_explanation_and_closes_without_environment_probe():
    machine = _routed_g1_machine(actions=("ACTION6",))
    view = machine.gate_view()
    assert view["status"] == "ANSWER_REQUIRED"
    assert view["next_operation"] == "SUBMIT_GATE_ANSWER"
    assert view["progress"]["coverage_total"] == 0
    assert view["answer_contract"]["closure_basis"] == (
        "G0 ACTION_SURFACE INTERFACE AXIOM"
    )
    assert machine.next_probe() is None

    answer = machine.submit_answer({
        "answer_id": "A-pointer",
        "answer_kind": "POINTER_GOD_MODE",
        "subjects": ["the ACTION6 site-selecting control locus"],
        "mechanism": (
            "Duck moves its pointer ego by choosing a new grid coordinate for ACTION6"
        ),
        "action_laws": {
            "ACTION6": "places the pointer control locus at the supplied row and column"
        },
        "conditions": ["the selected coordinate is within the legal grid"],
        "constraints": ["target effects remain unknown until later gates probe them"],
        "evidence_refs": ["G0-ACTION-METADATA"],
        "competing_models": ["a persistent embodied ego exists on the visible grid"],
        "falsifier": "ACTION6 ceases to accept a selected row and column",
        "limitations": ["click-target physics has not been inferred"],
    })

    assert answer.novel_prediction == {}
    assert machine.gate_id == "G2-COUNTER"
    assert machine.status == "ACTIVE"
    assert machine.ego.evidence == []
    assert machine.ego.ego_law is not None
    assert machine.ego.ego_law.status == "INTERFACE_AXIOM"
    assert machine.ego.ego_law.demonstration_ref == "G0-ACTION-METADATA"
    assert machine.completed_gate_rows()[-1]["product_id"] == machine.ego.ego_law.law_id


def test_g1_pairs_buttons_consecutively_then_covers_finite_frame0_sites():
    machine = EgoGateMachine(valid_actions=["ACTION1", "ACTION2", "ACTION6"], initial_grid=FRAME0)
    actions = []
    while machine.status == "ACTIVE":
        actions.append(machine.next_probe().actions[0])
        _execute_next(machine)
    assert actions[:4] == [
        {"action": "ACTION1"}, {"action": "ACTION1"},
        {"action": "ACTION2"}, {"action": "ACTION2"},
    ]
    assert actions[4:] == [
        {"action": "ACTION6", "row": 1, "col": 1},
        {"action": "ACTION1"}, {"action": "ACTION1"},
        {"action": "ACTION2"}, {"action": "ACTION2"},
        {"action": "ACTION6", "row": 0, "col": 0},
    ]
    assert machine.status == "ANSWER_REQUIRED"


def test_gate_id_stays_stable_while_revision_and_probe_advance():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    first = machine.snapshot()
    _execute_next(machine)
    second = machine.snapshot()
    assert first["gate_id"] == second["gate_id"] == "G1-EGO"
    assert second["revision"] > first["revision"]
    assert first["next_probe"]["probe_id"] != second["next_probe"]["probe_id"]


def test_wrong_or_semantically_named_probe_cannot_be_executed():
    machine = EgoGateMachine(valid_actions=["ACTION1", "ACTION2"], initial_grid=FRAME0)
    with pytest.raises(GateContractError, match="next gated probe"):
        machine.validate_probe(_decision(machine), [{"action": "ACTION2"}])
    with pytest.raises(GateContractError, match="opaque"):
        machine.validate_probe(_decision(machine), [{"action": "LEFT"}])
    assert machine.evidence == []


def test_label_only_answer_fails_and_explanatory_prediction_must_be_demonstrated():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    evidence = [_execute_next(machine), _execute_next(machine)]
    assert machine.status == "ANSWER_REQUIRED"
    with pytest.raises(GateContractError, match="mechanism"):
        machine.submit_answer({
            "answer_id": "A-label", "answer_kind": "ego", "subjects": ["cursor"],
            "mechanism": "cursor", "action_laws": {"ACTION1": "moves the cursor somehow"},
            "conditions": [], "constraints": [], "evidence_refs": evidence,
            "competing_models": ["not cursor"], "falsifier": "cursor does not move",
            "novel_prediction": {"action": {"action": "ACTION1"}, "expected": "CHANGED"},
            "limitations": [],
        })

    answer = {
        "answer_id": "A1",
        "answer_kind": "embodied ego",
        "subjects": ["the single component that translates after ACTION1"],
        "mechanism": "ACTION1 directly translates the candidate ego while the surrounding field remains fixed",
        "action_laws": {"ACTION1": "translates the candidate component by one repeated displacement"},
        "conditions": ["candidate is not blocked"],
        "constraints": ["only direct visible effects are claimed"],
        "evidence_refs": evidence,
        "competing_models": ["ACTION1 moves a remote object rather than an ego"],
        "falsifier": "the predicted component fails to translate on the next legal ACTION1",
        "novel_prediction": {
            "action": {"action": "ACTION1"}, "predicate": "ANY_CHANGE",
            "scope": {"representation": "CELLS", "cells": [[1, 1]]},
            "because": "the inferred action law is repeatable",
            "novelty": "this transition starts from the new post-opening state",
        },
        "limitations": ["direction is described relationally until more evidence exists"],
    }
    machine.submit_answer(answer)
    assert machine.status == "DEMONSTRATION_REQUIRED"
    _execute_next(machine, changed=True)
    assert machine.status == "CLOSED"


def test_contradicted_demonstration_reopens_the_gate():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    evidence = [_execute_next(machine), _execute_next(machine)]
    machine.submit_answer({
        "answer_id": "A2",
        "answer_kind": "embodied ego",
        "subjects": ["candidate component"],
        "mechanism": "ACTION1 directly moves the candidate component through otherwise stable terrain",
        "action_laws": {"ACTION1": "moves the candidate component by one repeatable displacement"},
        "conditions": [], "constraints": [], "evidence_refs": evidence,
        "competing_models": ["remote actuator"],
        "falsifier": "the candidate does not move under an unblocked repetition",
        "novel_prediction": {
            "action": {"action": "ACTION1"}, "predicate": "ANY_CHANGE",
            "scope": {"representation": "CELLS", "cells": [[1, 1]]},
            "because": "the inferred action law is repeatable",
            "novelty": "this transition starts from the new post-opening state",
        },
        "limitations": [],
    })
    _execute_next(machine, changed=False)
    assert machine.status == "REOPENED"


def test_exact_form_prediction_closes_g1_and_surfaces_footprint_verdict():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    evidence = [_execute_next(machine), _execute_next(machine)]
    machine.submit_answer({
        "answer_id": "A-form",
        "answer_kind": "embodied ego",
        "subjects": ["the one-cell component at (1,1)"],
        "mechanism": "ACTION1 directly recolors the declared component while its footprint stays fixed",
        "action_laws": {"ACTION1": "recolors the declared component from integer 5 to integer 6"},
        "conditions": [],
        "constraints": ["4-connected equal-integer component convention"],
        "evidence_refs": evidence,
        "competing_models": ["the rewrite is a remote environmental effect"],
        "falsifier": "the component fails to retain its footprint and change from 5 to 6",
        "novel_prediction": {
            "action": {"action": "ACTION1"},
            "predicate": "RECOLOR",
            "scope": {"representation": "CELLS", "cells": [[1, 1]]},
            "expected_parameters": {
                "before_footprint": [[1, 1]],
                "after_footprint": [[1, 1]],
                "before_integer": 5,
                "after_integer": 6,
                "recolor": True,
            },
            "because": "the observed direct action law predicts the same exact rewrite",
            "novelty": "this demonstration occurs after the completed opening probes",
        },
        "limitations": [],
    })
    _execute_next(machine, changed=True)
    assert machine.status == "CLOSED"
    assert machine.ego_law is not None
    assert machine.last_comparison is not None
    persisted_event = machine.evidence[-1]
    assert persisted_event["gate_status_after"] == "CLOSED"
    assert persisted_event["demonstration_comparison"]["outcome"] == "SUPPORTED"
    assert persisted_event["ego_law"]["law_version_id"] == machine.ego_law.law_version_id
    assert machine.last_comparison.observed_form == "RECOLOR"
    assert machine.last_comparison.before_footprint == ((1, 1),)
    assert machine.last_comparison.after_footprint == ((1, 1),)
    assert machine.current_grid()[1][1] == 6
    assert machine.embodied_ego_binding() == (
        ((1, 1),), "DEMONSTRATED_AFTER_FOOTPRINT"
    )


def test_structured_qwen_answer_normalizes_and_demonstrates_multicolor_ego():
    frames = (
        ((0, 0, 0, 0, 0, 0), (5, 6, 0, 0, 0, 0), (9, 9, 9, 0, 0, 0)),
        ((0, 0, 0, 0, 0, 0), (0, 5, 6, 0, 0, 0), (8, 9, 9, 0, 0, 0)),
        ((0, 0, 0, 0, 0, 0), (0, 0, 5, 6, 0, 0), (8, 8, 9, 0, 0, 0)),
        ((0, 0, 0, 0, 0, 0), (0, 0, 0, 5, 6, 0), (8, 8, 8, 0, 0, 0)),
    )
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=frames[0])

    evidence = []
    for index in range(2):
        probe = machine.next_probe()
        assert probe is not None
        validated = machine.validate_probe(_decision(machine), list(probe.actions))
        outcome = compile_probe_outcome(
            probe_id=probe.probe_id,
            transition_id=index + 1,
            action=probe.actions[0],
            before_frame=Frame(grid=frames[index], step=index, level=1),
            after_frame=Frame(grid=frames[index + 1], step=index + 1, level=1),
            available_actions_before=["ACTION1"],
            available_actions_after=["ACTION1"],
            callback_payload={"board_changed": True, "state": "PLAYING"},
        )
        evidence.append(machine.record_outcome(validated, outcome)["evidence_id"])

    machine.submit_answer({
        "answer_id": "G1-QWEN-SHAPE",
        "answer_kind": "embodied ego",
        "subjects": [{
            "description": "the adjacent two-integer pattern directly controlled by ACTION1",
            "role": "embodied ego",
        }],
        "mechanism": "ACTION1 translates the complete two-integer ego pattern one cell right",
        "action_laws": [{
            "action": "ACTION1",
            "effect": "translates the complete pattern one column right",
            "displacement": {"row": 0, "col": 1},
        }],
        "conditions": [],
        "constraints": ["the next destination remains unblocked"],
        "evidence_refs": evidence,
        "competing_models": ["only one colored subcomponent is controlled"],
        "falsifier": "the complete pattern fails to reappear at the predicted translated footprint",
        "novel_prediction": {
            "action": "ACTION1",
            "predicate": "PATTERN_TRANSLATION",
            "scope.representation": "CELLS",
            "scope.cells": [[1, 2], [1, 3]],
            "expected_parameters": {
                "before_footprint": [[1, 2], [1, 3]],
                "after_footprint": [[1, 3], [1, 4]],
                "displacement": {"row": 0, "col": 1},
            },
            "because": "the paired probes showed the same repeatable direct translation",
            "novelty": "the demonstration begins from the later post-opening grid state",
        },
        "limitations": ["the separate bottom-row rewrite remains untyped"],
    })
    assert machine.status == "DEMONSTRATION_REQUIRED"

    probe = machine.next_probe()
    assert probe is not None
    validated = machine.validate_probe(_decision(machine), list(probe.actions))
    outcome = compile_probe_outcome(
        probe_id=probe.probe_id,
        transition_id=3,
        action=probe.actions[0],
        before_frame=Frame(grid=frames[2], step=2, level=1),
        after_frame=Frame(grid=frames[3], step=3, level=1),
        available_actions_before=["ACTION1"],
        available_actions_after=["ACTION1"],
        callback_payload={"board_changed": True, "state": "PLAYING"},
    )
    machine.record_outcome(validated, outcome)

    assert machine.status == "CLOSED"
    assert machine.last_comparison is not None
    assert machine.last_comparison.observed_form == "PATTERN_TRANSLATION"
    assert machine.last_comparison.remote_changes
    assert machine.embodied_ego_binding() == (
        ((1, 3), (1, 4)), "DEMONSTRATED_AFTER_FOOTPRINT"
    )


def test_prediction_copied_from_prior_evidence_without_a_novel_scope_is_rejected():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    evidence = [_execute_next(machine), _execute_next(machine)]
    with pytest.raises(GateContractError, match="scope"):
        machine.submit_answer({
            "answer_id": "A-copy", "answer_kind": "ego", "subjects": ["component"],
            "mechanism": "ACTION1 repeatedly translates the same directly controlled component",
            "action_laws": {"ACTION1": "moves the controlled component by one displacement"},
            "conditions": [], "constraints": [], "evidence_refs": evidence,
            "competing_models": ["remote object"], "falsifier": "the component stays fixed",
            "novel_prediction": {"action": {"action": "ACTION1"}, "expected": "CHANGED"},
            "limitations": [],
        })


def test_live_action_metadata_extends_coverage_without_changing_gate_identity():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    _execute_next(machine)
    _execute_next(machine)
    assert machine.status == "ANSWER_REQUIRED"
    machine.update_action_metadata(["ACTION1", "ACTION5"])
    assert machine.gate_id == "G1-EGO"
    assert machine.status == "ACTIVE"
    assert machine.next_probe().actions == ({"action": "ACTION5"},)


def test_closed_ego_law_records_later_reuse_and_opens_next_gate():
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    evidence = [_execute_next(machine), _execute_next(machine)]
    machine.submit_answer({
        "answer_id": "A-reuse", "answer_kind": "embodied ego", "subjects": ["component"],
        "mechanism": "ACTION1 directly translates the candidate component through stable surrounding terrain",
        "action_laws": {"ACTION1": "moves the candidate component by one repeatable displacement"},
        "conditions": [], "constraints": [], "evidence_refs": evidence,
        "competing_models": ["remote actuator"], "falsifier": "the candidate stays fixed",
        "novel_prediction": {
            "action": {"action": "ACTION1"}, "predicate": "ANY_CHANGE",
            "scope": {"representation": "CELLS", "cells": [[1, 1]]},
            "because": "the action law predicts repeated displacement",
            "novelty": "the test begins after completing the opening",
        },
        "limitations": [],
    })
    _execute_next(machine)
    assert machine.ego_law is not None
    event = machine.record_reuse({
        "decision_id": "G2-D1", "law_id": machine.ego_law.law_id, "action": "ACTION1",
        "use": "uses the ego displacement law to test adjacent terrain",
    })
    snapshot = machine.snapshot()
    assert event["decision_id"] == "G2-D1"
    assert snapshot["next_gate_id"] == "G2-COUNTER"
    assert snapshot["reuse_events"][0]["law_id"] == machine.ego_law.law_id
    assert snapshot["ego_law"]["law_id"] == machine.ego_law.law_id


def test_semantic_answer_revision_does_not_mutate_raw_runtime_observation(tmp_path):
    state_path = tmp_path / f"raw_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=FRAME0, step=2, level=1),
        history=[],
    )
    machine = EgoGateMachine(valid_actions=["ACTION1"], initial_grid=FRAME0)
    evidence = [_execute_next(machine), _execute_next(machine)]
    raw_before = state_path.read_bytes()
    machine.submit_answer({
        "answer_id": "A-immutable", "answer_kind": "embodied ego", "subjects": ["component"],
        "mechanism": "ACTION1 directly translates the candidate component through stable surrounding terrain",
        "action_laws": {"ACTION1": "moves the candidate component by one repeatable displacement"},
        "conditions": [], "constraints": [], "evidence_refs": evidence,
        "competing_models": ["remote actuator"], "falsifier": "the candidate stays fixed",
        "novel_prediction": {
            "action": {"action": "ACTION1"}, "predicate": "ANY_CHANGE",
            "scope": {"representation": "CELLS", "cells": [[1, 1]]},
            "because": "the action law predicts repeated displacement",
            "novelty": "the test begins after completing the opening",
        },
        "limitations": [],
    })
    assert state_path.read_bytes() == raw_before
