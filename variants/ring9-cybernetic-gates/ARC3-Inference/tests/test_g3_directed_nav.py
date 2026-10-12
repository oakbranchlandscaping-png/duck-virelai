"""WO-G3-DIRECTED, NAV selection and pursuit: Duck may choose one eligible NAV lever question; G3 admits it and
binds a pursuit the controller carries out route step by route step.

Author: Claude (Alpha build seat), 2026-10-12. Sol's directive (relayed by the Director): "In G3's NAV phase, Duck
may choose one eligible lever question. G3 admits the choice and binds a pursuit; the controller carries out the
route steps. Outcomes go through the existing G3 attribution and certification path. With no admissible choice,
coverage proceeds from the head as today." The fail-first baseline is ``ceeeabd``, where no NAV row was selectable
("a NAV row is not selectable in this slice") and the controller offered no NAV handoff.

The worlds are the two HYBRID development records, replayed through the production gate path to G3's NAV entry:

- k008 at transition 42: the CLICK pass is done; E0001 heads the NAV roster and E0002, E0004, E0005 and E0006 are
  the CLICK pass's scoped nulls, ``NO_RESPONSE_YET``, each still owing its body contact (genuinely eligible: the
  gate's own lifecycle put them there).
- k013 at transition 400 (life 8): the head's first planning call certifies a routing limit (a reachability
  obligation); every later row is in the same unreachable component.

Past the record, an action the record did not take has no recorded response. ``RigidEgoWorld`` synthesizes one
(test-only, from the record's own evidence): the ego footprint moves as one block by its G1-demonstrated bearing
onto cells holding the integer the ego leaves behind in the record's own moves; any other move changes nothing.
"""
from __future__ import annotations

import json
import pickle
from pathlib import Path

import pytest

from inference.framework import g3_selection
from inference.framework.controller_executor import ACTION, ANSWER, CONTROLLER, DUCK, next_owned_step
from inference.framework.library_agenda import gate_agenda, lever_question_id
from inference.framework.nav_control import compile_nav_control_map
from inference.framework.record_replay import lossless_outcome, merge_recorded_answer, record_like_live
from inference.framework.virelai_gates import GateContractError
from test_g3_directed_click import _replayed
from test_g3_hybrid_click_pass import HybridRun
from test_g3_hybrid_lifecycle_replay import K013, K013_FIRST_NAV, K013_LIVE_LEVERS, _drive, _levers

K008_NAV = 42  # k008: the CLICK pass ends at transition 42; the next capability call flips G3 into NAV
K008_TRUE_STAND = (12, 16)  # the ego's footprint after RESET 31 (test_k008_t44_plan_starts_from_...)
OFF_HEAD = "E0004"  # a NO_RESPONSE_YET row three places from the head, owing its body contact
SEL_PREFIX = "G3-LEVERS:NAV:SEL:"


class RigidEgoWorld:
    """Synthesized responses past the record (see the module docstring); never read by the solver."""

    def __init__(self, machine, recorded_steps) -> None:
        ledger = machine._adapters["G3-LEVERS"].entity_ledger
        ego = ledger.entities[ledger.role_entities("EGO")[0]].current
        self.integer, self.cells = int(ego.integer), set(ego.cells)
        self.floor = {int(cell[3]) for step in recorded_steps for cell in step["changed"] if int(cell[2]) == self.integer}
        self.bearings = compile_nav_control_map(machine.ego).bearing_map()
        self.extra: list[list[int]] = []  # one-shot changes added to the next response (a synthesized event)

    def changes(self, grid, action) -> list[list[int]]:
        extra, self.extra = self.extra, []
        delta = self.bearings.get(str(action.get("action")))
        if delta is None or len(self.floor) != 1:
            return extra
        moved = {(r + delta[0], c + delta[1]) for r, c in self.cells}
        inside = all(0 <= r < len(grid) and 0 <= c < len(grid[0]) for r, c in moved)
        if not inside or any(grid[r][c] not in self.floor for r, c in moved - self.cells):
            return extra
        floor = next(iter(self.floor))
        out = [[r, c, grid[r][c], floor] for r, c in sorted(self.cells - moved)]
        out += [[r, c, grid[r][c], self.integer] for r, c in sorted(moved - self.cells)]
        self.cells = moved
        return out + extra


