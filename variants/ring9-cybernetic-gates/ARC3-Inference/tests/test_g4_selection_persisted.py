"""WO-G4-DOSSIER-B, B2 revision 3: the saved v8 model enforces admitted question → selected-run receipts → chapter.

Author: Claude (Alpha build seat), 2026-10-18. Sol's review of B2 revision 2: the question-to-dossier check ran only on
live gate state in a test; the canonical v8 validator never invoked it. Revision 3 makes it a v8 validation step
(``lever_dossier_selection``) over the persisted audit rows and the level receipt index.

The artifact: the controller-driven ft09 ladder (``g4_no_choice_trace.Drive``) with Duck's G4-A choice of E0057 on
E0053's explanation turn, sealed at H2 as a v8 model embedding an audit-v2 journal of the machine's G4 selection
events. Each attack forges that canonical artifact and recomputes everything a forger can — the audit chain (event
ids, hashes, seal), the chapter stamp and indexes, and the model hash — then reads it with ``read_world_model``.
"""
from __future__ import annotations

import pickle
import tempfile
from pathlib import Path

import pytest

ORBITS = "G4.2-LEVER-ORBITS"
RUN = {"run_stem": "g_p0", "game_id": "g"}
SIDECAR = "g_p0_provenance.jsonl"
_CACHE: dict[str, bytes] = {}


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


def _unsealed(machine, persist_reason: str = "RUN_END") -> dict:
    """The H2 census of the machine, unsealed (``dossier_fixtures.compiled`` without its seal)."""
    from inference.framework.library_census import ExecutionRecord, compile_world_model

    board = tuple(tuple(int(cell) for cell in row) for row in machine.ego._initial_grid)
    rows = sorted(machine.transition_index, key=lambda row: int(row["transition_id"]))
    executed = tuple(str((row.get("action") or {}).get("action") or "") for row in rows)
    return compile_world_model(
        machine, ExecutionRecord(board, int(machine.lives.level), tuple(a.action for a in machine.ego.affordances),
                                 executed), game_id=RUN["game_id"], run_stem=RUN["run_stem"], persist_reason=persist_reason,
        frozen_levels=list(getattr(machine, "level_censuses", ()) or ()), reconcile_journal=False)


def journal_bytes(contents) -> bytes:
    """A sealed audit-v2 journal of ``contents`` (audit rows' content), chained and hashed by the real writer."""
    from inference.framework import audit_journal as aj

    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / SIDECAR
        written = aj.ProvenanceJournal.open(path, run_stem=RUN["run_stem"], game_id=RUN["game_id"])
        for content in contents:
            assert written.append(content) is not None, written.failed
        assert written.seal()
        return path.read_bytes()


def sealed_unvalidated(unsealed: dict, data: bytes) -> dict:
    """What ``world_model_v2.seal`` builds — chapter, indexes, dossier reconciliation, win episodes (v10), schema and
    hash — without its final validation: a forger's best artifact, for ``read_world_model`` to judge."""
    from inference.framework import provenance_chapter as pc
    from inference.framework.lever_dossier_provenance import reconcile
    from inference.framework.win_episode import reconcile as reconcile_episodes

    wm = _wm()
    chapter = pc.h2(unsealed, data=data, sidecar=SIDECAR, capture="ENABLED", answer_records=None)
    model = reconcile(pc.attach({**unsealed, "provenance": chapter}))
    model["levels"] = reconcile_episodes(model["levels"])
    model["schema"] = wm.SCHEMA
    model["content_sha256"] = wm.content_sha256(model)
    return model


def _translated(machine) -> list[dict]:
    from inference.framework import audit_journal as aj

    return [aj.translate_g4_event(event) for event in machine.g4_selection_events]


def chosen_run():
    """(machine, unsealed model): E0057 chosen on E0053's explanation turn, its run confirmed and explained."""
    if "chosen" not in _CACHE:
        from test_g4_selection import _at_explanation, _qid, _until_duck

        drive = _at_explanation()
        machine = drive.machine
        machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
        drive.duck_turn(None)
        _until_duck(drive)
        drive.duck_turn(None)
        _CACHE["chosen"] = pickle.dumps((machine, _unsealed(machine)))
    return pickle.loads(_CACHE["chosen"])


def _refused(model: dict, match: str) -> None:
    with pytest.raises(_wm().WorldModelV2Error, match=match):
        _wm().read_world_model(model)


def _level(model: dict) -> dict:
    return next(level for level in model["levels"] if level["state"] == "OPEN")


# ---- the genuine artifacts ---------------------------------------------------------------------------------------

