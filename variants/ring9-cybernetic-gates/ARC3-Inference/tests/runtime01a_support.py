"""WO-RUNTIME-01A: the production solver session on the ft09 world, scripted the way each canary world ended.

Author: Claude (Alpha build seat), 2026-10-22. Base ``8b47c73``. Interface:
``INTERFACE_WO_RUNTIME_01A_v1_2026-10-22`` §3 (the diagnosis) and §5 (the reproductions).

Nothing here is production code. ``Session`` is ``solver._HarnessGameSession`` over ``test_g3_directed_click``'s ft09
game: the real ``ToolAgent`` turn loop and settlement, the real controller, the real ``play`` loop and its
``_turn_ends_game``, the real journal, seal and H2 world-model write. Only the model is scripted (``Director``), and,
where a canary world's state cannot arise in ft09, one documented piece of scripted state:

* contract repair (dc22, ka59, sc25): Duck's calls at G4.2 follow the exported transcripts: a rejected gate answer,
  then, in that turn or the next, an executed press under the open repair obligation; dc22's step after the chapter
  close is handed to Duck, as its NAV ``no evidence-bounded route`` was (scripted ownership, one step);
* D22 (g50t, re86, sc25, wa30): at the canary's gate, the gate offers no probe, answer or end (``legal_move_status``)
  and owns nothing (``next_owned_step``), with the canary's own reason texts; Duck's turn then meets the analyzer's
  no-legal-move watchdog, as the exported ``TURN OUTCOME`` rows record.
"""
from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME
from inference.agent.tool_agent import _ChatCompletionResult

FIXTURES = Path(__file__).parent / "fixtures"
CANARY = FIXTURES / "runtime01a_canary_rows.json"
G2, G3, G42 = "G2-COUNTER", "G3-LEVERS", "G4.2-LEVER-ORBITS"
REPAIR_PROMPT = "GATE CONTRACT REPAIR"
BAD_ANSWER = "print(virelai('gate_answer', answer={'answer_id': 'X'}))"
PRESS = ("cap = virelai('next_probe')['data'] or {}\n"  # the gate's GUIDED capability: press one listed lever
         "levers = [l for l in (cap.get('target') or {}).get('levers') or () if l['status'] != 'CLOSED_UNRESOLVED']\n"
         "if levers:\n"
         "    pick = next((l for l in levers if l['status'] == 'CONFIRMED_AWAITING_EXPLANATION'), levers[0])\n"
         "    c = pick['click']\n"
         "    print(action([{'action': c['action'], 'row': c['row'], 'col': c['col']}],"
         " decision={'probe_token': cap['probe_token'], 'intent': 'press ' + pick['entity_id']}))\n"
         "else:\n"
         "    print(virelai('decline', question_id={question!r}))")  # elsewhere: an explicit, typed decline
READS = ("print(current_frame.step)", "print(len(history))", "print(valid_actions)")
AFTER_DECISIVE = 3  # actions the run may take after the decisive turn: enough to show play continues


def canary_rows() -> dict[str, Any]:
    """The pinned canary evidence (sha256 of every exported line it quotes is checked by the tests)."""
    return json.loads(CANARY.read_text())


def line_sha(row: dict[str, Any]) -> str:
    return hashlib.sha256(row["line"].encode()).hexdigest()


def _call(code: str, index: int) -> _ChatCompletionResult:
    return _ChatCompletionResult(
        message={"role": "assistant", "content": None, "tool_calls": [{
            "id": f"call-{index}", "type": "function",
            "function": {"name": "python", "arguments": json.dumps({"code": code})}}]},
        finish_reason="tool_calls", model_id="fixture-model")


