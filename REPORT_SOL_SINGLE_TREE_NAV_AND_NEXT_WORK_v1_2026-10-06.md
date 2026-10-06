# Sol report: single tree, NAV line, submission exposure, and next work

**Type:** `ALPHA_BUILD_REPORT` · **v1** · **2026-10-06**
**Author:** Sol (Alpha build seat, NAV line), signed
**Source read first-hand:** `ring9-unified` at `b1a4d71`; current branch adds only Sol's ls20 execution review at `a382f3a` before this report
**Evidence notation:** **COMMITTED** means the claim is in the cited source or commit. **BELIEVED** means it is an inference and states the observation that would settle it.

## 1. The single tree

1. **COMMITTED — one ordered epistemic ladder.** The registry orders G0 action metadata, G1 ego, G2 counter, G3 lever inventory, G4.1 reaction anatomy, G4-A orbits, G4-B relations, G4-C law, then `PLAY-NORMAL` (`virelai_gates.py:2020-2106`, `:6427-6474`). Each level rebuilds LEVEL-tier adapters while the game keeps its life record, frozen prior levels, transition index, and capability secret (`virelai_gates.py:6430-6490`; `life_record.py:31-89`).

2. **COMMITTED — shared spine, actuator branch.** G0 is always metadata-derived. `next_owned_step()` then sends NAVIGATION and HYBRID to `_nav_step`, CLICK to the ordinary path, and unknown types to Duck (`controller_executor.py:119-139`). G2's certified mask is reused downstream without reopening counter study; later transitions still enter G3's entity ledger (`virelai_gates.py:6696-6715`). G3 compiles one counter-filtered ranked roster and branches only in execution: coordinate click for CLICK, embodied approach/contact for NAV, CLICK then NAV for HYBRID (`virelai_gates.py:2916-3013`, `:3434-3495`). G4 consumes the same attributed reaction/anatomy/orbit/relation/law contracts, while NAV resolves each intervention into a contact procedure rather than raw action equality (`BUILD_PLAN_G4_NAV_COMPLETION_v1_2026-10-01.md:72-97`).

3. **COMMITTED — ownership is recomputed every frame.** The controller owns certified answers and exact bound actions; Duck owns explanations, ambiguous or unbound choices, G4 orbit explanations, unresolved predictions, and normal play (`controller_executor.py:14-40`). `run_controller_turn()` asks ownership before a prompt, executes exactly one environment action, then returns so the new frame is read (`controller_turn.py:52-95`, `:155-210`). A wake is delivered only if the recomputed next step belongs to Duck; otherwise it is logged and controller ownership continues (`controller_turn.py:71-85`). A gate with no legal move is forced into `PLAY-NORMAL`; a completed built ladder stops cleanly (`controller_turn.py:65-70`, `:98-107`; `controller_executor.py:93-116`).

4. **COMMITTED — CLICK, NAV, HYBRID behavior.** CLICK performs the ranked click sweep. NAV uses G1 bearings to approach and make target-bound contact attempts. HYBRID starts in CLICK and switches to NAV when the click roster is exhausted (`virelai_gates.py:3434-3460`). A changed board may reopen a previously bounded reachability hypothesis, but only when the target's actual cells or identity signature changed (`virelai_gates.py:3141-3268`).

## 2. NAV line status

Ranked by what blocks live use:

1. **BUILT\* — NAV-N0, structured control/intervention foundation.** `GateAnswer.action_law_specs` and evidence-derived `NavControlMap` exist (`virelai_gates.py:201-218`, `:6492-6507`). The representation is incomplete in production: G1 may close from prose laws with `{}` specs. The unified ls20 run directly observed that failure (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md:27-32`, `:58-69`).

2. **BUILT\* — NAV-N1/N2, deterministic routing and execution.** The controller has route/contact ownership, target-bound intervention identity, refused-contact handling, and one-action execution (`controller_executor.py:166-260`; `controller_turn.py:155-210`). The live unified canary never reached a route because the certified bearing map was empty; its one-request fallback exhausted 256 output tokens and stopped (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md:13-17`, `:32-33`).

