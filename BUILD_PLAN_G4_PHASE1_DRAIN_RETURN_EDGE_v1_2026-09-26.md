# Build plan: G4 Phase-1 drain and the pending-lever return edge

**Type:** `BUILD_PLAN_G4_PHASE1_DRAIN_RETURN_EDGE` · **v1** · **2026-09-26**
**Governs:** `DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`. **Active source:**
`variants/ring9-cybernetic-gates/ARC3-Inference/`. Anchored at commit 1bf09e0 (373 offline
tests green, Director-run). Re-verify every citation at the implementing anchor.

## The problem, exactly

G4.2 (`_LeverOrbitTarget`) already seeds **both** levers from the G4.1 anatomies and
`_current_entity()` returns the first unanswered — so E0005 is queued the whole time. The only
thing stranding it is the router: `TargetRouter.current` (`cybernetic_targeting.py:176`) skips
any gate holding an active product, so the moment G4.2 emits `LeverOrbitSet` for E0004
(`virelai_gates.py:4137`) the router steps to G4.3 and never returns to G4.2 for E0005. The queue
exists; nothing drives it.

The generic router and journal must stay gate-agnostic (their own contract). The drive lives in
the machine as a **descent controller** over `_active_adapter`/`gate_id`
(`virelai_gates.py:4708`), leaving G0–G4.1 routing untouched.

## The design (Phase-1 drain)

```
                 G3 inventory (roster)                      [built]
                          |
                          v
        +----------------- DESCENT CONTROLLER ----------------+
        |  dynamic lever queue: [E0004, E0005, ...(newborns)] |
        |  current lever = first not-yet-classified           |
        +-----------------------------------------------------+
                          |
            (per current lever, Phase 1 only)
                          v
      G4.2 orbit: consecutive same-lever presses  --> period, null/recurrence   [built]
                          |
                          v
      classify: typing.classify_effect_channel(orbit steps) --> class            [new, small]
                          |
              classified? --yes--> mark lever done; advance current lever
                          |                         |
                          | newborn appeared -------+--> append to queue
                          v
        queue drained (every lever period+class, nothing pending)
                          |
                          v
              emit PHASE-1-COMPLETE signal  ------------------> gates Phase 2
                                                               (G4.3 re-homed,
                                                                couplings, mechanics)
```

The controller's rule: **active gate = the shallowest Phase-1 step the current lever has not
completed.** For E0004: orbit not done -> G4.2(E0004); orbit+class done -> advance. Current
lever advances to E0005 -> G4.2(E0005). When no lever remains un-classified and the queue is
empty, emit PHASE-1-COMPLETE. Products **accumulate** (G4.2 `submit_answer` already builds from
all answered levers); the controller never invalidates a prior lever's belief.

## The slices

**S1 — Phase-1 drain (the return edge). THIS SLICE.**
- Descent controller in the machine: owns the dynamic lever queue and current-lever pointer;
  overrides gate selection for the G4.2+ region only.
- Classification step: run `classify_effect_channel` on each completed orbit's step sequence;
  store the class on the per-lever orbit record. A lever is Phase-1-done at period + class.
- Newborn append: an entity id first seen during an orbit step (already journaled in the orbit
  event's `new_visual_entity_ids`) enters the queue as a Phase-1 obligation. Full G3-reopen for
  newborns is S4; S1 wires the append hook and the queue growth.
- PHASE-1-COMPLETE signal: emitted when the queue holds no un-classified lever.
- **G4.3 re-home:** move `_LeverLimitTarget`'s open-condition behind the PHASE-1-COMPLETE
  signal. Its tested endpoint/persistence/reversal code is preserved; it simply cannot fire
  until every lever is classified — enforcing "AAAA, BBBB, then ABA." No rewrite.

**S2 — Phase-2 sequence engine (later).** The ABA/ABC generator over classified levers; drives
the re-homed G4.3 (reversal, persistence) as its first consumers.

**S3 — Couplings and world mechanics (later).** G4.5 coupling detection and the G4.6
connected-resource synthesis, reading the finished per-lever dossiers.

**S4 — New-object full reopen (later).** The born-object -> G3 -> G4.1 path that feeds the
queue with a fully classified-from-scratch newborn, not just an appended id.

## Exit criteria for S1 (graded from artifact state, not prose)

1. Two confirmed levers drain fully through Phase 1: each reaches period + class; the queue
   empties; PHASE-1-COMPLETE emits.
2. `LeverOrbitSet` ends with **both** levers in `lever_entities`, `pending_lever_entities`
   empty — accumulated, never replaced.
3. No invalidation of a prior lever's orbit/class anywhere in the trace (planted-defect test).
4. G4.3 does not open before PHASE-1-COMPLETE (planted-defect test: attempt to enter G4.3 with a
   lever still unclassified is refused).
5. A newborn id observed mid-orbit appears in the queue as a Phase-1 obligation.
6. The existing entity-local and routing tests stay green (373+).

## Tests owed with S1 (production-shaped)

Full two-lever Phase-1 drain to PHASE-1-COMPLETE; accumulation without invalidation; classify
runs on real orbit steps and lands a class; G4.3 open gated on the signal; newborn append grows
the queue; the discontinuity/entity-local suite unchanged.

## Discipline

Diagnostic-before-fix (this plan is the audit). Test-before-fix (regression tests fail before
S1 lands). Canary-before-closure: S1 touches the decision substrate (gate selection), so a
bounded vc33 OpenRouter run is its live closure — Director-run, graded against these exit
criteria, no live run against a red suite. Ground truth is the committed state.

*Read-only plan; no code changed. S1 is the next build.*
