"""
virelai_v4/library/cycle_probe.py — Cycle Probe per-frame state machine.

V3.5 source: ``Universal_Solver_v3_5/discovery/physics/cycle_probe.py`` (467 lines).
Filed: WO-CAMPAIGN3-PHASE3-01 (May 3, 2026); refactored at
WO-CAMPAIGN3-PHASE3-01-AMEND (May 3, 2026) per Director ratification.

V3.5 classification primitive ports verbatim from cycle_probe.py:181-287:
    - Per-pixel sign-reversal classifier (lines 209-221)
    - Cycle equality test on toggle pixels only (line 261)
    - Saturation = immediate-predecessor equality on toggle pixels (line 249)

V4 integration adaptation per Director framing (May 3, 2026): port the
intelligence; adapt the integration. V3.5's synchronous probe API was the
integration pattern V3.5 used because V3.5 had synchronous discovery phases.
V4's ``choose_action(frames, latest_frame) -> GameAction`` has no env access;
the framework owns ``env.step()``. The classification primitive (pure function
on raw frames) transcends the container; the activation harness adapts.

Signature divergence from stride probe (intentional): cycle probe takes
``latest_frame: np.ndarray`` because it accumulates raw frames for
classification. Stride probe doesn't take ``latest_frame`` because it
observes derived state (``library.header.ego_displacement_map``). The
state machine pattern is invariant across V4 probes; the input parameter
list reflects observation surface.

State machine (mirrors V4 stride probe at ``library/stride_probe.py:96-138``):

    Substrate: ``context.cycle_probe_state: Optional[CycleProbeState]``
    PER_LIFE_SCRATCHPAD per WO-PHASE3-01-AMEND Step 0 Recommendation 1.

    Per-frame entry: ``run_cycle_probe_step(context, library,
    available_actions, latest_frame) -> Optional[GameAction]``.

    State transitions per call:
      1. ``state is None``: no probe initialized; return None (caller falls through)
      2. ``state.iteration >= 4``: classification commit
         - Run ``_classify_transition`` on ``accumulated_frames`` (V3.5 verbatim)
         - Write verdict to ``LibraryObject.lever_mechanism``
         - Clear state; return None
      3. ``state.iteration < 4``: activation step
         - Append ``latest_frame`` to ``accumulated_frames`` (post-prior-activation)
         - For CLICK mode: emit ACTION6 click; advance iteration
         - For NAV_OCCUPANCY mode: emit next cardinal in BFS path or initialize path
         - Return GameAction

NAV_OCCUPANCY navigation pattern:
    Activation requires multi-step navigation: navigate to lever cell,
    step on (= activation), navigate off, navigate back, step on, ...
    Per WO-PHASE3-02 Step 0 Recommendation 2 ratified May 3, 2026:
    Interpretation (a) — budget at activation layer; navigation overhead
    acceptable.

    Unreachable lever (Step 0 Recommendation 4 refinement): if BFS
    returns None, set ``LibraryObject.lever_mechanism = UNKNOWN`` and
    clear state. UNKNOWN routes to Gray code per Hybrid dispatch
    (WO-PHASE3-02 sub-deliverable 1B); lever may be reached indirectly
    through combinatorial enumeration. Substrate-honest verdict;
    prevents retry loop.
"""
from __future__ import annotations

import hashlib
import logging
from typing import TYPE_CHECKING, List, Optional, Tuple

import numpy as np

from virelai_v4.library.library_roles import LibraryRole
from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
from virelai_v4.contracts.lever_mechanism import (
    ActivationMode,
    CycleProbeState,
    LeverCensus,
    LeverMechanism,
    TransitionProfile,
)

if TYPE_CHECKING:
    from arcengine import GameAction

    from virelai_v4.context import VirelaiContext
    from virelai_v4.library.semantic_library import SemanticLibrary


logger = logging.getLogger(__name__)


# WO-OCD-CYCLE-PROBE-VARIABLE-K (May 15, 2026): the cycle probe's
# fixed K=4 "budget" is replaced with a variable-K design driven by
# world termination conditions. K=20 is a CAP — a safety backstop
# that fires only when neither saturation (zero delta after a press)
# nor cycle detection (post-press state matches an earlier session
# state) resolves the classification within 20 consecutive presses.
# K counts consecutive presses in the current session; each fresh
# captain dispatch of a target lever (via _initialize_cycle_probe_state)
# resets the counter. This preserves Groundhog Day determinism: a
# lever that hits K=20 in Life 1 gets another K=20 in Life 2 against
# the same starting state, with reinvestigation eligibility per the
# Per-Object Investigation Budgets Amendment.
#
# Governing principle: spam before quit early. Action budget is
# recoverable across lives via Groundhog Day; lever-behavior
# information is not. The cycle probe stops when the world says it
# has nothing more to teach, not when an arbitrary budget runs out.
#
# V3.5 origin: cycle_probe.py:169 ("Budget: exactly 4 adapter.step()
# calls.") The V3.5 fixed-K invariant is superseded; the V3.5 verdict-
# discrimination logic (per-pixel sign-reversal, saturation, cycle
# equality, drift detection) is preserved in _classify_transition.
_PROBE_CAP = 20

# Backwards-compatible alias. Some upstream documentation, audit
# reports, and AST contract pins still reference _PROBE_BUDGET. The
# alias preserves these references' validity for one cycle while the
# campaign migrates explicitly to _PROBE_CAP. Deprecation removal
# scheduled with the reconciliation hygiene WO.
_PROBE_BUDGET = _PROBE_CAP


