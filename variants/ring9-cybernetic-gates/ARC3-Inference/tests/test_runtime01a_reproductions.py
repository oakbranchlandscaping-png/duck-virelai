"""WO-RUNTIME-01A §5: the seven canary worlds that still ended badly, reproduced fail-first through the production session.

Author: Claude (Alpha build seat), 2026-10-22. Base ``8b47c73``. Interface: ``INTERFACE_WO_RUNTIME_01A_v1_2026-10-22``
§2 and §3 (the diagnosis), §5 (these tests). Labels, as Sol ruled for the Runtime-01 public stops: **ledger-faithful
scripted reproductions**, not frame replays (the export holds no frames of these worlds). Each runs
``solver._HarnessGameSession.play()`` on the ft09 world (``runtime01a_support.Session``) and follows the typed sequence
of its world's exported rows, pinned by sha256 in ``fixtures/runtime01a_canary_rows.json``:

* dc22, ka59, sc25: on the base each ends the game ``controlled_stop: contract_repair_loop`` on a turn that executed
  an admitted action under an open repair obligation; after the build the turn is ``ACTION_EXECUTED`` and play goes on;
* g50t, re86, sc25, wa30: on the base the watchdog close cites no recovery check, the journal fails audit-v3 rule 5
  and the provenance is ``OPEN / INCOMPLETE``; after the build the close cites its checks and the journal seals.

Every reproduction then requires the finalization invariant (WO §4.3): a sealed journal, a ``SEALED / COMPLETE``
provenance chapter with ``journal_check`` ``RECONCILED``, a model that reads back, a byte-identical second compilation
and an idempotent reseal.
"""
from __future__ import annotations

import json

import pytest

from runtime01a_support import G2, G3, G42, Session, canary_rows, line_sha
from inference.framework import audit_journal as aj

CANARY = canary_rows()
STOP = "controlled_stop: contract_repair_loop"


def _typed(row: dict) -> tuple:
    return (row["operation"], row["event"], row["disposition"], row["executor"], (row["reason"] or {}).get("code"))


def _pinned(rows: list[dict]) -> list[dict]:
    for row in rows:
        assert line_sha(row) == row["sha256"], row["source"]
    return [json.loads(row["line"]) for row in rows]


def _contains_in_order(haystack: list, needle: list) -> bool:
    position = 0
    for item in haystack:
        if position < len(needle) and item == needle[position]:
            position += 1
    return position == len(needle)


def _sealed_and_complete(run: Session) -> dict:
    """The finalization invariant: sealed, complete, reconciled, readable, deterministic, idempotent."""
    from inference.framework import world_model_v2 as wm

    assert run.agent._provenance.failed == ""
    journal_bytes = run.state_path.with_name(f"{run.stem}_provenance.jsonl").read_bytes()
    assert aj.read_journal_bytes(journal_bytes).status == "SEALED"
    model = run.model()
    chapter = model["provenance"]
    assert chapter["phase"] == "H2"  # the final write, never an interim model
    assert (chapter["integrity"], chapter["completeness"], chapter["reasons"]) == ("SEALED", "COMPLETE", [])
    assert chapter["reconciliation"]["findings"] == [] and chapter["writer_failure"] is None
    assert model["manifest"]["journal_check"] == "RECONCILED"
    assert wm.read_world_model(model) is not None  # write, then read back
    first = run.model_path().read_bytes()
    run.session._write_l2a_world_model(final=True)  # a second compilation from the same state
    assert run.model_path().read_bytes() == first
    assert run.agent._provenance.seal() is False  # already sealed: resealing changes nothing
    assert run.state_path.with_name(f"{run.stem}_provenance.jsonl").read_bytes() == journal_bytes
    assert wm.canonical_bytes(wm.seal(model)) == wm.canonical_bytes(model)
    return model


# ---- contract repair: dc22, ka59, sc25 ----------------------------------------------------------------------------

def _repair_rows(run: Session) -> tuple[list[dict], dict, dict]:
    """The one exhaustion close of lever A and the recovery that names it."""
    journal = run.journal()
    closes = [row for row in journal if (row["operation"], row["event"]) == ("GATE", "CLOSE")]
    first = run.director.closed
    lever_a = [row for row in closes if row["refs"]["subject"] == first]
    assert len(lever_a) == 1, closes
    (close,) = lever_a
    recoveries = [row for row in journal if row["event"] == "RECOVERY"
                  and (row["submitted"] or {}).get("resulting_event_id") == close["event_id"]]
    assert len(recoveries) == 1
    return journal, close, recoveries[0]


