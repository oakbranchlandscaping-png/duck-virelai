"""
virelai_v4/library/semantic_library.py — SemanticLibrary artifact.

Transplanted with refactor from V3.5 observer/knife/semantic_library.py.
Schema aligned with the Semantic Library Contract (Phase 2 Strategy Chamber).
Where V3.5 and the contract disagree, the contract governs.

The SemanticLibrary is the single mutable artifact consolidating all solver
knowledge: objects, actions, exploration state, and header metadata. Every
probe feeds it. Every observation updates it. Every decision reads it.

Four sections:
    HEADER      — game_id, life, level, world type, ego mode.
    OBJECTS     — one LibraryObject per GridScan Region, keyed by region_id.
    ACTIONS     — sdk_actions (dict[int, SDKAction]) + lever_actions (dict[int, LeverAction]).
    EXPLORATION — novel/repeated state tracking (LibraryExploration).

Key V4 changes from V3.5:
    - SemanticLibrary is a @dataclass (not __init__-constructed).
    - update_object_role() raises ValueError on illegal transitions.
    - collection fields (reacts_to, causes, etc.) are tuples, not lists.
    - LibraryObject gains: cells (frozenset), shape_desc, position_desc, count_like.
    - LibraryAction split into SDKAction (by int key) and LeverAction (by region_id).
    - render() extracted to field_card.py (WO-05). Placeholder below.
    - Serialization helpers extracted to library_serializer.py (file-size rule).

Import sovereignty: imports from contracts/ and stdlib only.
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field, replace
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from virelai_v4.contracts.lever_effect import LeverEffect
from virelai_v4.contracts.conserved_transfer import ConservedTransfer
from virelai_v4.contracts.lever_mechanism import LeverMechanism
from virelai_v4.library.library_roles import LibraryRole, ObservationStatus

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# WO-BLUEPRINT-04 — BBA Layer One log-score sigmoid-read constants
# Per Blueprint Section 2.6.1 cap (0.98) and floor (0.02) for non-falsified axes.
# ---------------------------------------------------------------------------
_SIGMOID_CAP = 0.98
_SIGMOID_FLOOR = 0.02
# DD gap-5: the floor is the FIVE role axes. `gate` is NOT a floor role — it is a
# killed-prediction frontier CHILD of a typed lever (a lever-subtree node), so it
# has no place among the foundation categories and was retired here (it never
# received evidence: unmapped in log_score_accumulator._ROLE_TO_AXIS). Do not
# re-add it to the floor; if gate belief is needed, it lives under the lever tree.
_LOG_SCORE_CATEGORIES = (
    "static",
    "reactive",
    "ego",
    "counter",
    "lever",
)


# ---------------------------------------------------------------------------
# LibraryHeader
# ---------------------------------------------------------------------------

@dataclass
class LibraryHeader:
    """Per-step metadata. Updated every action."""
    game_id:          str   = ""
    life:             int   = 1
    actions_taken:    int   = 0
    level:            int   = 1
    world_type:            str   = "UNKNOWN"
    ego_mode:              str   = "UNKNOWN"
    ego_confidence:        float = 0.0
    world_type_confidence: float = 0.0
    ego_confirmed:         bool  = False          # WO-04: True when ego object identified
    ego_object_ids:        tuple = ()            # WO-04c: region_ids of confirmed ego objects (multi-class)
    ego_value_set:         tuple = ()            # WO-04c: pixel class IDs composing the ego
    ego_displacement_map:  dict  = field(default_factory=dict)  # WO-04c: {action_id: (d_row, d_col)}
    ego_centroid:          tuple = ()            # WO-04f: (row, col) centroid of last detected ego displacement
    ego_body_cells:        frozenset = field(default_factory=frozenset)  # WO-04g: spawn-frame ego footprint (direct capture)
    grid_rows:        int   = 64
    grid_cols:        int   = 64
    nav_stride:       int   = 0
    actions_remaining: int  = -1


# ---------------------------------------------------------------------------
# LibraryObject
# ---------------------------------------------------------------------------

@dataclass
class LibraryObject:
    """One row in the OBJECTS table.

    Identity group: set at spawn from GridScan Region. Should not change.
    Classification group: earned through evidence. Starts at defaults.
    Behavior group: accumulated from CellHistory over time.
    Causal group: populated as lever effects are confirmed.
    Counter group: COUNTER-role objects only.
    """
    # Set at spawn, immutable by convention.
    # WO-B2-03 (AMENDMENT_RULING_LIB1 §2 layer 1): region_id is a PER-LEVEL SPAWN
    # ORDINAL — a LABEL, never an identity. It is the canonical rank the spawn
    # scan mints (grid_scan.py:164, by area then class); it restarts each level
    # and is falsified across levels. Nothing trusts it as identity: rank-ness is
    # redundant where it means anything, ties are chosen not accidental, and
    # earned identity lives in the weave's worldlines (the Rosetta reads R<n> as
    # a name for a ### worldline). The name stays because, correctly named, it is
    # honest — it names a spawn region's label, nothing more.
    region_id:    int
    class_id:     int
    cells:        FrozenSet[Tuple[int, int]]
    cell_count:   int
    shape_desc:   str
    zone:         str
    position_desc: str
    layer:        str
    count_like:   int

    # Classification (earned through evidence)
    role:           LibraryRole = LibraryRole.UNKNOWN
    confidence:     float = 0.0
    sub_role:       str = ""
    evidence_basis: str = ""

    # Behavior (accumulated from CellHistory)
    change_count:     int = 0
    flash_count:      int = 0
    transition_count: int = 0
    reacts_to:        Tuple[int, ...] = ()
    reaction_type:    str = ""
    cycle_length:     int = 0
    direction_label:  str = ""
    saturated:        bool = False
    # WO-CAMPAIGN3-PHASE3-01: per-lever cycle probe verdict (May 3, 2026).
    # Categorical verdict from CycleProbe (TOGGLE / CYCLE / DIRECTIONAL /
    # SATURATED / UNKNOWN). Distinct from MechanicMemory.mechanic_type
    # (level-wide); this is per-lever. Wired in WO-PHASE3-02 Lever
    # Verdict Integration.
    lever_mechanism:  Optional[LeverMechanism] = None
    # WO-DIVE-01 R3 (path-dependent typing): the masked-frame signature at
    # dive start — state_hashes[0], the pre-press baseline E. Every lever type
    # is CONDITIONAL on the entry state it was typed from; a lever re-dived from
    # a different E may legally retype without contradiction (the belief is
    # conditional by construction). None until the lever is dived.
    entry_state_signature: Optional[bytes] = None
    # WO-DIVE-01 R4 (falsification-not-proof): coverage-weighted confidence of
    # the lever type — how much of the probe budget supported the verdict, NOT
    # proof of period. Confidence is coverage, not truth. None until typed.
    lever_typing_confidence: Optional[float] = None

    # Active/static observation — factual record, never modified by classifier (WO-RM-02)
    # is_active: True once any of this object's cells appeared in the world delta (monotone)
    # active_frame_count: number of frames on which this object had at least one world delta cell
    # first_active_frame: step number of first observed world delta involvement (-1 = never)
    # last_active_frame:  step number of most recent world delta involvement (-1 = never)
    is_active:          bool = False
    active_frame_count: int = 0
    first_active_frame: int = -1
    last_active_frame:  int = -1

    # Action Independence Metric (WO-C5-01) — accumulated across lives (Groundhog Day)
    # actions_observed: total NOT_FINISHED frames processed by Mode B for this object
    # actions_with_change: subset where at least one of this object's cells had a delta
    # Ratio near 1.0 → LC candidate; near 0.0 → background; between → lever
    actions_observed:   int = 0
    actions_with_change: int = 0

    @property
    def action_independence_ratio(self) -> float:
        """Fraction of observed actions on which this object had at least one changed cell.

        0.0 when no actions have been observed (avoids ZeroDivisionError).
        Near 1.0 → object changes on almost every action → Life Counter candidate.
        Near 0.0 → object rarely changes → background or inert.
        Between   → object changes selectively → lever or target.
        """
        if self.actions_observed == 0:
            return 0.0
        return self.actions_with_change / self.actions_observed

    # Causal
    causes:                   Tuple[int, ...] = ()
    caused_by:                Tuple[int, ...] = ()
    causal_observation_count: int = 0
    causal_agreement:         float = 0.0
    # WO-EFFECT-LABEL — live/HUD regions (the COUNTER) observed to change on this
    # lever's presses but CONSCIOUSLY DISREGARDED as effects (active labeling, not
    # a silent mask). Accumulated across presses so the lever can be described in
    # full: "drives X; disregards the counter tick Y". Never enters causes.
    disregarded_live_region_ids: Tuple[int, ...] = ()
    # Physics observation (WO-A2c-Core, NR-01 Layer 1). observation_status
    # is the three-state measurer report the captain (A.3) will gate tier-6
    # closure on. rigid_observation_count is the CLEAN count of OBSERVED_RIGID
    # presses — distinct from causal_observation_count, which retains its
    # cross-role display semantics (read by attribution.py for REACTIVE).
    # NOTE (Layer 2 migration): rigid_observation_count is currently polluted
    # by bounce presses in the same way causal_agreement is — Layer 2 (A.4-
    # gated) reclassifies OBSERVED_BOUNDARY and recomputes both. Do not reopen.
    observation_status:       ObservationStatus = ObservationStatus.NOT_OBSERVED
    rigid_observation_count:  int = 0
    # Measured-effect store (WO-EFFECT-STORE-RIGID, WO1). Durable per-lever
    # per-subject-region displacement records. Populated by the accumulator's
    # rigid-press path via record_lever_effect. PERSIST_LIVES_RESET_LEVEL
    # semantics by virtue of LibraryObject lifecycle (accumulates across lives,
    # rebuilt per level). Additive; does not touch causes/causal_agreement.
    lever_effects:            Tuple[LeverEffect, ...] = ()
    # WO-E6 (Per-Lever B3 loop guard). Count of silent (zero-delta) effect-
    # probe presses this lever has absorbed — incremented in the accumulator's
    # ZERO_DELTA_SILENT path for a typed lever (physics_accumulator). Used ONLY
    # as the no-effects default in predicate_evaluators._lever_effort so a
    # genuinely-saturated lever's effort rises with each null re-probe and the
    # least-observed round-robin de-prioritizes it (no loop-forever). Discovery,
    # not composition — counts what was observed (a null press), nothing planned.
    effect_null_presses:      int = 0

    # WO-C3: the lever-keyed conserved-transfer relation, authored from measured
    # deltas at the recording seam (single writer: record_conserved_transfer).
    # None until the relation is licensed (integer-exact conservation AND a
    # passing forward out-prediction). Holds the relation; per-subject
    # lever_effects carry only a membership flag.
    conserved_transfer:       Optional["ConservedTransfer"] = None

    # Counter (COUNTER role only)
    lc_rate:       float = 0.0
    lc_initial:    int = 0
    lc_budget_est: int = -1
    # WO-C5-02: pixel count tracking for rate and budget estimation.
    # initial_cell_count: set once during Mode A spawn from region.area.
    # current_cell_count: updated each Mode B sync from live grid inspection.
    # lc_rate and lc_budget_est are derived from these two fields.
    initial_cell_count: int = 0
    current_cell_count: int = 0
    # WO-E09-v2 D1: bounded per-sync live-count history for the march recognizer.
    # Maintained by the (widened) sync writer for coverage-bounded non-EGO
    # candidates; bounded to _COUNTER_MARCH_WINDOW + 1 counts. Empty for objects
    # outside the candidate domain, so the recognizer self-fences via empty history.
    cell_count_history: Tuple[int, ...] = ()

    # Background recognition (WO-C5-05) — ignore score channels and tag.
    # ignore_score: composite score 0.0–1.0 from four evidence channels.
    # is_background: True when ignore_score >= 0.60 (defeasible: cleared on unexpected change).
    # ignore_channels: compact label of contributing channels (e.g. "zero_change+size+dominant").
    # Objects tagged is_background are excluded from targeting unmapped counts.
    ignore_score:    float = 0.0
    is_background:   bool = False
    ignore_channels: str = ""

    # Tier 3 lever evidence (WO-02) — accumulated from CLICK world probing.
    # lever_confidence: [0.0, 0.95] aggregate confidence that this object is a lever.
    #   Starts at 0.0. First positive observation → 0.60. Each additional → +0.10 (cap 0.95).
    #   Zero deltas do NOT decrement. Evidence accumulates; never overwrites.
    # lever_locality: "LOCAL" | "REMOTE" | None.
    #   LOCAL: probed object's own cells changed (probed object is a lever).
    #   REMOTE: only other objects' cells changed (probed object affects others).
    #   None: not yet probed or inert.
    # lever_effect_cells: set of (row, col) cells that changed on this object
    #   when it was the probed target (LOCAL evidence). Empty if not yet probed.
    # lever_effect_region_ids: list of region_ids affected when this object was probed
    #   (REMOTE evidence — objects that changed as a side effect). Empty if LOCAL or inert.
    # inert_probe_count: count of times probed with zero delta.
    #   Incremented on zero-delta observations. Does NOT trigger reclassification.
    lever_confidence:       float = 0.0
    lever_locality:         Optional[str] = None       # "LOCAL" | "REMOTE" | None
    lever_effect_cells:     Optional[set] = None       # set of (row, col) cells changed
    lever_effect_region_ids: Optional[list] = None     # list of region_ids affected
    inert_probe_count:      int = 0

    # Attribution (WO-01 LEVER-CATALOG) — set by update_attribution() every frame.
    # is_attributed = False: no confirmed cause in library. Tier 4 probe candidate.
    # is_attributed = True:  cause confirmed (EGO/COUNTER/LEVER/REACTIVE+caused_by/STATIC@≥0.90).
    # attribution_evidence: short list of reason strings explaining the attribution.
    is_attributed:        bool = False
    attribution_evidence: List[str] = field(default_factory=list)

    # Probe outcome counters (WO-02 LEVER-CATALOG) — accumulated from Tier 4 probing.
    # probe_confirmation_count: incremented each time a LEVER outcome (any of the three) is recorded.
    #   inert_probe_count already exists above (shared with Tier 3 lever evidence).
    # ambiguous_probe_count: incremented each time an AMBIGUOUS outcome is recorded.
    # lever_locked: True when role became LEVER via probe evidence. Guards against demotion.
    #   When True, _classify_objects will skip this object regardless of other evidence.
    probe_confirmation_count: int = 0
    ambiguous_probe_count:    int = 0
    lever_locked:             bool = False

    # Investigation dossier (Tier 4 per-object summary) — WO-OCD-01
    # Per-object summary fields indexing into SemanticLibrary.probe_event_log
    # for fast ranker/router access. Library-wide probe_event_log remains
    # the canonical append-only event stream; these fields are the index.
    # Sentinels distinguish "never probed" from valid zero-state observations:
    #   last_probe_frame = -1, last_probe_state_hash = "" → never probed.
    # last_probe_state_hash is a hex string (per perception/state_tracker.py
    # compute_state_signature, SHA-256 truncated to 16 hex chars).
    # needs_reinvestigation is declared here; WO-OCD-05 (Evidence Asymmetry
    # Engine) is the write site; WO-OCD-02 (Ranker Upgrade) is the read site.
    last_probe_frame:         int = -1
    last_probe_outcome:       str = ""
    last_probe_state_hash:    str = ""
    probe_count:              int = 0
    needs_reinvestigation:    bool = False

    # WO-OCD-05 (Evidence Asymmetry Engine) — additive belief fields.
    # inert_coverage: count of zero-delta probes under DISTINCT grid-state hashes
    #   (OBJECT_INVESTIGATION_DOCTRINE.md:94 — the binding definition). Maintained
    #   as a bounded distinct-consecutive integer (CE Option-2 ruling): incremented
    #   on a genuine null only when the current hash differs from last_probe_state_hash.
    #   This is the input to inert_confidence = min(0.90, 0.30 + 0.10 * inert_coverage);
    #   distinct-hash counting is the asymmetry — N nulls under one world-state count once.
    # ever_reactive: monotone latch — set True on any positive/causal outcome, never
    #   cleared by a later null (the demotion guard: a confirmed responder is never
    #   pushed toward inert). Ported from v3.5 evidence_accumulator.ever_reactive.
    inert_coverage:           int = 0
    ever_reactive:            bool = False

    # Per-action attempt tracking (WO-OCD-FLAGS-CLICK)
    # Keyed by integer action ID. Absent key = action never attempted on this
    # object. Present with True = attempted at least once via deliberate probe.
    # Set at the action emitter site (strategy/tier4_click.py and the Tier 3
    # CLICK branch of strategy/action_selector.py), not at observation time.
    # Field card displays one slot per action ID in library.sdk_actions; the
    # dict stays sparse (only attempted action IDs are stored).
    actions_attempted:        Dict[int, bool] = field(default_factory=dict)

    # ----- WO-BLUEPRINT-04: BBA Layer One log-scores (INVENT #2 staging) -----
    # Per Blueprint Section 2.6.1 — six per-axis log-scores stored on each
    # Slot. Read via sigmoid_confidence(category) at prerequisite-evaluation
    # time. Written by BBA Layer One (Sub-Phase 3 / WO-BLUEPRINT-08); for this
    # WO they exist as fields with default value 0.0 (sigmoid-read 0.5 = no
    # evidence either way).
    #
    # Per Section 2.6.4 world-type gates:
    #   ego_log_score is pinned at -inf in CLICK/GLOBAL worlds (the substrate
    #   sets it when world_type is confirmed; not enforced at LibraryObject
    #   construction).
    #
    # Persistence tier per Section 2.10: PERSIST_LIVES_AND_LEVELS.
    static_log_score:    float = 0.0
    reactive_log_score:  float = 0.0
    ego_log_score:       float = 0.0
    counter_log_score:   float = 0.0
    lever_log_score:     float = 0.0
    # DD gap-5: gate_log_score retired — gate is a lever-subtree frontier child,
    # not a floor axis (it never received evidence). See _LOG_SCORE_CATEGORIES.

    # ----- WO-BLUEPRINT-04: Class-change revocation tracking field -----
    # Per Blueprint Section 1.7 (class-change revocation) and Section 2.4.6
    # (LibraryDerivedState — but the previous_class_signature lives on the
    # Slot for per-Slot tracking, not on LibraryDerivedState).
    #
    # Substrate hygiene (library/library_sync.py revoke_on_class_change hook)
    # compares the Slot's currently-observed class signature against this
    # tracked value. When changed: revoke all six log-scores to 0.0 and
    # update this field.
    #
    # None on first observation (sentinel). Substrate initializes during
    # Mode A spawn.
    #
    # Persistence tier per Section 2.10: PER_LIFE_SCRATCHPAD (resets on life
    # retry so a fresh life re-observes class signatures).
    previous_class_signature: Optional[int] = None

    # ----- WO-BLUEPRINT-04: BBA Layer One sigmoid-read accessor -----

    def sigmoid_confidence(self, category: str) -> float:
        """Read a category's BBA-Layer-One sigmoid confidence.

        Per Blueprint Section 2.6.3:

            confidence = sigmoid(log_score) bounded by cap (0.98) and
            floor (0.02) for non-falsified axes.

        Args:
            category: One of "static", "reactive", "ego", "counter",
                      "lever".

        Returns:
            Sigmoid-read confidence in [0.02, 0.98]. Log-scores of -inf
            (hard falsification per Section 2.6.3, e.g. INERT axis after
            observed change) return 0.0 (sentinel below the floor).
            Log-scores of +inf return 1.0 (sentinel above the cap).

        Raises:
            ValueError: if `category` is not a recognized log-score axis.
        """
        if category not in _LOG_SCORE_CATEGORIES:
            raise ValueError(
                f"sigmoid_confidence: category must be one of "
                f"{_LOG_SCORE_CATEGORIES}; got {category!r}"
            )
        log_score = getattr(self, f"{category}_log_score")
        # Hard falsification sentinels per Section 2.6.3:
        if log_score == float("-inf"):
            return 0.0
        if log_score == float("inf"):
            return 1.0
        # Standard sigmoid clamped to cap/floor:
        raw = 1.0 / (1.0 + math.exp(-log_score))
        return max(_SIGMOID_FLOOR, min(_SIGMOID_CAP, raw))


# ---------------------------------------------------------------------------
# SDKAction
# ---------------------------------------------------------------------------

@dataclass
class SDKAction:
    """One SDK-level action row. Keyed by action_id (integer).

    Schema legacy (pre WO-LGTD-02): action_id, status, delta_cells,
    affected_regions, notes, test_count. The `status` string field
    ("UNTESTED" / "LIVE" / "DEAD" / "NOOP") is preserved for backward
    compatibility with world_type_classifier.py and library_sync.py
    readers. Migration to the typed OperationalBelief enum is staged for
    WO-LGTD-02 Phase 4 (write) and a follow-on WO (reader migration).

    Schema extension (WO-LGTD-02 Phase 1, May 28, 2026): the Affordance
    Layer's Entry A belief structure per Library Blueprint Section 5.2.1.
    Five new fields:
      action_name           — canonical name from ACTION_NAME_MAP
      semantic_role         — canonical role from SEMANTIC_ROLE_MAP
      declarative_belief    — DECLARED / ABSENT, refreshes per frame
      operational_belief    — UNTESTED / INERT / EFFECTIVE_* (four-state)
      operational_confidence — sigmoid-style axis [0.0, 1.0]

    See library/affordance_belief.py for the enum definitions and maps.
    Phase 1 defaults the new fields; substrate writes happen in Phase 4.
    """
    action_id:        int
    status:           str = "UNTESTED"   # UNTESTED, LIVE, DEAD, NOOP
    delta_cells:      int = 0
    affected_regions: Tuple[int, ...] = ()
    notes:            str = ""
    test_count:       int = 0
    # ----- WO-LGTD-02 Phase 1: Affordance Layer Entry A extension -----
    action_name:            str = ""
    semantic_role:          str = ""
    declarative_belief:     "DeclarativeBelief" = field(  # type: ignore[name-defined]
        default_factory=lambda: _default_declarative_belief()
    )
    operational_belief:     "OperationalBelief" = field(  # type: ignore[name-defined]
        default_factory=lambda: _default_operational_belief()
    )
    operational_confidence: float = 0.0


# Deferred default factories — avoid module-level import cycles.
# affordance_belief is stdlib-only and never imports from semantic_library;
# we defer the import to call time as a defensive pattern matching the
# inline-import style used elsewhere in this module.
def _default_declarative_belief():
    from virelai_v4.library.affordance_belief import DeclarativeBelief
    return DeclarativeBelief.ABSENT


def _default_operational_belief():
    from virelai_v4.library.affordance_belief import OperationalBelief
    return OperationalBelief.UNTESTED


# ---------------------------------------------------------------------------
# LeverAction
# ---------------------------------------------------------------------------

@dataclass
class LeverAction:
    """One lever-level action row. Keyed by region_id."""
    region_id:        int
    parent_action_id: int
    verb:             str = ""
    delta_cells:      int = 0
    affected_regions: Tuple[int, ...] = ()
    effect_locality:  str = ""
    direction_label:  str = ""
    confidence:       float = 0.0
    evidence_count:   int = 0


# ---------------------------------------------------------------------------
# LibraryExploration
# ---------------------------------------------------------------------------

@dataclass
class LibraryExploration:
    """Single row updated after every step."""
    unique_states:        int   = 0
    repeated_states:      int   = 0
    efficiency:           float = 1.0
    consecutive_repeated: int   = 0
    actions_monitored:    int   = 0


# ---------------------------------------------------------------------------
# Role transition graph (contract-authoritative)
# ---------------------------------------------------------------------------

_VALID_TRANSITIONS: Dict[LibraryRole, Set[LibraryRole]] = {
    LibraryRole.UNKNOWN:  {
        LibraryRole.EGO, LibraryRole.COUNTER, LibraryRole.LEVER,
        LibraryRole.REACTIVE, LibraryRole.TARGET, LibraryRole.SIGNAL, LibraryRole.STATIC,
    },
    LibraryRole.STATIC:   {LibraryRole.TARGET, LibraryRole.LEVER, LibraryRole.REACTIVE},
    LibraryRole.REACTIVE: {
        LibraryRole.REACTIVE,   # confidence update, more observations
        LibraryRole.LEVER,      # Tier 4, future campaign — causal direction established
        LibraryRole.TARGET,     # Tier 4, future campaign — object is an effect target
        LibraryRole.EGO,        # WO-RM-03: partition from active population (displacement coherence)
        LibraryRole.COUNTER,    # WO-RM-04-FIX-2: life counter misclassified REACTIVE before
                                # actions_observed reaches _COUNTER_MIN_OBSERVATIONS (Pre-B fires
                                # at active_frame_count=2; Rule A needs obs>=5). Once obs>=5,
                                # Rule A must be able to promote REACTIVE → COUNTER.
        # REACTIVE → STATIC is intentionally ABSENT: observed activity is permanent evidence
    },
    LibraryRole.TARGET:   {LibraryRole.LEVER},
    LibraryRole.LEVER:    {LibraryRole.STATIC, LibraryRole.EGO},  # WO-04: LEVER→EGO legal
    LibraryRole.SIGNAL:   {LibraryRole.TARGET, LibraryRole.LEVER, LibraryRole.REACTIVE},
    LibraryRole.EGO:      set(),
    LibraryRole.COUNTER:  set(),
}


# ---------------------------------------------------------------------------
# SemanticLibrary
# ---------------------------------------------------------------------------

@dataclass
class SemanticLibrary:
    """The single mutable artifact consolidating all solver knowledge.

    Holds four sections: header, objects, sdk_actions, lever_actions, exploration.
    Provides typed update methods and query helpers. Persists via Groundhog Day.
    """
    header:        LibraryHeader
    objects:       Dict[int, LibraryObject]
    sdk_actions:   Dict[int, SDKAction]
    lever_actions: Dict[int, LeverAction]
    exploration:   LibraryExploration

    # probe_event_log: append-only log of probe outcome events (WO-02 LEVER-CATALOG).
    # Each entry is a dict with keys: frame, region_id, outcome, notes.
    # Persists across lives (Groundhog Day). Accumulates evidence for assessor (WO-06).
    probe_event_log: List[Dict] = field(default_factory=list)

    # ── OBJECTS ──────────────────────────────────────────────────────────

    def add_object(self, obj: LibraryObject) -> None:
        """Add one LibraryObject row keyed by its region_id.

        WO-B2-03: the key is region_id — a PER-LEVEL SPAWN LABEL, not an earned
        identity (AMENDMENT_RULING_LIB1 §2). The roster is single-node-born (this
        is its only key-write, fed only by the single-frame spawn/rebuild scan),
        so the label's order IS the birth order within the level; the two are
        identical by construction. The key becomes the worldline only at layer 3,
        when the incremental engine feeds this method from threaded worldlines
        (populate-from-weave, parked). Until then: a label, honestly named."""
        self.objects[obj.region_id] = obj

    def update_object_role(
        self,
        region_id: int,
        role: LibraryRole,
        confidence: Optional[float] = None,
    ) -> None:
        """Update role classification with transition validation.

        Raises:
            KeyError:   region_id not in objects.
            ValueError: transition not permitted by the role graph.
        """
        obj = self.objects[region_id]   # raises KeyError if absent
        current = obj.role
        if current == role:
            if confidence is not None:
                obj.confidence = confidence
            return
        allowed = _VALID_TRANSITIONS.get(current, set())
        if role not in allowed:
            raise ValueError(
                f"Role transition {current.value} → {role.value} blocked "
                f"for region {region_id}. Allowed from {current.value}: "
                f"{[r.value for r in sorted(allowed, key=lambda x: x.value)]}"
            )
        obj.role = role
        if confidence is not None:
            obj.confidence = confidence

    def update_object_behavior(
        self,
        region_id: int,
        change_count: Optional[int] = None,
        reacts_to: Optional[Tuple[int, ...]] = None,
        reaction_type: Optional[str] = None,
        cycle_length: Optional[int] = None,
        direction_label: Optional[str] = None,
        causes: Optional[Tuple[int, ...]] = None,
        caused_by: Optional[Tuple[int, ...]] = None,
        saturated: Optional[bool] = None,
        flash_count: Optional[int] = None,
        transition_count: Optional[int] = None,
        causal_observation_count: Optional[int] = None,
        causal_agreement: Optional[float] = None,
    ) -> None:
        """Incremental behavioral update. Tuple fields merge (dedup, sorted)."""
        obj = self.objects.get(region_id)
        if obj is None:
            return
        if change_count is not None:
            obj.change_count = change_count
        if flash_count is not None:
            obj.flash_count = flash_count
        if transition_count is not None:
            obj.transition_count = transition_count
        if reacts_to is not None:
            obj.reacts_to = tuple(sorted(set(obj.reacts_to) | set(reacts_to)))
        if reaction_type is not None:
            obj.reaction_type = reaction_type
        if cycle_length is not None:
            obj.cycle_length = cycle_length
        if direction_label is not None:
            obj.direction_label = direction_label
        if causes is not None:
            obj.causes = tuple(sorted(set(obj.causes) | set(causes)))
        if caused_by is not None:
            obj.caused_by = tuple(sorted(set(obj.caused_by) | set(caused_by)))
        if saturated is not None:
            obj.saturated = saturated
        if causal_observation_count is not None:
            obj.causal_observation_count = causal_observation_count
        if causal_agreement is not None:
            obj.causal_agreement = causal_agreement

    def record_lever_effect(
        self,
        lever_rid: int,
        subject_region_id: int,
        vector: Optional[Tuple[float, float]] = None,
        operation_kind: str = "RIGID",
        cell_count_delta: Optional[int] = None,
    ) -> None:
        """Append or merge a LeverEffect on the lever's library object
        (WO-EFFECT-STORE-RIGID, WO1; WO3 non-rigid extension). Idempotent on
        (subject_region_id, operation_kind): a repeated observation increments
        observation_count and updates the measured fields (last-wins). RIGID
        effects carry `vector`; NON_RIGID effects carry `cell_count_delta`
        (WO3). No-op when the region is absent or not a LEVER. Additive — does
        not touch causes / causal_agreement / causal_observation_count."""
        obj = self.objects.get(lever_rid)
        if obj is None or obj.role != LibraryRole.LEVER:
            return
        new_effects: List[LeverEffect] = []
        merged = False
        for effect in obj.lever_effects:
            if (effect.subject_region_id == subject_region_id
                    and effect.operation_kind == operation_kind):
                new_effects.append(replace(
                    effect,
                    observation_count=effect.observation_count + 1,
                    vector=vector,
                    cell_count_delta=cell_count_delta,
                ))
                merged = True
            else:
                new_effects.append(effect)
        if not merged:
            new_effects.append(LeverEffect(
                subject_region_id=subject_region_id,
                vector=vector,
                observation_count=1,
                operation_kind=operation_kind,
                cell_count_delta=cell_count_delta,
            ))
        obj.lever_effects = tuple(new_effects)

    def record_conserved_transfer(
        self, lever_rid: int, transfer: ConservedTransfer,
    ) -> None:
        """Store a licensed ConservedTransfer on its lever and flip the
        membership flag on the participating per-subject effects (WO-C3 §4,
        Fold 4 single-writer). The Substrate is the ONLY writer of this belief;
        the accumulator authors/licenses (read-only) and calls here. No-op when
        the region is absent or not a LEVER. The relation lives here; the
        member entries gain a reference (membership), never the relation."""
        obj = self.objects.get(lever_rid)
        if obj is None or obj.role != LibraryRole.LEVER:
            return
        obj.conserved_transfer = transfer
        members = set(transfer.member_subject_ids)
        obj.lever_effects = tuple(
            replace(e, conserved_transfer_member=True)
            if e.subject_region_id in members else e
            for e in obj.lever_effects
        )

    def update_object_lc(
        self, region_id: int, lc_rate: float, lc_initial: int, lc_budget_est: int = -1,
    ) -> None:
        """Set life counter fields. Valid for COUNTER-role objects only."""
        obj = self.objects.get(region_id)
        if obj is None:
            return
        obj.lc_rate = lc_rate
        obj.lc_initial = lc_initial
        obj.lc_budget_est = lc_budget_est

    # ── QUERIES ───────────────────────────────────────────────────────────

    def objects_by_role(self, role: LibraryRole) -> List[LibraryObject]:
        """All objects with the given role."""
        return [o for o in self.objects.values() if o.role == role]

    def unknown_objects(self) -> List[LibraryObject]:
        """All UNKNOWN-role objects. Sorted by cell_count ascending (smallest first — Law 9).
        Zone is not a classification input (WO-06a: evidence-first architecture)."""
        result = [o for o in self.objects.values() if o.role == LibraryRole.UNKNOWN]
        result.sort(key=lambda o: o.cell_count)
        return result

    def levers(self) -> List[LibraryObject]:
        return self.objects_by_role(LibraryRole.LEVER)

    def reactives(self) -> List[LibraryObject]:
        return self.objects_by_role(LibraryRole.REACTIVE)

    def targets(self) -> List[LibraryObject]:
        return self.objects_by_role(LibraryRole.TARGET)

    def ego_object(self) -> Optional[LibraryObject]:
        egos = self.objects_by_role(LibraryRole.EGO)
        return egos[0] if egos else None

    def counter_object(self) -> Optional[LibraryObject]:
        counters = self.objects_by_role(LibraryRole.COUNTER)
        return counters[0] if counters else None

    def object_count(self) -> int:
        return len(self.objects)

    def unknown_count(self) -> int:
        return sum(1 for o in self.objects.values() if o.role == LibraryRole.UNKNOWN)

    def coverage(self) -> float:
        total = self.object_count()
        return 1.0 if total == 0 else (total - self.unknown_count()) / total

    # ── EXPLORATION ───────────────────────────────────────────────────────

    def record_state(self, is_novel: bool) -> None:
        """Record a state observation. Recomputes efficiency."""
        exp = self.exploration
        if is_novel:
            exp.unique_states += 1
            exp.consecutive_repeated = 0
        else:
            exp.repeated_states += 1
            exp.consecutive_repeated += 1
        total = exp.unique_states + exp.repeated_states
        exp.efficiency = exp.unique_states / total if total > 0 else 1.0
        exp.actions_monitored += 1

    # ── AFFORDANCE LAYER ENTRY A SUBSTRATE WRITES (WO-LGTD-02 Phase 4) ───

    def refresh_affordance_declarative_belief(
        self,
        available_actions: List[int],
    ) -> None:
        """Substrate write of Entry A declarative belief per Section 5.3.

        For each action_id in available_actions:
          - Ensure an SDKAction entry exists (create if absent).
          - Mark declarative_belief = DECLARED.
          - Populate action_name and semantic_role on first declaration
            from ACTION_NAME_MAP / SEMANTIC_ROLE_MAP.

        For each existing SDKAction not in available_actions:
          - Mark declarative_belief = ABSENT.

        Called every frame from library_sync.sync_library. Refresh is
        platform-authoritative — the platform's declaration this frame
        overwrites any prior belief.
        """
        from virelai_v4.library.affordance_belief import (
            ACTION_NAME_MAP,
            DeclarativeBelief,
            SEMANTIC_ROLE_MAP,
        )
        declared_set = set(available_actions)
        # Mark DECLARED + populate names on first declaration; create
        # missing SDKActions for newly-declared ids.
        for action_id in declared_set:
            sdk_action = self.sdk_actions.get(action_id)
            if sdk_action is None:
                sdk_action = SDKAction(action_id=action_id)
                self.sdk_actions[action_id] = sdk_action
            sdk_action.declarative_belief = DeclarativeBelief.DECLARED
            if not sdk_action.action_name:
                sdk_action.action_name = ACTION_NAME_MAP.get(
                    action_id, f"ACTION{action_id}"
                )
            if not sdk_action.semantic_role:
                sdk_action.semantic_role = SEMANTIC_ROLE_MAP.get(action_id, "")
        # Mark ABSENT for prior-declared actions not in this frame
        for action_id, sdk_action in self.sdk_actions.items():
            if action_id not in declared_set:
                sdk_action.declarative_belief = DeclarativeBelief.ABSENT

    def update_operational_belief_after_outcome(
        self,
        action_id: int,
        status: str,
        delta_cells: int,
    ) -> None:
        """Write Entry A operational belief per Section 5.3 after probe outcome.

        v1.0 four-state collapse: INERT subsumes ACKNOWLEDGED_INERT and
        ZERO_DELTA_SILENT until v1.1 amendment specifies the
        cosmetic-vs-causal distinction.

        Status interpretation:
          - "LIVE" with delta_cells > 0 → effective outcome.
            First effective attempt: EFFECTIVE_UNCONDITIONAL (no prior
            inconsistency).
            Subsequent effective: stays EFFECTIVE_UNCONDITIONAL if prior
            was UNCONDITIONAL; downgrades to CONDITIONAL if prior was
            INERT (the action is effective some-of-the-time).
          - "NOOP" or zero-delta outcome → INERT (collapsed). Confidence
            decrements.
          - Other statuses ("UNTESTED", "DEAD") leave operational_belief
            unchanged.

        Confidence update (sigmoid-style approximation per WO Section 4.3.2):
          - Effective: confidence increments by 0.2, capped at 1.0.
          - Inert:     confidence decrements by 0.1, floored at 0.0.

        Called from delta_updater._update_from_delta alongside the legacy
        status write. The legacy status field is preserved for backward
        compatibility with world_type_classifier and library_sync readers.
        """
        from virelai_v4.library.affordance_belief import OperationalBelief
        sdk_action = self.sdk_actions.get(action_id)
        if sdk_action is None:
            return
        prior = sdk_action.operational_belief
        if status == "LIVE" and delta_cells > 0:
            if prior == OperationalBelief.INERT:
                # Was inert, now effective — clearly conditional
                sdk_action.operational_belief = (
                    OperationalBelief.EFFECTIVE_CONDITIONAL
                )
            elif prior == OperationalBelief.EFFECTIVE_CONDITIONAL:
                # Stay conditional; the inconsistency stands
                sdk_action.operational_belief = (
                    OperationalBelief.EFFECTIVE_CONDITIONAL
                )
            else:
                # UNTESTED or already UNCONDITIONAL — UNCONDITIONAL stands
                sdk_action.operational_belief = (
                    OperationalBelief.EFFECTIVE_UNCONDITIONAL
                )
            sdk_action.operational_confidence = min(
                1.0, sdk_action.operational_confidence + 0.2
            )
        elif status == "NOOP" or (status == "LIVE" and delta_cells == 0):
            sdk_action.operational_belief = OperationalBelief.INERT
            sdk_action.operational_confidence = max(
                0.0, sdk_action.operational_confidence - 0.1
            )
        # else: UNTESTED, DEAD, or unknown status — no Entry A update

    def reset_sdk_actions_for_new_level(self) -> None:
        """Reset per-level SDKAction operational evidence at level advance.

        Per WO-LGTD-02 Phase 4 + Section 5.5: operational_belief is
        PERSIST_LIVES_RESET_LEVEL — resets at level advance, survives
        life retry. SemanticLibrary identity persists (whole-field tier
        PERSIST_LIVES_AND_LEVELS at context.py:437); only operational
        fields are zeroed.

        Fields reset:
          - operational_belief → UNTESTED
          - operational_confidence → 0.0
          - declarative_belief → ABSENT (refreshed on first frame of
            new level by the substrate write)

        Fields preserved (legacy, PERSIST_LIVES_AND_LEVELS):
          - status, test_count, delta_cells, notes, affected_regions
          - action_name, semantic_role (derived from action_id; stable)

        Called from VirelaiContext.reset_for_new_level() following the
        NavAtlas precedent at context.py:583-587 and the WO-LGTD-01
        reset_objects_for_new_level precedent.
        """
        from virelai_v4.library.affordance_belief import (
            DeclarativeBelief,
            OperationalBelief,
        )
        for sdk_action in self.sdk_actions.values():
            sdk_action.operational_belief = OperationalBelief.UNTESTED
            sdk_action.operational_confidence = 0.0
            sdk_action.declarative_belief = DeclarativeBelief.ABSENT

    # ── AFFORDANCE LAYER ENTRY C (WO-LGTD-02 Phase 3) ────────────────────

    def available_probes(self) -> Tuple:
        """Compute the Available Probes view per Library Blueprint Section 5.2.3.

        Returns a tuple of AvailableProbe instances — the subset of
        PROBE_CATALOG whose:
          1. required_actions are all DECLARED in self.sdk_actions, AND
          2. operational_preconditions all evaluate True against current
             library state.

        Library-locus per Structural Law 5. Recomputed each call; not
        persisted. Read-only: no library state mutation.

        Phase 3 (WO-LGTD-02): method introduced; not yet consumed by
        captain or legacy ladder. Phase 4 wires the consumers.
        """
        # Inline imports to avoid top-level circular dependency (catalog
        # references SemanticLibrary in TYPE_CHECKING).
        from virelai_v4.library.affordance_belief import DeclarativeBelief
        from virelai_v4.library.probe_catalog import (
            AvailableProbe,
            PROBE_CATALOG,
            compute_operational_state,
            compute_target_list,
        )
        from virelai_v4.library.probe_preconditions import evaluate_precondition

        available: List = []
        for probe_decl in PROBE_CATALOG:
            # Check 1: all required actions are present and DECLARED
            actions_satisfied = True
            for action_id in probe_decl.required_actions:
                sdk_action = self.sdk_actions.get(action_id)
                if (
                    sdk_action is None
                    or sdk_action.declarative_belief != DeclarativeBelief.DECLARED
                ):
                    actions_satisfied = False
                    break
            if not actions_satisfied:
                continue

            # Check 2: all operational preconditions hold
            preconditions_satisfied = all(
                evaluate_precondition(name, self)
                for name in probe_decl.operational_preconditions
            )
            if not preconditions_satisfied:
                continue

            # Probe is available; compute derived view fields
            target_list = compute_target_list(probe_decl, self)
            operational_state = compute_operational_state(probe_decl, self)
            available.append(
                AvailableProbe(
                    probe_name=probe_decl.probe_name,
                    discovery_type=probe_decl.discovery_type,
                    target_list=target_list,
                    operational_state=operational_state,
                )
            )
        return tuple(available)

    # ── PER-LEVEL OPERATIONAL EVIDENCE RESET (WO-LGTD-01) ────────────────

    def reset_objects_for_new_level(self) -> None:
        """Reset per-object operational-evidence fields at level advance.

        Per WO-LGTD-01 (Library-Grounded Tool Dispatch Campaign), eight
        per-object operational-evidence fields are operationally per-level.
        SemanticLibrary identity persists across level advance (whole-field
        tier remains PERSIST_LIVES_AND_LEVELS at context.py:437); only the
        eight per-object evidence fields are zeroed.

        GAP-7 hazard closed: region_ids regenerate per level via GridScan
        rebuild. Evidence keyed on region_id and carried across a level
        boundary is evidence about a region that may no longer denote the
        same object. The classifier (role_classifier.py:294-302 Rule A
        COUNTER), the ignore_score rule (ignore_score.py:127-133), the
        REACTIVE Pre-B rule (role_classifier.py:327-333), and the
        counter_stats.lc_rate denominator (counter_stats.py:40-42) all
        treat carried evidence as identical to fresh evidence with no
        mechanism to distinguish.

        Fields zeroed (the WO-LGTD-01 eight):
          - lever_confidence (semantic_library.py:203)
          - probe_count (semantic_library.py:239)
          - probe_confirmation_count (semantic_library.py:222)
          - inert_probe_count (semantic_library.py:207)
          - ambiguous_probe_count (semantic_library.py:223)
          - actions_observed (semantic_library.py:147)
          - actions_with_change (semantic_library.py:148)
          - active_frame_count (semantic_library.py:139)

        Intentionally NOT touched by this reset:
          - role and confidence (classification persists; re-derived from
            fresh evidence by the next sync_library pass).
          - lever_locked (the demotion guard; PERSIST_LIVES_AND_LEVELS).
          - causes / caused_by (causal map; survives per Blueprint Section 4).
          - is_active, first_active_frame, last_active_frame (factual
            observation record; monotone per WO-RM-02).
          - The six BBA Layer One log-scores (revoked on class-change per
            Blueprint Section 1.7, not at level advance).
          - All identity, behavior, and counter fields not on the eight-list.

        Called from VirelaiContext.reset_for_new_level() following the
        NavAtlas precedent at context.py:583-587 — whole-field tier
        PERSIST_LIVES_AND_LEVELS plus an explicit granular reset call.
        """
        for obj in self.objects.values():
            obj.lever_confidence = 0.0
            obj.probe_count = 0
            obj.probe_confirmation_count = 0
            obj.inert_probe_count = 0
            obj.ambiguous_probe_count = 0
            obj.actions_observed = 0
            obj.actions_with_change = 0
            obj.active_frame_count = 0

    # ── HEADER HELPERS ────────────────────────────────────────────────────

    def record_action(self) -> None:
        self.header.actions_taken += 1
        if self.header.actions_remaining > 0:
            self.header.actions_remaining -= 1

    def set_world_type(self, world_type: str) -> None:
        self.header.world_type = world_type

    def set_ego(self, ego_mode: str, nav_stride: Optional[int] = None) -> None:
        self.header.ego_mode = ego_mode
        if nav_stride is not None:
            self.header.nav_stride = nav_stride

    # ── FIELD CARD RENDER (WO-05) ─────────────────────────────────────────

    def render(self) -> str:
        """Full field card rendering — delegates to field_card.py (WO-05)."""
        from virelai_v4.library.field_card import render_field_card
        return render_field_card(self)

    # ── SERIALIZATION (helpers in library_serializer.py) ──────────────────

    def to_dict(self) -> dict:
        """Full serialization for Groundhog Day persistence."""
        from virelai_v4.library.library_serializer import (
            exploration_to_dict, header_to_dict, lever_action_to_dict,
            object_to_dict, sdk_action_to_dict,
        )
        return {
            "header":        header_to_dict(self.header),
            "objects":       {str(rid): object_to_dict(o) for rid, o in self.objects.items()},
            "sdk_actions":   {str(aid): sdk_action_to_dict(a) for aid, a in self.sdk_actions.items()},
            "lever_actions": {str(rid): lever_action_to_dict(la) for rid, la in self.lever_actions.items()},
            "exploration":   exploration_to_dict(self.exploration),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "SemanticLibrary":
        """Reconstruct from persisted dict."""
        from virelai_v4.library.library_serializer import (
            exploration_from_dict, header_from_dict, lever_action_from_dict,
            object_from_dict, sdk_action_from_dict,
        )
        return cls(
            header=header_from_dict(d["header"]),
            objects={int(rid): object_from_dict(od) for rid, od in d["objects"].items()},
            sdk_actions={int(aid): sdk_action_from_dict(ad) for aid, ad in d.get("sdk_actions", {}).items()},
            lever_actions={int(rid): lever_action_from_dict(ld) for rid, ld in d.get("lever_actions", {}).items()},
            exploration=exploration_from_dict(d["exploration"]),
        )


__all__ = [
    "LibraryHeader",
    "LibraryObject",
    "SDKAction",
    "LeverAction",
    "LibraryExploration",
    "SemanticLibrary",
]
