# Review: ring9-carry-vc33-v2 (Kaggle, 2026-10-02)

**Author:** Claude (Alpha build seat), signed
**Run:** notebook `stephenkaskin/taaf-virelai-ring9-carry-vc33-v2` v1
**Package:** `065a4554…7e50`, source `fbbc7f4`
**Output:** `runs/kaggle-ring9-carry-vc33-v2/output/`
**Evidence basis:** artifact state (turn ledger, gate events, answers, annotations), the vLLM and notebook logs, and an offline reproduction at `fbbc7f4`.

## Verdict in one paragraph

Self-hosting works end to end, and level 1 replayed the exit run exactly: the gate events are byte-identical. The level freeze and the carry worked: level 1 froze with the expected model, the ladder restarted at G0 on level 2, and 4 carry candidates were frozen before any level-2 click.

Then the run **deadlocked at level 2's G1 for the whole remaining budget**: about 3 hours, 131 Duck turns, about 380 model requests, and zero actions. The cause is a code defect, reproduced offline:
- **D1:** the post-action metadata refresh flips a freshly built pointer ego from ANSWER_REQUIRED to UNRESOLVED.
- **D2:** the axiom-A2 watchdog does not treat that state as illegal.
- **D3:** offline replay does not apply the refresh, so the R9-R17 and R9-R18 tests could not see D1.

These are code-level faults, not plan-level ones. X-2's carry grades are ungraded, because no level-2 click happened.

## Grades

| Criterion | Result | Evidence |
|---|---|---|
| **I5** self-hosted setup | **PASS** | Wheelhouse path `/kaggle/input/datasets/stephenkaskin/virelai-vllm-wheelhouse-v3`, model path `…/stephenkaskin/virelai-qwen3-6-27b-fp8`, pip "Successfully installed …" (vllm 0.19.0, torch 2.10.0, flashinfer 0.6.6), smoke test "2 + 2 equals 4.", **model 33.66 GiB, KV cache 43.62 GiB**: identical to the exit run. Weight loading took 386.9 s, against 202.5 s in the exit run. That is mount read speed, not a fault, but it is about 3 more minutes of setup. |
| **I6** comparability | **PASS** | `vc33-5430563c_p0_gate_events.jsonl` is **byte-identical** to the exit run's: 26 controller transitions, the same actions, and level 1 won at t26 by the G4-A study of E0005. Duck's two level-1 turns (orientation and G4-A explanations) did not change the path. |
| I0, I1, I2, I3 | PASS | Source and receipt verified at start (217 files; receipt verified); controller executor on; artifacts written. |
| M5-1 card budget | PASS | Largest binding card 10,940 characters, under 16,200; the 24,000 guard never fired. |
| M5-2 (level 1) | PASS | G0 to G4.1 closed by the controller with zero model calls; orientation accepted at t15. |
| M5-2 (level 2) | **FAIL** | G0 closed by the controller. **G1 never closed** (D1). |
| A (G4-A) | As in the exit run | LeverOrbitSet CLOSED_BY_LEVEL_BOUNDARY at t26: E0004 ABSORBING, E0005 interrupted. |
| **X-1** level freeze | **PASS** | Card: `[prior] level 1 (frozen, unconfirmed here): E0004 ABSORBING, E0005 interrupted; G4 reached G4.2-LEVER-ORBITS; won at t26 by ACTION6(32,60) on E0005, same action failed 7x before (context mattered, UNTESTED)`. The ladder restarted at G0-ACTION-METADATA on level 2's board. The run did not stop. |
| **X-2** carry | **Frozen; ungraded** | Card: `[carry] level 1 levers E0004, E0005 -> 4 same-type objects here (4 UNCONFIRMED); not found: none`. Four candidates were frozen at level entry, before any level-2 click, the count the offline test predicted for the real level-2 spawn. None was graded: no level-2 click occurred, and G2's mask was never certified. |
| X-3 no verdict carried | PASS (trivially) | No level-2 product exists beyond G0. |
| L-1 lives | Vacuous | No death occurred. |
| **N-1** (axiom A2) | **FAIL** | G1 idled about 3 h in `UNRESOLVED / WAIT_FOR_REPRESENTATION_OR_NEW_ACTION` with no probe and no template. `legal_move_status` reported it legal (DECLARED_STATE), so the watchdog never fired (D2). |
| E ending | Time budget, no crash | `summary.txt`: 26 actions, 3h 0m 5s, level 1 of 7, score 0.26. |

## Root cause (reproduced offline at `fbbc7f4`)

