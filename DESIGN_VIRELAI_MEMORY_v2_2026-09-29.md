# Design: Virelai memory and the controller executor

**Type:** `DESIGN_VIRELAI_MEMORY` · **v2** · **2026-09-29** (supersedes v1 of 2026-09-28)
**Author:** Claude (Alpha build seat), signed
**Status:** **RATIFIED** by the Director on 2026-09-28: "all are ratified" (D1–D7 in §11, all
yes). It is the governing plan we build toward; §12 lists what stays fixed and what adapts. The
build status of each stage is recorded in the build plan's revision ledger (plan v6 onward), not
here. Stage M-0 (R9-R06) is the first build.
**What changed from v1** (recorded as the design's §12 requires, from building stage M-1, R9-R07):
- §5.3: the slot budgets are tuned against the measured cards.
- §5.3 now records how the card presents itself to Duck.
- §5.3.1 is new: certified fields are filled by the controller.
- The G3 probe is placed on the card.

No law, tier, ruling or test changed.
**Scope:** the Cybernetic Duck (Ring 9) in CLICK worlds, designed so that NAV and cross-level work
(G9) fit without redesign.

**Director rulings this design implements (2026-09-28):**
1. "We must have a large memory ability for the agent. That is the only way our internal world
   model can exist." The agent "must live in the moment with enough tokens to reason while still
   having access to its entire accumulated memory based on the gates it has passed."
2. "The controller should execute scripted moves when possible, which in theory should get us to
   gate 3 without needing the Duck."
3. "This is not something we should implement piecemeal." Build one comprehensive plan, even
   though targets shift as results come in.

**Evidence and prior art:**
- `REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md`
- `MINE_AGENT_MEMORY_PRIOR_ART_v1_2026-09-28.md`: external sources and URLs are there, not
  repeated here.

**Ported from our own record:**
- `BUILD_SPEC_G3_CONTEXT_COMPACTION_v1` (the Duck Turn Contract)
- `BUILD_PLAN_RING8_PERSISTENT_WORLD_MODEL_v1`
- the Ring 8 expandable memory card

---

## 1 · Why memory is the architecture, and where the score comes from

**The canon.** "The belief state is the only brain." Duck's context is not the world model. It is
a *view* of the world model that the controller holds and certifies.

**The scoring.** ARC-AGI-3's scoring (RHAE, from `ARC_3_Official.pdf`) makes this concrete:
- Each level scores `min(1.15, (human_actions / our_actions)²)`.
- Levels are weighted 1…n within an environment.
- In a 6-level world, level 1 is 1/21 of the score and levels 2–6 are 20/21.
- ft09's level 1 human baseline is 43 actions. Our exploration of level 1 has cost more than 121.

**What follows:** exploring an early level is an *investment*. It is repaid only if the certified
knowledge carries forward and makes later levels cheap. Memory is the mechanism that repays it.

The design therefore has two jobs:
1. Keep Duck's working context small and decision-ready, so it can reason.
2. Keep everything the gates have certified available to Duck (pinned when compact, recallable
   when detailed), across lives and, through G9, across levels.

## 2 · Constraints: measured and assumed

| Constraint | Value | Source |
|---|---|---|
| Model | Qwen3.6-27B-FP8, local vLLM, thinking on | package receipt |
| Context window | 65,536 tokens | `LOCAL_ANALYZER_CONTEXT_WINDOW` |
| Card guard (ours, not Kaggle's) | 24,000 characters of gate payload (`tool_agent.py:50`) | code |
| Generation speed | ≈ 35 tokens/s (single stream) | v2 `summary.txt` |
| Generated tokens per Duck turn | mean 1,348 (G2) / 1,230 (G3) | v2 `benchmark.json` |
| Wall time per action (one Duck turn each) | ≈ 36–38 s | v2 `benchmark.json` |
| Recall queries Duck made | 0 in 121 actions | v2 transcript |
| Scoring | per-level (h/a)², capped at 1.15, levels weighted 1…n | `ARC_3_Official.pdf` §4 |
| Private environments | 55 | ARC-AGI-3 technical report, dataset table |
| Kaggle notebook runtime | **assumed** 12 h. This is Tufa's `deploy_kaggle.py` default; unverified for the 2026 competition. | code |
| Parallel throughput (several games at once on one GPU) | **unmeasured** | — |

**What the numbers say:**
- The **context window is not the binding limit.** The card is about 6–7k tokens of 65k.
- **Wall time is the binding limit.** Under the assumptions above, running one game at a time
  gives about 13 minutes, or about 20 Duck turns, per environment.
- The largest cost is Duck turns spent on moves the controller already chose. G3 on ft09 cost 64
  full turns (about 37 minutes) with zero decisions.
- Memory design and turn economy are therefore one design.

## 3 · What failed, stated once

- **The card overflowed four times**, at 277,963 → 24,632 → 67,939 → 25,502 characters. Each
  time we trimmed the field that overflowed.
- **Root cause.** Every gate's working view is a *copy of the gate's full state, then trimmed*
  (`virelai_gates.py:3629 _working_gate_view`, `:3778 _bound_working_card`). A field nobody
  trimmed reaches Duck by default. In v2 that was the confirmation records (+957 characters per
  lever) and the dossier answers (+1,094 per lever), plus "notable" entities: capped at 8, but
  each is large.
- **The card is also larger than the gate payload.** The whole user message is assembled from
  several sections:
  - the automatic briefing (`tool_agent.py:1606`)
  - the controller focus (`:1200`)
  - the gate payload (`:1286`, `:1328`)
  - the summarized knowledge lines (`:1531`)
  - the prompt body (`:1683`)

  Only the gate payload is guarded.
- **Recall existed but went unused.** The `entity`, `inventory` and `evidence` queries exist, and
  Duck called none of them.

---

## 4 · The memory laws

Each law ends in a test (§10). The laws are proposed as the governing doctrine for memory and,
once ratified, are appended to the friction-axioms doctrine.

- **M1 · The record is complete and controller-written.**
  - Every transition is recorded losslessly and append-only.
  - Duck never writes the record.
  - The record already exists: the lossless outcomes, gate events, answers and snapshots.
- **M2 · Only certified knowledge enters the world model.**
  - A product is promoted into the world model only when its gate certifies it.
  - A contradiction reopens it, and the reopening is visible.
  - Refutations and scoped nulls are kept in the record and are recallable. They are not pinned.
- **M3 · The card is built, never trimmed.**
  - The model-visible message is assembled from a fixed schema of named slots, each with a
    character budget.
  - Content that has no slot cannot reach Duck.
- **M4 · The card's size does not depend on world size or on how much has been found.**
  - This is A6 v2. Every list on the card is windowed to the current work, with a count and a
    recall handle.
  - The certified digest is grouped by identical signature, so it stays bounded.
- **M5 · The present is never hidden.**
  - Anything the current decision needs is on the card: the target, the template, and the
    evidence for the current subject.
  - Only history moves behind recall.
- **M6 · Recall is injected first and pulled second.**
  - When the current step touches something the memory knows, the controller places it in the
    recall slot.
  - Duck can also query anything from Python.
  - Both paths are tested for delivery: the content must appear in the next message Duck
    actually sees.
- **M7 · Compaction is deterministic projection.**
  - No model summary is used anywhere in memory.
  - Counts, windows, identifiers, grouped signatures and placeholders are rendered from
    structured state. Identical state renders to identical bytes.
- **M8 · Duck spends turns only where judgment is needed.**
  - A move the controller can compute is executed by the controller: one action, then the new
    frame is read, then the next decision.
  - Duck is woken for hypotheses, explanations, predictions whose content is not mechanical, and
    choices between experiments that are not equivalent.
  - The law "one frame in, one action out" is kept. The executor never queues a plan.
- **M9 · Scope.**
  - The world model is scoped to the level and persists across lives on that level.
  - When a level ends, its model is frozen as a finished level model.
  - Carrying it to the next level is a hypothesis layer until behaviour re-confirms it (G9).
- **M10 · Every memory path is measured.**
  - Each turn is logged with: prompt characters per slot, estimated tokens, generated tokens,
    wall time, who acted (the controller or Duck), and actions.

---

## 5 · Architecture: three tiers and an executor

```
                ┌──────────────────────── CONTROLLER (sole writer) ────────────────────────┐
 frame ──►  RECORD (lossless, append-only) ──gate certifies──►  WORLD MODEL (typed products)
                │        ▲                                            │
                │        └──────── recall (inject / pull) ────────────┤
                ▼                                                     ▼
         EXECUTOR: owner(next step)?  ── CONTROLLER ──►  step env (1 action) ──► record
                          │
                          └── DUCK ──►  CARD BUILDER (slots + budgets) ──► Duck turn ──► action / answer
```

### 5.1 · The record tier (exists; gets one interface)

**What it holds.** Lossless probe outcomes, gate events, gate answers, each gate's `snapshot()`,
and the target-journal products. All of it is already produced.

**New: a read-only `MemoryStore` facade** over the record and the world model. It is the single
place every recall goes through, whether injected or pulled:
- `MemoryStore.product(product_id)`
- `MemoryStore.subject(entity_id)` returns an object's file: sightings, witnesses,
  confirmations, dossier and product lines.
- `MemoryStore.site(row, col)` returns prior outcomes at a click site.
- `MemoryStore.transitions(offset, limit)`
- `MemoryStore.evidence(evidence_id)`

Every method is paged and bounded. The facade writes nothing.

### 5.2 · The world-model tier (certified products, one digest line each)

| Gate | Product (existing type) | Promoted when | Digest line (template) | Invalidated by |
|---|---|---|---|---|
| G0 | ActionMetadata | G0 closes | `[G0] actions: ACTION6 (coordinates)` | — |
| G1 | EgoLaw | G1 closes | `[G1] ego: POINTER (god mode) · law …` | contradiction → REOPEN |
| G2 | CounterGateProduct: CounterModel and MaskLaw | prediction SUPPORTED and purity holds | `[G2] counter: bar row 63 (64 cells) 12→11 ×2 · trigger EFFECTIVE_TRANSITIONS_ONLY · masked · remaining 38` | monitor REOPEN |
| G3 | LeverInventory, plus one line per lever | inventory accepted | `[G3] levers 8: LOCAL recolour 9↔8 6×6 ×8 {E0053@36,36 …} · nulls 54 · unknown 0` | a lever retraction |
| G4.1 | LeverEffectAnatomySet | anatomy answers accepted | `[G4.1] anatomy: 8 levers · channel LOCAL · rewrite 9→8 (36 cells)` | — |
| G4-A | LeverOrbitSet | per lever, when its run is confirmed | `[G4-A] orbits: toggle period 2 ×5 · pending 3 · interrupted 0` | DIVERGED run |
| G4-B/C | relations / law set (future) | predictions supported | `[G4-B] E0053∘E0054: …` | a failed prediction |
| Level | level win record (Ring 8 precedent) | level completed | `[L1] won at t… · final state …` | — |
| G9 | carry hypotheses (future) | level entry | `[carry?] levers like L1 … (unconfirmed)` | re-probe |

**Rules:**
- **Grouping.** Lines are grouped by *identical signature*: same class, same shape, same rewrite,
  same result. Eight identical levers render as one line with an ID list. Anything that differs
  in any field gets its own line. Grouping never merges non-identical items (M7).
- **Budget.** The digest slot is 4,000 characters. If the grouped digest still exceeds it, the
  oldest gate's lines collapse to one count line with a recall handle. Most recent gates stay
  expanded. The collapse is recorded in the line itself.
- **Lane for Duck's notes.** Duck may attach *annotations* (names, hunches) through its answers.
  They are stored in a separate UNCERTIFIED lane, shown only if a slot budget allows, and always
  labelled as proposals. Only the controller promotes. This keeps the writer rule (M1, M2) while
  still letting Duck contribute language.

### 5.3 · The card tier (built from slots)

The card is the **whole model-visible user message**, not just the gate payload. The system
prompt and tool schemas are fixed and measured separately.

| Slot | Content | Budget (characters) |
|---|---|---|
| Slot | Content | v1 budget | v2 budget (as built, R9-R07) |
|---|---|---|---|
| S1 Goal | goal question and completion predicate, unmet requirements, done-when, target, rules | 1,000 | 2,000 |
| S2 Subject | the current object or lever: identity, cells (bounded), its evidence for this step | 2,000 | 2,000 |
| S3 Last transition | compact changed-cell summary, counter-masked | 1,500 | 600 |
| S4 Template | the answer template, or the action capability (probe token, admissible actions) | 2,500 | 3,000 |
| S5 World model | grouped digest (§5.2) | 4,000 | 3,000 |
| S6 Recall | controller-injected facts about the subject or site (§5.4; built in M-3) | 2,500 | 2,000 |
| S7 Progress | counts, a window of the ranked list, the budgets the world imposes (§6) | 1,500 | 1,500 |
| S8 Index | the recall handles available, one line each | 800 | 800 |
| Envelope | schema, gate, status, next operation, card meta | — | 700 |
| **Total** | | 15,800 | **15,600** (≈ 4.5k tokens) |

**Why the budgets moved.** They were tuned against the cards measured on the real ft09 records
and on stress worlds.
- **The goal grew.** The goal question plus the completion predicate plus a gate's done-when and
  rules runs about 1,000–1,900 characters.
- **The last transition shrank.** It needs counts and a bounding box, not cells.

Measured largest cards in the R9-R07 tests:

| Gate | Largest card (characters) |
|---|---|
| G2 | about 5,800 |
| G3 | about 3,750 |
| G4.0/4.1 | about 4,300 |
| G4-A | about 6,500 |

Each is the same whether the world holds 2 levers or 20.

**How the card presents itself to Duck.**
- The fields Duck already acts on stay at the top level, under the names the prompt uses:
  `gate_id`, `status`, `next_operation`, `current_probe`, `instruction` and `answer_template`.
- The slots follow as named blocks: `goal`, `subject`, `last_transition`, `world_model`,
  `progress`, `index`, and `recall` from M-3.
- `virelai('gate')` returns the same card. Query errors return the card, not the full gate view.
- **Placing the current probe.** It appears on the card whenever the gate's next operation is to
  take a probe, including G3's roster. Duck no longer spends a query to fetch it.
- **Windowing a guided capability.** A guided capability's lever list is ordered with the current
  work first, then windowed, so the window always shows the next lever to study.

**Build rule.** Each gate adapter implements `card_slots()`, which returns typed slot objects.
One `CardBuilder` renders them:
- Each slot is enforced to its budget by deterministic rules: a list becomes a window plus a
  typed remainder line, and a record becomes a handle. Nothing is ever cut mid-record.
- The builder reports each slot's size in the turn ledger (M10).

The existing 24,000-character guard stays as a tripwire that should never fire.

**Grid.** The current frame is delivered as it is today, through the multimodal current grid.
The design does not change frame delivery.

#### 5.3.1 · Certified fields are the controller's to fill (new in v2)

Some answer templates carried controller-certified data that Duck had to copy back exactly:
- evidence references;
- the counter's 64-cell footprint;
- G3's certified entity lists, which grow with the world;
- G4.1's effect channels.

That broke M4 (the G3 inventory template grows with the roster), and it spent Duck's tokens on
copying.

In v2, the card shows each such field as `CERTIFIED`. The controller fills it from the live
template when the answer arrives (`fill_certified_fields`):
- A field Duck omits or leaves marked is filled.
- A field Duck does write is kept and **validated as written**, so a wrong value is still
  refused.

What Duck needs to read in order to answer stays on the card in the subject slot: the counter
candidate, the record's trigger class, the lever's effect summary, and the lever's channels.

The certified fields are, per gate:
- **G2:** `candidate_id`, `evidence_refs`, `novel_prediction.scope`.
- **G3:** `effect_summary`, `evidence_refs`, `lever_entities`, `clean_null_entities`,
  `ambiguous_entities`.
- **G4.0/4.1:** `effect_channels`.

This is M1 (the controller writes what it certified) applied to answers.

### 5.4 · Recall: injected first, pulled second

**The injection rule** is deterministic and keyed on the subject of the current step:
- the entity or lever in S2;
- the click site in S4;
- the gate.

The controller asks `MemoryStore` for facts about that key, in priority order:
1. open contradictions about it;
2. certified product lines about it;
3. its prior outcomes, most recent first;
4. prior outcomes at the same click site;
5. scoped nulls about it.

It fills S6 to budget and adds a remainder line with a handle.

- There is no similarity search, because the key is structural.
- If nothing is known, S6 says so in one line. That tells Duck the subject is unexplored.

**Pull.** One stable Python function: `virelai('memory', kind=…, id=…, offset=…, limit=…)` over
the `MemoryStore` kinds. The existing `entity`, `inventory` and `evidence` queries are kept as
aliases.

- One interface only, because the ARC-AGI-3 winners found hand-crafted tools hurt this model.
- Results count against the same request budget.

**Delivery.** Both paths are verified in the next message Duck actually sees (the
Ring 8 failure class: "computed but omitted").

### 5.5 · The executor (turn economy)

**Decision:** before each Duck turn, the executor asks the gate machine who owns the next step.

```
while not stop:
    owner = machine.next_step_owner()      # CONTROLLER | DUCK | END
    if owner == CONTROLLER:
        execute exactly one bound action via step_env; record; re-read frame   # M8
        continue                                                                # no model call
    if owner == DUCK: build card; one Duck turn
    if owner == END: declared end (A2)
```

**Landing site** (to be interface-checked at file:line before build):
- `solver.py:441 play()` calls `ToolAgent.analyze()` (`tool_agent.py:2745`).
- The executor runs at the top of `analyze()`, or in `play()`, before the prompt is built.
- It reuses the gate-recording path that today lives inside the nested `_handle_action` closure
  (`tool_agent.py:2139`). That closure is **extracted into a method first** (ratchet: extract,
  then call), so controller and Duck actions share one recording path.
- Probe envelopes gain an `executor: CONTROLLER|DUCK` field.

**Stop-and-wake conditions.** The executor hands control to Duck when any of these happens:
- a boundary event (level completed, game over);
- a counter-monitor REOPEN;
- an attribution outcome the gate marks AMBIGUOUS or UNRESOLVED;
- any contradiction;
- budget thresholds (actions, bar, time);
- a DUCK-owned step.

The controller never presses on through the unexpected.

**Ownership by gate (proposed):**

| Gate step | Owner now | Owner in this design | Why |
|---|---|---|---|
| G0 action metadata | Duck answers | **CONTROLLER** | derived from environment metadata |
| G1 ego (CLICK) | Duck answers | **CONTROLLER** | pointer god mode follows from metadata. NAV G1 probes are scriptable too, but NAV is shelved. |
| G2 search (ranked list) | Duck, guided | **CONTROLLER** | Duck followed the rank order exactly in v1 and v2 (ruling: "the ranked list… no thought needed") |
| G2 candidate, purity, trigger class | controller | CONTROLLER | already computed |
| G2 frozen prediction | Duck | **CONTROLLER** | mechanical: when the record is OPEN, predict COUNTER_SILENT on the next dead click (which discriminates between the trigger classes), otherwise COUNTER_REWRITE on the next effective click. Frozen before observation. |
| G2 label (structured) | Duck | **CONTROLLER** | the structured label is the certified content (trigger, rewrite, footprint) |
| G3 sweep and confirmations | Duck issues bound actions | **CONTROLLER** | scripted by ruling |
| G3 re-sweep of G2 total nulls | re-clicked | **inherited, not re-clicked** (recorded as scoped nulls in the recorded state) | saves 54 actions on ft09 (score and time) |
| G3 dossiers | Duck, 1 per lever (3 refusals in v2) | **CONTROLLER** (structured) | the effect summary is computed; the prose is not certified content |
| **Orientation turn** (new, at G3 close) | — | **DUCK** | Duck reads the certified world model for the first time: it can annotate, name things, and propose what to study. The first semantic turn. |
| G4.0 / G4.1 anatomy | Duck answers | CONTROLLER-certified anatomy, **Duck explains** (1 turn) | anatomy is computed; the explanation is judgment |
| G4-A run each lever to its endpoint | Duck presses | **proposed: CONTROLLER runs; Duck explains each confirmed orbit** | the runs are a procedure. This revises the 09-27 "G4 stated target" ruling for G4-A and needs a ruling (§11, D3). |
| G4-B relations and predictions | planned | **DUCK** | Duck's core: hypotheses and predictions |
| G4-C mechanics in plain language | planned | **DUCK** | language and new predictions |

**Estimated effect on ft09 level 1** (from the v2 record and the offline ladder; an estimate, not
a result):

| | Before | After |
|---|---|---|
| Duck turns | ≈ 130+ | ≈ 3–12: orientation, anatomy explanation, orbit explanations |
| Wall time to G4-A complete | ≈ 80+ min | ≈ 5–10 min |
| Actions (the scoring still counts every action) | ≈ 131 | ≈ 77 (the G3 nulls are inherited) |

Actions still exceed the human baseline on level 1. That is the investment §1 describes; it
repays only through G9.

---

## 6 · Scope: lives, levels, and the bar

- **Lives.** A GAME_OVER or reset on the same level is a *life boundary*, not a level boundary:
  - The world model persists.
  - The record continues through the existing reset path (`EntityLedger.observe_reset`, the
    Groundhog-Day precedent).
  - A lever study interrupted by a death is re-studied in the next life.

  This needs a ruling (D4), because A3 as ruled speaks only of level boundaries.
- **Levels.** On completion, the level's products freeze as `LevelModel(L)`. Entering level L+1:
  - the digest shows the L model as *carry candidates*, marked unconfirmed;
  - re-confirmation probes are chosen by G9.

  This design only makes room for G9. G9's probing is its own design document.
- **Budgets on the card.** S7 always shows the three budgets that bind: actions remaining,
  counter-bar cells remaining (once G2 has certified a counter), and wall time remaining. The
  executor uses the same numbers for its stop conditions.

## 7 · Instrumentation (M10)

A new artifact, `{stem}_turn_ledger.jsonl`, with one row per step:
- `executor`
- `gate`
- `action`
- per-slot characters and total characters
- estimated prompt tokens
- generated tokens
- wall seconds
- recall injected (ids) and recall pulled (kinds)

The run summary adds, per gate:
- controller actions
- Duck turns
- Duck seconds
- largest card

This folds in R9-I01 (the target journal persisted to the run artifacts).

## 8 · The Duck Turn Contract, completed

The unbuilt parts of `BUILD_SPEC_G3_CONTEXT_COMPACTION_v1` are subsumed here:
- **Per-section budgets** are §5.3.
- **Worst-case packager preflight** computes the maximum possible request: system prompt + tool
  schemas + the card at every slot's budget + the recall ceiling + the output reserve. A package
  is refused if that exceeds the model window with margin.
- **The delivery test** is T4 in §10.

## 9 · Mapping from today's card fields to the tiers

| Field today | Where it goes | What remains on the card |
|---|---|---|
| `goal_card` | S1 | goal, done-when |
| `inherited_frontier` (windowed roster) | record | S7 window of current plus 5, with a count |
| `source_frontier` | record | nothing (recall) |
| `entity_ledger` | record | the subject in S2 |
| `lifecycle_journal` | record | S7 state counts |
| `attribution_contract.confirmation_records` | record | the current lever's record in S2/S4 |
| `attribution_contract.dossier_answers` | world model (lever product) plus record | S5 digest line |
| `attribution_contract.evidence` | record | handles in S8 |
| `scheduler` | executor | S7 position |
| `answer_template` / `current_probe` | S4 | as is, budgeted |
| `counter_model_ref`, `mask_law_ref` | world model | S5 `[G2]` line |
| `card_bound` | removed | — |
| automatic briefing, controller focus, summarized knowledge lines | S5 / S6 / S7 by content | budgeted, no free text |

## 10 · Acceptance tests (all offline; they must pass before any Kaggle run)

| ID | Test |
|---|---|
| T1 | **Flat card.** Stress worlds with 2, 8 and 20 levers through every gate. The largest card is within 15,800, and `size(20) − size(2) ≤ 1,000` characters at every gate. |
| T2 | **Real records.** The ft09 v1 (57 transitions) and v2 (121 transitions) records replay through the executor. The v2 G3 card measures 25,502 on today's code (regression anchor) and is within budget under the builder. |
| T3 | **Nothing without a slot.** Injecting an arbitrary new field into any gate snapshot leaves the card byte-identical. |
| T4 | **Delivery.** Injected recall, and a pulled `virelai('memory', …)` result, both appear in the next message Duck actually sees (production prompt path). |
| T5 | **Grouping.** 20 identical levers produce one digest line; one differing lever produces two lines. Grouping never merges items with different signatures. |
| T6 | **Executor.** ft09, offline, G0 to G3 closure with **zero model calls** (a mock model that fails if called). One action per step. Artifacts carry the same schema plus `executor`. The stop-and-wake conditions each fire in a synthetic case. |
| T7 | **Promotion.** A product enters S5 only on gate closure. A monitor REOPEN marks its line reopened. |
| T8 | **Lives** (if D4 is ruled yes). A GAME_OVER in the middle of G4-A leads to re-study in the next life, and the world model persists. |
| T9 | **Ledger.** Turn-ledger rows exist for every step, and per-gate totals match the benchmark history. |
| T10 | **Preflight.** The worst-case request computed at package time is within the window, and packaging refuses otherwise. |
| T11 | **Determinism.** The same record renders the same card bytes (M7). |

## 11 · Rulings needed (Director)

| ID | Question | Recommendation |
|---|---|---|
| D1 | Ratify the memory laws M1–M10 as doctrine (appended to the friction axioms)? | Yes |
| D2 | G0–G3 run entirely by the controller, including structured G2 labels and G3 dossiers, with Duck's first turn being the orientation turn at G3 close? This revises how the 09-27 "stated target" ruling applies to G2 in CLICK worlds. | Yes. This is your ruling of today, taken to its conclusion. |
| D3 | G4-A: the controller runs each lever to its endpoint and Duck explains? This revises the 09-27 ruling for G4-A. | Yes, with Duck able to request an extra run |
| D4 | Does a lever study continue across a death on the same level? | Yes (knowledge persists; the world resets) |
| D5 | Does G3 inherit G2's total nulls as scoped nulls in the recorded state? | Yes |
| D6 | May Duck's annotations be stored in an UNCERTIFIED lane? | Yes, clearly labelled and never promoted without a gate |
| D7 | Measure parallel throughput (several games at once on the RTX Pro 6000) in a dedicated Kaggle run before setting per-game budgets? | Yes. It is cheap and settles the biggest unknown. |

## 12 · The build plan: one design, staged

Labels are provisional and assigned at commit, per the label rule.

| Stage | Label | Delivers | Tests | Behaviour change |
|---|---|---|---|---|
| M-0 | R9-R06 | Turn ledger; `MemoryStore` facade (read-only); replay harness over the real ft09 records; extraction of the gate-action recording path out of the `_handle_action` closure | T2 (anchor), T9 | none |
| M-1 | R9-R07 | `CardBuilder`, slot schema, `card_slots()` for G0–G4-A, digest renderer with grouping, packager preflight | T1, T3, T5, T7, T10, T11 | the card only |
| M-2 | R9-R08 | Executor: `next_step_owner()`, controller execution for G0–G3, inherited G2 nulls, controller G2 prediction and structured labels and dossiers | T6 | G0–G3 without Duck |
| M-3 | R9-R09 | Orientation turn, UNCERTIFIED annotation lane, injected recall (S6), `virelai('memory', …)` | T4 | Duck's first turn at G3 close |
| M-4 | R9-R10 | G4.1 split (controller anatomy, Duck explains); G4-A split (per D3); lives rule (per D4) | T8 | G4 economy |
| M-5 | package | `ring9-memory-ft09-v1` on Kaggle, plus the D7 throughput run. Preregistered: zero overflow; Duck turns per gate; minutes to G4-A; G3 closes with the ft09 levers; G4-A progress; bar remaining; card size per gate | review | live |
| M-6 | — | Design document for G9 carry and cross-level memory | — | — |

G4-B and G4-C move after M-5. They are built on this memory, not beside it.

**What stays fixed as results come in:** the laws M1–M10, the three tiers, the builder principle,
the executor's stop-and-wake rule, and the acceptance tests.

**What adapts:** slot budgets, digest templates, the ownership table (a step can move between the
controller and Duck as evidence shows where judgment is needed), and injection priorities.

A change to what adapts is recorded as a design revision (`DESIGN_VIRELAI_MEMORY_v2`, …), never as
a silent edit.

## 13 · Risks and the honest ledger

- **The experiment's claim changes.** With G0–G3 run by the controller, the result is no longer
  "Duck plays". It becomes "Virelai certifies by procedure; Duck reasons where judgment is
  needed". That fits the thesis (software encoding a reasoning process). The paper must say it
  plainly.
- **A controller cannot improvise.** An unmodelled event handled by the controller could waste
  actions. The mitigation is the stop-and-wake rule: anything unexpected wakes Duck.
- **Injected recall can become noise.** It is bounded by its slot budget and keyed structurally
  rather than by similarity. The ledger will show whether Duck uses it.
- **Grouping can hide differences** if signatures are defined too coarsely. Signatures must
  include every certified field, and T5 guards this.
- **The time estimates** assume environment steps are fast relative to model turns. This is to be
  measured in M-0 (the ledger records wall time for controller steps).
- **Kaggle runtime and game count are assumptions** (12 h, 55). D7 measures throughput. The real
  limits must be confirmed from the competition rules before per-game budgets are set.
- **Action efficiency on level 1 stays below the human baseline** under exhaustive study. The
  design moves the cost from time to actions and relies on G9 to repay it. If G9 cannot transfer,
  the per-level score stays low. That would be a plan-level finding for Apex, not something this
  design fixes.
- **The ft09 bar** allows about 32 effective clicks per life, and the full protocol with 8 levers
  exceeds that. D4 decides whether that ends studies.
- **The mythology guard.** This document is design only. Nothing in it is true of the code until
  a stage commits and its tests pass. The State of the Build tags it SPECIFIED.

## 14 · Alignment with the canon

- **The belief state is the only brain.** The world-model tier is the certified belief state, and
  the card is its view.
- **Evidence before belief; falsification.** Promotion only on gate certification; frozen
  predictions, including the controller's; contradictions reopen.
- **The frame is truth.** The record is lossless frames; nothing is paraphrased (M7).
- **One frame in, one action out.** The executor acts one step at a time from the current frame.
  No queued plans.
- **Universality.** No world name, colour or position enters any rule here. ft09 appears only as a
  test fixture and in the worked estimates.
- **PORT default.** The design ports the Duck Turn Contract, the Ring 8 persistent world model and
  expandable card, and external prior art (tiered memory, deterministic compaction,
  harness-injected recall, controller-certified promotion).

— Claude, Alpha build seat, 2026-09-28; v2 2026-09-29