class Sim:
    """The machine at a record cut, driven at the controller's level (``next_owned_step``, then act)."""

    def __init__(self, name: str = "k008", cut: int = K008_NAV) -> None:
        from inference.framework.record_replay import load_record
        from test_g3_directed_click import RECORDS

        result = pickle.loads(_replayed(name, cut))
        self.machine, self.grid = result.machine, [list(row) for row in result.grid]
        self.capability = self.machine.next_probe_capability()  # the gate advances its own state first
        self.g3 = self.machine._adapters["G3-LEVERS"]
        steps = [step for step in load_record(RECORDS[name])["steps"] if int(step["transition_id"]) > cut]
        self.world = RigidEgoWorld(self.machine, steps)
        self.valid = [item.action for item in self.machine.ego.affordances]
        self.probes: list = []
        self.receipts: list[dict] = []  # the G3 event each recorded outcome returns

    def choose(self, entity_id: str) -> str:
        qid = lever_question_id(int(self.machine.lives.level), entity_id)
        self.machine.select_g3_question(qid, actor="DUCK")
        return qid

    def step(self):
        owned = next_owned_step(self.machine)
        if owned.owner != CONTROLLER:
            return owned
        if owned.kind == ANSWER:
            self.machine.submit_answer(owned.answer)
            return owned
        probe = self.machine.validate_probe({"probe_token": owned.probe_token, **dict(owned.decision or {})},
                                            [owned.action])
        changed = self.world.changes(self.grid, owned.action)
        self.grid, outcome = lossless_outcome(self.grid, self.machine.observed_through_step + 1, owned.action,
                                              changed, probe_id=probe.probe_id)
        self.receipts.append(self.machine.record_outcome(probe, outcome))  # ``record_like_live``, keeping the receipt
        self.machine.update_action_metadata(list(self.valid))
        self.probes.append(probe)
        return owned

    def events(self) -> list[str]:
        return [row["event"] for row in self.g3._selection_events]


def _distance(cells_a, cells_b) -> int:
    return min(abs(a[0] - b[0]) + abs(a[1] - b[1]) for a in cells_a for b in cells_b)


def _target_cells(g3, entity_id):
    return g3.entity_ledger.entities[entity_id].current.cells


# ---- 1 · G3 owns admission -----------------------------------------------------------------------------------

def test_k008_nav_entry_offers_a_genuine_choice_the_gate_admits():
    sim = Sim()
    assert sim.g3._phase == "NAV" and sim.g3._world_type == "HYBRID"
    assert sim.capability["purpose"] == "PILOT_TO_LEVER_CONTACT" and sim.capability["target"]["entity_id"] == "E0001"
    rows = g3_selection.admission_candidates(sim.g3)
    selectable = [row["entity_id"] for row in rows if row["selectable"]]
    assert selectable == ["E0001", "E0002", "E0004", "E0005", "E0006"]
    journal = sim.g3.lifecycle_journal
    assert {journal.entities[e].state for e in selectable[1:]} == {"NO_RESPONSE_YET"}  # owed body contact
    agenda = gate_agenda(sim.machine)
    assert agenda["eligible"] == [lever_question_id(1, e) for e in selectable]  # the gate's eligibility, reported
    assert agenda["selected"] == lever_question_id(1, "E0001")  # with no choice, the coverage head


def test_an_off_head_nav_choice_binds_a_selected_pursuit_on_the_true_post_reset_board():
    sim = Sim()
    head_token = sim.capability["probe_token"]
    qid = sim.choose(OFF_HEAD)
    capability = sim.machine.next_probe_capability()
    assert capability["purpose"] == "PILOT_TO_LEVER_CONTACT" and capability["question_id"] == qid
    assert capability["target"]["entity_id"] == OFF_HEAD and capability["target"]["question_id"] == qid
    assert capability["probe_token"] != head_token
    with pytest.raises(GateContractError, match="Stale probe_token"):
        sim.machine.validate_probe({"probe_token": head_token, "pilot_intent": "APPROACH"}, [{"action": "ACTION1"}])
    probe = sim.g3.next_probe()
    assert probe.probe_id.startswith(f"{SEL_PREFIX}M0007:L1P2:R") and probe.probe_id.endswith(":1")
    plan = sim.g3.planned_nav_step(capability["target"])
    assert tuple(plan.stand) == K008_TRUE_STAND  # planned from where the ego really is after RESET 31
    assert gate_agenda(sim.machine)["selected"] == qid
    selection = sim.g3._selection
    assert selection["entity_id"] == OFF_HEAD and selection["phase"] == "NAV"
    assert selection["entity_version"] == sim.g3.entity_ledger.entities[OFF_HEAD].version


