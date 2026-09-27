# Review: G4 Phase-1 drain (S1) Kaggle checkpoint, notebook version 1

**Reviewed:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed
**Executed artifact:** `runs/kaggle-ring9-g4-phase1-drain-v1/output/` (downloaded from notebook
`stephenkaskin/taaf-virelai-ring9-g4-phase1-drain-v1`, version 1)
**Package:** `ring9-g4-phase1-drain-v1` (`777dc39`), source `f8a967e`
**World / model:** `vc33-5430563c`, `vrfai/Qwen3.6-27B-FP8` via local vLLM
**Graded against:** `G4_PHASE1_DRAIN_KAGGLE_RUNBOOK_2026-09-27.md` (criteria frozen in
`checkpoint-preflight.json` before launch)

## Verdict

**S1's return edge works live; the run then deadlocked on a case S1 does not handle.**
G3 closed on Kaggle's exact model for the first time. G4.2 drained E0004 to a fixed point, then
held in G4.2 and moved to E0005 exactly as designed. E0005's sixth press completed the level, the
orbit was correctly marked interrupted, and from then on the S1 hold kept the machine in a G4.2
that had no admissible action and refused every answer. That consumed about 90 of the 120 minutes.

| Item | Grade |
|---|---|
| Infrastructure | **PASS** |
| Precondition (G3 closes with ≥ 2 levers; G4.1 for each) | **MET** |
| C1 — every lever drains to a period and a class | **PARTIAL**: E0004 yes; E0005 interrupted by a level boundary |
| C2 — final `LeverOrbitSet` has nothing pending | **NOT REACHED** (E0005 legitimately interrupted) |
| C3 — no prior orbit or class invalidated | **PASS** on available evidence |
| C4 — hold in G4.2 for the next lever; G4.3 only after pending is empty | **PASS** for the hold; the "then G4.3 opens" half **UNTESTED** |
| New defect — S1 hold has no exit for a boundary-interrupted lever | **FOUND** (lifecycle class) |

## Integrity and infrastructure (direct observation)

- The downloaded `execution_receipt.json` is byte-identical to the frozen package receipt. The run
  is attributable to this package.
- Kernel log: `source manifest verified (197 files)`; `CUDA GPU check passed for rtx-pro-6000 x1`
  (NVIDIA RTX PRO 6000 Blackwell Server Edition); vLLM ready at ~564 s; `checkpoint worlds verified`;
  `G0-G4 execution receipt verified` at 588 s.
- Deadline respected: the benchmark ran 2 h 0 m 42 s and ended `cancelled` at the behavior deadline.
- No tracebacks, no `GateContractError`, no G4.3 guard message, no circuit-breaker trip. Qwen
  emitted a parsed tool call in every one of 235 responses.

## Timeline (kernel-log progress lines, seconds since notebook start)

| Time | Actions |
|---|---|
| 588 | 0 (benchmark start) |
| 1,188 | 9 |
| 1,789 | 15 |
| 2,389 | 25 |
| 2,389 → 7,830 | 25 (no further action) |

All 25 actions — G0 through the E0005 boundary — happened within about 30 minutes of play (roughly
70 s per action, consistent with the budget model). The last 90 minutes produced no action.

## Gate-by-gate (direct observation, `*_gate_answers.jsonl` and `*_gate_events.jsonl`)

- **G0, G1** answered. **G2** closed after three probes.
- **G3** — twelve probes; accepted dossiers for M0004/E0004 and M0009/E0005 (remote erasure of a
  ~264-cell strip per click, counter cells masked), then an accepted `LEVER_INVENTORY`: two levers,
  eight scoped nulls. **First G3 closure on `Qwen3.6-27B-FP8` on Kaggle** (the G3-v3 run looped on
  the counter object). G4.1 opening confirms the inventory product was active.
- **G4.1** — accepted anatomies for E0004 and E0005.
- **G4.2, E0004** (events 16–19): masked changes of 265, 266, 249 cells, then a press changing one
  cell (the counter) → `NULL_AT_OBSERVED_STATE`, recurrence index 3. Accepted orbit answer
  `G4O-105d8a59d6056934`. `_lever_class` on that answer gives **ABSORBING**.
