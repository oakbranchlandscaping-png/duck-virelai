"""Phase 1 must not deadlock on a boundary-interrupted lever.

Author: Claude (Alpha build seat), 2026-09-27.

Regression for REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md. In that Kaggle run the S1 return
edge held G4.2 for a lever whose orbit had been interrupted by a level transition; the lever could
no longer be activated or answered, so the machine offered no legal move for ~90 minutes.

Director ruling (2026-09-27): cross-level work is a separate gate (G9). G4 records a boundary
interruption and releases the lever from Phase-1 pending; a level transition closes the previous
level's G4 study instead of carrying it across.
"""
from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from inference.framework.counter_verification import MaskLaw
from inference.framework.cybernetic_targeting import MemoryProduct
from inference.framework.virelai_gates import CyberneticGateMachine, GateContractError

ORBITS = "G4.2-LEVER-ORBITS"
LIMITS = "G4.3-LEVER-LIMITS"
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


def _press(machine, before, after, transition_id, boundary=None):
    capability = machine.next_probe_capability()
    assert capability is not None, "expected an admissible G4.2 activation"
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, capability["actions"])
    outcome = _outcome(before, after, transition_id, capability["actions"][0], boundary)
    return machine.record_outcome(probe, outcome)


def _answer_current(machine, mechanism="Consecutive presses of this lever reached the observed stopping state."):
    template = machine.gate_view()["answer_template"]
    machine.submit_answer({
        **template,
        "mechanism_explanation": mechanism,
        "competing_models": ["The same lever may respond differently from another state."],
        "falsifier": "A repeat from this exact masked state later behaves differently.",
    })


def _g(value):
    return ((0, value), (0, 0))


SYNTHETIC_LEVERS = [
    {"entity_id": "E-A", "intervention": {"action": "ACTION6", "row": 1, "col": 0}},
    {"entity_id": "E-B", "intervention": {"action": "ACTION6", "row": 1, "col": 1}},
]
LEVEL_UP = {"level_completed": True, "level_before": 1, "level_after": 2, "state": "NOT_FINISHED"}
GAME_OVER = {"game_over": True, "level_before": 1, "level_after": 1, "state": "GAME_OVER"}


def _orbit_product(machine):
    return machine.target_journal.active_product(ORBITS).payload


def test_g4_2_is_not_reported_satisfied_while_a_lever_is_pending():
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    _press(machine, _g(2), _g(2), 1)
    _answer_current(machine)
    assert machine.gate_id == ORBITS
    view = machine.gate_view()
    assert view["progress"]["current_entity_id"] == "E-B"
    assert view["status"] == "PROBE_REQUIRED"
    assert view["next_operation"] == "QUERY_NEXT_PROBE"


def test_level_transition_interrupts_the_lever_and_closes_the_level_study():
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    _press(machine, _g(2), _g(2), 1)
    _answer_current(machine)
    _press(machine, _g(2), _g(3), 2)
    _press(machine, _g(3), _g(7), 3, LEVEL_UP)

    payload = _orbit_product(machine)
    assert payload["lever_entities"] == ["E-A"]
    assert payload["pending_lever_entities"] == []
    assert payload["interrupted_lever_entities"] == ["E-B"]
    assert payload["phase1_status"] == "CLOSED_BY_LEVEL_BOUNDARY"
    assert payload["level_boundary"]["level_after"] == 2
    assert payload["lever_classes"] == {"E-A": "ABSORBING"}
    assert [row["entity_id"] for row in payload["orbits"]] == ["E-A"]

    # No deadlock: the machine rests in a coherent closed state, not a refused-probe loop.
    assert machine.gate_id == ORBITS
    view = machine.gate_view()
    assert view["next_operation"] == LEVEL_CLOSED
    assert view["status"] == "SATISFIED"
    assert view["answer_template"] is None
    assert not view.get("probe_available")
    assert machine.next_probe_capability() is None
    # G4.3 is same-level Phase-2 study; it must not open across the level transition.
    with pytest.raises(GateContractError, match="cross-level"):
        machine._adapters[LIMITS]._orbit_product()


def test_same_level_boundary_releases_the_lever_and_phase2_opens():
    machine = _machine(_g(2), SYNTHETIC_LEVERS)
    _press(machine, _g(2), _g(3), 1, GAME_OVER)

    payload = _orbit_product(machine)
    assert payload["interrupted_lever_entities"] == ["E-A"]
    assert payload["pending_lever_entities"] == ["E-B"]
    assert payload["phase1_status"] == "IN_PROGRESS"
    assert machine.gate_id == ORBITS
    assert machine.gate_view()["progress"]["current_entity_id"] == "E-B"

    _press(machine, _g(3), _g(3), 2)
    _answer_current(machine)
    payload = _orbit_product(machine)
    assert payload["lever_entities"] == ["E-B"]
    assert payload["pending_lever_entities"] == []
    assert payload["phase1_status"] == "COMPLETE"
    assert machine.gate_id == LIMITS


def _load_fixture():
    return json.loads(gzip.open(FIXTURE).read())


def _decode(rows):
    return tuple(tuple(HEX.index(ch) for ch in row) for row in rows)


def test_vc33_kaggle_v1_g4_2_replay_matches_the_record_and_closes_cleanly():
    data = _load_fixture()
    steps = data["steps"]
    mask = MaskLaw(
        law_id="MASK-V1", law_version_id="MASK-V1-616e3428c12c843c", revision=1,
        status="SUPPORTED", cells=tuple(tuple(cell) for cell in data["mask_cells"]),
        rewrite="counter", witness_evidence_refs=(), demonstration_ref="",
    )
    machine = _machine(_decode(steps[0]["before"]), data["levers"], mask)
    interventions = {item["entity_id"]: item["intervention"] for item in data["levers"]}

    for index, step in enumerate(steps):
        capability = machine.next_probe_capability()
        assert capability is not None, f"no admissible activation at replay step {index + 1}"
        assert capability["actions"] == [interventions[step["entity_id"]]]
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        assert probe.probe_id == step["probe_id"]
        event = machine.record_outcome(probe, _outcome(
            _decode(step["before"]), _decode(step["after"]), step["transition_id"],
            capability["actions"][0], step["boundary_event"],
        ))
        # Fidelity: the replay computes exactly the masked addresses the Kaggle run recorded.
        assert event["orbit_step"]["before_world_address"] == step["recorded_before_address"]
        assert event["orbit_step"]["after_world_address"] == step["recorded_after_address"]
        assert event["orbit_step"]["disposition"] == step["recorded_disposition"]
        if step["recorded_disposition"] == "NULL_AT_OBSERVED_STATE":
            template = machine.gate_view()["answer_template"]
            assert template["state_sequence"] == data["e0004_recorded_state_sequence"]
            _answer_current(machine, data["e0004_answer_mechanism"])
            # The live S1 signature: stay in G4.2 and move to the next lever.
            assert machine.gate_id == ORBITS
            assert machine.gate_view()["progress"]["current_entity_id"] == "E0005"

    payload = _orbit_product(machine)
    assert payload["lever_classes"] == {"E0004": "ABSORBING"}
    assert payload["interrupted_lever_entities"] == ["E0005"]
    assert payload["pending_lever_entities"] == []
    assert payload["phase1_status"] == "CLOSED_BY_LEVEL_BOUNDARY"
    assert machine.gate_id == ORBITS
    assert machine.gate_view()["next_operation"] == LEVEL_CLOSED
    assert machine.next_probe_capability() is None
