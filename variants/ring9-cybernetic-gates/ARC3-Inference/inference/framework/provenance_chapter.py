"""WO-PE-02: the provenance chapter of world model schema v4 — the validated audit journal, absorbed once.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_02_SCHEMA_V4_PROVENANCE_v2``; Sol's
rulings 1-9 on the WO-PE-02 sweep.

A pure compiler and validator. It reads no file: the solver hands H2 the journal bytes it read once (so the file hash
and the parse come from one buffer), and the sidecar verifier is a separate, explicit step.

* ``live()`` and ``h1()``: ``integrity NOT_EVALUATED``. H1 may carry the writer's in-memory prefix, labelled
  ``WRITER_REPORTED``; it has no evidentiary authority.
* ``h2()``: the reader's verdict on the bytes (SEALED / OPEN / CORRUPT / UNAVAILABLE), the verified rows embedded once,
  the stamp (semantic seal hash and exact-file hash), reconciliation against the model's own levels, the gate-answer
  cross-check, typed and scoped references, and the verdict: ``COMPLETE`` only when nothing at all is open.
* ``attach()`` gives every level its event-id index (rows are never duplicated); ``validate_chapter()`` re-verifies
  the embedded journal and recomputes everything derivable from the model, so a forged verdict fails.

Integrity (what the bytes are) and reconciliation (whether admissions, executions, transitions, evidence and gate
products join) are kept apart. The existing ``journal_check`` fields are H2's record check and are not touched.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from inference.framework import answer_shapes as shapes
from inference.framework import audit_journal as aj
from inference.framework import product_origins as origins
from inference.framework.answer_shapes import sha16  # re-exported: the census and tests hash with it

CHAPTER_SCHEMA = "virelai-provenance-chapter-v1"
PHASES = ("H1", "H2", "LIVE_VIEW")
H2_INTEGRITY = ("SEALED", "OPEN", "CORRUPT", "UNAVAILABLE")
CAPTURE = ("ENABLED", "DISABLED", "FAILED", "UNKNOWN")
UNAVAILABLE_REASONS = ("CAPTURE_DISABLED", "JOURNAL_MISSING", "JOURNAL_UNREADABLE", "JOURNAL_NOT_SUPPLIED",
                       "CHAPTER_COMPILE_FAILED")
LIVE_VIEW = "LIVE_VIEW"
FINAL_REASONS = frozenset({"RUN_END", "BUDGET_STOP", "CONTROLLED_STOP", "CRASH", "CANCELLED"})
INDEX_KEYS = ("admissions", "executions", "answers", "selections", "annotations")
FINDINGS = frozenset({
    "ADMISSION_UNCONSUMED", "EXECUTION_NOT_RECORDED", "EVIDENCE_WITHOUT_EXECUTION", "EXECUTION_WITHOUT_EVIDENCE",
    "EXECUTION_EVIDENCE_DISAGREES", "DUPLICATE_EVIDENCE_EXECUTION", "UNGATED_TRANSITION",
    "PRODUCT_UNATTRIBUTED", "PRODUCT_REFERENCE_WITHOUT_SEMANTICS", "PRODUCT_WITHOUT_ADMITTED_ANSWER",
    "AMBIGUOUS_PRODUCT_ANSWER",
    "PRODUCT_ANSWERS_NOT_RECORDED", "UNRESOLVED_REQUIRED_REFERENCE", "INTERIM_PREFIX_CONTRADICTED",
})
CROSSCHECK_FINDINGS = frozenset({"GATE_ANSWERS_MISSING", "GATE_ANSWER_COUNT_MISMATCH", "GATE_ANSWER_MISMATCH"})
STATE_REASONS = frozenset({"JOURNAL_OPEN", "JOURNAL_CORRUPT", "JOURNAL_UNAVAILABLE", "WRITE_FAILED", "RUN_MISMATCH"})
LIVE_KEYS = frozenset({"schema", "phase", "capture", "integrity", "completeness"})
H1_KEYS = LIVE_KEYS | {"writer_reported"}
H2_KEYS = frozenset({
    "schema", "phase", "capture", "integrity", "failure", "unavailable_reason", "writer_failure", "stamp", "rows",
    "seal", "unscoped", "reconciliation", "answer_crosscheck", "typed_refs", "answer_refs", "note_refs",
    "interim_prefixes", "completeness", "completeness_scope", "reasons"})
STAMP_KEYS = frozenset({"sidecar", "journal_sha256", "seal_event_hash", "head_hash", "event_count", "run", "verified"})
_HEX64 = re.compile(r"[0-9a-f]{64}")
HINTS = ((re.compile(r"E-[0-9a-f]"), "EVIDENCE"), (re.compile(r"E\d+$"), "ENTITY"), (re.compile(r"LC-\d"), "LIFECYCLE_EVENT"),
         (re.compile(r"N\d+$"), "NOTE"), (re.compile(r"PV-"), "PROVENANCE_EVENT"), (re.compile(r"LEVER-"), "WITNESS"))


class ProvenanceChapterError(ValueError):
    """A provenance chapter violates the schema-v4 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProvenanceChapterError(message)


