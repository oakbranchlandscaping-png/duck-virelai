"""WO-G4-DOSSIER-A: the pure projections from gate-payload-shaped content to lever-dossier chapter facts.

Author: Claude (Alpha build seat), 2026-10-16. Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2`` §5.

One projection per chapter, shared by the compiler (``lever_dossiers``) and the validator (``lever_dossier_schema``).
Every input is already plain JSON (``plain``): a stored product payload from ``product_content``, or the same shape
built from a gate's retained objects (``anatomy_payload``, a run's orbit snapshot, ``asdict`` of a prediction or an
answer). The same projection of the same content therefore gives the same facts, which is how the validator refuses
a dossier that disagrees with its certifying product.

Duck's prose never becomes a fact (Sol's ruling R4): an answer's explanation, competing models, falsifier and
limitations, a relation's claim and a prediction's ``because`` are kept only as strict sha16 references.

Revision 2 (2026-10-17, Sol's directive): a relation set names its submission source and the gate as its certifier,
never Duck as certifier (blocker 2; the frozen G4-B payload is not changed); an anatomy channel's event links and
affected subject are added from the level's description (``lever_dossier_links``); the derived chapter lists every
typed PROVENANCE_INCOMPLETE item (``lever_dossier_provenance``), and the affected-subject identity is unavailable
only where a channel stays an unresolved region.
"""
from __future__ import annotations

import json
from typing import Any, Iterable, Mapping, Sequence

from inference.framework import strict_json
from inference.framework.descriptive_events import cell_runs

CHAPTERS = ("identity", "anatomy", "orbit", "limits", "relations", "law_tests", "open_items")
GATES = {"anatomy": "G4-REACTIONS", "orbit": "G4.2-LEVER-ORBITS", "limits": "G4.2-LEVER-ORBITS",
         "relations": "G4-B-LEVER-RELATIONS", "law_tests": "G4-C-LEVER-LAW"}
PRODUCT_TYPES = {"anatomy": "LeverEffectAnatomySet", "orbit": "LeverOrbitSet", "limits": "LeverOrbitSet",
                 "relations": "LeverRelationSet", "law_tests": "LeverReactionLawSet"}
# Sol's origin matrix: (origin, basis) pairs that may complete a chapter, and the gate-derived closures that close it.
MAY_COMPLETE = {
    "anatomy": {("ANSWER_CERTIFIED", "PAYLOAD_ANSWERS")},
    "orbit": {("ANSWER_CERTIFIED", "PAYLOAD_ANSWERS")},
    "relations": {("ANSWER_CERTIFIED", "PAYLOAD_ANSWER"), ("ANSWER_CERTIFIED", "RELATIONS_CERTIFIED_FROM_RECORD")},
    "law_tests": {("ANSWER_CERTIFIED", "LAW_TEST_IS_CERTIFIED_PREDICTION")},
}
CLOSES = {
    "relations": {("GATE_DERIVED", "RELATIONS_UNRESOLVED"), ("GATE_DERIVED", "RELATIONS_CLOSED_BY_LEVEL_BOUNDARY")},
    "law_tests": {("GATE_DERIVED", "LAW_UNRESOLVED"), ("GATE_DERIVED", "LAW_CLOSED_BY_LEVEL_BOUNDARY")},
}
CLOSING_BASIS = {"UNRESOLVED": "PRODUCT_UNRESOLVED", "CLOSED_BY_LEVEL_BOUNDARY": "PRODUCT_CLOSED_BY_LEVEL_BOUNDARY"}
PROSE = {
    "G4-REACTIONS": ("mechanism_explanation", "competing_models", "falsifier", "limitations"),
    "G4.2-LEVER-ORBITS": ("mechanism_explanation", "competing_models", "falsifier", "limitations"),
    "G4-B-LEVER-RELATIONS": ("description", "competing_models", "falsifier", "limitations"),
}
ENDPOINTS = ("NULL_AT_OBSERVED_STATE", "OBSERVED_STATE_RECURRENCE")
PREDICTION_KINDS = {"LEVER_PREDICTION": "RELATION_TEST", "LAW_PREDICTION": "LAW_TEST"}
PROBE_OWED = ("LIMITS_PERSISTENCE", "LIMITS_REVERSAL", "ORBIT_PHASE_NOW")
UNAVAILABLE = ("AFFECTED_SUBJECT_IDENTITY", "CROSS_LEVEL_LIMITS")
PROVENANCE_PENDING = "PROVENANCE_NOT_FINAL"
EVIDENCE_KEYS = ("evidence_ref", "witness_evidence_ref", "confirmation_evidence_ref")
FACT_KEYS = {
    "identity": {"entity_id", "witnesses", "lifecycle", "appearance", "activation", "actor", "reachability",
                 "repeat_reading", "inventory_status"},
    "anatomy": {"anatomy_id", "attribution_id", "mask_law_version_id", "witness_evidence_ref",
                "confirmation_evidence_ref", "record_ref", "intervention", "residue", "coverage_complete", "channels",
                "gate_open_questions", "gate_limitations"},
    "orbit": {"run", "lever_class", "typing", "period", "recurrence_to_state_index", "life_restudies", "interruption"},
    "limits": {"endpoint", "saturated", "mechanism", "tested_states", "boundary_interruptions", "persistence",
               "reversal", "cross_level", "evidence_refs"},
    "relations": {"pressed", "submission", "description", "relations", "tests", "missing_conditions", "couplings"},
    "law_tests": {"tests", "law_status", "certified_test", "member"},
    "open_items": {"incomplete_chapters", "contradictions", "rejected_models", "probe_owed", "unavailable", "next_test",
                   "provenance_incomplete"},
}


