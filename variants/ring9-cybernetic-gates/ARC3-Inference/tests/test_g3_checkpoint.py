from inference.framework.counter_verification import MaskLaw
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.g3_checkpoint import evaluate_g3_checkpoint
from inference.framework.virelai_gates import CyberneticGateMachine


GRID = ((0, 0, 0, 0), (0, 2, 0, 3), (0, 0, 0, 0))


def _machine():
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=GRID)
    machine.submit_answer({
        "answer_id": "G0-test",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EGO-test", product_type="EgoLaw", target_id="G1-EGO", revision=1,
        payload={"mode": "POINTER_GOD_MODE"}, dependencies=("G0-ACTION-METADATA",),
    ))
    machine.target_journal.put(MemoryProduct(
        product_id="COUNTER-test", product_type="CounterGateProduct", target_id="G2-COUNTER", revision=1,
        payload={"counter_model": {"model_id": "CM-test"}, "mask_law": {"law_version_id": "MASK-1"},
                 "ranked_object_frontier": {"schema": "virelai-ranked-object-frontier-v1"}},
        dependencies=("G1-EGO",),
    ))
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-1", law_version_id="MASK-1", revision=1, status="LOCKED",
        cells=(), rewrite="remove sealed counter cells from the derived G3 view",
        witness_evidence_refs=("E-counter-witness",),
        demonstration_ref="E-counter-demonstration",
    )
    return machine