def _last_user(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            content = message.get("content")
            return content if isinstance(content, str) else json.dumps(content)
    return ""


class Session:
    """The production session on ft09 with a scripted Duck; ``play()`` runs it to its own end."""

    def __init__(self, tmp_path: Path, pattern: str, monkeypatch: Any, reason: str | None = None) -> None:
        from inference.agent.tool_agent import ToolAgent
        from inference.framework.solver import HarnessSolver, _HarnessGameSession
        from test_g3_directed_click import _Ft09Game

        self.pattern, self.tmp, self.reason = pattern, tmp_path, reason  # reason: the canary's own owned_because
        self.solver = HarnessSolver(virelai_mode="gated")
        self.solver.job_dir = tmp_path
        self.solver.max_actions_per_game = 400  # a bound; the director ends the run sooner
        game = _Ft09Game()
        self.stem = self.solver._run_stem(game.game_run.game_id, 0)
        self.agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                               controller_executor_enabled=True, provenance_enabled=True)
        self.agent._ensure_session = lambda _path: None
        self.agent._controller.g3_choice_handoff = False
        state_path = self.solver._artifacts_dir() / f"{self.stem}_{RUNTIME_STATE_FILENAME}"
        self.session = _HarnessGameSession(
            solver=self.solver, game=game, analyzer=self.agent, game_index=0, pass_index=0, state_path=state_path,
            transcript_path=tmp_path / "t.txt", analysis_html_relpath="a.html", stop_event=threading.Event(),
            viewer_data_path=tmp_path / "v.json")
        self.director = Director(self)
        self.agent._chat_completion = self.director
        real = self.agent._ensure_gate_machine

        def ensure(path: Path) -> Any:  # scripted state: the orientation turn is behind the run (PlayRun.to_play)
            machine = real(path)
            if machine is not None:
                machine.annotations.oriented = True
                self.director.attach(machine)
            return machine

        self.agent._ensure_gate_machine = ensure
        from inference.framework import controller_executor

        owned = controller_executor.next_owned_step
        monkeypatch.setattr(controller_executor, "next_owned_step",
                            lambda machine, *a, **k: self.director.owned(machine, owned(machine, *a, **k)))

    # ---- what the run left behind ----------------------------------------------------------------------------

    def play(self) -> "Session":
        self.session.play()
        return self

    @property
    def state_path(self) -> Path:
        return self.session.state_path

    def rows(self, suffix: str) -> list[dict[str, Any]]:
        path = self.state_path.with_name(f"{self.stem}{suffix}")
        return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []

    def journal(self) -> list[dict[str, Any]]:
        """The journal's events (the seal record left out)."""
        return [row for row in self.rows("_provenance.jsonl") if row.get("record") == "EVENT"]

    def ledger(self) -> list[dict[str, Any]]:
        return self.rows("_turn_ledger.jsonl")

    def model_path(self) -> Path:
        return self.tmp / "virelai" / self.stem / "world_model.json"

    def model(self) -> dict[str, Any]:
        return json.loads(self.model_path().read_text())

    def note(self) -> str | None:
        return self.session.game.game_run.solver_note