- **G4.2, E0005** (events 20–25): five novel masked states (250, 265, 265, 265, 266 cells), then the
  sixth press changed **2,771** cells: a level transition. Disposition `BOUNDARY_INTERRUPTED`; no
  period, no class. The orbit was not falsely completed.
- **Level 1 cleared** on that sixth E0005 press (score 0.28, levels 1/7). Recorded as an observed
  terminal transition; explaining it is G8 work, outside this checkpoint.

## The S1 signature (C4)

After E0004's orbit answer was accepted, the router would have advanced to G4.3 under the old code.
Instead the next six gate events are G4.2 activations of E0005, and no `G4.3-LEVER-LIMITS` event
occurs anywhere in the run. That is the return edge (`_effective_target_id`) working live. The half
of C4 that says "G4.3 opens once nothing is pending" was never exercised, because E0005 never
stopped being pending.

C3: E0004 has exactly one accepted G4.2 answer, nothing re-opened it, and the logs show no product
invalidation. The target journal is still not persisted to artifacts, so this is graded from answers
and events, not from the product history.

## The new defect: S1 hold deadlocks on a boundary-interrupted lever

After the level change (transcript from ~2.02 M characters to the end):

- The G4.2 card served to Duck showed `status: SATISFIED`, `next_operation: BOUNDARY_INTERRUPTED`,
  `current_entity_id: E0005`, and advertised `"repeated confirmed lever activation"` as an admissible
  probe kind.
- Every activation attempt was refused: `"G4.2 has no admissible activation in its current state"`
  (239 occurrences).
- Every attempt to close the orbit was refused: `"a boundary-interrupted orbit is unresolved and
  cannot be closed by prose"` (384 occurrences).
- Because E0005 stayed in `pending_lever_entities`, `_effective_target_id` kept returning G4.2, and
  the G4.3 guard would have refused anyway. No legal move existed.
- Duck behaved well — 65 turns and 138 tool calls exploring cards, physics, carry and orbit queries —
  but the controller offered it nothing to do.

Triage (protocol §10): **lifecycle**. The first broken layer is that S1 treats a lever whose orbit
was interrupted by a level boundary as "pending", when it can no longer be studied on this level.
The contradictory card (SATISFIED, a non-operation as `next_operation`, an advertised but refused
probe) is a secondary delivery defect.

This is not an edge case for vc33: pressing E0005 repeatedly *is* what completes level 1, so a
faithful Phase-1 orbit of that lever cannot reach a period without crossing the boundary.

## What this run does not establish

- G4.3 opening after a full drain (never reached).
- Any class for E0005.
- Phase 2, couplings, or any explanation of the win.
- Newborn objects: 37 new segmentation ids appeared during the orbits (E0023–E0059). They were
  recorded, not queued (S1 does not append newborns), and segmentation churn on a transforming board
  does not by itself show new objects.

## Decision needed (architectural — Director's ruling)

What should Phase 1 do when a lever's orbit ends in a level transition? Three candidate rulings:

1. **Terminal disposition.** Treat a boundary reached by the orbit itself as a Phase-1 terminus
   (for example class `LEVEL_TERMINAL`): record it, remove the lever from pending, release the hold.
   This fits "classify from the lever's own orbit" and "the win is observed": the orbit *observed*
   the transition.
2. **Interrupted, not pending.** Record the lever as `PHASE1_INTERRUPTED` (neither classified nor
   pending), release the hold, and define Phase-1-complete as "every lever classified or explicitly
   interrupted".
3. **Clean stop.** On a level transition during G4, close the level's G4 study with the interrupted
   lever recorded and end gated work cleanly, leaving level re-entry to G9 per the 2026-09-26 scope
   ruling.

Any of the three removes the deadlock. The card must also stop reporting `SATISFIED` with no legal
operation. Whichever is chosen, the fix is small and testable offline against this run's frozen
events.

— Claude, Alpha build seat, 2026-09-27
