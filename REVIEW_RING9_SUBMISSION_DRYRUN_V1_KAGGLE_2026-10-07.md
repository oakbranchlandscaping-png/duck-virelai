# Review: ring9-submission-dryrun-v1 on Kaggle (110 competition clones, 10 at a time)

**Date:** 2026-10-07
**Author:** Claude (Alpha build seat, click line), signed
**Package:** `kaggle/ring9-submission-dryrun-v1`, source `d751a5b`. It predates Sol's cell-site repair `4970953`.
**Graded against:** `UPLOAD_STATUS_RING9_SUBMISSION_DRYRUN_v1_2026-10-06.md` §4, which covers:
- C-1 to C-7;
- the infrastructure criteria;
- the measurement of NAV and HYBRID clones.

**Output:** `runs/kaggle-ring9-submission-dryrun-v1/output`, downloaded by the Director on 2026-10-07.

**Method:** artifact state, read on the Director's disk.
- **Kernel log:** read in full, for all 110 games.
- **Per-game artifacts:** turn ledgers, gate answers and gate events for k000 to k054, which is the first download page.
- **Cross-game check:** 486 files of those 55 games.
- **Not yet read:** the rest of the artifacts and the execution receipt. They are on the next download page (§6).

Nothing was rerun.

**Clone mapping** [OBS, `taaf/competition_arcade.py:48-56`, `:104-105`]: clone `kNNN` plays the official game at index NNN mod 25.

## 0 · Verdict

**The machinery passed.**
- All 110 games started, played and were finished by the harness, with no crash.
- No artifact carries another game's identity.
- The run ended about 22 minutes before its soft end, with nothing in flight.
- The largest prompt was 40,819 tokens.
- vc33 cleared at least level 1 on every clone.
- The whole notebook used **1.83 GPU-hours** (6,600 s), against 2.3 expected.

**The solver did not hold up under the submission profile.** Two code defects and one disposition question decide most outcomes:

| ID | Altitude | Finding |
|---|---|---|
| **D-1** | code, critical | **ACTION7 does not exist for the harness.** `inference/agent/action_names.py:7-15` maps ACTION1 to ACTION6 and RESET, but not ACTION7. The engine has ACTION7 (`arcengine.GameAction`). So every ACTION7 press, by the controller or by Duck, is refused with "Unknown action at index 1: 'ACTION7'" (`solver.py:762-769`). |
| **D-2** | code, critical | **After an environment refusal, the controller spins on a used probe token.** It retries the same bound probe with a consumed token. `_gate_probe_begin` refuses it ("This probe_token has already been used"), the wake keeps controller ownership, and the solver loop retries at once (`controller_turn.py:66-87`, `:172-183`; `solver.py:517-528`). **18 of 110 games** (lf52, bp35, ar25 and sk48, every clone) spun about 12,000 to 18,500 times each, with no action and no Duck turn, until their 600-s slice ended. Axiom A2 (I11) failed: no watchdog fired. |
| **D-3** | architecture, for the Director | **A controlled stop ends the game.** 34 of 110 games ended on a controlled stop: 16 `no_progress_tool_loop`, 14 `contract_repair_loop`, 4 `g3_route_retry_exhausted`. **8 of them at 0 actions.** In a scored run, each forfeits the rest of its slice. This is P3 of `REVIEW_SOL_SINGLE_TREE_REPORT_v1`, now measured. |

D-1 and D-2 are one chain: the first ACTION7 probe fails (D-1), and the controller then spins on it (D-2). They are listed separately because each needs its own fix. D-2 is a general defect: any environment refusal of a controller action triggers it, not only ACTION7.

## 1 · Grades