def _typing_coverage(state: "CycleProbeState") -> float:
    """WO-DIVE-01 R4 — coverage-weighted confidence, NOT proof of period.

    The dive types a lever on the FIRST recurrence within ``_PROBE_CAP``
    presses; "confirmed" means the presses observed so far were consistent
    with the verdict (a wrong cycle would have broken it), not that the period
    is proven. Coverage = the fraction of the probe budget that produced
    evidence (presses observed / cap), bounded to [0, 1]: each additional
    press the pattern survives is one more falsification passed, so more
    presses ⇒ higher coverage. Confidence is coverage, not truth — the belief
    stays conditional. ``state_hashes[0]`` is the pre-press baseline, so
    presses = len(state_hashes) - 1.

    NOTE (honest limitation, for CE): the current machinery commits on first
    recurrence; it does not yet press the two EXTRA confirm-steps the CE walk
    named. This tag reports coverage over the presses actually taken. Adding
    the explicit predict-then-press 2-confirm is a possible follow-up if CE
    wants the stronger protocol; it is not built this rung.
    """
    if _PROBE_CAP <= 0:
        return 0.0
    presses = max(0, len(state.state_hashes) - 1)
    return min(1.0, presses / _PROBE_CAP)


# ===========================================================================
# WO-DIVE-01.1 — the 2-confirm falsification loop (frame-spanning)
# ===========================================================================
# A detected recurrence enters CONFIRMING instead of committing on first sight.
# The captain presses 2 more (one per frame — §4 one-action-out), predicting the
# continuation; the type is committed only when both predicted transitions HOLD
# (R4: "confirmed" = predicted-and-held, not first-seen). A broken prediction
# resumes pressing. All bounded by _PROBE_CAP.
_CONFIRM_PENDING = "PENDING"        # a predicted transition held; more needed
_CONFIRM_COMMITTED = "COMMITTED"    # all predicted transitions held → confirmed
_CONFIRM_FALSIFIED = "FALSIFIED"    # a prediction broke → coincidence / longer cycle


def _enter_saturation_confirmation(state: "CycleProbeState") -> None:
    """A self-loop (no-delta) was detected. Predict the next 2 presses also yield
    no observable change (the same masked hash) and enter CONFIRMING. Deferred:
    SATURATED-as-condition is written only if both predictions hold."""
    last = state.state_hashes[-1]
    state.confirming = True
    state.confirm_predictions = [last, last]
    state.confirm_index = 0
    state.pending_saturation = True
    state.pending_mechanism = None
    state.pending_cycle_length = None


def _enter_cycle_confirmation(
    state: "CycleProbeState", j: int, cycle_length: int
) -> None:
    """A recurrence to an earlier state (index j) was detected. Predict the next
    2 presses reproduce the recorded continuation (state_hashes[j+1], [j+2]) and
    enter CONFIRMING. Deferred: TOGGLE/CYCLE-N is written only if both hold.
    j+1 and j+2 both exist: period = i - j >= 2 with i = len-1 ⇒ j+2 <= i."""
    hashes = state.state_hashes
    state.confirming = True
    state.confirm_predictions = [hashes[j + 1], hashes[j + 2]]
    state.confirm_index = 0
    state.pending_saturation = False
    state.pending_mechanism = (
        LeverMechanism.TOGGLE if cycle_length == 2 else LeverMechanism.CYCLE
    )
    state.pending_cycle_length = cycle_length


def _advance_confirmation(state: "CycleProbeState", observed_hash: bytes) -> str:
    """Compare the just-observed masked hash against the pending prediction. A
    mismatch is FALSIFIED (the recurrence was coincidence, or the cycle is
    longer). A match advances; when all predictions have held it is COMMITTED."""
    expected = state.confirm_predictions[state.confirm_index]
    if observed_hash != expected:
        return _CONFIRM_FALSIFIED
    state.confirm_index += 1
    if state.confirm_index >= len(state.confirm_predictions):
        return _CONFIRM_COMMITTED
    return _CONFIRM_PENDING


def _reset_confirmation(state: "CycleProbeState") -> None:
    """Exit CONFIRMING on a falsified prediction; resume normal pressing. The
    recorded sequence keeps growing; a later real recurrence re-triggers a fresh
    confirmation."""
    state.confirming = False
    state.confirm_predictions = []
    state.confirm_index = 0
    state.pending_saturation = False
    state.pending_mechanism = None
    state.pending_cycle_length = None


def _commit_pending_type(obj, state: "CycleProbeState") -> None:
    """Write the CONFIRMED type after the 2-confirm HELD. Mirrors the DIVE-01
    commit writes: SATURATED stays a CONDITION on obj.saturated (R2); TOGGLE/
    CYCLE write the type + cycle_length; both stamp entry-state E (R3) and
    coverage confidence (R4), and fire the BBA LEVER-axis hook."""
    if state.pending_saturation:
        obj.saturated = True
    else:
        obj.lever_mechanism = state.pending_mechanism
        obj.cycle_length = state.pending_cycle_length or 0
    obj.entry_state_signature = (
        state.state_hashes[0] if state.state_hashes else None
    )
    obj.lever_typing_confidence = _typing_coverage(state)
    accumulate_role_evidence(obj, LibraryRole.LEVER, 1.0)


