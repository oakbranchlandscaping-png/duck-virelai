"""The gate agenda: the library's open questions, derived cheaply from gate-owned state (WO-G3-DIRECTED).

Author: Claude (Alpha build seat), 2026-10-11. Design: ``INTERFACE_WO_G3_DIRECTED_LIBRARY_TARGET`` v2 §2 (Sol's
review of v1, relayed by the Director): "Proceed with the split, gate-owned agenda design ... G3 must supply its
own eligibility list."

Two projections share one question vocabulary:

- **this gate agenda** is computed from the gate machine's own state (target journal, registry, G3 lifecycle and
  ``admission_candidates``, G4 adapters) in well under a millisecond, so it can run on every controller step. It
  is the only source of the selected question and of its binding;
- the **census** (``library_census``) is compiled on Duck turns and at H1/H2 checkpoints and adds object context.
  ``census_agreement`` checks the two agree on every subject both cover.

Nothing here writes: no role, witness, law, product or file. It never calls a gate's ``_ensure_*`` or
``next_probe`` (both can advance gate state); the machine is byte-identical after a call. A question that cannot
be derived from gate state stays open or typed; ``NOT_BUILT`` chapters are listed and never selectable.

G4 per-lever questions open with the witness, but stay ``BLOCKED_BY_PREREQUISITE`` until the G3
``LeverInventory`` product is active (Sol, 2026-10-11): a witness admits the lever; the inventory admits G4.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

SCHEMA = "virelai-library-agenda-v1"
G3 = "G3-LEVERS"
PLAY = "PLAY-NORMAL"
G4_GATES = ("G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW")

# One question per gate, in ruling 22's sharpened wording.
GATE_QUESTIONS = {
    "G0-ACTION-METADATA": ("ACTION_SURFACE", "Which actions does this world offer, and which take coordinates?"),
    "G1-EGO": ("CONTROL_LOCUS", "Where is the control locus: what do actions move or select?"),
    "G2-COUNTER": ("COUNTER", "Which object is the counter, and what changes it?"),
    G3: ("LEVER_INVENTORY", "Which objects are levers: what responds when the ego acts on it?"),
    "G4-REACTIONS": ("LEVER_EFFECTS", "What does each lever's activation change?"),
    "G4.2-LEVER-ORBITS": ("LEVER_ORBITS", "Which states does each lever move through when pressed repeatedly?"),
    "G4-B-LEVER-RELATIONS": ("LEVER_RELATIONS", "How do the levers' effects relate to one another?"),
    "G4-C-LEVER-LAW": ("LEVER_LAW", "Which law, stated for the boards tested, governs the levers together?"),
    PLAY: ("FREE_PLAY", "No gate can act on this level: every action is recorded as FREE_PLAY, never as gated."),
}
G4_CHAPTERS = (
    ("G4-REACTIONS", "EFFECTS", "What does activating this lever change?"),
    ("G4.2-LEVER-ORBITS", "ORBIT", "Which states does this lever move through when pressed repeatedly?"),
    ("G4-B-LEVER-RELATIONS", "RELATIONS", "How does this lever's effect relate to the other levers?"),
    ("G4-C-LEVER-LAW", "LAW", "Which law covers this lever together with the others?"),
)
NOT_BUILT = (
    ("ENVIRONMENTAL_FORCE", "Does any environmental force act on this level?"),
    ("REACTIVE_DRIVEN", "Which objects are driven by another object?"),
    ("SCOPED_NEGATIVES", "What was shown not to happen, and under what scope?"),
    ("INERT", "Is any object coverage-certified INERT?"),
    ("BAND1", "Which objects are STATIC or REACTIVE under the animation law?"),
)
LIFECYCLE_DISPOSITION = {
    "UNTOUCHED": "OPEN", "REOPENED": "OPEN", "ATTEMPTED": "OPEN_IN_PROGRESS", "RESPONDED": "OPEN_IN_PROGRESS",
    "NO_RESPONSE_YET": "OPEN_IN_PROGRESS", "WITNESSED": "ANSWERED_LEVER", "G4-READY": "ANSWERED_LEVER",
    "AMBIGUOUS": "INCONCLUSIVE", "BUDGET_STOPPED": "BUDGET_LIMITED", "PRESUMED_UNREACHABLE": "REACHABILITY_LIMITED",
    "FILED_TO_G5": "NOT_BUILT",
}
SELECTABLE = frozenset({"OPEN_ACTIONABLE", "OBLIGATION"})
OBLIGATION_KINDS = {"CONFIRMATION": "CONFIRM_WITNESS", "DOSSIER": "DOSSIER_ANSWER",
                    "REACHABILITY": "REACHABILITY_ANSWER", "MU_REVISIT": "MU_REVISIT",
                    "REOPENED_REACHABILITY": "REOPENED_REACHABILITY"}


# A G4-B/G4-C product's own status (g4b_gate.py:353, g4c_gate.py:264), read as a disposition: only COMPLETE
# answers the question; an unresolved or boundary close is a typed, closed question (Sol's review, 2026-10-11).
PRODUCT_STATUS = {"COMPLETE": "ANSWERED", "UNRESOLVED": "CLOSED_UNRESOLVED",
                  "CLOSED_BY_LEVEL_BOUNDARY": "CLOSED_BY_LEVEL_BOUNDARY"}


def _product_disposition(product: Any) -> str:
    status = (product.payload or {}).get("status") if product is not None else None
    return "ANSWERED" if status is None else PRODUCT_STATUS.get(str(status), f"PRODUCT_{status}")


def question_id(level: int, gate: str, subject: str, kind: str) -> str:
    """The stable question identity: game-local, level-scoped, by subject and kind (never by revision)."""
    return f"Q:L{int(level)}:{gate}:{subject}:{kind}"


def lever_question_id(level: int, entity_id: str) -> str:
    return question_id(level, G3, entity_id, "IS_LEVER")


def _question(level: int, gate: str | None, subject: str, kind: str, text: str, disposition: str,
              **extra: Any) -> dict[str, Any]:
    return {"id": question_id(level, gate or "LIBRARY", subject, kind), "gate": gate, "subject": subject,
            "kind": kind, "question": text, "disposition": disposition, **extra}


def _gate_questions(machine: Any, level: int) -> list[dict[str, Any]]:
    journal, current, questions = machine.target_journal, machine.gate_id, []
    for contract in machine.target_registry.ordered():
        gate = contract.target_id
        kind, text = GATE_QUESTIONS.get(gate, ("GATE", f"Answer {gate}."))
        missing = [item for item in contract.prerequisites if journal.active_product(item) is None]
        product = journal.active_product(gate)
        if product is not None:
            disposition = _product_disposition(product)
        elif gate == current:  # the gate the machine is in (a forced rest in PLAY-NORMAL included)
            disposition = "OPEN_FALLBACK" if gate == PLAY else "OPEN_ACTIONABLE"
        elif missing:
            disposition = "BLOCKED_BY_PREREQUISITE"
        else:
            disposition = "OPEN"
        questions.append(_question(level, gate, f"LEVEL-{level}", kind, text, disposition,
                                   prerequisites_missing=missing,
                                   product_id=None if product is None else product.product_id))
    return questions


def _g3_questions(machine: Any, level: int) -> tuple[list[dict[str, Any]], dict[str, Any] | None, list[dict[str, Any]]]:
    adapter = (getattr(machine, "_adapters", None) or {}).get(G3)
    ledger = getattr(adapter, "entity_ledger", None)
    lifecycle = getattr(adapter, "lifecycle_journal", None)
    if adapter is None or ledger is None or lifecycle is None:
        return [], None, []
    from inference.framework import g3_selection

    candidates = list(g3_selection.admission_candidates(adapter)) if machine.gate_id == G3 else []
    selectable = {row["entity_id"]: row for row in candidates if row.get("selectable")}
    terrain = getattr(adapter, "_terrain_roles", None) or {}
    questions = []
    for entity_id, item in sorted(lifecycle.entities.items()):
        if item.witness_refs:  # a witness admits a lever whatever else was observed of it
            disposition = "ANSWERED_LEVER"
        elif entity_id in terrain:
            disposition = "ANSWERED_TERRAIN"
        elif item.state == "G3-CLOSED":
            disposition = "ANSWERED_SCOPED_NULL"
        else:
            disposition = LIFECYCLE_DISPOSITION.get(item.state, "OPEN")
        if entity_id in selectable and disposition in {"OPEN", "OPEN_IN_PROGRESS"}:
            disposition = "OPEN_ACTIONABLE"
        hypothesis = ledger.entities.get(entity_id)
        questions.append(_question(
            level, G3, entity_id, "IS_LEVER", "Is this object a lever: does it respond when the ego acts on it?",
            disposition, lifecycle_state=item.state, evidence_refs=list(item.witness_refs)[-3:],
            binding={"entity_version": None if hypothesis is None else hypothesis.version,
                     "member_id": (selectable.get(entity_id) or {}).get("member_id")},
        ))
    return questions, g3_selection.obligation(adapter), candidates


def _g4_questions(machine: Any, level: int, levers: list[str]) -> list[dict[str, Any]]:
    journal = machine.target_journal
    inventory = journal.active_product(G3)
    adapters = getattr(machine, "_adapters", None) or {}
    answered = {
        "G4-REACTIONS": set(getattr(adapters.get("G4-REACTIONS"), "_answers", None) or ()),
        "G4.2-LEVER-ORBITS": set(getattr(adapters.get("G4.2-LEVER-ORBITS"), "_completed", None) or ()),
    }
    relations = journal.active_product("G4-B-LEVER-RELATIONS")
    pressed = set((relations.payload.get("pressed_levers") or ()) if relations is not None else ())
    law = journal.active_product("G4-C-LEVER-LAW")
    questions = []
    for entity_id in levers:
        for gate, kind, text in G4_CHAPTERS:
            if inventory is None:
                disposition = "BLOCKED_BY_PREREQUISITE"  # a witness admits the lever; the inventory admits G4
            elif gate == "G4-C-LEVER-LAW":
                disposition = "OPEN" if law is None else _product_disposition(law)
            elif gate == "G4-B-LEVER-RELATIONS":
                disposition = _relations_disposition(relations, entity_id in pressed)
            else:
                disposition = "ANSWERED" if entity_id in answered[gate] else "OPEN"
            questions.append(_question(level, gate, entity_id, kind, text, disposition,
                                       prerequisites_missing=[] if inventory is not None else [G3]))
    return questions


def _relations_disposition(product: Any, pressed: bool) -> str:
    """G4-B per lever: COMPLETE answers every lever; an unresolved close leaves pressed levers partial."""
    if product is None:
        return "OPEN"
    disposition = _product_disposition(product)
    if disposition == "CLOSED_UNRESOLVED" and pressed:
        return "PARTIAL_CLOSED_UNRESOLVED"
    return disposition


def _selected(machine: Any, level: int, gates: list[dict[str, Any]], obligation: dict[str, Any] | None,
              candidates: list[dict[str, Any]]) -> str | None:
    current = machine.gate_id
    if current == G3:
        if obligation is not None:
            return question_id(level, G3, str(obligation["entity_id"]), OBLIGATION_KINDS[obligation["kind"]])
        adapter = machine._adapters[G3]
        selection = getattr(adapter, "_selection", None)
        if selection is not None and any(row["entity_id"] == selection["entity_id"] for row in candidates):
            return str(selection["question_id"])
        if candidates:
            return lever_question_id(level, candidates[0]["entity_id"])
    current_question = next((q for q in gates if q["gate"] == current), None)
    if current_question is not None and current_question["disposition"] != "BLOCKED_BY_PREREQUISITE":
        return current_question["id"]
    return None


def _revision(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:12]


def gate_agenda(machine: Any) -> dict[str, Any]:
    """The open questions of the current level, their dispositions and the one selected question."""
    level = int(machine.lives.level)
    gates = _gate_questions(machine, level)
    g3, obligation, candidates = _g3_questions(machine, level)
    levers = [q["subject"] for q in g3 if q["disposition"] == "ANSWERED_LEVER"]
    g4 = _g4_questions(machine, level, levers)
    library = [_question(level, None, f"LEVEL-{level}", chapter, text, "NOT_BUILT") for chapter, text in NOT_BUILT]
    owed = []
    if obligation is not None and machine.gate_id == G3:  # the gate's own pending work comes first
        kind = OBLIGATION_KINDS[obligation["kind"]]
        owed = [_question(level, G3, str(obligation["entity_id"]), kind,
                          f"Finish the gate's {obligation['kind'].lower().replace('_', ' ')} for this object.",
                          "OBLIGATION")]
    questions = gates + owed + g3 + g4 + library
    selected = _selected(machine, level, gates, obligation, candidates)
    eligible = [q["id"] for q in g3 if q["disposition"] == "OPEN_ACTIONABLE"]
    agenda = {
        "schema": SCHEMA, "level": level, "life": int(machine.lives.life), "gate": machine.gate_id,
        "questions": questions, "selected": selected, "eligible": eligible,
        "obligation": obligation,
        "counts": {"questions": len(questions),
                   "unresolved": sum(1 for q in questions if not q["disposition"].startswith("ANSWERED")),
                   "not_built": len(library)},
    }
    agenda["agenda_revision"] = _revision({key: agenda[key] for key in ("questions", "selected", "obligation")})
    return agenda


def selected_question(machine: Any) -> str | None:
    return gate_agenda(machine)["selected"]


def selected_target(machine: Any) -> dict[str, Any]:
    """The selected question as the digest shows it: id, gate, subject, question and disposition."""
    agenda = gate_agenda(machine)
    question = next((q for q in agenda["questions"] if q["id"] == agenda["selected"]), None)
    if question is None:
        return {"question_id": None, "gate_id": agenda["gate"], "level": agenda["level"],
                "question": "No question is selectable now.", "disposition": None,
                "agenda_revision": agenda["agenda_revision"]}
    return {"question_id": agenda["selected"], "gate_id": question["gate"], "subject": question["subject"],
            "level": agenda["level"], "question": question["question"], "disposition": question["disposition"],
            "agenda_revision": agenda["agenda_revision"]}


def census_agreement(agenda: Mapping[str, Any], model: Mapping[str, Any]) -> dict[str, tuple[list[str], list[str]]]:
    """Where the gate agenda and the validated census disagree on a subject both cover; empty when they agree."""
    level = next((item for item in model["levels"] if item["level"] == agenda["level"]), None)
    if level is None:
        return {"level": ([str(agenda["level"])], [])}
    g3: dict[str, set[str]] = {}
    for q in agenda["questions"]:
        if q["gate"] == G3 and q["kind"] == "IS_LEVER":
            g3.setdefault(q["disposition"], set()).add(q["subject"])

    def gaps(reason: str, source: str = "") -> set[str]:
        return {gap["subject"] for gap in level["gaps"] if gap["reason"] == reason
                and gap["archetype_question"] == "Is this object a lever?" and source in gap["source"]}

    pairs = {
        "lever": (g3.get("ANSWERED_LEVER", set()),
                  {role["entity_id"] for role in level["certified"]["roles"] if role["role"] == "LEVER"}),
        "scoped_null": (g3.get("ANSWERED_SCOPED_NULL", set()),
                        {item["entity_id"] for item in level["certified"]["scoped_nulls"]}),
        "terrain": (g3.get("ANSWERED_TERRAIN", set()),
                    {item["entity_id"] for item in level["observation"]["terrain"]}
                    - {role.get("entity_id") for role in level["certified"]["roles"]}),
        "inconclusive": (g3.get("INCONCLUSIVE", set()), gaps("INCONCLUSIVE")),
        "budget": (g3.get("BUDGET_LIMITED", set()), gaps("BUDGET")),
        "unreachable": (g3.get("REACHABILITY_LIMITED", set()), gaps("NOT_REACHED", "PRESUMED_UNREACHABLE")),
        "no_response_yet": ({q["subject"] for q in agenda["questions"] if q.get("lifecycle_state") == "NO_RESPONSE_YET"
                             and q["disposition"] != "ANSWERED_LEVER"},
                            gaps("NOT_REACHED", "NO_RESPONSE_YET")),
    }
    certified = {row["gate_id"]: row["disposition"] for row in level["certified"]["gates"]}
    pairs["certified_gates"] = ({q["gate"] for q in agenda["questions"] if q["subject"] == f"LEVEL-{agenda['level']}"
                                 and q["gate"] and q.get("product_id")},
                                {gate for gate, disposition in certified.items() if disposition == "CERTIFIED"})
    return {name: (sorted(a - b), sorted(b - a)) for name, (a, b) in pairs.items() if a != b}


__all__ = ["GATE_QUESTIONS", "NOT_BUILT", "PRODUCT_STATUS", "SCHEMA", "census_agreement", "gate_agenda",
           "lever_question_id", "question_id", "selected_question", "selected_target"]
