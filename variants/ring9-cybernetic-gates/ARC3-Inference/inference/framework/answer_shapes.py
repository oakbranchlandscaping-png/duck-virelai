"""WO-PE-02 revision 2: the accepted-answer normalizer — how each gate's accepted answer relates to what was submitted.

Author: Claude (Alpha build seat), 2026-10-15. Ruling: Sol, ``REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v1`` §3–§4.

A gate validates the submitted (effective) payload and keeps an accepted answer object. Most fields are copied; some
are renamed, wrapped, flattened or filled with a declared default; some the gate generates, derives or later writes as
an outcome. Every field of every registered answer dataclass is named below with exactly one rule, so nothing is
compared "because it happens to overlap":

* ``project(shape, record)`` turns an accepted answer into **clauses** (what the effective payload must contain) and
  an **omitted** map (each field not compared, with its disposition). A record whose fields are not exactly the
  shape's inventory is refused, so a truncated or padded record cannot pass.
* ``unmet(clauses, effective)`` is directional containment: every clause must find its field in the effective payload
  with the same strict canonical hash. A declared default may be absent from the effective payload only when the
  accepted value equals that default.
* Hashing is strict canonical JSON (no ``default=``, no NaN): a non-JSON value is an ``AnswerProjectionError``, never
  a stringified match.

Pure: no I/O and no gate import (``test_world_model_v4_provenance`` pins the inventories to the dataclasses).
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from inference.framework import strict_json

ID, GENERATED, DERIVED, OUTCOME = "ANSWER_ID", "GENERATED", "DERIVED", "OUTCOME"
NOT_COMPARED = (ID, GENERATED, DERIVED, OUTCOME)
UNCHANGED = "UNCHANGED"  # g4_relations.UNCHANGED: a lever a prediction leaves unnamed
_NONE = object()


class AnswerProjectionError(ValueError):
    """An accepted answer cannot be projected: ``code`` is UNREGISTERED_ANSWER_SHAPE, ANSWER_SHAPE_MISMATCH or
    NON_JSON_VALUE."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


def canonical_json(value: Any) -> str:
    """WO-G4-DOSSIER-A (R10): the shared strict canonicalizer; a non-string key is refused, never collapsed."""
    try:
        return strict_json.canonical_json(value)
    except strict_json.StrictJsonError as exc:
        raise AnswerProjectionError("NON_JSON_VALUE", str(exc)) from exc


