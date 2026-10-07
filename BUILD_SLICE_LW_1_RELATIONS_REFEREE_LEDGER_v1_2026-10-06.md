# Build slice LW-1: win relations, the win referee and the win ledger (W-1, W-2, W-4)

**Date:** 2026-10-06
**Author:** Claude (Alpha build seat, click line), signed
**Status:** proposal; nothing built. It needs the Director's rulings in §6 before code.
**Governs:**
- `BUILD_PLAN_PORTS_AND_PILLARS_v1_2026-10-04` §2 (W-1, W-2, W-4);
- `PILLARS_PORT_AND_LEARN_TO_WIN_v1_2026-10-04` (LW-1);
- `RULINGS_PORT_AND_PILLARS_v1_2026-10-04` R-6 (the referee is built from Tycho and JustAdev742, in code, with zero model calls);
- the order Sol and I agreed: W-1, W-2, W-4, then W-3, W-5, W-6, W-7 (`REPORT_SOL_SINGLE_TREE…` §5, `REVIEW_SOL_SINGLE_TREE_REPORT_v1` §5).

**Read at:** `ring9-unified` `7ea851e`; its solver source is identical to the `d751a5b` export.

**Prior art, at the pinned revisions:**

| Source | Revision | Licence | Lines |
|---|---|---|---|
| JustAdev742 `Arc-Agi-3-Kaggle-comp` `arc3/dsl.py` | `8b8a728f7a5e` | Apache-2.0 (`LICENSE` read) | 2,037 |
| NIMI-research `Tycho` `tycho/workspace/wmlib_template.py` | `f68912a76437` | Apache-2.0 (`LICENSE` read) | 1,773 |

Both repositories were cloned in the cloud and read at the pinned commits with `git show`. Nothing in them was executed.

**Tags:** [OBS] read at the cited file:line; [HYP] inference.

## 0 · In one paragraph

These three work orders are new files with toy-world tests, and they touch no shared file. They build:
- the vocabulary a win can be stated in (W-1);
- the code that admits or kills a stated win condition against the record (W-2);
- the cumulative ledger of surviving conditions (W-4).

The WO-00 read found four things:
1. **The referee should port less of Tycho than the plan assumed.** Its outcome check is the right core; its transition check grades laws, not wins, and can wait (F-B).
2. **JustAdev742's goal relations are generic geometry chosen with game knowledge.** The relation set must be derived on our own terms (F-A).
3. **I read game-specific remarks in that code and declare them** (§5).
4. **The live records do not hold the board on which a win condition becomes true.** W-1, W-2 and W-4 are not blocked by this; W-3 and W-6 are (F-C).

## 1 · WO-00 findings

**F-A · JustAdev742's relations are generic in form, game-informed in selection** [OBS, `dsl.py:1597-1688`].

- *What is there.* `goal_predicates` enumerates:
  - `none_left`, `count == n`, `aligned`, `all_same_colour_as`;
  - `overlap`, `touch`, `same_box`, `same_columns`, `same_rows`, `inside`, `shape_matches`;
  - a shape-class vanish;
  - avatar-relative `inside` and `touch`.

  It keeps a candidate only if it is true at the last frame of every won level and false at every earlier frame of those levels. That is the strict separator, and it is the mechanism to port.
- *What makes it game-informed.* Its comments justify several kinds by named public games. Its constants are tuned:
  - `count` uses n from 1 to 4;
  - shape classes are limited to size ≤ 400 and at most 4 per class;
  - every relation is keyed on colour.
- *Ruling proposed (Q-1).* W-1's relation set is a closed enumeration over our own certified vocabulary:
  - **Which entities:** ego, counter (masked out), levers, and other persistent entities with their D18 region states.
  - **Which relations:** a fixed set of pairwise geometric relations, each defined from cells: equal cells, equal shape up to translation, containment, overlap, 4-adjacency, equal row span, equal column span. To these add unary presence and count over the entities of one certified class.
  - **What is not ported:** no colour constants and no size or count thresholds from the source. Where a relation coincides with one of JustAdev742's, the provenance header says so.

  The firewall then holds by construction: nothing in W-1 is selected by a game.

