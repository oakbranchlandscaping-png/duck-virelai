"""WO-B3-R1a-3 · THE INTEGRATION ROSTER — color-first, full-member dossier.

Renders the integration the weave already computes and this rung retains
(``ctx.woven_worldlines``) at the ONTOLOGY-correct grain: a visual object is a
distinct ``(class, cell-set)`` fingerprint (SPEC_SIGHTING_LEDGER §1, SPEC_WEAVE §1
``≈ ⊇ ~``). A STILL object is ONE visual object with many appearances (a wall is
one visual object all game); an ACTIVE object mints a NEW visual object per delta
(a counter throws off one per tick). The count of distinct visual objects in a
``###`` is its activity signal — static = 1, active = many.

R1a-2 rendered the distinct grain but keyed each object by its raw ``class`` int
(``c9``) and hid the per-``###`` members behind a verbose flag. R1a-3 makes the
dossier readable to the Director: the class int is rendered as its **bold color
name** (the platform's universal 0–15 render palette), each object carries its
NW-most member cell as a location, and every ``###`` lists its full member set of
distinct visual objects — no verbose flag needed to see them.

§8-legal: a read-time view over the already-retained members (reusing the committed
collapse core ``capture/clay.collapse_fingerprints`` over each ``Worldline.steps``),
never a second stored accumulator. Pure read over ``Worldline`` (``id`` + ``steps``).
Writes nothing, lands no role (R1b).

THE COLOR PALETTE — sourced, not invented. The 16 names below mirror the platform's
authoritative render map ``COLOR_MAP`` at
``.venv/.../arc_agi/rendering.py:21-37`` (value → hex, with the name in the source
comment). That module is NOT importable here: it top-imports ``arcengine`` and
``numpy`` (``from arcengine import FrameDataRaw`` / ``from numpy import ndarray``),
which would drag the SDK across the sandbox fence and break scipy-free execution.
So the names are transcribed as a small local constant, cited to source — a mirror
of the platform palette (universal machinery, shared by every world), rendered only
in this diagnostic dossier for the Director's read, never written to belief.

Cell-site rendered compactly (count + NW-most cell); the exact per-cell set and the
integer-delta magnitude are a later drill-down rung (the per-cell set is opt-in
behind ``verbose``).

Scope: ``ctx.woven_worldlines`` is PERSIST_LIVES_RESET_LEVEL — overwritten each
life — so the roster is THIS level's LAST life (labelled last-life, not accumulated).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from virelai_v4.capture.clay import collapse_fingerprints

# The platform's universal 0–15 render palette, mirrored from
# ``arc_agi/rendering.py:21-37`` COLOR_MAP (value → hex; name = source comment).
# Local (not imported) to keep this diagnostic scipy-/SDK-free. Diagnostic label
# only — never a belief-write. If a class int falls outside 0–15, ``_color`` emits
# a traceable ``c{id}`` placeholder, never an invented name.
COLOR_NAMES = {
    0: "White",
    1: "Off-white",
    2: "Neutral-light",
    3: "Neutral",
    4: "Off-black",
    5: "Black",
    6: "Magenta",
    7: "Magenta-light",
    8: "Red",
    9: "Blue",
    10: "Blue-light",
    11: "Yellow",
    12: "Orange",
    13: "Maroon",
    14: "Green",
    15: "Purple",
}


def _color(class_id: int) -> str:
    """A class int as its bold platform color name WITH the raw class integer in
    parentheses, e.g. ``**Blue (9)**`` — the human-readable color and the value the
    solver actually holds, side by side, so the grader can cross-check a suspect
    color against the raw frame. Out-of-palette ids stay traceable: ``**c{id} ({id})**``."""
    name = COLOR_NAMES.get(class_id)
    label = name if name is not None else f"c{class_id}"
    return f"**{label} ({class_id})**"


def _location(cells: Iterable[Tuple[int, int]]) -> Tuple[int, int]:
    """The NW-most MEMBER cell — the actual cell smallest by (row, col). Distinct
    from clay's ``_anchor`` (bbox top-left, which need not be a member). Empty →
    (-1, -1) sentinel."""
    cs = list(cells)
    if not cs:
        return (-1, -1)
    return min(cs, key=lambda c: (c[0], c[1]))


def _members_of(worldline: Any) -> List[Any]:
    """A worldline's ``steps`` as ``(node_index, node_hash, region)`` triples for
    the collapse core. ``steps`` carries no node_hash (not retained on the weave),
    so it is left empty — the roster reads only class/cells/anchor/counts."""
    return [(node_index, "", region) for (node_index, region) in worldline.steps]


def _object_line(entry: Any, verbose: bool = False) -> str:
    """One distinct visual object, color-first: bold color · size · NW cell ·
    appearances · node span. ``verbose`` appends the full member cell-set (the
    drill-down, opt-in)."""
    cls, cells = entry.fingerprint
    lr, lc = _location(cells)
    nodes = [ap.node_index for ap in entry.trail]
    span = f"{nodes[0]}–{nodes[-1]}" if nodes else "?"
    line = (f"{_color(cls)} · {entry.cell_count} cells · NW ({lr},{lc}) · "
            f"{entry.seen_count} appearance(s) · nodes {span}")
    if verbose:
        cell_str = " ".join(f"({r},{c})" for r, c in sorted(cells))
        line += f" · cells [{cell_str}]"
    return line


def _y_label(y: int, lives_observed: Optional[int]) -> str:
    """Y, labelled honestly as last-life (no cross-life accumulation)."""
    if lives_observed:
        return f"Y={y} (last life; {lives_observed} lives observed)"
    return f"Y={y} (last life)"


def _class_field(classes: List[int]) -> str:
    """The ###-header color field: one → its color; two → a→b; else MIXED."""
    if len(classes) == 1:
        return _color(classes[0])
    if len(classes) == 2:
        return f"{_color(classes[0])}→{_color(classes[1])}"
    return "**MIXED**"


