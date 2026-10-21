"""WO-PE-02 revisions 2-3: the census-time provenance adapter — each active gate product's origin and certifying answer.

Author: Claude (Alpha build seat), 2026-10-15. Rulings: Sol, ``REVIEW_WO_PE_02_SCHEMA_V4_PROVENANCE_v1`` §2 and ``_v2``
§3 and §5 (revision 3: a record-derived G4-B answer is reconstructed in full from its record; the G1 law and the G2
model and mask must equal the gate's retained state).

It reads gate state; it never calls a gate method and changes no gate behaviour. Every product type the gates emit is
enumerated, and each resolves to exactly one origin:

* ``ANSWER_CERTIFIED`` — the accepted answer the product was built from, established soundly: the payload is or
  embeds the answer, or (G1, G2, G4-C) the gate retains the certifying answer and the product provably derives from it
  (the EgoLaw is the retained law, whose id is the hash of the answer id; the counter model and mask are the retained
  ones, and the model copies the answer's fields and candidate; the law set's ``law_test`` is the retained certified
  prediction; a record-derived relation answer is exactly what its record reconstructs to, under a content-addressed
  id).
* ``GATE_DERIVED`` — only the declared closures below, each stated by the product's own payload, where no answer is
  expected: a counter search with no counter observed; a law, relation or orbit study closed by a level boundary or,
  for law and relations, unresolved when Duck's budget was spent; and (WO-RUNTIME-01, ruling B) a G1, G2, G3, G4.1 or
  G4.2 product closed CLOSED_UNRESOLVED with no answer (``UNRESOLVED_BASES``: its payload states ``status: UNRESOLVED``
  and its ``unresolved_reason``; a G4.1 or G4.2 close that kept answers is still certified by them).
* ``UNATTRIBUTED`` — everything else, with the reason. It always blocks COMPLETE.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from typing import Any, Callable, Mapping

from inference.framework import answer_shapes as shapes

CERTIFIED, DERIVED, UNATTRIBUTED = "ANSWER_CERTIFIED", "GATE_DERIVED", "UNATTRIBUTED"
ORIGINS = (CERTIFIED, DERIVED, UNATTRIBUTED)
LINKS = ("PAYLOAD_ANSWER", "PAYLOAD_ANSWERS", "PRODUCT_ID", "GATE_STATE", "NONE")
CERTIFIED_BASES = frozenset({"PRODUCT_IS_ANSWER", "PAYLOAD_ANSWER", "PAYLOAD_ANSWERS", "EGO_LAW_DERIVED_FROM_ANSWER",
                             "COUNTER_MODEL_COPIES_ANSWER", "LAW_TEST_IS_CERTIFIED_PREDICTION",
                             "RELATIONS_CERTIFIED_FROM_RECORD"})
GATE_DERIVED_BASES = {  # basis -> the one product type whose payload may state it
    "COUNTER_NOT_OBSERVED": "CounterGateProduct",
    "LAW_CLOSED_BY_LEVEL_BOUNDARY": "LeverReactionLawSet", "LAW_UNRESOLVED": "LeverReactionLawSet",
    "RELATIONS_CLOSED_BY_LEVEL_BOUNDARY": "LeverRelationSet", "RELATIONS_UNRESOLVED": "LeverRelationSet",
    "ORBITS_CLOSED_BY_LEVEL_BOUNDARY": "LeverOrbitSet"}
UNRESOLVED_BASES = {"EgoLaw": "EGO_UNRESOLVED", "CounterGateProduct": "COUNTER_UNRESOLVED",  # WO-RUNTIME-01
                    "LeverInventory": "INVENTORY_UNRESOLVED", "LeverEffectAnatomySet": "ANATOMY_UNRESOLVED",
                    "LeverOrbitSet": "ORBITS_UNRESOLVED"}
GATE_DERIVED_BASES.update({basis: product_type for product_type, basis in UNRESOLVED_BASES.items()})
UNATTRIBUTED_BASES = frozenset({"NO_RETAINED_ANSWER", "ANSWER_DOES_NOT_DERIVE_PRODUCT", "NO_DECLARED_CLOSURE",
                                "UNREGISTERED_PRODUCT_TYPE", "UNREGISTERED_ANSWER_SHAPE", "ANSWER_SHAPE_MISMATCH",
                                "NON_JSON_ANSWER_FIELD", "PRODUCT_DIFFERS_FROM_RETAINED_STATE"})
ID_DERIVED_BASES = frozenset({"EGO_LAW_DERIVED_FROM_ANSWER"})  # product identity independently derived from the id
LAW_GATE_ID = "G4-C-LEVER-LAW"
RECORD_KIND = "LEVER_RELATIONS_FROM_RECORD"
RECORD_FALSIFIER = "A later press whose recorded effect differs from the effects cited for its lever."
COUNTER_MODEL_FIELDS = ("candidate_id", "tracked_variable", "mechanism", "bookkeeping_reason", "conditions",
                        "evidence_refs", "competing_models", "falsifier", "limitations", "trigger")
_BASIS_FOR_ERROR = {"UNREGISTERED_ANSWER_SHAPE": "UNREGISTERED_ANSWER_SHAPE",
                    "ANSWER_SHAPE_MISMATCH": "ANSWER_SHAPE_MISMATCH", "NON_JSON_VALUE": "NON_JSON_ANSWER_FIELD"}

Origin = tuple[str, str, str, list]  # (origin, basis, link, accepted answer records)


def _plain(answer: Any) -> Any:
    return asdict(answer) if is_dataclass(answer) and not isinstance(answer, type) else answer


def _same(left: Any, right: Any) -> bool:
    return shapes.canonical_json(left) == shapes.canonical_json(right)


def _unattributed(basis: str) -> Origin:
    return UNATTRIBUTED, basis, "NONE", []


def ego_law_id(answer_id: str) -> str:
    """ego_verification: an EgoLaw's id is derived from the id of the answer that certified it."""
    return "EL-" + hashlib.sha256(f"G1-EGO|{answer_id}".encode()).hexdigest()[:16]


