# Review: ring9-carry-vc33-v7 (R9-R23 mu bucket), Kaggle

**Date:** 2026-10-04
**Author:** Claude (Alpha build seat), signed
**Run:** `stephenkaskin/taaf-virelai-ring9-carry-vc33-v7`; output in `runs/kaggle-ring9-carry-vc33-v7/output`
**Source:** `ec8554d` (R9-R23). Package `03980ef7…`. Upload record: `UPLOAD_STATUS_RING9_CARRY_VC33_V7_2026-10-03.md`
**Method:** read first-hand from the run's artifacts. These include the benchmark history, gate events, gate answers, the turn ledger, the transcript and the kernel log. Every number below was computed from those files.

## 0 · The result in one paragraph

R9-R23 worked exactly as built. On level 3, G3 closed PARTIAL with 7 levers and set the one mystery object (E0028) aside in the mu bucket. The controller wrote that inventory, and the ladder went on through G4-A, G4-B and G4-C. That is the first time a vc33 run has reached G4-C.

The score did not move. It was 1.51, two of seven levels, the same as v6. The extra 2.9 hours bought understanding claims, not wins.

The run ended on the 3-hour clock, after 165 of its 200 actions. Most of that time went to Duck: the G4-B and G4-C turns took 24 actions and about 157 minutes, 91% of the behaviour time. All 11 of Duck's G4-C law predictions were contradicted by the frame, and every contradiction reopened G4-B.

Separately, level 3's move counter ran out at t144, during the study. That was a GAME_OVER, and the board reset.

## 1 · Grades

| Criterion | Grade | Evidence |
|---|---|---|
| I6 (comparability) | **PASS** | v7's first 110 actions are identical to v6's (0 differences). Levels 1 and 2 were won at the same transitions: level 1 in 26 actions, level 2 at t69. |
| I8 (pinned image) | **PASS** | Python 3.12 paths; the wheelhouse installed; `source manifest verified (221 files)` |
| I11 (A2 general rule, and the notebook ending with the run) | **PASS** | No gate state was left without a legal move. The run ended at its time budget (`state=cancelled`). The notebook ended 14 s after the run finished. |
| **I12 (G3 partial close)** | **PASS** | Gate answer 34, by the CONTROLLER: `LEVER_INVENTORY` with E0010–E0013 and E0015–E0017 as levers, 23 clean nulls, and `ambiguous_entities: ["E0028"]`. Its text reads "set aside in the mu bucket … (G3 closes PARTIAL)". No Duck turn was spent on it. At t110 the ladder entered G4.2-LEVER-ORBITS. G4-A queued and studied all 7 levers (t111–t140), with 7 accepted Duck explanations. |
| **I13 (mu return)** | **Ungraded (precondition)** | The ladder never got stuck. G4-C always had a move, so the run hit the clock first. E0028 stays OPEN in mu, and no MU_REVISIT click was made. |
| L-1 (life record) | **PASS** | The GAME_OVER at t144 took G4-B's P4. P4 has no grade: it is the only prediction of the 13 without one (P1–P3 and P5–P13 are all graded). The board reset at t145, and the study continued in the next life. |
| E (end) | **PASS**, by the time budget | The run never crashed. It was stopped mid-turn by the run deadline (t165, a `no_step` at the end). |
| A (G4-A, level 3) | **PASS** | The orbit set was complete for all 7 levers. Typing: all 7 UNIFORM, with no condition. Effective presses before holding: E0010 1, E0011 2, E0012 1, E0013 3, E0015 3, E0016 3, E0017 3. E0010 and E0012 had G3 repeats of NULL_AT_OBSERVED_STATE; the other five had NOVEL_STATE_REVEALED. |
| B/C (G4-B, G4-C) | **Reached; not satisfied** | G4-B: 1 of 12 graded predictions SUPPORTED (P13: pressing E0017 changes E0015, E0016 and E0017). G4-C: 0 of 11 SUPPORTED. Every G4-C prediction was contradicted, and each contradiction reopened G4-B, as specified (`g4c_gate.py`: "A contradiction reopens G4-B"). |

**The score: 1.51.** Levels 1 and 2 cost 26 and 43 actions, against human baselines of 7 and 18, as in v6. Level 3 cost 96 actions and was not won (human baseline 44).

## 2 · What happened, as gameplay

**Levels 1 and 2** repeated v6 move for move.

**Level 3, the sweep (t70–t110, 41 actions, zero Duck turns).**
- G3 clicked every object.
- Seven buttons along the bottom row (row 56, columns 12–50) moved large parts of the board: 28–51 cells per press.
- E0028 had already been pushed off the board by earlier presses, so G3 set it aside in mu rather than stopping.
- This is the v6 stall, removed.

**The study (t111–t140, 30 actions, 7 Duck turns).**
- The controller pressed each button until it stopped responding.
- Some buttons act once, then do nothing (E0010). Others act two or three times, then hold (E0013, E0017).
- Duck explained each orbit, and each explanation was accepted.
- No press in the study won the level. On levels 1 and 2, a study press happened to be the winning move.

**The relations and the law (t141–t165, 24 actions, about 157 minutes).**
- Duck predicted what each button would do.
- Almost every prediction was wrong. Most said a button changes only its own region; in fact a press often changed several regions, or nothing at all once the button was spent.
- Duck's law predictions repeated the same claim against the frame: "pressing E0010 steps only E0010", made at L1, L3, L7 and L9, and contradicted each time.
- The board state matters. A spent button does nothing, and the reset at t145 un-spent all of them. Duck's predictions did not carry that state.

