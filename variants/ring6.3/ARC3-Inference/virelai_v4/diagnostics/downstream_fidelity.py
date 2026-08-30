"""
virelai_v4/diagnostics/downstream_fidelity.py — WO-4 downstream fidelity grade
(Campaign A · rung 1 / fidelity).

Grades whether the lens FAITHFULLY renders the solver's actual belief code-state
on the classification + dispatch panels. Oracle = CODE-STATE: an INDEPENDENT raw
read of the belief state, on its own code path, separate from per_stage_render's
formatter — so it catches lens drift / stale / mis-format. Verdict is per-field
MATCH / MISMATCH.

TWO-ORACLE BOUNDARY (charter §2, binding):
  - This is a FIDELITY grade — "does the lens show what the solver ACTUALLY
    believes," KNOWN-FALSE beliefs included. There is NO external oracle here
    (internal consistency — exactly what lets a false belief render honestly).
  - CORRECTNESS-vs-reality (is the belief true?) is the MODEL oracle — Campaign
    B — and is NOT wired here. The perception .json oracle (rung 3) is never
    applied to downstream; this code-state oracle is never applied to
    perception.

Compose: render≡code-state (here) + terminal≡JSON (rung 0 / WO-5) ⇒
terminal ≡ JSON ≡ code-state.

Read-only w.r.t. belief; no cross-frame state; stdlib only. The grade reads the
same library/context the captain reads and writes nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from virelai_v4.diagnostics.per_stage_render import (
    render_classification,
    render_dispatch,
)

# This module's only oracle is the solver's own code-state. Named explicitly so
# the boundary is auditable (T4): no external/correctness oracle is imported.
ORACLE = "CODE_STATE"

_CLASSIFICATION_SINGLETONS = (
    "world_type", "world_type_confidence", "ego_mode",
    "ego_object_ids", "ego_confidence", "counter_region_id",
)
_SLOT_FIELDS = ("role", "class_id", "cell_count", "confidence")
_DISPATCH_FIELDS = ("selected", "chosen_probe", "provenance")


@dataclass(frozen=True)
class FidelityVerdict:
    """One field: what the lens rendered vs the independent code-state read."""
    field: str
    rendered: Any
    codestate: Any
    verdict: str          # MATCH / MISMATCH


# ---------------------------------------------------------------------------
# Independent code-state readers (separate code path from the formatter)
# ---------------------------------------------------------------------------

def _effect_tuple(effect: Any) -> Dict[str, Any]:
    return {
        "subject_region_id": getattr(effect, "subject_region_id", None),
        "vector": getattr(effect, "vector", None),
        "cell_count_delta": getattr(effect, "cell_count_delta", None),
        "observation_count": getattr(effect, "observation_count", None),
    }


def read_classification_codestate(library: Any) -> Dict[str, Any]:
    """Raw read of foundation singletons + per-slot belief, on an independent
    code path (NOT via render_classification). Also surfaces the per-slot
    observation_status enum + lever effects (§4.3), sourced from the layer."""
    if library is None:
        return {"status": "OUT_OF_TAPE"}
    h = library.header
    counter = library.counter_object()
    slots: List[Dict[str, Any]] = []
    from virelai_v4.diagnostics.store_a_readout import render_read
    for region_id in library.objects:
        o = library.objects[region_id]
        # DD gap-1 (class-D oracle re-ground): the fidelity oracle is the CAPTAIN'S
        # STORE. role/tag/locality/confidence are read via render_read (Store A),
        # not obj.role (Store B). Honesty is preserved exactly — a false belief
        # injected into the AXES renders verbatim; the render never silently
        # corrects. Only the store fidelity is measured against moved.
        _tag, _role, _loc, _conf = render_read(o)
        slots.append({
            "region_id": o.region_id,
            "tag": _tag,
            "role": _role if _role is not None else "UNCLASSIFIED",
            "locality": _loc,
            "class_id": o.class_id,
            "cell_count": o.cell_count,
            "confidence": _conf,
            # §4.3 — observation_status sourced from the layer, not inferred.
            "observation_status": o.observation_status.value,
            "lever_effects": [_effect_tuple(e) for e in o.lever_effects],
        })
    return {
        "status": "IN_TAPE",
        "world_type": h.world_type,
        "world_type_confidence": h.world_type_confidence,
        "ego_mode": h.ego_mode,
        "ego_object_ids": list(h.ego_object_ids),
        "ego_confidence": h.ego_confidence,
        "counter_region_id": (counter.region_id if counter is not None else None),
        "slots": slots,
    }


def read_dispatch_codestate(context: Any) -> Dict[str, Any]:
    """Raw read of the captain's dispatch selection, on an independent code
    path (compute_captain_target / DISPATCH_TABLE / ATTRIBUTE_TYPE_TO_PROBE_NAME
    directly), separate from render_dispatch."""
    library = getattr(context, "semantic_library", None)
    provenance = getattr(context, "last_emitter_path", None)
    if library is None:
        return {"status": "OUT_OF_TAPE", "selected": None,
                "chosen_probe": None, "provenance": provenance}

    from virelai_v4.captain import (
        ATTRIBUTE_TYPE_TO_PROBE_NAME,
        DISPATCH_TABLE,
        compute_captain_target,
    )
    world_type = library.header.world_type
    target = compute_captain_target(library)
    if target is None:
        return {"status": "IN_TAPE", "selected": None,
                "chosen_probe": None, "provenance": provenance}
    _slot, attribute_type, region_id = target
    return {
        "status": "IN_TAPE",
        "selected": {
            "world_type": world_type,
            "attribute_type": attribute_type.name,
            "region_id": region_id,
            "wired_primitive": (world_type, attribute_type) in DISPATCH_TABLE,
        },
        "chosen_probe": ATTRIBUTE_TYPE_TO_PROBE_NAME.get(attribute_type),
        "provenance": provenance,
    }


# ---------------------------------------------------------------------------
# Fidelity grade (render-output vs the independent code-state read)
# ---------------------------------------------------------------------------

def _eq(a: Any, b: Any) -> bool:
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        return list(a or []) == list(b or [])
    return a == b


def _verdict(field: str, rendered: Any, codestate: Any) -> FidelityVerdict:
    return FidelityVerdict(field, rendered, codestate,
                           "MATCH" if _eq(rendered, codestate) else "MISMATCH")


def grade_classification(library: Any) -> List[FidelityVerdict]:
    """Per-field fidelity: render_classification output vs the independent
    code-state read. FIDELITY ONLY — never a correctness verdict."""
    rendered = render_classification(library)
    truth = read_classification_codestate(library)
    if rendered.get("status") != "IN_TAPE" or truth.get("status") != "IN_TAPE":
        return [_verdict("status", rendered.get("status"), truth.get("status"))]

    verdicts = [_verdict(f, rendered.get(f), truth.get(f))
                for f in _CLASSIFICATION_SINGLETONS]

    r_slots = {s["region_id"]: s for s in rendered.get("slots", [])}
    t_slots = {s["region_id"]: s for s in truth.get("slots", [])}
    verdicts.append(_verdict("slot_region_ids",
                             sorted(r_slots), sorted(t_slots)))
    for rid in sorted(t_slots):
        r = r_slots.get(rid, {})
        t = t_slots[rid]
        for f in _SLOT_FIELDS:
            verdicts.append(_verdict(f"slot[{rid}].{f}", r.get(f), t.get(f)))
    return verdicts


def grade_dispatch(context: Any) -> List[FidelityVerdict]:
    """Per-field fidelity: render_dispatch output vs the independent code-state
    read of the captain's selection. FIDELITY ONLY."""
    rendered = render_dispatch(context)
    truth = read_dispatch_codestate(context)
    return [_verdict(f, rendered.get(f), truth.get(f)) for f in _DISPATCH_FIELDS]


