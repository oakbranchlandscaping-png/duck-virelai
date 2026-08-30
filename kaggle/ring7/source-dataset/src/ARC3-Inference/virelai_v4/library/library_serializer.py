"""
virelai_v4/library/library_serializer.py — Groundhog Day serialization helpers.

Extracted from semantic_library.py per the Green-tier rule:
semantic_library.py exceeded 500 lines with serialization included.

These functions convert SemanticLibrary section dataclasses to/from plain
dicts for JSON-compatible persistence across lives.

Import sovereignty: imports from library/ and stdlib only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.semantic_library import (
    LibraryExploration,
    LibraryHeader,
    LibraryObject,
    LeverAction,
    SDKAction,
)


# ---------------------------------------------------------------------------
# LibraryHeader
# ---------------------------------------------------------------------------

def header_to_dict(h: LibraryHeader) -> dict:
    return {
        "game_id": h.game_id, "life": h.life, "actions_taken": h.actions_taken,
        "level": h.level, "world_type": h.world_type, "ego_mode": h.ego_mode,
        "ego_confidence": h.ego_confidence, "grid_rows": h.grid_rows,
        "grid_cols": h.grid_cols, "nav_stride": h.nav_stride,
        "actions_remaining": h.actions_remaining,
        "world_type_confidence": h.world_type_confidence,
        "ego_confirmed": h.ego_confirmed,
        "ego_object_ids": list(h.ego_object_ids),                           # WO-04c
        "ego_value_set": list(h.ego_value_set),                             # WO-04c
        "ego_displacement_map": {str(k): list(v) for k, v in h.ego_displacement_map.items()},  # WO-04c
        "ego_centroid": list(h.ego_centroid),                               # WO-04f
        "ego_body_cells": [list(cell) for cell in sorted(h.ego_body_cells)],  # WO-04g
    }


def header_from_dict(d: dict) -> LibraryHeader:
    return LibraryHeader(
        game_id=d.get("game_id", ""), life=d["life"],
        actions_taken=d.get("actions_taken", 0), level=d["level"],
        world_type=d["world_type"], ego_mode=d["ego_mode"],
        ego_confidence=d.get("ego_confidence", 0.0),
        grid_rows=d.get("grid_rows", 64), grid_cols=d.get("grid_cols", 64),
        nav_stride=d.get("nav_stride", 0),
        actions_remaining=d.get("actions_remaining", -1),
        world_type_confidence=d.get("world_type_confidence", 0.0),
        ego_confirmed=d.get("ego_confirmed", False),
        ego_object_ids=tuple(d.get("ego_object_ids", [])),                               # WO-04c
        ego_value_set=tuple(d.get("ego_value_set", [])),                                 # WO-04c
        ego_displacement_map={int(k): tuple(v) for k, v in d.get("ego_displacement_map", {}).items()},  # WO-04c
        ego_centroid=tuple(d.get("ego_centroid", [])),                                   # WO-04f
        ego_body_cells=frozenset(tuple(cell) for cell in d.get("ego_body_cells", [])),  # WO-04g
    )


# ---------------------------------------------------------------------------
# LibraryObject
# ---------------------------------------------------------------------------

def object_to_dict(o: LibraryObject) -> dict:
    return {
        "region_id": o.region_id, "class_id": o.class_id,
        "cells": [list(c) for c in sorted(o.cells)],
        "cell_count": o.cell_count, "shape_desc": o.shape_desc,
        "zone": o.zone, "position_desc": o.position_desc,
        "layer": o.layer, "count_like": o.count_like,
        "role": o.role.value, "confidence": o.confidence,
        "sub_role": o.sub_role, "evidence_basis": o.evidence_basis,
        "change_count": o.change_count, "flash_count": o.flash_count,
        "transition_count": o.transition_count,
        "reacts_to": list(o.reacts_to), "reaction_type": o.reaction_type,
        "cycle_length": o.cycle_length, "direction_label": o.direction_label,
        "saturated": o.saturated, "causes": list(o.causes),
        "caused_by": list(o.caused_by),
        "causal_observation_count": o.causal_observation_count,
        "causal_agreement": o.causal_agreement,
        "lc_rate": o.lc_rate, "lc_initial": o.lc_initial,
        "lc_budget_est": o.lc_budget_est,
        # Action Independence Metric (WO-C5-01) — persists across lives (Groundhog Day)
        "actions_observed": o.actions_observed,
        "actions_with_change": o.actions_with_change,
        # Cell count tracking (WO-C5-02) — persists across lives
        "initial_cell_count": o.initial_cell_count,
        "current_cell_count": o.current_cell_count,
        # WO-E09-v2 D1: march recognizer history (list on disk, tuple in memory)
        "cell_count_history": list(o.cell_count_history),
        # Background recognition (WO-C5-05) — persists across lives
        "ignore_score": o.ignore_score,
        "is_background": o.is_background,
        "ignore_channels": o.ignore_channels,
        # Active/static observation (WO-RM-02) — persists across lives (Groundhog Day)
        "is_active": o.is_active,
        "active_frame_count": o.active_frame_count,
        "first_active_frame": o.first_active_frame,
        "last_active_frame": o.last_active_frame,
        # Attribution (WO-01 LEVER-CATALOG) — recomputed each frame; no cross-life persistence
        "is_attributed": o.is_attributed,
        "attribution_evidence": list(o.attribution_evidence),
        # Tier 3 lever evidence (WO-02 LEVER-CATALOG) — persists across lives (Groundhog Day)
        "lever_confidence": o.lever_confidence,
        "lever_locality": o.lever_locality,
        "lever_effect_cells": (
            [list(c) for c in sorted(o.lever_effect_cells)]
            if o.lever_effect_cells is not None else None
        ),
        "lever_effect_region_ids": (
            list(o.lever_effect_region_ids)
            if o.lever_effect_region_ids is not None else None
        ),
        "inert_probe_count": o.inert_probe_count,
        # Probe outcome counters (WO-02 LEVER-CATALOG) — persists across lives (Groundhog Day)
        "probe_confirmation_count": o.probe_confirmation_count,
        "ambiguous_probe_count": o.ambiguous_probe_count,
        "lever_locked": o.lever_locked,
        # Investigation dossier (WO-OCD-01) — persists across lives (Groundhog Day)
        "last_probe_frame": o.last_probe_frame,
        "last_probe_outcome": o.last_probe_outcome,
        "last_probe_state_hash": o.last_probe_state_hash,
        "probe_count": o.probe_count,
        "needs_reinvestigation": o.needs_reinvestigation,
        # Per-action attempt flags (WO-OCD-FLAGS-CLICK) — persists across lives.
        # Mirrors ego_displacement_map convention: int keys serialized as str
        # for JSON-compat, deserialized back to int via from_dict.
        "actions_attempted": {str(k): v for k, v in o.actions_attempted.items()},
    }


def object_from_dict(d: dict) -> LibraryObject:
    return LibraryObject(
        region_id=d["region_id"], class_id=d["class_id"],
        cells=frozenset(tuple(c) for c in d["cells"]),
        cell_count=d["cell_count"], shape_desc=d["shape_desc"],
        zone=d["zone"], position_desc=d["position_desc"],
        layer=d["layer"], count_like=d["count_like"],
        role=LibraryRole(d["role"]), confidence=d["confidence"],
        sub_role=d.get("sub_role", ""), evidence_basis=d.get("evidence_basis", ""),
        change_count=d["change_count"], flash_count=d.get("flash_count", 0),
        transition_count=d.get("transition_count", 0),
        reacts_to=tuple(d.get("reacts_to", [])),
        reaction_type=d.get("reaction_type", ""),
        cycle_length=d.get("cycle_length", 0),
        direction_label=d.get("direction_label", ""),
        saturated=d["saturated"], causes=tuple(d.get("causes", [])),
        caused_by=tuple(d.get("caused_by", [])),
        causal_observation_count=d.get("causal_observation_count", 0),
        causal_agreement=d.get("causal_agreement", 0.0),
        lc_rate=d.get("lc_rate", 0.0), lc_initial=d.get("lc_initial", 0),
        lc_budget_est=d.get("lc_budget_est", -1),
        # Action Independence Metric (WO-C5-01) — .get() with default 0 for backward compat
        actions_observed=d.get("actions_observed", 0),
        actions_with_change=d.get("actions_with_change", 0),
        # Cell count tracking (WO-C5-02) — .get() with default 0 for backward compat
        initial_cell_count=d.get("initial_cell_count", 0),
        current_cell_count=d.get("current_cell_count", 0),
        # WO-E09-v2 D1: march history — tuple in memory, .get() default for back-compat
        cell_count_history=tuple(d.get("cell_count_history", ())),
        # Background recognition (WO-C5-05) — .get() with defaults for backward compat
        ignore_score=d.get("ignore_score", 0.0),
        is_background=d.get("is_background", False),
        ignore_channels=d.get("ignore_channels", ""),
        # Active/static observation (WO-RM-02) — .get() with defaults for backward compat
        is_active=d.get("is_active", False),
        active_frame_count=d.get("active_frame_count", 0),
        first_active_frame=d.get("first_active_frame", -1),
        last_active_frame=d.get("last_active_frame", -1),
        # Attribution (WO-01 LEVER-CATALOG) — .get() with defaults; recomputed each frame
        is_attributed=d.get("is_attributed", False),
        attribution_evidence=list(d.get("attribution_evidence", [])),
        # Tier 3 lever evidence (WO-02 LEVER-CATALOG) — .get() with defaults for backward compat
        lever_confidence=d.get("lever_confidence", 0.0),
        lever_locality=d.get("lever_locality", None),
        lever_effect_cells=(
            set(tuple(c) for c in d["lever_effect_cells"])
            if d.get("lever_effect_cells") is not None else None
        ),
        lever_effect_region_ids=(
            list(d["lever_effect_region_ids"])
            if d.get("lever_effect_region_ids") is not None else None
        ),
        inert_probe_count=d.get("inert_probe_count", 0),
        # Probe outcome counters (WO-02 LEVER-CATALOG) — .get() with defaults for backward compat
        probe_confirmation_count=d.get("probe_confirmation_count", 0),
        ambiguous_probe_count=d.get("ambiguous_probe_count", 0),
        lever_locked=d.get("lever_locked", False),
        # Investigation dossier (WO-OCD-01) — .get() with sentinels for backward compat
        last_probe_frame=d.get("last_probe_frame", -1),
        last_probe_outcome=d.get("last_probe_outcome", ""),
        last_probe_state_hash=d.get("last_probe_state_hash", ""),
        probe_count=d.get("probe_count", 0),
        needs_reinvestigation=d.get("needs_reinvestigation", False),
        # Per-action attempt flags (WO-OCD-FLAGS-CLICK) — int keys round-trip
        # through str (JSON-compat). Backward-compat default: empty dict.
        actions_attempted={int(k): v for k, v in d.get("actions_attempted", {}).items()},
    )


# ---------------------------------------------------------------------------
# SDKAction
# ---------------------------------------------------------------------------

def sdk_action_to_dict(a: SDKAction) -> dict:
    # WO-LGTD-02 Phase 1: Affordance Layer Entry A fields serialized
    # alongside legacy fields. Enums serialize as .value strings; ints/strs/floats inline.
    return {
        "action_id": a.action_id, "status": a.status,
        "delta_cells": a.delta_cells,
        "affected_regions": list(a.affected_regions),
        "notes": a.notes, "test_count": a.test_count,
        "action_name": a.action_name,
        "semantic_role": a.semantic_role,
        "declarative_belief": a.declarative_belief.value,
        "operational_belief": a.operational_belief.value,
        "operational_confidence": a.operational_confidence,
    }


def sdk_action_from_dict(d: dict) -> SDKAction:
    # WO-LGTD-02 Phase 1: default-tolerant deserialization. A pre-extension
    # serialized dict (without the five Entry A fields) hydrates from
    # defaults — DeclarativeBelief.ABSENT, OperationalBelief.UNTESTED,
    # empty strings, 0.0 confidence. Groundhog Day cross-version
    # persistence does not break.
    from virelai_v4.library.affordance_belief import (
        DeclarativeBelief,
        OperationalBelief,
    )
    declarative_raw = d.get("declarative_belief", DeclarativeBelief.ABSENT.value)
    operational_raw = d.get("operational_belief", OperationalBelief.UNTESTED.value)
    return SDKAction(
        action_id=d["action_id"], status=d.get("status", "UNTESTED"),
        delta_cells=d.get("delta_cells", 0),
        affected_regions=tuple(d.get("affected_regions", [])),
        notes=d.get("notes", ""), test_count=d.get("test_count", 0),
        action_name=d.get("action_name", ""),
        semantic_role=d.get("semantic_role", ""),
        declarative_belief=DeclarativeBelief(declarative_raw),
        operational_belief=OperationalBelief(operational_raw),
        operational_confidence=d.get("operational_confidence", 0.0),
    )


# ---------------------------------------------------------------------------
# LeverAction
# ---------------------------------------------------------------------------

def lever_action_to_dict(la: LeverAction) -> dict:
    return {
        "region_id": la.region_id, "parent_action_id": la.parent_action_id,
        "verb": la.verb, "delta_cells": la.delta_cells,
        "affected_regions": list(la.affected_regions),
        "effect_locality": la.effect_locality,
        "direction_label": la.direction_label,
        "confidence": la.confidence, "evidence_count": la.evidence_count,
    }


def lever_action_from_dict(d: dict) -> LeverAction:
    return LeverAction(
        region_id=d["region_id"], parent_action_id=d["parent_action_id"],
        verb=d.get("verb", ""), delta_cells=d.get("delta_cells", 0),
        affected_regions=tuple(d.get("affected_regions", [])),
        effect_locality=d.get("effect_locality", ""),
        direction_label=d.get("direction_label", ""),
        confidence=d.get("confidence", 0.0),
        evidence_count=d.get("evidence_count", 0),
    )


# ---------------------------------------------------------------------------
# LibraryExploration
# ---------------------------------------------------------------------------

def exploration_to_dict(e: LibraryExploration) -> dict:
    return {
        "unique_states": e.unique_states, "repeated_states": e.repeated_states,
        "efficiency": e.efficiency, "consecutive_repeated": e.consecutive_repeated,
        "actions_monitored": e.actions_monitored,
    }


def exploration_from_dict(d: dict) -> LibraryExploration:
    return LibraryExploration(
        unique_states=d["unique_states"], repeated_states=d["repeated_states"],
        efficiency=d["efficiency"], consecutive_repeated=d["consecutive_repeated"],
        actions_monitored=d.get("actions_monitored", 0),
    )
