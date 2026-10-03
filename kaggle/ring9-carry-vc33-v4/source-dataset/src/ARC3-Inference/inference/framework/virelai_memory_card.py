"""Compact player-facing index into Virelai's persistent evidence.

The card is a view, not a second model.  It contains only bounded summaries and
stable query handles; detailed claims remain in the canonical runtime archive.
"""
from __future__ import annotations

from typing import Any


CARD_SCHEMA = "virelai-expandable-memory-card-v1"


def build_memory_card(
    *,
    entered_level: int,
    completed_level: int | None,
    world_mode: str,
    win: dict[str, Any] | None,
    mechanics: dict[str, Any] | None,
    carry: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a bounded index plus expansion handles for a newly entered level."""
    win = dict(win or {})
    mechanics = dict(mechanics or {})
    carry = dict(carry or {})
    all_controls = list(mechanics.get("controls") or ())
    controls = [
        item for item in all_controls
        if item.get("presentation_ready", True)
    ][:4]
    controls_total = int(mechanics.get("controls_total") or len(all_controls))
    controls_not_player_ready = sum(
        not item.get("presentation_ready", True) for item in all_controls
    )
    shared_mechanics = list(mechanics.get("shared_mechanics") or ())[:3]
    shared_total = int(
        mechanics.get("shared_mechanics_total")
        or len(mechanics.get("shared_mechanics") or ())
    )
    correspondences = list(carry.get("candidate_controls") or ())[:4]

    known = []
    for item in controls:
        known.append({
            "name": item.get("name") or "observed control",
            "kind": item.get("kind") or "UNKNOWN",
            "location": item.get("location"),
            "effect": item.get("mechanism") or "effect not compressed",
            "affected_regions": list(item.get("affected_regions") or ())[:2],
            "observations": int(item.get("observations") or 0),
            "period": item.get("period"),
            "periods": list(item.get("periods") or ())[:3],
        })

    returned = []
    for item in correspondences:
        returned.append({
            "prior_control": item.get("prior_control"),
            "prior_location": item.get("prior_location"),
            "candidate_locations": list(item.get("candidate_locations") or ())[:3],
            "status": "UNTESTED",
        })

    previous_win = None
    if completed_level and win:
        previous_win = {
            "completed_level": completed_level,
            "winning_action": win.get("winning_action"),
            "acted_cell": win.get("acted_cell"),
            "explanation_status": win.get("status") or "UNMEASURED",
            "earlier_same_action_failures": int(
                win.get("earlier_same_action_failures") or 0
            ),
            "distinguishing_conditions": list(
                win.get("distinguishing_conditions") or ()
            )[:2],
            "causal_limit": win.get("causal_limit")
            or "The winning transition was observed; its cause is not proven.",
        }

    level = completed_level or max(1, entered_level - 1)
    handles = [
        {
            "label": "previous win",
            "query": f"virelai('win', level={level})",
            "provides": "winning edge and contrast with earlier failures",
        },
        {
            "label": "known mechanics",
            "query": f"virelai('mechanics', level={level})",
            "provides": "observed controls, effects and affected regions",
        },
        {
            "label": "level comparison",
            "query": f"virelai('carry', level={level})",
            "provides": "untested counterparts in the new level",
        },
        {
            "label": "full lesson",
            "query": f"virelai('lesson', level={level}, detail='full')",
            "provides": "full evidence-linked lesson and limitations",
        },
    ]

    unknowns = []
    if previous_win:
        unknowns.append("The causal condition of the previous win is not proven.")
    if returned:
        unknowns.append("Candidate counterparts in this level are not confirmed identities.")
    else:
        unknowns.append("No cross-level control counterpart has been established.")
    unknowns.append("Prior-level mechanics may change and must be checked against this level.")

    card = {
        "schema": CARD_SCHEMA,
        "entered_level": entered_level,
        "world_mode": world_mode or "UNKNOWN",
        "previous_win": previous_win,
        "known_mechanics": known,
        "shared_mechanics": shared_mechanics,
        "level_comparison": returned,
        "unknowns": unknowns,
        "display": {
            "controls_shown": len(known),
            "controls_total": controls_total,
            "controls_omitted": max(
                0, controls_total - len(known) - controls_not_player_ready
            ),
            "controls_not_player_ready": controls_not_player_ready,
            "shared_mechanics_shown": len(shared_mechanics),
            "shared_mechanics_total": shared_total,
            "shared_mechanics_omitted": max(0, shared_total - len(shared_mechanics)),
        },
        "expand": handles,
    }
    card["text"] = render_memory_card(card)
    return card


def render_memory_card(card: dict[str, Any]) -> str:
    """Render a short index in player language; never dump internal identifiers."""
    lines = [
        f"VIRELAI WORLD MEMORY — LEVEL {card['entered_level']}",
        f"WORLD: {card.get('world_mode') or 'UNKNOWN'}",
        "",
        "PREVIOUS WIN",
    ]
    win = card.get("previous_win")
    if win:
        lines.append(
            f"- Level {win['completed_level']} ended after {win.get('winning_action')}; "
            f"acted cell={win.get('acted_cell')}."
        )
        lines.append(
            f"- Explanation status: {win.get('explanation_status')}; the same action failed "
            f"{win.get('earlier_same_action_failures', 0)} earlier time(s)."
        )
        conditions = win.get("distinguishing_conditions") or []
        if conditions:
            lines.append(f"- Pre-win separators observed: {conditions}.")
    else:
        lines.append("- No previous-level win is recorded.")

    lines.extend(["", "KNOWN MECHANICS"])
    mechanics = card.get("known_mechanics") or []
    if mechanics:
        for item in mechanics:
            lines.append(
                f"- {item['name']} [{item['kind']}] at {item.get('location')}: "
                f"{item['effect']}; affected={item.get('affected_regions')}; "
                f"period={item.get('period') or item.get('periods') or 'unmeasured'}; "
                f"observed {item.get('observations', 0)} time(s)."
            )
    else:
        lines.append("- No control mechanic has been established.")
    for relation in card.get("shared_mechanics") or []:
        lines.append(
            f"- Shared relation [{relation.get('kind') or 'OBSERVED'}]: "
            f"{relation.get('controls')} {relation.get('relationship') or 'share effects'}; "
            f"affected={list(relation.get('affected_regions') or ())[:2]}."
        )
    display = card.get("display") or {}
    omitted = int(display.get("controls_omitted") or 0) + int(
        display.get("shared_mechanics_omitted") or 0
    )
    if omitted:
        lines.append(
            f"- Display limit: {omitted} additional established mechanic record(s) omitted; "
            "expand known mechanics to inspect them."
        )
    not_ready = int(display.get("controls_not_player_ready") or 0)
    if not_ready:
        lines.append(
            f"- Presentation limit: {not_ready} additional raw control record(s) lack "
            "a usable location or effect summary; expand known mechanics to inspect them."
        )

    lines.extend(["", "LEVEL COMPARISON"])
    comparison = card.get("level_comparison") or []
    if comparison:
        for item in comparison:
            lines.append(
                f"- {item.get('prior_control')} from {item.get('prior_location')} may correspond "
                f"to {item.get('candidate_locations')} here [UNTESTED]."
            )
    else:
        lines.append("- No cross-level counterpart has been established.")

    lines.extend(["", "UNKNOWNS"])
    lines.extend(f"- {item}" for item in card.get("unknowns") or [])
    lines.extend(["", "EXPAND IF USEFUL"])
    lines.extend(
        f"- {item['label']}: {item['query']}"
        for item in card.get("expand") or []
    )
    lines.append("This is observational memory, not a required plan.")
    return "\n".join(lines)


__all__ = ["CARD_SCHEMA", "build_memory_card", "render_memory_card"]