| Criterion | Grade | Evidence |
|---|---|---|
| Setup, U-SRC, I5, I8 | **PASS** | `source manifest verified (230 files)`; Python 3.12; the wheelhouse installed; vLLM served `vrfai/Qwen3.6-27B-FP8` from the Director's dataset; `TRUE_SUBMISSION=False`; a dry-run competition arcade; `competition games verified: 110 unique ids`; `G0-G4 execution receipt verified`; `controller executor on`; soft end at setup + 2 h |
| **C-1** no crash | **PASS** | 110 of 110 `[finished]` lines, 110 unique ids, every state `gave_up`. That is the harness's label for any stop short of a win, whether by slice, cap or controlled stop. None is `crashed`. |
| **C-2** gate records, GATED or FREE_PLAY | **PASS, with a note** | Every game has gate answers. The 8 games that ended at 0 actions have no transitions, so they have nothing to receipt. Two of the 55 games read reached `PLAY-NORMAL`. |
| **C-3** no cross-game mixing | **PASS** (55 games read) | 486 artifact files: no `game_id` and no file stem names another clone. The other 55 games are pending (§6). |
| **C-4** ends before the soft end, nothing in flight | **PASS** | Games ran from 701 s to 6,581 s of notebook time; the soft end was 7,901 s. The last game finished before the benchmark closed, and teardown followed at 6,593 s. |
| **C-5** turns cut by the clock under contention | **REPORTED** | 254 Duck turns in the 55 games read; 122 (48%) ended on the 60-s turn budget. In v8, alone on the GPU, 21 of 22 play turns were cut. Contention did not make turns worse. |
| **C-6** prompt tokens under 65,536 | **PASS** | The largest per-turn prompt was 40,819. |
| **C-7** vc33 clears level 1 | **PASS** | Clones k010, k035, k060 and k085 cleared 2, 1, 1 and 2 levels. |
| I0, I3 | **PASS** | No forbidden module (packager guard); per-game turn ledgers, gate answers, probe envelopes and outcomes were written. |
| I2 receipt | **PENDING** | `execution_receipt.json` is on the next download page. |
| **I11** (A2: no idling without a legal move) | **FAIL** | D-2: 18 games idled in a refusal loop for their full slice. |
| Score | — | Every local score is 0.00, including clones that cleared levels. **This is an artifact of the simulator, not a failure:** the arcade hides baselines (`per-level=24/?,38/?…`), so no level can be scored locally. 11 levels were cleared in total, across 9 clones. |

## 2 · Where each game ended

The clones of one game behave almost identically: the controller is deterministic, and Duck varies little.

