"""S-1: games can share one process. Concurrent replays equal serial replays, byte for byte.

Author: Claude (Alpha build seat), 2026-10-06. BUILD_PLAN_PORTS_AND_PILLARS_v1 §1 S-1; submission mode.

A submission plays many games as threads of one process (``HarnessSolver.concurrency``, a
``ThreadPoolExecutor``). DIAG_R5 §3 audited the package statically and found no cross-game state.
This is the runtime proof: the recorded live worlds are replayed once one after another, then all at
once on a thread pool with their order interleaved, and every game's machine state must be
identical. The worlds cover both actuators: CLICK (ft09, vc33) and NAV (ls20, the N5.1 live record
replayed from G0), so the NAV G3 state (entities, scheduler, terrain, reachability, contacts) is
compared as well as the click products (amended 2026-10-06 after Sol's report §4.4).

The second test shows the check can see a leak: a deliberately shared cache, injected only here,
makes one game decode another game's board (it changes the vc33 and the ls20 digests).
"""
from __future__ import annotations

import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from inference.framework import record_replay
from inference.framework.record_replay import load_record, replay
from inference.framework.virelai_gates import LEVER_GATE_ID, GateContractError

FIXTURES = Path(__file__).parent / "fixtures"
RECORDS = (  # the live records: two worlds, several runs each; each replays in 5-15 s
    "ft09_kaggle_v2_record.json.gz",
    "ft09_kaggle_memory_v1_record.json.gz",
    "vc33_kaggle_exit_v1_record.json.gz",
    "vc33_kaggle_carry_v6_record.json.gz",
    "ft09_kaggle_exit_v1_record.json.gz",
    "ls20_kaggle_n5_1_record.json.gz",  # NAV: replay() starts it at G0 (protocol.replay_from_g0)
)  # v7 is left out: its level 1 is v6's, action for action, so its replayed state is the same


def _digest(name: str) -> str:
    """Everything a game's machine certified, as one hash: rows, products, gate, G3 state, lives, levels.

    A replay that raises is a result too (a leak can crash a game instead of changing it).
    """
    try:
        result = replay(load_record(FIXTURES / name), measure=False)
    except Exception as exc:  # noqa: BLE001 - the comparison, not the test, judges a crash
        return f"RAISED {type(exc).__name__}"
    machine = result.machine
    state = {
        "steps": result.steps_replayed,
        "answers": result.answers_used,
        "stopped": result.stopped,
        "gate": machine.gate_id,
        "transitions": machine.transition_index,
        "products": machine.target_journal.snapshot(),
        "g3": _g3_state(machine),  # NAV: entities, scheduler, terrain, reachability, contacts
        "lives": machine.lives.summary(),
        "levels": machine.levels,
    }
    return hashlib.sha256(json.dumps(state, sort_keys=True, default=str).encode()).hexdigest()


def _g3_state(machine) -> object:
    """The current level's G3 adapter state; a level whose G2 has not closed has no G3 yet."""
    g3 = machine._adapters.get(LEVER_GATE_ID)
    if g3 is None:
        return None
    try:
        return g3.snapshot()
    except GateContractError as exc:  # G3 not open on this level: that is the state
        return f"UNOPENED {exc}"


@pytest.fixture(scope="module")
def serial() -> dict[str, str]:
    return {name: _digest(name) for name in RECORDS}


def _concurrent() -> dict[str, str]:
    order = list(RECORDS[::2]) + list(RECORDS[1::2])  # interleaved: neighbours are different worlds
    with ThreadPoolExecutor(max_workers=len(order), thread_name_prefix="s1-game") as pool:
        digests = list(pool.map(_digest, order))
    return dict(zip(order, digests))


def test_s1_concurrent_replays_equal_serial_replays_game_for_game(serial):
    assert len(set(serial.values())) == len(RECORDS)  # the games really are different
    assert not any(value.startswith("RAISED") for value in serial.values())
    assert _concurrent() == serial


def test_s1_the_check_sees_a_shared_cache_leaking_between_games(monkeypatch, serial):
    """Fail-first: one module-level cache shared by every game must make the check fail."""
    original = record_replay.decode_grid
    shared: dict[int, list[list[int]]] = {}

    def leaky_decode_grid(rows):
        key = len(rows)  # every board is 64 rows: the first game to decode wins for all
        if key not in shared:
            shared[key] = original(rows)
        return [list(row) for row in shared[key]]

    monkeypatch.setattr(record_replay, "decode_grid", leaky_decode_grid)
    leaked = _concurrent()
    assert leaked != serial
    assert sum(leaked[name] != serial[name] for name in RECORDS) >= 2  # games took another's board
