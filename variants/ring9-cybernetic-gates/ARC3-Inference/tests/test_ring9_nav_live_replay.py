"""Pin the N5.1 ls20 record as live NAV evidence without inheriting its old G3 law.

Author: Sol (Alpha build seat), 2026-10-06.

N5.1 ran the pre-first-witness confirmation protocol.  The same recorded transition 18 is replayed
through the unified protocol to grade what the current controller learns from that live frame.  The
later reachability answers remain direct historical observations; their unified bounded-state
contract is covered by ``test_ring9_unified_presumed_unreachable`` until a unified live record
exists.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from inference.framework.record_replay import load_record, replay


FIXTURE = Path(__file__).parent / "fixtures" / "ls20_kaggle_n5_1_record.json.gz"


def test_live_transition_18_is_a_first_witness_under_the_unified_nav_law():
    record = deepcopy(load_record(FIXTURE))
    record["protocol"]["legacy_g3_confirmation_replay"] = False
    result = replay(record, max_steps=18, measure=False)

    assert result.stopped is None and result.steps_replayed == 18
    g3 = result.machine._adapters["G3-LEVERS"]
    assert g3._pending_confirmation is None
    assert len(g3._lever_discoveries) == 1
    discovery = next(iter(g3._lever_discoveries.values()))
    assert discovery["status"] == "LEVER_FOUND"
    assert discovery["channel"] == "BODY"
    assert discovery["remote_residue_cells"]
    assert g3.lifecycle_journal.entities[discovery["entity_id"]].state == "G4-READY"
    assert g3._target_index == 1


def test_fixture_preserves_live_reachability_releases_and_nav_intent():
    record = load_record(FIXTURE)
    reachability = [
        answer for answer in record["answers"]
        if answer["gate_id"] == "G3-LEVERS"
        and answer.get("answer_kind") == "TARGET_REACHABILITY"
    ]
    assert [answer["novel_prediction"]["status"] for answer in reachability] == [
        "PRESUMED_UNREACHABLE",
        "PRESUMED_UNREACHABLE",
        "PRESUMED_UNREACHABLE",
        "PRESUMED_UNREACHABLE",
    ]
    assert {answer["novel_prediction"]["target_entity_id"] for answer in reachability} == {
        "E0005", "E0006", "E0007",
    }
    transition_18 = next(step for step in record["steps"] if step["transition_id"] == 18)
    assert transition_18["decision"] == {"pilot_intent": "CONTACT_ATTEMPT"}
