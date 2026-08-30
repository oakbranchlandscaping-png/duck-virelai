"""
virelai_v4/diagnostics/render_stages.py — WO-1.1 universal render-stages runner.

A universal, READ-ONLY live runner. Given a game id at invocation, it drives
ONE episode through the EXISTING harness run entry and prints the WO-1 v2
three-stage lens — render_all(context, grid).to_text() — per frame, out of
band.

Usage (the working, stranger-runnable invocation — WO-D3 Fix A):

  uv run python -m virelai_v4.diagnostics.render_stages --game <id> \
      [--dossier | --dossier-final] [--final-only] [--max-frames N] \
      [--at i,j,k] [--axiom-key PATH] [--effect-model-key PATH] [--detail SPEC]

  --dossier        render the world-dossier overview PER FRAME (stage debug).
  --dossier-final  render the dossier ONCE, from the final belief state, after
                   the run (the single gradeable artifact — WO-D3 Fix B).
  --final-only     suppress the per-frame three-stage lens; the run drives
                   silently and (with --dossier-final) prints only the final
                   dossier (WO-FINAL-ONLY — the clean canary).

(The bare `python virelai_v4/diagnostics/render_stages.py …` form does not
resolve the package on the Mac path; use the `uv run python -m …` form above.)

Design (Mine-Then-Reuse; nothing here reimplements game-driving):
  - RenderObserverMixin overrides choose_action to call super().choose_action(
    ...) UNCHANGED, then render the three stages AFTER the decision. The action
    is returned verbatim; the render reads context + grid and mutates nothing.
    An observer exception is swallowed (printed, non-fatal) so the instrument
    can never perturb the run — read-only w.r.t. belief, dispatch, and timing.
  - The mixin is bound onto the production Virelai agent ONLY at live-run time
    (type(RenderObserverMixin, Virelai)). Virelai imports the live ARC SDK
    (arcengine), which is absent in the sandbox; keeping the mixin SDK-free
    lets this module and its tests import and run in the sandbox. super() in
    the mixin resolves to Virelai.choose_action via MRO at live time.
  - The CLI registers the bound agent into AVAILABLE_AGENTS and delegates to
    the harness's own entry (main.main() -> Agent.main()). The harness does all
    driving, scorecard, and API work exactly as for any canary.

Firewall: there is NO game-name literal anywhere in this module. The game is
read solely from --game and forwarded to the harness. The runner is pure
machinery; the game id is supplied content.

Scope (WO-1.1): render only. No grading, no oracle, no fixture injection, no
fault localization, no per-game branch. It edits neither the harness nor
per_stage_render.py — it imports and calls.

NOTE: the live drive requires the ARC API (network + ARC_API_KEY) and is the
Director's to run (§4b). Cowork's sandbox validates imports, arg-parse, and
the read-only observe hook on a constructed context over a fake base.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Optional, Sequence, Set

import numpy as np

from virelai_v4.diagnostics.per_stage_render import render_all
from virelai_v4.diagnostics.perception_oracle import (
    load_oracle_frames,
    render_perception_graded,
)
from virelai_v4.diagnostics.downstream_fidelity import render_downstream_fidelity
from virelai_v4.diagnostics.dossier import (
    build_dossier,
    render_overview,
    load_axiom_key,
    load_effect_model_key,
    render_detail,
)


# ---------------------------------------------------------------------------
# Lazy SDK indirection (only resolved at live-run time; sandbox never calls it)
# ---------------------------------------------------------------------------

def _get_grid(latest_frame: Any) -> Any:
    """Current grid for the frame, via the agent module's own extractor.

    Imported lazily because virelai_v4.virelai pulls the live ARC SDK, absent
    in the sandbox. Tests monkeypatch this symbol to stay SDK-free.
    """
    from virelai_v4.virelai import _grid_from_frame
    return _grid_from_frame(latest_frame)


# ---------------------------------------------------------------------------
# The read-only observer (SDK-free; mixed into Virelai at live-run time)
# ---------------------------------------------------------------------------

class RenderObserverMixin:
    """Adds a post-decision three-stage render to whatever agent it is mixed
    into. Behaviorally identical to the base agent: choose_action delegates to
    super() and returns its action verbatim; the render runs AFTER and writes
    no state. Any observer error is non-fatal (the run must never be perturbed
    by the lens).

    Render bounds (class-level, set by the CLI before the harness builds the
    agent, since the harness — not this module — constructs it):
      _render_max_frames : render only frames with index < N (None = all)
      _render_at         : render only these frame indices (None = all)
    """

    _render_max_frames: Optional[int] = None
    _render_at: Optional[Set[int]] = None
    _oracle_frames: Optional[list] = None   # official replay grids (read-only key)
    _dossier: bool = False                   # --dossier overview (rung 0), per-frame
    _dossier_final: bool = False             # --dossier-final: render once post-loop
    _dossier_rendered: bool = False          # WO-REFORMAT D4: render-once guard
    _final_only: bool = False                # WO-FINAL-ONLY: suppress per-frame lens
    _axiom_key: Optional[dict] = None        # external axiom key (read-only)
    _effect_model_key: Optional[dict] = None  # external effect-model key (read-only)
    _details: Optional[list] = None          # --detail render-modes
    _capture_verify: bool = False            # WO-CC-S1-SEAL: --capture-verify seal hook
    _capture_verified: bool = False          # WO-CC-S1-SEAL-FIX: seal render-once latch
    _clay_compile: bool = False              # WO-CC-S2-CLAY: --clay-compile hook
    _clay_compiled: bool = False             # WO-CC-S2-CLAY: clay render-once latch
    _weave_w0: bool = False                  # WO_WEAVE_W0: --weave-w0 still-bridge hook
    _weave_w0_done: bool = False             # WO_WEAVE_W0: feed-once latch
    _weave_hash: bool = False                # WO_HASH_A: --weave-hash render hook
    _weave_hash_done: bool = False           # WO_HASH_A: render-once latch
    _acted_on_rendered: bool = False         # WO_ACTED_ON_FINAL_RENDER_HOOK: render-once latch
    _footprint_key: bool = False             # --footprint-key: acted-on t-1 footprint appendix

    @classmethod
    def configure(cls, max_frames: Optional[int] = None,
                  at: Optional[Set[int]] = None,
                  oracle_frames: Optional[list] = None,
                  dossier: bool = False,
                  dossier_final: bool = False,
                  final_only: bool = False,
                  axiom_key: Optional[dict] = None,
                  effect_model_key: Optional[dict] = None,
                  details: Optional[list] = None,
                  capture_verify: bool = False,
                  clay_compile: bool = False,
                  weave_w0: bool = False,
                  weave_hash: bool = False,
                  footprint_key: bool = False) -> None:
        cls._render_max_frames = max_frames
        cls._render_at = at
        cls._oracle_frames = oracle_frames
        cls._dossier = dossier
        cls._dossier_final = dossier_final
        cls._final_only = final_only
        cls._axiom_key = axiom_key
        cls._effect_model_key = effect_model_key
        cls._details = details
        cls._capture_verify = capture_verify
        cls._clay_compile = clay_compile
        cls._weave_w0 = weave_w0
        cls._weave_hash = weave_hash
        cls._footprint_key = footprint_key

    def choose_action(self, frames: Any, latest_frame: Any) -> Any:
        action = super().choose_action(frames, latest_frame)   # UNCHANGED
        try:
            self._render_stage(latest_frame)
        except Exception as exc:  # observer must never perturb the run
            print(f"[render_stages] observer error (non-fatal): {exc!r}")
        if self._capture_verify:
            # WO-CC-S1-SEAL: record the frame HANDED at this node (a deep int
            # copy, aliasing nothing) so the post-loop verify compares the log
            # against what actually arrived, not against itself. Index-aligned
            # with the capture call site (virelai.choose_action) — both run once
            # per entry. Guarded: the seal never perturbs the run.
            try:
                handed = getattr(self, "_handed_frames", None)
                if handed is None:
                    handed = []
                    self._handed_frames = handed
                layers = getattr(latest_frame, "frame", []) or []
                handed.append(
                    [[[int(c) for c in row] for row in layer] for layer in layers]
                )
            except Exception as exc:  # seal capture never perturbs the run
                print(f"[render_stages] capture-verify record error (non-fatal): {exc!r}")
        return action

    # -- observation only; reads, never writes --

    def _obs_index(self) -> int:
        idx = getattr(self, "_render_idx", 0)
        self._render_idx = idx + 1
        return idx

    def _should_render(self, idx: int) -> bool:
        # WO-FINAL-ONLY — suppress the per-frame lens entirely (print-only; the
        # decision path/timing are untouched, and cleanup's --dossier-final
        # render is a separate path, so the final dossier still prints).
        if self._final_only:
            return False
        if self._render_at is not None:
            return idx in self._render_at
        if self._render_max_frames is not None:
            return idx < self._render_max_frames
        return True

    def _render_stage(self, latest_frame: Any) -> None:
        idx = self._obs_index()
        if not self._should_render(idx):
            return
        raw = _get_grid(latest_frame)
        grid = np.asarray(raw) if raw is not None else None
        print(f"\n########## FRAME {idx} — per-stage render ##########")
        if self._dossier:                              # WO-5 rung-0 overview
            print(render_overview(build_dossier(self.ctx),
                                  axiom_key=self._axiom_key))
            for spec in (self._details or []):         # WO-5.1 drill-downs
                print(render_detail(self.ctx, spec, axiom_key=self._axiom_key,
                                    effect_model_key=self._effect_model_key))
        print(render_all(self.ctx, grid).to_text())
        self._render_graded_perception(idx, grid)
        print(render_downstream_fidelity(self.ctx))   # WO-4 rung-1 fidelity

    def _render_graded_perception(self, idx: int, grid: Any) -> None:
        """Append the WO-3 graded-perception triple (intake/delta vs the
        EXTERNAL official oracle; individuation per its boundary).

        P8: graded verdicts require the external official replay. When --oracle
        is absent (or the run runs past the oracle's frames), oracle_cur is None
        and the whole graded panel renders NOT_GRADED — there is NO grade
        against the solver's own grids (the deleted frame-vs-itself fallback).
        Read-only; reuses render_perception_graded."""
        if grid is None:
            return
        oracle = self._oracle_frames
        if oracle is not None and idx < len(oracle):
            oracle_cur = oracle[idx]                  # file[N] ↔ call N
            oracle_prev = oracle[idx - 1] if idx > 0 else None
        else:
            oracle_cur = None                         # P8 → NOT_GRADED (no oracle)
            oracle_prev = None
        print(render_perception_graded(self.ctx, grid, oracle_prev, oracle_cur))

    # -- WO-D3 Fix B: render the dossier ONCE, post-loop, from final belief --

    def cleanup(self, scorecard: Any = None) -> None:
        """Episode-end hook (called by the harness after the dispatch loop,
        agent.py:89). WO-D3 Fix B: when --dossier-final is set, render the
        dossier exactly once here, from the FINAL belief state — the single
        gradeable artifact, instead of the per-frame stack.

        Instrument-only: base teardown runs first (unchanged); the render is
        read-only over belief and any error is non-fatal (the instrument must
        never perturb the run). This changes WHEN/HOW-MANY-TIMES the dossier
        renders, never WHAT it renders (same build_dossier(context) path)."""
        super().cleanup(scorecard)          # base scorecard/recording/logging, unchanged

        # WO-CC-S1-SEAL-FIX: capture round-trip verdict — the Stage-1 seal.
        # Relocated ABOVE the --dossier-final gate below (WO_CC_S1_SEAL_DIAG root
        # cause: co-locating it in the dossier-final tail gated it off on the
        # --final-only --capture-verify seal command). Read-only over
        # ctx.frame_record_log + the observer's _handed_frames. cleanup runs
        # twice (agent.py:89 no-scorecard, then swarm.py:133 with-scorecard); the
        # pure evaluate_seal fires exactly once, only on a COMPLETE, length-
        # matched record, and emits an explicit SKIPPED line if the definitive
        # (scorecard-bearing) call still sees incomplete data — never silent.
        if self._capture_verify and not self._capture_verified:
            try:
                from virelai_v4.capture.verify import evaluate_seal
                decision = evaluate_seal(
                    capture_verify=self._capture_verify,
                    already_verified=self._capture_verified,
                    handed_frames=getattr(self, "_handed_frames", []),
                    log=getattr(self.ctx, "frame_record_log", None),
                    is_final_call=scorecard is not None,
                )
                if decision.output is not None:
                    print(decision.output)
                if decision.latch:
                    self._capture_verified = True
            except Exception as exc:        # the instrument never perturbs the run
                print(f"[render_stages] capture-verify error (non-fatal): {exc!r}")

        # WO-CC-S2-CLAY: offline clay compile — cut every captured node and print
        # three raw views (per-node present list, object master list, node map).
        # The CUT runs here (scan_grid needs scipy, the Mac path); the compilers
        # are the pure clay module. Read-only over the record; latched once
        # (cleanup runs twice); non-fatal — never perturbs the run. No behavior
        # when --clay-compile is absent. Placed above the --dossier-final gate so
        # --final-only --clay-compile prints.
        if self._clay_compile and not self._clay_compiled:
            try:
                import numpy as np
                from virelai_v4.perception.grid_scan import scan_grid
                from virelai_v4.capture.clay import (
                    RegionClay, NodeCut, present_list,
                    master_object_list, node_map,
                    render_master_list, render_node_map, _hash_visible,
                )
                from virelai_v4.capture.ledger import grade_pristine, format_pristine
                from virelai_v4.capture.ledger_build import delivery_of
                log = getattr(self.ctx, "frame_record_log", None)
                n = len(log) if log is not None else 0
                if n == 0:
                    print("\n########## CLAY COMPILE — record empty, nothing to cut ##########")
                else:
                    print(f"\n########## CLAY COMPILE — {n} nodes "
                          "(--clay-compile) ##########")
                    print("\n--- PER-NODE PRESENT LISTS ---")
                    cuts = []
                    # WO-DELIVERY-CLASS-02 · the previous node's settled grid, carried one
                    # iteration. `None` on the first node says a predecessor does not exist.
                    _previous_settled = None
                    for rec in log.records:
                        # WO-ANIMATION-01 · bound once; `[-1]` unmoved. All FOUR production
                        # construction sites carry the delivery or the views desynchronise.
                        _delivered = log.reconstruct(rec.node_index)
                        visible = _delivered[-1]                       # the visible layer
                        grid = np.array(visible, dtype=np.int32)
                        regions = tuple(RegionClay.from_region(r) for r in scan_grid(grid).regions)
                        _n, _cls, _mag = delivery_of(_delivered, _previous_settled)
                        _previous_settled = visible
                        # v3 atom: address on the VISIBLE-grid hash, computed here.
                        cut = NodeCut.from_record(
                            rec, regions,
                            visible_hash=_hash_visible(visible),
                            grid_shape=(int(grid.shape[0]), int(grid.shape[1])),
                            delivery_layers=_n, delivery_class=_cls,
                            delivery_magnitude=_mag,
                        )
                        cuts.append(cut)
                        print(present_list(cut))
                    print("\n--- OBJECT MASTER LIST ---")
                    print(render_master_list(master_object_list(cuts)))
                    print("\n--- NODE / CONFIGURATION MAP ---")
                    print(render_node_map(node_map(cuts)))
                    # rung-0 fidelity gate: the cut is lossless iff every node
                    # round-trips from its sightings to the captured visible grid.
                    print("\n--- SIGHTING-LEDGER PRISTINE ---")
                    print(format_pristine(grade_pristine(cuts, log)))
                self._clay_compiled = True
            except Exception as exc:        # the instrument never perturbs the run
                print(f"[render_stages] clay-compile error (non-fatal): {exc!r}")

        # WO_ACTED_ON_FINAL_RENDER_HOOK: the ACTED-ON block on the final artifact —
        # a third instrument block, mirroring --clay-compile: frame_record_log source,
        # render-once latch, non-fatal fence, Mac-scipy posture. WEAVE-SOURCED ONLY
        # (Director ruling 2026-07-12): renders over the weave ### roster, never Slot.
        # Default-on under --dossier-final (part of the final artifact by definition).
        if self._dossier_final and not self._acted_on_rendered:
            try:
                from virelai_v4.capture.ledger_build import (
                    ledger_from_capture, load_node_actions_from_log,
                )
                from virelai_v4.weave.worldline import weave_window
                from virelai_v4.weave.rejoin import re_join
                from virelai_v4.weave.acted_on_render import render_acted_on_block
                log = getattr(self.ctx, "frame_record_log", None)
                n = len(log) if log is not None else 0
                if n == 0:
                    print("\n########## ACTED-ON — record empty, nothing to resolve ##########")
                else:
                    # FULL framed-node range of the run (no truncated window -> no node
                    # reads out-of-window). scipy cut runs on the Mac path.
                    cuts = ledger_from_capture(log)
                    worldlines = re_join(weave_window(cuts), cuts=cuts)
                    # WO-A2-03 Part 1: the acted-on oracle reads the LOG, not the
                    # sidecar. Both are built from the same `log` — the oracle was
                    # already in scope at the line above, and the sidecar was asked
                    # anyway. The sidecar keys on `frame_index` (== actions_this_life,
                    # PERSIST_LEVELS_RESET_LIFE) while the node array is
                    # PERSIST_LIVES_RESET_LEVEL: no key in the record sits at the
                    # node's lifetime tier. Ruled on the live canary at ecee9d0 —
                    # 1294 of 1322 nodes wrong under BOTH candidate keys, 1222 rows
                    # destroyed by last-write-wins. The log needs no index rule:
                    # entry t IS node t, dense over every action type (R1-02c).
                    node_actions = load_node_actions_from_log(log)
                    print("\n########## ACTED-ON — weave ### roster, resolved against cut[t-1] "
                          "(--dossier-final) ##########")
                    # WO-SPLIT-AND-SHOW-01: capture the PanelRow mapping the acted-on
                    # block already builds, so the verb-stream block below can render each
                    # worldline's action marginal without a second build_coupling call.
                    _panel_sink = {}
                    print(render_acted_on_block(cuts, worldlines, node_actions,
                                                footprint_key=self._footprint_key,
                                                panel_sink=_panel_sink))

                    # WO-VERB-STREAM-01 · rung four made visible on the LIVE path.
                    # The worldlines built above already carry every edge and every
                    # verb; before this hook they were used only for the acted-on
                    # resolution and then discarded, so a live dossier contained zero
                    # occurrences of any verb name while the renderer for them sat
                    # committed and offline-only in dossier/canary_dossier.py.
                    #
                    # `window_edges(cuts)` is a SECOND, independent flattening of the
                    # cascade — deliberately NOT re-derived from the worldlines,
                    # because the census must count the terminating verdicts (DEATH /
                    # AMBIGUOUS) the threader drops and no worldline can carry.
                    # Two populations, never one; see verb_stream_render's docstring.
                    #
                    # Own guard, mirroring the acted-on fence: a render fault here
                    # must never cost the acted-on block that already printed.
                    try:
                        from virelai_v4.weave.worldline import window_edges
                        from virelai_v4.weave.verb_stream_render import (
                            render_verb_stream_block,
                        )
                        _lo = cuts[0].node_index if cuts else 0
                        _hi = cuts[-1].node_index if cuts else 0
                        print("\n########## VERB-STREAM — rung four, per ### and window "
                              "residual census (--dossier-final) ##########")
                        # max_stream bounds a full-run stream (~1300 edges) to a
                        # readable line and states the count it withheld. The offline
                        # dossier keeps the unbounded default, so its bytes are
                        # unchanged (WO-W2-D-01's switched-instrument precedent).
                        # WO-SPLIT-AND-SHOW-01: `panel` comes from the sink above — the
                        # single build this branch already performed. `.get` rather than
                        # `[...]` so a coupling read that raised leaves it None and the
                        # renderer prints an explicit absence, never a zero.
                        print(render_verb_stream_block(
                            worldlines, window_edges(cuts), _lo, _hi, max_stream=40,
                            panel=_panel_sink.get("panel")))
                    except Exception as _vexc:
                        print(f"[render_stages] verb-stream error (non-fatal): {_vexc!r}")
                self._acted_on_rendered = True
            except Exception as exc:        # the instrument never perturbs the run
                print(f"[render_stages] acted-on error (non-fatal): {exc!r}")

        # WO_WEAVE_W0: route still-object Ledger evidence into the role spine.
        # For every worldline whose fingerprint is unchanged from spawn (a still
        # object), join it to its spawn Slot by fingerprint EQUALITY and feed a
        # STATIC verdict (confidence from coverage) into accumulate_role_evidence.
        # Movers are quarantined to W1. This WRITES belief (axes) — but post-loop,
        # over the settled Ledger + library, not in the live loop. Latched once;
        # non-fatal. The cut runs here (scipy, Mac path); the resolver is pure.
        if self._weave_w0 and not self._weave_w0_done:
            try:
                import numpy as np
                from virelai_v4.perception.grid_scan import scan_grid
                from virelai_v4.capture.clay import (
                    RegionClay, NodeCut, master_object_list, _hash_visible,
                )
                from virelai_v4.capture.ledger_build import delivery_of
                from virelai_v4.weave.still_bridge import feed_still_evidence
                from virelai_v4.library.log_score_accumulator import accumulate_role_evidence
                from virelai_v4.library.library_roles import LibraryRole
                log = getattr(self.ctx, "frame_record_log", None)
                lib = getattr(self.ctx, "semantic_library", None)
                n = len(log) if log is not None else 0
                if n == 0 or lib is None:
                    print("\n########## WEAVE-W0 — no Ledger or library, skipped ##########")
                else:
                    cuts = []
                    # WO-DELIVERY-CLASS-02 · the predecessor, carried one iteration.
                    _previous_settled = None
                    for rec in log.records:
                        # WO-ANIMATION-01 · bound once; `[-1]` unmoved.
                        _delivered = log.reconstruct(rec.node_index)
                        visible = _delivered[-1]
                        grid = np.array(visible, dtype=np.int32)
                        regions = tuple(RegionClay.from_region(r) for r in scan_grid(grid).regions)
                        _n, _cls, _mag = delivery_of(_delivered, _previous_settled)
                        _previous_settled = visible
                        cuts.append(NodeCut.from_record(
                            rec, regions, visible_hash=_hash_visible(visible),
                            grid_shape=(int(grid.shape[0]), int(grid.shape[1])),
                            delivery_layers=_n, delivery_class=_cls,
                            delivery_magnitude=_mag,
                        ))
                    master = master_object_list(cuts)
                    # spawn Slot fingerprints: (class_id, frozen cells) -> region_id
                    slot_fps = {(o.class_id, o.cells): rid for rid, o in lib.objects.items()}

                    def _feed(rid, role_name, conf):
                        accumulate_role_evidence(lib.objects[rid], LibraryRole(role_name), conf)

                    report = feed_still_evidence(master, slot_fps, _feed)
                    print(f"\n########## WEAVE-W0 — {report.still} still worldlines, "
                          f"{report.joined} joined to slots, {report.unjoined} unjoined, "
                          f"{report.skipped_movers} movers skipped; evidence fed ##########")
                self._weave_w0_done = True
            except Exception as exc:        # the instrument never perturbs the run
                print(f"[render_stages] weave-w0 error (non-fatal): {exc!r}")

        # WO_HASH_A: render the Persistent (###) Objects section — the still
        # integral made visible, a derived VIEW over the Ledger + Slot resolution.
        # RENDER-ONLY: no accumulate_role_evidence, no belief write, no store
        # (recomputed each render; the Ledger is the only store). Still-only
        # (≈ = ~); movers excluded. build_dossier stays untouched. Latched once.
        if self._weave_hash and not self._weave_hash_done:
            try:
                import numpy as np
                from virelai_v4.perception.grid_scan import scan_grid
                from virelai_v4.capture.clay import (
                    RegionClay, NodeCut, master_object_list, _hash_visible,
                )
                from virelai_v4.capture.ledger_build import delivery_of
                from virelai_v4.weave.still_bridge import (
                    group_hash_objects, render_hash_section,
                )
                log = getattr(self.ctx, "frame_record_log", None)
                lib = getattr(self.ctx, "semantic_library", None)
                n = len(log) if log is not None else 0
                if n == 0:
                    print("\n########## PERSISTENT (###) OBJECTS — record empty ##########")
                else:
                    cuts = []
                    # WO-DELIVERY-CLASS-02 · the predecessor, carried one iteration.
                    _previous_settled = None
                    for rec in log.records:
                        # WO-ANIMATION-01 · bound once; `[-1]` unmoved.
                        _delivered = log.reconstruct(rec.node_index)
                        visible = _delivered[-1]
                        grid = np.array(visible, dtype=np.int32)
                        regions = tuple(RegionClay.from_region(r) for r in scan_grid(grid).regions)
                        _n, _cls, _mag = delivery_of(_delivered, _previous_settled)
                        _previous_settled = visible
                        cuts.append(NodeCut.from_record(
                            rec, regions, visible_hash=_hash_visible(visible),
                            grid_shape=(int(grid.shape[0]), int(grid.shape[1])),
                            delivery_layers=_n, delivery_class=_cls,
                            delivery_magnitude=_mag,
                        ))
                    master = master_object_list(cuts)
                    slot_fps = ({(o.class_id, o.cells): rid for rid, o in lib.objects.items()}
                                if lib is not None else {})
                    print("\n########## PERSISTENT (###) OBJECTS (--weave-hash) ##########")
                    print(render_hash_section(group_hash_objects(master, slot_fps)))
                self._weave_hash_done = True
            except Exception as exc:        # the instrument never perturbs the run
                print(f"[render_stages] weave-hash error (non-fatal): {exc!r}")

        if not self._dossier_final:
            return
        # WO-REFORMAT D4 — render-once guard. The harness calls cleanup on both
        # game-terminal and shutdown (agent.py), so the dossier printed twice.
        # A per-instance flag (set on first emit, checked before the second)
        # collapses it to one. Mixin-layer only — no harness-lifecycle change.
        if getattr(self, "_dossier_rendered", False):
            return
        self._dossier_rendered = True
        try:
            print("\n########## FINAL DOSSIER — one render from the final "
                  "belief state (--dossier-final) ##########")
            print(render_overview(build_dossier(self.ctx),
                                  axiom_key=self._axiom_key))
            for spec in (self._details or []):
                print(render_detail(self.ctx, spec, axiom_key=self._axiom_key,
                                    effect_model_key=self._effect_model_key))
        except Exception as exc:            # the instrument never perturbs the run
            print(f"[render_stages] final-dossier render error (non-fatal): {exc!r}")

        # SC1 (WO_STORE_A_OBSERVABILITY): Store-A read-out — the captain's actual
        # decision substrate (six BBA log-score axes), pure read, additive, never
        # perturbs the run. Lands in a separate diagnostic module (store_a_readout)
        # to avoid the live dossier.py collision. The per-object axes print on the
        # canary; the divergence table prints when VIRELAI_STORE_DIVERGENCE_DUMP=1.
        try:
            import os
            from virelai_v4.diagnostics.store_a_readout import (
                render_store_a_panel, render_divergence_table,
                render_lever_cause_table,
            )
            _lib = getattr(self.ctx, "semantic_library", None)
            if _lib is not None:
                print(render_store_a_panel(_lib))
                if os.environ.get("VIRELAI_STORE_DIVERGENCE_DUMP", "0") == "1":
                    print(render_divergence_table(_lib))
                    # SC2-REGROUND: per-lever revoke-vs-never-written verdict.
                    print(render_lever_cause_table(_lib))
        except Exception as exc:            # the instrument never perturbs the run
            print(f"[render_stages] store-A read-out error (non-fatal): {exc!r}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

_AGENT_KEY = "virelai_render_stages"


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="render_stages",
        description="Universal read-only per-stage render runner. Drives one "
                    "episode of --game through the existing harness and prints "
                    "the three-stage lens per frame.",
        epilog="example: uv run python -m virelai_v4.diagnostics.render_stages "
               "--game <id> --dossier-final --effect-model-key PATH",
    )
    p.add_argument("--game", required=True,
                   help="game_id to drive (supplied content; no game logic here)")
    p.add_argument("--max-frames", type=int, default=None,
                   help="render only the first N frames (default: all)")
    p.add_argument("--at", type=str, default=None,
                   help="comma-separated frame indices to render (overrides "
                        "--max-frames)")
    p.add_argument("--oracle", type=str, default=None,
                   help="path to an official replay (.json or .recording.jsonl) "
                        "used as the perception oracle for the graded triple "
                        "(supplied content; no replay path baked in code)")
    p.add_argument("--dossier", action="store_true",
                   help="render the WO-5 world-dossier overview per frame "
                        "(stage debug)")
    p.add_argument("--dossier-final", action="store_true",
                   help="render the world-dossier ONCE, from the final belief "
                        "state, after the run — the single gradeable artifact "
                        "(WO-D3). If both --dossier and --dossier-final are "
                        "given, --dossier-final wins (render once).")
    p.add_argument("--footprint-key", action="store_true",
                   help="append the ACTED-ON FOOTPRINT KEY to the acted-on block — "
                        "every acted-on ###'s FULL t-1 cell footprint in raw grid "
                        "coords, for machine cross-check against the replay .json. "
                        "OFF by default (WO-W2-D-01): it was 557 of the block's 703 "
                        "lines on the last canary and its reader is not a human.")
    p.add_argument("--final-only", action="store_true",
                   help="suppress the per-frame three-stage lens so the run "
                        "drives silently and only the final dossier prints "
                        "(pair with --dossier-final for a clean canary).")
    p.add_argument("--axiom-key", type=str, default=None,
                   help="path to an external axiom key (✓/⚠ overlay on the "
                        "axiom rows; read-only ground truth, never seen by the "
                        "solver)")
    p.add_argument("--effect-model-key", type=str, default=None,
                   help="path to an external effect-model key (✓/⚠ grade of the "
                        "recorded lever effects vs the functional class; "
                        "read-only ground truth, never seen by the solver). "
                        "Used by --detail effects")
    p.add_argument("--detail", action="append", default=None,
                   help="dossier drill-down render-mode (repeatable): "
                        "slot:N | probes | axioms | role:NAME | effects | "
                        "effects:N | partition | deepening")
    p.add_argument("--capture-verify", action="store_true",
                   help="WO-CC-S1-SEAL: after the run, assert the capture log "
                        "round-trips to the frames handed per node (all layers, "
                        "byte-equal) and print the verdict. Read-only; the "
                        "Stage-1 live seal. No effect when absent.")
    p.add_argument("--clay-compile", action="store_true",
                   help="WO-CC-S2-CLAY: after the run, cut every captured node "
                        "and print three raw views — per-node present list, "
                        "object master list, node/configuration map. Read-only, "
                        "geometry-only, zero inference. No effect when absent.")
    p.add_argument("--weave-w0", action="store_true",
                   help="WO_WEAVE_W0: after the run, route still-object Ledger "
                        "evidence into the role spine — join fingerprint-invariant "
                        "worldlines to their spawn Slots and feed STATIC evidence. "
                        "Writes belief (post-loop). Movers quarantined. No effect "
                        "when absent.")
    p.add_argument("--weave-hash", action="store_true",
                   help="WO_HASH_A: after the run, print the Persistent (###) "
                        "Objects section — the still-integral as a derived view "
                        "(one row per still worldline: id, class, trail, slot, "
                        "role). RENDER-ONLY, no belief write, no store. No effect "
                        "when absent.")
    return p


def _parse_at(at: Optional[str]) -> Optional[Set[int]]:
    if not at:
        return None
    return {int(tok) for tok in at.split(",") if tok.strip() != ""}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)


def build_observer_agent() -> type:
    """Bind the SDK-free observer onto the production Virelai agent. Deferred:
    importing Virelai pulls the live ARC SDK (live-run time only).

    Import order is load-bearing. There is an order-dependent cycle in the
    harness: agents/__init__.py imports virelai_v4.virelai, and virelai.py
    imports agents.agent. The harness resolves it by importing `agents` first
    (so Virelai finishes before agents/__init__ needs it). Importing Virelai
    COLD here would run agents/__init__ mid-import of virelai.py — before
    Virelai is defined — raising ImportError. So initialize the `agents`
    package FIRST, matching the harness's own resolution order, THEN import
    Virelai (now fully defined in sys.modules). No edit to agents/__init__.py
    or virelai.py (the harness is reused, not modified)."""
    import agents  # noqa: F401 — initialize the package first (cycle order)
    from virelai_v4.virelai import Virelai
    return type("RenderStagesVirelai", (RenderObserverMixin, Virelai), {})


def run(argv: Optional[Sequence[str]] = None) -> None:
    """Configure render bounds, register the observer, and delegate to the
    harness's own entry. Heavy harness/SDK imports are deferred to here so
    module import stays light for sandbox smoke-testing."""
    args = parse_args(argv)
    oracle_frames = load_oracle_frames(args.oracle) if args.oracle else None
    agent_cls = build_observer_agent()
    axiom_key = load_axiom_key(args.axiom_key) if args.axiom_key else None
    effect_model_key = (load_effect_model_key(args.effect_model_key)
                        if args.effect_model_key else None)
    # WO-D3 Fix B: --dossier-final wins over --dossier (render once, not per-frame).
    per_frame_dossier = args.dossier and not args.dossier_final
    if args.dossier and args.dossier_final:
        print("[render_stages] both --dossier and --dossier-final given; "
              "--dossier-final wins (rendering once, post-loop).")
    # WO-FINAL-ONLY: a harmless-but-useless combination — nothing would print.
    # WO-CC-S1-SEAL: --capture-verify also prints post-loop, so --final-only
    # paired with it is the clean silent seal, not a nothing-to-print case.
    if (args.final_only and not args.dossier_final
            and not args.capture_verify and not args.clay_compile
            and not args.weave_w0 and not args.weave_hash):
        print("[render_stages] --final-only without --dossier-final: per-frame "
              "lens suppressed and no final dossier requested — nothing to print.")
    agent_cls.configure(max_frames=args.max_frames, at=_parse_at(args.at),
                        oracle_frames=oracle_frames, dossier=per_frame_dossier,
                        dossier_final=args.dossier_final,
                        final_only=args.final_only,
                        axiom_key=axiom_key, effect_model_key=effect_model_key,
                        details=args.detail,
                        capture_verify=args.capture_verify,
                        clay_compile=args.clay_compile,
                        weave_w0=args.weave_w0,
                        weave_hash=args.weave_hash,
                        footprint_key=args.footprint_key)

    import agents
    agents.AVAILABLE_AGENTS[_AGENT_KEY] = agent_cls

    # Reuse the existing run entry verbatim — do not reimplement driving.
    import main as harness_main  # noqa: WPS433 (deferred: pulls requests/dotenv)
    sys.argv = ["main", "--agent", _AGENT_KEY, "--game", args.game]
    harness_main.main()


if __name__ == "__main__":  # pragma: no cover
    run()
