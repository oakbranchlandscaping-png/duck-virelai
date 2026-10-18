"""The persisted G4-A selection log and its question-to-dossier chain (WO-G4-DOSSIER-B, B2 revisions 3 and 4).

Author: Claude (Alpha build seat), 2026-10-18. Sol's review of B2 revision 2: the chain "admitted question → selected
experiment receipts → completed dossier chapter" must be enforced by the canonical v8 validator on the saved model,
not by a checker that only reads live gate state. This module is that validator step (``world_model_v2`` calls
``problems`` for schema v8 only; the frozen v7 reader never does). It is pure and reads only the model.

No question id is stored in a dossier (Sol's ruling): ``dossier_question`` derives it from level, gate, lever and
chapter. What the saved model holds, and what is checked:

* **the audit rows** (the H2 provenance chapter's embedded journal, audit schema v2): each G4 selection event as a
  ``G4_SELECTION`` row whose ``refs.source_event.event`` is ``ADMITTED``, ``REFUSED``, ``STALE`` or ``FINISHED``. A G4
  gate holds at most one choice: an ``ADMITTED`` row opens it, ``STALE`` or ``FINISHED`` closes it;
* **the level receipt index** (``receipts.evidence``): each transition's evidence id with its ``probe_id``. A run the
  choice bound has identity-bearing probe ids, ``G4.2-LEVER-ORBITS:GUIDED:SEL:{lever}:L{level}P{life}:R{n}:{k}``,
  where ``n`` is the admission's ordinal among the game's G4 admissions — the persisted substitute for the in-memory
  receipt's ``question_id``.

Rules (revision 4, Sol's review of revision 3: the selection log is a state machine, valid at any stop):

1. every ``ADMITTED`` row — open or closed, at a run end, a budget or controlled stop, or a crash — is G4-A's, on a
   level the model holds, about a lever with a dossier there, and names the question derived from level, G4-A,
   lever and ``ORBIT``; a valid admission may stay open;
2. an ``ADMITTED`` row opens the one choice of its level and gate; a second may not open while it is open. A
   ``STALE`` or ``FINISHED`` row closes it and must match it on level, life, gate, executor, subject and question
   (the writer scopes a close to the choice it closes); an orphan close is refused. ``REFUSED`` opens and closes
   nothing. Each row's audit event and disposition must fit its source event;
3. the orbit chapter of a ``FINISHED`` selection cites at least one receipt of that selected run (unless the chapter
   failed closed, when it states nothing);
4. every evidence reference of an orbit chapter resolves in the level's receipt index, and a cited selected-run receipt
   names that chapter's own lever;
5. a chapter with no G4 selection needs no selected probe id: ordinary controller coverage is valid as it is.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

ORBITS = "G4.2-LEVER-ORBITS"
OPERATION = "G4_SELECTION"
CLOSING = ("STALE", "FINISHED")
SELECTED = f"{ORBITS}:GUIDED:SEL:"
CHAPTER_GATES = {"anatomy": "G4-REACTIONS", "orbit": ORBITS}
CHAPTER_KINDS = {"anatomy": "EFFECTS", "orbit": "ORBIT"}


def dossier_question(level: int, entity_id: str, chapter: str) -> str | None:
    """The question a lever's dossier chapter answers, derived (never stored): level, gate, lever and chapter."""
    from inference.framework.library_agenda import question_id

    if chapter not in CHAPTER_GATES:
        return None
    return question_id(int(level), CHAPTER_GATES[chapter], entity_id, CHAPTER_KINDS[chapter])


def selected_run(level: int, life: int, entity_id: str, admission: int) -> str:
    """The probe-id prefix every receipt of one admitted G4-A choice's run carries."""
    return f"{SELECTED}{entity_id}:L{int(level)}P{int(life)}:R{int(admission)}:"


def probe_lever(probe_id: Any) -> str | None:
    """The lever a selected-run probe id names; None for an ordinary coverage probe."""
    text = str(probe_id or "")
    return text[len(SELECTED):].split(":", 1)[0] if text.startswith(SELECTED) else None


def _event(row: Mapping[str, Any]) -> str:
    return str(((row.get("refs") or {}).get("source_event") or {}).get("event") or "")


MATCHED = ("level", "life", "gate_id", "executor")  # a close must describe the choice it closes (revision 4)


def _admission_problem(levels: Mapping[Any, Mapping[str, Any]], row: Mapping[str, Any]) -> str | None:
    """Revision 4, rule 1: every ADMITTED row is a well-formed G4-A choice, open or not."""
    refs, number, where = row["refs"], row.get("level"), f"ADMITTED selection {row['event_id']}"
    if row.get("gate_id") != ORBITS:
        return f"{where} is not G4-A's"
    if number not in levels:
        return f"{where} names level {number}, not a level this model holds"
    if refs["question_id"] != dossier_question(number, str(refs["subject"]), "orbit"):
        return (f"{where} names {refs['question_id']}, not the question derived from level, G4-A, {refs['subject']} "
                "and ORBIT")
    if refs["subject"] not in (levels[number].get("lever_dossiers") or {}):
        return f"{where} names {refs['subject']}, which has no dossier on level {number}"
    return None