class Director:
    """The scripted Duck (and the one-step scripted ownership) for one canary pattern."""

    def __init__(self, run: Session) -> None:
        self.run = run
        self.machine: Any = None
        self.requests = 0
        self.turns: dict[str, int] = {}  # Duck turns per question
        self._turn_id: int | None = None
        self.closed: str | None = None  # the first closed G4.2 chapter's lever
        self.second: str | None = None  # the next question Duck explains after it
        self.decisive_step: int | None = None  # the analysis step of the turn the canary world ended on
        self.forced = False
        self.dead_end_turns = 0
        self.entered: int | None = None  # the step at which the D22 gate was first seen
        self.d22 = run.pattern.startswith("D22")
        self.d22_gate = {"D22_G2": G2, "D22_G3": G3, "D22_G2_END": G2}.get(run.pattern)

    def attach(self, machine: Any) -> None:
        if self.machine is machine:
            return
        self.machine = machine
        if self.d22:
            real = machine.legal_move_status

            def legal() -> dict[str, Any]:
                if self.dead_end():
                    return {"gate_id": machine.gate_id, "legal": False,
                            "reason": "WAIT_FOR_REPRESENTATION_OR_NEW_ACTION offers no probe, answer or end"}
                return real()

            machine.legal_move_status = legal

    def dead_end(self) -> bool:
        """At the canary's gate, after the gate's own first executed step (the canary's dead ends followed G2's pilot
        or demonstration probes and G3's sweep): no probe, answer or end until the gate is closed."""
        machine = self.machine
        if machine is None or machine.gate_id != self.d22_gate \
                or machine.target_journal.active_product(self.d22_gate) is not None:
            return False
        step = int(machine.observed_through_step or 0)
        self.entered = step if self.entered is None else self.entered
        return step > self.entered

    def owned(self, machine: Any, step: Any) -> Any:
        from inference.framework.controller_executor import DUCK, OwnedStep

        if self.d22 and self.dead_end():
            return OwnedStep(owner=DUCK, gate_id=machine.gate_id, reason=self.run.reason or (
                "G2 offers no active target or exact counter probe" if machine.gate_id == G2
                else "G3 NAV needs an answer or has no active target"))
        self._note_closure()
        if self.run.pattern == "dc22" and self.closed and not self.forced and machine.gate_id == G42:
            self.forced = True  # scripted ownership: the step after the close is Duck's (dc22's NAV route gap)
            return OwnedStep(owner=DUCK, gate_id=G42, reason="no evidence-bounded route to the next lever")
        return step

    # ---- the scripted model -----------------------------------------------------------------------------------

    def __call__(self, messages: list[dict], **_kwargs: Any) -> _ChatCompletionResult:
        self.requests += 1
        turn = getattr(self.run.agent, "_duck_turn", None) or {}
        question = str(turn.get("question_id") or "")
        if id(turn) != self._turn_id:
            self._turn_id = id(turn)
            self.turns[question] = self.turns.get(question, 0) + 1
        self._note_closure()
        code = self._decide(question, REPAIR_PROMPT in _last_user(messages))
        return _call(code.replace("{question!r}", repr(question)) if code is PRESS else code, self.requests)

    def _note_closure(self) -> None:
        from inference.framework import chapter_closure

        adapter = (getattr(self.machine, "_adapters", None) or {}).get(G42)
        if self.closed is None and adapter is not None and chapter_closure.closed(adapter):
            self.closed = next(iter(chapter_closure.closed(adapter)))

    def _decisive(self) -> str:
        if self.decisive_step is None:
            self.decisive_step = int(self.run.session.analysis_step)
            self.run.solver.max_actions_per_game = self.run.session.action_count + AFTER_DECISIVE
        return PRESS

    def _decide(self, question: str, repair: bool) -> str:
        if self.decisive_step is not None:
            return PRESS
        if self.d22:
            return self._dead_end_call()
        if not question.endswith(":ORBIT"):
            return PRESS
        if self.closed is None or f":{self.closed}:" in question:
            return BAD_ANSWER  # a rejected gate answer, until the HARD budget closes this chapter
        if self.run.pattern == "dc22":
            return self._decisive()  # the step after the close, under the closed chapter's open obligation
        self.second = self.second or question
        if self.run.pattern == "ka59":
            return self._decisive() if repair else BAD_ANSWER  # rejected, then an executed press in the same turn
        return self._decisive() if self.turns[question] >= 2 else BAD_ANSWER  # sc25: the next turn presses

    def _dead_end_call(self) -> str:
        if not self.dead_end():
            if self.run.pattern == "D22_G2_END":
                return PRESS
            self._decisive()
            return PRESS
        self.dead_end_turns += 1
        if self.run.pattern == "D22_G2_END" and self.dead_end_turns >= len(READS):
            self.run.session.stop_event.set()  # the run ends right after the no-legal-move outcome
        return READS[(self.dead_end_turns - 1) % len(READS)]


__all__ = ["BAD_ANSWER", "CANARY", "G2", "G3", "G42", "PRESS", "Session", "canary_rows", "line_sha"]