def _action_surface(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    if payload.get("answer_id") is not None and payload.get("answer_id") == product.product_id:
        return CERTIFIED, "PRODUCT_IS_ANSWER", "PRODUCT_ID", [dict(payload)]
    return _unattributed("ANSWER_DOES_NOT_DERIVE_PRODUCT")


def _ego_law(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    answer = _plain(getattr(machine.ego, "answer", None))
    if not isinstance(answer, Mapping):
        return _unattributed("NO_RETAINED_ANSWER")
    if not _same(payload, _plain(getattr(machine.ego, "ego_law", None))):
        return _unattributed("PRODUCT_DIFFERS_FROM_RETAINED_STATE")
    law_id = ego_law_id(str(answer.get("answer_id")))
    if product.product_id != law_id or payload.get("law_id") != law_id:
        return _unattributed("ANSWER_DOES_NOT_DERIVE_PRODUCT")
    return CERTIFIED, "EGO_LAW_DERIVED_FROM_ANSWER", "GATE_STATE", [answer]


def _counter(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    kind, model = payload.get("product_kind"), payload.get("counter_model")
    if kind == "COUNTER_NOT_OBSERVED" and model is None and isinstance(payload.get("search_disposition"), Mapping) \
            and payload["search_disposition"]:
        return DERIVED, "COUNTER_NOT_OBSERVED", "NONE", []
    if kind != "COUNTER_MODEL_AND_MASK" or not isinstance(model, Mapping):
        return _unattributed("NO_DECLARED_CLOSURE")
    answer = _plain(getattr(machine.counter, "answer", None))
    if not isinstance(answer, Mapping):
        return _unattributed("NO_RETAINED_ANSWER")
    mask = _plain(getattr(machine.counter, "mask_law", None))
    if mask is None or not _same(model, _plain(getattr(machine.counter, "counter_model", None))) \
            or not _same(payload.get("mask_law"), mask):
        return _unattributed("PRODUCT_DIFFERS_FROM_RETAINED_STATE")
    if not all(field in model and field in answer and _same(model[field], answer[field])
               for field in COUNTER_MODEL_FIELDS):
        return _unattributed("ANSWER_DOES_NOT_DERIVE_PRODUCT")
    return CERTIFIED, "COUNTER_MODEL_COPIES_ANSWER", "GATE_STATE", [answer]


def _inventory(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    answer = payload.get("answer")
    if not isinstance(answer, Mapping):
        return _unattributed("NO_RETAINED_ANSWER")
    if answer.get("answer_id") != product.product_id:
        return _unattributed("ANSWER_DOES_NOT_DERIVE_PRODUCT")
    return CERTIFIED, "PAYLOAD_ANSWER", "PAYLOAD_ANSWER", [answer]


def _answers(payload: Mapping[str, Any]) -> list | None:
    answers = payload.get("answers")
    if isinstance(answers, list) and answers and all(isinstance(item, Mapping) for item in answers):
        return list(answers)
    return None


def _anatomy(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    answers = _answers(payload)
    return (CERTIFIED, "PAYLOAD_ANSWERS", "PAYLOAD_ANSWERS", answers) if answers else _unattributed("NO_RETAINED_ANSWER")


def _orbits(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    answers = _answers(payload)
    if answers:
        return CERTIFIED, "PAYLOAD_ANSWERS", "PAYLOAD_ANSWERS", answers
    if payload.get("phase1_status") == "CLOSED_BY_LEVEL_BOUNDARY" and payload.get("level_boundary"):
        return DERIVED, "ORBITS_CLOSED_BY_LEVEL_BOUNDARY", "NONE", []
    return _unattributed("NO_DECLARED_CLOSURE")


def _closure(payload: Mapping[str, Any], held: str, prefix: str) -> Origin:
    """A G4-B or G4-C product with no answer: allowed only when its payload states a boundary or unresolved close."""
    if payload.get(held) is not None:
        return _unattributed("NO_DECLARED_CLOSURE")
    if payload.get("status") == "CLOSED_BY_LEVEL_BOUNDARY" and payload.get("level_boundary"):
        return DERIVED, f"{prefix}_CLOSED_BY_LEVEL_BOUNDARY", "NONE", []
    if payload.get("status") == "UNRESOLVED" and payload.get("unresolved_reason"):
        return DERIVED, f"{prefix}_UNRESOLVED", "NONE", []
    return _unattributed("NO_DECLARED_CLOSURE")


def record_answer_id(record: Mapping[str, Any]) -> str:
    """record_relations: a record answer's id is the hash of its relations' levers, claims and transitions and its
    description (transitions, not evidence ids, so the same record replayed is the same answer)."""
    seed = json.dumps({"relations": [{key: item[key] for key in ("levers", "claim", "transitions")}
                                     for item in record["relations"]],
                       "description": record["description"]}, sort_keys=True)
    return "G4B-REC-" + hashlib.sha256(seed.encode()).hexdigest()[:16]


def record_relations_answer(record: Mapping[str, Any]) -> dict[str, Any]:
    """g4b_gate._certify_from_record's fixed transformation of the record into the accepted RelationsAnswer."""
    return {"answer_id": record["answer_id"], "answer_kind": RECORD_KIND, "description": record["description"],
            "relations": list(record["relations"]), "open_conditions": [], "competing_models": [],
            "falsifier": RECORD_FALSIFIER, "limitations": [record["epistemic_limit"]]}


def _derives_from_record(record: Any, answer: Mapping[str, Any]) -> bool:
    """The whole accepted answer is what the record reconstructs to, and the record's id is its content hash."""
    try:
        return isinstance(record, Mapping) and record.get("answer_kind") == RECORD_KIND \
            and record["answer_id"] == record_answer_id(record) and _same(record_relations_answer(record), answer)
    except (KeyError, TypeError, AttributeError):
        return False


def _relations(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    answer = payload.get("answer")
    if payload.get("status") != "COMPLETE" or not isinstance(answer, Mapping):
        return _closure(payload, "answer", "RELATIONS")
    if str(answer.get("answer_kind")) == RECORD_KIND:
        if not _derives_from_record(payload.get("from_record"), answer):
            return _unattributed("ANSWER_DOES_NOT_DERIVE_PRODUCT")
        return CERTIFIED, "RELATIONS_CERTIFIED_FROM_RECORD", "PAYLOAD_ANSWER", [answer]
    return CERTIFIED, "PAYLOAD_ANSWER", "PAYLOAD_ANSWER", [answer]


def _law(machine: Any, product: Any, payload: Mapping[str, Any]) -> Origin:
    law_test = payload.get("law_test")
    if payload.get("status") != "COMPLETE" or not isinstance(law_test, Mapping):
        return _closure(payload, "law_test", "LAW")
    retained = _plain(getattr((getattr(machine, "_adapters", None) or {}).get(LAW_GATE_ID), "_certified", None))
    if not isinstance(retained, Mapping):
        return _unattributed("NO_RETAINED_ANSWER")
    if not _same(retained, law_test):
        return _unattributed("ANSWER_DOES_NOT_DERIVE_PRODUCT")
    return CERTIFIED, "LAW_TEST_IS_CERTIFIED_PREDICTION", "PAYLOAD_ANSWER", [law_test]


ADAPTERS: dict[str, Callable[[Any, Any, Mapping[str, Any]], Origin]] = {
    "ActionSurface": _action_surface, "EgoLaw": _ego_law, "CounterGateProduct": _counter,
    "LeverInventory": _inventory, "LeverEffectAnatomySet": _anatomy, "LeverOrbitSet": _orbits,
    "LeverRelationSet": _relations, "LeverReactionLawSet": _law,
}


def certifying_answers(machine: Any, product: Any) -> Origin:
    """(origin, basis, link, accepted answer records) for one active product."""
    adapter = ADAPTERS.get(product.product_type)
    if adapter is None:
        return _unattributed("UNREGISTERED_PRODUCT_TYPE")
    payload = product.payload if isinstance(product.payload, Mapping) else {}
    if product.product_type in UNRESOLVED_BASES and payload.get("status") == "UNRESOLVED" \
            and payload.get("unresolved_reason") and not payload.get("answers") and payload.get("answer") is None:
        return DERIVED, UNRESOLVED_BASES[product.product_type], "NONE", []
    try:
        return adapter(machine, product, payload)
    except shapes.AnswerProjectionError as exc:
        return _unattributed(_BASIS_FOR_ERROR[exc.code])


def entry(machine: Any, gate_id: str, product: Any) -> dict[str, Any]:
    """The stored product_answers entry: origin, basis, link and one shaped reference per certifying answer."""
    origin, basis, link, records = certifying_answers(machine, product)
    references = []
    if origin == CERTIFIED:
        try:
            references = [shapes.reference(gate_id, record) for record in records]
        except shapes.AnswerProjectionError as exc:
            origin, basis, link, _none = _unattributed(_BASIS_FOR_ERROR[exc.code])
            references = []
    return {"gate_id": gate_id, "product_type": product.product_type, "origin": origin, "basis": basis,
            "link": link, "answers": references}


def entry_problem(stored: Any) -> str | None:
    """Why a stored entry breaks the origin contract (None: it keeps it). The chapter validator uses this, so a
    certified product relabelled GATE_DERIVED, or a reference with a weakened clause, fails validation."""
    keys = {"gate_id", "product_type", "origin", "basis", "link", "answers"}
    if not isinstance(stored, Mapping) or set(stored) != keys or stored["origin"] not in ORIGINS \
            or stored["link"] not in LINKS or not isinstance(stored["answers"], list):
        return "the entry names its origin, basis, link and answers"
    origin, basis, answers = stored["origin"], stored["basis"], stored["answers"]
    if origin == CERTIFIED and (basis not in CERTIFIED_BASES or not answers):
        return "an ANSWER_CERTIFIED product names a certified basis and at least one answer"
    if origin == DERIVED and (GATE_DERIVED_BASES.get(basis) != stored["product_type"] or answers):
        return "GATE_DERIVED only for a declared closure of its own product type, with no answer"
    if origin == UNATTRIBUTED and (basis not in UNATTRIBUTED_BASES or answers):
        return "an UNATTRIBUTED product names why, with no answer"
    return next((problem for problem in (shapes.check_reference(ref) if isinstance(ref, Mapping)
                                         else "malformed reference" for ref in answers) if problem), None)


__all__ = ["ADAPTERS", "CERTIFIED_BASES", "GATE_DERIVED_BASES", "ORIGINS", "UNATTRIBUTED_BASES", "UNRESOLVED_BASES",
           "certifying_answers", "ego_law_id", "entry", "entry_problem", "record_answer_id", "record_relations_answer"]