def _mismatch(admitted: Mapping[str, Any], row: Mapping[str, Any]) -> str | None:
    for field in MATCHED:
        if admitted.get(field) != row.get(field):
            return field
    for field in ("subject", "question_id"):
        if admitted["refs"][field] != row["refs"][field]:
            return field
    return None


def _log(levels: Mapping[Any, Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]
         ) -> tuple[list[tuple[Mapping[str, Any], Mapping[str, Any], int]], list[str]]:
    """Revision 4: the selection log as a state machine. ADMITTED opens the one choice of its level and gate (a
    second may not open while it is open); STALE or FINISHED closes it and must match it on level, life, gate,
    executor, subject and question; REFUSED opens and closes nothing. Returns each FINISHED with its admission."""
    from inference.framework.audit_journal import G3_TRANSLATION

    open_choices: dict[tuple[Any, Any], tuple[Mapping[str, Any], int]] = {}
    pairs, problems, admissions = [], [], 0
    for row in sorted((r for r in rows if r.get("operation") == OPERATION), key=lambda r: int(r["seq"])):
        event, key = _event(row), (row.get("level"), row.get("gate_id"))
        where = f"{event or 'G4'} selection {row['event_id']}"
        if (row.get("event"), row.get("disposition")) != G3_TRANSLATION.get(event):
            problems.append(f"{where} does not fit its audit event {row.get('event')}/{row.get('disposition')}")
        elif event == "ADMITTED":
            admissions += 1
            problem = _admission_problem(levels, row)
            if problem is not None:
                problems.append(problem)
            if key in open_choices:
                problems.append(f"second ADMITTED selection {row['event_id']} while "
                                f"{open_choices[key][0]['event_id']} is still open")
            open_choices[key] = (row, admissions)
        elif event in CLOSING:
            admitted = open_choices.pop(key, None)
            field = None if admitted is None else _mismatch(admitted[0], row)
            if admitted is None or field is not None:
                problems.append(f"{where} closes no matching earlier ADMITTED selection"
                                + ("" if field is None else f": its {field} differs"))
            elif event == "FINISHED":
                pairs.append((admitted[0], row, admitted[1]))
    return pairs, problems


def _orbit_receipts(level: Mapping[str, Any]) -> list[str]:
    """Rule 2: every orbit chapter's evidence resolves; a cited selected-run receipt names the chapter's lever."""
    evidence, problems = level["receipts"]["evidence"], []
    for entity_id, dossier in sorted((level.get("lever_dossiers") or {}).items()):
        for ref in dossier["chapters"]["orbit"]["evidence_refs"]:
            if ref not in evidence:
                problems.append(f"level {level['level']}: {entity_id}'s orbit cites {ref}, which no receipt resolves")
                continue
            lever = probe_lever(evidence[ref].get("probe_id"))
            if lever is not None and lever != entity_id:
                problems.append(f"level {level['level']}: {entity_id}'s orbit cites {ref}, a selected-run receipt of "
                                f"{lever}")
    return problems


def _completed(levels: Mapping[Any, Mapping[str, Any]], admitted: Mapping[str, Any], finished: Mapping[str, Any],
               admission: int) -> str | None:
    """Rule 3 for one FINISHED selection whose admission is well formed: its run reached its lever's orbit chapter."""
    number, entity = admitted.get("level"), str(admitted["refs"]["subject"])
    level = levels.get(number)
    dossier = None if level is None else (level.get("lever_dossiers") or {}).get(entity)
    if dossier is None:
        return None  # the admission's own problem is already reported
    orbit = dossier["chapters"]["orbit"]
    if orbit["integrity"].get("status") == "FAILED_CLOSED":
        return None  # a failed chapter states nothing; its own integrity reason is the record
    prefix = selected_run(number, admitted["life"], entity, admission)
    evidence = level["receipts"]["evidence"]
    if not any(str((evidence.get(ref) or {}).get("probe_id") or "").startswith(prefix) for ref in orbit["evidence_refs"]):
        return f"FINISHED selection {finished['event_id']}: {entity}'s orbit chapter cites no receipt of the selected run {prefix}*"
    return None


def problems(payload: Mapping[str, Any]) -> list[str]:
    """Every way the saved model breaks the chain admitted question → selected run receipts → completed chapter."""
    levels = {level["level"]: level for level in payload.get("levels") or ()}
    chapter = payload.get("provenance") or {}
    rows = list(chapter.get("rows") or ()) if chapter.get("phase") == "H2" else []
    found = [problem for level in levels.values() for problem in _orbit_receipts(level)]
    pairs, log = _log(levels, rows)
    found += log
    found += [problem for admitted, finished, admission in pairs
              if (problem := _completed(levels, admitted, finished, admission)) is not None]
    return found


__all__ = ["dossier_question", "probe_lever", "problems", "selected_run"]
