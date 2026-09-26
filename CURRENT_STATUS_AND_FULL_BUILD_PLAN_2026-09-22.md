# Cybernetic Duck: current status and build ladder

**Updated:** 2026-09-25  
**Active source:** `variants/ring9-cybernetic-gates/ARC3-Inference/`  
**Newest completed behavioral evidence:** OpenRouter vc33 G4 fast v1, mechanical closure with one inaccurate prose explanation  
**Current execution:** no live run; G4.2 CLICK orbit controller is built locally and unconfirmed  
**North Star:** Explore the world's physics through gated interaction and stable record keeping;
observe a win rather than guessing it; then describe the observed goal in the learned grammar.

## Evidence discipline

`LIVE CONFIRMED` means a completed served-model run met the stated checkpoint. `LIVE DIAGNOSTIC`
means a run supplied useful direct evidence but missed its exit. `BUILT, LIVE UNCONFIRMED` means
the active source and local checks are complete but the served Duck has not demonstrated the
behavior. Tests establish infrastructure behavior, not model understanding.

Frozen packages and run artifacts describe only their own bytes. Active-source repairs do not
retroactively change their result.

## Current position

| Layer | State | Evidence boundary |
|---|---|---|
| Universal ontology and cybernetic mission | **LIVE CONFIRMED** | Present in the completed `ls20` prompt trace. |
| G0 action surface | **LIVE CONFIRMED** | Duck accepted the exact opaque `ACTION1`-`ACTION4` interface before acting. |
| Binding Delphi order | **LIVE CONFIRMED** | `ls20` executed exactly two probes for each opaque action in controller order. |
| G1 ego localization and explanation | **LIVE CONFIRMED ON `ls20`** | Duck identified the full two-color composite and explained all four five-cell cardinal laws. |
| G1 prospective demonstration and `EgoLaw` | **LIVE CONFIRMED ON `ls20`** | A future 25-cell translation was frozen, executed, and marked `SUPPORTED`; G1 closed. |
| G1 → G2 handoff | **LIVE CONFIRMED ON `ls20`** | G2 received the demonstrated complete post-action ego footprint. |
| Ranked NAV/HYBRID collision opening | **LIVE CONFIRMED AT ENTRY** | G2 bound rank-1 object `[32,20]` and admitted two approach actions. |
| G2 counter identity and masking | **LIVE CONFIRMED; STABLE-BASELINE REPAIR OFFLINE CONFIRMED** | G2's complete downstream product is the reversible total mask. Later counter behavior is actively ignored and cannot revise products or reopen gates. The September 26 regression repair has 351 offline tests passing and awaits a focused live rerun. |
| G3 broad lever location | **LIVE CONFIRMED ON vc33** | OpenRouter v8 completed the counter-masked click sweep, accepted two prospectively confirmed levers, retained eight scoped nulls, recorded zero bounded unknowns, and handed off a terminal `LeverInventory`. |
| G4 per-lever reaction study | **G4.0/G4.1 LIVE CONFIRMED; G4.2 CLICK BUILT, LIVE UNCONFIRMED** | Fast vc33 v1 closed two evidence-bound first impressions. The new controller repeats each exact click through novel masked states, stops only on an observed null or exact recurrence, records the full orbit, and suppresses the passive agenda. NAV/HYBRID re-contact remains to build. |
| G5 forces through G9 transfer | **PLANNED** | Mine prior art before each remaining gate and judge each only on its own question. |

The project has crossed G1 and G2 on served runs and completed G3 on vc33. G4.0/G4.1 is live
confirmed and the first G4.2 implementation is now built:
the controller carries G3 identity and causal evidence forward, decomposes the exact counter-masked
residue, makes Duck explain what changed, then repeatedly activates each confirmed CLICK lever while
masked states remain novel. It returns on the first observed null or recurrence and requires a
state-scoped explanation. The next evidence step is a bounded vc33 fast-model run; the next
engineering slice for embodied worlds is NAV/HYBRID re-contact piloting.

## Current exact-Qwen Kaggle checkpoint

