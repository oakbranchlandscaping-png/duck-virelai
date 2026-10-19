"""WO-G4-DOSSIER-B3: bounded experiments for the lever mechanics the record leaves owed.

Author: Claude (Alpha build seat), 2026-10-18. Interface: ``INTERFACE_WO_G4_DOSSIER_B3_v1``. Written before the
production edits (fail-first on ``ef8289d``).

The real states, all from committed records:

* **the opening** — the ft09 memory-v1 record replayed to G4-A's close, on the offline world it defines
  (``test_g4b_relations.start_g4b``): G4-B open in life 2, where E0053, E0054 and E0055 have no self-press;
* **the owed state** (B1's acceptance case) — the opening after Duck's eight frozen predictions, one press each:
  E0053, E0054 and E0055 each have exactly one self-press in life 2 and owe reversal (``test_b1_10``).

Test doubles, labelled where used: a death or a level change delivered on an experiment's own press (B2's
technique, ``test_b2_05``); the harness reset after a death, returning the board to the record's level start; a
cap lowered to one press; a world where one lever cycles through three contents, or where one lever's press also
moves another's region; a lever taken off the board; execution evidence removed or duplicated.
"""
from __future__ import annotations

import json
import pickle

import pytest

import dossier_fixtures as fx
from ft09_world import V1_RECORD, Ft09World
from inference.framework.controller_executor import next_owned_step
from inference.framework.virelai_gates import GateContractError
from test_g4b_relations import TILES, _predict, _take, start_g4b

RELATIONS, LAW = "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"
OWED = ("E0053", "E0054", "E0055")
EXP = "G4-B-LEVER-RELATIONS:EXP:"
_CACHE: dict[str, bytes] = {}


def _qid(entity: str) -> str:
    return f"Q:L1:LIBRARY:{entity}:LIMITS"


def _cached(key: str, build):
    if key not in _CACHE:
        _CACHE[key] = pickle.dumps(build())
    return pickle.loads(_CACHE[key])


def _opening():
    """(machine, world): G4-B just opened in life 2; the last G4-A explanation was Duck's turn."""
    return _cached("opening", start_g4b)


def _owed_state():
    """(machine, world): Duck's eight predictions taken (``test_g4c_law._described`` before its description)."""
    def build():
        machine, world = start_g4b()
        for entity in TILES:
            _predict(machine, entity, {entity: "STEPS", "E0054": "STEPS" if entity == "E0054" else "UNCHANGED"})
            _take(machine, world)
        return machine, world
    return _cached("owed", build)


def _act(machine, world, step, boundary=None):
    """Execute the controller's step on the world; ``boundary`` (a labelled double) ends the life or the level."""
    from inference.framework.record_replay import lossless_outcome, record_like_live

    probe = machine.validate_probe({"probe_token": step.probe_token, **(step.decision or {})}, [step.action])
    if boundary is None:
        outcome = world.step(step.action)
    else:
        world.transition_id += 1
        world.grid, outcome = lossless_outcome(world.grid, world.transition_id, step.action,
                                               world.changes(step.action), boundary)
    record_like_live(machine, probe, outcome, world.valid_actions)
    return probe, machine.transition_index[-1]


def _controller(machine, world, limit: int = 40) -> list:
    """The controller alone, no Duck turn: every owned step until the gate leaves G4-B or another owner is due."""
    taken = []
    for _ in range(limit):
        if machine.gate_id != RELATIONS:
            return taken
        step = next_owned_step(machine)
        if step.owner != "CONTROLLER":
            taken.append((step, None))
            return taken
        if step.kind == "ANSWER":
            machine.submit_answer(json.loads(json.dumps(step.answer)))
            taken.append((step, None))
        else:
            taken.append((step, _act(machine, world, step)[1]))
    raise AssertionError("the controller never left G4-B")


def _reset(machine, world) -> int:
    """Labelled double: the harness reset after a death returns the board to the record's level start."""
    from inference.framework.record_replay import decode_grid, load_record, lossless_outcome

    start = decode_grid(load_record(V1_RECORD)["initial_grid"])
    changed = [[r, c, world.grid[r][c], start[r][c]] for r in range(len(start)) for c in range(len(start[r]))
               if world.grid[r][c] != start[r][c]]
    world.transition_id += 1
    world.grid, outcome = lossless_outcome(world.grid, world.transition_id, {"action": "RESET"}, changed,
                                           {"state": "NOT_FINISHED", "actor": "SYSTEM_RESET", "reset": True})
    machine.observe_system_reset(outcome)
    return world.transition_id


