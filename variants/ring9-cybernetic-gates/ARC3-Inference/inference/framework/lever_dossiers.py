"""WO-G4-DOSSIER-A: a durable, chapter-statused mechanics dossier for every certified lever (world model schema v6).

Author: Claude (Alpha build seat), 2026-10-16. Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2`` (Sol's rulings R1-R13).

A pure projection; the gate machine stays the only certifier. ``gate_view`` reads retained gate attributes only (never
``_seed``, ``assess``, ``snapshot``, ``next_probe`` or any view that builds state) and turns them into plain JSON;
``build`` combines that view with the census level (receipts, product content, product origins) into one dossier per
LEVER role. Chapters are statused independently (``lever_dossier_facts``):

* COMPLETE only through the chapter's certifying product (Sol's origin matrix); GATE_RETAINED work never completes;
* accepted per-lever work an aggregate has not yet carried is PRODUCT_PENDING; work in progress is IN_PROGRESS;
* a census label (R1): at an H1 freeze open work becomes CLOSED_UNRESOLVED/``LEVEL_ENDED``; at an H2 stop it becomes
  INTERRUPTED/<reason>; PRODUCT_PENDING keeps its basis, and ``census_context`` records why the model was persisted;
* integrity (R8): a chapter whose evidence fails resolution, whose product disagrees with retained state, or whose
  evidence lies on a transition H2 found mismatched fails closed (CLOSED_UNRESOLVED, prior status kept, facts null).

``attach`` (called by ``library_census.compile_level``) and ``finalize`` (called by ``compile_world_model``) are the
only hooks. Nothing here runs per controller action.

WO-G4-DOSSIER-B (B1, 2026-10-18; schema v7): every dossier also holds ``observations`` derived from the level's
own record (``lever_dossier_state``): the lever region's current state, persistence and reversal, scoped to one
level and one life; the limits chapter reads persistence and reversal from them.

Revision 2 (2026-10-17, Sol's directive): the identity chapter's ``actor`` names the chooser from the G3 selection
event and leaves the executor to provenance (``lever_dossier_provenance``: pending until H2, reconciled at seal); a
relation set names its submission source and the gate as certifier; anatomy channels carry their exact observed
events and affected subject (``lever_dossier_links``).
"""
from __future__ import annotations

import copy
from dataclasses import asdict
from typing import Any, Mapping, Sequence

from inference.framework import lever_dossier_facts as F
from inference.framework import lever_dossier_links as L
from inference.framework import lever_dossier_provenance as P
from inference.framework import lever_dossier_state as S
from inference.framework import strict_json
from inference.framework.descriptive_events import cell_runs

FINAL_REASONS = frozenset({"BUDGET_STOP", "CONTROLLED_STOP", "RUN_END", "CRASH", "CANCELLED"})
LEVER_GROUNDED = "Is the LEVER claim grounded?"
NULL_JOIN = {"status": "UNRESOLVED", "track_id": None, "basis": None}
OK = {"status": "OK", "reasons": [], "refs": []}
G3, G41, G4A, G4B, G4C = "G3-LEVERS", "G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"


# ---- the gate view: retained attributes, read only -----------------------------------------------------------

# A gate view with nothing retained: a census taken before any G3 or G4 state exists (and hand-built test levels).
EMPTY_VIEW: dict[str, Any] = {
    "g3": {"lifecycle": {}, "appearance": {}, "activation": {}, "choosers": {}, "repeat": {}},
    "g41": {"anatomies": {}, "answers": {}},
    "g4a": {"ordered": [], "runs": {}, "completed": {}, "answers": {}, "interruptions": {}, "restudies": {},
            "level_closed": False},
    "g4b": {"levers": [], "predictions": [], "pressed": [], "conditions": [], "answer": None, "from_record": None,
            "reopened": [], "unresolved": None, "level_closed": False, "active_product": None, "stale": []},
    "g4c": {"tests": [], "certified": None, "unresolved": None, "level_closed": False},
}