3. **PARTIAL — NAV-N3, G3 completion.** First positive attributed contact is the discovery law and confirmation moved to G4-A; bounded `PRESUMED_UNREACHABLE` releases a target and can reopen on relevant world change. N5.1 supplies one historical live positive contact at transition 18; N5.3 proves the first-witness trajectory synthetically. No unified Qwen3.6 live trace has yet executed a contact, completed the roster, or opened G4 (`RECORD_RING9_SINGLE_TREE_AGREEMENT_v1_2026-10-05.md:31-46`; unified ls20 review `:35-46`).

4. **BUILT, LOCAL/HISTORICAL ONLY — NAV-N4/N5, reaction anatomy and repeated contact orbits.** The shared G4.1 and G4-A contracts and NAV controller routes are implemented, and dedicated tests pass; the NAV plan explicitly records that live validation remained pending (`BUILD_PLAN_G4_NAV_COMPLETION_v1_2026-10-01.md:3-14`, `:99-115`).

5. **PARTIAL — NAV-N6, relations.** G4-B can consume record-derived CLICK presses, but `level_record.presses()` identifies a press from click coordinates and masks only the counter (`level_record.py:94-130`). The agreed NAV intervention-plus-residue record seam exists in the single tree, but NAV-aware `presses()` remains Claude's step 7 (`RECORD_RING9_SINGLE_TREE_AGREEMENT_v1_2026-10-05.md:53-70`, `:102-112`). Until it lands, NAV G4-B safely falls back to Duck.

6. **BUILT, LOCAL/HISTORICAL ONLY — NAV-N7, law tests; PARTIAL — NAV-N8, live checkpoint.** G4-C shares the target-bound NAV execution path, but no unified live NAV run has reached it. The current live checkpoint proves G0-G2 and the controlled G3 stop, not NAV G3/G4 (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md:11-17`).

**What N5.1 proves.** **COMMITTED:** a real ls20 trace produced a positive contact at transition 18, and its fixture can exercise full G0-start replay. **It does not prove:** current Qwen3.6 G1 emits structured laws, the unified controller can route to that contact, the full roster closes, or NAV G4 works live.

## 3. Honest ledger

1. **COMMITTED — wrong production boundary:** G1 accepts explanatory movement prose without a nonempty machine-readable bearing product. Synthetic tests supplied richer structured specs than production did. This is the present highest blocker (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md:58-79`).

2. **COMMITTED — brittle fallback:** the missing-bearing route checkpoint allows one required-tool model request capped at 256 output tokens; the canary exhausted it without a tool call and stopped. Longer game time cannot repair that immediate stop (same review `:15`, `:32`, `:69`).

3. **COMMITTED — NAV record relations incomplete:** the row-level NAV identity/residue seam is present, but `level_record.presses()` remains click-shaped and would count ego motion as an elsewhere effect (`level_record.py:108-130`; single-tree agreement `:53-70`).

4. **COMMITTED — no current live proof of the unified NAV ladder after G2:** the canary took zero G3 navigation steps and attempted no contact (ls20 review `:30-33`).

5. **COMMITTED — repeated observation is harmless, but unpinned by a focused regression.** G4 NAV first calls G3 observation scope and then applies the counter baseline. `EntityLedger.observe()` returns the existing transition on a repeated transition id, so versions do not increment twice (`entity_observation.py:377-380`, `:443-466`). G3 separately guards observed ids (`virelai_gates.py:3122-3129`). Reopening compares actual old/new cells and ignores STILL version increments (`virelai_gates.py:3168-3192`). **BELIEVED:** a small double-observation test is worthwhile documentation; it should show byte-identical ledger versions and one reopening. That test would settle the belief.

6. **COMMITTED — HYBRID remains less proven than either pure arm.** The mu return after the NAV handoff is implemented, but no full live HYBRID scheduler trace establishes CLICK-to-NAV roster accounting and G4 continuation (`3f2531b`).

## 4. Submission-mode exposure

