# Interface: WO-DESC-B, Duck's semantic world description and the world report

**Version:** v3, 2026-10-13. Supersedes v2 of the same date; v1 and v2 stay in place as history.
**Author:** Claude (Alpha build seat)
**Rulings applied:**
- Sol's review of v1 (rulings 1-7, the semantic corrections, the additional tests);
- `REVIEW_WO_DESC_B_INTERFACE_V2_2026-10-13` (blocking amendments 1 and 2);
- `PRIOR_ART_WEAVE_COMPACTION_TRANSFORMATION_LIBRARY_v1_2026-10-13` §3, §7 and §8.

**Base:** `ring9-unified` at `66b91cb`, verified by Sol.
**This return:**
- this interface;
- the fail-first suite `tests/test_world_description.py`, rerun on `66b91cb` (`failfirst_descB_v3_on_66b91cb.txt`: **50 of 50 fail**);
- the revised folding examples (`FOLDING_EXAMPLES_v3.txt`).

Production follows in the order of §14.

**Governs:** `EXECUTION_PLAN_SEMANTIC_LIBRARY_v4` §3, `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v4` §3, §4 (D0) and §7, and the Director's DESC-B brief.
**Acceptance records:** k008 at transition 45, k013 at 401, and carry-v7 at 20.

## 0a · What changed from v2

| v2 | v3 |
|---|---|
| An event folded when its changed sites were already covered by earlier primary events | **A fold needs evidence** (amendment 1): `OWNER_EXCHANGE` (Ring 7 provenance, adapted to DESC-A footprints) or `G2_MASK_REWRITE`. Coverage is still checked, but alone it never folds. |
| A fold recorded `mirror_of` | It also records its **`basis`** and the **exact exchanged `cells`** (row runs). The validator recomputes them. |
| Display priority: bound role, then mask source, then verb kind | **Explanation strength is added after the bound role**: EXPLAINED, then PARTLY_EXPLAINED, then UNEXPLAINED (prior-art §3.2) |
| `T{n}` ids, ranked by count | **Content-derived ids** (amendment 2). Patterns are `P-` + hash(level, appearance key, verb, rewrite set); questions are `Q-` + hash(level, pattern id, kind). Rank is display only. |
| — | **A residual census** over every verified DESC-A event, including STILL, folded, terminal and ambiguous ones (prior-art §3.3). Bounded lists state "+N more of M". |
| — | The active vocabulary is stated: the nine accepted verbs, plus observed effect types. No historical relation catalogue is claimed (prior-art §5). |

Sections 0 to 4 and 7 to 11 of v2 stand as approved. Their text below is carried over, with only the folding and id references updated.

## 0 · What changed from v1

