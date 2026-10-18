"""WO-PE-02 fail-first tests: schema v4 absorbs the validated provenance journal (one chapter, rows once).

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v2``; Sol's
rulings 1-9 and semantic corrections on the WO-PE-02 sweep.

Two kinds of test live here, and the fail-first record keeps them apart:

* **new behaviour** (``test_v4_*``): fails on ``afe93c8``, where there is no chapter, no schema v4, no
  ``provenance_chapter`` module and no run roster;
* **compatibility guards** (``test_guard_*``): pass on ``afe93c8`` and must still pass: v1, v2 and v3 artifacts
  read; Duck's digest and pages are unchanged apart from the model revision label; nothing reads the journal on
  the per-action path.

Nothing here parses transcript prose.
"""
from __future__ import annotations

import builtins
import copy
import hashlib
import json
import pathlib
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from inference.agent.runtime_state import RUNTIME_STATE_FILENAME

FIXTURES = Path(__file__).parent / "fixtures"
RUN = {"run_stem": "g_p0", "game_id": "g"}
G0_PAYLOAD = {"answer_id": "G0-A", "action_metadata": [{"action": "ACTION6", "requires_coordinates": True}],
              "semantic_claims": [], "epistemic_limit": "Action effects remain unknown until observed."}


def _pc():
    from inference.framework import provenance_chapter

    return provenance_chapter


def _aj():
    from inference.framework import audit_journal

    return audit_journal


# ---- a small synthetic run: one level, one probe executed at transition 1, one G0 answer and its product ----------

def _model(*, persist_reason: str = "BUDGET_STOP") -> dict:
    from test_world_model_v2 import _model as v3_model, _with_dossiers

    model = v3_model()
    model["manifest"]["persist_reason"] = persist_reason
    level = model["levels"][0]
    level["record"]["reset_transition_ids"] = []
    level["receipts"]["products"] = {"G0-A": {"gate_id": "G0-ACTION-METADATA", "product_type": "ActionSurface",
                                              "revision": 1, "payload_sha256": _g0_content()[1]}}
    level["product_answers"] = {"G0-A": _entry(G0_PAYLOAD)}
    if _g0_content()[0] is not None:  # schema v5 (WO-PE-03A): the product's body beside its receipt
        level["product_content"] = {"G0-A": _g0_content()[0]}
    return _with_dossiers(model)  # schema v6 (WO-G4-DOSSIER-A): dossiers recompiled for this persist reason


def _g0_content():
    """The G0 product's v5 content entry and the legacy receipt hash it agrees with; (None, zeros) before v5."""
    try:
        from inference.framework import product_content
    except ImportError:  # before schema v5
        return None, "0" * 64
    product = SimpleNamespace(product_id="G0-A", product_type="ActionSurface", revision=1, dependencies=(),
                              payload=G0_PAYLOAD)
    return (product_content.entry("G0-ACTION-METADATA", product),
            product_content.legacy_payload_sha256(product.payload))


def _entry(record=G0_PAYLOAD, *, gate="G0-ACTION-METADATA", product_type="ActionSurface", basis="PRODUCT_IS_ANSWER",
           link="PRODUCT_ID"):
    """The census entry for a product certified by ``record``. Revision 2 stores a shaped reference (clauses and
    omitted fields); on revision 1 (the fail-first run) the same scenario gets the entry revision 1's census wrote,
    so the attacks below test each revision's own matcher on identical evidence."""
    try:
        from inference.framework import answer_shapes
    except ImportError:  # revision 1
        return {"gate_id": gate, "product_type": product_type, "link": link,
                "answers": [{"answer_id": record["answer_id"], "fields": _pc().field_hashes(record)}]}
    return {"gate_id": gate, "product_type": product_type, "origin": "ANSWER_CERTIFIED", "basis": basis,
            "link": link, "answers": [answer_shapes.reference(gate, record)]}


def _probe(level=1, life=1, probe="G3-LEVERS:CLICK:1"):
    aj = _aj()
    return {"level": level, "life": life, "gate_id": "G3-LEVERS", "at_transition": 0, "executor": "CONTROLLER",
            "operation": "PROBE", "event": "ADMISSION", "disposition": "ADMITTED",
            "submitted": {"actions": [{"action": "ACTION6"}], "decision": {"probe_token": "CAPABILITY:X:R1"}},
            "effective": None, "field_sources": None, "refs": aj.make_refs(probe_id=probe), "reason": None}


def _execution(admission, *, evidence="E-1", transition=1):
    aj = _aj()
    return {**{k: admission[k] for k in ("level", "life", "gate_id", "at_transition", "executor")},
            "operation": "PROBE", "event": "EXECUTION", "disposition": "EXECUTED", "submitted": None, "effective": None,
            "field_sources": None, "reason": None,
            "refs": aj.make_refs(probe_id=admission["refs"]["probe_id"], evidence_id=evidence,
                                 executed_transition=transition, admission_event_id=admission["event_id"])}


def _answer(payload=G0_PAYLOAD, *, level=1, life=1, gate="G0-ACTION-METADATA", answer_id="G0-A"):
    aj = _aj()
    return {"level": level, "life": life, "gate_id": gate, "at_transition": 1, "executor": "CONTROLLER",
            "operation": "ANSWER", "event": "ADMISSION", "disposition": "ADMITTED", "submitted": payload,
            "effective": payload, "field_sources": {k: "SUBMITTER" for k in payload}, "reason": None,
            "refs": aj.make_refs(answer_id=answer_id)}


def _sidecar(payload=G0_PAYLOAD, gate="G0-ACTION-METADATA"):
    return {"schema": "virelai-cybernetic-gates-v1", "gate_id": gate, "executor": "CONTROLLER", **payload}


def _journal(path: Path, *, extra=(), seal=True, run=RUN, answers=1) -> bytes:
    """The standard synthetic journal: an admitted probe, its execution, ``answers`` G0 answers, then ``extra``."""
    aj = _aj()
    journal = aj.ProvenanceJournal.open(path, run_stem=run["run_stem"], game_id=run["game_id"])
    admission = journal.append(_probe())
    journal.append(_execution(admission))
    for _ in range(answers):
        journal.append(_answer())
    for content in extra:
        journal.append(content(journal) if callable(content) else content)
    assert not journal.failed, journal.failed
    if seal:
        assert journal.seal()
    return path.read_bytes()


def _h2(model, data, *, records=(_sidecar(),), **kwargs):
    return _pc().h2(model, data=data, sidecar="g_p0_provenance.jsonl", capture=kwargs.pop("capture", "ENABLED"),
                    answer_records=None if records is None else [dict(r) for r in records], **kwargs)


def _sealed(model, chapter):
    from inference.framework.world_model_v2 import seal

    return seal({**model, "provenance": chapter})


# ---- 1 · sealed, complete, embedded once, indexed once ------------------------------------------------------------

def test_v4_a_sealed_reconciled_run_is_complete_with_every_row_embedded_and_indexed_once(tmp_path):
    from inference.framework.world_model_v2 import SCHEMA, canonical_bytes, read_world_model

    data = _journal(tmp_path / "j.jsonl")
    sealed = _sealed(_model(), _h2(_model(), data))
    chapter = sealed["provenance"]
    assert SCHEMA == "virelai-world-model-v7" and sealed["schema"] == SCHEMA
    assert (chapter["phase"], chapter["integrity"], chapter["completeness"], chapter["completeness_scope"]) == (
        "H2", "SEALED", "COMPLETE", "RUN")
    assert chapter["reasons"] == [] and chapter["reconciliation"]["findings"] == []
    rows = _aj().read_journal(tmp_path / "j.jsonl")
    assert chapter["rows"] == rows.rows and chapter["seal"] == rows.seal  # exactly the validated rows, once
    assert chapter["stamp"]["journal_sha256"] == hashlib.sha256(data).hexdigest()
    assert chapter["stamp"]["seal_event_hash"] == rows.seal["event_hash"] and chapter["stamp"]["verified"]
    index = sealed["levels"][0]["provenance_index"]
    listed = [i for key in ("admissions", "executions", "answers", "selections", "annotations") for i in index[key]]
    assert sorted(listed + chapter["unscoped"]) == sorted(r["event_id"] for r in rows.rows)
    assert chapter["answer_crosscheck"]["status"] == "MATCHED"
    (join,) = chapter["reconciliation"]["product_joins"]
    assert join["status"] == "EXACT" and join["answer_event_id"] == rows.rows[2]["event_id"]
    assert read_world_model(json.loads(canonical_bytes(sealed)))["provenance"] == chapter