def sha16(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()[:16]


def _c(*keys: str, default: Any = _NONE) -> tuple:
    return ("COPIED", keys, default)


C = ("COPIED", (), _NONE)  # copied under its own name


def _d(default: Any) -> tuple:
    return ("COPIED", (), default)


SHAPES: dict[str, dict[str, Any]] = {
    "ACTION_SURFACE_ANSWER": {"answer_id": ID, "action_metadata": C, "semantic_claims": C, "epistemic_limit": C},
    "EGO_ANSWER": {
        "answer_id": ID, "answer_kind": C, "subjects": C, "mechanism": C, "action_laws": C, "conditions": _d([]),
        "constraints": _d([]), "evidence_refs": C, "competing_models": C, "falsifier": C, "novel_prediction": _d({}),
        "limitations": _d([]), "action_law_specs": _d({})},
    "COUNTER_ANSWER": {
        "answer_id": ID, "candidate_id": C, "tracked_variable": C, "mechanism": C, "bookkeeping_reason": C,
        "conditions": _d([]), "evidence_refs": C, "competing_models": C, "falsifier": C, "limitations": _d([]),
        "novel_prediction": C, "trigger": _d("UNSPECIFIED")},
    "G3_INVENTORY_ANSWER": {
        "answer_id": ID, "answer_kind": DERIVED, "subjects": DERIVED, "mechanism": _c("explanation", "mechanism"),
        "action_laws": GENERATED, "conditions": _d([]), "constraints": _c("limitations", default=[]),
        "evidence_refs": C, "competing_models": C, "falsifier": C,
        "novel_prediction": ("FLATTENED", ("lever_entities", "clean_null_entities", "ambiguous_entities")),
        "limitations": _d([]), "action_law_specs": _d({})},
    "G3_REACHABILITY_ANSWER": {
        "answer_id": ID, "answer_kind": C, "subjects": DERIVED, "mechanism": _c("explanation"),
        "action_laws": GENERATED, "conditions": _c("reopen_conditions"), "constraints": ("SINGLETON", "epistemic_limit"),
        "evidence_refs": C, "competing_models": GENERATED, "falsifier": GENERATED, "novel_prediction": DERIVED,
        "limitations": ("SINGLETON", "epistemic_limit"), "action_law_specs": _d({})},
    "G3_DOSSIER_ANSWER": {
        "answer_id": ID, "answer_kind": C, "target_member_id": C, "explanation": _c("explanation", "mechanism"),
        "intervention": C, "effect_summary": C, "evidence_refs": C, "competing_models": C, "falsifier": C,
        "conditions": _d([]), "limitations": _d([])},
    "LEVER_REACTION_ANSWER": {
        "answer_id": ID, "answer_kind": C, "entity_id": C, "target_member_id": GENERATED, "intervention": C,
        "effect_channels": C, "mechanism_explanation": C, "evidence_refs": C, "record_refs": C, "competing_models": C,
        "falsifier": C, "limitations": C},
    "LEVER_ORBIT_ANSWER": {
        "answer_id": ID, "answer_kind": C, "entity_id": C, "intervention": C, "stop_disposition": C,
        "state_sequence": C, "recurrence_to_state_index": C, "observed_period": C, "mechanism_explanation": C,
        "evidence_refs": C, "competing_models": C, "falsifier": C, "limitations": C},
    "RELATIONS_ANSWER": {
        "answer_id": ID, "answer_kind": C, "description": C, "relations": C, "open_conditions": C,
        "competing_models": C, "falsifier": C, "limitations": C},
    "RECORD_RELATIONS_ANSWER": {  # the gate re-derives the relations from the record; the controller names the kind
        "answer_id": ID, "answer_kind": C, "description": DERIVED, "relations": DERIVED, "open_conditions": GENERATED,
        "competing_models": GENERATED, "falsifier": GENERATED, "limitations": DERIVED},
    "LEVER_PREDICTION": {
        "prediction_id": ID, "action": C, "acted_lever": DERIVED, "expected": ("EXPECTATION",), "named": DERIVED,
        "elsewhere": _d("NO_CHANGE"), "because": C, "declared_at_transition": GENERATED, "status": OUTCOME,
        "observed": OUTCOME, "observed_elsewhere": OUTCOME, "missed": OUTCOME, "evidence_ref": OUTCOME,
        "transition_id": OUTCOME, "answer_kind": C, "from_relations": _d([])},
}
GATE_SHAPES = {"G0-ACTION-METADATA": "ACTION_SURFACE_ANSWER", "G1-EGO": "EGO_ANSWER", "G2-COUNTER": "COUNTER_ANSWER",
               "G4-REACTIONS": "LEVER_REACTION_ANSWER", "G4.2-LEVER-ORBITS": "LEVER_ORBIT_ANSWER"}
KIND_SHAPES = {
    "G3-LEVERS": {"LEVER_INVENTORY": "G3_INVENTORY_ANSWER", "G3_BOUNDED_COVERAGE_REPORT": "G3_INVENTORY_ANSWER",
                  "TARGET_REACHABILITY": "G3_REACHABILITY_ANSWER", "LEVER_DOSSIER": "G3_DOSSIER_ANSWER"},
    "G4-B-LEVER-RELATIONS": {"LEVER_PREDICTION": "LEVER_PREDICTION", "LEVER_RELATIONS": "RELATIONS_ANSWER",
                             "LEVER_RELATIONS_FROM_RECORD": "RECORD_RELATIONS_ANSWER"},
    "G4-C-LEVER-LAW": {"LAW_PREDICTION": "LEVER_PREDICTION"},
}
# The gate-answer sidecar (``gate_artifacts.record_gate_answer``) adds bookkeeping and, for G1 and G2, gate state
# captured at declaration time. These are the only fields removed before the sidecar answer is projected.
SIDECAR_BOOKKEEPING = frozenset({"schema", "gate_id", "executor"})
SIDECAR_GATE_STATE = {
    "G1-EGO": frozenset({"gate_status_after_answer", "coverage_certificate", "pending_prediction", "ego_law"}),
    "G2-COUNTER": frozenset({"gate_status_after_answer", "counter_candidate", "pending_prediction"}),
}


def answer_shape(gate_id: str, record: Mapping[str, Any]) -> str | None:
    if gate_id in KIND_SHAPES:
        return KIND_SHAPES[gate_id].get(str(record.get("answer_kind") or "").strip().upper())
    return GATE_SHAPES.get(gate_id)


def id_field(shape: str) -> str:
    return next(name for name, rule in SHAPES[shape].items() if rule == ID)


def omitted_of(shape: str) -> dict[str, str]:
    return {name: rule for name, rule in sorted(SHAPES[shape].items()) if isinstance(rule, str)}


def layout(shape: str) -> dict[str, tuple[str, list[str], Any]]:
    """Clause field -> (rule, effective keys, declared default) for every compared field of a shape."""
    out: dict[str, tuple[str, list[str], Any]] = {}
    for name, rule in sorted(SHAPES[shape].items()):
        if isinstance(rule, str):
            continue
        if rule[0] == "COPIED":
            out[name] = ("COPIED", list(rule[1] or (name,)), rule[2])
        elif rule[0] == "SINGLETON":
            out[name] = ("SINGLETON", [rule[1]], _NONE)
        elif rule[0] == "FLATTENED":
            out.update({f"{name}.{sub}": ("COPIED", [sub], _NONE) for sub in rule[1]})
        else:
            out[name] = ("EXPECTATION", [name], _NONE)
    return out


def _value(record: Mapping[str, Any], field: str, shape: str) -> Any:
    if "." not in field:
        return record[field]
    outer, inner = field.split(".", 1)
    nested = record[outer]
    expected = set(SHAPES[shape][outer][1])
    if not isinstance(nested, Mapping) or set(nested) != expected:
        raise AnswerProjectionError("ANSWER_SHAPE_MISMATCH", f"{outer} must hold exactly {sorted(expected)}")
    return nested[inner]


def project(shape: str, record: Mapping[str, Any]) -> dict[str, Any]:
    """The clauses an effective payload must satisfy, and every field that is not compared, by name."""
    if shape not in SHAPES:
        raise AnswerProjectionError("UNREGISTERED_ANSWER_SHAPE", str(shape))
    if set(record) != set(SHAPES[shape]):
        raise AnswerProjectionError("ANSWER_SHAPE_MISMATCH", f"{shape}: missing {sorted(set(SHAPES[shape]) - set(record))}"
                                    f", unexpected {sorted(set(record) - set(SHAPES[shape]))}")
    clauses = []
    for field, (rule, keys, default) in layout(shape).items():
        value = _value(record, field, shape)
        absent_ok = default is not _NONE and canonical_json(value) == canonical_json(default)
        clauses.append({"field": field, "rule": rule, "keys": keys, "sha": sha16(value), "absent_ok": absent_ok,
                        "value": json.loads(canonical_json(value)) if rule == "EXPECTATION" else None})
    return {"clauses": clauses, "omitted": omitted_of(shape)}


def reference(gate_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
    """A stored answer reference: the answer id, its shape, its clauses and its omitted fields."""
    shape = answer_shape(gate_id, record)
    if shape is None:
        raise AnswerProjectionError("UNREGISTERED_ANSWER_SHAPE", f"{gate_id} {record.get('answer_kind')!r}")
    projected = project(shape, record)
    return {"answer_id": str(record[id_field(shape)]), "shape": shape, **projected}


def sidecar_answer(gate_id: str, record: Mapping[str, Any]) -> dict[str, Any]:
    removed = SIDECAR_BOOKKEEPING | SIDECAR_GATE_STATE.get(gate_id, frozenset())
    return {key: value for key, value in record.items() if key not in removed}


def _expectation_holds(accepted: Mapping[str, Any], submitted: Any) -> bool:
    """g4_relations.validate_prediction: named levers keep their stated outcome (stripped, upper-cased); every other
    lever of the accepted map is UNCHANGED."""
    if not isinstance(submitted, Mapping) or not submitted or not isinstance(accepted, Mapping):
        return False
    named = {str(key).strip(): str(value or "").strip().upper() for key, value in submitted.items()}
    return set(named) <= set(accepted) and all(accepted[key] == value for key, value in named.items()) and all(
        value == UNCHANGED for key, value in accepted.items() if key not in named)


def _holds(clause: Mapping[str, Any], value: Any) -> bool:
    try:
        if clause["rule"] == "EXPECTATION":
            return _expectation_holds(clause["value"], value)
        return sha16([value] if clause["rule"] == "SINGLETON" else value) == clause["sha"]
    except AnswerProjectionError:
        return False


def unmet(clauses: Sequence[Mapping[str, Any]], effective: Any) -> list[str]:
    """The clause fields an effective payload fails (empty: it contains the answer)."""
    if not isinstance(effective, Mapping):
        return ["<effective>"]
    failed = []
    for clause in clauses:
        keys = clause["keys"]
        key = next((k for k in keys if k in effective and (len(keys) == 1 or effective[k])), None)
        if key is None:
            if not clause["absent_ok"]:
                failed.append(clause["field"])
        elif not _holds(clause, effective[key]):
            failed.append(clause["field"])
    return failed


def semantic(clauses: Sequence[Mapping[str, Any]]) -> bool:
    """At least one clause the effective payload must actually carry."""
    return any(not clause["absent_ok"] for clause in clauses)


def check_reference(ref: Mapping[str, Any]) -> str | None:
    """Why a stored reference does not follow the shape table (None: it does). The validator uses it, so a stored
    reference with a dropped, weakened or renamed clause fails."""
    if set(ref) != {"answer_id", "shape", "clauses", "omitted"} or ref["shape"] not in SHAPES:
        return "malformed reference"
    if ref["omitted"] != omitted_of(ref["shape"]):
        return "omitted fields are not the shape's"
    expected = layout(ref["shape"])
    if [clause.get("field") for clause in ref["clauses"]] != list(expected):
        return "clauses are not the shape's"
    for clause in ref["clauses"]:
        rule, keys, default = expected[clause["field"]]
        if set(clause) != {"field", "rule", "keys", "sha", "absent_ok", "value"} or clause["rule"] != rule \
                or clause["keys"] != keys or (clause["absent_ok"] and (default is _NONE or clause["sha"] != sha16(default))) \
                or (rule == "EXPECTATION") != (clause["value"] is not None) \
                or (rule == "EXPECTATION" and sha16(clause["value"]) != clause["sha"]):
            return f"clause {clause['field']} does not follow its rule"
    return None


__all__ = ["AnswerProjectionError", "SHAPES", "SIDECAR_BOOKKEEPING", "SIDECAR_GATE_STATE", "answer_shape",
           "canonical_json", "check_reference", "id_field", "layout", "project", "reference", "semantic", "sha16",
           "sidecar_answer", "unmet"]
