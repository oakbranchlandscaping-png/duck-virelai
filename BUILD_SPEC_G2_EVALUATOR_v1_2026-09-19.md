# Build spec: receipt-bound G2 counter-checkpoint evaluator

Date: 2026-09-19
Source family: `variants/ring9-cybernetic-gates`
Phase: A, item 2 (collaborator integration §11)
Status: built and locally verified in the active Ring 9 source; live use awaits downloadable output
from the queued G0–G2 notebook version 2. The original version 1 failed before the benchmark and
contains no gate behavior to grade.

## Local question

Given a downloaded Ring 9 G0–G2 run, decide per world whether G2 counter behavior was correct —
`PASS`, `FAIL`, `REPRESENTATION_GAP`, `BUDGET_EXHAUSTED`, or `NOT_REACHED` — from the executed
artifacts alone, with a receipt-bound human frame review as the only path to semantic PASS.

## Evidence the tool binds to (all per-world `artifacts/{stem}_*.jsonl`)

- `gate_answers.jsonl` — the G2 answer row as `tool_agent.py` writes it: the `CounterAnswer`
  fields plus `gate_status_after_answer`, `counter_candidate`, `pending_prediction`.
- `gate_events.jsonl` — per-probe events carrying `evidence_id`, `gate_status_after`, and when
  present `counter_candidate`, `counter_comparison`, `mask_law`, `counter_boundary`.
- `probe_envelopes.jsonl` — G2 probes with purpose `PROBE` / `DEMONSTRATE` / `CONFIRM_BOUNDARY`.
- `probe_outcomes.jsonl` — lossless outcomes with `site_transitions` (total site ledger),
  `changed_cells`, `acted_site`, `boundary_event`, `evidence_id`.
- `probe_frames.jsonl` — raw frame rows per evidence id.
- `execution_receipt.json` — schema `virelai-g2-execution-receipt-v1`; every review binds to its
  SHA-256.
- `human_review.json` — schema `virelai-g2-human-review-v1` (defined by this tool).

**Finding surfaced, not patched:** the locked `CounterModel` product and the
`virelai-masked-state-archive-v1` snapshot are never persisted to run artifacts — they exist only
in the in-memory gate view. The evaluator therefore recomputes every mask/state claim from the
lossless outcomes and does not require a product row. A future slice should persist the product
payload at lock; until then this is recorded here as an open friction.

## Grade groups (automated) and the checks each holds

1. **protocol** — G1 closed before G2 (an accepted G1 answer with an `INTERFACE_AXIOM` or
   `OBSERVED` ego law); unique G2 probe ids; exact probe↔event and probe↔outcome joins; opaque
   action ids only; frames present for every G2 evidence id.
2. **discovery** — recomputed, never trusted from the candidate row: ≥2 witnesses with ≥2 distinct
   intervention keys; the candidate rewrite occurs on every witness with exactly the recorded
   amount, each matching cell `source -> replacement`; no acted site inside the support or
   footprint; support ⊆ footprint; on every fully-covered witness the footprint holds only the two
   counter integers; conservation — source count falls by the amount the replacement count rises,
   recomputed from the site ledger.
3. **explanation** — required `CounterAnswer` fields present at word minimums; competing model and
   falsifier present; `evidence_refs` exactly the candidate witnesses; answer explains the active
   candidate.
4. **prediction** — prospective prediction persisted with the answer; expected rewrite is the
   candidate rewrite; declared strictly before the comparison transition; comparison `SUPPORTED`
   with the expected amount; the demonstration probe purpose is `DEMONSTRATE`; the confirming
   action is counter-only — changed cells ⊆ mask, acted site outside it (failure class 12).
5. **boundary_lock** — boundary comparison `SUPPORTED` with a legal kind; extremum recomputed from
   the site ledger (`source == 0`, `replacement == footprint size` for the game-over kind); the
   boundary probe purpose is `CONFIRM_BOUNDARY`; final G2 status `CLOSED`; mask law present,
   rewrite-matched, demonstration-bound.
6. **mask_and_state** — recomputed over every fully-covered G2 outcome: raw delta partitions
   exactly into HUD and world cells; counter-only transitions leave the masked view identical
   (shared world address) while outside-mask change makes it differ; every in-mask change is the
   counter exchange or its respawn reversal (nothing causal hides in the mask); the mask contains
   both integer classes at some observed frame (failure class 11 — one-sided masks minted false
   states).
7. **correctness** — human, never inferable from schema: review bound to the exact receipt
   SHA-256, one row per game, all verdicts true, every cited witness plus the demonstration and
   boundary evidence explicitly reviewed.

## Dispositions

`NOT_REACHED` — no G2 artifacts (prerequisite never closed; a later gate is never graded FAIL for
that). `BUDGET_EXHAUSTED` — G2 opened but ended `UNRESOLVED` or mid-status when the run ended.
`REPRESENTATION_GAP` — an `INDETERMINATE` comparison, or witnesses lacking the total site ledger
where a full-footprint claim requires it. `PASS` — every automated group passes and the
receipt-bound human review passes. `FAIL` — otherwise, with the failing checks named.

Report `passed` is strict: receipt PASS and every expected world PASS. Evidence-backed non-PASS
dispositions are reported per world for the Phase A.5 decision; the tool never loosens the gate.

## Verification of this slice

`tests/test_g2_checkpoint_evaluation.py` builds its fixtures by driving the real
`CyberneticGateMachine` through G0→G1→G2 and writing rows exactly as `tool_agent.py` writes them
(failure class 7: fixtures must not be richer than production). Planted defects: a one-sided mask
(class 11), a non-counter-only confirmation action (class 12), a prediction journaled after its
comparison, a review bound to the wrong receipt, a world with no G2 artifacts, and an
extrema-without-consequence run. Focused tests pass, then the full Ring 9 suite must stay green.

## Claim limit

Automated grades establish protocol, recomputed arithmetic, prospectivity, and mask/state
invariants over executed artifacts. They do not establish that Duck understood anything: only the
receipt-bound human frame review can grade semantic correctness, and this tool refuses to mark a
world PASS without it.
