"""WO-G4-DOSSIER-A: the pure schema-v6 validator of a level's lever dossiers.

Author: Claude (Alpha build seat), 2026-10-16. Interface: ``INTERFACE_WO_G4_DOSSIER_A_v2`` §6 (Sol's origin matrix).

It reads only the level and the model manifest. What it proves: every dossier belongs to a certified lever of its own
level; every status and basis is in the ruled vocabulary and fits the census that wrote it; every reference resolves;
COMPLETE holds exactly when a product of the chapter's type, with an origin the matrix allows, covers the lever; a
chapter built from a stored product equals that product's projection; retained content is internally consistent and
never COMPLETE; the derived chapter equals its recomputation; every digest recomputes. What it cannot prove: that a
retained fact came from the gate machine (the honest limit of the receipts index, unchanged).

Revision 2 (2026-10-17, Sol's directive): every provenance-dependent fact (the activation's executor, the relation
set's submitter, a receipt an execution contradicts) is recomputed from the model's embedded provenance chapter;
every anatomy channel's event links and affected subject are recomputed from the level's description.
"""
from __future__ import annotations

from typing import Any, Mapping

from inference.framework import lever_dossier_facts as F
from inference.framework import lever_dossier_links as L
from inference.framework import lever_dossier_provenance as P
from inference.framework import lever_dossiers as D
from inference.framework import strict_json

STATUSES = ("NOT_BUILT", "IN_PROGRESS", "PRODUCT_PENDING", "COMPLETE", "CLOSED_UNRESOLVED", "INTERRUPTED")
INTEGRITY = frozenset({"RECORD_MISMATCH", "PRODUCT_MISMATCH", "EVIDENCE_UNRESOLVED", "PROVENANCE_INCOMPLETE"})
BASES = {
    "NOT_BUILT": frozenset({"GATE_NOT_SEEDED", "NO_EVIDENCE"}),
    "IN_PROGRESS": frozenset({"LIFECYCLE_REOPENED", "ANSWER_REQUIRED", "RUN_OPEN", "RUN_ENDED_RESTART_NEEDED",
                              "INTERRUPTED_RESTUDY_PENDING", "ENDPOINT_OBSERVED_PROBES_OWED", "STUDY_OPEN",
                              "REOPENED_BY_CONTRADICTION", "OPEN_ITEMS_REMAIN"}),
    "PRODUCT_PENDING": frozenset({"ANSWER_ACCEPTED_AGGREGATE_OPEN", "RUN_CONFIRMED_EXPLANATION_PENDING",
                                  "AGGREGATE_INVALIDATED"}),
    "COMPLETE": frozenset({"WITNESS_CERTIFIED", "PRODUCT_CERTIFIED", "NO_OPEN_ITEMS"}),
    "CLOSED_UNRESOLVED": frozenset({"INTERRUPTION_RELEASED", "UNSTUDIED_AT_LEVEL_CLOSE", "PRODUCT_UNRESOLVED",
                                    "PRODUCT_CLOSED_BY_LEVEL_BOUNDARY", "LEVEL_ENDED"}) | INTEGRITY,
    "INTERRUPTED": D.FINAL_REASONS,
}
SOURCES = frozenset({"GATE_WITNESS", "PRODUCT_CONTENT", "GATE_RETAINED", "DERIVED", None})
CHAPTER_KEYS = frozenset({"status", "basis", "prior_status", "prior_basis", "source", "product_ref", "answer_ref",
                          "evidence_refs", "facts", "history", "integrity", "open", "digest"})
OPEN_KINDS = frozenset({"PRODUCT_NOT_CERTIFYING", "PROBE_OWED", "UNAVAILABLE", P.INCOMPLETE})