**What happened.** The winning click at t26 is recorded through `record_outcome`. That calls `_advance_level`, which calls `_build_level`, which builds a **new** `EgoGateMachine` for level 2. For a CLICK_GOD_MODE world it starts with status **ANSWER_REQUIRED**, which is the state in which the controller answers G1 "pointer ego from metadata". Immediately afterwards, the same action's artifact path (`agent/gate_artifacts.py`) calls `gate_machine.update_action_metadata(valid_actions)`. That runs `EgoGateMachine._settle_coverage()`. A pointer ego has no coverage and no coverage effects, so `_settle_coverage` sets **UNRESOLVED, `REPRESENTATION_GAP_NO_VISIBLE_EFFECT`**.

From then on:
- The controller answered G0, then found G1 "offers no probe and no answer", and handed the turn to Duck.
- Duck's actions were refused: "G1 has no admissible probe while status is UNRESOLVED."
- Duck's answers had no template.

Duck tried for 131 turns, each ending at the turn time budget (about 75 s). The record shows it doing what it could and finding nothing legal: it was not the model's fault.

**Why level 1 never hit this.** Level 1's G0 and G1 are answered in the controller's first turn, before any action, so G1 is already CLOSED when the first metadata refresh runs. Level 2 is the first ego born **inside** an action's recording.

**Reproduction.** I replayed the live record (`tools/record_from_artifacts.py`, 26 transitions) and called `update_action_metadata(["ACTION6"])` once, exactly as `gate_artifacts` does:

```
G1 ego status UNRESOLVED REPRESENTATION_GAP_NO_VISIBLE_EFFECT
CONTROLLER ANSWER G0 metadata
DUCK G1-EGO offers no probe and no answer
G1-EGO UNRESOLVED WAIT_FOR_REPRESENTATION_OR_NEW_ACTION {... 'legal': True, 'move': 'DECLARED_STATE'}
```

Without that call, the same replay goes G0, then G1 (controller), then G2 (controller action). The test harness simply never makes that call.

## Defects, by altitude

All three are **code-level**.

**D1: the pointer ego is settled by coverage logic.** `EgoGateMachine.update_action_metadata` calls `_settle_coverage()` whenever the status is ACTIVE, ANSWER_REQUIRED, REOPENED or UNRESOLVED. For CLICK_GOD_MODE, G1's closure basis is the G0 interface axiom, not coverage. A refresh that adds no action must not touch a pointer ego's status. The fix belongs in `virelai_gates.py`, extracted rather than interleaved, under the ratchet.

**D2: axiom A2 has a hole.** `legal_move_status` counts any operation other than SUBMIT_GATE_ANSWER and QUERY_NEXT_* as a legal declared state. `WAIT_FOR_REPRESENTATION_OR_NEW_ACTION`, with no probe, no template and no event that could ever arrive, is exactly the deadlock A2 forbids. The fix:
- The state is illegal when nothing can change it without a move.
- The controller's own "offers no probe and no answer" handoff counts toward the watchdog.

Either change alone would have ended this run cleanly in minutes instead of spending 3 GPU-hours.

**D3: replay is not faithful to the live recording path (F-R4).** `record_replay.replay` does not apply the post-action `update_action_metadata` that `gate_artifacts` applies after every live action. That is why the R9-R17 and R9-R18 offline tests passed while the live run deadlocked.

The R9-R15 lesson recurs here: every live-path side effect the replay omits is a place where offline proof and live behaviour can diverge. The fix:
- Replay applies the same refresh.
- The v2 live record becomes a fixture that must reach G2 on level 2.

## What the run did establish

- **Self-hosted dependencies:** the setup is identical to the third-party one by every logged measure.
- **Determinism:** with the controller deterministic and Duck's two level-1 turns not altering the path, two runs a day apart produced byte-identical level-1 gate events.
- **R9-R16 and R9-R17 live:** a level change no longer ends the run, the frozen level-1 model is correct and displayed, and the ladder restarts on the next board.
- **R9-R18 live, up to freezing:** 4 type-matched candidates, frozen before any level-2 click. Grading them is what this run could not reach.

## Recommendation

1. **R9-R19 (a code slice, mine to build):**
   - D1, D2 and D3, test-first: every fix gets a regression test that fails before it.
   - The v2 live record becomes a fixture: with the live metadata refresh, level 2 must reach G2 under the controller.
   - Each defect gets its own fail-first test.
2. **Repackage as `ring9-carry-vc33-v3`:** same everything except the source commit. Re-verify, then run.
   - I6 should again reproduce level 1.
   - X-2 should finally be graded.
   - The 200-action budget is the next likely limit, as the v1 risks said.
3. **Not needed:** a model or plan change. The model never got a fair chance to act on level 2.

— Claude, Alpha build seat, 2026-10-02
