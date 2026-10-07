# State of the Duck build (Cybernetic Duck, Ring 9): the single tree

**Type:** `STATE_OF_THE_DUCK_BUILD` · **v2** · **2026-10-07** (supersedes v1, 2026-09-27, filed in the Engineering project)
**True as of:** `main` = `ring9-unified` = `f333919`. Runtime source floor at `c5e8ff6`: 619 passed, 1 skipped.
**Working tree:** the Mac checkouts carry local, untracked `kaggle/` and `runs/` (never committed).
**Author:** Claude (Alpha build seat, click line), signed
**Reader:** any project, any new collaborator
**Game-free:**
- Worlds are named only as run labels (vc33, ft09, ls20 and so on), never with their mechanics.
- This document compresses the repo. Where they disagree, the repo wins.

**Tags:** **[C]** committed, at a cited commit or file. **[B]** believed, with what would settle it.

---

## 1 · The cursor (what is open now)

| Rung | Exit observable | Owner | Gated by (honest ledger, §5) |
|---|---|---|---|
| **First scored submission** (`DIRECTIVE_COMPETITION_ENDGAME_v2` D-4, about 12 October) | The 110-game dry run graded against C-1 to C-7. Then `ring9-submission-v1` built from `main` and submitted by the Director. | Claude builds and grades. The Director confirms the Kaggle facts and submits. | L-1, L-2, L-6 |
| **NAV G1→G3 handoff, live** (`BUILD_PLAN_RING9_CELL_SITE_TARGETING_v1`) | Sol's short canary `ring9-unified-ls20-cellsite-v1` (48 actions, 1,200 s) meets CS-1 to CS-5: four bearings and the full ego; the roster accounted for; controller-owned approach and contact; at least one target settled and the roster advanced. | Sol | L-1, L-2 |

**In flight:**

| Run | Package and source | State |
|---|---|---|
| Submission dry run | `ring9-submission-dryrun-v1`, from `d751a5b` | Notebook complete; output downloading |
| Sol's cell-site canary | from `4cd7a28` | Pushed 2026-10-07 |
| Unified vc33 canary | `ring9-unified-vc33-v1`, from `b06fa68` | Queued 2026-10-06; no review filed |

## 2 · Open questions for the receiving seat (Director)

1. **The learn-to-win rulings Q-1 to Q-5** (`BUILD_SLICE_LW_1_RELATIONS_REFEREE_LEDGER_v1` §6):
   - Q-1: the relation set is our own closed enumeration;
   - Q-2: the outcome referee now, the transition referee later;
   - Q-3: a read-only check for the winning frame;
   - Q-4: ownership;
   - Q-5: the exposure declaration. The prereg's held-out set is `lp85`, `s5i5`, `su15`, so ls20 and ar25 are not held out.
2. **What an exhausted G3 checkpoint does in a scored run:** end the game, or hand the level to `PLAY-NORMAL` (`REVIEW_SOL_SINGLE_TREE_REPORT_v1` P3).
3. **Which commit the scored package is built from:** `main` with the cell-site repair, if Sol's canary passes CS-5; otherwise `d751a5b` (§3).
4. **The four Kaggle facts:** the runtime limit (9 h assumed), submissions per day (public sources say 1 or 5), the GPU quota, and whether a failed rerun counts.
5. **The ownership table** in `REVIEW_SOL_SINGLE_TREE_REPORT_v1` §5.

## 3 · Horizon

**Short (this week).**
- Grade the dry run.
- Grade Sol's canary.
- Build `ring9-submission-v1` from `main`. Kaggle's save run of the notebook is its rehearsal (about 2.3 GPU-hours).
- Submit by about 12 October.

**Medium: learn to win** (`BUILD_PLAN_PORTS_AND_PILLARS_v1` §2; `PILLARS_PORT_AND_LEARN_TO_WIN_v1`).
- W-1 relations, W-2 referee, W-4 ledger: new files, no GPU.
- Then W-3 (explaining an observed win), W-5 (carrying the goal to the next level), W-6 (the offline vc33 lab) and W-7 (the live level-3 test).
- Exit: an explanation in certified terms, admitted by code, that holds at every observed win, fails where no win came, and predicts the next level's win before it happens.