# ===========================================================================
# Class wrapper — top of module; AST contract pin target per binding
# methodology #13 (V4 Testability Idiom).
# ===========================================================================


class CycleProbe:
    """Cycle probe — per-frame state machine for lever mechanism classification.

    Per V3.5 invariant (``cycle_probe.py:169``):
      - Budget = exactly 4 activations per lever
      - Per-pixel sign-reversal classifier separates toggle pixels from drift
      - Cycle equality test runs on toggle pixels only
      - Saturation test = immediate-predecessor equality on toggle pixels

    Dual-mode activation:
      - CLICK mode: V3.5-direct ACTION6 click at lever coordinate (verified
        against arcengine on Mac pytest May 3, 2026 per WO-PHASE3-01 Step 3
        Outcome A)
      - NAV_OCCUPANCY mode: cardinal navigation to lever cell + step-on
        activation (V4 invention per WO-PHASE3-01 §6.1; orchestrator wires
        in this amendment using existing NavAtlas BFS substrate per
        WO-PHASE3-02 Step 0 Hypothesis B)

    State machine substrate: ``context.cycle_probe_state: Optional[CycleProbeState]``
    PER_LIFE_SCRATCHPAD. See module docstring for state machine progression.
    """

    def run_step(
        self,
        context: "VirelaiContext",
        library: "SemanticLibrary",
        available_actions: List[int],
        latest_frame: np.ndarray,
    ) -> Optional["GameAction"]:
        """Per-frame state machine entry; class wrapper delegates to free function.

        Per binding methodology #13 (V4 Testability Idiom): lazy imports
        break import-cycle pressure; class wrapper is AST contract pin target.

        Returns
        -------
        Optional[GameAction]
            GameAction to emit (probe in progress; activation step or
            navigation step) or None (probe complete this frame; verdict
            written to LibraryObject.lever_mechanism; caller falls through
            to dispatch routing per lever_dispatch).
        """
        from virelai_v4.library.cycle_probe import _run_cycle_probe_step_impl

        return _run_cycle_probe_step_impl(
            context, library, available_actions, latest_frame
        )


# ===========================================================================
# Module-level entry point — V4 idiom matching stride probe
# (library/stride_probe.py:96-138).
# ===========================================================================


def run_cycle_probe_step(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    available_actions: List[int],
    latest_frame: np.ndarray,
) -> Optional["GameAction"]:
    """Per-frame state machine entry point. V4 idiom matching stride probe.

    See module docstring + ``CycleProbe.run_step`` for state machine
    description.
    """
    return _run_cycle_probe_step_impl(
        context, library, available_actions, latest_frame
    )


# ===========================================================================
# Invocation helpers — moved to library/cycle_probe_invocation.py per
# WO-PHASE3-02-RESUMPTION Step 1 corrective (May 5, 2026). The split
# preserves Phase Sovereignty (cycle probe domain owns invocation logic;
# helpers are reachable via ``from virelai_v4.library.cycle_probe_invocation
# import _has_unprobed_lever, _select_next_unprobed_lever,
# _initialize_cycle_probe_state``) while honoring Constitution §2 Ratchet
# Rule (cycle_probe.py would have crossed Yellow → Red without the split).
# ===========================================================================


# ===========================================================================
# Free functions — bottom of module; tested in isolation per binding
# methodology #13 (V4 Testability Idiom).
# ===========================================================================


def _hud_masked_state_hash(
    frame: np.ndarray,
    hud_mask: Optional[np.ndarray],
    lc_region: Optional[Tuple[int, int, int, int]],
    extra_cells=None,
) -> bytes:
    """Compute a HUD-mask-filtered state hash for cycle/saturation detection.

    Per WO-OCD-CYCLE-PROBE-VARIABLE-K (May 15, 2026): the cycle probe's
    per-press world-driven termination uses this hash to detect when a
    press produces no observable change (saturation: hash[i] == hash[i-1])
    or revisits an earlier session state (cycle: hash[i] == hash[j] for
    some j < i-1).

    Masking pipeline mirrors _classify_transition's pixel-precise
    filtering pattern:
      1. LC region zeroed via _mask_lc (V3.5 invariant cycle_probe.py:75-83)
      2. HUD mask cells zeroed (V3.5 invariant cycle_probe.py:181-187)

    The masked frame's bytes are hashed via sha256, which is overkill for
    collision resistance but cheap on 64x64 grids and gives a stable
    fingerprint across runs (deterministic per Groundhog Day discipline).

    WO-CP1-FIX-B: routed through the shared `mask_live_regions` util
    (WO-CP1-FIX-A) with an `extra_cells` channel — the library's
    COUNTER-classified slots' cells — so the per-press termination hash is
    robust even when `hud_mask`/`lc_region` are unavailable (the hollow
    action_reality_report chain). Without this, the live counter tick changed
    every press hash and saturation never fired (the WO-DIAG-CP1 K-cap burn).
    """
    from virelai_v4.perception.live_region_mask import mask_live_regions
    masked = mask_live_regions(
        frame, hud_mask=hud_mask, lc_region=lc_region, extra_cells=extra_cells,
    )
    return hashlib.sha256(masked.tobytes()).digest()


def _live_counter_cells(library: Optional["SemanticLibrary"]):
    """The union of COUNTER-classified slots' cells — the robust live-region
    source for the termination hash when arr/hud_mask are unavailable."""
    if library is None:
        return ()
    cells = []
    for obj in library.objects.values():
        if obj.role == LibraryRole.COUNTER and obj.cells:
            cells.extend(obj.cells)
    return tuple(cells)


