"""The five-category grader (WO-PE-03D; RULINGS_PAPER_EVIDENCE D9-D11, Sol D20, interface v2 §4).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §4.

Inputs:
- one packet (``paper_evidence.json``);
- one validated key;
- its confirmed mapping sheet;
- the human verdicts.

Every proposition gets exactly one grade, and so does every required key item:
- **CORRECT:** the claim joins a key item exactly (subject, family, predicate and object, or an accepted
  alternative), or a human rules it correct.
- **WRONG:** a single-valued fact whose value contradicts the key's for the same subject, or a human ruling.
- **UNVERIFIABLE:** the key cannot decide it. A proposition about a subject and family the key is silent on is
  UNVERIFIABLE by rule (``KEY_SILENT``), with no human needed. A human may still rule on it.
- **INVENTED:** a human ruling on a positive proposition. Never a gap.
- **MISSED:** a required key item that no CORRECT claim satisfies. A gap or closure audit never satisfies one (D20).

Audit statements (GAP, closures, prediction outcomes) are graded as audits. They are CORRECT when the sealed model
supports them, and the packet is a pure read of that model. Audit and proposition totals are kept apart in every table.

Consequence of ``KEY_SILENT`` (flagged in the interface §6): INVENTED is counted only where a human looked. Inside the
key's coverage, every unsettled claim is shown to a human. Outside it, a human may still mark a claim, but the INVENTED
total is a lower bound.

The grade is incomplete, and the tool exits non-zero, while any in-coverage proposition lacks a verdict or any mapping
row is unconfirmed.
"""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from inference.paper_evidence import claims as c
from inference.paper_evidence import keys as k
from inference.paper_evidence import mapping as mp

GRADES = ("CORRECT", "WRONG", "UNVERIFIABLE", "INVENTED")
VERDICT_SHEET, GRADE_SCHEMA = "virelai-paper-verdicts-v1", "virelai-paper-grade-v1"


def _sid(subject: Any) -> str:
    return c.sha256(c.identity_subject(subject)) if isinstance(subject, Mapping) else c.sha256(subject)


def _mapped(maps: Mapping[tuple[int, str], list[str]], level: int, subject: Mapping[str, Any]) -> set[str]:
    return set(maps.get((level, c.sha256(subject)), ()))


def _object_equal(claim: Mapping[str, Any], item: Mapping[str, Any], obj: Any, maps) -> bool:
    if isinstance(obj, Mapping) and obj.get("type") in c.SUBJECT_TYPES:  # a relation's other lever
        return _sid(claim["object"]) in _mapped(maps, item["level"], obj)
    return c.sha256(claim["object"]) == c.sha256(obj)


def _join(claim: Mapping[str, Any], item: Mapping[str, Any], maps) -> str | None:
    """EXACT / ALTERNATIVE / CONTRADICTION for a claim about the same mapped subject and family, else None."""
    if claim["family"] != item["family"] or _sid(claim["subject"]) not in _mapped(maps, item["level"], item["subject"]):
        return None
    if claim["predicate"] == item["predicate"] and _object_equal(claim, item, item["object"], maps):
        return "EXACT"
    for alt in item.get("accepted_alternatives") or ():
        if claim["predicate"] == alt.get("predicate") and _object_equal(claim, item, alt.get("object"), maps):
            return "ALTERNATIVE"
    if claim["predicate"] == item["predicate"] and item["predicate"] in k.SINGLE_VALUED:
        return "CONTRADICTION"
    return "IN_COVERAGE"


def _settle(claim: Mapping[str, Any], items: list[Mapping[str, Any]], maps) -> tuple[str | None, str, list[str]]:
    """(grade or None when a human must rule, basis, satisfied key ids) for one proposition."""
    joins = [(item, _join(claim, item, maps)) for item in items if item["level"] == claim["level"]]
    hits = [item["key_id"] for item, how in joins if how in ("EXACT", "ALTERNATIVE")]
    if hits:
        return "CORRECT", "JOINED", hits
    if any(how == "CONTRADICTION" for _, how in joins):
        return "WRONG", "CONTRADICTS_KEY", []
    if any(how == "IN_COVERAGE" for _, how in joins):
        return None, "NEEDS_VERDICT", []
    return "UNVERIFIABLE", "KEY_SILENT", []


def _verdict(verdicts: Mapping[str, Any], claim: Mapping[str, Any]) -> Mapping[str, Any] | None:
    found = verdicts.get(claim["assertion_id"])
    return found if found and found.get("verdict") in GRADES else None


def _grade_claim(claim, items, maps, verdicts) -> dict[str, Any]:
    if claim["kind"] == "AUDIT":
        return {"assertion_id": claim["assertion_id"], "grade": "CORRECT", "basis": "MODEL_SUPPORTED", "satisfies": []}
    grade, basis, hits = _settle(claim, items, maps)
    ruled = _verdict(verdicts, claim)
    if ruled is not None and basis != "JOINED":
        grade, basis, hits = ruled["verdict"], "HUMAN_VERDICT", list(ruled.get("satisfies") or ())
    if grade == "INVENTED" and claim["family"] == "GAP":
        grade, basis = "UNVERIFIABLE", "A_GAP_IS_NEVER_INVENTED"
    return {"assertion_id": claim["assertion_id"], "grade": grade, "basis": basis,
            "satisfies": hits if grade == "CORRECT" else []}


