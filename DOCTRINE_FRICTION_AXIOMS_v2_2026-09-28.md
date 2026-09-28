# Doctrine: friction axioms

**Type:** `DOCTRINE_FRICTION_AXIOMS` · **v2** · **2026-09-28** (supersedes v1 of 2026-09-27)
**Author:** Claude (Alpha build seat), signed. Recorded from Director rulings of 2026-09-27 and 2026-09-28.
**What changed since v1:**
- A1 is sharpened: the label must agree with the whole record.
- A5 records the ranked-list ruling.
- A6 is new: the card is bounded.

All three come from the ft09 guided Kaggle run (`REVIEW_G4_FT09_GUIDED_KAGGLE_V1_2026-09-28.md`).
**Status:** Director-ruled. It binds every gate on the Cybernetic Duck (Ring 9) line. The highest
version wins; amend it by adding a version, never by editing this one.
**Game-free by construction.** No world's name, colour, position or mechanic appears in an axiom.
Worlds appear only in the friction record, as the evidence that produced each axiom.

## The rule that produces this document

> "Every friction should help us define an axiom in a more absolute term." (Director, 2026-09-27)

Every friction answers one question before any code changes: **which axiom does it sharpen, or
does it need a new one?** An axiom is absolute when it holds for every world. The test is simple:
**an axiom may not name a form**. For example, "the counter can be poked in isolation" names a form
that a counter might or might not take. A closure test that presupposes a form will fail on the
first world that lacks it.

A second rule travels with this one:

> "A stated target is the goal when possible." (Director, 2026-09-27)

Each gate gives Duck a direct, explicit target and a closure test, and then lets Duck execute it
as needed. The controller owns the question, the evidence rules, coverage, recording, grading,
reopening and boundaries. Duck owns every action, its order, the hypotheses, the explanations and
the predictions. Scripted gates are exceptions, and the Director names them: G3 is scripted.

## The axioms

### A1 · Counters: find, label, mask, prove purity

**Axiom.** A counter is any visible process whose changes track bookkeeping (actions, effective
moves, time, lives) rather than the state of the world. Counters come in many forms. The target is
always the same: **find it, label its law, and mask it, so lever data stays pure.**

**Closure test, true for every form:**
- **Find:** a footprint whose changes follow one rewrite law across varied actions.
- **Label:** the law. That means footprint, rewrite and rate; what triggers a tick (every action,
  only effective actions, time); and the limit, if one is observed.
- **Mask, with purity checked both ways on the whole record:**
  1. every change inside the footprint follows the counter law (or its inverse, a refill), so the
     mask never swallows lever data;
  2. at least one witness acted away from the footprint, so the rewrite is not the footprint's own
     response to being targeted.
- **Prediction:** one frozen prediction, scoped to the footprint, on an action Duck chooses, is
  supported. `COUNTER_REWRITE` means exactly *n* footprint cells rewrite. `COUNTER_SILENT` means the
  footprint holds. Changes elsewhere are recorded and not held against it.
- **No counter:** if none appears, the gate closes as "not observed" after full coverage. It never
  claims global absence.
- **The label agrees with the whole record (v2).** The label states the trigger as a structured
  field:
  - `EVERY_TRANSITION`;
  - `EFFECTIVE_TRANSITIONS_ONLY`: it ticks only when something outside the footprint changes;
  - `IRREGULAR`.

  The controller computes the trigger class from the record, and the claim must match it. When
  the record cannot yet tell the two simple classes apart (`OPEN`), either claim is admissible,
  and a `COUNTER_SILENT` prediction on an action expected to change nothing would separate them.
  The record's own class is always admissible, so this check can never deadlock (A2).

**Friction record.** ft09 Kaggle v1, 2026-09-27. The bar ticked only on effective clicks, so every
witness also changed a control. The old closure demanded a "counter-only" action, found none, and
deadlocked. See `REVIEW_G4_FT09_PHASE1_KAGGLE_V1_2026-09-27.md`.

**Friction record, v2.** ft09 guided Kaggle v1, 2026-09-28. G2 closed live with a pure mask.
Duck labelled the bar a count of every action "regardless of which grid cell is clicked", while
the record held 54 clicks that changed nothing and did not tick it. The prediction, made on a
control click, could not separate the two readings, so the wrong label passed.

**Built:**
- `BUILD_SLICE_G2_COUNTER_AXIOM_AND_LEGAL_MOVE_GUARD_2026-09-27.md` (R9-R03);
- the label check, in `BUILD_SLICE_G3_BOUNDED_CARD_AND_COUNTER_TRIGGER_2026-09-28.md` (R9-R04).

