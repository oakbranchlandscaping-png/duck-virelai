"""NAV control, routing, and intervention contracts.  Author: Sol, 2026-10-01."""
from types import SimpleNamespace

from inference.framework.nav_control import compile_nav_control_map
from inference.framework.nav_intervention import ContactEpoch, ContactProcedure, InterventionRef
from inference.framework.nav_route import NavLattice, classify_contact, plan_contact
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.virelai_gates import CyberneticGateMachine
from inference.framework.controller_executor import next_owned_step
from inference.framework.nav_route import NavStep


def test_target_identity_survives_shared_final_action():
    a = ContactProcedure.create(target_entity_id="E-A", target_cells=((1, 3),), allowed_actions=("ACTION1",))
    b = ContactProcedure.create(target_entity_id="E-B", target_cells=((2, 3),), allowed_actions=("ACTION1",))
    assert a.procedure_id != b.procedure_id
    assert a.intervention != b.intervention
    assert a.intervention.payload()["entity_id"] == "E-A"


def test_route_uses_stood_anchors_and_labels_only_terminal_press_as_contact():
    base = dict(shape=frozenset({(0, 0)}), bearings={"ACTION1": (0, 1)},
                refused=frozenset(), bounds=(3, 5))
    step = plan_contact(NavLattice(anchor=(1, 1), stands=frozenset({(1, 1), (1, 2)}), **base),
                        "E-T", {(1, 3)})
    assert (step.action, step.intent, step.landing) == ("ACTION1", "APPROACH", (1, 2))
    contact = plan_contact(NavLattice(anchor=(1, 2), stands=frozenset({(1, 1), (1, 2)}), **base),
                           "E-T", {(1, 3)})
    assert contact.intent == "CONTACT_ATTEMPT"


def test_route_never_plans_through_an_unobserved_anchor():
    lat = NavLattice(anchor=(1, 0), shape=frozenset({(0, 0)}),
                     bearings={"ACTION1": (0, 1)}, stands=frozenset({(1, 0)}),
                     refused=frozenset(), bounds=(3, 6))
    step = plan_contact(lat, "E-T", {(1, 5)})
    assert step.intent == "APPROACH"
    assert step.landing == (1, 1)  # one frontier experiment, not a fictional route


def test_refused_edge_is_not_retried():
    lat = NavLattice(anchor=(1, 1), shape=frozenset({(0, 0)}),
                     bearings={"ACTION1": (0, 1), "ACTION2": (1, 0)},
                     stands=frozenset({(1, 1)}), refused=frozenset({((1, 1), "ACTION1")}),
                     bounds=(4, 4))
    assert plan_contact(lat, "E-T", {(1, 2)}).action == "ACTION2"


def test_contact_classification_separates_refusal_from_motion():
    assert classify_contact({(1, 1)}, {(1, 1)}, {(1, 2)}, False) == "REFUSED"
    assert classify_contact({(1, 1)}, {(1, 2)}, {(1, 2)}, True) == "ENTERED"


def test_epoch_keeps_route_refs_out_of_terminal_contact_identity():
    proc = ContactProcedure.create(target_entity_id="E-T", target_cells=((1, 2),), allowed_actions=("ACTION1",))
    epoch = ContactEpoch.create(procedure=proc, route_evidence_refs=("E-route",),
                                contact_evidence_ref="E-contact", final_action="ACTION1",
                                stand=(1, 1), outcome="REFUSED")
    assert epoch.route_evidence_refs == ("E-route",)
    assert epoch.contact_evidence_ref == "E-contact"
    assert InterventionRef.nav("E-T", proc.procedure_id) == proc.intervention


def test_control_map_accepts_only_supported_structured_demonstration():
    answer = SimpleNamespace(action_law_specs={
        "ACTION1": {"effect": "moves right", "displacement": [0, 1]},
        "ACTION5": {"effect": "extra interaction"},
    })
    comparison = SimpleNamespace(outcome="SUPPORTED", observed_translation=(0, 1), comparison_id="CMP-1")
    pending = SimpleNamespace(action=SimpleNamespace(action="ACTION1"))
    ego = SimpleNamespace(answer=answer, last_comparison=comparison, pending_prediction=pending,
                          affordances=(SimpleNamespace(action="ACTION1"), SimpleNamespace(action="ACTION5")),
                          _currently_available={"ACTION1", "ACTION5"}, _lossless_outcomes=(), evidence=(),
                          current_grid=lambda: ((0, 0), (0, 2)),
                          embodied_ego_binding=lambda: (((1, 1),), "DEMONSTRATED"))
    control = compile_nav_control_map(ego)
    assert control.bearing_map() == {"ACTION1": (0, 1)}
    assert control.unresolved_actions == ("ACTION5",)


