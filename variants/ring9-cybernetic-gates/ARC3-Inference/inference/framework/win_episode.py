"""The observed-win episode: one retrospective record of the life that cleared a level, never a winning rule.

Author: Claude (Alpha build seat), 2026-10-19 (WO-WIN-01; INTERFACE_WO_WIN_01_v1). Pure projection, compiled where
the census is: once at H1 (``attach``, from ``library_census.freeze_census_or_failure``, before the ended level is
frozen) and again whenever a model is sealed (``reconcile``, from ``world_model_v2.seal``, after the dossiers'
provenance reconciliation: H2, the interim write and the live view). Never on the controller path, never per step.

What it states, all read from the sealed level and the H1 boundary:

* identity: the level, the life, the winning transition, its action, actor and evidence receipt, the entry board and
  the board hashes either side of the clear;
* the clear as a boundary, not a transformation (revision 2, Sol's review): the after-board is the game's next-level
  spawn, so no winning render or terminal visual transformation was observed (``clear.visual_status``). The
  winning transition's ledger events are kept only as an uninterpreted ``clear.boundary_delta`` (their ids resolve
  for audit) and never reach the participants, the counts, the explanations or the state;
* the semantic window: the whole winning life before the clear, in record order, from just after its entry or reset;
  resets and deaths are never actions, and no "minimal suffix" is inferred;
* each participant: a certified role only through ``description.role_bindings``, a census track handle, or an
  unresolved region with its identity gap; never a role from appearance;
* each event's stored explanation status (``descriptive_events.explain``, recomputed by the description validator):
  nothing causal is derived here, and no Duck text is ever read;
* its honest limits. It is one observation: it claims neither necessity nor sufficiency.

``derive(level, boundary)`` is the whole episode; the v10 validator (``win_episode_check``) recomputes it and refuses
any stored episode that differs.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence

EPISODE_SCHEMA = "virelai-win-episode-v1"
NOT_OBSERVED, FAILED_CLOSED = "NOT_OBSERVED", "FAILED_CLOSED"
OBSERVED_STATES = ("OBSERVED", "OBSERVED_PARTLY_EXPLAINED", "OBSERVED_UNEXPLAINED")
STATES = (NOT_OBSERVED, *OBSERVED_STATES, FAILED_CLOSED)
FAILURES = ("NOT_A_LEVEL_CLEAR", "BOARD_DISAGREES", "RECORD_MISMATCH", "RECEIPT_UNRESOLVED", "WINDOW_BROKEN",
            "COMPILE_ERROR", "NOT_COMPILED_AT_H1")
KINDS = ("BOUND_ROLE", "TRACK", "UNRESOLVED_REGION")
CLAIM = "RETROSPECTIVE_ONLY"
TERMINAL_VISUAL = "SUCCESSOR_SPAWN_NOT_WINNING_RENDER"  # the clear's after-board is the next level's spawn
DELTA_EXCLUDED = ("participants", "verb_counts", "explanations", "patterns", "state")
EXPLAINED_STATUSES = ("EXPLAINED", "PARTLY_EXPLAINED")


class EpisodeFailure(Exception):
    """The episode fails closed: nothing is claimed but the reason."""

    def __init__(self, reason: str, detail: str) -> None:
        super().__init__(f"{reason}: {detail}")
        self.reason, self.detail = reason, detail


def not_observed() -> dict[str, Any]:
    return {"schema": EPISODE_SCHEMA, "state": NOT_OBSERVED}


def failed(boundary: Mapping[str, Any] | None, reason: str, detail: str) -> dict[str, Any]:
    episode: dict[str, Any] = {"schema": EPISODE_SCHEMA, "state": FAILED_CLOSED,
                               "failure": {"reason": reason, "detail": detail}}
    if boundary is not None:
        episode["boundary"] = dict(boundary)
    return episode


def board_sha256(board: Sequence[Sequence[int]]) -> str:
    """The census's board hash (``library_census.compile_level``'s entry ``board_sha256``)."""
    return hashlib.sha256(repr([list(row) for row in board]).encode()).hexdigest()


# ---- H1 ------------------------------------------------------------------------------------------------------------

def attach(machine: Any, census: Mapping[str, Any], outcome: Mapping[str, Any]) -> dict[str, Any]:
    """The frozen census with its ``win_episode``. Never raises: a compile error fails the episode closed."""
    if "census_failed" in census:
        return dict(census)
    boundary = None
    try:
        boundary = _boundary(machine, census, outcome)
        episode = derive(census, boundary)
    except EpisodeFailure as exc:
        episode = failed(boundary, exc.reason, exc.detail)
    except Exception as exc:  # noqa: BLE001 - recorded, never raised into the gate machine
        episode = failed(boundary, "COMPILE_ERROR", type(exc).__name__)
    return {**census, "win_episode": episode}


def _boundary(machine: Any, census: Mapping[str, Any], outcome: Mapping[str, Any]) -> dict[str, Any]:
    """What only H1 sees: the boundary event and the boards either side of the clear (replayed from the record and,
    when the outcome carries lossless grids, checked against them)."""
    event = outcome.get("boundary_event") if isinstance(outcome.get("boundary_event"), Mapping) else {}
    t = int(outcome.get("transition_id") or 0)
    rows = sorted((row for row in machine.transition_index if row.get("level") == census["level"]),
                  key=lambda row: int(row["transition_id"]))
    row = next((item for item in rows if int(item["transition_id"]) == t), {})
    pre, post = _replayed(machine.ego._initial_grid, rows, t)
    after = event.get("level_after")
    boundary = {"kind": "LEVEL_CLEAR" if event.get("level_completed") else "LEVEL_CHANGE", "transition_id": t,
                "level_before": int(event.get("level_before") if event.get("level_before") is not None else -1),
                "level_after": None if after is None else int(after), "state": event.get("state"),
                "life": int(row.get("life") or 0), "pre_board_sha256": pre, "successor_entry_sha256": post}
    if boundary["kind"] != "LEVEL_CLEAR":
        raise EpisodeFailure("NOT_A_LEVEL_CLEAR", f"the level changed at t{t} without a recorded level clear")
    _check_grids(outcome, pre, post, boundary)
    return boundary


def _replayed(entry: Sequence[Sequence[int]], rows: Sequence[Mapping[str, Any]], t: int) -> tuple[str, str]:
    """The board hashes just before and just after ``t``: the entry board with every recorded change applied."""
    board = [list(row) for row in entry]
    pre = None
    for row in rows:
        if int(row["transition_id"]) == t:
            pre = board_sha256(board)
        for cell in row.get("changed") or ():
            board[int(cell[0])][int(cell[1])] = int(cell[3])
        if int(row["transition_id"]) == t:
            break
    if pre is None:
        raise EpisodeFailure("WINDOW_BROKEN", f"t{t} is not a recorded transition of this level")
    return pre, board_sha256(board)


def _check_grids(outcome: Mapping[str, Any], pre: str, post: str, boundary: Mapping[str, Any]) -> None:
    from inference.framework.masked_world_state import grids_from_probe_outcome

    grids = grids_from_probe_outcome(outcome)
    if grids is not None and (board_sha256(grids[0]) != pre or board_sha256(grids[1]) != post):
        raise EpisodeFailure("BOARD_DISAGREES", f"the replayed record disagrees with the outcome's boards at "
                                                f"t{boundary['transition_id']}")


# ---- H2: every seal ------------------------------------------------------------------------------------------------

def reconcile(levels: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Every level with its episode, re-derived from the settled level: an open level or a level never cleared is
    NOT_OBSERVED; a frozen level H1 never compiled fails closed; a failed episode is never upgraded."""
    out = []
    for level in levels:
        episode = level.get("win_episode")
        if episode is None:
            episode = failed(None, "NOT_COMPILED_AT_H1", "no H1 episode") if level.get("state") == "FROZEN" \
                else not_observed()
        elif episode.get("state") in OBSERVED_STATES:
            try:
                episode = derive(level, episode["boundary"])
            except EpisodeFailure as exc:
                episode = failed(episode["boundary"], exc.reason, exc.detail)
        out.append({**level, "win_episode": episode})
    return out