def test_the_controller_pursues_the_chosen_row_for_several_steps_then_coverage_resumes_without_it():
    sim = Sim()
    qid = sim.choose(OFF_HEAD)
    target = _target_cells(sim.g3, OFF_HEAD)
    start = _distance(sim.world.cells, target)
    for _ in range(60):
        if "FINISHED" in sim.events():
            break
        owned = sim.step()
        assert owned.owner == CONTROLLER and owned.kind == ACTION, owned.reason
    selected = [p for p in sim.probes if p.probe_id.startswith(SEL_PREFIX)]
    assert len(selected) >= 2 and len(selected) == len(sim.probes)  # every step of the pursuit is the bound one
    admission = {p.probe_id.rsplit(":", 1)[0] for p in selected}
    assert len(admission) == 1  # one admission identity across its route steps ...
    rows = [row for row in sim.machine.transition_index if (row.get("probe_id") or "").startswith(SEL_PREFIX)]
    assert [row["probe_id"] for row in rows] == [p.probe_id for p in selected]  # ... distinct steps and evidence
    assert len({row["evidence_id"] for row in rows}) == len(rows)
    assert all(p.target["entity_id"] == OFF_HEAD and p.target["question_id"] == qid for p in selected)
    assert _distance(sim.world.cells, target) < start  # driven toward the chosen object
    assert sim.events() == ["ADMITTED", "FINISHED"]
    assert sim.g3.lifecycle_journal.entities["E0001"].state == "NO_RESPONSE_YET"  # the head was not consumed
    journal = sim.g3.lifecycle_journal.entities[OFF_HEAD]
    assert journal.state == "G3-CLOSED" and journal.events[-1].evidence_ref == rows[-1]["evidence_id"]  # its own outcome
    resumed = sim.g3.next_probe()
    assert resumed.probe_id == "G3-LEVERS:NAV:1:1" and "question_id" not in resumed.target  # coverage, from its head
    assert OFF_HEAD not in {row["entity_id"] for row in g3_selection.admission_candidates(sim.g3)}
    assert lever_question_id(1, OFF_HEAD) not in gate_agenda(sim.machine)["eligible"]
    assert _levers(sim.g3) == (set(), set(), set())  # no lever from movement on k008
    # The full coverage pass after a finished choice (never serving it again) is driven on k013 below, where
    # each row resolves in one reachability answer; on k008 each row costs a full route (~2.5 s a step).


def test_an_explicit_head_choice_is_bound_and_an_implicit_head_step_stays_on_the_coverage_path():
    implicit = Sim()
    implicit.step()
    assert implicit.probes[0].probe_id == "G3-LEVERS:NAV:1:1" and "question_id" not in implicit.probes[0].target
    assert implicit.events() == []
    explicit = Sim()
    qid = explicit.choose("E0001")
    explicit.step()
    probe = explicit.probes[0]
    assert probe.probe_id.startswith(f"{SEL_PREFIX}M0004:L1P2:R") and probe.target["question_id"] == qid
    assert probe.actions == implicit.probes[0].actions  # the same route step, under the selected identity
    assert explicit.machine.transition_index[-1]["probe_id"] == probe.probe_id
    assert explicit.events() == ["ADMITTED"]


# ---- 2 · mandatory work keeps its priority -------------------------------------------------------------------

def test_a_started_coverage_pursuit_owes_its_body_contact_before_any_choice():
    sim = Sim()
    sim.step()  # the head's pursuit is under way
    assert sim.g3._navigation_steps == 1
    assert not any(row["selectable"] for row in g3_selection.admission_candidates(sim.g3))
    assert gate_agenda(sim.machine)["eligible"] == [] and not g3_selection.choice_handoff_due(sim.g3)
    with pytest.raises(GateContractError, match="body contact"):
        sim.choose(OFF_HEAD)
    assert sim.events() == ["REFUSED"]
    assert sim.g3.next_probe().probe_id == "G3-LEVERS:NAV:1:2"


@pytest.fixture(scope="module")
def k013_certified():
    record, _result, machine, g3 = _drive(K013, K013_FIRST_NAV)
    first = next_owned_step(machine)  # the live controller's planning call certifies the routing limit
    return record, machine, g3, first


