# The two pillars: port from the public notebooks, and learn to win (v1, 2026-10-04)

**Author:** Claude (Alpha build seat), signed. Planning document; nothing built.
**Stated by the Director, 2026-10-04:**
1. *Use what we can of the now-public notebooks: what can we port from others to our agent?*
2. *Learn to win: can Virelai add the ability to truly explain why a win exists, in terms of our own internal language of a given world's mechanics?*

**Repo:** `7f7cb9b` (`main`). The click line (vc33) lives on branch `r9-r20-level-entry`.
**Builds on:** `MINE_M2_NOTEBOOK_SWEEP_v1_2026-10-01`, `STUDY_JUSTADEV742_CONVERGENCE_v1_2026-10-01`, `MINE_FRANZEN_M2_PATCH_v1_2026-10-01`, `REVIEW_LEARN_TO_WIN_v1_2026-10-02`.
**Supersedes** `REVIEW_LEARN_TO_WIN_v1` §0 item 4 and §2's "blocker" paragraph. The level-2 deadlock (D1–D3) is resolved: by carry-vc33-v6 (`1e10466`), level 2 was won at t69 by the G4-A study of E0007, and level 3 was reached.
**Constraints in force:** Directives of 2026-10-03 (`1195028`):
- first scored submission by about 12 October;
- freeze 27–30 October;
- paper by 8 November;
- keep Qwen3.6-27B-FP8;
- about 30 GPU-hours a week across all seats.

Prereg v2 already names Qwen3.6-27B-FP8, so it needs no change. [OBS]

---

## How the pillars relate

Pillar 1 serves pillar 2 and the submission. **The single most valuable port is JustAdev742's goal-predicate machinery, and its only use is pillar 2.** We port nothing that serves neither the gates, nor learn-to-win, nor a scored submission on time.

---

## PILLAR 1 · Port from the public notebooks

**Rules for every port:**
- **Licence.** No licence, no port.
- **Transcribe, never copy.** Each module carries a provenance header with source, commit and licence.
- **Firewall.** The machinery must be generic; nothing derived from reading game source code is ported.
- **Tests first.** Toy-frame tests are written and fail before the port lands.
- **Gate terms.** Ported code takes certified gate products as input, never raw colours.

### Port register (consolidated, ranked)

| # | Component | Source @ rev | Licence | Serves | Status / note |
|---|---|---|---|---|---|
| **P1** | Goal relations: `none_left`, `count`, `aligned`, `same_box`/`rows`/`columns`, `inside`, `overlap`, `touch`, `shape_matches`, `vanish_shape`, `every_<rel>` | JustAdev742 `arc3/dsl.py:1597-1688` @ `8b8a728` | Apache-2.0 | **Pillar 2** (describe step) | **PORT FIRST.** Re-key on certified entity types, not colour. |
| **P2** | Colour-free lift and re-instantiation on a new level (`goal_signature`, `instantiate_goals`) | `dsl.py:1744-1793` | Apache-2.0 | **Pillar 2** (generalise; goal at level entry) | PORT, with P1 |
| **P3** | Satisfied-without-win falsification and distance ranking (`goal_progress`, `goal_distance`) | `dsl.py:1830-1953` | Apache-2.0 | **Pillar 2** (specialise and kill; later, plan) | PORT with the action-gating guard (pillar 2, step C) |
| **P4** | Plain-component frames for goals (lesson 0015) | JustAdev742 tracker | Apache-2.0 | Pillar 2 (perception for goals) | CHECK first: our entities may already be plain components |
| **P5** | Terminal-layer rule (lesson 0017) | `perception.terminal_layer` | Apache-2.0 | Pillar 2 (correct winning frame) | CHECK: our capsule takes `len-2` (`virelai_win_capsule.py:85-90`). Port only the "switch still pending" case if a toy test shows a gap. |
| P6 | Object-change reports (P23/P24) | JustAdev742 `scripts/taaf_ours_patch.py:1133-1637` | Apache-2.0 | Duck's reading of each action (their lesson 0024: helps level 1) | CANDIDATE. Compare with our turn ledger first. |
| P7 | Per-action `plan` line persisted in history | Lord Han Solo `ca1bd02` `python_tool_sandbox.py:206-361` | Apache-2.0 | Glass engine: every action's hypothesis on record | CHECK whether our turn ledger or scientist note already records it |
| P8 | Cause-of-death label (budget ran out vs board killed), checked against the G2-certified budget | Lord Han Solo `solver.py:record_life_action` | Apache-2.0 | Pillar 2 (deaths as non-win evidence) | SMALL. Our life record (R9-R16) is otherwise stronger. |
| P9 | Stall trigger (time since the last clear) | Lord Han Solo `solver.py:244` | Apache-2.0 | Gate re-entry | LOW. A2's general rule already ends stalls (`1e10466`). |
| P10 | `arc3/scoring.py` (RHAE scorer) | JustAdev742 | Apache-2.0 | Prereg metric `a_n/b_n` | PORT when the prereg runs |
| P11 | No-LLM CPU explorer as the prereg floor arm | Lockhart lean, after FrugalExplorer `7dccef1` | MIT-0 | Prereg control | PROPOSED (Director ruling) |
| P12 | Frame-change classes (unchanged / sparse / local / global / resize) | Lockhart lean | MIT-0 | G2/G4 cross-check | LOW |
| — | Serving stack and priority scheduler | Franzen M2 | Apache-2.0 | Throughput | **DEFERRED by R2.** It is built for Qwen3.8 Flash-Next; we keep Qwen3.6-27B. Revisit only prefix caching and the scheduler, for submission throughput. |
| — | Dual wheelhouse-mount resolver | jessky fork | Apache-2.0 | Packaging | **NOT NEEDED.** Our packages already pass three mount layouts (`43e083b`). |