# ---- the episode -------------------------------------------------------------------------------------------------

def derive(level: Mapping[str, Any], boundary: Mapping[str, Any]) -> dict[str, Any]:
    """The whole observed episode, from the level and the H1 boundary alone (raises ``EpisodeFailure``)."""
    t = int(boundary["transition_id"])
    records = {int(r["transition_id"]): r for r in level["description"]["transitions"]}
    _check_level(level, boundary, records)
    opened, window, prior = window_records(level, int(boundary["life"]), t)
    semantic, terminal = window[:-1], records[t]  # the clear is a boundary: its after-board is the next spawn
    receipt = level["receipts"]["evidence"][terminal["evidence_ref"]]
    transitions = [_transition(record) for record in semantic]
    participants = _participants(level, semantic)
    explanations = _explanations(semantic)
    entry = {key: level["entry"][key] for key in ("source", "after_transition", "board_sha256") if key in level["entry"]}
    return {
        "schema": EPISODE_SCHEMA,
        "state": _state(explanations),
        "boundary": dict(boundary),
        "identity": {"level": int(level["level"]), "life": int(boundary["life"]), "winning_transition": t,
                     "terminal_action": terminal["action"], "actor": terminal["actor"],
                     "evidence_ref": terminal["evidence_ref"],
                     "receipt": {"gate_id": receipt.get("gate_id"), "probe_id": receipt.get("probe_id")}, "entry": entry},
        "clear": {"transition_id": t, "visual_status": TERMINAL_VISUAL,
                  "boundary_delta": {"event_ids": [e["event_id"] for e in terminal["events"]],
                                     "events": len(terminal["events"]), "excluded_from": list(DELTA_EXCLUDED)}},
        "window": {"opened_by": opened, "first_transition": window[0]["transition_id"], "clear_transition": t,
                   "actions": len(window), "semantic_transitions": len(semantic), "prior_lives": prior},
        "transitions": transitions,
        "participants": participants,
        "explanations": explanations,
        "limits": _limits(level, transitions, participants),
    }


