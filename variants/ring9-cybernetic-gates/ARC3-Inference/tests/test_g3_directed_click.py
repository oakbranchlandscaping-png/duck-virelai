"""WO-G3-DIRECTED, CLICK slice: the gate agenda selects; G3 admits, binds and attributes a choice.

Author: Claude (Alpha build seat), 2026-10-11. Design: INTERFACE_WO_G3_DIRECTED_LIBRARY_TARGET v2 (Sol's review,
relayed by the Director). Numbered as in its §7:

0. With no choice, every probe envelope, evidence id and product replays byte-identical (Sol's decision 2).
1. An empty level selects its foundation question; no role is fabricated; NOT_BUILT never wins.
2. a) Duck chooses a non-head row: a fresh token binds that row's probe and the outcome is attributed to it;
   b) the bounded handoff happens once per G3 phase per level, then the controller serves the coverage head;
   c) a stale choice is refused and the head resumes; d) a choice never manufactures a lever.
3. A witness opens the lever's G4 questions, blocked by the G4 prerequisite until LeverInventory is active.
5. The card, the agenda and the action capability name the same question (answer turns: card and agenda).
6. Unresolved questions stay typed; free play is a fallback, never FILLED.
7. The agenda is pure and deterministic, and agrees with the validated census on every subject both cover.
8. Sol's review of the slice: the card, the library digest and the capability name one question; an explicit head
   choice is bound and attributed; G4-C's real product statuses close its questions; a handoff Duck spends without
   a choice (a turn-time yield) resumes coverage on the live session path; every choice event reaches disk.

Fixtures are development records (ruling 10): carry-v7 (a CLICK world), k008 (HYBRID: CLICK then NAV) and
k013 (HYBRID, nine witnessed levers, inventory pending), replayed through the production gate path.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pickle
from types import SimpleNamespace

import pytest

from g3_no_choice_trace import GOLDEN, RECORDS, no_choice_trace
from inference.framework.controller_executor import CONTROLLER, DUCK, next_owned_step
from inference.framework.gate_card import binding_gate_payload
from inference.framework.library_agenda import (
    G4_CHAPTERS, census_agreement, gate_agenda, lever_question_id, question_id,
)
from inference.framework.library_census import ExecutionRecord, compile_world_model
from inference.framework.play_gate import rest_in_play
from inference.framework.record_replay import lossless_outcome, record_like_live
from inference.framework.virelai_gates import CyberneticGateMachine, GateContractError
from replay_checkpoints import checkpoint_bytes
from test_l1a_pointer_g1_contract import GRID


def _digest(machine) -> str:
    return hashlib.sha256(pickle.dumps(machine)).hexdigest()


def _replayed(name: str, cut: int) -> bytes:
    """The pickled replay of ``name`` to ``cut``, from the shared checkpoint layer (WO-1): keyed by the record's
    content and options, built once per process; every consumer unpickles its own copy."""
    return checkpoint_bytes(RECORDS[name], max_steps=cut, measure=False)


def _at(name: str, cut: int):
    """Replay to ``cut`` (a fresh copy each call), then let the gate advance its own state as the live
    controller does first."""
    result = pickle.loads(_replayed(name, cut))
    capability = result.machine.next_probe_capability()
    return result, capability


def _census(machine):
    board = tuple(tuple(row) for row in machine.ego._initial_grid)
    recorded = tuple(str((row.get("action") or {}).get("action") or "") for row in machine.transition_index)
    execution = ExecutionRecord(board, int(machine.lives.level), tuple(a.action for a in machine.ego.affordances), recorded)
    return compile_world_model(machine, execution, game_id="g", run_stem="g", persist_reason="LIVE_VIEW",
                               frozen_levels=list(machine.level_censuses), reconcile_journal=False)


def _by_id(agenda):
    return {question["id"]: question for question in agenda["questions"]}


# ---- 0 · the no-choice regression guard --------------------------------------------------------------------

@pytest.mark.parametrize("name", sorted(RECORDS))
def test_0_no_choice_replays_keep_every_envelope_evidence_id_and_product(name):
    golden = json.loads(GOLDEN.read_text())[name]
    assert no_choice_trace(RECORDS[name]) == golden


# ---- 1 · foundations first ---------------------------------------------------------------------------------

def test_1_an_empty_level_selects_its_foundation_question_and_fabricates_no_role():
    machine = CyberneticGateMachine(valid_actions=["ACTION5", "ACTION6", "ACTION7"], initial_grid=GRID,
                                    observed_through_step=0)
    agenda = gate_agenda(machine)
    assert agenda["selected"] == question_id(1, "G0-ACTION-METADATA", "LEVEL-1", "ACTION_SURFACE")
    assert not any(q["gate"] == "G3-LEVERS" and q["kind"] == "IS_LEVER" for q in agenda["questions"])
    assert not any(q["disposition"].startswith("ANSWERED") for q in agenda["questions"])
    not_built = {q["id"] for q in agenda["questions"] if q["disposition"] == "NOT_BUILT"}
    assert len(not_built) == 5 and agenda["selected"] not in not_built and not set(agenda["eligible"]) & not_built


def test_1_a_new_level_restarts_at_its_foundation_without_the_previous_levels_levers():
    result, _ = _at("carry_v7", 26)
    agenda = gate_agenda(result.machine)
    assert agenda["level"] == 2 and agenda["selected"] == question_id(2, "G0-ACTION-METADATA", "LEVEL-2",
                                                                      "ACTION_SURFACE")
    assert not any(q["subject"] in {"E0004", "E0005"} for q in agenda["questions"])  # level 1's levers stay frozen


# ---- 3 · witnessed levers open G4, blocked until the inventory ---------------------------------------------

def test_3_witnessed_levers_open_g4_questions_blocked_until_the_inventory_is_active():
    result, _ = _at("k013", 400)
    agenda, questions = gate_agenda(result.machine), _by_id(gate_agenda(result.machine))
    levers = sorted(q["subject"] for q in agenda["questions"] if q["disposition"] == "ANSWERED_LEVER")
    assert len(levers) == 9 and result.machine.target_journal.active_product("G3-LEVERS") is None
    for lever in levers:
        chapters = [questions[question_id(1, gate, lever, kind)] for gate, kind, _text in G4_CHAPTERS]
        assert {q["disposition"] for q in chapters} == {"BLOCKED_BY_PREREQUISITE"}
        assert all(q["prerequisites_missing"] == ["G3-LEVERS"] for q in chapters)
    assert not set(agenda["eligible"]) & {q["id"] for q in agenda["questions"] if q["gate"] in {g for g, _, _ in G4_CHAPTERS}}


def test_3_after_the_inventory_each_lever_keeps_its_own_dossier_questions():
    result, _ = _at("carry_v7", 20)  # G4.2 under way on level 1; the inventory is active
    questions = _by_id(gate_agenda(result.machine))
    for lever in ("E0004", "E0005"):
        effects = questions[question_id(1, "G4-REACTIONS", lever, "EFFECTS")]
        orbit = questions[question_id(1, "G4.2-LEVER-ORBITS", lever, "ORBIT")]
        assert effects["disposition"] == "ANSWERED" and orbit["disposition"] in {"OPEN", "ANSWERED"}
    assert questions[question_id(1, "G4.2-LEVER-ORBITS", "E0004", "ORBIT")] is not \
        questions[question_id(1, "G4.2-LEVER-ORBITS", "E0005", "ORBIT")]


# ---- 5 · one target on the card, in the agenda and in the capability ---------------------------------------

G3_CUTS = [("carry_v7", cut) for cut in (3, 5, 7, 9, 11, 13, 15)] + [("k008", cut) for cut in (38, 40, 42, 44, 50, 60)]


@pytest.mark.parametrize(("name", "cut"), G3_CUTS)
def test_5_with_no_choice_the_agenda_selects_exactly_what_the_gate_serves(name, cut):
    result, capability = _at(name, cut)
    machine = result.machine
    agenda = gate_agenda(machine)
    if capability is None:  # an answer turn: card and agenda align; there is no capability
        assert binding_gate_payload(copy.deepcopy(machine))["question_id"] == agenda["selected"]
        return
    assert capability["question_id"] == agenda["selected"]
    target = capability.get("target") or {}
    if capability["purpose"] in {"RANKED_CLICK_TARGET", "PILOT_TO_LEVER_CONTACT"}:
        assert agenda["selected"] == lever_question_id(agenda["level"], target["entity_id"])
    else:
        assert agenda["selected"] == question_id(agenda["level"], "G3-LEVERS", target["entity_id"], "CONFIRM_WITNESS")
    card = binding_gate_payload(copy.deepcopy(machine))
    assert card["question_id"] == agenda["selected"]


def test_5_an_answer_turn_aligns_the_card_with_the_agenda_without_a_capability():
    result, capability = _at("carry_v7", 8)  # a G3 dossier answer is due
    assert capability is None
    agenda = gate_agenda(result.machine)
    assert agenda["obligation"]["kind"] == "DOSSIER"
    assert agenda["selected"] == question_id(1, "G3-LEVERS", agenda["obligation"]["entity_id"], "DOSSIER_ANSWER")
    assert binding_gate_payload(result.machine)["question_id"] == agenda["selected"]


# ---- 2 · a directed CLICK choice ---------------------------------------------------------------------------

def _choose(machine, entity_id):
    qid = lever_question_id(int(machine.lives.level), entity_id)
    machine.select_g3_question(qid, actor="DUCK")
    return qid, machine.next_probe_capability()


def _act(result, capability, changed=()):
    machine = result.machine
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, capability["actions"])
    transition_id = machine.observed_through_step + 1
    result.grid, outcome = lossless_outcome(result.grid, transition_id, capability["actions"][0], list(changed),
                                            probe_id=probe.probe_id)
    record_like_live(machine, probe, outcome, ["ACTION6"])
    return probe


def test_2a_duck_chooses_a_row_away_from_the_head_and_the_outcome_is_attributed_to_it():
    result, head = _at("carry_v7", 3)
    machine = result.machine
    agenda = gate_agenda(machine)
    assert len(agenda["eligible"]) >= 2 and agenda["selected"] == agenda["eligible"][0]
    chosen = agenda["eligible"][-1].split(":")[3]
    head_entity = head["target"]["entity_id"]
    qid, capability = _choose(machine, chosen)
    assert capability["target"]["entity_id"] == chosen and capability["question_id"] == qid
    assert capability["probe_token"] != head["probe_token"]
    with pytest.raises(GateContractError, match="Stale probe_token"):  # the head's token no longer binds
        machine.validate_probe({"probe_token": head["probe_token"]}, head["actions"])
    probe = _act(result, capability)
    assert probe.probe_id.startswith("G3-LEVERS:CLICK:SEL:") and probe.target["entity_id"] == chosen
    journal = machine._adapters["G3-LEVERS"].lifecycle_journal
    evidence = next(row["evidence_id"] for row in machine.transition_index if row["probe_id"] == probe.probe_id)
    assert journal.entities[chosen].state == "G3-CLOSED"  # a CLICK world's scoped null, on the chosen row
    assert journal.entities[chosen].events[-1].evidence_ref == evidence and not journal.entities[chosen].witness_refs
    assert journal.entities[head_entity].state == "UNTOUCHED"  # the head is not consumed by another row's outcome
    resumed = machine.next_probe_capability()
    assert resumed["target"]["entity_id"] == head_entity and resumed["question_id"] == lever_question_id(1, head_entity)
    assert gate_agenda(machine)["selected"] == lever_question_id(1, head_entity)


def test_2a_a_chosen_row_is_not_served_again_by_the_coverage_sweep():
    result, _ = _at("carry_v7", 3)
    machine = result.machine
    chosen = gate_agenda(machine)["eligible"][1].split(":")[3]
    _act(result, _choose(machine, chosen)[1])
    served = []
    for _ in range(12):
        capability = machine.next_probe_capability()
        if capability is None or capability["gate_id"] != "G3-LEVERS" or capability["purpose"] != "RANKED_CLICK_TARGET":
            break
        served.append(capability["target"]["entity_id"])
        _act(result, capability)
    assert served and chosen not in served


def test_2b_the_handoff_happens_once_per_phase_then_the_controller_serves_the_head():
    result, head = _at("carry_v7", 3)  # a CLICK world: the controller owns G3 clicks
    machine = result.machine
    assert next_owned_step(copy.deepcopy(machine)).owner == CONTROLLER  # default: unchanged controller path
    first = next_owned_step(machine, g3_choice_handoff=True)
    assert first.owner == DUCK and "G3 choice" in first.reason
    second = next_owned_step(machine, g3_choice_handoff=True)  # Duck chose nothing: coverage resumes
    assert second.owner == CONTROLLER and second.action == head["actions"][0]


def test_2c_a_stale_choice_is_refused_and_the_head_resumes():
    result, head = _at("carry_v7", 3)
    machine = result.machine
    eligible = gate_agenda(machine)["eligible"]
    _qid, first = _choose(machine, eligible[1].split(":")[3])
    _choose(machine, eligible[2].split(":")[3])
    with pytest.raises(GateContractError, match="Stale probe_token"):
        machine.validate_probe({"probe_token": first["probe_token"]}, first["actions"])
    machine.lives.life += 1  # a new life: the binding is no longer current
    resumed = machine.next_probe_capability()
    assert resumed["target"]["entity_id"] == head["target"]["entity_id"]
    events = machine._adapters["G3-LEVERS"]._selection_events
    assert events[-1]["event"] == "STALE"


@pytest.mark.parametrize("question", [
    "Q:L1:LIBRARY:LEVEL-1:ENVIRONMENTAL_FORCE", "Q:L1:G3-LEVERS:E9999:IS_LEVER", "not a question",
])
def test_2c_an_inadmissible_choice_is_refused_once_with_its_reason(question):
    result, head = _at("carry_v7", 3)
    machine = result.machine
    with pytest.raises(GateContractError, match="not admissible"):
        machine.select_g3_question(question, actor="DUCK")
    assert machine.next_probe_capability()["target"]["entity_id"] == head["target"]["entity_id"]
    assert machine._adapters["G3-LEVERS"]._selection_events[-1]["event"] == "REFUSED"


def test_2c_no_choice_is_admitted_while_the_gate_owes_an_obligation():
    result, capability = _at("carry_v7", 7)  # a witness awaits its confirmation
    assert capability["purpose"] == "CONFIRM_LEVER_WITNESS"
    agenda = gate_agenda(result.machine)
    assert agenda["obligation"]["kind"] == "CONFIRMATION" and agenda["eligible"] == []
    with pytest.raises(GateContractError, match="obligation"):
        result.machine.select_g3_question(lever_question_id(1, "E0010"), actor="DUCK")


def test_2d_a_choice_never_manufactures_a_lever():
    result, _ = _at("carry_v7", 3)
    machine = result.machine
    chosen = gate_agenda(machine)["eligible"][1].split(":")[3]
    _qid, capability = _choose(machine, chosen)
    elsewhere = [[row, col, 0, 9] for row, col in ((0, 0), (0, 1))]  # a change away from the chosen row
    _act(result, capability, elsewhere)
    item = machine._adapters["G3-LEVERS"].lifecycle_journal.entities[chosen]
    assert not item.witness_refs and item.state != "WITNESSED"


# ---- 6 · typed unresolved questions; free play is a fallback -----------------------------------------------

def test_6_unresolved_questions_stay_typed_and_nothing_claims_filled():
    result, _ = _at("k013", 400)
    agenda = gate_agenda(result.machine)
    dispositions = {q["disposition"] for q in agenda["questions"]}
    assert "INCONCLUSIVE" in dispositions and "NOT_BUILT" in dispositions and "FILLED" not in dispositions
    inconclusive = {q["id"] for q in agenda["questions"] if q["disposition"] == "INCONCLUSIVE"}
    assert len(inconclusive) == 5 and not inconclusive & set(agenda["eligible"])
    assert agenda["counts"]["unresolved"] > 0


def test_6_free_play_is_the_fallback_question_never_a_gated_one():
    result, _ = _at("k008", 60)
    rest_in_play(result.machine, "test: the level rests in normal play")
    agenda = gate_agenda(result.machine)
    play = _by_id(agenda)[agenda["selected"]]
    assert play["gate"] == "PLAY-NORMAL" and play["disposition"] == "OPEN_FALLBACK"
    assert agenda["eligible"] == []


# ---- 7 · pure, deterministic, and in agreement with the census ---------------------------------------------

@pytest.mark.parametrize(("name", "cut"), [("k013", 400), ("k008", 44), ("k008", 60), ("carry_v7", 9), ("carry_v7", 20)])
def test_7_the_agenda_is_pure_deterministic_and_agrees_with_the_census(name, cut):
    result, _ = _at(name, cut)
    machine = result.machine
    before = _digest(machine)
    first, second = gate_agenda(machine), gate_agenda(machine)
    assert _digest(machine) == before and first == second
    assert json.loads(json.dumps(first)) == first
    assert census_agreement(first, _census(machine)) == {}


def test_5_duck_chooses_through_the_tool_and_the_card_names_the_same_question(tmp_path):
    """The production bridge: virelai('next_probe', question_id=Q) admits the choice and binds the capability."""
    from test_gated_python_bridge import _agent

    result, head = _at("carry_v7", 3)
    agent, state_path = _agent(tmp_path)
    agent._gate_machine = result.machine
    chosen = gate_agenda(result.machine)["eligible"][1]
    reply = agent._run_python_tool(state_path, {"code": f"result = virelai('next_probe', question_id={chosen!r})"})
    visible = json.loads(json.loads(reply.content)["stdout"])
    assert visible["error"] is None and visible["data"]["question_id"] == chosen
    assert visible["data"]["target"]["question_id"] == chosen and visible["data"]["probe_token"] != head["probe_token"]
    card = agent._binding_gate_payload(result.machine)
    assert card["question_id"] == chosen == gate_agenda(result.machine)["selected"]
    refused = agent._run_python_tool(state_path, {"code": "result = virelai('next_probe', question_id='Q:L1:G3-LEVERS:E9999:IS_LEVER')"})
    shown = json.loads(json.loads(refused.content)["stdout"])
    assert shown["error"].startswith("G3 choice not admissible") and shown["data"]["question_id"] == chosen


# ---- 8 · Sol's review of the slice (2026-10-11) ------------------------------------------------------------

def _surfaces(tmp_path, machine):
    """The three surfaces Duck reads on one turn: the card and the digest as rendered into the prompt, and the
    capability the controller or Duck acts on."""
    from inference.framework.gate_card import BINDING_HEADER
    from inference.framework.library_view import HEADER
    from test_gated_python_bridge import _agent

    agent, state_path = _agent(tmp_path)
    agent._gate_machine = machine
    context = agent._gate_context_update(state_path)
    card_text, digest_text = context.split(HEADER)
    card = json.loads(card_text.strip()[len(BINDING_HEADER.strip()):])
    capability = machine.next_probe_capability()
    return card, json.loads(digest_text), capability


@pytest.mark.parametrize(("cut", "choose"), [(3, None), (3, 2), (7, None), (20, None)])
def test_8_the_card_the_digest_and_the_capability_name_one_question(tmp_path, cut, choose):
    """Finding 1: the digest's goal is the agenda's selected question, not the gate marked in progress."""
    result, _ = _at("carry_v7", cut)
    machine = result.machine
    if choose is not None:
        machine.select_g3_question(gate_agenda(machine)["eligible"][choose], actor="DUCK")
    selected = gate_agenda(machine)["selected"]
    card, digest, capability = _surfaces(tmp_path, machine)
    assert selected is not None and card["question_id"] == digest["goal"]["question_id"] == selected
    if capability is not None:
        assert capability["question_id"] == selected
    question = _by_id(gate_agenda(machine))[selected]
    assert digest["goal"]["gate_id"] == question["gate"] and digest["goal"]["question"] == question["question"]


def test_8_the_digest_keeps_its_goal_and_budget_at_the_minimal_tier():
    from inference.framework.library_agenda import selected_target
    from inference.framework.library_view import live_model, render_library_digest

    result, _ = _at("k013", 400)
    target = selected_target(result.machine)
    model = live_model(result.machine)
    for budget in (3000, 1200, 700):
        rendered = render_library_digest(model, budget, target=target)
        assert len(rendered) <= budget and f'"question_id": "{target["question_id"]}"' in rendered


def test_8_an_explicit_head_choice_is_bound_receipted_and_attributed_then_coverage_resumes():
    """Finding 2: the head chosen explicitly gets its own bound envelope; the no-choice envelope is unchanged."""
    result, head = _at("carry_v7", 3)
    machine = result.machine
    g3 = machine._adapters["G3-LEVERS"]
    head_entity, head_member = head["target"]["entity_id"], head["target"]["member_id"]
    coverage = g3.next_probe()
    assert coverage.probe_id == "G3-LEVERS:CLICK:1" and "question_id" not in coverage.target  # no choice: as golden
    qid, capability = _choose(machine, head_entity)
    assert capability["question_id"] == qid == lever_question_id(1, head_entity)
    assert capability["target"]["question_id"] == qid and capability["target"]["selected_by"] == "DUCK"
    assert capability["actions"] == head["actions"] and capability["probe_token"] != head["probe_token"]
    probe = _act(result, capability)
    assert probe.probe_id.startswith(f"G3-LEVERS:CLICK:SEL:{head_member}:L1P1:R")
    row = machine.transition_index[-1]
    assert row["probe_id"] == probe.probe_id  # the transition row names the bound probe
    journal = machine._adapters["G3-LEVERS"].lifecycle_journal
    assert journal.entities[head_entity].state == "G3-CLOSED"
    assert journal.entities[head_entity].events[-1].evidence_ref == row["evidence_id"]  # attributed to the head
    events = [event["event"] for event in machine._adapters["G3-LEVERS"]._selection_events]
    assert events == ["ADMITTED", "FINISHED"]
    after = machine.next_probe_capability()
    resumed = g3.next_probe()
    assert resumed.probe_id == "G3-LEVERS:CLICK:2" and after["target"]["entity_id"] != head_entity
    assert "question_id" not in resumed.target and after["question_id"] == gate_agenda(machine)["selected"]


def test_8_g4c_law_questions_close_on_the_products_real_statuses():
    """Finding 3: G4-C writes COMPLETE, UNRESOLVED or CLOSED_BY_LEVEL_BOUNDARY, never SUPPORTED."""
    from test_g4b_relations import _take, start_g4b
    from test_g4c_law import LAW, _described, _law

    def law_dispositions(machine):
        agenda = gate_agenda(machine)
        gate = {q["disposition"] for q in agenda["questions"] if q["gate"] == LAW and q["kind"] == "LEVER_LAW"}
        levers = {q["disposition"] for q in agenda["questions"] if q["gate"] == LAW and q["kind"] == "LAW"}
        return gate, levers, machine.target_journal.active_product(LAW).payload["status"]

    machine, world = start_g4b()
    _described(machine, world)
    _law(machine, "E0055")
    _take(machine, world)
    assert law_dispositions(machine) == ({"ANSWERED"}, {"ANSWERED"}, "COMPLETE")

    machine, world = start_g4b()
    _described(machine, world)
    machine._adapters[LAW].close_unresolved("test: Duck's G4-C budget is spent")
    assert law_dispositions(machine) == ({"CLOSED_UNRESOLVED"}, {"CLOSED_UNRESOLVED"}, "UNRESOLVED")


def test_8_a_refused_choice_reaches_the_durable_event_log(tmp_path):
    """Selection events survive the in-memory list: an admitted and a refused choice, with no action taken."""
    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
    from test_gated_python_bridge import _agent

    result, _ = _at("carry_v7", 3)
    agent, state_path = _agent(tmp_path)
    agent._gate_machine = result.machine
    chosen = gate_agenda(result.machine)["eligible"][1]
    for question in (chosen, "Q:L1:G3-LEVERS:E9999:IS_LEVER"):
        agent._run_python_tool(state_path, {"code": f"result = virelai('next_probe', question_id={question!r})"})
    path = state_path.with_name(state_path.name.replace(f"_{RUNTIME_STATE_FILENAME}", "_g3_selection_events.jsonl"))
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    assert [(row["event"], row["question_id"]) for row in rows] == [
        ("ADMITTED", chosen), ("REFUSED", "Q:L1:G3-LEVERS:E9999:IS_LEVER")]
    assert all(row["schema"] == "virelai-g3-selection-event-v1" and row["level"] == 1 for row in rows)
    assert rows[1]["reason"] == "the question names no row this G3 roster serves now"


class _Ft09Game:
    """The ft09 continuation behind the harness's game interface (ACTION6 data: x is the column, y the row)."""

    def __init__(self) -> None:
        from ft09_world import Ft09World

        self.world = Ft09World()
        self.game_run = SimpleNamespace(
            game_id="fixture", history=[], state="playing", solver_note=None, solver_analysis_html=None,
            final_score=None, levels_completed=0, number_of_levels=1, actions_per_level=[])
        self.number_of_levels = 1
        self.current_state = self._state()

    def _state(self):
        import arcengine
        from test_duck_native_observer import _Grid

        grid = _Grid([list(row) for row in self.world.grid])
        raw = SimpleNamespace(game_id="fixture", frame=[grid], state=arcengine.GameState.NOT_FINISHED,
                              levels_completed=0, win_levels=1, guid="fixture-guid", full_reset=False,
                              available_actions=(6,))
        return SimpleNamespace(raw=raw, frame=SimpleNamespace(data=grid), levels_completed=0, won=False,
                               just_won_level=False, available_actions=(6,))

    def execute_action(self, action, *, generated_tokens, uncached_input_tokens):
        del generated_tokens, uncached_input_tokens
        self.world.step({"action": action.id.name, "row": int(action.data["y"]), "col": int(action.data["x"])})
        self.game_run.history.append(SimpleNamespace(action=action))
        self.current_state = self._state()
        return self.current_state

    def finish_game(self):
        self.game_run.final_score = 0.0


