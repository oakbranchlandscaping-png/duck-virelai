from __future__ import annotations

import json

from inference.agent.runtime_state import (
    Frame,
    HistoryEntry,
    RUNTIME_STATE_FILENAME,
    write_runtime_state,
)
from inference.agent.tool_agent import ToolAgent
from inference.agent.tool_agent import _build_system_prompt


def _agent(tmp_path):
    state_path = tmp_path / f"gated_{RUNTIME_STATE_FILENAME}"
    write_runtime_state(
        state_path,
        current_frame=Frame(grid=((0, 1), (0, 0)), step=0, level=1),
        history=[],
    )
    agent = ToolAgent(
        model="fixture-model",
        virelai_enabled=True,
        virelai_gates_enabled=True,
    )
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["ACTION1", "ACTION2"]
    return agent, state_path


def _capability(agent, state_path):
    machine = agent._ensure_gate_machine(state_path)
    if machine.g0_answer is None:
        machine.submit_answer({
            "answer_id": "G0-test",
            "action_metadata": [
                {"action": item.action, "requires_coordinates": item.requires_coordinates}
                for item in machine.ego.affordances
            ],
            "semantic_claims": [],
            "epistemic_limit": "Action effects remain unknown until they are observed through probes.",
        })
    capability = machine.next_probe_capability()
    assert capability is not None
    return capability


def test_bare_action_is_rejected_before_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    result = agent._run_python_tool(state_path, {"code": "action(['ACTION1'])"})
    assert not result.step_executed
    assert calls == []
    assert "G0 action metadata is unanswered" in result.content


def test_semantic_action_name_is_rejected_before_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    capability = _capability(agent, state_path)
    decision = repr({"probe_token": capability["probe_token"]})
    result = agent._run_python_tool(
        state_path, {"code": f"action(['LEFT'], decision={decision})"}
    )
    assert not result.step_executed
    assert calls == []
    assert "opaque" in result.content