def plain(value: Any) -> Any:
    """Strict-JSON plain form: tuples become lists, and a non-JSON value is refused rather than stringified."""
    return json.loads(strict_json.canonical_json(value))


def evidence_ids(value: Any, out: set[str] | None = None) -> set[str]:
    """Every evidence id a fact or history row cites: the values under evidence keys and ``evidence_refs`` lists."""
    out = set() if out is None else out
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in EVIDENCE_KEYS and isinstance(item, str):
                out.add(item)
            elif key == "evidence_refs" and isinstance(item, list):
                out.update(ref for ref in item if isinstance(ref, str))
            else:
                evidence_ids(item, out)
    elif isinstance(value, list):
        for item in value:
            evidence_ids(item, out)
    return out


def intervention_key(intervention: Any) -> tuple | None:
    """What makes two interventions the same activation: the NAV procedure, or the action and its coordinates."""
    if not isinstance(intervention, Mapping):
        return None
    if str(intervention.get("kind") or "").upper() == "NAV":
        return ("NAV", intervention.get("entity_id"), intervention.get("procedure_id"))
    return (intervention.get("action"), intervention.get("row"), intervention.get("col"))


def entity_entry(rows: Iterable[Any], entity_id: str) -> Mapping[str, Any] | None:
    return next((row for row in rows or () if isinstance(row, Mapping) and row.get("entity_id") == entity_id), None)


