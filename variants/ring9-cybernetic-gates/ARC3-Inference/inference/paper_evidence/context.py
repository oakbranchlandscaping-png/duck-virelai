"""One level of a sealed v11 model, indexed for claim projection (WO-PE-03B).

Author: Claude (Alpha build seat), 2026-10-25. Interface: ``INTERFACE_WO_PE_03BCD_v1_2026-10-25`` §2.

Pure reads of the canonical model: tracks by id, entities to their tracks, the level's entry board hash, each gate's
active product and its origin, and the provenance answer rows of the level. Nothing here derives a fact the model
does not state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from inference.paper_evidence import claims as c


@dataclass
class LevelContext:
    game_id: str
    level: Mapping[str, Any]
    answer_rows: list[Mapping[str, Any]] = field(default_factory=list)
    tracks: dict[str, Mapping[str, Any]] = field(default_factory=dict)
    entity_tracks: dict[str, str] = field(default_factory=dict)
    products: dict[str, Mapping[str, Any]] = field(default_factory=dict)  # gate_id -> product_content entry
    product_ids: dict[str, str] = field(default_factory=dict)  # gate_id -> product_id

    @property
    def number(self) -> int:
        return int(self.level["level"])

    @property
    def entry_sha256(self) -> str | None:
        return (self.level.get("entry") or {}).get("board_sha256")


def _entity_tracks(level: Mapping[str, Any], tracks: Mapping[str, Mapping[str, Any]]) -> dict[str, str]:
    """Entity to track, from the census joins and the certified roles' identities (exact one-to-one only)."""
    found: dict[str, str] = {}
    for track_id, track in tracks.items():
        join = track.get("g3_join") or {}
        if join.get("entity_id") and join.get("status") == "EXACT_ONE_TO_ONE":
            found.setdefault(join["entity_id"], track_id)
    for role in level["certified"]["roles"]:
        identity = role.get("identity") or {}
        if identity.get("status") == "EXACT_ONE_TO_ONE" and identity.get("track_id") in tracks:
            found.setdefault(role["entity_id"], identity["track_id"])
    return found


def level_context(model: Mapping[str, Any], level: Mapping[str, Any]) -> LevelContext:
    tracks = {track["track_id"]: track for track in (level.get("observation") or {}).get("tracks") or ()}
    gates = {row["gate_id"]: row["product_id"] for row in level["certified"]["gates"] if row.get("product_id")}
    content = level.get("product_content") or {}
    rows = [row for row in (model.get("provenance") or {}).get("rows") or ()
            if row.get("operation") == "ANSWER" and row.get("event") == "ADMISSION"
            and row.get("level") == level["level"]]
    return LevelContext(game_id=str(model["game_id"]), level=level, answer_rows=rows, tracks=tracks,
                        entity_tracks=_entity_tracks(level, tracks),
                        products={gate: content[pid] for gate, pid in gates.items() if pid in content},
                        product_ids=gates)


def _composite(ctx: LevelContext, entity_id: str) -> dict[str, Any] | None:
    """A composite lever ``{A=B}``: the union of its members' first sightings, when every member is located."""
    members = [part for part in entity_id.strip("{}").split("=") if part]
    parts = [entity_subject(ctx, member) for member in members]
    if len(parts) < 2 or any(part["geometry"] is None for part in parts):
        return None
    shapes = [part["geometry"] for part in parts]
    boxes = [shape["bbox"] for shape in shapes]
    at_entry = all(shape["frame"] == "ENTRY" for shape in shapes)
    classes = {shape["class"] for shape in shapes}
    bbox = [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)]
    return {"type": "OBJECT", "handle": "+".join(part["handle"] for part in parts),
            "geometry": {"frame": "ENTRY" if at_entry else next(s["frame"] for s in shapes if s["frame"] != "ENTRY"),
                         "board_sha256": ctx.entry_sha256 if at_entry else None,
                         "class": classes.pop() if len(classes) == 1 else None, "anchor": bbox[:2], "bbox": bbox,
                         "cell_count": sum(shape["cell_count"] for shape in shapes)},
            "trace": {"track_id": None, "entity_id": entity_id,
                      "members": [part["trace"]["track_id"] for part in parts]}}


