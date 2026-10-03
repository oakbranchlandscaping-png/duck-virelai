"""NAV control, routing, and intervention contracts.  Author: Sol, 2026-10-01."""
import json
from types import SimpleNamespace

from inference.framework.nav_control import compile_nav_control_map
from inference.framework.nav_intervention import ContactEpoch, ContactProcedure, InterventionRef
from inference.framework.nav_route import (
    NavLattice, certify_unreachable, classify_contact, plan_contact,
)
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.virelai_gates import CyberneticGateMachine
from inference.framework.controller_executor import next_owned_step, wake_reason
from inference.framework import controller_executor as executor
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


def test_route_searches_another_stands_frontier_before_giving_up():
    lat = NavLattice(
        anchor=(1, 1), shape=frozenset({(0, 0)}),
        bearings={"ACTION1": (0, 1), "ACTION2": (1, 0)},
        stands=frozenset({(1, 1), (1, 2)}),
        refused=frozenset({((1, 1), "ACTION2"), ((1, 2), "ACTION1")}),
        bounds=(4, 5),
    )
    step = plan_contact(lat, "E-T", {(3, 2)})
    assert (step.action, step.intent, step.reason) == (
        "ACTION1", "APPROACH", "shortest demonstrated route to an untried frontier edge",
    )
    advanced = NavLattice(
        anchor=(1, 2), shape=lat.shape, bearings=lat.bearings,
        stands=lat.stands, refused=lat.refused, bounds=lat.bounds,
    )
    assert plan_contact(advanced, "E-T", {(3, 2)}).landing == (2, 2)


def test_unreachable_certificate_requires_exhausted_reachable_component():
    open_lat = NavLattice(
        anchor=(1, 1), shape=frozenset({(0, 0)}),
        bearings={"ACTION1": (0, 1), "ACTION2": (1, 0)},
        stands=frozenset({(1, 1)}), refused=frozenset(), bounds=(3, 3),
    )
    assert certify_unreachable(open_lat, "E-HUD", {(0, 0)}) is None
    closed = NavLattice(
        anchor=open_lat.anchor, shape=open_lat.shape, bearings=open_lat.bearings,
        stands=open_lat.stands,
        refused=frozenset({((1, 1), "ACTION1"), ((1, 1), "ACTION2")}),
        bounds=open_lat.bounds,
    )
    certificate = certify_unreachable(closed, "E-HUD", {(0, 0)})
    assert certificate.status == "PRESUMED_UNREACHABLE"
    assert certificate.open_frontier_edge_count == 0
    assert certificate.contact_surface_count == 0
    assert certificate.refused_edges == (
        ((1, 1), "ACTION1"), ((1, 1), "ACTION2"),
    )
    assert certificate.inertness_claim_permitted is False


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


def test_nav_g4_requires_one_semantic_orientation_before_mechanical_study():
    step = next_owned_step(_nav_g4_machine())
    assert step.owner == "DUCK"
    assert step.reason == "the orientation turn is due"


def test_nav_certified_answers_reuse_the_controller_renderer(monkeypatch):
    class CertifiedAnswerMachine:
        def __init__(self, gate_id):
            self.gate_id = gate_id
            self.lives = SimpleNamespace(level=1)

        def gate_view(self):
            return {"status": "ANSWER_REQUIRED", "revision": 7, "answer_template": {"gate": self.gate_id}}

        def next_probe_capability(self):
            return None

    monkeypatch.setattr(
        executor, "controller_answer",
        lambda machine, view: ({"answer_id": f"CERTIFIED-{machine.gate_id}"}, "certified record"),
    )
    for gate_id in ("G2-COUNTER", "G3-LEVERS", "G4-REACTIONS"):
        step = executor._nav_step(CertifiedAnswerMachine(gate_id))
        assert (step.owner, step.kind, step.answer["answer_id"]) == (
            "CONTROLLER", "ANSWER", f"CERTIFIED-{gate_id}",
        )


def test_nav_extra_run_is_routed_by_controller_before_duck_explains():
    class ExtraRunMachine:
        gate_id = "G4.2-LEVER-ORBITS"
        _adapters = {
            "G4.2-LEVER-ORBITS": SimpleNamespace(
                planned_nav_step=lambda entity: NavStep(
                    "ACTION1", "CONTACT_ATTEMPT", (0, 1), (0, 2), entity,
                    "terminal contact for requested rerun",
                ),
            ),
        }

        def next_probe_capability(self):
            return {"probe_token": "P-RERUN"}

    step = executor._nav_step(
        ExtraRunMachine(),
        rerun={"entity_id": "E-T", "left": 2, "click": {"kind": "NAV"}},
    )
    assert step.owner == "CONTROLLER"
    assert step.gate_id == "G4.2-LEVER-ORBITS"
    assert step.decision["intent"].startswith("NAV:")


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