**Medium: NAV G3 to G4.**
- A roster-drain fixture.
- Then live roster completion and G4 entry on ls20.
- Then NAV-aware `level_record.presses()`, so G4-B can read NAV relations from the record.

**Long.**

| Date | Event |
|---|---|
| 13–24 Oct | Model swap window (D-3) |
| 25–26 Oct | Switch decision (D-8) |
| 27–30 Oct | Code freeze and final submission |
| 2 Nov | Deadline (hour to confirm) |
| 8 Nov | Paper |

`ACT_ON_GOAL` (planning toward an observed goal, R-7) opens only after W-7.

## 4 · Recent frictions (last cycle, ranked)

| Friction | Altitude | Disposition |
|---|---|---|
| G1 accepted Duck's prose movement laws with no structured bearings, so NAV G3 could not take its first step (ls20 unified canary) | code | **Resolved locally** in `4970953`: bearings are compiled from recorded cell changes. Live proof pending (Sol's canary). |
| An exhausted bounded G3 checkpoint ends the game; in a scored run that wastes its slice | architecture | **Escalated** to the Director (§2 Q2) |
| Every Ring 9 notebook checked the game list against a fixed world allowlist, which would raise in a competition rerun | code | **Resolved** in SUB-1 (`d751a5b`): a count-and-uniqueness contract |
| F1: a released NAV target `PRESUMED_UNREACHABLE` counted as unbounded, so a complete roster had no legal move | code | **Resolved** in `fa9617b` |
| JustAdev742's goal relations are generic in form but chosen with game knowledge | plan (firewall) | **Carried:** ruling Q-1, and an exposure declaration (LW-1 §5) |

## 5 · Honest ledger (known wrong or incomplete)

- **L-1** [C]. No unified-tree NAV run has yet made a G3 contact. The ls20 unified canary stopped at the G1→G3 boundary (`REVIEW_RING9_UNIFIED_LS20_V1_KAGGLE`).
- **L-2** [C]. A NAV world with no certifiable bearing still falls to one 256-token model request. If that fails, it is a controlled stop that ends the game (`tool_agent.py:252`, `solver.py:173-178`). Why the request produced nothing is unexplained.
- **L-3** [C]. `level_record.presses()` is click-shaped. NAV G4-B falls back to Duck until it is made NAV-aware.
- **L-4** [C]. Nothing aims play at a win. vc33's best is still 1.51 (2 of 7 levels; v7 and v8). Level 3 has not been won.
- **L-5** [C]. The level records do not keep the board on which a win becomes true; the winning row's after-board is the next level's spawn. W-3 and W-6 need it (LW-1 F-C).
- **L-6** [B]. The Kaggle facts in §2 Q4 come from secondary sources. The competition's Rules tab settles them.
- **L-7** [C]. `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27` is still marked OPEN in the repo. Rotation of the OpenRouter and ARC keys has not been recorded.
- **L-8** [C]. HYBRID's switch from CLICK to NAV, and its mu return, have never run live end to end.
- **L-9** [C]. Long play turns lose their earliest history to the context trim (`tool_agent.py:2830-2848`). It prevents overflow, not forgetting.
- **L-10** [C]. Exposures are declared:
  - su15 (R-4);
  - a docstring naming vc33's win kind (pillars document);
  - remarks on ls20, vc33 and ar25 win relations (LW-1 §5).

  vc33 results show the machinery works, never that it generalises.

## 6 · Build status (the Solver Totality, compressed)

**Tags:**

| Tag | Meaning |
|---|---|
| BUILT | Implemented and live-confirmed in a reviewed run |
| BUILT\* | Built, but with a known incomplete representation |
| PARTIAL | Partly implemented |
| SPECIFIED | Designed, not built |
| NAMED-ONLY | Named, not designed |