**F-B · Port Tycho's outcome check now; its transition check later** [OBS, `wmlib_template.py:1071-1375`, `:434-500`].

- *What `verify_outcome` grades.* A full world model (init state, transition, outcome, render):
  - at each solved level, the model's terminal after the winning action must say "level complete", and every observed decision state must say "ongoing";
  - the same holds for deaths;
  - misfires are typed (missed or false level-complete, missed or false game-over, terminal render) and kept per level.
- *What our referee grades instead.* A win **condition**: a predicate over recorded states, with no simulation. We port:
  - the grading shape: true at every win, false at every observed non-terminal state, typed misfires, per-level buckets;
  - the anti-vacuity rule, `_coverage_status`: a candidate that abstains everywhere is "vacuous" and refused (`:467-480`).
- *What waits.* The transition check (`verify`, `:567`; `_cell_stats`, `:434-465`) grades a law's predicted cells against observed cells, under an UNKNOWN mask. The note on prior art (`NOTE_G4_CONTROLLER_FIRST_PRIOR_ART_v1` §3.2) said to build it once for both jobs, with our G2 mask as UNKNOWN. That is right, but no work order in LW-1 needs it; G4-C's law referee does. **Proposed (Q-2):** W-2 ports the outcome check now. The transition check becomes its own work order when G4-C laws are refereed.
- *Zero tolerance.* From JustAdev742 `Claim.contradicts` and `score_rule` (`dsl.py:246-289`, `:905-918`): one recorded counterexample kills; support counts only events the claim asserts. A "nothing happens" claim earns no support, so vacuous agreement cannot carry a rule.

**F-C · The record does not hold the winning board** [OBS].
- *What the record shows.* In the vc33 v6 fixture (`tests/fixtures/vc33_kaggle_carry_v6_record.json.gz`), the level-1 win is transition 26. Its row carries `boundary.level_completed = true` and changes **2,772 cells**: its after-board is level 2's spawn.
- *Where the winning board lives.* It is an intermediate frame layer. The observer's win capsule refers to it only by hash (`virelai_win_capsule.py`, `winning_render_ref`), and the live `capsule` takes layer `len-2` (pillars P5).
- *What is blocked.* W-3 and W-6 need that board, or must state the condition on the pre-win board together with the winning action. Which of the two is a ruling for W-3, not for LW-1.
- *Proposed (Q-3).* Before W-3, a read-only check of whether the live artifacts (probe envelopes) keep the frame layers of a winning transition. If they do, the record keeps the winning layer as a new optional field. W-1, W-2 and W-4 take states as input and are tested on toy boards, so they are not blocked.

**F-D · The action-gating guard needs an action class** [HYP]. The broad contrast counts a state as a counterexample only if a "winning-class" action was taken from it. W-2 takes that class as a parameter: a predicate over the recorded action. What the class is for CLICK and for NAV is decided at W-3, from G4's vocabulary:
- CLICK: the same lever.
- NAV: contact with the same target.

## 2 · W-1 · `inference/framework/win_relations.py`