def _nav_machine():
    actions = ["ACTION1", "ACTION2", "ACTION3", "ACTION4"]
    machine = CyberneticGateMachine(valid_actions=actions, initial_grid=GRID)
    machine.submit_answer({
        "answer_id": "G0-nav-test",
        "action_metadata": [
            {"action": action, "requires_coordinates": False} for action in actions
        ],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    machine.target_journal.put(MemoryProduct(
        product_id="EGO-nav-test", product_type="EgoLaw", target_id="G1-EGO", revision=1,
        payload={"mode": "EMBODIED_EGO"}, dependencies=("G0-ACTION-METADATA",),
    ))
    machine.target_journal.put(MemoryProduct(
        product_id="COUNTER-nav-test", product_type="CounterGateProduct", target_id="G2-COUNTER", revision=1,
        payload={"counter_model": {"model_id": "CM-nav-test"}, "mask_law": {"law_version_id": "MASK-NAV"},
                 "ranked_object_frontier": {"schema": "virelai-ranked-object-frontier-v1"}},
        dependencies=("G1-EGO",),
    ))
    machine.counter.mask_law = MaskLaw(
        law_id="MASK-NAV", law_version_id="MASK-NAV", revision=1, status="LOCKED",
        cells=(), rewrite="remove sealed counter cells from the derived G3 view",
        witness_evidence_refs=("E-counter-witness",),
        demonstration_ref="E-counter-demonstration",
    )
    machine._adapters["G3-LEVERS"]._navigation_limit = 1
    return machine


def _outcome(step, changed):
    return {
        "transition_id": step,
        "action": {"action": "ACTION6", "row": 1, "col": 1},
        "changed_cells": [{"row": row, "col": col} for row, col in changed],
        "site_transitions": [
            {"row": row, "col": col, "before": GRID[row][col], "after": GRID[row][col]}
            for row in range(3) for col in range(4)
        ],
        "shape_before": [3, 4], "shape_after": [3, 4],
        "boundary_event": {"state": "PLAYING"},
    }


def _finish_click_sweep(machine, trace, *, start_step):
    step = start_step
    while True:
        capability = machine.next_probe_capability()
        if capability is None:
            break
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        trace.append(machine.record_outcome(probe, _outcome(step, [])))
        step += 1


def _submit_inventory(machine):
    # Checkpoint construction evaluates the lossless store.  The model-facing
    # completion card intentionally omits the lifecycle journal.
    view = machine.snapshot()
    ready = [
        entity_id for entity_id, row in view["lifecycle_journal"]["entities"].items()
        if row["state"] == "G4-READY"
    ]
    refs = [
        ref for entity_id in ready
        for ref in view["lifecycle_journal"]["entities"][entity_id]["witness_refs"]
    ]
    clean_null = [
        entity_id for entity_id, row in view["lifecycle_journal"]["entities"].items()
        if row["state"] == "G3-CLOSED" and not row["witness_refs"]
    ]
    refs.extend(
        view["lifecycle_journal"]["entities"][entity_id]["events"][-1]["evidence_ref"]
        for entity_id in clean_null
    )
    return machine.submit_answer({
        "answer_kind": "LEVER_INVENTORY",
        "lever_entities": ready,
        "clean_null_entities": clean_null,
        "ambiguous_entities": [],
        "explanation": "The completed click roster isolated the witnessed lever entities.",
        "evidence_refs": refs,
        "competing_models": ["The response was spontaneous rather than intervention-caused."],
        "falsifier": "A reset and repeated intervention fails to reproduce the response.",
    })


def _submit_pending_dossier(machine, *, explanation=None):
    template = machine.gate_view()["answer_template"]
    return machine.submit_answer({
        **template,
        "explanation": explanation or (
            "The confirmed click changes the admitted target residue while counter bookkeeping "
            "remains outside the supplied causal effect summary."
        ),
        "competing_models": ["A hidden autonomous process produced the same visible response."],
        "falsifier": "A later identical click repeatedly fails to reproduce the scoped response.",
    })


def test_checkpoint_certificate_passes_complete_click_trace():
    machine = _machine()
    trace = []
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    event = machine.record_outcome(probe, _outcome(1, [(1, 1)]))
    trace.append(event)
    confirm = machine.next_probe_capability()
    confirm_probe = machine.validate_probe({"probe_token": confirm["probe_token"]}, confirm["actions"])
    trace.append(machine.record_outcome(confirm_probe, _outcome(2, [(1, 1)])))
    _submit_pending_dossier(machine)
    second = machine.next_probe_capability()
    second_probe = machine.validate_probe({"probe_token": second["probe_token"]}, second["actions"])
    trace.append(machine.record_outcome(second_probe, _outcome(3, [])))
    _finish_click_sweep(machine, trace, start_step=4)
    machine.next_probe()
    _submit_inventory(machine)
    certificate = evaluate_g3_checkpoint(
        trace,
        world_type="CLICK_GOD_MODE",
        final_snapshot=machine._adapters["G3-LEVERS"].snapshot(),
    )
    assert certificate.status == "PASS"
    assert all(item["status"] == "PASS" for item in certificate.checks)


def test_contradicted_only_trace_does_not_vacuously_pass_checkpoint():
    machine = _machine()
    trace = []
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    event = machine.record_outcome(probe, _outcome(1, [(1, 1)]))
    trace.append(event)
    confirm = machine.next_probe_capability()
    confirm_probe = machine.validate_probe({"probe_token": confirm["probe_token"]}, confirm["actions"])
    contradicted = machine.record_outcome(confirm_probe, _outcome(2, []))
    trace.append(contradicted)
    assert contradicted["confirmation"]["status"] == "CONTRADICTED"
    _finish_click_sweep(machine, trace, start_step=3)
    certificate = evaluate_g3_checkpoint(
        trace, world_type="CLICK_GOD_MODE", final_snapshot=machine.snapshot()
    )
    assert certificate.status == "FAIL"
    check = next(item for item in certificate.checks if item["name"] == "accepted_lever_inventory")
    assert check["status"] == "FAIL"


def test_checkpoint_recomputes_strict_prospectivity():
    machine = _machine()
    trace = []
    first = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    event = machine.record_outcome(probe, _outcome(1, [(1, 1)]))
    trace.append(event)
    confirm = machine.next_probe_capability()
    confirm_probe = machine.validate_probe({"probe_token": confirm["probe_token"]}, confirm["actions"])
    confirmation = machine.record_outcome(confirm_probe, _outcome(2, [(1, 1)]))
    confirmation["confirmation"]["graded_at_transition"] = 1
    trace.append(confirmation)
    _submit_pending_dossier(machine)
    _finish_click_sweep(machine, trace, start_step=3)
    certificate = evaluate_g3_checkpoint(
        trace, world_type="CLICK_GOD_MODE", final_snapshot=machine.snapshot()
    )
    check = next(item for item in certificate.checks if item["name"] == "strict_prospectivity")
    assert check["status"] == "FAIL"


def test_navigation_budget_exhaustion_without_contact_does_not_pass_checkpoint():
    machine = _nav_machine()
    trace = []
    step = 1
    while True:
        capability = machine.next_probe_capability()
        if capability is None:
            break
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"], "pilot_intent": "CONTACT_ATTEMPT"},
            [{"action": "ACTION1"}],
        )
        outcome = _outcome(step, [])
        outcome["action"] = {"action": "ACTION1"}
        outcome["refused_contact"] = True
        trace.append(machine.record_outcome(probe, outcome))
        step += 1
    certificate = evaluate_g3_checkpoint(
        trace, world_type="NAVIGATION", final_snapshot=machine.snapshot()
    )
    assert certificate.status == "FAIL"
    assert machine.snapshot()["scheduler"]["complete_reason"] == "NAV_ENUMERATION_COMPLETE"


def test_active_ambiguous_live_shape_cannot_pass_vacuously():
    snapshot = {
        "status": "ACTIVE",
        "mask_law_ref": "MASK-1",
        "scheduler": {"complete_reason": "CLICK_ENUMERATION_COMPLETE", "pending_confirmation": None},
        "attribution_contract": {"dossier_answers": [], "inventory_answer": None},
        "lifecycle_journal": {
            "entities": {
                "E1": {"state": "G3-CLOSED", "witness_refs": [], "answer_refs": []},
                "E2": {"state": "AMBIGUOUS", "witness_refs": [], "answer_refs": []},
            }
        },
    }
    certificate = evaluate_g3_checkpoint([], world_type="CLICK_GOD_MODE", final_snapshot=snapshot)
    assert certificate.status == "FAIL"
    assert next(
        item for item in certificate.checks if item["name"] == "accepted_lever_inventory"
    )["status"] == "FAIL"
