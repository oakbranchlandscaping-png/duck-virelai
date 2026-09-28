# Build plan: G4 CLICK branch as stated targets

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v3** · **2026-09-27** (supersedes v1 and v2 of the same day)
**Author:** Claude (Alpha build seat), signed
**Governing doctrine:** `DOCTRINE_FRICTION_AXIOMS_v1_2026-09-27.md` (A1–A5) and
`DOCTRINE_TWO_PHASE_LEVER_STUDY_v1`.

**Rulings (Director, 2026-09-27):**
- NAV is shelved.
- Cross-level work is G9.
- Guide the agent, do not plot every move.
- G3 is scripted; G4 becomes stated targets.
- A stated target is the goal when possible.
- Every friction sharpens an axiom.

**What changed since v2:** the ft09 Kaggle run stalled in G2 on a counter that ticks only on
effective clicks. That friction produced axioms A1 (counter purity) and A2 (no legal move). G2
became a stated target in CLICK worlds and the no-legal-move guard was built. Guided G4-A was
committed; the G2 and guard work awaits commit.

## 1 · Where we sit

```
G0 ─► G1 ─► G2 counter ─► G3 levers ─► G4.0/4.1 ─► G4-A levers alone ─► G4-B together ─► G4-C explain+predict ─► EXIT
LIVE  LIVE   STATED TARGET   SCRIPTED     LIVE          STATED TARGET        SPEC              SPEC
             (offline)                                  (offline)
                ▲ next live test: one ft09 Kaggle run through guided G2 → scripted G3 → guided G4-A
```

| Component | Mode | Status |
|---|---|---|
| G0 action surface, G1 ego | scripted | Live-confirmed on ft09, vc33, ls20 |
| G2 counter | **stated target** (CLICK) | Built offline; replays the real ft09 record to closure. Not yet live. |
| G3 lever inventory | scripted (ruling) | Live-confirmed on vc33 (OpenRouter and Kaggle); not yet reached on ft09 |
| G4.0 bind / G4.1 anatomy | answer-only | Live-confirmed on vc33 |
| G4-A levers alone | **stated target** | Built offline (`G4-A` commit). Not yet live. |
| G4-B levers together | stated target | Specified (below) |
| G4-C explain and predict | stated target | Specified (below) |
| Axiom A2 guard | runtime | Built offline |

## 2 · The targets

**G2 (A1).** Find any counter, label its law, and mask it so lever data stays pure. The mask passes
purity on the record, and one frozen footprint-scoped prediction on a Duck-chosen action is
supported. If no counter appears, G2 closes as not-observed after every ranked object has been
clicked.

**G4-A.** For every lever, press its click repeatedly until the counter-masked board stops
changing or returns to an earlier state. Then confirm the endpoint (A4) and explain it. Done when
every lever has a confirmed or diverged run and an accepted explanation. Boundaries release levers;
a level change closes the study (A3).

**G4-B.** Find how the levers affect each other; before each test, declare what you expect.
- **Done when:** every lever appears in at least one graded prediction; every claimed relation
  rests on a supported prediction; contradictions and split outcomes are kept.
- **Needs:** a `predict` tool that freezes a prediction before the action, frame grading, and a
  prediction ledger. `g4_limits.py` is the port source for reversal and persistence grading.

**G4-C.** Explain the level's lever mechanics in plain language, then make one new prediction.
Done when that prediction is supported; the product is `LeverReactionLaw` set; a contradiction
reopens G4-B.

## 3 · Order of work

1. **Now:** Mac pytest, then commit the G2 axiom and legal-move guard slice.
2. **Package `ring9-g4-ft09-guided-v1`.** Base: the committed ft09 package. Same world, model and
   budget (200 actions, 10,800 s). Source: the new commit. Preregistered criteria:
   - G2 closes under A1 with a pure mask, or closes as not-observed after coverage;
   - G3 closes with at least two levers (the precondition for grading G4);
   - G4-A closes, or records its interruptions honestly;
   - no controller idle: any stall ends as `controller_no_legal_move`;
   - reported, not graded as pass/fail: actions and time per gate, and the quality of Duck's choices.
3. **Grade and review.** Every friction goes to the axioms doctrine first.
4. **Build G4-B offline**, then one Kaggle run.
5. **Build G4-C**, then the G4 CLICK exit run.

Infrastructure between steps:
- persist the target journal to run artifacts (before G4-B grading);
- a clean planned stop after a declared end (needed before any vc33 run);
- retry backoff.

## 4 · Decisions owed

- **G4 CLICK exit definition.** Proposed: supported `LeverReactionLaw` sets on both ft09 and vc33.
- **Newborn objects in guided G4-A:** they are surfaced on the card, and Duck decides whether to
  study them. Should an unstudied newborn block closure?
- **Guided G2 budget:** is the world budget enough of a stop, or should the card show a soft
  action estimate?

## 5 · Honest ledger

- No guided gate has run live. We have not measured how Qwen chooses actions under a stated target.
- G3 has never closed on ft09.
- The "effective-move counter" reading of ft09's bar rests on 2 ticks and 54 non-ticks in one
  opening.
- A declared end still idles to the deadline (A2 open item).
- CLICK only: NAV is shelved, not solved.

— Claude, Alpha build seat, 2026-09-27
