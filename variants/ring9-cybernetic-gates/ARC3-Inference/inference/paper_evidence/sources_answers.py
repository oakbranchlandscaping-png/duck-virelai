"""Claims from submitted answers, admitted and refused (WO-PE-03B; D4, D11, Sol §10).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.2, last row.

Each provenance ``ANSWER / ADMISSION`` row is one submission. Every independently interpretable field becomes its own
claim, executed by its submitter. A field the controller filled (``field_sources``) is the controller's, never Duck's.
A field the answer shape marks ``GENERATED``, ``DERIVED``, ``OUTCOME`` or the id is the gate's, never the submitter's.
A refusal stays in the denominator. A refusal with no interpretable field becomes one open GAP audit.

Not propositions, so never projected:
- evidence and record references;
- competing models (alternatives, not assertions);
- limitations and epistemic limits;
- the intervention and the state sequence (evidence);
- descriptions (prose summaries).

Answers at G0 restate the platform's action metadata and assert nothing about the world.
"""
from __future__ import annotations

from typing import Any, Iterator, Mapping

from inference.framework import answer_shapes
from inference.paper_evidence import claims as c
from inference.paper_evidence.context import LevelContext, agent_subject, counter_subject, entity_subject

TEXT = {"mechanism": ("LAW", "MECHANISM"), "mechanism_explanation": ("LAW", "MECHANISM"),
        "explanation": ("LAW", "MECHANISM"), "falsifier": ("CONDITION", "FALSIFIER"),
        "tracked_variable": ("LAW", "COUNTER_TRACKS"), "stop_disposition": ("LAW", "ORBIT_STOP")}
SKIPPED_GATES = frozenset({"G0-ACTION-METADATA"})
SUBMITTED = frozenset({"SUBMITTER", "SUBMITTER_CONFIRMED_BY_CONTROLLER"})


def _gate_owned(row: Mapping[str, Any], field: str) -> bool:
    """True for a field the answer shape says the gate produces (id, generated, derived, outcome)."""
    shape = answer_shapes.answer_shape(row["gate_id"], row.get("submitted") or {})
    rule = (answer_shapes.SHAPES.get(shape) or {}).get(field) if shape else None
    return isinstance(rule, str)


def _subject(ctx: LevelContext, row: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    if payload.get("entity_id"):
        return entity_subject(ctx, payload["entity_id"])
    if row["gate_id"] == "G1-EGO":
        return agent_subject(ctx)
    if row["gate_id"] == "G2-COUNTER":
        return counter_subject(ctx)
    return c.plain_subject("LEVEL", f"level-{ctx.number}")


def _values(field: str, value: Any) -> Iterator[tuple[str, str, Any, int]]:
    """(family, predicate, object, index) for each proposition one field states."""
    if field in TEXT and value not in (None, "", []):
        yield (*TEXT[field], value, 0)
    elif field == "trigger" and value not in (None, "", "UNSPECIFIED"):
        yield "LAW", "COUNTER_TRIGGER", value, 0
    elif field == "observed_period" and value:
        yield "LAW", "ORBIT_PERIOD", value, 0
    elif field == "conditions":
        yield from (("CONDITION", "CONDITION_TEXT", item, i) for i, item in enumerate(value or ()))
    elif field == "action_laws" and isinstance(value, Mapping):  # subject ACTION, object the effect (as the product)
        yield from (("LAW", "ACTION_EFFECT", (str(k), v), i) for i, (k, v) in enumerate(sorted(value.items())))
    elif field == "effect_channels":
        for name, predicate in (("locality", "EFFECT_LOCALITY"), ("transform", "EFFECT_TRANSFORM")):
            yield from (("LAW", predicate, item, i) for i, item in enumerate(sorted({ch.get(name) for ch in value or ()
                                                                                     if ch.get(name)})))
    elif field == "relations":
        yield from (("RELATION", "RECORDED_EFFECT", item.get("claim") if isinstance(item, Mapping) else item, i)
                    for i, item in enumerate(value or ()))
    elif field in ("novel_prediction", "prediction_options", "expected") and value:
        yield "PREDICTION", "PREDICTS", value, 0


def _inventory(ctx: LevelContext, payload: Mapping[str, Any]) -> Iterator[tuple[dict, str, str, Any, int]]:
    """A G3 inventory answer's flattened prediction: which entities it says are levers or clean nulls."""
    prediction = payload.get("novel_prediction") or {}
    for key, family, predicate, obj in (("lever_entities", "ROLE", "ROLE_IS", "LEVER"),
                                        ("clean_null_entities", "CONDITION", "NO_OBSERVED_EFFECT",
                                         "OBSERVED_INTERACTION_IN_RECORDED_STATE")):
        for index, entity_id in enumerate(prediction.get(key) or ()):
            yield entity_subject(ctx, entity_id), family, predicate, obj, index


def _located(ctx: LevelContext, row: Mapping[str, Any], payload: Mapping[str, Any],
             value: tuple[str, str, Any, int]) -> tuple[dict, str, str, Any, int]:
    """An action law is about its action (subject ACTION), exactly as the certified ego law states it."""
    family, predicate, obj, index = value
    if predicate == "ACTION_EFFECT":
        return c.plain_subject("ACTION", obj[0]), family, predicate, obj[1], index
    return _subject(ctx, row, payload), family, predicate, obj, index


def _field_claims(ctx: LevelContext, row: Mapping[str, Any]) -> Iterator[dict[str, Any]]:
    submitted, effective = row.get("submitted") or {}, row.get("effective") or row.get("submitted") or {}
    sources = row.get("field_sources") or {key: "SUBMITTER" for key in submitted}
    for field in sorted(sources):
        if "." in field or _gate_owned(row, field):
            continue
        mine = sources[field] in SUBMITTED
        payload = submitted if mine else effective
        executor = row["executor"] if mine else "CONTROLLER"
        rows = list(_inventory(ctx, payload)) if (field == "novel_prediction" and row["gate_id"] == "G3-LEVERS") else \
            [_located(ctx, row, payload, value) for value in _values(field, payload.get(field))]
        for subject, family, predicate, obj, index in rows:
            yield c.claim(game_id=ctx.game_id, level=ctx.number, family=family, kind="PROPOSITION", subject=subject,
                          predicate=predicate, obj=obj, status="PREDICTED" if family == "PREDICTION" else "PROPOSED",
                          executor=executor, admission=row["disposition"], certification="NONE",
                          field_source=sources[field], refs=payload.get("evidence_refs"),
                          source={"provenance_event": row["event_id"], "field": field, "index": index})


def _unparseable(ctx: LevelContext, row: Mapping[str, Any]) -> dict[str, Any]:
    return c.claim(game_id=ctx.game_id, level=ctx.number, family="GAP", kind="AUDIT",
                   subject=c.plain_subject("LEVEL", f"level-{ctx.number}"), predicate="UNPARSEABLE_ANSWER",
                   obj={"gate_id": row["gate_id"], "reason": (row.get("reason") or {}).get("code")}, status="OPEN",
                   executor=row["executor"], admission="REFUSED", certification="NONE",
                   source={"provenance_event": row["event_id"]})


def answer_claims(ctx: LevelContext) -> Iterator[dict[str, Any]]:
    for row in ctx.answer_rows:
        if row["gate_id"] in SKIPPED_GATES or row.get("disposition") not in ("ADMITTED", "REFUSED"):
            continue
        found = list(_field_claims(ctx, row)) if isinstance(row.get("submitted"), Mapping) else []
        if found:
            yield from found
        elif row["disposition"] == "REFUSED":
            yield _unparseable(ctx, row)


__all__ = ["answer_claims"]