| Game ended on | Games (all clones) |
|---|---|
| D-2 refusal spin in G1, 0 Duck turns | lf52, bp35, ar25, sk48 |
| Controlled stop at G1 with 0 actions (`contract_repair_loop`: Duck's click-only G1 explanation rejected twice) | sb26, plus one held-out game |
| Controlled stop in G1 (`no_progress_tool_loop`: Duck repeated read-only tool calls) | most clones of cn04, m0r0 and cd82; half of sc25; one clone each of tu93, sp80, g50t and tr87 |
| Controlled stop in G1 or G2 (`contract_repair_loop`, after some actions) | two clones each of wa30 and dc22; one clone of a held-out game |
| `g3_route_retry_exhausted` (the G1→G3 NAV boundary, repaired after this package) | ls20 |
| 600-s slice inside G1, G2 or G3 (5 to 13 Duck turns of 60 to 120 s each) | wa30, tu93, sp80, ka59, dc22, g50t, tr87 (the remaining clones of each) |
| 600-s slice inside G4-A | tn36, r11l, vc33, ft09, and one held-out game |
| Reached `PLAY-NORMAL` | re86 |
| Level cleared | vc33 (2, 1, 1, 2 levels), and one held-out game |

**Reading the table.** CLICK worlds reach G4-A within 600 s. The worlds that stall do so in G1: on Duck's explanation turns, on the two loop guards, or on D-1 and D-2. In the 2,700-s submission slice, the slice-limited rows would get about 4.5 times as long. The D-1, D-2 and controlled-stop rows would not change at all, because they end or spin regardless of time.

## 3 · Held-out exposure (declared)

The prereg's held-out worlds are `lp85`, `s5i5` and `su15` (`PREREG_SMALL_MODEL_GLASS_ENGINE_v2` §held-out). They are among the 25 official games, so a 110-clone run plays them.

While grading I read our own solver's outcomes on them: levels cleared, the gate each game ended on, and its stop reason. I opened no frame, mechanic or reference of theirs. In this document they are masked by name.

**Recommendation for the Director.** The dry-run and submission grading should report held-out clones only in aggregate, from a script that masks them before any build seat sees per-game rows. Otherwise each graded run becomes held-out leakage into development. The fixes proposed here are each motivated by named development worlds (D-1, D-2: lf52, bp35, ar25, sk48; the G1 contract stop: sb26), never by a held-out row.

## 4 · What to fix before the scored package

**SUB-2, submission hardening.** Code-level; Claude proposes to build it, with fail-first tests.

1. **D-1.** Add `ACTION7` to `ENGINE_TO_MODEL_ACTION` as an opaque label (`"ACTION7": "ACTION7"`). The label is deliberately not "undo": that would be a semantic claim the world must earn.
   - **Test:** `to_engine_action("ACTION7") == "ACTION7"`, and `_normalize_actions` accepts it.
   - **Ownership:** this is a shared harness file, so the change is announced.
2. **D-2.** When the environment does not execute a controller action, the controller must not replay the bound probe.
   - The refusal is recorded against that step: the action is marked unexecutable here, and G1 coverage treats it as an observed refusal.
   - The next owned step is recomputed.
   - If the controller has no new step, the turn goes to Duck, or the level rests in `PLAY-NORMAL` under A2.
   - **A spin guard:** after K consecutive non-executed controller turns (K small, for example 3), the A2 rest fires.
   - **The solver loop** backs off briefly after a non-executed turn, so no thread busy-waits.
   - **Tests:** a fail-first replay of the observed sequence (8 G1 actions, then an environment refusal) must end in a legal disposition within K turns, not a spin.
3. **D-3, the Director's ruling.** In submission mode, should a controlled stop (from a loop guard or a bounded G3 checkpoint) end the game, or close the gate with its product and rest the level in `PLAY-NORMAL` for the rest of the slice?
   - **My recommendation is PLAY-NORMAL.** An ended game cannot score, while a resting one might.
   - **The cost** is Duck time under contention. The dry run's throughput margin covers it: 5,880 s used of 7,200 s with 600-s slices. Submission slices, though, are sized to fill the run, which needs checking once the fix lands.

**Then:**
- the Mac floor;
- a short dry-run re-check;
- `ring9-submission-v1`, built from `main` with SUB-2 and Sol's `4970953`. Its own Kaggle save run serves as the rehearsal.

The **G1 contract stop** (Duck's click-only explanation rejected twice before any action, as on sb26) is the next most costly row. Whether the click-only G1 explanation turn should come before the first action at all is an architecture question for the click line. Recorded, not proposed here.

## 5 · Throughput

| | Planned | Observed |
|---|---|---|
| 110 games at 10 a time with 600-s slices | 6,600 s of slot time; the window is 7,200 s | Finished in 5,880 s. 28 games ended early on controlled stops or at 0 actions, freeing slots. |
| GPU | about 2.3 GPU-hours | 1.83 GPU-hours |

**What this means for the submission settings** (2,700-s slices, 10 at a time, about 8 h 35 min of play): the plan of 110 × 2,700 s ÷ 10 = 8.25 h holds if every game uses its whole slice. D-2's spinning games used their whole slice doing nothing; fixing D-2 returns that time.

## 6 · Download not complete

`kaggle kernels output` (CLI 2.0.0) returned the first page: 499 files, 3.0 GB, artifacts through k055, plus the kernel log. It then printed a next-page token. CLI 2.0.0 has no flag to request the next page; CLI 2.2.2 adds `--page-token` and `--page-size` (checked against both versions' `kernels output -h`).

**Still to read:**
- the rest of the artifacts (k055 to k109);
- `execution_receipt.json`, for I2;
- the benchmark summary files.

This review will be amended in a later version once they are read.

## Download log (Director's terminal, 2026-10-07)

| Step | Result |
|---|---|
| `kaggle kernels output stephenkaskin/taaf-virelai-ring9-submission-dryrun-v1 -p runs/kaggle-ring9-submission-dryrun-v1/output` | First page: `.per_game_cards.pkl`, `artifacts/k000…k055` (499 files), the kernel log (468,559 bytes). 3.0 GB on disk. It printed `Next page token: eyJHY3NQYWdlVG9rZW4iOi…`. |

— Claude, Alpha build seat (click line), 2026-10-07
