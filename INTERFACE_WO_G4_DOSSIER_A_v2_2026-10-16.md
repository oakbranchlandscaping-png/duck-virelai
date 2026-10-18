# INTERFACE: WO-G4-DOSSIER-A, durable per-lever mechanics dossiers (v2, 2026-10-16)

**Seat:** Claude, Alpha build seat (Ring 9)
**Status:** binding interface for the build. This revision supersedes `INTERFACE_WO_G4_DOSSIER_A_v1_2026-10-16`. It applies Sol's review (WO-G4-DOSSIER-A interface accepted with rulings R1–R13, the origin-matrix correction, the identity and lever-set rule, the k031 rule, the `library_census.py` exception and eight added tests). Sections 1–4, 10 and 12 are unchanged from v1 except where marked. Sections 5–9 and 11 are restated in full.
**Base:** `ring9-unified` at `e8984c2`, confirmed before any work. All 361 tracked files under `ARC3-Inference/` and all 23 under `tufa-arc-agi-framework/` are byte-identical to the commit's blobs. The runtime directories hold no untracked files. The Mac worktree is at `e8984c2` with a clean tracked state.
**Governing documents:**
- `TARGET_SEMANTIC_LIBRARY_WORLD_MACHINE_v2_2026-10-15`
- `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v5_2026-10-15` (Stage 1)
- `EXECUTION_PLAN_SEMANTIC_LIBRARY_v5_2026-10-15` (§2–§3)
- the WO-G4-DOSSIER-A directive and Sol's interface review

**Evidence for this interface:** read-only probes (§12). These are replays of committed record fixtures with a class-level wrapper that logs the retained attributes after every outcome and answer. They make no production edit.

---

## 0 · Answers the directive asks for first

1. **Everything in the minimum contract can be built without changing a gate**, except three field groups:
   - persistence through a control;
   - reversal by another lever;
   - orbit phase on the current board.

   Every per-lever chapter fact is held in LEVEL-tier attributes of the G3 and G4 adapters (`life_record.PERSISTENCE`, `life_record.py:71-89`). Those attributes are present at every handled census: H1 runs inside `_advance_level` before `_build_level`, and H2 runs in `play()`'s `finally`. The census can read them as attributes without calling a gate method.
2. **Per-lever state the gates accept but v5 loses before aggregate closure.** The probes confirm six cases (§3):
   - G4.1 accepted anatomy answers;
   - G4-A runs that are confirmed but not yet explained, plus broken and in-progress runs;
   - every G4-B graded prediction before the description;
   - G4-C law tests, and a contradicted law test after it reopens G4-B;
   - all G4 content after an upstream product re-emission;
   - the k031 shape, where an orbit product is emitted at a death with no answers and so is UNATTRIBUTED.
3. **Fields that need a later probe:**
   - persistence through a control intervention;
   - reversal by another lever, including re-enablement;
   - orbit phase relative to the current board.

   No live gate produces any of these. `g4_limits.py` is imported by no runtime module, and `g4b_gate.py:9-10` records its retirement. Cross-level limits are UNAVAILABLE (G9 is not built).
4. **Proposed schema:** v6 adds `levels[].lever_dossiers`, one dossier per certified lever keyed by the level-scoped G3 entity id, with seven independently statused chapters (§5).
5. **Validation and evidence rules:** §6.
6. **Shared files and owners:** §8.
7. **Fail-first tests:** §9.
8. **Performance and size risks:** §10.
9. **Rulings:** applied (§11).

---

## 1 · Where per-lever state lives (file:line at `e8984c2`)

| Gate | Adapter | Per-lever retained state | Product, and when it is emitted |
|---|---|---|---|
| G3-LEVERS | `_LeverTarget` | `lifecycle_journal.entities[e]`: state, events, `witness_refs`. `evidence._witnesses[member]` (`LeverWitness`) and `evidence._attributions[member]` (`LeverAttribution`). `_lever_discoveries[member]`, set at `virelai_gates.py:4262`, the first attributed activation. Legacy path: `_dossier_answers[member]` (`:4406`) with `_confirmation_records`. `_repeat_readings[e]` (`:2943`). `entity_ledger.entities[e]` (sightings, current). NAV records. | `LeverInventory` at inventory acceptance (`:4646`) |
| G4-REACTIONS (G4.1) | `_ReactionTarget` (`:5598`) | `_anatomies[e]`: controller-compiled, exact, set at first seed (`:5683`), before any answer. `_answers[e]`: the accepted anatomy answer (`:5746`). | `LeverEffectAnatomySet` only when **every** lever is answered (`:5748`, `:5752`) |
| G4.2-LEVER-ORBITS (G4-A) | `_LeverStudyTarget` (`:5869`) | `_runs[e]`: every `LeverRun`, including BROKEN and INTERRUPTED. `_completed[e]` (`:6258`), `_answers[e]`, `_interruptions[e]` (`:6260-6272`), `_active_run`, `_life_restudies`, `_events`. | `LeverOrbitSet` on each answer (`:6370`) and on each boundary (`:6287`). The payload holds only **answered** levers (`:6290`) plus interruptions and unstudied levers. |
| G4-B-LEVER-RELATIONS | `LeverRelationsTarget` (`g4b_gate.py:79`) | `_regions` (`LeverRegion`), `_predictions`, `_record.conditions`, `_answer`, `_from_record`, `_reopened` | `LeverRelationSet` only on an accepted description (`:293`), a record certification (`:312`), a level boundary (`:223`, `:235`) or an unresolved close (`:160`) |
| G4-C-LEVER-LAW | `LeverLawTarget` (`g4c_gate.py:70`) | `_tests`, `_pending`, `_certified`, `_level_closed`, `_unresolved` | `LeverReactionLawSet` only on SUPPORTED, a level boundary or an unresolved close (`:245-246`). A CONTRADICTED test reopens G4-B and **invalidates** the G4-B product (`:247-249`). |

**Journal rule (`cybernetic_targeting.py:139-141`).** `put()` of any product invalidates the previous product **and every descendant**. A revised G3 inventory (late lever, D15) or a re-emitted G4.1 product therefore removes all downstream G4 products from the active set until they are re-emitted. The adapters keep their per-lever state (`mu_return.seeded`). Stale products stay in `target_journal.history`.

**Order at a level change (`virelai_gates.py:6816-6827`).** Only the **active** adapter sees the terminal outcome before `_advance_level` runs the H1 census (`:6580`). The non-active G4 adapters keep their pre-boundary state as attributes.

---

## 2 · Field inventory and availability

Column meanings:

