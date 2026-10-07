# Learn to win: zoom-in, with a first offline lab result (v1, 2026-10-05)

**Author:** Claude (Alpha build seat), signed. Read-only. **No repo code was changed.** The probe ran on an exported copy of `ring9-unified` (`501a6e6`) in the build seat's scratch space.
**Asked by the Director (2026-10-05 16:39):** "we pour all of our focus into 'learn to win', let's zoom in there."
**Tags:** [OBS] = measured or read here; [HYP] = inference.

## 0 · What changed since the build plan [OBS]

- **The merge happened.** Branch `ring9-unified` (`501a6e6`, Sol, with audits from the Claude seats) holds CLICK and NAV in one tree. 605 tests passed and 1 was skipped.
- **R9-R24 landed** (`c9b246b`):
  - G4-B is certified by the controller from the record (`record_relations.py`);
  - lever states are named from the level's own boards (`level_record.py`);
  - Duck has a per-level G4 budget;
  - **normal play after the gates is receipted FREE_PLAY, with labelled harness refusals** (`play_gate.py`). That is S-5 and R-8, already built.
- **vc33 v8 is packaged** (`d807d88`). It has not run.
- The unification document lists **"G8 win explanation, win ledger, and `ACT_ON_GOAL`"** as deliberately deferred post-merge slices. This document is the zoom into the first two.

## 1 · The question

> Can Virelai explain an observed win only in its own certified vocabulary, so that the explanation (a) holds at every observed win, (b) fails at the recorded states that did not win, and (c) predicts the next level's win before it happens?

That is `PILLARS_PORT_AND_LEARN_TO_WIN_v1` §2, unchanged. Before building anything, the first useful question is empirical: **on the wins we already hold, does our vocabulary contain the difference between winning and not winning at all?**

## 2 · The lab: two recorded vc33 wins, probed offline [OBS]

**Method.**
- Drive the **v7 record** (`tests/fixtures/vc33_kaggle_carry_v7_record.json.gz`) through the unified gate machine as live, using the R9-R24 test driver's pattern: controller answers derived, Duck's recorded answers merged. Stop at the transition before each level win.
- At that point, take the certified lever regions (G4.1 anatomies, `lever_regions`) and every board the level has shown (`level_boards`). Then ask whether the board the winning action was taken from is told apart from the earlier boards by the certified lever-region contents. Use the same exact search the existing `_minimal_separator` uses, with at most 3 regions.

**Contrasts:**
- **strict:** earlier uses of the same action;
- **broad:** every earlier board on the level.

**Firewall.** Only counts and internal entity IDs were printed. No board contents and no colours. I did not look at the frames.

| | Level 1 win (t26) | Level 2 win (t69) |
|---|---|---|
| Gate at the moment of the win | G4.2 (lever orbits) | G4.2 (lever orbits) |
| Certified levers | 2 | 4 |
| Boards on the level before the win | 25 | 42 |
| Earlier uses of the winning action | 7 | 6 |
| Was the pre-win **lever-state** combination seen before on this level? | **No** | **Yes** (the boards before t67 and t68) |
| Separator over lever regions (LOCAL cells) | **1 region** (E0004), strict and broad | **None** within 3 regions, strict or broad |
| Separator over every anatomy channel (incl. REMOTE effects) | **1 channel** (E0004, REMOTE) | **None** within 3 |
| Was the **whole masked board** at the win seen before? | No | No |
| Where the level-2 pre-win board differs from the two earlier boards with identical lever states | — | 172 and 316 masked cells, **all on four G3-ledger entities that are not levers**: E0078, E0079 (newly numbered, so possibly objects born on level 2 [HYP]), E0002, E0003 |

## 3 · What the lab says

