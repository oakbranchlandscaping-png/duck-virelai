"""The replay checkpoint layer's safety contract (WO-1, test-runtime infrastructure; hazards 1-6 and 8).

Author: Claude (Alpha build seat), 2026-10-13. A shared cache is only an optimization if no test can tell it is
there: each consumer gets its own state, keys separate everything that changes the machine, a failed build
leaves nothing behind, a patched production path never reads or seeds the cache, and the no-choice golden still
replays and traces the whole record itself.
"""
from __future__ import annotations

import gzip
import json
import shutil
from pathlib import Path

import pytest

import replay_checkpoints
from replay_checkpoints import checkpoint, checkpoint_bytes, checkpoint_stats

FIXTURES = Path(__file__).parent / "fixtures"
CARRY = FIXTURES / "vc33_kaggle_carry_v7_record.json.gz"
K008 = FIXTURES / "ring9_v2_k008_g3_lifecycle_record.json.gz"


def _fingerprint(result) -> tuple:
    machine = result.machine
    return (result.steps_replayed, machine.observed_through_step, machine.gate_id, len(machine.transition_index),
            tuple(map(tuple, result.grid)))


# ---- 1, 2 · isolation ---------------------------------------------------------------------------------------

def test_1_two_consumers_of_one_checkpoint_receive_independent_machines():
    first, second = checkpoint(CARRY, max_steps=5), checkpoint(CARRY, max_steps=5)
    assert first is not second and first.machine is not second.machine
    assert first.machine.transition_index is not second.machine.transition_index
    assert first.grid is not second.grid and _fingerprint(first) == _fingerprint(second)


def test_2_mutating_one_copy_never_reaches_the_next_consumer():
    reference = _fingerprint(checkpoint(CARRY, max_steps=5))
    mutated = checkpoint(CARRY, max_steps=5)
    mutated.machine.transition_index.clear()
    mutated.machine.lives.life += 7
    mutated.grid[0][0] = (mutated.grid[0][0] + 1) % 10
    mutated.steps_replayed = -1
    fresh = checkpoint(CARRY, max_steps=5)
    assert _fingerprint(fresh) == reference and fresh.machine.lives.life != mutated.machine.lives.life


# ---- 3, 4, 5 · keys --------------------------------------------------------------------------------------------

def test_3_different_cuts_never_collide():
    three, five = checkpoint(CARRY, max_steps=3), checkpoint(CARRY, max_steps=5)
    assert three.steps_replayed == 3 and five.steps_replayed == 5
    assert checkpoint(CARRY, max_steps=3).steps_replayed == 3  # a hit still names its own cut


def _write_record(path: Path, record: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt") as handle:
        json.dump(record, handle)
    return path


def test_4_records_with_the_same_name_but_different_contents_never_collide(tmp_path):
    from inference.framework.record_replay import load_record

    record = load_record(CARRY)  # its first answer is due after two steps
    one = _write_record(tmp_path / "a" / "record.json.gz", dict(record, steps=record["steps"][:2]))
    two = _write_record(tmp_path / "b" / "record.json.gz", dict(record, steps=record["steps"][:1]))
    assert checkpoint(one).steps_replayed == 2 and checkpoint(two).steps_replayed == 1
    _write_record(one, dict(record, steps=record["steps"][:1]))  # the same path, new contents
    assert checkpoint(one).steps_replayed == 1


def test_5_replay_options_are_part_of_the_key():
    measured = checkpoint(CARRY, max_steps=5, measure=True)
    unmeasured = checkpoint(CARRY, max_steps=5, measure=False)
    assert measured.measure is True and unmeasured.measure is False
    assert measured.samples and not unmeasured.samples
    assert checkpoint(CARRY, max_steps=5, measure=True).samples == measured.samples


# ---- 6 · failure --------------------------------------------------------------------------------------------

def test_6_a_failed_build_is_not_cached(monkeypatch, tmp_path):
    record = tmp_path / "carry.json.gz"  # a key no other test can have built, whatever the order
    shutil.copy(CARRY, record)
    real = replay_checkpoints._build
    calls = []

    def failing_once(*args):
        calls.append(args)
        if len(calls) == 1:
            raise RuntimeError("replay failed half-way")
        return real(*args)

    monkeypatch.setattr(replay_checkpoints, "_build", failing_once)
    before = checkpoint_stats()
    with pytest.raises(RuntimeError, match="half-way"):
        checkpoint(record, max_steps=7)
    assert checkpoint_stats()["entries"] == before["entries"]
    assert checkpoint(record, max_steps=7).steps_replayed == 7 and len(calls) == 2  # rebuilt, not served


# ---- the patch guard: a monkeypatched production path never reads or seeds the cache ------------------------

def test_a_patched_replay_bypasses_the_cache_in_both_directions(monkeypatch):
    """The reset-continuity tests replay under a deliberately corrupting ``observe_system_reset``."""
    from inference.framework.virelai_gates import CyberneticGateMachine

    clean = checkpoint(K008, max_steps=32)
    original = CyberneticGateMachine.observe_system_reset

    def corrupting(self, outcome):
        result = original(self, outcome)
        self.lives.life += 100  # a visible mark of the patched path
        return result

    monkeypatch.setattr(CyberneticGateMachine, "observe_system_reset", corrupting)
    assert replay_checkpoints.production_patched()
    patched = checkpoint(K008, max_steps=32)
    assert patched.machine.lives.life == clean.machine.lives.life + 100  # built by the patched code, not served
    monkeypatch.undo()
    assert not replay_checkpoints.production_patched()
    assert checkpoint(K008, max_steps=32).machine.lives.life == clean.machine.lives.life  # nor did it seed the cache


# ---- 8 · the no-choice golden replays and traces the whole record itself -----------------------------------

def test_8_the_no_choice_golden_compares_its_own_full_traced_replay(monkeypatch):
    from g3_no_choice_trace import GOLDEN, RECORDS, no_choice_trace

    def forbidden(*_args, **_kwargs):
        raise AssertionError("the no-choice golden must not read a cached checkpoint")

    monkeypatch.setattr(replay_checkpoints, "checkpoint_bytes", forbidden)
    monkeypatch.setattr(replay_checkpoints, "checkpoint", forbidden)
    golden = json.loads(GOLDEN.read_text())["carry_v7"]
    trace = no_choice_trace(RECORDS["carry_v7"])
    assert trace == golden and trace["events"] and trace["steps_replayed"] == golden["steps_replayed"]


def test_checkpoint_bytes_are_immutable_and_equal_for_one_key():
    blob = checkpoint_bytes(CARRY, max_steps=5)
    assert isinstance(blob, bytes) and checkpoint_bytes(CARRY, max_steps=5) is blob


def test_the_layer_has_no_disk_cache(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    shutil.copy(CARRY, tmp_path / "carry.json.gz")
    checkpoint(tmp_path / "carry.json.gz", max_steps=2)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["carry.json.gz"]