def _died():
    """(machine, world, death, reset): E0053's first experiment press ends life 2 (double), then the harness resets."""
    def build():
        machine, world = start_g4b()
        step = next_owned_step(machine)
        _probe, row = _act(machine, world, step, fx.GAME_OVER)
        reset = _reset(machine, world)
        return machine, world, row["transition_id"], reset
    return _cached("died", build)


def _events(machine) -> list[tuple]:
    return [(e["event"], e["entity_id"], e["actor"], e["reason"].split(":")[0]) for e in machine.g4_selection_events]


def _dossiers(machine) -> dict:
    return fx.open_level(fx.compiled(machine, persist_reason="BUDGET_STOP"))["lever_dossiers"]


def _click(entity: str) -> dict:
    row, col = TILES[entity]
    return {"action": "ACTION6", "row": row, "col": col}


# ---- 1 · the owed set, on ef8289d (a guard) ---------------------------------------------------------------------

def test_b3_01_ft09_life_2_reversal_stays_owed_on_the_base_record():
    """Guard (passes on ef8289d): the record alone leaves E0053-E0055's reversal owed in life 2 — untested at G4-B's
    opening, tested once without a return after Duck's predictions — and nothing else in limits owed."""
    for state, tested in ((_opening, 0), (_owed_state, 1)):
        machine, _world = state()
        for entity, dossier in _dossiers(machine).items():
            observations, items = dossier["observations"], dossier["chapters"]["open_items"]["facts"]["probe_owed"]
            assert observations["scope"]["life"] == 2
            if entity in OWED:
                assert observations["reversal"]["toggle_reversal"]["tested"] == tested
                assert not observations["reversal"]["toggle_reversal"]["cases"] and "LIMITS_REVERSAL" in items
            else:
                assert "LIMITS_REVERSAL" not in items
            assert "LIMITS_PERSISTENCE" not in items


# ---- 2-4 · selection: Duck's choice, decline, timeout ------------------------------------------------------------

def test_b3_02_a_chosen_owed_lever_binds_one_experiment_and_one_question_everywhere(tmp_path):
    from inference.framework import lever_dossier_selection as sel
    from inference.framework import lever_experiments as X
    from inference.framework.library_agenda import gate_agenda, selected_target
    from test_g3_directed_click import _surfaces

    machine, world = _owed_state()
    assert [(row["entity_id"], row["open_item"]) for row in X.plan(machine)] == [
        (entity, "LIMITS_REVERSAL") for entity in OWED]
    chosen = _qid("E0054")
    assert chosen in gate_agenda(machine)["eligible"]
    transitions = len(machine.transition_index)
    selection = machine.select_question(chosen, actor="DUCK")
    assert (selection["entity_id"], selection["kind"], selection["cap"]) == ("E0054", "SELF_REVERSAL", 8)
    assert len(machine.transition_index) == transitions  # choosing consumes no action
    card, digest, capability = _surfaces(tmp_path, machine)
    assert card["question_id"] == digest["goal"]["question_id"] == capability["question_id"] == chosen
    assert selected_target(machine)["question_id"] == chosen
    assert capability["target"]["question_id"] == chosen and capability["target"]["selected_by"] == "DUCK"
    assert card["subject"]["experiments"]["under_way"]["question_id"] == chosen  # the card Duck reads
    step = next_owned_step(machine)
    assert (step.owner, step.action) == ("CONTROLLER", _click("E0054")) and chosen in step.reason
    probe, row = _act(machine, world, step)
    name = selection["experiment_id"]
    assert probe.probe_id == row["probe_id"] == f"{name}:1" and name == f"{EXP}REVERSAL:E0054:L1P2:R1"
    receipt = machine._adapters[RELATIONS]._events[-1]
    assert receipt["question_id"] == chosen and receipt["evidence_id"] == row["evidence_id"]
    assert receipt["experiment"]["entity_id"] == "E0054" and receipt["experiment"]["terminal"] == "REVERSAL_OBSERVED"
    assert sel.dossier_question(1, "E0054", "limits") == chosen
    assert _events(machine) == [("ADMITTED", "E0054", "DUCK", "LIMITS_REVERSAL owed"),
                                ("FINISHED", "E0054", "DUCK", "REVERSAL_OBSERVED")]
    cases = _dossiers(machine)["E0054"]["observations"]["reversal"]["toggle_reversal"]["cases"]
    assert [case["evidence_ref"] for case in cases] == [row["evidence_id"]]


