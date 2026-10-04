"""The level freeze: when a level ends, its model is frozen and the ladder starts again on the next.

Author: Claude (Alpha build seat), 2026-10-01. R9-R17 (MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1 §4, L1;
DESIGN_VIRELAI_MEMORY_v2 M9). Director rulings 2026-10-01: carry hypotheses only (G0-G2 run again
on each level; nothing carried is a verdict there); "learn how to win" is recorded only.

``freeze_level`` builds ``LevelModel(L)`` from the gate machine's own certified products and record
(never from the observer's win capsule: the belief state is the only brain). It holds every
LEVEL-tier product of the level whole, a compact lever roster, Duck's uncertified notes, the
level's lives, and, when the level was won, the win record:

- the winning transition, its action and probe, and the lever whose click it was, if any;
- every earlier use of the same action on the level that did not end it. If there is one, the
  win needed more than the action (the board it was taken from mattered): recorded as the
  hypothesis WIN_NEEDS_CONTEXT_BEYOND_THE_ACTION, status UNTESTED. Nothing seeks it.

The frozen model is evidence about level L only. On the next level it is shown as unconfirmed
prior-level knowledge; G9 (R9-R18) matches and re-confirms it. Port precedent: virelai_v4
``library/substrate/level_advance.py`` (snapshot, then rebuild from the new level's spawn).
"""
from __future__ import annotations

from typing import Any, Mapping

SCHEMA = "virelai-level-model-v1"
UNTESTED = "UNTESTED"


def _levers(products: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    inventory = products.get("G3-LEVERS") or {}
    anatomies = {item.get("entity_id"): item for item in (products.get("G4-REACTIONS") or {}).get("anatomies") or ()}
    orbits = products.get("G4.2-LEVER-ORBITS") or {}
    explained = {item.get("entity_id") for item in orbits.get("answers") or ()}
    interrupted = set(orbits.get("interrupted_lever_entities") or ())
    rows = []
    for entity in inventory.get("lever_entities") or ():
        anatomy = anatomies.get(entity) or {}
        rows.append({
            "entity_id": entity,
            "click": anatomy.get("intervention"),
            "channels": [f"{ch.get('locality')} {ch.get('transform')} {ch.get('changed_cell_count')}"
                         for ch in anatomy.get("channels") or ()],
            "locality": sorted({ch.get("locality") for ch in anatomy.get("channels") or () if ch.get("locality")}),
            "orbit_class": (orbits.get("lever_classes") or {}).get(entity),
            "study": "EXPLAINED" if entity in explained else "INTERRUPTED" if entity in interrupted else "NOT_STUDIED",
        })
    return rows


def _orbit_views(machine: Any, levers: list[dict[str, Any]]) -> dict[str, Any]:
    """Each lever's G4-A study as it stood (runs, states, status), for G9's re-confirmation (R9-R18)."""
    if machine.gate_id not in {"G4.2-LEVER-ORBITS", "G4-B-LEVER-RELATIONS", "G4-C-LEVER-LAW"}:
        return {}
    return {item["entity_id"]: machine.orbit_view(item["entity_id"]) for item in levers}


def _win(machine: Any, outcome: Mapping[str, Any], level: int | None, levers: list[dict[str, Any]]) -> dict[str, Any] | None:
    boundary = outcome.get("boundary_event") if isinstance(outcome.get("boundary_event"), Mapping) else {}
    if not boundary.get("level_completed"):
        return None
    action = dict(outcome.get("action") or {})
    won_at = int(outcome.get("transition_id") or 0)
    earlier = [
        row["transition_id"] for row in machine.transition_index
        if row.get("kind") == "PROBE" and row.get("level") == level and row.get("action") == action
        and row["transition_id"] < won_at
    ]
    row = next((item for item in reversed(machine.transition_index) if item.get("transition_id") == won_at), {})
    return {
        "transition_id": won_at, "action": action, "probe_id": row.get("probe_id"), "gate_id": row.get("gate_id"),
        "acted_lever": next((item["entity_id"] for item in levers if item.get("click") == action), None),
        "earlier_same_action": earlier,
        "hypothesis": "WIN_NEEDS_CONTEXT_BEYOND_THE_ACTION" if earlier else "NO_EARLIER_USE_OF_THE_ACTION",
        "status": UNTESTED,
    }


def freeze_level(machine: Any, outcome: Mapping[str, Any]) -> dict[str, Any]:
    """``LevelModel(L)`` at the transition that ended level L (call before the next level is built)."""
    boundary = outcome.get("boundary_event") if isinstance(outcome.get("boundary_event"), Mapping) else {}
    level = boundary.get("level_before")
    from inference.framework.carry import lever_signatures

    products = {row["gate_id"]: row["answer"] for row in machine.completed_gate_rows()}
    levers = [{**item, "signatures": lever_signatures(machine, item["entity_id"])} for item in _levers(products)]
    return {
        "schema": SCHEMA, "level": level, "level_after": boundary.get("level_after"),
        "frozen_at_transition": int(outcome.get("transition_id") or 0), "gate_at_freeze": machine.gate_id,
        "carry_status": "UNCONFIRMED",  # hypotheses only on the next level (ruling 2026-10-01)
        "products": products, "product_types": {row["gate_id"]: row["product_type"] for row in machine.completed_gate_rows()},
        "levers": levers, "orbit_views": _orbit_views(machine, levers), "win": _win(machine, outcome, level, levers),
        "lives": [item for item in machine.lives.summary() if item.get("level") == level],
        "notes": [note.line() for note in getattr(machine.annotations, "notes", ())],
        "mu": machine.mu.snapshot() if hasattr(machine, "mu") else [],  # R9-R23 D16: the level's open questions
    }


def level_line(model: Mapping[str, Any]) -> str:
    """One card line: what level L established, marked unconfirmed on this level."""
    levers = ", ".join(
        f"{item['entity_id']} {item.get('orbit_class') or item['study'].lower()}" for item in model.get("levers") or ()
    ) or "no levers certified"
    win = model.get("win")
    won = "" if win is None else (
        f"; won at t{win['transition_id']} by {win['action'].get('action')}"
        f"({win['action'].get('row')},{win['action'].get('col')})"
        + (f" on {win['acted_lever']}" if win.get("acted_lever") else "")
        + (f", same action failed {len(win['earlier_same_action'])}x before (context mattered, UNTESTED)"
           if win.get("earlier_same_action") else "")
    )
    return (f"level {model.get('level')} (frozen, unconfirmed here): {levers}; G4 reached "
            f"{model.get('gate_at_freeze')}{won}")


def compact(model: Mapping[str, Any]) -> dict[str, Any]:
    """The memory view of a frozen level: everything but the whole products and lever studies."""
    return {key: value for key, value in model.items() if key not in {"products", "orbit_views"}}


__all__ = ["SCHEMA", "compact", "freeze_level", "level_line"]