def _g3_view(adapter: Any, machine: Any) -> dict[str, Any]:
    from inference.framework.lever_repeat import certified

    ledger = getattr(adapter, "entity_ledger", None)
    member_to_entity = dict(getattr(ledger, "member_to_entity", None) or {})
    journal = getattr(adapter, "lifecycle_journal", None)
    lifecycle = {entity: {"state": item.state, "events": [
        {"event_id": ev.event_id, "from": ev.from_state, "to": ev.to_state, "ref": ev.evidence_ref, "actor": ev.actor,
         "reason": ev.reason} for ev in item.events]} for entity, item in ((journal.entities if journal else {}).items())}
    appearance = {}
    for entity, hypothesis in ((ledger.entities if ledger is not None else {}).items()):
        if hypothesis.sightings:
            appearance[entity] = {"first": _sight(hypothesis.sightings[0]), "current": _sight(hypothesis.current),
                                  "status": hypothesis.status}
    activation: dict[str, Any] = {}
    for member, discovery in (getattr(adapter, "_lever_discoveries", None) or {}).items():
        activation[str(discovery.get("entity_id"))] = {
            "source": "G3_DISCOVERY", "intervention": F.plain(discovery.get("intervention") or {}),
            "channel": discovery.get("channel"), "record_ref": discovery.get("record_ref"),
            "witness_evidence_ref": discovery.get("evidence_ref"), "confirmation_evidence_ref": None}
    readings = getattr(adapter, "_repeat_readings", None) or {}
    for member, answer in (getattr(adapter, "_dossier_answers", None) or {}).items():
        entity = member_to_entity.get(member)
        if entity is None or entity in activation:
            continue
        records = [item for item in getattr(adapter, "_confirmation_records", None) or ()
                   if item.get("entity_id") == entity and item.get("target_member_id") == member and certified(item, readings)]
        last = records[-1] if records else {}
        activation[entity] = {"source": "G3_DOSSIER_LEGACY", "intervention": F.plain(answer.intervention),
                              "channel": None, "record_ref": answer.answer_id,
                              "witness_evidence_ref": last.get("witness_evidence_ref"),
                              "confirmation_evidence_ref": last.get("confirmation_evidence_ref")}
    choosers: dict[str, list] = {}
    for event in getattr(machine, "g3_selection_events", None) or ():
        if event.get("event") == "ADMITTED" and event.get("entity_id"):
            choosers.setdefault(str(event["entity_id"]), []).append((int(event.get("at_transition") or 0), event.get("actor")))
    return {"lifecycle": lifecycle, "appearance": appearance, "activation": activation, "choosers": choosers,
            "repeat": {entity: F.plain(item) for entity, item in readings.items()}}


def _sight(sighting: Any) -> dict[str, Any] | None:
    if sighting is None:
        return None
    cells = [(int(r), int(c)) for r, c in sighting.cells]
    rows, cols = [r for r, _ in cells], [c for _, c in cells]
    return {"class": int(sighting.integer), "transition_id": int(sighting.transition_id), "relation": sighting.relation,
            "anchor": [min(cells)[0], min(cells)[1]] if cells else None,
            "bbox": [min(rows), min(cols), max(rows), max(cols)] if cells else None,
            "cell_count": len(cells), "cell_runs": cell_runs(cells)}


def _run_view(run: Any) -> dict[str, Any]:
    body = F.plain({**run.orbit.snapshot(), "run_id": run.run_id, "run_status": run.status,
                    "confirmation": list(run.confirmation)})
    return {"run": body, "lever_class": run.lever_class(), "typing": F.plain(run.typing())}


def _prediction(item: Any) -> dict[str, Any]:
    return F.plain(asdict(item))