1. **COMMITTED — 600 seconds.** On current Qwen3.6, ls20 reached G3 in about 343 behavior seconds, then stopped immediately on the missing-bearing fallback. A 600-second slice therefore reaches the defect but does not test contact. A CLICK world can progress farther because it has no bearing dependency. A HYBRID world can progress through its CLICK arm and becomes exposed when NAV routing is needed. A world whose type is unsupported is handed to Duck (`controller_executor.py:132-139`) and consumes model time rather than deterministic controller throughput.

2. **COMMITTED — 2,700 seconds.** More wall time does not help the current ls20 failure because the route checkpoint stops after its configured failed request. Once the G1 bearing product is repaired, 2,700 seconds should expose actual routing, release/reopen, contact, G4, and play; that outcome is **BELIEVED** until a canary runs.

3. **COMMITTED — ten games.** SUB-1 starts ten game sessions and relies on server batching; S-3 priority admission is explicitly absent (`BUILD_SLICE_SUB_1_SUBMISSION_MODE_2026-10-06.md:58-67`). Controller turns need no model slot, so CLICK/controller-heavy games remain cheap. NAV's current G1 explanation and route fallback, HYBRID's judgments, and unresolved world types compete for model service. **BELIEVED:** request queues will disproportionately truncate NAV/HYBRID Duck turns under the fixed per-game clocks; the 110-clone dry run's per-game cutoff and ladder-rest table will confirm or refute it.

4. **COMMITTED — concurrency state.** Every gate machine creates its own adapters, ledgers, targets, life record, capability state, and transition index (`virelai_gates.py:6430-6475`). The inspected NAV modules contain constants and pure functions but no module- or class-level mutable runtime cache. S-1 currently proves five CLICK records only (`test_s1_concurrent_replay.py:24-70`). Add ls20 N5.1 using the ordinary `replay(load_record(...), measure=False)` call: `record_replay.replay()` reads the fixture's `protocol.replay_from_g0` and constructs `CyberneticGateMachine` automatically (`record_replay.py:212-232`). Add the G3 adapter snapshot to the digest because it contains NAV entity, scheduler, terrain, reachability, contact, and bounded-ambiguity state; also include `lives.summary()` and `levels` for cross-life/level state.

5. **COMMITTED — idle/loop/play exits.** NAV can wake Duck when no evidence-bounded route exists (`controller_executor.py:201-216`, `:233-255`), stop at the route retry guard (`solver.py:557`), or move to `PLAY-NORMAL` when `legal_move_status()` is false (`controller_turn.py:98-107`). It cannot silently spin one controller action plan: each controller turn executes at most one action and rereads the frame (`controller_turn.py:52-95`). `PLAY-NORMAL` can be reached without a gate legal move by design; that is a safe throughput disposition, not proof the gate was satisfied.

## 5. Learn-to-win

1. **COMMITTED — foundations already present.** Counter-masked world addresses, transition evidence, entity continuity, lever reactions/orbits/relations/laws, life/level records, level freeze/carry, and normal-play recording already provide much of W-1's input substrate and W-4/W-5's storage substrate (`g4_relations.py:155`; `virelai_gates.py:6439-6490`; `play_gate.py:106-235`). **They are not the W products themselves.** The plan explicitly said none of W-1 through W-7 had been built at its authored base (`BUILD_PLAN_PORTS_AND_PILLARS_v1_2026-10-04.md:5-8`), and the named `win_relations.py`, `win_referee.py`, `win_ledger.py`, and `g8_explain.py` modules are absent at `b1a4d71`.

2. **COMMITTED — order.** Build W-1 relation extraction first, W-2 code-only transition referee second (R-6), W-4 win ledger third, then W-3 observed-goal explanation, W-5 cross-level goal carry, W-6 offline vc33 proof, and W-7 live level-3 validation. Only then open the separately named `ACT_ON_GOAL` project under R-7. This puts the referee before both explanation and action selection and keeps observed wins distinct from guessed goals.

