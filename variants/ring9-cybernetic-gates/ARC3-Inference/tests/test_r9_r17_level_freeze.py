"""R9-R17: the level freeze. A finished level's model is frozen, and the ladder starts on the next.

Author: Claude (Alpha build seat), 2026-10-01. MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1 §4 (L1);
DESIGN_VIRELAI_MEMORY_v2 M9; Director rulings 2026-10-01 (carry hypotheses only; record the win only).

On the live vc33 exit record: the G4-A study of E0005 completed level 1 at transition 26. Live (at
d2bf323) the run stopped there. Each test failed before R9-R17.
"""
from __future__ import annotations

from inference.framework.card_builder import build_card, world_model_digest
from inference.framework.controller_executor import ladder_end, next_owned_step
from inference.framework.life_record import undeclared
from inference.framework.memory_store import MemoryStore
from inference.framework.record_replay import lossless_outcome, load_record, replay, record_like_live
from test_r9_r15_replay_fidelity import FT09_EXIT, VC33_EXIT

WIN = {"action": "ACTION6", "row": 32, "col": 60}


def _vc33():
    result = replay(load_record(VC33_EXIT))
    return result.machine, result.grid


def test_the_finished_level_is_frozen_from_the_gate_machines_own_record():
    machine, _grid = _vc33()
    (level,) = machine.levels
    assert (level["level"], level["level_after"], level["frozen_at_transition"]) == (1, 2, 26)
    assert level["carry_status"] == "UNCONFIRMED" and level["gate_at_freeze"] == "G4.2-LEVER-ORBITS"
    assert set(level["product_types"]) == {
        "G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER", "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS",
    }
    levers = {item["entity_id"]: item for item in level["levers"]}
    assert levers["E0004"]["study"] == "EXPLAINED" and levers["E0004"]["orbit_class"] == "ABSORBING"
    assert levers["E0005"]["study"] == "INTERRUPTED" and levers["E0005"]["click"] == WIN


def test_the_win_is_recorded_as_an_untested_hypothesis_never_a_goal():
    """The same click failed 7 times on level 1 before it won: the board it was taken from mattered.
    This matches the observer's independent level lesson for the same run."""
    machine, _grid = _vc33()
    win = machine.levels[0]["win"]
    assert (win["transition_id"], win["action"], win["acted_lever"]) == (26, WIN, "E0005")
    assert win["earlier_same_action"] == [9, 10, 21, 22, 23, 24, 25]
    assert (win["hypothesis"], win["status"]) == ("WIN_NEEDS_CONTEXT_BEYOND_THE_ACTION", "UNTESTED")


def test_the_ladder_starts_again_on_level_two_and_the_run_does_not_stop():
    machine, _grid = _vc33()
    assert ladder_end(machine) is None
    assert machine.gate_id == "G0-ACTION-METADATA" and machine.lives.level == 2
    step = next_owned_step(machine)
    assert step.owner == "CONTROLLER" and step.refusal_key == ("G0-ACTION-METADATA", 1, 2)  # refusals are per level
    assert machine.completed_gate_rows() == []  # nothing carried as a verdict (ruling 2026-10-01)
    assert undeclared(machine) == [] and all(undeclared(item) == [] for item in machine._adapters.values())


def test_level_two_runs_g0_to_g3_on_its_own_board():
    """On level 2's spawn board (a stand-in world: every click only ticks a bar), the controller
    certifies G0, G1 and G2 and sweeps level 2's objects in G3, all rows tagged level 2."""
    machine, grid = _vc33()
    transition = 26
    for _ in range(40):
        step = next_owned_step(machine)
        if step.owner != "CONTROLLER" or machine.gate_id == "G3-LEVERS":
            break
        if step.kind == "ANSWER":
            machine.submit_answer(step.answer)
            continue
        probe = machine.validate_probe({"probe_token": step.probe_token}, [step.action])
        transition += 1
        grid, outcome = lossless_outcome(grid, transition, step.action, [[0, 90 - transition, 7, 4]])
        record_like_live(machine, probe, outcome, ["ACTION6"])  # with the live metadata refresh (R9-R20)
    assert [row["gate_id"] for row in machine.completed_gate_rows()] == ["G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER"]
    assert {row["level"] for row in machine.transition_index if row["transition_id"] > 26} == {2}


def test_memory_shows_the_frozen_level_and_keeps_level_one_out_of_level_two_recall():
    """A level-1 object is not the level-2 object at the same cell (the ring8 audit's lesson)."""
    machine, _grid = _vc33()
    store = MemoryStore(machine)
    (row,) = store.query("levels")["rows"]
    assert row["level"] == 1 and "products" not in row and row["win"]["acted_lever"] == "E0005"
    assert store.query("site", row=32, col=60)["total"] == 0
    assert store.query("transitions")["total"] == 26  # the whole-game record keeps level 1
    digest = world_model_digest(machine)
    assert digest[0].startswith("[prior] level 1 (frozen, unconfirmed here): E0004 ABSORBING, E0005 interrupted")
    card = build_card(machine)
    assert not card.over_budget


def test_a_game_with_no_level_change_freezes_nothing():
    machine = replay(load_record(FT09_EXIT)).machine
    assert machine.levels == [] and machine.lives.level == 1
    assert ladder_end(machine) is None and machine.gate_id == "PLAY-NORMAL"  # R9-R24 D22: normal play, not a stop