# ---------------------------------------------------------------------------
# Render (the fidelity panel; read-only)
# ---------------------------------------------------------------------------

def _verdict_line(v: FidelityVerdict) -> str:
    if v.verdict == "MATCH":
        return f"{v.field}: MATCH"
    return (f"{v.field}: MISMATCH "
            f"(rendered={v.rendered!r} | code-state={v.codestate!r})")


def _effects_lines(library: Any) -> List[str]:
    """§4.3 — surface the observation_status enum where effects render,
    sourced from obj.observation_status (not inferred)."""
    if library is None:
        return []
    lines: List[str] = []
    for region_id in library.objects:
        o = library.objects[region_id]
        status = o.observation_status.value
        if status == "NOT_OBSERVED" and not o.lever_effects:
            continue
        eff = "; ".join(
            f"->R{e.subject_region_id} vec={e.vector} Δcells={e.cell_count_delta} "
            f"obs={e.observation_count}" for e in o.lever_effects
        ) or "(no stored effects)"
        lines.append(f"  R{region_id}: observation_status={status} | {eff}")
    return lines


def render_downstream_fidelity(context: Any) -> str:
    """Render per-field FIDELITY verdicts for classification + dispatch, plus
    the observation_status enum on lever effects. Read-only; the grade reads
    the same library/context the captain reads and writes nothing."""
    library = getattr(context, "semantic_library", None)
    lines = ["=== DOWNSTREAM FIDELITY (render vs code-state; fidelity-only) ==="]

    lines.append("  --- classification ---")
    for v in grade_classification(library):
        lines.append(f"  {_verdict_line(v)}")

    lines.append("  --- dispatch ---")
    for v in grade_dispatch(context):
        lines.append(f"  {_verdict_line(v)}")

    eff = _effects_lines(library)
    if eff:
        lines.append("  --- lever effects (observation_status, sourced) ---")
        lines.extend(eff)

    lines.append("  (fidelity only — correctness-vs-reality is Campaign B, "
                 "not graded here)")
    return "\n".join(lines)


__all__ = [
    "ORACLE",
    "FidelityVerdict",
    "read_classification_codestate",
    "read_dispatch_codestate",
    "grade_classification",
    "grade_dispatch",
    "render_downstream_fidelity",
]