def test_b3_03_a_declined_turn_leaves_the_controller_to_run_the_head_of_coverage():
    machine, world = _owed_state()
    step = next_owned_step(machine)  # Duck declined: no choice was made on its turn
    assert (step.owner, step.kind, step.action) == ("CONTROLLER", "ACTION", _click("E0053"))
    assert _qid("E0053") in step.reason and "Duck's choice" not in step.reason
    probe, _row = _act(machine, world, step)
    assert probe.probe_id == f"{EXP}REVERSAL:E0053:L1P2:R1:1"
    assert _events(machine)[0] == ("ADMITTED", "E0053", "CONTROLLER", "LIMITS_REVERSAL owed")


def test_b3_04_a_timeout_costs_only_the_turn_duck_held_and_the_controller_resumes():
    """The last G4-A explanation opened G4-B on Duck's turn; Duck timed out (no call). Every later G4-B step is the
    controller's, the same as the no-choice run's, and none charges Duck's per-level G4-B budget."""
    machine, world = _opening()
    budget = machine.duck_budget.snapshot()
    taken = _controller(machine, world)
    assert all(step.owner == "CONTROLLER" for step, _row in taken) and machine.gate_id == LAW
    acted = [step.action for step, row in taken if row is not None]
    assert acted == [_click(entity) for entity in OWED for _ in (1, 2)]  # two presses each: S0 -> S1 -> S0
    assert taken[-1][0].kind == "ANSWER" and "record certifies" in taken[-1][0].reason
    assert machine.duck_budget.snapshot() == budget
    again, world2 = _opening()
    first = next_owned_step(again)
    assert (first.reason, _act(again, world2, first)[0].probe_id) == (taken[0][0].reason, taken[0][1]["probe_id"])


# ---- 5-7 · self-reversal: a return, a longer recurrence, the cap -------------------------------------------------

def test_b3_05_a_self_press_that_returns_records_the_observed_reversal_for_this_level_and_life_only():
    """B1's acceptance case: E0053 pressed once in life 2; one more press returns it, and the dossier cites only
    that receipt, of this level and life."""
    machine, world = _owed_state()
    step = next_owned_step(machine)
    _probe, row = _act(machine, world, step)
    assert _events(machine)[-1] == ("FINISHED", "E0053", "CONTROLLER", "REVERSAL_OBSERVED")
    dossier = _dossiers(machine)["E0053"]
    observations, limits = dossier["observations"], dossier["chapters"]["limits"]
    toggle = observations["reversal"]["toggle_reversal"]
    assert toggle["status"] == "OBSERVED" and [c["evidence_ref"] for c in toggle["cases"]] == [row["evidence_id"]]
    assert toggle["cases"][0]["transition_id"] == row["transition_id"] and toggle["cases"][0]["cycle_length"] == 2
    assert (observations["scope"]["level"], observations["scope"]["life"]) == (1, 2)
    lives = {r["transition_id"]: r["life"] for r in machine.transition_index}
    from inference.framework import lever_dossier_state as S

    assert {lives[t] for t in S.cited_transitions(observations)} == {2}
    assert limits["facts"]["reversal"] == "OBSERVED"
    assert "LIMITS_REVERSAL" not in dossier["chapters"]["open_items"]["facts"]["probe_owed"]
    assert all("LIMITS_REVERSAL" in _dossiers(machine)[e]["chapters"]["open_items"]["facts"]["probe_owed"]
               for e in ("E0054", "E0055"))


class _Cycling(Ft09World):
    """Labelled double: E0053's tile cycles through three contents instead of toggling between two."""

    THIRD = 15

    def changes(self, action):
        changed = super().changes(action)
        box = self._tile_at(int(action["row"]), int(action["col"]))
        if box is None or (action["row"], action["col"]) != TILES["E0053"]:
            return changed
        low, high = self.tiles[box]
        before = self.grid[box[0]][box[1]]
        after = {low: high, high: self.THIRD, self.THIRD: low}[before]
        return [[r, c, b, after] if (r, c) in self._cells(box) else [r, c, b, a] for r, c, b, a in changed]

    @staticmethod
    def _cells(box):
        return {(r, c) for r in range(box[0], box[2] + 1) for c in range(box[1], box[3] + 1)}


