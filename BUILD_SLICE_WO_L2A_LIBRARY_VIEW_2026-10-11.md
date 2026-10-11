# Build slice: WO-L2a close-out (live free play, the controlled stop) and the library view Duck reads

**Date:** 2026-10-11
**Author:** Claude (Alpha build seat, click line), signed
**Governs:** Sol's rulings on the three hooks findings and the next directive, relayed by the Director on 2026-10-11. `NOTE_SHARED_FILE_WO_L2A_LIBRARY_VIEW_2026-10-11.md` was filed before any shared edit.
**Base:** `main` = `ring9-unified` = `472aa32`, pushed. Mac floor 683 passed, 1 skipped. Before building, the device's copies of the five touched shared files had the same hashes as the base.

## 0 · The three findings, closed

| Finding | Sol's ruling | What I did | Result |
|---|---|---|---|
| 1. Unrecorded free play | Reproduce through the live gated play path before changing code | Drove one Duck free-play action through the production path: `_HarnessGameSession.play`, a real gated `ToolAgent`, its gate machine and the python-tool `action()` bridge (details below) | **The finding was wrong.** The action is recorded, receipted and accounted. No code change. |
| 2. Gated-only writing | Keep it | Pinned the behaviour with a test | Confirmed |
| 3. Controlled stops | Record them accurately | Built the end reason, with tests | Fixed |

### Finding 1: live free play

**The test.** One Duck free-play action through the production path:
- `_HarnessGameSession.play`;
- a real gated `ToolAgent` and its gate machine;
- `rest_in_play`;
- the python-tool `action()` bridge with the play gate's token.

**What it shows:** the action reaches all four places.
- **The transition index:** it appears as transition 1, with `gate_id` `PLAY-NORMAL` and action ACTION1.
- **The free-play receipt:** a `FREE_PLAY` event is written, carrying the same `evidence_id` as the row.
- **The final census:** recorded = executed = 1, and the check is ok.
- **Accounting:** the level is ACCOUNTED.

**Where my finding came from.** The replay of the carry-v7 development record stops at transition 26, where it has no recorded G0 answer for the second level. The 165 actions in that record are not 165 actions that a live run would leave unrecorded.

**Two follow-ons:**
- Historical records with genuinely missing actions still report `RECORD_MISMATCH` (the hooks tests).
- The row identifies free play by its `gate_id` and links to the `FREE_PLAY` receipt by `evidence_id`. It has no `receipt` field of its own. If Sol wants that field on the row literally, it is a one-line change to the shared recording path (`memory_store.transition_index_row`), which this slice does not touch.

### Finding 2: canonical v2 writing stays in gated mode

Writing was already scoped to gated mode. A test now pins it: in `observe`, `tool` and `controller` modes, the real `play()` leaves an existing `world_model.json` byte-identical.

### Finding 3: `CONTROLLED_STOP`

**The change.**
- When a turn ends the game with a controlled stop, `play` records it at the `break` through `_note_turn_end`.
- `_l2a_persist_reason` then returns `CONTROLLED_STOP`. That comes after CRASH and CANCELLED, and before the budget test.

**A stop that rests the gates is not the run's end.** It returns earlier, through `_rest_after_controlled_stop`. Play resumes, and the run ends `RUN_END`.

The tests cover three sequences:
1. a controlled stop that ends the run;
2. a stop that rests the gates, then free play, then a planned stop;
3. a stop that rests the gates, then free play, then a second controlled stop in `PLAY-NORMAL` that ends the run.

## 1 · The library view Duck reads

**The module:** `inference/framework/library_view.py` (new, mine).

**`live_model(machine)`** compiles the census in memory and seals it, so it passes the v2 validator.
- Its persist reason is the new `LIVE_VIEW`. `write_canonical` refuses that reason: only H1 and H2 write the canonical file.
- Journal checks stay PENDING, so the view never claims ACCOUNTED.
- A cache keyed on what the census reads returns the same sealed model until something changes. The key covers transition rows, level censuses, frozen levels, the gate, level and life, active products, and G3 lifecycle, terrain, bound and discovery counts.
- The gate machine stays byte-identical.

