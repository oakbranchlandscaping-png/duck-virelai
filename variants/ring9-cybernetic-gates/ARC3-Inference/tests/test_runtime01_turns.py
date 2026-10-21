"""WO-RUNTIME-01 §1–§2, §8: every Duck turn ends in exactly one typed outcome, with no added model call.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Fail-first: on the base the endings below stop the game,
crash it, or retry without a bound; there is no typed outcome. Each test names the work order's acceptance case.
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest
import requests

from runtime01_support import Script, guarded_agent, ledger_rows, prose, read_only, refused
from inference.agent.tool_agent import _ToolDispatchResult
from inference.framework.solver import _turn_ends_game

INSPECT = "print(current_frame.step)"


def _run():
    return SimpleNamespace(solver_note=None, state="playing")


def _typed(result):
    return getattr(result, "turn_outcome", None), getattr(result, "recovery_reason", None)


def test_read_only_then_read_only_is_recoverable_with_no_extra_model_call(tmp_path, monkeypatch):
    """Interface 1 / WO 4: the second read-only response after the correction ends the turn as a recovery."""
    script = Script([INSPECT])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=read_only)
    agent._max_read_only_without_progress = 2
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "READ_ONLY_REPEAT")
    assert len(script.requests) == 3  # two read-only calls, the correction turn, and nothing after the halt
    assert _turn_ends_game(result, _run()) is False
    assert agent._controller.recovery is not None and agent._controller.recovery["reason"] == "READ_ONLY_REPEAT"


def test_two_no_tool_replies_do_not_crash_the_game(tmp_path, monkeypatch):
    """Interface 2 / WO 6: two replies without a tool call are a recovery, not ``fatal_failure``."""
    script = Script([prose])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "NO_TOOL_CALL")
    assert len(script.requests) == 2
    assert _turn_ends_game(result, _run()) is False  # on the base this raised "failed permanently"


def test_a_malformed_action_is_an_attempt_with_one_repair_then_a_recovery(tmp_path, monkeypatch):
    """Interface 3 / WO 2: a refused action is never read-only; one repair names the refusal, the call shape and
    the selected question; a second refusal ends the turn."""
    script = Script(["action(['ACTION6(row=18, col=17)'])"])
    dispatch = refused("MALFORMED_ACTION", "Gated mode accepts opaque ACTION<number> names only")
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION6"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "MALFORMED_ACTION")
    assert len(script.requests) == 2
    repair = [text for text in script.user_texts(-1) if "ACTION REPAIR" in text]
    assert len(repair) == 1
    assert "Gated mode accepts opaque ACTION<number> names only" in repair[0]
    assert "action([" in repair[0] and "question" in repair[0].lower()
    assert agent._read_only_calls_without_progress == 0  # never counted as inspection


def test_a_same_board_no_effect_refusal_is_action_refused(tmp_path, monkeypatch):
    """WO 3: the harness's R-8 refusal is ACTION_REFUSED, not malformed and not read-only."""
    script = Script(["action([{'action': 'ACTION6', 'row': 1, 'col': 1}])"])
    dispatch = refused("ACTION_REFUSED", "Blocked by the harness, not the game: this action changed nothing")
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION6"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "ACTION_REFUSED")


def test_a_python_error_that_ends_the_turn_is_python_error(tmp_path, monkeypatch):
    """Interface 4: the turn's last read-only call raised in the sandbox."""
    script = Script(["boom()"])
    agent, state_path = guarded_agent(
        tmp_path, monkeypatch, script,
        dispatch=lambda *_a: _ToolDispatchResult('{"error": "NameError: name \'boom\' is not defined"}'))
    agent._max_read_only_without_progress = 2
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "PYTHON_ERROR")


def test_a_model_timeout_is_a_recovery_and_never_a_retry(tmp_path, monkeypatch):
    """Interface 5 / WO 7: a timed-out request returns a typed recovery; nothing retries it in the turn."""
    script = Script([requests.ReadTimeout("read timed out")])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script)
    agent._yield_seconds = None
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"], request_timeout_seconds=900.0)
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "MODEL_TIMEOUT")
    assert len(script.requests) == 1
    assert _turn_ends_game(result, _run()) is False


