# Duck-Virelai documentation authority map

**Updated:** 2026-10-03
**Active source:** `variants/ring9-cybernetic-gates/`
**Purpose:** Distinguish the present North Star and build state from historical plans, frozen
packages, execution evidence, and prior-art trees.

> **2026-10-03 R9-R23 LANDED: THE MU BUCKET (Claude, Alpha build seat) — signed.** The ring9-carry-vc33-v6
> run cleared levels 1 and 2 (score 1.51). On level 3, G3 stalled on one object it could not attribute
> (`REVIEW_RING9_CARRY_VC33_V6_KAGGLE_2026-10-03.md`). The Director ruled a mu bucket
> (`RULING_MU_BUCKET_v1`): an object that stumps a gate never stops the ladder, and the ladder returns to it only when
> stuck and only on a changed board. R9-R23 is committed `ec8554d` on branch `r9-r20-level-entry` (Mac 529
> passed, 1 skipped), and its pre-flight tool is on main (`e869ef9`). **Finding: the Ring 9 source has forked.**
> The click line is on the branch; Sol's NAV line is on main. Four shared files are changed on both lines, and
> the first 110-game submission needs one tree, so the merge is a Director decision. Next: v7.
> `RECORD_R9_R23_LANDING_v1_2026-10-03.md`.

> **2026-10-04 PROJECT DIRECTIVES v2: R2 REOPENED FOR THE FINAL SUBMISSION (Claude, Alpha build
> seat; RATIFIED by the Director) — signed.** Supersedes v1 below. The first scored submission
> (~12 October) stays on Qwen3.6-27B-FP8. A model swap window runs 13–24 October under the
> `DESIGN_MODEL_PORTABILITY_v1` protocol. The final submission switches model only if the new
> model's canary passes D-8: the gates hold, Duck's answers are admitted at least as reliably,
> vc33 reaches the same level or further, and the submission dry run fits 9 hours. Decision
> 25–26 October. Prereg claims stay at a fixed model. Corrects the 2026-10-01 plan: 4-bit
> Qwen3.8-Flash-Next does run on one RTX PRO 6000 (three public stacks).
> `DIRECTIVE_COMPETITION_ENDGAME_v2_2026-10-04.md`.

> **2026-10-03 PROJECT DIRECTIVES: THE COMPETITION ENDGAME (Claude, Alpha build seat; RATIFIED by
> the Director) — signed.** Binding on every seat. The paper is the goal through 8 November, and it
> requires a linked, scored Kaggle submission, so a submission track runs in parallel with the
> evidence work: first scored ARC-AGI-3 submission by about 12 October; code freeze and final
> submission 27–30 October (deadline 2 November); paper 31 October–8 November. R2: the model stays
> Qwen3.6-27B-FP8. R3: about 30 GPU-hours a week, **shared by all seats**; state each run's expected
> GPU-hours in its upload record; submissions take priority when quota runs short. Run windows stay
> at 3 hours, since R9-R22's general A2 rule ends stalls. One run is one sample. Four Kaggle facts
> are still to verify (deadline time, submissions per day, RTX PRO 6000 quota, whether reruns count).
> `DIRECTIVE_COMPETITION_ENDGAME_v1_2026-10-03.md`.

> **2026-10-03 G3 NAV INTEGER TERRAIN MINE (Sol, Alpha build seat) — signed.** The repo contains
> the exact shortcut needed after the target-ledger failure. Universal Solver v3.5 projects
> confirmed floor/wall integers into a position passability map; Golden supplies the necessary
> corrections: use the full ego footprint, learned action displacements, target contact surfaces,
> empirical pose-edge overrides and world-state reopening. The proposed Ring 9 slice computes one
> shared reachable ego-pose component and forms a hypothesis for every target. It then tries to
> falsify that hypothesis with the shortest target-relevant route or boundary probe; only failed
> bridge attempts can license provisional unreachability. Mine and build outline:
> `MINE_G3_NAV_INTEGER_TERRAIN_REACHABILITY_v1_2026-10-03.md`.

> **2026-10-03 G3 TARGET LEDGER LS20 RESULT (Sol, Alpha build seat) — signed.** The run is
> **COMPLETE; CHECKPOINT FAILED DIAGNOSTICALLY**. It proved roster-before-execution, stable visual
> types, complete counter exclusions, source identity and controller ownership of all 96 actions.
> It did not complete the sweep: 3/16 eligible targets executed, 2 remained in progress, 11 were
> queued, and no unreachable certificate fired. Rank 5 consumed 61 actions while the sound but
> expensive reachability rule explored the shared floor component. The next slice must amortize
> that map across targets, forbid advancement past nonterminal rows, and close scoped nulls at the
> row boundary. Review: `REVIEW_RING9_G3_TARGET_LEDGER_LS20_V1_2026-10-03.md`. Package and launch
> records: `CHECKPOINT_G3_TARGET_LEDGER_LS20_V1_2026-10-03.md` and
> `UPLOAD_STATUS_RING9_G3_TARGET_LEDGER_LS20_V1_2026-10-03.md`.

> **2026-10-03 G3 TARGET EXECUTION LEDGER (Sol, Alpha build seat) — signed.** G3 now emits one
> complete `<world>_<pass>_g3_target_ledger.json`: the visual roster is populated before execution,
> and every row carries visual type, execution status, reachability, contact result, physics type
> and evidence. NAV marks `REACHABLE` only after observed contact and
> `UNREACHABLE_IN_CURRENT_WORLD_STATE` only after exhausting the demonstrated reachable component;
> world changes reopen the latter. The full source suite passes 553 tests. Status is **BUILT, LIVE
> PARTIALLY CONFIRMED; FULL ACCOUNTING FAILED**. Build and live exit criteria:
> `BUILD_SLICE_G3_TARGET_EXECUTION_LEDGER_2026-10-03.md`.

> **2026-10-03 CONTROLLER OWNERSHIP LS20 V2 RESULT (Sol, Alpha build seat) — signed.** The bounded
> live checkpoint is a **FULL PASS (9/9)**. All 16 environment actions were controller-owned. Duck
> supplied the accepted G1 embodied-ego explanation; the controller demonstrated and closed G1,
> formed and demonstrated the recurrent 84-cell counter law, installed the complete mask, closed
> G2, and performed four G3 actions. Runtime fell from v1's roughly 20 minutes to 3 minutes 33
> seconds and ledger tokens from 44,370 to 8,514. This closes the ownership checkpoint through G2;
> it does not yet prove G3 closure, lever discovery or G4 NAV. Evidence review:
> `REVIEW_RING9_CONTROLLER_FIRST_LS20_V2_2026-10-03.md`.

> **2026-10-03 CONTROLLER OWNERSHIP LS20 V2 CHECKPOINT (Sol, Alpha build seat) — signed.** A bounded
> successor to the partial-pass v1 run is preregistered against source `4e1be00`: all eight Delphi
> actions, the G1 demonstration, G2 pursuit, certified G2 answer, and G2 demonstration must be
> controller-owned; the complete counter mask must open G3; Duck may explain but may not select an
> environment action. The limits remain 16 actions and 1200 seconds for direct comparison.
> `CHECKPOINT_CONTROLLER_OWNERSHIP_LS20_V2_2026-10-03.md`.