def gate_view(machine: Any) -> dict[str, Any] | None:
    """Every retained per-lever G3/G4 field, as plain JSON, without calling a gate method that can change state."""
    if machine is None:
        return None
    from inference.framework.g4_reactions import anatomy_payload

    adapters = getattr(machine, "_adapters", None) or {}
    g41, g4a, g4b, g4c = (adapters.get(key) for key in (G41, G4A, G4B, G4C))
    active = {key: machine.target_journal.active_product(key) for key in (G4B,)}
    levers = [region.entity_id for region in getattr(g4b, "_regions", ()) or ()]
    predictions = [_prediction(item) for item in getattr(g4b, "_predictions", ()) or ()]
    acted = {p["acted_lever"] for p in predictions if p["status"] in ("SUPPORTED", "CONTRADICTED") and p["acted_lever"]}
    answer = getattr(g4b, "_answer", None)
    from_record = getattr(g4b, "_from_record", None)
    stale = []
    for product in machine.target_journal.history:
        if product.status == "STALE" and product.target_id == G4B and all(p["product_id"] != product.product_id for p in stale):
            stale.append({"product_id": product.product_id, "payload": F.plain(product.payload)})
    return {
        "g3": _g3_view(adapters.get(G3), machine),
        "g41": {"anatomies": {e: F.plain(anatomy_payload(a)) for e, a in (getattr(g41, "_anatomies", None) or {}).items()},
                "answers": {e: F.plain(asdict(a)) for e, a in (getattr(g41, "_answers", None) or {}).items()}},
        "g4a": {"ordered": list(getattr(g4a, "_ordered_entities", ()) or ()),
                "runs": {e: [_run_view(r) for r in runs] for e, runs in (getattr(g4a, "_runs", None) or {}).items()},
                "completed": {e: run.run_id for e, run in (getattr(g4a, "_completed", None) or {}).items()},
                "answers": {e: F.plain(asdict(a)) for e, a in (getattr(g4a, "_answers", None) or {}).items()},
                "interruptions": {e: F.plain(item) for e, item in (getattr(g4a, "_interruptions", None) or {}).items()},
                "restudies": dict(getattr(g4a, "_life_restudies", None) or {}),
                "level_closed": getattr(g4a, "_level_closed", None) is not None},
        "g4b": {"levers": levers, "predictions": predictions, "pressed": sorted(acted),
                "conditions": F.plain(list(getattr(getattr(g4b, "_record", None), "conditions", ()) or ())),
                "answer": None if answer is None else F.plain(asdict(answer)),
                "from_record": None if from_record is None else F.plain(from_record),
                "reopened": list(getattr(g4b, "_reopened", ()) or ()), "unresolved": getattr(g4b, "_unresolved", None),
                "level_closed": getattr(g4b, "_level_closed", None) is not None,
                "active_product": None if active[G4B] is None else active[G4B].product_id, "stale": stale},
        "g4c": {"tests": [_prediction(item) for item in getattr(g4c, "_tests", ()) or ()],
                "certified": None if getattr(g4c, "_certified", None) is None else _prediction(g4c._certified),
                "unresolved": getattr(g4c, "_unresolved", None),
                "level_closed": getattr(g4c, "_level_closed", None) is not None},
    }


# ---- chapters ----------------------------------------------------------------------------------------------------

def _chapter(status: str, basis: str, source: str | None = None, facts: Any = None, *, product: Any = None,
             answer: Any = None, history: Sequence[Any] = (), open_items: Sequence[Any] = ()) -> dict[str, Any]:
    return {"status": status, "basis": basis, "prior_status": None, "prior_basis": None, "source": source,
            "product_ref": product, "answer_ref": answer, "evidence_refs": [], "facts": facts,
            "history": list(history), "integrity": dict(OK), "open": list(open_items), "digest": None}


class _Products:
    """The level's stored products for one chapter's gate: certifying, closing, or neither (an open item)."""

    def __init__(self, level: Mapping[str, Any]) -> None:
        self.content = level.get("product_content") or {}
        self.origins = level.get("product_answers") or {}

    def get(self, chapter: str) -> tuple[dict | None, str | None, dict | None]:
        for pid, entry in sorted(self.content.items()):
            if entry.get("gate_id") == F.GATES[chapter]:
                origin = self.origins.get(pid) or {}
                return entry, pid, origin
        return None, None, None

    def judge(self, chapter: str, entity_id: str) -> tuple[str | None, Any, Any, list]:
        """('COMPLETE' | 'CLOSED' | None, payload, product_ref, open items)."""
        entry, pid, origin = self.get(chapter)
        if entry is None:
            return None, None, None, []
        pair = (origin.get("origin"), origin.get("basis"))
        ref = {"product_id": pid, "gate_id": entry["gate_id"], "product_type": entry["product_type"],
               "revision": entry["revision"]}
        if entry.get("status") != "CAPTURED":
            return None, None, None, [{"kind": "PRODUCT_NOT_CERTIFYING", "product_id": pid, "origin": pair[0],
                                       "basis": "PRODUCT_CONTENT_UNREPRESENTABLE"}]
        payload = entry["payload"]
        if pair in F.MAY_COMPLETE.get(chapter, ()):
            return ("COMPLETE" if F.covers(chapter, payload, entity_id) else None), payload, ref, []
        if pair in F.CLOSES.get(chapter, ()):
            return ("CLOSED" if F.closes(chapter, payload, entity_id) else None), payload, ref, []
        if pair[0] == "GATE_DERIVED":  # a declared closure the matrix does not list here (orbit): per-lever retained state
            return None, payload, ref, []
        return None, None, None, [{"kind": "PRODUCT_NOT_CERTIFYING", "product_id": pid, "origin": pair[0], "basis": pair[1]}]


