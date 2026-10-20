"""What Duck and the report show of a win episode: compact, read-only, and never a winning rule (WO-WIN-01).

Author: Claude (Alpha build seat), 2026-10-19 (INTERFACE_WO_WIN_01_v1 §5). Pure renderings of a stored episode in a
model the caller has already validated (v10): the world report's section, the ``win_episode`` library page and the
digest's optional ``win`` line. Each says the episode is one retrospective observation; none says it is a rule, a
strategy or a way to win, and none claims necessity or sufficiency. Revision 2 (Sol's review): each says the game
supplied the next level's entry board at the clear, so no winning render or terminal visual transformation was
observed; the clear's board-replacement events are never described as level physics.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping, Sequence

from inference.framework.win_episode import OBSERVED_STATES

PAGE_CALL = "virelai('library', kind='win_episode', level={level})"
LIFE = {"OBSERVED": "explained", "OBSERVED_PARTLY_EXPLAINED": "partly explained", "OBSERVED_UNEXPLAINED": "unexplained"}


def no_render(episode: Mapping[str, Any], *, short: bool = False) -> str:
    """What the clear's after-board is, and what was therefore not observed."""
    after = episode["boundary"].get("level_after")
    seen = "no winning render was observed" if short else \
        "no winning render or terminal visual transformation was observed"
    if after is None:
        return f"the record holds no winning render after the clear, so {seen}"
    return f"the game immediately supplied level {after}'s entry board, so {seen}"


def _action(action: Mapping[str, Any] | None) -> str:
    action = action or {}
    where = f"({action['row']},{action['col']})" if action.get("row") is not None else ""
    return f"{action.get('action')}{where}"


def _claim(text: str, refs: Sequence[Any]) -> str:
    return f"{text}; refs: {', '.join(str(ref) for ref in refs)}"


def _opened(window: Mapping[str, Any]) -> str:
    opened = window["opened_by"]
    if opened["kind"] == "RESET":
        return f"after the reset at t{opened['transition_id']}"
    return "after the initial frame" if opened["kind"] == "INITIAL_FRAME" else "after the level entry"


# ---- the world report --------------------------------------------------------------------------------------------

def report_lines(level: Mapping[str, Any], at: str) -> list[str]:
    """The level's ``### Win episode`` section (nothing when no clear was observed)."""
    episode = level.get("win_episode") or {}
    path = f"{at}.win_episode"
    if episode.get("state") == "FAILED_CLOSED":
        return ["### Win episode", "", _claim(f"- the level's win episode failed closed: {episode['failure']['reason']}; "
                                              "nothing is claimed about it", [path]), ""]
    if episode.get("state") not in OBSERVED_STATES:
        return []
    identity, limits, delta = episode["identity"], episode["limits"], episode["clear"]["boundary_delta"]
    return ["### Win episode", "",
            _claim(f"- level {identity['level']} cleared at t{identity['winning_transition']} by "
                   f"{_action(identity['terminal_action'])} ({identity['actor']}) in life {identity['life']}: one "
                   "retrospective observation, not a winning rule", [path, identity["evidence_ref"]]),
            _life_line(episode, path),
            _claim(f"- {no_render(episode)}; the clear's {delta['events']} recorded board-replacement events stay an "
                   "uninterpreted boundary delta, never counted as level physics", [f"{path}.clear"]),
            _participant_line(episode, path),
            _claim(f"- limits: transitions with no known mechanism {len(limits['unexplained_transitions'])}; objects "
                   f"without an identity join {len(limits['identity_gaps'])}; dossier chapters incomplete at the win "
                   f"{len(limits['incomplete_chapters'])}; neither necessity nor sufficiency is claimed",
                   [f"{path}.limits"]),
            ""]


def _participant_line(episode: Mapping[str, Any], path: str) -> str:
    kinds = {kind: [p for p in episode["participants"] if p["kind"] == kind]
             for kind in ("BOUND_ROLE", "TRACK", "UNRESOLVED_REGION")}
    roles = ", ".join(f"{r['role']} {r['role_ref']}" for p in kinds["BOUND_ROLE"] for r in p["roles"]) or "no role"
    return _claim(f"- participants: {len(kinds['BOUND_ROLE'])} bound through role bindings ({roles}), "
                  f"{len(kinds['TRACK'])} census tracks, {len(kinds['UNRESOLVED_REGION'])} unresolved regions",
                  [f"{path}.participants"])