# ---- 2 · OPEN, CORRUPT, UNAVAILABLE: typed, visible, never omitted --------------------------------------------------

def test_v4_an_open_journal_after_a_write_failure_embeds_its_verified_prefix_and_is_incomplete(tmp_path):
    data = _journal(tmp_path / "j.jsonl", seal=False)
    chapter = _h2(_model(), data, capture="FAILED", writer_failure="OSError: disk full")
    sealed = _sealed(_model(), chapter)["provenance"]
    assert (sealed["integrity"], sealed["completeness"]) == ("OPEN", "INCOMPLETE")
    assert {"JOURNAL_OPEN", "WRITE_FAILED"} <= set(sealed["reasons"])
    assert len(sealed["rows"]) == 3 and sealed["seal"] is None and sealed["writer_failure"] == "OSError: disk full"
    assert sealed["stamp"]["journal_sha256"] == hashlib.sha256(data).hexdigest()
    assert sealed["stamp"]["seal_event_hash"] is None and sealed["stamp"]["verified"] is False


def test_v4_a_corrupt_journal_keeps_only_the_validated_prefix_and_its_typed_failure(tmp_path):
    data = _journal(tmp_path / "j.jsonl")
    lines = data.split(b"\n")[:-1]
    torn = b"\n".join(lines[:-1])[: -len(lines[-2]) // 2]  # the seal and half of the last row are lost
    chapter = _sealed(_model(), _h2(_model(), torn))["provenance"]
    assert (chapter["integrity"], chapter["completeness"]) == ("CORRUPT", "INCOMPLETE")
    assert chapter["failure"]["code"] == "TRUNCATED_TAIL" and "JOURNAL_CORRUPT" in chapter["reasons"]
    assert len(chapter["rows"]) == 2 and chapter["stamp"]["verified"] is False


@pytest.mark.parametrize(("data", "reason", "capture"), [
    (None, "JOURNAL_MISSING", "ENABLED"), (None, "CAPTURE_DISABLED", "DISABLED")])
def test_v4_an_unavailable_journal_is_typed_and_incomplete(data, reason, capture):
    chapter = _sealed(_model(), _h2(_model(), data, capture=capture, unavailable_reason=reason))["provenance"]
    assert (chapter["integrity"], chapter["unavailable_reason"], chapter["completeness"]) == (
        "UNAVAILABLE", reason, "INCOMPLETE")
    assert chapter["rows"] == [] and chapter["reasons"] == ["JOURNAL_UNAVAILABLE"]


def test_v4_a_live_view_model_is_v4_not_evaluated_and_never_opens_the_journal(monkeypatch):
    from inference.framework.world_model_v2 import seal

    _forbid_journal_reads(monkeypatch)
    model = seal(_model(persist_reason="LIVE_VIEW"))
    assert model["schema"] == "virelai-world-model-v7"
    chapter = model["provenance"]
    assert (chapter["phase"], chapter["integrity"], chapter["completeness"]) == ("LIVE_VIEW", "NOT_EVALUATED",
                                                                                "NOT_EVALUATED")


def _forbid_journal_reads(monkeypatch):
    real_open, real_read = builtins.open, pathlib.Path.read_bytes

    def guarded_open(file, *args, **kwargs):
        assert not str(file).endswith("_provenance.jsonl"), f"journal opened: {file}"
        return real_open(file, *args, **kwargs)

    def guarded_read(self):
        assert not str(self).endswith("_provenance.jsonl"), f"journal read: {self}"
        return real_read(self)

    monkeypatch.setattr(builtins, "open", guarded_open)
    monkeypatch.setattr(pathlib.Path, "read_bytes", guarded_read)


# ---- 3 · run, file and identity ------------------------------------------------------------------------------------

def test_v4_a_journal_of_another_run_is_a_run_mismatch(tmp_path):
    data = _journal(tmp_path / "j.jsonl", run={"run_stem": "other_p0", "game_id": "other"})
    chapter = _h2(_model(), data)
    assert chapter["completeness"] == "INCOMPLETE" and "RUN_MISMATCH" in chapter["reasons"]


def test_v4_the_sidecar_verifier_tells_verified_missing_substituted_and_rewritten_apart(tmp_path):
    pc = _pc()
    path = tmp_path / "g_p0_provenance.jsonl"
    data = _journal(path)
    model = _sealed(_model(), _h2(_model(), data))
    assert pc.verify_sidecar(model, path)["status"] == "VERIFIED"
    path.write_bytes(b"\n".join(json.dumps(json.loads(line), indent=None, sort_keys=False).encode()
                                for line in data.splitlines()) + b"\n")  # same rows, different bytes
    assert pc.verify_sidecar(model, path)["status"] == "REWRITTEN"
    other = tmp_path / "other.jsonl"
    path.write_bytes(_journal(other, answers=2))
    assert pc.verify_sidecar(model, path)["status"] == "SUBSTITUTED"
    missing = tmp_path / "gone.jsonl"
    assert pc.verify_sidecar(model, missing)["status"] == "MISSING"
    from inference.framework.world_model_v2 import validate

    validate(model)  # a missing or replaced sidecar never invalidates the written model


@pytest.mark.parametrize("damage", ["missing", "duplicated", "mismatched"])
def test_v4_missing_duplicated_and_mismatched_admissions_make_the_journal_corrupt(tmp_path, damage):
    from test_provenance_capture import _r2_admission, _r2_event_id, _r2_execution, _r2_forge

    first = _r2_admission(1)
    first_id = _r2_event_id(1, first)
    contents = {"missing": [first, _r2_execution(1, None)],
                "duplicated": [first, _r2_execution(1, first_id), _r2_execution(1, first_id)],
                "mismatched": [first, _r2_admission(2), _r2_execution(2, first_id)]}[damage]
    _r2_forge(tmp_path / "j.jsonl", [dict(c) for c in contents])
    model = {**_model(), "run_stem": "fixture_p0"}
    chapter = _h2(model, (tmp_path / "j.jsonl").read_bytes())
    assert chapter["integrity"] == "CORRUPT" and chapter["failure"]["code"] == {
        "missing": "ADMISSION_MISSING", "duplicated": "ADMISSION_ALREADY_CONSUMED",
        "mismatched": "ADMISSION_MISMATCH"}[damage]


# ---- 4 · reconciliation -----------------------------------------------------------------------------------------

def test_v4_an_execution_without_a_receipt_and_a_receipt_without_an_execution_are_findings(tmp_path):
    model = _model()
    model["levels"][0]["receipts"]["evidence"]["E-9"] = {"transition_id": 1, "gate_id": "G3-LEVERS", "probe_id": "x"}
    data = _journal(tmp_path / "j.jsonl", extra=[
        lambda j: _execution(j.append(_probe(probe="P-2")), evidence="E-7", transition=1)])
    codes = {f["code"] for f in _h2(model, data)["reconciliation"]["findings"]}
    assert {"EVIDENCE_WITHOUT_EXECUTION", "EXECUTION_WITHOUT_EVIDENCE"} <= codes


def test_v4_an_admitted_probe_never_executed_is_unconsumed(tmp_path):
    data = _journal(tmp_path / "j.jsonl", extra=[_probe(probe="P-2")])
    chapter = _h2(_model(), data)
    assert "ADMISSION_UNCONSUMED" in chapter["reasons"] and chapter["completeness"] == "INCOMPLETE"


def test_v4_a_product_with_no_admitted_answer_blocks_complete(tmp_path):
    data = _journal(tmp_path / "j.jsonl", answers=0)
    chapter = _h2(_model(), data, records=())
    assert "PRODUCT_WITHOUT_ADMITTED_ANSWER" in chapter["reasons"]


def test_v4_resets_without_evidence_are_typed_and_any_other_ungated_transition_is_a_finding(tmp_path):
    data = _journal(tmp_path / "j.jsonl")
    model = _model()
    model["levels"][0]["record"]["transition_ids"] = [1, 2, 3]
    model["levels"][0]["record"]["reset_transition_ids"] = [2]
    chapter = _h2(model, data)
    assert chapter["reconciliation"]["ungated_resets"] == [[1, 2]]
    assert [(f["code"], f["transition_id"]) for f in chapter["reconciliation"]["findings"]] == [
        ("UNGATED_TRANSITION", 3)]


def test_v4_repeated_answer_ids_join_within_their_own_level_and_ambiguity_blocks_complete(tmp_path):
    two = _model()
    second = copy.deepcopy(two["levels"][0])
    second["level"] = 2
    second["record"]["transition_ids"], second["receipts"]["evidence"] = [], {}
    two["levels"].append(second)
    data = _journal(tmp_path / "a.jsonl", extra=[_answer(level=2)])
    joins = _h2(two, data, records=(_sidecar(), _sidecar()))["reconciliation"]["product_joins"]
    assert [(j["level"], j["status"]) for j in joins] == [(1, "EXACT"), (2, "EXACT")]
    assert joins[0]["answer_event_id"] != joins[1]["answer_event_id"]
    twice = _h2(_model(), _journal(tmp_path / "b.jsonl", answers=2), records=(_sidecar(), _sidecar()))
    assert twice["reconciliation"]["product_joins"][0]["status"] == "AMBIGUOUS"
    assert "AMBIGUOUS_PRODUCT_ANSWER" in twice["reasons"] and twice["completeness"] == "INCOMPLETE"
    other = {**G0_PAYLOAD, "epistemic_limit": "a different limit"}
    distinct = _h2(_model(), _journal(tmp_path / "c.jsonl", extra=[_answer(other)]),
                   records=(_sidecar(), _sidecar(other)))
    assert distinct["reconciliation"]["product_joins"][0]["status"] == "EXACT"  # the payload identifies the answer


def test_v4_an_unattributed_product_is_typed_with_its_reason_and_blocks_complete(tmp_path):
    model = _model()
    model["levels"][0]["product_answers"]["G0-A"].update(origin="UNATTRIBUTED", basis="NO_RETAINED_ANSWER",
                                                         link="NONE", answers=[])
    chapter = _h2(model, _journal(tmp_path / "j.jsonl"))
    join = chapter["reconciliation"]["product_joins"][0]
    assert (join["status"], join["basis"]) == ("UNATTRIBUTED", "NO_RETAINED_ANSWER")
    assert "PRODUCT_UNATTRIBUTED" in chapter["reasons"] and chapter["completeness"] == "INCOMPLETE"
    _sealed(model, chapter)  # an UNATTRIBUTED entry is a valid, typed record: it seals, and it blocks


# ---- 5 · the gate-answer cross-check ------------------------------------------------------------------------------

def test_v4_the_gate_answer_cross_check_compares_sequence_gate_executor_id_and_payload(tmp_path):
    data = _journal(tmp_path / "j.jsonl")
    assert _h2(_model(), data)["answer_crosscheck"]["status"] == "MATCHED"
    changed = _h2(_model(), data, records=(_sidecar({**G0_PAYLOAD, "semantic_claims": ["changed"]}),))
    assert changed["answer_crosscheck"]["status"] == "MISMATCH"
    assert "GATE_ANSWER_MISMATCH" in changed["reasons"] and changed["completeness"] == "INCOMPLETE"
    missing = _h2(_model(), data, records=None)
    assert "GATE_ANSWERS_MISSING" in missing["reasons"]


# ---- 6 · typed and scoped references ----------------------------------------------------------------------------

def test_v4_typed_references_resolve_by_index_and_unknown_ids_stay_unresolved(tmp_path):
    cited = {**G0_PAYLOAD, "evidence_refs": ["E-1", "G0-A", "E0001", "W-1", "LC-00001"]}
    data = _journal(tmp_path / "j.jsonl", answers=0, extra=[_answer(cited)])
    model = _model()  # the accepted G0 answer keeps no evidence_refs: the submitted field is effective-only
    chapter = _h2(model, data, records=(_sidecar(),))
    answer_id = chapter["rows"][2]["event_id"]
    kinds = [(r["id"], r["kind"]) for r in chapter["typed_refs"][answer_id]]
    assert kinds == [("E-1", "EVIDENCE"), ("G0-A", "PRODUCT"), ("E0001", "ENTITY"), ("W-1", "WITNESS"),
                     ("LC-00001", "UNRESOLVED")]
    assert chapter["answer_refs"][answer_id] == {"kind": "ANSWER", "gate_id": "G0-ACTION-METADATA", "level": 1,
                                                 "life": 1, "answer_id": "G0-A", "ordinal": 1}
    executed = chapter["rows"][1]["event_id"]
    assert chapter["typed_refs"][executed] == [{"field": "evidence_id", "kind": "EVIDENCE", "id": "E-1",
                                                "scope": {"level": 1}, "required": True, "hint": None}]
    assert chapter["completeness"] == "COMPLETE"  # payload references are typed and kept, never blocking


def test_v4_restarting_note_ids_become_distinct_scoped_references(tmp_path):
    aj = _aj()

    def note(level):
        return {"level": level, "life": 1, "gate_id": "G3-LEVERS", "at_transition": 1, "executor": "DUCK",
                "operation": "ANNOTATION", "event": "ADMISSION", "disposition": "UNCERTIFIED", "submitted": [],
                "effective": None, "field_sources": None, "reason": None, "refs": aj.make_refs(note_ids=["N0001"])}

    chapter = _h2(_model(), _journal(tmp_path / "j.jsonl", extra=[note(1), note(2)]))
    refs = [ref["ref"] for row in chapter["rows"][3:] for ref in chapter["note_refs"][row["event_id"]]]
    assert refs == ["NOTE:L1:F1:N0001", "NOTE:L2:F1:N0001"]


# ---- 7 · H1, prefixes, determinism, the validator ----------------------------------------------------------------

def test_v4_h2_verifies_every_writer_reported_prefix_and_a_contradicted_one_blocks_complete(tmp_path):
    data = _journal(tmp_path / "j.jsonl")
    rows = _aj().read_journal(tmp_path / "j.jsonl").rows
    good = _h2(_model(), data, interim_prefixes=[{"event_count": 2, "head_hash": rows[1]["event_hash"]}])
    assert good["interim_prefixes"][0]["status"] == "VERIFIED" and good["completeness"] == "COMPLETE"
    bad = _h2(_model(), data, interim_prefixes=[{"event_count": 2, "head_hash": "f" * 64}])
    assert bad["interim_prefixes"][0]["status"] == "CONTRADICTED" and "INTERIM_PREFIX_CONTRADICTED" in bad["reasons"]


def test_v4_an_identical_compilation_is_byte_identical(tmp_path):
    from inference.framework.world_model_v2 import canonical_bytes

    data = _journal(tmp_path / "j.jsonl")
    assert canonical_bytes(_sealed(_model(), _h2(_model(), data))) == canonical_bytes(
        _sealed(_model(), _h2(_model(), data)))


@pytest.mark.parametrize("forgery", ["complete_claim", "dropped_finding", "altered_row", "foreign_index",
                                     "weakened_reference", "derived_claim"])
def test_v4_the_validator_recomputes_the_chapter_and_rejects_a_forged_one(tmp_path, forgery):
    from inference.framework.world_model_v2 import WorldModelV2Error, content_sha256, validate

    data = _journal(tmp_path / "j.jsonl", extra=[_probe(probe="P-2")])  # one unconsumed admission
    model = _sealed(_model(), _h2(_model(), data))
    chapter = model["provenance"]
    assert chapter["completeness"] == "INCOMPLETE" and "ADMISSION_UNCONSUMED" in chapter["reasons"]
    if forgery == "complete_claim":
        chapter.update(completeness="COMPLETE", reasons=[], completeness_scope="RUN")
    elif forgery == "dropped_finding":
        chapter["reconciliation"]["findings"] = []
    elif forgery == "altered_row":
        chapter["rows"][0]["executor"] = "DUCK"
    elif forgery == "foreign_index":
        model["levels"][0]["provenance_index"]["answers"].append("PV-0000000000000000")
    elif forgery == "weakened_reference":  # drop a clause so a truncated payload would match
        model["levels"][0]["product_answers"]["G0-A"]["answers"][0]["clauses"].pop()
    else:  # an answer-certified product relabelled as gate-derived so nothing has to join
        model["levels"][0]["product_answers"]["G0-A"].update(origin="GATE_DERIVED", basis="COUNTER_NOT_OBSERVED",
                                                             link="NONE", answers=[])
    model["content_sha256"] = content_sha256(model)  # a forger who recomputes the model hash
    with pytest.raises((WorldModelV2Error, ValueError)):
        validate(model)


# ---- 8 · the solver: H1 from memory, H2 once after the seal, crash, pre-play ---------------------------------------

def _session(tmp_path: Path, *, analyze=None, stop: bool = False, enabled: bool = True):
    from inference.agent.tool_agent import ToolAgent
    from inference.framework.solver import HarnessSolver, _HarnessGameSession
    from test_g3_directed_click import _Ft09Game

    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    game = _Ft09Game()
    run_stem = solver._run_stem(game.game_run.game_id, 0)
    agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                      controller_executor_enabled=True, provenance_enabled=enabled)
    agent._ensure_session = lambda _path: None
    state_path = solver._artifacts_dir() / f"{run_stem}_{RUNTIME_STATE_FILENAME}"
    session = _HarnessGameSession(
        solver=solver, game=game, analyzer=agent, game_index=0, pass_index=0, state_path=state_path,
        transcript_path=tmp_path / "t.txt", analysis_html_relpath="a.html", stop_event=threading.Event(),
        viewer_data_path=tmp_path / "v.json")
    if analyze is not None:
        agent.analyze = lambda *a, **k: analyze(agent, session)
    if stop:
        session.stop_event.set()
    return session, agent, tmp_path / "virelai" / run_stem


