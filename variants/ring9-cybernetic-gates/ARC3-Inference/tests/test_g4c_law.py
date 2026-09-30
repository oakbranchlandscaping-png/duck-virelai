"""R9-R13: G4-C tests the description with one new prediction (Director rulings 2026-09-30).

Author: Claude (Alpha build seat), 2026-09-30. BUILD_PLAN_G4_CLICK_COMPLETION_v11 §Rulings.

On the real ft09 levers (the live memory-v1 record, continued on the offline world it defines):
supported, the law set is certified and the run ends; contradicted, G4-B reopens and the level's
record keeps the contradiction; an action already graded from the same masked board is refused.
"""
from __future__ import annotations

import pytest

from inference.framework.card_builder import build_card, world_model_digest
from inference.framework.controller_executor import ladder_end, next_owned_step
from inference.framework.virelai_gates import GateContractError
from test_g4b_relations import TILES, _click, _describe, _predict, _take, start_g4b

RELATIONS, LAW = "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"
@pytest.fixture
def g4b():
    return start_g4b()


INDEPENDENT = [{"levers": ["E0053", "E0054"], "claim": "pressing E0053 left E0054 unchanged here", "prediction_refs": ["P1"]}]


def _law(machine, entity: str, expected: dict | None = None, relations: list | None = None):
    return machine.submit_answer({
        "answer_kind": "LAW_PREDICTION", "from_relations": [0] if relations is None else relations,
        "action": _click(entity), "expected": expected if expected is not None else {entity: "STEPS"},
        "elsewhere": "NO_CHANGE", "because": f"relation 0 says {entity} changes only its own tile",
    })


def _described(machine, world, extra: tuple[str, ...] = ()):
    """G4-B closed: every lever pressed once (P1..P8), then any extra presses, then the description."""
    for entity in (*TILES, *extra):
        _predict(machine, entity, {entity: "STEPS", "E0054": "STEPS" if entity == "E0054" else "UNCHANGED"})
        _take(machine, world)
    _describe(machine, INDEPENDENT)
    assert machine.gate_id == LAW


def test_a_supported_new_prediction_certifies_the_law_set_and_ends_the_ladder(g4b):
    machine, world = g4b
    _described(machine, world)
    card = build_card(machine).payload
    assert card["answer_template"]["answer_kind"] == "LAW_PREDICTION"
    assert card["subject"]["relations"][0]["number"] == 0 and card["subject"]["description"].startswith("Eight tiles")
    assert next_owned_step(machine).owner == "DUCK"
    _law(machine, "E0055")
    assert next_owned_step(machine).owner == "CONTROLLER"
    _take(machine, world)
    law = machine.target_journal.active_product(LAW).payload
    assert law["status"] == "COMPLETE" and law["law_test"]["status"] == "SUPPORTED"
    assert law["relations"][0]["prediction_refs"] == ["P1"] and law["law_test"]["from_relations"] == [0]
    assert ladder_end(machine) == "every built gate is satisfied, through G4-C; the next slice is not built"
    assert any(line.startswith(f"[{LAW}] law: 1 relations · new test SUPPORTED") for line in world_model_digest(machine))


def test_a_contradicted_prediction_reopens_g4b_and_stays_on_the_record(g4b):
    machine, world = g4b
    _described(machine, world)
    _law(machine, "E0055", {"E0055": "UNCHANGED"})
    _take(machine, world)
    assert machine.gate_id == RELATIONS and machine.target_journal.active_product(RELATIONS) is None  # reopened
    view = build_card(machine).payload
    assert "L1" in view["goal"]["answer_template_note"] and view["answer_template"]["answer_kind"] == "LEVER_RELATIONS"
    ledger = machine.relations_view()["predictions"]
    assert ledger[-1]["prediction_id"] == "L1" and ledger[-1]["status"] == "CONTRADICTED"
    with pytest.raises(GateContractError, match="CONTRADICTED"):
        _describe(machine, [{**INDEPENDENT[0], "prediction_refs": ["L1"]}])
    _describe(machine, INDEPENDENT)  # the revised description; G4-C asks for a new test again
    assert machine.gate_id == LAW and machine.status == "ANSWER_REQUIRED"
    _law(machine, "E0056")
    _take(machine, world)
    law = machine.target_journal.active_product(LAW).payload
    assert law["status"] == "COMPLETE" and [item["status"] for item in law["tests"]] == ["CONTRADICTED", "SUPPORTED"]
    assert "1 reopenings of G4-B" in law["digest_lines"][0]


def test_new_means_an_action_no_graded_prediction_has_taken_from_this_board(g4b):
    machine, world = g4b
    _described(machine, world, extra=("E0053", "E0053"))  # P9 and P10: E0053 away and back
    with pytest.raises(GateContractError, match="already graded from this same board"):
        _law(machine, "E0053")  # P9 took exactly this action from exactly this masked board
    with pytest.raises(GateContractError, match="from_relations must be numbers from 0 to 0"):
        _law(machine, "E0054", relations=[3])
    with pytest.raises(GateContractError, match="from_relations must be a non-empty list"):
        _law(machine, "E0054", relations=[])
    _law(machine, "E0054")
    with pytest.raises(GateContractError, match="frozen and not yet taken"):
        _law(machine, "E0055")
