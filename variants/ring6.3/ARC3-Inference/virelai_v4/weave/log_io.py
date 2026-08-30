"""WO_INDUCED_MAP · capture-log serialization — the read-sidecar that lets a
live-captured log cross from the Director's capture run to a sandbox render.

Pure and dependency-light: stdlib only. It READS a ``FrameRecordLog`` (duck-typed
``.records``) and writes JSON; it loads that JSON back into minimal record-likes
the induced-map merge consumes. It never mutates the log and derives nothing —
it carries only the four fields the map is built from, plus context fields kept
for legibility.

The edge is the composite ``(action_id, target)`` EdgeKey. JSON has no tuples, so
a coordinate ``target`` round-trips through a list and is restored to a tuple on
load; a keyed action's ``None`` target round-trips as ``null``. This keeps edge
labels hashable and identical across the serialize/deserialize boundary, which
the induced map's set semantics (and thus I3) require.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

Label = Optional[Tuple[int, Any]]


@dataclass(frozen=True)
class LogRecord:
    """A minimal, frozen record-like: exactly the fields the merge reads, plus
    context fields carried for the render (never used by the graph)."""

    node_index: int
    layered_hash: str
    edge: Label
    full_reset: bool
    state: str = ""
    available_actions: Tuple[int, ...] = ()


def _to_tuple_target(target: Any) -> Any:
    """Restore a JSON-listified coordinate target to a tuple; pass None / scalars
    through. Nested lists (unlikely for a coordinate) recurse."""
    if isinstance(target, list):
        return tuple(_to_tuple_target(t) for t in target)
    return target


def _edge_to_json(edge: Label) -> Any:
    if edge is None:
        return None
    action_id, target = edge
    return [action_id, target]


def _edge_from_json(raw: Any) -> Label:
    if raw is None:
        return None
    action_id, target = raw
    return (int(action_id), _to_tuple_target(target))


def records_to_dicts(records: Any) -> List[dict]:
    """Read a ``FrameRecordLog`` (or any iterable of record-likes) into plain
    dicts. Additive read only — the log is untouched."""
    out: List[dict] = []
    seq = records.records if hasattr(records, "records") else records
    for r in seq:
        out.append({
            "node_index": int(r.node_index),
            "layered_hash": str(r.layered_hash),
            "edge": _edge_to_json(getattr(r, "edge", None)),
            "full_reset": bool(getattr(r, "full_reset", False)),
            "state": str(getattr(r, "state", "") or ""),
            "available_actions": [int(a) for a in (getattr(r, "available_actions", ()) or ())],
        })
    return out


def dump_log(records: Any, path: str) -> int:
    """Serialize a captured log to ``path`` as JSON. Returns the record count."""
    dicts = records_to_dicts(records)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"records": dicts}, fh)
    return len(dicts)


def dicts_to_records(dicts: List[dict]) -> List[LogRecord]:
    out: List[LogRecord] = []
    for d in dicts:
        out.append(LogRecord(
            node_index=int(d["node_index"]),
            layered_hash=str(d["layered_hash"]),
            edge=_edge_from_json(d.get("edge")),
            full_reset=bool(d.get("full_reset", False)),
            state=str(d.get("state", "") or ""),
            available_actions=tuple(int(a) for a in (d.get("available_actions") or ())),
        ))
    return out


def load_log(path: str) -> List[LogRecord]:
    """Load a serialized capture log into record-likes for the merge."""
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    dicts = payload["records"] if isinstance(payload, dict) else payload
    return dicts_to_records(dicts)
