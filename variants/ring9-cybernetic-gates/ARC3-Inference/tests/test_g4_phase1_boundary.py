"""Phase 1 must not deadlock on a boundary, now under the guided G4-A target.

Author: Claude (Alpha build seat), 2026-09-27.

Regression for REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md (the S1 hold deadlocked on a lever
whose orbit a level transition interrupted). Director rulings, 2026-09-27: cross-level work is a
separate gate (G9); G4 becomes stated targets that Duck executes as needed. These tests carry the
boundary-release semantics of 8cfb782 into the guided G4-A study: a level transition closes the
level's G4 study, and the machine always rests in a coherent state. Since R9-R10 (ruling D4) a
death on the same level returns the lever to the study for the next life, and only a lever that
keeps dying is released.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

from inference.framework.counter_verification import MaskLaw
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.virelai_gates import CyberneticGateMachine

ORBITS = "G4.2-LEVER-ORBITS"
LEVEL_CLOSED = "G4_LEVEL_STUDY_CLOSED_CROSS_LEVEL_IS_G9"
FIXTURE = Path(__file__).parent / "fixtures" / "vc33_kaggle_v1_g4_2_segment.json.gz"
HEX = "0123456789abcdef"


def _machine(initial, levers, mask_law=None):
    machine = CyberneticGateMachine(valid_actions=["ACTION6"], initial_grid=initial)
    machine.submit_answer({
        "answer_id": "G0-test",
        "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
        "semantic_claims": [],
        "epistemic_limit": "Effects remain unknown until observed.",
    })
    entity_ids = [item["entity_id"] for item in levers]
    for product in (
        MemoryProduct(
            product_id="EGO-test", product_type="EgoLaw", target_id="G1-EGO", revision=1,
            payload={"mode": "POINTER_GOD_MODE"}, dependencies=("G0-ACTION-METADATA",),
        ),
        MemoryProduct(
            product_id="COUNTER-test", product_type="CounterGateProduct",
            target_id="G2-COUNTER", revision=1, payload={"mask_law": None},
            dependencies=("G1-EGO",),
        ),
        MemoryProduct(
            product_id="LEVERS-test", product_type="LeverInventory", target_id="G3-LEVERS",
            revision=1, payload={"lever_entities": entity_ids, "clean_null_entities": []},
            dependencies=("G2-COUNTER",),
        ),
        MemoryProduct(
            product_id="ANATOMY-test", product_type="LeverEffectAnatomySet",
            target_id="G4-REACTIONS", revision=1,
            payload={"anatomies": [dict(item) for item in levers]},
            dependencies=("G3-LEVERS",),
        ),
    ):
        machine.target_journal.put(product)
    machine.counter.mask_law = mask_law
    return machine


def _outcome(before, after, transition_id, action, boundary=None):
    rows, cols = len(before), len(before[0])
    return {
        "transition_id": transition_id,
        "action": dict(action),
        "changed_cells": [
            {"row": r, "col": c, "before": before[r][c], "after": after[r][c]}
            for r in range(rows) for c in range(cols) if before[r][c] != after[r][c]
        ],
        "site_transitions": [
            {"row": r, "col": c, "before": before[r][c], "after": after[r][c]}
            for r in range(rows) for c in range(cols)
        ],
        "shape_before": [rows, cols],
        "shape_after": [rows, cols],
        "boundary_event": boundary or {"state": "PLAYING"},
    }


def _act(machine, action, before, after, transition_id, boundary=None):
    """Duck's own choice of action through the guided capability."""
    capability = machine.next_probe_capability()
    assert capability is not None, "expected the guided G4-A capability"
    assert capability["purpose"] == "GUIDED_ACTION"
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [action])
    return machine.record_outcome(probe, _outcome(before, after, transition_id, action, boundary))