**The clock that ended the level.**
- The counter is a bar on the top row that loses one cell per counted move. It ran from column 63 at t70 down to column 0 at t144, and the level ended in GAME_OVER.
- So level 3 allows about 64 counted moves. The study spent them: 41 on the sweep, 30 on G4-A, and 4 on G4-B.
- G2 had certified this counter on level 3 as bookkeeping, and masked it. Nothing in the ladder reads it as a move budget.

## 3 · Where the time and GPU went

| Phase | Actions | Behaviour time | Generated tokens |
|---|---|---|---|
| G0–G3 (all levels) | 77 | about 0.5 min | 249 |
| G4-A (all levels) | 63 | 15.1 min | 32,674 |
| G4-B (level 3) | 13 | 41.9 min | 90,429 |
| G4-C (level 3) | 11 | 115.6 min | 237,566 |

- **Notebook wall time:** 11,694 s, about **3.25 GPU-hours**. That is within the upload record's ceiling of 3.3. Setup and model load took about 14 minutes. Weekly share: about 3.25 of roughly 30 GPU-hours.
- **The cost driver.** On each G4-B re-answer and each G4-C prediction, Duck ran turn after turn into its per-turn time budget. The ledger has 98 such turns. Its prompt grew within one decision to about 51,000 tokens, against a 65,536-token window.
- **The loop has no cost bound.** Each contradicted G4-C prediction reopens G4-B, and G4-B needs a new accepted description before G4-C can predict again: about 10 minutes per round. A2 cannot see this loop, because a legal move always exists.

## 4 · Frictions, ranked, with altitude

**F1. The G4-B/G4-C contradiction loop has no stop (architectural, for CE or the Director).**
- **What happened.** The loop worked as specified, and never converged: 11 rounds, 0 laws supported, 115 minutes. The frame was doing its job (falsification is law), and the machine kept paying Duck to re-describe.
- **What's missing:** a ruled bound on reopenings, or a rule for when a law gate closes UNRESOLVED. That is a ruling about the ladder, not a code fix. It is not mine to invent.

**F2. The study spends the level's lives (architectural).**
- **What happened.** Level 3's move counter, about 64 moves, is a life clock, and the sweep plus the orbit study consumed it.
- **The open question:** the machine already certifies the counter in G2. Whether that certified counter should become a budget that the study plans against is a question about what G2's product means. It needs a ruling.

**F3. Nothing in the built ladder aims at the win (plan-level, for the Director and Apex).**
- **What happened.** Both wins in v6 and v7 were side effects of G4-A presses. Level 3 needed a combination or an order of presses, the kind of thing a 44-action human solution implies, and the ladder's gates ask "what does each lever do?", not "what wins?"
- **What it means.** The score is therefore capped by accidental wins. This is the honest reading of 1.51 → 1.51.
- **Why it is not mine to rule.** The ladder's goal rung, whether a G4-C law feeds a planner and when, is the plan's to rule.

**F4. Duck's law predictions ignore lever state (code-level candidate, not yet diagnosed).**
- **What happened.** G4-A's typing carries `effective_presses` (how many presses a lever takes before it holds). Yet Duck's laws predicted STEPS for spent levers.
- **What isn't known yet:** whether the G4-C card shows Duck each lever's press history on the current board. A read-only diagnostic should precede any fix.
- **How it relates to F1.** If the card omits press history, F4 is a cause of F1, not a separate friction.

**F5. The submission budget (plan-level; directive D-2).**
- **The submission budget.** A submission plays 110 games in 9 hours: about 4.9 minutes per game, model load included.
- **What this run used.** v7 spent 8.6 minutes of behaviour time to win levels 1 and 2 of one game, and 3 hours on that game in all.
- **The implication.** The current per-game cost does not fit the submission, whatever the study finds. The first scored submission, due by about 12 October, needs a per-game time policy that the vc33 diagnostic runs do not have. This is in addition to the Ring 9 merge in `RECORD_R9_R23_LANDING_v1`.

## 5 · The Honest Ledger, after v7

**Built and live-confirmed:**
- R9-R22 typing;
- the A2 general rule;
- the R9-R23 partial close (I12);
- the life record across a GAME_OVER (L-1).

**Still open:**
- **Built, not yet exercised live:** the R9-R23 mu return (I13). A changed-board retry and an ABSENT settlement have only been seen in tests.
- **Open questions for the Director:**
  - newborn objects (E0071);
  - the Ring 9 merge;
  - F1–F3 above.
- **Kaggle facts to verify** (still open from the directive):
  - the deadline time;
  - submissions per day;
  - the RTX PRO 6000 quota;
  - whether reruns count.

## 6 · What I recommend next

These are recommendations, not rulings.

1. **Do not rerun vc33 as it is.** A v8 with the same ladder would spend another 3 GPU-hours on the same loop.
2. **Rule F1 first.** It is the cheapest lever on cost. A bound such as "G4-C closes UNRESOLVED after k contradictions on a level" would have saved about 100 minutes here.
3. **Run the F4 diagnostic (read-only)** in parallel: what does the G4-C card show Duck about each lever's presses on the current board?
4. **Escalate F3 and F5 to Apex, through the Director.** These are the plan questions that decide whether the next two weeks go to the ladder or to the submission. With the first scored submission due by about 12 October, F5 is the more urgent of the two.

— Claude, Alpha build seat, 2026-10-04
