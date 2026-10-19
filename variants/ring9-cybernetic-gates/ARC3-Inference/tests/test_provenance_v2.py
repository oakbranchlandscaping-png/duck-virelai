"""WO-G4-DOSSIER-B, slice B2 revision 2: the audit journal's G4 vocabulary is schema v2, never an amended v1.

Author: Claude (Alpha build seat), 2026-10-18. Sol's review of B2 revision 1 (blocker 2): "Create audit schema v2,
preserve the frozen v1 reader, and measure whether embedding v2 provenance requires a world-model schema bump. Do
not silently amend either schema."

The measurement (``AMENDED_INTERFACE_WO_G4_DOSSIER_B2_v2`` §3): a sealed H2 model embeds the journal's rows verbatim
and re-verifies them (``provenance_chapter._validate_h2`` → ``audit_journal.verify_embedded``). The embedded rows
carry their own audit schema, so a model holding v2 rows breaks the v7 contract: the world model becomes v8, its
provenance chapter ``virelai-provenance-chapter-v2``, and v7 (chapter v1, audit v1 only) is frozen.

Fixtures written by ``0119a74`` code, before any B2 edit: ``provenance_v1_journal.jsonl`` (a sealed v1 journal:
probe admission and execution, an answer and a G3 selection) and ``world_model_v7_frozen.json`` (a sealed H2 v7
model embedding that journal).
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

import dossier_provenance_fixtures as pf

FIXTURES = Path(__file__).parent / "fixtures"
V1_JOURNAL = FIXTURES / "provenance_v1_journal.jsonl"
V7_MODEL = FIXTURES / "world_model_v7_frozen.json"
G4_EVENT = {"schema": "virelai-g4-selection-event-v1", "event": "ADMITTED",
            "question_id": "Q:L1:G4.2-LEVER-ORBITS:E0001:ORBIT", "entity_id": "E0001", "actor": "DUCK",
            "reason": "away from the coverage head", "gate_id": "G4.2-LEVER-ORBITS", "level": 1, "life": 1,
            "at_transition": 1, "gate_revision": 3}


def _aj():
    from inference.framework import audit_journal

    return audit_journal


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


def _v2_journal(folder: Path, events=(G4_EVENT,)) -> bytes:
    return pf.journal(folder, extra=[_aj().translate_g4_event(event) for event in events])


# ---- the audit journal --------------------------------------------------------------------------------------------

def test_pv2_01_the_writer_is_v2_and_v1_is_frozen_with_its_own_vocabulary():
    aj = _aj()
    assert (aj.SCHEMA, aj.V1_SCHEMA) == ("virelai-provenance-v2", "virelai-provenance-v1")
    assert "G4_SELECTION" in aj.VALID and "G4_SELECTION" not in aj.VALID_V1
    assert "G4_EVENT" in aj.REASON_CODES and "G4_EVENT" not in aj.REASON_CODES_V1
    assert {key: aj.VALID[key] for key in aj.VALID_V1} == aj.VALID_V1  # v2 extends v1 and changes nothing in it


def test_pv2_02_an_existing_v1_journal_still_validates_byte_for_byte_under_both_readers():
    aj = _aj()
    data = V1_JOURNAL.read_bytes()
    for read in (aj.read_journal(V1_JOURNAL), aj.read_journal_v1(V1_JOURNAL), aj.read_journal_bytes(data)):
        assert read.status == "SEALED" and read.failure is None and len(read.rows) == 4
        assert b"".join(aj.canonical(row) + b"\n" for row in [*read.rows, read.seal]) == data  # byte for byte
        assert {row["schema"] for row in [*read.rows, read.seal]} == {aj.V1_SCHEMA}


def test_pv2_03_a_v2_journal_holds_g4_selections_and_the_v1_reader_never_reinterprets_it(tmp_path):
    aj = _aj()
    data = _v2_journal(tmp_path)
    read = aj.read_journal_bytes(data)
    assert read.status == "SEALED" and {row["schema"] for row in read.rows} == {aj.SCHEMA}
    (row,) = [item for item in read.rows if item["operation"] == "G4_SELECTION"]
    assert (row["event"], row["disposition"], row["gate_id"]) == ("ADMISSION", "ADMITTED", "G4.2-LEVER-ORBITS")
    frozen = aj.read_journal_v1(tmp_path / pf.SIDECAR)
    assert frozen.status == "CORRUPT" and frozen.rows == [] and frozen.failure["code"] == "SCHEMA_INVALID"
    assert "virelai-provenance-v2" in frozen.failure["detail"]
    embedded = aj.verify_embedded_v1(read.rows, read.seal)
    assert embedded.status == "CORRUPT" and embedded.rows == []


def test_pv2_04_v1_stays_closed_to_g4_rows_and_a_journal_never_mixes_schemas(tmp_path):
    aj = _aj()
    row = {**aj.translate_g4_event(G4_EVENT)}
    with pytest.raises(aj.ProvenanceError, match="invalid combination G4_SELECTION"):
        aj.check_content(row, schema=aj.V1_SCHEMA)
    aj.check_content(row)  # v2 admits it
    v1 = V1_JOURNAL.read_bytes().splitlines()
    rows = [json.loads(line) for line in v1[:-1]]  # the v1 events, unsealed
    relabeled = {**rows[-1], "schema": aj.SCHEMA}  # one row claims v2 inside a v1 journal
    read = aj.verify_embedded([*rows[:-1], relabeled], None)
    assert read.status == "CORRUPT" and read.failure["code"] == "SCHEMA_INVALID" and len(read.rows) == 3
    assert "mixes" in read.failure["detail"]


def test_pv2_05_the_writer_continues_an_open_v1_journal_in_v1_and_refuses_g4_rows_there(tmp_path):
    aj = _aj()
    path = tmp_path / pf.SIDECAR
    lines = V1_JOURNAL.read_bytes().splitlines(keepends=True)
    path.write_bytes(b"".join(lines[:-1]))  # the v1 journal, still OPEN
    written = aj.ProvenanceJournal.open(path, run_stem=pf.RUN["run_stem"], game_id=pf.RUN["game_id"])
    assert written.schema == aj.V1_SCHEMA and not written.failed
    assert written.append(aj.translate_g4_event(G4_EVENT)) is None and "G4_SELECTION" in written.failed
    assert aj.read_journal(path).status == "OPEN" and len(aj.read_journal(path).rows) == 4  # nothing written


# ---- the world model that embeds it ---------------------------------------------------------------------------------

def test_pv2_06_the_world_model_is_v8_and_the_frozen_v7_model_still_reads():
    wm = _wm()
    v7 = json.loads(V7_MODEL.read_text())
    assert (wm.SCHEMA, wm.V8_SCHEMA, wm.V7_SCHEMA) == (  # B3 r2: the writer is v9; v8 and v7 are frozen
        "virelai-world-model-v9", "virelai-world-model-v8", "virelai-world-model-v7")
    assert v7["provenance"]["schema"] == "virelai-provenance-chapter-v1" and len(v7["provenance"]["rows"]) == 4
    wm.validate_v7(v7)
    assert wm.read_world_model(v7)["schema"] == "virelai-world-model-v7"
    assert wm._canonical(v7) == V7_MODEL.read_bytes()  # read back unchanged: the v7 bytes 0119a74 wrote
    with pytest.raises(wm.WorldModelV2Error, match="schema must be virelai-world-model-v9"):
        wm.validate(v7)  # the v8 contract is never applied to a v7 artifact


def test_pv2_07_a_v8_model_embeds_a_v2_journal_and_v7_never_accepts_one(tmp_path):
    wm = _wm()
    model = pf.sealed(pf.model("RUN_END"), _v2_journal(tmp_path))
    assert model["schema"] == wm.SCHEMA and model["provenance"]["schema"] == "virelai-provenance-chapter-v2"
    assert {row["schema"] for row in model["provenance"]["rows"]} == {"virelai-provenance-v2"}
    assert model["provenance"]["integrity"] == "SEALED"
    wm.validate(model)
    assert model["levels"][0]["provenance_index"]["selections"]  # G4 rows index as selections
    relabeled = copy.deepcopy(model)
    relabeled["schema"] = wm.V7_SCHEMA
    relabeled["provenance"]["schema"] = "virelai-provenance-chapter-v1"
    relabeled["content_sha256"] = wm.content_sha256(relabeled)
    with pytest.raises(wm.WorldModelV2Error, match="provenance"):
        wm.validate_v7(relabeled)  # v7 embeds v1 journals only: the v2 rows are refused, never reinterpreted


def test_pv2_08_a_v8_model_still_embeds_a_v1_journal_verified_by_its_own_vocabulary():
    wm = _wm()
    model = pf.sealed(pf.model("RUN_END"), V1_JOURNAL.read_bytes())
    assert model["schema"] == wm.SCHEMA and {row["schema"] for row in model["provenance"]["rows"]} == {
        "virelai-provenance-v1"}
    wm.validate(model)