# ---- the three phases -------------------------------------------------------------------------------------------

def live() -> dict[str, Any]:
    return {"schema": CHAPTER_SCHEMA, "phase": LIVE_VIEW, "capture": "UNKNOWN", "integrity": "NOT_EVALUATED",
            "completeness": "NOT_EVALUATED"}


def h1(*, capture: str, writer: tuple[int, str] | None = None) -> dict[str, Any]:
    """The interim chapter: from the writer's memory only, never the file."""
    reported = None if writer is None else {"label": "WRITER_REPORTED", "event_count": int(writer[0]),
                                            "head_hash": str(writer[1])}
    return {"schema": CHAPTER_SCHEMA, "phase": "H1", "capture": capture, "integrity": "NOT_EVALUATED",
            "completeness": "PENDING", "writer_reported": reported}


def default_for(persist_reason: Any) -> dict[str, Any]:
    """What a model compiled without a journal honestly is: live, pending, or final with no journal supplied."""
    if persist_reason == LIVE_VIEW:
        return live()
    if persist_reason in FINAL_REASONS:
        return _unavailable(None, capture="UNKNOWN", reason="JOURNAL_NOT_SUPPLIED", writer_failure=None,
                            prefixes=(), persist_reason=persist_reason)
    return h1(capture="UNKNOWN")


def h2(payload: Mapping[str, Any], *, data: bytes | None, sidecar: str, capture: str = "ENABLED",
       writer_failure: str | None = None, answer_records: Sequence[Mapping[str, Any]] | None = None,
       interim_prefixes: Sequence[Mapping[str, Any]] = (), unavailable_reason: str | None = None) -> dict[str, Any]:
    """The final chapter from the journal bytes H2 read once (``None`` when there were none to read)."""
    persist_reason = (payload.get("manifest") or {}).get("persist_reason")
    prefixes = [{"event_count": int(p["event_count"]), "head_hash": str(p["head_hash"])} for p in interim_prefixes]
    if data is None:
        reason = unavailable_reason or ("CAPTURE_DISABLED" if capture == "DISABLED" else "JOURNAL_MISSING")
        return _unavailable(sidecar, capture=capture, reason=reason, writer_failure=writer_failure,
                            prefixes=prefixes, persist_reason=persist_reason)
    read = aj.read_journal_bytes(data)
    rows, seal = list(read.rows), read.seal
    stamp = {"sidecar": sidecar, "journal_sha256": hashlib.sha256(data).hexdigest(),
             "seal_event_hash": seal["event_hash"] if read.status == "SEALED" else None,
             "head_hash": rows[-1]["event_hash"] if rows else None, "event_count": len(rows),
             "run": None if read.run is None else dict(read.run), "verified": read.status == "SEALED"}
    chapter = {"schema": CHAPTER_SCHEMA, "phase": "H2", "capture": capture, "integrity": read.status,
               "failure": read.failure, "unavailable_reason": None, "writer_failure": writer_failure or None,
               "stamp": stamp, "rows": rows, "seal": seal,
               "answer_crosscheck": cross_check(rows, answer_records)}
    chapter.update(derive(payload, rows, read.status, prefixes))
    chapter.update(verdict(chapter, payload))
    return chapter