def entity_subject(ctx: LevelContext, entity_id: str | None) -> dict[str, Any]:
    """An entity's canonical subject: its track's first sighting, a composite's union, or an unresolved object."""
    if entity_id and str(entity_id).startswith("{") and (found := _composite(ctx, str(entity_id))) is not None:
        return found
    track_id = ctx.entity_tracks.get(str(entity_id)) if entity_id else None
    if track_id is not None:
        return c.track_subject(ctx.tracks[track_id], ctx.entry_sha256)
    # No exact track: the subject cannot be located, so it can never join a key's geometry (it is UNMATCHED).
    return {"type": "OBJECT", "handle": f"unresolved:{entity_id}", "geometry": None,
            "trace": {"track_id": None, "entity_id": entity_id}}


def track_or_level(ctx: LevelContext, ref: str | None) -> dict[str, Any]:
    """The subject a gap or pattern names: a track, an entity, or the level itself."""
    if ref in ctx.tracks:
        return c.track_subject(ctx.tracks[ref], ctx.entry_sha256)
    if ref in ctx.entity_tracks:
        return entity_subject(ctx, ref)
    return c.plain_subject("LEVEL", f"level-{ctx.number}", {"ref": ref})


def role_subject(ctx: LevelContext, role: str) -> dict[str, Any] | None:
    """The track the certified role (EGO or COUNTER) is bound to, when it is bound exactly."""
    for row in ctx.level["certified"]["roles"]:
        identity = row.get("identity") or {}
        if row["role"] == role and identity.get("track_id") in ctx.tracks:
            return c.track_subject(ctx.tracks[identity["track_id"]], ctx.entry_sha256)
    return None


def _mask_geometry(ctx: LevelContext) -> dict[str, Any] | None:
    """The counter mask's cells as geometry (the G2 product's mask law), when the counter has no bound track."""
    payload = (ctx.products.get("G2-COUNTER") or {}).get("payload") or {}
    cells = [tuple(cell) for cell in (payload.get("mask_law") or {}).get("cells") or ()]
    if not cells:
        return None
    rows, cols = [r for r, _ in cells], [col for _, col in cells]
    return {"frame": "MASK", "board_sha256": None, "class": None, "anchor": [min(rows), min(cols)],
            "bbox": [min(rows), min(cols), max(rows), max(cols)], "cell_count": len(set(cells))}


def counter_subject(ctx: LevelContext) -> dict[str, Any]:
    bound = role_subject(ctx, "COUNTER")
    if bound is not None:
        return bound
    geometry = _mask_geometry(ctx)
    handle = f"mask@{geometry['anchor'][0]},{geometry['anchor'][1]}" if geometry else "counter"
    return {"type": "COUNTER", "handle": handle, "geometry": geometry, "trace": {"role": "COUNTER"}}


def agent_subject(ctx: LevelContext) -> dict[str, Any]:
    """The embodied ego's track when bound; otherwise the agent itself (a pointer ego has no grid footprint)."""
    return role_subject(ctx, "EGO") or c.plain_subject("AGENT", "agent")


def role_claim_subject(ctx: LevelContext, role: Mapping[str, Any]) -> dict[str, Any]:
    if role.get("entity_id"):
        return entity_subject(ctx, role["entity_id"])
    return counter_subject(ctx) if role["role"] == "COUNTER" else agent_subject(ctx)


def product_attribution(ctx: LevelContext, gate_id: str) -> dict[str, Any]:
    """Who certified a gate's product: its origin, and the admitted answer row that triggered it (if any)."""
    product_id = ctx.product_ids.get(gate_id)
    origin = (ctx.level.get("product_answers") or {}).get(product_id) or {}
    answer_ids = {item["answer_id"] for item in origin.get("answers") or ()}
    trigger = next((row["event_id"] for row in ctx.answer_rows
                    if row.get("disposition") == "ADMITTED" and (row.get("refs") or {}).get("answer_id") in answer_ids),
                   None)
    certification = origin.get("origin") or "NONE"
    if certification not in c.CERTIFICATIONS:
        certification = "NONE"
    return {"certification": certification, "product_id": product_id, "provenance_event": trigger}


__all__ = ["LevelContext", "agent_subject", "counter_subject", "entity_subject", "level_context", "product_attribution",
           "role_claim_subject", "role_subject", "track_or_level"]
