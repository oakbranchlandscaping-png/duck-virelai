"""Memory stage M-0 (R9-R06): the replay harness, the record index, the memory store, the ledger.

Author: Claude (Alpha build seat), 2026-09-28. DESIGN_VIRELAI_MEMORY_v1 §5.1, §7, §10 (T2, T9).

Nothing here changes what Duck sees or does. These tests pin the instruments every later memory
stage is measured with:

- the real ft09 guided-v2 record (121 transitions, Kaggle 2026-09-28) replays through the gate
  machine and reproduces the card that crashed the run (25,502 characters) — the regression anchor
  the slot-built card (stage M-1) must beat;
- the record index and the read-only memory store recall a subject's whole file, bounded;
- the turn ledger records what each Duck turn was shown and what it cost;
- Duck's and the controller's gate actions share one recording path that names who acted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from inference.agent.runtime_state import Frame, write_runtime_state
from inference.agent.tool_agent import ToolAgent, _ChatCompletionResult
from inference.framework.gate_card import render_binding_gate_context
from inference.framework.memory_store import MAX_PAGE, MemoryStore
from inference.framework.record_replay import load_record, replay

V2_RECORD = Path(__file__).parent / "fixtures" / "ft09_kaggle_v2_record.json.gz"
RESPONSE_CEILING = 8_000  # characters; every memory-store response is bounded below this


@pytest.fixture(scope="module")
def v2():
    return replay(load_record(V2_RECORD))


def test_the_real_v2_record_replays_through_the_gate_machine(v2):
    assert v2.stopped is None
    assert v2.steps_replayed == 121
    assert v2.answers_used == 5  # the G2 label and four G3 dossiers, all accepted as recorded
    counter = v2.machine.target_journal.active_product("G2-COUNTER").payload["counter_model"]
    assert counter["trigger"] == "EFFECTIVE_TRANSITIONS_ONLY"
    witnesses = [
        row["transition_id"] for row in v2.machine.transition_index
        if row["disposition"] == "LOCAL_LEVER_WITNESS"
    ]
    assert witnesses == list(range(112, 122))  # five levers, each witnessed then confirmed


def test_regression_anchor_the_card_that_crashed_v2_is_now_within_budget(v2):
    """T2, amended by R9-R07 (memory stage M-1).

    At R9-R06 this replay reproduced the card that crashed the Kaggle run exactly: 25,502
    characters after transition 121 (G3, answer required), against the 24,000 guard. The
    slot-built card replaces it; the same state now renders within the card budget.
    """
    from inference.framework.card_builder import CARD_BUDGET

    final = v2.samples[-1]
    assert (final.after_transition, final.gate_id, final.status) == (121, "G3-LEVERS", "ANSWER_REQUIRED")
    assert final.chars < CARD_BUDGET < 24_000
    assert all(sample.chars < CARD_BUDGET for sample in v2.samples)


def test_the_harness_measures_the_production_renderer(tmp_path):
    state_path = tmp_path / "gated_tool_runtime_state.json"
    write_runtime_state(state_path, current_frame=Frame(grid=((0, 1), (0, 0)), step=0, level=1), history=[])
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True)
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["ACTION1", "ACTION2"]
    machine = agent._ensure_gate_machine(state_path)
    card = render_binding_gate_context(machine)
    context = agent._gate_context_update(state_path)
    # WO-L2a library view (2026-10-11): the measured card bytes come first and unchanged; the library
    # digest follows as its own budgeted section, built from the validated live library.
    assert context.startswith(card)
    assert context[len(card):].startswith("\nVIRELAI LIBRARY (read-only")


def test_every_recorded_transition_is_indexed_once_and_sparse(v2):
    ids = [row["transition_id"] for row in v2.machine.transition_index]
    assert ids == list(range(1, 122))
    click = next(row for row in v2.machine.transition_index if row["transition_id"] == 112)
    assert click["gate_id"] == "G3-LEVERS"
    assert click["acted_site"] == {"row": 36, "col": 36}
    assert len(click["changed"]) == 38  # 36 tile cells plus the 2 bar cells, lossless and sparse


def test_memory_store_recalls_a_subject_file_and_a_site_history(v2):
    store = MemoryStore(v2.machine)
    assert [row["gate_id"] for row in store.products()["rows"]] == [
        "G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER",
    ]
    site = store.site(36, 36)
    assert [row["transition_id"] for row in site["rows"]] == [113, 112, 55]
    assert [row["gate_id"] for row in site["rows"]] == ["G3-LEVERS", "G3-LEVERS", "G2-COUNTER"]
    subject = store.subject("E0053")
    assert subject["lifecycle_state"] == "G4-READY"
    assert len(subject["confirmations"]) == 1
    assert len(subject["dossiers"]) == 1
    assert subject["aimed_transitions"]["total"] == 3
    assert store.subject("E9999") is None


def test_memory_store_responses_are_bounded_and_paged(v2):
    store = MemoryStore(v2.machine)
    product = store.product("G2-COUNTER")
    assert product["fields"]["state_identity"]["omitted"] is True  # 13k characters, not inlined
    field = store.product("G2-COUNTER", field="counter_model")
    assert field["value"]["trigger"] == "EFFECTIVE_TRANSITIONS_ONLY"
    page = store.transitions(offset=100, limit=500)
    assert (page["total"], page["limit"], len(page["rows"]), page["remaining"]) == (121, MAX_PAGE, 21, 0)
    for response in (
        store.products(), product, field, page, store.site(36, 36), store.subject("E0053"),
        store.transition(112), store.transitions(),
    ):
        assert len(json.dumps(response, default=str)) < RESPONSE_CEILING


def test_memory_store_is_read_only(v2):
    before_card = render_binding_gate_context(v2.machine)
    before_index = json.dumps(v2.machine.transition_index)
    store = MemoryStore(v2.machine)
    for recall in (
        store.products, lambda: store.product("G2-COUNTER", field="mask_law"), store.transitions,
        lambda: store.transition(57), lambda: store.site(36, 44), lambda: store.subject("E0054"),
    ):
        recall()
    assert render_binding_gate_context(v2.machine) == before_card
    assert json.dumps(v2.machine.transition_index) == before_index


def _ledger_agent(tmp_path, monkeypatch):
    state_path = tmp_path / "tool_runtime_state.json"
    write_runtime_state(state_path, current_frame=Frame(grid=((0, 0), (0, 0)), step=0, level=1), history=[])
    monkeypatch.setattr("inference.agent.tool_agent._LOCAL_ANALYZER_MAX_NO_TOOL_RESPONSES", 2)
    agent = ToolAgent(
        model="fixture-model", provider="openai", base_url="https://fixture.invalid/v1",
        api_key="fixture", virelai_gates_enabled=True,
    )
    tool = [{"type": "function", "function": {
        "name": "python", "description": "fixture", "parameters": {"type": "object", "properties": {}},
    }}]
    monkeypatch.setattr(agent, "_ensure_session", lambda _path: None)
    monkeypatch.setattr(agent, "_tools", lambda _path: tool)
    monkeypatch.setattr(agent, "_automatic_virelai_update", lambda *args, **kwargs: "")
    monkeypatch.setattr(agent, "_controller_focus_update", lambda: "FOCUS")
    monkeypatch.setattr(agent, "_gate_context_update", lambda _path: "G" * 1200)
    monkeypatch.setattr(agent, "_build_user_prompt", lambda *args, **kwargs: "P" * 300)
    monkeypatch.setattr(agent, "_build_user_message", lambda prompt, _frame: {"role": "user", "content": prompt})
    return agent, state_path


def test_turn_ledger_records_the_card_sections_and_the_cost_of_the_turn(tmp_path, monkeypatch):
    """T9 (first half): one row per Duck turn, with what it was shown and what it cost."""
    agent, state_path = _ledger_agent(tmp_path, monkeypatch)
    monkeypatch.setattr(agent, "_chat_completion", lambda messages, **_kw: _ChatCompletionResult(
        message={"role": "assistant", "content": "thinking without a tool call"},
        finish_reason="stop",
        usage={"prompt_tokens": 4321, "completion_tokens": 555, "total_tokens": 4876},
    ))
    agent.analyze(state_path, 7, valid_actions=["ACTION6"], analysis_step=3)
    json.loads(state_path.read_text())  # the runtime state file is untouched by the ledger
    rows = [json.loads(line) for line in (tmp_path / "tool_runtime_state_turn_ledger.jsonl").read_text().splitlines()]
    assert len(rows) == 1
    row = rows[0]
    assert row["schema"] == "virelai-turn-ledger-v2"  # WO-RUNTIME-01: v2 adds the typed outcome fields
    assert (row["executor"], row["analysis_step"], row["action_num"]) == ("DUCK", 3, 7)
    assert row["section_chars"] == {
        "prompt_body": 300, "automatic_update": 0, "controller_focus": 5, "gate_card": 1200,
        "controller_handoff": 0,
    }
    assert row["card_chars"] == 1505
    assert row["request_count"] == 2
    assert (row["prompt_tokens_max"], row["generated_tokens"]) == (4321, 1110)
    assert row["step_executed"] is False
    assert row["gate_before"] == row["gate_after"] == "G0-ACTION-METADATA"


def test_turn_ledger_counts_recall_queries_and_envelopes_name_who_acted(tmp_path):
    from inference.agent.turn_ledger import TurnLedger

    state_path = tmp_path / "gated_tool_runtime_state.json"
    write_runtime_state(state_path, current_frame=Frame(grid=((0, 1), (0, 0)), step=0, level=1), history=[])
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True)
    agent._ensure_session(state_path)
    agent._current_valid_actions = ["ACTION1", "ACTION2"]
    agent._turn_ledger = TurnLedger(
        tmp_path / "ledger.jsonl", analysis_step=1, action_num=0, executor="DUCK",
        gate_before="G0-ACTION-METADATA", sections={},
    )
    agent._run_python_tool(state_path, {"code": "result = virelai('gate')"})
    assert agent._turn_ledger._row["recall_queries"] == ["gate"]

    machine = agent._ensure_gate_machine(state_path)
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
    agent._step_env_callback = lambda payload: {
        "executed": True, "action_num": 1, "transition_id": 1, "level": 1,
        "valid_actions": ["ACTION1", "ACTION2"], "board_changed": True,
    }
    decision = repr({"probe_token": capability["probe_token"]})
    result = agent._run_python_tool(
        state_path, {"code": f"action({capability['actions']!r}, decision={decision})"}
    )
    assert result.step_executed
    envelopes = [
        json.loads(line)
        for line in (tmp_path / "gated_probe_envelopes.jsonl").read_text().splitlines()
    ]
    assert [row["executor"] for row in envelopes] == ["DUCK"]
    assert [row["transition_id"] for row in machine.transition_index] == [1]