@pytest.mark.parametrize("world", ["dc22", "ka59", "sc25"])
def test_contract_repair_world_continues_through_a_typed_bounded_close(tmp_path, monkeypatch, world):
    expected = CANARY["contract_repair"][world]
    _pinned(expected["journal"])
    ledger_rows = _pinned(expected["ledger"])
    assert ledger_rows[-1]["turn_outcome"] == "ACTION_EXECUTED" and ledger_rows[-1]["outcome"] == "step"
    run = Session(tmp_path, world, monkeypatch).play()
    director = run.director
    assert director.decisive_step is not None and director.closed is not None
    # the canary's end is gone: the run ends at its action cap, never on the repair stop
    assert not str(run.note() or "").startswith(STOP), run.note()
    assert expected["finished_note"].startswith(STOP)  # what the base did, in the canary and here
    ledger = run.ledger()
    decisive = [row for row in ledger if row["analysis_step"] == director.decisive_step]
    assert [(row["executor"], row["turn_outcome"], row["step_executed"]) for row in decisive] == [
        ("DUCK", "ACTION_EXECUTED", True)]
    assert any(row["analysis_step"] > director.decisive_step for row in ledger)  # play resumed after it
    # one typed exhaustion of lever A, one close of that chapter only, one recovery naming it
    journal, close, recovery = _repair_rows(run)
    by_id = {row["event_id"]: row for row in journal}
    assert close["submitted"]["scope"] == "CHAPTER" and close["gate_id"] == G42
    assert (close["reason"]["code"], close["submitted"]["class"], close["submitted"]["budget"]) == (
        "HARD_BUDGET_SPENT", "HARD", 2)
    cited = [by_id[item] for item in close["submitted"]["history"]]
    assert [(row["event"], row["reason"]["code"], row["refs"]["question_id"]) for row in cited] == [
        ("OUTCOME", "CONTRACT_REPAIR_EXHAUSTED", close["refs"]["question_id"])] * 2
    assert recovery["submitted"]["turn_event_id"] == cited[-1]["event_id"]
    exhausted = [row for row in ledger if row.get("budget_exhausted")]
    assert [(row["recovery_reason"], row["question_id"]) for row in exhausted] == [
        ("CONTRACT_REPAIR_EXHAUSTED", close["refs"]["question_id"])]
    # the world's own typed sequence, in order
    if expected["journal"]:
        canary = [_typed(row) for row in _pinned(expected["journal"]) if row["operation"] != "G3_SELECTION"]
        assert _contains_in_order([_typed(row) for row in journal], canary)
    model = _sealed_and_complete(run)
    level = next(item for item in model["levels"] if item["state"] == "OPEN")
    rows = {row["gate_id"]: row["disposition"] for row in level["certified"]["gates"]}
    assert rows[G42] != "CERTIFIED"  # a repair failure certifies nothing
    assert rows[G3] == "CERTIFIED" and rows["G4-REACTIONS"] == "CERTIFIED"  # supported facts are kept


# ---- D22: g50t, re86, sc25, wa30 ----------------------------------------------------------------------------------

@pytest.mark.parametrize("world", ["g50t", "re86", "sc25", "wa30"])
def test_d22_world_close_cites_its_checks_and_the_journal_seals(tmp_path, monkeypatch, world):
    expected = CANARY["d22"][world]
    check_row, outcome_row = _pinned(expected["journal"])
    assert expected["provenance"] == ["OPEN", "INCOMPLETE"] and "rule 5" in expected["writer_failure"]
    gate = expected["gate"]
    run = Session(tmp_path, "D22_G3" if gate == G3 else "D22_G2", monkeypatch,
                  reason=outcome_row["submitted"]["owned_because"]).play()
    journal = run.journal()
    by_id = {row["event_id"]: row for row in journal}
    closes = [row for row in journal if (row["operation"], row["event"]) == ("GATE", "CLOSE")
              and row["reason"]["code"] == "NO_LEGAL_CONTROLLER_MOVE"]
    assert closes, "base: the close is refused by the writer (rule 5) and never written"
    # G2 closes the gate once; G3 closes its entity questions one at a time (Runtime-01's entity closure), then the gate
    scopes = [row["submitted"]["scope"] for row in closes]
    assert scopes == ["GATE"] if gate == G2 else (set(scopes[:-1]) == {"ENTITY"} and scopes[-1] == "GATE")
    for close in closes:
        position = journal.index(close)
        check, outcome = journal[position - 2], journal[position - 1]
        assert [_typed(check), _typed(outcome)] == [_typed(check_row), _typed(outcome_row)]
        assert outcome["submitted"]["owned_because"] == outcome_row["submitted"]["owned_because"]
        assert close["gate_id"] == gate and close["submitted"]["class"] is None
        cited = [by_id[item] for item in close["submitted"]["history"]]
        assert cited and check in cited and all(
            (row["event"], row["gate_id"], row["level"], row["life"]) == (
                "RECOVERY_CHECK", close["gate_id"], close["level"], close["life"]) for row in cited)
        recovery = journal[position + 1]
        assert (recovery["event"], recovery["disposition"]) == ("RECOVERY", "CLOSED_UNRESOLVED")
        assert recovery["submitted"] == {"turn_event_id": outcome["event_id"],
                                         "resulting_event_id": close["event_id"]}
    cited_ids = [item for close in closes for item in close["submitted"]["history"]]
    assert len(cited_ids) == len(set(cited_ids))  # no check is cited by two closes
    machine = run.agent._gate_machine
    assert machine.target_journal.active_product(gate).payload["status"] == "UNRESOLVED"
    assert machine.gate_id != gate  # the ladder continued past the closed gate
    _sealed_and_complete(run)


def test_a_run_that_ends_right_after_no_legal_controller_move_still_seals(tmp_path, monkeypatch):
    """WO §4.2: H2 seals even when the run ends immediately after ``NO_LEGAL_CONTROLLER_MOVE`` (the open outcome is
    resolved ``RUN_ENDED``, then sealed). A guard: the base already holds it."""
    run = Session(tmp_path, "D22_G2_END", monkeypatch).play()
    journal = run.journal()
    outcome, recovery = journal[-2:]
    assert (outcome["event"], outcome["reason"]["code"]) == ("OUTCOME", "NO_LEGAL_CONTROLLER_MOVE")
    assert (recovery["event"], recovery["disposition"], recovery["reason"]["code"]) == (
        "RECOVERY", "NO_CONTROLLER_ACTION", "RUN_ENDED")
    assert recovery["submitted"]["turn_event_id"] == outcome["event_id"]
    _sealed_and_complete(run)