def _unavailable(sidecar: str | None, *, capture: str, reason: str, writer_failure: str | None,
                 prefixes: Sequence[Mapping[str, Any]], persist_reason: Any) -> dict[str, Any]:
    chapter = {"schema": CHAPTER_SCHEMA, "phase": "H2", "capture": capture, "integrity": "UNAVAILABLE",
               "failure": None, "unavailable_reason": reason, "writer_failure": writer_failure or None,
               "stamp": None, "rows": [], "seal": None,
               "answer_crosscheck": {"status": "NOT_EVALUATED", "compared": 0, "findings": []}}
    chapter.update(derive({"levels": [], "manifest": {"persist_reason": persist_reason}}, [], "UNAVAILABLE",
                          prefixes))
    chapter.update(verdict(chapter, {"manifest": {"persist_reason": persist_reason}}))
    return chapter


# ---- derivation: everything recomputable from the model and the embedded rows ------------------------------------

def _category(row: Mapping[str, Any]) -> str:
    operation, event = row["operation"], row["event"]
    if operation == "PROBE":
        return "admissions" if event == "ADMISSION" else "executions"
    return {"ANSWER": "answers", "G3_SELECTION": "selections", "ANNOTATION": "annotations"}[operation]


def indexes(levels: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]
            ) -> tuple[dict[Any, dict[str, list[str]]], list[str]]:
    numbers = {level["level"] for level in levels}
    index = {number: {key: [] for key in INDEX_KEYS} for number in numbers}
    unscoped = []
    for row in rows:
        if row["level"] in numbers:
            index[row["level"]][_category(row)].append(row["event_id"])
        else:
            unscoped.append(row["event_id"])
    return index, unscoped


def _is(row: Mapping[str, Any], operation: str, event: str, disposition: str | None = None) -> bool:
    return row["operation"] == operation and row["event"] == event and (
        disposition is None or row["disposition"] == disposition)