| Subsystem | Status | Evidence |
|---|---|---|
| Harness, packaging and verification (self-hosted model and wheelhouse, pinned image, manifests, receipts, secret guard, mount simulation) | BUILT | Every canary since v4; `tools/verify_kaggle_package.py` |
| G0 action surface (CLICK, NAVIGATION or HYBRID, from metadata) | BUILT | Live on vc33, ft09 and ls20 |
| G1 ego, CLICK | BUILT | Live |
| G1 ego, NAV | BUILT\* | Explained live. The bearing product is repaired in `4970953` and proven locally; live pending. |
| G2 counter (find, label, mask, then ignore) | BUILT | Live on vc33, ft09 and ls20 |
| G3 levers, CLICK (first witness, ruling F2a) | BUILT\* | Live under the confirmation rule (v6 to v8). First-witness CLICK has not run live in a reviewed run. |
| G3 levers, NAV (route, contact, first witness, `PRESUMED_UNREACHABLE` with reopening) | PARTIAL | Live contact only in the historical N5.1 record; synthetic tests otherwise |
| G4.1 anatomy and G4-A orbits, CLICK | BUILT | Live on vc33 (levels 1 and 2 won through G4-A) |
| G4-B relations from the record, and G4-C with Duck's 3-turn budget, CLICK (R9-R24) | BUILT | Live on v8: G4 took 136 s, against v7's 163 min |
| G4 for NAV (anatomy, orbits, laws) | PARTIAL | Local tests only. G4-B from the record waits on L-3. |
| `PLAY-NORMAL` with FREE_PLAY receipts, harness-labelled refusals (R-2, R-8) | BUILT | Live on v8 |
| Memory: transition record, life record, level freeze, lever carry, mu bucket, replay | BUILT | Live on vc33 v6 to v8; replay fixtures |
| HYBRID (CLICK then NAV, with mu return) | PARTIAL | Built, never live (L-8) |
| Submission mode (SUB-1: 10 concurrent games, slices, caps, deadline, gateway contract, S-1 and S-2 tests) | BUILT\* | Simulated and rehearsed; the dry run is executed, its grade pending |
| G5 environmental forces, G6 scoped inertness, G7 novelty under the counter mask | NAMED-ONLY | `CYBERNETIC_TARGET_TREE_v1` |
| G8 win explanation and the W-series (relations, referee, ledger) | SPECIFIED | `BUILD_PLAN_PORTS_AND_PILLARS_v1` §2; `BUILD_SLICE_LW_1…` (rulings owed) |
| G9 cross-level transfer | PARTIAL | Lever carry and level freeze built; goal carry (W-5) specified |
| `ACT_ON_GOAL` | NAMED-ONLY | R-7; opens after W-7 |

**Read of the proportions.** The investigative ladder through G4 is built for CLICK and partial for NAV. The submission machinery is built. Everything that makes play aim at a win is specified or only named.

## 7 · The floor

- **Tests** [C]: 619 passed, 1 skipped, on the Director's Mac at `c5e8ff6` (`RECORD_RING9_TEST_FLOOR_v1_2026-10-07`). `f333919` differs only in documents and a packager.
- **Best live score** [C]: vc33 1.51, 2 of 7 levels (`ring9-carry-vc33-v7` and `-v8`).
- **No scored competition submission yet.**

## 8 · The Solver in one paragraph

**What it is.** The Cybernetic Duck is the Virelai Solver's thesis carried onto Tufa Labs' open Duck harness. The thesis: intelligence is the efficient reduction of uncertainty about an unknown world through structured interaction.

**How it works.** A deterministic controller runs a gated ladder:
- action surface;
- ego;
- counter;
- levers;
- lever reactions, orbits, relations and laws.

It records every transition losslessly, certifies each gate's product from that record, and gives the language model (Qwen3.6-27B, self-hosted on one Kaggle GPU) a turn only for what the record cannot settle, within a budget. After the ladder, Duck plays with every certified product on its card.

**What done means in this phase.** A scored ARC-AGI-3 submission of the unified tree. Then a win explained in the solver's own certified vocabulary, admitted by code and carried as a falsifiable hypothesis to the next level. The win is never guessed: it is admitted only from an observed terminal transition.

**Where to start reading.** `handoff/FRESH_TASK_BOOTSTRAP_2026-10-07.md`.

— Claude, Alpha build seat (click line), 2026-10-07