def _nav_g4_machine():
    machine = CyberneticGateMachine(valid_actions=["ACTION1"], initial_grid=((2, 0, 3),))
    machine.submit_answer({"answer_id": "G0", "action_metadata": [{"action": "ACTION1", "requires_coordinates": False}],
                           "semantic_claims": [], "epistemic_limit": "Action effects remain unknown until controlled observation."})
    products = (
        MemoryProduct("EGO", "EgoLaw", "G1-EGO", 1, {"mode": "EMBODIED_EGO"}, ("G0-ACTION-METADATA",)),
        MemoryProduct("COUNTER", "CounterGateProduct", "G2-COUNTER", 1, {"mask_law": None}, ("G1-EGO",)),
        MemoryProduct("LEVERS", "LeverInventory", "G3-LEVERS", 1, {"lever_entities": ["E-T"], "clean_null_entities": []}, ("G2-COUNTER",)),
        MemoryProduct("ANATOMY", "LeverEffectAnatomySet", "G4-REACTIONS", 1, {"anatomies": [{
            "entity_id": "E-T", "intervention": {"kind": "NAV", "entity_id": "E-T",
            "procedure_id": "NAVP-T", "final_action": {"action": "ACTION1"}, "target_cells": [[0, 2]]},
        }]}, ("G3-LEVERS",)),
    )
    for product in products:
        machine.target_journal.put(product)
    return machine


def _nav_outcome(before, after, transition):
    return {"transition_id": transition, "action": {"action": "ACTION1"},
            "changed_cells": [{"row": 0, "col": c, "before": before[0][c], "after": after[0][c]}
                              for c in range(3) if before[0][c] != after[0][c]],
            "site_transitions": [{"row": 0, "col": c, "before": before[0][c], "after": after[0][c]}
                                 for c in range(3)], "shape_before": [1, 3], "shape_after": [1, 3],
            "boundary_event": {"state": "PLAYING"}}


def test_g4_nav_approach_does_not_advance_orbit_but_contact_does():
    machine = _nav_g4_machine()
    capability = machine.next_probe_capability()
    approach = machine.validate_probe({"probe_token": capability["probe_token"], "intent": "NAV:APPROACH:E-T"},
                                      [{"action": "ACTION1"}])
    event = machine.record_outcome(approach, _nav_outcome(((2, 0, 3),), ((0, 2, 3),), 1))
    assert event["run"] == {"kind": "NAV_APPROACH", "orbit_advanced": False}
    assert machine.orbit_view("E-T")["runs"] == []

    capability = machine.next_probe_capability()
    contact = machine.validate_probe({"probe_token": capability["probe_token"], "intent": "NAV:CONTACT_ATTEMPT:E-T"},
                                     [{"action": "ACTION1"}])
    event = machine.record_outcome(contact, _nav_outcome(((0, 2, 3),), ((0, 2, 4),), 2))
    assert event["lever_entity_id"] == "E-T"
    assert event["run"]["kind"] == "LEVER_PRESS"
    assert len(machine.orbit_view("E-T")["runs"][0]["orbit"]["steps"]) == 1


def test_g4b_nav_prediction_routes_without_grading_then_grades_contact():
    machine = _nav_g4_machine()
    intervention = machine.target_journal.active_product("G4-REACTIONS").payload["anatomies"][0]["intervention"]
    machine.target_journal.put(MemoryProduct(
        "ORBITS", "LeverOrbitSet", "G4.2-LEVER-ORBITS", 1,
        {"lever_entities": ["E-T"], "lever_classes": {"E-T": "ABSORBING"}, "orbits": [{
            "entity_id": "E-T", "steps": [{"changed_cells": [[0, 2, 3, 4]]}],
        }]}, ("G4-REACTIONS",)))
    assert machine.gate_id == "G4-B-LEVER-RELATIONS"
    prediction = machine.submit_answer({
        "answer_kind": "LEVER_PREDICTION", "action": intervention,
        "expected": {"E-T": "STEPS"}, "elsewhere": "NO_CHANGE",
        "because": "contact with E-T should repeat its recorded local step",
    })
    assert prediction.acted_lever == "E-T"
    capability = machine.next_probe_capability()
    assert capability["purpose"] == "NAV_PREDICTION_TEST" and capability["actions"] == []
    approach = machine.validate_probe({"probe_token": capability["probe_token"], "intent": "NAV:APPROACH:E-T"},
                                      [{"action": "ACTION1"}])
    event = machine.record_outcome(approach, _nav_outcome(((2, 0, 3),), ((0, 2, 3),), 1))
    assert event["graded"] is False and prediction.status == "PENDING"
    assert machine.next_probe_capability()["target"]["prediction_id"] == prediction.prediction_id

    capability = machine.next_probe_capability()
    contact = machine.validate_probe({"probe_token": capability["probe_token"], "intent": "NAV:CONTACT_ATTEMPT:E-T"},
                                     [{"action": "ACTION1"}])
    machine.record_outcome(contact, _nav_outcome(((0, 2, 3),), ((0, 2, 4),), 2))
    assert prediction.status == "SUPPORTED"