> **2026-10-03 CONTROLLER OWNERSHIP LS20 V2 PACKAGE (Sol, Alpha build seat) — signed.** The frozen
> package binds source `4e1be00`, package hash `b24e6bb…`, and source-manifest hash `807ce79c…`.
> Verification passes 9/9, source is byte-identical to the commit export, receipts match, and the
> secret scan is clean. The local three-layout simulator cannot create `/kaggle` on the Mac's
> read-only root; this is recorded as unverified rather than inferred. The private dataset and
> notebook version 1 were accepted through the terminal path and the run is now **COMPLETE**. Upload record:
> `UPLOAD_STATUS_RING9_CONTROLLER_FIRST_LS20_V2_2026-10-03.md`.

> **2026-10-03 CONTROLLER OWNERSHIP PARITY (Sol, Alpha build seat) — signed.** The controller-first
> rule now governs the whole CLICK/NAV ladder: a wake supplies context but cannot transfer an exact
> action or certified answer to Duck. NAV reuses controller answers for certified G2, G3 and G4.1;
> receives the same one-time semantic G4 orientation as CLICK; and routes Duck-requested extra G4-A
> runs without spending model turns on approach or contact actions. Duck remains responsible for
> the embodied-ego explanation, confirmed-orbit explanations, uncertain trigger experiments, and
> G4-B/C predictions and descriptions. Build record and checkpoint criteria:
> `BUILD_SLICE_CONTROLLER_OWNERSHIP_PARITY_2026-10-03.md`. The complete source suite passes 549
> tests; live confirmation remains pending.

> **2026-10-03 CONTROLLER-FIRST LS20 RESULT (Sol, Alpha build seat) — signed.** The bounded live
> checkpoint is a **PARTIAL PASS (5 pass, 2 partial, 1 fail)**. The controller closed G0, performed
> seven of eight Delphi actions, demonstrated and closed G1, entered G2, and formed an 84-cell
> recurrent counter candidate after two deterministic pursuit actions. Duck gave a strong accepted
> ego explanation. A generic low-budget wake wrongly overrode one exact G1 action, then NAV G2
> handed its mechanically complete counter result to Duck, which exhausted the remaining time
> without answering. Do not rerun unchanged; exact actions must outrank wakes and certified NAV G2
> closure should be controller-owned. Evidence review:
> `REVIEW_RING9_CONTROLLER_FIRST_LS20_V1_2026-10-03.md`.

> **2026-10-02 CONTROLLER-FIRST ACTION MINE (Sol, Alpha build seat) — signed.** The completed v7
> ls20 review exposed an ownership regression: NAV/HYBRID G0, G1 and G2 bypass the existing generic
> controller executor, even when the gate binds an exact action. The current Director ruling is
> controller by default and Duck only when code cannot compute the lawful next action. The repo mine,
> superseded-document analysis and four-slice repair plan are in
> `MINE_CONTROLLER_FIRST_ACTION_BOUNDARY_v1_2026-10-02.md`.

> **2026-10-03 CONTROLLER-FIRST G1/G2 NAV SLICE (Sol, Alpha build seat) — signed.** G0 now
> closes through the controller in every world; all exact NAV/HYBRID G1 Delphi probes and the
> prospective demonstration are controller actions; the accepted ego model remains visible in the
> compact card; and G2 begins deterministic ranked-object pursuit using only G1-demonstrated
> bearings, floor stands and refused edges. G2 pursuit state is isolated from the post-mask G3
> frontier, and a remote counter tick cannot hide an observed ego refusal at the target. The
> complete local suite passes 546 tests. Status is **BUILT, LIVE UNCONFIRMED**. Build
> record and bounded ls20 checkpoint criteria:
> `BUILD_SLICE_CONTROLLER_FIRST_G1_G2_NAV_v1_2026-10-03.md`.

> **2026-10-03 CONTROLLER-FIRST LS20 CHECKPOINT (Sol, Alpha build seat) — signed.** A new bounded
> package freezes source commit `0b1a5e4` for one ls20 world, 16 actions and 1200 behavior seconds.
> It pins the successful Python 3.12 Kaggle image, limits each model response to 4096 tokens, and
> grades controller ownership through the first deterministic G2 pursuit. Package verification is
> 9/9 and the secret scan is clean. Upload state and preregistered criteria:
> `UPLOAD_STATUS_RING9_CONTROLLER_FIRST_LS20_V1_2026-10-03.md`.

> **2026-09-29 NIGHT STATUS (Claude, Alpha build seat) — signed.** R9-R09 (memory M-3) committed `e2c2b06` (Mac 461). **R9-R10 (memory M-4, G4 economy and lives)** built: ft09 offline reaches a satisfied G4-A in 92 actions and 7 Duck turns (orientation, 5 orbit explanations, 1 budget wake); the controller certifies G4.1 and runs every lever (D3), Duck may ask for an extra run, a same-level death re-studies the lever (D4), and the counter, action and time budgets wake Duck once on crossing (ruled 2026-09-29). Finding: on the continued-law world the ft09 bar does not cover the full five-lever protocol. Pending Mac pytest (470) and commit. State: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_NIGHT.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v10_2026-09-29.md`. Next: M-5, the package and the D7 throughput run.
>
> **2026-09-29 EVENING STATUS (Claude, Alpha build seat) — signed.** R9-R08 (memory M-2, the controller executor) committed `2941f53` (Mac 450). **R9-R09 (memory M-3)** built: at G3 close Duck's first turn is the orientation turn; its notes go to an UNCERTIFIED lane no gate reads (D6); every card carries keyed recall; `virelai('memory', …)` is the one pull interface, and every pull is fitted to reach Duck whole (T4 found a subject file that would have been truncated). Pending Mac pytest (461) and commit. State: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_EVENING.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v9_2026-09-29.md`. Next: M-4, G4 economy and lives.
>
> **2026-09-29 PM STATUS (Claude, Alpha build seat) — signed.** R9-R07 (memory M-1) committed `ee826ab` (Mac 431, the full suite). **R9-R08 (memory M-2, the controller executor)** built: the production agent carries ft09 from G0 to G3 closure with zero model calls in 72 actions (live v2: 121 actions, G3 not closed); G3 inherits G2's 54 total nulls (D5); every envelope carries the recording protocol. Five design deviations await ratification. Pending Mac pytest (450) and commit. State: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_PM.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v8_2026-09-29.md`. Next: M-3, recall and the orientation turn.
>
> **2026-09-29 STATUS (Claude, Alpha build seat) — signed.** R9-R06 (memory M-0) committed `1a4b6bd` (Mac 409). **R9-R07 (memory M-1, the slot-built card)** built: the v2 crash card is now ~4,700 characters (was 25,502); a Duck that reads only the card carries stress worlds with 2, 8 and 20 levers from G2 to G4-A satisfied, every card flat in the lever count; certified fields are filled by the controller. Design v2 records the M-1 revisions. Pending Mac pytest (419) and commit. State: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v7_2026-09-29.md`. Next: M-2, the controller executor.

> **2026-09-28 EVENING STATUS (Claude, Alpha build seat) — signed.** R9-R05 committed `4329185`; ft09 guided v2 ran: G2 closed, **G3 confirmed five levers (R9-R05 held live)**, then the card overflowed at the fifth dossier (25,502). Prior-art survey done. Director: "the controller should execute scripted moves when possible"; build memory as one comprehensive design. **`DESIGN_VIRELAI_MEMORY_v1` RATIFIED (D1–D7)**: three tiers (record, certified world model, slot-built card), injected recall, controller executor for G0–G3, lives persist. Doctrine v3 adds memory laws M1–M10. R9-R06 (memory M-0: replay harness, record index, memory store, turn ledger) built, pending Mac pytest (409) and commit. State: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_EVENING.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v6_2026-09-28.md`.

