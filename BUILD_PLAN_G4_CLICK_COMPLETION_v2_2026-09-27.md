# Build plan: G4 CLICK branch as stated targets

**Type:** `BUILD_PLAN_G4_CLICK_COMPLETION` · **v2** · **2026-09-27** (supersedes v1 of the same day)
**Author:** Claude (Alpha build seat), signed

**Rulings (Director, 2026-09-27):**
- NAV is shelved; G4 work is CLICK only.
- Cross-level work is G9.
- **"A direct and explicit target for the Duck, then allow the Duck to execute it as needed."**
- **G3 stays scripted; G4 becomes stated targets.**

## 1 · The principle

The controller owns:
- the question;
- the closure test;
- the evidence rules (counter mask, executed frames only, predictions declared before the action);
- coverage (Duck may not skip a lever);
- recording, attribution, grading, reopening, and level boundaries.

Duck owns:
- every action, and its order;
- hypotheses;
- explanations;
- predictions.

The controller never selects Duck's next move. It checks the record against the target, then either
accepts or names exactly what is unmet.

Every G4 card has four parts:
- **target:** one plain sentence;
- **done when:** the closure test applied to the record;
- **rules:** the evidence rules;
- **progress:** computed from the record.

Duck acts through a `GUIDED_ACTION` capability. That capability admits any one valid action, with
an optional free-text `intent`.

## 2 · Where we sit

```
G3 (scripted) ─► G4.0 bind ─► G4.1 anatomy ─► G4-A levers alone ─► G4-B levers together ─► G4-C explain + predict ─► G4 EXIT
    LIVE           LIVE          LIVE         BUILT (offline) ◄── HERE      SPEC                    SPEC
```

- **G4-A is built offline** in this session: `g4_guided.py`, the guided adapter, and 10 new tests.
- **Suite:** 384 passed, 1 skipped (cloud); Mac confirmation owed.
- **Scripted baseline:** the ft09 Kaggle run in flight is the scripted version of G4-A. Guided G4-A on the same world is the comparison run.

## 3 · The three G4 targets

### G4-A: each lever alone (built)

**Target:** for every lever, press its click repeatedly until the counter-masked board stops
changing or returns to an earlier state, then confirm that endpoint. Confirmation is one more null
press, or one more full cycle that retraces the recorded states. Explain each lever.

**Done when:** every lever has a CONFIRMED (or DIVERGED) run read from Duck's own consecutive
presses, plus an accepted explanation.

**How the record is audited:**
- A press counts only if it uses the lever's exact listed click.
- Any other action, a reset or a boundary ends an open run. The ended run stays on the record.
- A boundary releases the lever it cut off.
- A level change closes the level's study; G9 owns cross-level work.

### G4-B: levers together (next)

**Target:** find how the levers affect each other. Before each test, declare what you expect to see.

**Done when:**
- every lever appears in at least one graded prediction;
- every claimed relation rests on a supported prediction;
- contradicted predictions stay on the record;
- two outcomes that disagree are recorded as a missing condition.

**Absorbs:** persistence, reversal, conditions (old G4.4) and couplings (old G4.5).

**Needs:**
- a `predict` tool that freezes a prediction before the action;
- grading against the masked frames;
- the prediction ledger.

The G4.3 study code in `g4_limits.py` is the port source for grading reversal and persistence.

### G4-C: exit

**Target:** explain the lever mechanics of this level in plain language, then make one new
prediction.

**Done when:** that prediction is supported. The product is a `LeverReactionLaw` set. If the
prediction is contradicted, G4-B reopens.

## 4 · What was removed from v1, and why

- **G4.3-LEVER-LIMITS is retired from the ladder.** Its endpoint confirmation now happens inside
  each G4-A run. This removes the continuity defect
  (`FINDING_G4_3_CONTINUITY_AFTER_PHASE1_DRAIN_2026-09-27`): the defect's mixed-lever cases now
  complete in either order. The regression test is in `tests/test_g4_guided.py`.
- **Removed as controller-plotted work:** the scripted Phase-2 sequence generator (v1 P5), and
  step-based classification as a scheduling input (v1 P3).
- **Merged into G4-B:** separate G4.4 and G4.5 builds.

## 5 · Order of work

1. **Read the ft09 scripted run.** Grade its preregistered criteria. It is the baseline.
2. **Mac pytest, then commit G4-A.**
3. **Package guided G4-A for ft09.** Same world, model and budget as the scripted run. Criteria
   are preregistered before launch:
   - G4-A closes;
   - actions spent;
   - time to closure;
   - explanation quality;
   - no deadlock.
4. **Build G4-B offline:** `predict`, grading, the ledger, and the closure test.
5. **One Kaggle run through G4-B.**
6. **Build G4-C and run the G4 exit.**

Infrastructure fitted between steps:
- persist the target journal to artifacts, before G4-B grading;
- clean stop after a level closes, before any vc33 run;
- retry backoff.

## 6 · Decisions still owed

- **G4 CLICK exit definition.** Proposed: supported `LeverReactionLaw` sets on both ft09 and vc33.
- **Newborn objects in guided mode.** A newborn is surfaced on the card, and Duck decides whether
  to study it. Should unstudied newborns block G4-A closure?

## 7 · Honest ledger

- Guided G4-A has never run with a live model. We have not yet measured how well Duck chooses its
  own presses in gated mode.
- If G2 closes without a mask on ft09 (the ticker risk), no run can reach a null or a recurrence.
  That holds in guided and scripted mode alike.
- The vc33 Kaggle segment replayed through G4-A matches the recorded addresses. That run never
  confirmed E0004, so under the guided rules E0004 is unconfirmed. The replay records this rather
  than hiding it.
- CLICK-only: NAV is shelved, not solved.

— Claude, Alpha build seat, 2026-09-27
