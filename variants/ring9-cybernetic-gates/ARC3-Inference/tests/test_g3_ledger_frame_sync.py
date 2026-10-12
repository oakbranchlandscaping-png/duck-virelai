"""G3 reset continuity: G3's entity ledger sees the same board and life resets the agent observed.

Author: Claude (Alpha build seat), 2026-10-11. DIAGNOSTIC_G3_LEDGER_FRAME_SYNC_v1_2026-10-11 (option A, ruled by Sol):
G2 starts from the latest observed board, including a G1 reset. G3's ledger threads the resets since that seed, in
transition order, alongside G2's outcomes, each as a full before and after board rebuilt and verified from the
level-entry record. A broken record is reported, never silently resynchronised. A frame mismatch is never evidence.

F1-F5 are the diagnostic's fail-first plan (F5 is record-free); F6 pins "reject or report". G1-G2 are guards that
pass before and after: carry-v7 has no mismatch, and its no-choice golden stays byte-identical (test 0 in
``test_g3_directed_click``).
"""
from __future__ import annotations

import pickle

import pytest

from inference.framework.entity_observation import EntityLedger
from inference.framework.masked_world_state import grids_from_probe_outcome
from inference.framework.record_replay import decode_grid, load_record
from test_g3_directed_click import RECORDS, _replayed

MISMATCH = "before frame did not match the ledger's current frame"


def _record_board(name: str, through: int) -> tuple[tuple[int, ...], ...]:
    """The board after ``through``, rebuilt from the record alone (its initial board and every step's changes)."""
    record = load_record(RECORDS[name])
    grid = decode_grid(record["initial_grid"])
    for step in record["steps"]:
        if int(step["transition_id"]) > through:
            break
        for row, col, _before, after in step["changed"]:
            grid[row][col] = after
    return tuple(tuple(row) for row in grid)


def _board(grid) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(int(cell) for cell in row) for row in grid)


def _mismatched(ledger: EntityLedger) -> list[int]:
    return [item.transition_id for item in ledger.transitions if MISMATCH in item.limitations]


def test_f1_g2_starts_from_the_board_after_the_g1_reset():
    """k008 loses its first life during G1 (RESET at 31) and demonstrates once more (32) before G2 starts."""
    machine = pickle.loads(_replayed("k008", 32)).machine
    assert machine.gate_id == "G2-COUNTER" and machine.lives.life == 2
    assert machine.counter.initial_grid == _record_board("k008", 32)
    assert machine.counter.initial_grid != _record_board("k008", 30)  # the pre-reset board it used to start from


def test_f2_k008_g3_ledger_never_loses_the_frame():
    machine = pickle.loads(_replayed("k008", 60)).machine
    ledger = machine._adapters["G3-LEVERS"].entity_ledger
    assert ledger is not None and len(ledger.transitions) >= 28
    assert _mismatched(ledger) == []


def test_f3_k013_ledger_threads_the_six_g2_resets_and_keeps_g2s_entity_history():
    machine = pickle.loads(_replayed("k013", 400)).machine
    ledger = machine._adapters["G3-LEVERS"].entity_ledger
    assert _mismatched(ledger) == []
    resets = [row["transition_id"] for row in machine.transition_index if row.get("kind") == "RESET"]
    assert resets == [60, 113, 166, 219, 272, 325, 378]
    sighted = {sighting.transition_id for entity in ledger.entities.values() for sighting in entity.sightings}
    assert any(61 <= transition <= 377 for transition in sighted)  # G2's span is in the entity history again


def test_f4_k008_click_with_a_local_response_is_an_attributed_lever_witness(tmp_path):
    """The evidence result: a synthesized local response on E0004 is attributed to the clicked object."""
    from test_g3_hybrid_click_pass import HybridRun, _respond_on

    monkeypatch = pytest.MonkeyPatch()
    try:
        run = HybridRun(tmp_path, monkeypatch)  # k008 at G3's entry, the production agent and recorder
        run.agent._controller.g3_choice_handoff = False
        for _ in range(2):  # E0001 and E0002: the record's own clicks (counter-only responses)
            assert run.turn().step_executed
        target = run.machine.next_probe_capability()
        assert target["target"]["entity_id"] == "E0004"
        _respond_on(run, [tuple(cell) for cell in target["target"]["cells"]], run.transition + 1,
                    target["actions"][0])
        assert run.turn().step_executed
        attribution = run.rows("_gate_events.jsonl")[-1]["attribution"]
        assert attribution["attribution_basis"] == "PRE_ACTION_POINTER_OWNER" and attribution["contact_attributed"]
        assert attribution["disposition"] == "LOCAL_LEVER_WITNESS"
    finally:
        monkeypatch.undo()


