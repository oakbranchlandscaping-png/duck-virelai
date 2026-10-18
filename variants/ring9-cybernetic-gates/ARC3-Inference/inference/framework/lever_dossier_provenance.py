"""WO-G4-DOSSIER-A revision 2: the dossier facts that depend on provenance, reconciled only at H2 (blocker 1, scope).

Author: Claude (Alpha build seat), 2026-10-17. Sol's revision-2 directive.

Provenance decides three things a dossier may say, and nothing else (Sol's scope correction):

* **who executed a G3 activation** — the identity chapter's ``actor``. The chooser comes from the G3 selection event
  that chose the lever (or, with none, the coverage order); it is gate-retained and not journal-verified in this
  slice: ``actor.status`` and ``actor.basis`` attest the executor only. The executor comes only from the embedded
  journal's executed probe on the dossier's own level whose ``evidence_id`` is the activation's witness evidence. It
  is never inferred from the chooser and never defaults to the controller;
* **who submitted a G4-B answer** — the relations chapter's ``submission``. The gate is always the certifier; the
  record is the source of a record-derived relation set; otherwise the submitter is the executor of the journal's
  admitted answer with that answer id;
* **whether an execution contradicts a receipt** — an executed probe on the receipt's own level whose transition
  disagrees with the evidence receipt it names fails every chapter resting on that receipt closed (R8, basis
  PROVENANCE_INCOMPLETE).

Revision 3 (2026-10-18, Sol's level-scoping correction): executions are joined by ``(level, evidence_id)``. Receipts
and dossiers are level-scoped and deterministic evidence ids may recur, so a row of another level never verifies,
duplicates or contradicts anything on this one; there is no cross-level fallback.

Live and H1 models carry no final provenance: ``PENDING``, executor and submitter ``null``. At H2 a missing,
unreadable or ambiguous record gives ``FAILED_CLOSED`` and a typed ``PROVENANCE_INCOMPLETE`` open item, while the
witness and mechanic facts stay. ``reconcile`` runs once per seal (``world_model_v2.seal``) and recomputes from
scratch, so sealing a sealed model again changes nothing; the validator recomputes the same functions.

The same seal-time pass refreshes every anatomy channel's event links from the level's stored description
(``lever_dossier_links``): H2's record check can rewrite a frozen level's description after its H1 freeze, and a
link must always be one the stored description supports.
"""
from __future__ import annotations

import copy
from typing import Any, Mapping, Sequence

from inference.framework import lever_dossier_facts as F
from inference.framework import lever_dossier_links as L

PENDING = F.PROVENANCE_PENDING
INCOMPLETE = "PROVENANCE_INCOMPLETE"
RELATIONS = "G4-B-LEVER-RELATIONS"
STATUSES = ("VERIFIED", "PENDING", "FAILED_CLOSED")
CHOOSER_BASES = ("G3_SELECTION_EVENT", "G3_COVERAGE_ORDER", "NOT_RECORDED")
ACTOR_KEYS = ("chooser", "chooser_basis", "executor", "status", "basis", "execution_event_id")
SUBMISSION_KEYS = ("submission_source", "certifier", "certification_origin", "status", "basis", "answer_event_id")


class Context:
    """What the model's provenance chapter makes final: the H2 journal's executed probes and admitted answers."""

    def __init__(self, chapter: Mapping[str, Any] | None) -> None:
        chapter = chapter or {}
        self.final = chapter.get("phase") == "H2"
        self.readable = self.final and chapter.get("integrity") != "UNAVAILABLE"
        self.executions: dict[tuple, list[Mapping[str, Any]]] = {}  # (level, evidence_id) -> executed probes
        self.answers: dict[tuple, list[Mapping[str, Any]]] = {}
        for row in (chapter.get("rows") or ()) if self.final else ():
            refs = row.get("refs") or {}
            kind = (row.get("operation"), row.get("event"), row.get("disposition"))
            if kind == ("PROBE", "EXECUTION", "EXECUTED"):
                self.executions.setdefault((row.get("level"), str(refs.get("evidence_id"))), []).append(row)
            elif kind == ("ANSWER", "ADMISSION", "ADMITTED"):
                self.answers.setdefault((row.get("level"), row.get("gate_id"), refs.get("answer_id")), []).append(row)

    def rows(self, level: Any, evidence: Any) -> list[Mapping[str, Any]]:
        """The executed probes on ``level`` that name ``evidence`` (never a row of another level)."""
        return self.executions.get((level, str(evidence)), [])

    def contradicted(self, level: Mapping[str, Any]) -> set[str]:
        """The level's evidence receipts that an executed probe on the same level names with another transition."""
        out = set()
        for ref, receipt in ((level.get("receipts") or {}).get("evidence") or {}).items():
            for row in self.rows(level.get("level"), ref):
                if (row.get("refs") or {}).get("executed_transition") != receipt.get("transition_id"):
                    out.add(str(ref))
        return out


