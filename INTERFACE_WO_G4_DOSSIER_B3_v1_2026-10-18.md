# INTERFACE — WO-G4-DOSSIER-B, slice B3 (bounded limits experiments) · v1 · 2026-10-18

- **Seat:** Alpha (Ring 9). **Base:** `ef8289d` on `ring9-unified` ("Complete library-directed G4 lever selection").
- **Mode:** Phase 1, read-only design. It was written before any production edit; the build follows it (§9).
- **Game-free:** record names (ft09, E00xx) appear only as fixture labels.

## 0 · Phase 0: the base

| Check | Result |
|---|---|
| HEAD | `ef8289d`, branch `ring9-unified` (read on the device) |
| Tracked tree | clean (0 changed tracked files) |
| Sandbox tree vs `ef8289d` | identical: the commit's variant diff applied to the `0119a74` snapshot equals the sandbox tree, file for file |
| B1 on the committed fixtures | `b1_*` tests: 7 passed |
| B2 on the committed fixtures | `test_g4_selection`, `test_g4_selection_persisted`, `test_g4b_relations`: 46 passed |
| ft09 life-2 owed set | `{E0053, E0054, E0055}`: `LIMITS_REVERSAL` owed, persistence observed. At G4-B's opening (record replayed to G4-A's close) each has 0 self-presses in life 2; after Duck's eight predictions each has exactly one (`test_b1_10`). |
| No-choice ladder at G4-B's opening | life 1, nothing owed for any of the eight levers (probed) |

## 1 · The map

