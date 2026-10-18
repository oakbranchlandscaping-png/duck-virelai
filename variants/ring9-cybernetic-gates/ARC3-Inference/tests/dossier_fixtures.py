"""WO-G4-DOSSIER-A test states, built only from committed record fixtures and the existing replay.

Author: Claude (Alpha build seat), 2026-10-16. Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2`` §9.

Every state is a real gate machine: the ft09 memory-v1 record replayed to a chosen transition (the record's own
answers are submitted the way ``record_replay`` submits them), the vc33 carry-v7 record (two levels), or the offline
ft09 world after G4-A (``test_g4b_relations.start_g4b``). Nothing here edits a gate; a boundary is delivered through
``record_outcome`` exactly as a live frame would deliver it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from inference.framework.record_replay import (
    _answer_due, _answer_index, decode_grid, load_record, lossless_outcome, merge_recorded_answer, record_like_live,
    replay,
)

FIXTURES = Path(__file__).parent / "fixtures"
FT09_V1 = FIXTURES / "ft09_kaggle_memory_v1_record.json.gz"
CARRY_V7 = FIXTURES / "vc33_kaggle_carry_v7_record.json.gz"
GAME_OVER = {"game_over": True, "level_before": 1, "level_after": 1, "state": "GAME_OVER"}
LEVEL_UP = {"level_completed": True, "level_before": 1, "level_after": 2, "state": "NOT_FINISHED"}
G3, G41, G4A = "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS"
FT09_LEVERS = ("E0053", "E0054", "E0055", "E0056", "E0057", "E0060", "E0061", "E0062")


def _steps_through(record: dict, transition_id: int) -> int:
    return next(index + 1 for index, step in enumerate(record["steps"]) if step["transition_id"] == transition_id)


def ft09_through(transition_id: int) -> Any:
    """The ft09 v1 record replayed through ``transition_id`` (answers due after it are not yet submitted)."""
    record = load_record(FT09_V1)
    return replay(record, max_steps=_steps_through(record, transition_id), measure=False)


def ft09_anatomy(answered: int) -> Any:
    """G4.1 open on the eight ft09 levers with the record's first ``answered`` anatomy answers accepted."""
    record = load_record(FT09_V1)
    result = replay(record, max_steps=_steps_through(record, 75), measure=False)
    machine = result.machine
    pending = {G3: [record["answers"][9]], G41: list(record["answers"][10:10 + answered])}
    machine.next_probe_capability()  # a completed roster asks for its answer only when probed
    while _answer_due(machine) and pending.get(machine.gate_id):
        queue = pending[machine.gate_id]
        template = machine.gate_view().get("answer_template") or {}
        machine.submit_answer(merge_recorded_answer(template, queue.pop(_answer_index(queue, template))))
    assert len(machine._adapters[G41]._answers) == answered and (answered == 8 or machine.gate_id == G41)
    return result


def answer_next_anatomy(machine: Any) -> Any:
    """Accept the record's next anatomy answer on the open G4.1 gate (no action, no transition)."""
    record = load_record(FT09_V1)
    done = len(machine._adapters[G41]._answers)
    template = machine.gate_view().get("answer_template") or {}
    return machine.submit_answer(merge_recorded_answer(template, record["answers"][10 + done]))


def deliver(result: Any, boundary: dict, *, transition_id: int | None = None) -> dict:
    """The record's next action at the current G4-A capability, delivered with ``boundary`` (a death or a level)."""
    record = load_record(FT09_V1)
    machine = result.machine
    last = max(int(row["transition_id"]) for row in machine.transition_index)
    step = next(item for item in record["steps"] if item["transition_id"] == last + 1)
    capability = machine.next_probe_capability()
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [step["action"]])
    result.grid, outcome = lossless_outcome(result.grid, transition_id or step["transition_id"], step["action"],
                                           step["changed"], boundary, probe_id=probe.probe_id)
    record_like_live(machine, probe, outcome, record.get("valid_actions") or ["ACTION6"])
    return outcome


def carry_v7() -> Any:
    return replay(load_record(CARRY_V7), measure=False)


def compiled(machine: Any, *, persist_reason: str = "RUN_END", reconcile: bool = False,
             rename: dict[int, str] | None = None) -> dict:
    """The sealed model of a gate machine at H2 (``reconcile``) or as an unreconciled write, as the solver builds it."""
    from inference.framework.library_census import ExecutionRecord, compile_world_model
    from inference.framework.world_model_v2 import seal

    board = tuple(tuple(int(cell) for cell in row) for row in machine.ego._initial_grid)
    rows = sorted(machine.transition_index, key=lambda row: int(row["transition_id"]))
    executed = [str((row.get("action") or {}).get("action") or "") for row in rows]
    for transition_id, name in (rename or {}).items():
        executed[int(transition_id) - 1] = name
    return seal(compile_world_model(
        machine, ExecutionRecord(board, int(machine.lives.level), tuple(a.action for a in machine.ego.affordances),
                                 tuple(executed)), game_id="g", run_stem="g_p0", persist_reason=persist_reason,
        frozen_levels=list(getattr(machine, "level_censuses", ()) or ()), reconcile_journal=reconcile))


def open_level(model: dict) -> dict:
    return next(level for level in model["levels"] if level["state"] == "OPEN")


def chapter(model_or_level: dict, entity_id: str, name: str) -> dict:
    level = open_level(model_or_level) if "levels" in model_or_level else model_or_level
    return level["lever_dossiers"][entity_id]["chapters"][name]


__all__ = ["CARRY_V7", "FT09_LEVERS", "FT09_V1", "GAME_OVER", "answer_next_anatomy", "LEVEL_UP", "carry_v7", "chapter", "compiled", "decode_grid",
           "deliver", "ft09_anatomy", "ft09_through", "open_level"]
