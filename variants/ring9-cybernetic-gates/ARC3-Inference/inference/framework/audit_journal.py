"""WO-PE-01: the audit journal, an append-only, hash-chained record of every gated proposal.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v3``; rulings
``RULINGS_PAPER_EVIDENCE_v1`` D1-D4 and Sol's revision-2 order. (Renamed from ``provenance.py`` at revision 2, so it
is never confused with the weave's cell-ownership provenance.)

Who proposed each gated operation, what they submitted, and whether a gate admitted, refused or executed it. One
row per decision, in one normalized vocabulary across all gates (D2):

* operation ``PROBE`` | ``ANSWER`` | ``G3_SELECTION`` | ``ANNOTATION``;
* event ``OPPORTUNITY`` | ``ADMISSION`` | ``EXECUTION``;
* disposition ``OFFERED`` | ``ADMITTED`` | ``REFUSED`` | ``EXECUTED`` | ``NOT_ATTEMPTED`` | ``SUPERSEDED`` |
  ``UNCERTIFIED``, in the valid combinations of ``VALID``.

The file is deterministic: strict canonical JSON (no ``default``, no non-finite number, no non-string key), a
per-journal sequence, a deterministic ``event_id``, ``previous_event_hash`` and ``event_hash``, and no wall-clock
value, path or random value anywhere. A closing ``SEAL`` record is journal control metadata, outside the D2 event
vocabulary: it names the run it closes (so even an empty journal has an identity) and lets a reader tell a complete
journal from one whose tail is missing. A journal is only ever extended by the run that began it.

A probe's ``ADMISSION / ADMITTED`` row is its operation anchor. Every probe ``EXECUTION`` row names that exact row in
``refs.admission_event_id``; the join must agree on operation, probe, executor, run, gate, level and life, and one
admission is consumed by at most one execution. ``probe_id`` alone is never a join key: it recurs across levels,
lives and replays.

``read_journal`` is a trust boundary: it validates the whole row contract and returns the verified prefix, a status
and a typed failure. The writer applies the same checks before it writes, so it never writes a row the reader would
reject. This module is neutral: it imports nothing from the agent, the gates or the census. A write failure never
raises into gameplay: the journal marks itself failed and stops, so the file stays a verifiable prefix.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

SCHEMA = "virelai-provenance-v1"
GENESIS = "0" * 64
EXECUTORS = ("DUCK", "CONTROLLER", "SYSTEM")
VALID: dict[str, dict[str, frozenset[str]]] = {
    "PROBE": {"ADMISSION": frozenset({"ADMITTED", "REFUSED"}), "EXECUTION": frozenset({"EXECUTED", "NOT_ATTEMPTED"})},
    "ANSWER": {"ADMISSION": frozenset({"ADMITTED", "REFUSED"})},
    "G3_SELECTION": {"OPPORTUNITY": frozenset({"OFFERED", "NOT_ATTEMPTED"}),
                     "ADMISSION": frozenset({"ADMITTED", "REFUSED", "SUPERSEDED"}),
                     "EXECUTION": frozenset({"EXECUTED"})},
    "ANNOTATION": {"ADMISSION": frozenset({"UNCERTIFIED", "REFUSED"})},
}
REASONED = frozenset({"REFUSED", "NOT_ATTEMPTED", "SUPERSEDED"})
REASON_CODES = frozenset({"GATE_CONTRACT", "ORIENTATION_DUE", "ANNOTATION_INVALID", "ACTION_CONTRACT",
                          "TERMINAL_STATE", "NOT_EXECUTED", "EXECUTION_ERROR", "G3_EVENT"})
REF_KEYS = ("question_id", "subject", "probe_id", "answer_id", "evidence_id", "executed_transition", "note_ids",
            "source_event", "admission_event_id")
_REF_TEXT = ("question_id", "subject", "probe_id", "answer_id", "evidence_id", "admission_event_id")
BODY_KEYS = ("level", "life", "gate_id", "at_transition", "executor", "operation", "event", "disposition",
             "submitted", "effective", "field_sources", "refs", "reason")
EVENT_KEYS = frozenset({"schema", "record", "seq", "event_id", "previous_event_hash", "event_hash", "run",
                        *BODY_KEYS})
SEAL_KEYS = frozenset({"schema", "record", "seq", "run", "previous_event_hash", "event_hash", "event_count",
                       "head_hash"})
RUN_KEYS = frozenset({"run_stem", "game_id"})
SOURCE_EVENT_KEYS = frozenset({"event", "actor", "phase", "gate_revision"})
FIELD_SOURCES = ("SUBMITTER", "CONTROLLER_FILLED", "SUBMITTER_CONFIRMED_BY_CONTROLLER")
# The fields on which a probe execution must agree with the admission it consumes.
JOIN_FIELDS = ("operation", "executor", "run", "gate_id", "level", "life")
# G3 selection events (g3_selection.py) translated into the audit vocabulary; the G3 vocabulary is kept in
# refs.source_event, never replaced. COVERAGE_RESUMED records Duck's unused opportunity: its executor is DUCK, and
# the controller's actor stays in refs.source_event.
G3_TRANSLATION = {
    "HANDOFF": ("OPPORTUNITY", "OFFERED"),
    "COVERAGE_RESUMED": ("OPPORTUNITY", "NOT_ATTEMPTED"),
    "ADMITTED": ("ADMISSION", "ADMITTED"),
    "REFUSED": ("ADMISSION", "REFUSED"),
    "STALE": ("ADMISSION", "SUPERSEDED"),
    "FINISHED": ("EXECUTION", "EXECUTED"),
}
STATUSES = ("SEALED", "OPEN", "CORRUPT")
FAILURES = ("TRUNCATED_TAIL", "MALFORMED_ROW", "SCHEMA_INVALID", "SEQUENCE_GAP", "DUPLICATE_SEQUENCE",
            "SEQUENCE_REORDERED", "HASH_MISMATCH", "CHAIN_BROKEN", "EVENT_ID_MISMATCH", "RUN_MISMATCH",
            "SEAL_MISMATCH", "ROWS_AFTER_SEAL", "ADMISSION_MISSING", "ADMISSION_MISMATCH",
            "ADMISSION_ALREADY_CONSUMED")
_HASH = re.compile(r"[0-9a-f]{64}")
_EVENT_ID = re.compile(r"PV-[0-9a-f]{16}")


class ProvenanceError(ValueError):
    """A provenance row or journal violates the contract."""


class JournalFault(ProvenanceError):
    """A typed reader failure: ``code`` is one of ``FAILURES``."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code, self.detail = code, detail


