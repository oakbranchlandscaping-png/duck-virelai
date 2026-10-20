"""World model v10: every level's ``win_episode`` against the level that holds it (WO-WIN-01, interface §4).

Author: Claude (Alpha build seat), 2026-10-19. A v10 validation step only (frozen readers v1-v9 never run it), called
by ``world_model_v2`` after the v9 rules. Pure: it reads the model and ``win_episode`` (constants, ``derive`` and
``window_records``), never the gate machine. Each refusal names its rule, and every hash a forger can reach is
assumed recomputed: the check is against the record, never against a seal.

Rules for an observed episode (``OBSERVED``, ``OBSERVED_PARTLY_EXPLAINED``, ``OBSERVED_UNEXPLAINED``):

1. the winning transition is in the level's recorded transitions;
2. its boundary is this level's ``LEVEL_CLEAR``, the level is FROZEN, the transition is no reset, and the next level,
   when the model holds it, entered at that transition;
3. the terminal action, actor and evidence receipt resolve to that transition;
4. the semantic window begins at the first record after the winning life's entry or reset and ends just before the
   clear;
5. every listed transition is a record of this level and life, and never the clear;
6. every event resolves to the descriptive ledger (id, track, verb, explanation status), and the clear's boundary
   delta is exactly the winning transition's ledger events, in order (revision 2: kept for audit, never counted);
7. every participant resolves to a role binding, a census track, or a declared unresolved region with its gap;
8. every explanation reference resolves to a product, evidence or witness receipt, a dossier or a binding;
9. the successor-entry hash equals the next level's entry board hash, when the model holds that level;
10. no transition after the win: it is the level's last record;
11. no participant belongs to another level, the next level's entry tracks included;
12. the stored episode equals its recompilation, byte for byte.

And for every level: an OPEN level is ``NOT_OBSERVED``; a level the record shows cleared (FROZEN, and another level
entered after its last transition) never is; a failed episode names a known reason and claims nothing else. What it
cannot check, stated: the pre-win board hash (the model stores no boards; H1 checked it against the replayed record),
and rule 9 when the next level is absent (a final win).
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from inference.framework import win_episode as W


class _Refused(Exception):
    pass


def _rule(condition: bool, number: int, message: str) -> None:
    if not condition:
        raise _Refused(f"rule {number}: {message}")


def problems(levels: Sequence[Mapping[str, Any]]) -> list[str]:
    """Every way the model's win episodes break the v10 contract (empty when they hold)."""
    found = []
    by_number = {level.get("level"): level for level in levels}
    for level in levels:
        try:
            _level(level, by_number)
        except _Refused as exc:
            found.append(f"win episode of level {level.get('level')}: {exc}")
    return found


def _level(level: Mapping[str, Any], by_number: Mapping[Any, Mapping[str, Any]]) -> None:
    episode = level.get("win_episode")
    if not isinstance(episode, Mapping) or episode.get("schema") != W.EPISODE_SCHEMA:
        raise _Refused(f"every v10 level holds a {W.EPISODE_SCHEMA} episode")
    state = episode.get("state")
    if state not in W.STATES:
        raise _Refused(f"unknown state {state!r}")
    if level.get("state") == "OPEN" and state != W.NOT_OBSERVED:
        raise _Refused("an open level has observed no clear")
    if state == W.NOT_OBSERVED and _recorded_clear(level, by_number.values()):
        raise _Refused("the record shows this level's clear (the next level entered at its last transition): its "
                       "episode is observed or failed closed")
    if state == W.NOT_OBSERVED:
        if set(episode) != {"schema", "state"}:
            raise _Refused("a NOT_OBSERVED episode claims nothing")
    elif state == W.FAILED_CLOSED:
        failure = episode.get("failure") or {}
        if failure.get("reason") not in W.FAILURES or not set(episode) <= {"schema", "state", "boundary", "failure"}:
            raise _Refused("a failed episode names a known reason and claims nothing else")
    else:
        _observed(level, episode, by_number)


def _recorded_clear(level: Mapping[str, Any], levels: Any) -> bool:
    """The persisted proof of a clear: a FROZEN level whose last transition another level entered after."""
    ids = (level.get("record") or {}).get("transition_ids") or ()
    return level.get("state") == "FROZEN" and bool(ids) and any(
        other is not level and (other.get("entry") or {}).get("source") == "LEVEL_ENTRY"
        and (other.get("entry") or {}).get("after_transition") == max(ids) for other in levels)


def _observed(level: Mapping[str, Any], episode: Mapping[str, Any], by_number: Mapping[Any, Mapping]) -> None:
    boundary = episode.get("boundary") or {}
    t = boundary.get("transition_id")
    records = {r["transition_id"]: r for r in level["description"]["transitions"]}
    record = records.get(t) or {}
    nxt = by_number.get(boundary.get("level_after"))
    _rule(t in level["record"]["transition_ids"], 1, f"t{t} is not a recorded transition of the level")
    _rule(boundary.get("kind") == "LEVEL_CLEAR" and boundary.get("level_before") == level["level"]
          and boundary.get("level_after") != level["level"], 2, "the boundary is not this level's clear")
    _rule(t not in (level["record"].get("reset_transition_ids") or ()) and record.get("kind") != "RESET", 2,
          f"t{t} is a reset, not a level clear")
    _rule(nxt is None or (nxt["entry"].get("source") == "LEVEL_ENTRY" and nxt["entry"].get("after_transition") == t), 2,
          f"the next level did not enter at t{t}")
    _terminal(level, episode, record, t)
    _window(level, episode, records, boundary)
    _events(episode, records, t)
    _participants(level, episode, nxt)
    _references(level, episode)
    _rule(nxt is None or nxt["entry"].get("board_sha256") == boundary.get("successor_entry_sha256"), 9,
          "the successor-entry hash is not the next level's entry board")
    try:
        recompiled = W.derive(level, boundary)
    except W.EpisodeFailure as exc:
        raise _Refused(f"rule 12: the level fails the episode closed ({exc.reason})") from None
    differs = sorted(key for key in set(recompiled) | set(episode) if recompiled.get(key) != episode.get(key))
    _rule(not differs, 12, f"the stored episode differs from its recompilation at {', '.join(differs)}")