def test_a_reachability_obligation_comes_before_any_choice(k013_certified):
    _record, machine, g3, first = k013_certified
    assert first.owner == DUCK and g3._pending_reachability["target_entity_id"] == "E0001"
    assert g3_selection.obligation(g3)["kind"] == "REACHABILITY"
    agenda = gate_agenda(machine)
    assert agenda["obligation"]["kind"] == "REACHABILITY" and agenda["eligible"] == []
    assert not g3_selection.choice_handoff_due(g3)
    with pytest.raises(GateContractError, match="reachability obligation"):
        machine.select_g3_question(lever_question_id(1, "E0016"), actor="DUCK")
    assert g3._selection is None and g3._selection_events[-1]["event"] == "REFUSED"


def test_k013_an_off_head_choice_ends_in_its_reachability_answer_and_is_not_served_again():
    record, _result, machine, g3 = _drive(K013, K013_FIRST_NAV)
    next_owned_step(machine)
    machine.submit_answer(merge_recorded_answer(machine.gate_view()["answer_template"], record["answers"][-1]))
    rows = g3_selection.admission_candidates(g3)
    assert rows[0]["entity_id"] == "E0002" and sum(row["selectable"] for row in rows) >= 2
    assert not any(row["selectable"] for row in rows if row["entity_id"] in {"E0015", "E0018", "E0020"})  # ambiguous
    machine.select_g3_question(lever_question_id(1, "E0016"), actor="DUCK")
    served = []
    for _ in range(80):
        if g3._complete_reason:
            break
        owned = next_owned_step(machine)
        if owned.owner == CONTROLLER and owned.kind == ANSWER:
            served.append(g3._pending_reachability["target_entity_id"])
            machine.submit_answer(owned.answer)
        else:
            assert owned.owner == DUCK
    assert served[0] == "E0016" and served.count("E0016") == 1  # pursued first, never again
    events = [(row["event"], row["entity_id"]) for row in g3._selection_events]
    assert events == [("ADMITTED", "E0016"), ("FINISHED", "E0016")]
    assert g3._complete_reason == "NAV_ENUMERATION_COMPLETE"
    assert g3.lifecycle_journal.entities["E0002"].state == "PRESUMED_UNREACHABLE"  # the head still answered
    witnessed, discovered, unsupported = _levers(g3)
    assert witnessed == discovered == K013_LIVE_LEVERS and unsupported == set()  # no false lever


# ---- 3 · staleness returns to coverage ----------------------------------------------------------------------

def test_a_new_life_makes_the_choice_stale_and_coverage_resumes():
    sim = Sim()
    sim.choose(OFF_HEAD)
    sim.step()
    sim.machine.lives.life += 1
    assert sim.g3.next_probe().probe_id.startswith("G3-LEVERS:NAV:1:")
    assert sim.events()[-1] == "STALE" and sim.g3._selection_events[-1]["reason"] == "a new life began"


def test_a_change_to_the_chosen_object_makes_the_choice_stale():
    sim = Sim()
    sim.choose(OFF_HEAD)
    r, c = _target_cells(sim.g3, OFF_HEAD)[0]
    sim.world.extra = [[r, c, sim.grid[r][c], (sim.grid[r][c] + 1) % 10]]  # the object changes during approach
    sim.step()
    assert sim.probes[-1].probe_id.startswith(SEL_PREFIX)
    assert not sim.g3.next_probe().probe_id.startswith(SEL_PREFIX)
    assert sim.g3._selection_events[-1]["event"] == "STALE"
    assert sim.g3._selection_events[-1]["reason"] == "the chosen object changed"
    assert OFF_HEAD not in sim.g3._chosen_members  # not finished: coverage still owes it


def _assert_fresh_coverage_step(sim, abandoned_refs):
    """Sol's review of revision 1: the first resumed action is a fresh coverage step at the head, with none of the
    abandoned pursuit's step count or route evidence, receipted and attributed to the head."""
    probe, receipt, row = sim.probes[-1], sim.receipts[-1], sim.machine.transition_index[-1]
    assert probe.probe_id == "G3-LEVERS:NAV:1:1" and "question_id" not in probe.target
    assert probe.target["entity_id"] == receipt["target"]["entity_id"] == "E0001"
    assert receipt["probe_id"] == row["probe_id"] == probe.probe_id and receipt["evidence_id"] == row["evidence_id"]
    assert receipt["scheduler"]["route_evidence_refs"] == [receipt["evidence_id"]]
    assert not set(abandoned_refs) & set(sim.g3._nav_route_evidence)
    assert sim.g3._navigation_steps == 1
    head = sim.g3.lifecycle_journal.entities["E0001"]
    assert head.state == "ATTEMPTED" and head.events[-1].evidence_ref == receipt["evidence_id"]
    assert [event for event in sim.events() if event == "STALE"] == ["STALE"]  # one STALE event