def test_every_request_is_capped_by_the_turn_allowance(tmp_path, monkeypatch):
    """WO 7 / §8: with a 60 s turn clock no request may wait 900 s."""
    script = Script(["action(['ACTION1'])"])
    agent, state_path = guarded_agent(
        tmp_path, monkeypatch, script, dispatch=lambda *_a: _ToolDispatchResult("{}", step_executed=True))
    agent._yield_seconds = 60.0
    agent.analyze(state_path, 0, valid_actions=["ACTION1"], request_timeout_seconds=900.0)
    cap = script.kwargs[0].get("request_timeout_seconds")
    assert cap is not None and cap <= 60.0


def test_a_timeout_at_the_turn_cap_is_the_turn_clock(tmp_path, monkeypatch):
    script = Script([requests.ReadTimeout("read timed out")])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script)
    agent._yield_seconds = 60.0
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"], request_timeout_seconds=900.0)
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "TURN_CLOCK")


def test_a_failed_request_that_is_not_a_timeout_is_model_request_failed(tmp_path, monkeypatch):
    """Sol's ruling 1 (2026-10-20): a separate reason in the clock class."""
    script = Script([requests.ConnectionError("connection refused")])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "MODEL_REQUEST_FAILED")


def test_turn_clock_expiry_is_a_recovery_and_the_next_turn_is_a_commit_turn(tmp_path, monkeypatch):
    """WO 8, 5: an expired clock ends the turn without another model call; the next Duck prompt on the same question
    is the commit prompt, and its first read-only call is corrected at once."""
    script = Script([INSPECT])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=read_only)
    agent._yield_seconds = 1e-9
    first = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(first) == ("RECOVERABLE_NO_ACTION", "TURN_CLOCK")
    assert len(script.requests) == 0  # the clock was spent before any request: none is sent
    agent._yield_seconds = None
    agent._controller.recovery = None  # the controller turn consumed it (no machine in this fixture)
    second = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    commit_prompt = script.user_texts(0)[-1]  # this turn's prompt (earlier turns stay in the session's history)
    assert "COMMIT TURN" in commit_prompt
    assert "expand:" not in commit_prompt  # no exploratory section
    assert any("NO-PROGRESS TOOL GUARD" in text for text in script.user_texts(1))
    assert len(script.requests) == 2
    assert _typed(second) == ("RECOVERABLE_NO_ACTION", "READ_ONLY_REPEAT")


def test_an_explicit_decline_ends_the_turn_without_another_call(tmp_path, monkeypatch):
    """Interface 6 / WO 26-27."""
    script = Script(["virelai('decline', question_id='Q:L1:G1-EGO:LEVEL-1:CONTROL_LOCUS')"])
    agent, state_path = guarded_agent(
        tmp_path, monkeypatch, script, dispatch=lambda *_a: _ToolDispatchResult('{"data": {"declined": true}}',
                                                                               interaction_kind="DECLINE"))
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(result) == ("EXPLICIT_DECLINE", "DECLINED")
    assert len(script.requests) == 1


def test_an_admitted_duck_action_still_executes_unchanged(tmp_path, monkeypatch):
    """Interface 7 / WO 35: a successful path keeps every field it had, and is typed ACTION_EXECUTED."""
    script = Script(["action(['ACTION1'])"])
    agent, state_path = guarded_agent(
        tmp_path, monkeypatch, script, dispatch=lambda *_a: _ToolDispatchResult("{}", step_executed=True))
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert result.step_executed and not result.controlled_stop and not result.fatal_failure
    assert _typed(result) == ("ACTION_EXECUTED", "")
    assert agent._controller.recovery is None


def test_an_accepted_gate_answer_is_gate_progress(tmp_path, monkeypatch):
    script = Script(["virelai('gate_answer', answer={})"])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script)

    def dispatch(*_args):
        agent._gate_transitioned_this_turn = True
        return _ToolDispatchResult("{}", interaction_kind="GATE_TRANSITION")

    monkeypatch.setattr(agent, "_dispatch_tool", dispatch)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert result.yielded_control
    assert _typed(result) == ("GATE_PROGRESS", "")


def test_a_contract_repair_loop_is_contract_repair_exhausted(tmp_path, monkeypatch):
    script = Script(["virelai('gate_answer', answer={})"])
    rejected = _ToolDispatchResult('{"error": "bad"}', interaction_kind="CONTRACT_REPAIR",
                                   repair_signature="same", repair_error="bad")
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=lambda *_a: rejected)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert _typed(result) == ("RECOVERABLE_NO_ACTION", "CONTRACT_REPAIR_EXHAUSTED")