**`library_digest(model)`** is pure and deterministic. **The whole rendered section, header included, fits 2,500 characters however large the library is** (revision 2, below). It holds:
- the **current goal**: the gate in progress and its question, in ruling 22's sharpened wording;
- the gate dispositions;
- **compact certified findings**: EGO mode and identity, the COUNTER mask, LEVERS with their inventory status and joins, scoped nulls (no inertness claim), and terrain as an observation, not a role;
- object counts;
- **typed open gaps**: grouped by reason and question, with a record mismatch first, then the active goal's own questions;
- each level's accounting and journal check status;
- the earlier levels;
- the **retrieval handles**.

**`library_page(model, kind, …)`** serves six kinds: `levels`, `objects`, `object`, `gaps` (filterable by reason and subject), `role` and `evidence`. **Every response is bounded and names its continuation** (revision 2, below). An unknown kind, id, part or level raises an error. Both the digest and the pages validate the model first, so a tampered model is refused.

### Revision 2: bounds enforced (Sol's review, 2026-10-11)

Sol held the Mac run for two faults in the first version:
- its last digest fallback returned without checking the length, and the header was outside the count;
- `levels` and `role` returned every item, and an `object` returned unbounded class events and gaps, so the tool could cut a reply with no way to continue.

**The digest.**
- The budget is measured on the whole rendered section: header plus JSON.
- Six tiers show progressively less: gap kinds, subjects per kind, IDs per findings line, earlier levels (older ones collapse to "+N earlier" with a handle), and handles. Every line is clipped.
- The last form keeps only the goal, the counts and one handle. If even that cannot fit the budget, the function refuses rather than exceed it.

**Every page.**

| Bound | Value |
|---|---|
| Rows | At most 25 |
| A page's own JSON | At most `PAGE_BUDGET` = 3,000 characters. The tool's output limit is `LOCAL_ANALYZER_TOOL_OUTPUT_TOKENS` × 4 = 4,096 characters by default; the reply envelope and the escaping of stdout take the rest. |
| A list inside an entry | Its first 8 entries plus `<key>_total` |
| A string | 240 characters, ending with the number of characters cut |

Over budget, the page first takes fewer rows, then shorter lists. If a single entry still cannot fit, the page returns an explicit error naming the next call; it never returns a cut response.

**Continuations.**
- A truncated page carries `next`: the exact `virelai('library', …)` call for the rest, with its offset and limit.
- `levels` and `role` are now paged.
- An `object` returns a bounded header (counts, plus a gap count and its `gaps` call) and pages one part at a time: `segments`, `class_events` or `possible_correspondence`, each with its own call.
- `gaps` gained a `subject` filter, so an object's or role's gaps are one call away.
- `virelai('library', …)` passes `subject` and `part` through.

**Wiring** (shared, declared):
- `ToolAgent._gate_context_update` appends the digest after the binding card, on Duck's turn only. A census failure becomes a one-line "unavailable this turn", and the card stays binding.
- `gated_memory_query` answers `virelai('library', kind=…)`. Errors come back in the reply, never as a crash.
- The controller path and `build_card` (replay measurement) never compile the census.

**Test amended:** `test_memory_m0`'s pin becomes "the card comes first, byte-identical; the library section follows."

**Cost** (cloud, measured on development records):

| Record | Compile and seal | Cached |
|---|---|---|
| k013, at 50 / 150 / 300 / 400 transitions | 1.2 / 2.2 / 3.6 / 4.7 s | about 0.1 ms |
| k008, at 61 transitions | 0.6 s | — |

This cost falls only on a Duck turn after the record has changed. For comparison, the v2 mean Duck turn was 78 s. The digest measured 2,021–2,137 characters on k013 and k008.

## 2 · Fail-first evidence