> **2026-09-28 AFTERNOON STATUS (Claude, Alpha build seat) — signed.** R9-R04 committed `8319853` (Mac 393). Walking the whole ft09 ladder offline found that G3 would file both controls as unresolved and close with zero levers: a recolour in place lost its entity identity. **R9-R05** repairs identity to the contract (what persists is STILL; one exact source matches; several abstain); the ft09 ladder now reaches G4-A satisfied offline in 131 of 200 actions, every card within budget. Pending Mac pytest (400) and commit. Planned labels moved up by one (G4-B = R9-R06). Current state: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_PM.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md`. Proposed axiom A7 awaits the Director.

> **2026-09-28 STATUS (Claude, Alpha build seat) — signed.** ft09 guided v1 reviewed: **G2 closed live under axiom A1** (first live stated-target closure), then the run crashed at G3 entry on the 24,000-character card guard (card was 67,939). Director rulings: the ranked list stays; proceed with the bounded card and the trigger label; label every build revision (`R9-Rnn`, ledger in plan v4 §1). R9-R04 (G3 bounded card, axiom A6; counter trigger label, A1 v2) built and offline-green, pending Mac pytest (393) and commit. Next live test: `ring9-g4-ft09-guided-v2`. Current state: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28.md`; doctrine: `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v4_2026-09-28.md`. Security: never `git add kaggle/`.

> **2026-09-27 EVENING STATUS (Claude, Alpha build seat) — signed.** Director rulings: a stated target is the goal when possible (G2 CLICK and G4 are stated targets; G3 scripted); every friction sharpens an axiom (`DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md`); NAV shelved; cross-level is G9; Kaggle is the test venue. G4-A guided lever study committed `fcc7f11`; G2 counter axiom + no-legal-move guard pending commit. Both Kaggle runs today reviewed (vc33 S1; ft09 stalled in G2). Current state: `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27_PM.md`; plan: `BUILD_PLAN_G4_CLICK_COMPLETION_v3_2026-09-27.md`. Security: never `git add kaggle/`.

## 1. Authority rule

The user's current direction governs. Repository documents supply design, evidence, and port
material; they are not independent implementation orders. When documents conflict, use this order:

1. the user's current instructions;
2. this authority map and the current status document;
3. the governing target architecture and current gate contracts;
4. active-source implementation and its tests;
5. frozen package records and actual run artifacts for claims about a specific execution;
6. dated plans, reports, and older source families as historical evidence or port material.

Never rewrite an old run record to resemble the current source. A frozen package and its launch
record describe the bytes that were packaged or executed. Current-source improvements apply only
after a new package, hashes, receipt, and notebook version are created.

## 2. Read these first