def _identity(entity_id: str, level: Mapping[str, Any], role: Mapping[str, Any] | None, g3: Mapping[str, Any]) -> dict:
    witnesses = level["receipts"]["witnesses"]
    refs = sorted(role.get("witness_refs") or ()) if role else sorted(w for w, r in witnesses.items() if r.get("entity_id") == entity_id)
    rows = [{"witness_id": w, "evidence_ref": witnesses[w]["evidence_ref"], "transition_id": witnesses[w]["transition_id"],
             "channel": witnesses[w].get("channel")} for w in refs if w in witnesses]
    lifecycle = g3["lifecycle"].get(entity_id)
    if lifecycle is not None:
        lifecycle = {**lifecycle, "events": [{**ev, "ref_kind": _ref_kind(ev["ref"], level)} for ev in lifecycle["events"]]}
    activation = g3["activation"].get(entity_id)
    first = min((row["transition_id"] for row in rows), default=None)
    chosen = [actor for at, actor in g3["choosers"].get(entity_id, ()) if first is None or at <= first]
    actor = P.pending_actor(*P.chooser(chosen, activation))  # blocker 1: the executor is provenance's to name
    intervention = (activation or {}).get("intervention") or {}
    reach = None if activation is None else (
        {"kind": "NAV_PROCEDURE", "procedure_id": intervention.get("procedure_id")}
        if str(intervention.get("kind") or "").upper() == "NAV" else {"kind": "DIRECT_COORDINATE", "procedure_id": None})
    facts = {"entity_id": entity_id, "witnesses": rows, "lifecycle": lifecycle, "appearance": g3["appearance"].get(entity_id),
             "activation": activation, "actor": actor, "reachability": reach, "repeat_reading": g3["repeat"].get(entity_id),
             "inventory_status": None if role is None else role.get("inventory_status")}
    if lifecycle is not None and lifecycle["state"] == "REOPENED":
        return _chapter("IN_PROGRESS", "LIFECYCLE_REOPENED", "GATE_WITNESS", facts)
    return _chapter("COMPLETE", "WITNESS_CERTIFIED", "GATE_WITNESS", facts)


def _ref_kind(ref: Any, level: Mapping[str, Any]) -> str:
    receipts = level["receipts"]
    return "EVIDENCE" if ref in receipts["evidence"] else "WITNESS" if ref in receipts["witnesses"] else "OTHER"


def _anatomy(entity_id: str, products: _Products, g41: Mapping[str, Any], level: Mapping[str, Any]) -> dict:
    verdict, payload, ref, items = products.judge("anatomy", entity_id)
    retained = g41["anatomies"].get(entity_id)
    if verdict == "COMPLETE":
        facts, answer = F.product_body("anatomy", payload, entity_id)
        chapter = _chapter("COMPLETE", "PRODUCT_CERTIFIED", "PRODUCT_CONTENT", L.link_anatomy(facts, level),
                           product=ref, answer=answer)
        if retained is not None and F.anatomy_facts(retained) != facts:
            _fail(chapter, "PRODUCT_MISMATCH", [ref["product_id"]])
        return chapter
    if retained is None:
        return _chapter("NOT_BUILT", "GATE_NOT_SEEDED", open_items=items)  # R3: never ahead of G4.1's own seed
    facts = L.link_anatomy(F.anatomy_facts(retained), level)
    answer = g41["answers"].get(entity_id)
    if answer is not None:
        return _chapter("PRODUCT_PENDING", "ANSWER_ACCEPTED_AGGREGATE_OPEN", "GATE_RETAINED", facts,
                        answer=F.answer_ref(G41, answer), open_items=items)
    return _chapter("IN_PROGRESS", "ANSWER_REQUIRED", "GATE_RETAINED", facts, open_items=items)