def _mask_lc(
    frame: np.ndarray,
    lc_region: Optional[Tuple[int, int, int, int]],
) -> np.ndarray:
    """Return a copy of frame with the life-counter region zeroed out.

    V3.5 source: ``cycle_probe.py:67-84`` (verbatim port; preserved through
    refactor per WO-PHASE3-01-AMEND Step 0 Item 5).
    """
    f = np.asarray(frame, dtype=np.int32).copy()
    if lc_region is not None:
        r0, r1, c0, c1 = lc_region
        f[r0:r1 + 1, c0:c1 + 1] = 0
    return f


def _estimate_direction(
    raw_states: List[np.ndarray],
) -> Tuple[Optional[Tuple[int, int]], Optional[str]]:
    """Estimate direction vector from changed-coord centroids in S0→S1 and S1→S2.

    V3.5 source: ``cycle_probe.py:89-108`` (verbatim port; preserved through
    refactor per WO-PHASE3-01-AMEND Step 0 Item 5).
    """
    if len(raw_states) < 3:
        return None, None

    coords_a = np.argwhere(raw_states[1] != raw_states[0])
    coords_b = np.argwhere(raw_states[2] != raw_states[1])

    if len(coords_a) == 0 or len(coords_b) == 0:
        return None, None

    centroid_a = coords_a.mean(axis=0)
    centroid_b = coords_b.mean(axis=0)
    dr = int(round(float(centroid_b[0] - centroid_a[0])))
    dc = int(round(float(centroid_b[1] - centroid_a[1])))

    if dr == 0 and dc == 0:
        return None, None

    if abs(dr) > abs(dc):
        label = "DOWN" if dr > 0 else "UP"
    elif abs(dc) > abs(dr):
        label = "RIGHT" if dc > 0 else "LEFT"
    else:
        label = None

    return (dr, dc), label


# ===========================================================================
# State machine implementation
# ===========================================================================