def _check_level(level: Mapping[str, Any], boundary: Mapping[str, Any], records: Mapping[int, Mapping]) -> None:
    """The record must show this clear and nothing after it, verified and receipted, or the episode fails closed."""
    t = int(boundary["transition_id"])
    ids = list(level["record"]["transition_ids"])
    if boundary.get("kind") != "LEVEL_CLEAR" or boundary.get("level_before") != level["level"]:
        raise EpisodeFailure("NOT_A_LEVEL_CLEAR", f"the boundary is not this level's clear (level {level['level']})")
    if t not in ids or t != max(ids) or t in (level["record"].get("reset_transition_ids") or ()) \
            or len(set(ids)) != len(ids) or t not in records or records[t].get("kind") == "RESET":
        raise EpisodeFailure("WINDOW_BROKEN", f"t{t} is not the level's last recorded, non-reset transition")
    check = level["record"]["journal_check"]
    mismatch = level["description"].get("first_mismatch")
    listed = [int(r["transition_id"]) for r in level["description"]["transitions"]]
    if (check.get("status") == "CHECKED" and not check.get("ok")) or (mismatch and mismatch["transition_id"] <= t) \
            or sorted(listed) != sorted(ids):
        raise EpisodeFailure("RECORD_MISMATCH", "a recorded transition of the level is missing, duplicated or contradicted")
    ref = records[t].get("evidence_ref")
    if not ref or (level["receipts"]["evidence"].get(ref) or {}).get("transition_id") != t:
        raise EpisodeFailure("RECEIPT_UNRESOLVED", f"the winning transition t{t} has no evidence receipt of its own")


def window_records(level: Mapping[str, Any], life: int,
                   t: int) -> tuple[dict[str, Any], list[Mapping[str, Any]], list[dict[str, Any]]]:
    """(what opened the winning life, its records after that through ``t`` (the clear last), the earlier lives)."""
    order = {tid: index for index, tid in enumerate(level["record"]["transition_ids"])}
    records = sorted(level["description"]["transitions"], key=lambda r: order.get(r["transition_id"], len(order)))
    mine = [r for r in records if r.get("life") == life]
    if not mine or mine[-1]["transition_id"] != t or any(r.get("level") != level["level"] for r in mine):
        raise EpisodeFailure("WINDOW_BROKEN", f"life {life}'s records of the level do not end at t{t}")
    start = records.index(mine[0])
    if records[start:start + len(mine)] != mine:
        raise EpisodeFailure("WINDOW_BROKEN", f"life {life}'s records are not contiguous")
    if mine[0].get("kind") == "RESET":
        opened, window = {"kind": "RESET", "transition_id": mine[0]["transition_id"]}, mine[1:]
    else:
        if start:
            raise EpisodeFailure("WINDOW_BROKEN", f"life {life} began inside the level without a reset")
        opened = {"kind": level["entry"]["source"], "after_transition": int(level["entry"].get("after_transition") or 0)}
        window = mine
    if not window or any(r.get("record_status") != "VERIFIED" or r.get("kind") == "RESET" for r in window):
        raise EpisodeFailure("RECORD_MISMATCH", f"life {life}'s window holds an unverified or reset record")
    return opened, window, _prior_lives(records[:start])