def _orbit(entity_id: str, products: _Products, g4a: Mapping[str, Any]) -> dict:
    verdict, payload, ref, items = products.judge("orbit", entity_id)
    runs = g4a["runs"].get(entity_id, [])
    if verdict == "COMPLETE":
        facts, answer = F.product_body("orbit", payload, entity_id)
        run_id = facts["run"]["run_id"]
        history = [F.run_facts(view["run"]) for view in runs if view["run"]["run_id"] != run_id]
        chapter = _chapter("COMPLETE", "PRODUCT_CERTIFIED", "PRODUCT_CONTENT", facts, product=ref, answer=answer,
                           history=history, open_items=items)
        retained = next((view for view in runs if view["run"]["run_id"] == run_id), None)
        if retained is not None and F.run_facts(retained["run"]) != facts["run"]:
            _fail(chapter, "PRODUCT_MISMATCH", [ref["product_id"]])
        return chapter
    completed = g4a["completed"].get(entity_id)
    chosen = next((view for view in runs if view["run"]["run_id"] == completed), runs[-1] if runs else None)
    facts = None if chosen is None else F.orbit_facts(
        chosen["run"], chosen["lever_class"], chosen["typing"], g4a["restudies"].get(entity_id, 0),
        g4a["interruptions"].get(entity_id))
    history = [F.run_facts(view["run"]) for view in runs if view is not chosen]
    answer = g4a["answers"].get(entity_id)
    kwargs = {"history": history, "open_items": items}
    if completed is not None:
        basis = "ANSWER_ACCEPTED_AGGREGATE_OPEN" if answer else "RUN_CONFIRMED_EXPLANATION_PENDING"
        return _chapter("PRODUCT_PENDING", basis, "GATE_RETAINED", facts, answer=F.answer_ref(G4A, answer), **kwargs)
    if entity_id in g4a["interruptions"]:
        return _chapter("CLOSED_UNRESOLVED", "INTERRUPTION_RELEASED", "GATE_RETAINED", facts, **kwargs)
    if g4a["level_closed"] and entity_id in g4a["ordered"]:
        return _chapter("CLOSED_UNRESOLVED", "UNSTUDIED_AT_LEVEL_CLOSE", "GATE_RETAINED" if facts else None, facts, **kwargs)
    if chosen is not None:
        status = chosen["run"]["run_status"]
        basis = ("RUN_OPEN" if status in ("RUNNING", "CONFIRMING") else
                 "INTERRUPTED_RESTUDY_PENDING" if status == "INTERRUPTED" else "RUN_ENDED_RESTART_NEEDED")
        return _chapter("IN_PROGRESS", basis, "GATE_RETAINED", facts, **kwargs)
    return _chapter("NOT_BUILT", "NO_EVIDENCE" if entity_id in g4a["ordered"] else "GATE_NOT_SEEDED", **kwargs)


def _limits(orbit: Mapping[str, Any]) -> dict:
    owed = [{"kind": "PROBE_OWED", "field": "LIMITS_PERSISTENCE"}, {"kind": "PROBE_OWED", "field": "LIMITS_REVERSAL"},
            {"kind": "UNAVAILABLE", "field": "CROSS_LEVEL_LIMITS"}]
    run = (orbit.get("facts") or {}).get("run")
    if not F.has_endpoint(run):
        return _chapter("NOT_BUILT", "NO_EVIDENCE" if run else "GATE_NOT_SEEDED", open_items=owed)
    facts = F.limits_facts(run, (orbit.get("facts") or {}).get("typing"))
    return _chapter("IN_PROGRESS", "ENDPOINT_OBSERVED_PROBES_OWED", orbit["source"], facts, product=orbit["product_ref"],
                    open_items=owed)


def _withdrawn(entity_id: str, g4b: Mapping[str, Any], g4c: Mapping[str, Any]) -> list[dict]:
    """R13: every G4-B description a contradiction (or a later description) withdrew, as a typed rejected model."""
    current = (g4b["answer"] or {}).get("answer_id")
    tests = {test["prediction_id"]: test for test in g4c["tests"]}
    out, index = [], 0
    for stale in g4b["stale"]:
        payload = stale["payload"]
        answer = payload.get("answer")
        if payload.get("status") != "COMPLETE" or not isinstance(answer, Mapping) or stale["product_id"] == g4b["active_product"]:
            continue
        if answer.get("answer_id") == current:
            continue  # the same description, invalidated upstream (D15): it is still the gate's answer
        reopened = g4b["reopened"][index] if index < len(g4b["reopened"]) else None
        index += 1
        if entity_id not in (payload.get("lever_entities") or ()):
            continue
        test = tests.get(reopened) or {}
        out.append({
            "kind": "WITHDRAWN_DESCRIPTION", "status": "CONTRADICTED" if reopened else "WITHDRAWN",
            "reason": "CONTRADICTED_BY_LAW_TEST" if reopened else "SUPERSEDED", "product_id": stale["product_id"],
            "answer_id": answer.get("answer_id"),
            **{key: value for key, value in (F.submission(answer, payload.get("from_record")) or {}).items()
               if key in ("certifier", "certification_origin")},
            "relations": [F.relation_struct(i, r) for i, r in enumerate(answer.get("relations") or ())
                          if entity_id in (r.get("levers") or ())],
            "contradiction": None if not reopened else {"prediction_id": reopened, "evidence_ref": test.get("evidence_ref"),
                                                        "transition_id": test.get("transition_id")},
        })
    return out