| Document | Role |
|---|---|
| `DOCTRINE_FRICTION_AXIOMS_v2_2026-09-28.md` | Superseded by v3 (supersedes v1): axioms A1–A6. A1 v2: the counter label's trigger must agree with the record. A5: the ranked-list ruling. A6 (new): the card is bounded regardless of world size. Every friction is routed here first. Claude, signed. |
| `DESIGN_VIRELAI_MEMORY_v2_2026-09-29.md` | **Current governing design** (supersedes v1; RATIFIED): v1 plus the M-1 revisions — tuned slot budgets, the card's presentation to Duck, §5.3.1 certified fields filled by the controller. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_NIGHT.md` | Current state (supersedes 2026-09-29 evening): stage table, builder notes on the G4 executor, the lives rule and budget wakes, handoff actions. Claude, signed. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29_NIGHT.md` | Current minimal read order, position and Kaggle procedure. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v10_2026-09-29.md` | Current revision ledger (supersedes v9): R9-R09 committed, R9-R10 built, M-5 next; honest ledger. Claude, signed. |
| `BUILD_SLICE_MEMORY_M4_G4_ECONOMY_AND_LIVES_2026-09-29.md` | R9-R10: controller G4.1 and G4-A runs, extra runs (D3), the lives rule (D4), budget wakes; ft09 offline to a satisfied G4-A (92 actions, 7 Duck turns); the ft09 bar finding. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_EVENING.md` | 2026-09-29 evening state (superseded by night; supersedes 2026-09-29 PM): stage table, test commands, builder notes on pulls, orientation and notes. Claude, signed. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29_EVENING.md` | Superseded by 2026-09-29 night. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v9_2026-09-29.md` | Superseded by v10 (supersedes v8): R9-R08 committed, R9-R09 built; honest ledger. Claude, signed. |
| `BUILD_SLICE_MEMORY_M3_RECALL_AND_ORIENTATION_2026-09-29.md` | R9-R09: orientation turn, UNCERTIFIED lane (D6), injected recall (M6), the one pull interface and PULL_CHARS; T4 on the production path. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29_PM.md` | 2026-09-29 PM state (superseded by evening; its test commands and executor notes still apply): stage table, the Mac and cloud test commands, executor builder notes, handoff actions. Claude, signed. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29_PM.md` | Superseded by 2026-09-29 evening. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v8_2026-09-29.md` | Superseded by v9 (supersedes v7): R9-R07 committed, R9-R08 built; R9-I02 stays open; honest ledger with the design deviations. Claude, signed. |
| `BUILD_SLICE_MEMORY_M2_CONTROLLER_EXECUTOR_2026-09-29.md` | R9-R08: the controller executor (ownership, controller answers, stop-and-wake), D5 inherited nulls, the recording protocol; T6 measured 72 actions and 0 model calls through G3 on ft09; five deviations for ratification. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-29.md` | 2026-09-29 morning state (superseded by 2026-09-29 PM; supersedes 2026-09-28 evening): stage table, builder notes on the card builder, certified fields and the card-only Duck, handoff actions. Claude, signed. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-29.md` | Superseded by 2026-09-29 PM. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v7_2026-09-29.md` | Superseded by v8 (supersedes v6): R9-R06 committed, R9-R07 built. Claude, signed. |
| `BUILD_SLICE_MEMORY_M1_SLOT_CARD_2026-09-29.md` | R9-R07: the slot-built card (card_builder.py), certified fields, preflight; measured 25,502 → ~4,700; card-only Duck on 2/8/20-lever stress worlds; T1/T3/T5/T7/T10/T11. Claude, signed. |
| `DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md` | Superseded by v2 (RATIFIED 2026-09-28) (D1–D7): memory laws M1–M10, three tiers (record / certified world model / slot-built card), injected + pulled recall, controller executor (G0–G3 without Duck), lives and levels, instrumentation, acceptance tests T1–T11, staged build M-0…M-6. Claude, signed. |
| `DOCTRINE_FRICTION_AXIOMS_v3_2026-09-28.md` | Current doctrine (supersedes v2): A5 revised (controller executes computable moves), A6 v2 (bounded regardless of findings), memory laws M1–M10 ratified, D4–D7 recorded; A7 still proposed. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_EVENING.md` | 2026-09-28 evening state (status superseded by 2026-09-29; supersedes 2026-09-28 PM): v2 result, survey, constraints, rulings, R9-R06, handoff actions, read order. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v6_2026-09-28.md` | Superseded by v7 (supersedes v5): R9-R06…R9-R10 = memory M-0…M-4, then the M-5 package; honest ledger. Claude, signed. |
| `BUILD_SLICE_MEMORY_M0_INSTRUMENTS_2026-09-28.md` | R9-R06: replay harness + real v2 record fixture, record index, read-only memory store, turn ledger, shared gate-action recording path; ratchet table; findings. Claude, signed. |
| `REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md` | Graded ft09 guided v2: G2 closed (trigger check fired and corrected), G3 five levers confirmed, card overflow at 25,502 (per-finding growth), P not met; search order; bar budget. Claude, signed. |
| `MINE_AGENT_MEMORY_PRIOR_ART_v1_2026-09-28.md` | WO-00 mining: our own four overflows and the half-built Duck Turn Contract; external prior art (tiered memory, deterministic compaction, injected recall, game-agent memory failures) with URLs. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28_PM.md` | 2026-09-28 afternoon state (status superseded by the evening memory; supersedes the morning memory): R9-R04 committed, the R9-R05 identity finding, offline-ladder practice, the two-path export command, handoff actions. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md` | Superseded by v6 (supersedes v1–v4): revision ledger with R9-R05 and the label rule, offline ft09 ladder, preregistration additions, decisions owed (including proposed A7), honest ledger. Claude, signed. |
| `BUILD_SLICE_G3_RECOLOR_IDENTITY_AND_FT09_LADDER_2026-09-28.md` | R9-R05: entity identity survives a recolour in place and ambiguity abstains (contract §1); the ft09 ladder from the real G2 record to G4-A satisfied, offline; bar capacity; proposed A7. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-28.md` | Morning 2026-09-28 state (status superseded by the PM memory; supersedes 2026-09-27 PM): rulings of the day, revision ledger, guided-v1 evidence, A6 and A1 v2 for builders, handoff actions, read order. Claude, signed. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-28.md` | Current minimal read order and position for a new builder. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v4_2026-09-28.md` | Superseded by v5 (supersedes v1–v3): **revision ledger R9-R01…R9-I02**, where we sit, targets, order of work, decisions owed, honest ledger. Claude, signed. |
| `BUILD_SLICE_G3_BOUNDED_CARD_AND_COUNTER_TRIGGER_2026-09-28.md` | R9-R04: windowed G3 card (A6; ft09 entry card 67,939 → about 10,061 characters) and `record_trigger` with a required, record-checked `trigger` on the G2 answer (A1 v2); tests; known limits. Claude, signed. |
| `REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md` | Graded ft09 guided v1: G2 closed live under A1 with a pure mask; wrong trigger label accepted; G3 card overflow crash; P not met, G4 ungraded; frictions routed to A6 and A1. Claude, signed. |
| `DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md` | Superseded by v2. Director rulings as axioms A1–A5: counter purity (find, label, mask), no-legal-move, level boundary, continuity, guidance (stated targets). Every friction is routed here first. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27_PM.md` | 2026-09-27 rulings and evidence (status superseded by 2026-09-28; supersedes the morning memory): rulings of the day, commit ledger, evidence, two gate modes, handoff actions, read order. Claude, signed. |
| `BUILD_PLAN_G4_CLICK_COMPLETION_v3_2026-09-27.md` | Superseded by v4 (supersedes v1, v2): G2 and G4 as stated targets, G4-A/B/C, order of work, decisions owed. Claude, signed. |
| `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md` | G2 under axiom A1 (purity, not isolation; stated target in CLICK worlds; REWRITE or SILENT prediction), `legal_move_status` and the runtime watchdog (A2); real ft09 replay fixture. Claude, signed. |
| `REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md` | Graded ft09 run: G2 deadlock on the counter-only rule (effective-move counter), P not met, G4 ungraded; repair options. Claude, signed. |
| `BUILD_SLICE_G4A_GUIDED_LEVER_STUDY_2026-09-27.md` | G4-A as a stated target (`fcc7f11`): Duck chooses presses, runs read from the record with in-run confirmation, G4.3 retired from the ladder. Claude, signed. |
| `FINDING_G4_3_CONTINUITY_AFTER_PHASE1_DRAIN_2026-09-27.md` | G4.3 continuity defect after the Phase-1 drain, with a prediction filed before the ft09 output; resolved by G4-A (axiom A4). Claude, signed. |
| `UPLOAD_STATUS_G4_FT09_PHASE1_V1_2026-09-27.md` | ft09 checkpoint: full Phase-1 drain then G4.3 on a world whose levers return without a level change (Director ruling: cross-level is G9); identifiers, budget reasoning, preregistered P/C1–C7/I1–I4, stated risks (ft09 untested live; timer contamination). Claude, signed. |
| `BUILD_SLICE_G4_PHASE1_BOUNDARY_RELEASE_2026-09-27.md` | S1 deadlock fix (`8cfb782`): interrupted levers leave pending, a level transition closes the level's G4 study, G4.2 no longer SATISFIED while a lever is pending; tests including a real-data replay of the Kaggle v1 G4.2 segment. Claude, signed. |
| `REVIEW_G4_PHASE1_DRAIN_KAGGLE_V1_2026-09-27.md` | Graded S1 Kaggle run: first G3 closure on the exact model, S1 return edge confirmed live (C4 hold), E0005 orbit ended in a level transition, then an S1-hold deadlock on the interrupted lever; three candidate rulings. Claude, signed. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-27.md` | Current state (supersedes 2026-09-26 for status): S1 committed, live Kaggle test running, commit ledger, corrections, ranked risks, handoff action. Claude, signed. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-27.md` | Current minimal read order and first action for a new builder. Claude, signed. |
| `BUILD_SLICE_G4_PHASE1_DRAIN_RETURN_EDGE_2026-09-27.md` | S1 as built: classifier, return edge, G4.3 guard, seed fix, tests, deviations from the plan (no newborn append). Claude, signed. |
| `INFRASTRUCTURE_G4_PHASE1_DRAIN_KAGGLE_CHECKPOINT_2026-09-27.md` | G4 Kaggle package: authorized skip of the OpenRouter rung, committed-source packaging and secret guard, budget evidence, full pre-upload verification. Claude, signed. |
| `G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md` | Preregistered C1–C4 grading from artifacts, outcome table, and the reusable Kaggle launch procedure (`-r skip`). Claude, signed. |
| `UPLOAD_STATUS_G4_PHASE1_DRAIN_V1_2026-09-27.md` | Frozen G4 identifiers, hashes, budgets and upload log. Claude, signed. |
| `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27.md` | OPEN: API keys packaged into the G3-era Kaggle bundles; exposure, containment, Director actions. Claude, signed. |
| `tools/verify_kaggle_package.py` | Stand-alone pre-upload check: manifests, receipts, src.zip identity, offline/GPU kernel, secret scan, optional byte-identity to a commit. Claude, signed. |
| `tools/simulate_kaggle_preflight.py` | Runs a package notebook's real startup cells against a simulated /kaggle mount in three layouts (Linux). Claude, signed. |
| `ALPHA_BUILDER_OPERATING_PROTOCOL_2026-09-26.md` | Replacement-ready protocol for philosophy, repository identity, gate doctrine, engineering rhythm, evidence standards, execution, review, and the active G4.2 handoff. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-26.md` | Current execution state, proof boundary, active G4.2 run, remaining plans, and immediate handoff action. |
| `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-24.md` | Current continuity memory: North Star, repository identities, direct v2 evidence, reset repair, G3/G4 boundary, OpenRouter-first build ladder, and v3 exit. |
| `handoff/FRESH_TASK_BOOTSTRAP_2026-09-24.md` | Minimal current read order and execution boundary for a new task or collaborator. |
| `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1_2026-09-26.md` | LOCKED strategy governing G4: Phase 1 deepens each lever alone (consecutive presses to period + class, dynamic queue); Phase 2, gated on Phase-1-complete, presses lever sequences for reversal, persistence, couplings, mechanics. |
| `BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE_v1_2026-09-26.md` | The pending-lever return edge: machine-level descent controller, per-orbit classification, PHASE-1-COMPLETE signal, G4.3 re-homed behind it; slices S1..S4, exit criteria, owed tests. |
| `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-22.md` | Authoritative current implementation, v3 result, evidence boundary, and full build ladder; updated 2026-09-24. |
| `INFRASTRUCTURE_G3_QWEN36_KAGGLE_CHECKPOINT_2026-09-23.md` | Exact-Tufa-model Kaggle packaging, receipt binding, source transport, version-1 pre-model failure, version-2 recovery, and pending review boundary. |
| `runs/kaggle-ring9-g3-qwen36-compatibility-v1/REVIEW_V2.md` | Completed exact-Qwen review: vc33 gate grades, attribution and certificate failures, deadline starvation of ft09/ls20, and required repair slice. |
| `BUILD_PLAN_G3_LIVE_CLOSURE_2026-09-23.md` | Six-slice repair plan for atomic pointer attribution, mask-ready G2 handoff, lifecycle correctness, aggregate lever inventory, hardened certificate, and a one-world vc33 exit run. |
| `runs/kaggle-ring9-g3-vc33-closure-v2/REVIEW.md` | Completed v2 live evidence: automatic reset bypassed the observer, ranks 4 and 5 exposed large remote changes without admissible ownership, unresolved targets were consumed, and G3 did not close. |
| `runs/kaggle-ring9-g3-vc33-closure-v3/REVIEW_2026-09-24.md` | Completed v3 live evidence: ranks 4 and 5 became prospectively confirmed remote levers, then rank 6 exposed an unbounded known-counter retry and dossier semantic-validation gaps; G3 did not close. |
| `BUILD_SLICE_G3_TOTAL_COUNTER_MASK_AND_LEVER_FOCUS_2026-09-24.md` | Implemented mask-focused G3 slice: eligible/excluded frontier accounting, masked entity construction, defensive counter-only attribution, checkpoint grading, 328 offline tests, and passing frozen v3 replay. |
| `BUILD_SLICE_G2_STABLE_IGNORED_BASELINE_2026-09-26.md` | Superseding contract: after mask lock, counter behavior is actively ignored and cannot revise downstream products. |
| `runs/replay-g3-v3-total-counter-mask-v1/result.json` | New deterministic replay result over frozen v3 observations: rank 6 counter excluded, rank 7 next, and 31 historical counter-loop transitions create no masked entity churn. |
| `BUILD_SLICE_G3_TYPED_DOSSIER_AND_BOUNDED_AMBIGUITY_2026-09-24.md` | Implemented typed effect summaries, exact intervention/evidence validation, counter-causality exclusion, logical CLICK ambiguity bounds, unresolved coverage reports, 330 offline tests, and passing v3 dossier regrade. |
| `runs/replay-g3-v3-typed-dossier-v1/result.json` | Frozen M0009 regrade: legacy shape and counter-inclusive prose rejected; corrected 264-cell remote residue with two masked counter cells accepted. |
| `BUILD_SLICE_G2_G3_RESET_CONTINUITY_2026-09-24.md` | Current repair: mined site-only reset back-edge, exact spawn identity, runtime-history reset bridge, mask-ready G2 handoff, same-rank retry, local validation, and v3 exit criteria. |
| `UPLOAD_STATUS_G3_VC33_CLOSURE_V3_2026-09-24.md` | Frozen v3 identifiers, budgets, hashes, validation, and current external-upload boundary. |
| `DESIGN_MODEL_PORTABILITY_v1_2026-09-23.md` | Model/engine boundary, exact-checkpoint adoption protocol, current candidate roster, and incumbent Qwen compatibility lane. |
| `MODEL_LADDER_OPENROUTER_TO_KAGGLE_2026-09-24.md` | Current development model policy: fast same-generation proxy, dense Qwen3.6 rehearsal, exact Kaggle milestone, ceiling diagnostic, evidence boundaries, and required OpenRouter receipt controls. |
| `BUILD_SLICE_OPENROUTER_MODEL_PROFILES_2026-09-24.md` | Implemented OpenRouter reasoning/routing controls, request and response identity receipts, fast and dense-rehearsal profiles, complete validation, and live tool-call canary. |
| `BUILD_SPEC_G3_CONTEXT_COMPACTION_v1_2026-09-23.md` | Deterministic prompt-view compaction, persistent evidence-store boundary, request budgets, and G3 delivery acceptance criteria. |
| `BUILD_SLICE_G3_COMPLETION_CARD_AND_INVENTORY_QUERY_2026-09-25.md` | Current post-sweep delivery repair: exact v6 replay, 7,623-character completion card, paginated callable inventory, lossless evaluator boundary, and focused live exit criterion. |
| `BUILD_SLICE_G3_PRODUCTIVE_HANDOFF_2026-09-25.md` | Current handoff repair: counter-only scoped responses, terminal aggregate answers, executable expansion handles, passing frozen-v7 regrade, and G4-ready LeverInventory. |
| `variants/ring9-cybernetic-gates/ARC3-Inference/runs/20260925_043120_ring9-g3-vc33-openrouter-fast-rung-20260925-v8/REVIEW.md` | Live v8 review: G3 productive handoff passed on vc33; records the complete inventory, terminal controller behavior, passive-agenda conflict, evidence limits, and G4 boundary. |
| `MINE_G4_LEVER_SUBTREES_2026-09-25.md` | Post-v8 G4 mine: verified active dark machinery, Captain/Golden ports, executed depth evidence, human explanation standard, ordered lever-question subtree, and first-slice exit criterion. |
| `BUILD_PLAN_G4_LEVER_REACTION_GATE_2026-09-25.md` | Governing G4 build ladder and first-slice record: evidence-bound lever binding, exact effect anatomy, compact/callable delivery, 341 offline tests, passing frozen-v8 replay, and the remaining live explanation exit. |
| `BUILD_SLICE_G4_REPEATED_ACTIVATION_ORBITS_2026-09-25.md` | Implemented G4.2 CLICK slice: exact repeated lever activation, counter-masked state orbits, null/recurrence stopping law, boundary interruption, strict Duck explanation, passive-agenda suppression, 348 passing offline tests, and NAV re-contact boundary. |
| `BUILD_SLICE_G4_3_LIMITS_PERSISTENCE_REVERSAL_2026-09-26.md` | Implemented G4.3 CLICK slice: entity-local G4.2 handoff, second-null endpoint confirmation, optional scoped persistence control, exact prior-orbit restoration, original-lever re-enablement, strict explanation, and 360 passing offline tests. |
| `G4_3_FT09_CANARY_PLAN_2026-09-26.md` | Planned complementary CLICK canary: ft09 recurrence branch, prior controlled evidence, required second-period confirmation slice, preregistered criteria, and comparison boundary. |
| `REVIEW_G4_LIMITS_VC33_OPENROUTER_V1_2026-09-26.md` | Invalid G4.3 live attempt: Venice returned prose/Markdown instead of native tool calls, zero actions executed, TLS errors were secondary, and a pinned provider canary is required before rerun. |
| `G4_REPEATED_ACTIVATION_LOCAL_PILOT_RUNBOOK_2026-09-25.md` | Preregistered vc33 fast OpenRouter validation for G4.2, including exact continuation/stopping rules, Duck explanation requirements, external safety bounds, and failure classification. |
| `G4_EFFECT_ANATOMY_LOCAL_PILOT_RUNBOOK_2026-09-25.md` | Preregistered one-world fast OpenRouter checkpoint for G4.0/G4.1, including exact pass conditions and failure classification. |
| `variants/ring9-cybernetic-gates/ARC3-Inference/runs/20260925_053815_ring9-g4-vc33-openrouter-fast-rung-20260925-v1/REVIEW.md` | G4 fast v1 live diagnostic: exact mechanical closure, correct structured anatomies, E0004 prose-count mismatch, passive-agenda terminal loop, and required repair boundary. |
| `variants/ring9-cybernetic-gates/ARC3-Inference/runs/20260925_025301_ring9-g3-vc33-openrouter-fast-rung-20260925-v7/REVIEW.md` | Completed v7 live review: completion-card delivery passed, exhaustive sweep and two levers preserved, counter-only ambiguity blocked G4, and callable-handle/answer-idempotency defects exposed. |
| `BUILD_SLICE_G1_CLOSURE_RELIABILITY_2026-09-22.md` | Exact G1 answer interface, Qwen-shape normalization, full multi-color ego verifier, error visibility, runtime binding, and validation. |
| `G1_CLOSURE_LOCAL_PILOT_RUNBOOK_2026-09-22.md` | Exact one-world OpenRouter test configuration, launch command, grade boundary, and stop conditions. |
| `handoff/COLLABORATOR_INTEGRATION_CYBERNETIC_DUCK_2026-09-19.md` | Dated end-to-end onboarding guide with a 2026-09-24 supersession notice; use the new institutional memory for current execution state. |
| `CYBERNETIC_TARGET_TREE_v1_2026-09-18.md` | Governing dependency tree and definition of the gate/product lifecycle. |
| `BUILD_SLICE_UNIVERSAL_ONTOLOGY_PROMPT_2026-09-20.md` | Current prompt architecture, research basis, verification, and package boundary. |
| `BUILD_SLICE_BINDING_OPENING_PROTOCOL_2026-09-20.md` | Binding Captain protocol, strict object ranking, and shared click/collision frontier. |
| `BUILD_SLICE_DUCK_PILOTED_COLLISION_SWEEP_2026-09-20.md` | Duck-piloted embodied target contract, G1-to-G2 handoff, result dispositions, tests, and limitations. |
| `BUILD_SLICE_G2_PRODUCTIVE_CLOSURE_AND_RUNTIME_2026-09-20.md` | Provisional mask handoff, scoped no-counter disposition, runtime feasibility, and frozen ls20 package. |
| `BUILD_SLICE_G2_COUNTER_KNOWLEDGE_AND_BOUNDARY_LOCK_2026-09-22.md` | Current strict G2 explanation, prediction, recurrence, mask, and min/max boundary-lock build. |
| `G2_COUNTER_LOCK_LOCAL_PILOT_RUNBOOK_2026-09-22.md` | Prepared 48-action local `ls20` checkpoint and G2-only grading contract. |
| `REVIEW_G2_COUNTER_LOCK_LOCAL_LS20_V2_2026-09-22.md` | Completed served G2 pass, scoped quality notes, and placement of expiry consequences in G4. |
| `BUILD_SLICE_G3_ENTRY_AND_FRONTIER_HANDOFF_2026-09-22.md` | G3 registration, exact frontier/mask handoff, derived counter period, and deferred G4 seed observation. |
| `BUILD_SLICE_G3_SCOPED_LEVER_ATTRIBUTION_2026-09-22.md` | Lossless pointer/body attribution, ego/counter/ground subtraction, existential witnesses, and production-adapter boundary. |
| `BUILD_SLICE_G3_ENTITY_OBSERVATION_ADAPTER_2026-09-22.md` | Persistent entity hypotheses, conservative continuity, pre-action ownership, production observation scopes, and ego-confounded ambiguity. |
| `BUILD_PLAN_G3_LEVER_GATE_2026-09-22.md` | Governing ten-slice G3 plan, per-slice products and exit criteria, live checkpoint, and evidence language. |
| `BUILD_SLICE_G3_ENTITY_LIFECYCLE_JOURNAL_2026-09-22.md` | Per-entity lifecycle states, write authority, immutable witness retention, and entity-local reopening. |
| `BUILD_SLICE_G3_SCHEDULER_2026-09-22.md` | Strict CLICK, NAV, and HYBRID target scheduling, lifecycle evidence, and cross-gate counter monitoring. |
| `BUILD_SLICE_G3_ATTRIBUTION_DOSSIER_2026-09-22.md` | Scheduler-to-attribution wiring and the evidence-bound Duck dossier answer contract. |
| `BUILD_SLICE_G3_PROSPECTIVE_CONFIRMATION_2026-09-22.md` | Separate witness confirmation, entity-local lifecycle closure, and G4 handoff behavior. |
| `BUILD_SLICE_G3_LIVE_CERTIFICATE_2026-09-22.md` | Live checkpoint runbook and per-contract G3 certificate evaluator. |
| `G3_LIVE_CHECKPOINT_RUNBOOK_2026-09-22.md` | Controlled served-run procedure, trace retention, stopping rule, and grading language. |
| `G3_THREE_WORLD_ARC_ONLINE_PILOT_2026-09-22.md` | Focused `ls20` / `vc33` / `ft09` behavioral pilot before a Kaggle sweep. |
| `variants/ring9-cybernetic-gates/ARC3-Inference/configs/g3-three-world-openai.json` | Dedicated three-world OpenAI-key pilot configuration; contains no key. |
| `BUILD_SLICE_G3_PRERUN_REVIEW_CORRECTIONS_2026-09-23.md` | Closes contradicted-confirmation, prospectivity, NAV-fixture, and boundary-retry findings before live execution. |
| `REVIEW_COLLABORATOR_G3_LEVER_LIFECYCLE_2026-09-22.md` | Accepted G3 lifecycle guidance, corrections to slice order and gate scope, entity-continuity requirement, and revised build ladder. |
| `BUILD_RHYTHM.md` | Repeated engineering rhythm: step back, mine, specify, build one slice, validate, then reassess. |