The current immutable package is `kaggle/ring9-g3-vc33-closure-v3/`. It runs vc33 alone with
`vrfai/Qwen3.6-27B-FP8`, 96 actions, and 2,700 seconds of behavior time after model setup. Its
specific question was whether automatic reset enters the observer, exact spawn identities survive,
unresolved targets remain pending, ranks 4 and 5 receive valid attribution, and G3 can close an
accepted inventory. Notebook version 1 completed. It directly confirmed the rank-4/rank-5 lever
path, but the run never reached reset and G3 did not close because rank 6 looped. See
`runs/kaggle-ring9-g3-vc33-closure-v3/REVIEW_2026-09-24.md`.

The paragraphs below describe earlier exact-Qwen checkpoints and remain historical evidence.

The current frozen package is `kaggle/ring9-g3-qwen36-compatibility-v1/`. It runs the exact Tufa
model family, `vrfai/Qwen3.6-27B-FP8`, through local vLLM on vc33, ft09, and ls20 sequentially,
with 96 actions and 2,700 seconds per world. The execution receipt fixes the model, worlds,
budgets, source-manifest hash, mode, and concurrency.

Notebook version 1 failed source verification before model startup because its manifest included
a `.DS_Store` file that Kaggle omitted from the mounted archive. This is direct infrastructure
evidence and no gate behavior was exercised. The corrected version 2 excludes operating-system
metadata, passed package/source/archive verification, and completed. It exercised vc33 for 62
actions, then the notebook-wide deadline left ft09 and ls20 at zero actions. vc33 completed the
ranked click sweep but failed G3 closure because pointer attribution remained unresolved. See
`INFRASTRUCTURE_G3_QWEN36_KAGGLE_CHECKPOINT_2026-09-23.md` and
`runs/kaggle-ring9-g3-qwen36-compatibility-v1/LAUNCH_RECORD.md`.

## Direct observations from the local G2 counter-lock pilot

- G2 formed an 84-cell, two-row counter candidate from transitions 10–12.
- Duck submitted an accepted evidence-bound explanation and future `ACTION3` prediction.
- Transition 13 supported the prediction with exactly two `11→3` cells and created the mask.
- G2 stayed in boundary confirmation until the bar reached 0 source and 84 replacement cells.
- Transition 43 reset all 84 cells `3→11`, respawned the 25-cell ego from rows 30–34 to rows
  45–49, and depleted four separate `8` cells.
- The controller marked G2 `SATISFIED` with `COUNTER_LOCKED_BY_MIN_MAX_BOUNDARY`.
- Duck's accepted answer incorrectly inferred a 21-action capacity from an 84-cell footprint and a
  two-cell rate; the observed period was 42 actions. This is a counter-local quality note and can
  be corrected with derived arithmetic without reopening the gate.
- The simultaneous ego respawn and four-cell `8→3` change are preserved for G4 conditional
  reaction typing; G2 is not responsible for explaining their full causal role.

See `REVIEW_G2_COUNTER_LOCK_LOCAL_LS20_V2_2026-09-22.md`. Zero levels cleared is outside this
checkpoint's target and does not reverse the structural pass.

## Direct observations from the local G1 closure pilot

- The run admitted 11 actions and ended at its experiment deadline with complete artifacts.
- G0 closed, then G1 executed `1,1,2,2,3,3,4,4` in controller order.
- Duck explained the 25-cell orange/blue ego and exact five-cell action laws.
- Two exact-geometry submissions were rejected with visible reasons; Duck corrected both, and its
  third answer was accepted.
- Transition 9 supported the prospective full-pattern prediction and closed G1.
- G2 opened on the rank-1 one-cell target and separated a repeated two-cell bottom-bar rewrite
  from ego motion.
- G2 then deadlocked: it blocked new actions pending an explanation while rejecting the explanation
  because it claimed no unused intervention was available for prospective confirmation.
- Source tracing found the precise guard error: `submit_answer()` calls `_current_action()` while
  status is still `ANSWER_REQUIRED`, but NAV/HYBRID's stored counter-only action is exposed only in
  `DEMONSTRATION_REQUIRED`. The fallback probe-action list is intentionally empty for Duck-piloted
  navigation, producing the false absence result.