def _relations(entity_id: str, products: _Products, g4b: Mapping[str, Any], g4c: Mapping[str, Any]) -> dict:
    verdict, payload, ref, items = products.judge("relations", entity_id)
    history = _withdrawn(entity_id, g4b, g4c)
    if verdict == "COMPLETE":
        facts, answer = F.product_body("relations", payload, entity_id)
        return _chapter("COMPLETE", "PRODUCT_CERTIFIED", "PRODUCT_CONTENT", facts, product=ref, answer=answer,
                        history=history, open_items=items)
    if verdict == "CLOSED":
        facts, answer = F.product_body("relations", payload, entity_id)
        return _chapter("CLOSED_UNRESOLVED", F.CLOSING_BASIS[payload["status"]], "PRODUCT_CONTENT", facts, product=ref,
                        answer=answer, history=history, open_items=items)
    if entity_id not in g4b["levers"]:
        return _chapter("NOT_BUILT", "GATE_NOT_SEEDED", history=history, open_items=items)
    retained = {"predictions": g4b["predictions"], "missing_conditions": g4b["conditions"], "answer": g4b["answer"],
                "from_record": g4b["from_record"], "pressed_levers": g4b["pressed"]}
    facts = F.relations_facts(retained, entity_id)
    kwargs = {"history": history, "open_items": items}
    if g4b["answer"] is not None:
        return _chapter("PRODUCT_PENDING", "AGGREGATE_INVALIDATED", "GATE_RETAINED", facts,
                        answer=F.answer_ref(G4B, g4b["answer"]), **kwargs)
    if g4b["unresolved"] or g4b["level_closed"]:
        basis = "PRODUCT_UNRESOLVED" if g4b["unresolved"] else "PRODUCT_CLOSED_BY_LEVEL_BOUNDARY"
        return _chapter("CLOSED_UNRESOLVED", basis, "GATE_RETAINED", facts, **kwargs)
    basis = "REOPENED_BY_CONTRADICTION" if g4b["reopened"] else "STUDY_OPEN"
    return _chapter("IN_PROGRESS", basis, "GATE_RETAINED", facts, **kwargs)


def _law(entity_id: str, products: _Products, g4b: Mapping[str, Any], g4c: Mapping[str, Any],
         relations_open: bool) -> dict:
    verdict, payload, ref, items = products.judge("law_tests", entity_id)
    if verdict == "COMPLETE":
        facts, _ = F.product_body("law_tests", payload, entity_id)
        return _chapter("COMPLETE", "PRODUCT_CERTIFIED", "PRODUCT_CONTENT", facts, product=ref, open_items=items)
    if verdict == "CLOSED":
        facts, _ = F.product_body("law_tests", payload, entity_id)
        return _chapter("CLOSED_UNRESOLVED", F.CLOSING_BASIS[payload["status"]], "PRODUCT_CONTENT", facts, product=ref,
                        open_items=items)
    retained = {"tests": g4c["tests"], "status": None, "law_test": g4c["certified"], "lever_entities": g4b["levers"]}
    facts = F.law_facts(retained, entity_id)
    if not facts["tests"] and not relations_open:
        return _chapter("NOT_BUILT", "GATE_NOT_SEEDED", open_items=items)
    if g4c["unresolved"] or g4c["level_closed"]:
        basis = "PRODUCT_UNRESOLVED" if g4c["unresolved"] else "PRODUCT_CLOSED_BY_LEVEL_BOUNDARY"
        return _chapter("CLOSED_UNRESOLVED", basis, "GATE_RETAINED", facts, open_items=items)
    return _chapter("IN_PROGRESS", "STUDY_OPEN", "GATE_RETAINED", facts, open_items=items)


def open_items(chapters: Mapping[str, Mapping[str, Any]], observations: Mapping[str, Any] | None = None,
               v7: bool = False) -> dict:
    """The derived chapter (R7): recomputed whenever any other chapter or the observations change."""
    intervention = ((chapters["identity"].get("facts") or {}).get("activation") or {}).get("intervention")
    facts = F.open_items_facts(chapters, intervention, observations, v7)
    if F.open_items_complete(facts):
        return _chapter("COMPLETE", "NO_OPEN_ITEMS", "DERIVED", facts)
    return _chapter("IN_PROGRESS", "OPEN_ITEMS_REMAIN", "DERIVED", facts)


# ---- integrity, labels, digests ---------------------------------------------------------------------------------

def _fail(chapter: dict, reason: str, refs: Sequence[Any]) -> None:
    """R8: the chapter fails closed; the status it would have held is kept as ``prior_status``."""
    if chapter["integrity"]["status"] == "FAILED_CLOSED":
        return
    chapter.update(prior_status=chapter["status"], prior_basis=chapter["basis"], status="CLOSED_UNRESOLVED",
                   basis=reason, facts=None, history=[],
                   integrity={"status": "FAILED_CLOSED", "reasons": [reason], "refs": sorted({str(r) for r in refs})})