def _run_cycle_probe_step_impl(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    available_actions: List[int],
    latest_frame: np.ndarray,
) -> Optional["GameAction"]:
    """Core state machine logic — per-frame advance.

    State machine cases per WO-PHASE3-01-AMEND Step 1 spec:
      1. ``state is None``: probe not initialized; return None (caller falls through)
      2. ``state.iteration >= 4``: classification commit
         - Run ``_classify_transition`` on accumulated_frames (V3.5 verbatim)
         - Write verdict to ``LibraryObject.lever_mechanism``
         - Clear state; return None
      3. ``state.iteration < 4``: activation step
         - Append ``latest_frame`` to ``accumulated_frames`` (post-prior-activation)
         - Mode dispatch: CLICK or NAV_OCCUPANCY
         - Return GameAction

    Per V3.5 invariant (``cycle_probe.py:169``): budget = exactly 4 activations.
    The state machine commits classification at ``state.iteration >= 4``;
    AST contract pin 1 re-pins against this check per WO-PHASE3-01-AMEND
    Step 0 Recommendation 5.
    """
    state = context.cycle_probe_state

    if state is None:
        return None  # No probe initialized; caller falls through

    # Append latest_frame as post-activation observation from prior iteration.
    # accumulated_frames holds: [spawn, post-act-1, post-act-2, ...] with one
    # entry per completed activation plus the spawn baseline. Under
    # WO-OCD-CYCLE-PROBE-VARIABLE-K, accumulated_frames can grow up to
    # _PROBE_CAP + 1 entries before the cap fires.
    if state.iteration > 0 and len(state.accumulated_frames) <= state.iteration:
        state.accumulated_frames.append(latest_frame)

        # WO-OCD-CYCLE-PROBE-VARIABLE-K (May 15, 2026): per-press
        # world-driven termination. After appending the post-press frame,
        # compute its HUD-masked hash, append to state.state_hashes, and
        # check the two world-stop conditions:
        #
        #   (1) Saturation — current hash equals the immediately previous
        #       hash. The press produced no observable change after HUD
        #       mask filtering. Verdict: SATURATED. Clear state, return None.
        #
        #   (2) Cycle detection — current hash matches an earlier session
        #       hash (with j < i-1 to ensure cycle_length >= 2). Verdict:
        #       TOGGLE if period 2, CYCLE otherwise. Clear state, return None.
        #
        # If neither fires and the cap is reached, _commit_classification
        # runs the full V3.5 classifier (drift detection branch). Otherwise
        # the state machine continues to the next activation step.
        lc_region = None
        arr = context.action_reality_report
        if arr is not None:
            lc_region = getattr(arr, "life_counter_region", None)
        new_hash = _hud_masked_state_hash(
            latest_frame, context.hud_mask, lc_region,
            extra_cells=_live_counter_cells(library),  # WO-CP1-FIX-B
        )
        state.state_hashes.append(new_hash)

        # WO-DIVE-01.1 — the 2-confirm falsification loop. A recurrence no
        # longer commits a type on FIRST sight; it enters a frame-spanning
        # CONFIRMING phase and presses 2 more, predicting the continuation. The
        # type commits only when the 2 predicted transitions HOLD (R4: confirmed,
        # not first-seen). A broken prediction resumes pressing (coincidence, or
        # a longer cycle). Every press — including the confirm presses — is
        # bounded by the _PROBE_CAP check below.
        obj = library.objects.get(state.target_object_region_id)

        if state.confirming:
            # Frame-spanning re-entry: check this frame's press against the
            # pending prediction (never a within-frame loop — §4 one-action-out).
            status = _advance_confirmation(state, state.state_hashes[-1])
            if status == _CONFIRM_COMMITTED:
                if obj is not None:
                    _commit_pending_type(obj, state)
                context.cycle_probe_state = None
                return None
            if status == _CONFIRM_FALSIFIED:
                # Recurrence falsified — resume pressing; do NOT re-detect on this
                # frame (a later real recurrence re-triggers on a later frame).
                _reset_confirmation(state)
            # _CONFIRM_PENDING or just-reset: fall through to press again.
        else:
            # (1) Saturation check — immediate-predecessor equality → CONFIRM
            # (predict 2 more no-deltas). Deferred commit.
            if (len(state.state_hashes) >= 2
                    and state.state_hashes[-1] == state.state_hashes[-2]):
                _enter_saturation_confirmation(state)
            else:
                # (2) Cycle detection — current hash matches an earlier session
                # hash with j < i-1 (ensures cycle_length >= 2; j == i-1 is the
                # saturation check above) → CONFIRM (predict the recorded
                # continuation reproduces). Deferred commit.
                current_hash = state.state_hashes[-1]
                for j in range(0, len(state.state_hashes) - 2):
                    if state.state_hashes[j] == current_hash:
                        cycle_length = (len(state.state_hashes) - 1) - j
                        _enter_cycle_confirmation(state, j, cycle_length)
                        break

    # Cap firing (was V3.5 fixed-budget commit). Under WO-OCD-CYCLE-PROBE-
    # VARIABLE-K, this fires only when neither per-press saturation nor
    # per-press cycle detection resolved the classification within
    # _PROBE_CAP consecutive presses. The full V3.5 classifier runs at
    # this commit point to do drift detection (DIRECTIONAL) or fall
    # through to UNKNOWN.
    if state.iteration >= _PROBE_CAP:
        return _commit_classification(context, library, state, latest_frame)

    if state.mode == ActivationMode.CLICK:
        # WO-OCD-CAPTAIN-TIER4-INSTANTIATION (May 15, 2026) — the inner
        # captain gate that lived here (added in WO-OCD-CAPTAIN-
        # IMPLEMENTATION Step 4) was REMOVED. Probes are inert tools;
        # gating belongs at the dispatch layer (action_selector.py:172
        # bypass gate + the captain's structural priority in
        # Virelai.choose_action). When the captain dispatches the cycle
        # probe at cursor=5 (Tier 4 LEVER TYPING), the inner gate would
        # have deadlocked the captain's own dispatch. The state machine
        # is now structurally indifferent to captain ownership — it
        # executes whenever called. See FRICTION-OCD-INNER-GATE-REMOVAL.
        #
        # WO-OCD-CHOKE-POINT (Step 5) — wire the cycle probe's missing
        # target ID. The cycle probe knows its target via state.target_
        # object_region_id; recording it on context here lets the
        # consolidated choke-point write in Virelai.choose_action emit
        # an accurate target_region_id and toggle the per-object
        # actions_attempted[6] flag for the cycle-probe's chosen target.
        # Without this, the cycle-probe path landed at the choke point
        # with target_rid=None and silently no-op'd the flag write.
        context.last_probe_target_region_id = state.target_object_region_id
        return _activate_click_step(state)
    elif state.mode == ActivationMode.NAV_OCCUPANCY:
        return _activate_nav_occupancy_step(state, context, library)
    else:
        raise ValueError(f"Unknown ActivationMode: {state.mode!r}")


def _commit_classification(
    context: "VirelaiContext",
    library: "SemanticLibrary",
    state: CycleProbeState,
    latest_frame: np.ndarray,
) -> Optional["GameAction"]:
    """Iteration==4 commit point. V3.5 ``_classify_transition`` runs verbatim.

    Verdict writeback uses pre-wired LibraryObject fields per WO-PHASE3-01
    Step 0 favorable surprise (cycle_length, direction_label, saturated
    fields already on LibraryObject).

    State cleared after commit; probe complete this frame.
    """
    # Append final frame if not already appended (handles boundary at iteration==4)
    if len(state.accumulated_frames) == _PROBE_BUDGET:
        state.accumulated_frames.append(latest_frame)

    # V3.5 classification — runs verbatim per cycle_probe.py:181-287
    arr = context.action_reality_report
    lc_region = None
    if arr is not None:
        lc_region = getattr(arr, "life_counter_region", None)

    profile = _classify_transition(
        state.accumulated_frames,
        lc_region,
        context.hud_mask,
    )

    # Verdict writeback to LibraryObject (per WO-PHASE3-01 Step 0
    # favorable surprise: cycle_length, direction_label, saturated fields
    # already pre-wired on LibraryObject).
    obj = library.objects.get(state.target_object_region_id)
    if obj is not None:
        # WO-E7 (type/condition de-collapse): the full-classifier producer.
        # A SATURATED verdict is a CONDITION, recorded on obj.saturated below;
        # it must NOT pollute the type field. So lever_mechanism receives the
        # mechanism ONLY when it is a real type (TOGGLE/CYCLE/DIRECTIONAL/...),
        # never SATURATED — a saturated lever keeps its prior type (None/UNKNOWN
        # if it was never typed, or its real type if it was). cycle_length /
        # direction_label are independent fields and write as before.
        # WO-DIVE-01 R1 (CE type-vocabulary ruling): the cap fired without a
        # per-press recurrence (saturation/cycle both missed within _PROBE_CAP).
        # A non-recurrent, non-saturated cap-commit is UNDETERMINED — the
        # dynamics did not settle within the bound, so the masked frame cannot
        # capture this lever from its entry state (terminal-for-this-E,
        # hidden/unrendered state). DIRECTIONAL is RESERVED for the effect
        # sub-tree (monotonic-forever vs hidden-state is undecidable without the
        # effect axis), so the classifier's DIRECTIONAL/UNKNOWN both type
        # UNDETERMINED this rung. SATURATED stays a CONDITION (R2, unchanged).
        if profile.mechanism in (LeverMechanism.TOGGLE, LeverMechanism.CYCLE):
            obj.lever_mechanism = profile.mechanism
        elif profile.mechanism != LeverMechanism.SATURATED:
            obj.lever_mechanism = LeverMechanism.UNDETERMINED
        obj.cycle_length = profile.cycle_length or 0
        obj.direction_label = profile.direction_label or ""
        obj.saturated = (profile.mechanism == LeverMechanism.SATURATED)
        # WO-DIVE-01 R3 + R4: stamp entry-state E and coverage confidence.
        obj.entry_state_signature = (
            state.state_hashes[0] if state.state_hashes else None
        )
        obj.lever_typing_confidence = _typing_coverage(state)
        # WO-BLUEPRINT-07: BBA Layer One accumulator hook (tertiary site,
        # cap-firing profile commit). Per audit §3.4: every terminal
        # `lever_mechanism` commit emits LEVER-axis evidence.
        accumulate_role_evidence(obj, LibraryRole.LEVER, 1.0)

    # Clear state — probe complete; caller falls through to dispatch
    context.cycle_probe_state = None
    return None


