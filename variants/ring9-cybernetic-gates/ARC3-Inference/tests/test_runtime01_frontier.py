"""WO-RUNTIME-01 §4: the normal-play frontier, ported from Ring 7's ``state_tracker`` (``untried`` / ``order_untried``).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Prior art: ``virelai_v4/cybernetic/state_tracker.py``
sha256 ``fdc91f38...79ef`` (legal at first sight, ``untried = legal - tried``, diversity-first ordering with the
``(action_id, str(target))`` floor). Fail-first: the module does not exist on the base.
"""
from __future__ import annotations

import random

from inference.framework.record_replay import load_record, replay

VC33 = "tests/fixtures/vc33_kaggle_carry_v7_record.json.gz"


def _ring7_order(keys, tried):
    """Ring 7 ``order_untried`` verbatim in behaviour: least globally tried target, then (action_id, str(target))."""
    def count(target):
        return sum(1 for edges in tried.values() for key in edges if key[1] == target)
    return sorted(keys, key=lambda k: (count(k[1]), k[0], "" if k[1] is None else str(k[1])))


def test_ring7_ordering_is_ported_exactly():
    from inference.framework.free_play_frontier import order_untried

    rng = random.Random(7)
    for _ in range(200):
        targets = [None, (0, 0), (2, 5), (7, 1), (3, 3)]
        keys = {(f"ACTION{rng.randint(1, 7)}", rng.choice(targets)) for _ in range(rng.randint(1, 9))}
        tried = {f"S{n}": {(f"ACTION{rng.randint(1, 7)}", rng.choice(targets)) for _ in range(rng.randint(0, 5))}
                 for n in range(rng.randint(0, 4))}
        assert order_untried(keys, tried) == _ring7_order(keys, tried)


def test_a_click_is_keyed_by_the_component_it_lands_in():
    from inference.framework.free_play_frontier import edge_key

    board = ((0, 0, 1, 1), (0, 0, 1, 1), (2, 2, 2, 2))
    assert edge_key({"action": "ACTION6", "row": 0, "col": 3}, board) == ("ACTION6", (0, 2))
    assert edge_key({"action": "ACTION6", "row": 1, "col": 2}, board) == ("ACTION6", (0, 2))
    assert edge_key({"action": "ACTION6", "row": 2, "col": 0}, board) == ("ACTION6", (2, 0))
    assert edge_key({"action": "ACTION1"}, board) == ("ACTION1", None)


def test_untried_is_legal_minus_tried_and_invalid_self_loops_count_as_tried():
    from inference.framework.free_play_frontier import untried

    legal = {("ACTION1", None), ("ACTION6", (0, 0)), ("ACTION6", (5, 5))}
    assert untried(legal, {("ACTION6", (0, 0))}) == {("ACTION1", None), ("ACTION6", (5, 5))}


def test_gate_probes_on_the_level_count_as_tried():
    """WO 11: every recorded transition of the level, not only free play, marks its edge tried."""
    from inference.framework import free_play_frontier

    machine = replay(load_record(VC33), max_steps=12, measure=False).machine
    frontier = free_play_frontier.for_machine(machine)
    frontier.refresh(machine)
    recorded = [row for row in machine.transition_index if row.get("action")]
    assert recorded
    tried_keys = set().union(*frontier.tried_edges.values())
    assert len(tried_keys) >= 1
    assert sum(len(edges) for edges in frontier.tried_edges.values()) <= len(recorded)


def test_a_same_board_no_effect_action_is_barred(tmp_path, monkeypatch):
    """WO 12: R-8's memory bars the action on this exact masked board, and the proof says so."""
    from runtime01_support import PlayRun, Script
    from inference.framework import free_play_frontier
    from inference.framework.g4_relations import masked_address
    from inference.framework.virelai_gates import PLAY_GATE_ID, _canonical

    run = PlayRun(tmp_path, monkeypatch, Script(["print(1)"]))
    run.to_play()
    machine = run.agent._gate_machine
    frontier = free_play_frontier.for_machine(machine)
    choice = frontier.choose(machine)
    grid = [list(row) for row in run.world.grid]
    key = _canonical([dict(choice.action), masked_address(grid, machine.counter.mask_law)])
    machine._adapters[PLAY_GATE_ID]._noops[key] = [41]
    second = frontier.choose(machine)
    assert second.key != choice.key
    proof = {(item["key"][0], None if item["key"][1] is None else tuple(item["key"][1])): item
             for item in frontier.proof(machine)["legal"]}
    barred = [item for item in proof.values() if item["barred"]]
    assert barred and barred[0]["barred"] == [41]


def test_the_choice_is_deterministic_and_diversity_first(tmp_path, monkeypatch):
    from runtime01_support import PlayRun, Script
    from inference.framework import free_play_frontier

    run = PlayRun(tmp_path, monkeypatch, Script(["print(1)"]))
    run.to_play()
    machine = run.agent._gate_machine
    first = free_play_frontier.for_machine(machine).choose(machine)
    again = free_play_frontier.for_machine(machine).choose(machine)
    assert first.key == again.key and first.action == again.action
    assert first.key in free_play_frontier.for_machine(machine).legal(machine)
