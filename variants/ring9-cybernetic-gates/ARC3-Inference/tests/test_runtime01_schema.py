"""WO-RUNTIME-01 §10: audit journal v3, turn ledger v2, world model v11; the frozen audit-v2 and world-model-v10 readers.

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. The frozen fixtures were written by the base code before
any production edit (``tools/freeze_base_fixtures.py`` in the build package): ``world_model_v10_frozen.json.gz`` and
``provenance_v2_journal_73f13d1.jsonl``. Attacks are labelled doubles: each changes only what it names.
"""
from __future__ import annotations

import copy
import gzip
import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
V10_MODEL = FIXTURES / "world_model_v10_frozen.json.gz"
V2_JOURNAL = FIXTURES / "provenance_v2_journal_73f13d1.jsonl"
RUN = {"run_stem": "g_p0", "game_id": "g"}


def _aj():
    from inference.framework import audit_journal

    return audit_journal


def _row(operation, event, disposition, *, executor="DUCK", gate="G1-EGO", reason=("READ_ONLY_REPEAT", "x"),
         submitted=None, question="Q:L1:G1-EGO:LEVEL-1:CONTROL_LOCUS", **refs):
    aj = _aj()
    return {"level": 1, "life": 1, "gate_id": gate, "at_transition": 3, "executor": executor,
            "operation": operation, "event": event, "disposition": disposition, "submitted": submitted,
            "effective": None, "field_sources": None, "refs": aj.make_refs(question_id=question, **refs),
            "reason": None if reason is None else {"code": reason[0], "text": reason[1]}}


def _journal(tmp_path, rows, *, seal=True):
    aj = _aj()
    journal = aj.ProvenanceJournal(tmp_path / "j.jsonl", dict(RUN))
    written = [journal.append(row) for row in rows]
    if seal:
        journal.seal()
    return journal, written


