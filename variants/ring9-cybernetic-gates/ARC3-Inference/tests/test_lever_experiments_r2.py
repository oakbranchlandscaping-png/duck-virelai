"""WO-G4-DOSSIER-B3 revision 2: the recorded terminal outcome, the v9 world model, the persisted contract module.

Author: Claude (Alpha build seat), 2026-10-18. Sol's review of B3 revision 1: (1) the validator never compared a
close's recorded type with the outcome its evidence supports, so a rehashed model could relabel a finish; (2) an
``ef8289d`` v8 reader refuses a valid B3 model, so B3 writes v9 and keeps v8 frozen; (3) the persisted contract
moves to a small module the validator shares with the runtime. Written before the revision-2 edits (fail-first on
revision 1).

The genuine artifacts are sealed at H2 from real runs (the committed ft09 record, continued on its offline world):
the owed-state run (three ``REVERSAL_OBSERVED``), a three-content cycle (``RECURRENCE_OBSERVED``, labelled world
double), a lever that saturates after one press (``CAPPED`` at the real cap of 8, labelled world double), a
persistence trial in the life after a death (``PERSISTENCE_UNCHANGED``), and that death's ``STALE``. Each attack
changes only the close's reason, re-chains the journal with the real writer and recomputes every hash.
"""
from __future__ import annotations

import json
import pickle
import subprocess
import sys
from pathlib import Path

import pytest

import test_lever_experiments as T
from ft09_world import Ft09World
from inference.framework.controller_executor import next_owned_step

FIXTURES = Path(__file__).parent / "fixtures"
V8_MODEL = FIXTURES / "world_model_v8_frozen.json"
_CACHE: dict[str, bytes] = {}


def _wm():
    from inference.framework import world_model_v2

    return world_model_v2


class _Saturating(Ft09World):
    """Labelled double: E0053's tile changes on its first press only; every later press of it changes nothing."""

    def changes(self, action):
        if (action["row"], action["col"]) == T.TILES["E0053"] and getattr(self, "_pressed", False):
            return []
        if (action["row"], action["col"]) == T.TILES["E0053"]:
            self._pressed = True
        return super().changes(action)


def _until_closed(machine, world, entity):
    """The controller's steps until ``entity``'s experiment closes."""
    for _ in range(12):
        T._act(machine, world, next_owned_step(machine))
        if any(e["event"] in ("FINISHED", "STALE") and e["entity_id"] == entity for e in machine.g4_selection_events):
            return
    raise AssertionError(f"{entity}'s experiment never closed")


def _artifact(name):
    """(machine, unsealed H2 model) of one genuine run."""
    def build():
        from test_g4_selection_persisted import _unsealed

        if name == "reversal":
            machine, _unsealed_model = T._finished_run()
            return machine, _unsealed_model
        if name == "persistence":
            machine, world, _death, _reset = T._died()
            _until_closed(machine, world, "E0053")
        else:
            machine, world = T._opening()
            world = T._with_world(world, T._Cycling if name == "recurrence" else _Saturating)
            _until_closed(machine, world, "E0053")
        return machine, _unsealed(machine)
    if name not in _CACHE:
        _CACHE[name] = pickle.dumps(build())
    return pickle.loads(_CACHE[name])


def _rows(machine):
    from test_g4_selection_persisted import _translated

    return _translated(machine)


def _relabel(rows, entity, event, text):
    """Only the close's reason changes; the real writer re-chains the journal and every hash is recomputed."""
    out = [dict(row) for row in rows]
    index = next(i for i, row in enumerate(out) if row["refs"]["subject"] == entity
                 and row["refs"]["source_event"]["event"] == event and row["gate_id"] == T.RELATIONS)
    out[index]["reason"] = {"code": "G4_EVENT", "text": text}
    return out


def _refused(machine, unsealed, rows, match):
    with pytest.raises(_wm().WorldModelV2Error, match=match):
        _wm().read_world_model(T._sealed(machine, unsealed, rows))