def test_r3_01_the_genuine_chain_reads_and_its_derived_question_closes_it():
    from inference.framework import lever_dossier_selection as sel

    machine, unsealed = chosen_run()
    model = sealed_unvalidated(unsealed, journal_bytes(_translated(machine)))
    _wm().read_world_model(model)
    rows = [row for row in model["provenance"]["rows"] if row["operation"] == "G4_SELECTION"]
    assert [row["refs"]["source_event"]["event"] for row in rows] == ["ADMITTED", "FINISHED"]
    derived = sel.dossier_question(1, "E0057", "orbit")
    assert {row["refs"]["question_id"] for row in rows} == {derived} == {"Q:L1:G4.2-LEVER-ORBITS:E0057:ORBIT"}
    orbit = _level(model)["lever_dossiers"]["E0057"]["chapters"]["orbit"]
    evidence = _level(model)["receipts"]["evidence"]
    cited = [evidence[ref]["probe_id"] for ref in orbit["evidence_refs"]]
    assert cited and all(probe.startswith(sel.selected_run(1, 1, "E0057", 1)) for probe in cited)
    assert sel.problems(model) == []


def test_r3_02_ordinary_coverage_needs_no_selected_probe_id():
    """Rule 4: the no-choice ladder (G4.1 → G4-C, every chapter by coverage) is valid with an empty G4 journal."""
    from g4_no_choice_trace import Drive

    machine = Drive().run().machine
    model = sealed_unvalidated(_unsealed(machine), journal_bytes([]))
    _wm().read_world_model(model)
    orbits = [d["chapters"]["orbit"] for d in _level(model)["lever_dossiers"].values()]
    assert all(chapter["evidence_refs"] for chapter in orbits)
    probes = [e["probe_id"] for e in _level(model)["receipts"]["evidence"].values()]
    assert not any(":SEL:" in str(probe) for probe in probes)


# ---- the attacks: each forged, fully rehashed v8 artifact is refused by read_world_model -------------------------

def test_r3_03_a_changed_selection_question_is_refused_even_with_the_chain_and_hashes_recomputed():
    machine, unsealed = chosen_run()
    forged = _translated(machine)
    for row in forged:  # both rows, so the pair still matches: only the derivation can refuse it
        row["refs"] = {**row["refs"], "question_id": "Q:L1:G4.2-LEVER-ORBITS:E0054:ORBIT"}
    _refused(sealed_unvalidated(unsealed, journal_bytes(forged)), "not the question derived from level, G4-A, E0057")


def test_r3_04_a_selected_receipt_naming_another_lever_is_refused():
    machine, unsealed = chosen_run()
    model = sealed_unvalidated(unsealed, journal_bytes(_translated(machine)))
    level = _level(model)
    ref = level["lever_dossiers"]["E0057"]["chapters"]["orbit"]["evidence_refs"][0]
    receipt = level["receipts"]["evidence"][ref]
    receipt["probe_id"] = receipt["probe_id"].replace(":SEL:E0057:", ":SEL:E0054:")
    model["content_sha256"] = _wm().content_sha256(model)
    _refused(model, "a selected-run receipt of E0054")


def test_r3_05_a_completed_chapter_without_the_selected_runs_evidence_is_refused():
    """The forger rewrites every receipt of the selected run as an ordinary coverage probe: the chapter still cites
    four receipts, none of the run the FINISHED selection says reached it."""
    machine, unsealed = chosen_run()
    model = sealed_unvalidated(unsealed, journal_bytes(_translated(machine)))
    level = _level(model)
    for ref in level["lever_dossiers"]["E0057"]["chapters"]["orbit"]["evidence_refs"]:
        receipt = level["receipts"]["evidence"][ref]
        receipt["probe_id"] = f"{ORBITS}:GUIDED:{receipt['probe_id'].rsplit(':', 1)[1]}"
    model["content_sha256"] = _wm().content_sha256(model)
    _refused(model, "orbit chapter cites no receipt of the selected run")


def test_r3_05_removing_the_selected_run_from_the_chapter_itself_is_refused():
    from inference.framework import lever_dossiers

    machine, unsealed = chosen_run()
    model = sealed_unvalidated(unsealed, journal_bytes(_translated(machine)))
    orbit = _level(model)["lever_dossiers"]["E0057"]["chapters"]["orbit"]
    orbit["evidence_refs"] = []
    orbit["digest"] = lever_dossiers.chapter_digest("E0057", "orbit", orbit)
    model["content_sha256"] = _wm().content_sha256(model)
    _refused(model, "evidence_refs")


def test_r3_06_a_finished_selection_without_its_admission_is_refused():
    machine, unsealed = chosen_run()
    forged = [row for row in _translated(machine) if row["refs"]["source_event"]["event"] != "ADMITTED"]
    _refused(sealed_unvalidated(unsealed, journal_bytes(forged)), "closes no matching earlier ADMITTED selection")


