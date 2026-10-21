"""WO-PE-01: the audit journal, an append-only, hash-chained record of every gated proposal.

Author: Claude (Alpha build seat), 2026-10-14. Interface: ``INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v3``; rulings
``RULINGS_PAPER_EVIDENCE_v1`` D1-D4 and Sol's revision-2 order. (Renamed from ``provenance.py`` at revision 2, so it
is never confused with the weave's cell-ownership provenance.)

Who proposed each gated operation, what they submitted, and whether a gate admitted, refused or executed it. One
row per decision, in one normalized vocabulary across all gates (D2):

* operation ``PROBE`` | ``ANSWER`` | ``G3_SELECTION`` | ``ANNOTATION``, and in schema v2 ``G4_SELECTION``;
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

**Schema versions** (WO-G4-DOSSIER-B, B2 revision 2; Sol: "Do not silently amend either schema"). The writer writes
``virelai-provenance-v2``: v1's vocabulary plus G4 selections (operation ``G4_SELECTION``, reason ``G4_EVENT``). v1 is
frozen (``VALID_V1``, ``REASON_CODES_V1``). Every row of a journal, its seal included, carries the journal's one
schema and is checked with that schema's vocabulary; a journal never mixes schemas. ``read_journal`` and
``verify_embedded`` read both versions; ``read_journal_v1`` and ``verify_embedded_v1`` are the frozen v1 readers, which
refuse a v2 row rather than reinterpret it. The writer continues an OPEN journal in that journal's own schema.

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

from inference.framework import audit_v3_rules as v3_rules

V1_SCHEMA = "virelai-provenance-v1"
V2_SCHEMA = "virelai-provenance-v2"  # B2 revision 2: v1 plus G4 selections (frozen since WO-RUNTIME-01)
SCHEMA = "virelai-provenance-v3"  # the writer's (WO-RUNTIME-01): v2 plus the TURN and GATE recovery rows
SCHEMAS = (V1_SCHEMA, V2_SCHEMA, SCHEMA)
V2_SCHEMAS = (V1_SCHEMA, V2_SCHEMA)  # the frozen v2 reader: a v3 row is CORRUPT, never reinterpreted
GENESIS = "0" * 64
EXECUTORS = ("DUCK", "CONTROLLER", "SYSTEM")
VALID_V1: dict[str, dict[str, frozenset[str]]] = {  # frozen: the v1 contract
    "PROBE": {"ADMISSION": frozenset({"ADMITTED", "REFUSED"}), "EXECUTION": frozenset({"EXECUTED", "NOT_ATTEMPTED"})},
    "ANSWER": {"ADMISSION": frozenset({"ADMITTED", "REFUSED"})},
    "G3_SELECTION": {"OPPORTUNITY": frozenset({"OFFERED", "NOT_ATTEMPTED"}),
                     "ADMISSION": frozenset({"ADMITTED", "REFUSED", "SUPERSEDED"}),
                     "EXECUTION": frozenset({"EXECUTED"})},
    "ANNOTATION": {"ADMISSION": frozenset({"UNCERTIFIED", "REFUSED"})},
}
VALID_V2: dict[str, dict[str, frozenset[str]]] = {  # v2: v1 unchanged, plus G4 selections (no opportunity: no handoff)
    **VALID_V1, "G4_SELECTION": {"ADMISSION": VALID_V1["G3_SELECTION"]["ADMISSION"], "EXECUTION": frozenset({"EXECUTED"})},
}
VALID: dict[str, dict[str, frozenset[str]]] = {**VALID_V2, **v3_rules.VALID}  # v3: v2 unchanged, plus TURN and GATE
REASONED = frozenset({"REFUSED", "NOT_ATTEMPTED", "SUPERSEDED"}) | v3_rules.REASONED
REASON_CODES_V1 = frozenset({"GATE_CONTRACT", "ORIENTATION_DUE", "ANNOTATION_INVALID", "ACTION_CONTRACT",
                             "TERMINAL_STATE", "NOT_EXECUTED", "EXECUTION_ERROR", "G3_EVENT"})
REASON_CODES_V2 = REASON_CODES_V1 | {"G4_EVENT"}
REASON_CODES = REASON_CODES_V2 | v3_rules.REASON_CODES
VOCABULARY = {V1_SCHEMA: (VALID_V1, REASON_CODES_V1), V2_SCHEMA: (VALID_V2, REASON_CODES_V2),
              SCHEMA: (VALID, REASON_CODES)}
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


def _check_reason(content: Mapping[str, Any], codes: frozenset[str]) -> None:
    reason, disposition = content.get("reason"), content.get("disposition")
    if reason is not None:
        _require(isinstance(reason, Mapping) and set(reason) == {"code", "text"} and reason["code"] in codes
                 and isinstance(reason["text"], str) and bool(reason["text"]), "a reason is a typed code and its text")
    if disposition in REASONED or content.get("event") == "OPPORTUNITY":
        _require(reason is not None, f"{content.get('operation')}/{disposition} needs a typed reason")


def check_content(content: Mapping[str, Any], *, schema: str = SCHEMA) -> None:
    """The audit fields of one event under ``schema``'s vocabulary: types, a valid combination, a known executor, a
    typed reason where one is owed, the references an execution owes, and the field-source map only an answer carries."""
    _require(schema in VOCABULARY, f"unknown schema {schema!r}")
    valid, codes = VOCABULARY[schema]
    operation, event, disposition = content.get("operation"), content.get("event"), content.get("disposition")
    _require(disposition in valid.get(operation, {}).get(event, ()),
             f"invalid combination {operation}/{event}/{disposition}")
    _require(content.get("executor") in EXECUTORS, f"unknown executor {content.get('executor')!r}")
    for key in ("level", "life", "at_transition"):
        _require(_optional(content.get(key), int), f"{key} must be an integer or null")
    _require(_optional(content.get("gate_id"), str), "gate_id must be text or null")
    _check_reason(content, codes)
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


def _check_schema(row: Mapping[str, Any], accepted: Sequence[str], journal: str | None) -> None:
    """The row's schema is one this reader accepts and, once a journal has one, that journal's (never mixed)."""
    _require(row["schema"] in accepted, f"unknown schema {row['schema']!r} (this reader accepts {list(accepted)})")
    _require(journal is None or row["schema"] == journal,
             f"a {row['schema']} row in a {journal} journal: a journal never mixes schemas")


def _check_event_shape(row: Mapping[str, Any], accepted: Sequence[str] = SCHEMAS, journal: str | None = None) -> None:
    _require(row.get("record") == "EVENT", f"record must be EVENT or SEAL, not {row.get('record')!r}")
    _require(set(row) == EVENT_KEYS, "event keys differ from the schema")
    _check_schema(row, accepted, journal)
    _require(_optional(row["seq"], int) and row["seq"] is not None and row["seq"] > 0,
             "seq must be a positive integer")
    _check_run(row["run"])
    _require(isinstance(row["event_id"], str) and bool(_EVENT_ID.fullmatch(row["event_id"])), "malformed event_id")
    for key in ("previous_event_hash", "event_hash"):
        _require(isinstance(row[key], str) and bool(_HASH.fullmatch(row[key])), f"malformed {key}")
    check_content(row, schema=row["schema"])


def _check_run(run: Any) -> None:
    _require(isinstance(run, Mapping) and set(run) == RUN_KEYS
             and all(isinstance(run[key], str) and run[key] for key in RUN_KEYS),
             "run must carry exactly a nonempty run_stem and game_id")


def _check_seal_shape(row: Mapping[str, Any], accepted: Sequence[str] = SCHEMAS, journal: str | None = None) -> None:
    _require(set(row) == SEAL_KEYS, "seal keys differ from the schema")
    _check_schema(row, accepted, journal)
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


def _seal_row(seq: int, run: Mapping[str, Any], previous: str, count: int, head: str,
              schema: str = SCHEMA) -> dict[str, Any]:
    """Journal control metadata (outside the D2 vocabulary): the run it closes, and the prefix it seals."""
    row = {"schema": schema, "record": "SEAL", "seq": seq, "run": normalized(run), "previous_event_hash": previous,
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
    accepted: tuple[str, ...] = SCHEMAS  # the schemas this reader admits (the frozen v1 reader: v1 only)
    schema: str | None = None  # the journal's one schema, fixed by its first row
    v3: v3_rules.V3State = field(default_factory=v3_rules.V3State)  # WO-RUNTIME-01: the recovery rules

    @staticmethod
    def _key(row: Mapping[str, Any]) -> tuple[Any, ...]:
        return (row["refs"]["probe_id"], *(json.dumps(row[name], sort_keys=True) for name in JOIN_FIELDS))

    def check_event(self, row: Mapping[str, Any], *, hashes: bool = True) -> None:
        """Raise ``JournalFault`` unless ``row`` is the valid next event of this chain."""
        try:
            _check_event_shape(row, self.accepted, self.schema)
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
        if row["schema"] == SCHEMA:
            self.v3.check(row, lambda message: _v3_fault(message))

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
        if row["schema"] == SCHEMA:
            self.v3.accept(row)
        self.run = self.run or dict(row["run"])
        self.schema = self.schema or str(row["schema"])
        self.head, self.count = row["event_hash"], self.count + 1

    def check_seal(self, row: Mapping[str, Any]) -> None:
        try:
            _check_seal_shape(row, self.accepted, self.schema)
        except ProvenanceError as exc:
            raise JournalFault("SCHEMA_INVALID", str(exc)) from None
        if row["event_hash"] != _hashed(row):
            raise JournalFault("HASH_MISMATCH", "the seal's hash does not match its content")
        if self.run is not None and row["run"] != self.run:
            raise JournalFault("RUN_MISMATCH", f"seal of run {row['run']} on a journal of run {self.run}")
        if (row["previous_event_hash"], row["head_hash"], row["event_count"]) != (self.head, self.head, self.count):
            raise JournalFault("SEAL_MISMATCH", "the seal does not match the rows it seals")
        if row["schema"] == SCHEMA:
            self.v3.check_seal(lambda message: _v3_fault(message))


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
    g4_cursor: int = 0  # the same for G4's (WO-G4-DOSSIER-B, B2)
    schema: str = SCHEMA  # the journal's schema: v2 for a new journal, its own for a continued one
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
                journal.schema = str(chain.schema)  # continued in its own schema, never relabelled
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
            row = {"schema": self.schema, "record": "EVENT", "seq": seq, "run": run, **body,
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
            row = _seal_row(self.seq + 1, self.run, self.head, self.seq, self.head, self.schema)
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


def _verify_lines(lines: list[bytes], ended_with_newline: bool,
                  accepted: Sequence[str] = SCHEMAS) -> tuple[JournalRead, _Chain]:
    rows: list[dict[str, Any]] = []
    chain = _Chain(accepted=tuple(accepted))
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


def _parse_bytes(data: bytes, accepted: Sequence[str] = SCHEMAS) -> tuple[JournalRead, _Chain]:
    if not data:
        return JournalRead([], "OPEN"), _Chain(accepted=tuple(accepted))
    lines = data.split(b"\n")
    ended = lines[-1] == b""
    if ended:
        lines = lines[:-1]
    return _verify_lines(lines, ended, accepted)


def _read(path: Path, accepted: Sequence[str] = SCHEMAS) -> tuple[JournalRead, _Chain]:
    return _parse_bytes(path.read_bytes() if path.exists() else b"", accepted)


def read_journal(path: str | Path) -> JournalRead:
    """The verified prefix and its status: SEALED, OPEN (no seal) or CORRUPT (a typed failure). Reads v1 and v2."""
    return _read(Path(path))[0]


def read_journal_bytes(data: bytes) -> JournalRead:
    """WO-PE-02: the same verdict as ``read_journal``, from bytes already read, so that a caller can hash and parse
    one buffer (no second read between the file hash and the parse)."""
    return _parse_bytes(bytes(data))[0]


def _v3_fault(message: str) -> None:
    raise JournalFault("SCHEMA_INVALID", f"audit v3: {message}")


def read_journal_v2(path: str | Path) -> JournalRead:
    """The frozen v2 reader (WO-RUNTIME-01): v1 and v2 only; a v3 row is CORRUPT (``SCHEMA_INVALID``)."""
    return _read(Path(path), V2_SCHEMAS)[0]


def read_journal_v2_bytes(data: bytes) -> JournalRead:
    return _parse_bytes(bytes(data), V2_SCHEMAS)[0]


def read_journal_v1(path: str | Path) -> JournalRead:
    """The frozen v1 reader: a v2 row is CORRUPT (``SCHEMA_INVALID``), never reinterpreted as v1."""
    return _read(Path(path), (V1_SCHEMA,))[0]


def read_journal_bytes_v1(data: bytes) -> JournalRead:
    return _parse_bytes(bytes(data), (V1_SCHEMA,))[0]


def verify_embedded(rows: Sequence[Mapping[str, Any]], seal: Mapping[str, Any] | None,
                    accepted: Sequence[str] = SCHEMAS) -> JournalRead:
    """WO-PE-02: re-verify rows (and a seal) embedded in another artifact exactly as the reader verifies a file."""
    lines = [_dumps(row) for row in rows] + ([_dumps(seal)] if seal is not None else [])
    return _verify_lines(lines, True, accepted)[0]


def verify_embedded_v1(rows: Sequence[Mapping[str, Any]], seal: Mapping[str, Any] | None) -> JournalRead:
    """The frozen v1 verification an artifact written before audit schema v2 (world model v4-v7) is held to."""
    return verify_embedded(rows, seal, (V1_SCHEMA,))


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


def translate_g4_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """One G4 selection event (``g4_selection``, B2) as an audit row: G3's translation under operation
    ``G4_SELECTION`` and the event's own gate. G4 offers no handoff turn, so it never records an opportunity.

    WO-G4-DOSSIER-B3 revision 2: a G4-B experiment's ``FINISHED`` row keeps its reason, which names the finished type
    (``TYPE: detail``) the v9 validator checks against the evidence. The row shape and the v2 vocabulary are unchanged:
    every row already carries ``reason``, ``G4_EVENT`` is a v2 code, and a reason is allowed on any disposition."""
    kind = str(event.get("event") or "")
    _require(kind in G3_TRANSLATION and G3_TRANSLATION[kind][0] != "OPPORTUNITY", f"unknown G4 selection event {kind!r}")
    row = translate_g3_event({**event, "phase": event.get("gate_id")}, str(event.get("gate_id") or ""))
    reason = row["reason"]
    if kind == "FINISHED" and event.get("gate_id") == "G4-B-LEVER-RELATIONS":  # B3 r2: a finished experiment's type
        reason = {"text": str(event.get("reason") or kind)}
    return {**row, "operation": "G4_SELECTION",
            "reason": None if reason is None else {"code": "G4_EVENT", "text": reason["text"]}}


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
    "event_id", "field_sources", "make_refs", "normalized", "read_journal", "read_journal_bytes", "translate_g3_event",
    "translate_g4_event", "read_journal_v1", "read_journal_bytes_v1", "verify_embedded_v1", "V1_SCHEMA", "SCHEMAS",
    "VALID_V1", "REASON_CODES_V1", "VOCABULARY", "V2_SCHEMA", "V2_SCHEMAS", "VALID_V2", "REASON_CODES_V2",
    "read_journal_v2", "read_journal_v2_bytes",
    "validate_rows", "verify_embedded",
]