def answer_ref(gate_id: str, answer: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(answer, Mapping):
        return None
    return {"answer_id": str(answer.get("answer_id")), "gate_id": gate_id,
            "fields": {name: strict_json.sha16(answer.get(name)) for name in PROSE[gate_id]}}


# ---- chapter projections -------------------------------------------------------------------------------------

def anatomy_facts(anatomy: Mapping[str, Any]) -> dict[str, Any]:
    channels = [{
        "channel_id": item["channel_id"], "locality": item["locality"], "transform": item["transform"],
        "changed_cell_count": int(item["changed_cell_count"]), "bbox": list(item["bbox"]),
        "cell_runs": cell_runs((int(r), int(c)) for r, c in item.get("cells") or ()),
        "integer_transitions": [list(row) for row in item.get("integer_transitions") or ()],
        "signed_integer_delta": item.get("signed_integer_delta"),
    } for item in anatomy.get("channels") or ()]  # events, event_status and subject: ``lever_dossier_links``
    return {
        "anatomy_id": anatomy["anatomy_id"], "attribution_id": anatomy.get("attribution_id"),
        "mask_law_version_id": anatomy.get("mask_law_version_id"),
        "witness_evidence_ref": anatomy.get("witness_evidence_ref"),
        "confirmation_evidence_ref": anatomy.get("confirmation_evidence_ref"),
        "record_ref": anatomy.get("dossier_answer_ref"), "intervention": anatomy.get("intervention"),
        "residue": {"total": anatomy.get("residue_cell_count"), "local": anatomy.get("local_residue_cell_count"),
                    "remote": anatomy.get("remote_residue_cell_count")},
        "coverage_complete": bool(anatomy.get("coverage_complete")), "channels": channels,
        "gate_open_questions": list(anatomy.get("open_questions") or ()),
        "gate_limitations": list(anatomy.get("limitations") or ()),
    }


def run_facts(run: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """One G4-A run: a product orbit entry, or a retained run in the same shape."""
    if run is None:
        return None
    steps = [{
        "activation_index": step.get("activation_index"), "evidence_ref": step.get("evidence_ref"),
        "transition_id": step.get("transition_id"), "disposition": step.get("disposition"),
        "world_changed": step.get("world_changed"), "changed_cell_count": step.get("changed_cell_count"),
        "cell_runs": cell_runs((int(cell[0]), int(cell[1])) for cell in step.get("changed_cells") or ()),
        "recurrence_to_state_index": step.get("recurrence_to_state_index"),
        "observed_period": step.get("observed_period"),
    } for step in run.get("steps") or ()]
    confirmation = [{key: item.get(key) for key in ("evidence_ref", "transition_id", "expected_world_address",
                                                   "after_world_address", "disposition")}
                    for item in run.get("confirmation") or ()]
    return {"run_id": run.get("run_id"), "run_status": run.get("run_status"), "intervention": run.get("intervention"),
            "mask_law_version_id": run.get("mask_law_version_id"), "stop_disposition": run.get("status"),
            "state_sequence": list(run.get("state_sequence") or ()),
            "unique_state_count": run.get("unique_state_count"), "activation_count": run.get("activation_count"),
            "steps": steps, "confirmation": confirmation}


def interruption_facts(item: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(item, Mapping):
        return None
    return {"run_id": item.get("run_id"), "evidence_ref": item.get("evidence_ref"),
            "level_transition": bool(item.get("level_transition")), "resolution": item.get("resolution")}


def orbit_facts(run: Mapping[str, Any] | None, lever_class: Any, typing: Any, restudies: int,
                interruption: Mapping[str, Any] | None) -> dict[str, Any]:
    facts = run_facts(run)
    last = facts["steps"][-1] if facts and facts["steps"] else {}
    return {"run": facts, "lever_class": lever_class, "typing": typing, "period": last.get("observed_period"),
            "recurrence_to_state_index": last.get("recurrence_to_state_index"), "life_restudies": int(restudies or 0),
            "interruption": interruption_facts(interruption)}


def has_endpoint(run: Mapping[str, Any] | None) -> bool:
    return bool(run) and run.get("stop_disposition") in ENDPOINTS


def limits_facts(run: Mapping[str, Any], typing: Mapping[str, Any] | None) -> dict[str, Any]:
    """Endpoint and saturation from the run; persistence and reversal have no live probe (R5)."""
    confirmations = run.get("confirmation") or []
    boundary = sum(1 for item in [*(run.get("steps") or ()), *confirmations]
                   if item.get("disposition") == "BOUNDARY_INTERRUPTED")
    return {
        "endpoint": {"stop_disposition": run.get("stop_disposition"),
                     "confirmation": confirmations[-1]["disposition"] if confirmations else None,
                     "confirmed": run.get("run_status") == "CONFIRMED"},
        "saturated": None if not isinstance(typing, Mapping) else typing.get("condition") == "SATURATED",
        "mechanism": None if not isinstance(typing, Mapping) else typing.get("mechanism"),
        "tested_states": run.get("unique_state_count"), "boundary_interruptions": boundary,
        "persistence": "PROBE_OWED", "reversal": "PROBE_OWED", "cross_level": "UNAVAILABLE",
        # the endpoint rests on every press of the run (its state sequence) and on the confirmation presses
        "evidence_refs": [item["evidence_ref"] for item in [*(run.get("steps") or ()), *confirmations]
                          if item.get("evidence_ref")],
    }


def involves(prediction: Mapping[str, Any], entity_id: str) -> bool:
    """Sol's R6: a prediction belongs to the lever it pressed and to every lever it named."""
    return prediction.get("acted_lever") == entity_id or entity_id in (prediction.get("named") or ())


def prediction_facts(prediction: Mapping[str, Any], entity_id: str) -> dict[str, Any]:
    observed = prediction.get("observed")
    return {
        "prediction_id": prediction.get("prediction_id"),
        "kind": PREDICTION_KINDS.get(str(prediction.get("answer_kind")), "RELATION_TEST"),
        "action": prediction.get("action"), "acted": prediction.get("acted_lever") == entity_id,
        "named": entity_id in (prediction.get("named") or ()),
        "expected": (prediction.get("expected") or {}).get(entity_id),
        "observed": None if observed is None else observed.get(entity_id),
        "elsewhere": prediction.get("elsewhere"), "observed_elsewhere": prediction.get("observed_elsewhere"),
        "status": prediction.get("status"), "missed": entity_id in (prediction.get("missed") or ()),
        "evidence_ref": prediction.get("evidence_ref"), "transition_id": prediction.get("transition_id"),
        "declared_board": {"after_transition": prediction.get("declared_at_transition")},
        "from_relations": list(prediction.get("from_relations") or ()),
        "because_sha16": strict_json.sha16(prediction.get("because")),
    }


def relation_struct(index: int, relation: Mapping[str, Any]) -> dict[str, Any]:
    """A relation's typed structure; its wording (Duck's, or the record's rendering) only as a sha16."""
    return {"index": index, "kind": relation.get("kind") or "DUCK_RELATION", "levers": list(relation.get("levers") or ()),
            "prediction_refs": list(relation.get("prediction_refs") or ()),
            "evidence_refs": list(relation.get("evidence_refs") or ()),
            "transitions": list(relation.get("transitions") or ()), "claim_sha16": strict_json.sha16(relation.get("claim"))}


def submission(answer: Mapping[str, Any] | None, from_record: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """Blocker 2: the gate certifies; a record-derived set names the record as its source; any other submitter is
    provenance's to name (pending until H2, ``lever_dossier_provenance``)."""
    if not isinstance(answer, Mapping):
        return None
    if isinstance(from_record, Mapping) and from_record.get("answer_id") == answer.get("answer_id"):
        return {"submission_source": "RECORD", "certifier": GATES["relations"],
                "certification_origin": "RELATIONS_CERTIFIED_FROM_RECORD", "status": "VERIFIED",
                "basis": "GATE_RECORD_DERIVATION", "answer_event_id": None}
    return {"submission_source": None, "certifier": GATES["relations"], "certification_origin": "ANSWER_CERTIFIED",
            "status": "PENDING", "basis": PROVENANCE_PENDING, "answer_event_id": None}


def _label_ids(label: str) -> set[str]:
    return set(str(label).strip("{}").split("="))


def _couplings(payload: Mapping[str, Any], entity_id: str) -> dict[str, Any] | None:
    record, answer = payload.get("from_record"), payload.get("answer")
    if not isinstance(record, Mapping) or not isinstance(answer, Mapping) or record.get("answer_id") != answer.get("answer_id"):
        return None
    groups = [list(group) for group in record.get("coupled_groups") or () if any(entity_id in _label_ids(x) for x in group)]
    reach = {source: list(targets) for source, targets in sorted((record.get("one_way_reach") or {}).items())
             if entity_id in _label_ids(source) or any(entity_id in _label_ids(x) for x in targets)}
    return {"coupled_groups": groups, "one_way_reach": reach}


def relations_facts(payload: Mapping[str, Any], entity_id: str) -> dict[str, Any]:
    """A G4-B product payload, or the retained gate state in the same keys, for lever ``entity_id``."""
    predictions = [item for item in payload.get("predictions") or () if isinstance(item, Mapping)]
    tests = [prediction_facts(item, entity_id) for item in predictions
             if item.get("answer_kind") == "LEVER_PREDICTION" and involves(item, entity_id)]
    pressed_actions = {strict_json.canonical_json(item.get("action")) for item in predictions
                       if item.get("acted_lever") == entity_id}
    conditions = [{"condition_id": item.get("condition_id"), "before_address": item.get("before_address"),
                   "outcomes": [{"after_address": address, "evidence_refs": list(refs)}
                                for address, refs in sorted((item.get("outcomes") or {}).items())]}
                  for item in payload.get("missing_conditions") or ()
                  if strict_json.canonical_json(item.get("action")) in pressed_actions]
    answer = payload.get("answer") if isinstance(payload.get("answer"), Mapping) else None
    relations = [] if answer is None else [relation_struct(index, item) for index, item in
                                           enumerate(answer.get("relations") or ()) if entity_id in (item.get("levers") or ())]
    return {"pressed": entity_id in (payload.get("pressed_levers") or ()),
            "submission": submission(answer, payload.get("from_record")),
            "description": None if answer is None else {"answer_id": answer.get("answer_id"),
                                                        "description_sha16": strict_json.sha16(answer.get("description"))},
            "relations": relations, "tests": tests, "missing_conditions": conditions,
            "couplings": _couplings(payload, entity_id)}


def law_facts(payload: Mapping[str, Any], entity_id: str) -> dict[str, Any]:
    tests = [prediction_facts(item, entity_id) for item in payload.get("tests") or ()
             if isinstance(item, Mapping) and involves(item, entity_id)]
    law_test = payload.get("law_test") if isinstance(payload.get("law_test"), Mapping) else {}
    return {"tests": tests, "law_status": payload.get("status"), "certified_test": law_test.get("prediction_id"),
            "member": entity_id in (payload.get("lever_entities") or ())}


# ---- what a stored product says about one lever (shared by the compiler and the validator) ---------------------

def covers(chapter: str, payload: Mapping[str, Any], entity_id: str) -> bool:
    members = entity_id in (payload.get("lever_entities") or ())
    if chapter == "anatomy":
        return members and entity_entry(payload.get("anatomies"), entity_id) is not None \
            and entity_entry(payload.get("answers"), entity_id) is not None
    if chapter == "orbit":
        return members and entity_entry(payload.get("orbits"), entity_id) is not None
    if chapter in ("relations", "law_tests"):
        return members and payload.get("status") == "COMPLETE"
    return False


def closes(chapter: str, payload: Mapping[str, Any], entity_id: str) -> bool:
    return chapter in CLOSES and entity_id in (payload.get("lever_entities") or ()) and payload.get("status") in CLOSING_BASIS


def product_body(chapter: str, payload: Mapping[str, Any], entity_id: str) -> tuple[dict[str, Any], dict | None]:
    """(facts, answer_ref) of ``chapter`` for ``entity_id`` from a stored product payload."""
    if chapter == "anatomy":
        return (anatomy_facts(entity_entry(payload["anatomies"], entity_id)),
                answer_ref(GATES[chapter], entity_entry(payload["answers"], entity_id)))
    if chapter in ("orbit", "limits"):
        run = entity_entry(payload.get("orbits"), entity_id)
        typing = (payload.get("lever_typing") or {}).get(entity_id)
        if chapter == "limits":
            return limits_facts(run_facts(run), typing), None
        facts = orbit_facts(run, (payload.get("lever_classes") or {}).get(entity_id), typing,
                            (payload.get("life_restudies") or {}).get(entity_id, 0), None)
        return facts, answer_ref(GATES[chapter], entity_entry(payload.get("answers"), entity_id))
    if chapter == "relations":
        return relations_facts(payload, entity_id), answer_ref(GATES[chapter], payload.get("answer"))
    return law_facts(payload, entity_id), None


# ---- the derived chapter ----------------------------------------------------------------------------------------

def next_test(orbit: Mapping[str, Any] | None, intervention: Any) -> dict[str, Any]:
    """The typed next falsifying experiment the stored orbit admits (never prose)."""
    run = (orbit or {}).get("run")
    chosen = run["intervention"] if run else intervention
    stop = run.get("stop_disposition") if run else None
    if stop == "NULL_AT_OBSERVED_STATE":
        return {"kind": "PRESS_AT_ENDPOINT", "intervention": chosen, "period": None,
                "expect": "NO_MASKED_CHANGE", "falsified_if": "MASKED_CHANGE"}
    if stop == "OBSERVED_STATE_RECURRENCE":
        return {"kind": "RETRACE_CYCLE", "intervention": chosen, "period": (orbit or {}).get("period"),
                "expect": "RECORDED_STATE_SEQUENCE", "falsified_if": "STATE_DIVERGES"}
    return {"kind": "REPEAT_UNTIL_STOP", "intervention": chosen, "period": None,
            "expect": "NULL_OR_RECURRENCE", "falsified_if": None}


def _runs(chapter: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    facts = chapter.get("facts") or {}
    return [run for run in [facts.get("run"), *(chapter.get("history") or ())] if isinstance(run, Mapping)
            and "run_status" in run]


LIMIT_FIELDS = (("persistence", "LIMITS_PERSISTENCE"), ("reversal", "LIMITS_REVERSAL"))


def limit_readings(observations: Mapping[str, Any] | None) -> dict[str, str] | None:
    """WO-G4-DOSSIER-B (B1): what the record-derived observations say of persistence and reversal (None: v6, or
    nothing derived, so the product's own ``PROBE_OWED`` stands)."""
    from inference.framework import lever_dossier_state as S

    persistence, reversal = S.persistence_reading(observations), S.reversal_reading(observations)
    return None if persistence is None else {"persistence": persistence, "reversal": reversal}


def limits_overlay(facts: Mapping[str, Any] | None, observations: Mapping[str, Any] | None) -> Any:
    """Limits facts with persistence and reversal read from the observations (``limit_readings``); with nothing
    derived (or derived facts failed closed) both stay ``PROBE_OWED``, the product's own reading."""
    if facts is None:
        return None
    return {**facts, **(limit_readings(observations) or {"persistence": "PROBE_OWED", "reversal": "PROBE_OWED"})}


def limits_open(observations: Mapping[str, Any] | None, v7: bool) -> list[dict[str, str]]:
    """The limits chapter's typed open items: a field is owed until the record shows it."""
    readings = limit_readings(observations) or {}
    owed = [{"kind": "PROBE_OWED", "field": field} for name, field in LIMIT_FIELDS
            if not v7 or readings.get(name) != "OBSERVED"]
    return owed + [{"kind": "UNAVAILABLE", "field": "CROSS_LEVEL_LIMITS"}]


LIMITS_OWED, LIMITS_SHOWN = "ENDPOINT_OBSERVED_PROBES_OWED", "RECORD_OBSERVED_NOT_GATE_CERTIFIED"


def limits_basis(observations: Mapping[str, Any] | None) -> str:
    """B1 revision 2 (Sol): the limits chapter's IN_PROGRESS basis. ``ENDPOINT_OBSERVED_PROBES_OWED`` while either
    field is owed; ``RECORD_OBSERVED_NOT_GATE_CERTIFIED`` once the record shows both and no limits probe remains — the
    chapter stays IN_PROGRESS (no product certifies limits), incomplete but with nothing left to probe."""
    owed = [item for item in limits_open(observations, True) if item["kind"] == "PROBE_OWED"]
    return LIMITS_OWED if owed else LIMITS_SHOWN


def open_items_facts(chapters: Mapping[str, Mapping[str, Any]], intervention: Any,
                     observations: Mapping[str, Any] | None = None, v7: bool = False) -> dict[str, Any]:
    contradictions: list[dict[str, Any]] = []
    for name in ("relations", "law_tests"):
        for test in (chapters[name].get("facts") or {}).get("tests") or ():
            if test.get("status") == "CONTRADICTED":
                contradictions.append({"kind": "PREDICTION_CONTRADICTED", "chapter": name,
                                       "prediction_id": test["prediction_id"], "evidence_ref": test.get("evidence_ref")})
    for run in _runs(chapters["orbit"]):
        if run.get("run_status") == "DIVERGED":
            confirmation = run.get("confirmation") or [{}]
            contradictions.append({"kind": "CONFIRMATION_DIVERGED", "chapter": "orbit", "run_id": run.get("run_id"),
                                   "evidence_ref": confirmation[-1].get("evidence_ref")})
    for condition in (chapters["relations"].get("facts") or {}).get("missing_conditions") or ():
        contradictions.append({"kind": "MISSING_CONDITION", "chapter": "relations",
                               "condition_id": condition["condition_id"]})
    contradictions.sort(key=lambda item: strict_json.canonical_json(item))
    channels = (chapters["anatomy"].get("facts") or {}).get("channels") or ()
    unresolved = any((channel.get("subject") or {}).get("status") != "EXACT_TRACK" for channel in channels)
    probe_owed, unavailable = list(PROBE_OWED), [field for field in UNAVAILABLE
                                                 if field != "AFFECTED_SUBJECT_IDENTITY" or unresolved]
    if v7:  # B1: owed until the record shows it; an orbit phase is named only through an exact mapping
        from inference.framework import lever_dossier_state as S

        shown = {item["field"] for item in limits_open(observations, True) if item["kind"] == "PROBE_OWED"}
        probe_owed = [field for field in PROBE_OWED if field in shown]
        unavailable += [] if S.phase_named(observations) else ["ORBIT_PHASE_NOW"]
    return {
        "incomplete_chapters": [name for name in CHAPTERS[:-1] if chapters[name]["status"] != "COMPLETE"],
        "contradictions": contradictions,
        "rejected_models": [dict(item) for item in chapters["relations"].get("history") or ()],
        "probe_owed": probe_owed,
        "unavailable": unavailable,
        "next_test": next_test(chapters["orbit"].get("facts"), intervention),
        "provenance_incomplete": [{"chapter": name, **item} for name in CHAPTERS[:-1]
                                  for item in chapters[name].get("open") or () if item.get("kind") == "PROVENANCE_INCOMPLETE"],
    }


def open_items_complete(facts: Mapping[str, Any]) -> bool:
    return not (facts["incomplete_chapters"] or facts["contradictions"] or facts["probe_owed"]
                or facts["provenance_incomplete"])


__all__ = ["CHAPTERS", "CLOSES", "CLOSING_BASIS", "ENDPOINTS", "FACT_KEYS", "GATES", "MAY_COMPLETE", "PRODUCT_TYPES",
           "PROSE", "answer_ref", "anatomy_facts", "closes", "covers", "entity_entry", "evidence_ids", "has_endpoint",
           "interruption_facts", "intervention_key", "involves", "law_facts", "limits_facts", "next_test",
           "open_items_complete", "open_items_facts", "orbit_facts", "plain", "prediction_facts", "product_body",
           "relation_struct", "relations_facts", "run_facts", "submission", "limit_readings", "limits_open",
           "limits_overlay"]