def _item_outcomes(items, graded, excluded) -> list[dict[str, Any]]:
    by: dict[str, list[str]] = {}
    for row in graded:
        for key_id in row["satisfies"]:
            by.setdefault(key_id, []).append(row["assertion_id"])
    out = []
    for item in items:
        if str(item["level"]) in excluded:
            outcome = "EXCLUDED"
        else:
            outcome = "SATISFIED" if by.get(item["key_id"]) else ("MISSED" if item["required"] else "NOT_COVERED")
        out.append({"key_id": item["key_id"], "level": item["level"], "family": item["family"],
                    "required": item["required"], "outcome": outcome, "by": sorted(by.get(item["key_id"], ()))})
    return out


def _tables(packet, graded, outcomes) -> dict[str, Any]:
    grade_of = {row["assertion_id"]: row["grade"] for row in graded}
    basis_of = {row["assertion_id"]: row["basis"] for row in graded}
    rows = Counter((cl["level"], cl["family"], cl["kind"], cl["executor"], cl["admission"], cl["certification"],
                    grade_of.get(cl["assertion_id"]) or "PENDING") for cl in packet["claims"])
    items = Counter((o["level"], o["family"], o["required"], o["outcome"]) for o in outcomes)
    props = Counter(grade_of.get(cl["assertion_id"]) or "PENDING" for cl in packet["claims"] if cl["kind"] == "PROPOSITION")
    prop_bases = Counter(basis_of.get(cl["assertion_id"]) or "PENDING" for cl in packet["claims"]
                         if cl["kind"] == "PROPOSITION")
    audits = Counter(grade_of.get(cl["assertion_id"]) or "PENDING" for cl in packet["claims"] if cl["kind"] == "AUDIT")
    return {"provenance_sealed": packet["stamp"]["provenance_sealed"], "propositions": dict(sorted(props.items())),
            "proposition_bases": dict(sorted(prop_bases.items())),
            "audits": dict(sorted(audits.items())), "items": dict(Counter(o["outcome"] for o in outcomes)),
            "by_level_family_kind_executor_admission_certification_grade": [[*key, n] for key, n in sorted(rows.items())],
            "items_by_level_family_required_outcome": [[*key, n] for key, n in sorted(items.items())]}


def grade(packet: Mapping[str, Any], key: Mapping[str, Any], sheet: Mapping[str, Any],
          verdicts: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """The grade report. ``complete`` is false while any mapping is unconfirmed or any verdict is owed."""
    if sheet.get("packet") != packet["stamp"]["content_sha256"] or key.get("game_id") != packet["stamp"]["game_id"]:
        raise ValueError("the mapping sheet and key must belong to this packet's model and game")
    if verdicts and (verdicts.get("packet"), verdicts.get("key")) != (packet["stamp"]["content_sha256"], c.sha256(key)):
        raise ValueError("the verdict sheet must belong to this packet and this key")
    excluded = k.excluded_levels(key, packet["stamp"])
    pending_maps = mp.unconfirmed(sheet)
    maps = mp.lookup({"rows": [r for r in sheet.get("rows") or () if isinstance(r.get("confirmed"), list)]})
    items = [item for item in key["items"]]
    live = [item for item in items if str(item["level"]) not in excluded]
    ruled = {v["assertion_id"]: v for v in (verdicts or {}).get("claims") or ()}
    graded = [_grade_claim(claim, live, maps, ruled) for claim in packet["claims"]
              if str(claim["level"]) not in excluded]
    owed = [row["assertion_id"] for row in graded if row["grade"] is None]
    outcomes = _item_outcomes(items, graded, excluded)
    return {"schema": GRADE_SCHEMA, "game_id": packet["stamp"]["game_id"], "packet": packet["stamp"]["content_sha256"],
            "key": c.sha256(key), "excluded_levels": excluded, "unconfirmed_mappings": len(pending_maps),
            "owed_verdicts": len(owed), "complete": not pending_maps and not owed,
            "claims": graded, "items": outcomes, "tables": _tables(packet, graded, outcomes)}


def verdict_sheet(packet: Mapping[str, Any], key: Mapping[str, Any], report: Mapping[str, Any]) -> dict[str, Any]:
    """The human's worksheet: every in-coverage proposition the join could not settle, with the key items in reach."""
    claims = {cl["assertion_id"]: cl for cl in packet["claims"]}
    rows = []
    for row in report["claims"]:
        if row["grade"] is None:
            cl = claims[row["assertion_id"]]
            reach = [i["key_id"] for i in key["items"] if i["level"] == cl["level"] and i["family"] == cl["family"]]
            rows.append({"assertion_id": cl["assertion_id"], "level": cl["level"], "subject": cl["subject"]["handle"],
                         "family": cl["family"], "predicate": cl["predicate"], "object": cl["object"],
                         "executor": cl["executor"], "admission": cl["admission"], "status": cl["status"],
                         "key_items_in_reach": reach, "verdict": None, "satisfies": [], "note": ""})
    return {"schema": VERDICT_SHEET, "packet": report["packet"], "key": report["key"], "reviewer": None,
            "blind": None, "claims": rows}


__all__ = ["GRADES", "grade", "verdict_sheet"]