def _activate_click_step(state: CycleProbeState) -> "GameAction":
    """CLICK mode: emit ACTION6 click; advance iteration.

    V4 pattern (verified against arcengine source at
    ``arcengine/enums.py:88-93``):

        action = GameAction.from_id(6)
        action.set_data({"x": col, "y": row})
        return action

    V3.5 source comment at ``cycle_probe.py:118`` documents
    ``adapter.action_from_id(6, {"x": col, "y": row})`` — but that is
    V3.5's wrapped adapter signature, not arcengine's direct API. V4
    calls arcengine directly; ACTION6 is ComplexAction requiring
    ``set_data`` invocation per ``enums.py:58``. The V3.5 intent (build
    ACTION6 with x/y coordinates) ports verbatim; the V3.5 adapter
    signature does NOT because V4's container has different interface
    depth (no adapter layer). Per Director framing (May 3, 2026): port
    the intelligence; adapt the integration. The intent is invariant;
    the adapter signature is integration container.

    Pattern V4-A (see virelai.py:680-689 choose_action random fallback)
    chosen over Pattern V4-B (``GameAction.ACTION6.set_data(...)``)
    because Pattern V4-A returns the GameAction enum (not the
    ComplexAction instance), matching choose_action's per-frame contract.

    Verified against arcengine on Mac pytest May 3, 2026 per
    WO-CAMPAIGN3-PHASE3-01-AMEND Step 2.5 correction; previously-failing
    arcengine-gated tests pass post-correction.
    """
    row, col = state.target_lever_coord
    state.iteration += 1
    # WO-OCD-CYCLE-PROBE-VARIABLE-K (May 15, 2026): per-session
    # consecutive press counter. Distinct from `iteration` (preserved
    # for state-machine progression backwards-compat). Tracks how many
    # consecutive presses have fired in the CURRENT session. Reset to
    # 0 by _initialize_cycle_probe_state on every fresh captain
    # dispatch of a target lever (Groundhog Day reset, reinvestigation
    # trigger, or any captain re-entry). Used by future logic that may
    # report or gate on session-scoped press counts.
    state.consecutive_press_count += 1
    # Lazy import per V4 convention (see library/plan.py:62-67).
    from arcengine import GameAction

    action = GameAction.from_id(6)
    action.set_data({"x": col, "y": row})
    return action


