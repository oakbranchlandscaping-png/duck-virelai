# Interface: WO-DESC-A, schema-v3 descriptive event ledger and scene state

**Version:** v2, 2026-10-13, as built. Supersedes v1 of the same date; v1 stays in place as history. §11 lists where the build refined this text.
**Author:** Claude (Alpha build seat).
**Governs:** `EXECUTION_PLAN_SEMANTIC_LIBRARY_v4_2026-10-12` §2; `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v4_2026-10-12` §2-§4 (D0); `PRIOR_ART_WORLD_DESCRIPTION_GRAMMAR_v1_2026-10-12` §2A-B, §3-§5.
**Ruling applied:** Sol's review of v1, "proceed with amendments" (rulings 1-6, amendments 1-4, the added fail-first coverage).

**Bases:**
- **Integration head:** `ring9-unified` at `5538816`. Every file this slice edits is byte-identical there and at `5fdac9a`.
- **Test-infrastructure and runtime-behavior base:** `5fdac9a` (the tier runner and checkpoint cache, WO-TEST-RHYTHM). Fail-first output is recorded against it.

## 0 · What changed from v1

| v1 | v2 (Sol's ruling) |
|---|---|
| STILL for certified tracks and the acted-site track, counted in `still_count` | Same scope, now with `still_total`, `still_emitted` and `still_omitted` (total = emitted + omitted). Only a role **currently** bound to the track counts. |
| `CAUSED` refused (proposed) | Refused outright. Every event is `OBSERVED`. G4 dossiers may cite event ids later. |
| A class change kept the role and added a gap | The certification history is kept, a `CLASS_CHANGED` gap is added, and the role's binding **ends at that transition**. Later events and the scene do not show the old role. The gate owns retyping. |
| Explanations cited refs only | Receipts carry the evidence needed to **recompute** each explanation. The validator recomputes it and refuses any mismatch. |
| A broken record left later records unverified | Same, and the scene is taken from the **last verified board**. Nothing is derived from boards rebuilt after the break. |
| The v2 read was tested on a v3 object with `description` removed | A **frozen, genuine v2 artifact** produced by the accepted v2 code (`tests/fixtures/world_model_v2_carry_v7_frozen.json`) is read by an explicit v2 validator. |
| Identity from `weave_window` + `re_join` | Unchanged, and now pinned: the description **replays** the same `weave_edge` over the same cuts only to recover the terminal verdicts that `weave_window` discards. No other matcher, no threshold change, no independent join. |

## 1 · The slice in one paragraph

Every level of `world_model.json` gains a `description` chapter (schema `virelai-world-model-v3`):
- **A ledger.** One record per recorded transition, each with zero or more observation events.
- **A presence index.** For each track, the verified node spans in which it was seen.
- **A scene.** The board as of the last verified transition.

An event says what a tracked object did, never why. Its verb is the accepted continuity's verdict on a census track. Its explanation is recomputed from receipts: `EXPLAINED`, `PARTLY_EXPLAINED` or `UNEXPLAINED`. **Its status is always `OBSERVED`.**

## 2 · Where it lives

| Piece | Change |
|---|---|
| `inference/framework/descriptive_events.py` (**new, pure**) | <ul><li>`describe_level` compiles the chapter.</li><li>`explain` gives one event's explanation from stored data alone.</li><li>`scene_at` builds the scene from the presence index.</li><li>`restrict_description` applies H2's verdicts: truncation and roles withdrawn.</li><li>`validate_description` checks the chapter.</li></ul>It imports no gate and mutates nothing. |
| `library_census.project_tracks` | Also returns each window's `cuts` and woven `lines`, the objects it already builds. The track output is unchanged. |
| `library_census._receipts` | **Enriched for v3.** A G2 product with a mask law carries `mask` {`cell_runs`, `cell_count`, `rewrite` {`from`, `to`}, `law_version_id`}. A G3 witness carries `residue` {`local_runs`, `remote_runs`, `cell_count`} and a `witness_sha256` over its whole receipt. |
| `library_census.compile_level` | One helper call attaches the description, after `_fail_closed`. It also:<ul><li>ends role bindings on a class change, adding `CLASS_CHANGED` gaps;</li><li>adds the description's `RECORD_MISMATCH` gap.</li></ul>Two gap loops move into a helper, so the function shrinks (the ratchet). |
| `library_census._apply_check` (H2) | A mismatched level's description is truncated at that level's earliest mismatched id. Roles H2 withdraws are withdrawn from the events too. Explanations and the scene are recomputed. |
| `world_model_v2.py` | <ul><li>`SCHEMA = virelai-world-model-v3`; `V2_SCHEMA` is kept.</li><li>`validate` gives the v2 rules plus the description and the enriched receipts.</li><li>`validate_v2` is the dedicated v2 compatibility validator.</li><li>`read_world_model` reads v1, v2 and v3.</li></ul>It remains the only writer. |
| `library_view.py` | Untouched. Pages and digest are WO-DESC-B. The live view seals v3. |

The description is compiled only where the census is compiled, at H1, H2 and the live view. **It is never on the per-action path.**

## 3 · Identity and verbs: the accepted weave, replayed exactly

`project_tracks` cuts every board (`board_cut`), one window per life, then runs `lines = re_join(weave_window(cuts), cuts)`. For each line, `edges[i]` joins `steps[i]` to `steps[i+1]`, and every step `(node, component)` belongs to exactly one census track.

`weave_window` keeps only the continue verbs (STILL, RECOLOR, MOVE, GROW and SHRINK). It calls `weave_edge(cut[t-1].regions, cut[t].regions)` and discards the rest. The description calls **the same function on the same two cuts** to read the verdicts that were discarded. That is a replay of a deterministic function, not a second matcher.

For each adjacent pair `(t-1, t)` in a window, one event per track touched at `t`:

| The track at `t-1` and `t` | Verb | Source |
|---|---|---|
| Seen at both, joined by a woven edge | That edge's verb (STILL · RECOLOR · MOVE · GROW · SHRINK) | The line's edge |
| Seen at both, joined by a `dominant_mutual_overlap` bridge | `DEFORM`, witness = the bridge kind | The line's edge |
| First seen at `t`, after the window's first cut | `BIRTH` | The line's first step |
| Resumed at `t` after a gap (`occlusion` or `exact_return` bridge) | `DEFORM`, witness = the kind, `gap_from` = last node | The line's edge |
| Seen at `t-1`, absent at `t` | The replayed cascade verdict on that sighting: `DEATH` · `AMBIGUOUS` (`MULTIPLE_LICENSED_SUCCESSORS`) · `DEFORM` (`golden_cascade_unmatched`). Plus `resumes_at` when the track resumes at a verified node. | The replayed `weave_edge` |

- **Every subject is an accepted census track.** The validator refuses an unknown one.
- **A regression test pins it:** every event verb equals the accepted weave's verdict on that sighting, for all nine verbs and for the bridges.
- **The nine verbs** are STILL, RECOLOR, MOVE, GROW, SHRINK, BIRTH, DEATH, DEFORM and AMBIGUOUS. SPLIT and MERGE are not emitted.

**STILL (ruling 1).** A STILL event is emitted only for:
- a track bound to a certified role at `t-1`: an exact identity whose binding has not ended;
- the track holding the action's `acted_site` in cut `t-1`.

Every STILL edge counts once in `still_total`: `still_total = still_emitted + still_omitted`.

## 4 · The chapter

```text
level.description = {
  "schema": "virelai-description-v1",
  "basis": {"continuity": "virelai-golden-weave-v1:weave_window+re_join", "entry_node": n,
            "windows": [{life, from_node, to_node}]},
  "integrity": "VERIFIED" | "RECORD_MISMATCH",
  "first_mismatch": null | {"transition_id", "reason": CONTRADICTED_BEFORE_VALUE | DUPLICATE_TRANSITION
                                                        | MISSING_TRANSITION | JOURNAL_CHECK},
  "transitions": [ <record> ],          # one per distinct recorded transition id, ascending
  "presence": {track_id: [[from_node, to_node], ...]},   # verified nodes only
  "role_bindings": [{role, gate_id, role_ref, track_id, ends_at_transition | null}],
  "scene": <scene>,
}
```

### 4.1 · Record

```text
{ "transition_id", "level", "life", "kind", "action", "actor", "evidence_ref",
  "pixel_rewrite": {"changed": [rewrite groups with runs], "held_cells", "signed_class_delta"},
  "still_total", "still_emitted", "still_omitted",
  "events": [ <event> ],                 # sorted by (track_id, verb)
  "boundary": null | {"kind": "RESET", "life_before", "life_after", "tracks_ended", "tracks_started",
                      "possible_correspondences"},
  "record_status": "VERIFIED" | "UNVERIFIED_AFTER_MISMATCH" }
```

- **A RESET** carries a boundary and no events. Lives are never joined.
- **An unverified record** carries no events, no pixel rewrite and zero still counts.
- **A level entered but never acted in** has `transitions: []`, and its scene is the entry board.

### 4.2 · Event

```text
{ "event_id": "EV-" + sha256(level, transition_id, track_id, verb)[:16],
  "transition_id", "level", "life",
  "subject": {"track_id", "roles": [{"role", "gate_id", "role_ref"}]},  # roles bound at t-1, exact identity only
  "verb", "before": null | snapshot, "after": null | snapshot,
  "delta": {"translation"?, "count"?, "class"?, "entered_sites"?, "departed_sites"?,
            "footprint": {"membership_groups": {...}, "retained_same_value_cells": n}},
  "correspondence": {"source": "SITE"|"CLASS"|"NONE", "witness", "ambiguity", "resumes_at"?, "gap_from"?},
  "flags": {"recolor", "returns_to_prior_state", "reopens_role_typing", "role_binding_ends"},
  "status": "OBSERVED",
  "explanation": {"status", "refs", "basis"} }
```

- **The footprint groups** are the accepted `arithmetic_signature` membership groups, valued at cut `t-1` and cut `t`. `retained_same_value` is stored as a count. A BIRTH has only `later_footprint_only`; a terminal verdict only `prior_footprint_only`.
- **Snapshots** state a sighting as the census segments do: class, anchor, bbox, cell count and shape hash. They carry no cell runs. The changed footprint groups keep their runs, so every changed site is stored exactly. `entered_sites` and `departed_sites` are counts.
- **`changed_sites(event)`** is the set of cells in the groups whose before and after integers differ. The validator checks that every changed site appears in the record's pixel rewrite with the same rewrite.

### 4.3 · Scene (from the last verified board)

```text
{ "as_of_transition": last verified id | null (entry board), "as_of_node", "life",
  "record_mismatch": null | first_mismatch,       # prominent: the scene says it stopped early
  "present":  [{track_id, class, anchor, bbox, cell_count, roles: [bound roles] | "UNRESOLVED_OBJECT"}],
  "departed": [{track_id, last_seen_node, end_reason: DEPARTED | LIFE_ENDED}],
  "unverified_tracks": [track_id],                 # first seen after the verified prefix
  "verb_counts": {verb: n},
  "unexplained": [event_id],                       # non-STILL UNEXPLAINED events
  "open_identity": [{role, gate_id, subject}] }    # certified roles whose identity is UNRESOLVED
```

- **Partition.** `present`, `departed` and `unverified_tracks` cover every track exactly once.
- **References resolve.** Every `unexplained` id names an event of a verified record. Every `open_identity` row names an `IDENTITY_UNRESOLVED` gap.

## 5 · Explanations: recomputed from the certified tier and its receipts

`explain(event, record, receipts, bindings)` is deterministic. The compiler and the validator call the same function, and the validator refuses any stored explanation that differs from the recomputed one.

| Status | Exactly when | Refs |
|---|---|---|
| `EXPLAINED` (G2) | <ul><li>A certified COUNTER role cites a product whose receipt carries a `mask`.</li><li>The record has a non-empty `evidence_ref`, and that receipt resolves to **this** transition (revision 1).</li><li>The event's changed sites are non-empty and all lie in the mask.</li><li>**Every** changed group's rewrite equals the mask's `from → to`.</li></ul>No inverse rewrites, refills, triggers or quantities. Without the transition's own evidence, the event stays `UNEXPLAINED`. | Exactly that product id and that evidence ref |
| `PARTLY_EXPLAINED` (G3) | <ul><li>A witness receipt is recorded at this transition.</li><li>A certified LEVER role cites that witness.</li><li>The changed sites are non-empty and lie within that witness's local and remote residue.</li></ul> | Each such witness id |
| `PARTLY_EXPLAINED` (G1) | The event is a **MOVE** of the EGO role's exact track, with its binding still active at `t-1`. G1's law covers displacement, so a recolor or growth of the ego stays `UNEXPLAINED`. | The G1 product id |
| `UNEXPLAINED` | Everything else, including every STILL. | `[]` |

The rows are checked in that order.

**Unresolved identities are never guessed (ruling 6).** On k008 the EGO identity is unresolved, so its moves stay `UNEXPLAINED`, and `open_identity` names the gap. This slice adds no current-life join.

## 6 · Verified prefix (amendment 4)

`first_mismatch` is the earliest of three:
- a contradicted before-value (the census's own discontinuity);
- a duplicated id;
- a missing id, meaning a gap in the level's contiguous ids.

From that transition on:
- records are `UNVERIFIED_AFTER_MISMATCH`, with no events;
- `presence` is clipped to the verified nodes;
- `resumes_at` beyond the prefix is withheld;
- class changes beyond it do not end bindings;
- the scene is taken at the last verified node.

The level gains a `RECORD_MISMATCH` gap (source `description_prefix`) and is never `ACCOUNTED`.

**At H2**, `_apply_check` truncates at the level's earliest mismatched id when that is earlier still (reason `JOURNAL_CHECK`). It withdraws from the events any role that H2 withdraws, then recomputes explanations and the scene.

## 7 · Class change (ruling 4)

On the first verified `RECOLOR` of a track bound to a certified role:
- the role stays in `certified.roles` (history) and gains `binding_ends_at`;
- the event at that transition still carries the role, with `flags.role_binding_ends`;
- later events, the scene and explanations do not carry the role;
- the level gains a `CLASS_CHANGED` gap naming the role subject, the track and the transition.

The validator checks the end against a verified RECOLOR event on that track, and checks the gap.

## 8 · Schema (ruling 5)

- `seal` stamps v3.
- `validate` applies the v2 rules, then the v3 additions: a description on every level and the enriched receipts.
- `validate_v2` is the accepted v2 rule set, unchanged.
- `read_world_model` dispatches by schema: v1 to its own reader, v2 to `validate_v2`, v3 to `validate`.

**Test edits.** `tests/test_wo_l2a_census_paths.py:68` reads v3.

**A finding against v1 §9 Q5.** v1 said only that one assertion pins v2. It is not the only test touched: `tests/test_world_model_v2.py::_model()` hand-builds a minimal model and seals it, so under v3 it needs a minimal valid description. Every assertion stays. The fixture gains the chapter its schema now requires, and the shared-file note names this edit.

## 9 · Validator rules (each is a test)

1. **Coverage:** one record per distinct recorded id, ascending; unverified records hold no events.
2. **Verbs and status:** verbs are among the nine. Status is `OBSERVED`; anything else is refused with "causal…". No `causal` key is allowed.
3. **Event ids:** each id is unique and equals its hash, and each event sits under exactly one record whose id is its own.
4. **Subjects and roles:** every subject is a known track. Its `roles` equal the roles bound to that track at `t-1`.
5. **Still arithmetic:** `still_total == still_emitted + still_omitted`, and `still_emitted` equals the number of STILL events.
6. **Explanations:** each one equals `explain(...)`. Refs must resolve, and `UNEXPLAINED` has none. Changed sites must lie in the record's pixel rewrite.
7. **Scene:** the partition and reference resolution of §4.3 hold, and `present` equals the presence at `as_of_node`.
8. **Bindings and gaps:** binding ends and their `CLASS_CHANGED` gaps are consistent. A mismatch carries a `RECORD_MISMATCH` gap.
9. **Receipts:** witness hashes match, and mask runs agree with their counts.

## 10 · Out of scope

- WO-DESC-B (pages, digest, `world_report.md`).
- G4 dossiers and causal sentences.
- G5/G6, Band 1 and INERT.
- SPLIT and MERGE.
- A current-life EGO join.
- Push, SUB-4, PLAY-NORMAL wording and win transfer.

## 11 · As built: refinements made during the build

| Point | As built | Why |
|---|---|---|
| G1 scope | `PARTLY_EXPLAINED` only for a MOVE of the bound ego track. | G1's law is a displacement law. The fail-first assertion that the ego's recolor is `PARTLY_EXPLAINED` was narrowed to `UNEXPLAINED`. |
| `basis` | A rule code: `G2_MASK_LAW`, `G3_WITNESS_RESIDUE`, `G1_EGO_MOVE`, `NO_CHANGE` (a STILL) or `NOT_COVERED`. | Recomputed and compared by the validator. A code per event is small; their meanings are in `explain`'s docstring. |
| Snapshots | No cell runs (see §4.2). | They roughly halve the chapter on k013. The changed groups still carry every changed site. |
| Footprints | `descriptive_events.footprint` reads each cut's values once per transition. | It calls `_rewrite_groups`, the accepted primitive. `arithmetic_signature` rebuilt both cuts' values on every call. A regression test pins equality with `arithmetic_signature`'s membership groups on every paired event. |
| Two further test-fixture edits | <ul><li>`tests/test_world_model_v2.py::_model()` gains the minimal v3 description and witness residue. Its pointer-ego edit swaps in the matching description.</li><li>`tests/test_library_view.py::_large` makes its fabricated frozen levels transition-free (`_light`). A level copied 40 times with 400 shared transition ids would otherwise carry 40 ledgers.</li></ul> | Every assertion stays. These are fixture builders that v3 must satisfy. |

## 12 · Revision 1 (Sol's review: two contract gaps)

1. **The first transition comes from the entry board.**
   - `library_census.entry_board_node(entry)` gives node 0 for `INITIAL_FRAME` and `after_transition` for `LEVEL_ENTRY`. `_windows` cuts the entry board at that node; previously it used the first recorded id minus one.
   - `first_mismatch(rows, discontinuities, entry_node)` now also reports:
     - a leading gap (the first recorded id is past `entry_node + 1`), as `MISSING_TRANSITION` at `entry_node + 1`;
     - an id at or before the entry, as `BEFORE_ENTRY`.
   - A later gap keeps its behavior. With a leading gap nothing is verified, and the scene stays at the entry board.
   - The validator refuses a verified prefix that does not run contiguously from `entry_node + 1`. `world_model_v2` refuses a `basis.entry_node` that disagrees with the level's own entry.
   - At one id, the record faults rank in this order: duplicate, missing, before-entry, contradicted.
2. **G2 needs the transition's own evidence.** See §5. The refs are exactly `[product, evidence]`. A product-only claim is refused because it differs from the recomputed explanation.
3. **For DESC-B (not changed here).** The ledger is exhaustive at the substrate. It describes semantic objects and also the complementary grid regions around them:
   - a counter shrink also appears as growth of the rewritten region beside it;
   - large terrain regions produce DEFORM bridges whenever something moves through them.

   That raw accounting is kept in DESC-A. DESC-B must render it as a concise semantic presentation, so that Duck does not read complementary pixel regions as separate mechanisms.

## 13 · Revision 2 (Sol's review: the entry board under `BEFORE_ENTRY`)

**The entry board is always trusted.** `verified_node(node, entry_node, limit)` admits:
- the entry node itself;
- every later node before the first mismatch.

`_presence`, the compiler, H2's `restrict_description` and the validator all use it. So when a row numbered at or before the entry is the first mismatch, the scene is still exactly the entry board, and the entry tracks are present.

**`_windows` gives such a row no cut.** Its changes are still replayed onto the board, so later before-value checks are unchanged. But a row numbered *at* the entry no longer overwrites the entry sighting's source. Previously the entry tracks' first sighting was relabelled as that transition. A row numbered *below* the entry no longer creates a backwards cut. Valid records never contain such a row, so their projection is unchanged.
