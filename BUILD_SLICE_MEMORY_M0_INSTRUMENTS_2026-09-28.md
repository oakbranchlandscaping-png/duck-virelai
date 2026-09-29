# Build slice R9-R06: memory stage M-0, the instruments

**Revision label:** `R9-R06`
**Date:** 2026-09-28
**Author:** Claude (Alpha build seat), signed
**Governing design:** `DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md` (RATIFIED 2026-09-28), stage M-0: §5.1
(record tier), §5.5 (shared recording path), §7 (turn ledger), §10 (T2, and T9 in part).
**Base:** `4329185` (R9-R05). Active source: `variants/ring9-cybernetic-gates/ARC3-Inference/`.

**What M-0 is.** The instruments every later memory stage is measured with.

- **It changes nothing Duck sees or does.** The card, the gates and the decisions are unchanged.
  The full suite passes unchanged apart from the new tests.
- **It adds** a replay harness over real records, a record-tier index, a read-only memory store, a
  per-turn ledger, and one shared recording path for gate actions, which the controller executor
  (M-2) will reuse.

## What was built

| File | What |
|---|---|
| `inference/framework/gate_card.py` (new) | The binding-card renderer, moved out of `ToolAgent` (`_binding_gate_payload`, `_gate_context_update` now delegate). Production, the replay harness and the tests measure the same bytes. |
| `inference/framework/record_replay.py` (new) | **The replay harness.** It drives the production gate machine through a recorded world (initial grid, sparse per-transition changes, and the Duck-written part of each accepted answer). Controller-derived fields are re-derived, so a record replays under changed code. It measures the binding card after every step. No model is called. |
| `tests/fixtures/ft09_kaggle_v2_record.json.gz` (new, 4.8 KB) | The real ft09 guided-v2 record: 121 transitions, the G2 label and four G3 dossiers, built from the run's artifacts. |
| `tools/record_from_artifacts.py` (new) | Builds such a record from any run's artifacts directory, and `--replay` prints the largest card per gate. Next time a run crashes, it reproduces offline in one command. |
| `virelai_gates.py`, `CyberneticGateMachine` | **The record-tier index.** `transition_index` holds one sparse, lossless row per recorded transition, whichever gate recorded it: action, acted site, changed cells, evidence id, disposition, boundary. The row builder lives in `memory_store.py`. |
| `inference/framework/memory_store.py` (new) | **The read-only memory store.** `products()`; `product(key, field, offset, limit)`, where long fields are described and paged, not inlined; `transitions()`; `transition(id)`; `site(row, col)`, every action aimed at a cell; `subject(entity_id)`, an object's whole file: identity, lifecycle, confirmations, dossier, and every action aimed at it; and `evidence(id)`. Every response is paged and bounded, and the store writes nothing. |
| `inference/agent/turn_ledger.py` (new) and three one-line hooks in `ToolAgent` | **The turn ledger** (M10). One row per Duck turn in `{stem}_turn_ledger.jsonl`. Each row records who acted, the gate before and after, the characters of each card section (prompt body, automatic update, controller focus, gate card) and their sum, each request's prompt and generated tokens as the server reports them, wall seconds, the recall queries Duck issued, and whether an action executed. |
| `ToolAgent._gate_probe_begin` / `_gate_probe_record` (extracted) | The gate-action recording path, extracted from the nested `_handle_action` closure, unchanged. Probe envelopes now carry `executor` (`DUCK` today). |

## Ratchet (non-blank, non-comment lines)

| Function or file | Before | After |
|---|---|---|
| `ToolAgent.analyze` | 455 | 423 |
| `ToolAgent._run_python_tool` | 513 | 457 |
| `tool_agent.py` | 2,947 | 2,909 |
| `CyberneticGateMachine.record_outcome` | 4 | 7 |
| `virelai_gates.py` | 5,822 | 5,826 |

The compensating extractions, all moved unchanged:
- the retry prompt, to `prompts.no_tool_followup_prompt`;
- the scientist-note parser, to the new `inference/agent/scientist_note.py`;
- the renderer, to `gate_card.py`.

`virelai_gates.py` grows by 4 lines of wiring for the record index. I did not make a gratuitous
move to hide those 4 lines. They are declared here.

## Tests (`tests/test_memory_m0.py`, 9 new)

- **The real v2 record replays** through the gate machine:
  - 121 transitions and 5 answers, all accepted as recorded;
  - G2's trigger `EFFECTIVE_TRANSITIONS_ONLY`;
  - five levers witnessed and confirmed at transitions 112–121.
- **Regression anchor (T2).** The card that crashed v2 is reproduced exactly: **25,502** characters
  after transition 121, G3, answer required. This pins today's card as a baseline, not a target.
  Stage M-1 must replace it with a slot-built card within budget, and amends this test when it
  does.
- **The harness measures the production renderer:** `ToolAgent._gate_context_update` equals
  `render_binding_gate_context` byte for byte.
- **The record index** holds every transition exactly once (1–121), sparse and lossless (38 changed
  cells at the first control click).
- **The memory store recalls** the certified products in gate order; the site history at (36,36)
  (transitions 113, 112 in G3 and 55 in G2); and the file of E0053 (G4-READY, 1 confirmation,
  1 dossier, 3 aimed actions).
- **Memory-store responses are bounded.** Every one is under 8,000 characters on the real record,
  and pages cap at 50. The G2 product's 13,475-character `state_identity` field is described, not
  inlined.
- **The memory store is read-only.** The card and the index are byte-identical after every recall.
- **The turn ledger** records the section sizes, the card total, per-request tokens (prompt maximum
  and generated sum), the gates before and after, and the outcome. It never touches the runtime
  state file.
- **Recall queries are counted, and probe envelopes name who acted** (`executor: DUCK`); the index
  sees the executed transition.

`tests/test_bounded_cards.py` now measures with the production renderer instead of a hand-written
copy of it.

**Suite:** 420 passed, 1 skipped (cloud). Ruff is clean on every new and changed file. **Mac
expected: 409** (400 + 9).

## Findings made while building

- **The G2 product already derives the bar's period.** `derived_period_actions: 32`. The controller
  knows the counter allows 32 effective actions. The M-1 world-model digest will show it, and the
  M-2 executor's stop conditions will use it (DESIGN §6: budgets on the card).
- **Pulled results must fit the tool-output budget.** `LOCAL_ANALYZER_TOOL_OUTPUT_TOKENS` is 1,024
  tokens, about 3,000 characters. The store bounds every response at 8,000, which is safe for the
  store but larger than what a pull can deliver whole. Stage M-3 renders pulls to the tool budget
  and adds the delivery test (T4).
- **The first artifact-path pattern could have written into the state file.** Artifact names are
  derived by replacing `_tool_runtime_state.json` in the state file's name. On a state file named
  without that prefix, the replacement does nothing. The ledger now derives its name safely, and a
  test pins that the state file is untouched. The older artifacts use the same pattern and are
  only safe because production names always carry the prefix. That is recorded for M-1.

## Next

M-1 (R9-R07): the `CardBuilder` and slot schema for every gate, the grouped world-model digest,
the worst-case packager preflight; tests T1, T3, T5, T7, T10 and T11, and the amended T2 anchor.

— Claude, Alpha build seat, 2026-09-28