## 3. Present North Star

Duck is an LLM-centered ARC investigator controlled by a gated cybernetic targeting system. Its
pre-win objective is to explore the local world's physics through interaction and record keeping.
The dependency spine is:

```text
G0 action surface
-> G1 ego
-> G2 counter
-> G3 levers
-> G4 reactions and terrain
-> G5 environmental forces
-> G6 scoped inertness
-> G7 counter-masked novelty exploration
-> G8 observed win explanation
-> G9 cross-level transfer
```

Each gate gets one narrow question, authorized probes, lossless evidence, an explanatory product,
a competing model and falsifier, and prospective support where the gate requires it. A later gate
does not receive semantic credit when its prerequisite was not satisfied. An integrated later-gate
implementation may still be exercised in the same checkpoint to expose handoff and stopping
friction.

The win is never guessed. It is admitted only from an observed terminal transition. Duck then
describes that observed event with the physics grammar and stable laws it built. On a later level,
that description becomes a falsifiable hypothesis rather than guaranteed truth.

## 4. Current prompt design

The active gated prompt has three layers:

1. **Universal ontology:** the grid as a flip book of integer states; literal pixel arithmetic;
   entities and worldlines; transformations; control archetypes; levers; reactions; hidden state;
   environmental forces; scoped inertness; observed wins; and transfer.