# ---- F5 · record-free: the reconstruction rule and the ledger it feeds -----------------------------------

ENTRY = ((1, 1, 0), (0, 0, 0), (2, 0, 0))
ROWS = [  # a move, a reset back to the spawn board, the same move again
    {"transition_id": 1, "kind": "PROBE", "changed": [[0, 0, 1, 0], [0, 2, 0, 1]]},
    {"transition_id": 2, "kind": "RESET", "changed": [[0, 0, 0, 1], [0, 2, 1, 0]]},
    {"transition_id": 3, "kind": "PROBE", "changed": [[0, 0, 1, 0], [0, 2, 0, 1]]},
]
MOVED = ((0, 1, 1), (0, 0, 0), (2, 0, 0))


def test_f5_the_board_is_rebuilt_from_the_level_entry_record_and_each_reset_is_a_verified_full_frame():
    from inference.framework.level_board import board_through, reset_frames

    assert board_through(ENTRY, ROWS, entry=0, through=1) == MOVED
    assert board_through(ENTRY, ROWS, entry=0, through=2) == ENTRY
    assert board_through(ENTRY, ROWS, entry=0) == MOVED  # the latest observed board
    (reset,) = reset_frames(ENTRY, ROWS, entry=0, since=1)
    before, after = grids_from_probe_outcome(reset)
    assert reset["transition_id"] == 2 and (_board(before), _board(after)) == (MOVED, ENTRY)
    assert reset_frames(ENTRY, ROWS, entry=0, since=2) == []


def test_f5_a_ledger_that_threads_the_reset_observes_the_next_outcome_and_one_that_does_not_cannot():
    from inference.framework.level_board import reset_frames
    from inference.framework.record_replay import lossless_outcome

    after_move, first = lossless_outcome([list(row) for row in ENTRY], 1, {"action": "ACTION1"}, ROWS[0]["changed"])
    _board, third = lossless_outcome([list(row) for row in ENTRY], 3, {"action": "ACTION1"}, ROWS[2]["changed"])
    threaded, skipped = EntityLedger(ENTRY), EntityLedger(ENTRY)
    for ledger in (threaded, skipped):
        ledger.observe(first)
    threaded.observe_reset(reset_frames(ENTRY, ROWS, entry=0, since=1)[0])
    threaded.observe(third)
    skipped.observe(third)
    assert _mismatched(threaded) == [] and _mismatched(skipped) == [3]


# ---- F6 · a broken record is reported, never silently resynchronised ----------------------------------------

def test_f6_a_contradicted_or_duplicated_row_is_rejected_with_its_transition():
    from inference.framework.level_board import BrokenBoardRecord, board_through

    contradicted = [dict(ROWS[0]), {**ROWS[1], "changed": [[0, 0, 7, 1], [0, 2, 1, 0]]}, dict(ROWS[2])]
    with pytest.raises(BrokenBoardRecord, match="transition 2"):
        board_through(ENTRY, contradicted, entry=0)
    with pytest.raises(BrokenBoardRecord, match="transition 1"):
        board_through(ENTRY, [ROWS[0], ROWS[0]], entry=0)


def test_f6_a_broken_reset_row_is_reported_on_the_ledger_and_nothing_is_resynchronised():
    """k013 just before G3: corrupt the first G2 reset's record, then build G3's ledger."""
    machine = pickle.loads(_replayed("k013", 377)).machine
    row = next(item for item in machine.transition_index if item.get("transition_id") == 60)
    row["changed"][0][2] = (int(row["changed"][0][2]) + 1) % 10  # the recorded "before" no longer matches
    ledger = machine._adapters["G3-LEVERS"]._ensure_entity_ledger()
    assert any("transition 60" in item for item in ledger.limitations)
    assert len(_mismatched(ledger)) > 0  # the ledger stays out of step: no silent resync


# ---- G1 · guard ----------------------------------------------------------------------------------------------