# ---- the actor of a G3 activation (identity) ---------------------------------------------------------------------

def chooser(selected: Sequence[Any], activation: Mapping[str, Any] | None) -> tuple[str | None, str]:
    """The G3 selection event's actor when one chose the lever; the coverage order when G3 discovered it unchosen."""
    if selected:
        return str(selected[-1]), "G3_SELECTION_EVENT"
    return ("CONTROLLER", "G3_COVERAGE_ORDER") if activation is not None else (None, "NOT_RECORDED")


def pending_actor(who: str | None, basis: str) -> dict[str, Any]:
    return {"chooser": who, "chooser_basis": basis, "executor": None, "status": "PENDING", "basis": PENDING,
            "execution_event_id": None}


def actor_evidence(facts: Mapping[str, Any]) -> str | None:
    """The witness evidence of the activation: G3's own discovery reference, else the lever's first witness."""
    activation = facts.get("activation") or {}
    if activation.get("witness_evidence_ref"):
        return str(activation["witness_evidence_ref"])
    witnesses = sorted(facts.get("witnesses") or (), key=lambda row: (row.get("transition_id"), row.get("witness_id")))
    return str(witnesses[0]["evidence_ref"]) if witnesses and witnesses[0].get("evidence_ref") else None


def attest_actor(actor: Mapping[str, Any], evidence: str | None, level: Any, context: Context) -> dict[str, Any]:
    """The executor, from the one executed probe on the dossier's own ``level`` that names ``evidence``."""
    out = pending_actor(actor.get("chooser"), actor.get("chooser_basis"))
    if not context.final:
        return out
    rows = context.rows(level, evidence) if evidence else []
    if evidence is None:
        basis = "NO_WITNESS_EVIDENCE"
    elif not context.readable:
        basis = "JOURNAL_UNAVAILABLE"
    elif not rows:
        basis = "EXECUTION_MISSING"
    elif len(rows) > 1:
        basis = "EXECUTION_DUPLICATED"
    else:
        return {**out, "executor": rows[0].get("executor"), "status": "VERIFIED", "basis": "EVIDENCE_LINKED_EXECUTION",
                "execution_event_id": rows[0].get("event_id")}
    return {**out, "status": "FAILED_CLOSED", "basis": basis}


# ---- the submitter of a G4-B answer (relations) -----------------------------------------------------------------

def attest_submission(stored: Mapping[str, Any] | None, answer_id: Any, level: Any, context: Context) -> Any:
    if stored is None or stored.get("submission_source") == "RECORD":
        return None if stored is None else dict(stored)
    out = {**dict(stored), "submission_source": None, "status": "PENDING", "basis": PENDING, "answer_event_id": None}
    if not context.final:
        return out
    rows = context.answers.get((level, RELATIONS, answer_id), [])
    basis = ("JOURNAL_UNAVAILABLE" if not context.readable else "ANSWER_ADMISSION_MISSING" if not rows
             else "ANSWER_ADMISSION_AMBIGUOUS" if len(rows) > 1 else None)
    if basis is not None:
        return {**out, "status": "FAILED_CLOSED", "basis": basis}
    return {**out, "submission_source": rows[0].get("executor"), "status": "VERIFIED", "basis": "ANSWER_ADMISSION",
            "answer_event_id": rows[0].get("event_id")}


# ---- typed open items --------------------------------------------------------------------------------------------