def _closes(rows):
    return [(r["refs"]["subject"], r["refs"]["source_event"]["event"], (r["reason"] or {}).get("text", "").split(":")[0])
            for r in rows if r["gate_id"] == T.RELATIONS and r["refs"]["source_event"]["event"] in ("FINISHED", "STALE")]


# ---- 1 · the genuine closes read, each with its typed reason on the record ---------------------------------------

def test_t2_01_every_genuine_close_records_its_type_and_reads():
    expected = {"reversal": [("E0054", "FINISHED", "REVERSAL_OBSERVED"), ("E0053", "FINISHED", "REVERSAL_OBSERVED"),
                             ("E0055", "FINISHED", "REVERSAL_OBSERVED")],
                "recurrence": [("E0053", "FINISHED", "RECURRENCE_OBSERVED")],
                "capped": [("E0053", "FINISHED", "CAPPED")],
                "persistence": [("E0053", "STALE", "INTERRUPTED_DEATH"), ("E0053", "FINISHED", "PERSISTENCE_UNCHANGED")]}
    for name, closes in expected.items():
        machine, unsealed = _artifact(name)
        rows = _rows(machine)
        assert _closes(rows) == closes, name
        _wm().read_world_model(T._sealed(machine, unsealed, rows))


# ---- 2 · each forged close is refused, every hash recomputed -------------------------------------------------------

def test_t2_02_a_reversal_relabelled_capped_is_refused():
    machine, unsealed = _artifact("reversal")
    rows = _relabel(_rows(machine), "E0053", "FINISHED", "CAPPED: no return in 8 presses")
    _refused(machine, unsealed, rows, "its close records CAPPED, but its evidence shows REVERSAL_OBSERVED")


def test_t2_03_a_reversal_relabelled_recurrence_is_refused():
    machine, unsealed = _artifact("reversal")
    rows = _relabel(_rows(machine), "E0054", "FINISHED", "RECURRENCE_OBSERVED: step 1 returned E0054 (cycle 3)")
    _refused(machine, unsealed, rows, "its close records RECURRENCE_OBSERVED, but its evidence shows REVERSAL_OBSERVED")


def test_t2_04_an_unchanged_persistence_trial_relabelled_changed_is_refused():
    machine, unsealed = _artifact("persistence")
    rows = _relabel(_rows(machine), "E0053", "FINISHED", "PERSISTENCE_CHANGED: E0054's press, E0053 changed")
    _refused(machine, unsealed, rows, "its close records PERSISTENCE_CHANGED, but its evidence shows PERSISTENCE_UNCHANGED")


def test_t2_05_a_persistence_trial_closed_with_a_reversal_type_is_refused():
    machine, unsealed = _artifact("persistence")
    rows = _relabel(_rows(machine), "E0053", "FINISHED", "REVERSAL_OBSERVED: forged")
    _refused(machine, unsealed, rows, "FINISHED close names REVERSAL_OBSERVED, which a PERSISTENCE experiment")


def test_t2_06_a_capped_reversal_relabelled_observed_without_a_return_is_refused():
    machine, unsealed = _artifact("capped")
    rows = _relabel(_rows(machine), "E0053", "FINISHED", "REVERSAL_OBSERVED: forged")
    _refused(machine, unsealed, rows, "its close records REVERSAL_OBSERVED, but its evidence shows CAPPED")


def test_t2_07_a_finished_close_with_an_interruption_and_a_stale_close_with_an_outcome_are_refused():
    machine, unsealed = _artifact("reversal")
    rows = _relabel(_rows(machine), "E0055", "FINISHED", "INTERRUPTED_DEATH: forged")
    _refused(machine, unsealed, rows, "FINISHED close names INTERRUPTED_DEATH")
    machine, unsealed = _artifact("persistence")
    rows = _relabel(_rows(machine), "E0053", "STALE", "CAPPED: forged")
    _refused(machine, unsealed, rows, "STALE close names CAPPED")