def _model_of(folder: Path) -> dict:
    return json.loads((folder / "world_model.json").read_text())


def test_v4_a_zero_action_run_writes_a_sealed_complete_v4_model(tmp_path):
    session, _agent, folder = _session(tmp_path, stop=True)
    session.play()
    model = _model_of(folder)
    assert model["schema"] == "virelai-world-model-v7"
    chapter = model["provenance"]
    assert (chapter["integrity"], chapter["completeness"], chapter["rows"]) == ("SEALED", "COMPLETE", [])
    assert chapter["stamp"]["run"]["run_stem"] == model["run_stem"]


def test_v4_a_handled_crash_is_complete_through_recorded_termination(tmp_path):
    def crash(agent, session):
        raise RuntimeError("boom")

    session, _agent, folder = _session(tmp_path, analyze=crash)
    session.play()
    model = _model_of(folder)
    assert model["manifest"]["persist_reason"] == "CRASH"
    chapter = model["provenance"]
    assert (chapter["completeness"], chapter["completeness_scope"]) == ("COMPLETE", "THROUGH_RECORDED_TERMINATION")


def test_v4_h1_reads_no_file_and_reports_the_writers_prefix_without_authority(tmp_path, monkeypatch):
    session, agent, _folder = _session(tmp_path)
    journal = _aj().ProvenanceJournal.open(tmp_path / "x_provenance.jsonl", run_stem="fixture_p0", game_id="fixture")
    journal.append(_answer())
    agent._provenance = journal
    _forbid_journal_reads(monkeypatch)
    chapter = session._provenance_chapter({"run_stem": "fixture_p0", "levels": []}, final=False)
    assert (chapter["phase"], chapter["integrity"], chapter["completeness"]) == ("H1", "NOT_EVALUATED", "PENDING")
    assert chapter["writer_reported"] == {"label": "WRITER_REPORTED", "event_count": 1, "head_hash": journal.head}