def _unchanged_outcome(grid, transition, action="ACTION1"):
    return {
        "transition_id": transition,
        "action": {"action": action},
        "changed_cells": [],
        "site_transitions": [
            {"row": row, "col": col, "before": value, "after": value}
            for row, values in enumerate(grid)
            for col, value in enumerate(values)
        ],
        "shape_before": [len(grid), len(grid[0])],
        "shape_after": [len(grid), len(grid[0])],
        "boundary_event": {"state": "PLAYING"},
    }


def _changed_outcome(before, after, transition, action="ACTION1"):
    return {
        "transition_id": transition,
        "action": {"action": action},
        "changed_cells": [
            {"row": row, "col": col, "before": before[row][col], "after": value}
            for row, values in enumerate(after)
            for col, value in enumerate(values)
            if before[row][col] != value
        ],
        "site_transitions": [
            {
                "row": row, "col": col,
                "before": before[row][col], "after": value,
            }
            for row, values in enumerate(after)
            for col, value in enumerate(values)
        ],
        "shape_before": [len(before), len(before[0])],
        "shape_after": [len(after), len(after[0])],
        "boundary_event": {"state": "PLAYING"},
    }


def test_g3_failed_approach_is_wall_evidence_and_does_not_type_target():
    from test_g3_scheduler import GRID, machine_for

    machine = machine_for(
        ["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO"
    )
    adapter = machine._adapters["G3-LEVERS"]
    ledger = adapter._ensure_entity_ledger()
    assert ledger.bind_role_cells("EGO", ((1, 1),))
    adapter._target_index = 1
    capability = machine.next_probe_capability()
    target_entity = capability["target"]["entity_id"]
    adapter._last_nav_plan = NavStep(
        "ACTION1", "APPROACH", (1, 1), (1, 2), target_entity,
        "one-step frontier experiment",
    )
    probe = machine.validate_probe(
        {"probe_token": capability["probe_token"], "pilot_intent": "APPROACH"},
        [{"action": "ACTION1"}],
    )
    event = machine.record_outcome(probe, _unchanged_outcome(GRID, 1))

    assert event["nav_terrain"]["disposition"] == "WALL_EDGE_REFUSED"
    assert ((1, 1), "ACTION1") in adapter._nav_refused
    assert adapter.lifecycle_journal.entities[target_entity].state == "ATTEMPTED"
    assert adapter._target_index == 1
    assert wake_reason(machine, event, {}) is None


def test_non_ego_world_delta_invalidates_old_refusals_before_learning_new_state():
    from test_g3_scheduler import GRID, machine_for

    machine = machine_for(
        ["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO"
    )
    adapter = machine._adapters["G3-LEVERS"]
    ledger = adapter._ensure_entity_ledger()
    assert ledger.bind_role_cells("EGO", ((1, 1),))
    adapter._target_index = 1
    capability = machine.next_probe_capability()
    target_entity = capability["target"]["entity_id"]
    old_edge = ((1, 1), "ACTION2")
    adapter._nav_refused.add(old_edge)
    adapter._nav_refused_evidence[old_edge] = "E-OLD-STATE"
    adapter._last_nav_plan = NavStep(
        "ACTION1", "APPROACH", (1, 1), (1, 2), target_entity,
        "one-step frontier experiment",
    )
    probe = machine.validate_probe(
        {"probe_token": capability["probe_token"], "pilot_intent": "APPROACH"},
        [{"action": "ACTION1"}],
    )
    after = tuple(
        tuple(5 if (row, col) == (0, 0) else value for col, value in enumerate(values))
        for row, values in enumerate(GRID)
    )
    event = machine.record_outcome(probe, _changed_outcome(GRID, after, 1))

    transition = event["nav_world_state"]
    assert transition["before_world_address"] != transition["after_world_address"]
    assert transition["world_delta_cells"] == [[0, 0]]
    assert transition["invalidated_refused_edges"] == [
        {"stand": [1, 1], "action": "ACTION2"}
    ]
    assert old_edge not in adapter._nav_refused
    # The failed ACTION1 belongs to the new state and is learned after the old
    # state's refusal set is invalidated.
    assert ((1, 1), "ACTION1") in adapter._nav_refused


def test_g3_confirmation_approach_remains_pending_and_is_not_graded():
    from test_g3_scheduler import GRID, machine_for

    machine = machine_for(
        ["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO"
    )
    adapter = machine._adapters["G3-LEVERS"]
    ledger = adapter._ensure_entity_ledger()
    assert ledger.bind_role_cells("EGO", ((1, 1),))
    adapter._target_index = 1
    original = machine.next_probe_capability()
    entity_id = original["target"]["entity_id"]
    journal = adapter.lifecycle_journal
    journal.attempt(entity_id, evidence_ref="E-WITNESS")
    journal.response(entity_id, positive=True, evidence_ref="E-WITNESS")
    adapter._pending_confirmation = {
        "probe_id": "G3-LEVERS:CONFIRM:test",
        "phase": "NAV",
        "target": dict(original["target"]),
        "action": {"action": "ACTION1"},
        "target_member_id": original["target"]["member_id"],
        "entity_id": entity_id,
        "pre_action_owner_entity_id": entity_id,
        "witness_evidence_ref": "E-WITNESS",
        "declared_at_transition": 0,
        "local_cells": tuple(tuple(cell) for cell in original["target"]["cells"]),
        "remote_cells": (),
    }
    adapter._last_nav_plan = NavStep(
        "ACTION1", "APPROACH", (1, 1), (1, 2), entity_id,
        "route through demonstrated floor",
    )
    capability = machine.next_probe_capability()
    probe = machine.validate_probe(
        {"probe_token": capability["probe_token"], "pilot_intent": "APPROACH"},
        [{"action": "ACTION1"}],
    )
    event = machine.record_outcome(probe, _unchanged_outcome(GRID, 1))

    assert event["confirmation"]["status"] == "ROUTING"
    assert event["confirmation"]["graded"] is False
    assert adapter._pending_confirmation is not None
    assert adapter.lifecycle_journal.entities[entity_id].state == "RESPONDED"


def test_reachability_answer_explains_limit_releases_target_and_stays_bounded():
    from test_g3_scheduler import machine_for

    machine = machine_for(
        ["ACTION1", "ACTION2", "ACTION3", "ACTION4"], "EMBODIED_EGO"
    )
    adapter = machine._adapters["G3-LEVERS"]
    target = machine.next_probe_capability()["target"]
    stands = [[row, col] for row in range(40) for col in range(40)]
    refused = [[[row, col], "ACTION1"] for row, col in stands]
    adapter._pending_reachability = {
        "schema": "virelai-nav-reachability-certificate-v1",
        "target_entity_id": target["entity_id"],
        "target_member_id": target["member_id"],
        "target_version": 1,
        "status": "PRESUMED_UNREACHABLE",
        "reachable_stands": stands,
        "refused_edges": refused,
        "closest_stand": [1, 1],
        "remaining_gap": 3,
        "contact_surface_count": 0,
        "open_frontier_edge_count": 0,
        "inertness_claim_permitted": False,
        "reopen_conditions": [
            "new stood anchor", "previously refused edge yields",
            "target geometry or identity changes",
            "ego footprint, bearing map, or action surface changes",
            "terrain or level state changes",
        ],
        "evidence_refs": ["E-FLOOR", "E-WALL"],
    }
    compact = machine.gate_view()
    assert len(json.dumps(compact)) < 24_000
    assert "reachable_stands" not in compact["scheduler"]["pending_reachability"]
    template = compact["answer_template"]
    answer = machine.submit_answer({
        **template,
        "explanation": (
            "Every demonstrated floor stand and every remaining frontier press was tested; "
            "none provides a contact surface to this object, so the sweep should continue."
        ),
    })

    assert answer.answer_kind == "TARGET_REACHABILITY"
    assert adapter.lifecycle_journal.entities[target["entity_id"]].state == "PRESUMED_UNREACHABLE"
    assert adapter._target_index == 1
    assert adapter._reachability_records[-1]["inertness_claim_permitted"] is False
    assert machine.next_probe_capability()["target"]["rank"] == 2

    adapter._reopen_reachability(
        evidence_ref="E-NEW-FLOOR",
        reason="a new demonstrated floor stand expanded the reachable component",
    )
    reopened = machine.next_probe_capability()
    assert reopened["target"]["rank"] == 1
    assert adapter.lifecycle_journal.entities[target["entity_id"]].state == "REOPENED"
    assert target["entity_id"] not in adapter._bounded_ambiguities
    assert adapter._reachability_records[-1]["reopened_by_evidence_ref"] == "E-NEW-FLOOR"