class DossierError(ValueError):
    """A level's lever dossiers break the schema-v6 contract."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DossierError(message)


def validate_level(level: Mapping[str, Any], manifest: Mapping[str, Any], provenance: Any = None) -> None:
    dossiers = level.get("lever_dossiers")
    context = P.Context(provenance)
    context.level_contradicted = context.contradicted(level)
    _require(isinstance(dossiers, Mapping), f"level {level.get('level')} has a lever_dossiers chapter")
    roles = {role["entity_id"]: role for role in level["certified"]["roles"] if role.get("role") == "LEVER"}
    withdrawn = D.withdrawn_levers(level)
    _require(set(dossiers) == set(roles) | withdrawn,
             f"level {level.get('level')}: lever_dossiers name exactly the certified LEVER roles (and withdrawn levers)")
    for entity_id, dossier in dossiers.items():
        try:
            _dossier(entity_id, dossier, level, roles.get(entity_id), manifest, context)
        except DossierError as exc:
            raise DossierError(f"lever_dossiers[{entity_id}]: {exc}") from exc


def _dossier(entity_id: str, dossier: Any, level: Mapping[str, Any], role: Mapping[str, Any] | None,
             manifest: Mapping[str, Any], context: P.Context) -> None:
    _require(isinstance(dossier, Mapping) and set(dossier) == {"subject", "track_join", "census_context", "chapters"},
             "a dossier holds subject, track_join, census_context and chapters")
    _require(dossier["subject"] == {"kind": "G3_ENTITY", "entity_id": entity_id, "level": int(level["level"])},
             "the subject is this level's G3 entity")
    _require(dossier["track_join"] == (dict(role["identity"]) if role else dict(D.NULL_JOIN)),
             "the track_join equals the LEVER role's identity (context only, never identity)")
    frozen = level.get("state") == "FROZEN"
    expected = {"census": "H1_FROZEN", "persist_reason": "LEVEL_ADVANCE"} if frozen else {
        "census": "OPEN", "persist_reason": manifest.get("persist_reason")}
    _require(dossier["census_context"] == expected, "census_context records the census that persisted the level")
    chapters = dossier["chapters"]
    _require(isinstance(chapters, Mapping) and tuple(sorted(chapters)) == tuple(sorted(F.CHAPTERS)), "seven chapters")
    for name in F.CHAPTERS:
        _chapter(entity_id, name, chapters[name], chapters, level, role, manifest, frozen, context)


def _chapter(entity_id: str, name: str, chapter: Any, chapters: Mapping[str, Any], level: Mapping[str, Any],
             role: Mapping[str, Any] | None, manifest: Mapping[str, Any], frozen: bool, context: P.Context) -> None:
    where = f"chapter {name}"
    _require(isinstance(chapter, Mapping) and set(chapter) == CHAPTER_KEYS, f"{where} has exactly the declared keys")
    status, basis = chapter["status"], chapter["basis"]
    _require(status in STATUSES and basis in BASES[status], f"{where}: {status}/{basis} is not in the ruled vocabulary")
    _require(chapter["source"] in SOURCES, f"{where}: unknown source")
    _require(chapter["digest"] == D.chapter_digest(entity_id, name, chapter), f"{where}: the digest does not recompute")
    _require(chapter["evidence_refs"] == sorted(F.evidence_ids(chapter["facts"]) | F.evidence_ids(chapter["history"])),
             f"{where}: evidence_refs are exactly the evidence its facts and history cite")
    _require(all(isinstance(item, Mapping) and item.get("kind") in OPEN_KINDS for item in chapter["open"]),
             f"{where}: open items are typed")
    _require([item for item in chapter["open"] if item.get("kind") == P.INCOMPLETE] == P.open_items(name, chapter),
             f"{where}: its PROVENANCE_INCOMPLETE items are exactly the ones its provenance-dependent facts owe")
    if chapter["integrity"].get("status") == "FAILED_CLOSED":
        return _failed(entity_id, name, chapter, level, context)
    _require(not set(chapter["evidence_refs"]) & context.level_contradicted,
             f"{where}: rests on an evidence receipt the embedded journal contradicts and is not failed closed")
    _require(chapter["integrity"] == D.OK, f"{where}: integrity is OK or FAILED_CLOSED")
    _require(entity_id not in D.withdrawn_levers(level), f"{where}: a withdrawn lever's chapters fail closed")
    evidence = level["receipts"]["evidence"]
    unresolved = [ref for ref in chapter["evidence_refs"] if ref not in evidence]
    _require(not unresolved, f"{where}: evidence {unresolved[:3]} does not resolve on this level")
    _census(where, chapter, frozen, manifest)
    if chapter["facts"] is not None:
        _require(set(chapter["facts"]) == F.FACT_KEYS[name], f"{where}: facts hold exactly the declared keys")
    _require(chapter["source"] != "GATE_RETAINED" or status != "COMPLETE", f"{where}: retained work is never COMPLETE")
    if name == "anatomy" and chapter["facts"] is not None:
        _links(where, chapter["facts"], level)
    if name == "relations" and chapter["facts"] is not None:
        _submission(where, chapter["facts"], level, context)
    {"identity": _identity, "open_items": _open_items}.get(name, _gated)(entity_id, name, chapter, chapters, level, role,
                                                                       context)


def _links(where: str, facts: Mapping[str, Any], level: Mapping[str, Any]) -> None:
    """Blockers 3 and 4: each channel's event links and affected subject are what the description supports."""
    for channel in facts["channels"]:
        problem = L.link_problem(channel, level, facts["witness_evidence_ref"])
        _require(problem is None, f"{where}: channel {channel.get('channel_id')}: {problem}")