- **Pre-agg.** Whether the field is persisted today (v5) before the aggregate product closes. "attr" means it is retained only as an adapter attribute.
- **Stops.** Behaviour at:
  - level advance (H1);
  - budget stop (H2 `BUDGET_STOP`);
  - controlled stop (rest in play, followed later by H1 or H2, or H2 `CONTROLLED_STOP`);
  - run end (H2 `RUN_END`);
  - crash or cancellation (H2 `CRASH` or `CANCELLED`).

  For every row these values hold:
  - "A": the field is an attribute present at that census. The dossier reads it, and v5 holds it only if a product holds it.
  - "P": the field is in the active product when that product is active.
  - "S": the field can drop out of the active products because a downstream product was invalidated.

  A hard kill writes no H2. The latest interim model (written only after an H1) is then the last persisted state, for every field (§4).
- **Ch.** The dossier chapter: 1 identity and activation, 2 anatomy, 3 orbit, 4 limits, 5 relations, 6 law tests, 7 contradictions and next tests.

### 2.1 G3 (chapter 1)

| # | Source and product | Exact attribute or field | Lever identity | References | Pre-agg. | Stops | Current consumer | Normalization | Ch. | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | G3, LeverInventory | `lifecycle_journal.entities[e]` with `witness_refs` non-empty | `e` (level-scoped `E####`) | witness ids | attr; the payload `lifecycle_journal` snapshot is in the product once the inventory exists | A, P after inventory | census LEVER role (`library_census.py:409-436`) | state and event list (id, from, to, evidence, actor, reason) | 1 | AVAILABLE |
| 2 | G3 | `evidence._witnesses[member]` with `entity_ledger.member_to_entity` | member to `e` | `witness_id`, `evidence_ref`, `transition_id` | attr; already in v5 `receipts.witnesses` | A | receipts | residue as `cell_runs` | 1 | AVAILABLE |
| 3 | G3 | `_lever_discoveries[member]`: `intervention`, `channel`, `record_ref` `G3-DISCOVERY-…`, `effect_summary`, local and remote residue | member to `e` | `evidence_ref`, `witness_id`, `record_ref` | attr; partly in the census LEVER role | A | census role, G4.1 seed | intervention verbatim; residue as `cell_runs` | 1 | AVAILABLE |
| 3L | G3 legacy | `_dossier_answers[member]` (intervention, `answer_id`, `effect_summary`) plus the `_confirmation_records` certified by `_repeat_readings` | member to `e` | witness and confirmation evidence, `answer_id` | attr; inventory answer only | A | G4.1 seed (`:5658-5674`) | as row 3; the Duck explanation is held by reference only (R4) | 1 | AVAILABLE |
| 4 | G3 | `evidence._attributions[member]` (`LeverAttribution`): changed, counter-masked, ego-motion, ground-exchange, residue, disposition, basis | member | `attribution_id`, `evidence_ref` | attr | A | G4.1 anatomy compile | counts plus `cell_runs` per class | 1 | AVAILABLE |
| 5 | G3 | `_repeat_readings[e]`: witness and confirmation evidence, `repeat_disposition`, `prediction_status` | `e` | evidence refs | attr; in `LeverOrbitSet.g3_pairs` after G4-A emits | A, P later | G4-A card | verbatim | 1 and 3 | AVAILABLE |
| 6 | G3 | `entity_ledger.entities[e]`: first sighting and `.current` (integer, cells, relation, transition), status | `e` | sighting transitions | attr | A | census joins | class, anchor, bbox, cell count, `cell_runs` | 1 | AVAILABLE |
| 7 | census | `_g3_joins` exact one-to-one `(time, integer, cells)` track join | `e` to track | basis | already in v5, on the role identity | n/a | census | copied from the role; context only | 1 | DERIVABLE |
| 8 | G3 | Activation actor: `machine.g3_selection_events` (`entity_id`, `actor`, `at_transition`). The executor of every gate probe is the controller: transition row `gate_id` and `probe_id`, verified at H2 by provenance execution rows. | `e` | selection event, `probe_id` | attr (GAME tier) | A | provenance, agenda | `{chooser, executor, basis}` | 1 | DERIVABLE |
| 9 | G3 | Reachability. CLICK is a direct coordinate (the intervention). NAV uses `procedure_id`, `target_cells`, `_reachability_answers`, `_nav_contact_records`, and the lifecycle state `PRESUMED_UNREACHABLE`. | `e` | contact evidence | attr | A | G3 NAV | typed `DIRECT_COORDINATE`, `NAV_PROCEDURE` or `PRESUMED_UNREACHABLE` | 1 | AVAILABLE |
| 10 | G3 product | `LeverInventory.lever_entities`, `closure` | `e` | product id | P | P | census `inventory_status` | `ACCEPTED` or `PENDING` | 1 | AVAILABLE |

### 2.2 G4.1 (chapter 2)

| # | Source and product | Exact attribute or field | Lever identity | References | Pre-agg. | Stops | Current consumer | Normalization | Ch. | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| 11 | G4.1, LeverEffectAnatomySet | `_anatomies[e]`: `anatomy_id`; channels (id, locality, transform, count, cells, bbox, `integer_transitions`, signed delta); residue counts; `coverage_complete`; `mask_law_version_id`; `attribution_id`; `open_questions`; `limitations` | `e` | witness and confirmation evidence, `dossier_answer_ref`, `attribution_id` | **attr only until all levers are answered** | A; S on a G3 revision | G4.1 card, G4-B regions | channel cells as `cell_runs`; transitions verbatim | 2 | AVAILABLE |
| 12 | G4.1 | `_answers[e]` (`LeverReactionAnswer`) | `e` | `answer_id`, `evidence_refs`, `record_refs` | **attr only** | A | product (all levers) | `answer_id` plus a strict sha16 per field; prose held by reference (R4) | 2 | AVAILABLE |
| 13 | derived | Local affected subjects: the LOCAL channel regions | `e` | witness transition | n/a | n/a | none | each channel kept as a typed region (`cell_runs`, bbox, transitions) with `subject.status = UNRESOLVED_REGION`; subject identity waits for WO-NOUN-CONTINUITY (v2: the compiler invents no identity join) | 2 | AVAILABLE as a region; identity UNAVAILABLE |
| 14 | derived | Remote affected subjects or unresolved regions: the REMOTE channels | `e` | as above | n/a | n/a | none | as above | 2 | AVAILABLE as a region; identity UNAVAILABLE |
| 15 | derived | Exact observed transformation events: the channels' exact `integer_transitions` and `cell_runs` at the witness transition. Links to `description.transitions[t].events` are computed at render time, not stored, because H2 may truncate the description. | `e` | witness transition | n/a | n/a | descriptive ledger | stored as typed rewrites | 2 | AVAILABLE (rewrites); DERIVABLE (event links, render-time) |
| 16 | G3 to G4.1 | Anatomy before G4.1 has seeded (witnessed, inventory not yet accepted) | `e` | attribution | n/a | n/a | none | `compile_effect_anatomy` is pure | 2 | DERIVABLE, **not proposed** (R3) |