def _explain(machine, entity_id, mechanism="Consecutive presses of this lever reached the observed stopping state."):
    templates = {item["entity_id"]: item for item in machine.gate_view()["answer_templates"]}
    machine.submit_answer({
        **templates[entity_id],
        "mechanism_explanation": mechanism,
        "competing_models": ["The same lever may respond differently from another state."],
        "falsifier": "A repeat from this exact masked state later behaves differently.",
    })


def _g(value):
    return ((0, value), (0, 0))


A = {"action": "ACTION6", "row": 1, "col": 0}
B = {"action": "ACTION6", "row": 1, "col": 1}
SYNTHETIC_LEVERS = [{"entity_id": "E-A", "intervention": A}, {"entity_id": "E-B", "intervention": B}]
LEVEL_UP = {"level_completed": True, "level_before": 1, "level_after": 2, "state": "NOT_FINISHED"}
GAME_OVER = {"game_over": True, "level_before": 1, "level_after": 1, "state": "GAME_OVER"}


def _orbit_product(machine):
    return machine.target_journal.active_product(ORBITS).payload


def test_g4_2_is_not_reported_satisfied_while_a_lever_is_pending():
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    _act(machine, A, _g(2), _g(2), 1)   # null
    _act(machine, A, _g(2), _g(2), 2)   # confirmation null
    _explain(machine, "E-A")
    assert machine.gate_id == ORBITS
    view = machine.gate_view()
    assert view["status"] == "PROBE_REQUIRED"
    assert view["next_operation"] == "QUERY_NEXT_PROBE"
    statuses = {item["entity_id"]: item["status"] for item in view["levers"]}
    assert statuses == {"E-A": "EXPLAINED", "E-B": "NOT_STARTED"}
    assert _orbit_product(machine)["pending_lever_entities"] == ["E-B"]


def test_level_transition_interrupts_the_lever_and_closes_the_level_study():
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    _act(machine, A, _g(2), _g(2), 1)
    _act(machine, A, _g(2), _g(2), 2)
    _explain(machine, "E-A")
    _act(machine, B, _g(2), _g(3), 3)
    _act(machine, B, _g(3), _g(7), 4, LEVEL_UP)

    payload = _orbit_product(machine)
    assert payload["lever_entities"] == ["E-A"]
    assert payload["pending_lever_entities"] == []
    assert payload["interrupted_lever_entities"] == ["E-B"]
    assert payload["phase1_status"] == "CLOSED_BY_LEVEL_BOUNDARY"
    assert payload["level_boundary"]["level_after"] == 2
    assert payload["lever_classes"] == {"E-A": "ABSORBING"}
    assert [row["entity_id"] for row in payload["orbits"]] == ["E-A"]

    # No deadlock: a coherent closed state with no capability and nothing to answer.
    view = machine.gate_view()
    assert view["next_operation"] == LEVEL_CLOSED
    assert view["status"] == "SATISFIED"
    assert view["answer_template"] is None
    assert machine.next_probe_capability() is None


def test_same_level_death_returns_the_lever_to_the_study_next_life():
    """Ruling D4 (R9-R10): knowledge persists and the world resets, so the lever is re-studied."""
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    _act(machine, A, _g(2), _g(3), 1, GAME_OVER)

    payload = _orbit_product(machine)
    assert payload["interrupted_lever_entities"] == []
    assert payload["pending_lever_entities"] == ["E-A", "E-B"]
    assert payload["life_restudies"] == {"E-A": 1}
    assert machine.orbit_view("E-A")["status"] == "RUN_ENDED_RESTART_NEEDED"

    _act(machine, A, _g(3), _g(3), 2)  # the next life: the same lever, run again
    _act(machine, A, _g(3), _g(3), 3)
    _explain(machine, "E-A")
    _act(machine, B, _g(3), _g(3), 4)
    _act(machine, B, _g(3), _g(3), 5)
    _explain(machine, "E-B")
    payload = _orbit_product(machine)
    assert payload["lever_entities"] == ["E-A", "E-B"]
    assert payload["phase1_status"] == "COMPLETE"
    assert machine._adapters["G4.2-LEVER-ORBITS"].assess().disposition == "SATISFIED"  # the ladder then opens G4-B


