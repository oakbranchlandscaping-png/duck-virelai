# Mining record: Daniel Franzen's Milestone 2 solution, against Ring 9

**Type:** `MINE_FRANZEN_M2_PATCH` · **v1** · **2026-10-01**
**Author:** Claude (Alpha build seat), signed. Read-only mining (protocol step 2); no code changed.
**Director ruling (2026-09-30/10-01):** build the gated target system to full force around the best
model; NAV is built as soon as the CLICK gate clears; mine Franzen's patch and licence first.

## 1 · Provenance (pinned)

- **Notebook:** `dfranzen/arc-agi-3-milestone-2-solution` (Kaggle, public, 46 votes, last run
  2026-09-30 08:21 UTC), pulled by the Director 2026-09-30 into `virelai-review/recon_m2/dfranzen/`.
- **Base:** Tufa Labs' Duck, upstream `Tufalabs/duck-harness` `7652836` (the same base as Ring 9),
  via dataset `dfranzen/taaf-kaggle-source-bundle-copy` ("an unchanged copy of Tufa Labs' original
  bundle").
- **The patch:** notebook cell 2 (`/kaggle/harness-changes.patch`), 16 files, about 7.7k added
  lines. It applies cleanly to upstream `7652836` (verified with `git apply --recount`, after adding
  the missing trailing newline).
- **Serving and models (outside the patch):**
  - dataset `dfranzen/pennyroyal-v253`: an SGLang fork, "Pennyroyal" v2.5.3, plus his patches;
  - model `dfranzen/intel-qwen3.8-flash-next-w4a16-autoround`: Qwen3.8-Flash-Next, INT4 W4A16;
  - model `dfranzen/albucino-qwen3-8-flash-next-drafter`: the MTP/NEXTN draft head for speculative
    decoding;
  - notebook cells 4, 12 and 16 hold the environment flags, the server config and the submission
    concurrency.

## 2 · Licence

| Component | Finding | Status |
|---|---|---|
| Franzen's notebook and patch | No licence text in the notebook. Cell 0: "Third-party code and model weights remain subject to their respective licenses." Public Kaggle notebooks conventionally display "released under the Apache 2.0 open source license"; the page did not render to our tools. The competition requires prize-eligible code to be open-sourced. | **Probably Apache 2.0, NOT VERIFIED.** The Director checks the notebook page footer before any port. |
| Tufa Duck upstream (ours and his) | **No LICENSE file** in `Tufalabs/duck-harness` `7652836`. `ARC3-Inference/pyproject.toml` declares the classifier "MIT License"; `tufa-arc-agi-framework` declares nothing. | Existing exposure: Ring 9 already builds on it. Worth asking Tufa to add a LICENSE file. |
| Pennyroyal SGLang fork | Upstream SGLang is Apache 2.0; the fork's own terms are unread. | Unverified. |
| Qwen3.8-Flash-Next (Intel AutoRound) and the Albucino drafter | Weights carry their own licences; not read. | Unverified. |
| Our repo | `LICENSE` is MIT-0 (Stephen Kaskin, 2026). | Apache 2.0 code may be included with its licence and NOTICE kept; the repo then becomes mixed-licence. |

**Gate:** nothing from the patch is copied into Ring 9 until the Director confirms Franzen's licence.

## 3 · What the patch does, by purpose (from the 2026-09-30 code audit)

- **Serving and throughput** (notebook cells, not the patch): an INT4 MoE with MTP speculative
  decoding on tuned SGLang, a 128k context, 10 active streams, and 110 games admitted under a
  priority gate.
- **Allocating GPU time:** `priority_scheduler.py` plus `_PriorityGate` admit and rank games by the
  value of the next level. The endgame switch is "worth 8 to 12% of total score at constrained
  budgets" (his comment).
- **Context management:** drain at 58k, history trimming, prefix-cache-friendly ordering ("15%
  shared prefix against 99%").
- **Perception given to the model:**
  - `frame_diff.py`: Hungarian object matching, reporting moved, rotated and appeared objects;
  - rotation-canonical hashes in `segmentation.py`;
  - diff and game-over diff images in `vision_context.py`;
  - animation frames in `animation.py`.
- **Action-waste guards:**
  - batch no-op stop and stale-state latch;
  - terminal latch;
  - known-death and known-no-op refusals, with the repeat guard in `noop_repeat_guard.py`;
  - most of them start at level 2 (`GUARDS_FROM_LEVEL=2`).
- **Memory:** the upstream world-model block is switched OFF (`ARC3_MEMORY_SECTIONS=off`), because
  "Cross-level notes ZERO" writes were measured across 25 games. Retained Python functions persist
  per game, and a level-transfer prompt is on.
- **His own measurement discipline:** several features ship switched off pending evidence. One
  change set "lost 43% of the previous competition score".

## 4 · Merge feasibility (trial three-way merge, base `7652836`)

Ring 9 at HEAD `40fdcb2` (tree clean) versus upstream patched with Franzen's changes:

| File | Ring 9 vs upstream | Conflict hunks |
|---|---|---|
| `agent/tool_agent.py` | +1115 / -141 | **34** |
| `framework/solver.py` | +239 / -14 | 5 |
| `agent/python_tool_sandbox.py` | +97 / -5 | 6 |
| `agent/prompts.py` | +116 / -1 | 4 |
| `framework/run.py` | +75 / -4 | 0 |
| `utils/openai_compat.py` | +18 / -1 | 0 |
| 4 upstream files Ring 9 never touched, 6 new Franzen files | none | 0 (clean) |

The 34 `tool_agent.py` conflicts sit exactly where the two designs meet: `_build_system_prompt`,
`_build_user_prompt`, `post_chat`, `_handle_action`, `_handle_virelai_query`, the summary/memory turn
context, and `control_yield_reason`. The text merge is tractable. The design question underneath it
is not.

## 5 · The design fork the merge exposes (needs a ruling)

- **Franzen's loop:** the model writes Python snippets that call `action(...)` many times per turn
  (batching), and the guards refuse individual actions inside a snippet.
- **Ring 9's loop:** the controller owns the gate. Scripted gates execute controller actions (G0-G3
  with zero model calls); guided gates admit Duck's actions through a capability token and audit
  the record.

Both can coexist. The gate machine decides **which question is open and what counts as an answer**;
Franzen's loop decides **how fast the model can act and how little it wastes.** The open question is
**who owns the action channel during a guided gate**: Duck's batched snippets, under Franzen's
guards *and* the gate's audit, or the gate's capability token. This is architecture (CE altitude)
and is listed for the Director's ruling.

## 6 · Port candidates, ranked (pending the licence)

1. **Serving stack:** Qwen3.8-Flash-Next INT4 plus MTP draft on Pennyroyal SGLang, with his server
   config. It is the largest single lever in every team's record (the model swap). It lives in
   notebook cells and attached datasets, separable from the harness patch.
2. **The priority scheduler** across games: gate-independent, measured value at constrained budgets.
3. **Context management** (drain, trimming, prefix-stable ordering): gate-independent.
4. **Perception utilities** (`frame_diff`, animation frames, rotation hashes): new files, clean;
   consistent with "the frame is truth"; offered to Duck only when relevant.
5. **Action-waste guards:** they compose with Virelai's exact masked-state identity (the learned
   counter mask replaces the fixed 4-cell border, the documented weakness of their
   "gameplay changed" signal).

**Not ported:** the memory-sections-off flag needs no port. Ring 9 replaces that block with
controller-certified products (the memory card), which do not depend on the model writing notes:
the failure Franzen measured.

## 7 · Open items

| Item | Owner |
|---|---|
| Confirm Franzen's licence (notebook page footer; Kaggle rules on winner licences) | Director |
| Confirm availability and licence of the Pennyroyal, Intel AutoRound and Albucino artifacts on Kaggle | Director |
| Rule on action-channel ownership during guided gates (section 5) | Director (CE altitude) |
| Preregister the comparison: Franzen as-is versus the gated stack, same model and budget, at least 4 paired hidden submissions, plus the glass-engine grading | Build seat, after the rulings |
| CLICK exit not yet met (`f733333`); NAV follows the CLICK clear | Build seat |

— Claude, Alpha build seat, 2026-10-01