1. **Level 1's separator is weak evidence.** The winning board's lever-state combination had never occurred before, so *any* first-time configuration separates from the past. One win cannot tell "this condition" from "something new". This is the one-positive problem predicted in `REVIEW_LEARN_TO_WIN_v1`, now observed. A second win must generalise it.
2. **Level 2 cannot be explained in lever states at all.** The same lever configuration held on the two boards just before, without a win. The difference is in **objects that are not levers**. An explanation built from lever states would be refused by the referee, rightly. **The vocabulary must include every certified entity on the board, not only the levers.** Those are the G3 ledger's entities and their relations: position, shape, containment, alignment (W-1).
3. **Newborn objects matter.** Two of the four distinguishing entities have the highest IDs on the level [OBS]. Whether they were born during level 2 is unverified [HYP]. "Newborn objects (E0071)" is already an open item in the unification and R9-R24 records. Learn-to-win now has a direct stake in it.
4. **As far as this record shows, the win is a function of the board.** At both wins the full masked board was new, so no evidence yet calls for hidden state or history. That keeps the explanation a state condition, which is the simpler case.
5. **The winning render is not in the record format.** `virelai-recorded-world-v1` stores one `changed` list per step: the final layer, which at a level switch is the next level's spawn. The board *at* the win, which the goal-state predicate needs, lives only in the runtime's win capsule (`virelai_win_capsule.py:85-90`, frames in `runs/.../virelai/<game>/frames.bin`). **Either the record format gains the winning layer, or the explanation reads the capsule.** (The capsule is the observer's; phase sovereignty says the gate machine reads its own record, `level_model.py:8`. So the record format gaining the layer is the cleaner fix [HYP].)

## 4 · What this changes in the learn-to-win design

| Item | Before | Now |
|---|---|---|
| **Vocabulary for the explanation** | Lever states plus relations | **Every G3-ledger entity on the level, levers included,** with their relations (W-1). Lever states alone fail on level 2. |
| **The first win** | Explain it | Explain it, and **mark the explanation as "novelty-separated"** when the winning configuration had never occurred, so it is held as weak until a second win supports it |
| **Goal state (the board at the win)** | From the record | Needs the **winning layer in the record format** (or the capsule) |
| **Order** | R9-R24 first | Done. Next is the **record format and newborn-object coverage**, then W-1 and W-2 |

## 5 · The zoomed-in rung sequence (offline first; GPU last)

| Rung | What | GPU | Exit |
|---|---|---|---|
| **LW-A** | **The record keeps the board at the win.** Extend the record format so a level-ending step also stores the winning layer (`virelai-recorded-world-v2`). Regenerate the vc33 v6/v7 fixtures from their run artifacts, which hold every layer. | none | A replayed record yields the winning board, matching the capsule's SHA |
| **LW-B** | **Every entity in the description.** W-1 relations over all G3-ledger entities present on the level, keyed on entity type (never colour): position, extent, containment, adjacency, alignment, shape match. Newborn entities are included as soon as the ledger records them. | none | On the v7 level-2 win, a separator **exists** in the entity vocabulary, strict and broad. Otherwise the vocabulary gap is declared, not patched. |
| **LW-C** | **The referee** (W-2): the strict and broad contrasts with the action-gating guard; the novelty flag; refusal of vacuous candidates | none | Planted toy cases, plus the v7 level-1 and level-2 wins replayed |
| **LW-D** | **Two-win lab** (W-4, W-6): explain level 1; freeze its lifted survivors at level-2 entry; grade them against the recorded level-2 win (retrospective); update the ledger (generalise, specialise or kill) | none | A preregistered verdict per candidate; a two-win ledger |
| **LW-E** | **Live level-3 test** (W-7): the ledger's goal frozen at level-3 entry and graded live. The Director runs the canary. | one canary | A verdict before the level-3 win |

**Hooks into shared files** stay as in the build plan (H-8 for the G8 target, H-9 for its card slot), applied on `ring9-unified` once its owner opens the window.

## 6 · Rulings owed (Director)

1. **Go on LW-A and LW-B**, offline and on `ring9-unified`: the record format change and the entity vocabulary. LW-A touches `record_replay.py` and the fixture generator, which both lines share. LW-B is a new file.
2. **Where the winning board comes from:** the record format gains the winning layer (recommended; the gate machine reads its own record), or the explanation reads the observer's capsule.
3. **Newborn objects:** schedule the open item now, since learn-to-win depends on it, or let LW-B include whatever the ledger records today and declare the gap.

## 7 · Firewall and exposure

- vc33 is a dev world, and I have read a description of its win kind elsewhere (declared 2026-10-02).
- This probe printed only counts and entity IDs, never contents or colours. I did not view any frame.
- The relation set in LW-B is fixed from the certified vocabulary and generic geometry **before** it is run on any win record.
- vc33 results show the machinery works. Generalisation waits for the held-out worlds.

## Reproduction

The probe script is in the build seat's scratch space (`lw_probe2.py`). It drives the v7 fixture with the R9-R24 test-driver pattern and uses only `level_record`, `g4_relations` and the G3 entity ledger. If the Director wants it in the repo, it can be committed as `tools/probe_win_separability.py`, read-only and with no hooks.

— Claude