def _life_line(episode: Mapping[str, Any], path: str) -> str:
    """The semantic window: the life before the clear, and how much of it the stored explanations cover."""
    window, counts, items = episode["window"], episode["explanations"], episode["transitions"]
    if not items:
        return _claim(f"- the preceding life holds no action before the clear ({_opened(window)}); state "
                      f"{episode['state']}", [f"{path}.window"])
    span = f"t{items[0]['transition_id']}-t{items[-1]['transition_id']}"
    changes = sum(counts[s] for s in ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED"))
    return _claim(f"- the preceding life is {LIFE[episode['state']]}: {len(items)} actions {_opened(window)}, {span}, "
                  f"with {changes} change events (EXPLAINED {counts['EXPLAINED']}, PARTLY_EXPLAINED "
                  f"{counts['PARTLY_EXPLAINED']}, UNEXPLAINED {counts['UNEXPLAINED']}); "
                  f"{len(window['prior_lives'])} earlier lives on this level; state {episode['state']}",
                  [f"{path}.window", f"{path}.explanations", span])


# ---- the library page and the digest ---------------------------------------------------------------------------

def page(page_head: dict[str, Any], level: Mapping[str, Any], offset: Any, limit: Any,
         paged: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    """The ``win_episode`` page: the episode's summary and its clear, then the life before the clear, paged."""
    episode = level.get("win_episode") or {}
    if episode.get("state") not in OBSERVED_STATES:
        head = {**page_head, "episode": {"state": episode.get("state"),
                                         **({"failure": episode["failure"]} if "failure" in episode else {})}}
        return paged(head, [], offset, limit, {"kind": "win_episode", "level": level["level"]})
    limits = episode["limits"]
    summary = {
        "state": episode["state"], "claim": limits["claim"], "observations": limits["observations"],
        "identity": {key: episode["identity"][key] for key in ("level", "life", "winning_transition",
                                                                "terminal_action", "actor", "evidence_ref")},
        "clear": {"transition_id": episode["clear"]["transition_id"], "visual_status": episode["clear"]["visual_status"],
                  "boundary_delta_events": episode["clear"]["boundary_delta"]["events"],
                  "observed": no_render(episode)},
        "window": {key: episode["window"][key] for key in ("first_transition", "clear_transition", "actions",
                                                            "semantic_transitions")},
        "explanations": {key: episode["explanations"][key] for key in ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED")},
        "participants": {kind: sum(1 for p in episode["participants"] if p["kind"] == kind)
                         for kind in ("BOUND_ROLE", "TRACK", "UNRESOLVED_REGION")},
        "limits": {"unexplained_transitions": len(limits["unexplained_transitions"]),
                   "identity_gaps": len(limits["identity_gaps"]),
                   "incomplete_chapters": len(limits["incomplete_chapters"])},
    }
    rows = [{"transition_id": item["transition_id"], "action": _action(item["action"]), "actor": item["actor"],
             "evidence_ref": item["evidence_ref"], "verbs": _verbs(item["events"]),
             "explained": sum(1 for e in item["events"] if e["explanation"] != "UNEXPLAINED")}
            for item in episode["transitions"]]
    return paged({**page_head, "episode": summary}, rows, offset, limit, {"kind": "win_episode", "level": level["level"]})


def _verbs(events: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        counts[event["verb"]] = counts.get(event["verb"], 0) + 1
    return dict(sorted(counts.items()))


def digest_lines(model: Mapping[str, Any]) -> list[str]:
    """One line per observed episode, the latest level first."""
    lines = []
    for level in sorted(model["levels"], key=lambda item: -int(item["level"])):
        episode = level.get("win_episode") or {}
        if episode.get("state") not in OBSERVED_STATES:
            continue
        identity = episode["identity"]
        lines.append(f"L{identity['level']} cleared at t{identity['winning_transition']} by "
                     f"{_action(identity['terminal_action'])} in life {identity['life']} after "
                     f"{episode['window']['actions']} actions; the preceding life is {LIFE[episode['state']]}; "
                     f"{no_render(episode, short=True)}; one retrospective observation: "
                     + PAGE_CALL.format(level=identity["level"]))
    return lines


def with_win(model: Mapping[str, Any], digest: dict[str, Any], budget: int,
             render: Callable[[Mapping[str, Any]], str]) -> dict[str, Any]:
    """The fitted digest plus as many win lines as still fit the one section; the digest itself is never reduced."""
    lines = digest_lines(model)
    while lines and len(render({**digest, "win": lines})) > budget:
        lines = lines[:-1]
    return {**digest, "win": lines} if lines else digest


__all__ = ["digest_lines", "no_render", "page", "report_lines", "with_win"]