# WO-ROSTER-SEVER-01 · THE BAND-2 VOCABULARY — SOURCED, NOT INVENTED, AND PINNED.
#
# This set was `{EGO, LEVER, REACTIVE, COUNTER, STATIC}` — the five BBA log-odds axes of
# `library/store_a_role_read.py`, the LEGACY producer this rung severs. It was never the
# weave's vocabulary, and it went stale twice without anything noticing: R-3 renamed
# `DEPENDENT` to `REACTIVE-DRIVEN`, WO-INERT-CERTIFICATE-01 added `INERT`, and both
# rendered as `UNKNOWN` here. R-4 retired `UNKNOWN` as a value outright and this file kept
# emitting it. That staleness is what WO-LIST-3-01 surfaced and what this constant fixes.
#
# It now mirrors the Band-2 values `weave.role_read.infer_roles` ACTUALLY EMITS, read off
# its `RoleVerdict(...)` construction sites rather than off its declared vocabulary tuple:
#
#     COUNTER · LEVER · REACTIVE · REACTIVE-DRIVEN · INERT      and `None`, rendered ∅
#
# `EGO`, `STATIC` and `UNKNOWN` are DECLARED in `role_read.py`'s vocabulary tuple and
# NEVER CONSTRUCTED. `STATIC` was vacated to Band 1 (WO-STATIC-VACATION-01); `UNKNOWN` was
# retired as a value (R-4); `EGO` is named-only — the mover-with-no-directional-input site
# emits `None` with an "EGO out-of-input" basis, so the weave cannot presently say EGO.
# Mirroring the EMITTED set rather than the declared one is deliberate: the declared tuple
# would silently re-admit two dead names and one unreachable one.
#
# A MIRROR, BECAUSE IMPORTING WOULD BREACH THE FENCE — the same discipline `COLOR_NAMES`
# above already uses, and for the same reason: this module's three-import purity is what
# lets it run where the SDK and scipy are absent. The mirror cannot drift, because
# `tests/diagnostics/test_roster_sever.py` re-derives the emitted set from `role_read.py`'s
# AST and fails if the two disagree. The next value the weave learns to emit breaks that
# test rather than rendering as UNKNOWN for a campaign or two.
# WO-EGO-01 v2 · `EGO` joins the emitted set. It was a declared value with no
# construction site until `weave/ego_read.py` gave it one; the pin below caught the
# staleness on the FIRST vocabulary change since it was built, which is what it is
# for. The mirror stays a mirror — importing `weave.role_read` would breach this
# renderer's own import purity, so the pin re-derives the truth every run instead.
_ROLE_BUCKETS = frozenset({"COUNTER", "LEVER", "REACTIVE", "REACTIVE-DRIVEN",
                           "INERT", "EGO"})

# `role is None` — no role earned. R-4: "UNKNOWN is retired as a value; an empty Band 2 is
# None, rendered ∅." Distinct from `UNKNOWN`, which this file now emits for exactly one
# condition: no verdict at all for that ###.
_BAND2_EMPTY = "∅"


def _role_bucket(role_verdicts: Optional[Mapping[int, Any]], wid: int) -> str:
    """The ###'s Band-2 value alone, without the confidence. Extracted (WO-MERGE-01) so
    the bucket has ONE definition: the summary line's flag and the label must never
    disagree about what role a ### is in, and parsing the bucket back out of
    ``_role_label``'s formatted string would be a second, drift-prone definition.

    THREE OUTCOMES, THREE MEANINGS — WO-ROSTER-SEVER-01:
      ``UNKNOWN``  no verdict for this ### at all (or no mapping supplied).
      ``∅``        a verdict exists and earned no role. NOT the same statement.
      the value    a verdict earned one of the emitted Band-2 names.
    An unrecognised token still reads ``UNKNOWN`` rather than rendering blind — but that
    branch is now a bug report, not a routine path, because the mirror is pinned to the
    producer by test."""
    if not role_verdicts or wid not in role_verdicts:
        return "UNKNOWN"
    raw = getattr(role_verdicts[wid], "role", None)
    if raw is None:
        return _BAND2_EMPTY
    role = str(raw)
    return role if role in _ROLE_BUCKETS else "UNKNOWN"


