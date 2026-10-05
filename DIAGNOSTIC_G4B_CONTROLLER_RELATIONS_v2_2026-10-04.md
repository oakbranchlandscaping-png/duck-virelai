# Diagnostic: what the controller knew at G4-B, and what Duck's card showed (v7, level 3)

**Type:** `DIAGNOSTIC_G4B_CONTROLLER_RELATIONS` · **v2** · **2026-10-04** (supersedes v1)
**Author:** Claude (Alpha build seat), signed. The diagnostic itself was read-only.
**Ruling it serves:** `RULING_G4_CONTROLLER_FIRST_v2_2026-10-04.md` (Director-ruled).

**What changed from v1: a correction to D3.**
- v1 called E0010–E0011 and E0012–E0013 "coupled pairs". That was wrong. While building R9-R24 I found that the two levers in each pair have exactly the same region: all 35 cells for E0010 and E0011, and all 36 for E0012 and E0013. So a press that changes the region "changes" both levers by construction. Each pair is two controls of one shared region, not two regions that act on each other.
- The coupling claims are corrected in D3 below. The other findings are unchanged.
- §2 now points to what was built, `BUILD_SLICE_R9_R24_G4_CONTROLLER_FIRST_2026-10-04.md`.
**Input:** the v7 live record, built from the run's artifacts with `tools/record_from_artifacts.py`. That gives `v7_record.json.gz`: 165 transitions and 78 written answers, sha256 `5f276f4f…b76a3`.
**Source:** `ec8554d`, the v7 source.
**Tool:** `tools/diagnose_g4b_controller_relations_from_record.py RECORD 141 70`.

**How the tool works.**
- It drives the record as it ran live. The controller gives its own answers, Duck's recorded answers are used only where the gate asked Duck, and the harness RESET at t145 is delivered as it was live.
- The replay reaches G4-B at t140 and ends at t165 at G4-B, as the live run did.
- It labels every level-3 transition with G4-B's own region grading.
- It then scores simple record-lookup predictors online on the 23 graded G4-B and G4-C transitions. "Online" means each prediction uses only the transitions before it.

## 1 · Findings

**D1. Duck's card never showed a lever's state (code-level bug).**
- G4-B's rules promise Duck that "a lever's state (S0, S1, ...) names which of its recorded region contents it shows now". In v7, every one of the 1,947 `state_now` fields Duck saw read `UNRECORDED`. In the replay, all 665 labels across level 3 read `UNRECORDED` too.
- **The cause.** `LeverRegion._contents` only counts a recorded step as a state when the step rewrites *every* cell of the region. On this level a press moves part of a region, and part of its neighbour's. So no step ever qualifies, and no state is ever named.
- **The effect.** Duck was asked to predict a stateful mechanism while blind to its state. That is the root of review friction F4, and it feeds F1.

**D2. The record predicts the next press better than Duck did, at no model cost.** Scored on the 23 graded transitions, t141–t165, excluding the GAME_OVER at t144:

| Predictor (history = every earlier level-3 transition) | Made a prediction | Correct | Cost |
|---|---|---|---|
| Duck, live (G4-B P1–P13 and G4-C L1–L11) | 23 | **1** | 131 Duck turns, about 163 min |
| M1: same action from the same masked board | 3 | 3 | none |
| M3: same lever, same `state_now` (always UNRECORDED, so in effect "same lever") | 23 | 7 | none |
| **M5: same lever, same contents of its own region** | 18 | **10** | none |

A lookup on the region's own contents is right on 10 of the 18 transitions it covers, against Duck's 1 of 23. It is a lookup, not a law: it says nothing about board states never seen before. It shows that the controller held most of what Duck was being asked to work out.

**D3. The relations G4-B asked for were already in the record by t140.** Every effective press before G4-B opened, by the lever regions it changed (C = changed, + = something changed outside every lever region):