def _label(chapter: dict, frozen: bool, reason: str | None) -> None:
    """R1: a census closes or interrupts open work; PRODUCT_PENDING keeps its basis."""
    if chapter["status"] != "IN_PROGRESS" or chapter["prior_status"] is not None:
        return
    if frozen:
        chapter.update(prior_status="IN_PROGRESS", prior_basis=chapter["basis"], status="CLOSED_UNRESOLVED", basis="LEVEL_ENDED")
    elif reason in FINAL_REASONS:
        chapter.update(prior_status="IN_PROGRESS", prior_basis=chapter["basis"], status="INTERRUPTED", basis=reason)


def chapter_digest(entity_id: str, name: str, chapter: Mapping[str, Any]) -> dict[str, str]:
    return strict_json.digest_record({"entity_id": entity_id, "chapter": name,
                                      **{key: value for key, value in chapter.items() if key != "digest"}})


def _seal(entity_id: str, dossier: dict, level: Mapping[str, Any]) -> None:
    """Evidence refs, open items, the census label and digests: the last step whenever a dossier changes."""
    frozen = level.get("state") == "FROZEN"
    reason = dossier["census_context"]["persist_reason"]
    chapters, observations = dossier["chapters"], dossier.get("observations")
    v7 = "observations" in dossier
    if v7:
        _observe_limits(chapters["limits"], observations)
    chapters["open_items"] = (open_items(chapters, observations, v7) if chapters["open_items"]["integrity"]["status"] == "OK"
                              else chapters["open_items"])
    for name in F.CHAPTERS:
        _label(chapters[name], frozen, reason)
        chapter = chapters[name]
        chapter["evidence_refs"] = sorted(F.evidence_ids(chapter["facts"]) | F.evidence_ids(chapter["history"]))
        chapter["digest"] = chapter_digest(entity_id, name, chapter)
    if v7:
        S.seal(entity_id, observations)


def _observe_limits(limits: dict, observations: Mapping[str, Any]) -> None:
    """B1: the limits chapter reads persistence and reversal from the observations; owed until the record shows."""
    if limits["integrity"]["status"] != "OK":
        return
    limits["facts"] = F.limits_overlay(limits["facts"], observations)
    kept = [item for item in limits["open"] if item.get("kind") not in ("PROBE_OWED", "UNAVAILABLE")]
    limits["open"] = kept + F.limits_open(observations, True)
    key = "prior_basis" if limits["prior_status"] == "IN_PROGRESS" else "basis"  # a census label keeps the basis it closed
    if limits[key] in (F.LIMITS_OWED, F.LIMITS_SHOWN):  # revision 2: the basis follows what is still owed, both ways
        limits[key] = F.limits_basis(observations)


def _resolution(dossier: dict, level: Mapping[str, Any]) -> None:
    evidence = level["receipts"]["evidence"]
    for name in F.CHAPTERS[:-1]:
        chapter = dossier["chapters"][name]
        missing = sorted(ref for ref in F.evidence_ids(chapter["facts"]) | F.evidence_ids(chapter["history"])
                         if ref not in evidence)
        if missing:
            _fail(chapter, "EVIDENCE_UNRESOLVED", missing)


fail_closed, reseal = _fail, _seal  # revision 2: provenance (``lever_dossier_provenance``) reuses R8 and the seal


def withdrawn_levers(level: Mapping[str, Any]) -> set[str]:
    """Levers whose role a record break withdrew: kept as entirely failed-closed dossiers."""
    roles = {role["entity_id"] for role in level["certified"]["roles"] if role.get("role") == "LEVER"}
    return {str(gap["subject"]) for gap in level.get("gaps") or ()
            if gap.get("reason") == "RECORD_MISMATCH" and gap.get("archetype_question") == LEVER_GROUNDED} - roles