def _prompt_text(message) -> str:
    content = message.get("content")
    if isinstance(content, str):
        return content
    return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))


def test_8_a_handoff_that_times_out_resumes_coverage_on_the_live_session_path(tmp_path):
    """Finding 4: ``_HarnessGameSession.play`` with the production ``ToolAgent`` and its live handoff on. Duck's
    one G3 choice turn reaches the model, which answers without a tool call; the turn-time budget yields. The
    next turn is the controller's coverage action, receipted as such, and the run does not stop."""
    import threading

    from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
    from inference.agent.tool_agent import ToolAgent, _ChatCompletionResult
    from inference.framework.library_view import HEADER
    from inference.framework.solver import HarnessSolver, _HarnessGameSession

    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True)
    assert agent._controller.g3_choice_handoff is True  # the live default (D3)
    agent._ensure_session = lambda _path: None
    game = _Ft09Game()
    prompts: list[str] = []
    seen: dict = {}

    def model(messages, **_kwargs):
        machine = agent._gate_machine
        prompts.append(_prompt_text(messages[-1]))
        seen.update(selected=gate_agenda(machine)["selected"], action_count=session.action_count)
        agent._yield_seconds = 0.0  # the turn-time budget is spent while Duck is still thinking
        solver.max_actions_per_game = session.action_count + 1  # end the run after the next action
        return _ChatCompletionResult(message={"role": "assistant", "content": "Weighing the rows."})

    agent._chat_completion = model
    state_path = tmp_path / f"fixture_{RUNTIME_STATE_FILENAME}"
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=agent, game_index=0, pass_index=0, state_path=state_path,
        transcript_path=tmp_path / "t.txt", analysis_html_relpath="a.html", stop_event=threading.Event(),
        viewer_data_path=tmp_path / "v.json")
    session.play()

    machine = agent._gate_machine
    assert len(prompts) == 1 and "G3 choice" in prompts[0] and machine.gate_id == "G3-LEVERS"
    card_text, digest_text = prompts[0].split(HEADER)
    assert f'"question_id": "{seen["selected"]}"' in card_text
    assert json.loads(digest_text.splitlines()[0])["goal"]["question_id"] == seen["selected"]
    # The one action after the yield: the controller's coverage probe, receipted as such.
    assert session.action_count == seen["action_count"] + 1 and game.game_run.state == "playing"
    envelope = json.loads((tmp_path / "fixture_probe_envelopes.jsonl").read_text().splitlines()[-1])
    receipt = json.loads((tmp_path / "fixture_gate_events.jsonl").read_text().splitlines()[-1])
    row = machine.transition_index[-1]
    assert envelope["executor"] == "CONTROLLER" and envelope["purpose"] == "RANKED_CLICK_TARGET"
    assert ":SEL:" not in envelope["probe_id"] and envelope["probe_id"].startswith("G3-LEVERS:CLICK:")
    assert receipt["probe_id"] == row["probe_id"] == envelope["probe_id"]
    assert receipt["evidence_id"] == row["evidence_id"] and row["transition_id"] == session.action_count
    assert lever_question_id(1, envelope["target"]["entity_id"]) == seen["selected"]  # the head Duck was shown
    ledger = [json.loads(line) for line in (tmp_path / "fixture_turn_ledger.jsonl").read_text().splitlines()]
    assert [(turn["executor"], turn["outcome"]) for turn in ledger[-2:]] == [
        ("DUCK", "turn_time_budget"), ("CONTROLLER", "controller_step")]
    rows = [json.loads(line) for line in (tmp_path / "fixture_g3_selection_events.jsonl").read_text().splitlines()]
    assert [row["event"] for row in rows] == ["HANDOFF", "COVERAGE_RESUMED"]
    assert session._l2a_end_reason == ""  # no turn ended the run: the yield was not a stop