def _role_label(role_verdicts: Optional[Mapping[int, Any]], wid: int) -> str:
    """The ###'s BAND 2 + confidence, e.g. ``COUNTER (FIRM)`` — one producer,
    ``weave.role_read.infer_roles``, since WO-ROSTER-SEVER-01. Never blank.

    WHY BAND 2 AND NOT BAND 1 — the P5 question, answered rather than assumed. Before the
    severance this slot showed `store_a_role_verdicts`'s argmax over
    ``(ego, lever, reactive, counter, static)``: a set mixing Band-2 archetypes with
    Band-1 self-state names, so the slot has been showing WHICHEVER BAND happened to hold
    the most accumulated evidence. That collapse is the thing being severed, and choosing
    Band 1 here would rebuild it one layer over — the closing summary's own header names
    this field ``role``, and role is Band 2 in the ratified taxonomy. Band 1 is not lost:
    the ``###`` line already carries its STATIC/ACTIVE composition read, and LIST 3
    carries Band 1 with coverage and flash count.

    ``∅`` DOES NOT CARRY ITS COVERAGE HERE, AND THAT IS REPORTED RATHER THAN FAKED.
    R-4 requires an empty Band 2 to be "always accompanied by its coverage", and Band 2's
    coverage is `live_presses` — which `RoleVerdict` carries on NO FIELD; it exists only
    inside the free-text ``basis``. Parsing a number back out of a rendered sentence is
    the second drift-prone definition this function was extracted to prevent, and §4
    forbids computing what is not in hand. ``band1_coverage`` IS in hand but is Band 1's
    number, and pinning it beside a Band-2 value is the band collapse again. So the
    confidence renders alone and the gap is named in the return: the fix is a
    ``band2_coverage`` field on ``RoleVerdict``, one line, in a file this rung may not
    touch."""
    if not role_verdicts or wid not in role_verdicts:
        return "UNKNOWN (—)"
    conf = str(getattr(role_verdicts[wid], "confidence", "") or "—")
    return f"{_role_bucket(role_verdicts, wid)} ({conf})"


# WO-COMPOUND-ROLE-01 · a second, independently-sourced confirmation, additive to
# whatever `_role_label` above already says. FOUNDATIONAL_ARCHETYPES_v2 §3: STATIC
# (self-delta) and LEVER (what clicking it causes elsewhere) are true answers to
# two different questions, not competing answers to one — this is not a second
# vote on the SAME question `_role_label` answers, so it is never folded into
# `_role_bucket`/`_role_label`'s own five-bucket vocabulary. Empty string when the
# worldline was not repeatedly, really contacted — matches `_multi_member_flag`'s
# own "append only when it fires" discipline, so a clean ### keeps its exact
# pre-suffix shape.

def _repeated_contact_suffix(repeated_contact: Optional[Iterable[int]], wid: int) -> str:
    """`` · LEVER (confirmed by repeated contact)`` when ``wid`` is in the
    independently-confirmed set (``weave.repeated_contact``), else ``""``. Display
    only — decides nothing, lands no role (RULING_OBSERVERS_INTEGRATOR_v1: the
    integrator's role verdict stays the sole decider)."""
    if not repeated_contact or wid not in repeated_contact:
        return ""
    return " · LEVER (confirmed by repeated contact)"


# WO-MERGE-01 Part 1 · THE COMPREHENSION FLAG, as amended by WO-MERGE-02 Part A.
#
# `TARGET_INTEGRATION_ROSTER_v1` §3 makes List 2 — each ### with its member visual
# objects — the ROOT grade: "a merge (two real objects woven into one ###) ... poisons
# every role above it." Reading it means checking every ###'s member list by eye.
#
# This is NOT a merge detector. It cannot be: whether two members are one object across
# time or two objects wrongly fused is a question about the world, and the roster is a
# pure read over already-woven output. It is a WHERE-TO-LOOK column.
#
# WO-MERGE-02: keyed on MEMBER SPAN, not on role. MERGE-01 exempted COUNTER and warned on
# everything else with more than one member, which flagged five vc33 worldlines that
# WO-MERGE-01 Part 2 then proved were not merges at all — their two members are never
# co-present, and Part B confirmed the revert in the raw frames (265 cells out at node 6,
# 264 back to their exact prior value at node 7). Five false positives.
#
#   SETTLED  a member spanning MORE THAN ONE node. Two or more of these is the merge
#            signature — two real objects, each persisting, fused into one ###. The only
#            condition that warns.
#   FLASH    a member spanning exactly one node where the worldline held one fingerprint
#            at n-1 and the SAME one again at n+1 — out and straight back. Annotated,
#            never warned: a transient excursion does not flip the settled tag.
#   TICK     a member spanning exactly one node that does NOT revert — forward progress.
#            A counter mints one per tick.
#
# The role check is GONE, and its removal is measured, not assumed: on the vc33 run both
# COUNTERs read settled=0, flash=0, tick=51/49 — all ticks, so they never reach the
# warning without any exemption. The span rule subsumes the role rule, which is the right
# way round for this project: the annotation is earned from the measurement rather than
# granted by a label.
#
# Display only. Writes no belief, changes no worldline, decides nothing.