def _prior_lives(records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    lives: dict[int, list[int]] = {}
    for record in records:
        lives.setdefault(int(record.get("life") or 0), []).append(int(record["transition_id"]))
    return [{"life": life, "first_transition": ids[0], "last_transition": ids[-1]} for life, ids in lives.items()]


def _transition(record: Mapping[str, Any]) -> dict[str, Any]:
    return {"transition_id": record["transition_id"], "action": record["action"], "actor": record["actor"],
            "evidence_ref": record["evidence_ref"],
            "events": [{"event_id": e["event_id"], "track_id": e["subject"]["track_id"], "verb": e["verb"],
                        "explanation": e["explanation"]["status"]} for e in record["events"]]}


def _participants(level: Mapping[str, Any], window: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Each track the window's events name: its bindings (the only source of roles), its join and identity gaps."""
    tracks = {track["track_id"]: track for track in level["observation"]["tracks"]}
    unresolved = {gap["subject"] for gap in level["gaps"] if gap.get("reason") == "IDENTITY_UNRESOLVED"}
    events: dict[str, list[Mapping[str, Any]]] = {}
    for record in window:
        for event in record["events"]:
            events.setdefault(event["subject"]["track_id"], []).append(event)
    out = []
    for track_id in sorted(events):
        roles = sorted(({"role": b["role"], "gate_id": b["gate_id"], "role_ref": b["role_ref"],
                         "ends_at_transition": b["ends_at_transition"]}
                        for b in level["description"]["role_bindings"] if b["track_id"] == track_id),
                       key=lambda item: (item["role"], str(item["role_ref"])))
        gaps = _identity_gaps(events[track_id], track_id in unresolved)
        join = (tracks.get(track_id) or {}).get("g3_join") or {}
        kind = "BOUND_ROLE" if roles else "UNRESOLVED_REGION" if gaps else "TRACK"
        out.append({"track_id": track_id, "kind": kind, "roles": roles, "g3_join": join.get("entity_id"),
                    "identity_gaps": gaps, "events": len(events[track_id])})
    return out


def _identity_gaps(events: Sequence[Mapping[str, Any]], unresolved: bool) -> list[dict[str, Any]]:
    ambiguous = sorted({int(e["transition_id"]) for e in events
                        if e["verb"] == "AMBIGUOUS" or (e.get("correspondence") or {}).get("ambiguity")})
    gaps = [{"reason": "AMBIGUOUS_CORRESPONDENCE", "transitions": ambiguous}] if ambiguous else []
    return gaps + ([{"reason": "IDENTITY_UNRESOLVED", "transitions": []}] if unresolved else [])


def _explanations(window: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """The stored explanation statuses of the semantic window's change events, counted; nothing is re-derived."""
    counts = {status: 0 for status in ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED")}
    refs, bases, still = set(), set(), 0
    for record in window:
        for event in record["events"]:
            if event["verb"] == "STILL":
                still += 1
                continue
            explanation = event["explanation"]
            counts[explanation["status"]] += 1
            refs.update(explanation["refs"])
            bases.add(explanation["basis"])
    return {**counts, "still": still, "refs": sorted(refs), "bases": sorted(bases)}


def _state(explanations: Mapping[str, Any]) -> str:
    explained, partly, unexplained = (explanations[s] for s in ("EXPLAINED", "PARTLY_EXPLAINED", "UNEXPLAINED"))
    if explained and not partly and not unexplained:
        return "OBSERVED"
    return "OBSERVED_PARTLY_EXPLAINED" if explained or partly else "OBSERVED_UNEXPLAINED"


def _limits(level: Mapping[str, Any], transitions: Sequence[Mapping[str, Any]],
            participants: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """What the episode does not know at the win, stated."""
    unexplained = [item["transition_id"] for item in transitions
                   if any(e["verb"] != "STILL" for e in item["events"])
                   and not any(e["verb"] != "STILL" and e["explanation"] in EXPLAINED_STATUSES for e in item["events"])]
    gaps = [p["track_id"] for p in participants
            if p["kind"] == "UNRESOLVED_REGION" or (p["kind"] == "TRACK" and p["g3_join"] is None)]
    chapters = [{"entity_id": entity_id, "chapter": name, "status": chapter["status"]}
                for entity_id, dossier in sorted((level.get("lever_dossiers") or {}).items())
                for name, chapter in sorted(dossier["chapters"].items()) if chapter["status"] != "COMPLETE"]
    unbound = sorted(({"role": role["role"], "gate_id": role["gate_id"]} for role in level["certified"]["roles"]
                      if not (role.get("identity") or {}).get("track_id")), key=lambda item: (item["role"], item["gate_id"]))
    return {"unexplained_transitions": unexplained, "identity_gaps": gaps, "incomplete_chapters": chapters,
            "unbound_roles": unbound, "terminal_visual": TERMINAL_VISUAL, "observations": 1, "claim": CLAIM}


__all__ = ["CLAIM", "DELTA_EXCLUDED", "EPISODE_SCHEMA", "EpisodeFailure", "FAILED_CLOSED", "FAILURES", "KINDS", "NOT_OBSERVED",
           "OBSERVED_STATES", "STATES", "TERMINAL_VISUAL", "attach", "board_sha256", "derive", "failed", "not_observed", "reconcile",
           "window_records"]