def test_after_the_chosen_object_changes_the_resumed_coverage_step_starts_fresh():
    sim = Sim()
    sim.choose(OFF_HEAD)
    sim.step()  # a selected approach step
    r, c = _target_cells(sim.g3, OFF_HEAD)[0]
    sim.world.extra = [[r, c, sim.grid[r][c], (sim.grid[r][c] + 1) % 10]]  # the object changes during approach
    sim.step()
    abandoned = [receipt["evidence_id"] for receipt in sim.receipts]
    assert all(p.probe_id.startswith(SEL_PREFIX) for p in sim.probes) and sim.g3._navigation_steps == 2
    sim.step()  # the first resumed controller action
    assert sim.g3._selection_events[-1]["reason"] == "the chosen object changed"
    _assert_fresh_coverage_step(sim, abandoned)


def test_after_a_new_life_the_resumed_coverage_step_starts_fresh():
    sim = Sim()
    sim.choose(OFF_HEAD)
    sim.step()
    sim.step()
    abandoned = [receipt["evidence_id"] for receipt in sim.receipts]
    sim.machine.lives.life += 1  # a new life: the binding is no longer current
    sim.step()  # the first resumed controller action
    assert sim.g3._selection_events[-1]["reason"] == "a new life began"
    _assert_fresh_coverage_step(sim, abandoned)


def test_a_row_chosen_in_the_click_pass_still_owes_its_nav_body_contact():
    """A HYBRID world's CLICK choice finishes the row's CLICK work only: its NAV body contact is still owed."""
    sim = Sim(cut=37)  # G3's entry, in its CLICK pass
    assert sim.g3._phase == "CLICK"
    sim.choose(OFF_HEAD)
    for _ in range(8):
        if sim.g3._phase == "NAV":
            break
        sim.step()  # the chosen click, then the coverage clicks (the record shows scoped nulls only)
    assert sim.g3._phase == "NAV"
    clicked = [p.target["entity_id"] for p in sim.probes]
    assert clicked[0] == OFF_HEAD and clicked.count(OFF_HEAD) == 1  # served once in CLICK
    assert sim.g3.lifecycle_journal.entities[OFF_HEAD].state == "NO_RESPONSE_YET"
    rows = {row["entity_id"]: row for row in g3_selection.admission_candidates(sim.g3)}
    assert OFF_HEAD in rows and rows[OFF_HEAD]["obligation"] == "BODY_CONTACT_OWED"


# ---- 4 · the bounded NAV handoff -----------------------------------------------------------------------------

class NavRun(HybridRun):
    """The production agent from k008's NAV entry; past the record the world is ``RigidEgoWorld``."""

    def __init__(self, tmp_path: Path, monkeypatch, choice: str | None = None) -> None:
        super().__init__(tmp_path, monkeypatch, name="k008", cut=K008_NAV)
        self.choice, self.chose = choice, False
        recorded = [step for transition, step in self.recorded.items() if transition > K008_NAV]
        self.machine.next_probe_capability()
        self.world = RigidEgoWorld(self.machine, recorded)

    def _model(self, messages, **kwargs):
        from inference.agent.tool_agent import _ChatCompletionResult

        if self.choice is None or self.chose:
            return super()._model(messages, **kwargs)
        self.chose = True
        self.prompts.append(str(messages[-1].get("content")))
        code = f"result = virelai('next_probe', question_id={lever_question_id(1, self.choice)!r})"
        call = {"id": "c1", "type": "function", "function": {"name": "python", "arguments": json.dumps({"code": code})}}
        return _ChatCompletionResult(message={"role": "assistant", "content": "", "tool_calls": [call]},
                                     finish_reason="tool_calls", usage={"prompt_tokens": 1, "completion_tokens": 1})

    def step_env(self, payload: dict) -> dict:
        from inference.agent.runtime_state import Frame, HistoryEntry, write_runtime_state

        self.env_calls.append(payload)
        action = dict(payload["actions"][0])
        transition = self.transition + 1
        before = [list(row) for row in self.grid]
        self.grid, _outcome = lossless_outcome(self.grid, transition, action, self.world.changes(self.grid, action))
        frame = Frame(grid=tuple(tuple(r) for r in self.grid), step=transition, level=1)
        self.history.append(HistoryEntry(action=str(action["action"]), frame=frame))
        write_runtime_state(self.state_path, current_frame=frame, history=self.history)
        return {"executed": True, "action_num": transition, "transition_id": transition, "level": 1,
                "state": "NOT_FINISHED", "valid_actions": list(self.valid), "board_changed": before != self.grid,
                "done": False, "level_completed": False, "game_over": False}