### 2.3 G4-A (chapters 3 and 4)

| # | Source and product | Exact attribute or field | Lever identity | References | Pre-agg. | Stops | Current consumer | Normalization | Ch. | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| 17 | G4-A, LeverOrbitSet | `_runs[e][*]`: `run_id`, status, `end_reason` | `e` | step evidence | **attr only**, except a released interruption's run snapshot | A | `orbit_view` | one row per run | 3 | AVAILABLE |
| 18 | G4-A | `LeverOrbit` per run: `state_sequence` (masked world addresses); steps (index, evidence, transition, before and after address, disposition, `world_changed`, count, `changed_cells`, recurrence, period, `boundary_state`); `stop_disposition` | `e` | `evidence_ref` and `transition_id` per step | P only for answered levers | A; P when answered | G4-B regions, G4-A card | addresses verbatim; cells as `cell_runs` | 3 | AVAILABLE |
| 19 | G4-A | `run.confirmation[*]` (expected and after address, disposition) | `e` | evidence | as row 18 | A | product | verbatim | 4 | AVAILABLE |
| 20 | G4-A | `run.lever_class()`, `run.typing()` (pure over the run) | `e` | run | P for answered levers | A | G4-B classes, carry | verbatim | 3 and 4 | DERIVABLE |
| 21 | G4-A | `_completed[e]`, CONFIRMED or DIVERGED and awaiting explanation | `e` | evidence | **attr only** | A | agenda (as ANSWERED) | status `PRODUCT_PENDING` | 3 | AVAILABLE |
| 22 | G4-A | `_answers[e]` (`LeverOrbitAnswer`) | `e` | `answer_id`, `evidence_refs` | P | P | product | id plus sha16; prose by reference | 3 | AVAILABLE |
| 23 | G4-A | `_interruptions[e]`, `_life_restudies[e]`, `_level_closed` | `e` | evidence, boundary | P after the next emit | A, P | product | verbatim | 3 and 7 | AVAILABLE |
| 24 | G4-A | `_events` (NAV `attributed_residue`, intervention per press) | `e` | evidence | attr | A | none | NAV rows only | 3 | AVAILABLE |
| 25 | G4-A | Endpoint: `NULL_AT_OBSERVED_STATE` with `ENDPOINT_CONFIRMED`, `RECURRENCE_CONFIRMED` or `CONFIRMATION_DIVERGED`; saturation from `typing.condition` | `e` | confirmation evidence | as row 18 | A | product | typed | 4 | AVAILABLE |
| 26 | none | Persistence through a control intervention | `e` | none | none | none | none | none | 4 | **PROBE_OWED** |
| 27 | none | Reversal by another lever, including re-enablement | `e` | none | none | none | none | none | 4 | **PROBE_OWED** |
| 28 | derived | Tested limits: the states visited and the boundary-interrupted presses | `e` | runs | n/a | n/a | none | lists | 4 | DERIVABLE |
| 29 | derived | Orbit phase now: the current masked board as an orbit state | `e` | none | none | none | none | none | 3 | **PROBE_OWED** (a masked world address includes the other levers; only the region label below exists) |
| 30 | G4-B, D18 | Region state label `S0…` (`level_record.region_histories`) | `e` (its region) | boards | attr | A | G4-B card | label plus the transition read | 1 | DERIVABLE once regions exist (after G4.1 and G4-A products) |
| 31 | none | Cross-level limits and carry | `e` | none | none | none | none | none | 4 | UNAVAILABLE (G9 is not built; carry is a hypothesis) |

### 2.4 G4-B and G4-C (chapters 5 and 6)

| # | Source and product | Exact attribute or field | Lever identity | References | Pre-agg. | Stops | Current consumer | Normalization | Ch. | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| 32 | G4-B, LeverRelationSet | `_regions[e]` (cells, steps, class) | `e` | anatomy and orbit products | attr; DERIVABLE from content | A | G4-B and G4-C | `cell_runs` | 5 | AVAILABLE |
| 33 | G4-B | `_predictions` where `acted_lever == e` or `e in named`: `prediction_id`, action, `expected[e]`, `observed[e]`, elsewhere, status, missed, `evidence_ref`, `transition_id`, `declared_at_transition` | `e` | evidence | **attr only before closure**; **S after a G4-C contradiction** | A | product at closure | lever-scoped columns only (R6) | 5 and 6 | AVAILABLE |
| 34 | G4-B | `_record.conditions` (`MC-…`) whose action is `e`'s intervention | `e` | evidence per outcome | attr only before closure | A | product | verbatim | 7 | AVAILABLE |
| 35 | G4-B | `_answer.relations` with `e in levers`: structure (levers, `prediction_refs`, all SUPPORTED) | `e` | prediction refs | P | P, S | product | structure as fact; Duck's `claim` by reference (R4) | 5 | AVAILABLE |
| 36 | G4-B | `_from_record` relations (controller-generated, record-certified) | `e` | transitions | P | P | product | verbatim (gate text) | 5 | AVAILABLE |
| 37 | G4-B | Pressed or unpressed: `coverage(_predictions, levers)` | `e` | none | P at closure | A | agenda | boolean | 5 | DERIVABLE |
| 38 | G4-B | `_reopened`, and withdrawn descriptions in `target_journal.history` (STALE) | set | prediction ids, product ids | attr | A | G4-B card | ids only (R13) | 5 and 7 | AVAILABLE |
| 39 | G4-C, LeverReactionLawSet | `_tests` with `acted_lever == e` or `e in named`, including `from_relations` | `e` | evidence | **attr only before closure** | A | product | as row 33 | 6 | AVAILABLE |
| 40 | G4-C | `_certified` (the supported law test), `_level_closed`, `_unresolved` | set | evidence | P | P | product | verbatim | 6 | AVAILABLE |
| 41 | G4-B and G4-C | Declared board or state of each prediction: the masked address before at grading (`OutcomeRecord.seen`), else the board after `declared_at_transition` (`level_record.level_boards`) | `e` | transition | attr | A | G4-C "new" check | masked address | 6 | DERIVABLE |
| 42 | G4-B and G4-C | `_pending` frozen and untaken | `e` | `declared_at` | attr (TRANSIENT) | A | card | status `PENDING` | 6 | AVAILABLE |
| 43 | non-lever subjects affected by a press | | | | | | | `elsewhere = CHANGES` only; no subject identity | 5 | UNAVAILABLE beyond rows 13 and 14 |