def build(level: Mapping[str, Any], view: Mapping[str, Any] | None) -> dict[str, Any]:
    """One dossier per certified lever (and per withdrawn lever), pure over the census level and the gate view."""
    if view is None:
        return {}
    roles = {role["entity_id"]: role for role in level["certified"]["roles"] if role.get("role") == "LEVER"}
    withdrawn = withdrawn_levers(level)
    products = _Products(level)
    frozen = level.get("state") == "FROZEN"
    relations_product, _pid, origin = products.get("relations")
    relations_open = relations_product is not None and (origin or {}).get("origin") == "ANSWER_CERTIFIED"
    scope = view.get("scope")
    dossiers = {}
    for entity_id in sorted(set(roles) | withdrawn):
        role = roles.get(entity_id)
        identity = _identity(entity_id, level, role, view["g3"])
        orbit = _orbit(entity_id, products, view["g4a"])
        chapters = {"identity": identity, "anatomy": _anatomy(entity_id, products, view["g41"], level), "orbit": orbit,
                    "limits": _limits(orbit), "relations": _relations(entity_id, products, view["g4b"], view["g4c"]),
                    "law_tests": _law(entity_id, products, view["g4b"], view["g4c"], relations_open)}
        chapters["open_items"] = _chapter("IN_PROGRESS", "OPEN_ITEMS_REMAIN", "DERIVED")
        dossier = {"subject": {"kind": "G3_ENTITY", "entity_id": entity_id, "level": int(level["level"])},
                   "track_join": dict(role["identity"]) if role else dict(NULL_JOIN),
                   "census_context": {"census": "H1_FROZEN" if frozen else "OPEN",
                                      "persist_reason": "LEVEL_ADVANCE" if frozen else None},
                   "chapters": chapters,
                   "observations": S.with_phase(S.derive(scope, entity_id), scope, entity_id, orbit)}
        if entity_id in withdrawn:
            for name in F.CHAPTERS:
                _fail(chapters[name], "RECORD_MISMATCH", [entity_id])
            S.fail(dossier["observations"], "RECORD_MISMATCH", [entity_id])
        _resolution(dossier, level)
        _seal(entity_id, dossier, level)
        dossiers[entity_id] = dossier
    return dossiers


def attach(machine: Any, level: dict[str, Any]) -> dict[str, Any]:
    """``compile_level``'s one hook: the level with its dossiers (an H1 freeze labels them at once). B1: the scope
    of the level's own record is read here, once, beside the gate view."""
    view = gate_view(machine)
    if view is not None:
        view = {**view, "scope": S.observe(machine, int(level["level"]), view["g41"]["anatomies"],
                                           level["receipts"]["evidence"])}
        view["scope"] = _experiment_failures(machine, view["scope"], level["receipts"]["evidence"])
    level["lever_dossiers"] = build(level, view)
    return level


def _experiment_failures(machine: Any, scope: dict[str, Any] | None, evidence: Mapping[str, Any]) -> Any:
    """B3: a G4-B experiment of this level and life whose execution evidence is not one-to-one fails its subject's
    observations closed (``lever_dossier_state.derive``); every other dossier and chapter is untouched."""
    from inference.framework import lever_experiments

    if scope is None:
        return None
    failures = lever_experiments.evidence_failures(machine, scope["level"], scope["life"], evidence)
    return {**scope, "experiment_failures": failures} if failures else scope


def _mismatched(level: Mapping[str, Any]) -> set[int]:
    check = (level.get("record") or {}).get("journal_check") or {}
    return {int(t) for key in ("extra", "renamed", "duplicated") for t in check.get(key) or ()}


def finalize(levels: Sequence[Mapping[str, Any]], persist_reason: str) -> list[dict[str, Any]]:
    """``compile_world_model``'s one hook: H2 integrity, then the persist reason and its label on the open level."""
    out = []
    for level in levels:
        level = dict(level)
        dossiers = copy.deepcopy(level.get("lever_dossiers") or {})
        broken, evidence = _mismatched(level), level["receipts"]["evidence"]
        withdrawn = withdrawn_levers(level)
        for entity_id, dossier in dossiers.items():
            if level.get("state") != "FROZEN":
                dossier["census_context"] = {"census": "OPEN", "persist_reason": persist_reason}
            if entity_id in withdrawn:  # H2 withdrew the role: nothing in the dossier is claimed, its join included
                dossier["track_join"] = dict(NULL_JOIN)
                for name in F.CHAPTERS:
                    _fail(dossier["chapters"][name], "RECORD_MISMATCH", [entity_id])
                if "observations" in dossier:
                    S.fail(dossier["observations"], "RECORD_MISMATCH", [entity_id])
            for name in F.CHAPTERS[:-1]:
                chapter = dossier["chapters"][name]
                cited = {evidence[ref]["transition_id"] for ref in chapter["evidence_refs"] if ref in evidence}
                if cited & broken:
                    _fail(chapter, "RECORD_MISMATCH", sorted(cited & broken))
            observed = S.cited_transitions(dossier.get("observations") or {})
            if observed & broken:  # B1: a derived fact resting on a mismatched transition states nothing
                S.fail(dossier["observations"], "RECORD_MISMATCH", sorted(observed & broken))
            _seal(entity_id, dossier, level)
        level["lever_dossiers"] = dossiers
        out.append(level)
    return out


__all__ = ["EMPTY_VIEW", "FINAL_REASONS", "attach", "build", "chapter_digest", "fail_closed", "finalize", "gate_view",
           "open_items", "reseal", "withdrawn_levers"]