def test_r3_07_a_finished_selection_of_another_lever_than_its_admission_is_refused():
    machine, unsealed = chosen_run()
    forged = _translated(machine)
    forged[-1]["refs"] = {**forged[-1]["refs"], "subject": "E0054",
                          "question_id": "Q:L1:G4.2-LEVER-ORBITS:E0054:ORBIT"}
    _refused(sealed_unvalidated(unsealed, journal_bytes(forged)), "closes no matching earlier ADMITTED selection")


def test_r3_08_the_frozen_v7_reader_never_runs_the_v8_rule(monkeypatch):
    import json

    from inference.framework import lever_dossier_selection as sel

    calls = []
    monkeypatch.setattr(sel, "problems", lambda payload: calls.append(payload["schema"]) or [])
    v7 = json.loads((Path(__file__).parent / "fixtures" / "world_model_v7_frozen.json").read_text())
    _wm().validate_v7(v7)
    assert _wm().read_world_model(v7)["schema"] == _wm().V7_SCHEMA and calls == []
    machine, unsealed = chosen_run()
    _wm().read_world_model(sealed_unvalidated(unsealed, journal_bytes(_translated(machine))))
    assert calls == [_wm().SCHEMA]


# ---- revision 4 (Sol's review of revision 3): the selection log is a state machine ---------------------------------

def _rows_named(rows, event):
    return [row for row in rows if row["refs"]["source_event"]["event"] == event]


def _with(row, **refs_and_fields):
    refs = {key: value for key, value in refs_and_fields.items() if key in ("question_id", "subject")}
    fields = {key: value for key, value in refs_and_fields.items() if key not in refs}
    return {**row, **fields, "refs": {**row["refs"], **refs}}


def admitted_only():
    """(machine, unsealed BUDGET_STOP model): E0057 admitted on E0053's explanation turn; the run stops before it runs."""
    if "admitted" not in _CACHE:
        from test_g4_selection import _at_explanation, _qid

        machine = _at_explanation().machine
        machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
        _CACHE["admitted"] = pickle.dumps((machine, _unsealed(machine, "BUDGET_STOP")))
    return pickle.loads(_CACHE["admitted"])


def test_r4_01_a_valid_open_admission_at_a_budget_stop_is_accepted():
    machine, unsealed = admitted_only()
    rows = _translated(machine)
    assert [row["refs"]["source_event"]["event"] for row in rows] == ["ADMITTED"]
    model = sealed_unvalidated(unsealed, journal_bytes(rows))
    assert model["manifest"]["persist_reason"] == "BUDGET_STOP"
    _wm().read_world_model(model)


def test_r4_02_an_open_admission_with_a_forged_question_is_refused_with_no_finished_row():
    machine, unsealed = admitted_only()
    forged = [_with(row, question_id="Q:L1:G4.2-LEVER-ORBITS:E0054:ORBIT") for row in _translated(machine)]
    _refused(sealed_unvalidated(unsealed, journal_bytes(forged)),
             "ADMITTED selection .* not the question derived from level, G4-A, E0057")


def test_r4_03_an_open_admission_must_name_g4a_a_held_level_and_a_lever_with_a_dossier():
    machine, unsealed = admitted_only()
    (row,) = _translated(machine)
    for forged, match in ((_with(row, gate_id="G4-REACTIONS"), "ADMITTED selection .* is not G4-A's"),
                          (_with(row, level=7, question_id="Q:L7:G4.2-LEVER-ORBITS:E0057:ORBIT"), "level this model"),
                          (_with(row, subject="E9999", question_id="Q:L1:G4.2-LEVER-ORBITS:E9999:ORBIT"),
                           "has no dossier")):
        _refused(sealed_unvalidated(unsealed, journal_bytes([forged])), match)


def test_r4_04_a_finished_selection_in_another_life_is_refused():
    machine, unsealed = chosen_run()
    rows = _translated(machine)
    rows[-1] = _with(rows[-1], life=2)
    _refused(sealed_unvalidated(unsealed, journal_bytes(rows)), "closes no matching earlier ADMITTED selection.*life")


def test_r4_05_a_finished_selection_by_another_executor_is_refused():
    machine, unsealed = chosen_run()
    rows = _translated(machine)
    rows[-1] = _with(rows[-1], executor="CONTROLLER")
    _refused(sealed_unvalidated(unsealed, journal_bytes(rows)), "closes no matching earlier ADMITTED selection.*executor")


