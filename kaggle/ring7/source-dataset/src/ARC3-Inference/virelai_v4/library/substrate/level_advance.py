"""
virelai_v4/library/substrate/level_advance.py — the §2.8.5 level-advance hook,
sub-WO 02a: snapshot + rescan + discard (the revoke-safe rebuild, Shape 2).

SEAM (trace f71b507, WO-XLEVEL-02-TRACE): called from virelai.py's level-advance
block, AFTER reset_for_new_level() + spawn_grid assignment, BEFORE
_sync_library(). Shape 2: the hook repopulates the library itself (V3.5
analogue: execution/level_transition.py bootstrap_new_level), so Mode A's
empty-library gate stays shut and the whole §2.8.5 hook lives at the one
verified seam.

WHY THIS STOPS THE SPASM (FM6/FM8, vc33 Level-2+ mindlessness):
Without the hook, Level-N ghost slots persist into Level N+1
(semantic_library is PERSIST_LIVES_AND_LEVELS; reset_objects_for_new_level
zeroes only the LGTD-01 eight). The captain walks ghosts from the advance
frame onward, the sweep builds from ghosts, and on the first Mode-B-eligible
frame revoke_on_class_change mass-zeroes the carried axes (ghost
previous_class_signature vs the new grid). After this hook, the library holds
FRESH Level N+1 slots: unprobed by construction (empty actions_attempted,
previous_class_signature=None), so the first Mode B pass initializes
signatures WITHOUT revoking (library_sync.py:177-180).

TIMING (corrected from the trace — see the trace doc's ERRATA): the mass
revoke fires at advance+2, the first Mode-B-eligible frame, NOT on the
advance frame: reset_for_new_level clears frame_delta AND prev_grid
(PER_LIFE_SCRATCHPAD, context.py:467-468), so the advance frame syncs Mode C
and the L(N)->L(N+1) mega-delta is structurally discarded before Mode B ever
sees it. STEP D of the WO (delta guard) is therefore architecture-already-
present; it is pinned by regression test, not by new code.

SINGLE RESPONSIBILITY (02a): the revoke-safe rebuild. The snapshot rides here
only because ghost priors are unreadable once discarded. WO-XLEVEL-02b
(Option A, CE-ratified) extends the same hook with type-match +
CLAMP-inherit (apply_type_inheritance below): matched fresh slots receive
the §12 priors at re-confirmable strength — every axis strictly below its
completion threshold — so an inherited belief is a SUSPICION the captain
re-confirms, never a CONFIRMATION it skips. NO revoke-on-contradiction, NO
re-falsification gating (WO-XLEVEL-03), NO captain changes, NO Mode A gate
changes.

§12 ruling carried: the snapshot is keyed by TypeSignature (pixel_class +
scale-normalized shape, library/cross_level_identity.py) — region_id is a
PER-LEVEL SPAWN LABEL (WO-B2-03 / AMENDMENT_RULING_LIB1 §2), falsified across
levels, appearing only as provenance, never trusted as identity. Same-type ghost
collisions merge deterministically: the slot with the strictly higher
lever_log_score wins; ties resolve to the earlier-born worldline — which, at the
single-node-born roster, is the lower spawn label (sorted iteration). The final
tie policy (RULING_LEVEL_BOUNDARY §4) and this label-order coincide by
construction until the roster is fed cross-node worldlines (layer 3).
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from virelai_v4.contracts.lever_mechanism import LeverMechanism
from virelai_v4.library.constants import (
    LEVER_LOCKED_THRESHOLD,
    LEVER_TYPED_THRESHOLD,
)
from virelai_v4.library.cross_level_identity import TypeSignature, type_signature
from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
from virelai_v4.library.semantic_library import SemanticLibrary
from virelai_v4.library.spawn_populator import _populate_from_scan
from virelai_v4.perception.grid_scan import scan_grid

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SlotPrior:
    """The §12 priors read off one ghost slot before discard.

    region_id is PROVENANCE ONLY (which ghost this came from) — never a
    match key. The match key is the TypeSignature this prior is stored under.
    Consumed by WO-XLEVEL-02b (type-match + inherit); 02a only captures."""
    region_id: int
    role: LibraryRole
    lever_mechanism: Optional[LeverMechanism]
    lever_locked: bool
    static_log_score: float
    reactive_log_score: float
    ego_log_score: float
    counter_log_score: float
    lever_log_score: float
    # DD gap-5: gate axis retired (not a floor role).


PriorSnapshot = Dict[TypeSignature, SlotPrior]


def build_prior_snapshot(library: SemanticLibrary) -> PriorSnapshot:
    """STEP A — capture the §12 priors of every ghost slot, keyed by type.

    Reads only fields that survive reset_for_new_level (the granular reset
    zeroes the LGTD-01 eight and explicitly NOT these —
    semantic_library.py:851-860), so snapshot-after-reset is sufficient.
    Collision rule: strictly higher lever_log_score wins; ties resolve to the
    lower spawn-label — arbitrary-but-stable, CHOSEN (WO-LB-01 ruling §4 interim,
    via sorted iteration), pending B2's final worldline tie policy. Pure read."""
    snapshot: PriorSnapshot = {}
    for region_id in sorted(library.objects.keys()):
        obj = library.objects[region_id]
        if not obj.cells:
            continue  # degenerate ghost — no shape, no type
        sig = type_signature(obj.class_id, obj.cells)
        prior = SlotPrior(
            region_id=region_id,
            role=obj.role,
            lever_mechanism=obj.lever_mechanism,
            lever_locked=obj.lever_locked,
            static_log_score=obj.static_log_score,
            reactive_log_score=obj.reactive_log_score,
            ego_log_score=obj.ego_log_score,
            counter_log_score=obj.counter_log_score,
            lever_log_score=obj.lever_log_score,
        )
        held = snapshot.get(sig)
        if held is None or prior.lever_log_score > held.lever_log_score:
            snapshot[sig] = prior
    return snapshot