| Test | Before the change | After |
|---|---|---|
| `test_a_controlled_stop_that_ends_the_run_is_persisted_as_such` | `'RUN_END' == 'CONTROLLED_STOP'` | Passed |
| `test_a_second_controlled_stop_in_normal_play_ends_the_run` | `'RUN_END' == 'CONTROLLED_STOP'` | Passed |
| `test_duck_reads_the_digest_after_the_card_and_pages_the_library`, with the two wiring files at the base | `ValueError: not enough values to unpack`: there is no library section after the card | Passed |
| The other library-view tests | The module did not exist | Passed |
| Revision 2's ten large-library tests, and the object-page and evidence-page assertions, run against the first version (with its missing constants supplied) | **11 failed, 6 passed.** On the inflated library, the first version gave: a digest section of 50,702 characters (budget 2,500); a `levels` page of 9,129; an `object` page of 237,607; a 25-row `gaps` page of 4,485 (over the tool's limit). | All passed. Revision 2 gives 2,276; 2,470; 1,206; 2,436. |
| The free-play, rest-and-resume and non-gated tests | Passed at the base. They pin behaviour Sol asked to be verified, and their passing at the base is the finding. | Passed |

## 3 · Verification

| Run | Result |
|---|---|
| Cloud, focused: close-out, library view, `memory_m0`, gated bridge, schema, hooks, census paths | **84 passed** (revision 2; it was 74) |
| **Cloud, full** (Python 3.12, 97 files) | **707 passed, 1 skipped**, 0 failed (revision 2; it was 697) |
| **Mac, focused** (Director, 2026-10-11; the main checkout's venv, Python 3.12; the same seven files) | **84 passed**, 14 warnings, in 25.45 s |
| **Mac floor** (Director, 2026-10-11; `tests --ignore=tests/test_physics_grammar_contract.py`) | **707 passed, 1 skipped**, 14 warnings, in 540.97 s (0:09:00) |
| ruff | The new and changed files are clean |

The Mac and cloud counts are equal. Before the run, the eight copied code and test files in the Director's worktree matched the revision-2 delivery hash for hash, and the parked first version was never in the worktree. The 14 warnings are matplotlib's pyparsing deprecations from the venv.

How the count adds up: 707 = 683 + 7 close-out tests + 17 library-view tests.

**The large library.** The test fixture is a deliberately large library:
- it starts from the k013 development record, re-sealed so it still passes the validator;
- 40 levels;
- 300 more gap kinds with 400-character text, and one record-mismatch gap listing 600 IDs;
- 120 terrain labels;
- one object with 500 class events and 300 possible correspondences.

The tests check:
- the whole digest section stays within budget at 2,500, 1,200, 800 and 500 characters, and a budget of 120 is refused;
- every page kind is followed through its literal `next` calls to every row, and each response stays within `PAGE_BUDGET`;
- a 600-ID list comes back clipped, with its total;
- through the real python tool, a page and its `next` come back with no `[truncated` marker, and the per-turn digest fits.

## 4 · Ratchet (non-blank, non-comment lines)

| Function | Before | After |
|---|---|---|
| `_HarnessGameSession.play` | 87 | 88 (one call; still well below the 114 before the hooks slice) |
| `_HarnessGameSession._l2a_persist_reason` | 12 | 14 |
| `gated_memory_query` | 26 | 28 (the logic is in the new `_library_query`, 9) |
| `ToolAgent._gate_context_update` | 11 | 11 |
| New | — | `_note_turn_end` 3, `_library_digest_section` 6; `library_view.py` is a new file of 335 lines, whose largest function is `library_page` at 43 |

## 5 · Not in this slice

- The shared G3 admission design, kept for its own review.
- SUB-4.
- A `receipt` field on transition rows (see finding 1).
- Showing Duck what changed since the last revision. The digest carries a revision hash, but it does not yet show a delta.
- The world/run manifest and the human report renderer.

— Claude, Alpha build seat (click line)
