"""Bounded, read-only access to a compiled semantic-library snapshot.

This is the consumer seam.  It is intentionally not registered with Duck yet.
"""
from __future__ import annotations

from typing import Any


class SemanticLibraryView:
    def __init__(self, library: dict[str, Any]) -> None:
        self._library = library

    def query(self, operation: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        params = dict(parameters or {})
        op = str(operation or "").strip().lower()
        limit = max(1, min(50, int(params.get("limit", 20))))
        segments = self._library.get("segments", [])
        if op == "overview":
            return {
                "game_id": self._library.get("game_id"),
                "observed_nodes": self._library.get("observed_nodes"),
                "levels_observed": self._library.get("levels_observed", []),
                "summary": self._library.get("summary", {}),
                "epistemic_limits": self._library.get("epistemic_limits", []),
            }
        if op == "segments":
            rows = [
                {
                    "segment": segment["segment"],
                    "level": segment["level"],
                    "life": segment["life"],
                    "nodes": [segment["first_node"], segment["last_node"]],
                    "shape": segment["shape"],
                    "control": segment["control"],
                    "entities": len(segment["entities"]),
                }
                for segment in segments
            ]
            return {"items": rows[:limit], "truncated": len(rows) > limit}
        if op == "entities":
            role = str(params.get("role") or "").upper()
            rows = [
                entity
                for segment in segments
                for entity in segment["semantic_entities"]
                if not role or any(claim["role"] == role for claim in entity["roles"])
            ]
            return {"items": rows[:limit], "truncated": len(rows) > limit}
        if op == "mechanics":
            requested = str(params.get("segment") or "")
            rows = [
                {"segment": segment["segment"], **segment["lever_mechanics"]}
                for segment in segments
                if not requested or segment["segment"] == requested
            ]
            return {"items": rows[:limit], "truncated": len(rows) > limit}
        if op == "entity":
            handle = str(params.get("handle") or "")
            entity = next(
                (
                    entity
                    for segment in segments
                    for entity in segment["semantic_entities"]
                    if entity["handle"] == handle
                ),
                None,
            )
            if entity is None:
                return {"error": "entity not found"}
            members = set(entity["member_handles"])
            history = [
                {"left_node": row["left_node"], "right_node": row["right_node"], **change}
                for segment in segments
                for row in segment["joint_deltas"]
                for change in row["objects"]
                if change["handle"] in members
            ]
            return {"entity": entity, "observed_changes": history}
        if op == "transition":
            requested = int(params.get("right_node", -1))
            row = next(
                (
                    row
                    for segment in segments
                    for row in segment["joint_deltas"]
                    if row["right_node"] == requested
                ),
                None,
            )
            return row if row is not None else {"error": "transition not found"}
        return {
            "error": "unknown operation",
            "available": ["overview", "segments", "entities", "entity", "mechanics", "transition"],
        }