def _member_spans(entries: Iterable[Any]) -> Tuple[int, int, int]:
    """``(settled, flash, tick)`` over one ###'s distinct visual objects.

    A member is FLASH when it occupies exactly one node ``n`` and the worldline held some
    OTHER fingerprint at both ``n-1`` and ``n+1`` — the same one. Note this is the reverse
    of a naive reading: a flash member's own fingerprint can never match an earlier
    member's, because `collapse_fingerprints` would have merged them into one entry. It is
    the WORLDLINE that reverts, not the member that repeats."""
    ent = list(entries)
    at = {ap.node_index: e.fingerprint for e in ent for ap in e.trail}
    settled = flash = tick = 0
    for e in ent:
        nodes = [ap.node_index for ap in e.trail]
        if len(nodes) > 1:
            settled += 1
            continue
        n = nodes[0]
        before = at.get(n - 1)
        if before is not None and before == at.get(n + 1) and before != e.fingerprint:
            flash += 1
        else:
            tick += 1
    return settled, flash, tick


def _multi_member_flag(settled: int, flash: int, tick: int) -> str:
    """The suffix for one ### — ``""`` when there is nothing to say.

    Appends ONLY when it fires: a single-member ###'s line keeps its exact pre-flag shape,
    so the majority case is unchanged and anything appended reads as an exception rather
    than as decoration (WO-MERGE-01 §Part 1.3). Counts ride in the suffix, which is the
    only place the line grows."""
    if settled >= 2:
        return f" ⚠ MULTI-MEMBER ({settled}), verify"
    parts = []
    if flash:
        parts.append(f"✦ FLASH ×{flash}")
    if tick:
        parts.append(f"✓ TICKS ×{tick}")
    return (" " + " ".join(parts)) if parts else ""


# ---- WO-ROSTER-SEVER-01 · LIST 3, SINGLE-PRODUCER ----------------------------
#
# `TARGET_INTEGRATION_ROSTER_v1` specifies THREE independently-gradeable lists. WO-LIST-3-01
# built List 3 as a TWO-producer section — the weave beside `library/store_a_role_read.py`,
# each labelled, neither reconciled — on CE's then-standing ruling that the legacy role
# source was an authorized bridge.
#
# THAT RULING IS REVERSED. `RULING_GOLDEN_RUN_v1`'s method is locate → label → port →
# ISOLATE, and the prior ruling stopped at label. The measurement that settled it: of the
# 8 `⚠ DISAGREE` markers the two-producer section fired on the primary canary, ONE was a
# genuine disagreement. Seven compared a BAND-1 statement (Store-A argmaxes `static` and
# `reactive`, which are self-state names) against a BAND-2 slot — the two columns were not
# answering the same question, so the marker was measuring a category error, not a
# conflict. Two real conflicts went unmarked because weave `∅` reads as a silence.
#
# A comparison that is invalid seven times in eight is not a weak instrument; it is a
# wrong one. So the second column is GONE, and with it the marker — with one producer
# there is nothing to disagree with. This is not the section getting smaller. It is the
# roster no longer grading itself against a source whose vocabulary crosses the band
# boundary the taxonomy exists to hold.
#
# THE SEVERANCE IS STRUCTURAL, NOT POLITE. This renderer no longer has a PARAMETER for a
# second producer: `weave_verdicts` and `role_verdicts_producer` are removed, and
# `role_verdicts` is the weave. There is no slot a future caller could quietly refill.
# `library/store_a_role_read.py` is not deleted and not edited — it is left in the tree,
# labelled, and unread by any golden-run rendering path.
#
# ONE LINE PER ###, NO CONTINUATION. The `↳` line carried clipped basis fragments, and a
# clipped fragment is worse than an absent one: `coverage: ai…(+92 chars)` costs a line and
# answers nothing. The full, unclipped basis for every ### is in the ROLE INFERENCE block,
# and the header says so once.
#
# THREE DISTINCT ABSENCES, THREE DISTINCT MARKERS — kept verbatim from WO-LIST-3-01, the
# discipline `_marginal_str` (`weave/verb_stream_render.py`) and the interaction
# certificate (`weave/role_read.py`) already carry. A blank cell and a measured value must
# never look alike:
#
#   ``(not supplied)``   the caller passed no mapping at all.
#   ``(no verdict)``     the mapping exists; THIS worldline is absent from it.
#   ``(not observed)``   the verdict exists; that field on it is empty — Band 1's `""`,
#                        which `RoleVerdict` documents as distinct from either tag and
#                        which must never be rendered as one.