- **Input:** a board (a grid of integers), the certified counter mask (cells to ignore), and an entity binding: an id and a certified class for each cell set, such as `ego`, `lever:E0016`, or `persistent`. The binding comes from the G3 entity ledger and the D18 region states. W-1 receives it and never derives it.
- **Output:** the set of true atoms. An atom is a relation over entity ids. Each atom also has a class-level lift, which replaces ids with classes, so that a condition can be carried to a new level (P2's colour-free lift, re-keyed on class).
- **Contract:**
  - pure functions;
  - no constant beyond the grid it is given;
  - deterministic output order;
  - no model call.
- **Fail-first tests,** `tests/test_w1_relations.py`, on toy boards:
  - each relation true and false on a minimal pair;
  - counter-masked cells never produce an atom;
  - two boards that differ only in colour give equal class-level lifts;
  - the module holds no integer literal other than 0 and 1, checked by an AST scan.

## 3 · W-2 · `inference/framework/win_referee.py`

- **Input:**
  - a candidate (a conjunction of atoms, possibly ordered "A then B");
  - the level records: for each level, its states in order, the action taken from each state, and whether that level was won (with its winning state);
  - the action-class predicate (F-D).
- **Verdict:**
  - **ADMITTED:** true at every winning state and false at every contrast state.
  - **KILLED:** with typed misfires, each citing its level and transition:
    - `missed-win`: false at a winning state;
    - `false-win`: true at a non-winning state from which a winning-class action was taken, with no win.
  - **VACUOUS:** the candidate is never evaluable or never true, per Tycho's coverage status.
- **Contrast sets:** strict (earlier uses of the winning action) and broad (every earlier state, under the guard), reported separately.
- **Contract:** pure code, zero model calls, deterministic, and every misfire carries its transition id.
- **Fail-first tests,** `tests/test_w2_referee.py`; these are the plan's four:
  1. a planted correct condition is admitted;
  2. a planted wrong one is killed, with the right misfire type;
  3. a condition that abstains everywhere is refused as vacuous;
  4. under the guard, a state satisfying the condition with no winning-class action taken is not a counterexample.

## 4 · W-4 · `inference/framework/win_ledger.py`

- **Purpose:** the cumulative ledger of surviving win conditions. Its operations follow the Director's statement of 2026-10-02:
  - **generalise:** after a second win, keep the class-level atoms both wins share;
  - **specialise:** the condition held and a winning-class action was taken, but no win came. Open the candidate conjunctions that add one atom, or an ordered stage, with the order taken from when each atom first became true in the record;
  - **kill:** a win arrived while the condition was false.
- Every operation cites the transitions that caused it.
- The ledger renders one sentence per surviving condition, with each clause's entity class and source.
- **Fail-first tests,** `tests/test_w4_ledger.py`, on toy two-level worlds: generalise, specialise (including an ordered "then"), and kill, each with citations.

## 5 · Exposure declaration (the honesty rule, as for `su15` under R-4)

While reading `dsl.py:1597-1688` on 2026-10-06, I read the author's comments. They state, for three public games (ls20, vc33, ar25), which relation holds at a recorded win: a human recording for ls20, and a one-line remark each for vc33 and ar25.
- **vc33:** already declared, in `PILLARS_PORT_AND_LEARN_TO_WIN_v1`, "Honesty declarations".
- **ls20 and ar25:** declared here.

**Consequences:**
- W-6 and W-7 on vc33 show the machinery works, never that it generalises (unchanged).
- Any learn-to-win result on ls20 or ar25 must cite this exposure.
- If either game is in the prereg's held-out set, the next prereg version declares it, as for `su15`.

F-A's derivation rule keeps the exposure out of the code. I did not read `dsl.py:1700-1793` (the universal kinds and the lift), which the plan already marks as derived from game source. P2's lift will be written from our own class binding.

## 6 · Rulings owed (Director)

| # | Question | Recommendation |
|---|---|---|
| Q-1 | W-1's relation set: a closed enumeration over our certified vocabulary (F-A), with no third-party thresholds or colour keys | Yes |
| Q-2 | W-2 ports Tycho's outcome check and JustAdev742's zero-tolerance claims now; the transition check waits for the G4-C law referee (F-B) | Yes |
| Q-3 | Before W-3: a read-only check of whether live artifacts keep the winning frame layer; if so, an optional record field (F-C) | Yes; Claude, read-only |
| Q-4 | Ownership: W-1, W-2, W-4 by Claude, in new files only. Sol reviews the ego and NAV atoms in W-1 and the NAV action class (F-D). | Yes |
| Q-5 | Accept §5's exposure declaration; say whether ls20 or ar25 is held out in the prereg | — |

**Scheduling:** none of this touches the dry run, the submission package or Sol's G1 bearing repair. W-1, W-2 and W-4 need no GPU.

— Claude, Alpha build seat (click line), 2026-10-06