def _submission(where: str, facts: Mapping[str, Any], level: Mapping[str, Any], context: P.Context) -> None:
    """Blocker 2: the gate certifies; the record or provenance names the submitter, never Duck by default."""
    stored = facts["submission"]
    if stored is None:
        _require(facts["description"] is None, f"{where}: an answered relation set names its submission")
        return
    _require(isinstance(stored, Mapping) and tuple(sorted(stored)) == tuple(sorted(P.SUBMISSION_KEYS))
             and stored["certifier"] == P.RELATIONS
             and (stored["submission_source"] == "RECORD") == (stored["certification_origin"] == "RELATIONS_CERTIFIED_FROM_RECORD")
             and stored["certification_origin"] in ("ANSWER_CERTIFIED", "RELATIONS_CERTIFIED_FROM_RECORD"),
             f"{where}: the G4-B gate is the certifier and the record is the source only of a record-derived set")
    answer_id = (facts["description"] or {}).get("answer_id")
    _require(stored == P.attest_submission(stored, answer_id, level.get("level"), context),
             f"{where}: the submitter is not what the embedded provenance records")


def _failed(entity_id: str, name: str, chapter: Mapping[str, Any], level: Mapping[str, Any], context: P.Context) -> None:
    integrity = chapter["integrity"]
    reasons = integrity.get("reasons") or []
    _require(len(reasons) == 1 and reasons[0] in INTEGRITY, f"chapter {name}: one typed integrity reason")
    _require(chapter["status"] == "CLOSED_UNRESOLVED" and chapter["basis"] == reasons[0] and chapter["prior_status"] in STATUSES
             and chapter["facts"] is None and chapter["history"] == [],
             f"chapter {name}: a failed chapter is CLOSED_UNRESOLVED with its prior status and no facts")
    if reasons[0] == "EVIDENCE_UNRESOLVED":
        _require(bool(integrity["refs"]) and all(ref not in level["receipts"]["evidence"] for ref in integrity["refs"]),
                 f"chapter {name}: EVIDENCE_UNRESOLVED names refs that indeed do not resolve")
    if reasons[0] == P.INCOMPLETE:
        _require(bool(integrity["refs"]) and set(integrity["refs"]) <= context.level_contradicted,
                 f"chapter {name}: PROVENANCE_INCOMPLETE names evidence the embedded journal contradicts")


def _census(where: str, chapter: Mapping[str, Any], frozen: bool, manifest: Mapping[str, Any]) -> None:
    """R1: who may hold IN_PROGRESS, INTERRUPTED and LEVEL_ENDED, by the census that persisted the level."""
    status, basis, prior = chapter["status"], chapter["basis"], chapter["prior_status"]
    reason = manifest.get("persist_reason")
    labelled = basis == "LEVEL_ENDED" or status == "INTERRUPTED"
    _require(labelled == (prior is not None), f"{where}: a prior status is kept only by a census label or an integrity failure")
    if labelled:
        _require(prior == "IN_PROGRESS" and chapter["prior_basis"] in BASES["IN_PROGRESS"],
                 f"{where}: only open work is labelled by a census")
    if frozen:
        _require(status not in ("IN_PROGRESS", "INTERRUPTED"), f"{where}: an H1-frozen level holds no open or interrupted work")
    else:
        _require(basis != "LEVEL_ENDED", f"{where}: LEVEL_ENDED belongs to an H1-frozen level")
        final = reason in D.FINAL_REASONS
        _require(not (final and status == "IN_PROGRESS"), f"{where}: an H2 stop leaves no work IN_PROGRESS")
        _require(status != "INTERRUPTED" or (final and basis == reason), f"{where}: INTERRUPTED names this model's stop")