_L3_NOT_SUPPLIED = "(not supplied)"
_L3_NO_VERDICT = "(no verdict)"
_L3_NOT_OBSERVED = "(not observed)"
# A parallax carried by at least this many rows is stated once in the header instead of
# repeating verbatim down the section. Two, because the second occurrence is the first
# time repetition exists to remove.
_L3_SHARED_PARALLAX_MIN = 2



# ---- WO-LABEL-RENDER-01 · THE ADDITIVE FIELDS, PRINTED ------------------------
#
# `ground` and `wall` are computed, attached to `RoleVerdict`, and were printed NOWHERE:
# zero occurrences of either in the whole rendered roster. `###019` read `LEVER
# (PROVISIONAL)` while carrying `ground=True`; `###016` and `###020` read `∅
# (PROVISIONAL)` while typing WALL on 20 and 21 of 21 records offline. **Two of the four
# labels this lab has built could not be graded from the artifact the Director grades
# from.**
#
# BESIDE THE ROLE, NEVER REPLACING IT. The Band-2 role is the ratified slot and it prints
# first, unchanged, byte-for-byte; the fields follow it. A worldline carrying neither gets
# the EMPTY STRING and its line keeps its exact prior shape — the same "appends only when
# it fires" discipline `_multi_member_flag` states, so anything appended reads as an
# exception rather than as decoration.
#
# ONE PRODUCER, NOTHING RECOMPUTED. Both fields are read off `RoleVerdict` with `getattr`
# and defaulted to `False`. This module derives nothing, calls no seal, and would render
# identically if every predicate in the weave were deleted — which is the only honest
# shape for a render (the discipline `contact_line` and `declare_intent` set).
#
# ORDER IS FIXED AND ALPHABETICAL-BY-CONSTRUCTION rather than by importance: GROUND then
# WALL, always, so two runs of the same input cannot reorder the suffix and a diff of two
# rosters shows a changed BELIEF rather than a changed rendering.

def _label_fields(role_verdicts: Optional[Mapping[int, Any]], wid: int) -> str:
    """`" + GROUND"`, `" + WALL"`, both, or `""` — the additive fields on this ###'s
    verdict, in fixed order.

    `getattr(..., False)` is deliberate on both: a verdict built before either field
    existed reads `False` rather than raising, so an older stored verdict renders as
    "not typed" instead of taking the roster down. That is the same read
    `weave/wall_read.wall_worldlines` makes, and the two cannot disagree because neither
    computes anything."""
    if role_verdicts is None or wid not in role_verdicts:
        return ""
    v = role_verdicts[wid]
    out = ""
    if getattr(v, "ground", False):
        out += " + GROUND"
    if getattr(v, "wall", False):
        out += " + WALL"
    return out

def _l3_lookup(verdicts: Optional[Mapping[int, Any]], wid: int) -> Tuple[str, Any]:
    """``(marker, verdict)`` — ``marker`` empty when a verdict is in hand. The single
    absence gate every List 3 cell goes through, so the three markers have one
    definition and cannot drift between columns."""
    if verdicts is None:
        return _L3_NOT_SUPPLIED, None
    if wid not in verdicts:
        return _L3_NO_VERDICT, None
    return "", verdicts[wid]


def _l3_role_cell(verdicts: Optional[Mapping[int, Any]], wid: int) -> str:
    """``ROLE/CONF`` — the weave's Band 2, or an absence marker. ``∅`` is the vocabulary's
    own name for "no role earned" (`RoleVerdict.role is None`) — rendered as itself, never
    collapsed into UNKNOWN, which R-4 retired as a value."""
    marker, v = _l3_lookup(verdicts, wid)
    if marker:
        return marker
    role = getattr(v, "role", None)
    conf = str(getattr(v, "confidence", "") or "—")
    # WO-LABEL-RENDER-01 · the additive fields ride the B2 cell, AFTER role/confidence.
    # The section's one-line-per-### rule is kept: a suffix, never a second column and
    # never a continuation line.
    return (f"{_BAND2_EMPTY if role is None else role}/{conf}"
            f"{_label_fields(verdicts, wid)}")


