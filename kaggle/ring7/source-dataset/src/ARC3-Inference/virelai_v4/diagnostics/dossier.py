"""
virelai_v4/diagnostics/dossier.py — WO-5 rung-0 dossier spine
(Campaign A · rung 0 / dossier-form).

The dossier SPINE: one overview render + one JSON machine-form, both derived
from a single belief read, so terminal ≡ JSON ≡ code-state holds by
construction. Drill-down render-modes, axiom ✓/⚠ auto-grading, and the
fault-fixture gate are WO-5.1.

Disciplines (DIAGNOSTIC_DOSSIER_SPEC_v1 §2, binding):
  - Read-only w.r.t. belief; no cross-frame state; stdlib + sparse ANSI/glyphs.
  - PLANNING-COMPLETE shape, RECORD-THEN-DEDUCE honesty: every lever-effect
    carries the full shape (quality · direction · grid-location · sub-taxonomy),
    but each field is populated ONLY from what the belief holds. A field the
    belief lacks renders as an explicit excluded token — terminal "⊙ not built",
    JSON null + sibling "_excluded":"<reason>" — never fabricated, never
    defaulted to a plausible value.
  - Two forms, one content: neither may carry a fact the other omits (§5).
  - The lever-effect reality line is "graded in Campaign B" (charter A/B cut) —
    belief side only in this rung; no correctness verdict here.

Single read: build_dossier consumes downstream_fidelity.read_classification_
codestate (the rung-1 reader) for foundation singletons + per-slot belief, and
reads obj.lever_mechanism / lever_effects off the SAME library for the lever
deepening — no recompute, one source.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from virelai_v4.diagnostics.downstream_fidelity import read_classification_codestate
from virelai_v4.diagnostics.store_a_readout import render_read, animation_annotation  # DD gap-1 + WO_AR D3
from virelai_v4.diagnostics.foundation_grade import (   # DD gap-6: correctness column
    is_foundation_key,
    render_foundation_grade,
)


# ---------------------------------------------------------------------------
# Excluded sentinel — an absent belief field, marked honestly (never faked)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Excluded:
    reason: str


_NOT_BUILT = "⊙ not built"
_REALITY_CAMPAIGN_B = "graded in Campaign B"

# Sub-taxonomy the belief can carry (LeverMechanism). The spec's broader set
# (global · one-shot · gated) is NOT carried by the substrate — those render
# excluded when asked for, never invented.
# WO-E7 (de-collapse): SATURATED removed — it is a CONDITION (read from
# obj.saturated), not a sub-taxonomy TYPE value. lever_mechanism no longer
# carries it, so the type render shows the real type (or UNKNOWN), never the
# condition. The condition renders via the B2 intrinsic note (_has_dynamics).
_CARRIED_SUBTAXONOMY = ("TOGGLE", "CYCLE", "DIRECTIONAL", "UNKNOWN")


@dataclass(frozen=True)
class WorldDossier:
    """One content; two forms derive from it."""
    axioms: Dict[str, Any]
    objects: List[Dict[str, Any]]
    levers: List[Dict[str, Any]]
    frontier: Dict[str, Any]
    # WO-D1 — coarse banded dossier: per-object band columns ride in objects[*]
    # ["bands"]; the conserved-transfer composition (a relation over a SET of
    # edges) renders here, never in a per-entity band cell. Defaulted so rung-0
    # constructors stay valid.
    causal_map: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Build — one belief read → the content
# ---------------------------------------------------------------------------

def _anchor(cells) -> Any:
    if not cells:
        return Excluded("no cells carried for this slot")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (min(rows), min(cols))


def _bbox(cells) -> Any:
    """WO_DOSSIER_MASTER_ROSTER M1 — derive a slot's bounding-box dimensions
    (height, width) from its cells: height = max_row − min_row + 1, width =
    max_col − min_col + 1. Reuses the SAME cells _anchor reads (no new belief
    read, no stored field, no write). Excluded when no cells are carried — the
    geometry is then honestly blank, never fabricated."""
    if not cells:
        return Excluded("no cells carried for this slot")
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return (max(rows) - min(rows) + 1, max(cols) - min(cols) + 1)


_GRID_LOC_EXCLUDED = ("absolute coords not stored in effect; derivable from "
                      "subject anchor + vector — WO-5.1")


def _bearing_and_magnitude(effect: Any) -> Any:
    """Decompose the recorded displacement into a bearing label + scalar
    magnitude (both sourced from the SAME vector — never one populated and the
    other excluded for the same quantity). Returns (direction, magnitude)."""
    vector = getattr(effect, "vector", None)
    if vector is not None:                         # RIGID displacement
        dr, dc = round(vector[0]), round(vector[1])
        dirs = []
        if dr:
            dirs.append("SOUTH" if dr > 0 else "NORTH")
        if dc:
            dirs.append("EAST" if dc > 0 else "WEST")
        direction = "+".join(dirs) if dirs else "NONE"
        return direction, max(abs(dr), abs(dc))
    ccd = getattr(effect, "cell_count_delta", None)
    if ccd is not None:                            # NON_RIGID: magnitude only
        return (Excluded("non-rigid effect — no displacement bearing"), abs(ccd))
    return (Excluded("no displacement vector measured"),
            Excluded("no magnitude recorded"))


def _quality(operation_kind: Optional[str]) -> Any:
    if not operation_kind:
        return Excluded("effect kind not recorded")
    return "RIGID DISPLACEMENT" if operation_kind == "RIGID" else operation_kind


def _effect_struct(effect: Any) -> Dict[str, Any]:
    """The planning-complete effect shape; each field populated-or-excluded.

    grid_location is the absolute spatial coordinate of the effect — which the
    substrate does NOT store (P3); it is rendered NOT-STORED (derivable later),
    never the subject SLOT reference (that is the lever's target, rendered at
    the lever level), never fabricated coordinates. direction + magnitude are
    BOTH sourced from the vector (no excluded-magnitude beside a populated
    bearing). The reserved-uninitialized WO3 scalars are not surfaced."""
    direction, magnitude = _bearing_and_magnitude(effect)
    subject = getattr(effect, "subject_region_id", None)
    return {
        # D5: each effect carries its OWN target (the affected slot), paired
        # inline so positional reading can't mis-map a multi-effect lever.
        "target": (f"Slot#{subject}" if subject is not None
                   else Excluded("no subject region on effect")),
        "quality": _quality(getattr(effect, "operation_kind", None)),
        "direction": direction,
        "magnitude": magnitude,
        "grid_location": Excluded(_GRID_LOC_EXCLUDED),
        "observation_count": getattr(effect, "observation_count", None),
        # reality line is Campaign B (charter A/B cut) — not auto-filled here.
        "reality": Excluded(_REALITY_CAMPAIGN_B),
    }


def _sub_taxonomy(obj: Any) -> Any:
    mech = getattr(obj, "lever_mechanism", None)
    if mech is None:
        return Excluded("lever type not yet probed")
    name = getattr(mech, "name", str(mech))
    return name if name in _CARRIED_SUBTAXONOMY else Excluded(
        f"sub-taxonomy '{name}' not in carried set")


def _candidate_roster(context: Any, lever_obj: Any, lever_rid: int) -> Any:
    """WO-D0.5 — read-only render of the ConservedTransfer CANDIDATE cache
    (context.conserved_transfer_candidates), surfaced BEFORE license so the
    roster is observable even when the verb abstains at per-lever keying — the
    vc33 case, where the licensed obj.conserved_transfer never appears.

    HARD FENCE (A3, identical to MOVE 1): renders the raw {member_id:
    signed-delta} roster AS MEASURED and DECIDES NOTHING about source/sink — no
    sort / min / max / argmax / sign-test / role-label over the member deltas.
    The sign is carried as evidence, never acted on. license_status is a
    None-check on the licensed relation, not a delta test. Returns Excluded when
    no candidate has formed (never a fabricated roster)."""
    cache = getattr(context, "conserved_transfer_candidates", {}) or {}
    entry = cache.get(lever_rid)
    if entry is None:
        return Excluded("candidate: none formed")
    candidate, functional = entry
    # iterate member_subject_ids as stored (id-sorted upstream at authoring); no
    # ordering/comparison performed here — pure lookup of the measured delta.
    members = {mid: functional.get(mid) for mid in candidate.member_subject_ids}
    return {
        "members": members,
        "conserved_quantity": candidate.conserved_quantity,
        "license_status": ("licensed"
                           if getattr(lever_obj, "conserved_transfer", None)
                           is not None else "abstained"),
    }


# ---------------------------------------------------------------------------
# WO-D1 — coarse banded dossier (B0–B3) derived from belief.
# Band state from the NAMED §2 belief signals ONLY; never the six-Tier assessor
# RYG (targeting/assessor.py) — hold #2. Contiguity makes the cap c_{b+1} <= c_b
# automatic: a band is UNREACHED when the band beneath it is not GREEN, and B3
# GREEN requires B2 GREEN. Render-not-runtime: pure read of existing belief.
# ---------------------------------------------------------------------------

_GREEN, _OPEN, _UNREACHED = "GREEN", "OPEN", "UNREACHED"

# §0.4 fallback (b): the probe-outcome enum carries NO `SATURATED` label
# (saturation logs as NO_EFFECT), so the intrinsic-dynamics determination is
# read from lever_mechanism / saturated here, not from the outcome stream. Any
# concrete lever-mechanism verdict is a dynamics determination; UNKNOWN is none.
# WO-E7 (de-collapse): SATURATED removed — _has_dynamics reads the saturated
# CONDITION from obj.saturated alone (the `if getattr(obj, "saturated") ...`
# branch), never from the lever_mechanism TYPE field. This closes the WO-E6
# B2-carry: when obj.saturated clears (E6 revision), the B2 note now fully
# clears, because the type field no longer re-supplies "SATURATED".
_DYNAMICS_MECHANISMS = ("TOGGLE", "CYCLE", "DIRECTIONAL")

# Self-null evidence outcomes (Director ruling: remote-only + dead presses).
# Saturation is excluded structurally by _has_dynamics, not by an outcome label.
_SELF_NULL_OUTCOMES = ("LEVER_REMOTE_ONLY", "NO_EFFECT")

_B2_NULL_THRESHOLD = 2   # Director ruling: N >= 2


def _has_dynamics(obj: Any) -> Optional[str]:
    """The confirmed intrinsic-dynamics determination for a lever, or None.
    Generalizes the LOCAL exclusion (§0.4/§3 fold): a lever that changes its own
    state — LOCAL self-change, a saturated flag, or any concrete lever_mechanism
    verdict — is dynamics-bearing, so its null presses are NOT remote-relay
    self-nulls and it can never clear B2 as a self-null. Returns the
    determination name for the explicit render, or None when no dynamics."""
    if getattr(obj, "lever_locality", None) == "LOCAL":
        return "LOCAL"
    if getattr(obj, "saturated", False):
        return "SATURATED"
    mech = getattr(obj, "lever_mechanism", None)
    mech_name = getattr(mech, "value", mech)
    if mech_name in _DYNAMICS_MECHANISMS:
        return mech_name
    return None


def _b2_self_null_count(library: Any, region_id: int) -> int:
    """The B2 COVERAGE count: qualifying self-null events for a lever from the
    durable probe_event_log (D0.6 outcome ii). §0.5 gate-scoped fallback: the log
    stores no confirmation-frame, so count ALL qualifying events for a
    now-confirmed lever — the caller's lever-confirmed gate forecloses padding.

    WO-D2: this is now PURELY the coverage gate (hold #1). The remoteness
    DETERMINATION is read from lever_locality == "REMOTE" (the field), no longer
    re-derived here — but the count is retained so a single-observation REMOTE
    cannot clear B2 GREEN without evidence. Pure read; no measurement, no probe."""
    log = getattr(library, "probe_event_log", None) or []
    n = 0
    for e in log:
        if (e.get("region_id") == region_id
                and e.get("outcome") in _SELF_NULL_OUTCOMES):
            n += 1
    return n


def _recorded_edges(obj: Any) -> List[Dict[str, Any]]:
    """The lever's OWN recorded effects on subjects (B3 edge). A4/A3: the signed
    delta is the lever's own recorded measurement on a single lever->subject
    edge — NOT a cross-member comparison producing a role. Read from
    lever_effects; raw, never paired across members."""
    out: List[Dict[str, Any]] = []
    for e in getattr(obj, "lever_effects", ()) or ():
        out.append({
            "subject": e.subject_region_id,
            "signed_delta": getattr(e, "cell_count_delta", None),
            "vector": getattr(e, "vector", None),
        })
    return out


def _object_bands(library: Any, slot: Dict[str, Any], obj: Any) -> Dict[str, Any]:
    """B0->B3 for one object, each derived from its §2 belief signal. Contiguity
    enforces the cap: a band is UNREACHED when the one beneath is not GREEN, and
    B3 GREEN requires B2 GREEN — so no band out-confirms the band beneath it."""
    # B0 Partition — geometry present for an individuated slot (the floor).
    b0_green = (slot.get("region_id") is not None
                and (slot.get("cell_count") or 0) > 0)
    b0 = {"state": _GREEN if b0_green else _OPEN,
          "note": "geometry present" if b0_green else "geometry incomplete"}

    # B1 Existence — role posterior crossed (role != UNKNOWN); UNREACHED below B0.
    if b0["state"] != _GREEN:
        b1 = {"state": _UNREACHED, "note": "B0 not GREEN"}
    elif slot.get("role", "UNKNOWN") not in ("UNKNOWN", "UNCLASSIFIED"):
        # DD gap-1: UNCLASSIFIED (the nested read's no-child-yet) is a no-role
        # sentinel like UNKNOWN — B1 stays OPEN, not a confirmed existence.
        b1 = {"state": _GREEN, "note": f"role {slot['role']} confirmed"}
    else:
        b1 = {"state": _OPEN, "note": "role believed, below threshold"}

    # B2 Intrinsic — lever self-null (levers only); UNREACHED below B1.
    is_lever = slot.get("role") == "LEVER"
    if b1["state"] != _GREEN:
        b2 = {"state": _UNREACHED, "note": "B1 not GREEN"}
    elif not is_lever:
        b2 = {"state": _UNREACHED, "note": "not a lever — self-check n/a"}
    else:
        locality = getattr(obj, "lever_locality", None)
        gated = locality is not None
        dynamics = _has_dynamics(obj)
        if not gated:
            b2 = {"state": _OPEN,
                  "note": "not lever-confirmed (no locality) — gate unmet"}
        elif dynamics is not None:
            b2 = {"state": _OPEN,
                  "note": f"intrinsic: {dynamics} (not a self-null)"}
        elif locality != "REMOTE":
            # WO-D2: the remoteness DETERMINATION is read from the field, not
            # re-derived. (After gate + no-dynamics the value is REMOTE in the
            # current enum; this branch keeps the field the explicit source.)
            b2 = {"state": _OPEN,
                  "note": f"intrinsic: lever_locality={locality} "
                          f"— not a remote relay"}
        else:
            # WO-D2: remoteness from lever_locality == "REMOTE" (the field).
            # The count is RETAINED purely as the coverage gate hold #1 demands
            # — a single-observation REMOTE must NOT clear GREEN without it.
            coverage = _b2_self_null_count(library, slot["region_id"])
            if coverage >= _B2_NULL_THRESHOLD:
                b2 = {"state": _GREEN,
                      "note": f"intrinsic: remote-relay null, "
                              f"lever_locality=REMOTE, coverage={coverage}"}
            else:
                b2 = {"state": _OPEN,
                      "note": f"intrinsic: remote-relay null, "
                              f"lever_locality=REMOTE, coverage={coverage} "
                              f"(< {_B2_NULL_THRESHOLD})"}

    # B3 Edge — recorded lever->subject edge; GREEN only if B2 GREEN (cap).
    edges = _recorded_edges(obj)
    if b2["state"] == _UNREACHED:
        b3 = {"state": _UNREACHED, "note": "B2 UNREACHED", "edges": edges}
    elif not edges:
        b3 = {"state": _OPEN if is_lever else _UNREACHED,
              "note": "no recorded edge", "edges": edges}
    elif b2["state"] == _GREEN:
        b3 = {"state": _GREEN,
              "note": "edge recorded; B2 GREEN (contiguous)", "edges": edges}
    else:
        b3 = {"state": _OPEN,
              "note": "edge recorded; B2 OPEN (contiguity cap)", "edges": edges}

    return {"B0": b0, "B1": b1, "B2": b2, "B3": b3}


def _build_causal_map(library: Any, lever_rids: List[int]) -> Dict[str, Any]:
    """Per-lever recorded edges + the conserved-transfer composition row. The
    composition (a relation over a SET of edges sharing a subject) is NOT a
    per-entity band cell — it renders here, flagged OPEN, because no
    ConservedTransfer candidate forms at per-lever grain (D0.5/D0.6, §0.6).
    Membership is DERIVED from recorded edges (shared subject), never from a
    cross-member delta comparison (A3: no source/sink assignment is made)."""
    edges: List[Dict[str, Any]] = []
    subject_to_levers: Dict[int, List[int]] = {}
    for rid in lever_rids:
        obj = library.objects.get(rid)
        if obj is None:
            continue
        for ed in _recorded_edges(obj):
            edges.append({"lever": rid, "subject": ed["subject"],
                          "signed_delta": ed["signed_delta"]})
            subject_to_levers.setdefault(ed["subject"], []).append(rid)

    compositions: List[Dict[str, Any]] = []
    for subj, levs in sorted(subject_to_levers.items()):
        if len(levs) < 2:
            continue
        licensed = any(
            getattr(library.objects.get(l), "conserved_transfer", None) is not None
            for l in levs)
        compositions.append({
            "levers": sorted(levs),
            "subject": subj,
            "members": sorted(levs) + [subj],
            "state": _GREEN if licensed else _OPEN,
            "note": ("multiple levers change this subject; whether they compose "
                     "into a conserved opposing-operator machine is unresolved "
                     "— no candidate forms at per-lever grain (D0.5)"),
        })
    return {"edges": edges, "compositions": compositions}


def build_dossier(context: Any) -> WorldDossier:
    """One belief read → WorldDossier. Pure, read-only."""
    library = getattr(context, "semantic_library", None)
    code = read_classification_codestate(library)   # the single P2 read

    if library is None or code.get("status") != "IN_TAPE":
        return WorldDossier(axioms={"status": Excluded("no library on context")},
                            objects=[], levers=[], frontier={})

    # --- World axioms (foundation singletons from the one read) ---
    # WO_SWEEP_EGO_BIND D2: GOD_MODE is a POSITIVE resolution — agency confirmed
    # unembodied on a CLICK world (world_type_classifier.py:133 pairs CLICK with
    # GOD_MODE; stored at library_sync.py:432-435) — never a fallback for "ego
    # unknown". An embodied world with a bound ego lists its region ids; a
    # GLOBAL world renders GLOBAL; anything else — a NAV world whose ego is not
    # yet bound, or an unclassified world — is honestly unresolved. Evidence
    # before belief: the world row no longer fabricates GOD_MODE from an empty
    # id-list. (Byte-stable on stored-CLICK goldens: world_type == "CLICK".)
    if code["ego_object_ids"]:
        ego = list(code["ego_object_ids"])
    elif code["world_type"] == "CLICK":
        ego = "GOD_MODE"
    elif code["world_type"] == "GLOBAL":
        ego = "GLOBAL"
    else:
        ego = "UNKNOWN (unresolved)"
    # WO-E14 D2: the foundation counter view (counter_region_id) keys on the
    # categorical COUNTER role; a REACTIVE region deepened with sub_role="counter"
    # is also the counter. Render-local fallback (no belief-layer change): if no
    # categorical counter, surface the first sub_role=="counter" slot.
    _counter_rid = code["counter_region_id"]
    if _counter_rid is None:
        _sub = next((s["region_id"] for s in code["slots"]
                     if s.get("sub_role") == "counter"), None)
        _counter_rid = _sub
    counter = (f"Slot#{_counter_rid}" if _counter_rid is not None else "none")
    legible = sorted(getattr(library, "sdk_actions", {}).keys())
    axioms = {
        "game_id": library.header.game_id,
        "world_type": code["world_type"],
        "world_type_confidence": code["world_type_confidence"],
        "ego": ego,
        "counter": counter,
        "actions": legible if legible else Excluded("no SDK actions recorded"),
    }

    # --- Object list (canonical order: class, then region) ---
    from virelai_v4.diagnostics.store_a_readout import render_read, animation_annotation

    slots = sorted(code["slots"], key=lambda s: (s["class_id"], s["region_id"]))

    def _entry(s):
        obj = library.objects[s["region_id"]]
        # DD gap-1: role label reads the captain's store (render_read), NOT
        # Store-B s["role"]. tag is Band-1 (recorded); role is the inferred child
        # (never "REACTIVE" — that dissolved into the tag); locality is LOCAL/
        # REMOTE for levers. The (tag=REACTIVE, role=COUNTER) pair subsumes the
        # retired sub_role="counter" render (ruling R2).
        tag, role, locality, _conf = render_read(obj)
        return {
            "region_id": s["region_id"],
            "class_id": s["class_id"],
            "cell_count": s["cell_count"],
            "anchor": _anchor(obj.cells),
            "bbox": _bbox(obj.cells),        # WO_DOSSIER_MASTER_ROSTER
            "tag": tag,                      # Band-1 self-state (R3)
            "role": role if role is not None else "UNCLASSIFIED",
            "locality": locality,
            "animation": animation_annotation(obj),    # WO_AR D3: separate ANIM tag (None unless witnessed)
            "bands": _object_bands(library, s, obj),   # WO-D1
        }

    objects = [_entry(s) for s in slots]

    # --- Lever deepening (per believed lever) ---
    levers = []
    for s in slots:
        if s["role"] != "LEVER":
            continue
        obj = library.objects[s["region_id"]]
        # D5: target lives per-effect (each effect → its own subject slot),
        # paired inline at the effect level so a multi-effect lever can't be
        # mis-read positionally. The lever line carries the sub-taxonomy.
        effects = [_effect_struct(e) for e in obj.lever_effects]
        levers.append({
            "region_id": s["region_id"],
            "sub_taxonomy": _sub_taxonomy(obj),
            "observation_status": s["observation_status"],
            "effects": effects if effects else Excluded("no effect measured yet"),
            "candidate_roster": _candidate_roster(context, obj, s["region_id"]),
        })

    # --- Frontier ---
    individuated = sum(1 for s in code["slots"] if s["role"] != "UNKNOWN")
    # WO-E7 (de-collapse): the saturated tally reads the CONDITION field
    # obj.saturated, not the lever_mechanism TYPE field (which no longer carries
    # SATURATED). Without this the frontier count would zero out post-de-collapse.
    saturated = sum(1 for s in slots
                    if getattr(library.objects[s["region_id"]], "saturated", False))
    frontier = {
        "slots_total": len(code["slots"]),
        "slots_individuated": individuated,
        "levers_saturated": saturated,
        "probe_count": Excluded("per-turn probe log is the WO-5.1 drill-down"),
    }

    # WO-D1 — the conserved-transfer composition renders as a Causal-Map
    # relation row (OPEN at per-lever grain), not a per-entity band cell.
    lever_rids = [s["region_id"] for s in slots if s["role"] == "LEVER"]
    causal_map = _build_causal_map(library, lever_rids)

    return WorldDossier(axioms=axioms, objects=objects, levers=levers,
                        frontier=frontier, causal_map=causal_map)


# ---------------------------------------------------------------------------
# JSON machine-form — absent fields: null + sibling "_excluded"
# ---------------------------------------------------------------------------

def _json_node(v: Any) -> Any:
    if isinstance(v, dict):
        return _json_dict(v)
    if isinstance(v, list):
        return [_json_node(x) for x in v]
    return v


def _json_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if isinstance(v, Excluded):
            out[k] = None
            out[f"{k}_excluded"] = v.reason
        else:
            out[k] = _json_node(v)
    return out


def dossier_to_json(d: WorldDossier) -> Dict[str, Any]:
    """Machine form. Planning-complete shape present even where values are
    excluded (null + sibling "_excluded")."""
    return {
        "axioms": _json_dict(d.axioms),
        "objects": [_json_dict(o) for o in d.objects],
        "levers": [_json_dict(_lever_for_json(l)) for l in d.levers],
        "frontier": _json_dict(d.frontier),
        # WO-D1 — same single read; bands ride inside objects[*] via _json_dict.
        "causal_map": _json_node(d.causal_map),
    }


def _lever_for_json(l: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(l)
    eff = out.get("effects")
    if isinstance(eff, list):
        out["effects"] = [_json_dict(e) for e in eff]
    return out


# ---------------------------------------------------------------------------
# Terminal overview — one screen; excluded → "⊙ not built"
# ---------------------------------------------------------------------------

def _val(v: Any) -> str:
    return _NOT_BUILT if isinstance(v, Excluded) else str(v)


def _effect_line(e: Dict[str, Any]) -> str:
    """One effect, target paired inline (D5): `→ Slot#3 RIGID DISPLACEMENT ·
    2 EAST · ⊙ grid loc not stored`."""
    target = e["target"]
    target_txt = _NOT_BUILT if isinstance(target, Excluded) else str(target)
    dirn = e["direction"]
    motion = (_NOT_BUILT if isinstance(dirn, Excluded)
              else f"{_val(e['magnitude'])} {dirn}")
    gl = e["grid_location"]
    gl_txt = "⊙ grid loc not stored" if isinstance(gl, Excluded) else str(gl)
    return f"→ {target_txt}  {_val(e['quality'])} · {motion} · {gl_txt}"


# ---------------------------------------------------------------------------
# Axiom ✓/⚠ overlay (D1, ruling 5) — graded against an EXTERNAL key only
# ---------------------------------------------------------------------------

def load_axiom_key(path: str) -> Dict[str, Any]:
    """Read the external axiom key (read-only ground truth). The solver never
    sees it."""
    with open(path) as fh:
        return json.load(fh)


def _categorical_ego(ego_val: Any) -> str:
    return "GOD_MODE" if ego_val == "GOD_MODE" else "EMBODIED"


def _categorical_counter(counter_val: Any) -> str:
    # present/none categorical — never the slot id (D1).
    return "none" if counter_val == "none" else "present"


def grade_axioms(axioms: Dict[str, Any], key: Dict[str, Any]) -> Dict[str, Any]:
    """Per-row ✓ (MATCH) / ⚠ (DIVERGE) of the solver's belief vs the external
    key. Categorical for ego/counter; never a slot id."""
    solver = {
        "world_type": axioms.get("world_type"),
        "ego": _categorical_ego(axioms.get("ego")),
        "counter": _categorical_counter(axioms.get("counter")),
        "actions": (list(axioms.get("actions"))
                    if not isinstance(axioms.get("actions"), Excluded) else None),
    }
    out: Dict[str, Any] = {}
    for row in ("world_type", "ego", "counter", "actions"):
        kv = key.get(row)
        sv = solver[row]
        kvn = list(kv) if isinstance(kv, list) else kv
        out[row] = {"solver": sv, "key": kvn,
                    "verdict": "MATCH" if sv == kvn else "DIVERGE"}
    return out


def _axiom_row(label: str, value: str, grade: Optional[Dict[str, Any]]) -> str:
    if grade is None:
        return f"   {label:<12} {value}   NOT_GRADED (no axiom key)"
    g = grade[label]
    mark = "✓" if g["verdict"] == "MATCH" else "⚠"
    return f"   {label:<12} {value}   reality {g['key']}   {mark}"


# ---------------------------------------------------------------------------
# WO_DOSSIER_OVERVIEW_REFORMAT — render-layer presentation helpers.
# Pure presentation: every helper consumes ONLY the passed WorldDossier (F2);
# no new belief read, no build-layer touch (F1). Band semantics are unchanged —
# only the LABELS and GLYPHS change (transform 1). No source/sink/pairing label
# is ever emitted (F3/F4 fences).
# ---------------------------------------------------------------------------

# Transform 1 — band relabel + glyphs. Semantics from the _object_bands
# docstrings (B0 Partition · B1 Existence · B2 Intrinsic · B3 Edge); rename only.
_BAND_LABELS = (("B0", "Partition"), ("B1", "Existence"),
                ("B2", "Intrinsic"), ("B3", "Edge"))
# WO-REVISION R1 — the confirmed glyph is ● (not ✓). ✓/⚠ are reserved strictly
# for grade-vs-reality (the axiom overlay + the future grade-fold); no band state
# may use them, so a reader never confuses "band confirmed" with "matches key".
_BAND_GLYPH = {_GREEN: "●", _OPEN: "◯", _UNREACHED: "—"}


def _glyph(state: str) -> str:
    return _BAND_GLYPH.get(state, "?")


def _band_strip(o: Dict[str, Any]) -> str:
    """The four relabeled bands as a glyph strip for one object."""
    b = o.get("bands") or {}
    return " · ".join(f"{label} {_glyph(b.get(key, {}).get('state', _UNREACHED))}"
                      for key, label in _BAND_LABELS)


def _rn(ids: List[int]) -> str:
    """Sorted, de-duplicated `Rn` id list — the locator for a deduped item."""
    return ", ".join(f"R{i}" for i in sorted(set(ids)))


def _edge_inline(ed: Dict[str, Any]) -> str:
    """One recorded edge shown adjacently (F4: display only — no sign-test,
    no pairing, no source/sink label). Signed delta shown verbatim; a rigid
    displacement that stores no scalar delta shows `rigid`."""
    sd = ed.get("signed_delta")
    val = f"{sd:+d}" if isinstance(sd, int) else "rigid"
    return f"R{ed['lever']} {val}"


# ---- Transform 2 — FRICTIONS header (restates the belief's own gaps) --------

def _friction_rows(d: WorldDossier) -> List[Tuple[str, str]]:
    """Walk the dossier for non-GREEN bands, Excluded reasons, and OPEN
    compositions; DEDUPE by message so an identical note states once with its
    id list. Restates only what the belief already records about its gaps —
    asserts no new judgment (every message is a stored band-note / _excluded
    reason / composition note)."""
    band_items: Dict[str, List[int]] = {}
    for o in d.objects:
        b = o.get("bands") or {}
        for key, label in _BAND_LABELS:
            bd = b.get(key)
            if bd and bd["state"] != _GREEN:
                msg = f"{label} {bd['state'].lower()} — {bd['note']}"
                band_items.setdefault(msg, []).append(o["region_id"])
    lev_items: Dict[str, List[int]] = {}
    for lev in d.levers:
        rid = lev["region_id"]
        for fld in (lev.get("sub_taxonomy"), lev.get("candidate_roster"),
                    lev.get("effects")):
            if isinstance(fld, Excluded):
                lev_items.setdefault(fld.reason, []).append(rid)
    comp_items: Dict[str, List[int]] = {}
    for comp in (d.causal_map or {}).get("compositions", []):
        if comp.get("state") == _OPEN:
            comp_items.setdefault(comp["note"], []).append(comp["subject"])

    rows: List[Tuple[str, str]] = []
    for msg, ids in band_items.items():
        rows.append((msg, _rn(ids)))
    for reason, ids in lev_items.items():
        rows.append((reason, _rn(ids)))
    for note, subs in comp_items.items():
        loc = ", ".join(f"Slot#{s}" for s in sorted(set(subs)))
        rows.append((f"composition unresolved — {note}", loc))
    return rows


def _frictions_block(d: WorldDossier) -> List[str]:
    rows = _friction_rows(d)
    L = [" FRICTIONS  (where the belief marks its own gaps)"]
    if not rows:
        L.append("   none — every rendered surface is confirmed")
        return L
    for msg, loc in rows:
        L.append(f"   • {msg}  [{loc}]")
    return L


# ---- Transforms 3·4·5 — object list grouped by role -------------------------

def _object_list_block(d: WorldDossier) -> List[str]:
    L = [f" OBJECT LIST   {len(d.objects)} slots · canonical order "
         f"(class, then region)"]
    # DD gap-1: group by the inferred ROLE child; show TAG · ROLE on every line
    # (ruling R3). The role column never reads "REACTIVE" (it is the Band-1 tag);
    # a reactive counter reads `REACTIVE · COUNTER`, natively subsuming the
    # retired sub_role="counter" split (ruling R2, D5).
    levers = [o for o in d.objects if o["role"] == "LEVER"]
    counters = [o for o in d.objects if o["role"] == "COUNTER"]
    shown = {o["region_id"] for o in levers} | {o["region_id"] for o in counters}
    others = [o for o in d.objects if o["region_id"] not in shown]

    def _tr(o: Dict[str, Any]) -> str:
        loc = f"·{o['locality']}" if o.get("locality") else ""
        anim = f" ·{o['animation']}" if o.get("animation") else ""  # WO_AR D3: separate ANIM tag
        return f"{o['tag']} · {o['role']}{loc}{anim}"

    # Transform 4 — levers promoted; the shared intrinsic note stated ONCE.
    if levers:
        L.append(f"   LEVERS  ×{len(levers)}")
        b2_notes = {(o.get("bands") or {}).get("B2", {}).get("note")
                    for o in levers}
        shared = len(b2_notes) == 1 and None not in b2_notes
        if shared:
            L.append(f"     shared intrinsic: {next(iter(b2_notes))}")
        lev_by_rid = {lev["region_id"]: lev for lev in d.levers}
        for o in levers:
            lv = lev_by_rid.get(o["region_id"], {})
            note = (f"   {_val(lv.get('sub_taxonomy'))} / "
                    f"{_val(lv.get('observation_status'))}") if lv else ""
            L.append(f"     R{o['region_id']:<3} {_tr(o)}  class {_val(o['class_id'])} "
                     f"@{_val(o['anchor'])}  {_band_strip(o)}{note}")
            edges = (o.get("bands") or {}).get("B3", {}).get("edges") or []
            if edges:
                def _e(e: Dict[str, Any]) -> str:
                    sd = e.get("signed_delta")
                    val = f"{sd:+d}" if isinstance(sd, int) else "rigid"
                    return f"→ Slot#{e['subject']} {val}"
                L.append("          edges  "
                         + " · ".join(_e(e) for e in edges))
            if not shared and o.get("bands"):
                L.append(f"          intrinsic: {o['bands']['B2']['note']}")

    # Transform 5 — counter line (R63: REACTIVE · COUNTER); "levers tick by 0".
    for o in counters:
        L.append(f"   R{o['region_id']:<3} {_tr(o)}  class {_val(o['class_id'])} "
                 f"@{_val(o['anchor'])}  {_band_strip(o)}")
        ticks = [ed for ed in (d.causal_map or {}).get("edges", [])
                 if ed["subject"] == o["region_id"]]
        if ticks and all(ed.get("signed_delta") == 0 for ed in ticks):
            L.append(f"          note  all {len(ticks)} lever edge(s) tick "
                     f"this counter by 0")

    for o in others:
        L.append(f"   R{o['region_id']:<3} {_tr(o)}  class {_val(o['class_id'])} "
                 f"@{_val(o['anchor'])}  {_band_strip(o)}")
    return L


# ---- Transform 6 — causal map re-pivoted by subject -------------------------

def _object_roster_block(d: WorldDossier) -> List[str]:
    """WO_DOSSIER_MASTER_ROSTER M2 — the Director's screen→solver legend: one
    row per slot, full geometry, ordered for screen→name decode (you scan the
    grid, find the thing, read left-to-right to its name). Columns:
    anchor(r,c) · bbox · cells · class · role · id. Canonical order (class, then
    region) — same as d.objects. Additive: coexists with the collapsed OBJECT
    LIST summary above. Pure read of d.objects; honest ⊙ where a field is
    Excluded (e.g. a cells-absent slot's anchor/bbox)."""
    L = [f" OBJECT ROSTER   {len(d.objects)} slots · screen → solver's name",
         f"   {'anchor(r,c)':<14}{'bbox':<13}{'cells':<8}{'class':<8}"
         f"{'tag·role':<24}id"]
    for o in d.objects:
        anchor = o.get("anchor")
        anchor_txt = _NOT_BUILT if isinstance(anchor, Excluded) else f"@{anchor}"
        bbox = o.get("bbox")
        bbox_txt = (_NOT_BUILT if isinstance(bbox, Excluded)
                    else f"{bbox[0]}×{bbox[1]}")
        anim = f" ·{o['animation']}" if o.get("animation") else ""  # WO_AR D3
        L.append(f"   {anchor_txt:<14}{bbox_txt:<13}{_val(o['cell_count']):<8}"
                 f"{_val(o['class_id']):<8}"
                 f"{o['tag'] + '·' + _val(o['role']) + anim:<24}"
                 f"R{o['region_id']}")
    return L


def _causal_map_block(d: WorldDossier) -> List[str]:
    cmap = d.causal_map or {}
    edges = cmap.get("edges", [])
    comps = cmap.get("compositions", [])
    if not edges and not comps:
        return []
    L = ["", " CAUSAL MAP  (by subject)"]
    by_subject: Dict[int, List[Dict[str, Any]]] = {}
    for ed in edges:
        by_subject.setdefault(ed["subject"], []).append(ed)
    # Grouping is by shared subject ONLY (F4). Recorded order preserved — no
    # sort by delta, no min/max/argmax, no pairing or source/sink label. Signed
    # deltas shown adjacently so the reader sees structure; the instrument
    # names none of it.
    for subj in sorted(by_subject):
        adj = " · ".join(_edge_inline(ed) for ed in by_subject[subj])
        L.append(f"   Slot#{subj} ◀──  {adj}")
    for comp in comps:
        mem = ", ".join([f"R{l}" for l in comp["levers"]]
                        + [f"Slot#{comp['subject']}"])
        L.append(f"   composition {{{mem}}}: {comp['state']}")
    return L


# ---- Transform 8 — totals line ----------------------------------------------

def _totals_line(d: WorldDossier) -> str:
    f = d.frontier
    levers = sum(1 for o in d.objects if o["role"] == "LEVER")
    # DD gap-1: a REACTIVE·COUNTER reads role=COUNTER natively (the sub_role hack
    # is retired); reactive is counted off the Band-1 TAG, not the role.
    counters = sum(1 for o in d.objects if o["role"] == "COUNTER")
    reactive = sum(1 for o in d.objects if o["tag"] == "REACTIVE")
    return (f" {_val(f.get('slots_individuated'))}/{_val(f.get('slots_total'))} "
            f"individuated · {levers} levers · {counters} counter · "
            f"{reactive} reactive · {_val(f.get('levers_saturated'))} saturated "
            f"· probes {_val(f.get('probe_count'))}")


# ---- Transform 7 — deduped constants (footnotes, header tag) ----------------

_REALITY_FOOTNOTE = (" note  lever-effect reality: graded in Campaign B "
                     "(charter A/B cut)")


def render_overview(d: WorldDossier,
                    axiom_key: Optional[Dict[str, Any]] = None) -> str:
    """The human overview, reformatted for a reader (WO_DOSSIER_OVERVIEW_
    REFORMAT). Pure presentation of the SAME single belief read — frictions
    surfaced first, bands relabeled, reactives collapsed, levers promoted, the
    causal map pivoted by subject, repeated constants deduped, plus a
    deterministic NARRATIVE. Asserts no fact the granular JSON form omits."""
    a = d.axioms
    if isinstance(a.get("status"), Excluded):
        return f"══ WORLD DOSSIER ══\n  {_NOT_BUILT}: {a['status'].reason}"

    # DD gap-6: the foundation key rides the same --axiom-key arg as the world-
    # axioms key, told apart by key_type. Split so grade_axioms only ever sees a
    # world key (a foundation key → world grade None → NOT_GRADED, honest); the
    # foundation key drives its own FOUNDATION GRADE block appended below.
    _fkey = axiom_key if is_foundation_key(axiom_key) else None
    _wkey = None if _fkey is not None else axiom_key
    grade = grade_axioms(a, _wkey) if _wkey is not None else None

    L: List[str] = []
    L.append(f"══ WORLD DOSSIER · {_val(a.get('game_id'))} "
             f"════════════════════════")
    L.append("  legend  ● confirmed · ◯ open · — unreached   |   "
             "bands: Partition · Existence · Intrinsic · Edge")
    L.append("")

    # Transform 2 — frictions first.
    L.extend(_frictions_block(d))
    L.append("")

    # World axioms. Transform 7: NOT_GRADED stated ONCE as a header tag (not
    # appended to every row). Graded rows still carry per-row ✓/⚠ verbatim.
    if grade is not None:
        L.append(" WORLD AXIOMS")
        L.append(_axiom_row("world_type",
                            f"{_val(a.get('world_type'))} "
                            f"{_val(a.get('world_type_confidence'))}", grade))
        L.append(_axiom_row("ego", _val(a.get("ego")), grade))
        L.append(_axiom_row("counter", _val(a.get("counter")), grade))
        L.append(_axiom_row("actions", _val(a.get("actions")), grade))
    else:
        L.append(" WORLD AXIOMS   [NOT_GRADED (no axiom key)]")
        L.append(f"   {'world_type':<12} {_val(a.get('world_type'))} "
                 f"{_val(a.get('world_type_confidence'))}")
        L.append(f"   {'ego':<12} {_val(a.get('ego'))}")
        L.append(f"   {'counter':<12} {_val(a.get('counter'))}")
        L.append(f"   {'actions':<12} {_val(a.get('actions'))}")
    L.append("")

    # Transforms 3·4·5 — object list grouped + collapsed + promoted.
    L.extend(_object_list_block(d))
    L.append("")

    # WO_DOSSIER_MASTER_ROSTER — the full per-object legend, immediately after
    # the collapsed OBJECT LIST. The collapsed list is the summary ("what shape
    # is this world"); the roster is the key ("which object is that"). Both earn
    # their place; the roster is additive and reads only d.objects.
    L.extend(_object_roster_block(d))
    L.append("")

    # WO-REVISION R3 — the per-lever deepening detail (candidate roster + the
    # per-effect quality/direction/grid-loc lines) is DEMOTED to a drill-down to
    # end the three-way restatement (frictions ‖ narrative ‖ deepening). Each
    # lever's type/status/edges now shows once on the R2 lever line above; the
    # granular per-effect block lives at `--detail deepening`. Lossless-by-drill:
    # the drill-down + dossier_to_json still carry every effect field.

    # Transform 8 — totals.
    L.append(_totals_line(d))

    # Transform 6 — causal map by subject.
    L.extend(_causal_map_block(d))

    # D3 — narrative.
    L.append("")
    L.append(render_narrative(d))

    # DD gap-6 — FOUNDATION GRADE (the correctness column), appended when a
    # foundation key is supplied. Pure read over d.objects; no belief write.
    if _fkey is not None:
        L.append("")
        L.extend(render_foundation_grade(d.objects, _fkey))

    L.append("")
    L.append(_REALITY_FOOTNOTE)
    L.append(" ▸ slot <id> · probes · axioms · deepening   (drill-downs: "
             "--detail deepening for per-effect quality/grid-loc + roster)")
    L.append("═" * 60)
    return "\n".join(L)


# ---------------------------------------------------------------------------
# D3 — render_narrative: deterministic template-fill. NO LLM, NO synthesis.
# F3 HARD FENCE: every sentence stamps a field present in dossier_to_json
# output. Verb discipline: reads-as / records / is-believed / has-not-confirmed
# — never is / knows / works. No sentence asserts a relation the belief lacks
# (no "oppose", "pair", "conserved" as a claim); no source/sink/donor/recipient
# designation. Confidence values retained verbatim.
# ---------------------------------------------------------------------------

def render_narrative(d: WorldDossier) -> str:
    a = d.axioms
    if isinstance(a.get("status"), Excluded):
        return f" NARRATIVE\n   {_NOT_BUILT}: {a['status'].reason}"

    L = [" NARRATIVE  (deterministic; every sentence stamps a stored field)"]

    # Paragraph 1 — world / ego / actions / counter (all from d.axioms).
    L.append(f"   The world reads-as {_val(a.get('world_type'))} at confidence "
             f"{_val(a.get('world_type_confidence'))}. The ego is-believed "
             f"{_val(a.get('ego'))}. The recorded actions are "
             f"{_val(a.get('actions'))}. The counter is-believed "
             f"{_val(a.get('counter'))}.")

    # Paragraph 2 — object roster + per-lever recorded effects (from d.objects,
    # d.levers — each effect's stored target/quality/direction/magnitude).
    levers = [o for o in d.objects if o["role"] == "LEVER"]
    counters = [o for o in d.objects if o["role"] == "COUNTER"]
    reactive = [o for o in d.objects if o["tag"] == "REACTIVE"]   # DD gap-1: tag, not role
    p2 = (f"   The belief records {len(d.objects)} objects: {len(levers)} "
          f"levers, {len(counters)} counter, {len(reactive)} reactive.")
    for lev in d.levers:
        rid = lev["region_id"]
        effs = lev.get("effects")
        if isinstance(effs, Excluded):
            p2 += f" Lever R{rid} has-not-confirmed an effect ({effs.reason})."
            continue
        descs = []
        for e in effs:
            tgt = e["target"]
            tgt_txt = _NOT_BUILT if isinstance(tgt, Excluded) else str(tgt)
            dirn = e["direction"]
            motion = (_NOT_BUILT if isinstance(dirn, Excluded)
                      else f"{_val(e['magnitude'])} {dirn}")
            descs.append(f"{tgt_txt} ({_val(e['quality'])}, {motion})")
        p2 += f" Lever R{rid} records effects on " + "; ".join(descs) + "."
    L.append(p2)

    # Paragraph 3 — where knowledge ends: the Excluded reasons + non-GREEN
    # bands + OPEN compositions, read out as sentences (each a stored field).
    rows = _friction_rows(d)
    if rows:
        gaps = " ".join(f"On {loc}, the belief has-not-confirmed: {msg}."
                        for msg, loc in rows)
        L.append("   Where knowledge ends — " + gaps)
    else:
        L.append("   Where knowledge ends — the belief marks no open gaps on "
                 "the rendered surfaces.")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Drill-down render-modes (D3/D4, ruling 4) — render-modes, not a REPL.
# Read-only; honest excluded-with-reason for fields the belief does not store.
# ---------------------------------------------------------------------------

def render_slot_detail(context: Any, region_id: int) -> str:
    lib = getattr(context, "semantic_library", None)
    if lib is None or region_id not in lib.objects:
        return f"── SLOT #{region_id} ──\n  (not found)"
    o = lib.objects[region_id]
    L = [f"── SLOT #{region_id} ──"]
    L.append(f"  geometry   class {o.class_id} · {o.shape_desc} · "
             f"anchor {_val(_anchor(o.cells))} · {o.cell_count} cells")
    # DD gap-1: TAG (recorded) then ROLE (inferred), off the captain's store.
    _tag, _role, _loc, _conf = render_read(o)
    _role_disp = _role if _role is not None else "UNCLASSIFIED"
    _loc_disp = f" · {_loc}" if _loc else ""
    L.append(f"  TAG        {_tag}")
    L.append(f"  ROLE       resolved {_role_disp}{_loc_disp} · confidence {_conf}")
    _anim = animation_annotation(o)   # WO_AR D3: separate ANIMATION tag, present only when witnessed
    if _anim:
        L.append(f"  ANIMATION  {_anim} · transient (interior planes); settled tag·role unaffected")
    L.append(f"  ROLE POSTERIOR (5 axiomatic categories)   {_NOT_BUILT}: "
             f"five-category posterior not stored; belief carries the resolved "
             f"role + a single confidence (P3)")
    if _role == "LEVER":
        L.append(f"  LEVER SUB-TAXONOMY   {_val(_sub_taxonomy(o))}")
        for e in o.lever_effects:
            L.append(f"     effect  {_effect_line(_effect_struct(e))}")
            L.append(f"             reality  {_REALITY_CAMPAIGN_B}")
    L.append(f"  touch history   change_count={o.change_count} · "
             f"active_frames={o.active_frame_count} · first={o.first_active_frame} "
             f"· last={o.last_active_frame} · observed={o.actions_observed}")
    L.append(f"     per-touch timeline   {_NOT_BUILT}: per-timestamp touch list "
             f"not stored (counts + first/last only)")
    return "\n".join(L)


def render_axioms_detail(context: Any,
                         axiom_key: Optional[Dict[str, Any]] = None) -> str:
    a = build_dossier(context).axioms
    if isinstance(a.get("status"), Excluded):
        return f"── AXIOMS ──\n  {_NOT_BUILT}: {a['status'].reason}"
    # DD gap-6: a foundation key is not a world-axioms key — never grade the
    # world rows against it (would read absent rows as DIVERGE). World key only.
    _wkey = None if is_foundation_key(axiom_key) else axiom_key
    grade = grade_axioms(a, _wkey) if _wkey is not None else None
    L = ["── AXIOMS ──"]
    L.append(_axiom_row("world_type",
                        f"{_val(a.get('world_type'))} "
                        f"{_val(a.get('world_type_confidence'))}", grade))
    L.append(_axiom_row("ego", _val(a.get("ego")), grade))
    L.append(_axiom_row("counter", _val(a.get("counter")), grade))
    L.append(_axiom_row("actions", _val(a.get("actions")), grade))
    return "\n".join(L)


def render_role_detail(context: Any, role_name: str) -> str:
    lib = getattr(context, "semantic_library", None)
    role = role_name.upper()
    L = [f"── ROLE {role} ──"]
    if lib is not None:
        for rid in sorted(lib.objects):
            o = lib.objects[rid]
            _tag, _role, _loc, _conf = render_read(o)   # DD gap-1: derived role
            if _role == role:
                L.append(f"   R{rid}  {_tag}·{_role}  class {o.class_id} · conf {_conf}")
    if len(L) == 1:
        L.append("   (no slots resolved to this role)")
    return "\n".join(L)


def render_probes_detail(context: Any) -> str:
    """The probe log from the RECORDED subset only (ruling 2): per-region probe
    counts + the last probe. The dispatched-question and belief-built columns
    are excluded-with-reason — the solver stores no per-turn dispatch log."""
    ph = getattr(context, "probe_history", None) or {}
    L = ["── PROBE LOG  (record → deduce) ──"]
    L.append("  per-region probe counts (the recorded subset):")
    for rid in sorted(ph):
        L.append(f"     Slot#{rid}: {ph[rid]} probes")
    if not ph:
        L.append("     (no probes recorded yet)")
    last_rid = getattr(context, "last_probe_target_region_id", None)
    last_kind = getattr(context, "last_probe_action_kind", None)
    L.append(f"  last probe: target="
             f"{'Slot#' + str(last_rid) if last_rid is not None else 'none'} "
             f"· action={last_kind or 'none'}")
    L.append(f"  dispatched-question   {_NOT_BUILT}: excluded — not recorded "
             f"(per-turn dispatch log not stored; ruling 2)")
    L.append(f"  belief-built          {_NOT_BUILT}: excluded — not recorded "
             f"(per-turn integration result not stored; ruling 2)")
    L.append(f"  per-turn timeline     {_NOT_BUILT}: excluded — only per-region "
             f"counts + last probe are stored (ruling 2)")
    return "\n".join(L)


def render_lever_deepening(context: Any) -> str:
    """WO-REVISION R3 — the per-lever deepening drill-down (the block demoted
    out of the default overview). Per believed lever: the candidate roster
    (raw id→signed-delta, pre-license) and the per-effect quality · direction ·
    grid-location lines. Read-only over the SAME single belief read
    (build_dossier(context)); no new belief field. Lossless host for the detail
    the overview no longer restates — dossier_to_json still carries it all."""
    d = build_dossier(context)
    L = ["── LEVER DEEPENING  (per-effect quality · direction (NSWE) · "
         "grid location · roster) ──"]
    if not d.levers:
        L.append("  (no levers in belief)")
        return "\n".join(L)
    for lev in d.levers:
        L.append(f"   R{lev['region_id']}  sub-taxonomy "
                 f"{_val(lev['sub_taxonomy'])}  "
                 f"[status {_val(lev.get('observation_status'))}]")
        # WO-D0.5 — candidate roster (pre-license), raw id→signed-delta map.
        roster = lev.get("candidate_roster")
        if isinstance(roster, Excluded):
            L.append(f"         candidate roster: {_NOT_BUILT} ({roster.reason})")
        else:
            members_txt = ", ".join(f"Slot#{mid}: {dl:+d}"
                                    for mid, dl in roster["members"].items())
            L.append(f"         candidate roster: {{{members_txt}}} · "
                     f"conserved_quantity {roster['conserved_quantity']} · "
                     f"[{roster['license_status']}]")
        effects = lev.get("effects")
        if isinstance(effects, Excluded):
            L.append(f"         {_NOT_BUILT}: {effects.reason}")
            continue
        for e in effects:
            L.append(f"         {_effect_line(e)}")
    return "\n".join(L)


def render_detail(context: Any, spec: str,
                  axiom_key: Optional[Dict[str, Any]] = None,
                  effect_model_key: Optional[Dict[str, Any]] = None) -> str:
    """Dispatch a --detail render-mode. No shell, no cross-frame state."""
    spec = spec.strip()
    if spec == "probes":
        return render_probes_detail(context)
    if spec == "axioms":
        return render_axioms_detail(context, axiom_key)
    if spec == "partition":
        return render_cell_partition(context)
    if spec == "deepening":
        return render_lever_deepening(context)
    if spec == "effects":
        return render_effect_grade(context, effect_model_key)
    if spec.startswith("effects:"):
        try:
            return render_effect_grade(context, effect_model_key,
                                       int(spec.split(":", 1)[1]))
        except ValueError:
            return f"── detail ──\n  bad region id in '{spec}'"
    if spec.startswith("slot:"):
        try:
            return render_slot_detail(context, int(spec.split(":", 1)[1]))
        except ValueError:
            return f"── detail ──\n  bad slot id in '{spec}'"
    if spec.startswith("role:"):
        return render_role_detail(context, spec.split(":", 1)[1])
    return f"── detail ──\n  unknown render-mode '{spec}'"


# ---------------------------------------------------------------------------
# Effect-model grade surface (WO_EFFECT_DIVERGENCE_GRADE · Campaign B · v2).
#
# Realizes the effect-reality slot Campaign A rendered as "graded in Campaign
# B": the RECORDED per-subject representation (each subject's class resolved
# from belief), graded against the committed effect-model oracle —
# REALITY (the key's functional class + background figure/ground pair) and
# GRADE (computed ✓/⚠: is the functional class tracked? is a conserved relation
# representable?). LOCATE, NOT CLOSE — this surface names the stage, the
# measurement, and the delta; it does NOT name the operation verb (Campaign C)
# and asserts no reality verdict of its own (the key is the pre-registered
# reality; with no key the surface is NOT_GRADED).
#
# v2 corrections over v1: the grade is aimed at the functional class (key),
# NOT an internal Δ-sum (which conflated the background figure/ground pair with
# the functional class); net-grid Δ, if shown, is labeled background
# bookkeeping, never "conservation"; the PIN measurement/delta prose is COMPUTED
# from the resolved classes and recorded deltas, not templated.
#
# Floor-safe by construction (as the A instrument was): read-only over belief
# (reads obj.lever_effects + obj.class_id only), no write path, no decision-walk
# touch, and ADDITIVE — the existing _effect_struct reality placeholder
# (_REALITY_CAMPAIGN_B) is unchanged; this is a separate render, exactly as
# WO-5.1's axiom overlay was added beside the base render.
# ---------------------------------------------------------------------------

# The recording seam: record_lever_effect stores one independent LeverEffect
# per subject, and the contract (contracts/lever_effect.py:50-57) carries no
# field coupling two entries — there is no place to represent a conserved
# relation across subjects. That structural fact is the located stage.
_RECORDING_SEAM = (
    "record_lever_effect (semantic_library.py:566) stores one independent "
    "LeverEffect per subject; the contract (contracts/lever_effect.py:50-57) "
    "carries no field coupling paired subjects — no conserved relation is "
    "representable in the store"
)


def _effect_signed_delta(effect: Any) -> Any:
    """The signed per-subject cell-delta the store holds for this effect
    (RECORD-THEN-DEDUCE):
      - NON_RIGID: cell_count_delta (already signed: +grew / -shrank).
      - RIGID:     no scalar cell-delta is stored (the vector is a per-subject
                   displacement) → excluded, never fabricated.
    NOTE (v2): this is a per-subject recorded value shown for honesty. It is
    NOT summed into a cross-subject 'conservation' figure — the v1 Δ-sum
    conflated the background figure/ground pair with the functional class and
    reported a value the fixed-grid representation forces. The grade is against
    the committed key (grade_effect_model), not an internal sum.
    """
    ccd = getattr(effect, "cell_count_delta", None)
    if ccd is not None:
        return int(ccd)
    return Excluded("rigid effect stores a per-subject vector; "
                    "no scalar cell-delta recorded")


def _resolve_subject_class(library: Any, subject_region_id: Any) -> Any:
    """Resolve a recorded effect's subject to its object class (P2 accessor:
    ``library.objects[subject_region_id].class_id``, the per-slot class the
    rung-1 reader already exposes). A subject that does not resolve renders
    ``class excluded — unresolved`` — never a guessed class. This is what lets
    the grade tell a functional-class subject from a background-class one."""
    if library is None or subject_region_id is None:
        return Excluded("class excluded — unresolved")
    obj = getattr(library, "objects", {}).get(subject_region_id)
    if obj is None:
        return Excluded("class excluded — unresolved")
    cls = getattr(obj, "class_id", None)
    if cls is None:
        return Excluded("class excluded — unresolved")
    return cls


def effect_model_view(obj: Any, library: Any = None) -> Dict[str, Any]:
    """The recorded per-subject representation for one lever, each subject's
    class resolved from belief (P2). Pure, read-only. No cross-subject
    'conservation' is computed here (v1's Δ-sum conflated background with the
    functional class); the recorded effects are graded against the committed
    key by grade_effect_model. REALITY and GRADE fill only with a key."""
    effects = list(getattr(obj, "lever_effects", ()) or ())
    rows: List[Dict[str, Any]] = []
    for e in effects:
        subj = getattr(e, "subject_region_id", None)
        rows.append({
            "subject": subj,
            "subject_class": _resolve_subject_class(library, subj),
            "operation_kind": getattr(e, "operation_kind", None),
            "recorded_delta": _effect_signed_delta(e),
            "observation_count": getattr(e, "observation_count", None),
        })
    return {
        "region_id": getattr(obj, "region_id", None),
        "recorded": rows,                          # representation: independent
        "representation_note": _RECORDING_SEAM,    # why a relation is unrepresentable
        # WO-C3: the lever's authored conserved-transfer relation (or None). The
        # grade reads its PRESENCE to flip conserved-relation-represented.
        "conserved_transfer": getattr(obj, "conserved_transfer", None),
        "reality": Excluded(_REALITY_CAMPAIGN_B),  # filled only from the key
        "grade": Excluded("NOT_GRADED (no effect-model oracle — §5)"),
    }


def grade_effect_model(view: Dict[str, Any],
                       model_key: Optional[Dict[str, Any]] = None
                       ) -> Dict[str, Any]:
    """Grade the recorded representation against the EXTERNAL effect-model
    oracle (committed, verb-free, the solver never reads it — Ruling 5 / axiom-
    key precedent). Computes two ✓/⚠ checks from the key + the classes resolved
    in `view`, and fills REALITY from the key. No key → NOT_GRADED (no
    fabricated pass/fail). Names no verb; asserts no fix.

    Checks:
      functional-class-tracked      — are any recorded effects on the key's
                                      functional_transfer.class?
      conserved-relation-represented — structural: the contract has no field
                                      coupling a source and a sink, so
                                      independent per-subject entries can never
                                      represent it (always ⚠, stated from the
                                      contract, key-independent)."""
    out = dict(view)
    if model_key is None:
        out["reality"] = Excluded("NOT_GRADED (no effect-model oracle — §5)")
        out["grade"] = Excluded("NOT_GRADED (no effect-model oracle — §5)")
        return out
    ft = model_key.get("functional_transfer", {}) or {}
    bg = model_key.get("background", {}) or {}
    functional_class = ft.get("class")
    background_pair = list(bg.get("figure_ground_pair", []) or [])
    recorded_classes = sorted({
        r["subject_class"] for r in view["recorded"]
        if not isinstance(r["subject_class"], Excluded)
    })
    out["reality"] = {
        "functional_class": functional_class,
        "conserved": ft.get("conserved"),
        "structure": ft.get("structure"),
        "background_pair": background_pair,
        "net_grid_delta_zero": model_key.get("net_grid_delta_zero"),
    }
    # WO-C3 §5 — GRADE READ-SCOPE FENCE: the grade reads functional_class and
    # conserved ONLY. It must NOT read structure: the key says
    # structure=object_to_object, but C3 authors a global-total-over-boundary
    # structure that is not object_to_object — a structure-reading grader would
    # false-fail a correct verb. structure stays in REALITY (display) only.
    conserved_key = ft.get("conserved")        # read: conserved  ✓
    # (ft.get("structure") deliberately NOT read into the grade — fence)
    transfer = view.get("conserved_transfer")
    conserved_relation_represented = (
        transfer is not None and conserved_key is True)
    out["grade"] = {
        "functional_class_tracked": functional_class in recorded_classes,
        "recorded_classes": recorded_classes,
        "functional_class": functional_class,
        "background_pair": background_pair,
        # WO-C3: ✓ once the lever holds an authored ConservedTransfer and the key
        # marks the transfer conserved. The relation now HAS a field to live in
        # (contracts/conserved_transfer.py); ⚠ only while it is absent.
        "conserved_relation_represented": conserved_relation_represented,
    }
    return out


def load_effect_model_key(path: str) -> Dict[str, Any]:
    """Read the external effect-model oracle (read-only ground truth; the
    solver never sees it), mirroring load_axiom_key."""
    with open(path) as fh:
        return json.load(fh)


def _grade_val(v: Any) -> str:
    return _NOT_BUILT if isinstance(v, Excluded) else str(v)


def _class_txt(cls: Any) -> str:
    return cls.reason if isinstance(cls, Excluded) else f"class {cls}"


def _mark(ok: bool) -> str:
    return "✓" if ok else "⚠"


def _subject_role(cls: Any, functional_class: Any,
                  background_pair: List[Any]) -> str:
    """Name a recorded subject's role from its RESOLVED class against the key:
    functional (the key's functional class), background (the key's figure/
    ground pair), or other. Render-only labelling for the PIN prose — it reads
    the already-resolved class and the key fields; it computes no grade."""
    if isinstance(cls, Excluded):
        return "unresolved"
    if cls == functional_class:
        return "functional"
    if cls in (background_pair or []):
        # potential_background: the is_background belief is a graded, defeasible
        # hypothesis (ignore_score >= 0.60, cleared on unexpected change), not a
        # verdict — figure/ground is a lossless choice the cells do not assert.
        # Render candidacy, not a hard call. (Score-bearing form deferred: the
        # ignore_score is not in scope at this render seam.)
        return "potential_background"
    return "other"


def render_effect_grade(context: Any,
                        model_key: Optional[Dict[str, Any]] = None,
                        region_id: Optional[int] = None) -> str:
    """The effect-model grade surface: RECORDED (per-subject, class-resolved) ‖
    REALITY (the committed key) ‖ GRADE (computed ✓/⚠), then the PIN
    (stage · measurement · delta), the measurement and delta COMPUTED from the
    resolved classes and recorded deltas — not a template. Locates #4 against
    the key; never names the verb."""
    lib = getattr(context, "semantic_library", None)
    L: List[str] = ["══ EFFECT-MODEL GRADE  (recorded ‖ reality(key) ‖ grade) ══"]
    if lib is None:
        L.append(f"  {_NOT_BUILT}: no library on context")
        L.append("═" * 60)
        return "\n".join(L)
    if region_id is not None:
        rids = [region_id]
    else:
        rids = [rid for rid in sorted(lib.objects)
                if getattr(getattr(lib.objects[rid], "role", None), "value",
                           None) == "LEVER"]
    any_lever = False
    for rid in rids:
        obj = lib.objects.get(rid)
        if obj is None or getattr(getattr(obj, "role", None), "value",
                                  None) != "LEVER":
            continue
        any_lever = True
        view = grade_effect_model(effect_model_view(obj, lib), model_key)
        L.append("")
        L.append(f" R{rid}  lever effect model")
        # RECORDED — independent per-subject entries, each with resolved class
        L.append("   RECORDED (representation · per-subject, independent):")
        if not view["recorded"]:
            L.append(f"      {_NOT_BUILT}: no effect recorded yet")
        for r in view["recorded"]:
            subj = r["subject"]
            subj_txt = f"Slot#{subj}" if subj is not None else _NOT_BUILT
            L.append(f"      → {subj_txt} [{_class_txt(r['subject_class'])}]  "
                     f"{r['operation_kind'] or _NOT_BUILT}  "
                     f"Δ={_grade_val(r['recorded_delta'])}  "
                     f"(n={r['observation_count']})")
        # REALITY — the committed key (verb-free), or NOT_GRADED
        reality = view["reality"]
        if isinstance(reality, Excluded):
            L.append(f"   REALITY (model oracle):  {reality.reason}")
        else:
            L.append(f"   REALITY (model oracle):  functional effect class "
                     f"{reality['functional_class']}, conserved="
                     f"{reality['conserved']}, structure {reality['structure']} "
                     f"· background pair {reality['background_pair']} "
                     f"(bookkeeping) · net-grid-zero incidental")
        # GRADE — computed ✓/⚠ from the key + resolved classes
        grade = view["grade"]
        if isinstance(grade, Excluded):
            L.append(f"   GRADE:  {grade.reason}")
        else:
            L.append("   GRADE (computed ✓/⚠):")
            L.append(f"      {_mark(grade['functional_class_tracked'])} "
                     f"functional-class-tracked  (recorded classes "
                     f"{grade['recorded_classes']} vs functional class "
                     f"{grade['functional_class']})")
            _ct = view.get("conserved_transfer")
            _ct_reason = (
                f"coupled relation present — members "
                f"{list(_ct.member_subject_ids)}, conserved quantity "
                f"{_ct.conserved_quantity}"
                if _ct is not None
                else "independent per-subject entries — no coupled relation "
                     "authored yet (coupling field available)")
            L.append(f"      {_mark(grade['conserved_relation_represented'])} "
                     f"conserved-relation-represented  ({_ct_reason})")
            signed = [r["recorded_delta"] for r in view["recorded"]
                      if not isinstance(r["recorded_delta"], Excluded)]
            if signed:
                L.append(f"      net-grid Δ (recorded): Σ={sum(signed)} — "
                         f"background bookkeeping (figure/ground pair "
                         f"{grade['background_pair']} per key; not a "
                         f"conservation signal)")
        # THE PIN — stage fixed; measurement + delta COMPUTED from values
        L.append("   PIN (locate, not close):")
        L.append(f"      stage        recording seam — {_RECORDING_SEAM}")
        if isinstance(grade, Excluded):
            L.append("      measurement  NOT_GRADED — supply the effect-model "
                     "oracle (§5)")
            L.append("      delta        NOT_GRADED")
        else:
            fc = grade["functional_class"]
            rc = grade["recorded_classes"]
            on_fc = sum(1 for r in view["recorded"]
                        if not isinstance(r["subject_class"], Excluded)
                        and r["subject_class"] == fc)
            # Name each subject by its RESOLVED class (functional / background /
            # other) so the prose cannot contradict the ✓/⚠ grade — the v1
            # template said "sit on background classes" for every subject,
            # mislabelling a functional-class subject as background.
            deltas_txt = ", ".join(
                f"Slot#{r['subject']}[{_class_txt(r['subject_class'])} · "
                f"{_subject_role(r['subject_class'], fc, grade['background_pair'])}]:"
                f"{_grade_val(r['recorded_delta'])}"
                for r in view["recorded"]) or "none"
            L.append(f"      measurement  recorded subject classes {rc} vs "
                     f"functional class {fc}; {on_fc} recorded effect(s) on "
                     f"class {fc}")
            _rep = "represented (coupled relation authored)" \
                if view.get("conserved_transfer") is not None \
                else ("unrepresented (stored as independent per-subject "
                      "entries; no coupled relation)")
            L.append(f"      delta        the class-{fc} conserved relation is "
                     f"{_rep}; recorded effects {{{deltas_txt}}}")
    if not any_lever:
        L.append("  (no levers in belief to grade)")
    L.append("═" * 60)
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Cell-partition surface (WO_CELL_PARTITION_RENDER · Campaign B · v1).
#
# Makes the cell accounting TOTAL and CLASS-ATTRIBUTED so individuation is
# un-hideable: every Slot + a class-attributed named residual summing to the
# grid total per frame (Part A), plus a per-press delta sum-check naming each
# changed cell's destination class (Part B). LOCATE, NOT CLOSE — the surface
# reports where cells land; it asserts neither individuation-held nor failed.
#
# Read-only over belief (Ruling 2), additive, floor-safe. §4b read-only seam:
# the per-press delta is CONSUMED from context.world_delta (the canonical
# per-frame delta, contracts/world_delta.py) — never recomputed, never written.
# Firewall: no class number / colour / position / magnitude / 4096 literal in
# code — the grid total comes from the grid's own shape, residual classes are
# runtime grid values, the per-cell destination is read from belief membership
# + the consumed delta. (class_id == region pixel value, role_classifier.py:270
# / spawn_populator.py:118 — so residual-by-grid-value shares the Slot's scale.)
# ---------------------------------------------------------------------------

def _grid_shape(grid: Any) -> Optional[Tuple[int, int]]:
    """Read (H, W) from a grid (numpy array or nested sequence) without a
    dimension literal. None when no usable grid."""
    if grid is None:
        return None
    shape = getattr(grid, "shape", None)
    if shape is not None and len(shape) >= 2:
        return int(shape[0]), int(shape[1])
    try:
        return len(grid), len(grid[0])
    except (TypeError, IndexError):
        return None


def _grid_at(grid: Any, r: int, c: int) -> int:
    """Cell value (== class_id) at (r, c); numpy and nested-sequence safe."""
    return int(grid[r][c])


def _delta_attribution(context: Any, lib: Any,
                       cell_to_slot: Dict[Tuple[int, int], int]) -> Any:
    """Part B (§4a): attribute every changed cell this frame to a NAMED
    destination — the Slot it joined, or the residual class it now shows
    (which keeps un-individuated `residual:class K` distinct from repainted-
    to-background `residual:class B`). The delta is CONSUMED read-only from
    context.world_delta (§4b); nothing is recomputed."""
    wd = getattr(context, "world_delta", None)
    if wd is None:
        return Excluded("no per-press delta at the render seam "
                        "(context.world_delta is None)")
    changed = getattr(wd, "world_cells", frozenset()) or frozenset()
    transitions = getattr(wd, "world_transitions", {}) or {}
    by_destination: Dict[str, int] = {}
    rows: List[Dict[str, Any]] = []
    for cell in sorted(changed):
        old_new = transitions.get(cell)
        new_cls = old_new[1] if old_new else None
        rid = cell_to_slot.get(cell)
        if rid is not None:
            dest = f"Slot#{rid}"
        elif new_cls is not None:
            dest = f"residual:class {new_cls}"
        else:
            dest = "unattributed"
        rows.append({"cell": cell, "transition": old_new, "destination": dest})
        by_destination[dest] = by_destination.get(dest, 0) + 1
    attributed = sum(by_destination.values())
    return {
        "changed": len(changed),
        "attributed": attributed,
        "by_destination": by_destination,
        "sum_check": attributed == len(changed)
                     and by_destination.get("unattributed", 0) == 0,
        "rows": rows,
    }


def cell_partition_view(context: Any) -> Dict[str, Any]:
    """Total, class-attributed cell partition for one frame. Pure, read-only.
    Reads each Slot's `.cells`/`class_id`, the grid from `context.prev_grid`
    (grid total + residual classes), and the per-press delta from
    `context.world_delta` (consumed, never recomputed)."""
    lib = getattr(context, "semantic_library", None)
    grid = getattr(context, "prev_grid", None)
    shape = _grid_shape(grid)
    if lib is None or shape is None:
        return {"status": Excluded("no library or grid at the render seam; "
                                   "partition states its own incompleteness")}
    height, width = shape
    total = height * width
    slots: List[Dict[str, Any]] = []
    covered: set = set()
    sum_slots = 0
    overlap = False
    cell_to_slot: Dict[Tuple[int, int], int] = {}
    for rid in sorted(lib.objects):
        o = lib.objects[rid]
        cells = set(o.cells or ())
        cls = getattr(o, "class_id", None)
        slots.append({
            "region_id": rid,
            "class_id": cls if cls is not None
            else Excluded("excluded — unresolved"),
            "cell_count": len(cells),
        })
        if cells & covered:
            overlap = True
        for cell in cells:
            cell_to_slot.setdefault(cell, rid)
        covered |= cells
        sum_slots += len(cells)
    residual_by_class: Dict[int, int] = {}
    for r in range(height):
        for c in range(width):
            if (r, c) in covered:
                continue
            v = _grid_at(grid, r, c)
            residual_by_class[v] = residual_by_class.get(v, 0) + 1
    sum_residual = sum(residual_by_class.values())
    return {
        "grid_total": total,
        "slots": slots,
        "residual_by_class": residual_by_class,
        "sum_slots": sum_slots,
        "sum_residual": sum_residual,
        "covered": len(covered),
        "overlap": overlap,
        "sum_check": (sum_slots + sum_residual == total) and not overlap,
        "delta": _delta_attribution(context, lib, cell_to_slot),
    }


def render_cell_partition(context: Any) -> str:
    """The cell-partition surface: every Slot + class-attributed residual +
    Σ = grid-total (Part A), then the per-press delta sum-check (Part B).
    Read-only; honest excluded-with-reason where belief is incomplete."""
    v = cell_partition_view(context)
    L: List[str] = ["══ CELL PARTITION  (Slots + class-residual = grid-total) ══"]
    if isinstance(v.get("status"), Excluded):
        L.append(f"  {_NOT_BUILT}: {v['status'].reason}")
        L.append("═" * 60)
        return "\n".join(L)
    L.append(" SLOTS")
    if not v["slots"]:
        L.append(f"   {_NOT_BUILT}: no slots in belief")
    for s in v["slots"]:
        cls = s["class_id"]
        cls_txt = cls.reason if isinstance(cls, Excluded) else f"class {cls}"
        L.append(f"   R{s['region_id']:<3} [{cls_txt}]  {s['cell_count']} cells")
    L.append(" RESIDUAL  (cells in no Slot, by class):")
    if v["residual_by_class"]:
        for cls in sorted(v["residual_by_class"]):
            L.append(f"   class {cls} → {v['residual_by_class'][cls]}")
    else:
        L.append("   (none — every cell individuated)")
    mark = "✓" if v["sum_check"] else "⚠"
    grand = v["sum_slots"] + v["sum_residual"]
    L.append(f" SUM-CHECK  Σ(Slot cells) {v['sum_slots']} + Σ(residual) "
             f"{v['sum_residual']} = {grand}  vs grid-total {v['grid_total']}"
             f"   {mark}")
    if v["overlap"]:
        L.append(f"   ⚠ Slot cell overlap (Σ per-slot {v['sum_slots']} "
                 f"> covered {v['covered']}) — partition not disjoint")
    d = v["delta"]
    L.append(" PER-PRESS DELTA SUM-CHECK  "
             "(consumed read-only from context.world_delta):")
    if isinstance(d, Excluded):
        L.append(f"   {_NOT_BUILT}: {d.reason}")
    else:
        dmark = "✓" if d["sum_check"] else "⚠"
        L.append(f"   changed {d['changed']} cells · attributed "
                 f"{d['attributed']}   {dmark}")
        for dest in sorted(d["by_destination"]):
            L.append(f"      {dest}: {d['by_destination'][dest]}")
    L.append("═" * 60)
    return "\n".join(L)


__all__ = [
    "Excluded",
    "WorldDossier",
    "build_dossier",
    "dossier_to_json",
    "render_overview",
    "render_narrative",
    "load_axiom_key",
    "grade_axioms",
    "render_detail",
    "render_lever_deepening",
    "render_slot_detail",
    "render_axioms_detail",
    "render_role_detail",
    "render_probes_detail",
    "effect_model_view",
    "grade_effect_model",
    "load_effect_model_key",
    "render_effect_grade",
    "cell_partition_view",
    "render_cell_partition",
]