# ---------------------------------------------------------------------------
# WO-XLEVEL-02b (Option A, CE-ratified) — type-match + clamp-inherit.
# ---------------------------------------------------------------------------

# DD gap-5: the five BBA Layer One floor axes, in field order (gate retired).
_AXES = ("static", "reactive", "ego", "counter", "lever")

# WO-LB-01 — the door's inverse: axis name -> the LibraryRole that routes to it
# (the mirror of log_score_accumulator._ROLE_TO_AXIS). The carry seeds an axis
# by calling the door with the axis's role; the door owns the write (A3 seal).
_AXIS_TO_ROLE = {
    "static": LibraryRole.STATIC,
    "reactive": LibraryRole.REACTIVE,
    "ego": LibraryRole.EGO,
    "counter": LibraryRole.COUNTER,
    "lever": LibraryRole.LEVER,
}


def _safe_sigmoid(x: float) -> float:
    """logit's inverse, overflow-guarded. Maps a log-score back to the
    confidence that, fed to accumulate_role_evidence on a fresh (0.0) axis,
    reproduces that log-score as the door's delta."""
    if x >= 0.0:
        return 1.0 if x >= 700.0 else 1.0 / (1.0 + math.exp(-x))
    e = 0.0 if x <= -700.0 else math.exp(x)
    return e / (1.0 + e)


def _clamp_log_score() -> float:
    """The §0(a) clamp target, computed from the threshold CONSTANTS.

    GOVERNING PRINCIPLE (Director directive): an inherited belief is a
    SUSPICION, never a CONFIRMATION. Every inherited axis is clamped strictly
    below its completion threshold so no inherited belief ever reads as a
    filled tier — the captain re-confirms each level with real evidence.

    Target sigmoid = LEVER_LOCKED_THRESHOLD + 0.1 (= 0.7): a fixed,
    conservative distance INTO the locked band. Returned as a log-score via
    the logit, since the axes store log-scores. Per the §0(b) enumeration
    this single bound sits strictly below every constant-threshold,
    axis-reading gate in the codebase:
      - LEVER_TYPED (completion): sigmoid("lever") >= 0.95
        (predicate_evaluators.py:322) — 0.7 < 0.95;
      - COUNTER_IDENTIFIED (prerequisite, declared/unwired):
        sigmoid("counter") >= CONFIRMATION_THRESHOLD (0.8)
        (predicate_evaluators.py:107) — 0.7 < 0.8; the Tier-2 instance of
        the same trap (a saturated counter inheritance would skip Tier 2
        exactly as a saturated lever inheritance skips Tier 4);
      - SLOT_IS_LEVER_LOCKED (prerequisite): sigmoid("lever") >= 0.6
        (predicate_evaluators.py:191) — 0.7 >= 0.6 FIRES, by design: the
        matched lever goes straight to eager cycle-probe re-confirmation.
    static/reactive/ego/gate currently have NO constant-threshold per-slot
    completion gate (the walk's static completion DISTINCT_PROBES_AT_LEAST
    reads actions_attempted, never an axis; SUBLIBRARY_* are parametrized
    and unwired in the Sub-Phase 2 walk) — the uniform clamp bounds them
    anyway, conservatively. Tier 2's assessor reads categorical role +
    `confidence` (assessor.py:140-153); `confidence` is never inherited,
    so Tier 2 cannot be forged by this path either."""
    target = LEVER_LOCKED_THRESHOLD + 0.1
    assert target < LEVER_TYPED_THRESHOLD, (
        "clamp target must stay strictly below the TYPED completion read"
    )
    return math.log(target / (1.0 - target))