def _l3_band1_cell(verdicts: Optional[Mapping[int, Any]], wid: int) -> str:
    """Band 1 with its coverage, and its flash count only where non-zero — the claim and
    the evidence for the claim in one cell. Coverage is part of the claim, not decoration:
    a self-state observed over 2 steps and one observed over 51 are not the same fact."""
    marker, v = _l3_lookup(verdicts, wid)
    if marker:
        return marker
    band1 = str(getattr(v, "band1", "") or "")
    if not band1:
        return _L3_NOT_OBSERVED
    # WO-BAND-1-REVISIT-01 · `revisit`, not `flash`. The count is steps that returned to a
    # fingerprint the worldline already held — NOT canon §3's transient excursion, which
    # lives in the frame layers beneath the visible one and never reaches `Worldline.steps`
    # (`capture/ledger_build.py:49` takes `reconstruct(node)[-1]`). Renamed rather than
    # dropped: a number that outlives its concept under the old name is a phantom.
    #
    # Rendered for a CHANGER only. A STATIC worldline holds one fingerprint, so its revisit
    # count is `coverage - 1` by construction and says nothing the coverage does not. The
    # count separates an object that CYCLES among a few states from one that MARCHES
    # through many, and only a changer can do either.
    revisits = int(getattr(v, "band1_revisits", 0) or 0)
    coverage = int(getattr(v, "band1_coverage", 0) or 0)
    show = revisits and band1 != "STATIC"
    return f"{band1}(cov {coverage}{f', revisit {revisits}' if show else ''})"


def _l3_contact_cell(repeated_contact: Optional[Iterable[int]], wid: int) -> str:
    """Repeated-contact membership, in the EVIDENCE position — never the role position.
    `weave/repeated_contact.py` is a contact tally thresholded to a set; its own docstring
    says it "decides nothing about which tag is correct".

    THE COUNT IS NOT RENDERED, AND THAT IS REPORTED RATHER THAN PAPERED OVER.
    ``count_acted_on_by_worldline`` computes the per-worldline tally and
    ``confirmed_by_repeated_contact`` discards it, returning only the thresholded set — so
    the count is not in hand at this render site, and §4 forbids computing what is not."""
    if repeated_contact is None:
        return _L3_NOT_SUPPLIED
    return "CONFIRMED*" if wid in repeated_contact else "—"


def _l3_shared_parallax(ids: List[int],
                        verdicts: Optional[Mapping[int, Any]]) -> List[str]:
    """Parallax notes carried by ``_L3_SHARED_PARALLAX_MIN`` or more rows, in first-
    appearance order.

    A note that is true of eight rows is a fact about the RULE, not about any one ###.
    Repeating `PROVISIONAL by construction: the offered action classes were all …`
    verbatim down every INERT row costs eight lines and tells the grader the same thing
    eight times. Stated once in the header, it reads as what it is.

    DISPLAY-ONLY AGGREGATION — a frequency count over strings already in hand. It measures
    nothing, derives nothing, and changes no verdict; drop it and every value in the
    section is unchanged. Deterministic by first appearance, so the header cannot reorder
    between runs on the same input."""
    if verdicts is None:
        return []
    order: List[str] = []
    counts: Dict[str, int] = {}
    for wid in ids:
        v = verdicts.get(wid)
        note = str(getattr(v, "parallax", "") or "") if v is not None else ""
        if not note:
            continue
        if note not in counts:
            order.append(note)
        counts[note] = counts.get(note, 0) + 1
    return [f"   ‡ shared by {counts[n]} ###: {n}"
            for n in order if counts[n] >= _L3_SHARED_PARALLAX_MIN]


def _list3_section(
    ids_classes: List[Tuple[int, str]],
    role_verdicts: Optional[Mapping[int, Any]],
    repeated_contact: Optional[Iterable[int]],
) -> List[str]:
    """LIST 3 — one row per ###, worldline-id order, ONE producer.

    Extracted rather than interleaved (THE INTERLEAVING BAN): the caller passes the
    ``(id, class-field)`` pairs its own single collapse pass already produced, so this
    section re-collapses nothing and adds no measurement of its own.

    Exactly one line per worldline. No continuation, no second column, no disagreement
    marker — see the block comment above for why each of the three is gone."""
    ids = [wid for wid, _ in ids_classes]
    out = [
        "── LIST 3 · ### SEMANTIC ROLE — one row per ###, single producer: "
        "weave.role_read.infer_roles (WO-ROSTER-SEVER-01) ──",
        "   B1 = did this ### ever change, over its coverage · revisit N = steps that "
        "returned to a fingerprint it already held, NOT an animation reading · B2 = the "
        "role, ∅ = none earned · contact = repeated-contact evidence, never a role · "
        "full unclipped basis for every ### is in the ROLE INFERENCE block",
    ]
    out.extend(_l3_shared_parallax(ids, role_verdicts))
    for wid, class_field in ids_classes:
        out.append(
            f"  ###{wid:03d} · {class_field} · B1 "
            f"{_l3_band1_cell(role_verdicts, wid)} · B2 "
            f"{_l3_role_cell(role_verdicts, wid)} · contact "
            f"{_l3_contact_cell(repeated_contact, wid)}")
    out.append(
        "  * contact = repeated-contact MEMBERSHIP only. The per-worldline tally exists "
        "inside weave.repeated_contact.count_acted_on_by_worldline and is discarded by "
        "confirmed_by_repeated_contact, so the count is not in hand here; reported, not "
        "computed at the render site (WO-ROSTER-SEVER-01 §4).")
    return out