def test_new_journals_are_v3_and_the_new_operations_validate(tmp_path):
    aj = _aj()
    assert aj.SCHEMA == "virelai-provenance-v3"
    journal, written = _journal(tmp_path, [_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION")], seal=False)
    assert written[0] is not None and written[0]["schema"] == "virelai-provenance-v3"
    recovery = _row("TURN", "RECOVERY", "DUCK_REWOKEN", executor="CONTROLLER",
                    submitted={"turn_event_id": written[0]["event_id"], "resulting_event_id": None})
    assert journal.append(recovery) is not None
    assert journal.seal()
    assert aj.read_journal(journal.path).status == "SEALED"


def test_the_frozen_v2_reader_refuses_a_v3_journal_and_still_reads_its_own(tmp_path):
    """WO 31-32: the v2 reader never reinterprets v3; the base's own v2 journal still reads SEALED."""
    aj = _aj()
    journal, _written = _journal(tmp_path, [_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION"),
                                            _row("TURN", "RECOVERY", "DUCK_REWOKEN", executor="CONTROLLER",
                                                 submitted={"turn_event_id": None, "resulting_event_id": None})],
                                 seal=False)
    read = aj.read_journal_v2(journal.path)
    assert read.status == "CORRUPT" and read.failure["code"] == "SCHEMA_INVALID"
    base = aj.read_journal_v2_bytes(V2_JOURNAL.read_bytes())
    assert base.status == "SEALED"
    assert aj.read_journal_bytes(V2_JOURNAL.read_bytes()).status == "SEALED"


def test_a_v2_vocabulary_refuses_the_turn_operations():
    aj = _aj()
    with pytest.raises(aj.ProvenanceError):
        aj.check_content(_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION"), schema="virelai-provenance-v2")


def test_an_outcome_left_unresolved_at_the_seal_is_refused(tmp_path):
    aj = _aj()
    journal, written = _journal(tmp_path, [_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION")])
    assert written[0] is not None  # the outcome itself is valid v3
    assert journal.sealed is False and journal.failed  # the writer never seals an open recovery
    assert "OUTCOME" in journal.failed


def test_a_recovery_must_resolve_an_open_outcome(tmp_path):
    aj = _aj()
    journal, written = _journal(tmp_path, [_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION")], seal=False)
    assert written[0] is not None
    stray = _row("TURN", "RECOVERY", "DUCK_REWOKEN", executor="CONTROLLER",
                 submitted={"turn_event_id": "PV-0000000000000000", "resulting_event_id": None})
    assert journal.append(stray) is None and journal.failed


def test_a_controller_action_recovery_must_name_a_controller_admission(tmp_path):
    aj = _aj()
    journal, written = _journal(tmp_path, [
        _row("PROBE", "ADMISSION", "ADMITTED", executor="DUCK", gate="PLAY-NORMAL", reason=None, question=None,
             probe_id="PLAY-NORMAL:1"),
        _row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION", gate="PLAY-NORMAL", question="FREE_PLAY")], seal=False)
    attack = _row("TURN", "RECOVERY", "CONTROLLER_ACTION", executor="CONTROLLER", gate="PLAY-NORMAL",
                  question="FREE_PLAY", reason=("MODEL_TIMEOUT", "x"),
                  submitted={"turn_event_id": written[1]["event_id"], "resulting_event_id": written[0]["event_id"]})
    assert journal.append(attack) is None and journal.failed  # it names Duck's admission


def test_a_budget_close_must_cite_exactly_its_budget_of_consecutive_failures(tmp_path):
    aj = _aj()
    q = "Q:L1:G1-EGO:LEVEL-1:CONTROL_LOCUS"
    journal, written = _journal(tmp_path, [_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION")], seal=False)
    journal.append(_row("TURN", "RECOVERY", "DUCK_REWOKEN", executor="CONTROLLER",
                        submitted={"turn_event_id": written[0]["event_id"], "resulting_event_id": None}))
    attack = _row("GATE", "CLOSE", "CLOSED_UNRESOLVED", executor="CONTROLLER", reason=("HARD_BUDGET_SPENT", "x"),
                  question=q, submitted={"scope": "GATE", "class": "HARD", "budget": 2,
                                         "history": [written[0]["event_id"]]})
    assert journal.append(attack) is None and journal.failed  # one failure cited, budget 2


def test_a_frontier_exhaustion_without_its_proof_is_refused(tmp_path):
    aj = _aj()
    journal, written = _journal(tmp_path, [_row("TURN", "OUTCOME", "RECOVERABLE_NO_ACTION", gate="PLAY-NORMAL",
                                                question="FREE_PLAY")], seal=False)
    attack = _row("TURN", "RECOVERY", "NO_CONTROLLER_ACTION", executor="CONTROLLER", gate="PLAY-NORMAL",
                  question="FREE_PLAY", reason=("FREE_PLAY_FRONTIER_EXHAUSTED", "x"),
                  submitted={"turn_event_id": written[0]["event_id"], "resulting_event_id": None, "proof": None})
    assert journal.append(attack) is None and journal.failed


def test_the_frozen_v10_model_still_reads_and_the_writer_is_v11():
    """WO 31: the base's own v10 model reads unchanged; new models are v11."""
    from inference.framework import world_model_v2 as wm

    model = json.loads(gzip.decompress(V10_MODEL.read_bytes()))
    assert model["schema"] == "virelai-world-model-v10"
    wm.read_world_model(model)
    wm.validate_v10(model)
    assert wm.SCHEMA == "virelai-world-model-v11"


def test_a_v11_model_relabelled_v10_is_refused():
    """WO 32: a downgrade attack (v11 relabelled v10 and rehashed) is refused, however it is presented."""
    import dossier_fixtures as fx
    from inference.framework import world_model_v2 as wm

    model = fx.compiled(fx.carry_v7().machine, persist_reason="RUN_END", reconcile=True)
    assert model["schema"] == "virelai-world-model-v11"
    forged = copy.deepcopy(model)
    forged["schema"] = "virelai-world-model-v10"
    forged["content_sha256"] = wm.content_sha256(forged)
    with pytest.raises(wm.WorldModelV2Error):
        wm.read_world_model(forged)
    with pytest.raises(wm.WorldModelV2Error):
        wm.validate_v10(forged)


def test_a_v10_model_relabelled_v11_is_refused():
    from inference.framework import world_model_v2 as wm

    model = json.loads(gzip.decompress(V10_MODEL.read_bytes()))
    forged = copy.deepcopy(model)
    forged["schema"] = "virelai-world-model-v11"
    forged["content_sha256"] = wm.content_sha256(forged)
    with pytest.raises(wm.WorldModelV2Error):
        wm.read_world_model(forged)


def test_a_closed_unresolved_gate_never_renders_certified():
    """A gate closed CLOSED_UNRESOLVED is a typed disposition in the v11 census, never CERTIFIED."""
    import dossier_fixtures as fx
    from inference.framework import gate_closure
    from inference.framework.record_replay import load_record, replay

    machine = replay(load_record("tests/fixtures/ls20_kaggle_unified_v1_record.json.gz"), max_steps=8,
                     measure=False).machine
    gate_closure.close_gate(machine, "G1-EGO", "HARD_BUDGET_SPENT")
    model = fx.compiled(machine, persist_reason="RUN_END")
    gates = {row["gate_id"]: row for row in model["levels"][-1]["certified"]["gates"]}
    assert gates["G1-EGO"]["disposition"] == "CLOSED_UNRESOLVED"
    assert not any(role["role"] == "EGO" for role in model["levels"][-1]["certified"]["roles"])
    origins = model["levels"][-1]["product_answers"]
    entry = next(item for item in origins.values() if item["gate_id"] == "G1-EGO")
    assert entry["origin"] == "GATE_DERIVED" and entry["basis"] == "EGO_UNRESOLVED"
