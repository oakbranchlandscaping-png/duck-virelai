# INTERFACE — WO-G4-DOSSIER-B · v1 · 2026-10-18 (read-only; stop for Sol's rulings)

- **Seat:** Alpha (Ring 9).
- **Base:** `87639d7` on `ring9-unified`, as the Director reported it. I could not read the hash myself: the worktree's git directory lies outside the mounted folder. What I verified: the device tree matches every file in the WO-G4-DOSSIER-A revision-3 slice checksum list.
- **Mode:** read-only. Nothing was edited, and no shared-file note is filed yet.
- **Governing documents:** `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v5` §3 Stage 2, and `EXECUTION_PLAN_SEMANTIC_LIBRARY_v5` §1, §3, §4 and §9.
- **Game-free:** record names appear only as fixture labels.

## 1 · Two descriptions of DOSSIER-B: a plan-level question first

The Director's handoff and the locked plan describe DOSSIER-B differently. They overlap but are not the same work.

| Source | DOSSIER-B is |
|---|---|
| Director, 2026-10-18 | "adding the missing experiments for persistence, reversal, and current orbit phase" |
| Locked plan, Stage 2 | **library-selected study**. The earliest incomplete actionable dossier chapter becomes the selected question, in the order anatomy → orbit → limits → relations → law. Gate obligations stay first. Duck may choose another eligible subject only through the gate's admission contract. A decline or timeout consumes no experiment and returns to controller coverage. |

The plan's exit evidence for Stage 2:

- the card, digest, capability, probe, route, execution, receipt and updated dossier all name the same subject and question;
- a no-choice golden;
- controller fallback;
- completing one lever never closes another lever's dossier.

So the plan's DOSSIER-B is selection and routing machinery. The three owed fields are a subset: they are the open items of the limits and orbit chapters that the selection would target. The read below (§2) also finds that on the committed record **none of the three needs a new experiment to be stated for the cases observed**; all three are derivable from data the machine already records. That changes what "adding experiments" would mean. **Ruling Q1.**

## 2 · The three owed fields: prior art and availability

Revision 1 classified all three as `PROBE_OWED`. Read again against the committed code, each is **`DERIVABLE` from the level's record within a stated scope**. An experiment is owed only where the record holds no evidence for that scope.

The prior art is committed and pure:

- **`level_record`** (R9-R24, D18/D19). `level_boards` rebuilds every board of the level from `transition_index`. `region_histories` gives each lever region's distinct contents in first-seen order (S0, S1, …). `presses` gives each recorded press with its acting lever, the lever regions it changed, `elsewhere`, and the masked before/after addresses.
- **`g4_relations.LeverRegion.state_label`**. This is what G4-B's and G4-C's cards already show as `state_now`.
- **`g4_limits.py`**. This is the retired G4.3 study, kept as port source (`virelai_gates.py:2168`: G4.3 was retired by Director ruling on 2026-09-27; persistence and reversal became Duck-frozen G4-B predictions).