def test_exact_next_probe_executes_and_persists_evidence(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {
        "executed": True,
        "action_num": 1,
        "transition_id": 1,
        "level": 1,
        "valid_actions": ["ACTION1", "ACTION2"],
        "board_changed": True,
    }
    capability = _capability(agent, state_path)
    decision = repr({"probe_token": capability["probe_token"]})
    result = agent._run_python_tool(
        state_path, {"code": f"action({capability['actions']!r}, decision={decision})"}
    )
    assert result.step_executed
    assert len(calls) == 1
    assert calls[0]["actions"] == [{"action": "ACTION1"}]
    assert calls[0]["decision"]["gate_id"] == "G1-EGO"
    events = [json.loads(line) for line in (tmp_path / "gated_gate_events.jsonl").read_text().splitlines()]
    assert len(events) == 1
    assert events[0]["probe_id"].endswith("PAIR-ACTION1-1")
    assert events[0]["gate_status_after"] == "ACTIVE"
    assert events[0]["coverage_certificate"]["schema"] == (
        "virelai-g1-coverage-certificate-v1"
    )


def test_gate_query_result_is_visible_without_an_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    result = agent._run_python_tool(state_path, {"code": "result = virelai('gate')"})
    payload = json.loads(result.content)
    visible = json.loads(payload["stdout"])
    assert visible["data"]["gate_id"] == "G0-ACTION-METADATA"
    assert visible["data"]["next_operation"] == "SUBMIT_GATE_ANSWER"
    assert visible["data"]["action_metadata"] == [
        {"action": "ACTION1", "requires_coordinates": False},
        {"action": "ACTION2", "requires_coordinates": False},
    ]
    assert visible["data"]["answer_template"]["semantic_claims"] == []
    assert calls == []


def test_passive_agenda_cannot_override_binding_gate(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    result = agent._run_python_tool(state_path, {"code": "result = virelai('agenda')"})
    payload = json.loads(result.content)
    visible = json.loads(payload["stdout"])
    assert visible["data"]["gate_id"] == "G0-ACTION-METADATA"
    assert "passive agenda is suspended" in visible["error"]
    assert calls == []


def test_visible_exact_g0_answer_opens_g1_without_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {"executed": True}
    answer = {
        "answer_id": "G0-bridge",
        "action_metadata": [
            {"action": "ACTION1", "requires_coordinates": False},
            {"action": "ACTION2", "requires_coordinates": False},
        ],
        "semantic_claims": [],
        "epistemic_limit": "Action effects remain unknown until they are observed through controlled probes.",
    }
    result = agent._run_python_tool(
        state_path,
        {"code": f"result = virelai('gate_answer', answer={answer!r})"},
    )
    payload = json.loads(result.content)
    visible = json.loads(payload["stdout"])
    assert visible["error"] is None
    assert visible["data"]["gate_id"] == "G1-EGO"
    assert visible["data"]["next_operation"] == "QUERY_NEXT_PROBE"
    assert visible["data"]["current_probe"]["probe_token"].startswith("P1_")
    assert agent._gate_transitioned_this_turn
    assert calls == []
    assert (tmp_path / "gated_gate_answers.jsonl").exists()


def test_rejected_g1_answer_shows_error_before_compact_corrective_template(tmp_path):
    agent, state_path = _agent(tmp_path)
    machine = agent._ensure_gate_machine(state_path)
    _capability(agent, state_path)
    # Production-shaped state setup: the bridge only needs to exercise its
    # rejection rendering here, so admit the two required opening observations
    # directly through the real gate machine.
    for transition_id in (1, 2, 3, 4):
        capability = machine.next_probe_capability()
        assert capability is not None
        probe = machine.validate_probe(
            {"probe_token": capability["probe_token"]}, capability["actions"]
        )
        machine.record_outcome(
            probe, {"transition_id": transition_id, "board_changed": True}
        )
    assert machine.gate_view()["status"] == "ANSWER_REQUIRED"

    rejected = {
        "answer_id": "G1-live-rejected-shape",
        "answer_kind": "embodied ego",
        "subjects": [{"description": "the moving composite pattern"}],
        "mechanism": "opaque actions translate the same directly controlled composite pattern",
        "action_laws": [
            {"action": "ACTION1", "effect": "moves the pattern through the visible field"}
        ],
        "evidence_refs": machine.gate_view()["answer_contract"]["evidence_refs"],
        "competing_models": ["the changes are remote rather than embodied"],
        "falsifier": "the declared subject does not change under the next action",
        "novel_prediction": {
            "action": "ACTION1",
            "predicate": "PATTERN_TRANSLATION",
            "scope.representation": "CELLS",
            "scope.cells": [[0, 1]],
            "expected_parameters": {"displacement": {"row": 0, "col": 1}},
            "because": "the effect repeated during the paired opening probes",
            "novelty": "the next test starts from a later visible state",
        },
    }
    result = agent._run_python_tool(
        state_path,
        {"code": f"result = virelai('gate_answer', answer={rejected!r})"},
    )
    payload = json.loads(result.content)
    visible_text = payload["stdout"]
    visible = json.loads(visible_text)
    assert "before_footprint" in visible["error"]
    assert visible["answer_template"]["novel_prediction"]["scope"]["representation"] == "CELLS"
    assert visible_text.index('"error"') < visible_text.index('"answer_template"')
    assert "truncation_note" not in payload


def test_next_probe_returns_compact_one_field_capability_for_action(tmp_path):
    agent, state_path = _agent(tmp_path)
    _capability(agent, state_path)
    result = agent._run_python_tool(state_path, {"code": "result = virelai('next_probe')"})
    payload = json.loads(result.content)
    visible = json.loads(payload["stdout"])
    probe = visible["data"]
    assert probe["probe_token"].startswith("P1_")
    assert probe["actions"] == [{"action": "ACTION1"}]
    assert probe["gate_id"] == "G1-EGO"
    assert "coverage" not in probe and "evidence_ids" not in probe


def test_probe_token_replay_is_rejected_before_second_environment_call(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {
        "executed": True,
        "action_num": 1,
        "transition_id": 1,
        "level": 1,
        "valid_actions": ["ACTION1", "ACTION2"],
        "board_changed": True,
    }
    capability = _capability(agent, state_path)
    code = (
        f"action({capability['actions']!r}, "
        f"decision={{'probe_token': {capability['probe_token']!r}}})"
    )
    first = agent._run_python_tool(state_path, {"code": code})
    second = agent._run_python_tool(state_path, {"code": code})
    assert first.step_executed
    assert not second.step_executed
    assert len(calls) == 1
    assert "already been used" in second.content


def test_wrong_action_does_not_consume_current_probe_token(tmp_path):
    agent, state_path = _agent(tmp_path)
    calls = []
    agent._step_env_callback = lambda payload: calls.append(payload) or {
        "executed": True,
        "action_num": 1,
        "transition_id": 1,
        "level": 1,
        "valid_actions": ["ACTION1", "ACTION2"],
        "board_changed": True,
    }
    capability = _capability(agent, state_path)
    decision = {"probe_token": capability["probe_token"]}
    wrong = agent._run_python_tool(
        state_path, {"code": f"action(['ACTION2'], decision={decision!r})"}
    )
    corrected = agent._run_python_tool(
        state_path, {"code": f"action({capability['actions']!r}, decision={decision!r})"}
    )
    assert not wrong.step_executed
    assert corrected.step_executed
    assert len(calls) == 1


def test_gate_audit_is_paginated_and_kept_out_of_compact_gate_view(tmp_path):
    agent, state_path = _agent(tmp_path)
    _capability(agent, state_path)
    compact_result = agent._run_python_tool(state_path, {"code": "result = virelai('gate')"})
    compact = json.loads(json.loads(compact_result.content)["stdout"])["data"]
    audit_result = agent._run_python_tool(
        state_path, {"code": "result = virelai('gate_audit', offset=0, limit=1)"}
    )
    audit = json.loads(json.loads(audit_result.content)["stdout"])["data"]
    assert "coverage" not in compact
    assert audit["page"] == {"offset": 0, "limit": 1}
    assert len(audit["coverage"]) <= 1


def test_inventory_query_is_paginated_and_visible_to_duck(tmp_path):
    agent, state_path = _agent(tmp_path)
    machine = agent._ensure_gate_machine(state_path)
    calls = []

    def inventory_view(*, offset, limit):
        calls.append((offset, limit))
        return {
            "schema": "virelai-g3-inventory-view-v1",
            "page": {"offset": offset, "limit": limit, "returned": 1, "total": 3},
            "items": [{"entity_id": "VE-001", "disposition": "CONFIRMED_LEVER"}],
            "truncated": True,
        }

    machine.inventory_view = inventory_view
    result = agent._run_python_tool(
        state_path, {"code": "result = virelai('inventory', offset=1, limit=1)"}
    )
    payload = json.loads(result.content)
    visible = json.loads(payload["stdout"])
    assert calls == [(1, 1)]
    assert visible["data"]["schema"] == "virelai-g3-inventory-view-v1"
    assert visible["data"]["items"] == [
        {"entity_id": "VE-001", "disposition": "CONFIRMED_LEVER"}
    ]
    assert visible["truncated"] is True


def test_entity_query_keyword_handle_is_executable_and_visible(tmp_path):
    agent, state_path = _agent(tmp_path)
    machine = agent._ensure_gate_machine(state_path)
    calls = []

    def entity_view(entity_id, *, offset, limit):
        calls.append((entity_id, offset, limit))
        return {
            "schema": "virelai-g3-entity-detail-v1",
            "entity_id": entity_id,
            "current": {"cells_page": [[4, 5]], "page": {"offset": offset, "limit": limit}},
        }

    machine.entity_view = entity_view
    result = agent._run_python_tool(
        state_path,
        {"code": "result = virelai('entity', id='E0008', offset=10, limit=25)"},
    )
    visible = json.loads(json.loads(result.content)["stdout"])

    assert calls == [("E0008", 10, 25)]
    assert visible["error"] is None
    assert visible["data"]["entity_id"] == "E0008"


def test_reaction_query_keyword_handle_is_executable_and_visible(tmp_path):
    agent, state_path = _agent(tmp_path)
    machine = agent._ensure_gate_machine(state_path)
    calls = []

    def reaction_view(entity_id):
        calls.append(entity_id)
        return {
            "schema": "virelai-g4-reaction-detail-v1",
            "anatomy": {"entity_id": entity_id, "coverage_complete": True},
        }

    machine.reaction_view = reaction_view
    result = agent._run_python_tool(
        state_path, {"code": "result = virelai('reaction', id='E0004')"}
    )
    visible = json.loads(json.loads(result.content)["stdout"])

    assert calls == ["E0004"]
    assert visible["error"] is None
    assert visible["data"]["anatomy"]["coverage_complete"] is True


def test_already_accepted_gate_answer_does_not_invite_resubmission(tmp_path):
    from inference.framework.virelai_gates import GateContractError

    agent, state_path = _agent(tmp_path)
    machine = agent._ensure_gate_machine(state_path)
    machine.submit_answer = lambda raw: (_ for _ in ()).throw(
        GateContractError(
            "G3 aggregate answer is already accepted; do not resubmit it. "
            "Follow the gate's next_operation."
        )
    )
    machine.gate_view = lambda: {
        "gate_id": "G3-LEVERS",
        "status": "SATISFIED",
        "next_operation": "WAIT_FOR_NEXT_TARGET",
        "answer_template": None,
    }
    result = agent._run_python_tool(
        state_path, {"code": "result = virelai('gate_answer', answer={})"}
    )
    visible = json.loads(json.loads(result.content)["stdout"])

    assert visible["answer_template"] is None
    assert visible["next_operation"] == "WAIT_FOR_NEXT_TARGET"
    assert visible["correction"] == (
        "The answer is already accepted. Do not resubmit it; follow next_operation."
    )


def test_automatic_gate_context_uses_compact_goal_view(tmp_path):
    agent, state_path = _agent(tmp_path)
    capability = _capability(agent, state_path)
    context = agent._gate_context_update(state_path)
    assert '"goal_card"' in context
    assert '"coverage": [' not in context
    assert '"current_probe"' in context
    assert capability["probe_token"] in context


def test_gated_action_boundary_drops_consumed_tool_dialogue(tmp_path):
    agent, state_path = _agent(tmp_path)
    capability = _capability(agent, state_path)
    messages = [
        {"role": "system", "content": "system"},
        {"role": "user", "content": "probe"},
        {
            "role": "tool",
            "content": json.dumps({"probe_token": capability["probe_token"]}),
        },
    ]

    retained = agent._history_after_turn(messages, tools=None, step_executed=True)

    assert retained == []


def test_executed_probe_joins_real_before_after_frames_and_exposes_evidence(tmp_path):
    agent, state_path = _agent(tmp_path)
    capability = _capability(agent, state_path)

    def step(payload):
        after = Frame(grid=((0, 0), (0, 1)), step=1, level=1)
        write_runtime_state(
            state_path,
            current_frame=after,
            history=[HistoryEntry(action="ACTION1", frame=after)],
        )
        return {
            "executed": True,
            "action_num": 1,
            "transition_id": 1,
            "level": 1,
            "state": "PLAYING",
            "valid_actions": ["ACTION1", "ACTION2"],
            "board_changed": True,
        }

    agent._step_env_callback = step
    result = agent._run_python_tool(
        state_path,
        {"code": (
            f"action({capability['actions']!r}, "
            f"decision={{'probe_token': {capability['probe_token']!r}}})"
        )},
    )
    assert result.step_executed
    action_result = json.loads(result.content)["result"]
    evidence_id = action_result["virelai_evidence_id"]
    observation = action_result["virelai_observation"]
    assert observation["changed_cell_count"] == 2
    assert observation["board_changed"]
    assert observation["before_frame_ref"].startswith("F-")
    assert observation["after_frame_ref"].startswith("F-")
    assert observation["remote_changed_cell_count"] is None

    outcomes = [
        json.loads(line)
        for line in (tmp_path / "gated_probe_outcomes.jsonl").read_text().splitlines()
    ]
    frames = [
        json.loads(line)
        for line in (tmp_path / "gated_probe_frames.jsonl").read_text().splitlines()
    ]
    assert outcomes[0]["evidence_id"] == evidence_id
    assert len(outcomes[0]["changed_cells"]) == 2
    assert {row["role"] for row in frames} == {"before", "after"}

    evidence_result = agent._run_python_tool(
        state_path, {"code": f"result = virelai('evidence', id={evidence_id!r})"}
    )
    evidence = json.loads(json.loads(evidence_result.content)["stdout"])["data"]
    assert evidence["evidence_id"] == evidence_id
    assert evidence["observation"]["changed_cell_count"] == 2
    assert "changed_cells" not in evidence["observation"]


def test_gated_system_prompt_states_ontology_and_does_not_leak_legacy_action_aliases():
    prompt = _build_system_prompt(
        tool_output_tokens=1024,
        virelai_enabled=True,
        virelai_gates_enabled=True,
    )
    assert "flipbook of observed integer-grid states" in prompt
    assert "A win is a platform-observed event" in prompt
    assert "connected by opaque actions" in prompt
    assert "A4 - The legal action roster supplies the opening control archetype" in prompt
    assert "A5 - A lever is a relational role" in prompt
    assert "# Cybernetic targeting system" in prompt
    assert "Work on exactly one binding epistemic target at a time" in prompt
    assert "action surface -> ego -> counter -> levers" in prompt
    assert "The pre-win objective is a stable physics grammar" in prompt
    assert "Do not begin by guessing a hidden winning state" in prompt
    assert "Binding opening protocol" in prompt
    assert "click every controller-enumerated visual object once" in prompt
    assert "drive that ego into contact with every controller-enumerated visual object" in prompt
    assert "binding target across ordinary approach moves" in prompt
    assert "declare CONTACT_ATTEMPT only" in prompt
    assert "smallest cell footprint first" in prompt
    assert "rank is only an experiment order" in prompt
    assert "virelai('next_probe')" in prompt
    assert "probe_token" in prompt
    assert "complete decision fields" not in prompt
    assert "what the goal likely is" not in prompt
    assert "infer the desired environment change" not in prompt
    assert "classify it as HUD/timer state" not in prompt
    assert "MOUSE" not in prompt and "LEFT" not in prompt


def test_gated_turn_prompt_keeps_attention_on_one_epistemic_target(tmp_path):
    agent, _ = _agent(tmp_path)
    prompt = agent._build_user_prompt(
        0,
        valid_actions=["ACTION1", "ACTION2"],
        current_frame=Frame(grid=((0, 1), (0, 0)), step=0, level=1),
    )
    assert "current gate is binding" in prompt
    assert "Do not search for or guess a winning objective" in prompt
    assert "Maintain a compact gate model" in prompt
    assert "`Gate model:`" in prompt
    assert "what the goal seems to be" not in prompt
    assert "against the current goal" not in prompt


def test_tool_agent_delivers_automatic_reset_from_runtime_history(tmp_path):
    class ResetSink:
        def __init__(self):
            self.outcomes = []

        def observe_system_reset(self, outcome):
            self.outcomes.append(outcome)
            return object()

    before = Frame(grid=((4, 4, 4),), step=50, level=1)
    after = Frame(grid=((7, 7, 7),), step=51, level=1)
    state_path = tmp_path / "tool_runtime_state.json"
    write_runtime_state(
        state_path,
        current_frame=after,
        history=[HistoryEntry(action="ACTION6(row=1, col=1)", frame=before),
                 HistoryEntry(action="RESET", frame=after)],
    )
    agent = ToolAgent(model="gpt-4o", virelai_gates_enabled=True)
    sink = ResetSink()
    agent._gate_machine = sink
    agent._current_valid_actions = ["ACTION6"]

    agent._reconcile_gate_resets(state_path)
    agent._reconcile_gate_resets(state_path)

    assert len(sink.outcomes) == 1
    outcome = sink.outcomes[0]
    assert outcome["transition_id"] == 51
    assert outcome["action"] == {"action": "RESET"}
    assert outcome["boundary_event"]["actor"] == "SYSTEM_RESET"
    assert len(outcome["changed_cells"]) == 3