def apply_type_inheritance(
    library: SemanticLibrary,
    snapshot: PriorSnapshot,
) -> int:
    """§1 — SEED the §12 priors onto type-matched fresh slots, THROUGH THE DOOR.

    WO-LB-01 — the carry goes through the door. Prior-level knowledge re-enters
    ONLY via ``accumulate_role_evidence`` (the sole axis-writer since A3). There
    is no ``setattr`` copy and no Store-B carry:

      - Each routable axis is SEEDED, not copied: the door is called with the
        axis's role at a capped seed confidence ``sigmoid(min(prior, clamp))``,
        so on a fresh (0.0) axis the door's delta lands exactly ``min(prior,
        clamp)`` — the old clamped value, but now ADDITIVE and door-owned. A
        seed never exceeds the clamp, so it never saturates an axis on its own;
        real this-level evidence weight-combines on top of it (the seed→verdict
        ladder). A neutral prior (0.0) carries no seed.

      - ``role`` (Store-B) is NOT carried — period (ruled). The useful knowledge
        ("this class was a lever") rides the lever-axis seed at seed weight; the
        categorical verdict is re-derived from this-level evidence.

      - ``lever_mechanism`` is NOT carried — dropped, re-earned per level (ruled
        WO-LB-01). A mechanism is a doing-claim (toggle vs cycle) that can change
        across the level discontinuity with no witness; carrying it as settled
        fact is seeds-never-verdicts violated. The re-earn path is built and
        eager: the lever-axis seed reaches the clamp (sigmoid 0.7), fires
        SLOT_IS_LEVER_LOCKED, and routes the matched lever straight to cycle-probe
        re-typing — one probe per matched lever per level, and the mechanism is
        always this-level-witnessed. (Carrying the prior mechanism as a
        probe-ORDERING hint — "try toggle first" — is legitimate dispatch, not
        belief; it charters at DSP-2b if ever wanted, never here.)

    NOT touched: actions_attempted (stays empty -> probed=False -> the
    first-touch coverage question stays open), lever_locked (dead field — the
    clamp is the guarantee), confidence (Tier-2's assessor re-earns it).
    Unmatched slots: untouched — fresh, below LOCKED, role UNKNOWN -> LGTD-AGG
    weight 10 keeps the broad sweep ahead of the matched levers. Returns the
    number of slots that seeded."""
    clamp = _clamp_log_score()
    inherited = 0
    for region_id in sorted(library.objects.keys()):
        obj = library.objects[region_id]
        if not obj.cells:
            continue
        prior = snapshot.get(type_signature(obj.class_id, obj.cells))
        if prior is None:
            continue
        for axis in _AXES:
            prior_log = getattr(prior, f"{axis}_log_score")
            if prior_log == 0.0:
                continue  # neutral prior — no belief to carry
            seed_target = min(prior_log, clamp)   # never above the clamp -> never saturates
            accumulate_role_evidence(
                obj, _AXIS_TO_ROLE[axis], _safe_sigmoid(seed_target),
            )
        # role and lever_mechanism deliberately NOT carried (WO-LB-01 ruling).
        inherited += 1
    if inherited:
        logger.info(
            "[XLEVEL-02b] seeded clamped type-priors through the door onto "
            "%d fresh slot(s) (prior-level provenance; role + lever_mechanism "
            "re-earned this level, not carried)",
            inherited,
        )
    return inherited


def run_level_advance_rebuild(
    context,
    library: SemanticLibrary,
    grid,
    available_actions: List[int],
) -> PriorSnapshot:
    """STEPS A-C — snapshot ghosts, rescan the L(N+1) spawn, discard ghosts,
    repopulate fresh slots. Returns the snapshot for WO-XLEVEL-02b.

    Fresh slots are revoke-safe and unprobed BY CONSTRUCTION:
    _populate_from_scan (Mode A's tested populate body, called here without
    Mode A's gate) builds LibraryObjects at their dataclass defaults —
    previous_class_signature=None (first Mode B initializes, does not revoke,
    library_sync.py:177-180), actions_attempted={}, probe_count=0.

    Side effects, all level-boundary-scoped:
      - library.objects cleared and repopulated from the fresh GridScan;
      - context.grid_scan set (Mode A storage parity — the field is
        PERSIST_LIVES_RESET_LEVEL and was just cleared by reset);
      - sdk_actions entries ensured for available_actions (idempotent,
        same as Mode A).
    NOT touched: header counters, spawn_class_frequencies
    (PERSIST_LIVES_AND_LEVELS, write-once — persistence design, not ours),
    cell_history/state_tracker, frame_delta/prev_grid (already cleared by
    reset_for_new_level — the structural mega-delta guard)."""
    snapshot = build_prior_snapshot(library)

    np_grid = np.asarray(grid, dtype=np.int32)
    grid_scan = scan_grid(np_grid)

    library.objects.clear()
    _populate_from_scan(
        library, grid_scan, list(available_actions), library.header.game_id,
    )

    if context is not None:
        context.grid_scan = grid_scan

    # WO-XLEVEL-02b (Option A): land the clamped priors before the hook
    # returns — same seam, no new call site.
    apply_type_inheritance(library, snapshot)

    return snapshot


__all__ = ["SlotPrior", "PriorSnapshot", "build_prior_snapshot",
           "apply_type_inheritance", "run_level_advance_rebuild"]
