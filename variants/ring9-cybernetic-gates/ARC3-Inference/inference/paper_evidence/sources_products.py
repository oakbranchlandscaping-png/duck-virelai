"""Claims from the certified product content of each gate (WO-PE-03B, interface §2.2, product rows).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.2.

The product payload is the gate's certified state, so its claims are SYSTEM-executed, certified by the product's
origin (``product_answers``), with the triggering admitted answer in ``source`` (Sol §10). A product that states it is
unresolved yields one GAP audit and no proposition (a GATE_DERIVED closure never yields a LAW or RELATION).

Read per product type:
- EgoLaw: ``CONTROL_MODE`` and ``ACTION_EFFECT``;
- CounterGateProduct: ``COUNTER_REWRITE``, ``COUNTER_TRIGGER``, ``COUNTER_PERIOD``;
- LeverEffectAnatomySet: ``EFFECT_LOCALITY``, ``EFFECT_TRANSFORM``;
- LeverOrbitSet: ``LEVER_CLASS``, ``ORBIT_PERIOD``, plus closed and interrupted levers as audits;
- LeverRelationSet: ``COUPLED_WITH``, ``SHARES_REGION_WITH``, ``RECORDED_EFFECT`` (free text), and predictions with
  their graded outcomes as separate PREDICTION propositions and audits;
- LeverReactionLawSet (G4-C): the same relations and predictions when resolved.
ActionSurface (the platform's own metadata) and LeverInventory (whose certified projection is the roles and scoped
nulls) add no claims.
"""
from __future__ import annotations

from itertools import combinations
from typing import Any, Callable, Iterator, Mapping

from inference.paper_evidence import claims as c
from inference.paper_evidence.context import (LevelContext, agent_subject, counter_subject, entity_subject,
                                              product_attribution)

POINTER = {"POINTER_GOD_MODE": "POINTER"}
GRADED = frozenset({"SUPPORTED", "CONTRADICTED"})


def _law(ctx: LevelContext, gate_id: str, subject: Mapping[str, Any], predicate: str, obj: Any, *,
         family: str = "LAW", status: str = "CERTIFIED", scope: Mapping[str, Any] | None = None,
         detail: Mapping[str, Any] | None = None, refs: list[str] | None = None,
         certification: str | None = None) -> dict[str, Any]:
    who = product_attribution(ctx, gate_id)
    return c.claim(game_id=ctx.game_id, level=ctx.number, family=family, kind="PROPOSITION", subject=subject,
                   predicate=predicate, obj=obj, scope=scope, status=status, executor="SYSTEM",
                   admission="NOT_APPLICABLE", certification=certification or who["certification"],
                   source={"product_id": who["product_id"], "provenance_event": who["provenance_event"],
                           **dict(detail or {})}, refs=refs)


def _open(ctx: LevelContext, gate_id: str, subject: Mapping[str, Any], predicate: str, obj: Any,
          status: str = "OPEN", detail: Mapping[str, Any] | None = None) -> dict[str, Any]:
    who = product_attribution(ctx, gate_id)
    return c.claim(game_id=ctx.game_id, level=ctx.number, family="GAP", kind="AUDIT", subject=subject,
                   predicate=predicate, obj=obj, status=status, executor="SYSTEM", admission="NOT_APPLICABLE",
                   certification=who["certification"], source={"product_id": who["product_id"], **dict(detail or {})})


def _agent(ctx: LevelContext) -> dict[str, Any]:
    return agent_subject(ctx)


def _counter(ctx: LevelContext) -> dict[str, Any]:
    return counter_subject(ctx)