# ---- strict canonical JSON --------------------------------------------------------------------------------------

def _strict(value: Any) -> None:
    """Only JSON's own values: never an object's string representation, a non-finite number or a coerced key."""
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite number {value!r} is not JSON")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"non-string key {key!r} is not JSON")
            _strict(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _strict(item)
        return
    raise TypeError(f"unsupported {type(value).__name__} is not JSON")


def _dumps(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def canonical(value: Any) -> bytes:
    """Strict canonical bytes; raises ``TypeError`` or ``ValueError`` on anything that is not plain JSON."""
    _strict(value)
    return _dumps(value)


def normalized(value: Any) -> Any:
    """The JSON value of a submitted payload, exactly as it would be serialized (tuples become lists)."""
    return json.loads(canonical(value))


def _sha(value: Any) -> str:
    return hashlib.sha256(_dumps(value)).hexdigest()


def _hashed(row: Mapping[str, Any]) -> str:
    return _sha({key: value for key, value in row.items() if key != "event_hash"})


def event_id(run: Mapping[str, Any], seq: int, body: Mapping[str, Any]) -> str:
    """The deterministic identity of one event: its run, its sequence and its content."""
    return "PV-" + _sha({"run": run, "seq": seq, "content": {key: body[key] for key in BODY_KEYS}})[:16]


def _reject_constant(name: str) -> Any:
    raise ValueError(f"non-finite number {name} is not JSON")


# ---- the row contract -------------------------------------------------------------------------------------------

def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProvenanceError(message)


def _optional(value: Any, kind: type) -> bool:
    return value is None or (isinstance(value, kind) and not isinstance(value, bool))


def _check_refs(refs: Any) -> None:
    _require(isinstance(refs, Mapping) and set(refs) == set(REF_KEYS), "refs must carry exactly the reference keys")
    for key in _REF_TEXT:
        _require(_optional(refs[key], str), f"refs.{key} must be text or null")
    _require(_optional(refs["executed_transition"], int), "refs.executed_transition must be an integer or null")
    notes = refs["note_ids"]
    _require(notes is None or (isinstance(notes, list) and all(isinstance(n, str) for n in notes)),
             "refs.note_ids must be a list of text or null")
    source = refs["source_event"]
    if source is not None:
        _require(isinstance(source, Mapping) and set(source) == SOURCE_EVENT_KEYS
                 and source["event"] in G3_TRANSLATION and isinstance(source["actor"], str)
                 and _optional(source["phase"], str) and _optional(source["gate_revision"], int),
                 "refs.source_event must be a translated G3 event")


def _check_reason(content: Mapping[str, Any]) -> None:
    reason, disposition = content.get("reason"), content.get("disposition")
    if reason is not None:
        _require(isinstance(reason, Mapping) and set(reason) == {"code", "text"} and reason["code"] in REASON_CODES
                 and isinstance(reason["text"], str) and bool(reason["text"]), "a reason is a typed code and its text")
    if disposition in REASONED or content.get("event") == "OPPORTUNITY":
        _require(reason is not None, f"{content.get('operation')}/{disposition} needs a typed reason")


def check_content(content: Mapping[str, Any]) -> None:
    """The audit fields of one event: types, a valid combination, a known executor, a typed reason where one is owed,
    the references an execution owes, and the field-source map only an answer carries."""
    operation, event, disposition = content.get("operation"), content.get("event"), content.get("disposition")
    _require(disposition in VALID.get(operation, {}).get(event, ()),
             f"invalid combination {operation}/{event}/{disposition}")
    _require(content.get("executor") in EXECUTORS, f"unknown executor {content.get('executor')!r}")
    for key in ("level", "life", "at_transition"):
        _require(_optional(content.get(key), int), f"{key} must be an integer or null")
    _require(_optional(content.get("gate_id"), str), "gate_id must be text or null")
    _check_reason(content)
    refs = content.get("refs")
    _check_refs(refs)
    probe_execution = operation == "PROBE" and event == "EXECUTION"
    _require(probe_execution or refs["admission_event_id"] is None, "only a probe execution names an admission")
    if probe_execution:
        _require(bool(refs["probe_id"]), "a probe execution names its probe")
        if disposition == "EXECUTED":
            _require(bool(refs["evidence_id"]) and refs["executed_transition"] is not None,
                     "an executed probe names its evidence and transition")
    sources = content.get("field_sources")
    if operation == "ANSWER":
        _require(isinstance(sources, Mapping) and set(sources.values()) <= set(FIELD_SOURCES),
                 "an answer carries a field-source map")
    else:
        _require(sources is None and content.get("effective") is None, "only answers carry effective payloads")


def _check_event_shape(row: Mapping[str, Any]) -> None:
    _require(row.get("record") == "EVENT", f"record must be EVENT or SEAL, not {row.get('record')!r}")
    _require(set(row) == EVENT_KEYS, "event keys differ from the schema")
    _require(row["schema"] == SCHEMA, f"unknown schema {row['schema']!r}")
    _require(_optional(row["seq"], int) and row["seq"] is not None and row["seq"] > 0,
             "seq must be a positive integer")
    _check_run(row["run"])
    _require(isinstance(row["event_id"], str) and bool(_EVENT_ID.fullmatch(row["event_id"])), "malformed event_id")
    for key in ("previous_event_hash", "event_hash"):
        _require(isinstance(row[key], str) and bool(_HASH.fullmatch(row[key])), f"malformed {key}")
    check_content(row)


def _check_run(run: Any) -> None:
    _require(isinstance(run, Mapping) and set(run) == RUN_KEYS
             and all(isinstance(run[key], str) and run[key] for key in RUN_KEYS),
             "run must carry exactly a nonempty run_stem and game_id")


def _check_seal_shape(row: Mapping[str, Any]) -> None:
    _require(set(row) == SEAL_KEYS, "seal keys differ from the schema")
    _require(row["schema"] == SCHEMA, f"unknown seal schema {row['schema']!r}")
    _check_run(row["run"])
    _require(_optional(row["seq"], int) and row["seq"] is not None and row["seq"] > 0,
             "seq must be a positive integer")
    _require(_optional(row["event_count"], int) and row["event_count"] is not None, "event_count must be an integer")
    for key in ("previous_event_hash", "head_hash", "event_hash"):
        _require(isinstance(row[key], str) and bool(_HASH.fullmatch(row[key])), f"malformed {key}")


def make_refs(**values: Any) -> dict[str, Any]:
    unknown = set(values) - set(REF_KEYS)
    _require(not unknown, f"unknown reference keys {sorted(unknown)}")
    return {key: normalized(values.get(key)) for key in REF_KEYS}


def _seal_row(seq: int, run: Mapping[str, Any], previous: str, count: int, head: str) -> dict[str, Any]:
    """Journal control metadata (outside the D2 vocabulary): the run it closes, and the prefix it seals."""
    row = {"schema": SCHEMA, "record": "SEAL", "seq": seq, "run": normalized(run), "previous_event_hash": previous,
           "event_count": count, "head_hash": head}
    row["event_hash"] = _hashed(row)
    return row


# ---- the chain: one verifier for the writer and the reader ------------------------------------------------------

@dataclass
class _Chain:
    """What a valid prefix has established: its head, its run, its open admissions and its joins."""

    head: str = GENESIS
    count: int = 0
    run: dict[str, Any] | None = None
    admissions: dict[str, tuple[Any, ...]] = field(default_factory=dict)
    consumed: set[str] = field(default_factory=set)
    joins: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def _key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        return (row["refs"]["probe_id"], *(json.dumps(row[name], sort_keys=True) for name in JOIN_FIELDS))

    def check_event(self, row: Mapping[str, Any], *, hashes: bool = True) -> None:
        """Raise ``JournalFault`` unless ``row`` is the valid next event of this chain."""
        try:
            _check_event_shape(row)
        except ProvenanceError as exc:
            raise JournalFault("SCHEMA_INVALID", str(exc)) from None
        if hashes and row["event_hash"] != _hashed(row):
            raise JournalFault("HASH_MISMATCH", "the row's hash does not match its content")
        if row["previous_event_hash"] != self.head:
            raise JournalFault("CHAIN_BROKEN", "the row does not chain to the previous row")
        if hashes and row["event_id"] != event_id(row["run"], row["seq"], row):
            raise JournalFault("EVENT_ID_MISMATCH", "the event_id is not the one its run, sequence and content give")
        if self.run is not None and row["run"] != self.run:
            raise JournalFault("RUN_MISMATCH", f"run {row['run']} in a journal of run {self.run}")
        if row["operation"] == "PROBE" and row["event"] == "EXECUTION":
            self._check_join(row)

    def _check_join(self, row: Mapping[str, Any]) -> None:
        admission = row["refs"]["admission_event_id"]
        if not admission or admission not in self.admissions:
            raise JournalFault("ADMISSION_MISSING", f"execution names no admitted probe admission ({admission!r})")
        if admission in self.consumed:
            raise JournalFault("ADMISSION_ALREADY_CONSUMED", f"admission {admission} was already executed")
        if self.admissions[admission] != self._key(row):
            raise JournalFault("ADMISSION_MISMATCH",
                               f"execution disagrees with admission {admission} on probe, executor, run, gate, "
                               "level or life")

    def accept(self, row: Mapping[str, Any]) -> None:
        if row["operation"] == "PROBE" and row["event"] == "ADMISSION" and row["disposition"] == "ADMITTED":
            self.admissions[row["event_id"]] = self._key(row)
        elif row["operation"] == "PROBE" and row["event"] == "EXECUTION":
            admission = row["refs"]["admission_event_id"]
            self.consumed.add(admission)
            self.joins[row["event_id"]] = admission
        self.run = self.run or dict(row["run"])
        self.head, self.count = row["event_hash"], self.count + 1

    def check_seal(self, row: Mapping[str, Any]) -> None:
        try:
            _check_seal_shape(row)
        except ProvenanceError as exc:
            raise JournalFault("SCHEMA_INVALID", str(exc)) from None
        if row["event_hash"] != _hashed(row):
            raise JournalFault("HASH_MISMATCH", "the seal's hash does not match its content")
        if self.run is not None and row["run"] != self.run:
            raise JournalFault("RUN_MISMATCH", f"seal of run {row['run']} on a journal of run {self.run}")
        if (row["previous_event_hash"], row["head_hash"], row["event_count"]) != (self.head, self.head, self.count):
            raise JournalFault("SEAL_MISMATCH", "the seal does not match the rows it seals")


# ---- the writer -------------------------------------------------------------------------------------------------

@dataclass
class ProvenanceJournal:
    """Append-only writer. One ``open(..., "ab")`` and one line per row; no fsync; never raises on write."""

    path: Path
    run: dict[str, Any]
    seq: int = 0
    head: str = GENESIS
    sealed: bool = False
    failed: str = ""
    warned: bool = False
    g3_cursor: int = 0  # how far the game-long G3 selection-event list has been drained
    on_failure: Callable[[str], None] | None = field(default=None, repr=False)
    chain: _Chain = field(default_factory=_Chain, repr=False)

    @classmethod
    def open(cls, path: str | Path, *, run_stem: str, game_id: str) -> "ProvenanceJournal":
        """A new journal, or the continuation of an OPEN one by the run that began it. A sealed or corrupt journal,
        or an OPEN journal of another run, fails at once: it is never extended and never sealed by this caller.
        An OPEN journal with no events has no identity yet and may be continued by the requested run."""
        journal = cls(Path(path), {"run_stem": str(run_stem), "game_id": str(game_id)})
        if journal.path.exists() and journal.path.stat().st_size:
            existing, chain = _read(journal.path)
            if existing.status != "OPEN":  # a sealed or corrupt journal is never extended
                journal._fail(f"existing journal is {existing.status}; refusing to extend it")
            elif existing.rows and chain.run != journal.run:
                journal._fail(f"existing journal belongs to run {chain.run}, not {journal.run}; refusing to extend it")
            elif existing.rows:
                journal.chain = chain
                journal.seq = int(existing.rows[-1]["seq"])
                journal.head = str(existing.rows[-1]["event_hash"])
        return journal

    def append(self, content: Mapping[str, Any]) -> dict[str, Any] | None:
        """Chain and write one event; the stored row, or None once the journal has failed or been sealed."""
        if self.failed or self.sealed:
            return None
        try:
            seq = self.seq + 1
            body = {key: normalized(content.get(key)) for key in BODY_KEYS}
            run = normalized(self.run)
            row = {"schema": SCHEMA, "record": "EVENT", "seq": seq, "run": run, **body,
                   "event_id": event_id(run, seq, body), "previous_event_hash": self.head}
            row["event_hash"] = _hashed(row)
            self.chain.check_event(row, hashes=False)  # never write a row the reader would reject
            self._write(row)
        except Exception as exc:  # noqa: BLE001 - provenance never costs the game an action
            self._fail(f"{type(exc).__name__}: {exc}")
            return None
        self.chain.accept(row)
        self.seq, self.head = seq, row["event_hash"]
        return row

    def seal(self) -> bool:
        if self.failed or self.sealed:
            return False
        try:
            row = _seal_row(self.seq + 1, self.run, self.head, self.seq, self.head)
            self.chain.check_seal(row)  # the full seal validator, before anything is written
            self._write(row)
        except Exception as exc:  # noqa: BLE001
            self._fail(f"{type(exc).__name__}: {exc}")
            return False
        self.sealed = True
        return True

    def _write(self, row: Mapping[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("ab") as handle:
            handle.write(_dumps(row) + b"\n")

    def _fail(self, detail: str) -> None:
        if self.failed:
            return
        self.failed = detail
        if self.on_failure is not None:
            try:
                self.on_failure(detail)
                self.warned = True
            except Exception:  # noqa: BLE001 - a failing hook is itself never raised
                pass


# ---- the reader -------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class JournalRead:
    rows: list[dict[str, Any]]
    status: str
    failure: dict[str, Any] | None = None
    seal: dict[str, Any] | None = None
    joins: dict[str, str] = field(default_factory=dict)  # execution event_id -> the admission event_id it consumed
    run: dict[str, Any] | None = None  # the journal's run identity: from its events, or (empty) from its seal


def _sequence_fault(seq: int, expected: int, later: Sequence[bytes]) -> str:
    """A repeated row, a row that arrives early (the expected one follows later), or a missing row."""
    if seq < expected:
        return "DUPLICATE_SEQUENCE" if seq == expected - 1 else "SEQUENCE_REORDERED"
    for raw in later:
        try:
            if json.loads(raw).get("seq") == expected:
                return "SEQUENCE_REORDERED"
        except (ValueError, AttributeError):
            break
    return "SEQUENCE_GAP"


def _parse(raw: bytes, last: bool, ended: bool) -> dict[str, Any]:
    try:
        row = json.loads(raw, parse_constant=_reject_constant)
        if not isinstance(row, dict):
            raise ValueError("not an object")
    except ValueError as exc:
        raise JournalFault("TRUNCATED_TAIL" if last and not ended else "MALFORMED_ROW", str(exc)) from None
    if last and not ended:
        raise JournalFault("TRUNCATED_TAIL", "the final row has no line terminator")
    return row


def _verify_lines(lines: list[bytes], ended_with_newline: bool) -> tuple[JournalRead, _Chain]:
    rows: list[dict[str, Any]] = []
    chain = _Chain()
    for number, raw in enumerate(lines, start=1):
        last = number == len(lines)
        try:
            row = _parse(raw, last, ended_with_newline)
            seq, expected = row.get("seq"), len(rows) + 1
            if isinstance(seq, int) and not isinstance(seq, bool) and seq != expected:
                raise JournalFault(_sequence_fault(seq, expected, lines[number:]),
                                   f"sequence {seq} where {expected} was expected")
            if row.get("record") == "SEAL":
                chain.check_seal(row)
                if not last:
                    raise JournalFault("ROWS_AFTER_SEAL", "rows follow the seal")
                return JournalRead(rows, "SEALED", None, row, dict(chain.joins), chain.run or dict(row["run"])), chain
            chain.check_event(row)
        except JournalFault as fault:
            line = number + 1 if fault.code == "ROWS_AFTER_SEAL" else number
            failure = {"code": fault.code, "line": line, "detail": fault.detail}
            return JournalRead(rows, "CORRUPT", failure, None, dict(chain.joins), chain.run), chain
        chain.accept(row)
        rows.append(row)
    return JournalRead(rows, "OPEN", None, None, dict(chain.joins), chain.run), chain


def _read(path: Path) -> tuple[JournalRead, _Chain]:
    data = path.read_bytes() if path.exists() else b""
    if not data:
        return JournalRead([], "OPEN"), _Chain()
    lines = data.split(b"\n")
    ended = lines[-1] == b""
    if ended:
        lines = lines[:-1]
    return _verify_lines(lines, ended)


def read_journal(path: str | Path) -> JournalRead:
    """The verified prefix and its status: SEALED, OPEN (no seal) or CORRUPT (a typed failure)."""
    return _read(Path(path))[0]


def validate_rows(rows: Sequence[Mapping[str, Any]]) -> None:
    """Raise unless ``rows`` are a valid, complete chain from the first sequence number."""
    read, _chain = _verify_lines([canonical(row) for row in rows], True)
    _require(read.status != "CORRUPT", f"journal invalid: {read.failure}")


# ---- translation and authorship ---------------------------------------------------------------------------------

def translate_g3_event(event: Mapping[str, Any], gate_id: str) -> dict[str, Any]:
    """One G3 selection event as an audit row's content; the original event is kept in refs.source_event."""
    kind = str(event.get("event") or "")
    _require(kind in G3_TRANSLATION, f"unknown G3 selection event {kind!r}")
    audit_event, disposition = G3_TRANSLATION[kind]
    actor = str(event.get("actor") or "DUCK")
    executor = "DUCK" if kind == "COVERAGE_RESUMED" else actor
    question = event.get("question_id")
    reasoned = disposition in REASONED or audit_event == "OPPORTUNITY"
    return {
        "level": event.get("level"), "life": event.get("life"), "gate_id": gate_id,
        "at_transition": event.get("at_transition"), "executor": executor, "operation": "G3_SELECTION",
        "event": audit_event, "disposition": disposition,
        "submitted": {"question_id": question} if kind in {"ADMITTED", "REFUSED"} else None,
        "effective": None, "field_sources": None,
        "refs": make_refs(question_id=question, subject=event.get("entity_id"),
                          source_event={"event": kind, "actor": actor, "phase": event.get("phase"),
                                        "gate_revision": event.get("gate_revision")}),
        "reason": {"code": "G3_EVENT", "text": str(event.get("reason") or kind)} if reasoned else None,
    }


def _present(payload: Any, dotted: str) -> tuple[bool, Any]:
    node = payload
    for part in dotted.split("."):
        if not isinstance(node, Mapping) or part not in node:
            return False, None
        node = node[part]
    return True, node


def field_sources(submitted: Any, effective: Any, certified: Sequence[str], *, admitted: bool,
                  marker: str) -> dict[str, str]:
    """Who supplied each field of an answer (D4): the submitter, the controller's fill, or the submitter's value
    that the gate checked against the certified one."""
    sources: dict[str, str] = {}
    if isinstance(effective, Mapping):
        for key in effective:
            sources[str(key)] = "SUBMITTER"
    for dotted in certified:
        in_effective, _value = _present(effective, dotted)
        if not in_effective:
            continue
        wrote, value = _present(submitted, dotted)
        if not wrote or value is None or value == marker:
            sources[dotted] = "CONTROLLER_FILLED"
        else:
            sources[dotted] = "SUBMITTER_CONFIRMED_BY_CONTROLLER" if admitted else "SUBMITTER"
        head = dotted.split(".")[0]
        if "." in dotted and not _present(submitted, head)[0]:
            sources[head] = "CONTROLLER_FILLED"
    return dict(sorted(sources.items()))


__all__ = [
    "EXECUTORS", "FAILURES", "G3_TRANSLATION", "JOIN_FIELDS", "JournalFault", "JournalRead", "ProvenanceError",
    "ProvenanceJournal", "REASON_CODES", "REF_KEYS", "SCHEMA", "STATUSES", "VALID", "canonical", "check_content",
    "event_id", "field_sources", "make_refs", "normalized", "read_journal", "translate_g3_event", "validate_rows",
]