def test_g1_carry_v7_has_no_reset_and_no_mismatch():
    machine = pickle.loads(_replayed("carry_v7", 20)).machine  # level 1, after the inventory
    ledger = machine._adapters["G3-LEVERS"].entity_ledger
    assert [row for row in machine.transition_index if row.get("kind") == "RESET"] == []
    assert len(ledger.transitions) >= 15 and _mismatched(ledger) == []


# ---- the evidence result on the unmodified records: no lever is certified without its own witness -----------

K013_LIVE_LEVERS = {"E0007", "E0008", "E0009", "E0010", "E0011", "E0012", "E0013", "E0014", "E0024"}
LEVER_STATES = {"RESPONDED", "WITNESSED", "G4-READY"}


@pytest.mark.parametrize(("name", "cut", "expected"), [("k008", 60, set()), ("k013", 400, K013_LIVE_LEVERS)])
def test_the_repair_certifies_no_lever_the_records_did_not_witness(name, cut, expected):
    """With the ledger in step, the unmodified records certify exactly the levers they certified before: none
    on k008, the live run's nine pointer witnesses on k013, each carrying its own witness evidence."""
    g3 = pickle.loads(_replayed(name, cut)).machine._adapters["G3-LEVERS"]
    levers = {entity_id for entity_id, item in g3.lifecycle_journal.entities.items() if item.state in LEVER_STATES}
    assert levers == expected
    assert all(g3.lifecycle_journal.entities[entity_id].witness_refs for entity_id in levers)


# ---- revision 2 · Sol's rulings on revision 1 ---------------------------------------------------------------

def test_a_gap_in_the_levels_transition_ids_is_a_missing_row_and_is_rejected():
    """Transition ids are the game's history length, so a level's executed transitions are contiguous."""
    from inference.framework.level_board import BrokenBoardRecord, board_through

    with pytest.raises(BrokenBoardRecord, match="transition 2 is missing") as caught:
        board_through(ENTRY, [ROWS[0], ROWS[2]], entry=0)
    assert caught.value.transition_id == 2


def _replay_with_broken_row(name: str, cut: int, transition: int):
    """Replay with one RESET row's recorded ``before`` corrupted the moment it is recorded."""
    from inference.framework.record_replay import replay
    from inference.framework.virelai_gates import CyberneticGateMachine

    original = CyberneticGateMachine.observe_system_reset

    def corrupting(self, outcome):
        result = original(self, outcome)
        row = next(item for item in self.transition_index if item.get("transition_id") == transition)
        if int(outcome.get("transition_id") or 0) == transition:
            row["changed"][0][2] = (int(row["changed"][0][2]) + 1) % 10
        return result

    CyberneticGateMachine.observe_system_reset = corrupting
    try:
        return replay(load_record(RECORDS[name]), max_steps=cut, measure=False).machine
    finally:
        CyberneticGateMachine.observe_system_reset = original


def _live_level(machine):
    from inference.framework.library_view import live_model

    model = live_model(machine)
    return model, next(level for level in model["levels"] if level["level"] == machine.lives.level)


def _board_gaps(level):
    """The typed break itself (its stage and transition), not the claims demoted because of it."""
    return [gap for gap in level["gaps"]
            if gap["reason"] == "RECORD_MISMATCH" and gap["source"] == "board_record_break" and "stage" in gap]


def test_a_broken_g2_seed_fails_closed_in_the_live_library():
    """k008: RESET 31's record is broken, so G2 can only start from G1's own (pre-reset) board. Nothing that
    rests on that board may read as certified, and Duck's library names the break."""
    from inference.framework.library_view import library_digest

    machine = _replay_with_broken_row("k008", 60, 31)
    assert machine.counter.seed_limitations and machine.counter.seed_limitations[0]["transition_id"] == 31
    model, level = _live_level(machine)
    breaks = {gap["stage"]: gap for gap in _board_gaps(level)}  # the seed, and G3's reset replay from the same row
    assert set(breaks) == {"G2_SEED", "G3_RESET_CONTINUITY"}
    assert all(gap["transitions"] == [31] and gap["subject"] == "LEVEL-1" for gap in breaks.values())
    gates = {row["gate_id"]: row["disposition"] for row in level["certified"]["gates"]}
    assert gates["G2-COUNTER"] == "RECORD_MISMATCH" and gates["G1-EGO"] == "CERTIFIED"
    assert {role["role"] for role in level["certified"]["roles"]} <= {"EGO"}
    assert level["certified"]["scoped_nulls"] == []
    assert level["accounting"]["status"] == "NOT_ACCOUNTED" and "BOARD_DISCONTINUITY" in level["accounting"]["missing"]
    digest = library_digest(model)
    assert digest["open_gaps"]["kinds"][0].startswith("RECORD_MISMATCH")
    assert not any(line.startswith("COUNTER") for line in digest["certified"])


