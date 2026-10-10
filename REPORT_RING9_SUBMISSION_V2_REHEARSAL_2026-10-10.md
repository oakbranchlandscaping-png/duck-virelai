# Alpha build report: Ring 9 submission v2 rehearsal

**Date:** 2026-10-10  
**Audience:** Alpha build team, NAV line, learn-to-win chamber, Apex  
**Run:** `ring9-submission-v2`, Kaggle notebook save run, version 1, 2026-10-09  
**Status:** rehearsal evidence; this was not a scored submission

## Executive assessment

The submission package launched, executed a two-hour rehearsal, and preserved a complete downloadable output set. The SUB-3 repair to free play worked: Duck's 168 free-play actions were executed and reported consistently. Four games cleared a combined five levels. The largest observed prompt fit the model context window.

The learning path is still fragile. One game crashed when G3 tried to move a closed entity to an incompatible lifecycle state, and the log shows the same class of failure on a second G3 path. Nineteen gate stops sent play away from the active learning gate; twelve were at G1. Two games hit a G1 contract loop before making an action. The run also exposed substantial analyzer latency. No game completed a full win, and every final score was 0.00.

This run supports continued work on the semantic-library plan. It does **not** establish that the library is complete or that the Push is ready to take over. The first priority is to make the learning path safe and able to progress, then to measure the library's coverage rather than infer it from level clears.

## What ran and what the numbers mean

| Measure | Result |
|---|---:|
| Benchmark window | 2026-10-09 09:21:56–11:23:19; 2 h 1 m 23 s |
| Games in benchmark | 110 |
| Games with at least one action | 33 |
| Games cancelled before any action | 77 |
| Final states | 22 gave up; 1 crashed; 87 cancelled |
| Total environment actions | 2,966 |
| Levels cleared | 5, in `k005` (1), `k010` (2), `k022` (1), `k030` (1) |
| Complete wins / final score | 0 / 0.00 in all 110 records |
| Most actions in one game | 403, below the configured 1,000-action cap |

The 77 zero-action cancellations are a coverage limit of the fixed rehearsal window. They should not be reported as 77 gameplay failures. Ten of the cancelled games had already acted and retained events, gate events and turn ledgers. The run used 10 concurrent games with a 2,550-second per-world limit; it could not provide a complete playthrough of all 110 games inside roughly two hours. Comparisons with v1 are directional only because its settings and code differed: v1 had 36 active games, six level clears, 3,298 actions and no crashes; v2 had 33 active games, five clears, 2,966 actions and one crash.

## What worked

1. **Package and evidence integrity.** The saved run finished and produced `benchmark.json`, a kernel log, an execution receipt, per-game records and a submission artifact. All 2,506 listed Kaggle output files were downloaded, plus the kernel log. The downloaded receipt's SHA-256 matched the expected receipt. The full local output is about 2.3 GB.
2. **SUB-3 free-play feedback.** Across 26 worlds, 168 `FREE_PLAY` gate-event receipts corresponded to 168 Duck `step_executed` turns in `PLAY-NORMAL`, with no per-world mismatch. No transcript reported `action failed in sandbox host` or `Unknown action`. The v1 failure, where executed free-play actions were described to Duck as failed, was not reproduced.
3. **Some levels were cleared.** Four games cleared five levels in total. This shows the controller and Duck can still make progress through the gate/free-play machinery. It is not evidence of a complete win or a complete semantic library.
4. **Prompt headroom.** The largest observed prompt was 42,939 tokens against a 65,536-token context window. This rehearsal did not hit the context ceiling.
5. **Cancellation retained records for games already in play.** All 33 active games had gate events, gate answers, probe envelopes, turn ledgers, events and viewer data. All ten active games cancelled at the window boundary kept events, gate events and turn ledgers. Every one of the 110 records had events and viewer data; the 77 games never started had no gate turns to record.

## Frictions requiring resolution

### 1. G3 lifecycle contradiction — release blocker

