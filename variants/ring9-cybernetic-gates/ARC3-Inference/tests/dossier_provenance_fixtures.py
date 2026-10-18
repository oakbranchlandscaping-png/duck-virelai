"""WO-G4-DOSSIER-A revision 2: committed synthetic provenance fixtures for the dossier's provenance-dependent facts.

Author: Claude (Alpha build seat), 2026-10-17. Sol's revision-2 directive, blocker 1 and the provenance scope.

One lever (E0001: witness W-1 on evidence E-1 at transition 1, the minimal model of ``test_world_model_v2``) is
compiled from a hand-built gate view (its G3 activation and, when asked, the G3 selection event that chose it), then
sealed with a provenance chapter built from a real, hash-chained synthetic journal: one admitted G3 probe and its
execution per ``(executor, evidence, transition[, level])`` row asked for, then any extra rows. Nothing reads Kaggle
output.

Revision 3 (2026-10-18, Sol's level-scoping correction): ``two_level_model`` holds the same lever, witness and
evidence id (E-1 at transition 1) on a frozen level 1 and an open level 2, so a journal row of one level can be shown
never to verify, duplicate or contradict the other.
"""
from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Iterable, Sequence

RUN = {"run_stem": "g_p0", "game_id": "g"}
SIDECAR = "g_p0_provenance.jsonl"
ENTITY, EVIDENCE, TRANSITION = "E0001", "E-1", 1


def view(chooser: str | None = None) -> dict[str, Any]:
    """A gate view in which G3 discovered E0001 by pressing it; ``chooser`` adds the G3 selection event that chose it."""
    from inference.framework import lever_dossiers

    built = copy.deepcopy(lever_dossiers.EMPTY_VIEW)
    built["g3"]["activation"][ENTITY] = {
        "source": "G3_DISCOVERY", "intervention": {"action": "ACTION6", "row": 0, "col": 0}, "channel": "CLICK",
        "record_ref": None, "witness_evidence_ref": EVIDENCE, "confirmation_evidence_ref": None}
    if chooser is not None:
        built["g3"]["choosers"][ENTITY] = [(0, chooser)]
    return built


def model(persist_reason: str, *, chooser: str | None = None) -> dict[str, Any]:
    """The minimal model with E0001's dossier compiled from ``view(chooser)`` for ``persist_reason`` (unsealed)."""
    from inference.framework import lever_dossiers
    from test_world_model_v2 import _model

    built = _model()
    built["manifest"]["persist_reason"] = persist_reason
    for level in built["levels"]:
        level["lever_dossiers"] = lever_dossiers.build(level, view(chooser))
    built["levels"] = lever_dossiers.finalize(built["levels"], persist_reason)
    return built


def two_level_model(persist_reason: str = "RUN_END", *, chooser: str | None = None) -> dict[str, Any]:
    """Two levels that both hold E0001 witnessed on evidence E-1 at transition 1: level 1 frozen, level 2 open."""
    from inference.framework import lever_dossiers
    from test_world_model_v2 import _model

    built = _model()
    built["manifest"]["persist_reason"] = persist_reason
    first = built["levels"][0]
    second = copy.deepcopy(first)
    first["state"], second["level"] = "FROZEN", 2
    built["levels"] = [first, second]
    for level in built["levels"]:
        level["lever_dossiers"] = lever_dossiers.build(level, view(chooser))
    built["levels"] = lever_dossiers.finalize(built["levels"], persist_reason)
    return built


def admission(executor: str, index: int, *, level: int = 1) -> dict[str, Any]:
    from inference.framework import audit_journal as aj

    return {"level": level, "life": 1, "gate_id": "G3-LEVERS", "at_transition": 0, "executor": executor,
            "operation": "PROBE", "event": "ADMISSION", "disposition": "ADMITTED",
            "submitted": {"actions": [{"action": "ACTION6"}], "decision": {"probe_token": f"CAPABILITY:X:R{index}"}},
            "effective": None, "field_sources": None, "refs": aj.make_refs(probe_id=f"G3-LEVERS:CLICK:{index}"),
            "reason": None}