def render_delivery_roster(rows, nodes: int) -> str:
    """**ONE LINE PER NODE WHOSE TURN DELIVERED MORE THAN ONE GRID.**

    `rows` is `(node_index, layer count, class, magnitude)` per node, computed by the caller
    via `capture.ledger_build.deliveries_of`; `nodes` is how many the record held.

    **THE CALLER COMPUTES AND THIS ONLY FORMATS**, and that is a fence rather than a taste:
    this module's own locking test holds it to stdlib plus `capture.clay`, because that
    purity *"lets this diagnostic run where the SDK and scipy are absent"* — and the
    producer imports scipy through `grid_scan`. **The first draft of this rung imported it
    here and broke exactly that guarantee**; the fence caught it.

    **A READING, NOT A VERDICT** — the coverage roster's own contract. No seal consumes it,
    no belief is written from it, and every absence states itself: a record with no
    multi-grid delivery says so rather than printing nothing.

    **THE CLASS IS A DELIVERY FACT AND THE HEADER SAYS SO WHERE IT IS READ.** The trichotomy
    compares the first and last grid of ONE turn and never sees the previous node, so a
    single-grid turn reads `SILENT` however much the world moved. A reader who takes these
    as outcomes will be wrong."""
    out = ["########## DELIVERY ROSTER · what the platform handed, per turn ##########",
           "  (a DELIVERY fact, never an outcome — a single-grid turn reads SILENT "
           "however much the world moved)"]
    if not nodes:
        out.append("  no capture record — absence, not a run without animation.")
        out.append("########## END DELIVERY ROSTER ##########")
        return "\n".join(out)
    multi = [r for r in (rows or ()) if r[1] > 1]
    for node_index, n, cls, mag in multi:
        out.append(f"  node {node_index}  {n} grids  {cls}  interior cells moved {mag}")
    if not multi:
        out.append("  every turn delivered a single grid — no animation in this record.")
    out.append(f"  multi-grid deliveries  {len(multi)} of {nodes}")
    out.append("########## END DELIVERY ROSTER ##########")
    return "\n".join(out)