def _activate_nav_occupancy_step(
    state: CycleProbeState,
    context: "VirelaiContext",
    library: "SemanticLibrary",
) -> Optional["GameAction"]:
    """NAV_OCCUPANCY navigation state machine.

    Sub-modes:
        nav_in_reset == False: navigating TO lever; final step is activation
        nav_in_reset == True: navigating OFF lever to enable re-activation

    Per WO-PHASE3-02 Step 0 Recommendation 2 ratified May 3, 2026:
    Interpretation (a) — budget=4 activations (the moments of stepping
    ONTO the lever cell); navigation overhead acceptable for NAV_OCCUPANCY
    mode.

    Unreachable lever handling (WO-PHASE3-01-AMEND Step 0 Recommendation 4
    refinement ratified): BFS returns None → set
    ``LibraryObject.lever_mechanism = UNKNOWN``; clear state; return None.
    UNKNOWN routes to Gray code per Hybrid dispatch (WO-PHASE3-02
    sub-deliverable 1B); lever may be reached indirectly through
    combinatorial enumeration. Substrate-honest verdict; prevents retry loop.
    """
    if state.nav_path is None:
        if state.nav_in_reset:
            path = _compute_step_off_path(state, context, library)
        else:
            path = _compute_bfs_to_lever(state, context, library)

        if path is None or len(path) == 0:
            # Unreachable lever — substrate-honest UNKNOWN verdict
            obj = library.objects.get(state.target_object_region_id)
            if obj is not None:
                obj.lever_mechanism = LeverMechanism.UNKNOWN
                # WO-BLUEPRINT-07: BBA Layer One accumulator hook (tertiary
                # site, unreachable-lever UNKNOWN terminal). Per audit §3.4:
                # the substrate has confirmed the slot is a lever (even if
                # untypable) — LEVER-axis evidence fires.
                accumulate_role_evidence(obj, LibraryRole.LEVER, 1.0)
            context.cycle_probe_state = None
            return None

        state.nav_path = path
        state.nav_path_index = 0

    action_id = state.nav_path[state.nav_path_index]
    state.nav_path_index += 1

    # Path complete — advance state machine sub-mode
    if state.nav_path_index >= len(state.nav_path):
        if state.nav_in_reset:
            # Reset complete; clear nav_path; next iteration is activation
            state.nav_path = None
            state.nav_in_reset = False
        else:
            # Activation step taken (last cardinal stepped onto lever)
            state.iteration += 1
            state.nav_path = None
            if state.iteration < _PROBE_BUDGET:
                # Set up reset for next iteration
                state.nav_in_reset = True

    # Lazy import per V4 convention.
    from arcengine import GameAction

    return GameAction.from_id(action_id)


def _compute_bfs_to_lever(
    state: CycleProbeState,
    context: "VirelaiContext",
    library: "SemanticLibrary",
) -> Optional[List[int]]:
    """Compute BFS path from current ego position to lever cell.

    Uses existing NavAtlas BFS substrate per WO-PHASE3-02 Step 0 Item 4
    Hypothesis B confirmed. Returns the cardinal action sequence; None
    when lever is unreachable (caller writes UNKNOWN verdict and clears state).
    """
    from virelai_v4.library.nav_bfs import nav_bfs_stride

    nav_atlas = context.nav_atlas
    if nav_atlas is None or context.ego_current_pos is None:
        return None

    # Use V4 existing BFS substrate; passes blocked_classes for blacklist mode
    # (V4 NavAtlas pattern; see library/nav_bfs.py).
    grid = context.prev_grid  # current observation; falls back to spawn_grid if None
    if grid is None:
        grid = context.spawn_grid
    if grid is None:
        return None

    path = nav_bfs_stride(
        grid=np.asarray(grid),
        start=context.ego_current_pos,
        target=state.target_lever_coord,
        passable_classes=nav_atlas.walkable_classes,
        ego_value_set=nav_atlas.ego_value_set,
        action_dirs=nav_atlas.action_dirs,
        blocked_classes=nav_atlas.blocked_classes,
    )
    return path  # may be None if unreachable; caller handles


def _compute_step_off_path(
    state: CycleProbeState,
    context: "VirelaiContext",
    library: "SemanticLibrary",
) -> Optional[List[int]]:
    """Compute step-off path: emit one cardinal action away from lever cell.

    Per Interpretation (a) ratified: between activations, ego must step OFF
    the lever cell so the next activation produces an observable transition
    (stepping from non-lever cell ONTO lever cell). The simplest reset is
    one cardinal step in any walkable direction; subsequent BFS to lever
    handles the navigation back.
    """
    nav_atlas = context.nav_atlas
    if nav_atlas is None:
        return None

    # Pick first walkable cardinal action from current position
    # (any cardinal that doesn't hit a blocked class)
    grid = context.prev_grid
    if grid is None:
        grid = context.spawn_grid
    if grid is None:
        return None

    grid_arr = np.asarray(grid, dtype=np.int32)
    ego_pos = context.ego_current_pos
    if ego_pos is None:
        return None

    er, ec = ego_pos
    h, w = grid_arr.shape[:2]
    for action_id, (dr, dc) in sorted(nav_atlas.action_dirs.items()):
        nr, nc = er + dr, ec + dc
        if not (0 <= nr < h and 0 <= nc < w):
            continue
        cell_class = int(grid_arr[nr, nc])
        if cell_class in nav_atlas.blocked_classes:
            continue
        # Found a walkable adjacent cell; one step is enough to be off lever
        return [action_id]

    # No walkable adjacent cell; ego trapped on lever
    return None


# ===========================================================================
# V3.5 classification primitive — preserved verbatim from WO-PHASE3-01.
# Per WO-PHASE3-01-AMEND Step 0 Item 5: pure function on raw frames; no
# synchronous-API entanglement; ports through refactor without modification.
# AST contract pins 2, 3, 4 target this function body unchanged.
# ===========================================================================