See `REVIEW_G1_CLOSURE_LOCAL_LS20_V2_2026-09-22.md`. The zero game score is outside the G1
checkpoint and does not reverse this pass.

## Direct observations from the completed `ls20` run

- The notebook completed and preserved the frozen package and execution receipt.
- Duck executed eight authorized G1 actions only: `1,1,2,2,3,3,4,4`.
- Every action changed 52 cells: a 50-cell ledger for a 25-cell orange/blue composite translation
  plus a separate two-cell `11→3` bottom-bar rewrite.
- Duck correctly inferred `ACTION1` up five, `ACTION2` down five, `ACTION3` left five, and
  `ACTION4` right five.
- Duck separated the monotone bottom bar from the ego and treated it as a counter candidate.
- G1 reached `ANSWER_REQUIRED`, but 18 G1 submissions were rejected and no prospective
  demonstration or `EgoLaw` was recorded.
- Rejection reasons were hidden after a large gate payload. The run ended after about 943.6
  benchmark seconds because setup time had already consumed about 562.6 seconds of the notebook
  deadline.
- G2 was not reached. The run supplies no collision sweep, counter mask, boundary, or lever result.

The zero game score is outside this checkpoint's question. It does not grade G1.

## Active-source repairs now complete

The G1 closure reliability slice adds:

- a concrete nested answer template with current opaque actions and evidence ids;
- normalization for structured subjects, list-form action laws, flat scope keys, action strings,
  and `{row, col}` displacements;
- an exact color-agnostic `PATTERN_TRANSLATION` verifier for a complete multi-color ego;
- error-first compact rejection payloads and compact success payloads;
- a benchmark-start deadline that either grants the promised solver time or fails preflight;
- evaluator compatibility with the frozen reliability receipt v2 schema.

The G2 counter-knowledge slice adds:

- an evidence-bound explanation and prospective-prediction template;
- direct reuse of the stored NAV counter-only action, repairing the observed deadlock;
- validated recurrence, a complete reversible mask, and a retroactive masked-state archive;
- mask-ready handoff to G3 once the recurrent law receives prospective support;
- background monitoring that can later lock the extremal game-over or respawn boundary without
  blocking useful lever probes.

The full local suite passes **336 tests** when the vendored TAAF source is placed on `PYTHONPATH`.
The G3 pre-run review corrections add contradicted-confirmation, prospectivity, boundary-retry,
and NAV certificate coverage. OpenAI payloads now exclude vLLM-only fields, and rate limits wait
inside the current tool turn so partial model work is preserved. See
`BUILD_SLICE_G3_PRERUN_REVIEW_CORRECTIONS_2026-09-23.md`.

## Immediate execution ladder

**Credential readiness:** the ignored, owner-only `.env` loads the OpenRouter key; OpenRouter's
authenticated key endpoint accepts it; and a minimal request to the exact configured
`Qwen/Qwen3.6-27B` model succeeded on 2026-09-22. The credential and model response were not
displayed. The ARC key is also loaded from the same owner-only file; a read-only authenticated
`GET /api/games` returned HTTP 200 and exposed `ls20`, `ft09`, and `vc33`. No scorecard, game
session, or environment action was created during credential verification.

1. **Complete:** G2 emits its product at mask readiness as a stable ignored baseline during
   later work.
2. **Complete:** the automatic-reset runtime bridge, site-only reset back-edge, exact spawn
   identity, fail-closed frame mismatch, and same-rank retry are locally verified.
3. **Complete:** OpenRouter requests now bind reasoning and routing controls and record requested
   and returned model/provider identity. Fast and dense-rehearsal profiles are available.
4. **Complete diagnostic:** exact-Qwen vc33 v3 confirmed two levers, then exposed an unbounded
   retry on the known counter object. The reset bridge was not exercised.
