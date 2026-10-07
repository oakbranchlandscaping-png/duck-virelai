# Review: Sol's single-tree report and the unified ls20 canary review

**Date:** 2026-10-06
**Author:** Claude (Alpha build seat, click line), signed
**Reviewed:**
- `REPORT_SOL_SINGLE_TREE_NAV_AND_NEXT_WORK_v1_2026-10-06.md` (`85c9763`);
- `REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE_2026-10-06.md` (`a382f3a`);
- the Director's harmonization summary.

**Method:** I re-read every claim the submission and the next slice depend on, first-hand in the `d751a5b` export. Its solver source is identical to `b1a4d71` and `85c9763`, whose later commits are documents and tools only. I did not rerun the canary.

## 0 · Verdict

I accept the diagnosis. Every code claim I checked holds at the cited lines. Sol's next slice is the right priority for the NAV line: G1 must hand G3 a certified bearing map.

I add three things:
- **The bearing must come from recorded deltas, not from Duck's prose,** and must fail closed when ambiguous. Leaving G1 must require at least one certified bearing, not all of them, with a bounded exit.
- **A controlled stop ends the game.** For a competition game that is the wrong way to handle an exhausted checkpoint. It should go to `PLAY-NORMAL`.
- **The submission timetable does not wait on this fix.** The dry run stays as built and will measure how many games hit this defect.

I withdraw one claim of mine (§2).

## 1 · Verified first-hand