def test_v4_a_pre_play_crash_is_reported_as_a_missing_model_with_or_without_a_warning(tmp_path, monkeypatch):
    from inference.framework.run_roster import check_runs
    from inference.framework.solver import HarnessSolver
    from test_wo_l2a_census_paths import _CancelledGame

    solver = HarnessSolver(virelai_mode="gated")
    solver.job_dir = tmp_path
    monkeypatch.setattr(solver, "_make_analyzer", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no analyzer")))
    solver._play_one(_CancelledGame(), 0, 0)
    stem = solver._run_stem("fixture", 0)
    warnings = [json.loads(line) for line in (tmp_path / "virelai" / stem / "observer_warnings.jsonl").read_text()
                .splitlines()]
    assert [w["event"] for w in warnings] == ["WORLD_MODEL_NOT_WRITTEN"]
    report = check_runs(tmp_path, [stem, "never_started_p0"])
    assert report[stem]["model"] == "MODEL_MISSING" and report[stem]["warnings"] == ["WORLD_MODEL_NOT_WRITTEN"]
    assert report["never_started_p0"]["model"] == "MODEL_MISSING" and report["never_started_p0"]["warnings"] == []


@pytest.fixture(scope="module")
def controller_session(tmp_path_factory):
    """The production session on the continuation world: the controller plays to Duck's first turn, then the
    run ends; ``h2`` and the journal reader are counted."""
    from inference.agent.tool_agent import _ChatCompletionResult
    from inference.framework import audit_journal, provenance_chapter

    tmp = tmp_path_factory.mktemp("v4_controller")
    patch = pytest.MonkeyPatch()
    calls = {"h2": 0, "read": 0}
    h2, read = provenance_chapter.h2, audit_journal.read_journal_bytes
    patch.setattr(provenance_chapter, "h2", lambda *a, **k: calls.__setitem__("h2", calls["h2"] + 1) or h2(*a, **k))
    patch.setattr(audit_journal, "read_journal_bytes",
                  lambda *a, **k: calls.__setitem__("read", calls["read"] + 1) or read(*a, **k))
    session, agent, folder = _session(tmp)
    agent._controller.g3_choice_handoff = False

    def duck(messages, **kwargs):
        session.solver.max_actions_per_game = session.action_count
        return _ChatCompletionResult(message={"role": "assistant", "content": "Weighing the rows."})

    agent._chat_completion = duck
    session.play()
    patch.undo()
    return SimpleNamespace(model=_model_of(folder), calls=calls, session=session, agent=agent, folder=folder)


def test_v4_h2_reads_the_sealed_journal_once_and_absorbs_a_real_controller_run(controller_session):
    from inference.framework.provenance_chapter import verify_sidecar
    from inference.framework.world_model_v2 import validate

    model, chapter = controller_session.model, controller_session.model["provenance"]
    assert controller_session.calls == {"h2": 1, "read": 1}
    validate(model)
    assert chapter["integrity"] == "SEALED" and len(chapter["rows"]) > 100
    assert chapter["answer_crosscheck"]["status"] == "MATCHED"
    journal = controller_session.session.state_path.with_name(f"{model['run_stem']}_provenance.jsonl")
    assert verify_sidecar(model, journal)["status"] == "VERIFIED"
    # Revision 2 (Sol F1): an ordinary real run is SEALED / COMPLETE; every product is answer-certified and joins
    # exactly one admitted answer, the G1 law and the G2 counter product included; no product is ignored.
    assert chapter["reconciliation"]["findings"] == [] and chapter["reasons"] == []
    assert (chapter["integrity"], chapter["completeness"], chapter["completeness_scope"]) == ("SEALED", "COMPLETE", "RUN")
    joins = chapter["reconciliation"]["product_joins"]
    products = {pid for level in model["levels"] for pid in level["receipts"]["products"]}
    assert {j["product_id"] for j in joins} == products and all(
        (j["origin"], j["status"]) == ("ANSWER_CERTIFIED", "EXACT") for j in joins)
    rows = {row["event_id"]: row for row in chapter["rows"]}
    by_type = {j["product_type"]: j for j in joins}
    for product_type, gate, basis in (("EgoLaw", "G1-EGO", "EGO_LAW_DERIVED_FROM_ANSWER"),
                                      ("CounterGateProduct", "G2-COUNTER", "COUNTER_MODEL_COPIES_ANSWER")):
        join = by_type[product_type]
        answer = rows[join["answer_event_id"]]
        assert (join["basis"], answer["gate_id"], answer["refs"]["answer_id"]) == (basis, gate, join["answer_id"])


# ---- 9 · compatibility guards: pass on afe93c8 and after ------------------------------------------------------------

def test_guard_frozen_v1_v2_and_v3_artifacts_still_read():
    from inference.framework.virelai_world_model import empty_world_model
    from inference.framework.world_model_v2 import WorldModelV2Error, read_world_model

    v2 = json.loads((FIXTURES / "world_model_v2_carry_v7_frozen.json").read_text())
    assert read_world_model(v2)["schema"] == "virelai-world-model-v2"
    v3 = json.loads((FIXTURES / "world_model_v3_frozen.json").read_text())  # sealed by afe93c8's v3 code
    assert read_world_model(v3)["schema"] == "virelai-world-model-v3"
    tampered = copy.deepcopy(v3)
    tampered["levels"][0]["gaps"][0]["reason"] = "BUDGET"
    with pytest.raises(WorldModelV2Error):
        read_world_model(tampered)
    from dataclasses import asdict

    from inference.framework.virelai_world_model import canonical_bytes as v1_bytes

    v1 = json.loads(v1_bytes(empty_world_model(game_id="g", observed_through_step=0, levels_observed=(1,),
                                               current_level=1, source_schema="fixture")))
    assert asdict(read_world_model(v1))["schema"] == "virelai-world-model-v1"


DUCK_VIEWS_AFE93C8 = {  # carry-v7 replay, model revision label masked (written from afe93c8 before any edit)
    "digest": "bb268bff3fbd383130b8690ff36111549ed8815a3546915640f05158be15295b",
    "dossiers": "fdd21d89d0b78aed10ade2d99e3d4190df71fad1f1c7fa13502db46f32fa2f22",
    "events": "d618a025e1be14cb05633850cf2dc47670acd1979bc2c89063b4adb63babfab0",
    "evidence:COUNTER-7faa2e676a38a10d": "67b8b73fbb9ece3634ce52329a3634a181601837aef4be69f849aac05c0d0eeb",
    "gaps": "27c61375c6cd2d1a0fb290f83ddab22278a7e6b728ebc12320b2156ab2459053",
    "laws": "1f23910130418463d24f85852226b6477de499a428ba84ff5d06b96e6938dc6d",
    "levels": "439d0a7a5dba58f260c9fa309db00130696ea112602b9b7763046f8494915518",
    "objects": "d1d8eeb0afc547ae3caeb352123907e5f38f259b038c50e4719f1987d9aec54a",
    "scene": "9b97450478170d6025239ebd219d9039538f6454376b2028dcf5874cefabb6aa",
}


def test_guard_ducks_digest_and_pages_are_unchanged_apart_from_the_revision_label():
    from g3_no_choice_trace import RECORDS
    from inference.framework.library_view import library_page, live_model, render_library_digest
    from inference.framework.record_replay import load_record, replay

    machine = replay(load_record(RECORDS["carry_v7"]), measure=False).machine
    model = live_model(machine)
    rev = model["content_sha256"][:12]

    def masked(text: str) -> str:
        return hashlib.sha256(text.replace(rev, "<REVISION>").encode()).hexdigest()

    views = {"digest": masked(render_library_digest(model))}
    for kind in ("levels", "objects", "gaps", "scene", "events", "laws", "dossiers"):
        views[kind] = masked(json.dumps(library_page(model, kind), sort_keys=True))
    product = sorted(model["levels"][0]["receipts"]["products"])[0]
    views["evidence:" + product] = masked(json.dumps(library_page(model, "evidence", id=product), sort_keys=True))
    assert views == DUCK_VIEWS_AFE93C8


def test_guard_the_controllers_per_action_path_never_reads_the_journal(tmp_path):
    """The m2 controller run to Duck's first turn: the journal reader is never called while actions are taken."""
    from inference.framework import audit_journal
    from test_memory_m2 import Run
    from inference.agent.tool_agent import ToolAgent

    patch = pytest.MonkeyPatch()
    reads = []
    for name in ("read_journal", "_read", "read_journal_bytes"):
        if hasattr(audit_journal, name):
            original = getattr(audit_journal, name)
            patch.setattr(audit_journal, name, lambda *a, _o=original, _n=name, **k: reads.append(_n) or _o(*a, **k))
    try:
        run = Run(tmp_path, patch)
        agent = ToolAgent(model="fixture-model", virelai_enabled=True, virelai_gates_enabled=True,
                          controller_executor_enabled=True, provenance_enabled=True)
        patch.setattr(agent, "_ensure_session", lambda _path: None)
        patch.setattr(agent, "_chat_completion", run._model)
        agent._controller.g3_choice_handoff = False
        run.agent = agent
        run.until_duck(limit=40)
        assert len(run.env_calls) > 20 and reads == []
    finally:
        patch.undo()


# ---- 10 · revision 2 (Sol, REVIEW_WO_PE_02 §2-§4): product origins, exact containment, strict hashing ---------------
# The attack tests use ``_entry``, so on revision 1 they run against revision 1's own census entry and matcher.

def _answer_only(payload, *, answer_id="G0-A"):
    aj = _aj()
    return {**_answer(payload), "refs": aj.make_refs(answer_id=answer_id)}


@pytest.mark.parametrize("attack", ["only_answer_id", "omitted_differing_field", "same_id_outside_the_overlap"])
def test_v4_r2_a_truncated_or_partial_payload_never_joins_a_product(tmp_path, attack):
    """F2: revision 1 accepted any non-empty overlap of fields; every stored semantic field must now be present."""
    stored = {**G0_PAYLOAD, "epistemic_limit": "the stored answer's own limit"}
    model = _model()
    model["levels"][0]["product_answers"]["G0-A"] = _entry(stored)
    truncated = {key: value for key, value in stored.items() if key != "epistemic_limit"}
    if attack == "only_answer_id":
        journal, records = [_answer_only({"answer_id": "G0-A"})], (_sidecar({"answer_id": "G0-A"}),)
    elif attack == "omitted_differing_field":
        journal, records = [_answer_only(truncated)], (_sidecar(truncated),)
    else:  # one same-id answer lacks the distinguishing field, the other carries it: only the second is the answer
        journal, records = [_answer_only(truncated), _answer_only(stored)], (_sidecar(truncated), _sidecar(stored))
    chapter = _h2(model, _journal(tmp_path / "j.jsonl", answers=0, extra=journal), records=records)
    join = chapter["reconciliation"]["product_joins"][0]
    if attack == "same_id_outside_the_overlap":
        assert join["status"] == "EXACT" and join["answer_event_id"] == chapter["rows"][3]["event_id"]
    else:
        assert join["status"] == "NO_ADMITTED_ANSWER" and chapter["completeness"] == "INCOMPLETE"
        assert "PRODUCT_WITHOUT_ADMITTED_ANSWER" in chapter["reasons"]


@pytest.mark.parametrize("damage", ["missing", "altered"])
def test_v4_r2_a_sidecar_with_a_missing_or_altered_semantic_field_is_a_mismatch(tmp_path, damage):
    record = _sidecar()
    if damage == "missing":
        del record["epistemic_limit"]
    else:
        record["epistemic_limit"] = "altered"
    chapter = _h2(_model(), _journal(tmp_path / "j.jsonl"), records=(record,))
    assert chapter["answer_crosscheck"]["status"] == "MISMATCH"
    assert "GATE_ANSWER_MISMATCH" in chapter["reasons"] and chapter["completeness"] == "INCOMPLETE"


def test_v4_r2_only_the_named_sidecar_fields_are_removed_before_comparison(tmp_path):
    from inference.framework import answer_shapes

    assert answer_shapes.SIDECAR_BOOKKEEPING == {"schema", "gate_id", "executor"}
    padded = {**_sidecar(), "gate_status_after_answer": "CLOSED"}  # G1 gate state, not a G0 field
    chapter = _h2(_model(), _journal(tmp_path / "j.jsonl"), records=(padded,))
    finding = chapter["answer_crosscheck"]["findings"][0]
    assert (finding["field"], finding["unmet"]) == ("payload", ["ANSWER_SHAPE_MISMATCH"])


def test_v4_r2_field_hashes_are_strict_canonical_json():
    """F3: no ``default=str``. A non-JSON value is a typed failure, never a stringified match."""
    from types import SimpleNamespace as NS

    from inference.framework import answer_shapes, product_origins

    for value in (object(), {1, 2}, float("nan"), {"when": pathlib.Path("x")}):
        with pytest.raises(answer_shapes.AnswerProjectionError) as caught:
            answer_shapes.sha16(value)
        assert caught.value.code == "NON_JSON_VALUE"
    assert answer_shapes.sha16(("a", 1)) == answer_shapes.sha16(["a", 1])  # what ordinary JSON already does
    product = NS(product_id="G0-A", product_type="ActionSurface", payload={**G0_PAYLOAD, "semantic_claims": {"x"}})
    entry = product_origins.entry(NS(), "G0-ACTION-METADATA", product)
    assert (entry["origin"], entry["basis"], entry["answers"]) == ("UNATTRIBUTED", "NON_JSON_ANSWER_FIELD", [])


def test_v4_r2_the_shape_table_names_every_field_of_every_accepted_answer():
    from dataclasses import fields

    from inference.framework import answer_shapes
    from inference.framework.g4_orbits import LeverOrbitAnswer
    from inference.framework.g4_reactions import LeverReactionAnswer
    from inference.framework.g4_relations import NO_CHANGE, UNCHANGED, Prediction, RelationsAnswer
    from inference.framework.lever_dossier import LeverDossierAnswer
    from inference.framework.virelai_gates import ActionMetadataAnswer, CounterAnswer, GateAnswer

    classes = {"ACTION_SURFACE_ANSWER": ActionMetadataAnswer, "EGO_ANSWER": GateAnswer,
               "COUNTER_ANSWER": CounterAnswer, "G3_INVENTORY_ANSWER": GateAnswer, "G3_REACHABILITY_ANSWER": GateAnswer,
               "G3_DOSSIER_ANSWER": LeverDossierAnswer, "LEVER_REACTION_ANSWER": LeverReactionAnswer,
               "LEVER_ORBIT_ANSWER": LeverOrbitAnswer, "RELATIONS_ANSWER": RelationsAnswer,
               "RECORD_RELATIONS_ANSWER": RelationsAnswer, "LEVER_PREDICTION": Prediction}
    assert set(classes) == set(answer_shapes.SHAPES)
    for shape, cls in classes.items():
        assert set(answer_shapes.SHAPES[shape]) == {f.name for f in fields(cls)}, shape
    assert (answer_shapes.UNCHANGED, answer_shapes.SHAPES["LEVER_PREDICTION"]["elsewhere"][2]) == (UNCHANGED, NO_CHANGE)


def test_v4_r2_the_sidecar_gate_state_is_exactly_what_the_recorder_adds(tmp_path):
    from dataclasses import asdict
    from types import SimpleNamespace as NS

    from inference.agent.gate_artifacts import record_gate_answer
    from inference.framework import answer_shapes
    from inference.framework.virelai_gates import ActionMetadataAnswer

    answer = ActionMetadataAnswer(**G0_PAYLOAD)
    snapshot = {"status": "S", "coverage_certificate": {}, "pending_prediction": None, "ego_law": None,
                "candidate": None}
    machine = NS(ego=NS(snapshot=lambda: snapshot), counter=NS(snapshot=lambda: snapshot))
    state = tmp_path / f"g_p0_{RUNTIME_STATE_FILENAME}"
    for gate in ("G1-EGO", "G2-COUNTER", "G0-ACTION-METADATA"):
        record_gate_answer(state, machine, gate, answer, executor="CONTROLLER")
    lines = [json.loads(line) for line in (tmp_path / "g_p0_gate_answers.jsonl").read_text().splitlines()]
    for line in lines:
        added = set(line) - set(asdict(answer))
        assert added == answer_shapes.SIDECAR_BOOKKEEPING | answer_shapes.SIDECAR_GATE_STATE.get(line["gate_id"], set())


def test_v4_r2_an_ego_law_id_is_derived_from_its_answer_id():
    from inference.framework.ego_verification import ego_law_from_interface
    from inference.framework.product_origins import ego_law_id

    law = ego_law_from_interface({"answer_id": "G1-X", "action_laws": {"ACTION6": "selects a site"}},
                                 prerequisite_ref="G0-ACTION-METADATA")
    assert law.law_id == ego_law_id("G1-X") != ego_law_id("G1-Y")


def test_v4_r2_an_answer_certified_product_without_its_answer_stays_incomplete(controller_session, monkeypatch):
    """The real run's G1 and G2 products: no retained answer, or one the product does not derive from, is
    UNATTRIBUTED; a retained answer whose admission is missing from the journal joins nothing."""
    from dataclasses import replace

    from inference.framework import provenance_chapter
    from inference.framework.provenance_hooks import product_answers

    machine = controller_session.agent._gate_machine
    origin = {e["product_type"]: e for e in product_answers(machine).values()}
    assert (origin["EgoLaw"]["origin"], origin["CounterGateProduct"]["origin"]) == ("ANSWER_CERTIFIED",) * 2
    monkeypatch.setattr(machine.ego, "answer", None)
    monkeypatch.setattr(machine.counter, "answer", replace(machine.counter.answer, mechanism="another mechanism"))
    origin = {e["product_type"]: e for e in product_answers(machine).values()}
    assert (origin["EgoLaw"]["origin"], origin["EgoLaw"]["basis"]) == ("UNATTRIBUTED", "NO_RETAINED_ANSWER")
    assert (origin["CounterGateProduct"]["basis"]) == "ANSWER_DOES_NOT_DERIVE_PRODUCT"
    model = controller_session.model
    rows = [row for row in model["provenance"]["rows"]
            if not (row["operation"] == "ANSWER" and row["gate_id"] == "G1-EGO")]
    derived = provenance_chapter.derive(model, rows, "SEALED", [])
    lost = [j for j in derived["reconciliation"]["product_joins"] if j["product_type"] == "EgoLaw"]
    assert [j["status"] for j in lost] == ["NO_ADMITTED_ANSWER"]
    assert "PRODUCT_WITHOUT_ADMITTED_ANSWER" in {f["code"] for f in derived["reconciliation"]["findings"]}


def _law_world():
    from test_g4b_relations import start_g4b
    from test_g4c_law import _described

    machine, world = start_g4b()
    _described(machine, world)
    return machine, world


def _level_with(model, product_id, entry):
    level = model["levels"][0]
    level["receipts"]["products"] = {product_id: {"gate_id": entry["gate_id"], "product_type": entry["product_type"],
                                                  "revision": 1, "payload_sha256": "0" * 64}}
    level["product_answers"] = {product_id: entry}
    return model


def test_v4_r2_a_supported_law_set_joins_its_exact_admitted_prediction(tmp_path):
    from dataclasses import asdict

    from inference.framework.provenance_hooks import product_answers
    from test_g4b_relations import _click, _take
    from test_g4c_law import LAW

    machine, world = _law_world()
    raw = {"answer_kind": "LAW_PREDICTION", "from_relations": [0], "action": _click("E0055"),
           "expected": {"E0055": "steps"}, "elsewhere": "NO_CHANGE", "because": "relation 0 says E0055 steps alone"}
    effective = machine.prepare_answer(raw)
    accepted = asdict(machine.submit_prepared(effective, executor="DUCK"))
    _take(machine, world)
    product = machine.target_journal.active_product(LAW)
    entry = product_answers(machine)[product.product_id]
    assert (entry["origin"], entry["basis"], [a["answer_id"] for a in entry["answers"]]) == (
        "ANSWER_CERTIFIED", "LAW_TEST_IS_CERTIFIED_PREDICTION", ["L1"])
    model = _level_with(_model(), product.product_id, entry)
    sidecar = {"schema": "virelai-cybernetic-gates-v1", "gate_id": LAW, "executor": "DUCK", **accepted}

    def chapter(payload, name):
        row = {**_answer(payload, gate=LAW, answer_id="L1"), "executor": "DUCK"}
        return _h2(model, _journal(tmp_path / name, answers=0, extra=[row]), records=(sidecar,))

    exact = chapter(effective, "a.jsonl")
    assert [j["status"] for j in exact["reconciliation"]["product_joins"]] == ["EXACT"]
    assert exact["completeness"] == "COMPLETE"
    for name, altered in (("b.jsonl", {**effective, "expected": {"E0055": "UNCHANGED"}}),
                          ("c.jsonl", {key: value for key, value in effective.items() if key != "because"})):
        assert [j["status"] for j in chapter(altered, name)["reconciliation"]["product_joins"]] == [
            "NO_ADMITTED_ANSWER"]


@pytest.mark.parametrize("closure", ["level_boundary", "unresolved"])
def test_v4_r2_a_law_closed_without_a_test_is_gate_derived_and_claims_no_answer(tmp_path, closure):
    from inference.framework.provenance_hooks import product_answers
    from test_g4c_law import LAW

    machine, _world = _law_world()
    adapter = machine._adapters[LAW]
    if closure == "level_boundary":
        adapter._level_closed = {"evidence_ref": "E-boundary", "level_before": 1, "level_after": 2}
        adapter._emit_product()
    else:
        adapter.close_unresolved("test: Duck's G4-C budget is spent")
    product = machine.target_journal.active_product(LAW)
    entry = product_answers(machine)[product.product_id]
    basis = "LAW_CLOSED_BY_LEVEL_BOUNDARY" if closure == "level_boundary" else "LAW_UNRESOLVED"
    assert (entry["origin"], entry["basis"], entry["answers"]) == ("GATE_DERIVED", basis, [])
    chapter = _h2(_level_with(_model(), product.product_id, entry), _journal(tmp_path / "j.jsonl", answers=0),
                  records=())
    join = chapter["reconciliation"]["product_joins"][0]
    assert (join["status"], join["answer_id"], join["answer_event_id"]) == ("GATE_DERIVED", None, None)
    assert chapter["completeness"] == "COMPLETE"


def test_v4_r2_gate_derived_is_only_the_declared_closures():
    from types import SimpleNamespace as NS

    from inference.framework import product_origins

    def origin(product_type, payload):
        entry = product_origins.entry(NS(ego=NS(answer=None), counter=NS(answer=None), _adapters={}), "G",
                                      NS(product_id="P", product_type=product_type, payload=payload))
        return entry["origin"], entry["basis"]

    assert origin("LeverReactionLawSet", {"status": "CLOSED_BY_LEVEL_BOUNDARY", "law_test": {"x": 1},
                                          "level_boundary": {"evidence_ref": "E"}}) == ("UNATTRIBUTED",
                                                                                         "NO_DECLARED_CLOSURE")
    assert origin("LeverReactionLawSet", {"status": "CLOSED_BY_LEVEL_BOUNDARY", "law_test": None,
                                          "level_boundary": None}) == ("UNATTRIBUTED", "NO_DECLARED_CLOSURE")
    assert origin("CounterGateProduct", {"product_kind": "COUNTER_NOT_OBSERVED", "counter_model": {"m": 1},
                                         "search_disposition": {"scope": "S"}}) == ("UNATTRIBUTED",
                                                                                    "NO_DECLARED_CLOSURE")
    assert origin("EgoLaw", {"law_id": "EL-x"}) == ("UNATTRIBUTED", "NO_RETAINED_ANSWER")
    assert origin("SomethingNew", {}) == ("UNATTRIBUTED", "UNREGISTERED_PRODUCT_TYPE")


def test_v4_r2_a_counter_search_with_no_counter_is_a_declared_gate_derived_product():
    from inference.framework.provenance_hooks import product_answers
    from test_counter_gate import duck_choice, g2_machine

    machine = g2_machine()
    transition_id = 0
    while machine.counter.status == "ACTIVE":
        transition_id += 1
        capability = machine.next_probe_capability()
        actions = duck_choice(capability)
        probe = machine.validate_probe({"probe_token": capability["probe_token"]}, actions)
        machine.record_outcome(probe, {
            "transition_id": transition_id, "shape_before": [4, 6], "shape_after": [4, 6], "action": actions[0],
            "acted_site": {"row": actions[0]["row"], "col": actions[0]["col"]}, "board_changed": False,
            "changed_cell_count": 0, "changed_cells": [], "boundary_event": {"state": "PLAYING"}})
    product = machine.target_journal.active_product("G2-COUNTER")
    assert product.payload["product_kind"] == "COUNTER_NOT_OBSERVED"
    entry = product_answers(machine)[product.product_id]
    assert (entry["origin"], entry["basis"], entry["answers"]) == ("GATE_DERIVED", "COUNTER_NOT_OBSERVED", [])


# ---- 11 · revision 3 (Sol, REVIEW_WO_PE_02 v2 §3-§5): record-derived relations, retained state, two real levels -----

def _record_certified():
    """The real G4-B gate certifying its relations from the level's record (the controller's answer)."""
    from dataclasses import asdict

    from test_g4b_relations import start_g4b

    machine, _world = start_g4b()
    effective = machine.prepare_answer({"answer_kind": "LEVER_RELATIONS_FROM_RECORD"})
    accepted = asdict(machine.submit_prepared(effective, executor="CONTROLLER"))
    product = machine.target_journal.active_product("G4-B-LEVER-RELATIONS")
    return machine, product, effective, accepted


@pytest.mark.parametrize("mutation", ["none", "description", "relations", "limitation", "record_and_answer_together"])
def test_v4_r3_a_record_derived_relation_answer_is_rebuilt_in_full_from_its_record(tmp_path, mutation):
    """F4: same answer id, altered content, must not stay ANSWER_CERTIFIED. A record and answer altered together are
    caught by the record's content-addressed id."""
    from types import SimpleNamespace as NS

    from inference.framework import product_origins

    machine, product, effective, accepted = _record_certified()
    payload = copy.deepcopy(product.payload)
    answer, record = payload["answer"], payload["from_record"]
    assert answer["answer_id"] == record["answer_id"] and payload["certified_by"] == "RECORD"
    if mutation == "description":
        answer["description"] += " Altered."
    elif mutation == "relations":
        answer["relations"] = list(answer["relations"])[1:]
    elif mutation == "limitation":
        answer["limitations"] = ["an altered epistemic limit"]
    elif mutation == "record_and_answer_together":
        record["description"] = answer["description"] = answer["description"] + " Altered in both."
    entry = product_origins.entry(machine, "G4-B-LEVER-RELATIONS", NS(product_id=product.product_id,
                                                                      product_type=product.product_type,
                                                                      payload=payload))
    gate = "G4-B-LEVER-RELATIONS"
    row = {**_answer(effective, gate=gate, answer_id=accepted["answer_id"])}
    sidecar = {"schema": "virelai-cybernetic-gates-v1", "gate_id": gate, "executor": "CONTROLLER", **accepted}
    chapter = _h2(_level_with(_model(), product.product_id, entry),
                  _journal(tmp_path / "j.jsonl", answers=0, extra=[row]), records=(sidecar,))
    join = chapter["reconciliation"]["product_joins"][0]
    if mutation == "none":
        assert (entry["origin"], entry["basis"]) == ("ANSWER_CERTIFIED", "RELATIONS_CERTIFIED_FROM_RECORD")
        assert join["status"] == "EXACT" and chapter["completeness"] == "COMPLETE"
    else:
        assert (entry["origin"], entry["basis"]) == ("UNATTRIBUTED", "ANSWER_DOES_NOT_DERIVE_PRODUCT")
        assert join["status"] == "UNATTRIBUTED" and "PRODUCT_UNATTRIBUTED" in chapter["reasons"]
        assert chapter["completeness"] == "INCOMPLETE"


@pytest.mark.parametrize("mutation", ["ego_law_payload", "ego_law_retained", "counter_model_payload",
                                      "mask_law_payload", "mask_law_retained"])
def test_v4_r3_the_g1_law_and_the_g2_model_and_mask_must_equal_the_retained_state(controller_session, monkeypatch,
                                                                                    mutation):
    """§5: census-time comparisons only (no gate method is called). The real run's products, one field changed in
    the product or in the gate's retained state, become UNATTRIBUTED; unchanged, they stay certified."""
    from dataclasses import replace
    from types import SimpleNamespace as NS

    from inference.framework import product_origins

    machine = controller_session.agent._gate_machine
    products = {p.product_type: p for p in (machine.target_journal.active_product(c.target_id)
                                            for c in machine.target_registry.ordered()) if p is not None}
    gate = {"EgoLaw": "G1-EGO", "CounterGateProduct": "G2-COUNTER"}

    def origin(product_type, payload=None):
        product = products[product_type]
        shown = NS(product_id=product.product_id, product_type=product_type,
                   payload=product.payload if payload is None else payload)
        entry = product_origins.entry(machine, gate[product_type], shown)
        return entry["origin"], entry["basis"]

    assert origin("EgoLaw") == ("ANSWER_CERTIFIED", "EGO_LAW_DERIVED_FROM_ANSWER")
    assert origin("CounterGateProduct") == ("ANSWER_CERTIFIED", "COUNTER_MODEL_COPIES_ANSWER")
    changed = ("UNATTRIBUTED", "PRODUCT_DIFFERS_FROM_RETAINED_STATE")
    if mutation == "ego_law_payload":
        payload = {**products["EgoLaw"].payload, "limitations": ["a limitation the retained law does not state"]}
        assert origin("EgoLaw", payload) == changed
    elif mutation == "ego_law_retained":
        monkeypatch.setattr(machine.ego, "ego_law", replace(machine.ego.ego_law, mode="ANOTHER_MODE"))
        assert origin("EgoLaw") == changed
    elif mutation == "counter_model_payload":  # a model field the answer does not supply
        payload = copy.deepcopy(products["CounterGateProduct"].payload)
        payload["counter_model"]["status"] = "ANOTHER_STATUS"
        assert origin("CounterGateProduct", payload) == changed
    elif mutation == "mask_law_payload":
        payload = copy.deepcopy(products["CounterGateProduct"].payload)
        payload["mask_law"] = {**payload["mask_law"], "law_id": "ANOTHER-MASK"}
        assert origin("CounterGateProduct", payload) == changed
    else:
        monkeypatch.setattr(machine.counter, "mask_law", None)
        assert origin("CounterGateProduct") == changed


class _TwoLevelGame:
    """The ft09 continuation behind the harness's game interface, with one level boundary: the K-th action completes
    level 1 and the board starts again as level 2 (``levels_completed`` 0 -> 1, ``just_won_level``)."""

    BOUNDARY = 20

    def __init__(self) -> None:
        from test_g3_directed_click import _Ft09Game

        self._inner = _Ft09Game()
        self.world, self.game_run = self._inner.world, self._inner.game_run
        self.number_of_levels = self.game_run.number_of_levels = 2
        self.completed, self.just_won = 0, False
        self.current_state = self._state()

    def _state(self):
        self._inner.world = self.world
        state = self._inner._state()
        state.raw.levels_completed, state.raw.win_levels = self.completed, 2
        state.levels_completed, state.just_won_level = self.completed, self.just_won
        return state

    def execute_action(self, action, *, generated_tokens, uncached_input_tokens):
        from ft09_world import Ft09World

        del generated_tokens, uncached_input_tokens
        self.world.step({"action": action.id.name, "row": int(action.data["y"]), "col": int(action.data["x"])})
        self.game_run.history.append(SimpleNamespace(action=action))
        self.just_won = False
        if self.world.transition_id == self.BOUNDARY and self.completed == 0:
            transition, self.world = self.world.transition_id, Ft09World()
            self.world.transition_id = transition
            self.completed, self.just_won, self.game_run.levels_completed = 1, True, 1
        self.current_state = self._state()
        return self.current_state

    def finish_game(self):
        self.game_run.final_score = 0.0


@pytest.fixture(scope="module")
def two_level_session(tmp_path_factory):
    """The production session (real ToolAgent, controller executor, provenance capture) across one real boundary:
    H1 freezes level 1 and writes the interim model; level 2 runs its own ladder; H2 seals and compiles."""
    from inference.agent.tool_agent import _ChatCompletionResult
    from inference.framework import world_model_v2

    patch = pytest.MonkeyPatch()
    writes = []
    original = world_model_v2.write_canonical
    patch.setattr(world_model_v2, "write_canonical", lambda payload, directory: writes.append(
        (payload["manifest"]["persist_reason"], payload["provenance"]["phase"])) or original(payload, directory))
    session, agent, folder = _session(tmp_path_factory.mktemp("v4_two_levels"))
    session.game = _TwoLevelGame()
    agent._controller.g3_choice_handoff = False

    def duck(messages, **kwargs):
        session.solver.max_actions_per_game = session.action_count
        return _ChatCompletionResult(message={"role": "assistant", "content": "Weighing the rows."})

    agent._chat_completion = duck
    session.play()
    patch.undo()
    return SimpleNamespace(model=_model_of(folder), writes=writes, agent=agent)


def test_v4_r3_a_real_two_level_run_joins_each_product_only_to_its_own_levels_admission(two_level_session):
    """§4: level 1 frozen by the real H1 path, level 2 built fresh, H2 sealed and compiled. Each product joins an
    admission recorded on its own level; the ids level 2 shares with level 1 join level 2's own events."""
    model, chapter = two_level_session.model, two_level_session.model["provenance"]
    assert two_level_session.writes == [("LEVEL_ADVANCE", "H1"), ("BUDGET_STOP", "H2")]
    assert [level["level"] for level in model["levels"]] == [1, 2]
    assert [p["status"] for p in chapter["interim_prefixes"]] == ["VERIFIED"]  # H1's writer prefix, checked at H2
    assert (chapter["integrity"], chapter["completeness"], chapter["reasons"]) == ("SEALED", "COMPLETE", [])
    rows = {row["event_id"]: row for row in chapter["rows"]}
    joins = chapter["reconciliation"]["product_joins"]
    assert {j["level"] for j in joins} == {1, 2} and all(j["status"] == "EXACT" for j in joins)
    for join in joins:
        answer = rows[join["answer_event_id"]]
        assert (answer["level"], answer["gate_id"], answer["refs"]["answer_id"]) == (
            join["level"], join["gate_id"], join["answer_id"])
    shared = {j["answer_id"] for j in joins if j["level"] == 1} & {j["answer_id"] for j in joins if j["level"] == 2}
    assert shared  # the same answer ids recur on level 2 (G0, G1) ...
    for answer_id in shared:  # ... and each level's product joins its own, distinct admission
        events = {j["level"]: j["answer_event_id"] for j in joins if j["answer_id"] == answer_id}
        assert events[1] != events[2]


def test_v4_r3_a_level_two_product_never_borrows_a_level_one_admission(two_level_session):
    """With level 2's own G0 admission gone, level 2's G0 product joins nothing (the level-1 admission of the same id
    is not borrowed), while level 1's product still joins its own."""
    from inference.framework import provenance_chapter

    model = two_level_session.model
    rows = model["provenance"]["rows"]
    dropped = [row for row in rows if not (row["operation"] == "ANSWER" and row["level"] == 2
                                           and row["gate_id"] == "G0-ACTION-METADATA")]
    assert len(dropped) == len(rows) - 1
    derived = provenance_chapter.derive(model, dropped, "SEALED", [])
    g0 = {j["level"]: j for j in derived["reconciliation"]["product_joins"] if j["product_type"] == "ActionSurface"}
    assert g0[2]["status"] == "NO_ADMITTED_ANSWER" and g0[2]["candidates"] == []
    assert g0[1]["status"] == "EXACT" and {r["event_id"]: r for r in rows}[g0[1]["answer_event_id"]]["level"] == 1