3. **COMMITTED/BELIEVED — NAV requirements beyond CLICK.** CLICK can instantiate a candidate intervention as one coordinate action. NAV must bind a goal-relevant target to the current ego, find a demonstrated-ground route, distinguish approach from terminal contact, carry a target/procedure identity across several steps, and replan after any world delta that changes passability (`BUILD_PLAN_G4_NAV_COMPLETION_v1_2026-10-01.md:83-97`, `:186-245`). **BELIEVED:** `ACT_ON_GOAL` should use the existing NAV procedure/epoch contracts as its actuator boundary rather than inventing a second navigator. A synthetic planner test plus one live observed-goal replay would confirm this.

## 6. Explicit disagreements or corrections to Claude's documents

1. **`REVIEW_RING9_UNIFICATION_v1`: correction, now historical.** Its original F3 statement that NAV evidence was synthetic only is superseded: N5.1 has a live transition-18 contact and now has a replay fixture; N5.3 remains synthetic and ungraded. The agreement already records this correction (`RECORD...:43-46`). Its F1 is fixed; its warning about NAV record-derived G4-B remains current.

2. **`RECORD_RING9_SINGLE_TREE_AGREEMENT_v1`: agreement with one status update.** I agree with the architecture, ownership, and first-witness law. Section 5's ls20 criteria remain valid but were ungraded/failed before contact because the canary exposed the earlier G1 structured-bearing defect (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md:35-46`).

3. **`REVIEW_RING9_CARRY_VC33_V8_KAGGLE`: scope correction only.** I agree with the artifact grade. It validates controller-first CLICK G4 on pre-merge `c9b246b`, not unified first-witness G3 and not NAV (`REVIEW...:3-8`, `:80-84`). Its prompt-overflow concern is narrowed by SUB-1: context trimming already prevents overflow, though early history can be lost (`BUILD_SLICE_SUB_1...:27-34`).

4. **`BUILD_SLICE_SUB_1_SUBMISSION_MODE`: one incomplete criterion.** I agree with the packaging repair, deadlines, and settings. S-1 is not a complete concurrency proof for the submission population while its record set is CLICK-only (`test_s1_concurrent_replay.py:24-31`). Adding ls20 with the NAV adapter/life/level digest closes that gap.

5. **Dry-run upload record: status correction, no design disagreement.** At the inspected worktree the upload record is modified and intentionally uncommitted while Claude appends the notebook push result. Its committed portion proves package verification and dataset readiness, not a completed Kaggle dry run (`UPLOAD_STATUS...:83-97`). I did not edit it.

6. **Chronology correction requested by Claude.** I moved `main` to `e8d1f92` only after the full Mac suite passed **610 passed, 1 skipped** on that tree and after checking that the main checkout's existing tracked changes did not overlap the fast-forward. The earlier suite attempt found two stale replay expectations; I corrected them, reran the full floor, pushed `ring9-unified`, then fast-forwarded and pushed `main`. The statement that `main` moved before that floor is incorrect.

## 7. Proposed next work and ownership

1. **Code altitude — Sol, immediate:** repair G1's production control product. Deterministically derive/persist the observed displacements, require a nonempty certified bearing map before NAV can leave G1, add the exact Qwen3.6 prose-shaped regression fixture, and prove the first G3 approach is controller-owned. Then run a short ls20 canary whose exit is one real approach/contact disposition.

2. **Code altitude — Claude, after Sol's fixture amendment:** extend S-1 with ls20 and the NAV digest above; then build NAV-aware `level_record.presses()` and record-derived G4-B against the real fixture, preserving replay answer identity.

3. **Architecture altitude — shared review, one writer per window:** grade the 110-clone dry run for contention and ladder rests; do not interpret its score as solver ability. Repair only demonstrated submission failures before the scored package.

4. **Code altitude — split new-file work:** begin W-1/W-2/W-4 in new modules while the NAV canary queues. Sol owns NAV actuator contracts and hook review; Claude owns the code-only referee/CLICK integration unless the Director revises the split.

5. **Plan altitude — Director ruling after W-7:** open `ACT_ON_GOAL` as its own named project. Its first NAV slice must compile an observed goal into a target-bound contact procedure and use predict-act-compare; it must never infer the win before observation.

— **Sol**, Alpha build seat (NAV line), 2026-10-06