| Claim (Sol) | Source | Holds |
|---|---|---|
| Structured specs are built only from a *list* of objects. A mapping of prose yields `{}`. | `virelai_gates.py:7286-7300` (`_normalize_action_law_specs`: `if not isinstance(raw, (list, tuple)): return {}`) | Yes |
| The route checkpoint makes one required-tool request with no thinking, capped at 256 output tokens. The semantic checkpoint is the same. | `tool_agent.py:250-252`, `:3129-3135`, `:3158-3163`. Thinking reaches vLLM as `chat_template_kwargs.enable_thinking=False` (`utils/openai_compat.py:72`). | Yes |
| Exhaustion records `G3_ROUTE_RETRY_EXHAUSTED` and returns a controlled stop. | `tool_agent.py:3595-3621` | Yes |
| A controlled stop ends the game. | `solver.py:167-178` (`_turn_ends_game` returns True), `:513-514` (the session's loop breaks) | Yes. It ends **that session only** (see §4). |
| Repeating `observation_scope()` is harmless: `observe()` returns the stored transition for a transition id it has already seen. | `entity_observation.py:377-380` | Yes. I accept the answer to my question. A focused regression would pin it; it's small and low priority. |
| S-1 covers click records only. | `test_s1_concurrent_replay.py:25-31` | Yes |
| None of the learn-to-win modules (`win_relations`, `win_referee`, `win_ledger`, `g8_explain`) exists. | `inference/framework/` holds only `virelai_win_capsule.py` | Yes |

## 2 · Withdrawn

In my memo of 2026-10-06 I said `main` moved to `e8d1f92` before a floor ran. **That was wrong.** Sol fast-forwarded only after a full Mac suite at `e8d1f92`: 610 passed, 1 skipped. The counts agree: SUB-1 added 7 tests (2 + 5), and 610 + 7 = 617, the floor at `d751a5b`. No process slip occurred.

## 3 · Where I push

**P1 · Bearings come from recorded deltas, and fail closed.**
- *Where they come from.* "All mechanics are cell delta patterns." G1's eight controller actions recorded the ego's full before-and-after cells. A displacement should be compiled from those deltas: match the ego's whole component across the transition and take its translation. Duck's prose is the explanation; it is not the source of the bearing. The prospective prediction scoped only two cells, which is why recovery failed in a body of repeated colour. Matching the whole component removes that dependence.
- *The test.* The regression should prove the bearing compiles even when Duck's answer carries no structured specs at all, not only for the exact live prose.
- *Ambiguity.* A whole-component match can still be ambiguous: a body that is periodic along the move by exactly its period, or an action that moves nothing. Then the action gets no bearing, and the product says why (for example, an explicitly named "ambiguous" disposition). It is never guessed.

**P2 · Leave G1 with at least one bearing, and never get stuck there.** A rule requiring every action to have a bearing would hold G1 forever in a world where some action doesn't translate the ego. Two rules instead:
- G1 releases a NAV world to G3 when **at least one** action has a certified bearing.
- When none does, G1 has a bounded exit. Axiom I11: no gate idles without a legal move.

Sol's step 2 is right in intent; this states its edges.

**P3 · An exhausted checkpoint should lead to play, not to the end of the game.** For a canary, ending the game on `G3_ROUTE_RETRY_EXHAUSTED` gives a clean diagnosis. In a scored run it throws away the rest of that game's slice:
- An ended game can clear nothing more.
- `PLAY-NORMAL` might clear something.
- The ladder already has this path: a gate with no legal move goes to `PLAY-NORMAL` (`controller_turn.py:98-107`).

I propose that, in submission mode, a controlled stop from a bounded G3 checkpoint closes G3 with its product and hands the level to `PLAY-NORMAL`. That changes what a bounded guard does, so the Director rules on it. Sol's files would carry it; it's small.

**P4 · The 256-token truncation is not yet explained.** Thinking was disabled at the template, yet the model spent 256 tokens with no visible content and no tool call. There are two candidate causes, and each fix differs:
- **(a)** a forced Python action longer than 256 tokens, truncated, so the tool parser drops it;
- **(b)** the reasoning was not suppressed.

The response record's reasoning and content fields settle it. It matters beyond this route: the semantic checkpoint has the same cap.

**P5 · Order of my NAV work.** NAV-aware `level_record.presses()` (G4-B from the record) pays only once NAV reaches G4 live. No unified run has done that. I would build it after Sol's ls20 canary shows a real contact, and put submission and learn-to-win ahead of it.

The S-1 extension doesn't wait on Sol's amendment:
- It replays the existing N5.1 fixture, serially and concurrently, on the same code, so a change to G1 cannot make the two sides disagree.
- I'll add it now, with Sol's digest: the G3 adapter's snapshot, `lives.summary()` and `levels`.

## 4 · What this means for submission

- **Isolation holds.** A controlled stop breaks only its own session's loop (`solver.py:513-514`). The game is finished (`_finish_if_needed`), and its slot passes to the next game. It cannot end other games. The canary itself closed `COMPLETE` with a valid scorecard (score 0.00).
- **The dry run (`d751a5b`) proceeds as built.** It grades infrastructure (C-1 to C-6), which the G1 fix does not touch. It will also count how many clones end with `G3_ROUTE_RETRY_EXHAUSTED`, and at which gate every NAV and HYBRID clone rests. That tells us whether the bearing defect is general across NAV worlds or specific to ls20.
- **The scored package.** If Sol's fix and its short ls20 canary land before the submission date, `ring9-submission-v1` is built from that commit. Otherwise it is built from `d751a5b` and resubmitted after the fix, if the daily submission limit allows.
- **A second rehearsal comes free.** Kaggle runs a submitted notebook interactively first, to save the version. The submit package's interactive branch is the dry-run path (110 clones, 2-h window) with 2,700-s slices. That save run is a rehearsal on the final commit and costs about 2.3 GPU-hours, which the quota must cover.

## 5 · Ownership and order (proposed; the Director rules)

| # | Work | Owner | Altitude |
|---|---|---|---|
| 1 | Push and grade the 110-clone dry run (C-1 to C-7, plus the NAV/HYBRID rest table above) | Claude grades; Sol reads the NAV and HYBRID rows | code (grading) |
| 2 | G1 bearing repair (P1, P2), its regression, a controller-owned first G3 approach, and a short ls20 canary to one real contact | Sol | code |
| 3 | Disposition of an exhausted G3 checkpoint in submission mode (P3) | Director rules; Sol builds | architecture |
| 4 | Settle the 256-token truncation from the canary's response record (P4) | Sol | code (diagnostic) |
| 5 | S-1 extended with ls20 N5.1 and the NAV digest | Claude | code |
| 6 | `ring9-submission-v1` and the Kaggle facts (runtime limit, submissions per day, quota) | Claude builds; the Director confirms the facts and submits | code / Director |
| 7 | Learn-to-win W-1, W-2 (referee, R-6), W-4 in new modules; then W-3, W-5, W-6, W-7 | Claude: the referee and CLICK integration. Sol: NAV actuator contracts and hook review | code |
| 8 | NAV-aware `presses()` and record-derived G4-B for NAV, after #2 shows live contact | Claude | code |
| 9 | Open `ACT_ON_GOAL` after W-7 (R-7); its NAV slice runs on the existing procedure contracts, not a second navigator | Director | plan |

I agree with Sol's learn-to-win order (W-1, W-2, W-4, W-3, W-5, W-6, W-7) and with the NAV requirement for `ACT_ON_GOAL`: CLICK can act on a goal with one coordinate action, while NAV must compile it into a route and a target-bound contact. Sol's corrections to my documents (F3 superseded, v8's scope, S-1's incompleteness) are accepted.

— Claude, Alpha build seat (click line), 2026-10-06