def test_a_broken_reset_replay_fails_closed_for_g3_only():
    """k013: G2's seed (after 28) is sound; RESET 60's record is broken, so G3's ledger cannot thread it."""
    machine = _replay_with_broken_row("k013", 400, 60)
    assert machine.counter.seed_limitations == []
    _model, level = _live_level(machine)
    (gap,) = _board_gaps(level)
    assert gap["stage"] == "G3_RESET_CONTINUITY" and gap["transitions"] == [60]
    gates = {row["gate_id"]: row["disposition"] for row in level["certified"]["gates"]}
    assert gates["G3-LEVERS"] != "CERTIFIED" and gates["G2-COUNTER"] == "CERTIFIED"  # G3 is still in progress here
    roles = {role["role"] for role in level["certified"]["roles"]}
    assert roles == {"EGO"} and level["certified"]["scoped_nulls"] == []  # k013's G2 product carries no mask law
    demoted = {gap["subject"] for gap in level["gaps"] if gap["reason"] == "RECORD_MISMATCH"
               and gap["archetype_question"] == "Is the LEVER claim grounded?"}
    assert demoted == K013_LIVE_LEVERS


def test_a_sound_record_reports_no_board_break_and_keeps_its_certified_roles():
    machine = pickle.loads(_replayed("k013", 400)).machine
    _model, level = _live_level(machine)
    assert _board_gaps(level) == []
    assert {role["entity_id"] for role in level["certified"]["roles"] if role["role"] == "LEVER"} == K013_LIVE_LEVERS


def test_untouched_departed_objects_leave_the_actionable_agenda_but_not_the_evidence_history():
    """Sol's ruling 3, the excluded side: k013's G2-era objects stay in the ledger and the lifecycle."""
    from inference.framework.library_agenda import gate_agenda, lever_question_id

    machine = pickle.loads(_replayed("k013", 400)).machine
    g3 = machine._adapters["G3-LEVERS"]
    departed = {entity_id for entity_id, item in g3.lifecycle_journal.entities.items()
                if g3.entity_ledger.entities[entity_id].status == "ABSENT" and item.state == "UNTOUCHED"
                and not item.witness_refs and not item.events}
    assert len(departed) == 480 and departed <= set(g3.entity_ledger.entities)  # the history keeps them
    agenda = gate_agenda(machine)
    asked = {question["id"] for question in agenda["questions"]}
    assert not asked & {lever_question_id(1, entity_id) for entity_id in departed}
    assert agenda["departed_untouched"] == 480


def test_departed_objects_with_g3_work_or_a_witness_stay_on_the_agenda():
    """Sol's ruling 3, the kept side: departed rows G3 worked on (k013's five ambiguous rows) stay, and so would
    a departed row holding a witness (one is given a witness ref for the test)."""
    from inference.framework.library_agenda import gate_agenda, lever_question_id

    machine = pickle.loads(_replayed("k013", 400)).machine
    g3 = machine._adapters["G3-LEVERS"]
    worked = {entity_id for entity_id, item in g3.lifecycle_journal.entities.items()
              if g3.entity_ledger.entities[entity_id].status == "ABSENT" and item.events}
    assert worked == {"E0015", "E0018", "E0020", "E0021", "E0023"}
    witnessed = next(entity_id for entity_id, item in sorted(g3.lifecycle_journal.entities.items())
                     if g3.entity_ledger.entities[entity_id].status == "ABSENT" and item.state == "UNTOUCHED")
    g3.lifecycle_journal.entities[witnessed].witness_refs.append("E-test-witness")
    questions = {question["id"]: question for question in gate_agenda(machine)["questions"]}
    assert all(lever_question_id(1, entity_id) in questions for entity_id in worked)
    assert questions[lever_question_id(1, witnessed)]["disposition"] == "ANSWERED_LEVER"