### A2 · Every gate state admits a legal move or declares an end

**Axiom.** In every reachable gate state, Duck has at least one of these:
- an admissible action;
- an answer to give, with a template;
- a declared state that asks nothing of it.

A controller failure is itself a recorded state. It is never silence until the deadline.

**Closure test:**
- The machine reports `legal_move_status()`.
- An answer demanded with no template is illegal. So is a probe demanded with none offered.
- After consecutive illegal checks, the runtime ends gated work as a recorded controller failure
  (`controller_no_legal_move`).

**Friction record.** Three runs idled to their deadline:
- ls20 G2 (2026-09-22): new actions were blocked pending an explanation, while the explanation was
  rejected because no unused intervention was exposed for its prediction.
- vc33 G4.2 (Kaggle, 2026-09-27): about 90 minutes on an interrupted lever held as pending.
- ft09 G2 (Kaggle, 2026-09-27): about 2.5 hours with the answer template missing.

**Open, not yet an axiom breach:** a *declared* end, such as a level closed mid-study, still idles
until the deadline. A clean planned stop is harness work, and it must not be recorded as a crash.

### A3 · A level boundary ends the level's study

**Axiom.** A level change closes that level's study. Everything that crosses levels belongs to the
cross-level gate (G9). An experiment cut off by a boundary is recorded as interrupted, never as
complete.

**Friction record.** vc33 Kaggle, 2026-09-27: the second lever's run completed level 1. The
Director ruled that cross-level work is a separate gate. This was built in `8cfb782` and carried
into guided G4-A.

### A4 · Continuity: test a state while the world is in it

**Axiom.** A claim about a state (an end point, a recurrence, a limit) is tested while the world is
in that state. No evidence may depend on a stored state that the world has since left.

**Friction record.** `FINDING_G4_3_CONTINUITY_AFTER_PHASE1_DRAIN_2026-09-27.md`. After the Phase-1
drain, G4.3 expected each lever's stored end point. The world had moved, and presses were rejected
as discontinuous. **Built:** confirmation now happens inside each G4-A run
(`BUILD_SLICE_G4A_GUIDED_LEVER_STUDY_2026-09-27.md`).

### A5 · Guidance: state the target, audit the record

**Axiom.** Where a target can be stated, the controller states it and its closure test, and Duck
chooses every move. The controller audits the record against the test. It accepts, or it names
exactly what is unmet. It never selects Duck's next move.

**Ruling, 2026-09-28: the ranked list stays.** "The ranked list ensures an exhaustive search with
no thought needed." Coverage is the controller's to guarantee. An ordered roster on the card is a
coverage duty, not a plotted move. Where a gate's job includes exhaustive coverage (the G2 search,
the G3 sweep), the card may hand Duck the ranked list. Duck still chooses how to meet the target
beyond coverage: its predictions, and its answers. Observed live: Duck worked down the list in
order (ft09 guided v1).

**Friction record.** The G4 plan of 2026-09-27 (v1) scripted every Phase-2 move. The Director
ruled: "we are guiding the agent, not plotting every move". Then: "G3 is scripted and G4 becomes
stated targets"; then: "a stated target is the goal when possible". Built for G4-A and for G2 in
CLICK worlds.

### A6 · The card is bounded regardless of world size

**Axiom.** What Duck is shown each turn has a bound that does not grow with the world: counts, the
current target, a small window, and paged query handles. Detail is queried, never pushed. Nothing
is discarded: the lossless record stays in the snapshot and the artifacts.

**Closure test.** On the largest recorded world, every gate card in every reachable state fits
the runtime budget (24,000 characters). The test replays real records wherever possible.

**Friction record.** ft09 guided Kaggle v1, 2026-09-28. G3's card was 67,939 characters, because
it listed all 64 roster rows, the whole entity ledger and the lifecycle journal. The runtime's size
guard ended the game. vc33, with a smaller roster, had fit. **Built:** R9-R04. The ft09 G3 entry
card is now about 10,000 characters, and the full 64-object sweep peaks at about 13,500.

## How to add an axiom

1. Name the friction with its evidence: run, artifact path, direct observation.
2. Ask whether it sharpens an existing axiom. If it does, add a version of this document that
   restates that axiom and cites the new friction.
3. Write the axiom so that it names no form. Then write its closure test on the record.
4. Build the test before the fix, from the real run where possible. Replays of real segments are
   the preferred regression (see `tests/fixtures/`).

— Claude, Alpha build seat, 2026-09-27
