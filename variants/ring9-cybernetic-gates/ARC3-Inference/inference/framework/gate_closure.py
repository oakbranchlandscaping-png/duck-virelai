"""Close only the selected question or gate CLOSED_UNRESOLVED, and continue the ladder (WO-RUNTIME-01 §5).

Author: Claude (Alpha build seat), 2026-10-20. Base ``73f13d1``. Interface v2 §5.4 (per-gate closures, accepted) and
v3 §3 (closure scope), Director rulings B, Q1, Q2 and Q3 (the cascade rule).

A closed gate emits a product of its normal type whose payload states ``status: "UNRESOLVED"`` and an
``unresolved_reason``, the established G4-B/G4-C pattern (``g4b_gate.close_unresolved``): the router skips a gate with
an active product, so the next gate is built; accepted products and evidence are never invalidated. A downstream gate
closes ``UPSTREAM_UNRESOLVED`` only when it is structurally unbuildable from what it receives (no lever, no anatomy).

Scope by question (``library_agenda.question_id``):

* a gate-level question (``LEVEL-n``): the gate;
* a G3 entity question: that entity only, through G3's own bounded stop (``BUDGET_STOPPED``, ``_bound_ambiguity``);
* a G4.1 or G4.2 lever chapter: that chapter only (``chapter_closure``, Director ruling 1 of revision 2); the gate
  keeps studying every other lever and settles with a partial product;
* a ``LIMITS`` experiment question: nothing to close (the controller runs experiments; a declined choice resumes
  coverage).
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Mapping

G0, G1, G2, G3 = "G0-ACTION-METADATA", "G1-EGO", "G2-COUNTER", "G3-LEVERS"
G41, G42, G4B, G4C, PLAY = "G4-REACTIONS", "G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW", "PLAY-NORMAL"
UNRESOLVED = "UNRESOLVED"
UPSTREAM = "UPSTREAM_UNRESOLVED"
SETTLED_G3 = frozenset({"G3-CLOSED", "G4-READY", "BUDGET_STOPPED", "FILED_TO_G5", "PRESUMED_UNREACHABLE"})


@dataclass(frozen=True)
class Closure:
    status: str  # CLOSED | NOTHING_TO_CLOSE
    scope: str  # GATE | ENTITY | CHAPTER | EXPERIMENT | NONE
    gate_id: str | None
    subject: str | None = None
    cascaded: tuple[str, ...] = field(default=())


def _sha(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()[:16]


def parse(question_id: str | None) -> tuple[int, str, str, str] | None:
    parts = str(question_id or "").split(":")
    if len(parts) != 5 or parts[0] != "Q" or not parts[1].startswith("L"):
        return None
    try:
        return int(parts[1][1:]), parts[2], parts[3], parts[4]
    except ValueError:
        return None


def phase1_hold_reason(payload: Mapping[str, Any]) -> str | None:
    """Why Phase 2 (G4-B onward) may not open yet, or None (moved from ``virelai_gates``; WO-RUNTIME-01 adds the
    first line: a G4.2 closed CLOSED_UNRESOLVED releases its hold, so its unresolved close reaches G4-B)."""
    if payload.get("phase1_status") in (UNRESOLVED, "SETTLED_WITH_GAPS"):  # r3: settled with gaps, never COMPLETE
        return None
    if payload.get("pending_lever_entities"):
        return "Phase 1 is incomplete."
    if payload.get("phase1_status") == "CLOSED_BY_LEVEL_BOUNDARY":
        return "the level changed during Phase 1; cross-level work belongs to the G9 gate."
    if not payload.get("lever_entities"):
        return "no lever completed Phase 1 on this level."
    return None


# ---- the scope of one question -----------------------------------------------------------------------------------

def close_question(machine: Any, question_id: str | None, reason: str, history: tuple | list = (),
                   cause: str | None = None) -> Closure:
    parsed = parse(question_id)
    if parsed is None:
        return Closure("NOTHING_TO_CLOSE", "NONE", getattr(machine, "gate_id", None))
    _level, gate, subject, _kind = parsed
    if gate == "LIBRARY":
        return Closure("NOTHING_TO_CLOSE", "EXPERIMENT", G4B, subject)
    if gate in (G41, G42) and not subject.startswith("LEVEL-"):
        return _close_chapter(machine, gate, subject, question_id, reason, history, cause)
    if gate == G3 and not subject.startswith("LEVEL-"):
        return _close_g3_entity(machine, subject, reason)
    if gate in (PLAY, G0) or machine.target_journal.active_product(gate) is not None:
        return Closure("NOTHING_TO_CLOSE", "NONE", gate, subject)
    return close_gate(machine, gate, reason)


def close_gate(machine: Any, gate: str, reason: str) -> Closure:
    """Close ``gate`` CLOSED_UNRESOLVED (a product of its own type), then cascade only through unbuildable gates."""
    _CLOSERS[gate](machine, reason)
    return Closure("CLOSED", "GATE", gate, None, tuple(cascade(machine)))


def cascade(machine: Any) -> list[str]:
    """Close every following gate that cannot be built from the unresolved result it receives (Q3's rule)."""
    closed: list[str] = []
    while machine.target_router.current() is not None:
        gate = machine.target_router.current().target_id
        if gate not in (G41, G42, G4B, G4C) or not _unbuildable(machine, gate):
            break
        _CLOSERS[gate](machine, f"{UPSTREAM}: nothing to build {gate} from")
        closed.append(gate)
    return closed


def _payload(machine: Any, gate: str) -> Mapping[str, Any]:
    product = machine.target_journal.active_product(gate)
    return product.payload if product is not None and isinstance(product.payload, Mapping) else {}


def _unbuildable(machine: Any, gate: str) -> bool:
    if gate == G41:
        return not _payload(machine, G3).get("lever_entities")
    if gate in (G42, G4B):
        return not _payload(machine, G41).get("anatomies")
    return not _payload(machine, G4B).get("lever_entities")


def _put(machine: Any, gate: str, product_type: str, product_id: str, revision: int, payload: dict,
         dependencies: tuple[str, ...]) -> None:
    from inference.framework.cybernetic_targeting import MemoryProduct

    machine.target_journal.put(MemoryProduct(product_id=product_id, product_type=product_type, target_id=gate,
                                             revision=revision, payload=payload, dependencies=dependencies))


# ---- the gates ---------------------------------------------------------------------------------------------------

def _close_g1(machine: Any, reason: str) -> None:
    """G1: an EgoLaw-shaped product that certifies nothing; G2's input is still prepared from G1's board."""
    ego = machine.ego
    machine._prepare_counter_from_ego()
    ego.closed_unresolved = reason
    law_id = "G1-UNRESOLVED-" + _sha({"reason": reason, "revision": ego.revision, "at": machine.observed_through_step})
    payload = {"law_id": law_id, "law_version_id": law_id, "revision": int(ego.revision), "status": UNRESOLVED,
               "parent_law_version_id": None, "mode": UNRESOLVED, "subjects": [], "opaque_action_laws": [],
               "conditions": [], "constraints": [], "evidence_refs": [str(item.get("evidence_id")) for item in
                                                                       getattr(ego, "evidence", ()) or ()
                                                                       if isinstance(item, Mapping)
                                                                       and item.get("evidence_id")],
               "demonstration_ref": "", "competing_models": [], "falsifier": "", "limitations": [reason],
               "witness_transition_ids": [], "contradiction_transition_ids": [], "unresolved_reason": reason}
    _put(machine, G1, "EgoLaw", law_id, int(ego.revision), payload, (G0,))


def _close_g2(machine: Any, reason: str) -> None:
    """G2: no model and no mask; the plausible counter candidates and their exclusion region travel to G3 (Q3)."""
    from inference.framework import counter_exclusion

    counter = machine.counter
    roster = counter_exclusion.plausible(counter)
    region = sorted({tuple(cell) for item in roster for cell in item["footprint"]})
    counter.status, counter.stop_reason, counter.closed_unresolved = UNRESOLVED, reason, reason
    product_id = "COUNTER-UNRESOLVED-" + _sha({"reason": reason, "revision": counter.revision, "roster": roster})
    payload = {"product_kind": "COUNTER_UNRESOLVED", "status": UNRESOLVED, "unresolved_reason": reason,
               "counter_model": None, "mask_law": None, "boundary_obligation": counter.boundary_obligation,
               "search_disposition": counter.search_disposition, "derived_period_actions": None,
               "ranked_object_frontier": counter.sweep_frontier(), "state_identity": None,
               "plausible_counter_candidates": roster, "counter_exclusion_region": [list(cell) for cell in region]}
    _put(machine, G2, "CounterGateProduct", product_id, int(counter.revision), payload, (G1,))


def _close_g3(machine: Any, reason: str) -> None:
    """G3: the G4-ready levers only (each with its witness); every other entity is listed by its lifecycle state."""
    from inference.framework import mu_return

    g3 = machine._adapters[G3]
    g3._ensure_entity_ledger()
    journal = g3.lifecycle_journal
    states = {entity: journal.entities[entity].state for entity in sorted(journal.entities)}
    levers = [entity for entity, state in states.items() if state == "G4-READY"]
    payload = {"answer": None, "probe_protocol": g3._complete_reason, "lever_entities": levers,
               "clean_null_entities": [e for e, s in states.items() if s == "G3-CLOSED"],
               "ambiguous_entities": [e for e, s in states.items() if s in {"AMBIGUOUS", "BUDGET_STOPPED",
                                                                           "PRESUMED_UNREACHABLE"}],
               "unresolved_entities": [e for e, s in states.items() if s not in SETTLED_G3 and s != "AMBIGUOUS"],
               "closure": UNRESOLVED, "status": UNRESOLVED, "unresolved_reason": reason,
               "ranked_target_count": len(g3._ensure_frontier()), "frontier_accounting": g3._frontier_snapshot(),
               "lifecycle_journal": journal.snapshot()}
    g3.closed_unresolved = reason
    mu_return.settle_after_inventory(g3)
    _put(machine, G3, "LeverInventory", "G3-UNRESOLVED-" + _sha({"reason": reason, "states": states}),
         int(g3.revision), payload, (G2,))
    g3.revision += 1


def _close_g3_entity(machine: Any, entity: str, reason: str) -> Closure:
    """One G3 entity only: G3's own bounded stop, its pending obligation released; coverage moves past it."""
    from inference.framework import g3_selection

    g3 = machine._adapters[G3]
    journal, ledger = g3.lifecycle_journal, g3.entity_ledger
    if journal is None or ledger is None or entity not in journal.entities \
            or journal.entities[entity].state in SETTLED_G3:
        return Closure("NOTHING_TO_CLOSE", "ENTITY", G3, entity)
    members = sorted(member for member, owner in ledger.member_to_entity.items() if owner == entity)
    for name, key in (("_pending_confirmation", "entity_id"), ("_pending_dossier", "entity_id"),
                      ("_pending_reachability", "target_entity_id")):
        pending = getattr(g3, name, None)
        if isinstance(pending, Mapping) and str(pending.get(key) or "") == entity:
            setattr(g3, name, None)
    if entity in (getattr(g3, "_mu_revisit", None) or []):
        g3._mu_revisit.remove(entity)
    g3._bound_ambiguity(member_id=members[0] if members else entity, entity_id=entity,
                        evidence_ref=f"RECOVERY:{reason}", disposition=reason, terminal_state="BUDGET_STOPPED",
                        reason=f"closed CLOSED_UNRESOLVED by the runtime recovery ({reason}); no inertness is claimed")
    head = g3._eligible_frontier[g3._target_index]["member_id"] \
        if g3._eligible_frontier and g3._target_index < len(g3._eligible_frontier) else None
    selection = getattr(g3, "_selection", None)
    if head in members or (selection is not None and selection.get("member_id") in members):
        g3_selection.finish_target(g3, head if head in members else selection["member_id"])
    g3.revision += 1
    return Closure("CLOSED", "ENTITY", G3, entity)


def _close_g41(machine: Any, reason: str) -> None:
    """A seeded G4.1 closes chapter by chapter (r2: explicit rows, the answered kept); an unbuildable one, empty."""
    from inference.framework.g4_reactions import anatomy_payload

    reactions = machine._adapters[G41]
    if not _unbuildable(machine, G41):
        _close_chapters(machine, G41, reason, reactions._emit_anatomy_product)
        return
    entities = list(getattr(reactions, "_ordered_entities", ()) or ())
    anatomies = [anatomy_payload(reactions._anatomies[e]) for e in entities if e in reactions._anatomies]
    answers = [asdict(reactions._answers[e]) for e in entities if e in reactions._answers]
    reactions.closed_unresolved = reason
    payload = {"scope": "G4.0_BINDING_AND_G4.1_EFFECT_ANATOMY", "lever_entities": entities, "anatomies": anatomies,
               "answers": answers, "open_questions": [], "status": UNRESOLVED, "unresolved_reason": reason,
               "unresolved_lever_chapters": []}
    _put(machine, G41, "LeverEffectAnatomySet", "G4-ANATOMY-UNRESOLVED-" + _sha(payload), int(reactions.revision),
         payload, (G3,))


def _close_g42(machine: Any, reason: str) -> None:
    """A seeded G4.2 closes chapter by chapter (r2); an unbuildable one (no anatomy to study) closes empty."""
    study = machine._adapters[G42]
    if not _unbuildable(machine, G42):
        _close_chapters(machine, G42, reason, study._emit_orbit_product)
        return
    answered = [e for e in getattr(study, "_ordered_entities", ()) if e in study._answers]
    unresolved = [e for e in getattr(study, "_ordered_entities", ()) if e not in study._answers]
    study.closed_unresolved = reason
    payload = {"scope": "G4A_GUIDED_SINGLE_LEVER_STUDY", "lever_entities": answered, "pending_lever_entities": [],
               "interrupted_lever_entities": [], "unstudied_lever_entities": [], "unresolved_lever_entities": unresolved,
               "interruptions": [], "phase1_status": UNRESOLVED, "status": UNRESOLVED, "unresolved_reason": reason,
               "level_boundary": None,
               "orbits": [{**study._completed[e].orbit.snapshot(), "run_id": study._completed[e].run_id,
                           "run_status": study._completed[e].status,
                           "confirmation": list(study._completed[e].confirmation)}
                          for e in answered if e in study._completed],
               "answers": [asdict(study._answers[e]) for e in answered],
               "lever_classes": {e: study._completed[e].lever_class() for e in answered if e in study._completed},
               "lever_typing": {e: study._completed[e].typing() for e in answered if e in study._completed},
               "g3_pairs": {}, "life_restudies": dict(getattr(study, "_life_restudies", {}) or {}),
               "action_count": int(getattr(study, "_action_count", 0) or 0), "unresolved_lever_chapters": []}
    _put(machine, G42, "LeverOrbitSet", "G4-ORBITS-UNRESOLVED-" + _sha(payload), int(study.revision), payload, (G41,))


def _close_chapters(machine: Any, gate: str, reason: str, emit: Any) -> None:
    from inference.framework import chapter_closure

    machine._adapters[gate].closed_unresolved = reason
    chapter_closure.close_open(machine, gate, reason)
    if machine.target_journal.active_product(gate) is None:  # nothing was left open: the settled product
        emit()


def _close_existing(gate: str) -> Any:
    def close(machine: Any, reason: str) -> None:
        adapter = machine._adapters[gate]
        if _unbuildable(machine, gate):
            adapter._regions = ()  # nothing to seed: the gate closes on no levers
            if gate == G4C:
                machine._adapters[G4B]._regions = ()
        adapter.close_unresolved(reason)
    return close


def render_closed(gate: str, payload: Any, render: Any = None) -> list[str]:
    """The card's digest lines for a gate this module closed (it certifies nothing; a closed G2 masks nothing), or
    for a G4 product with closed chapters (r3: "settled with gaps", each gap's class, then the supported results);
    any other product renders as ``render`` does (unchanged)."""
    from inference.framework.chapter_semantics import settlement_note

    note = settlement_note(payload) if gate in (G41, G42) else None
    if note is not None:
        return [note, *(render() if render is not None and payload.get("answers") else [])]
    if gate not in (G1, G2, G3, G41, G42) or not isinstance(payload, Mapping) or payload.get("status") != UNRESOLVED:
        return [] if render is None else render()
    text = f"CLOSED_UNRESOLVED ({payload.get('unresolved_reason')}) · certifies nothing"
    if gate == G2:
        region = payload.get("counter_exclusion_region") or ()
        text += f" · counter change unmasked · exclusion region {len(region)} cells"
    if gate == G3:
        text += f" · levers {', '.join(payload.get('lever_entities') or ()) or 'none'}"
    return [text]


_CLOSERS = {G1: _close_g1, G2: _close_g2, G3: _close_g3, G41: _close_g41, G42: _close_g42,
            G4B: _close_existing(G4B), G4C: _close_existing(G4C)}
CLOSABLE = frozenset(_CLOSERS)  # the gates a CLOSED_UNRESOLVED product can close (never G0 or PLAY-NORMAL)


def close_stuck_gate(machine: Any, question_id: str | None, reason: str, history: tuple | list = (),
                     cause: str | None = None) -> Closure:
    """The controller's side (D22, D-2), revision 2 ruling 2, in order and always inside the stuck gate:

    1. the exact selected question, when it is this gate's;
    2. otherwise the gate's own current unsettled head, recomputed;
    3. if the gate has no question left and no product, the gate itself, unresolved.

    An upstream gate is never touched because a downstream gate stalled (a G4 stall never closes a G3 entity)."""
    gate = machine.gate_id
    parsed = parse(question_id)
    if parsed is not None and parsed[1] == gate:
        closure = close_question(machine, question_id, reason, history, cause)
        if closure.status == "CLOSED":
            return closure
    head = head_question(machine, gate)
    if head is not None and head != question_id:
        closure = close_question(machine, head, reason, history, cause)
        if closure.status == "CLOSED":
            return closure
    if head is None and gate in CLOSABLE and machine.target_journal.active_product(gate) is None:
        return close_gate(machine, gate, reason)
    return Closure("NOTHING_TO_CLOSE", "NONE", gate)


def head_question(machine: Any, gate: str) -> str | None:
    """The gate's own current unsettled head question (G3's coverage head, a G4.1 or G4.2 chapter), or None."""
    from inference.framework import g4_selection
    from inference.framework.library_agenda import question_id

    level = int(machine.lives.level)
    if gate == G3:
        entity = _g3_head_entity(machine)
        return None if entity is None else question_id(level, G3, entity, "IS_LEVER")
    if gate in (G41, G42):
        return g4_selection.selected_question(machine)
    from inference.framework.library_agenda import GATE_QUESTIONS

    return None if machine.target_journal.active_product(gate) is not None else question_id(
        level, gate, f"LEVEL-{level}", GATE_QUESTIONS.get(gate, ("GATE",))[0])


def _g3_head_entity(machine: Any) -> str | None:
    g3 = machine._adapters[G3]
    frontier, index, ledger = g3._eligible_frontier, g3._target_index, g3.entity_ledger
    if not frontier or index >= len(frontier) or ledger is None:
        return None
    entity = ledger.member_to_entity.get(frontier[index]["member_id"])
    journal = g3.lifecycle_journal
    settled = journal is None or entity not in journal.entities or journal.entities[entity].state in SETTLED_G3
    return None if settled else entity


def _close_chapter(machine: Any, gate: str, entity: str, question_id: str | None, reason: str,
                   history: tuple | list, cause: str | None = None) -> Closure:
    """One G4.1 or G4.2 lever chapter (``chapter_closure``); the ladder continues, cascading only if unbuildable."""
    from inference.framework import chapter_closure

    if gate not in machine._adapters or machine.gate_id != gate:
        return Closure("NOTHING_TO_CLOSE", "CHAPTER", gate, entity)
    status = chapter_closure.close(machine, gate, entity, question_id=question_id, reason=reason, history=history,
                                   cause=cause)
    cascaded = tuple(cascade(machine)) if status == "CLOSED" and machine.target_journal.active_product(gate) else ()
    return Closure(status, "CHAPTER", gate, entity, cascaded)


__all__ = ["CLOSABLE", "Closure", "UNRESOLVED", "UPSTREAM", "cascade", "close_gate", "close_question",
           "close_stuck_gate", "head_question", "parse", "phase1_hold_reason", "render_closed"]