`k008` crashed after 61 actions with `LifecycleError: illegal transition G3-CLOSED -> AMBIGUOUS for E0001`. The entity had already been marked `G3-CLOSED` as a scoped null while reachability was not yet settled. The lifecycle's allowed successors for `G3-CLOSED` are `G4-READY` and `REOPENED`; `AMBIGUOUS` is not one of them. The kernel log also records four sandbox-host lines for `gate_answer` attempting `G3-CLOSED -> PRESUMED_UNREACHABLE` for `E0001` (the lines may include duplicate logging). These are related contradictions in the G3 close/reassessment path. They are not failures of the SUB-3 free-play receipt.

**Required fix:** reproduce both sequences from the saved records, decide whether G3 closed too early or whether it must reopen before reassessment, and make the state change and its evidence atomic. Do not simply add broad successor edges to make the exception disappear. A regression replay must show both ambiguous and presumed-unreachable reassessments complete without a crash or a false certified lever law.

### 2. G1 stops — learning blocked at the foundation

There were 19 controlled gate stops in 18 games: G1 12, G2 2, G3 2, G4-C 2, and G4.2 1. By outcome, eight were no-progress tool loops, nine were contract-repair loops, one exhausted G3 semantic retries, and one exhausted G3 route retries. These are **gate** stops; later no-progress in normal free play is a separate observation.

The G1 set has two causes, so it needs two work orders:

- **Click-only G1 contract, three rests:** `k022` twice (on successive levels) and `k023` once. The G1 answer template describes every available action as selecting a grid coordinate, while the validator accepts only an `ACTION6` action law. In worlds offering `ACTION5` or `ACTION7`, the controller submits its own template, G1 rejects it, and Duck repeats the same answer. The first `k022` and `k023` rests occur before any action. Fix the template to state the `ACTION6` law alone and retain the other actions as explicit open questions. Then verify the controller can close G1 before any Duck explanation, as ruling 6 requires. This is WO-L1a.
- **Movement/NAV-path G1 loops, nine rests:** `k001`, `k002`, `k007`, `k014`, `k016`, `k026`, `k027`, `k028` and `k029`. These occurred after controller probes, 8–51 actions into the level. Seven ended in a no-progress tool loop and two in a contract-repair loop. This set includes movement-only as well as mixed-action games. Diagnose it on the NAV path with its own replay and fix; the click-only template repair does not cover it. This is WO-L1a-NAV.

The wider D-3 behavior remains a product issue: a controlled stop sends the level into free play while later library questions remain open. WO-L1b should measure the post-fix stop distribution, and the subsequent gate-ladder work should make a stuck gate close with an explicit unresolved disposition so the library can keep accounting for the level. Later gates must respect prerequisite rulings; diagnostic observation after an unresolved foundation must not certify laws.

### 3. Analyzer latency and turn budgets — throughput risk

The kernel log contains 38 `analyzer request failed` / read-timeout occurrences. Of 873 Duck turns, 499 ended with a `turn_time_budget` outcome (about 57%). Some timeouts were set from remaining wall time, but this report does not assign every timeout to a single root cause. The model was running ten games concurrently, and latency consumed a large portion of playable time.

**Required work:** report latency by game, turn type, concurrency and remaining budget; distinguish service stalls from deadline-driven cancellation; make the controller's useful work and short fallback behavior measurable. Rehearse with the intended submission concurrency and compare active games, actions, gate closure and time-budget cuts. Avoid treating extra wall time as proof that a gate became more reliable.

### 4. Evidence coverage and storage — reporting risk

The run wrote enough evidence to investigate the failures, but a literal claim that every game has a gate record would be false: 77 games never acted and had no gate events or turn ledgers. Acceptance checks should say **every game that enters a gate** has its gate record, while all benchmark entries retain a cancellation/never-started status. The output download was also large: about 2.3 GB for this shortened rehearsal. The size of a full-length output under Kaggle's working-disk limit has not been established.

**Required work:** retain a per-game manifest that distinguishes `never_started`, `active_cancelled`, `gave_up` and `crashed`; verify all active-game evidence is internally consistent; measure per-game output growth and project it against the actual Kaggle disk allowance before the longer run. Keep the receipt and raw source of counts. The 168 free-play receipt match is a strong model for such checks.

### 5. Semantic-library coverage remains unmeasured — strategic gap