def _evidence_findings(levels: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """R2-R3: executions against recorded transitions and against the levels' evidence receipts."""
    findings: list[dict[str, Any]] = []
    by_level = {level["level"]: level for level in levels}
    executed = [row for row in rows if _is(row, "PROBE", "EXECUTION", "EXECUTED")]
    for row in executed:
        level = by_level.get(row["level"])
        transition = row["refs"]["executed_transition"]
        if level is None or transition not in (level.get("record") or {}).get("transition_ids", ()):
            findings.append({"code": "EXECUTION_NOT_RECORDED", "event_id": row["event_id"], "level": row["level"],
                             "transition_id": transition})
    by_evidence: dict[str, list[Mapping[str, Any]]] = {}
    for row in executed:
        by_evidence.setdefault(row["refs"]["evidence_id"], []).append(row)
    receipts = {}
    for level in levels:
        for ref, receipt in sorted(((level.get("receipts") or {}).get("evidence") or {}).items()):
            receipts.setdefault(ref, (level["level"], receipt.get("transition_id")))
    for ref, (number, transition) in sorted(receipts.items()):
        found = by_evidence.get(ref, [])
        if not found:
            findings.append({"code": "EVIDENCE_WITHOUT_EXECUTION", "evidence_id": ref, "level": number,
                             "transition_id": transition})
        elif len(found) > 1:
            findings.append({"code": "DUPLICATE_EVIDENCE_EXECUTION", "evidence_id": ref,
                             "event_ids": [row["event_id"] for row in found]})
        elif (found[0]["level"], found[0]["refs"]["executed_transition"]) != (number, transition):
            findings.append({"code": "EXECUTION_EVIDENCE_DISAGREES", "evidence_id": ref,
                             "event_id": found[0]["event_id"]})
    for ref, found in sorted(by_evidence.items()):
        if ref not in receipts:
            findings.append({"code": "EXECUTION_WITHOUT_EVIDENCE", "evidence_id": ref,
                             "event_ids": [row["event_id"] for row in found]})
    return findings


def _ungated(levels: Sequence[Mapping[str, Any]]) -> tuple[list[list[int]], list[dict[str, Any]]]:
    """R4: a recorded transition with no evidence receipt is acceptable only as a typed harness reset."""
    resets, findings = [], []
    for level in levels:
        record = level.get("record") or {}
        evidenced = {receipt.get("transition_id") for receipt in ((level.get("receipts") or {}).get("evidence") or {})
                     .values()}
        allowed = set(record.get("reset_transition_ids") or ())
        for transition in record.get("transition_ids") or ():
            if transition in evidenced:
                continue
            if transition in allowed:
                resets.append([level["level"], transition])
            else:
                findings.append({"code": "UNGATED_TRANSITION", "level": level["level"], "transition_id": transition})
    return resets, findings


def _candidates(answers: Sequence[Mapping[str, Any]], gate_id: str, number: Any, ref: Mapping[str, Any]) -> list[str]:
    return [row["event_id"] for row in answers
            if row["gate_id"] == gate_id and row["level"] == number and row["refs"]["answer_id"] == ref["answer_id"]
            and not shapes.unmet(ref["clauses"], row["effective"])]


def _certified_joins(entry: Mapping[str, Any], base: Mapping[str, Any], answers: Sequence[Mapping[str, Any]]
                     ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """R6 for an ANSWER_CERTIFIED product: each stored reference joins one admitted answer of the same gate, level and
    id whose effective payload contains every clause (revision 2: directional containment, never overlap)."""
    joins, findings = [], []
    for ref in entry["answers"]:
        candidates = _candidates(answers, entry["gate_id"], base["level"], ref)
        status = "EXACT" if len(candidates) == 1 else "AMBIGUOUS" if candidates else "NO_ADMITTED_ANSWER"
        joins.append({**base, "answer_id": ref["answer_id"], "status": status,
                      "answer_event_id": candidates[0] if status == "EXACT" else None, "candidates": candidates})
        if status == "AMBIGUOUS":
            findings.append({"code": "AMBIGUOUS_PRODUCT_ANSWER", **base, "answer_id": ref["answer_id"],
                             "candidates": candidates})
        elif status == "NO_ADMITTED_ANSWER":
            findings.append({"code": "PRODUCT_WITHOUT_ADMITTED_ANSWER", **base, "answer_id": ref["answer_id"]})
        if not shapes.semantic(ref["clauses"]) and entry["basis"] not in origins.ID_DERIVED_BASES:
            findings.append({"code": "PRODUCT_REFERENCE_WITHOUT_SEMANTICS", **base, "answer_id": ref["answer_id"]})
    return joins, findings


def _product_joins(levels: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]
                   ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """R6: every product by its origin. GATE_DERIVED joins nothing and blocks nothing; UNATTRIBUTED always blocks;
    ANSWER_CERTIFIED joins exactly. Never 'the last answer before the revision'."""
    answers = [row for row in rows if _is(row, "ANSWER", "ADMISSION", "ADMITTED")]
    joins, findings = [], []
    for level in levels:
        stored = level.get("product_answers")
        for product_id in sorted(((level.get("receipts") or {}).get("products") or {})):
            entry = None if stored is None else stored.get(product_id)
            base = {"level": level["level"], "product_id": product_id}
            if entry is None:
                joins.append({**base, "product_type": None, "gate_id": None, "origin": None, "basis": None,
                              "answer_id": None, "status": "NOT_RECORDED", "answer_event_id": None, "candidates": []})
                findings.append({"code": "PRODUCT_ANSWERS_NOT_RECORDED", **base})
                continue
            meta = {**base, **{key: entry[key] for key in ("product_type", "gate_id", "origin", "basis")}}
            if entry["origin"] == "ANSWER_CERTIFIED":
                certified, blocked = _certified_joins(entry, meta, answers)
                joins += certified
                findings += blocked
                continue
            joins.append({**meta, "answer_id": None, "status": entry["origin"], "answer_event_id": None,
                          "candidates": []})
            if entry["origin"] == "UNATTRIBUTED":
                findings.append({"code": "PRODUCT_UNATTRIBUTED", **base, "basis": entry["basis"]})
    return joins, findings


def _resolver(levels: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]):
    tables: dict[str, dict[str, set[Any]]] = {kind: {} for kind in ("EVIDENCE", "WITNESS", "PRODUCT", "ENTITY")}

    def note(kind: str, ident: Any, number: Any) -> None:
        if ident:
            tables[kind].setdefault(str(ident), set()).add(number)

    for level in levels:
        number, receipts = level["level"], level.get("receipts") or {}
        for ref in receipts.get("evidence") or {}:
            note("EVIDENCE", ref, number)
        for ref, witness in (receipts.get("witnesses") or {}).items():
            note("WITNESS", ref, number)
            note("ENTITY", witness.get("entity_id"), number)
        for ref in receipts.get("products") or {}:
            note("PRODUCT", ref, number)
        certified = level.get("certified") or {}
        for item in list(certified.get("roles") or ()) + list(certified.get("scoped_nulls") or ()):
            note("ENTITY", item.get("entity_id"), number)
        for track in (level.get("observation") or {}).get("tracks") or ():
            note("ENTITY", (track.get("g3_join") or {}).get("entity_id"), number)
    row_ids = {row["event_id"] for row in rows}

    def resolve(ident: str, number: Any) -> tuple[str, Any, Any]:
        for kind in ("EVIDENCE", "WITNESS", "PRODUCT", "ENTITY"):
            found = tables[kind].get(ident)
            if found:
                return kind, {"level": number} if number in found else {"levels": sorted(found)}, None
        if ident in row_ids:
            return "PROVENANCE_EVENT", None, None
        hint = next((name for pattern, name in HINTS if pattern.match(ident)), None)
        return "UNRESOLVED", None, hint

    return resolve


def _typed(levels: Sequence[Mapping[str, Any]], rows: Sequence[Mapping[str, Any]]
           ) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    resolve = _resolver(levels, rows)
    typed, findings = {}, []

    def entry(field: str, ident: Any, number: Any, required: bool) -> dict[str, Any]:
        kind, scope, hint = resolve(str(ident), number)
        return {"field": field, "kind": kind, "id": str(ident), "scope": scope, "required": required, "hint": hint}

    for row in rows:
        refs: list[dict[str, Any]] = []
        if _is(row, "PROBE", "EXECUTION", "EXECUTED"):
            refs.append(entry("evidence_id", row["refs"]["evidence_id"], row["level"], True))
        elif _is(row, "ANSWER", "ADMISSION", "ADMITTED") and isinstance(row["effective"], Mapping):
            cited = row["effective"].get("evidence_refs")
            for ident in cited if isinstance(cited, list) else ():
                if ident not in (None, ""):
                    refs.append(entry("evidence_refs", ident, row["level"], False))
            single = row["effective"].get("evidence_ref")
            if isinstance(single, (str, int)) and single != "":
                refs.append(entry("evidence_ref", single, row["level"], False))
        if refs:
            typed[row["event_id"]] = refs
            findings.extend({"code": "UNRESOLVED_REQUIRED_REFERENCE", "event_id": row["event_id"], "id": item["id"]}
                            for item in refs if item["required"] and item["kind"] == "UNRESOLVED")
    return typed, findings


def _scoped(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    answer_refs, note_refs, seen = {}, {}, {}
    for row in rows:
        if _is(row, "ANSWER", "ADMISSION", "ADMITTED"):
            key = (row["gate_id"], row["level"], row["life"], row["refs"]["answer_id"])
            seen[key] = seen.get(key, 0) + 1
            answer_refs[row["event_id"]] = {"kind": "ANSWER", "gate_id": row["gate_id"], "level": row["level"],
                                            "life": row["life"], "answer_id": row["refs"]["answer_id"],
                                            "ordinal": seen[key]}
        if row["operation"] == "ANNOTATION" and row["refs"]["note_ids"]:
            note_refs[row["event_id"]] = [
                {"kind": "NOTE", "level": row["level"], "life": row["life"], "local_id": local,
                 "ref": f"NOTE:L{row['level']}:F{row['life']}:{local}"} for local in row["refs"]["note_ids"]]
    return answer_refs, note_refs


def _prefix_checks(rows: Sequence[Mapping[str, Any]], integrity: str,
                   prefixes: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    checked = []
    for prefix in prefixes:
        count, head = int(prefix["event_count"]), str(prefix["head_hash"])
        if count <= len(rows):
            actual = aj.GENESIS if count == 0 else rows[count - 1]["event_hash"]
            status = "VERIFIED" if actual == head else "CONTRADICTED"
        else:
            status = "CONTRADICTED" if integrity == "SEALED" else "UNVERIFIABLE"
        checked.append({"event_count": count, "head_hash": head, "status": status})
    return checked


def derive(payload: Mapping[str, Any], rows: Sequence[Mapping[str, Any]], integrity: str,
           prefixes: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Everything the chapter states that the model and its embedded rows determine (the validator recomputes it)."""
    levels = list(payload.get("levels") or ())
    _index, unscoped = indexes(levels, rows)
    checked = _prefix_checks(rows, integrity, prefixes)
    if integrity == "UNAVAILABLE":
        return {"unscoped": [], "typed_refs": {}, "answer_refs": {}, "note_refs": {}, "interim_prefixes": checked,
                "reconciliation": {"status": "NOT_EVALUATED", "findings": [], "ungated_resets": [],
                                   "product_joins": []}}
    admitted = [row for row in rows if _is(row, "PROBE", "ADMISSION", "ADMITTED")]
    consumed = {row["refs"]["admission_event_id"] for row in rows if _is(row, "PROBE", "EXECUTION")}
    findings = [{"code": "ADMISSION_UNCONSUMED", "event_id": row["event_id"]} for row in admitted
                if row["event_id"] not in consumed]
    findings += _evidence_findings(levels, rows)
    resets, ungated = _ungated(levels)
    joins, product_findings = _product_joins(levels, rows)
    typed, unresolved = _typed(levels, rows)
    findings += ungated + product_findings + unresolved
    findings += [{"code": "INTERIM_PREFIX_CONTRADICTED", "event_count": item["event_count"]}
                 for item in checked if item["status"] == "CONTRADICTED"]
    answer_refs, note_refs = _scoped(rows)
    return {"unscoped": unscoped, "typed_refs": typed, "answer_refs": answer_refs, "note_refs": note_refs,
            "interim_prefixes": checked,
            "reconciliation": {"status": "MISMATCH" if findings else "RECONCILED", "findings": findings,
                               "ungated_resets": resets, "product_joins": joins}}


def _sidecar_unmet(row: Mapping[str, Any], record: Mapping[str, Any]) -> list[str]:
    """The sidecar's accepted answer, with only the named bookkeeping and gate-state fields removed, projected through
    its shape (so a missing or extra field is refused) and contained in the journal's effective payload."""
    try:
        ref = shapes.reference(row["gate_id"], shapes.sidecar_answer(row["gate_id"], record))
    except shapes.AnswerProjectionError as exc:
        return [exc.code]
    if ref["answer_id"] != row["refs"]["answer_id"]:
        return ["answer_id"]
    return shapes.unmet(ref["clauses"], row["effective"])


def cross_check(rows: Sequence[Mapping[str, Any]], records: Sequence[Mapping[str, Any]] | None) -> dict[str, Any]:
    """R7: the k-th admitted answer against line k of ``_gate_answers.jsonl``: gate, executor, answer id, payload."""
    answers = [row for row in rows if _is(row, "ANSWER", "ADMISSION", "ADMITTED")]
    if records is None:
        findings = [{"code": "GATE_ANSWERS_MISSING", "answers": len(answers)}] if answers else []
        return {"status": "MISMATCH" if findings else "MATCHED", "compared": 0, "findings": findings}
    findings = []
    if len(records) != len(answers):
        findings.append({"code": "GATE_ANSWER_COUNT_MISMATCH", "answers": len(answers), "records": len(records)})
    for ordinal, (row, record) in enumerate(zip(answers, records), start=1):
        mismatch = [field for field, ok in (("gate_id", row["gate_id"] == record.get("gate_id")),
                                            ("executor", row["executor"] == record.get("executor"))) if not ok]
        unmet = [] if "gate_id" in mismatch else _sidecar_unmet(row, record)
        mismatch += ["answer_id"] if "answer_id" in unmet else []
        payload = [field for field in unmet if field != "answer_id"]
        findings.extend({"code": "GATE_ANSWER_MISMATCH", "ordinal": ordinal, "field": field} for field in mismatch)
        if payload:
            findings.append({"code": "GATE_ANSWER_MISMATCH", "ordinal": ordinal, "field": "payload", "unmet": payload})
    return {"status": "MISMATCH" if findings else "MATCHED", "compared": min(len(records), len(answers)),
            "findings": findings}


def verdict(chapter: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    """COMPLETE only with a verified seal of this run and nothing open; otherwise every reason, enumerated."""
    reasons = set()
    integrity = chapter["integrity"]
    if integrity != "SEALED":
        reasons.add(f"JOURNAL_{integrity}")
    if chapter.get("writer_failure"):
        reasons.add("WRITE_FAILED")
    run = (chapter.get("stamp") or {}).get("run")
    if run is not None and run.get("run_stem") != payload.get("run_stem"):
        reasons.add("RUN_MISMATCH")
    reasons |= {finding["code"] for finding in chapter["reconciliation"]["findings"]}
    reasons |= {finding["code"] for finding in chapter["answer_crosscheck"]["findings"]}
    complete = not reasons and integrity == "SEALED" and bool((chapter.get("stamp") or {}).get("verified"))
    crash = (payload.get("manifest") or {}).get("persist_reason") == "CRASH"
    return {"completeness": "COMPLETE" if complete else "INCOMPLETE",
            "completeness_scope": ("THROUGH_RECORDED_TERMINATION" if crash else "RUN") if complete else None,
            "reasons": sorted(reasons)}


# ---- attaching and validating -------------------------------------------------------------------------------------

def attach(payload: Mapping[str, Any]) -> dict[str, Any]:
    """The payload with its chapter (a default when none was supplied) and every level's event-id index.

    A live view's chapter is always ``live()``: a model relabelled as a live view (never written) carries no evidence
    from any journal, whatever chapter it had."""
    result = dict(payload)
    chapter = result.get("provenance")
    reason = (result.get("manifest") or {}).get("persist_reason")
    if chapter is None or reason == LIVE_VIEW:
        chapter = default_for(reason)
    chapter = dict(chapter)
    rows = (chapter.get("rows") or []) if chapter.get("phase") == "H2" else []
    index, unscoped = indexes(result.get("levels") or [], rows)
    result["levels"] = [{**level, "provenance_index": index[level["level"]]} for level in result.get("levels") or []]
    if chapter.get("phase") == "H2":
        chapter["unscoped"] = unscoped
    result["provenance"] = chapter
    return result


def _expected_phase(persist_reason: Any) -> str:
    return LIVE_VIEW if persist_reason == LIVE_VIEW else "H2" if persist_reason in FINAL_REASONS else "H1"


def validate_chapter(payload: Mapping[str, Any]) -> None:
    """The v4 provenance contract (pure): shape, the embedded journal re-verified, every derivable field recomputed."""
    chapter = payload.get("provenance")
    _require(isinstance(chapter, Mapping) and chapter.get("schema") == CHAPTER_SCHEMA,
             "a v4 model carries a provenance chapter")
    phase = chapter.get("phase")
    _require(phase == _expected_phase((payload.get("manifest") or {}).get("persist_reason")),
             f"provenance phase {phase!r} does not fit persist_reason")
    _require(chapter.get("capture") in CAPTURE, "provenance.capture is a known value")
    levels = list(payload.get("levels") or ())
    rows = list(chapter.get("rows") or ()) if phase == "H2" else []
    index, unscoped = indexes(levels, rows)
    for level in levels:
        _require(level.get("provenance_index") == index[level["level"]],
                 f"level {level.get('level')}'s provenance_index does not partition the embedded rows")
        _validate_product_answers(level)
    if phase == LIVE_VIEW:
        _require(set(chapter) == LIVE_KEYS and chapter["integrity"] == "NOT_EVALUATED"
                 and chapter["completeness"] == "NOT_EVALUATED", "a live view's chapter is NOT_EVALUATED")
        return
    if phase == "H1":
        _require(set(chapter) == H1_KEYS and chapter["integrity"] == "NOT_EVALUATED"
                 and chapter["completeness"] == "PENDING", "an H1 chapter is PENDING and NOT_EVALUATED")
        reported = chapter["writer_reported"]
        _require(reported is None or (set(reported) == {"label", "event_count", "head_hash"}
                                      and reported["label"] == "WRITER_REPORTED"
                                      and isinstance(reported["event_count"], int) and reported["event_count"] >= 0
                                      and bool(_HEX64.fullmatch(str(reported["head_hash"])))),
                 "an H1 prefix is WRITER_REPORTED {event_count, head_hash}")
        return
    _validate_h2(payload, chapter, rows, unscoped)


def _validate_product_answers(level: Mapping[str, Any]) -> None:
    stored = level.get("product_answers")
    if stored is None:
        return
    _require(isinstance(stored, Mapping), "product_answers is a mapping")
    for product_id, entry in stored.items():
        problem = origins.entry_problem(entry)
        _require(problem is None, f"product_answers[{product_id}]: {problem}")


def _validate_h2(payload: Mapping[str, Any], chapter: Mapping[str, Any], rows: list, unscoped: list) -> None:
    _require(set(chapter) == H2_KEYS, "an H2 chapter has exactly the declared keys")
    integrity = chapter["integrity"]
    _require(integrity in H2_INTEGRITY, "H2 integrity is SEALED, OPEN, CORRUPT or UNAVAILABLE")
    if integrity == "UNAVAILABLE":
        _require(not rows and chapter["seal"] is None and chapter["stamp"] is None and chapter["failure"] is None
                 and chapter["unavailable_reason"] in UNAVAILABLE_REASONS,
                 "an UNAVAILABLE chapter has no rows, seal or stamp, and a typed reason")
    else:
        _require(chapter["unavailable_reason"] is None, "only an UNAVAILABLE chapter names an unavailable reason")
        read = aj.verify_embedded(rows, chapter["seal"])
        expected = "SEALED" if integrity == "SEALED" else "OPEN"
        _require(read.status == expected and len(read.rows) == len(rows),
                 f"the embedded rows do not re-verify as a {expected} journal ({read.status}: {read.failure})")
        _require(integrity == "SEALED" or chapter["seal"] is None, "only a SEALED chapter embeds a seal")
        failure = chapter["failure"]
        if integrity == "CORRUPT":
            _require(isinstance(failure, Mapping) and set(failure) == {"code", "line", "detail"}
                     and failure["code"] in aj.FAILURES, "a CORRUPT chapter keeps its typed failure")
        else:
            _require(failure is None, "only a CORRUPT chapter carries a failure")
        _validate_stamp(chapter, rows, read)
    _require(chapter["unscoped"] == unscoped, "provenance.unscoped does not match the embedded rows")
    prefixes = [{"event_count": item["event_count"], "head_hash": item["head_hash"]}
                for item in chapter["interim_prefixes"]]
    derived = derive(payload, rows, integrity, prefixes)
    for key, value in derived.items():
        _require(chapter[key] == value, f"provenance.{key} is not what the model and its rows give")
    crosscheck = chapter["answer_crosscheck"]
    _require(set(crosscheck) == {"status", "compared", "findings"}
             and all(item.get("code") in CROSSCHECK_FINDINGS for item in crosscheck["findings"])
             and crosscheck["status"] == ("NOT_EVALUATED" if integrity == "UNAVAILABLE"
                                          else "MISMATCH" if crosscheck["findings"] else "MATCHED"),
             "the gate-answer cross-check is internally consistent")
    stated = {key: chapter[key] for key in ("completeness", "completeness_scope", "reasons")}
    _require(stated == verdict(chapter, payload), "provenance completeness does not follow from its own fields")


def _validate_stamp(chapter: Mapping[str, Any], rows: list, read: Any) -> None:
    stamp = chapter["stamp"]
    _require(isinstance(stamp, Mapping) and set(stamp) == STAMP_KEYS, "the stamp has exactly the declared keys")
    sealed = chapter["integrity"] == "SEALED"
    _require(bool(_HEX64.fullmatch(str(stamp["journal_sha256"]))), "the stamp names the exact file hash")
    _require(stamp["event_count"] == len(rows)
             and stamp["head_hash"] == (rows[-1]["event_hash"] if rows else None)
             and stamp["seal_event_hash"] == (chapter["seal"]["event_hash"] if sealed else None)
             and stamp["verified"] is sealed
             and stamp["run"] == (None if read.run is None else dict(read.run)),
             "the stamp disagrees with the embedded journal (never verified without a valid matching seal)")


# ---- the sidecar verifier (separate, explicit, reads a file) -----------------------------------------------------

def verify_sidecar(model: Mapping[str, Any], path: str | Path) -> dict[str, Any]:
    """Whether the journal file on disk is the one the model absorbed. A missing or replaced file never invalidates a
    written model: this only reports."""
    stamp = (model.get("provenance") or {}).get("stamp") or {}
    expected = stamp.get("journal_sha256")
    if not expected:
        return {"status": "NOT_APPLICABLE"}
    target = Path(path)
    if not target.is_file():
        return {"status": "MISSING", "path": str(target)}
    data = target.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual == expected:
        return {"status": "VERIFIED", "journal_sha256": actual}
    read = aj.read_journal_bytes(data)
    same_chain = read.status == "SEALED" and stamp.get("seal_event_hash") and \
        read.seal["event_hash"] == stamp["seal_event_hash"]
    return {"status": "REWRITTEN" if same_chain else "SUBSTITUTED", "journal_sha256": actual,
            "expected_sha256": expected}


__all__ = [
    "CHAPTER_SCHEMA", "FINAL_REASONS", "INDEX_KEYS", "ProvenanceChapterError", "attach", "cross_check", "default_for", "derive", "h1", "h2", "indexes", "live", "sha16",
    "validate_chapter", "verdict", "verify_sidecar",
]