def test_r4_06_a_second_admission_before_the_first_is_closed_is_refused():
    """Revision 3 let a later ADMITTED row silently replace an open one. A STALE row closing the first makes the
    same sequence valid (the second choice may then stay open at the stop)."""
    from inference.framework import audit_journal as aj

    machine, unsealed = chosen_run()
    admitted = _translated(machine)[0]
    second = _with(admitted, subject="E0060", question_id="Q:L1:G4.2-LEVER-ORBITS:E0060:ORBIT")
    _refused(sealed_unvalidated(unsealed, journal_bytes([admitted, second])), "second ADMITTED selection")
    stale = aj.translate_g4_event({**machine.g4_selection_events[0], "event": "STALE", "reason": "replaced"})
    _wm().read_world_model(sealed_unvalidated(unsealed, journal_bytes([admitted, stale, second])))


def test_r4_07_an_orphan_stale_selection_is_refused():
    from inference.framework import audit_journal as aj

    machine, unsealed = chosen_run()
    stale = aj.translate_g4_event({**machine.g4_selection_events[0], "event": "STALE", "entity_id": "E0060",
                                   "question_id": "Q:L1:G4.2-LEVER-ORBITS:E0060:ORBIT", "reason": "forged"})
    _refused(sealed_unvalidated(unsealed, journal_bytes([stale, *_translated(machine)])),
             "STALE selection .* closes no matching earlier ADMITTED selection")


def test_r4_08_a_death_triggered_stale_keeps_the_choices_own_scope_and_is_accepted():
    """The writer (revision 4): a STALE or FINISHED row describes the choice it closes — the admission's level and
    life — while ``at_transition`` is the transition at which it closed."""
    from inference.framework.record_replay import lossless_outcome, record_like_live
    from test_g4_selection import _at_explanation, _qid

    drive = _at_explanation()
    machine = drive.machine
    machine.select_question(_qid(ORBITS, "E0057"), actor="DUCK")
    drive.duck_turn(None)
    capability = machine.next_probe_capability()
    click = dict(machine._adapters[ORBITS]._interventions["E0054"])  # Duck presses another lever: it kills the life
    probe = machine.validate_probe({"probe_token": capability["probe_token"]}, [click])
    drive.world.transition_id += 1
    boundary = {"game_over": True, "level_before": 1, "level_after": 1, "state": "GAME_OVER"}
    drive.world.grid, outcome = lossless_outcome(drive.world.grid, drive.world.transition_id, click,
                                                 drive.world.changes(click), boundary)
    record_like_live(machine, probe, outcome, drive.world.valid_actions)
    assert machine.transition_index[-1]["probe_id"] == f"{ORBITS}:GUIDED:{machine._adapters[ORBITS]._action_count}"
    assert "question_id" not in machine._adapters[ORBITS]._events[-1]  # E0054's press never names E0057's choice
    drive.world.transition_id += 1
    drive.world.grid, reset = lossless_outcome(drive.world.grid, drive.world.transition_id, {"action": "RESET"}, [],
                                               {"state": "NOT_FINISHED", "actor": "SYSTEM_RESET", "reset": True})
    machine.observe_system_reset(reset)
    assert int(machine.lives.life) == 2
    machine.next_probe_capability()  # the gate's own step settles the choice the new life made stale
    stale = machine.g4_selection_events[-1]
    assert (stale["event"], stale["entity_id"], stale["level"], stale["life"]) == ("STALE", "E0057", 1, 1)
    assert stale["at_transition"] == drive.world.transition_id  # when it closed: in life 2
    rows = _translated(machine)
    assert [(r["refs"]["source_event"]["event"], r["life"]) for r in rows] == [("ADMITTED", 1), ("STALE", 1)]
    _wm().read_world_model(sealed_unvalidated(_unsealed(machine, "BUDGET_STOP"), journal_bytes(rows)))


def test_r4_09_a_source_event_must_fit_its_audit_disposition():
    """A forger cannot relabel an admission row as FINISHED (or the reverse) inside the audit vocabulary."""
    machine, unsealed = chosen_run()
    rows = _translated(machine)
    rows[-1] = {**rows[-1], "event": "ADMISSION", "disposition": "ADMITTED"}
    _refused(sealed_unvalidated(unsealed, journal_bytes(rows)), "does not fit its audit event")


def test_r4_10_a_level_change_closes_an_open_choice_on_the_record_in_its_own_scope():
    """The writer (revision 4): G4-A's study ends with its level, so a choice still open there never outlives it.
    ``_advance_level`` calls this before the level is censused; here it is called directly (no committed record
    changes level during a standing G4-A choice)."""
    from inference.framework import g4_selection

    machine, unsealed = admitted_only()
    g4_selection.close_at_level_change(machine._adapters[ORBITS])
    stale = machine.g4_selection_events[-1]
    assert (stale["event"], stale["entity_id"], stale["reason"], stale["level"], stale["life"]) == (
        "STALE", "E0057", "the level changed", 1, 1)
    assert g4_selection.chosen(machine) is None
    _wm().read_world_model(sealed_unvalidated(unsealed, journal_bytes(_translated(machine))))