### 2.5 Chapter 7, and what is excluded

| # | Source and product | Exact attribute or field | Lever identity | References | Pre-agg. | Stops | Current consumer | Normalization | Ch. | Class |
|---|---|---|---|---|---|---|---|---|---|---|
| 44 | derived | Contradictions: CONTRADICTED predictions involving `e`, DIVERGED confirmations, `RECURRENCE_DIVERGED`, missing conditions | `e` | refs | n/a | n/a | none | typed list | 7 | DERIVABLE |
| 45 | derived | Open questions: the anatomy's `open_questions` not yet answered by chapters 3 to 6, plus every PROBE_OWED field | `e` | none | n/a | n/a | agenda (unchanged) | typed list | 7 | DERIVABLE |
| 46 | derived | Next falsifying experiment, typed (for example `REPEAT_INTERVENTION` from state `i` expecting state `i+1`, or `CONFIRM_ENDPOINT`). Duck's falsifier text is held by reference only. | `e` | none | n/a | n/a | none | structured, never prose | 7 | DERIVABLE |
| 47 | AnnotationLane | Duck notes (UNCERTIFIED) | none | none | none | none | none | **excluded** | n/a | UNAVAILABLE as truth |
| 48 | GAME tier | `machine.levels[*]` (`freeze_level`), `carry` | none | none | none | none | carry, card | **excluded**: these are cross-level hypotheses, a later stage | n/a | UNAVAILABLE |

---

## 3 · Per-lever accepted state that v5 loses today (probe-confirmed)

The probes replay the committed records `ft09_kaggle_memory_v1`, `ft09_kaggle_exit_v1`, `vc33_kaggle_exit_v1` and `vc33_kaggle_carry_v7`. They log the attributes against the active products after each event (`probe_*.txt`).

| Loss | Probe evidence | Effect in v5 at any census taken then |
|---|---|---|
| L1 · G4.1 accepted answers before the last lever | ft09: `g41_answers` goes 1 to 7 at t75 with the G4-REACTIONS product absent; it appears only at 8/8 | No anatomy for any lever, although 7 are accepted |
| L2 · G4-A confirmed run awaiting explanation | ft09 t79, t83, … (`g4a_completed > g4a_answers`) | The confirmed orbit is absent from the product |
| L3 · G4-A broken and in-progress runs | ft09 t88: `g4a_runs` is 4 with 3 completed (an ended run); every `RUNNING` or `CONFIRMING` row | Steps and evidence of unfinished runs are absent |
| L4 · G4-B graded predictions before the description | ft09_exit t109-t116: 8 predictions, G4-B product absent | Every graded relation test is absent |
| L5 · G4-C tests and contradictions | A contradicted law test reopens G4-B and invalidates its product (`g4c_gate.py:247-249`) | The contradiction, the withdrawn description and every G4-B prediction drop from the active products |
| L6 · Upstream re-emission | `put()` invalidates descendants (D15 late lever, G3 revision) | All G4 content drops until it is re-emitted |
| L7 · k031 shape | Saved k031 v4 model: `G4-ORBITS-57ed18b62866f875` is UNATTRIBUTED `NO_DECLARED_CLOSURE` with 0 answers. This is a death boundary with no explained lever (G4-A `_record_boundary`, `virelai_gates.py:6287`). | The orbit content is held but must never certify a mechanic. Per-lever run state is in `_runs` only. |

What H1 already preserves is shown by vc33 carry v7 level 1. The level ended during G4-A. The active adapter emitted `CLOSED_BY_LEVEL_BOUNDARY` with E0004 answered and E0005 in `interruptions`, so v5 kept both. The losses therefore bite at H1 when the level ends through rest-in-play, after a controlled stop (D-3) at any gate, and at every H2 stop.

---

## 4 · Early-stop path map

| Path | Code site | Gate notified? | Census | v5 today | Dossier v6 |
|---|---|---|---|---|---|
| Level advance | `virelai_gates.py:6816-6827`, `:6572-6580` | the active adapter only | H1 `FROZEN` (`level_before`) | active products only | every chapter read from attributes; open chapters become `CLOSED_UNRESOLVED` (`LEVEL_ENDED`) (R1) |
| Death, not the level | G4-A `_record_boundary` (`:6275-6287`); G4-B and G4-C `void` | G4-A emits; G4-B and G4-C void the prediction (INDETERMINATE) | none | k031 UNATTRIBUTED when no lever is answered | no census; the next census shows INTERRUPTED runs as `IN_PROGRESS` with restudy counts |
| Duck G4 budget (D21) | `play_gate.py:59-67` | G4-B or G4-C `close_unresolved` emits UNRESOLVED | none at that point | product holds the predictions | chapters 5 and 6 become `CLOSED_UNRESOLVED` |
| Budget stop | `solver.py:352-365`, `:657-664` | no | H2 `BUDGET_STOP` | active products only | open chapters become `INTERRUPTED` (`BUDGET_STOP`); accepted per-lever work becomes `PRODUCT_PENDING` |
| Controlled stop with rest (submission) | `solver.py:725-748`, `play_gate.py:70-75` | PLAY is forced; gates rest without closing | later H1 or H2 | as above | as above, at whichever census follows |
| Controlled stop that ends the game | `solver.py:367-375` | no | H2 `CONTROLLED_STOP` | as above | `INTERRUPTED` (`CONTROLLED_STOP`) |
| Run end | `_turn_ends_game` and `finally` | no | H2 `RUN_END` | as above | `INTERRUPTED` (`RUN_END`) |
| Crash | `solver.py:651-656`, then `finally` | no; state may be mid-update | H2 `CRASH` | as above | `INTERRUPTED`; nothing is promoted (§5.3) |
| Cancellation | `solver.py:1354-1358` sets stop, then `finally` | no | H2 `CANCELLED` | as above (k031 was CANCELLED) | `INTERRUPTED` |
| Hard kill or timeout | none | no | none | the last interim (written only after an H1) | the same limit: no new write cadence is proposed (R12) |

---

## 5 · Schema v6 (rulings applied)

`SCHEMA = "virelai-world-model-v6"`. The v1–v5 readers and validators are frozen, and a valid v5 artifact reads under `validate_v5`, which is today's rules. v6 adds `levels[].lever_dossiers` and the strict whole-payload check before sealing (R10). Nothing else changes.

### 5.1 Shape