def _identity(entity_id: str, name: str, chapter: Mapping[str, Any], chapters: Mapping[str, Any],
              level: Mapping[str, Any], role: Mapping[str, Any] | None, context: P.Context) -> None:
    facts = chapter["facts"]
    witnesses = level["receipts"]["witnesses"]
    expected = [{"witness_id": w, "evidence_ref": witnesses[w]["evidence_ref"], "transition_id": witnesses[w]["transition_id"],
                 "channel": witnesses[w].get("channel")} for w in sorted((role or {}).get("witness_refs") or ()) if w in witnesses]
    _require(chapter["source"] == "GATE_WITNESS" and facts["entity_id"] == entity_id, "identity rests on the G3 witness")
    _require(facts["witnesses"] == expected and all(witnesses[w["witness_id"]].get("entity_id") == entity_id
                                                     for w in facts["witnesses"]),
             "identity witnesses are exactly this lever's witness receipts")
    lifecycle = facts["lifecycle"]
    reopened = lifecycle is not None and lifecycle.get("state") == "REOPENED"
    _require((chapter["status"], chapter["basis"]) in (
        {("IN_PROGRESS", "LIFECYCLE_REOPENED"), ("CLOSED_UNRESOLVED", "LEVEL_ENDED"), ("INTERRUPTED", chapter["basis"])}
        if reopened else {("COMPLETE", "WITNESS_CERTIFIED")}), "identity status follows the lifecycle")
    for event in (lifecycle or {}).get("events") or ():
        kind = event.get("ref_kind")
        _require(kind == "OTHER" or event["ref"] in level["receipts"]["evidence" if kind == "EVIDENCE" else "witnesses"],
                 "a lifecycle event's evidence or witness ref resolves")
    _require(facts["inventory_status"] == (role or {}).get("inventory_status"), "identity states the role's inventory status")
    _actor(facts, level, context)


def _actor(facts: Mapping[str, Any], level: Mapping[str, Any], context: P.Context) -> None:
    """Blocker 1: the chooser fits its basis (gate-retained, not journal-verified in this slice); ``status`` and
    ``basis`` attest the executor, which is exactly what the embedded provenance records on this level."""
    actor = facts["actor"]
    _require(isinstance(actor, Mapping) and tuple(sorted(actor)) == tuple(sorted(P.ACTOR_KEYS)),
             "the identity actor holds chooser, chooser_basis, executor, status, basis and execution_event_id")
    basis, activation = actor["chooser_basis"], facts["activation"]
    _require(basis in P.CHOOSER_BASES and (
        actor["chooser"] in ("DUCK", "CONTROLLER") if basis == "G3_SELECTION_EVENT" else
        (actor["chooser"], activation is not None) == (("CONTROLLER", True) if basis == "G3_COVERAGE_ORDER" else (None, False))),
             "the identity actor's chooser fits its basis")
    expected = P.attest_actor(actor, P.actor_evidence(facts), level.get("level"), context)  # revision 3: level-scoped
    _require(actor == expected, f"the identity actor's executor is not what the embedded provenance records "
                                f"(expected {expected['status']}/{expected['basis']})")


def _active(level: Mapping[str, Any], chapter: str) -> tuple[Any, Any, Any]:
    for pid, entry in sorted((level.get("product_content") or {}).items()):
        if entry.get("gate_id") == F.GATES[chapter]:
            return pid, entry, (level.get("product_answers") or {}).get(pid) or {}
    return None, None, None


def _gated(entity_id: str, name: str, chapter: Mapping[str, Any], chapters: Mapping[str, Any],
           level: Mapping[str, Any], role: Mapping[str, Any] | None, context: P.Context) -> None:
    """Anatomy, orbit, limits, relations and law tests: the origin matrix, product agreement and retained consistency."""
    where = f"chapter {name}"
    pid, entry, origin = _active(level, name)
    pair = (origin or {}).get("origin"), (origin or {}).get("basis")
    captured = entry is not None and entry.get("status") == "CAPTURED"
    certifying = captured and pair in F.MAY_COMPLETE.get(name, ()) and F.covers(name, entry["payload"], entity_id)
    closing = captured and pair in F.CLOSES.get(name, ()) and F.closes(name, entry["payload"], entity_id)
    if name != "limits":
        _require((chapter["status"] == "COMPLETE") == certifying,
                 f"{where}: COMPLETE holds exactly when a certifying {F.PRODUCT_TYPES[name]} covers the lever")
        if closing:
            _require(chapter["status"] == "CLOSED_UNRESOLVED", f"{where}: a gate-derived closure closes, never completes")
    else:
        _require(chapter["status"] != "COMPLETE" or chapter["facts"]["persistence"] != "PROBE_OWED",
                 f"{where}: limits is never COMPLETE while persistence or reversal is PROBE_OWED")
    if chapter["source"] == "PRODUCT_CONTENT":
        _require(captured and chapter["product_ref"] == {"product_id": pid, "gate_id": entry["gate_id"],
                                                         "product_type": entry["product_type"], "revision": entry["revision"]},
                 f"{where}: product_ref resolves to the level's stored {F.PRODUCT_TYPES[name]}")
        _require(name == "limits" or certifying or closing, f"{where}: product content is cited only by a covering product")
        facts, answer = _projection(name, entry["payload"], entity_id, level, context)
        _require(chapter["facts"] == facts and chapter["answer_ref"] == answer,
                 f"{where}: facts disagree with the stored product's projection for this lever")
    else:
        _require(chapter["product_ref"] is None, f"{where}: product_ref only for product content")
        _retained(where, name, chapter, level, entity_id, chapters)


