"""
virelai_v4/diagnostics/per_stage_render.py — WO-1 v2 per-stage-render
(Campaign A · rung 1).

A READ-ONLY, OUT-OF-BAND diagnostic that renders three pipeline stages of
one frame side by side:

    perception      raw per-press physics (frame_dump.compose_frame_event)
    classification  Library-expressed belief (library.header + objects[*].role)
    dispatch        the captain's algorithmic walk (field_card reuse) +
                    an honest typed-gap solver-prediction slot

Binding invariants (charter §3):
  - Read-only with respect to belief. This module writes no belief, alters
    no dispatch, adds no timing, and holds NO cross-frame state. It is
    invoked out of band; it is never wired into choose_action's mutation
    path.
  - Fidelity, not agreement. Each stage displays the recorded state read
    from the same surfaces the captain/router read. No recompute of a
    posterior, no cached display value.
  - Out-of-tape cases render distinctly. A present-but-unwired typed-gap
    label renders rather than being omitted.
  - The solver-prediction component renders the §5 typed gap VERBATIM; no
    prediction is synthesized or recomputed (none is recorded at HEAD —
    the falsification kernel is SPECIFIED-not-built; charter §8).

Surfaces read (all confirmed pure at the §0 gate; this module edits none
of their bodies — it reads via call/import only):
  - diagnostics/frame_dump.py :: compose_frame_event   (perception)
  - library/semantic_library.py :: library.header, library.objects,
    library.counter_object()                            (classification)
  - library/field_card.py :: _render_captain_target     (dispatch walk reuse)
  - captain.py :: compute_captain_target, DISPATCH_TABLE,
    ATTRIBUTE_TYPE_TO_PROBE_NAME                         (dispatch honesty)

Import sovereignty: the dispatch readers import captain/field_card lazily
(display-time only), mirroring field_card._render_captain_target, so this
diagnostic adds no import-time coupling to the spine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# The solver-prediction slot, rendered verbatim (WO-1 v2 §5 / P4). No
# pre-observation prediction is recorded at HEAD; this is an honest gap,
# not a synthesized value.
PREDICTION_TYPED_GAP = (
    "NOT RECORDED — captain enforces an algorithmic walk; no pre-observation "
    "prediction at HEAD; falsification kernel is long-horizon."
)

# Physics keys surfaced by the perception stage. Deliberately EXCLUDES the
# belief-tinged keys compose_frame_event also carries (mover_classification,
# causes_list, caused_by_list) so no classification content leaks into the
# perception stage (stage separation).
_PERCEPTION_PHYSICS_KEYS = (
    "delta_cells",
    "displacement_vector",
    "boundary_contact_state",
    "mover_count",
    "press_position_neighbors",
)


# ---------------------------------------------------------------------------
# Structured render (text presentation derived from it; no state retained)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StageRender:
    """One frame rendered as three independent stages, side by side.

    Frozen: the composer returns a fresh value each call and retains nothing
    between calls (no cross-frame state). The three stage payloads are plain
    read-only snapshots of belief surfaces.
    """
    perception: Dict[str, Any]
    classification: Dict[str, Any]
    dispatch: Dict[str, Any]

    def to_text(self) -> str:
        """Render the three stages as side-by-side text panels.

        Pure derivation from the structured payloads — adds no information
        not already in the snapshot.
        """
        return _stage_render_to_text(self)


# ---------------------------------------------------------------------------
# P2 — perception stage
# ---------------------------------------------------------------------------

def render_perception(
    context: Any,
    grid: Optional[Any] = None,
) -> Dict[str, Any]:
    """Render the perception stage: raw per-press physics only.

    Pure read of frame_dump.compose_frame_event (§0.1). Surfaces the physics
    keys (delta_cells, displacement_vector, boundary_contact_state,
    mover_count, press_position_neighbors) and NO belief lookup — no
    classification content leaks into this stage.

    The current-frame grid is NOT stored on context (context.py:135 — "live
    grid is always the current frame — no storage needed"), so it is passed
    in by the out-of-band caller. When it is absent — or there is no probe
    press to record — the stage renders OUT_OF_TAPE distinctly rather than
    fabricating physics.
    """
    library = getattr(context, "semantic_library", None)
    prev_grid = getattr(context, "prev_grid", None)

    if library is None:
        return {"status": "OUT_OF_TAPE", "reason": "no library on context"}
    if grid is None:
        return {"status": "OUT_OF_TAPE", "reason": "no current-frame grid supplied"}
    if prev_grid is None:
        return {"status": "OUT_OF_TAPE", "reason": "no prev_grid (life-start frame)"}

    # Lazy import — display-time only, mirrors field_card's spine isolation.
    from virelai_v4.diagnostics.frame_dump import compose_frame_event

    event = compose_frame_event(context, library, prev_grid, grid)
    if event is None:
        return {"status": "OUT_OF_TAPE", "reason": "no probed press this frame"}

    physics = {k: event.get(k) for k in _PERCEPTION_PHYSICS_KEYS}
    physics["status"] = "IN_TAPE"
    return physics


# ---------------------------------------------------------------------------
# P3 — classification stage
# ---------------------------------------------------------------------------

def render_classification(library: Any) -> Dict[str, Any]:
    """Render the classification stage: Library-expressed belief.

    PORT-read off library.header + library.objects[*].role + the
    counter_object() view (§0.2) — the SAME surfaces field_card reads. No
    recompute of any posterior (fidelity).
    """
    if library is None:
        return {"status": "OUT_OF_TAPE", "reason": "no library on context"}

    header = library.header
    counter = library.counter_object()

    from virelai_v4.diagnostics.store_a_readout import render_read

    slots: List[Dict[str, Any]] = []
    for region_id in library.objects:
        obj = library.objects[region_id]
        # DD gap-1: classification reads the captain's store (render_read), not
        # Store-B obj.role — the split brain dies here. tag is Band-1 (recorded);
        # role is the inferred child; the hand-rolled sub_role="counter" is
        # subsumed by the (tag=REACTIVE, role=COUNTER) pair (ruling R2).
        _tag, _role, _loc, _conf = render_read(obj)
        slots.append({
            "region_id": obj.region_id,
            "tag": _tag,                                 # Band-1 self-state (R3)
            "role": _role if _role is not None else "UNCLASSIFIED",
            "locality": _loc,
            "class_id": obj.class_id,
            "cell_count": obj.cell_count,
            "confidence": _conf,                         # R1 display
        })

    return {
        "status": "IN_TAPE",
        # Foundation singletons (pure reads off the header / counter view).
        "world_type": header.world_type,
        "world_type_confidence": header.world_type_confidence,
        "ego_mode": header.ego_mode,
        "ego_object_ids": list(header.ego_object_ids),
        "ego_confidence": header.ego_confidence,
        "counter_region_id": (counter.region_id if counter is not None else None),
        # Per-slot belief (role posteriors), canonical region order.
        "slots": slots,
    }


# ---------------------------------------------------------------------------
# P4 — dispatch stage
# ---------------------------------------------------------------------------

def render_dispatch(context: Any) -> Dict[str, Any]:
    """Render the dispatch stage: the captain's algorithmic walk.

    Reuses field_card._render_captain_target (§0.3) for the human-readable
    walk line — read via import, field_card's body untouched. Surfaces the
    selected (world_type, attribute_type), whether a primitive is wired for
    that cell (honest typed-gap flag), the chosen probe, the available
    probes, and the recorded provenance. The solver-prediction component is
    the §5 typed gap, verbatim.
    """
    library = getattr(context, "semantic_library", None)
    provenance = getattr(context, "last_emitter_path", None)

    out: Dict[str, Any] = {
        "status": "IN_TAPE",
        "provenance": provenance,
        # §5: honest typed gap — no recorded prediction at HEAD.
        "solver_prediction": PREDICTION_TYPED_GAP,
    }

    if library is None:
        out["status"] = "OUT_OF_TAPE"
        out["reason"] = "no library on context"
        out["captain_target_line"] = None
        out["selected"] = None
        out["chosen_probe"] = None
        out["available_probes"] = []
        out["typed_gap"] = None
        return out

    # Lazy display-time imports (spine isolation, mirrors field_card).
    from virelai_v4.captain import (
        ATTRIBUTE_TYPE_TO_PROBE_NAME,
        DISPATCH_TABLE,
        compute_captain_target,
    )
    from virelai_v4.library.field_card import _render_captain_target

    # Mine-Then-Reuse: the same human-readable line the field card renders.
    out["captain_target_line"] = _render_captain_target(library)

    world_type = library.header.world_type
    target = compute_captain_target(library)
    if target is None:
        out["selected"] = None
        out["chosen_probe"] = None
        out["typed_gap"] = None
    else:
        _slot, attribute_type, region_id = target
        wired = (world_type, attribute_type) in DISPATCH_TABLE
        out["selected"] = {
            "world_type": world_type,
            "attribute_type": attribute_type.name,
            "region_id": region_id,
            "wired_primitive": wired,
        }
        out["chosen_probe"] = ATTRIBUTE_TYPE_TO_PROBE_NAME.get(attribute_type)
        # Present-but-unwired typed-gap label rendered, not omitted.
        out["typed_gap"] = (
            None if wired
            else f"[TYPED_GAP] ({world_type}, {attribute_type.name})"
        )

    out["available_probes"] = [
        p.probe_name for p in library.available_probes()
    ]
    return out


# ---------------------------------------------------------------------------
# P1 — composer
# ---------------------------------------------------------------------------

def render_all(context: Any, grid: Optional[Any] = None) -> StageRender:
    """Render perception, classification, and dispatch side by side.

    Pure function. Calls the three stage readers and lays their results into
    one StageRender. Holds NO cache and NO state between calls; invoked out
    of band — never wired into choose_action.

    grid: the current-frame grid, supplied by the out-of-band caller. It is
    not stored on context (context.py:135); when omitted, the perception
    stage renders OUT_OF_TAPE distinctly (the other two stages are
    unaffected).
    """
    library = getattr(context, "semantic_library", None)
    return StageRender(
        perception=render_perception(context, grid),
        classification=render_classification(library),
        dispatch=render_dispatch(context),
    )


# ---------------------------------------------------------------------------
# Text presentation (pure derivation; no information added)
# ---------------------------------------------------------------------------

def _format_block(title: str, lines: List[str]) -> str:
    body = "\n".join(f"  {ln}" for ln in lines) if lines else "  (empty)"
    return f"=== {title} ===\n{body}"


def _perception_lines(p: Dict[str, Any]) -> List[str]:
    if p.get("status") != "IN_TAPE":
        return [f"OUT OF TAPE: {p.get('reason', 'unavailable')}"]
    return [
        f"delta_cells: {p.get('delta_cells')}",
        f"displacement_vector: {p.get('displacement_vector')}",
        f"boundary_contact_state: {p.get('boundary_contact_state')}",
        f"mover_count: {p.get('mover_count')}",
        f"press_position_neighbors: {p.get('press_position_neighbors')}",
    ]


def _classification_lines(c: Dict[str, Any]) -> List[str]:
    if c.get("status") != "IN_TAPE":
        return [f"OUT OF TAPE: {c.get('reason', 'unavailable')}"]
    lines = [
        f"world_type: {c.get('world_type')} ({c.get('world_type_confidence'):.2f})",
        f"ego_mode: {c.get('ego_mode')} | ego_object_ids: {c.get('ego_object_ids')}"
        f" (conf {c.get('ego_confidence'):.2f})",
        f"counter_region_id: {c.get('counter_region_id')}",
        f"slots ({len(c.get('slots', []))}):",
    ]
    for s in c.get("slots", []):
        # DD gap-1: tag·role off render_read; confidence is now a display STRING
        # (R1: axis sigmoid / "—(derived)" / "—"), never float-formatted.
        _loc = f"·{s['locality']}" if s.get("locality") else ""
        lines.append(
            f"  R{s['region_id']} {s['tag']}·{s['role']}{_loc} class={s['class_id']} "
            f"cells={s['cell_count']} conf={s['confidence']}"
        )
    return lines


def _dispatch_lines(d: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    if d.get("status") != "IN_TAPE":
        lines.append(f"OUT OF TAPE: {d.get('reason', 'unavailable')}")
    lines.append(f"captain walk: {d.get('captain_target_line')}")
    sel = d.get("selected")
    if sel is not None:
        lines.append(
            f"selected: world={sel['world_type']} "
            f"attr={sel['attribute_type']} rid={sel['region_id']} "
            f"wired={sel['wired_primitive']}"
        )
    if d.get("typed_gap"):
        lines.append(f"typed gap: {d['typed_gap']}")
    lines.append(f"chosen probe: {d.get('chosen_probe')}")
    lines.append(f"available probes: {d.get('available_probes')}")
    lines.append(f"provenance: {d.get('provenance')}")
    lines.append(f"solver prediction: {d.get('solver_prediction')}")
    return lines


def _stage_render_to_text(sr: StageRender) -> str:
    return "\n\n".join((
        _format_block("PERCEPTION", _perception_lines(sr.perception)),
        _format_block("CLASSIFICATION", _classification_lines(sr.classification)),
        _format_block("DISPATCH", _dispatch_lines(sr.dispatch)),
    ))


__all__ = [
    "StageRender",
    "render_all",
    "render_perception",
    "render_classification",
    "render_dispatch",
    "PREDICTION_TYPED_GAP",
]
