"""WO-G4-DOSSIER-A revision 2: an anatomy channel's exact observed events and its affected subject (blockers 3, 4).

Author: Claude (Alpha build seat), 2026-10-17. Sol's revision-2 directive.

Pure over the level's stored description; shared by the compiler (``lever_dossiers``) and the validator
(``lever_dossier_schema``), so a stored link that the description does not support is refused.

* **Event links.** The channel's witness transition is the described transition whose ``evidence_ref`` is the
  anatomy's witness evidence. A descriptive event there is linked when its changed footprint (the CHANGED cells of
  its membership groups) is non-empty and lies inside the channel's recorded residue. Only the reference is stored:
  event id, transition id and observational verb. The link is an observed effect associated with the certified
  activation; the mechanism stays certified at the G4 gate, never inferred here.
* **Affected subject.** A channel names a census track only through an exact, unique footprint match at the witness
  transition: a linked event whose changed footprint equals the residue and whose every recorded side (before,
  after) has exactly the residue's bounding box and cell count, on a track of this level. Anything else (no match,
  two matches, a track of another level, an undescribed transition) stays ``UNRESOLVED_REGION``. Proximity, colour
  and later appearance never join. A join is observational context; it certifies no role.
"""
from __future__ import annotations

from typing import Any, Iterable, Mapping, Sequence

from inference.framework.descriptive_events import run_cells

Cell = tuple[int, int]
EVENT_STATUSES = ("LINKED", "NO_MATCHING_EVENT", "TRANSITION_NOT_DESCRIBED")
SUBJECT_KEY = "EXACT_EVENT_FOOTPRINT"
LINK_KEYS = ("events", "event_status", "subject")


def changed_cells(event: Mapping[str, Any]) -> set[Cell]:
    """The cells an event changed: the CHANGED members of its footprint's groups."""
    groups = ((event.get("delta") or {}).get("footprint") or {}).get("membership_groups") or {}
    cells: set[Cell] = set()
    for items in groups.values():
        for item in items or ():
            if item.get("outcome") == "CHANGED":
                cells |= run_cells(item.get("cell_runs") or ())
    return cells


def witness_transition(level: Mapping[str, Any], evidence_ref: Any) -> Mapping[str, Any] | None:
    if evidence_ref is None:
        return None
    return next((record for record in (level.get("description") or {}).get("transitions") or ()
                 if record.get("evidence_ref") == evidence_ref), None)


def track_ids(level: Mapping[str, Any]) -> set[str]:
    return {str(track.get("track_id")) for track in (level.get("observation") or {}).get("tracks") or ()}


def _exact(event: Mapping[str, Any], cells: set[Cell], bbox: Sequence[int], tracks: set[str]) -> bool:
    sides = [side for side in (event.get("before"), event.get("after")) if isinstance(side, Mapping)]
    return (changed_cells(event) == cells and bool(sides) and (event.get("subject") or {}).get("track_id") in tracks
            and all(list(side.get("bbox") or ()) == list(bbox) and side.get("cell_count") == len(cells) for side in sides))


def link_channel(channel: Mapping[str, Any], transition: Mapping[str, Any] | None, tracks: Iterable[str]) -> dict:
    """``{events, event_status, subject}`` of one channel at its witness transition (``None``: not described)."""
    if transition is None:
        return {"events": [], "event_status": "TRANSITION_NOT_DESCRIBED",
                "subject": {"status": "UNRESOLVED_REGION", "reason": "TRANSITION_NOT_DESCRIBED"}}
    cells = run_cells(channel.get("cell_runs") or ())
    linked = [event for event in transition.get("events") or ()
              if (footprint := changed_cells(event)) and footprint <= cells]
    refs = [{"event_id": str(event["event_id"]), "transition_id": int(transition["transition_id"]),
             "verb": str(event.get("verb"))} for event in sorted(linked, key=lambda event: str(event["event_id"]))]
    exact = [event for event in linked if _exact(event, cells, channel.get("bbox") or (), set(tracks))]
    if len(exact) == 1:
        subject = {"status": "EXACT_TRACK", "track_id": str(exact[0]["subject"]["track_id"]),
                   "basis": {"key": SUBJECT_KEY, "event_id": str(exact[0]["event_id"]),
                             "transition_id": int(transition["transition_id"])}}
    else:
        subject = {"status": "UNRESOLVED_REGION", "reason": "AMBIGUOUS_MATCH" if exact else "NO_EXACT_MATCH"}
    return {"events": refs, "event_status": "LINKED" if refs else "NO_MATCHING_EVENT", "subject": subject}


def link_anatomy(facts: Mapping[str, Any] | None, level: Mapping[str, Any]) -> Any:
    """Anatomy facts with every channel's links recomputed from the level's description (``None`` stays ``None``)."""
    if facts is None:
        return None
    transition = witness_transition(level, facts.get("witness_evidence_ref"))
    tracks = track_ids(level)
    channels = [{**{key: value for key, value in channel.items() if key not in LINK_KEYS},
                 **link_channel(channel, transition, tracks)} for channel in facts.get("channels") or ()]
    return {**facts, "channels": channels}


def unresolved(facts: Mapping[str, Any] | None) -> bool:
    """Whether any channel of stored anatomy facts still has an unresolved affected subject."""
    return any((channel.get("subject") or {}).get("status") != "EXACT_TRACK"
               for channel in (facts or {}).get("channels") or ())


def link_problem(channel: Mapping[str, Any], level: Mapping[str, Any], witness: Any) -> str | None:
    """Why a stored channel's links are not the ones its description supports (``None`` when they are)."""
    transition = witness_transition(level, witness)
    events = {str(event.get("event_id")): event for record in (level.get("description") or {}).get("transitions") or ()
              for event in record.get("events") or () if event.get("transition_id") == record.get("transition_id")}
    cells = run_cells(channel.get("cell_runs") or ())
    for ref in channel.get("events") or ():
        event = events.get(str(ref.get("event_id")))
        if event is None or event.get("transition_id") != ref.get("transition_id") or event.get("verb") != ref.get("verb"):
            return f"event {ref.get('event_id')} is not an observed event at transition {ref.get('transition_id')}"
        if transition is None or ref.get("transition_id") != transition.get("transition_id"):
            return f"event {ref.get('event_id')} is not at the anatomy's witness transition"
        if not changed_cells(event) & cells:
            return f"event {ref.get('event_id')} does not intersect the certified residue"
    expected = link_channel(channel, transition, track_ids(level))
    if channel.get("events") != expected["events"] or channel.get("event_status") != expected["event_status"]:
        return "the event links are not exactly the observed events the residue covers"
    if channel.get("subject") != expected["subject"]:
        return "the subject track join is not the unique exact footprint match at the witness transition"
    return None


__all__ = ["EVENT_STATUSES", "LINK_KEYS", "SUBJECT_KEY", "changed_cells", "link_anatomy", "link_channel",
           "link_problem", "track_ids", "unresolved", "witness_transition"]
