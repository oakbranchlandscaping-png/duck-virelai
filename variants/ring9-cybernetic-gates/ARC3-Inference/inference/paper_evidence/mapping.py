"""Key subject → solver subject mapping: EXACT, COMPOSITE, UNMATCHED (WO-PE-03C; Sol D10, D16).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §3.

Ported from ``virelai_v4/diagnostics/foundation_grade.map_foundation`` (PORT default), adapted to v11's inclusive
``[r0,c0,r1,c1]`` boxes:
- **EXACT:** the solver subjects with equal anchor, bbox and cell count (and class, when both state one). Cell count
  is the disambiguator. More than one can match when the model holds one object twice (its track and the counter's
  mask): they are the same thing.
- **COMPOSITE:** unclaimed solver subjects lying inside the key's box whose cell counts sum exactly. Smallest key box
  first. No subset guessing.
- **UNMATCHED:** everything else.

The agent, the counter, a level and an action map by type (and handle, for an action). The code proposes and a human
confirms every non-EXACT row in ``mapping_sheet.json``. An unconfirmed row stops the grader.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping

from inference.paper_evidence import claims as c

SHEET = "virelai-paper-mapping-v1"


def _solver_subjects(packet: Mapping[str, Any], level: int) -> list[dict[str, Any]]:
    """The distinct located subjects of a level's propositions, by identity."""
    seen: dict[str, dict[str, Any]] = {}
    for item in packet["claims"]:
        if item["level"] == level and item["kind"] == "PROPOSITION":
            ident = c.identity_subject(item["subject"])
            seen.setdefault(c.sha256(ident), ident)
    return [seen[key] for key in sorted(seen)]


def _entry(subject: Mapping[str, Any]) -> Mapping[str, Any] | None:
    geometry = subject.get("geometry") or {}
    return geometry if geometry.get("frame") in ("ENTRY", "MASK") else None


def _same(key_geometry: Mapping[str, Any], solver: Mapping[str, Any]) -> bool:
    shape = _entry(solver)
    if shape is None:
        return False
    if key_geometry.get("class") is not None and shape.get("class") is not None and key_geometry["class"] != shape["class"]:
        return False
    return [list(key_geometry["anchor"]), list(key_geometry["bbox"]), key_geometry["cell_count"]] == [
        list(shape["anchor"]), list(shape["bbox"]), shape["cell_count"]]


def _inside(box: list[int], solver: Mapping[str, Any]) -> bool:
    inner = (_entry(solver) or {}).get("bbox")
    return bool(inner) and box[0] <= inner[0] and box[1] <= inner[1] and inner[2] <= box[2] and inner[3] <= box[3]


def _by_type(key_subject: Mapping[str, Any], pool: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    kind = key_subject["type"]
    return [dict(s) for s in pool if s["type"] == kind and (kind != "ACTION" or s["handle"] == key_subject["handle"])]


def _row(subject: Mapping[str, Any], outcome: str, members: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {"key_subject": dict(subject), "outcome": outcome, "proposed": [dict(m) for m in members],
            "confirmed": [dict(m) for m in members] if outcome == "EXACT" else None}


def _map_objects(subjects: list[Mapping[str, Any]], pool: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    claimed: set[str] = set()
    rows: dict[int, dict[str, Any]] = {}
    located = [i for i, s in enumerate(subjects) if _entry(s) is not None or (s.get("geometry") or {}).get("frame") == "ENTRY"]
    for i in located:  # pass 1 EXACT: every solver subject with this geometry is this object (a track and a mask)
        hits = [s for s in pool if c.sha256(s) not in claimed and _same(subjects[i]["geometry"], s)]
        if hits:
            claimed.update(c.sha256(s) for s in hits)
            rows[i] = _row(subjects[i], "EXACT", hits)
    pending = sorted((i for i in located if i not in rows), key=lambda i: _area(subjects[i]["geometry"]["bbox"]))
    for i in pending:  # pass 2 COMPOSITE, smallest key box first
        box, want = subjects[i]["geometry"]["bbox"], subjects[i]["geometry"]["cell_count"]
        members = [s for s in pool if c.sha256(s) not in claimed and _inside(box, s) and "+" not in s["handle"]]
        if members and sum(_entry(s)["cell_count"] for s in members) == want:
            claimed.update(c.sha256(s) for s in members)
            rows[i] = _row(subjects[i], "COMPOSITE", members)
    return rows


def _area(box: list[int]) -> int:
    return (box[2] - box[0] + 1) * (box[3] - box[1] + 1)


def propose(packet: Mapping[str, Any], key: Mapping[str, Any]) -> dict[str, Any]:
    """The mapping sheet for every distinct key subject, per level: proposals, with EXACT rows already confirmed."""
    rows: list[dict[str, Any]] = []
    for level in sorted({item["level"] for item in key.get("items") or ()}):
        pool = _solver_subjects(packet, level)
        subjects: dict[str, Mapping[str, Any]] = {}
        for item in key["items"]:
            if item["level"] == level:
                subjects.setdefault(c.sha256(item["subject"]), item["subject"])
                other = item.get("object")  # a relation's other lever is mapped like any subject
                if isinstance(other, Mapping) and other.get("type") in c.SUBJECT_TYPES:
                    subjects.setdefault(c.sha256(other), other)
        ordered = [subjects[k] for k in sorted(subjects)]
        objects = [s for s in ordered if s["type"] == "OBJECT"]
        mapped = _map_objects(objects, [s for s in pool if s["type"] in ("OBJECT", "COUNTER")])
        for i, subject in enumerate(objects):
            rows.append({"level": level, **mapped.get(i, _row(subject, "UNMATCHED", []))})
        for subject in (s for s in ordered if s["type"] != "OBJECT"):
            found = _by_type(subject, pool)
            rows.append({"level": level, **_row(subject, "EXACT" if len(found) == 1 else "UNMATCHED", found)})
    return {"schema": SHEET, "game_id": key.get("game_id"), "packet": packet["stamp"]["content_sha256"], "rows": rows}


def unconfirmed(sheet: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Rows a human has not confirmed (``confirmed`` must be a list; an empty list means no solver subject)."""
    return [row for row in sheet.get("rows") or () if not isinstance(row.get("confirmed"), list)]


def lookup(sheet: Mapping[str, Any]) -> dict[tuple[int, str], list[str]]:
    """(level, key-subject identity) → the identities of the confirmed solver subjects."""
    return {(row["level"], c.sha256(row["key_subject"])): [c.sha256(s) for s in row["confirmed"] or ()]
            for row in sheet.get("rows") or ()}


__all__ = ["SHEET", "lookup", "propose", "unconfirmed"]
