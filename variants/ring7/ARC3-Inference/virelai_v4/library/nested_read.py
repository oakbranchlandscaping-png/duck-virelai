"""virelai_v4/library/nested_read.py — the canonical nested taxonomy read.

WO_CAPTAIN_READS_TAPE D1 (PORT-move, zero logic change): the derivation that
was born in `diagnostics/store_a_readout.py` is promoted to the library so that
it is a first-class belief read, not a diagnostics-only convenience. Dispatch may
not import `diagnostics/`; after this move it need not — selection consumes the
tree from its library home (`library/nested_read.py`), and every render path
keeps importing the same names via the re-export shim in
`diagnostics/store_a_readout.py`.

PURE READ over object fields — the captain's decision substrate expressed as
(tag · role · locality). Store A is the six per-object BBA log-score axes
(`static / reactive / ego / counter / lever`); this module reads them and the
recorded self-state (`is_active`) and derives the nested foundation read. It
writes nothing — no `_log_score`, no `role`/`sub_role`, no belief-write path.

Import sovereignty: stdlib + the `LibraryRole` vocabulary + the shared
thresholds only. No belief-write path imported; no diagnostics import.

The bodies below are moved verbatim from `store_a_readout.py` at `bac3d88`
(byte-identical `render_read` output is a WO fence). Only the module home and
the added `derived_role` accessor (a thin public alias of the Band-2 role) are
new.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.constants import CONFIRMATION_THRESHOLD

# The five Store-A floor axes, in canonical display order (mirrors
# semantic_library._LOG_SCORE_CATEGORIES; redefined here to avoid importing a
# private name, and asserted equal nowhere — sigmoid_confidence validates each).
# DD gap-5: `gate` retired — it was never an evidence axis (a lever-subtree
# frontier child, not a floor role); the read-out no longer prints its column.
STORE_A_AXES: Tuple[str, ...] = (
    "static", "reactive", "ego", "counter", "lever",
)

# The five axes that map to a LibraryRole (mirrors
# log_score_accumulator._ROLE_TO_AXIS). `gate` is unwired — no role maps to it —
# so it is read and displayed but EXCLUDED from the argmax-implied role.
_AXIS_TO_ROLE: Dict[str, LibraryRole] = {
    "static":   LibraryRole.STATIC,
    "reactive": LibraryRole.REACTIVE,
    "ego":      LibraryRole.EGO,
    "counter":  LibraryRole.COUNTER,
    "lever":    LibraryRole.LEVER,
}
ROLE_MAPPED_AXES: Tuple[str, ...] = tuple(_AXIS_TO_ROLE.keys())

# DD gap-2 — the nested foundation split. `reactive` and `static` are the Band-1
# TAG (self-state, recorded from `is_active`), NOT role children — they dissolve
# into the tag. The axis-backed role CHILDREN are ego / lever / counter. Passive
# (TARGET) and inert (INERT) are DERIVED children (no accumulated axis) — passive
# from `reacts_to`, inert from static-branch coverage. Excluding reactive here is
# the retire of reactive-as-a-role at the derivation (the captain-store read),
# uniformly covering all three self-change verdicts (role_classifier.py:290/341/
# 356) without editing the counter-slice-tangled classifier.
CHILD_ROLE_AXES: Tuple[str, ...] = ("ego", "lever", "counter")

# Store-B roles with no Store-A axis (the accumulator no-ops on them,
# log_score_accumulator.py:108). Divergence is undefined over these — they are
# vocabulary-mismatch, never disagreement.
_VOCAB_MISMATCH_ROLES = frozenset({
    LibraryRole.TARGET, LibraryRole.SIGNAL, LibraryRole.UNKNOWN,
})

# A neutral axis (log_score == 0.0) reads sigmoid 0.5 — no evidence either way.
# An implied role requires at least one axis with positive evidence above this.
_NO_EVIDENCE_CEIL = 0.5


# ---------------------------------------------------------------------------
# Per-object reads (pure)
# ---------------------------------------------------------------------------

def read_object_axes(obj: Any) -> Dict[str, Dict[str, float]]:
    """Read the six Store-A axes for one object.

    Returns, per axis: {"sigmoid": <[0.0, 1.0] read>, "log_score": <raw>}.
    The sigmoid is `obj.sigmoid_confidence(axis)` (clamps to [0.02, 0.98] for
    finite scores; 0.0 for -inf, 1.0 for +inf). The raw exposes the ±inf
    sentinels. PURE — calls only the read accessor and getattr.
    """
    out: Dict[str, Dict[str, float]] = {}
    for axis in STORE_A_AXES:
        out[axis] = {
            "sigmoid": obj.sigmoid_confidence(axis),
            "log_score": getattr(obj, f"{axis}_log_score"),
        }
    return out


def implied_role(obj: Any) -> Tuple[Optional[str], float]:
    """Store-A's argmax-implied role: the role-mapped axis with the most
    evidence, measured in RAW log-score (not the capped sigmoid).

    Returns (role_name, confidence). role_name is None when no role-mapped axis
    carries positive evidence (every axis at or below the neutral raw 0.0 / the
    neutral 0.5 sigmoid) — an early object has no implied role, not a default
    one. `gate` is excluded (it maps to no role). The reported confidence is
    still the [0.0, 1.0] sigmoid read of the winning axis. This is the pure read
    SC2's derivation will become; building it now lets that derivation be
    verified against it.

    SC2b Leg 2 — argmax over RAW log-score, not the clamped sigmoid. Multiple
    axes can saturate the sigmoid cap (_SIGMOID_CAP = 0.98) and tie; a dominant
    axis in raw log-odds (e.g. reactive +1101 vs static +47, both → 0.98) is
    then invisible and the tie mis-breaks to declaration order (R63 read REACTIVE
    in Store B but STATIC by capped argmax). Raw-score argmax breaks the cap-tie
    by true evidence weight. Sealing is preserved: a +inf (sealed) axis is the
    raw maximum (inf > any finite), so it still wins.
    """
    # DD gap-2: argmax over the CHILD role axes only (ego/lever/counter).
    # reactive and static are the Band-1 tag, excluded here — this is the retire
    # of reactive-as-a-role at the derivation. Returns the axis-backed child role;
    # passive/inert (derived children) and the tag are added by _tag_then_role.
    best_axis: Optional[str] = None
    best_raw = float("-inf")
    for axis in CHILD_ROLE_AXES:
        raw = getattr(obj, f"{axis}_log_score")
        if raw > best_raw:
            best_raw, best_axis = raw, axis
    if best_axis is None or best_raw <= 0.0:
        return None, (obj.sigmoid_confidence(best_axis) if best_axis else 0.0)
    return _AXIS_TO_ROLE[best_axis].value, obj.sigmoid_confidence(best_axis)


# ---------------------------------------------------------------------------
# DD gap-2 — the nested foundation read: TAG (recorded) then ROLE (inferred)
# ---------------------------------------------------------------------------

def _has_lever_efficacy(obj: Any) -> bool:
    """True if the object shows any lever efficacy (so it is a lever, not inert)."""
    return (getattr(obj, "lever_log_score", 0.0) > 0.0
            or getattr(obj, "lever_locality", None) is not None
            or bool(getattr(obj, "lever_effects", ())))


def _is_probe_covered(obj: Any) -> bool:
    """Coverage proxy for the inert conjecture (D3 CARRIED FRICTION).

    NESTED_TAXONOMY_SPEC calls inert "held at static's coverage-bounded
    skepticism" but the code defines no "enough coverage to call inert"
    threshold. TODO(threshold): conservative default = probed at least once
    (`probe_count > 0`). The ft09 canary shows over/under-assignment; CE rules
    the real threshold from that evidence. No numeric invented here.
    """
    return getattr(obj, "probe_count", 0) > 0


def _tag_then_role(obj: Any) -> Tuple[str, Optional[str], Optional[str]]:
    """The nested foundation read → (tag, role, locality). PURE READ.

    tag (Band-1, RECORDED): from `is_active` — True→REACTIVE, False→STATIC. The
      ∃-eternal self-state; `reactive`-as-a-role dissolves into it.
    role (Band-2, INFERRED child under the tag):
      - axis-backed: ego / lever / counter (argmax; reactive & static excluded);
      - passive (TARGET): a reactive-branch object DRIVEN by something (`reacts_to`)
        with no axis-backed child — PORT of the existing TARGET role, not a mint;
      - inert (INERT): a static-branch, probe-covered object with no lever efficacy
        and no axis child — the coverage-bounded, re-openable role-null;
      - None: unclassified-pending (evidence not yet decisive).
    locality: LOCAL/REMOTE from `lever_locality` for a lever role (one role, the
      attribute carries local/remote); None otherwise.
    """
    is_active = bool(getattr(obj, "is_active", False))
    tag = LibraryRole.REACTIVE.value if is_active else LibraryRole.STATIC.value

    role, _conf = implied_role(obj)                      # axis-backed child
    locality = (getattr(obj, "lever_locality", None)
                if role == LibraryRole.LEVER.value else None)

    if role is None:
        if is_active and bool(getattr(obj, "reacts_to", ())):
            role = LibraryRole.TARGET.value              # passive: reactive, driven
        elif (not is_active) and _is_probe_covered(obj) and not _has_lever_efficacy(obj):
            role = LibraryRole.INERT.value               # inert: static, covered, no efficacy
    return tag, role, locality


def render_read(obj: Any) -> Tuple[str, Optional[str], Optional[str], str]:
    """DD gap-1 — the SINGLE classification read for every render path.

    Returns (tag, role, locality, confidence_display) off the captain's store
    (the nested derivation), so no render reads `classify_role` / Store-B
    `obj.role` for a label — killing the split brain.

    confidence_display per ruling R1 (no invented numeric):
      - axis-backed role (ego/lever/counter) → the winning-axis sigmoid, formatted;
      - derived child (passive/TARGET, inert/INERT) → "—(derived)";
      - no role → "—".
    """
    tag, role, locality = _tag_then_role(obj)
    axis_role, conf = implied_role(obj)
    if role is None:
        conf_display = "—"
    elif role == axis_role:                              # axis backs this role
        conf_display = f"{conf:.2f}"
    else:                                                # passive / inert — derived
        conf_display = "—(derived)"
    return tag, role, locality, conf_display


def animation_annotation(obj: Any) -> Optional[str]:
    """WO_AR D3 — the derived ANIMATION tag, a SEPARATE annotation read beside
    (never inside) tag·role. PURE READ.

    A settled-static or settled-reactive object can also be animated; this answers
    (1) is it animated? — ``animated ⟺ flash_count > 0`` — and (2) how expressed?
    — kind-level, from the recorded counts (`flash`, ×the flash tally). Derived,
    never stored (same law as roles). Returns ``None`` when unwitnessed so the
    annotation is present only when a flash was actually recorded; it never
    invents a number and never displaces the settled tag·role. Read `is_active`
    nowhere — the animation tag is orthogonal to the Band-1 settled tag.
    """
    flash = int(getattr(obj, "flash_count", 0) or 0)
    if flash <= 0:
        return None
    return f"ANIM(flash×{flash})"


# ---------------------------------------------------------------------------
# Public derived-role accessor (WO_CAPTAIN_READS_TAPE D4 enabler)
# ---------------------------------------------------------------------------

def derived_role(obj: Any) -> Optional[str]:
    """The object's Band-2 inferred role name (or None), off the nested read.

    Thin public alias of `_tag_then_role(obj)[1]` — the single accessor the
    dispatch surface consults instead of Store-B `obj.role`. Returns the string
    role name (e.g. "EGO", "LEVER", "COUNTER", "TARGET", "INERT") or None when
    the evidence is not yet decisive. PURE READ; no side effects.

    This is the belief the captain acts on: a categorical role with no Store-A
    axis backing (a one-sided write) does NOT surface here, so selection stops
    trusting an unbacked commitment — the whole point of the rung.
    """
    return _tag_then_role(obj)[1]


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
]
