"""Read-only facade over Virelai's memory: the record and the certified world model.

Author: Claude (Alpha build seat), 2026-09-28. R9-R06 (DESIGN_VIRELAI_MEMORY_v1 §5.1, stage M-0).

Every recall — injected by the controller onto the card, or pulled by Duck — goes through this one
facade. It writes nothing (memory law M1: the controller is the sole writer, and it writes through
the gate machine, never through here). Every list it returns is paged and bounded, so a recall can
never become the next card overflow.

Tiers it reads (§5):
- the record: ``machine.transition_index`` (one sparse, lossless row per recorded transition) and
  the G3 entity ledger, lifecycle journal and attribution evidence;
- the world model: the target journal's active, gate-certified products.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Mapping

SCHEMA = "virelai-memory-store-v1"
MAX_PAGE = 50
# A pull must reach Duck whole. The sandbox prints every query as indented JSON (about twice the
# compact size) and the tool result is capped at about 4,096 characters, so a pulled result is
# fitted to 1,800 compact characters: a page shrinks, a large field becomes a pull handle.
PULL_CHARS = 1_800
FIT_PROTECTED = frozenset({"schema", "kind", "total", "offset", "limit", "remaining", "rows", "label"})


def transition_index_row(
    probe: Any, outcome: Mapping[str, Any], event: Mapping[str, Any]
) -> dict[str, Any]:
    """One record-tier row: sparse changed cells are lossless for fixed geometry (R9-R06)."""
    attribution = event.get("attribution") if isinstance(event, Mapping) else None
    action = outcome.get("action") if isinstance(outcome.get("action"), Mapping) else {}
    acted = outcome.get("acted_site") if isinstance(outcome.get("acted_site"), Mapping) else None
    if acted is None and "row" in action and "col" in action:
        acted = {"row": action["row"], "col": action["col"]}
    boundary = outcome.get("boundary_event")
    return {
        "transition_id": int(outcome.get("transition_id") or 0),
        "gate_id": probe.gate_id,
        "probe_id": probe.probe_id,
        "evidence_id": event.get("evidence_id") if isinstance(event, Mapping) else None,
        "action": dict(action),
        "acted_site": None if acted is None else {"row": int(acted["row"]), "col": int(acted["col"])},
        "changed": [
            [int(item["row"]), int(item["col"]), item.get("before"), item.get("after")]
            for item in outcome.get("changed_cells") or ()
            if isinstance(item, Mapping) and "row" in item and "col" in item
        ],
        "boundary_state": boundary.get("state") if isinstance(boundary, Mapping) else None,
        "disposition": (
            attribution.get("disposition") if isinstance(attribution, Mapping) else None
        ),
    }


def _page(rows: list[Any], offset: int, limit: int) -> dict[str, Any]:
    offset = max(0, int(offset))
    limit = max(1, min(MAX_PAGE, int(limit)))
    return {
        "total": len(rows),
        "offset": offset,
        "limit": limit,
        "rows": rows[offset:offset + limit],
        "remaining": max(0, len(rows) - offset - limit),
    }


INLINE_CHARS = 240


def _field_summary(name: str, value: Any) -> Any:
    """Inline a short value; describe a long one and say how to page it."""
    rendered = json.dumps(value, sort_keys=True, default=str)
    if len(rendered) <= INLINE_CHARS:
        return value
    kind = type(value).__name__
    length = len(value) if isinstance(value, (list, tuple, dict, str)) else None
    return {"omitted": True, "type": kind, "length": length, "chars": len(rendered), "query_field": name}


def cell_bbox(cells: Any) -> list[int] | None:
    """[min row, min col, max row, max col] of ``(row, col)`` cells; None when there are none."""
    rows = [int(cell[0]) for cell in cells]
    cols = [int(cell[1]) for cell in cells]
    return [min(rows), min(cols), max(rows), max(cols)] if rows else None


def _compact_transition(row: Mapping[str, Any]) -> dict[str, Any]:
    changed = row.get("changed") or []
    return {
        "transition_id": row.get("transition_id"),
        "gate_id": row.get("gate_id"),
        "evidence_id": row.get("evidence_id"),
        "action": row.get("action"),
        "changed_cell_count": len(changed),
        "changed_bbox": cell_bbox([cell[:2] for cell in changed]),
        "disposition": row.get("disposition"),
        "boundary_state": row.get("boundary_state"),
        "kind": row.get("kind"),
        "life": row.get("life"),
        "level": row.get("level"),
    }


class MemoryStore:
    """Bounded, read-only recall over one gate machine."""

    def __init__(self, machine: Any) -> None:
        self._machine = machine

    # ---- world model (certified products) -------------------------------------------------
    def products(self) -> dict[str, Any]:
        """One row per active certified product, in gate order."""
        rows = [
            {
                "gate_id": row["gate_id"],
                "product_id": row["product_id"],
                "product_type": row["product_type"],
                "revision": row["revision"],
            }
            for row in self._machine.completed_gate_rows()
        ]
        return {"schema": SCHEMA, "kind": "products", "rows": rows}

    def product(
        self, key: str, field: str | None = None, offset: int = 0, limit: int = 20
    ) -> dict[str, Any] | None:
        """A certified product by product id or gate id, bounded.

        Without ``field``: every payload field, inline when short, otherwise its type, length and
        the ``field`` to page it by. With ``field``: that field, paged if it is a list.
        """
        wanted = str(key or "").strip()
        for row in self._machine.completed_gate_rows():
            if wanted not in {row["product_id"], row["gate_id"]}:
                continue
            payload = row["answer"]
            head = {name: row[name] for name in ("gate_id", "product_id", "product_type", "revision")}
            if field is None:
                return {"schema": SCHEMA, "kind": "product", **head,
                        "fields": {name: _field_summary(name, value) for name, value in sorted(payload.items())}}
            value = payload.get(field)
            if isinstance(value, (list, tuple)):
                return {"schema": SCHEMA, "kind": "product_field", **head, "field": field,
                        **_page(list(value), offset, limit)}
            if isinstance(value, Mapping):
                value = {name: _field_summary(f"{field}.{name}", item) for name, item in sorted(value.items())}
            else:
                value = _field_summary(field, value)
            return {"schema": SCHEMA, "kind": "product_field", **head, "field": field, "value": value}
        return None

    # ---- record ---------------------------------------------------------------------------
    def transitions(self, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        rows = [_compact_transition(row) for row in self._machine.transition_index]
        return {"schema": SCHEMA, "kind": "transitions", **_page(rows, offset, limit)}

    def transition(self, transition_id: int, offset: int = 0, limit: int = MAX_PAGE) -> dict[str, Any] | None:
        """One transition in full: its changed cells, paged."""
        for row in self._machine.transition_index:
            if row.get("transition_id") == int(transition_id):
                return {
                    "schema": SCHEMA,
                    "kind": "transition",
                    **_compact_transition(row),
                    "changed_cells": _page(list(row.get("changed") or []), offset, limit),
                }
        return None

    def lives(self, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Each life so far: its level, transitions, and how it ended (R9-R16)."""
        record = getattr(self._machine, "lives", None)
        rows = record.summary() if record is not None else []
        return {"schema": SCHEMA, "kind": "lives", "current_life": len(rows), **_page(rows, offset, limit)}

    def levels(self, level: Any = None) -> dict[str, Any]:
        """Each finished level's frozen model, compact; with ``id``, that level's (R9-R17)."""
        from inference.framework.level_model import compact

        rows = [compact(item) for item in getattr(self._machine, "levels", ()) if level in (None, item.get("level"))]
        return {"schema": SCHEMA, "kind": "levels", "carry_status": "UNCONFIRMED on this level", "rows": rows}

    def _this_level(self) -> list[dict[str, Any]]:
        """The record of the current level: an object on another level is not this one (R9-R17)."""
        level = getattr(getattr(self._machine, "lives", None), "level", None)
        return [item for item in self._machine.transition_index if level is None or item.get("level") in (None, level)]

    def site(self, row: int, col: int, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Every transition on this level aimed at this cell, most recent first."""
        target = {"row": int(row), "col": int(col)}
        rows = [_compact_transition(item) for item in reversed(self._this_level()) if item.get("acted_site") == target]
        return {"schema": SCHEMA, "kind": "site", "site": target, **_page(rows, offset, limit)}

    def evidence(self, evidence_id: str) -> dict[str, Any]:
        return {"schema": SCHEMA, "kind": "evidence", **self._machine.evidence_view(evidence_id)}

    # ---- a subject's file ---------------------------------------------------------------
    def subject(
        self, entity_id: str, field: str | None = None, offset: int = 0, limit: int = 20
    ) -> dict[str, Any] | None:
        """Everything recorded about one persistent object, bounded.

        Identity (sightings), lifecycle, attributed evidence, G3 confirmation and dossier, and
        every transition aimed at the object's current cells, most recent first. Opens once G3 has
        a ledger. With ``field``, that one part of the file, paged if it is a list.
        """
        lever = self._machine._adapters.get("G3-LEVERS")
        ledger = getattr(lever, "entity_ledger", None)
        requested = str(entity_id or "").strip()
        if ledger is None or requested not in ledger.entities:
            return None
        entity = lever.entity_view(requested, offset=0, limit=4)
        journal = getattr(lever, "lifecycle_journal", None)
        lifecycle = journal.entities.get(requested) if journal is not None else None
        member_ids = set(entity.get("member_ids") or ())
        confirmations = [
            lever._compact_confirmation_record(record)
            for record in getattr(lever, "_confirmation_records", ())
            if record.get("entity_id") == requested
        ]
        dossiers = [
            asdict(answer)
            for member_id, answer in sorted(getattr(lever, "_dossier_answers", {}).items())
            if member_id in member_ids
        ]
        cells = {tuple(cell) for cell in ledger.cells_for(requested)}
        aimed = [
            _compact_transition(item)
            for item in reversed(self._this_level())
            if item.get("acted_site")
            and (item["acted_site"]["row"], item["acted_site"]["col"]) in cells
        ]
        file = {
            "schema": SCHEMA,
            "kind": "subject",
            "entity": entity,
            "lifecycle_state": None if lifecycle is None else lifecycle.state,
            "lifecycle_events": (
                [] if lifecycle is None else [asdict(event) for event in lifecycle.events[-8:]]
            ),
            "confirmations": confirmations[-4:],
            "dossiers": dossiers[-2:],
            "aimed_transitions": _page(aimed, 0, 20),
        }
        if field is None:
            return file
        value = aimed if field == "aimed_transitions" else file.get(field)
        head = {"schema": SCHEMA, "kind": "subject_field", "entity_id": requested, "field": field}
        if isinstance(value, list):
            return {**head, **_page(value, offset, limit)}
        return {**head, "value": value}

    # ---- Duck's UNCERTIFIED lane (D6) -------------------------------------------------------
    def notes(self, subject: str | None = None, offset: int = 0, limit: int = 20) -> dict[str, Any]:
        """Duck's notes, newest first, optionally about one subject; always labelled."""
        lane = getattr(self._machine, "annotations", None)
        rows = [asdict(note) for note in reversed(lane.notes if lane is not None else [])
                if subject in (None, "", note.subject)]
        return {"schema": SCHEMA, "kind": "notes", "label": "UNCERTIFIED: Duck's notes; only a gate certifies",
                **_page(rows, offset, limit)}

    # ---- the one pull interface -------------------------------------------------------------
    def query(self, kind: str, **params: Any) -> dict[str, Any] | None:
        """``virelai('memory', kind=…, …)``: one bounded read, fitted to ``PULL_CHARS``."""
        result = self._query(kind, **params)
        ident = params.get("id")
        return _fit(result, lambda name: (
            f"virelai('memory', kind={kind!r}" + (f", id={ident!r}" if ident is not None else "")
            + f", field={name!r})"
        ))

    def _query(self, kind: str, **params: Any) -> dict[str, Any] | None:
        paging = {name: int(params[name]) for name in ("offset", "limit") if params.get(name) is not None}
        ident = params.get("id")
        if kind not in QUERY_KINDS:
            raise ValueError(f"memory kind must be one of {list(QUERY_KINDS)}.")
        if kind == "products":
            return self.products()
        if kind == "product":
            return self.product(str(ident or ""), params.get("field"), **paging)
        if kind == "transitions":
            return self.transitions(**paging)
        if kind == "transition":
            return self.transition(int(ident or 0), **paging)
        if kind == "lives":
            return self.lives(**paging)
        if kind == "carry":
            carry = getattr(self._machine, "carry", None)
            return {"schema": SCHEMA, "kind": "carry", **(carry.view() if carry is not None else {})}
        if kind == "levels":
            return self.levels(None if ident is None else int(ident))
        if kind == "site":
            return self.site(int(params.get("row", -1)), int(params.get("col", -1)), **paging)
        if kind == "evidence":
            return self.evidence(str(ident or ""))
        if kind == "subject":
            return self.subject(str(ident or ""), params.get("field"), **paging)
        return self.notes(params.get("subject") or ident, **paging)


QUERY_KINDS = (
    "products", "product", "transitions", "transition", "lives", "levels", "carry", "site", "evidence", "subject",
    "notes",
)


def _fit(result: dict[str, Any] | None, pull: Any) -> dict[str, Any] | None:
    """Shrink a pulled result to ``PULL_CHARS``: first its page, then its largest fields."""
    if result is None or _chars(result) <= PULL_CHARS:
        return result
    out = dict(result)
    if isinstance(out.get("rows"), list):
        rows = list(out["rows"])
        while len(rows) > 1 and _chars({**out, "rows": rows}) > PULL_CHARS:
            rows.pop()
        out.update(rows=rows, limit=len(rows), remaining=int(out["total"]) - int(out["offset"]) - len(rows))
    while _chars(out) > PULL_CHARS:
        names = [name for name, value in out.items()
                 if name not in FIT_PROTECTED and not (isinstance(value, dict) and value.get("omitted"))]
        if not names:
            break
        name = max(names, key=lambda item: _chars(out[item]))
        out[name] = {"omitted": True, "chars": _chars(result[name]), "pull": pull(name)}
    return out


def _chars(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, default=str))