def _with_world(world, cls):
    """The same board and clock, continued under a labelled double's law."""
    from inference.framework.record_replay import load_record

    double = cls(load_record(V1_RECORD))
    double.grid, double.transition_id = [row[:] for row in world.grid], world.transition_id
    return double


def test_b3_06_a_longer_recurrence_is_recurrence_not_a_two_state_reversal():
    machine, world = _opening()
    world = _with_world(world, _Cycling)
    taken = []
    while not machine.g4_selection_events or machine.g4_selection_events[-1]["event"] == "ADMITTED":
        step = next_owned_step(machine)
        taken.append(_act(machine, world, step)[1])
    assert len(taken) == 3 and _events(machine)[-1] == ("FINISHED", "E0053", "CONTROLLER", "RECURRENCE_OBSERVED")
    observations = _dossiers(machine)["E0053"]["observations"]
    recurrence, toggle = observations["reversal"]["self_recurrence"], observations["reversal"]["toggle_reversal"]
    assert recurrence["status"] == "OBSERVED" and recurrence["cases"][0]["cycle_length"] == 3
    assert recurrence["cases"][0]["evidence_ref"] == taken[-1]["evidence_id"] and toggle["status"] == "NOT_OBSERVED"
    limits = _dossiers(machine)["E0053"]["chapters"]["limits"]
    assert limits["facts"]["reversal"] == "PROBE_OWED"  # recurrence is not reversal: still owed, not re-admitted
    from inference.framework import lever_experiments as X

    assert "E0053" not in {row["entity_id"] for row in X.plan(machine)}


def test_b3_07_reaching_the_cap_leaves_reversal_unresolved(monkeypatch):
    from inference.framework import lever_experiments as X

    monkeypatch.setitem(X.KINDS, "LIMITS_REVERSAL", ("SELF_REVERSAL", "REVERSAL", 1))  # labelled double: cap 1
    machine, world = _opening()
    _probe, row = _act(machine, world, next_owned_step(machine))
    assert _events(machine)[-1] == ("FINISHED", "E0053", "CONTROLLER", "CAPPED")
    observations = _dossiers(machine)["E0053"]["observations"]
    toggle = observations["reversal"]["toggle_reversal"]
    assert (toggle["status"], toggle["tested"], toggle["cases"]) == ("NOT_OBSERVED", 1, [])
    assert _dossiers(machine)["E0053"]["chapters"]["limits"]["facts"]["reversal"] == "PROBE_OWED"
    assert [row["entity_id"] for row in X.plan(machine)][:1] == ["E0054"]  # the capped one is not re-admitted


# ---- 8-10 · boundaries: death, level change, reset ---------------------------------------------------------------

def test_b3_08_a_death_closes_the_experiment_and_no_evidence_crosses_into_the_next_life():
    machine, _world, death, reset = _died()
    assert _events(machine) == [("ADMITTED", "E0053", "CONTROLLER", "LIMITS_REVERSAL owed"),
                                ("STALE", "E0053", "CONTROLLER", "INTERRUPTED_DEATH")]
    stale = machine.g4_selection_events[-1]
    assert (stale["level"], stale["life"], stale["at_transition"]) == (1, 2, death)
    from inference.framework import lever_dossier_state as S
    from inference.framework import lever_experiments as X

    for dossier in _dossiers(machine).values():
        observations = dossier["observations"]
        assert observations["scope"]["life"] == 3 and observations["scope"]["entry_reset"] == reset
        assert all(t > reset for t in S.cited_transitions(observations))
    head = X.plan(machine)[0]
    assert (head["entity_id"], head["life"]) == ("E0053", 3)


def test_b3_09_a_level_change_closes_the_experiment_and_no_evidence_crosses_levels():
    machine, world = _owed_state()
    _act(machine, world, next_owned_step(machine), fx.LEVEL_UP)  # labelled double: E0053's press ends the level
    assert _events(machine)[-1] == ("STALE", "E0053", "CONTROLLER", "INTERRUPTED_LEVEL_CHANGE")
    assert machine.lives.level == 2 and machine.g4_selection_events[-1]["level"] == 1
    frozen = machine.level_censuses[-1]
    level = frozen if "lever_dossiers" in frozen else next(item for item in frozen["levels"] if item["level"] == 1)
    observations = level["lever_dossiers"]["E0053"]["observations"]
    assert observations["reversal"]["toggle_reversal"]["cases"] == []  # the level-ending press is no trial
    assert getattr(machine._adapters[RELATIONS], "_lever_experiments", []) == []  # level 2 starts with none