2. **Cybernetic mission:** discover physics through interaction; read metadata and branch by
   world type; run click-everything or Delphi-then-collide-everything in the strict controller
   ranking; explain mechanisms and limits; and accumulate versioned laws that reopen under
   contradiction.
3. **Dynamic gate context:** the single binding GoalCard, admitted products and evidence, unmet
   requirements, and next authorized operation.

The ontology supplies a language for hypotheses. It does not tell Duck which mechanisms exist in
the current world. The controller enforces focus and closure; observations establish world facts.

The active source contains this prompt upgrade. Its latest 2026-09-25 offline command passes 341 tests
when the two explicitly online/native suites are excluded and the vendored TAAF source is on
`PYTHONPATH`. The completed single-world
Kaggle reliability package confirmed prompt delivery. The later local OpenRouter `ls20` pilot
confirmed that the served Duck used the gated protocol through G1 closure and G2 entry.

## 5. Current gate status

| Gate/layer | Status | Evidence boundary |
|---|---|---|
| Harness and G0 | **LIVE CONFIRMED** | Clean G0 v2 Kaggle checkpoint on vc33, ft09, and ls20. |
| G1 Ego | **LIVE CONFIRMED ON ONE LOCAL ls20 PILOT** | Ordered Delphi probes, explanation, full-pattern prospective demonstration, and `EgoLaw` all completed. |
| G2 Counter | **LIVE CONFIRMED (vc33, ls20); A1 STATED TARGET LIVE CONFIRMED ON ft09 (R9-R03, 2026-09-28); TRIGGER LABEL (A1 v2) COMMITTED (R9-R04, `8319853`)** | ft09 guided v1: Duck-chosen `COUNTER_REWRITE` prediction supported, pure mask locked as baseline (`REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md`). The accepted label contradicted the record; R9-R04 requires the trigger to agree. |
| Universal prompt | **LIVE CONFIRMED AS DELIVERED** | Present in the completed ls20 prompt trace; semantic benefit remains bounded by the failed G1 exit. |
| Binding opening protocol | **LIVE CONFIRMED FOR NAV ENTRY** | G2 received the demonstrated ego footprint, bound rank-1 object `[32,20]`, and admitted two approach actions. CLICK and HYBRID remain unconfirmed. |
| G1 closure reliability | **LIVE CONFIRMED ON ONE LOCAL ls20 PILOT** | Visible errors enabled correction; the exact multi-color prediction was accepted and supported. |
| G2 productive closure/runtime | **LIVE CONFIRMED ON `ls20`** | The served run completed recognition, prediction, recurrence, masking, boundary focus, and extremal reset detection. |
| G3 broad lever location | **LIVE CONFIRMED ON vc33 (OpenRouter v8; Kaggle 2026-09-27); SCRIPTED BY RULING; ft09 CARD OVERFLOW FIXED (R9-R04, `8319853`); ft09 RECOLOUR IDENTITY FIXED OFFLINE (R9-R05); ft09 LADDER PASSES OFFLINE** | vc33 v8 completed the ranked click sweep, accepted one inventory with 2 confirmed levers and 8 scoped no-lever responses, reported `SATISFIED`, and handed off with `WAIT_FOR_NEXT_TARGET`. |
| G4 per-lever study | **G4.0/G4.1 LIVE CONFIRMED (vc33); G4-A STATED TARGET BUILT (R9-R02, `fcc7f11`), NOT YET LIVE** | G4 is a stated target (Duck chooses presses; runs read from the record; confirmation in-run). G4.3 retired; G4-B (R9-R06) and G4-C (R9-R07) planned. ft09 G4-A satisfied offline under the recorded control law (`tests/test_ft09_ladder_offline.py`). See `BUILD_PLAN_G4_CLICK_COMPLETION_v5_2026-09-28.md`. |
| G5-G9 | **PLANNED** | Remaining gates still require port-first slices. |

