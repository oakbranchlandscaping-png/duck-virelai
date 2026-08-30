"""WO-OCD-CHOKE-POINT — consolidated observability write helper.

Module-level helper extracted from virelai.py so it can be imported in
sandbox without dragging in arcengine. The function reads all action
fields via hasattr-guarded duck typing, so it accepts both real
arcengine.GameAction instances and SimpleNamespace fakes used in unit
tests.

Single production caller: Virelai.choose_action invokes this once per
frame just before `return action`. The choke-point write site remains
semantically a single location — choose_action — but the implementation
lives here so unit tests in tests/test_virelai.py can import it without
the arcengine dependency.

Sovereignty: stdlib + virelai_v4.context (type only). No arcengine, no
strategy/, no library/. The agents.recorder import is lazy inside the
function body to keep this module sandbox-importable.

Reads from ctx:
  ctx.last_probe_target_region_id   — target rid set by the emitter site
  ctx.last_emitter_path             — provenance tag set by the emitter
  ctx.semantic_library              — for objects.actions_attempted write
  ctx.action_log_path               — sidecar path (None-safe)
  ctx.lives_used / actions_this_life / step_count — record metadata

Writes:
  library.objects[target_rid].actions_attempted[6] = True
      (only when target_rid known + library set + region exists)
  one JSONL line to ctx.action_log_path
      (only when path set; silent skip otherwise)

Defensive: silent return on action.value != 6, missing action_data,
missing library/target. Never raises.
"""

from __future__ import annotations

from typing import Any, Optional

from virelai_v4.context import VirelaiContext


def record_action_at_choke_point(
    ctx: VirelaiContext,
    action: Any,
) -> None:
    """Consolidated observability write for ACTION6 emissions.

    Called once per frame from Virelai.choose_action just before
    `return action`. Replaces the per-emitter writes that
    WO-OCD-FLAGS-CLICK and WO-OCD-ACTIONLOG had previously inlined at
    the producer sites in tier4_click.py and action_selector.py.
    """
    action_value = action.value if hasattr(action, 'value') else None
    if action_value != 6:
        return

    coord_x: Optional[int] = None
    coord_y: Optional[int] = None
    if hasattr(action, 'action_data') and action.action_data is not None:
        try:
            _ad = action.action_data.model_dump()
            coord_x = _ad.get("x")
            coord_y = _ad.get("y")
        except Exception:  # pragma: no cover — defensive
            pass

    target_rid = ctx.last_probe_target_region_id
    lib = ctx.semantic_library
    if target_rid is not None and lib is not None:
        _region = lib.objects.get(target_rid)
        if _region is not None:
            _region.actions_attempted[6] = True

    # WO-PROBE-INSTRUMENT: observability-only choke-point dump. Reads existing
    # fields, writes nothing to belief; gated on VIRELAI_DIAG_DUMP so it is
    # silent in normal runs. Surfaces the three runtime fields source could not
    # resolve — the emitter path, the probe target, and the target's
    # actions_attempted (the completion field) — on each ACTION6 frame.
    import os
    if os.environ.get("VIRELAI_DIAG_DUMP"):
        _o = lib.objects.get(target_rid) if lib is not None else None
        _aa = dict(_o.actions_attempted) if _o is not None else "N/A"
        _pc = _o.probe_count if _o is not None else "N/A"
        # WO-OCD-05.1: surface the Evidence Asymmetry Engine's belief fields for
        # the probed object so the keystone is observable in-frame (the [CHOKE]
        # line was blind to them). Reads existing fields, writes nothing.
        _ic = _o.inert_coverage if _o is not None else "N/A"
        _ipc = _o.inert_probe_count if _o is not None else "N/A"
        _er = _o.ever_reactive if _o is not None else "N/A"
        _nr = _o.needs_reinvestigation if _o is not None else "N/A"
        print(
            f"[CHOKE] emitter={ctx.last_emitter_path} target_rid={target_rid} "
            f"action={action_value} actions_attempted[{target_rid}]={_aa} "
            f"probe_count[{target_rid}]={_pc} "
            f"inert_cov={_ic} inert_pc={_ipc} ever_react={_er} needs_reinv={_nr}",
            flush=True,
        )

    # WO-A2-03 Part 3 — THE JSONL SIDECAR WRITE IS RETIRED. The belief write
    # above (`actions_attempted[6] = True`) STAYS: it is the probe-completion
    # channel the captain's static completion `DISTINCT_PROBES_AT_LEAST` reads
    # (never an axis), and `level_advance.py` documents that leaving it empty
    # keeps the first-touch coverage question open forever. This module is the
    # probe-completion writer; only its second job is retired.
    #
    # Why the sidecar goes, ruled on the live canary at ecee9d0:
    #   fi_agree=32  gidx_agree=28  both_wrong=1265  of 1322 nodes
    #   fi_distinct_keys=144 of 1366 rows -> 1222 rows destroyed (89.5%)
    # `frame_index` was `ctx.actions_this_life` (PERSIST_LEVELS_RESET_LIFE —
    # resets at life). `global_action_idx` was `ctx.step_count`
    # (PERSIST_LIVES_AND_LEVELS — never resets). The node array is
    # `ctx.frame_record_log` (PERSIST_LIVES_RESET_LEVEL). NO FIELD IN THE RECORD
    # SAT AT THE NODE'S LIFETIME TIER: one key reset too often, the other never.
    # There was no index rule to find. The live log carries the action natively —
    # entry t IS node t, dense over every action type (R1-02c) — so the sidecar
    # re-derived, from a sparse source, what the log already had.
    #
    # Retiring this block also removes SEAM S8: the `importlib.spec_from_file_
    # location` load of `agents/recorder.py`, which bypassed `agents/__init__.py`
    # and was invisible to every AST import graph the census ever built.
    #
    # DEBT CREATED, NOT PAID: with the JSONL half gone, this module's sole act is
    # a belief write — `observability_choke_point` is now mis-named, and
    # `ctx.action_log_path` (PERSIST_LIVES_AND_LEVELS) has no remaining writer.
    # Both are reported to the strategy chamber; neither is renamed here.