```
levels[i].lever_dossiers = {               # key = level-scoped G3 entity id
  "<e>": {
    "subject":        {"kind": "G3_ENTITY", "entity_id": "<e>", "level": <int>},
    "track_join":     {"status", "track_id", "basis"},   # equals the LEVER role's identity; context, never identity
    "census_context": {"census": "OPEN" | "H1_FROZEN", "persist_reason": <manifest reason | "LEVEL_ADVANCE">},   # R1
    "chapters": {"identity", "anatomy", "orbit", "limits", "relations", "law_tests", "open_items"}
  }
}
<chapter> = {
  "status", "basis",                   # basis from the closed vocabulary of its status (§5.2)
  "prior_status", "prior_basis",       # null unless a census label (R1) or an integrity failure (R8) changed the status
  "source":      "GATE_WITNESS" | "PRODUCT_CONTENT" | "GATE_RETAINED" | "DERIVED" | null,
  "product_ref": {"product_id", "gate_id", "product_type", "revision"} | null,
  "answer_ref":  {"answer_id", "gate_id", "fields": {<prose field>: <strict sha16>}} | null,   # R4: Duck prose by reference
  "evidence_refs": [<E-…>],            # exactly the evidence ids found in facts and history, sorted
  "facts":   {...} | null,             # null when NOT_BUILT or FAILED_CLOSED
  "history": [...],                    # retained rows that are not the chapter's current fact (ended runs, withdrawn descriptions)
  "integrity": {"status": "OK" | "FAILED_CLOSED", "reasons": [<code>], "refs": [<failing ref or transition>]},
  "open":    [{"kind": "PRODUCT_NOT_CERTIFYING" | "PROBE_OWED" | "UNAVAILABLE", ...}],
  "digest":  {"algorithm": "sha256", "encoding": "virelai-canonical-json-v1", "value": <64 hex>}
}
```

The dossier set equals the level's certified LEVER role entities, which includes witness-certified levers whose G3 inventory is still pending. It also includes any lever whose role a record break withdrew; every chapter of such a dossier is FAILED_CLOSED with basis `RECORD_MISMATCH`, so its history stays visible and nothing in it is claimed.

The facts per chapter are:

- **identity** (source `GATE_WITNESS`):
  - the witnesses, copied from `receipts.witnesses`;
  - appearance at the first sighting and now (class, anchor, bbox, cell count, `cell_runs`);
  - the lifecycle state and events;
  - activation (source, intervention, channel, record ref, witness and confirmation evidence);
  - actor (`{chooser, executor, basis}`);
  - reachability;
  - the repeat reading;
  - inventory status.
- **anatomy**:
  - `anatomy_id`, `attribution_id` and mask law version;
  - residue counts;
  - channels (id, locality, transform, count, bbox, `cell_runs`, `integer_transitions`, signed delta, `subject: UNRESOLVED_REGION`);
  - the gate's own open questions and limitations.
- **orbit**:
  - the current run: id, status, intervention, `state_sequence`, and per step the evidence, transition, disposition, count, `cell_runs`, recurrence and period, plus the confirmation rows;
  - lever class and typing;
  - period and recurrence index;
  - life restudies;
  - the interruption record;
  - `history` holds the lever's other runs.
- **limits**:
  - the endpoint (stop disposition, confirmation disposition, confirmed);
  - saturation and mechanism;
  - tested states;
  - boundary interruptions;
  - `persistence: PROBE_OWED`, `reversal: PROBE_OWED`, `cross_level: UNAVAILABLE`.
- **relations**:
  - pressed;
  - the relation tests involving `e` (lever-scoped columns, R6);
  - certification (`DUCK` or `RECORD`);
  - the description reference (answer id, description sha16);
  - the active relation structures involving `e` (levers, prediction refs or record evidence and transitions, claim sha16);
  - missing conditions;
  - record couplings;
  - `history` holds withdrawn descriptions (R13).
- **law_tests**:
  - the G4-C law tests involving `e` (lever-scoped, with `from_relations`);
  - the law status;
  - the certified test id;
  - lever-set membership.
- **open_items** (source `DERIVED`, recomputed whenever any chapter changes):
  - incomplete chapters;
  - contradictions (contradicted predictions, diverged confirmations, missing conditions);
  - rejected models (the withdrawn descriptions);
  - `probe_owed` (`LIMITS_PERSISTENCE`, `LIMITS_REVERSAL`, `ORBIT_PHASE_NOW`);
  - `unavailable` (`AFFECTED_SUBJECT_IDENTITY`, `CROSS_LEVEL_LIMITS`);
  - the typed `next_test`.

A prediction's lever-scoped columns are:

- `prediction_id` and kind (`RELATION_TEST` or `LAW_TEST`);
- action;
- acted and named;
- `expected[e]` and `observed[e]`;
- elsewhere, both expected and observed;
- status, and whether it missed `e`;
- evidence and transition;
- the declared board (`after_transition = declared_at_transition`);
- `from_relations`;
- `because_sha16`.

Duck's text is never a fact (R4). Record-certified relations keep their typed transitions and evidence; their generated claim is held only as a sha16 of a rendering.

The `digest` covers the entity id, the chapter name and the chapter without its own digest, through the shared strict canonical JSON (§7).

### 5.2 Status derivation and basis vocabularies

**Basis vocabulary per status (closed):**

| Status | Bases |
|---|---|
| NOT_BUILT | `GATE_NOT_SEEDED`, `NO_EVIDENCE` |
| IN_PROGRESS | `LIFECYCLE_REOPENED`, `ANSWER_REQUIRED`, `RUN_OPEN`, `RUN_ENDED_RESTART_NEEDED`, `INTERRUPTED_RESTUDY_PENDING`, `ENDPOINT_OBSERVED_PROBES_OWED`, `STUDY_OPEN`, `REOPENED_BY_CONTRADICTION`, `OPEN_ITEMS_REMAIN` |
| PRODUCT_PENDING | `ANSWER_ACCEPTED_AGGREGATE_OPEN`, `RUN_CONFIRMED_EXPLANATION_PENDING`, `AGGREGATE_INVALIDATED` |
| COMPLETE | `WITNESS_CERTIFIED`, `PRODUCT_CERTIFIED`, `NO_OPEN_ITEMS` |
| CLOSED_UNRESOLVED | gate closures: `INTERRUPTION_RELEASED`, `UNSTUDIED_AT_LEVEL_CLOSE`, `PRODUCT_UNRESOLVED`, `PRODUCT_CLOSED_BY_LEVEL_BOUNDARY`; census: `LEVEL_ENDED`; integrity: `RECORD_MISMATCH`, `PRODUCT_MISMATCH`, `EVIDENCE_UNRESOLVED`, `PROVENANCE_INCOMPLETE` |
| INTERRUPTED | `BUDGET_STOP`, `CONTROLLED_STOP`, `RUN_END`, `CRASH`, `CANCELLED` |

**Status derivation per chapter:**

