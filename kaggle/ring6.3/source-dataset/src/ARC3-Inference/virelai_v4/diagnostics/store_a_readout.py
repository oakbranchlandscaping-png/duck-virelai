"""virelai_v4/diagnostics/store_a_readout.py — Store-A (BBA log-score) read-out.

Campaign Dossier Depth · SC1 · WO_STORE_A_OBSERVABILITY.

WO_CAPTAIN_READS_TAPE D1 (PORT-move): the canonical nested taxonomy read
(`read_object_axes`, `implied_role`, `_tag_then_role`, `render_read`,
`animation_annotation`, the constants, and the new `derived_role` accessor) has
been promoted to its library home, `virelai_v4/library/nested_read.py`, so the
dispatch surface can consume the tree without importing `diagnostics/`. This
module re-exports those names unchanged (byte-identical `render_read` output is
a WO fence) and retains the diagnostic-only renders that genuinely belong here:
the per-object Store-A panel, the SC1 Store-A/Store-B divergence table, and the
SC2-REGROUND lever-blindness-cause table.

PURE READ over belief. Store A is the captain's actual decision substrate: the
per-object BBA log-score axes the walk dispatches on. This module writes nothing.

Import sovereignty: stdlib + the `LibraryRole` vocabulary + the shared
thresholds + the library nested-read. No belief-write path imported.
"""

from __future__ import annotations

from typing import Any, Dict, List

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.constants import CONFIRMATION_THRESHOLD
# D1 re-export shim — the derivation now lives in library/nested_read.py.
from virelai_v4.library.nested_read import (  # noqa: F401  (re-export)
    STORE_A_AXES,
    ROLE_MAPPED_AXES,
    CHILD_ROLE_AXES,
    _AXIS_TO_ROLE,
    _VOCAB_MISMATCH_ROLES,
    _NO_EVIDENCE_CEIL,
    read_object_axes,
    implied_role,
    _has_lever_efficacy,
    _is_probe_covered,
    _tag_then_role,
    render_read,
    animation_annotation,
    derived_role,
)


# ---------------------------------------------------------------------------
# Display helpers (pure)
# ---------------------------------------------------------------------------

def _fmt_log_score(v: float) -> str:
    """Render a raw log-score, surfacing the ±inf seal sentinels."""
    if v == float("-inf"):
        return "-inf(falsified)"
    if v == float("inf"):
        return "+inf(sealed)"
    return f"{v:+.2f}"


def _fmt_axis(axis: str, cell: Dict[str, float]) -> str:
    return f"{axis}={cell['sigmoid']:.2f}[{_fmt_log_score(cell['log_score'])}]"