def render_integration_roster(
    worldlines: Iterable[Any],
    verbose: bool = False,
    lives_observed: Optional[int] = None,
    role_verdicts: Optional[Mapping[int, Any]] = None,
    repeated_contact: Optional[Iterable[int]] = None,
) -> str:
    """LIST 1 (distinct visual objects, color-first) + LIST 2 (each ### → a header
    plus its FULL list of distinct visual objects, STATIC/ACTIVE) + X→Y, from the
    retained worldline set. Pure; returns the block as one string. ``verbose``
    appends each object's full cell-set; ``lives_observed`` labels Y.

    ``role_verdicts`` — ``{worldline_id: verdict}``. **THE ONE ROLE SOURCE**, and since
    WO-ROSTER-SEVER-01 it is `weave.role_read.infer_roles` and nothing else. It feeds
    every role claim the roster makes: List 2's header field, the closing summary, and
    LIST 3. When given, each ### carries its BAND 2 + confidence — one of
    COUNTER/LEVER/REACTIVE/REACTIVE-DRIVEN/INERT, or ``∅`` for none earned, or
    ``UNKNOWN`` for no verdict at all. Never blank. When None (older callers), the role
    field is omitted from List 2 and LIST 3 renders its absence markers.

    THE SEVERANCE, RECORDED HERE BECAUSE THIS SIGNATURE IS WHERE IT IS ENFORCED:
    `library/store_a_role_read.py` used to fill this slot, and WO-LIST-3-01 rendered it
    beside the weave as a second labelled column. `RULING_GOLDEN_RUN_v1` is locate →
    label → port → ISOLATE; that stopped at label. Store-A's argmax runs over
    ``(ego, lever, reactive, counter, static)`` — Band-2 archetypes mixed with Band-1
    self-state names — so 7 of the 8 disagreements the two-column section flagged were
    comparing different questions. The second producer's PARAMETERS ARE GONE, not merely
    unused: there is no slot a later caller could quietly refill. DISPLAY ONLY:
    derived-not-stored, writes no belief — the role does not LAND on the ### here
    (the belief-rebind is halted architecturally; see the R1b build return).

    ``repeated_contact`` (WO-COMPOUND-ROLE-01) — an iterable of worldline ids
    independently confirmed as LEVER by real, repeated contact this life
    (``weave.repeated_contact.confirmed_by_repeated_contact``). ADDITIVE to
    whatever ``role_verdicts`` already says, never a replacement — a worldline can
    carry both ``STATIC (FIRM)`` (the correlation answer) and the repeated-contact
    suffix (a second, independently-sourced answer to a different question,
    FOUNDATIONAL_ARCHETYPES_v2 §3). When None or empty (older callers / no
    confirmed worldlines), every suffix is ``""`` and the line is byte-identical
    to before that WO."""
    wls = list(worldlines) if worldlines else []
    lines: List[str] = [
        "########## INTEGRATION ROSTER (WO-B3-R1a-3; distinct visual objects, "
        "color-first; this level's last life; pure read) ##########"
    ]
    if not wls:
        lines.append("  (no woven worldlines retained — empty window or no "
                     "landing on this level)")
        lines.append(f"  X→Y ── X=0 distinct visual objects → "
                     f"{_y_label(0, lives_observed)} · compression n/a")
        return "\n".join(lines)

    # LIST 1 — distinct visual objects across ALL worldlines' members (global
    # (class,cells) collapse via the shared primitive). X counts DISTINCT objects,
    # not appearances.
    all_members = [m for wl in wls for m in _members_of(wl)]
    list1 = collapse_fingerprints(all_members)
    x = len(list1)
    total_app = sum(e.seen_count for e in list1)
    y = len(wls)

    lines.append(f"── LIST 1 · VISUAL OBJECTS (X={x} distinct · "
                 f"{total_app} appearances total) ──")
    for e in list1:
        lines.append("  " + _object_line(e, verbose))

    # LIST 2 — each ### → a header (representative color/size/NW + activity) then
    # its FULL member list of distinct visual objects. Activity read straight off
    # the collapse (STATIC = 1, ACTIVE = >1).
    lines.append(f"── LIST 2 · ### WORLDLINES — {_y_label(y, lives_observed)} "
                 f"— each ###'s distinct visual objects ──")
    # CLOSING SUMMARY rows captured in the SAME pass (no re-collapse): one compact
    # line per ### — id · color(class) · footprint size · NW anchor · role.
    summary: List[str] = []
    # WO-LIST-3-01 — the (id, class-field) pairs LIST 3 renders from, collected in THIS
    # pass so the section re-collapses nothing. A collection, not logic: LIST 3's own
    # rendering lives entirely in `_list3_section` (THE INTERLEAVING BAN).
    ids_classes: List[Tuple[int, str]] = []
    for wl in sorted(wls, key=lambda w: w.id):
        entries = collapse_fingerprints(_members_of(wl))
        distinct = len(entries)
        app = sum(e.seen_count for e in entries)
        classes = sorted({e.fingerprint[0] for e in entries})
        ccs = sorted({e.cell_count for e in entries})
        cc_str = f"{ccs[0]}" if len(ccs) == 1 else f"{ccs[0]}–{ccs[-1]}"
        hlr, hlc = _location([c for e in entries for c in e.fingerprint[1]])
        activity = "STATIC" if distinct == 1 else "ACTIVE"
        header = (
            f"  ###{wl.id:03d} · {_class_field(classes)} · {cc_str} cells · "
            f"NW ({hlr},{hlc}) · {distinct} visual object(s) · "
            f"{app} appearance(s) · {activity}")
        if role_verdicts is not None:
            header += f" · {_role_label(role_verdicts, wl.id)}"
        header += _repeated_contact_suffix(repeated_contact, wl.id)
        lines.append(header)
        ids_classes.append((wl.id, _class_field(classes)))
        for e in entries:
            lines.append("      ▪ " + _object_line(e, verbose))
        summary.append(
            f"  ###{wl.id:03d}: {_class_field(classes)}: {cc_str} cells: "
            f"NW ({hlr},{hlc}): {_role_label(role_verdicts, wl.id)}"
            f"{_label_fields(role_verdicts, wl.id)}"
            f"{_repeated_contact_suffix(repeated_contact, wl.id)}"
            f"{_multi_member_flag(*_member_spans(entries))}")

    ratio = (x / y) if y else 0.0
    lines.append(f"── X→Y ── X={x} distinct visual objects → "
                 f"{_y_label(y, lives_observed)} · X/Y = {ratio:.2f} ──")

    # THE CLOSING SUMMARY — the whole roster at a glance, one line per ###:
    # id · color(class) · cell-footprint size · NW anchor cell · semantic role.
    # Same data as List 2's headers, compressed to a single readable line each.
    lines.append("── CLOSING SUMMARY · one line per ### "
                 "(id: color(class): size: NW anchor: role) ──")
    lines.extend(summary)

    # WO-LIST-3-01 — LIST 3, appended BELOW the closing summary and above the terminator.
    # Placement note, reported rather than assumed: the WO says "after List 2's X→Y line",
    # and the roster already renders a CLOSING SUMMARY block between that line and the
    # END ROSTER terminator — a block the WO does not name. Appending below it satisfies
    # the WO's byte-identity requirement STRICTLY MORE than asked (nothing at or above
    # X→Y moves, AND the closing summary is untouched too) and keeps the terminator
    # terminal. See the return.
    lines.extend(_list3_section(ids_classes, role_verdicts, repeated_contact))
    lines.append(f"########## END ROSTER · {y} ### · {x} visual objects ##########")
    return "\n".join(lines)
