# Doctrine: friction axioms

**Type:** `DOCTRINE_FRICTION_AXIOMS` · **v3** · **2026-09-28, evening** (supersedes v2 and v1)
**Author:** Claude (Alpha build seat), signed. Recorded from Director rulings of 2026-09-27 and 2026-09-28.
**What changed since v2** (from `REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md` and the ratification of
`DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md`, rulings D1–D7, all "yes"):
- A5 is revised. The controller executes every move it can compute; Duck is woken where judgment
  is needed. Stated targets remain for judgment.
- A6 is sharpened (v2): the card is bounded regardless of world size **and of how much has been
  found**.
- The memory laws M1–M10 are ratified as doctrine (new section).
- The proposed A7, "an object has one worldline", is still awaiting a ruling. It was not among D1–D7.
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
reopening and boundaries. Scripted gates are exceptions, and the Director names them: G3 is scripted.

**Revised 2026-09-28 (evening):** "The controller should execute scripted moves when possible,
which in theory should get us to gate 3 without needing the Duck." Every move the controller can
compute is executed by the controller, one action per frame. That covers coverage sweeps,
confirmations, mechanical predictions and runs to a lever's endpoint. Duck is woken for
hypotheses, explanations, non-mechanical predictions, and choices between experiments that are not
equivalent. See A5 below and memory law M8.

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

**Revision, 2026-09-28 (evening; rulings D2, D3):** *what the controller can compute, the
controller executes.*
- G0–G3 run without Duck: the G0 and G1 answers are derived from metadata; the G2 search, its
  frozen prediction and its structured label are the controller's; G3's sweep, confirmations and
  structured dossiers are the controller's; G3 inherits G2's total nulls (D5).
- In G4-A the controller runs each lever to its endpoint, and Duck explains the confirmed orbit.
- Duck's first turn is the **orientation turn** at G3 close, where it reads the certified world
  model.
- Stated targets remain the form for judgment: G4-B relations and predictions, G4-C mechanics.

This supersedes the 09-27 application of this axiom to G2 in CLICK worlds and to G4-A. The
evidence behind it:
- In v1 and v2 Duck followed the ranked list exactly, the prediction included.
- G3 cost 64 full model turns (about 37 minutes) with no decisions.
- On the assumed Kaggle budget, wall time is the binding limit (DESIGN_VIRELAI_MEMORY_v1 §2).

**Friction record.** The G4 plan of 2026-09-27 (v1) scripted every Phase-2 move. The Director
ruled: "we are guiding the agent, not plotting every move". Then: "G3 is scripted and G4 becomes
stated targets"; then: "a stated target is the goal when possible". Built for G4-A and for G2 in
CLICK worlds.

### A6 · The card is bounded regardless of world size and of how much has been found (v2)

**Axiom.** What Duck is shown each turn has a bound that grows neither with the world nor with the
findings. The card carries the current work. The record carries everything. Recall connects them.
The card is **built** from named slots with budgets, never copied from state and trimmed, so a
field without a slot cannot reach Duck. Nothing is discarded: the lossless record stays in the
record tier and the artifacts.

**Closure test** (DESIGN_VIRELAI_MEMORY_v1 §10, T1 and T3):
- Stress worlds with 2, 8 and 20 findings pass through every gate. The largest card fits the slot
  budget, and `size(20) − size(2) ≤ 1,000` characters.
- Adding an unslotted field to any gate's state leaves the card byte-identical.
- Real records are replayed wherever they exist.

**Friction record (v2).** ft09 guided Kaggle v2, 2026-09-28:
- G3 witnessed and confirmed five levers. Its card grew about 3,200 characters per lever, because
  the confirmation records and dossiers of every earlier lever were pushed onto it.
- At the fifth dossier it reached 25,502 characters, and the guard ended the run. This is
  reproduced exactly by replaying the real record (`tests/fixtures/ft09_kaggle_v2_record.json.gz`,
  R9-R06).
- It was the fourth overflow in a row, and each had been fixed by trimming one field. The pattern
  was the construction, not the field.

**Friction record.** ft09 guided Kaggle v1, 2026-09-28. G3's card was 67,939 characters, because
it listed all 64 roster rows, the whole entity ledger and the lifecycle journal. The runtime's size
guard ended the game. vc33, with a smaller roster, had fit. **Built:** R9-R04. The ft09 G3 entry
card is now about 10,000 characters, and the full 64-object sweep peaks at about 13,500.

## The memory laws (ratified 2026-09-28, ruling D1)

The full statement, architecture and tests are in `DESIGN_VIRELAI_MEMORY_v1_2026-09-28.md` §4. They
are doctrine with the same force as the axioms above.

| Law | Statement |
|---|---|
| **M1** | The record is complete, lossless, append-only, and written only by the controller. |
| **M2** | Only knowledge a gate has certified enters the world model. A contradiction reopens it. Nulls and refutations stay in the record and can be recalled. |
| **M3** | The card is built from named slots with budgets, never trimmed from state. |
| **M4** | The card's size depends on neither world size nor findings (A6 v2). |
| **M5** | The present is never hidden: everything the current decision needs is on the card, and only history moves behind recall. |
| **M6** | Recall is injected by the controller first and pulled by Duck second. Both are tested for delivery. |
| **M7** | Compaction is deterministic projection. No model summaries anywhere in memory; the same state renders the same bytes. |
| **M8** | Duck spends turns only where judgment is needed. The controller executes computable moves, one frame in, one action out. |
| **M9** | The world model is scoped to the level and persists across lives (D4). Carrying it across levels is a hypothesis until re-confirmed (G9). |
| **M10** | Every turn is measured: card sections, tokens, wall time, who acted, recall. |

**The other rulings of the same date:**
- D4: a lever study continues across a death on the same level.
- D5: G3 inherits G2's total nulls as scoped nulls in the recorded state.
- D6: Duck's own annotations live in a separate UNCERTIFIED lane and are never promoted without a
  gate.
- D7: parallel throughput is measured on Kaggle before per-game budgets are set.

## How to add an axiom

1. Name the friction with its evidence: run, artifact path, direct observation.
2. Ask whether it sharpens an existing axiom. If it does, add a version of this document that
   restates that axiom and cites the new friction.
3. Write the axiom so that it names no form. Then write its closure test on the record.
4. Build the test before the fix, from the real run where possible. Replays of real segments are
   the preferred regression (see `tests/fixtures/`).

— Claude, Alpha build seat, 2026-09-27; v3 2026-09-28