def ego_claims(ctx: LevelContext, gate_id: str, payload: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    if payload.get("mode") == "UNRESOLVED" or payload.get("status") == "UNRESOLVED":
        yield _open(ctx, gate_id, _agent(ctx), "UNRESOLVED", payload.get("unresolved_reason"))
        return
    mode = str(payload.get("mode"))
    yield _law(ctx, gate_id, _agent(ctx), "CONTROL_MODE", POINTER.get(mode, mode), refs=payload.get("evidence_refs"))
    for action, effect in payload.get("opaque_action_laws") or ():
        yield _law(ctx, gate_id, c.plain_subject("ACTION", str(action)), "ACTION_EFFECT", effect,
                   refs=payload.get("evidence_refs"))


def counter_claims(ctx: LevelContext, gate_id: str, payload: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    if payload.get("product_kind") != "COUNTER_MODEL_AND_MASK":
        yield _open(ctx, gate_id, _counter(ctx), "UNRESOLVED", payload.get("product_kind"))
        return
    model, mask, subject = payload.get("counter_model") or {}, payload.get("mask_law") or {}, _counter(ctx)
    refs = list(mask.get("witness_evidence_refs") or ())
    if mask.get("rewrite"):
        yield _law(ctx, gate_id, subject, "COUNTER_REWRITE", mask["rewrite"], refs=refs)
    if model.get("trigger"):
        yield _law(ctx, gate_id, subject, "COUNTER_TRIGGER", model["trigger"], refs=model.get("evidence_refs"))
    if payload.get("derived_period_actions") is not None:
        yield _law(ctx, gate_id, subject, "COUNTER_PERIOD", payload["derived_period_actions"], refs=refs)


def anatomy_claims(ctx: LevelContext, gate_id: str, payload: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    """One claim per lever and distinct channel value: channels are evidence, the locality is the fact."""
    for anatomy in payload.get("anatomies") or ():
        subject = entity_subject(ctx, anatomy.get("entity_id"))
        for field, predicate in (("locality", "EFFECT_LOCALITY"), ("transform", "EFFECT_TRANSFORM")):
            for value in sorted({channel[field] for channel in anatomy.get("channels") or ()}):
                yield _law(ctx, gate_id, subject, predicate, value, detail={"anatomy_id": anatomy.get("anatomy_id")},
                           refs=[anatomy.get("witness_evidence_ref") or ""])


def orbit_claims(ctx: LevelContext, gate_id: str, payload: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    for entity_id, lever_class in sorted((payload.get("lever_classes") or {}).items()):
        yield _law(ctx, gate_id, entity_subject(ctx, entity_id), "LEVER_CLASS", lever_class)
    for answer in payload.get("answers") or ():
        if answer.get("observed_period"):
            yield _law(ctx, gate_id, entity_subject(ctx, answer.get("entity_id")), "ORBIT_PERIOD",
                       answer["observed_period"], detail={"answer_id": answer.get("answer_id")},
                       refs=answer.get("evidence_refs"))
    for key, status in (("closed_entities", "CLOSED_WITHOUT_FINDING"), ("interrupted_lever_entities", "OPEN")):
        for entity_id in payload.get(key) or ():
            yield _open(ctx, gate_id, entity_subject(ctx, entity_id), "CHAPTER_STATE",
                        {"chapter": "orbit", "status": key.split("_")[0].upper()}, status=status)


def _relation_parts(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return payload.get("from_record") or payload.get("answer") or payload


def _from_record(payload: Mapping[str, Any]) -> str | None:
    """Sol §10: relations the gate re-derived from the record are RECORD_DERIVED; the admission only triggered them."""
    return "RECORD_DERIVED" if payload.get("certified_by") == "RECORD" or payload.get("from_record") else None


def _pair_claims(ctx: LevelContext, gate_id: str, groups: list, predicate: str,
                 certification: str | None) -> Iterator[dict[str, Any]]:
    for group in groups or ():
        for left, right in combinations(sorted(group), 2):
            yield _law(ctx, gate_id, entity_subject(ctx, left), predicate,
                       c.identity_subject(entity_subject(ctx, right)), family="RELATION", detail={"pair": [left, right]},
                       certification=certification)


def _prediction_claims(ctx: LevelContext, gate_id: str, predictions: list) -> Iterator[dict[str, Any]]:
    """A prediction proposition, and when graded, the separate audit of how it fared (D11)."""
    for prediction in predictions or ():
        subject = entity_subject(ctx, prediction.get("acted_lever"))
        expected = {"action": prediction.get("action"), "expected": prediction.get("expected")}
        proposition = _law(ctx, gate_id, subject, "PREDICTS", expected, family="PREDICTION", status="PREDICTED",
                           detail={"prediction_id": prediction.get("prediction_id")})
        yield proposition
        if prediction.get("status") in GRADED:
            yield _open(ctx, gate_id, subject, "PREDICTION_OUTCOME",
                        {"prediction": proposition["claim_key"], "outcome": prediction["status"]},
                        status=prediction["status"], detail={"prediction_id": prediction.get("prediction_id")})


def relation_claims(ctx: LevelContext, gate_id: str, payload: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    if payload.get("status") == "UNRESOLVED":
        yield _open(ctx, gate_id, c.plain_subject("LEVEL", f"level-{ctx.number}"), "UNRESOLVED",
                    payload.get("unresolved_reason") or gate_id)
        return
    parts, certification = _relation_parts(payload), _from_record(payload)
    yield from _pair_claims(ctx, gate_id, parts.get("coupled_groups"), "COUPLED_WITH", certification)
    yield from _pair_claims(ctx, gate_id, parts.get("shared_regions"), "SHARES_REGION_WITH", certification)
    for index, relation in enumerate(parts.get("relations") or ()):
        levers = sorted(relation.get("levers") or ())
        yield _law(ctx, gate_id, entity_subject(ctx, levers[0] if levers else None), "RECORDED_EFFECT",
                   relation.get("claim"), family="RELATION", scope={"levers": len(levers)},
                   detail={"relation_index": index}, refs=relation.get("evidence_refs"), certification=certification)
    yield from _prediction_claims(ctx, gate_id, payload.get("predictions"))


READERS: dict[str, Callable[[LevelContext, str, Mapping[str, Any]], Iterator[dict[str, Any]]]] = {
    "EgoLaw": ego_claims, "CounterGateProduct": counter_claims, "LeverEffectAnatomySet": anatomy_claims,
    "LeverOrbitSet": orbit_claims, "LeverRelationSet": relation_claims, "LeverReactionLawSet": relation_claims,
}


def product_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    for gate_id, entry in sorted(ctx.products.items()):
        reader = READERS.get(entry.get("product_type"))
        if reader is not None and entry.get("status") == "CAPTURED":
            yield from reader(ctx, gate_id, entry.get("payload") or {})


__all__ = ["READERS", "product_claims"]
