"""WO-R1-01b Part 1 · the weave→belief sink contract and the role landing.

R1's accumulator confluence: the weave's ``RoleVerdict``s land in Store-A through
``accumulate_role_evidence`` — a second WITNESS, not a second writer; the
accumulator keeps sole ownership of the axis write (``BUILD_LADDER_v2`` §4.1).
No direct field-write happens here or anywhere downstream of here.

CADENCE IS THE CALLER'S (``NOTE_WEAVE_SEQUENCING_ENDPOINT`` §4 — binding):
``land_weave_roles`` is a pure function over
``(verdicts, worldlines, slot_fingerprints, library)``. R1 calls it ONCE PER LIFE
at the end-of-life boundary (cadence D). Step 2's incremental every-move engine
will call this SAME function per-move, UNCHANGED, by swapping the caller only.
Nothing in this module makes end-of-loop load-bearing — end-of-loop is a cadence
choice, not an architecture. Record-first is Step 1 of three, never a
destination.

THE EXPLICIT SINK CONTRACT (``WO-R1-00`` L2; ``BUILD_LADDER_v2`` §8 RULED-IN).
The weave emits role names as plain ``str``. ``LibraryRole`` subclasses ``str``,
so a bare weave string would resolve against the accumulator's axis map BY
ACCIDENT — and would silently stop resolving if the enum ever stopped
subclassing ``str``. So the mapping is explicit, by name, in a literal map:
  * the five core roles (EGO / LEVER / REACTIVE / COUNTER / STATIC) → their
    ``LibraryRole`` members;
  * ``DEPENDENT`` → skipped-with-log. It is the weave's derived complement,
    consciously ignored (``weave/role_read.py``); it has no ``LibraryRole``, so
    ``LibraryRole("DEPENDENT")`` raises ``ValueError`` — the latent bug at
    ``render_stages.py:394``. Skipping it explicitly is the fix.
  * ``UNKNOWN`` / anything unrecognized → skipped (insufficient evidence).

CONFIDENCE — THE VOLUME DIAL (ruled: R1 whispers). ``RoleVerdict.confidence`` is
a STRING (``FIRM`` / ``PROVISIONAL`` / ``OUT_OF_INPUT``); the accumulator takes a
float where 0.5 is exactly "no evidence" (delta 0). Landed evidence enters the
log-score axes — which is what ``derived_role`` and the captain read — so the
volume decides whether the weave merely *speaks* or actually *drives*.

At R1 the weave is a **quiet witness**: heard, recorded, visible on the map, and
combined into the axes — but deliberately NOT loud enough to override Store-A's
committed evidence before the divergence map has proven the weave right for that
role. Landing loud would be a Step-3 promotion through the back door, which
``NOTE_WEAVE_SEQUENCING_ENDPOINT`` §3 explicitly sequences behind the map.
  * ``FIRM`` → 0.60 — real evidence, clearly above the 0.5 neutral, well below
    the 0.90 a committed classifier verdict carries (``classification_pass``'s
    EGO) and the 1.0 ``cycle_probe`` reserves for direct probe confirmation.
  * ``PROVISIONAL`` → 0.55 — barely above neutral: a murmur.
  * ``OUT_OF_INPUT`` → skipped (the weave saw no input; not evidence).

**VOLUME IS THE PROMOTION DIAL (Step 3's mechanism).** When the weave↔A map
proves the weave is a true superset for a role, that role's volume goes up — that
IS the promotion. No separate switch. R1 whispers; Step 3 decides who gets loud.
The map is unaffected by volume: it renders pre-landing off ``RoleVerdict``
directly, so visibility never depends on how loud the weave speaks.

The exact numbers are a judgment, not a read (flagged): if the canary shows the
weave landing invisibly (no axis movement at all) or still flipping belief, tune
them. Better too quiet than front-running the map.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional, Tuple

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
from virelai_v4.weave.worldline_binding import bind_worldlines_to_slots

# --- the explicit contract (never the str-Enum accident) ----------------------

_WEAVE_ROLE_TO_LIBRARY_ROLE: Dict[str, LibraryRole] = {
    "EGO":      LibraryRole.EGO,
    "LEVER":    LibraryRole.LEVER,
    "REACTIVE": LibraryRole.REACTIVE,
    "COUNTER":  LibraryRole.COUNTER,
    "STATIC":   LibraryRole.STATIC,
}

# WO-STATIC-VACATION-01 · THE BRIDGE NOW READS TWO FIELDS.
#
# Apex ruled this module Tier 2 — a sanctioned crossing built to carry GOLDEN output into
# Store-A — not legacy proper, and therefore the golden run's to maintain. The ruling that
# follows from it: `"STATIC" -> LibraryRole.STATIC` was the same band confusion one layer
# down. `STATIC` is SELF-STATE (Band 1), not a role, and reading it out of the Band-2 slot
# meant the axis was fed by whichever band happened to hold the word.
#
# So Band 1 is read for the Band-1 fact, and Band 2 keeps its archetypes.
#
# WHAT THIS DOES NOT MAKE TRUE, and the next chamber will assume otherwise unless it is
# said here: the counts matching is NOT a proof of equivalence. `static_log_score` was
# built to accumulate a ROLE claim gated on interaction (`wl_clicks and not churned`);
# Band 1 is an OBSERVATION over the worldline's whole settled record, computed for every
# worldline whether touched or not. On the live canary the two happen to select the same
# 56 worldlines, so the landing count is unchanged — but **feeding an observation into an
# axis built for a gated role claim changes what the number means even where the counts
# match.** Store-A has no Band-1 axis; `LibraryRole.STATIC` remains a Band-2-shaped home
# for a Band-1 fact. That mismatch dies when the weave gets its own belief home, not here.
#
# REACTIVE IS DELIBERATELY NOT REPOINTED. Measured, not feared: Band-1 REACTIVE fires on
# every changing worldline, which on the live canary adds 10 `reactive_log_score` landings
# to exactly the ten that are COUNTER and LEVER. That saturates `reactive` beside an
# already-saturated `counter`, and `store_a_role_read`'s `_AXES` order plus a strict `>`
# hands the tie to `reactive` — flipping the roster line COUNTER → REACTIVE.
# `WO_STATIC_VACATION_01_RETURN_v1` carries the measurement.
_WEAVE_BAND1_TO_LIBRARY_ROLE: Dict[str, LibraryRole] = {
    "STATIC": LibraryRole.STATIC,
}

# Skipped by contract, never fed: REACTIVE-DRIVEN (the weave's derived complement — no
# LibraryRole exists; LibraryRole("REACTIVE-DRIVEN") would raise) and a `None` Band 2
# (WO-BAND-SPLIT-01 R-4 retired UNKNOWN as a role; ∅ is the honest absence of one, and an
# absence is not evidence). "UNKNOWN" and "DEPENDENT" are retained ONLY as historical
# names: `role_read` no longer emits either, but a verdict deserialized from an older
# record still might, and naming them keeps such a skip CONTRACTED rather than
# UNRECOGNIZED — the distinction the skip-with-log payload exists to report.
_SKIPPED_ROLE_NAMES = frozenset({"REACTIVE-DRIVEN", "DEPENDENT", "UNKNOWN", "∅"})

# The volume dial — R1 whispers (ruled). Raising a role's volume here is how
# Step 3 promotes it from recording to driving, once the map has earned it.
_WEAVE_CONFIDENCE_TO_FLOAT: Dict[str, float] = {
    "FIRM":        0.60,
    "PROVISIONAL": 0.55,
    # OUT_OF_INPUT: absent by design → skipped.
}


def to_library_role(role_name: Any) -> Optional[LibraryRole]:
    """The explicit weave-role-name → ``LibraryRole`` conversion. Returns None for
    DEPENDENT / UNKNOWN / anything unrecognized — the caller skips those. Never
    raises (unlike ``LibraryRole(role_name)``)."""
    return _WEAVE_ROLE_TO_LIBRARY_ROLE.get(role_name)


def to_library_band1(band1_name: Any) -> Optional[LibraryRole]:
    """The explicit weave-BAND-1-name → ``LibraryRole`` conversion (WO-STATIC-VACATION-01).

    Returns ``None`` for an empty band (``library/store_a_role_read.py`` constructs
    ``RoleVerdict`` without one, so its verdicts carry ``""``), for ``REACTIVE`` — which is
    NOT repointed, see the block above — and for anything unrecognized. Never raises, the
    same contract ``to_library_role`` holds."""
    return _WEAVE_BAND1_TO_LIBRARY_ROLE.get(band1_name)


def to_confidence(confidence_name: Any) -> Optional[float]:
    """The explicit weave-confidence-name → float conversion. Returns None for
    OUT_OF_INPUT / anything unrecognized — the caller skips those."""
    return _WEAVE_CONFIDENCE_TO_FLOAT.get(confidence_name)


@dataclass(frozen=True)
class LandReport:
    """What the landing did — the honest per-call accounting, and the raw
    material of the weave↔A divergence map."""

    total: int                     # verdicts seen
    landed: int                    # fed to the accumulator
    skipped_unbound: int           # no spawn slot for the worldline (honest)
    skipped_role: int              # DEPENDENT / UNKNOWN / unrecognized role
    skipped_confidence: int        # OUT_OF_INPUT / unrecognized confidence
    # (region_id, role_name, confidence) per landed verdict — for the map.
    landed_detail: Tuple[Tuple[int, str, float], ...] = ()
    # role names skipped by contract — the "skip-with-log" payload.
    skipped_role_names: Tuple[str, ...] = ()


def weave_roles_by_region(
    verdicts: Dict[int, Any],
    worldlines: Iterable[Any],
    slot_fingerprints: Dict[Tuple[int, "frozenset"], int],
) -> Dict[int, str]:
    """``{region_id: weave_role_name}`` for every BOUND verdict — the weave's read
    keyed the way Store-A is keyed. PURE: binds and projects; writes nothing.

    Kept for the simple projection; the map should prefer
    ``weave_region_verdicts`` (below), which does not silently discard the extra
    verdicts a region collects."""
    out: Dict[int, str] = {}
    for rid, roles in weave_region_verdicts(
            verdicts, worldlines, slot_fingerprints).items():
        out[rid] = roles[0]
    return out


def weave_region_verdicts(
    verdicts: Dict[int, Any],
    worldlines: Iterable[Any],
    slot_fingerprints: Dict[Tuple[int, "frozenset"], int],
) -> Dict[int, Tuple[str, ...]]:
    """WO-R1-02c C5 — ``{region_id: (role, role, …)}``: EVERY bound verdict a region
    collects, not one silently-chosen winner.

    Many-worldlines-to-one-spawn-slot is the NORMAL case, not an error: a region
    re-born each life shares its spawn footprint, so several worldlines legitimately
    bind to it. The previous ``out[rid] = role`` last-wins projection discarded
    those without counting them — an instrument that drops evidence silently is not
    honest. Here they are all kept, in verdict order, so the map can report
    agreement (all roles equal) versus conflict (they disagree). PURE READ."""
    bindings = bind_worldlines_to_slots(worldlines, slot_fingerprints).bindings
    out: Dict[int, list] = {}
    for wid, verdict in verdicts.items():
        rid = bindings.get(wid)
        if rid is not None:
            out.setdefault(rid, []).append(verdict.role)
    return {rid: tuple(roles) for rid, roles in out.items()}


def weave_bind_rate(
    worldlines: Iterable[Any],
    slot_fingerprints: Dict[Tuple[int, "frozenset"], int],
) -> Tuple[int, int]:
    """WO-R1-02c C5 — the TRUE bind-rate as ``(bound, total)`` worldlines.

    The number the map must show. Region-coverage answers a different question
    ("does every slot have an opinion?") and reads as though binding were perfect
    while most worldlines may be unbound — most worldlines are never spawn objects
    (mid-run births, transients), which is honest, but it must be visible."""
    r = bind_worldlines_to_slots(worldlines, slot_fingerprints)
    return r.bound, r.total


def land_weave_roles(
    verdicts: Dict[int, Any],
    worldlines: Iterable[Any],
    slot_fingerprints: Dict[Tuple[int, "frozenset"], int],
    library: Any,
) -> LandReport:
    """Land the weave's role verdicts in Store-A through the accumulator.

    CADENCE-AGNOSTIC: the caller decides when this runs (once per life at R1;
    per-move once the incremental engine lands at Step 2). Pass whatever verdict
    set you have.

    For each verdict: resolve ``worldline_id → region_id`` via the R1-01a spawn
    binding; convert the role and confidence through the explicit contract; feed
    ``accumulate_role_evidence(slot, LibraryRole, float)``. Unbound worldlines,
    contract-skipped roles (DEPENDENT/UNKNOWN) and non-evidence confidences
    (OUT_OF_INPUT) are counted and skipped — never force-matched, never coerced.

    The accumulator owns the write; this function performs no field-write.
    """
    bindings = bind_worldlines_to_slots(worldlines, slot_fingerprints).bindings
    objects = getattr(library, "objects", {}) or {}

    landed = skipped_unbound = skipped_role = skipped_confidence = 0
    detail: list = []
    skipped_names: list = []
    total = 0

    for wid, verdict in verdicts.items():
        total += 1
        rid = bindings.get(wid)
        if rid is None or rid not in objects:
            skipped_unbound += 1
            continue
        # WO-STATIC-VACATION-01 · two fields, each landing its own band's fact. Band 2
        # first so the accounting below reads exactly as it did before for every archetype;
        # Band 1 second and independently — NOT gated on Band 2 being empty, which would
        # couple the two bands the split exists to separate.
        role = to_library_role(getattr(verdict, "role", None))
        band1_role = to_library_band1(getattr(verdict, "band1", None))
        if role is None and band1_role is None:
            skipped_role += 1
            # A `None` Band 2 is ∅, not a role name — report the symbol rather than the
            # Python repr `"None"`, which said nothing to a reader of the skip payload.
            _raw = getattr(verdict, "role", None)
            skipped_names.append("∅" if _raw is None else str(_raw))
            continue
        conf = to_confidence(getattr(verdict, "confidence", None))
        if conf is None:
            skipped_confidence += 1
            continue
        for _r in (r for r in (role, band1_role) if r is not None):
            accumulate_role_evidence(objects[rid], _r, conf)   # the sole writer
            landed += 1
            detail.append((rid, _r.value, conf))

    return LandReport(
        total=total,
        landed=landed,
        skipped_unbound=skipped_unbound,
        skipped_role=skipped_role,
        skipped_confidence=skipped_confidence,
        landed_detail=tuple(detail),
        skipped_role_names=tuple(skipped_names),
    )