| v1 | v2 (Sol's ruling) |
|---|---|
| Fold priority: bound role, then verb kind, then age | **The certified mask's source side** outranks its target region, ahead of verb kind (ruling 1) |
| A fold kept only a mirror reference | Every pattern keeps **separate mirror explanation counts** (ruling 1) |
| A 1,500-character world section beside the 2,500-character digest | **One combined 2,500-character library section.** World material takes at most 1,500 of it, and the selected question stays first (ruling 3). |
| `write_canonical` would also write Markdown | **`world_report.write_world_report(sealed, directory)`**, called by the solver only after the model write succeeds (ruling 4) |
| Import `classify_effect_channel` through `virelai_semantic` | **The neutral module `effect_typing.py`**, which the legacy module re-exports. On Duck's surface it is an *observed effect type* (ruling 5). |
| A question could link a role gap "by resemblance" | **Links only through exact references already in the model**; open role identities are listed separately |
| The laws page would show G1's law | **Stored evidence only.** G1 reads "G1 product recorded; structured movement law unavailable". G2 shows its stored mask. |
| New page filters were not wired through the query | **`memory_queries` forwards every new filter**, and continuations keep them |

Rulings 2 (appearance groups), 6 (questions are a view) and 7 (the dossier stub) are approved as proposed.

## 1 · The slice

DESC-B is a pure projection of the validated v3 model. It changes no schema, stored field, gate or agenda. It has three outputs:
- **The semantic view:** objects, folded mirrors, transformation patterns, open questions, the laws, and the dossier stubs.
- **Duck's surface:** a world block inside the one library section, and six bounded pages.
- **`world_report.md`:** deterministic Markdown from the same sealed model.

## 2 · Prior art (WO-00, unchanged from v1 §2)

| Source | Use |
|---|---|
| `library_view` | budgets and paging |
| `joint_transform` | rewrite-centred description |
| `mechanics._effect_channels` | channel grouping, with its identity limits |
| `classify_effect_channel` | effect typing; **extracted to a neutral module** (§10) |
| `render_semantic_library` | explicit empty sections |

None of the legacy writers, roles or compilers is reused.

## 3 · Modules and edits

| File | Change |
|---|---|
| `inference/framework/world_description.py` (**new, pure**) | <ul><li>`describe_level_view(level)` and `describe_world(model)` build the view.</li><li>`validate_level_view(view, level)` and `validate_view(view, model)` raise `WorldModelV2Error`.</li></ul> |
| `inference/framework/world_report.py` (**new**) | <ul><li>`render_world_report(model) -> str` is pure.</li><li>`write_world_report(sealed, directory) -> ReportResult(ok, path, content_sha256, error)` writes atomically.</li><li>`REPORT_NAME = "world_report.md"`.</li></ul> |
| `inference/framework/effect_typing.py` (**new, pure**) | `classify_effect_channel`, moved verbatim from `virelai_semantic/typing.py` |
| `inference/framework/virelai_semantic/typing.py` | Re-exports it: `from inference.framework.effect_typing import classify_effect_channel`. Its four typing guards in `test_semantic_library_shadow.py` stay unchanged. |
| `inference/framework/library_view.py` | <ul><li>`library_digest` gains a `world` block inside the same 2,500 budget.</li><li>`library_page` gains six kinds and six filters.</li><li>`HANDLES` gains one world handle.</li></ul> |
| `inference/agent/memory_queries.py` | `_library_query` forwards `transition`, `from_transition`, `to_transition`, `object`, `verb` and `include_folded` |
| `inference/framework/solver.py` | `_write_l2a_world_model`: after `write_canonical` succeeds, it calls `world_report.write_world_report`. A failure emits observer warning `WORLD_REPORT_WRITE_FAILED`. |
| Tests | `tests/test_world_description.py` (new). Tier sets `T0 desc-b`, and `T1 description` extended. The snapshot gains the new ids. |

`world_model.json` stays `virelai-world-model-v3`, byte-identical. `world_model_v2.py` is unchanged.

## 4 · Semantic objects

- **Named by role only through a binding.** A role-bound track is named `EGO`, `COUNTER` or `LEVER {entity}`. A role name never appears on any other track, whatever a pattern resembles. The validator refuses it.
  - k008's `c9@16,12` MOVE pattern is **not** the EGO.
  - k013's `c14@0,62` SHRINK pattern is **not** the COUNTER.
- **Every other track is named by its first appearance.** The handle is `c{class}@{row},{col}`, followed by "class-{c} {h}×{w} object, {n} cells, first seen at ({r},{c})".
- **An appearance group** (ruling 2) is the tracks whose first segment shares class, anchor and shape hash. It is presentation only:
  - it never joins identities;
  - it never transfers a role, explanation or receipt between tracks;
  - it always states its count of tracks and its lives;
  - the census's identity gaps stand untouched.
- **`open_identity`** lists the level's certified roles with an unresolved identity (k008: EGO and COUNTER; k013: EGO), on their own line, with their gaps.

## 5 · Folding complementary regions (v3: evidence-licensed)

**Ownership read from DESC-A** (no new matcher, no schema change). At transition `t`, an event's footprint groups give each cell's ownership movement:

| Group | Meaning |
|---|---|
| `prior_footprint_only` | the subject gave up the cell |
| `later_footprint_only` | it acquired the cell |
| `retained_rewritten` | it kept the cell, whose value changed. This is **intrinsic** change. |

The track that took or gave a cell is the event at `t` holding that cell in the opposite group. The partition guarantees there is exactly one.

**Continuing:** an event whose subject is seen at both `t-1` and `t`: it has `before` and `after`, and no `gap_from`. BIRTH, DEATH, AMBIGUOUS, a terminal DEFORM and a resumed bridge are **boundary** events, never continuing.

**Order.** For each verified transition, order its non-STILL events by:
1. the subject is bound to a certified role at `t-1`;
2. explanation strength: EXPLAINED, then PARTLY_EXPLAINED, then UNEXPLAINED;
3. the mask source side: `G2_MASK_LAW`, with `before.class` equal to the cited mask's `rewrite.from`;
4. the verb kind: whole-object, then GROW/SHRINK, then DEFORM;
5. the earlier first sighting;
6. the track id.

**Walk them in order.** Each event is primary unless one of these licenses folds it, checked in this order:

1. **`OWNER_EXCHANGE`** (adapted from Ring 7 `weave/provenance.py::complement_verdict`). All of these hold:
   - the candidate is continuing and has at least one changed cell;
   - it has no `retained_rewritten` changed cell;
   - every changed cell it gave up was taken by an already-primary, continuing event, and every changed cell it took was given up by one.

   The partners are those primary events. The cells are all the candidate's changed cells.
2. **`G2_MASK_REWRITE`.** All of these hold:
   - the candidate's explanation is `G2_MASK_LAW` citing mask product `P`;
   - it has no `retained_rewritten` changed cell;
   - each of its changed cells was given up or taken by an already-primary event whose explanation is also `G2_MASK_LAW` citing the same `P`.

   Because DESC-A's explanation already requires every changed cell to lie in the mask and to rewrite `from→to`, the two events jointly instantiate the receipt. This path, and only this path, may fold a boundary event: the target-side BIRTH, or a source-side DEATH. The gate product supplies the relation, not continuing identity.

Coverage is necessary (a licensed fold's cells equal its changed sites, and each lies in a partner's sites), but it is never sufficient.

**Fold record:** `{event_id, transition_id, track_id, basis, mirror_of: [partner event ids], cells: [row runs], explanation}`. The validator recomputes the basis, the partners and the cells from DESC-A and the receipts.

**What the rule guarantees** (each is a test):
- Every verified non-STILL event is primary (in exactly one pattern) or a licensed fold.
- A fold's partners are primary events of the same transition.
- An event with an intrinsic changed cell, or a boundary event outside the mask path, stays primary, whatever overlaps it.
- The primary sites equal all changed sites, so nothing is hidden.

**Mirror explanations stay separate.** A pattern carries:
- `explanations`: its own events, by DESC-A basis;
- `mirror_explanations`: its folds, by their own DESC-A basis;
- `mirror_basis`: its folds, by `OWNER_EXCHANGE` or `G2_MASK_REWRITE`.

**On the records** (`FOLDING_EXAMPLES_v3.txt`, scratch prototype):

| Record | Primary | Folded | Patterns |
|---|---|---|---|
| k008 | 63 | 63: 60 by `OWNER_EXCHANGE`, 3 by `G2_MASK_REWRITE` | 3 |
| carry | 48 | 25: 24 by `OWNER_EXCHANGE`, 1 by `G2_MASK_REWRITE` | 11 |
| k013 | 326 | 239, all by `OWNER_EXCHANGE` (no mask is certified) | 34 |

- **k008:** every mask tick has one primary, source-side statement: `c14@0,0` SHRINK ×42 and DEATH ×1.
  - The target BIRTHs at t1 and t32, and the target GROW at the t30 DEATH, fold through `G2_MASK_REWRITE`.
  - The vacated region's growth on the other ticks folds through `OWNER_EXCHANGE`.
  - The background folds against each ego-like move through `OWNER_EXCHANGE`.
- **carry:** the terrain folds through `OWNER_EXCHANGE`. The witness-touched patterns keep their mixed counts.
- **k013:** the stricter rule surfaces boundary transfers that v2's coverage rule had hidden:
  - The vacated region's BIRTH at each life's first tick (`c0@0,62` ×8) stays primary.
  - So does the counter's last-piece DEATH (×7), and the region's GROW at those DEATHs (×7).
  - The counter's SHRINK at those boundary ticks is no longer folded into the BIRTH, so `c14@0,62` SHRINK reads ×223 (v2: ×215).

  This is honest: with no certified mask, nothing licenses tying a born or dying region to the shrink.

## 6 · The view (`virelai-world-view-v1`)

```text
level view = {
  "level", "scene": {as_of_transition, life, objects_present, objects_departed, record_mismatch, integrity},
  "objects": [{handle, name, tracks, lives, role | null, present}],
  "patterns": [{
     "pattern_id": "P-{sha256(level, appearance key, verb, rewrite set)[:12]}", "rank",
     "object": {handle, name, tracks, lives, role},
     "verb", "sites": [[from, to]...], "events": [...], "transitions": [...], "count",
     "by_action": {action: {delta: n}},           # co-occurrence; worded "on ACTION1 transitions"
     "explanations": {basis: n}, "refs": [...],    # copied from DESC-A, counted, never promoted
     "mirrors": [...], "mirror_explanations": {basis: n}, "mirror_basis": {OWNER_EXCHANGE|G2_MASK_REWRITE: n},
     "observed_effect_type": [{track_id, type, status, witness_count, condition}],
     "sentence"}],
  "folds": [{event_id, transition_id, track_id, basis, mirror_of: [...], cells: [[row, first, last]...],
             explanation: {status, basis}}],
  "questions": [{question_id: "Q-{sha256(level, pattern id, kind)[:12]}", rank, pattern_id, kind, text,
                 unexplained, gaps: [gap index, ...]}],
  "open_identity": [{role, gate_id, subject, gaps: [gap index, ...]}],
  "census": {"verbs": {verb: n}, "explanations": {basis: n}, "folded": n, "primary": n, "still_omitted": n},
  "laws": [...], "dossiers": [...]
}
world view = {"schema", "content_sha256", "levels": [level view, ...]}
```

- **Identity, not rank** (amendment 2).
  - **The appearance key** is the first segment's `(class, anchor, shape_hash)`. **The rewrite set** is the sorted `(from, to)` pairs of the event's changed groups.
  - A pattern keeps its id as transitions accumulate: only its counts, events and last transition advance.
  - **Question kind** is `UNEXPLAINED_TRANSFORMATION` in DESC-B.
  - **`rank`** is display order only. Patterns rank by count, then handle; questions by unexplained count, then most recent transition. Every page handle uses the id.
- **The residual census** counts every verified DESC-A event: emitted STILL, folded, primary, terminal and ambiguous. So no verb is lost between compact patterns and the ledger. `still_omitted` sums the records' `still_omitted`.
- **Bounded lists** (patterns in the world block, examples, events on a page) state "+N more of M", where M counts the full population.
- **A question's `gaps`:** only exact references (subject equals a pattern track, a binding, a receipt or an event id). There are no resemblance links.

## 7 · Duck's surface

**One combined library section of 2,500 characters** (ruling 3):
- `library_digest(model)` keeps its keys and adds `world`.
- The world material takes at most 1,500 characters: a scene line, up to 5 pattern sentences, up to 3 questions, the open-identity line, and one handle.
- **The tiers shrink the world block first, then the library tiers.** The goal, which is the selected library question, is never dropped. The rendered JSON keeps `"goal"` ahead of `"world"`.

**Pages** (`PAGE_BUDGET` 3,000 each):

| Kind | Content | Filters |
|---|---|---|
| `scene` | `scene`, `objects`, `open_identity` | `level` |
| `events` | compact DESC-A events: id, transition, verb, object handle, delta, explanation basis, folded or `mirror_of` | `transition`, `from_transition`, `to_transition`, `object`, `verb`, `include_folded` (default false), `offset`, `limit` |
| `transformations` | patterns, by rank; `id=P-…` pages that pattern's events | `id`, `offset`, `limit` |
| `dossiers` | one stable row per certified LEVER: `{id: entity_id, status: "NOT_BUILT", witnesses, handle}`. The handle stays when WO-G4-DOSSIER-A lands. | `id` |
| `laws` | stored evidence only. G1: `{gate_id, product_id, mode, evidence_refs, structured_law: null, note: "G1 product recorded; structured movement law unavailable"}`. G2: `structured_law` = the stored mask receipt. | `id` |
| `residuals` | questions, then open identities, then unexplained events in no pattern, then description gaps | `offset`, `limit` |

- **Continuations:** `next` repeats **every active filter** (`_call` passes them all).
- **Forwarding:** `memory_queries._library_query` forwards the six new keys beside the old ones.

## 8 · `world_report.md` (ruling 4)

- **`render_world_report(model)`** is pure and deterministic.
  - It has no timestamps.
  - The first line embeds the model's full `content_sha256`.
  - Its sections follow v1 §11. Every claim line carries its refs.
- **`write_world_report(sealed, directory)`** writes atomically.
  - It refuses a `LIVE_VIEW` model and an unsealed one.
  - It renders first, then writes a unique sibling and replaces the report.
  - **On any failure** it removes an existing `world_report.md` and returns `ok=False`. A failed update therefore cannot leave a report of another model. A report that does exist always embeds the hash of the model beside it.
- **The solver** calls it only after `write_canonical` returns `ok`, with the same sealed payload: `write_canonical` gains no Markdown. A report failure never touches `world_model.json`; it is recorded through `_write_observer_warning("WORLD_REPORT_WRITE_FAILED", …)`.

## 9 · The epistemic boundary

- **Roles:** only through bindings (§4).
- **Explanations:** copied and counted, never promoted. A pattern reads `EXPLAINED` only when all its events are.
- **No causal language.** The validator refuses "causes", "caused", "because", "makes", "controls", "drives", "triggers" and "so that" in any rendered string: sentences, digest, pages and report.
- **No new evidence and no stored output.** The model file is byte-identical after the view, and the gate machine is untouched.
- **Questions stay in the view** (ruling 6). Agenda integration is a later, explicit slice.
- **Gaps:** unresolved identities and record mismatches are never omitted for budget. A tier keeps their counts and their handle.

## 10 · Effect typing (ruling 5)

- `effect_typing.classify_effect_channel` is the function moved verbatim. `virelai_semantic.typing` re-exports the same object.
- Importing `effect_typing` loads no legacy compiler (tested in a fresh interpreter).
- On Duck's surface, its `mechanism` field is renamed **`type`** inside `observed_effect_type`. Its status, witness count and condition are preserved. No pattern is called a mechanism, and DESC-B certifies no mechanics.

## 11 · Budgets and cost

| Measure | Prototype | Target |
|---|---|---|
| View compile (folding and patterns) | 3-6 ms on the three records | ≤ 100 ms on k013 at 400 |
| Combined library section | — | ≤ 2,500 characters, world material ≤ 1,500 |
| Page | — | ≤ 3,000 characters |
| Report render | — | ≤ 500 ms |

The view is cached with the live model, under its key.

## 12 · Fail-first suite (rerun on `66b91cb`: 50 of 50 fail)

`tests/test_world_description.py` holds v2's suite and **v3's additions** (amendments 1 and 2, and prior-art §8):

| v3 addition | What it proves |
|---|---|
| `test_an_overlapping_event_with_one_intrinsic_cell_stays_primary` | A background fully covered by a move and a birth, with one cell lost to the newborn, stays primary |
| `test_a_continuing_owner_exchange_folds_with_exact_partner_and_cells` | Folds as `OWNER_EXCHANGE`, with the move's event id and exactly its changed cells |
| `test_an_uncertified_boundary_birth_or_death_is_never_folded_by_overlap[BIRTH, DEATH]` | A pixel born from, or dying into, a bound ego's track stays primary, although the ego's sites cover it |
| `test_a_certified_mask_boundary_birth_folds_through_the_mask_rewrite` | Folds as `G2_MASK_REWRITE`, with the source shrink as partner and the cell `(0,5)` |
| `test_pattern_and_question_ids_survive_an_extended_record` | Compiled at k008 t20 and t45, every surviving pattern and question keeps its id while its counts and last transition advance |
| `test_the_residual_census_counts_every_verified_event` | Every verified event is counted; folds are counted |
| Validator forgeries `fold_basis` and `fold_cells` | A wrong basis and a wrong cell list are both refused |

The recorded failure reasons are unchanged from v2: the new modules, page kinds and filters do not exist yet.

## 13 · Out of scope

- G4 dossier content.
- The agenda.
- A k013 G2 mask law.
- A k008 EGO join.
- G5/G6, the grammar and Push.
- Any schema change.

## 14 · Build order (after this interface)

1. Extract `effect_typing.py` and the re-export, with a parity check against the legacy tests.
2. Build the pure `world_description.py`: folding, patterns, questions, census, laws, dossiers and the validator. Then run the synthetic and saved-record tests.
3. Add the pages, the combined section in `library_view.py`, and the `memory_queries` forwarding.
4. Add `world_report.py` and the solver call after a successful canonical write.
5. Add the tier sets (T0 `desc-b`, T1 `description` extended) and the snapshot. Run T0, then T1.
6. Inspect the actual sentences on k008, k013 and carry, and return them with the measurements.
