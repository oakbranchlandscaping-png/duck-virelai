from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

from inference.framework.virelai_clock import compile_clock_patterns


@dataclass(frozen=True)
class Delta:
    row: int
    col: int
    before_class: int
    after_class: int


class Record:
    layers = (SimpleNamespace(rows=4, cols=12),)

    def __init__(self, counts):
        cells = []
        for class_id, count in counts.items():
            cells.extend([class_id] * count)
        cells.extend([0] * (48 - len(cells)))
        self._cells = bytes(cells)

    def layer_bytes(self, index):
        return self._cells


def transition(step, action, deltas, *, acted_cell=None):
    return SimpleNamespace(
        transition_id=step,
        actor="DUCK",
        level_before=1,
        level_after=1,
        geometry_changed=False,
        level_completed=False,
        game_over=False,
        run_complete=False,
        action_name=action,
        acted_cell=acted_cell,
        cell_deltas=tuple(deltas),
    )


def draining(n=8, rates=None, same_action=False, targeted=False):
    rates = rates or [1] * n
    result = []
    cursor = 0
    for step, rate in enumerate(rates, 1):
        ds = []
        for _ in range(rate):
            ds.append(Delta(0, cursor, 7, 4))
            cursor += 1
        action = "LEFT" if same_action else ("LEFT" if step % 2 else "RIGHT")
        result.append(
            transition(step, action, ds, acted_cell=(0, cursor - 1) if targeted else None)
        )
    return result


def test_fixture_key_is_frozen_and_has_ten_cases():
    key = json.loads((Path(__file__).parent / "fixtures/clock/fixture_key.json").read_text())
    assert key["frozen_before_detector_run"] is True
    assert len(key["fixtures"]) == 10
    assert sum(item["expected_candidates"] > 0 for item in key["fixtures"]) == 4


def test_witness_floor_and_exact_positive():
    assert compile_clock_patterns(draining(7), Record({7: 9, 4: 7}), level=1) == []
    patterns = compile_clock_patterns(draining(8), Record({7: 8, 4: 8}), level=1)
    assert len(patterns) == 1
    assert {item["class_id"] for item in patterns[0]["tracked_classes"]} == {7}
    decreasing = patterns[0]
    assert decreasing["witness_steps"] == list(range(1, 9))
    assert decreasing["rate"]["recent"] == [-1] * 8
    assert decreasing["remaining_presses"] is None


def test_variable_rate_is_observed_not_hardcoded():
    patterns = compile_clock_patterns(
        draining(8, rates=[1, 2, 1, 2, 1, 2, 1, 2]),
        Record({7: 4, 4: 12}),
        level=1,
    )
    assert len(patterns) == 1
    decreasing = patterns[0]
    assert decreasing["rate"] == {
        "min": -2,
        "median": -1.5,
        "max": -1,
        "recent": [-1, -2, -1, -2, -1, -2, -1, -2],
        "unit": "visible cells per Duck action",
    }


def test_single_action_lever_and_direct_target_are_rejected():
    assert compile_clock_patterns(draining(8, same_action=True), Record({7: 8}), level=1) == []
    assert compile_clock_patterns(draining(8, targeted=True), Record({7: 8}), level=1) == []


def test_flat_or_reversal_reopens_claim():
    seq = draining(8)
    seq.append(transition(9, "UP", []))
    assert compile_clock_patterns(seq, Record({7: 8}), level=1) == []
    seq = draining(8)
    seq.append(transition(9, "UP", [Delta(0, 9, 4, 7)]))
    assert compile_clock_patterns(seq, Record({7: 9}), level=1) == []


def test_constant_count_moving_body_is_rejected():
    seq = [
        transition(
            step,
            "LEFT" if step % 2 else "RIGHT",
            [Delta(1, step, 6, 0), Delta(1, step + 1, 0, 6)],
        )
        for step in range(1, 9)
    ]
    assert compile_clock_patterns(seq, Record({6: 1}), level=1) == []