| Question | Finding |
|---|---|
| Can a G4-B admission and receipt carry an experiment? | **Yes.** G4-B already admits controller-executed, single-action probes (frozen predictions): `next_probe` → envelope → `record_outcome` → evidence id → transition row. An experiment step is the same thing with its own envelope. It uses no prediction, so it never enters G4-B's prediction ledger, coverage or product. |
| Retired G4.3 (`g4_limits.py`) | Two parts are worth porting: the **continuity check** (each step's before-board must be the last observed after-board; else the experiment is contradicted) and **"a terminal boundary interrupts, never grades"**. The rest is not ported: it needs an accepted orbit, reads whole-world masked addresses where B1 reads region content, and its runtime was retired. It does not become an authority. |
| Probe, transition and audit records | Unchanged. The step is an ordinary G4-B probe and transition. Its probe id carries the experiment's identity. The choice and its close are the existing G4 selection events (`ADMITTED` / `FINISHED` / `STALE` / `REFUSED`), in the existing audit translation (operation `G4_SELECTION`, gate `G4-B-LEVER-RELATIONS`). |
| World-model schema | **No bump.** No stored shape changes: the observations, audit rows and receipt index are v8 as they are. The outcome is recomputed from receipts and observations, never stored. |
| New Duck turn | **None.** Duck chooses only on a turn it already holds (§4). |
| Lifecycle transition table | Untouched (no G3 lifecycle state is added). |

## 2 · Architecture

- **New module `inference/framework/lever_experiments.py`, beside `g4_selection.py`.**
  - The pure planner: what is owed and what G4-B can serve.
  - The experiment state, its envelope and its step evaluation.
  - Its admission and close events.
- **G4-B (`g4b_gate.py`): delegation lines only.**
  - `next_probe` serves the active experiment.
  - `record_outcome` hands it its own steps.
  - `_freeze` refuses a prediction while an experiment is under way.
  - `_emit_product` closes an active experiment when the gate closes.
  - `compact_gate_view` shows the experiment block.
- **Controller (`controller_executor._relations_step`).** Before the record certifies the relations, the head of coverage is admitted and taken.
- **Selection (`g4_selection.select`).** A `…:LIMITS` question goes to `lever_experiments.select`. `virelai_gates.py` is not edited.
- **Agenda (`library_agenda`).**
  - The lever's existing limits question becomes actionable in G4-B while an experiment is eligible or active.
  - It stays `OPEN_NOT_ACTIONABLE` elsewhere, as B2 ruled.
- **Dossier (`lever_dossiers.attach`, `lever_dossier_state.derive`).** Missing or duplicated execution evidence fails only the subject's observations closed (`RECORD_MISMATCH`).
- **Validator (`lever_dossier_selection`).** It extends the v8 selection chain to G4-B experiments.
- **Persistence tiers (`life_record`).** It declares G4-B's two new attributes: the active experiment (TRANSIENT) and the level's closed experiments (LEVEL).

## 3 · The experiment contract

| Field | Value |
|---|---|
| `experiment_id` | `G4-B-LEVER-RELATIONS:EXP:{KIND}:{E}:L{level}P{life}:R{n}`. Here `n` is the admission ordinal among the game's G4 admissions, B2's numbering. Step `k`'s probe id appends `:{k}`. |
| level, life | as admitted; the experiment never outlives either |
| lever | `entity_id` (the subject) |
| chapter, open item | `limits`; `LIMITS_REVERSAL` or `LIMITS_PERSISTENCE` |
| question id | the lever's limits question, `Q:L{level}:LIBRARY:{E}:LIMITS`, exactly the agenda's existing row. Derived, never stored in a dossier: `dossier_question(level, E, "limits")`. |
| kind | `SELF_REVERSAL` (`REVERSAL` in the probe id) or `PERSISTENCE_TRIAL` (`PERSISTENCE`) |
| starting observed state | the subject's region state label and content hash in this level and life (B1's reading) |
| admissible action | `SELF_REVERSAL`: the subject's own click. `PERSISTENCE_TRIAL`: the click of the first other lever in coverage order. Only plain, currently available click actions are servable; NAV levers are not (§8). |
| maximum steps | `SELF_REVERSAL` 8 (the existing extra-run bound, `MAX_RERUN_PRESSES`); `PERSISTENCE_TRIAL` 1 |
| success condition | **Reversal:** the press returns the region to a state seen earlier in this level and life. A two-state return is `REVERSAL_OBSERVED`; a longer cycle is `RECURRENCE_OBSERVED`, which is not reversal. **Persistence:** the other lever's press leaves the region `UNCHANGED`, or `CHANGED`. |
| inconclusive condition | **Reversal:** the cap is reached with no return (`CAPPED`; reversal stays owed). **Persistence:** the trial's press cannot be attributed (`PERSISTENCE_INCONCLUSIVE`). |
| interruption | **Typed `STALE`:** `INTERRUPTED_DEATH`, `INTERRUPTED_LEVEL_CHANGE`, `STALE_SUBJECT` (the lever left the board), `CONTRADICTION` (a step's before-board is not the last observed state), `GATE_CHANGED` (G4-B closed) |
| receipts so far | each step's `k`, probe id, evidence id and transition, and the subject's state after it |

Current region state gets no experiment: B1 derives it from the board, with its transition stamp (unchanged).

## 4 · Scheduling and selection

**Eligible.** At G4-B, an experiment is eligible when all of these hold:

- the gate is open, no frozen prediction is pending and no experiment is under way;
- the life has an entry (a death not yet followed by its reset admits nothing);
- the lever's B1 observations are `OBSERVED` in this level and life, and its earliest owed limits item, in dossier order (persistence, then reversal), has no experiment closed in this level and life;
- the action is servable.

The plan is B1's own `observe` and `derive`, computed only at an admission point. It is never computed on a step of an experiment under way.

**Order of G4-B's next step:**

1. A pending frozen prediction, or the experiment under way: the controller takes it (in-progress work first).
2. The head of coverage: the first eligible experiment, levers in G4-B's order. The controller admits it (`ADMITTED`, actor `CONTROLLER`) and takes its first step.
3. The record certifies the relations: the controller answers (R9-R24 D19, unchanged).
4. Otherwise Duck.

**Duck's choice.** On any turn Duck already holds while G4-B is the current gate and an experiment is eligible, Duck may call `virelai('next_probe', question_id=Q)`. One such turn: the last G4-A explanation, whose acceptance opens G4-B within the same turn. `select` admits the choice (`ADMITTED`, actor `DUCK`); the controller then executes it. It refuses, recorded once, when:

- the gate is not G4-B;
- a prediction is pending;
- an experiment is under way: the choice cannot replace it;
- the question names no eligible experiment.

**Decline or timeout.** No call is made, so nothing is admitted. The next step is exactly the no-choice step (2).

**Close.** `FINISHED` (typed success or `CAPPED`), or `STALE` (typed interruption). The reason text begins with the type. The closed experiment is not re-admitted in that level and life; a new life plans afresh, inheriting no step count and no receipt.

## 5 · Evidence and fail-closed rules

- **The dossier is still derived by B1 from the record.** An experiment's steps are ordinary transitions, so a return is a B1 toggle or recurrence case citing the experiment's receipt, and a trial is a B1 persistence trial. Nothing is inferred from the experiment's own verdict.
- **Missing or duplicated execution evidence fails only the subject's observations closed (`RECORD_MISMATCH`).** Examples: a step with no receipt, a gap or repeat in `k`, or a G4-B step event with no transition. The lever's witness and its other chapters are kept.
- **Scope.** Life and level boundaries come from B1's scope: no evidence joins across them, and a harness reset is never a reversal.
- **The v8 validator, with hashes recomputed, refuses:**
  - a G4-B admission whose question is not the derived limits question;
  - an unheld level, or a lever with no dossier;
  - a receipt whose experiment was never admitted, or that names another lever, level or life;
  - steps that are not `1..m` exactly once, or beyond the cap;
  - a `FINISHED` reversal whose outcome disagrees with its receipts (a return cited at any step but the last, or no return and fewer than cap steps);
  - a `FINISHED` persistence trial its observations do not count;
  - a `STALE` close without a typed reason.

## 6 · Performance and size

- Only steps 2 and 4 of §4 compute the plan: once per experiment boundary, and on Duck's card.
- Measured at G4-B's opening:

  | Operation | Time |
  |---|---|
  | The plan (`observe` + `derive`, eight levers) | 11 ms |
  | `record_answer`, which the controller's G4-B step already calls each time | 113 ms |
  | `gate_view` | 11 ms |
  | The agenda | 0.5 ms |

- An experiment's own step reads one region from the outcome's grids.
- No census and no dossier compile is on the controller path.

## 7 · Shared files

`g4b_gate.py`, `controller_executor.py`, `g4_selection.py`, `library_agenda.py`, `lever_dossiers.py`, `lever_dossier_state.py`, `lever_dossier_selection.py`, `life_record.py`, `tests/test_g4b_relations.py`, and the tier manifest and snapshot. The shared-file note is filed before the first edit.

## 8 · Rulings requested (none blocks the build)

1. **A v8 artifact with G4-B selection rows is refused by `ef8289d`'s validator** ("is not G4-A's"). Under B2's rule (bump only when a stored row shape changes) this is not a bump, since no shape changes. If Sol reads "an older v8 reader refuses it" as a schema change, B3 needs v9.
2. **The committed assertion `test_g4b_opens_after_g4a_on_the_real_ft09_levers_and_asks_for_a_prediction` changes.** It expects the controller's first G4-B step, in the life-2 state, to be the record's relations answer. Under B3 rule 5 the controller first runs the owed experiment (E0053's self-reversal), then answers. The assertion is replaced by the B3 behaviour, followed by the record's answer. Nothing is weakened. This is the only committed behaviour that changes, and only where something is owed.
3. **In the controller-first ladder, Duck rarely holds a G4-B turn.** Its one routine turn with eligible experiments is the last G4-A explanation, which opens G4-B. B3 adds no turn, so on most levels coverage decides.
4. **NAV levers get no experiment.** Their owed items stay visibly owed.