Use `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-22.md` for detailed claims and exit decisions.

## 6. Active contracts and build records

These documents remain active within their stated scope:

- `G1_PRODUCT_AND_G2_ENTRY_CONTRACT_2026-09-19.md` — G1 product and per-world exit contract,
  updated to reflect integrated engineering without weakening prerequisite grading.
- `BUILD_SPEC_G2_EVALUATOR_v1_2026-09-19.md` — receipt-bound G2 evaluation contract.
- `BUILD_SLICE_G1_EXIT_AND_G2_EVIDENCE_KERNEL_2026-09-19.md` — click-only G1 boundary correction
  and G2 evidence kernel.
- `BUILD_SLICE_H3B_FOOTPRINT_VERIFIER_2026-09-19.md`,
  `BUILD_SLICE_H4_ADAPTIVE_DELPHI_COVERAGE_2026-09-19.md`, and
  `BUILD_SLICE_H5_BEHAVIORAL_EVALUATION_2026-09-19.md` — G1 verification slices.
- `REVIEW_H3_TRANSFORMATION_LEXICON_PIXEL_ARITHMETIC_v1_2026-09-19.md` — transformation and
  pixel-arithmetic port analysis.
- `MINING_INDEX_PROBE_STRATEGY_v1_2026-09-20.md` — locations of reusable probe machinery.
- `REVIEW_G1_CLOSURE_LOCAL_LS20_V2_2026-09-22.md` — direct review of the first successful G1
  closure and the G2 controller contradiction it exposed.