def _projection(name: str, payload: Mapping[str, Any], entity_id: str, level: Mapping[str, Any],
                context: P.Context) -> tuple[Any, Any]:
    """A stored product's projection for this lever, with the links and provenance a dossier adds to it."""
    facts, answer = F.product_body(name, payload, entity_id)
    if name == "anatomy":
        facts = L.link_anatomy(facts, level)
    if name == "relations":
        submission = facts["submission"]
        facts = {**facts, "submission": P.attest_submission(
            submission, (facts["description"] or {}).get("answer_id"), level.get("level"), context)}
    return facts, answer


def _retained(where: str, name: str, chapter: Mapping[str, Any], level: Mapping[str, Any], entity_id: str,
              chapters: Mapping[str, Any]) -> None:
    facts, evidence = chapter["facts"], level["receipts"]["evidence"]
    _require(chapter["status"] != "NOT_BUILT" or facts is None, f"{where}: NOT_BUILT holds no facts")
    activation = ((chapters["identity"].get("facts") or {}).get("activation") or {}).get("intervention")
    if name == "anatomy" and facts is not None and activation is not None:
        _require(F.intervention_key(facts["intervention"]) == F.intervention_key(activation),
                 f"{where}: the anatomy is this lever's activation")
    if name == "orbit":
        for run in [(facts or {}).get("run"), *chapter["history"]]:
            if not run:
                continue
            _require(len(run["state_sequence"]) == len(run["steps"]) + 1, f"{where}: a run's states follow its steps")
            if activation is not None and str(activation.get("kind") or "").upper() != "NAV":
                _require(F.intervention_key(run["intervention"]) == F.intervention_key(activation),
                         f"{where}: every run presses this lever's activation")
            for step in [*run["steps"], *run["confirmation"]]:
                ref = step.get("evidence_ref")
                _require(ref is None or evidence[ref]["transition_id"] == step["transition_id"],
                         f"{where}: a step's evidence lies on its own transition")
    if name in ("relations", "law_tests") and facts is not None:
        for test in facts["tests"]:
            _require(test["acted"] or test["named"], f"{where}: every prediction row concerns this lever")
            if test["evidence_ref"] is not None:
                _require(evidence[test["evidence_ref"]]["transition_id"] == test["transition_id"],
                         f"{where}: a graded prediction's evidence lies on its own transition")
            if test["status"] in ("SUPPORTED", "CONTRADICTED"):
                _require(test["transition_id"] > test["declared_board"]["after_transition"],
                         f"{where}: a prediction is graded after it was frozen")
    if chapter["basis"] == "ANSWER_ACCEPTED_AGGREGATE_OPEN":
        _require(chapter["answer_ref"] is not None, f"{where}: an accepted answer is referenced")


def _open_items(entity_id: str, name: str, chapter: Mapping[str, Any], chapters: Mapping[str, Any],
                level: Mapping[str, Any], role: Mapping[str, Any] | None, context: P.Context) -> None:
    derived = D.open_items(chapters)
    _require(chapter["source"] == "DERIVED" and chapter["facts"] == derived["facts"],
             "open_items equals its recomputation from the other chapters")
    complete = derived["status"] == "COMPLETE"
    _require((chapter["status"] == "COMPLETE") == complete and (chapter["prior_basis"] or chapter["basis"]) == derived["basis"],
             "open_items status follows its recomputation (PROBE_OWED blocks COMPLETE)")


def check_strict(payload: Mapping[str, Any]) -> None:
    """R10: the whole v6 payload is strict canonical JSON before its hash is trusted."""
    try:
        strict_json.check(payload)
    except strict_json.StrictJsonError as exc:
        raise DossierError(f"the model is not strict canonical JSON: {exc}") from exc


__all__ = ["BASES", "DossierError", "STATUSES", "check_strict", "validate_level"]