def test_t2_08_a_finished_close_that_names_no_type_is_refused():
    machine, unsealed = _artifact("recurrence")
    rows = _relabel(_rows(machine), "E0053", "FINISHED", "the experiment ended")
    _refused(machine, unsealed, rows, "FINISHED close names no terminal type")


# ---- 3 · schema v9, with v8 frozen ---------------------------------------------------------------------------------

def test_t2_09_the_writer_is_v9_and_the_frozen_v8_model_from_ef8289d_still_reads():
    wm = _wm()
    v8 = json.loads(V8_MODEL.read_text())
    assert (wm.SCHEMA, wm.V9_SCHEMA, wm.V8_SCHEMA) == (  # WIN-01: the writer is v10; v9 and v8 are frozen
        "virelai-world-model-v10", "virelai-world-model-v9", "virelai-world-model-v8")
    assert v8["schema"] == wm.V8_SCHEMA and v8["provenance"]["schema"] == "virelai-provenance-chapter-v2"
    assert [r["refs"]["source_event"]["event"] for r in v8["provenance"]["rows"] if r["operation"] == "G4_SELECTION"] \
        == ["ADMITTED", "STALE"]
    wm.validate_v8(v8)
    assert wm.read_world_model(v8)["schema"] == wm.V8_SCHEMA
    assert wm._canonical(v8) == V8_MODEL.read_bytes()  # read back unchanged: the bytes ef8289d wrote
    with pytest.raises(wm.WorldModelV2Error, match="schema must be virelai-world-model-v10"):
        wm.validate(v8)  # the v10 contract is never applied to a v8 artifact


def test_t2_10_v8_refuses_a_v9_artifact_at_the_schema_boundary_and_keeps_the_b2_contract():
    wm = _wm()
    machine, unsealed = _artifact("reversal")
    model = T._sealed(machine, unsealed)
    assert model["schema"] == wm.SCHEMA
    wm.read_world_model(model)
    with pytest.raises(wm.WorldModelV2Error, match="schema must be virelai-world-model-v8"):
        wm.validate_v8(model)
    relabeled = dict(model, schema=wm.V8_SCHEMA)
    relabeled["content_sha256"] = wm.content_sha256(relabeled)
    with pytest.raises(wm.WorldModelV2Error, match="ADMITTED selection .* is not G4-A's"):
        wm.read_world_model(relabeled)  # the same artifact under v8's own rules: G4-B rows are not G4-A's


def test_t2_11_frozen_v8_never_runs_the_experiment_check_and_v9_always_does(monkeypatch):
    from inference.framework import lever_experiment_check

    calls = []
    monkeypatch.setattr(lever_experiment_check, "problems", lambda *a, **k: calls.append(a) or [])
    _wm().validate_v8(json.loads(V8_MODEL.read_text()))
    assert calls == []
    machine, unsealed = _artifact("recurrence")
    _wm().read_world_model(T._sealed(machine, unsealed))
    assert len(calls) == 1


# ---- 4 · the persisted contract is the validator's, not the engine's ----------------------------------------------

def test_t2_12_the_validator_reads_a_b3_artifact_without_importing_the_experiment_engine(tmp_path):
    machine, unsealed = _artifact("reversal")
    path = tmp_path / "world_model.json"
    path.write_bytes(_wm().canonical_bytes(T._sealed(machine, unsealed)))
    code = ("import json, sys; from inference.framework.world_model_v2 import read_world_model; "
            f"read_world_model(json.loads(open({str(path)!r}).read())); "
            "print('inference.framework.lever_experiments' in sys.modules, "
            "'inference.framework.lever_experiment_contract' in sys.modules)")
    root = Path(__file__).resolve().parents[1]
    env = {"PYTHONPATH": f"{root.parent / 'tufa-arc-agi-framework' / 'src'}:{root}", "PATH": "/usr/bin:/bin"}
    result = subprocess.run([sys.executable, "-c", code], cwd=root, env=env, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, result.stderr[-2000:]
    assert result.stdout.split() == ["False", "True"]