def _terminal(level: Mapping[str, Any], episode: Mapping[str, Any], record: Mapping[str, Any], t: Any) -> None:
    identity = episode.get("identity") or {}
    ref = identity.get("evidence_ref")
    receipt = level["receipts"]["evidence"].get(ref) or {}
    _rule(identity.get("winning_transition") == t and identity.get("terminal_action") == record.get("action")
          and identity.get("actor") == record.get("actor"), 3, "the terminal action or actor is not the winning transition's")
    _rule(ref == record.get("evidence_ref") and receipt.get("transition_id") == t, 3,
          f"the evidence receipt {ref} does not resolve to t{t}")


def _window(level: Mapping[str, Any], episode: Mapping[str, Any], records: Mapping[Any, Mapping],
            boundary: Mapping[str, Any]) -> None:
    listed = [item.get("transition_id") for item in episode.get("transitions") or ()]
    t, life = boundary.get("transition_id"), boundary.get("life")
    ids = level["record"]["transition_ids"]
    _rule(all(isinstance(i, int) and i <= t for i in listed) and t == max(ids), 10,
          "a listed transition lies after the win, or the win is not the level's last record")
    _rule(t not in listed, 5, f"the clear t{t} is a boundary, never a listed transformation")
    _rule(all(records.get(i, {}).get("level") == level["level"] and records.get(i, {}).get("life") == life
              and records.get(i, {}).get("kind") != "RESET" for i in listed), 5,
          "a listed transition is not a record of this level and life")
    try:
        opened, window, _prior = W.window_records(level, life, t)
    except W.EpisodeFailure as exc:
        raise _Refused(f"rule 4: {exc.detail}") from None
    _rule(listed == [r["transition_id"] for r in window[:-1]] and (episode.get("window") or {}).get("opened_by") == opened, 4,
          "the window does not begin immediately after the winning life's entry or reset")


def _events(episode: Mapping[str, Any], records: Mapping[Any, Mapping], t: Any) -> None:
    delta = ((episode.get("clear") or {}).get("boundary_delta") or {}).get("event_ids")
    _rule(delta == [e["event_id"] for e in (records.get(t) or {}).get("events") or ()], 6,
          f"the boundary delta is not exactly the clear t{t}'s ledger events")
    for item in episode.get("transitions") or ():
        ledger = {e["event_id"]: e for e in records[item["transition_id"]]["events"]}
        for event in item.get("events") or ():
            found = ledger.get(event.get("event_id"))
            _rule(found is not None and found["subject"]["track_id"] == event.get("track_id")
                  and found["verb"] == event.get("verb") and found["explanation"]["status"] == event.get("explanation"),
                  6, f"event {event.get('event_id')} does not resolve to the descriptive ledger")


def _participants(level: Mapping[str, Any], episode: Mapping[str, Any], nxt: Mapping[str, Any] | None) -> None:
    tracks = {track["track_id"] for track in level["observation"]["tracks"]}
    elsewhere = {track["track_id"] for track in (nxt or {}).get("observation", {}).get("tracks") or ()}
    bindings = level["description"]["role_bindings"]
    for item in episode.get("participants") or ():
        track = item.get("track_id")
        _rule(track in tracks and track not in elsewhere, 11, f"participant {track} is not a track of this level")
        bound = sorted((b["role"], b["gate_id"], b["role_ref"], b["ends_at_transition"]) for b in bindings
                       if b["track_id"] == track)
        stated = sorted((r.get("role"), r.get("gate_id"), r.get("role_ref"), r.get("ends_at_transition"))
                        for r in item.get("roles") or ())
        _rule(item.get("kind") in W.KINDS and stated == bound and (item["kind"] == "BOUND_ROLE") == bool(bound), 7,
              f"participant {track}'s roles are not its role bindings")
        _rule(item["kind"] != "UNRESOLVED_REGION" or bool(item.get("identity_gaps")), 7,
              f"unresolved region {track} declares no identity gap")


def _references(level: Mapping[str, Any], episode: Mapping[str, Any]) -> None:
    receipts = level["receipts"]
    known = set(receipts["evidence"]) | set(receipts["products"]) | set(receipts["witnesses"])
    known |= set(level.get("lever_dossiers") or {}) | {str(b["role_ref"]) for b in level["description"]["role_bindings"]}
    unresolved = [ref for ref in (episode.get("explanations") or {}).get("refs") or () if ref not in known]
    _rule(not unresolved, 8, f"explanation reference {unresolved[:1]} resolves to no product, witness, dossier or receipt")


__all__ = ["problems"]