def test_b3_10_a_reset_is_never_counted_as_a_reversal():
    """The reset after the death returns E0053's tile to its life-2 entry content; it is the next life's entry, not
    a return, and the closed experiment's one press is not continued in life 3."""
    machine, world, _death, reset = _died()
    observations = _dossiers(machine)["E0053"]["observations"]
    assert all(item["status"] == "UNTESTED" and not item["cases"] for item in observations["reversal"].values())
    taken = _controller(machine, world)
    rows = [row for _step, row in taken if row is not None]
    assert rows and all(row["transition_id"] > reset for row in rows)
    assert all(":R1:" not in row["probe_id"] for row in rows)  # the life-2 experiment is not resumed
    from inference.framework import lever_dossier_state as S

    observations = _dossiers(machine)["E0053"]["observations"]
    assert reset not in S.cited_transitions(observations)
    assert all(case["transition_id"] > reset for item in observations["reversal"].values() for case in item["cases"])


# ---- 11-12 · evidence integrity and attribution -----------------------------------------------------------------

@pytest.mark.parametrize("damage", ["missing", "duplicated"])
def test_b3_11_missing_or_duplicated_execution_evidence_fails_only_that_observation_closed(damage):
    machine, world = _owed_state()
    _probe, row = _act(machine, world, next_owned_step(machine))
    if damage == "missing":  # labelled double: the step's transition lost its receipt
        machine.transition_index[-1] = {**machine.transition_index[-1], "evidence_id": None}
    else:  # labelled double: the gate recorded the step's execution twice
        adapter = machine._adapters[RELATIONS]
        adapter._events.append(dict(adapter._events[-1]))
    dossiers = _dossiers(machine)
    failed = dossiers["E0053"]["observations"]
    assert (failed["status"], failed["basis"]) == ("FAILED_CLOSED", "RECORD_MISMATCH")
    assert failed["failure"]["refs"] == [f"{EXP}REVERSAL:E0053:L1P2:R1"]
    assert dossiers["E0053"]["chapters"]["limits"]["facts"]["reversal"] == "PROBE_OWED"
    assert dossiers["E0053"]["chapters"]["identity"]["integrity"]["status"] == "OK"  # the witness is kept
    assert dossiers["E0053"]["chapters"]["anatomy"]["integrity"]["status"] == "OK"
    assert all(dossiers[e]["observations"]["status"] == "OBSERVED" for e in dossiers if e != "E0053")


def test_b3_12_a_press_of_another_lever_is_not_attributed_to_the_selected_lever():
    machine, world = _owed_state()
    machine.select_question(_qid("E0055"), actor="DUCK")
    step = next_owned_step(machine)
    assert step.action == _click("E0055")
    _probe, row = _act(machine, world, step)
    dossiers = _dossiers(machine)
    toggle = dossiers["E0055"]["observations"]["reversal"]["toggle_reversal"]
    assert [(c["evidence_ref"], c["acting_lever"]) for c in toggle["cases"]] == [(row["evidence_id"], "E0055")]
    for other in ("E0053", "E0054"):
        reversal = dossiers[other]["observations"]["reversal"]
        assert reversal["toggle_reversal"]["tested"] == 1 and not reversal["toggle_reversal"]["cases"]
        assert not any(c["evidence_ref"] == row["evidence_id"] for item in reversal.values() for c in item["cases"])
        assert "LIMITS_REVERSAL" in dossiers[other]["chapters"]["open_items"]["facts"]["probe_owed"]


# ---- 13-15 · persistence: an unchanged trial, a changed one, zero trials -----------------------------------------

def test_b3_13_a_persistence_trial_records_unchanged_with_its_own_receipt():
    machine, world, _death, _reset_id = _died()
    step = next_owned_step(machine)
    assert step.action == _click("E0054") and "PERSISTENCE_TRIAL of E0053" in step.reason
    probe, row = _act(machine, world, step)
    assert probe.probe_id == f"{EXP}PERSISTENCE:E0053:L1P3:R2:1"
    assert _events(machine)[-1] == ("FINISHED", "E0053", "CONTROLLER", "PERSISTENCE_UNCHANGED")
    dossiers = _dossiers(machine)
    persistence = dossiers["E0053"]["observations"]["persistence"]
    assert (persistence["status"], persistence["tested"], persistence["unchanged"]) == ("TESTED", 1, 1)
    assert persistence["unchanged_transitions"] == [row["transition_id"]]
    assert dossiers["E0053"]["observations"]["reversal"]["toggle_reversal"]["tested"] == 0  # E0054's press, not E0053's
    assert dossiers["E0054"]["observations"]["reversal"]["toggle_reversal"]["tested"] == 1