def open_items(name: str, chapter: Mapping[str, Any]) -> list[dict[str, Any]]:
    """The chapter's PROVENANCE_INCOMPLETE items, from its own content (the validator recomputes them)."""
    integrity = chapter.get("integrity") or {}
    if integrity.get("status") == "FAILED_CLOSED" and integrity.get("reasons") == [INCOMPLETE]:
        return [{"kind": INCOMPLETE, "field": "EVIDENCE_EXECUTION", "basis": "EXECUTION_EVIDENCE_DISAGREES",
                 "refs": list(integrity.get("refs") or ())}]
    facts = chapter.get("facts") or {}
    if name == "identity" and (facts.get("actor") or {}).get("status") == "FAILED_CLOSED":
        return [{"kind": INCOMPLETE, "field": "ACTIVATION_EXECUTOR", "basis": facts["actor"]["basis"],
                 "evidence_ref": actor_evidence(facts)}]
    if name == "relations" and (facts.get("submission") or {}).get("status") == "FAILED_CLOSED":
        return [{"kind": INCOMPLETE, "field": "ANSWER_SUBMITTER", "basis": facts["submission"]["basis"],
                 "answer_id": (facts.get("description") or {}).get("answer_id")}]
    return []


# ---- the reconciliation, once per seal ---------------------------------------------------------------------------

def _unlabel(chapter: dict) -> None:
    """A census label is reapplied after a failure, so the failure keeps the status the work itself had."""
    if chapter["integrity"]["status"] == "OK" and chapter["prior_status"] is not None:
        chapter.update(status=chapter["prior_status"], basis=chapter["prior_basis"], prior_status=None, prior_basis=None)


def reconcile_dossier(entity_id: str, dossier: dict, level: Mapping[str, Any], context: Context,
                      contradicted: set[str]) -> None:
    from inference.framework import lever_dossiers as D

    chapters = dossier["chapters"]
    for name in F.CHAPTERS[:-1]:
        hit = sorted(set(chapters[name]["evidence_refs"]) & contradicted)
        if hit and chapters[name]["integrity"]["status"] == "OK":
            _unlabel(chapters[name])
            D.fail_closed(chapters[name], INCOMPLETE, hit)
    identity, relations, anatomy = chapters["identity"], chapters["relations"], chapters["anatomy"]
    anatomy["facts"] = L.link_anatomy(anatomy["facts"], level)  # the description the model stores now
    if identity["facts"] is not None and identity["facts"].get("actor") is not None:
        identity["facts"]["actor"] = attest_actor(identity["facts"]["actor"], actor_evidence(identity["facts"]),
                                                  level.get("level"), context)
    if relations["facts"] is not None:
        answer_id = (relations["facts"].get("description") or {}).get("answer_id")
        relations["facts"]["submission"] = attest_submission(relations["facts"].get("submission"), answer_id,
                                                             level.get("level"), context)
    for name in F.CHAPTERS[:-1]:
        chapter = chapters[name]
        chapter["open"] = [item for item in chapter["open"] if item.get("kind") != INCOMPLETE] + open_items(name, chapter)
    D.reseal(entity_id, dossier, level)


def reconcile(payload: Mapping[str, Any]) -> dict[str, Any]:
    """The payload with every dossier's provenance-dependent facts made final (H2) or pending (live, H1)."""
    context = Context(payload.get("provenance"))
    levels = []
    for level in payload.get("levels") or ():
        if not level.get("lever_dossiers"):
            levels.append(level)
            continue
        level = dict(level)
        dossiers = copy.deepcopy(level["lever_dossiers"])
        contradicted = context.contradicted(level)
        for entity_id, dossier in dossiers.items():
            reconcile_dossier(entity_id, dossier, level, context, contradicted)
        level["lever_dossiers"] = dossiers
        levels.append(level)
    return {**payload, "levels": levels}


__all__ = ["ACTOR_KEYS", "CHOOSER_BASES", "Context", "INCOMPLETE", "PENDING", "STATUSES", "SUBMISSION_KEYS",
           "actor_evidence", "attest_actor", "attest_submission", "chooser", "open_items", "pending_actor",
           "reconcile", "reconcile_dossier"]