5. **Complete locally:** `BUILD_SLICE_G3_TOTAL_COUNTER_MASK_AND_LEVER_FOCUS_2026-09-24.md`
   excludes sealed counter members, suppresses masked entity churn, partitions world residue before
   attribution, and reconciles inventory against eligible targets plus audited exclusions. The
   frozen v3 replay passes: source rank 6 is excluded, rank 7 is next, and 31 counter-loop actions
   create no new masked entities.
6. **Complete locally:** typed dossier semantics and logical ambiguity bounding now reject the
   flawed frozen M0009 explanation and prevent same-target ambiguity loops without converting
   uncertainty into inertness or G3 success.
7. **Complete live:** vc33 OpenRouter v8 exhausted the eligible roster and emitted the exact final
   inventory partition with two confirmed levers and eight scoped nulls.
8. **Complete live:** G4.0/G4.1 bound the two identities and Duck supplied two first-impression
   explanations; structured anatomy stayed exact despite one revisable prose-count mismatch.
9. **Complete locally:** G4.2 CLICK orbit discovery repeats the bound lever, masks the whole
   counter, continues through novel states, stops on observed null/recurrence, records the full
   sequence, and suppresses the passive agenda. The offline suite passes 348 tests.
10. **Next evidence:** run one bounded fast OpenRouter vc33 checkpoint against the exact G4.2 exit.
11. **Next embodied slice:** build NAV/HYBRID move-away and re-contact piloting before making any
   embodied repetition claim.
12. **Promotion:** use dense Qwen3.6 after the fast infrastructure check; reserve Kaggle for the
   assembled G4 milestone. Any newly appearing visual object returns to G3 first.

The governing repair sequence is `BUILD_PLAN_G3_LIVE_CLOSURE_2026-09-23.md`.

This ordering incorporates the accepted corrections in
`REVIEW_COLLABORATOR_G3_LEVER_LIFECYCLE_2026-09-22.md`.

The entity continuity, production observation adapter, per-entity lifecycle journal, and world-type
scheduler are now built and documented at `BUILD_SLICE_G3_ENTITY_OBSERVATION_ADAPTER_2026-09-22.md`,
`BUILD_SLICE_G3_ENTITY_LIFECYCLE_JOURNAL_2026-09-22.md`, and
`BUILD_SLICE_G3_SCHEDULER_2026-09-22.md`. The G3.3 ego-motion hardening and cross-gate counter
monitor hook are included. Attribution, the evidence-bound Duck dossier contract, and prospective
witness confirmation, and the live certificate evaluator are now implemented in
`BUILD_SLICE_G3_ATTRIBUTION_DOSSIER_2026-09-22.md`,
`BUILD_SLICE_G3_PROSPECTIVE_CONFIRMATION_2026-09-22.md`, and
`BUILD_SLICE_G3_LIVE_CERTIFICATE_2026-09-22.md`. The controlled served run completed as a useful
failure diagnostic. No live lever result is claimed; see
`runs/kaggle-ring9-g3-qwen36-compatibility-v1/REVIEW_V2.md`.

## Full gate ladder

| Gate | Question | Required product |
|---|---|---|
| G0 | What opaque actions and arguments exist? | `ActionSurface` |
| G1 | What is the ego, and how does each direct control move or alter it? | demonstrated `EgoLaw` |
| G2 | Which visible process is bookkeeping noise, what does it track, and how is it masked? | `CounterModel` + `MaskLaw` |
| G3 | Which contacted or clicked objects are levers? | exhaustive evidence-bound `LeverInventory` |
| G4 | How does each confirmed lever work, and what reacts under which conditions? | entity-specific scoped reaction and transformation laws |
| G5 | What changes without direct intervention? | `ForceLaw` or bounded not-applicable product |
| G6 | Which tested objects are inert under a specified action and state? | scoped inertness certificates |
| G7 | Which reachable counter-masked integer configurations are new? | persistent quotient-state graph and frontier |
| G8 | Which observed transition produced a win, in the learned grammar? | evidence-linked `ObservedGoalLaw` |
| G9 | How should that observed law be tested on the next level? | falsifiable transferred goal hypothesis |