def render_store_a_panel(library: Any) -> str:
    """Per-object Store-A panel: the six axes (sigmoid + raw) and the implied
    role, for every Slot in canonical region order. PURE READ."""
    lines: List[str] = []
    lines.append("########## STORE A — captain's decision substrate (six BBA "
                 "log-score axes; pure read) ##########")
    lines.append("  legend  axis=sigmoid[raw]  ·  implied = argmax over the 5 "
                 "role-mapped axes (gate excluded)")
    objects = getattr(library, "objects", {}) or {}
    if not objects:
        lines.append("  (no objects in library)")
        return "\n".join(lines)
    for rid in sorted(objects.keys()):
        obj = objects[rid]
        axes = read_object_axes(obj)
        role_name, conf = implied_role(obj)
        implied = "—(no evidence)" if role_name is None else f"{role_name} {conf:.2f}"
        flag = ""
        if role_name is not None and conf < CONFIRMATION_THRESHOLD:
            flag = f"  ⚠ below CONFIRMATION_THRESHOLD ({CONFIRMATION_THRESHOLD:.2f})"
        axis_str = "  ".join(_fmt_axis(a, axes[a]) for a in STORE_A_AXES)
        lines.append(f"  R{rid:<3} implied={implied}{flag}")
        lines.append(f"        {axis_str}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# §2 — the divergence table (pure read; Director runs it on the canary)
# ---------------------------------------------------------------------------

def divergence_row(obj: Any) -> Dict[str, Any]:
    """One object's Store-A-implied vs Store-B-categorical comparison.

    classification ∈ {AGREE, DISAGREE, ONE_SIDED_CATEGORICAL, VOCAB_MISMATCH,
    NO_EVIDENCE}:
      - VOCAB_MISMATCH: Store-B role is TARGET/SIGNAL/UNKNOWN — no Store-A axis;
        undefined comparison, never a divergence.
      - ONE_SIDED_CATEGORICAL (WO_CAPTAIN_READS_TAPE D3): Store-B holds one of the
        five axis-backed roles (EGO/LEVER/REACTIVE/COUNTER/STATIC) while Store A
        has NO implied role — the categorical was written without its axis (the
        pre-fix ego, the 370 lever). This was previously buried as NO_EVIDENCE;
        it is now a named fence. The vocabulary residue (TARGET/SIGNAL/UNKNOWN,
        and INERT which is never a Store-B value) is excluded above, so this
        verdict fires ONLY on a genuine one-sided write, never on a
        structurally-axisless role.
      - NO_EVIDENCE: Store A has no implied role AND Store-B is UNKNOWN-adjacent
        (no axis-backed categorical to be one-sided about) — a genuinely early
        object.
      - AGREE / DISAGREE: over the shared 5-role vocabulary only.
    low_confidence flags an implied role whose confidence is below
    CONFIRMATION_THRESHOLD — a weak argmax, not a confident disagreement.
    PURE READ.
    """
    store_b_role: LibraryRole = obj.role
    a_role, a_conf = implied_role(obj)
    low_conf = a_role is not None and a_conf < CONFIRMATION_THRESHOLD

    if store_b_role in _VOCAB_MISMATCH_ROLES:
        classification = "VOCAB_MISMATCH"
    elif a_role is None:
        # Store A holds no implied role. If Store-B nonetheless asserts one of the
        # three CHILD roles (EGO/LEVER/COUNTER — the roles implied_role can
        # produce, and exactly where the census found one-sided writers), that is
        # a one-sided categorical (the burial the census named). STATIC/REACTIVE
        # are the Band-1 tag split (excluded — implied_role never returns them, so
        # they would false-positive); a genuinely-early object stays NO_EVIDENCE.
        if store_b_role.value in _CHILD_ROLE_VALUES:
            classification = "ONE_SIDED_CATEGORICAL"
        else:
            classification = "NO_EVIDENCE"
    elif a_role == store_b_role.value:
        classification = "AGREE"
    else:
        classification = "DISAGREE"

    return {
        "region_id": obj.region_id,
        "store_a_implied": a_role,
        "store_a_confidence": a_conf,
        "store_b_role": store_b_role.value,
        "sub_role": getattr(obj, "sub_role", ""),
        "classification": classification,
        "low_confidence": low_conf,
    }


# The three CHILD role NAMES (EGO/LEVER/COUNTER) — the roles implied_role can
# return, and exactly the roles a one-sided write can strand (categorical set,
# child axis empty). Derived from CHILD_ROLE_AXES so it never drifts. STATIC and
# REACTIVE (the Band-1 tag axes) are deliberately absent: implied_role excludes
# them, so including them would false-positive on every settled tag.
_CHILD_ROLE_VALUES = frozenset(_AXIS_TO_ROLE[a].value for a in CHILD_ROLE_AXES)


def divergence_rows(library: Any) -> List[Dict[str, Any]]:
    """The per-object divergence rows in canonical region order. PURE READ."""
    objects = getattr(library, "objects", {}) or {}
    return [divergence_row(objects[rid]) for rid in sorted(objects.keys())]


def render_divergence_table(library: Any) -> str:
    """The SC1 gate's empirical payload: per-object Store-A-vs-Store-B agree /
    disagree / one-sided / vocab-mismatch table, with a summary and the baked-in
    caveats. PURE READ — the captain's brain measured against the instrument's
    brain."""
    rows = divergence_rows(library)
    lines: List[str] = []
    lines.append("########## STORE-A vs STORE-B DIVERGENCE (SC1 gate; pure "
                 "read) ##########")
    lines.append("  rid  | store_A implied (conf) | store_B role | sub_role | "
                 "verdict")
    counts = {"AGREE": 0, "DISAGREE": 0, "ONE_SIDED_CATEGORICAL": 0,
              "VOCAB_MISMATCH": 0, "NO_EVIDENCE": 0}
    low_conf_n = 0
    for r in rows:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
        if r["low_confidence"]:
            low_conf_n += 1
        a = "—" if r["store_a_implied"] is None else r["store_a_implied"]
        lc = " ⚠low" if r["low_confidence"] else ""
        lines.append(
            f"  R{r['region_id']:<3} | {a:<14} {r['store_a_confidence']:.2f}{lc:<5}"
            f" | {r['store_b_role']:<12} | {r['sub_role'] or '-':<8} | "
            f"{r['classification']}"
        )
    total = len(rows)
    shared = counts["AGREE"] + counts["DISAGREE"]
    rate = (counts["DISAGREE"] / shared) if shared else 0.0
    lines.append("  " + "-" * 60)
    lines.append(
        f"  {total} objects · AGREE {counts['AGREE']} · DISAGREE "
        f"{counts['DISAGREE']} · ONE_SIDED_CATEGORICAL "
        f"{counts['ONE_SIDED_CATEGORICAL']} · VOCAB_MISMATCH "
        f"{counts['VOCAB_MISMATCH']} · NO_EVIDENCE {counts['NO_EVIDENCE']}"
    )
    lines.append(
        f"  divergence rate (over shared 5-role vocab) = {rate:.2f} "
        f"({counts['DISAGREE']}/{shared}) · low-confidence implied roles "
        f"= {low_conf_n}"
    )
    lines.append("  caveat: VOCAB_MISMATCH (Store-B TARGET/SIGNAL/UNKNOWN) has "
                 "no Store-A axis — not a divergence.")
    lines.append("  caveat: ONE_SIDED_CATEGORICAL = Store-B asserts an "
                 "axis-backed role Store-A does not hold (categorical written "
                 "without its axis) — the fence for the census's live risk.")
    lines.append("  caveat: Store-A implied = argmax; Store-B crossed a ratchet "
                 "threshold. ⚠low rows are weak argmax, not confident "
                 "disagreement.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# SC2-REGROUND — per-lever blindness-cause discriminator (pure read)
# ---------------------------------------------------------------------------
# Distinguishes a REVOKED lever (Store-A evidence written at lock, then zeroed
# by the class-change revoke) from a NEVER-LOCKED one, using only persistent
# fields readable at end-of-run. The discriminator is sound by grounding:
#   - lever_locked=True has exactly one writer (probe_outcome_processor.py:153),
#     and that writer co-accumulates LEVER 0.7 in the SAME branch (:190) — so a
#     locked lever necessarily HAD Store-A lever evidence.
#   - lever_log_score is zeroed by exactly one site (library_sync.py:191, the
#     class-change revoke). The accumulator only ADDS, and the lever axis has no
#     disconfirm path, so it never self-cancels to exactly 0.0; level_advance
#     CARRIES it (substrate/level_advance.py:116), never resets it.
# Therefore  lever_locked=True ∧ lever_log_score == 0.0  ⟹  revoke fired after
# the lock — the lock∧zero signature is the readable proof.

def lever_cause_row(obj):
    """Per-object lever-blindness cause discriminator. PURE READ."""
    locked = bool(getattr(obj, "lever_locked", False))
    raw = getattr(obj, "lever_log_score", 0.0)
    role_obj = getattr(obj, "role", None)
    role = role_obj.value if hasattr(role_obj, "value") else str(role_obj)
    if locked and raw == 0.0:
        verdict = "REVOKE_CONFIRMED"
    elif locked:
        verdict = "HEALTHY_EVIDENCE"
    else:
        verdict = "NEVER_LOCKED"
    return {
        "region_id": obj.region_id,
        "role": role,
        "lever_locked": locked,
        "lever_log_score": raw,
        "prev_class_sig": getattr(obj, "previous_class_signature", None),
        "verdict": verdict,
    }


def lever_cause_rows(library):
    """Per-object lever-cause rows in canonical region order. PURE READ."""
    objects = getattr(library, "objects", {}) or {}
    return [lever_cause_row(objects[rid]) for rid in sorted(objects.keys())]


def render_lever_cause_table(library) -> str:
    """SC2-REGROUND confirmation table: for each Store-B LEVER (or locked)
    object, the revoke-vs-never-written verdict from end-state fields. PURE
    READ — confirms or kills the revoke hypothesis per-object."""
    rows = [r for r in lever_cause_rows(library)
            if r["lever_locked"] or r["role"] == "LEVER"]
    lines = []
    lines.append("########## LEVER BLINDNESS CAUSE (SC2-REGROUND; pure read) "
                 "##########")
    lines.append("  rid | role | locked | lever_log_score | prev_class_sig | "
                 "verdict")
    counts = {}
    for r in rows:
        counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        lines.append(
            f"  R{r['region_id']:<3} | {r['role']:<8} | "
            f"{str(r['lever_locked']):<5} | {r['lever_log_score']:+.3f} | "
            f"{str(r['prev_class_sig']):<8} | {r['verdict']}"
        )
    if not rows:
        lines.append("  (no Store-B LEVER or locked objects)")
    lines.append("  " + "-" * 58)
    rc = counts.get("REVOKE_CONFIRMED", 0)
    nl = counts.get("NEVER_LOCKED", 0)
    he = counts.get("HEALTHY_EVIDENCE", 0)
    lines.append(f"  REVOKE_CONFIRMED {rc} · NEVER_LOCKED {nl} · "
                 f"HEALTHY_EVIDENCE {he}")
    lines.append("  read: REVOKE_CONFIRMED = locked (evidence written, "
                 "probe_outcome_processor:190) but lever_log_score zeroed "
                 "(library_sync:191 revoke) — hypothesis holds.")
    lines.append("  read: NEVER_LOCKED = role=LEVER without a CLICK lock — "
                 "evidence path is elsewhere; revoke hypothesis does NOT "
                 "explain that row.")
    return "\n".join(lines)


__all__ = [
    "STORE_A_AXES",
    "ROLE_MAPPED_AXES",
    "CHILD_ROLE_AXES",
    "read_object_axes",
    "implied_role",
    "_tag_then_role",
    "render_read",
    "animation_annotation",
    "derived_role",
    "render_store_a_panel",
    "divergence_row",
    "divergence_rows",
    "render_divergence_table",
    "lever_cause_row",
    "lever_cause_rows",
    "render_lever_cause_table",
    "weave_divergence_row",
    "weave_divergence_rows",
    "render_weave_a_divergence",
]


# ---------------------------------------------------------------------------
# WO-R1-01b Part 3 · the weave↔A divergence map — R1's deliverable.
#
# Mirrors the Store-A-vs-Store-B table above on a NEW AXIS: the weave's
# RoleVerdict vs Store-A's nested read, keyed by region_id, same verdict
# vocabulary. Build the axis, reuse the table (BUILD_LADDER_v2 §5).
#
# BAND-AWARE BY CONSTRUCTION (the WO-R1-01b-P4READ lesson): the weave's role
# vocabulary spans BOTH bands, and comparing across bands is exactly the error
# that would have pinned the REACTIVE gates RED. So:
#   · weave EGO/LEVER/COUNTER  → compared against Store-A's Band-2 role;
#   · weave STATIC/REACTIVE    → compared against Store-A's Band-1 tag
#     ("reactive-as-a-role dissolves into the tag" — nested_read);
#   · weave DEPENDENT/UNKNOWN  → VOCAB_MISMATCH (no Store-A equivalent; these
#     are the roles the sink contract skips).
# A region with no weave row is NO_WEAVE — honest coverage (an unbound mover, a
# mid-run birth), never a failure.
#
# PURE READ. Writes nothing. The pacing instrument, not a producer.
# ---------------------------------------------------------------------------

_WEAVE_BAND2_ROLES = frozenset({"EGO", "LEVER", "COUNTER"})
_WEAVE_BAND1_ROLES = frozenset({"STATIC", "REACTIVE"})


def weave_divergence_row(obj: Any, weave_role: Any) -> Dict[str, Any]:
    """One weave-vs-Store-A row for a region. PURE READ."""
    tag, role, _loc = _tag_then_role(obj)
    if weave_role is None:
        a_read, band, classification = None, "—", "NO_WEAVE"
    elif weave_role in _WEAVE_BAND2_ROLES:
        a_read, band = role, "B2"
        classification = ("NO_EVIDENCE" if a_read is None
                          else "AGREE" if a_read == weave_role else "DISAGREE")
    elif weave_role in _WEAVE_BAND1_ROLES:
        a_read, band = tag, "B1"
        classification = ("NO_EVIDENCE" if a_read is None
                          else "AGREE" if a_read == weave_role else "DISAGREE")
    else:
        a_read, band, classification = None, "—", "VOCAB_MISMATCH"
    return {
        "region_id": obj.region_id,
        "band": band,
        "store_a_read": a_read,
        "weave_role": weave_role,
        "classification": classification,
    }


def weave_divergence_rows(library: Any,
                          weave_roles_by_region: Dict[int, str]) -> List[Dict[str, Any]]:
    """Per-object weave↔A rows in canonical region order. ``weave_roles_by_region``
    is ``{region_id: weave_role_name}`` (see
    ``library.weave_role_landing.weave_roles_by_region``); a region absent from it
    has no bound weave verdict → NO_WEAVE. PURE READ."""
    objects = getattr(library, "objects", {}) or {}
    return [weave_divergence_row(objects[rid], weave_roles_by_region.get(rid))
            for rid in sorted(objects.keys())]


def render_weave_a_divergence(library: Any,
                              weave_roles_by_region: Dict[int, str],
                              bind_rate: Any = None,
                              region_verdicts: Any = None) -> str:
    """The weave↔A divergence table — R1's pacing instrument. Shows, per region,
    what the weave says vs what Store-A believes.

    ``bind_rate`` (WO-R1-02c C5): the TRUE ``(bound, total)`` worldline bind-rate
    from ``BindReport``. Region-coverage answers a different question and reads as
    though binding were perfect while most worldlines may legitimately be unbound;
    both are now reported, and labelled as the different things they are.
    ``region_verdicts`` (``{rid: (role, …)}``): every verdict a region collected,
    so collisions are counted and agreement/conflict flagged — never last-wins.
    PURE READ."""
    rows = weave_divergence_rows(library, weave_roles_by_region)
    lines: List[str] = []
    lines.append("########## WEAVE vs STORE-A DIVERGENCE (R1 map; pure read) "
                 "##########")
    lines.append("  rid  | band | store_A read | weave role   | n | verdict")
    counts = {"AGREE": 0, "DISAGREE": 0, "VOCAB_MISMATCH": 0,
              "NO_EVIDENCE": 0, "NO_WEAVE": 0}
    conflicts = 0
    for r in rows:
        counts[r["classification"]] = counts.get(r["classification"], 0) + 1
        a = "—" if r["store_a_read"] is None else str(r["store_a_read"])
        w = "—" if r["weave_role"] is None else str(r["weave_role"])
        seen = (region_verdicts or {}).get(r["region_id"], ())
        n = len(seen)
        conflict = n > 1 and len(set(seen)) > 1
        if conflict:
            conflicts += 1
        n_txt = f"{n}{'!' if conflict else ''}" if n else "—"
        lines.append(f"  R{r['region_id']:<3} | {r['band']:<4} | {a:<12} "
                     f"| {w:<12} | {n_txt:<3}| {r['classification']}")
    covered = len(rows) - counts["NO_WEAVE"]
    lines.append("   ── summary ──")
    if bind_rate is not None:
        bound, total = bind_rate
        pct = (100.0 * bound / total) if total else 0.0
        lines.append(f"   bind-rate  {bound}/{total} worldlines bound to a spawn "
                     f"slot ({pct:.0f}%) — unbound = never a spawn object "
                     f"(mid-run birth/transient), honest")
    lines.append(f"   coverage   {covered}/{len(rows)} regions carry a bound weave "
                 f"verdict ({counts['NO_WEAVE']} NO_WEAVE) — a DIFFERENT number "
                 f"from bind-rate: regions, not worldlines")
    lines.append(f"   collisions {conflicts} region(s) hold conflicting verdicts "
                 f"(n! above); many-worldlines-per-slot is normal (re-births share "
                 f"a spawn footprint), disagreement is the signal")
    lines.append(f"   agreement  AGREE {counts['AGREE']} · DISAGREE "
                 f"{counts['DISAGREE']} · NO_EVIDENCE {counts['NO_EVIDENCE']} · "
                 f"VOCAB_MISMATCH {counts['VOCAB_MISMATCH']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# WO-B2-01 · LIB-5 — THE KEYSPACE DIVERGENCE MAP (the re-plumb's pacing instrument)
# ---------------------------------------------------------------------------
#
# Built FIRST, before the key moves, so every later move is measured against it.
# It joins the weave's worldlines to the roster's slots by first_region
# fingerprint — the SAME `(class_id, frozenset(cells))` equality the bridge
# (worldline_binding.py) uses — and renders three disagreement classes:
#
#   UNBOUND-WORLDLINE   — a worldline whose first_region matched no slot.
#                         EXPECTED non-zero: mid-run births / transients are
#                         legitimately unbound (the bridge docstring's "honest").
#                         Informational count, not a failure.
#   WORLDLESS-SLOT      — a roster slot no worldline bound to. EXPECTED non-zero:
#                         a never-changing object may never spawn a ###.
#                         Informational count.
#   FINGERPRINT-MISMATCH — THE PACING INVARIANT. A worldline whose first_region
#                         shares a slot's class_id but whose full fingerprint is
#                         NOT a slot key — the same-class-different-cells signature
#                         of a keyspace that has DRIFTED. By construction this is
#                         empty at fe76efc (the join is exact fingerprint equality
#                         over spawn geometry). It MUST stay empty across Move 2
#                         (the key) and Move 3 (cells=current) — the latter is
#                         exactly where a naive `slot_fps` over CURRENT cells would
#                         break the spawn-fingerprint join. That is what spawn_cells
#                         (Move 3) preserves, and this class is how we would see it
#                         fail. "EMPTY" (clean) == FINGERPRINT-MISMATCH empty.


def keyspace_divergence(
    worldline_fps: "Dict[int, Any]",
    slot_fps: "Dict[Any, Any]",
    bindings: "Dict[int, Any]",
) -> "Dict[str, list]":
    """Pure classifier. Inputs are the join's raw material:
      worldline_fps : {worldline_id -> (class_id, frozenset(cells))}  (first_region)
      slot_fps      : {(class_id, frozenset(cells)) -> slot_key}       (the roster)
      bindings      : {worldline_id -> slot_key}                       (BindReport)
    Returns {UNBOUND_WORLDLINE, WORLDLESS_SLOT, FINGERPRINT_MISMATCH} lists.
    Key-agnostic: slot_key is region_id today, worldline_id after Move 2 — the
    classification is identical either way (the whole point of the instrument)."""
    slot_classes: "Dict[Any, list]" = {}
    for (cls, cells), skey in slot_fps.items():
        slot_classes.setdefault(cls, []).append((cells, skey))

    unbound = []
    mismatch = []
    for wid, fp in worldline_fps.items():
        if wid in bindings:
            continue
        cls, cells = fp
        # a slot of the same class exists but this fingerprint didn't join ->
        # same-class-different-cells: the keyspace-drift signature (the invariant)
        if cls in slot_classes and (cls, cells) not in slot_fps:
            mismatch.append((wid, cls))
        else:
            unbound.append((wid, cls))

    bound_slots = set(bindings.values())
    worldless = [skey for skey in slot_fps.values() if skey not in bound_slots]

    return {
        "UNBOUND_WORLDLINE": unbound,
        "WORLDLESS_SLOT": worldless,
        "FINGERPRINT_MISMATCH": mismatch,
    }


def render_keyspace_divergence(
    worldline_fps: "Dict[int, Any]",
    slot_fps: "Dict[Any, Any]",
    bindings: "Dict[int, Any]",
) -> str:
    """The LIB-5 render. EMPTY (clean) when FINGERPRINT-MISMATCH is empty — the
    keyspaces agree on every shared fingerprint. Unbound worldlines and worldless
    slots are reported as informational counts (births/statics are legitimate)."""
    d = keyspace_divergence(worldline_fps, slot_fps, bindings)
    mism = d["FINGERPRINT_MISMATCH"]
    lines = ["########## KEYSPACE DIVERGENCE (LIB-5; weave↔roster join; pure "
             "read) ##########"]
    if not mism:
        lines.append("  EMPTY — every shared fingerprint joined; keyspaces agree.")
    else:
        lines.append("  FINGERPRINT-MISMATCH (keyspace drift — the invariant broke):")
        for wid, cls in mism:
            lines.append(f"    worldline {wid} class {cls}: same-class slot exists, "
                         f"fingerprint did not join")
    lines.append(
        f"   ── summary ── mismatch {len(mism)} (MUST be 0) · "
        f"unbound-worldline {len(d['UNBOUND_WORLDLINE'])} (births/transients, ok) · "
        f"worldless-slot {len(d['WORLDLESS_SLOT'])} (never-changed objects, ok)"
    )
    return "\n".join(lines)


def unbound_reason_line(worldlines, slot_fps, life) -> str:
    """WO-B3-01 STAGE A · the loud per-life accounting of WHY the spawn-geometry
    bind left verdicts unbound — the split the Stage-B worldline rebind is graded
    against. Reuses the LIB-5 keyspace classifier (no parallel taxonomy):

      * MISMATCH — a same-class slot exists but the worldline's ``first_region``
        cells drifted (the object moved / grew / shrank), so the exact-fingerprint
        join missed it. A worldline-identity bind WOULD recover this one.
      * BIRTH — no slot of the worldline's class exists at all: an honest mid-run
        birth / transient, unrecoverable by any rebinding.

    The WO's ``NO_WORLDLINE_THREADED`` reason is structurally unreachable at the
    landing — every verdict's worldline is threaded and present (WO-B3-01-PRE
    B1/B3) — so it never emits (reported, not faked; cf. WO-B3-00's skipped_conf).

    PURE READ (WO-B3-01 §1 — Stage A instruments only): binds read-only and
    classifies; writes no belief and changes no bind logic. The Stage-B rebind is
    what acts on this measurement, not this line."""
    from virelai_v4.weave.worldline_binding import bind_worldlines_to_slots
    wls = list(worldlines)
    worldline_fps = {
        w.id: (w.first_region.class_id, w.first_region.cells) for w in wls
    }
    bindings = bind_worldlines_to_slots(wls, slot_fps).bindings
    d = keyspace_divergence(worldline_fps, slot_fps, bindings)
    mismatch = d["FINGERPRINT_MISMATCH"]   # same-class, cells drifted → recoverable
    birth = d["UNBOUND_WORLDLINE"]         # no same-class slot → honest
    tags = ([f"###{wid:03d}:MISMATCH" for wid, _cls in mismatch]
            + [f"###{wid:03d}:BIRTH" for wid, _cls in birth])
    return (
        f"WEAVE-LAND-UNBOUND | life={life} "
        f"unbound={len(mismatch) + len(birth)} "
        f"mismatch={len(mismatch)} (same-class cells drifted; worldline-bind recoverable) "
        f"birth={len(birth)} (no same-class slot; honest) "
        f"| {' '.join(tags) if tags else '(none)'}"
    )