Their authoring-time status statements may describe the frontier when the slice was created.
Explicit update notices and the current status map govern later execution claims.

## 7. Frozen package and run truth

The completed G2-v2 execution is bound to:

- package: `kaggle/ring9-g2-counter-checkpoint-v2/`;
- launch record: `runs/kaggle-ring9-g2-counter-checkpoint-v2/LAUNCH_RECORD.md`;
- notebook version: 2;
- package SHA-256: `a4cd720994a5a65ca02b046dd1bd867308ff2e46563f2f54b3f4d346d53f318a`;
- source-manifest SHA-256: `bfbc33fa45e8496a35813afb2c0e28acca06eb9578d8fced0e801a8e812610cf`.

That package passed 269 tests at freeze time. The active source later reached 270 through the
prompt slice and 273 through the binding-opening slice. The current active source's 2026-09-25
offline command passes 341 tests after the G3 stack, reset continuity, OpenRouter receipts,
compaction, batching, transport hardening, and the G3 completion-card slice when the two
explicitly online/native suites are excluded and the vendored TAAF source is on `PYTHONPATH`.
All claims are correct because they refer to different artifacts and test environments.

The newer completed single-world execution is bound to
`kaggle/ring9-g2-reliability-ls20-v1/` and reviewed at
`runs/kaggle-ring9-g2-reliability-ls20-v1/EVALUATION.md`. Its package SHA-256 is
`c48ee329cc4f90d908cad8114939814524cfdf7d66ed45c8fa394c9586`; its source-manifest SHA-256 is
`e4005f1722aacd79948f1ca1b0c645757f24b943dfa2573133995b61c904a47e`. The active source now
passes 286 tests after the G1 closure repair. None of those later bytes are part of the frozen run.

The executed run review is
`runs/kaggle-ring9-g2-counter-checkpoint-v2/REVIEW.md`. It records zero cleared levels, vc33's
strong partial counter result, ft09's unresolved stall, ls20's cancellation, and the mismatch
between the declared per-world runtime and the notebook-wide soft deadline.

Run directories, launch records, evaluation reports, receipts, manifests, and downloaded notebook
outputs are execution evidence. Treat them as immutable unless a correction is explicitly labeled
and preserves the original fact. Never infer model behavior from source code that was not present
in the executed package.

## 8. Historical plans and prior art

The following classes are retained for provenance and mining, not current status:

- `BUILD_PLAN_CYBERNETIC_GATED_DUCK_v1_2026-09-17.md` and the dated G0/G1 plans and status maps;
- `CURRENT_BUILD_MAP_CYBERNETIC_DUCK_2026-09-19.md` and
  `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md`, which predate the completed ls20 diagnostic
  and G1 closure repair;
- Ring 8 and earlier North Stars, work orders, reports, and handoffs;
- `variants/ring8-*`, `variants/ring7*`, `variants/ring6*`, and packaged copies beneath
  `kaggle/` and `runs/`;
- `/Users/stephenkaskin/Desktop/virelai-golden/`, the separate deterministic no-LLM solver.

Mine these sources before building each gate. Port useful detectors, evidence structures,
transform vocabularies, control hooks, and evaluation methods with provenance and limitations.
Do not inherit their old controller policy or promote builder reports to direct observations.

`handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-17.md` remains historical operational memory. Its
current successor is `handoff/TECHNICAL_INSTITUTIONAL_MEMORY_2026-09-24.md`. Neither document
overrides later user direction.

## 9. Evidence language

Use these labels consistently:

- **LIVE CONFIRMED:** a completed served-model execution directly demonstrated the claim; state
  whether it was Kaggle or local and name the exact run.
- **LIVE DIAGNOSTIC:** a live trace exposed behavior or friction but did not meet the gate contract.
- **BUILT, LIVE UNCONFIRMED:** active source implements the feature and local tests pass, but the
  served model has not demonstrated it in a complete checkpoint.
- **PLANNED:** no active Ring 9 implementation exists.
- **BUILDER REPORT:** a report from another development process, not independently observed here.
- **HYPOTHESIS:** an explanation or expected benefit still requiring evidence.

Keep source variants, packaged copies, and actual executed artifacts distinct. Compare runs only
when model, world set, budgets, passes, concurrency, package identity, and evaluation scope are
explicitly controlled or the differences are clearly stated.

## 10. Next execution decision

The bounded local OpenRouter G1 pilot is reviewed at
`REVIEW_G1_CLOSURE_LOCAL_LS20_V2_2026-09-22.md`. The completed G2 counter-lock pilot is reviewed
at `REVIEW_G2_COUNTER_LOCK_LOCAL_LS20_V2_2026-09-22.md`. It passed G2 within the counter gate's
scope. The G3 entry, attribution kernel, entity/lifecycle contract, production observation
adapter, world-type scheduler, dossier contract, prospective confirmation, working-view
compaction, completion card, callable inventory, and live certificate evaluator are built. The
vc33 v7 live run completed the eligible sweep and delivered the compact card beyond the former
overflow boundary. The productive-handoff slice now regrades pure counter-only responses as scoped
no-lever observations, makes the accepted aggregate answer terminal, and aligns expansion handles
with the keyword-only callable interface. Frozen-v7 replay emits a satisfied `LeverInventory` with
two confirmed levers, eight scoped nulls, zero bounded unknowns, and one counter exclusion. The
next execution decision is one focused vc33 live handoff confirmation. G4 reaction typing is the
next semantic build after that confirmation.