| Chapter | NOT_BUILT | IN_PROGRESS | PRODUCT_PENDING | COMPLETE | CLOSED_UNRESOLVED (gate) |
|---|---|---|---|---|---|
| identity | never | lifecycle REOPENED | never | witness in receipts (`WITNESS_CERTIFIED`) | never |
| anatomy | `e` not in `_anatomies` (R3: G4.1 not seeded) | compiled, answer not accepted | `_answers[e]` accepted, no certifying product covers `e` | certifying product covers `e` | never |
| orbit | no runs | run open, ended (restart needed) or interrupted with restudy | `_completed[e]` (explanation pending), or answered without a covering product | certifying product covers `e` | interruption released; unstudied at level close |
| limits | no run reached a stop | `ENDPOINT_OBSERVED_PROBES_OWED` (R5) | never (no accepted limit work exists yet) | only when no field is PROBE_OWED; never in this slice | follows orbit's gate closures |
| relations | G4-B not seeded, or `e` not among its levers | study open; reopened by a contradiction | the accepted answer's product was invalidated upstream | certifying product (Duck or record) covers `e` | closing product (unresolved or boundary), or the same closure retained |
| law_tests | G4-C not open and no test involves `e` | tests present or G4-C open, law not certified | never | certifying law product covers `e` | closing law product, or the same closure retained |
| open_items | never | items remain | never | no incomplete chapter, no contradiction and no PROBE_OWED field (R7) | never |

**Census labels (R1):**

- At an H1 freeze (level `FROZEN`), every IN_PROGRESS chapter becomes `CLOSED_UNRESOLVED` with basis `LEVEL_ENDED`.
- At an H2 final on the open level (`BUDGET_STOP`, `CONTROLLED_STOP`, `RUN_END`, `CRASH` or `CANCELLED`), every IN_PROGRESS chapter becomes `INTERRUPTED` with that reason as its basis.
- In both cases `prior_status` and `prior_basis` keep the open state.
- `PRODUCT_PENDING` is never relabelled. Its semantic basis stays, and `census_context` records why the model was persisted.
- A live view or an interim write labels nothing.

**Integrity (R8).** The following fail a chapter closed:

- evidence that does not resolve (`EVIDENCE_UNRESOLVED`);
- a covering product whose projection disagrees with the retained gate state (`PRODUCT_MISMATCH`);
- evidence on a transition the H2 record check marks extra, renamed or duplicated (`RECORD_MISMATCH`);
- a withdrawn lever role (`RECORD_MISMATCH`, every chapter).

Failing closed gives `status = CLOSED_UNRESOLVED`, `basis =` the reason, `prior_status` and `prior_basis` set, `facts = null`, `history = []`, `integrity.status = FAILED_CLOSED`. It is permitted on open and frozen levels alike. Unaffected chapters keep their status. `PROVENANCE_INCOMPLETE` is in the vocabulary but no producer sets it in this slice.

**k031 rule.** An orbit product that is UNATTRIBUTED, UNREPRESENTABLE or `NO_DECLARED_CLOSURE` certifies nothing. Retained runs keep their honest partial status. The chapter's `open` gains `{"kind": "PRODUCT_NOT_CERTIFYING", "product_id", "origin", "basis"}`. Recorded evidence stays, and no orbit law is inferred.

### 5.3 Origin matrix (replaces the v1 "COMPLETE requires ANSWER_CERTIFIED" rule)

| Chapter | Product type (gate) | May complete (origin, basis) | Closes without completing | Covers `e` when |
|---|---|---|---|---|
| anatomy | `LeverEffectAnatomySet` (G4-REACTIONS) | ANSWER_CERTIFIED, `PAYLOAD_ANSWERS` | none | `e` in `lever_entities`, with its anatomy and answer |
| orbit | `LeverOrbitSet` (G4.2) | ANSWER_CERTIFIED, `PAYLOAD_ANSWERS` | GATE_DERIVED `ORBITS_CLOSED_BY_LEVEL_BOUNDARY` (per-lever closure from retained state) | `e` in `lever_entities` (answered), with its orbit |
| relations | `LeverRelationSet` (G4-B) | ANSWER_CERTIFIED, `PAYLOAD_ANSWER` or `RELATIONS_CERTIFIED_FROM_RECORD` | GATE_DERIVED `RELATIONS_UNRESOLVED`, `RELATIONS_CLOSED_BY_LEVEL_BOUNDARY` | payload status COMPLETE and `e` in `lever_entities` |
| law_tests | `LeverReactionLawSet` (G4-C) | ANSWER_CERTIFIED, `LAW_TEST_IS_CERTIFIED_PREDICTION` | GATE_DERIVED `LAW_UNRESOLVED`, `LAW_CLOSED_BY_LEVEL_BOUNDARY` | payload status COMPLETE and `e` in `lever_entities` |
| limits | none in this slice | none | none | none |

The validator derives the allowed origin from the chapter and the product type. UNATTRIBUTED and UNREPRESENTABLE products never cover a chapter. COMPLETE is two-way: a chapter is COMPLETE exactly when a CAPTURED product of its type, whose origin is in the "may complete" column, covers `e`. The one exception is a FAILED_CLOSED chapter.

### 5.4 Accepted limitation (R12)

A hard process kill writes no H2. Per-lever work since the last on-disk write, which is the interim model written after an H1, is lost. No new write cadence is added. Handled crash, cancellation and stop paths still write through H2.

---

## 6 · Validation and evidence rules (pure, `lever_dossier_schema.validate_level`)

