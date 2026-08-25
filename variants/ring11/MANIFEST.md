# Variant: ring11 — the Virelai ontology implant (Ring 1 revision)

**Created:** 2026-08-25 · **From:** `variants/ring1` (verified 66-file baseline copy +
ledger), minus ring1's venv/scratch · **Ruling basis:** Memo №3 (cut line, lockstep
schedule) · Director's rulings 2026-08-25 (strategy replaces Tufa's; RESET root; v4 docs
as guide, v4 code as template) · CUT-DOCUMENTS-DRAFT v2 (approved by proceed order) ·
ontology correction (claude/ontology-correction-2026-08-25.md).

## The one variable (vs frozen baseline)

The Virelai world layer replaces Tufa's perception+strategy prose, and the ledger grows
root-tracking, batch accounting, and a queryable map. Baseline arm = frozen r0;
prior arm = ring1 (digest+subtraction over intact prose).

## Diff surface

| file | change |
|---|---|
| `inference/agent/prompts.py` | **VIRELAI_WORLD_ADDENDUM added** (axioms + output contract + five-beat strategy; sources cited in-file: canon 1/2/4, R-A, R-D, PROBE_STRATEGY_v2 + rider §C, SPEC_SOLVER_LOOPS_v2, Director 2026-08-25). **Deleted:** D1 object-matching recipe, D2 frame-diff recipe, D4 goal-search coaching (default loop line, "stop probing and search", goal-advance line — reworded to before-win/after-win form). GAME_OVERVIEW's observe-plan-act line reworded (goal-guessing removed). `virelai` runtime variable documented. **Kept per lockstep (Ring 2's rows):** HUD/timer warning, verification ritual, background coaching, scene framing. |
| `inference/agent/tool_agent.py` | system prompt gains the world addendum; D3 world-model mandate narrowed to INTERPRETIVE content (restate cadence KEPT per Memo №3 §6 — its softening is a separate A/B); `_virelai_state` stashed from action payloads and serialized into runtime state as `virelai` |
| `inference/agent/python_tool_sandbox.py` | exposes `virelai` as a runtime global |
| `inference/framework/virelai_ledger.py` | v2: `record_reset` (root marked on first RESET, confirmed on later ones, mismatch reported LOUDLY as boundary event; RESET excluded from map geometry per G11); `snapshot()` (full uncapped map for the sandbox); reset notes prepended to digest |
| `inference/framework/solver.py` | `step_env` final payload gains the loud batch account ("N presses; last board change at press K — presses K+1..N changed nothing") and `virelai_state` snapshot |

## Laws honored

Lockstep deletion (nothing cut ahead of capability — Ring 2 prose stands); no confidence
numbers anywhere (counts only); resolution-never-threshold (Tier-A unchanged, ratio-free);
loudness (batch account + RESET boundary events are stated, never absorbed); masked =
attribution-quarantine (axiom 4 wording per rider §C); full-structure-queryable/
delta-pushed (snapshot uncapped, prompt carries only the [MAP] delta); G10 (self-loops =
tried, no frontier); G11 (RESET not a transition).

## Verification at creation (cloud workspace, 2026-08-25)

py_compile clean ×5; ledger v2 unit tests (root mark/confirm/boundary, edge exclusion,
snapshot shape) PASS; system prompt renders with all implants present and all four
deletion targets verified absent (string-level). **End-to-end NOT_MEASURED until the
Kaggle run.** A/B bar: paired significance vs baseline on terminal + hold the
score-at-budget win; pre-registered: over-pressing (+69% actions in ring1) should fall;
exploration gains (cd82, ar25, ft09, sp80) should hold; ls20 mechanism-check via root
recognition corollary.

## Not done

frontier_tag label transcription (R-H1a not formally ratified — Tier-A labels remain
this build's own, equivalent semantics, cited as shape only); world-model restate
cadence unchanged (own A/B per Memo №3 §6); Ring 2 mask; nav queue.