| Lever | Region sets its presses changed, t70–t140 |
|---|---|
| E0010 | {10, 11} t82; {10, 11}+ t111 |
| E0011 | {10, 11} t84; {10, 11}+ t85, t114, t115 |
| E0012 | {12, 13} t86; {12, 13}+ t118 |
| E0013 | {12, 13} t88; {15}+ t89; {12, 13}+ t121, t122; {10, 11, 15} t123 |
| E0015 | {15, 16} t91; {12, 13, 15, 16, 17}+ t92; {15, 16, 17} t126; {12, 13, 16, 17} t127; {16, 17}+ t128 |
| E0016 | {15, 16, 17} t93; {16, 17} t94; {16, 17}+ t131–t133 |
| E0017 | {16, 17} t95; {15, 16, 17} t96; {16, 17}+ t136–t138 |

Every other press of these levers in that window changed nothing outside the counter.

**What the table shows (corrected in v2).**
- **Shared regions.** E0010 and E0011 have exactly the same region (35 cells), and so do E0012 and E0013 (36 cells). Each pair is two controls of one region. Their columns above can't separate them, so v1's "pairs" were not couplings.
- **Regions that act on each other.** E0015, E0016 and E0017 each changed the others' regions. The region shared by E0012 and E0013 and E0015's region also change each other: E0013 changed E0015's region at t89, and E0015 changed the shared region at t92 and t127. E0016's and E0017's regions overlap by 14 cells, so part of the change between those two may also be shared cells.
- **One-way reach.** A press of E0013 changed the region shared by E0010 and E0011 (t123). Nothing recorded went the other way.
- **Presses run out.** Within one G4-A run, each lever stopped having any effect after one to three effective presses, until the board changed.

That is the content of a LEVER_RELATIONS description. Duck's one accepted relation found a single piece of it: the E0015–E0016–E0017 group (P13). The controller could have certified the whole map at t140 with zero Duck turns, each line citing its transitions. R9-R24 now does exactly that, reporting shared regions separately from relations between regions.

**D4. The level is not a set of independent switches (this bounds what any lookup can do).** Presses move contents across region boundaries. So the same lever, pressed with the same contents in its own region, can still do different things when its neighbours differ. That is why M5 is wrong on 8 of the 18 transitions it covers.
- A real law needs a model of what moves where. That is beyond G4-B as built, and beyond this ruling.
- The point for the time budget stands: whatever the law turns out to be, asking Duck to rediscover the coupling map press by press cost about 163 minutes and found one relation.

## 2 · What the ruling's build contains (R9-R24; see the build slice for what was built and tested)

| Item | Altitude | Change |
|---|---|---|
| D18 | code-level | Lever state labels come from the region's own content history on the level (every distinct content seen, in first-seen order), not only from whole-region steps. `state_now` then names a real state (D1). |
| D19 | ruled (G-1, G-2) | The controller certifies G4-B's relations from recorded transitions, as corrected in D3: shared regions first, then the relations between regions, each relation citing its evidence refs. The G4-B answer is written by the CONTROLLER as soon as every lever has at least one recorded press. |
| D20 | ruled (G-3) | A per-level Duck turn budget for G4-B and G4-C together, counted in Duck turns (rejected and cut-off turns included). Duck may confirm the relations, extend them (with recorded evidence), or freeze a test prediction. |
| D21 | ruled (G-4) | When the budget is spent, G4-B or G4-C closes UNRESOLVED as a declared end. A G4-C contradiction after that point does not reopen G4-B. |

**Expected effect on v7's level 3**, a hypothesis for the next run to test:
- G4-B and G4-C would cost at most the budget: about 3 turns, or roughly 3.5 minutes, instead of 131 turns and about 163 minutes.
- The run would not have hit the 3-hour clock.
- The score is not expected to change, because nothing here aims at the win (F3).

**Proposed tests:**
- a fail-first test that `state_now` names a state on the v7 record (D18);
- the controller's G4-B product at t140 matching D3 (D19);
- the budget, then UNRESOLVED, with no reopen loop (D20, D21), driven on the v7 record.

— Claude, Alpha build seat, 2026-10-04