def test_an_unexpected_analyzer_exception_is_explicitly_unrecoverable(tmp_path, monkeypatch):
    """WO §1: an invariant violation stays unrecoverable, distinctly and testably."""
    script = Script([ValueError("an invariant broke")])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script)
    from inference.agent import turn_recovery

    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"])
    assert result is None  # the analyzer's contract is unchanged on this path (Sol's ruling 3: byte-identical)
    assert turn_recovery.classify(agent, result) == ("UNRECOVERABLE", "ANALYZER_EXCEPTION")
    assert ledger_rows(state_path)[-1]["turn_outcome"] == "UNRECOVERABLE"
    with pytest.raises(RuntimeError):
        _turn_ends_game(result, _run())  # None: "Analyzer did not return a result.", as on the base


def test_a_stop_request_is_terminal(tmp_path, monkeypatch):
    script = Script([INSPECT])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=read_only)
    result = agent.analyze(state_path, 0, valid_actions=["ACTION1"], should_stop=lambda: True)
    assert _typed(result) == ("TERMINAL", "STOP_REQUESTED")
    assert agent._controller.recovery is None


def test_the_turn_ledger_v2_records_the_operational_chain(tmp_path, monkeypatch):
    """WO 30: question, ownership, typed outcome, reason, counter, commit status, timing and the timeout bound."""
    script = Script([INSPECT])
    agent, state_path = guarded_agent(tmp_path, monkeypatch, script, dispatch=read_only)
    agent._max_read_only_without_progress = 2
    agent._yield_seconds = 60.0
    agent.analyze(state_path, 0, valid_actions=["ACTION1"], request_timeout_seconds=900.0)
    row = ledger_rows(state_path)[-1]
    assert row["schema"] == "virelai-turn-ledger-v2"
    assert row["executor"] == "DUCK" and row["turn_outcome"] == "RECOVERABLE_NO_ACTION"
    assert row["recovery_reason"] == "READ_ONLY_REPEAT" and row["failure_class"] == "HARD"
    assert row["recovery_count"] == 1 and row["commit_turn"] is False
    assert "question_id" in row and "owned_because" in row
    assert row["request_count"] == 3 and all(bound <= 60.0 for bound in row["request_timeouts"])
    assert isinstance(row["wall_seconds"], float)


def test_a_rate_limit_retry_never_outlives_the_request_cap(monkeypatch):
    """§8: the 429 retry loop inside one request stops at the request's own bound."""
    from inference.agent.tool_agent import ToolAgent

    agent = ToolAgent(model="fixture-model", provider="openai", base_url="https://fixture.invalid/v1",
                      api_key="fixture", virelai_gates_enabled=True)
    posts = []
    sleeps = []

    class Limited:
        status_code = 429
        headers = {"Retry-After": "5"}
        text = "rate limited"

        def json(self):
            return {"error": {"code": "rate_limit"}}

        def raise_for_status(self):
            raise requests.HTTPError("429 Too Many Requests")

    monkeypatch.setattr("inference.agent.tool_agent.requests.post", lambda *a, **k: posts.append(k) or Limited())
    monkeypatch.setattr("inference.agent.tool_agent.time.sleep", lambda seconds: sleeps.append(seconds))
    with pytest.raises(requests.RequestException):
        agent._chat_completion([{"role": "user", "content": "x"}], tools=None, request_timeout_seconds=1.0)
    assert len(posts) == 1 and sleeps == []  # a 5 s retry cannot fit a 1 s bound


def test_a_transition_view_error_gains_one_supported_access_hint(tmp_path, monkeypatch):
    """WO §9: an error naming TransitionView keeps its text and gains the one hint; other errors are unchanged."""
    import json

    from inference.agent.runtime_state import Frame, HistoryEntry, write_runtime_state

    agent, state_path = guarded_agent(tmp_path, monkeypatch, Script([]))
    frame = Frame(grid=((0, 0), (0, 1)), step=1, level=1)
    write_runtime_state(state_path, current_frame=frame, history=[HistoryEntry(action="ACTION1", frame=frame)])
    error = "last_transition.get('state')"  # public-25: Duck read the documented view as a mapping
    payload = json.loads(agent._run_python_tool(state_path, {"code": error}).content)
    assert "'TransitionView' object has no attribute 'get'" in payload["error"]
    assert payload["error"].count("HINT: a TransitionView is an object with exactly the fields") == 1
    other = json.loads(agent._run_python_tool(state_path, {"code": "{}['x']"}).content)
    assert "HINT" not in other["error"]