def test_duck_chooses_in_the_nav_handoff_and_every_surface_names_the_chosen_pursuit(tmp_path):
    monkeypatch = pytest.MonkeyPatch()
    try:
        run = NavRun(tmp_path, monkeypatch, choice=OFF_HEAD)
        qid = lever_question_id(1, OFF_HEAD)
        chose = run.turn()  # the one NAV handoff: Duck chooses through the tool
        assert chose is not None and not chose.step_executed and run.env_calls == []
        assert f'"question_id": "{lever_question_id(1, "E0001")}"' in run.prompts[0]
        g3 = run.machine._adapters["G3-LEVERS"]
        for _ in range(3):
            card = run.agent._binding_gate_payload(run.machine)
            assert card["question_id"] == qid == gate_agenda(run.machine)["selected"]
            acted = run.turn()
            assert acted is not None and acted.step_executed, "the selected pursuit went back to Duck"
            envelope, receipt, row = run.rows("_probe_envelopes.jsonl")[-1], run.rows("_gate_events.jsonl")[-1], \
                run.machine.transition_index[-1]
            assert envelope["executor"] == "CONTROLLER" and envelope["purpose"] == "PILOT_TO_LEVER_CONTACT"
            assert envelope["probe_id"] == receipt["probe_id"] == row["probe_id"]
            assert envelope["probe_id"].startswith(f"{SEL_PREFIX}M0007:L1P2:R")
            assert envelope["target"]["entity_id"] == receipt["target"]["entity_id"] == OFF_HEAD
            assert envelope["target"]["question_id"] == receipt["target"]["question_id"] == qid
            assert receipt["evidence_id"] == row["evidence_id"]
        assert len(run.prompts) == 2  # one Duck turn: the choice and its follow-up call
        assert [item["executor"] for item in run.rows("_turn_ledger.jsonl")] == ["DUCK"] + ["CONTROLLER"] * 3
        events = run.rows("_g3_selection_events.jsonl")
        assert [(item["event"], item["actor"], item["phase"]) for item in events] == [
            ("HANDOFF", "CONTROLLER", "NAV"), ("ADMITTED", "DUCK", "NAV")]
        assert g3._navigation_steps == 3
    finally:
        monkeypatch.undo()


def test_a_declined_nav_handoff_costs_one_duck_turn_and_coverage_continues(tmp_path):
    monkeypatch = pytest.MonkeyPatch()
    try:
        run = NavRun(tmp_path, monkeypatch)
        declined = run.turn()
        assert declined is not None and not declined.step_executed and len(run.prompts) == 1
        for _ in range(4):
            assert run.turn().step_executed and len(run.prompts) == 1  # no second NAV handoff
        assert run.rows("_probe_envelopes.jsonl")[0]["probe_id"] == "G3-LEVERS:NAV:1:1"
        assert [item["event"] for item in run.rows("_g3_selection_events.jsonl")] == ["HANDOFF", "COVERAGE_RESUMED"]
        assert [(item["executor"], item["outcome"]) for item in run.rows("_turn_ledger.jsonl")][0] == \
            ("DUCK", "turn_time_budget")
    finally:
        monkeypatch.undo()


def test_with_the_handoff_off_the_nav_pass_is_the_controllers_from_its_first_step(tmp_path):
    monkeypatch = pytest.MonkeyPatch()
    try:
        run = NavRun(tmp_path, monkeypatch)
        run.agent._controller.g3_choice_handoff = False
        assert run.turn().step_executed and run.prompts == []
        assert run.rows("_probe_envelopes.jsonl")[-1]["probe_id"] == "G3-LEVERS:NAV:1:1"
        assert run.rows("_g3_selection_events.jsonl") == []
    finally:
        monkeypatch.undo()