class _Coupled(Ft09World):
    """Labelled double: E0054's press also flips E0053's tile."""

    def changes(self, action):
        changed = super().changes(action)
        if (action["row"], action["col"]) != TILES["E0054"]:
            return changed
        return changed + [cell for cell in super().changes({"action": "ACTION6", "row": TILES["E0053"][0],
                                                            "col": TILES["E0053"][1]}) if cell[0] != 63]


def test_b3_14_a_changed_region_records_changed_not_persistence():
    machine, world, _death, _reset_id = _died()
    world = _with_world(world, _Coupled)
    _probe, row = _act(machine, world, next_owned_step(machine))
    assert _events(machine)[-1] == ("FINISHED", "E0053", "CONTROLLER", "PERSISTENCE_CHANGED")
    persistence = _dossiers(machine)["E0053"]["observations"]["persistence"]
    assert (persistence["unchanged"], persistence["changed"]) == (0, 1)
    assert persistence["changed_cases"][0]["transition_id"] == row["transition_id"]
    assert persistence["changed_cases"][0]["acting_lever"] == "E0054"


def test_b3_15_zero_trials_stay_untested_until_a_trial_is_recorded():
    from inference.framework import lever_experiments as X

    machine, _world, _death, _reset_id = _died()
    for dossier in _dossiers(machine).values():
        persistence = dossier["observations"]["persistence"]
        assert (persistence["status"], persistence["tested"]) == ("UNTESTED", 0)
        assert dossier["chapters"]["limits"]["facts"]["persistence"] == "UNTESTED"
        assert "LIMITS_PERSISTENCE" in dossier["chapters"]["open_items"]["facts"]["probe_owed"]
    head = X.plan(machine)[0]
    assert (head["entity_id"], head["kind"], head["acting_lever"]) == ("E0053", "PERSISTENCE_TRIAL", "E0054")


# ---- 16-17 · a stale subject, and no silent replacement --------------------------------------------------------

def test_b3_16_a_stale_chosen_subject_returns_to_coverage_with_nothing_inherited():
    machine, world = _owed_state()
    machine.select_question(_qid("E0054"), actor="DUCK")
    ledger = machine._adapters["G3-LEVERS"].entity_ledger
    ledger.entities["E0054"].status = "ABSENT"  # labelled double: the chosen lever left the board
    step = next_owned_step(machine)
    assert _events(machine)[:2] == [("ADMITTED", "E0054", "DUCK", "LIMITS_REVERSAL owed"),
                                    ("STALE", "E0054", "DUCK", "STALE_SUBJECT")]
    assert step.action == _click("E0053")
    probe, _row = _act(machine, world, step)
    assert probe.probe_id == f"{EXP}REVERSAL:E0053:L1P2:R2:1"  # a new admission, step 1, no receipt inherited


def test_b3_17_a_second_choice_cannot_replace_an_experiment_under_way():
    machine, _world = _owed_state()
    machine.select_question(_qid("E0054"), actor="DUCK")
    with pytest.raises(GateContractError, match="under way and cannot be replaced"):
        machine.select_question(_qid("E0055"), actor="DUCK")
    with pytest.raises(GateContractError, match="under way"):
        _predict(machine, "E0056")
    assert [e[:2] for e in _events(machine)] == [("ADMITTED", "E0054"), ("REFUSED", None)]
    assert machine._adapters[RELATIONS]._lever_experiment["entity_id"] == "E0054"


# ---- 18-19 · the persisted chain, and the three census points ---------------------------------------------------

def _finished_run():
    """(machine, unsealed H2 model): from the owed state, Duck chose E0054; the controller ran it, then E0053 and
    E0055, and the record certified G4-B."""
    def build():
        from test_g4_selection_persisted import _unsealed

        machine, world = _owed_state()
        machine.select_question(_qid("E0054"), actor="DUCK")
        _controller(machine, world)
        return machine, _unsealed(machine)
    return _cached("finished", build)


def _sealed(machine, unsealed, rows=None):
    from test_g4_selection_persisted import _translated, journal_bytes, sealed_unvalidated

    return sealed_unvalidated(unsealed, journal_bytes(_translated(machine) if rows is None else rows))