1. **Set.** The keys equal the LEVER role entity ids plus the subjects of withdrawn-lever RECORD_MISMATCH gaps; the latter are entirely FAILED_CLOSED. `subject.level` equals the level. Repeated `E####` across levels are separate because every check is scoped to its level.
2. **Join.** `track_join` equals the role's `identity`, or the null join for a withdrawn lever. Identity witnesses equal `receipts.witnesses` for `e` exactly. Every witness id inside a dossier resolves to `entity_id == e`. Every run and anatomy carries the activation intervention of `e`. Every prediction row involves `e` (acted or named), so another entity's work cannot be pasted in.
3. **Vocabulary.** The status and the basis come from §5.2. `prior_status` and `prior_basis` are set only for a census label (`LEVEL_ENDED` or a stop) or an integrity failure.
4. **Census context.** A FROZEN level has `{H1_FROZEN, LEVEL_ADVANCE}`; it has no IN_PROGRESS and no INTERRUPTED chapter. An OPEN level has `{OPEN, manifest.persist_reason}`. Under a final reason it has no IN_PROGRESS chapter, and every INTERRUPTED basis equals that reason. Under a non-final reason it has neither INTERRUPTED nor `LEVEL_ENDED`.
5. **Resolution.** `evidence_refs` equals the evidence ids collected from facts and history. Unless the chapter is FAILED_CLOSED, each resolves in `receipts.evidence`. `product_ref` resolves in `product_content` with equal gate, type and revision.
6. **Origin matrix (§5.3), two-way.**
7. **Product agreement.** For `source == PRODUCT_CONTENT`, `facts` and `answer_ref` equal the projection of the stored product payload for `e`, recomputed in the validator. This covers fail-first tests 10 and 12.
8. **Retained consistency.** GATE_RETAINED chapters are never COMPLETE. Their runs satisfy `len(state_sequence) == steps + 1`. Every step and prediction transition agrees with `receipts.evidence[ref].transition_id`. Graded predictions come after their declaration.
9. **Derived.** `open_items` equals its recomputation from the other six chapters.
10. **Failed closed.** `facts` is null, `history` is empty, the status is CLOSED_UNRESOLVED, the basis is `integrity.reasons[0]`, and `prior_status` is set. An `EVIDENCE_UNRESOLVED` failure must name refs that indeed do not resolve.
11. **Digests** recompute.
12. **Fact inventories.** Every chapter's fact keys are a fixed set.
13. **Strict model (R10).** The whole v6 payload passes the strict canonical JSON check before the content hash. This refuses a nested non-string key even in a correctly rehashed model.

The honest limit stands: validation proves resolution and consistency of retained facts, not that they came from the gate machine.

---

## 7 · Canonical JSON consolidation (R10 applied)

`inference/framework/strict_json.py` is the one strict canonicalizer. It provides `check(value)`, `canonical_json(value)`, `sha16(value)`, `digest_record(value)` and `StrictJsonError` with a JSON path. Its rules:

- every mapping key is a string, at every depth;
- integer, float, boolean and null keys are refused;
- NaN and infinity are refused;
- tuples become arrays;
- serialization is `json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)`.

Its users:

- `answer_shapes.canonical_json` wraps it and raises `AnswerProjectionError("NON_JSON_VALUE", …)`;
- `product_content.canonical_json` wraps it and raises `ProductContentError`;
- the dossier compiler and validator use it directly;
- `world_model_v2` runs `strict_json.check` over the whole payload in v6 `seal`, and in v6 validation, before the content hash.

The v1–v5 validators and the content-hash serializer `world_model_v2._canonical` are unchanged, and they are byte-identical to the strict serializer on valid payloads. The legacy gate ID seeds (`_canonical(default=str)`) and the frozen receipt hash `_payload_sha256` are untouched. The seal cost is measured (§10).

---

## 8 · Shared files and owners (Claude is the integration owner)

**New files:**

| File | Contents |
|---|---|
| `strict_json.py` | the shared strict canonicalizer |
| `lever_dossier_facts.py` | pure projections from payload-shaped dicts to chapter facts, shared by the compiler and the validator |
| `lever_dossiers.py` | the gate-view extraction (attribute reads only), the chapter builders, status derivation, integrity, census labels, `attach` and `finalize` |
| `lever_dossier_schema.py` | the pure v6 validator |
| `tests/test_world_model_v6_dossiers.py` | the v6 test suite |
| `tests/dossier_fixtures.py` | committed-record states |
| `tests/fixtures/world_model_v5_frozen.json` | a v5 model sealed by `e8984c2` |

**Edited shared files:**

| File | Change |
|---|---|
| `answer_shapes.py` | delegates to `strict_json` |
| `product_content.py` | delegates to `strict_json` |
| `world_model_v2.py` | v6, frozen `validate_v5`, the strict seal, v6 dossier validation, dispatch v1–v6 |
| `library_census.py` | **+2 approved delegation lines**: `compile_level` returns `lever_dossiers.attach(machine, level)`, and `compile_world_model` calls `lever_dossiers.finalize(...)`. Nothing else. |
| `library_view.py` | cache key with the G4 adapter revisions (R11); a dossier summary line in the digest findings and the selected lever's chapters (R9); a dossier detail page by id |
| `world_description.py` | `_dossiers` renders the stored v6 dossiers, with the v3–v5 `NOT_BUILT` stub kept, plus a chapter-row helper |
| `world_report.py` | dossier and chapter lines from the same rows |
| v5-pinning tests and hand-built v5 models | the version string plus the `lever_dossiers` a v6 model requires, built by the compiler from a stated gate view |
| `tests/tiers/test_tiers.toml` and `T2_collected.txt` | registration |

**Unchanged:** every gate module, the controller, the agenda's choice logic, card, tool agent, provenance, product origins, receipts, admission, lifecycle, coverage, Push and free play. If a gate edit proves necessary, I stop and return the missing field and its call site, and file a second note.

---

## 9 · Fail-first tests (written and run on `e8984c2` before production edits)

Cases 1–22 are as in v1 (table below, with case 4b, 5 and 8 built from replayed record states plus the recorded answers). Cases 23–30 are Sol's additions.

