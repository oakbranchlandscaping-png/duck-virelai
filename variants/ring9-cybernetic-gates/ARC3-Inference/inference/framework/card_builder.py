"""The slot-built card: what Duck is shown each turn, built from named slots with budgets.

Author: Claude (Alpha build seat), 2026-09-29. R9-R07 (DESIGN_VIRELAI_MEMORY_v1 stage M-1).

Memory laws implemented here (DOCTRINE_FRICTION_AXIOMS_v3):
- M3 · the card is **built**, never trimmed: every slot is a whitelisted projection of the gate's
  state, so a field without a slot cannot reach Duck;
- M4 · the card's size depends neither on the world nor on how much has been found: every list is
  windowed with a count, and the certified world model is a grouped digest;
- M5 · the present is never hidden: the goal, the current probe and the answer template are
  always on the card; only history moves behind recall;
- M7 · deterministic projection only: the same machine state renders the same bytes.

The card keeps the field names Duck already acts on at the top level (``gate_id``, ``status``,
``next_operation``, ``current_probe``, ``instruction``, ``answer_template``). Fields the controller
certifies (evidence references, certified entity lists, the counter footprint) are shown as
``CERTIFIED`` in the template and filled by the controller when the answer arrives
(``fill_certified_fields``); Duck writes only what is Duck's to write.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from inference.framework.annotation_lane import orientation_block, orientation_due
from inference.framework.memory_store import cell_bbox as _bbox
from inference.framework.recall import recall_key, recall_slot

SCHEMA = "virelai-card-v1"
CERTIFIED = "CERTIFIED: the controller fills this field"
WINDOW = 6

# Character budgets per slot (DESIGN §5.3; tuned at M-1, see the R9-R07 slice document).
SLOT_BUDGETS: dict[str, int] = {
    "goal": 2_000,
    "subject": 2_000,
    "template": 3_000,  # current_probe + instruction, or answer_template
    "last_transition": 600,
    "world_model": 3_000,
    "recall": 2_000,  # injected recall (M-3, recall.py)
    "orientation": 600,  # present only while the orientation turn is due (M-3, annotation_lane.py)
    "progress": 1_500,
    "index": 800,
}
ENVELOPE_CHARS = 700  # schema, gate id, status, next operation, revision, card meta
CARD_BUDGET = sum(SLOT_BUDGETS.values()) + ENVELOPE_CHARS

# Template fields the controller certifies, per gate. Dotted names are nested fields.
CERTIFIED_TEMPLATE_FIELDS: dict[str, tuple[str, ...]] = {
    "G2-COUNTER": ("candidate_id", "evidence_refs", "novel_prediction.scope"),
    "G3-LEVERS": (
        "effect_summary", "evidence_refs", "lever_entities", "clean_null_entities",
        "ambiguous_entities",
    ),
    "G4-REACTIONS": ("effect_channels",),
}

GOAL_KEYS = (
    "goal_card", "unmet_requirements", "done_when", "target", "rules", "answer_contract",
    "answer_template_note", "stop_reason", "opening_protocol",
)
INDEX_BY_GATE = {
    "G2-COUNTER": ("virelai('gate_audit', offset=0, limit=20)",),
    "G3-LEVERS": (
        "virelai('inventory', offset=0, limit=10)", "virelai('entity', id=ENTITY_ID)",
        "virelai('evidence', id=EVIDENCE_ID)",
    ),
    "G4-REACTIONS": ("virelai('reaction', id=ENTITY_ID)", "virelai('entity', id=ENTITY_ID)"),
    "G4.2-LEVER-ORBITS": (
        "virelai('orbit', id=ENTITY_ID)", "virelai('rerun', id=ENTITY_ID, presses=N)",
        "virelai('memory', kind='subject', id=ENTITY_ID)",
    ),
    "G4-B-LEVER-RELATIONS": ("virelai('relations')", "virelai('orbit', id=ENTITY_ID)"),
    "G4-C-LEVER-LAW": ("virelai('relations')",),
}


def _chars(value: Any) -> int:
    return len(json.dumps(value, sort_keys=True, default=str))


def windowed(value: Any, *, window: int = WINDOW) -> Any:
    """Deterministically bound a structure: cell lists become count + bbox, long lists a window.

    A list longer than ``window`` keeps its first ``window`` items and gains a sibling
    ``<key>_remaining`` count. The ``actions`` of a capability are never windowed.
    """
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if key == "cells" and isinstance(item, (list, tuple)):
                out["cell_count"] = len(item)
                out["bbox"] = _bbox(item)
                continue
            if isinstance(item, (list, tuple)) and key != "actions" and len(item) > window:
                out[key] = [windowed(entry, window=window) for entry in item[:window]]
                out[f"{key}_remaining"] = len(item) - window
                continue
            out[key] = windowed(item, window=window)
        return out
    if isinstance(value, (list, tuple)):
        return [windowed(entry, window=window) for entry in value]
    return value


def _fill_to_budget(candidates: Sequence[tuple[str, Any]], budget: int) -> dict[str, Any]:
    """Add candidate fields in priority order while they fit; name what did not."""
    slot: dict[str, Any] = {}
    omitted: list[str] = []
    for key, value in candidates:
        if value is None:
            continue
        if _chars({**slot, key: value}) <= budget - 120:
            slot[key] = value
        else:
            omitted.append(key)
    if omitted:
        slot["omitted"] = omitted
        slot["recall"] = "virelai('gate_audit', offset=0, limit=20)"
    return slot


def _goal_card_core(goal_card: Any) -> Any:
    """The goal itself: the question and what completes it (the rest is the gate's standing text)."""
    if not isinstance(goal_card, Mapping):
        return goal_card
    return {key: goal_card[key] for key in ("goal_id", "question", "completion_predicate") if key in goal_card}


# ---- the certified template ----------------------------------------------------------------

def _mark(template: Mapping[str, Any], dotted: str) -> None:
    head, _, rest = dotted.partition(".")
    if head not in template:
        return
    if rest:
        if isinstance(template[head], dict):
            _mark(template[head], rest)
        return
    template[head] = CERTIFIED


def card_template(gate_id: str, template: Mapping[str, Any] | None) -> dict[str, Any] | None:
    """The answer template as Duck sees it: certified fields marked, everything else whole."""
    if template is None:
        return None
    shown = json.loads(json.dumps(template, default=str))
    for dotted in CERTIFIED_TEMPLATE_FIELDS.get(gate_id, ()):
        _mark(shown, dotted)
    return shown


def fill_certified_fields(machine: Any, raw: Any) -> Any:
    """Fill the certified fields Duck left out (or left marked) from the live template.

    The gate still validates every field exactly; this only spares Duck from echoing what the
    controller already certified. Anything Duck does write is kept and checked as written.
    """
    if not isinstance(raw, Mapping):
        return raw
    fields = CERTIFIED_TEMPLATE_FIELDS.get(machine.gate_id, ())
    if not fields:
        return raw
    template = machine.gate_view().get("answer_template")
    if not isinstance(template, Mapping):
        return raw
    filled = json.loads(json.dumps(raw, default=str))
    for dotted in fields:
        head, _, rest = dotted.partition(".")
        if rest:
            inner = filled.get(head)
            source = template.get(head)
            if isinstance(inner, dict) and isinstance(source, Mapping) and rest in source:
                if inner.get(rest) in (None, CERTIFIED):
                    inner[rest] = source[rest]
            continue
        if head in template and filled.get(head) in (None, CERTIFIED):
            filled[head] = template[head]
    return filled


# ---- slots -----------------------------------------------------------------------------------

def _goal_slot(view: Mapping[str, Any]) -> dict[str, Any]:
    candidates = [
        ("goal_card", _goal_card_core(view.get("goal_card"))),
        *[(key, view.get(key)) for key in GOAL_KEYS if key != "goal_card"],
    ]
    return _fill_to_budget(candidates, SLOT_BUDGETS["goal"])


def _subject_slot(gate_id: str, view: Mapping[str, Any]) -> dict[str, Any]:
    candidates: list[tuple[str, Any]] = []
    if gate_id == "G0-ACTION-METADATA":
        candidates.append(("action_metadata", view.get("action_metadata")))
    elif gate_id == "G2-COUNTER":
        candidate = view.get("candidate")
        if isinstance(candidate, Mapping):
            candidates.append(("counter_candidate", windowed({
                key: candidate.get(key)
                for key in (
                    "candidate_id", "rewrite", "footprint_geometry", "full_bar_footprint",
                    "observed_support", "amount_per_transition", "witness_transition_ids",
                    "status",
                )
                if key in candidate
            })))
        candidates.append(("record_trigger", view.get("record_trigger")))
    elif gate_id == "G3-LEVERS":
        scheduler = view.get("scheduler") if isinstance(view.get("scheduler"), Mapping) else {}
        pending = scheduler.get("pending_dossier")
        candidates.append(("pending_dossier", windowed(pending)))
        template = view.get("answer_template")
        if isinstance(template, Mapping) and not isinstance(pending, Mapping):
            candidates.append(("effect_summary", template.get("effect_summary")))
        candidates.append(("completion", view.get("completion")))
    elif gate_id == "G4-REACTIONS":
        candidates.append(("current_lever", windowed(view.get("current_lever"))))
    elif gate_id == "G4.2-LEVER-ORBITS":
        levers = view.get("levers") or ()
        active = [
            item for item in levers
            if isinstance(item, Mapping) and item.get("status") in {
                "RUNNING", "CONFIRMING", "CONFIRMED_AWAITING_EXPLANATION",
            }
        ]
        candidates.append(("active_lever", active[0] if active else None))
    elif isinstance(view.get("subject"), Mapping):  # a gate that states its own subject (G4-B)
        candidates.extend(view["subject"].items())
    candidates.append(("epistemic_limits", view.get("epistemic_limits")))
    return _fill_to_budget(candidates, SLOT_BUDGETS["subject"])


def _template_slot(gate_id: str, view: Mapping[str, Any], capability: Any) -> dict[str, Any]:
    slot: dict[str, Any] = {}
    if capability is not None:
        slot["current_probe"] = windowed(_current_work_first(capability))
        slot["instruction"] = (
            "Execute current_probe directly. Its token is current for this turn; "
            "do not reuse a token from prior history."
        )
    template = view.get("answer_template")
    templates = view.get("answer_templates") or ()
    if template is None and templates:
        template = templates[0]
    shown = card_template(gate_id, template)
    if shown is not None:
        slot["answer_template"] = shown
        if any(value == CERTIFIED for value in _leaves(shown)):
            slot["answer_template_certified"] = (
                "Fields marked CERTIFIED are filled by the controller; omit them or leave them as shown."
            )
    if len(templates) > 1:
        slot["answer_templates_pending"] = len(templates)
    return slot


LEVER_STATUS_ORDER = {  # the controller's study order: a re-study after a death before a new lever (R9-R12)
    "RUNNING": 0, "CONFIRMING": 1, "CONFIRMED_AWAITING_EXPLANATION": 2, "RUN_ENDED_RESTART_NEEDED": 3, "NOT_STARTED": 4,
}


def _current_work_first(capability: Mapping[str, Any]) -> Mapping[str, Any]:
    """Order a guided capability's lever list so the window holds the current work, not the done."""
    target = capability.get("target")
    if not isinstance(target, Mapping) or not isinstance(target.get("levers"), (list, tuple)):
        return capability
    levers = sorted(
        target["levers"],
        key=lambda item: LEVER_STATUS_ORDER.get(str(item.get("status")), 9) if isinstance(item, Mapping) else 9,
    )
    return {**capability, "target": {**target, "levers": levers}}


def _leaves(value: Any):
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _leaves(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _leaves(item)
    else:
        yield value


def _last_transition_slot(machine: Any) -> dict[str, Any] | None:
    index = getattr(machine, "transition_index", None) or []
    if not index:
        return None
    row = index[-1]
    changed = row.get("changed") or []
    return {
        "transition_id": row.get("transition_id"),
        "gate_id": row.get("gate_id"),
        "action": row.get("action"),
        "changed_cell_count": len(changed),
        "changed_bbox": _bbox([cell[:2] for cell in changed]),
        "disposition": row.get("disposition"),
        "boundary_state": row.get("boundary_state"),
    }


def _progress_slot(gate_id: str, view: Mapping[str, Any], machine: Any) -> dict[str, Any]:
    candidates: list[tuple[str, Any]] = [("progress", windowed(view.get("progress")))]
    if gate_id == "G3-LEVERS":
        frontier = view.get("inherited_frontier")
        if isinstance(frontier, Mapping):
            rows = [
                {key: row.get(key) for key in ("rank", "member_id", "entity_id", "anchor", "cell_count", "state")
                 if key in row}
                for row in (frontier.get("candidates") or ())[:WINDOW]
                if isinstance(row, Mapping)
            ]
            candidates.append(("roster_window", {
                "candidate_count": frontier.get("candidate_count"),
                "rows": rows,
            }))
        journal = view.get("lifecycle_journal")
        if isinstance(journal, Mapping):
            candidates.append(("state_counts", journal.get("state_counts")))
        for key in ("confirmed_levers", "scoped_nulls", "bounded_unknowns", "unresolved_entities"):
            block = view.get(key)
            if isinstance(block, Mapping) and "total" in block:
                candidates.append((key, block["total"]))
    elif gate_id == "G4-REACTIONS":
        candidates.append(("subject_accounting", windowed(view.get("subject_accounting"))))
    elif gate_id == "G4.2-LEVER-ORBITS":
        levers = [item for item in view.get("levers") or () if isinstance(item, Mapping)]
        counts: dict[str, int] = {}
        for item in levers:
            counts[str(item.get("status"))] = counts.get(str(item.get("status")), 0) + 1
        candidates.append(("lever_status_counts", dict(sorted(counts.items()))))
    elif gate_id == "G2-COUNTER":
        rejected = view.get("rejected_candidates")
        if isinstance(rejected, (list, tuple)):
            candidates.append(("rejected_candidate_count", len(rejected)))
    candidates.append(("budgets", world_budgets(machine)))
    return _fill_to_budget(candidates, SLOT_BUDGETS["progress"])


def _current_grid(machine: Any) -> list[list[int]] | None:
    lever = getattr(machine, "_adapters", {}).get("G3-LEVERS")
    ledger = getattr(lever, "entity_ledger", None)
    if ledger is not None and getattr(ledger, "_grid", None) is not None:
        return [list(row) for row in ledger._grid]
    counter = getattr(machine, "counter", None)
    initial = getattr(counter, "initial_grid", None)
    if initial is None:
        return None
    grid = [list(row) for row in initial]
    for row in getattr(machine, "transition_index", None) or ():
        for r, c, _before, after in row.get("changed") or ():
            if after is not None:
                grid[r][c] = after
    return grid


def world_budgets(machine: Any) -> dict[str, Any] | None:
    """The budgets the world itself imposes, once a gate has certified them."""
    product = machine.target_journal.active_product("G2-COUNTER")
    counter = getattr(machine, "counter", None)
    candidate = getattr(counter, "candidate", None)
    mask = getattr(counter, "mask_law", None)
    if product is None or candidate is None or mask is None:
        return None
    grid = _current_grid(machine)
    if grid is None:
        return None
    source = int(candidate.source_integer)
    remaining = sum(1 for r, c in mask.cells if grid[r][c] == source)
    per_tick = max(candidate.amount_per_transition or (1,))
    return {
        "counter_source_cells_remaining": remaining,
        "counter_ticks_remaining": remaining // max(1, per_tick),
        "counter_trigger": (product.payload.get("counter_model") or {}).get("trigger"),
        "derived_period_actions": product.payload.get("derived_period_actions"),
        "life": getattr(getattr(machine, "lives", None), "life", 1),  # R9-R16
    }


def _index_slot(gate_id: str, view: Mapping[str, Any]) -> list[str]:
    handles = ["virelai('gate') returns this card", *INDEX_BY_GATE.get(gate_id, ())]
    for item in view.get("expand") or ():
        if isinstance(item, Mapping) and item.get("query") and item["query"] not in handles:
            handles.append(str(item["query"]))
    lines: list[str] = []
    for handle in handles:
        if _chars([*lines, handle]) > SLOT_BUDGETS["index"]:
            break
        lines.append(handle)
    return lines


# ---- the certified world model digest ---------------------------------------------------------

def _digest_lines(machine: Any) -> list[tuple[str, str]]:
    from inference.framework.level_model import level_line

    lines = [(f"LEVEL-{model.get('level')}", f"[prior] {level_line(model)}") for model in getattr(machine, "levels", ())]
    carry = getattr(machine, "carry", None)
    if carry is not None and carry.line():
        lines.append(("G9-CARRY", f"[carry] {carry.line()}"))
    for row in machine.completed_gate_rows():
        gate = row["gate_id"]
        payload = row["answer"]
        for text in _render_product(machine, gate, payload) or [f"certified {row['product_type']} rev {row['revision']}"]:
            lines.append((gate, f"[{gate}] {text}"))
    return lines


def _render_product(machine: Any, gate: str, payload: Mapping[str, Any]) -> list[str]:
    if gate == "G0-ACTION-METADATA":
        actions = [
            f"{item.get('action')}{'(coordinates)' if item.get('requires_coordinates') else ''}"
            for item in payload.get("action_metadata") or ()
        ]
        return [f"actions: {', '.join(actions)}"]
    if gate == "G1-EGO":
        return [f"ego: {payload.get('mode')}"]
    if gate == "G2-COUNTER":
        model = payload.get("counter_model") or {}
        candidate = getattr(machine.counter, "candidate", None)
        mask = payload.get("mask_law") or {}
        shape = (
            f"{candidate.footprint_geometry} {len(mask.get('cells') or ())} cells "
            f"{candidate.rewrite} x{max(candidate.amount_per_transition or (0,))} per tick"
            if candidate is not None else "counter"
        )
        return [
            f"counter: {shape} · trigger {model.get('trigger')} · status {model.get('status')} · "
            f"period {payload.get('derived_period_actions')} effective actions · masked"
        ]
    if gate == "G3-LEVERS":
        return _render_levers(machine, payload)
    if gate == "G4-REACTIONS":
        groups: dict[str, list[str]] = {}
        for anatomy in payload.get("anatomies") or ():
            signature = "; ".join(
                f"{ch.get('locality')} {ch.get('transform')} {ch.get('changed_cell_count')} cells "
                f"{','.join(f'{a}->{b}' for a, b, _n in ch.get('integer_transitions') or ())}"
                for ch in anatomy.get("channels") or ()
            )
            groups.setdefault(signature, []).append(str(anatomy.get("entity_id")))
        return [f"anatomy x{len(ids)}: {signature} · {_ids(ids)}" for signature, ids in groups.items()]
    if gate == "G4.2-LEVER-ORBITS":
        classes: dict[str, list[str]] = {}
        for entity_id, klass in sorted((payload.get("lever_classes") or {}).items()):
            classes.setdefault(str(klass), []).append(entity_id)
        summary = ", ".join(f"{klass} x{len(ids)} {_ids(ids)}" for klass, ids in classes.items())
        return [
            f"orbits: {summary or 'none yet'} · phase1 {payload.get('phase1_status')} · "
            f"pending {len(payload.get('pending_lever_entities') or ())} · "
            f"interrupted {len(payload.get('interrupted_lever_entities') or ())}"
        ]
    return list(payload.get("digest_lines") or ())  # a gate that renders its own lines (G4-B)


def _ids(ids: Sequence[str], limit: int = 4) -> str:
    shown = ",".join(ids[:limit])
    return f"{{{shown}{f' +{len(ids) - limit}' if len(ids) > limit else ''}}}"


def _render_levers(machine: Any, payload: Mapping[str, Any]) -> list[str]:
    lever = machine._adapters.get("G3-LEVERS")
    ledger = getattr(lever, "entity_ledger", None)
    dossiers = getattr(lever, "_dossier_answers", {}) or {}
    groups: dict[str, list[str]] = {}
    for entity_id in payload.get("lever_entities") or ():
        members = sorted(ledger.entities[entity_id].member_ids) if ledger is not None and entity_id in ledger.entities else []
        summary = next((dossiers[m].effect_summary for m in members if m in dossiers), None) or {}
        signature = (
            f"local {summary.get('local_changed_cell_count')} cells, "
            f"remote {summary.get('remote_changed_cell_count')} cells"
        )
        groups.setdefault(signature, []).append(str(entity_id))
    lines = [f"levers x{len(ids)}: {signature} · {_ids(ids)}" for signature, ids in groups.items()]
    lines.append(
        f"roster: {len(payload.get('lever_entities') or ())} levers, "
        f"{len(payload.get('clean_null_entities') or ())} scoped nulls, "
        f"{len(payload.get('ambiguous_entities') or ())} unresolved"
    )
    return lines


def world_model_digest(machine: Any, budget: int = SLOT_BUDGETS["world_model"]) -> list[str]:
    """One line per certified fact, grouped by identical signature, bounded by collapsing the oldest."""
    lines = _digest_lines(machine)
    collapsed: set[str] = set()
    gates = list(dict.fromkeys(gate for gate, _ in lines))
    while _chars([text for _, text in lines]) > budget and len(collapsed) < len(gates):
        oldest = next(gate for gate in gates if gate not in collapsed)
        collapsed.add(oldest)
        kept = [(gate, text) for gate, text in lines if gate != oldest]
        position = next((i for i, (gate, _) in enumerate(lines) if gate == oldest), 0)
        kept.insert(position, (oldest, f"[{oldest}] certified; recall virelai('gate_audit')"))
        lines = kept
    return [text for _, text in lines] + _uncertified_lines(machine, [text for _, text in lines], budget)


def _uncertified_lines(machine: Any, certified: list[str], budget: int) -> list[str]:
    """Duck's notes, newest first, only in the room the certified lines leave (D6)."""
    lane = getattr(machine, "annotations", None)
    notes = list(reversed(lane.notes)) if lane is not None else []
    shown: list[str] = []
    for note in notes:
        if _chars([*certified, *shown, note.line()]) > budget - 80:
            break
        shown.append(note.line())
    if len(shown) < len(notes):
        shown.append(f"[UNCERTIFIED] {len(notes) - len(shown)} more notes: virelai('memory', kind='notes')")
    return shown


# ---- the card ----------------------------------------------------------------------------------

@dataclass
class Card:
    payload: dict[str, Any]
    slot_chars: dict[str, int] = field(default_factory=dict)
    over_budget: list[str] = field(default_factory=list)

    def render(self) -> str:
        return json.dumps(self.payload, sort_keys=True, default=str)


def build_card(machine: Any) -> Card:
    view = machine.gate_view()
    capability = None
    if view.get("next_operation") in {"QUERY_NEXT_PROBE", "QUERY_NEXT_G3_TARGET"}:
        capability = machine.next_probe_capability()
        if capability is None:
            # Asking for the next probe can close an exhausted roster; render the state it left.
            view = machine.gate_view()
    gate_id = machine.gate_id
    next_operation = view.get("next_operation")
    slots: dict[str, Any] = {
        "goal": _goal_slot(view),
        "subject": _subject_slot(gate_id, view),
        "template": _template_slot(gate_id, view, capability),
        "last_transition": _last_transition_slot(machine),
        "world_model": world_model_digest(machine),
        "recall": recall_slot(machine, recall_key(gate_id, view, capability)),
        "progress": _progress_slot(gate_id, view, machine),
        "index": _index_slot(gate_id, view),
    }
    if orientation_due(machine):
        slots["orientation"] = orientation_block(machine, next_operation)
        next_operation = "SUBMIT_ORIENTATION"
    slot_chars = {name: _chars(value) for name, value in slots.items() if value}
    over = sorted(name for name, size in slot_chars.items() if size > SLOT_BUDGETS[name])
    template = slots.pop("template")
    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "gate_id": gate_id,
        "revision": view.get("revision"),
        "status": view.get("status"),
        "next_operation": next_operation,
        **template,
        **{name: value for name, value in slots.items() if value},
        "card": {"slot_chars": slot_chars, "budget": CARD_BUDGET, **({"over_budget": over} if over else {})},
    }
    return Card(payload=payload, slot_chars=slot_chars, over_budget=over)


def worst_case_request_chars(*, system_prompt_chars: int, tool_schema_chars: int, prompt_body_chars: int,
                             tool_output_chars: int, output_reserve_chars: int) -> int:
    """Packager preflight (T10): the largest request a turn can make, with every slot at budget."""
    return (
        system_prompt_chars + tool_schema_chars + prompt_body_chars + CARD_BUDGET
        + tool_output_chars + output_reserve_chars
    )