def test_b3_18_persisted_validation_refuses_forged_questions_subjects_scopes_outcomes_and_receipts():
    from inference.framework import lever_dossier_state as S
    from inference.framework import lever_dossiers as D
    from inference.framework import world_model_v2 as wm
    from test_g4_selection_persisted import _translated, _with

    machine, unsealed = _finished_run()
    wm.read_world_model(_sealed(machine, unsealed))  # the genuine chain
    rows = _translated(machine)
    assert [(r["refs"]["source_event"]["event"], r["refs"]["subject"], r["executor"]) for r in rows] == [
        ("ADMITTED", "E0054", "DUCK"), ("FINISHED", "E0054", "DUCK"), ("ADMITTED", "E0053", "CONTROLLER"),
        ("FINISHED", "E0053", "CONTROLLER"), ("ADMITTED", "E0055", "CONTROLLER"), ("FINISHED", "E0055", "CONTROLLER")]

    def refused(model, match):
        with pytest.raises(wm.WorldModelV2Error, match=match):
            wm.read_world_model(model)

    question = [_with(r, question_id=_qid("E0053")) if r["refs"]["subject"] == "E0054" else r for r in rows]
    refused(_sealed(machine, unsealed, question), "not the question derived from level, G4-B, E0054 and LIMITS")
    subject = [_with(r, subject="E0060", question_id=_qid("E0060")) if r["refs"]["subject"] == "E0054" else r
               for r in rows]
    refused(_sealed(machine, unsealed, subject), "belongs to no admitted experiment")
    scope = [_with(r, life=3) if r["refs"]["subject"] == "E0054" else r for r in rows]
    refused(_sealed(machine, unsealed, scope), "belongs to no admitted experiment")
    forged = pickle.loads(pickle.dumps(unsealed))  # the outcome: E0054's return removed, every digest recomputed
    level = next(item for item in forged["levels"] if item["state"] == "OPEN")
    dossier = level["lever_dossiers"]["E0054"]
    toggle = dossier["observations"]["reversal"]["toggle_reversal"]
    toggle.update(status="NOT_OBSERVED", cases=[])
    S.seal("E0054", dossier["observations"])
    D.reseal("E0054", dossier, level)
    refused(_sealed(machine, forged), "no return is cited, yet it finished after 1 of 8 steps")
    receipts = pickle.loads(pickle.dumps(unsealed))  # a receipt naming an experiment never admitted
    level = next(item for item in receipts["levels"] if item["state"] == "OPEN")
    ref = next(r for r, item in level["receipts"]["evidence"].items() if ":EXP:" not in str(item["probe_id"]))
    level["receipts"]["evidence"][ref]["probe_id"] = f"{EXP}REVERSAL:E0060:L1P2:R9:1"
    refused(_sealed(machine, receipts), "belongs to no admitted experiment")


def test_b3_19_live_view_h1_freeze_and_h2_agree_on_what_their_evidence_shows():
    """E0053 and E0054 finish; E0055's step ends the level (labelled double). The live view before that step, the
    H1 freeze of level 1 and the H2 write read the same observations: the level-ending press counts for nothing."""
    from inference.framework import world_model_v2 as wm
    from inference.framework.library_view import live_model
    from test_g4_selection_persisted import _unsealed

    machine, world = _owed_state()
    for _ in range(2):
        _act(machine, world, next_owned_step(machine))
    live = next(item for item in live_model(machine)["levels"] if item["level"] == 1)
    step = next_owned_step(machine)
    assert step.action == _click("E0055")
    _act(machine, world, step, fx.LEVEL_UP)
    model = _sealed(machine, _unsealed(machine))
    wm.read_world_model(model)
    h2 = next(item for item in model["levels"] if item["level"] == 1)
    frozen = machine.level_censuses[-1]
    h1 = frozen if "lever_dossiers" in frozen else next(item for item in frozen["levels"] if item["level"] == 1)
    for entity in OWED:
        views = [level["lever_dossiers"][entity]["observations"] for level in (live, h1, h2)]
        keep = ("status", "persistence", "reversal", "current_region_state")
        assert all({k: v[k] for k in keep} == {k: views[0][k] for k in keep} for v in views)
    assert live["lever_dossiers"]["E0053"]["observations"]["reversal"]["toggle_reversal"]["status"] == "OBSERVED"
    assert h2["lever_dossiers"]["E0055"]["observations"]["reversal"]["toggle_reversal"]["cases"] == []
    assert _events(machine)[-1] == ("STALE", "E0055", "CONTROLLER", "INTERRUPTED_LEVEL_CHANGE")