| # | Case | Fixture and setup | Assertion |
|---|---|---|---|
| 1 | A dossier exists before G4 | ft09 v1 replayed to step 70 (gate G3, 6 witnessed, no inventory) | identity COMPLETE; anatomy NOT_BUILT `GATE_NOT_SEEDED` |
| 2 | Anatomy complete, later chapters unbuilt | ft09 v1 with all 8 anatomy answers | anatomy COMPLETE through the certifying product; orbit NOT_BUILT |
| 3 | Two levers at different states | ft09 v1 through t80 | E0053 orbit COMPLETE; E0054 IN_PROGRESS `RUN_OPEN` |
| 4 | Partial work at a level boundary | (a) vc33 carry v7 H1; (b) ft09 through t79 then `freeze_level_census` | E0005 orbit CLOSED_UNRESOLVED `INTERRUPTION_RELEASED`; E0053 PRODUCT_PENDING; open work labelled `LEVEL_ENDED` |
| 5 | Budget stop | ft09 G4.1 at 7/8, `BUDGET_STOP` | 7 PRODUCT_PENDING, 1 INTERRUPTED `BUDGET_STOP` |
| 6 | Controlled stop | as #5 with `CONTROLLED_STOP`; `rest_in_play`, then H1 | the same retention |
| 7 | Interrupted work is not promoted | ft09 through t77, `CRASH` | orbit INTERRUPTED `CRASH`, prior IN_PROGRESS; never COMPLETE |
| 8 | An aggregate cannot hide partial work | G4.1 at 7/8 | v5 content has no G4.1 product; v6 has 7 anatomy chapters with exact channels |
| 9 | Exact resolution | all dossiers | refs resolve; an injected dangling ref is refused |
| 10 | Forged field after rehash | change a COMPLETE orbit's period and reseal | refused |
| 11 | Forged status | PRODUCT_PENDING to COMPLETE, and COMPLETE to IN_PROGRESS, resealed | refused |
| 12 | Product/dossier disagreement | the product payload's anatomy changed with its digests recomputed | refused |
| 13 | No contamination | inject another lever's witness; alter `track_join` | refused |
| 14 | Levels separate | vc33 carry v7, E0004 on both levels | separate dossiers; a cross-level ref is refused |
| 15 | Deterministic | compile twice | byte-identical |
| 16 | v1–v5 compatibility | the frozen fixtures, including the new v5 one | read |
| 17 | Live view | `live_model` | validated; the write is refused; the cache refreshes after an answer with no transition |
| 18 | Page and report | the dossier page and the report | the same rows; refs resolve |
| 19 | Strict JSON | `strict_json`, `answer_shapes`, `product_content` | nested non-string keys, NaN and infinity refused with paths |
| 20 | Hashes unchanged | the v4 frozen `product_answers` sha16 and the v5 frozen digests | equal |
| 21 | k031 shape | ft09 through t77, then a death through `record_outcome` | orbit product UNATTRIBUTED; orbit never COMPLETE; `PRODUCT_NOT_CERTIFYING` |
| 22 | Early stop keeps a completed outcome and its contradiction | `start_g4b`, one SUPPORTED and one CONTRADICTED prediction, then `BUDGET_STOP`; and the G4-C reopen | outcomes and contradiction kept with no G4-B product |
| 23 | Failed closed with prior status | a COMPLETE chapter whose evidence lies on a renamed transition at H2 | CLOSED_UNRESOLVED `RECORD_MISMATCH`, `prior_status` COMPLETE, facts null |
| 24 | Record-derived relations complete | `start_g4b`, all levers pressed, the `LEVER_RELATIONS_FROM_RECORD` answer | relations COMPLETE through `RELATIONS_CERTIFIED_FROM_RECORD` |
| 25 | A gate-derived closure cannot complete | G4-B and G4-C closed unresolved; G4-A closed at a level boundary without answers; a forged COMPLETE | CLOSED_UNRESOLVED; the forgery is refused |
| 26 | Withdrawn relation | the G4-C contradiction reopen | the withdrawn structure is in relations history and open items' rejected models, not in the active relations |
| 27 | Limits stays open | a confirmed endpoint | limits IN_PROGRESS `ENDPOINT_OBSERVED_PROBES_OWED` |
| 28 | PRODUCT_PENDING across reasons | each H1 and H2 persist reason | PRODUCT_PENDING keeps its basis; `census_context` records the reason |
| 29 | First-witness levers | ft09 at step 70 | dossiers for every witnessed lever, inventory PENDING |
| 30 | Strict seal | a nested integer key, model rehashed | refused |

Guards: the gate machine is byte-identical after compilation (the existing census pickle test plus a dossier case), there is no dossier compilation on the controller path, and the digest floor holds within 2,500 characters.

---

## 10 · Performance and artifact-size expectations (to be measured in the build)

- **Measured now** (ft09 G4-B fixture, sandbox): an uncached `live_model` takes 2.90 s on a 1.08 MB model. G4 content is about 7 KB per lever in `product_content` (anatomy 1.4 KB, orbit 2.4 KB, answers 1.2–2.4 KB).
- **Expected dossier size.** COMPLETE chapters store compact facts plus `product_ref`, with no repeated cells. Pending chapters store `cell_runs`. The estimate is 1.5–4 KB per lever: ft09 (8 levers) +1–3%, k031 (12) a similar share.
- **Size risks:**
  - predictions are listed per involved lever. That is O(levers × predictions), but only the lever-scoped columns (about 150 B each) are stored;
  - many restudy runs;
  - k013-scale G3-heavy levels.
- **Expected compile cost:** O(levers × (runs + predictions)), plus one transition-indexed pass over the descriptive ledger. The expectation is at most 50 ms beside the 2.9 s census.
- **Controller path:** no cost added. The dossiers are compiled only inside `compile_level`, which runs on live-view builds, at H1 and at H2. The cache-key change adds about a dozen attribute reads per Duck-turn view.
- **To measure in the build:** compile time; H1, H2 and live cost; model and report growth; digest size; per-lever and per-chapter counts; controller-path cost (expected none).

---

## 11 · Rulings applied

| Ruling | Applied as |
|---|---|
| R1 | census labels plus `census_context`; PRODUCT_PENDING keeps its semantic basis (§5.2) |
| R2 | `GATE_RETAINED` is never COMPLETE; the content is structured, evidence-linked and validated (§6.8) |
| R3 | anatomy stays NOT_BUILT `GATE_NOT_SEEDED` until G4.1 seeds |
| R4 | `answer_ref` with sha16 of prose fields; relation claims and prediction `because` as sha16; record-derived relations as typed transitions and evidence |
| R5 | limits is never COMPLETE while persistence or reversal is PROBE_OWED; `ENDPOINT_OBSERVED_PROBES_OWED` |
| R6 | acted or named; relation tests in relations; law tests in law_tests, each with `from_relations` |
| R7 | open_items statuses as ruled; PROBE_OWED blocks COMPLETE |
| R8 | FAILED_CLOSED becomes CLOSED_UNRESOLVED with prior status and basis, on any level |
| R9 | one findings line of chapter counts, plus the selected lever's chapters only when the selected question names a certified lever; no new section; the budget is unchanged |
| R10 | strict whole-payload check in v6 seal and validation |
| R11 | G4 adapter revisions in the live-view cache key |
| R12 | accepted limitation (§5.4) |
| R13 | withdrawn descriptions keep typed structure, prediction refs, contradiction evidence and status (`CONTRADICTED` or `WITHDRAWN`) with the reason, in relations `history` and open items' `rejected_models` |

The origin matrix, the identity and lever-set rule, the k031 rule and the `library_census.py` exception are applied in §5.2, §5.3 and §8.

---

## 12 · Probe evidence (parked with this interface)

| File | Contents |
|---|---|
| `probe_lost.py` | the class-level read-only wrapper that logs attributes against active products |
| `probe_ft09_kaggle_memory_v1.txt`, `probe_ft09_kaggle_exit_v1.txt`, `probe_vc33_kaggle_exit_v1.txt`, `probe_vc33_kaggle_carry_v7.txt` | the per-event state |
| `probe_h1.py` | the vc33 v7 H1 census content and origins |
| `probe_size.py` | sizes and live-model time |
| `tree_check.txt` | the blob check against `e8984c2` |

The k031 observation was read in place from the saved Kaggle output, through `product_answers` only. No test uses it.

This v2 is filed before any production edit; the shared-file note and the fail-first tests follow it.