def _classify_transition(
    raw_states: List[np.ndarray],
    lc_region: Optional[Tuple[int, int, int, int]],
    hud_mask: Optional[np.ndarray],
) -> TransitionProfile:
    """Classification logic — V3.5 verbatim per cycle_probe.py:181-287.

    Three-stage classifier:
      1. Per-pixel sign-reversal classifier separates toggle pixels from
         drift pixels (cycle_probe.py:209-221) — load-bearing stage
      2. Saturation test = immediate-predecessor equality on toggle pixels
         (cycle_probe.py:249)
      3. Cycle equality test on toggle pixels only (cycle_probe.py:261)

    LC region masking and HUD mask applied per V3.5 invariants
    (cycle_probe.py:75-83, 181-187).

    Per WO-PHASE3-01-AMEND: this function ports through refactor verbatim;
    pure function on List[np.ndarray] — invariant against integration
    container choice (synchronous probe vs per-frame state machine).
    """
    # V3.5 invariant (cycle_probe.py:75-83): apply LC region masking.
    masked_states = [_mask_lc(s, lc_region) for s in raw_states]

    # V3.5 invariant (cycle_probe.py:181-187): apply pixel-precise HUD mask.
    if hud_mask is not None:
        _hm = np.asarray(hud_mask, dtype=bool)
        for _s in masked_states:
            _s[_hm] = 0

    # V3.5 invariant (cycle_probe.py:189-190): direction estimation from
    # 2D frames before flattening.
    direction_vector, direction_label = _estimate_direction(masked_states)

    # Flatten to 1D for per-pixel trajectory analysis (cycle_probe.py:193).
    states = [s.flatten() for s in masked_states]

    # ── Per-pixel classification (V3.5 cycle_probe.py:209-221, verbatim) ─
    n_pixels = len(states[0])
    toggle_indices: List[int] = []
    drift_pixel_count = 0

    for p in range(n_pixels):
        traj = [int(states[i][p]) for i in range(len(states))]
        diffs = [traj[i + 1] - traj[i] for i in range(len(traj) - 1)]
        nonzero_diffs = [d for d in diffs if d != 0]

        if not nonzero_diffs:
            continue  # static — never changed

        signs = {1 if d > 0 else -1 for d in nonzero_diffs}
        if len(signs) > 1:
            toggle_indices.append(p)  # direction reversal → toggle pixel
        else:
            drift_pixel_count += 1  # monotonic → LC / score / DIRECTIONAL pixel

    # ── No toggle pixels → DIRECTIONAL or UNKNOWN (V3.5 cycle_probe.py:223-235)
    if not toggle_indices:
        if drift_pixel_count > 0:
            return TransitionProfile(
                mechanism=LeverMechanism.DIRECTIONAL,
                cycle_length=None,
                states_observed=0,
                deterministic=False,
                observation_depth=_PROBE_BUDGET,
                drift_pixel_count=drift_pixel_count,
                direction_vector=direction_vector,
                direction_label=direction_label,
            )
        return TransitionProfile(
            mechanism=LeverMechanism.UNKNOWN,
            cycle_length=None,
            states_observed=0,
            deterministic=False,
            observation_depth=_PROBE_BUDGET,
            drift_pixel_count=0,
            direction_vector=None,
            direction_label=None,
        )

    # ── Narrow to toggle pixels only (V3.5 cycle_probe.py:237-239) ─────
    toggle_idx_arr = np.array(toggle_indices, dtype=np.intp)
    toggle_states = [states[i][toggle_idx_arr] for i in range(len(states))]

    # ── Classify on toggle states (V3.5 cycle_probe.py:241-287, adapted
    # for variable-length sequences per WO-OCD-CYCLE-PROBE-VARIABLE-K).
    # Pre-WO: iteration bound was hardcoded as _PROBE_BUDGET + 1 (= 5,
    # for the V3.5 fixed K=4 budget). Post-WO: the bound is the actual
    # sequence length, allowing the classifier to run on sequences of
    # length 2 to _PROBE_CAP+1 (= 21).
    n_states = len(toggle_states)
    observation_depth = max(0, n_states - 1)  # number of activation transitions observed
    for i in range(1, n_states):
        # V3.5 invariant (cycle_probe.py:249): saturation = immediate-
        # predecessor equality on toggle pixels.
        if np.array_equal(toggle_states[i], toggle_states[i - 1]):
            return TransitionProfile(
                mechanism=LeverMechanism.SATURATED,
                cycle_length=None,
                states_observed=i,
                deterministic=True,
                observation_depth=observation_depth,
                drift_pixel_count=drift_pixel_count,
                direction_vector=direction_vector,
                direction_label=direction_label,
            )
        # V3.5 invariant (cycle_probe.py:261): cycle equality test on
        # toggle pixels only; j < i-1 ensures cycle_length >= 2.
        for j in range(0, i - 1):
            if np.array_equal(toggle_states[i], toggle_states[j]):
                cycle_length = i - j
                # V3.5 invariant (cycle_probe.py:265): TOGGLE if
                # cycle_length == 2 else CYCLE.
                mechanism = (
                    LeverMechanism.TOGGLE if cycle_length == 2
                    else LeverMechanism.CYCLE
                )
                return TransitionProfile(
                    mechanism=mechanism,
                    cycle_length=cycle_length,
                    states_observed=i,
                    deterministic=True,
                    observation_depth=observation_depth,
                    drift_pixel_count=drift_pixel_count,
                    direction_vector=direction_vector,
                    direction_label=direction_label,
                )

    # No saturation or cycle found on toggle pixels within the observed
    # sequence (which under WO-OCD-CYCLE-PROBE-VARIABLE-K can be up to
    # _PROBE_CAP+1 frames). V4 maps to UNKNOWN: had toggle pixels
    # (state-bearing) but no cycle within the observation window —
    # verdict is uncertain, not directional.
    return TransitionProfile(
        mechanism=LeverMechanism.UNKNOWN,
        cycle_length=None,
        states_observed=observation_depth,
        deterministic=False,
        observation_depth=observation_depth,
        drift_pixel_count=drift_pixel_count,
        direction_vector=direction_vector,
        direction_label=direction_label,
    )


__all__ = [
    "CycleProbe",
    "run_cycle_probe_step",
]