Level clears and a working free-play fallback do not tell us how much physics the system learned. This v2 runtime does not yet produce the planned per-level census of every observed worldline, its role evidence and its unresolved questions. It also lacks the planned G5 environmental-force and G6 scoped-negative chapters as certified library products, and it does not express every certified product as a grounded grammar sentence. Consequently, this rehearsal cannot grade M1 inventory coverage, M2 Push readiness, or M3 full-library completion.

**Required work:** implement the semantic-library plan in order: close and report stuck gates; build the census from one read-only entity ledger with explicit gaps; add grounded force and scoped-negative evidence; compile certified findings into typed grammar sentences. Keep the plan's distinction: M1 is an accounted inventory, M2 is a library ready to constrain the Push, and M3 is the full semantic library. A census with gaps is M1 evidence, not permission to hand control to Push. Free play remains the fallback when no gate can act.

## Proposed fix and verification order

| Priority | Work | Evidence that closes it |
|---|---|---|
| P0 | Repair G3 close/reassessment lifecycle | Replays of `k008` and the `gate_answer` error path complete without hidden exception or false certification; no game crash in the next rehearsal. |
| P0 | Fix click-only G1 contract (WO-L1a) | Fail-first tests for `ACTION6` plus other actions; `k022`/`k023` pattern closes G1 at zero actions without an explanation loop. |
| P1 | Diagnose and fix movement/NAV G1 loops (WO-L1a-NAV) | Replays of the nine affected cases show bounded explanation and an explicit gate disposition. |
| P1 | Rehearse v3 and grade gate stops (WO-L1b) | Report G1/G2/G3/G4 stops by cause and actions before rest, along with active-game coverage and cancellation status. |
| P1 | Build the per-level census (WO-L2) | Every observed worldline appears once with evidence-backed roles or a typed gap; report M1 by level, including early stops. |
| P2 | Trace analyzer latency and output growth | A measured latency breakdown and disk projection support the submission settings. |
| P2 | Add G5, G6 and typed grounding work | Force/negative laws meet their proof requirements, and every certified sentence cites valid transitions. |

The plan assigns click-only G1 and census work to Alpha, the movement/NAV G1 diagnosis to Sol, and shared grammar work to the learn-to-win chamber. The G3 lifecycle repair needs an explicit owner because it is now a release blocker. Apex's architecture and ownership rulings still matter for downstream observation, G5/G6 and the Push handoff; they do not need to hold up the P0 repairs.

## Grading notes and limits

- **SUB-3 free-play feedback:** passes on the 168 observed Duck free-play actions.
- **No crash:** fails on `k008`; the related `gate_answer` lifecycle errors also require investigation.
- **Gate evidence:** passes for all 33 active games; not applicable to the 77 that never entered a gate. The check must state that scope.
- **Cancellation:** the ten active cancellations retained key artifacts. The original “nothing in flight before soft end” expectation remains incompatible with a two-hour, 110-game rehearsal using long per-world slices.
- **Prompt window:** passes at 42,939 / 65,536 tokens.
- **Specific world identity / vc33 check:** not graded here because a trusted `kNNN`-to-world mapping was not established from this output.
- **Scored performance:** unknown. This was a saved rehearsal, not a scored submission; zero final score here does not replace an official submission result.

## Evidence reviewed

- `runs/kaggle-ring9-submission-v2/output/benchmark.json` and `summary.txt`: benchmark window, states, actions, levels and scores.
- `runs/kaggle-ring9-submission-v2/output/execution_receipt.json`: package, model, concurrency and budgets.
- `runs/kaggle-ring9-submission-v2/output/taaf-virelai-ring9-submission-v2.log`: crash, analyzer timeouts and sandbox-host lifecycle errors.
- Per-game `virelai/kNNN_p0` records and transcripts: gate outcomes, Duck turns, free-play receipts, prompt size and cancellation evidence.
- `EXECUTION_PLAN_SEMANTIC_LIBRARY_v1_2026-10-09.md` and `BUILD_PLAN_SEMANTIC_LIBRARY_PUSH_FALLBACK_v3_2026-10-09.md`: existing work orders and M1/M2/M3 criteria. These plans inform priorities; the observed run is the evidence for the findings above.