def execution(admitted: dict[str, Any], evidence: str, transition: int) -> dict[str, Any]:
    from inference.framework import audit_journal as aj

    return {**{key: admitted[key] for key in ("level", "life", "gate_id", "at_transition", "executor")},
            "operation": "PROBE", "event": "EXECUTION", "disposition": "EXECUTED", "submitted": None,
            "effective": None, "field_sources": None, "reason": None,
            "refs": aj.make_refs(probe_id=admitted["refs"]["probe_id"], evidence_id=evidence,
                                 executed_transition=transition, admission_event_id=admitted["event_id"])}


def answer_row(executor: str, gate_id: str, answer_id: str, *, level: int = 1) -> dict[str, Any]:
    """An admitted answer: who submitted ``answer_id`` to ``gate_id`` (the submitter a dossier may name)."""
    from inference.framework import audit_journal as aj

    payload = {"answer_id": answer_id}
    return {"level": level, "life": 1, "gate_id": gate_id, "at_transition": 1, "executor": executor,
            "operation": "ANSWER", "event": "ADMISSION", "disposition": "ADMITTED", "submitted": payload,
            "effective": payload, "field_sources": {"answer_id": "SUBMITTER"}, "reason": None,
            "refs": aj.make_refs(answer_id=answer_id)}


def journal(folder: Path, executions: Sequence[tuple] = (("CONTROLLER", EVIDENCE, TRANSITION),), *,
            extra: Iterable[dict[str, Any]] = ()) -> bytes:
    """A sealed synthetic journal: an admitted G3 probe and its execution for each ``(executor, evidence, transition)``,
    on level 1 unless the tuple names a fourth element, its level."""
    from inference.framework import audit_journal as aj

    path = Path(folder) / SIDECAR
    written = aj.ProvenanceJournal.open(path, run_stem=RUN["run_stem"], game_id=RUN["game_id"])
    for index, (executor, evidence, transition, *level) in enumerate(executions, start=1):
        admitted = written.append(admission(executor, index, level=level[0] if level else 1))
        written.append(execution(admitted, evidence, transition))
    for row in extra:
        written.append(row)
    assert not written.failed, written.failed
    assert written.seal()
    return path.read_bytes()


def sealed(unsealed: dict[str, Any], data: bytes | None) -> dict[str, Any]:
    """The model sealed at H2 with the chapter H2 builds from ``data`` (``None``: no journal could be read)."""
    from inference.framework import provenance_chapter as pc
    from inference.framework.world_model_v2 import seal

    chapter = pc.h2(unsealed, data=data, sidecar=SIDECAR, capture="ENABLED", answer_records=None)
    return seal({**unsealed, "provenance": chapter})


def executions_of(sealed_model: dict[str, Any], level: int | None = None) -> dict[str, list[str]]:
    """Evidence id -> the event ids of the executed probes the embedded journal records for it (on ``level``)."""
    out: dict[str, list[str]] = {}
    for row in sealed_model["provenance"].get("rows") or ():
        if (row["operation"], row["event"], row["disposition"]) == ("PROBE", "EXECUTION", "EXECUTED") and (
                level is None or row["level"] == level):
            out.setdefault(row["refs"]["evidence_id"], []).append(row["event_id"])
    return out


def dossier(sealed_model: dict[str, Any], entity_id: str = ENTITY, level_index: int = 0) -> dict[str, Any]:
    return sealed_model["levels"][level_index]["lever_dossiers"][entity_id]


__all__ = ["ENTITY", "EVIDENCE", "RUN", "SIDECAR", "TRANSITION", "admission", "answer_row", "dossier", "execution",
           "executions_of", "journal", "model", "sealed", "two_level_model", "view"]