def test_g4c_nav_law_test_also_grades_only_terminal_contact():
    machine = _nav_g4_machine()
    intervention = machine.target_journal.active_product("G4-REACTIONS").payload["anatomies"][0]["intervention"]
    machine.target_journal.put(MemoryProduct(
        "ORBITS", "LeverOrbitSet", "G4.2-LEVER-ORBITS", 1,
        {"lever_entities": ["E-T"], "lever_classes": {"E-T": "ABSORBING"}, "orbits": [{
            "entity_id": "E-T", "steps": [{"changed_cells": [[0, 2, 3, 4]]}],
        }]}, ("G4-REACTIONS",)))
    p1 = machine.submit_answer({"answer_kind": "LEVER_PREDICTION", "action": intervention,
        "expected": {"E-T": "STEPS"}, "elsewhere": "NO_CHANGE",
        "because": "contact with E-T should repeat its recorded local step"})
    cap = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": cap["probe_token"], "intent": "NAV:CONTACT_ATTEMPT:E-T"},
                                   [{"action": "ACTION1"}])
    machine.record_outcome(probe, _nav_outcome(((2, 0, 3),), ((2, 0, 4),), 1))
    assert p1.status == "SUPPORTED"
    machine.submit_answer({"answer_kind": "LEVER_RELATIONS",
        "description": "The embodied ego contacts this lever and the lever changes its own local region while the tested surrounding world stays unchanged.",
        "relations": [{"levers": ["E-T"], "claim": "Contacting E-T changes its own local region in the observed cases.", "prediction_refs": ["P1"]}],
        "open_conditions": [], "competing_models": ["the response may depend on an unseen state"],
        "falsifier": "a later contact leaves every lever region unchanged", "limitations": []})
    law = machine.submit_answer({"answer_kind": "LAW_PREDICTION", "from_relations": [0],
        "action": intervention, "expected": {"E-T": "CHANGES"}, "elsewhere": "NO_CHANGE",
        "because": "the accepted relation predicts another local E-T change"})
    cap = machine.next_probe_capability()
    approach = machine.validate_probe({"probe_token": cap["probe_token"], "intent": "NAV:APPROACH:E-T"},
                                      [{"action": "ACTION1"}])
    event = machine.record_outcome(approach, _nav_outcome(((2, 0, 4),), ((0, 2, 4),), 2))
    assert event["graded"] is False and law.status == "PENDING"
    cap = machine.next_probe_capability()
    contact = machine.validate_probe({"probe_token": cap["probe_token"], "intent": "NAV:CONTACT_ATTEMPT:E-T"},
                                     [{"action": "ACTION1"}])
    machine.record_outcome(contact, _nav_outcome(((0, 2, 4),), ((0, 2, 5),), 3))
    assert law.status == "SUPPORTED"
    assert machine.target_journal.active_product("G4-C-LEVER-LAW") is not None


def test_nav_controller_carries_computed_intent_with_the_bound_action(monkeypatch):
    from test_g3_scheduler import machine_for
    machine = machine_for(["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO")
    adapter = machine._adapters["G3-LEVERS"]
    monkeypatch.setattr(adapter, "planned_nav_step", lambda target: NavStep(
        "ACTION3", "CONTACT_ATTEMPT", (2, 2), (2, 3), str(target["entity_id"]),
        "predicted footprint intersects target"))
    step = next_owned_step(machine)
    assert (step.owner, step.action) == ("CONTROLLER", {"action": "ACTION3"})
    assert step.decision == {"pilot_intent": "CONTACT_ATTEMPT"}