### Not ported, with reasons

- **JustAdev742 lesson 0016 priors** (goal kind constant per game; target drawn on screen; catalogue of goal kinds). They were derived by reading game source code. At most they are a hypothesis our own wins must earn, never machinery.
- **`cognitive-rungs`.** No licence, and its mechanic templates are hand-written world content. Cited only as prior art for the initial-versus-solved diff.
- **Tong Hui Kang M1** (seeds tuned against the hidden set), **karnakbaev** (human answer key, quarantined), **avikdas** (opaque CNN). None of these passes the firewall or serves a pillar.
- **Prompt-advice add-ons** (obirdy, lucifer19, Lord Han Solo's audit text). Our referee replaces advice with enforcement; they are cited as the comparison.

---

## PILLAR 2 · Learn to win

### The question, made falsifiable

> **Can Virelai produce, for an observed win, an explanation written only in its own certified vocabulary of that world's mechanics, which (a) holds at every observed win, (b) fails at the recorded states that did not win, and (c) predicts the next level's win before it happens?**

"Truly explain" is defined by those three tests, not by how fluent the sentence is. An explanation that passes (a) and (b) but fails (c) is a description, not an explanation. One that passes all three on a held-out world is the claim of the paper.

### What counts, operationally

An explanation is **admitted** only if every one of these holds:
1. Every clause cites a certified gate product: a lever and its law (G3/G4), the counter mask (G2), ego (G1), or a relation computed over certified entities (P1).
2. It is true at the winning state of every observed win.
3. It is false across the contrast set:
   - **strict:** earlier uses of the winning action that did not win;
   - **broad:** every earlier state of the level, counted as a counterexample only when a winning-class action was taken from it.
4. It states a condition on the world, not "the last click was on lever X".
5. Its residue is declared: what it does not explain.

A refused explanation is recorded with its reason. **Admission is the referee's decision, made by code; Duck only proposes.**

### The refinement ledger (the Director's 2026-10-02 statement)

Every win updates one cumulative ledger of surviving win conditions:
- **Generalise:** a second win keeps only what both wins share, after the colour-free lift (P2).
- **Specialise:** the condition held, a winning-class action was taken, and no win came. Something is missing. A conjunct or an ordered stage ("then") is added; the order comes from when each part became true in the life record.
- **Kill:** a win arrived while the condition was false.

Every operation cites the transitions that caused it. The ledger renders as one sentence whose clauses each cite a gate product.

### Where we stand [OBS, `7f7cb9b` and branch `r9-r20-level-entry`]

- **Two observed wins on vc33:** level 1 at t26 (G4-A study of E0005) and level 2 at t69 (G4-A study of E0007). Level 3 has been reached.
- **Built:** win capsule, level lesson, gate-side win record (`level_model.py`), life record, level freeze, lever carry (4/4 on level 2, 7/8 on level 3).
- **Partially built:** a separator over old Ring 8 regions with the strict contrast only (`compile_post_win_grammars.py:101-111`). Nothing consumes it.
- **Not built:** an explanation in gate terms, the referee, the ledger, and the goal frozen at level entry.

### Rungs (cheap first; the GPU only at the end)

| Rung | What | GPU | Exit (observable) |
|---|---|---|---|
| **LW-1** | Port P1–P3 (plus the P4/P5 checks), re-keyed to certified entities; toy-frame tests first | none | Toy worlds: a separator is found; a lift survives across two toy levels; a satisfied-without-win case specialises; an action-gated case is not miscounted |
| **LW-2** | G8-EXPLAIN in the gate machine (describe, contrast, Duck's one question, referee) on the **vc33 level-1 record**. The machinery is committed before it runs on any vc33 record. | none (replay) | An admitted or refused explanation, with citations and residue, graded on fidelity |
| **LW-3** | **Retrospective test on level 2:** lift level 1's surviving set, instantiate it at level 2's entry, grade it against the recorded level-2 win. Then update the ledger with that win (generalise, specialise or kill). | none (replay) | A preregistered verdict per candidate, plus the two-win ledger |
| **LW-4** | **Prospective test on level 3:** freeze the ledger's goal at level-3 entry; grade it live | Director's canary (~0.4 GPU-h, like v6) | Reconfirm, specialise or kill, decided before the level-3 win |
| **LW-5** | ft09 (dev), then the held-out worlds under prereg v2 | prereg budget | Learning curve `a_n/b_n`, with repeats |

**Scope fence.** These rungs explain, carry and grade the goal. **Acting on the goal** (planning toward it) is the next slice, gated on LW-4.

### Honesty declarations

- vc33 is a documented dev world, and I read a JustAdev742 docstring that names its win kind. vc33 therefore shows the machinery **works**; it cannot show the machinery **generalises**. That claim waits for LW-5 on held-out worlds.
- The relation set (P1) is fixed from the certified vocabulary and from generic geometry before any win record is opened. It is not tuned to known games.

---

## Rulings owed (Director)

1. **Confirm the two pillars as the campaign,** with "the win is recorded only" (2026-10-01) lifted for pillar 2.
2. **Branch:** build pillar 2 on `r9-r20-level-entry` (the click line). This adds to the merge decision you already owe before the 110-game submission.
3. **Sequencing against the ~12 October submission:** LW-1 to LW-3 need no GPU and can run alongside submission work. Ship the first scored submission without pillar 2, or wait for LW-3?
4. **Lesson 0016's priors:** hypothesis only (recommended).
5. **Broad contrast with the action-gating guard:** adopt (recommended).
6. **P11, the CPU floor arm in the prereg:** yes or no.

— Claude