# ---- 20-22 · no-choice behaviour, controller-only, the per-step path ------------------------------------------

def test_b3_20_the_g3_and_g4_no_choice_goldens_stay_byte_identical():
    from g3_no_choice_trace import GOLDEN as G3_GOLDEN, RECORDS, no_choice_trace
    from g4_no_choice_trace import GOLDEN as G4_GOLDEN, traces

    assert traces() == json.loads(G4_GOLDEN.read_text())
    golden = json.loads(G3_GOLDEN.read_text())
    assert {name: no_choice_trace(path) for name, path in RECORDS.items()} == golden


def test_b3_21_controller_only_mode_runs_every_owed_experiment_with_no_duck_dependency():
    machine, world = _owed_state()
    taken = _controller(machine, world)
    assert all(step.owner == "CONTROLLER" for step, _row in taken) and machine.gate_id == LAW
    assert [e[:4] for e in _events(machine)] == [
        event for entity in OWED for event in (("ADMITTED", entity, "CONTROLLER", "LIMITS_REVERSAL owed"),
                                                ("FINISHED", entity, "CONTROLLER", "REVERSAL_OBSERVED"))]
    for entity, dossier in _dossiers(machine).items():
        assert "LIMITS_REVERSAL" not in dossier["chapters"]["open_items"]["facts"]["probe_owed"], entity


def test_b3_22_no_census_or_dossier_compile_runs_on_a_controller_step(monkeypatch):
    from inference.framework import library_census, lever_dossiers

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a census or dossier compile ran on the controller path")

    machine, world = _owed_state()
    for module, name in ((library_census, "compile_world_model"), (library_census, "compile_level"),
                         (lever_dossiers, "attach"), (lever_dossiers, "build")):
        if hasattr(module, name):
            monkeypatch.setattr(module, name, forbidden)
    taken = _controller(machine, world)
    assert sum(1 for _step, row in taken if row is not None) == 3 and machine.gate_id == LAW


def test_b3_23_a_records_experiment_step_replays_before_g4b_answers_and_readmits_ducks_choice():
    """A run's record names each experiment step from its envelope (``tools/record_from_artifacts``); replay holds
    G4-B's answers for it, as live, and admits Duck's choice again before its first step."""
    from inference.framework import lever_experiments as X
    from test_g4b_relations import _record_tool

    machine, _world = _owed_state()
    named = {"probe_id": f"{EXP}REVERSAL:E0054:L1P2:R1:1", "question_id": _qid("E0054"), "selected_by": "DUCK"}
    envelope = {"purpose": "LIMITS_EXPERIMENT", "probe_id": named["probe_id"],
                "target": {"question_id": named["question_id"], "selected_by": "DUCK", "entity_id": "E0054"}}
    assert _record_tool()._experiment(envelope) == {"experiment": named}
    assert _record_tool()._experiment({"purpose": "PREDICTION_TEST"}) == {}
    assert X.replay_hold(machine, {"action": {}}) is None
    assert X.replay_hold(machine, {"experiment": named}) == RELATIONS
    capability = machine.next_probe_capability()
    assert capability["target"]["entity_id"] == "E0054" and capability["target"]["selected_by"] == "DUCK"
    assert _events(machine) == [("ADMITTED", "E0054", "DUCK", "LIMITS_REVERSAL owed")]


def test_b3_24_the_card_and_the_library_section_keep_the_experiment_question_within_their_budgets():
    """Duck's card names the admissible experiments first in its subject and stays within its budget; the library
    section keeps the selected limits question at every tier, the ordinary one within 2,500 characters."""
    from inference.framework.card_builder import CARD_BUDGET, build_card
    from inference.framework.library_agenda import selected_target
    from inference.framework.library_view import DIGEST_BUDGET, live_model, render_library_digest

    machine, _world = _owed_state()
    card = build_card(machine)
    assert len(card.render()) <= CARD_BUDGET and not card.over_budget
    assert [row["question_id"] for row in card.payload["subject"]["experiments"]["admissible"]] == [
        _qid(entity) for entity in OWED]
    target = selected_target(machine)
    assert target["question_id"] == _qid("E0053") and DIGEST_BUDGET == 2500
    model = live_model(machine)
    for budget in (DIGEST_BUDGET, 1200, 700):
        rendered = render_library_digest(model, budget, target=target)
        assert len(rendered) <= budget and f'"question_id": "{target["question_id"]}"' in rendered