def test_a_lever_that_keeps_dying_is_released_after_the_life_cap_and_the_rest_drains():
    """The 8cfb782 boundary release still holds, after MAX_LIFE_RESTUDIES deaths: no deadlock."""
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    for life in range(3):
        _act(machine, A, _g(2 + life), _g(3 + life), 1 + life, GAME_OVER)

    payload = _orbit_product(machine)
    assert payload["interrupted_lever_entities"] == ["E-A"]
    assert payload["pending_lever_entities"] == ["E-B"]
    assert payload["life_restudies"] == {"E-A": 3}
    assert payload["phase1_status"] == "IN_PROGRESS"

    _act(machine, B, _g(5), _g(5), 4)
    _act(machine, B, _g(5), _g(5), 5)
    _explain(machine, "E-B")
    payload = _orbit_product(machine)
    assert payload["lever_entities"] == ["E-B"]
    assert payload["pending_lever_entities"] == []
    assert payload["phase1_status"] == "COMPLETE"
    assert machine._adapters["G4.2-LEVER-ORBITS"].assess().disposition == "SATISFIED"  # the ladder then opens G4-B


def _load_fixture():
    return json.loads(gzip.open(FIXTURE).read())


def _decode(rows):
    return tuple(tuple(HEX.index(ch) for ch in row) for row in rows)


def test_vc33_kaggle_v1_segment_replayed_as_duck_actions_matches_the_record_and_closes():
    """The real vc33 G4.2 presses, replayed as if Duck chose them under the guided target.

    Fidelity: every masked address equals the one the Kaggle run recorded. Semantics: E0004 reached
    its null but was never confirmed (the next press was E0005), so its run ends unconfirmed; the
    sixth E0005 press changed the level, which closes the level's study without a deadlock.
    """
    data = _load_fixture()
    steps = data["steps"]
    mask = MaskLaw(
        law_id="MASK-V1", law_version_id="MASK-V1-616e3428c12c843c", revision=1,
        status="SUPPORTED", cells=tuple(tuple(cell) for cell in data["mask_cells"]),
        rewrite="counter", witness_evidence_refs=(), demonstration_ref="",
    )
    machine = _machine(_decode(steps[0]["before"]), data["levers"], mask)
    interventions = {item["entity_id"]: item["intervention"] for item in data["levers"]}

    for step in steps:
        event = _act(
            machine, interventions[step["entity_id"]], _decode(step["before"]),
            _decode(step["after"]), step["transition_id"], step["boundary_event"],
        )
        assert event["lever_entity_id"] == step["entity_id"]
    detail_4 = machine.orbit_view("E0004")["runs"][0]
    detail_5 = machine.orbit_view("E0005")["runs"][0]
    replayed = detail_4["orbit"]["steps"] + detail_5["orbit"]["steps"]
    assert len(replayed) == len(steps)
    for recorded, step in zip(steps, replayed):
        assert step["before_world_address"] == recorded["recorded_before_address"]
        assert step["after_world_address"] == recorded["recorded_after_address"]
        assert step["disposition"] == recorded["recorded_disposition"]
    assert detail_4["orbit"]["state_sequence"] == data["e0004_recorded_state_sequence"]
    assert detail_4["status"] == "BROKEN"
    assert detail_5["status"] == "INTERRUPTED"

    payload = _orbit_product(machine)
    assert payload["lever_classes"] == {}
    assert payload["interrupted_lever_entities"] == ["E0005"]
    assert payload["unstudied_lever_entities"] == ["E0004"]
    assert payload["phase1_status"] == "CLOSED_BY_LEVEL_BOUNDARY"
    assert machine.gate_view()["next_operation"] == LEVEL_CLOSED
    assert machine.next_probe_capability() is None