**Read-only probe** (`probe_derivable.py`, ft09 G4-B closed by Duck's description, 59 recorded presses):

- `level_boards`, `region_histories` and `presses` left the machine byte-identical (pickled before and after).
- Every lever reads `state_now` S1, with 2 states seen.
- Every lever held its state across all 50–52 presses of other levers; none was moved by another lever.
- Each lever has 7–9 effective presses of its own, which return its region to an earlier content (S1 → S0 → S1).

| Field | Proposed class | How it is stated | Experiment owed only when |
|---|---|---|---|
| `ORBIT_PHASE_NOW` | `DERIVABLE` as of the census transition | The lever region's `state_label` against its own region history, mapped to the run's step sequence. It is not durable: it is stamped `as_of_transition`. | Never. `UNRECORDED` (content never seen) is reported as such. |
| `LIMITS_PERSISTENCE` | `DERIVABLE`, scoped | Counts of presses of other levers (and other recorded actions) that left the lever's region unchanged, versus those that changed it, with their evidence refs. Scope: *within the level, across the recorded interventions*; never "over time" and never across a life. | The record holds no press of anything else after the endpoint. The test would be a single press of another lever: a G4-B prediction with `expected[A] = UNCHANGED` already expresses it. |
| `LIMITS_REVERSAL` | `DERIVABLE` when observed | **Self-reversal:** the lever's own press returned its region to an earlier content (any confirmed cycle or toggle). **Cross-reversal:** another press did. Both cite the press. | Observed for neither: a saturating lever whose region never returned. The test needs an expectation G4-B cannot yet express ("returns to S0"). This is the only field where an experiment may truly be owed. |

Three cautions:

1. `presses` reaches the G3 entity ledger through `_ensure_entity_ledger()`. It changed nothing here because the ledger already existed, but the dossier's no-side-effect guard means the dossier must read the ledger attribute instead. The fix is a dossier-side read, with no gate edit.
2. Region states are per-lever cell contents. Orbit `state_sequence`s are masked whole-world addresses. The two are different readings and are reported as such, never equated.
3. Cross-level limits stay `UNAVAILABLE` (G9).

## 3 · Library-selected study: what exists and what is missing

**Exists today (`library_agenda.py`):**

- one question per gate;
- per-lever G3 questions with an admitted Duck choice (`g3_selection.select`, with a bounded handoff, staleness rules and coverage resume);
- per-lever G4 chapter questions (EFFECTS, ORBIT, RELATIONS, LAW), which are **listed but never selectable**.

In every G4 gate, `_selected` returns the gate's level question.

**Duck's existing per-lever entry points in G4:**

- G4-A's `virelai('rerun', id=E, presses=N)`, up to 8 activations, controller-executed (D3);
- G4-B predictions, Duck-frozen and controller-executed, within Duck's per-level budget (D20/D21);
- G4-C's law test.

The **controller orders** G4.1 and G4-A by `_ordered_entities` (`virelai_gates.py:5606`, `5905`).

**Missing for the plan's Stage 2:**

| Requirement | Today | Change implied |
|---|---|---|
| Earliest incomplete actionable chapter selected, per lever, in the order anatomy → orbit → limits → relations → law | Gate-level selection only | `library_agenda` reads the dossier chapter statuses (or the same gate state) and selects per lever |
| Duck chooses only through the gate's admission contract | G3 only | A G4 admission point per chapter: G4.1's next anatomy, G4-A's next run or a rerun, a limits test, a G4-B prediction |
| Decline or timeout consumes nothing; the controller resumes coverage | G3 only | The same in G4 |
| Card, digest, capability, probe, route, execution, receipt and dossier name one subject and question | The digest names the gate question | A `question_id` threaded through the G4 capability and receipt |
| No-choice golden | The G3 golden (`test_replay_checkpoints` case 8) | A G4 golden: with no choice made, the ladder is byte-identical to today's |

**Where the order collides with the ratchet:** limits sits before relations in the plan, but its only experiment home since 2026-09-27 is G4-B. The G4 admission points live in `virelai_gates.py`, which is far above the Green file band. Any G4 admission edit there must extract first (the ratchet), or live beside it in a module the way `g3_selection` does.

## 4 · Proposed slicing, for ruling

- **B1 · derived limits and phase.** Dossier-only: `lever_dossier_facts`, `lever_dossiers`, the schema validator and renderers. No gate, agenda or controller edit. Persistence and reversal (where observed) and phase-now become scoped derived facts with evidence refs. `PROBE_OWED` remains only where the record holds no case. Fail-first on `87639d7`; T0 plus the T1 `description` and `paper-evidence` sets.
- **B2 · library-selected study** (the plan's Stage 2 proper). The agenda's per-lever selection, the G4 admission points, the subject/question thread, controller fallback and a no-choice golden. Gate and selection edits mean a shared-file note, T1 `g3-directed`, and a golden.
- **B3, only if B1 leaves cases owed** (for example a saturating lever never reversed). The experiment: a G4-B prediction extended with a state-label expectation, or a ported `g4_limits` study. This is a gate edit and is ruled separately.

## 5 · Open questions for Sol and the Director

1. **Scope.** Is DOSSIER-B the plan's library-selected study (Stage 2) with the three fields inside it, or the three fields alone? I propose B1 then B2.
2. **Definitions.** Accept persistence as "held across recorded interventions within the level, counted and cited". Accept reversal as "self or cross, observed", with no claim beyond the record. Accept phase-now as a per-lever region state label stamped as of the census transition.
3. **Owed experiments.** Where B1 finds no case, does the remaining experiment belong to G4-B (an extended expectation vocabulary) or to a ported `g4_limits` study? The 2026-09-27 retirement ruling points to G4-B.
4. **Selection order versus gate order.** The plan orders limits before relations, but limits tests run inside G4-B. Should selection follow the plan's chapter order, or the gate ladder?
5. **The ratchet for B2.** Should the G4 admission points live in a new module beside the adapters (the `g3_selection` pattern), with only call lines in `virelai_gates.py`?

**Ground-truth request to the Director** (read-only), so the next build can record its base from the repo itself:

```
git -C ~/Desktop/virelai-review/duck-virelai-r9r20 --no-optional-locks log --oneline -1
```
