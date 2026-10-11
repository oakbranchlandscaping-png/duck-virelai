# Interface: the library as the cybernetic target, beginning with directed G3 admission

**Type:** `INTERFACE_WO_G3_DIRECTED_LIBRARY_TARGET` · **v2** · **2026-10-11**. Supersedes v1 (same day), which stays as history.
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `MEMO_TO_CLAUDE_LIBRARY_TARGETING_HARMONIZATION_v1_2026-10-11`, as amended by the Director (split cost design; identity rule; explicit dossier schema);
- `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v2` §5 D–E and §8;
- `EXECUTION_PLAN_SEMANTIC_LIBRARY_v2` orders 4–5;
- ruling 22, especially implementation caution 2 (directed G3).

**Status:** Sol approved v1 with four decisions and three corrections (2026-10-11, relayed by the Director). This version records them in §0 and amends the sections they change. The design itself was read-only; its implementation (the CLICK slice) is `BUILD_SLICE_WO_G3_DIRECTED_CLICK_2026-10-11`.

## 0 · Sol's decisions and corrections (binding on this version)

| # | Decision or correction | Where it lands |
|---|---|---|
| D1 | Claude is the implementation owner for **both** CLICK and NAV: CLICK first, NAV after the CLICK review. Sol owns the interface and the NAV review, not a concurrent edit to `virelai_gates.py`. File notes precede shared edits. | §1.4 |
| D2 | **Do not replace probe ids on the coverage path.** An unchanged coverage path keeps its probe ids and therefore its evidence ids, because the evidence hash includes `probe_id`. An explicit selection, including the head, gets an identity-based id. Separate admissions, lives and phases have distinct ids; retries within one admission reuse that id and have distinct transition and evidence records. Test 0 compares probe envelopes, evidence ids and products on no-choice replays. | §1.2 A; §7, test 0 |
| D3 | Existing Duck turns suffice for the first mechanical slice, but **not for closing directed G3**. Add a bounded handoff: at most one per G3 phase per level, when G3 has at least two eligible choices, no mandatory obligation, and a genuine choice for Duck. A timeout or no selection resumes the coverage head, with no repair loop and no game stop. Measure the added turn time and the useful choices in rehearsal. | §1.2 E |
| D4 | An accepted G4.1 answer may appear in the dossier as `GATE_ACCEPTED_PRODUCT_PENDING`, citing the gate-accepted answer and its same-level evidence. It does not mark the aggregate G4 product certified, and does not unlock a downstream gate. The v3 validator enforces this. | §5 |
| C1 | A witnessed lever opens its G4 questions while the G3 inventory is pending, but they stay **blocked by the G4 prerequisite** until `LeverInventory` is active. | §6; §7, test 3 |
| C2 | Card/digest/capability equality applies **when an action capability exists**. An answer-only turn needs card/digest/answer alignment and has no capability. | §4; §7, test 5 |
| C3 | After a hard process kill, a missing final model cannot itself report `RECORD_MISMATCH`. The absent artifact is reported from the run manifest or an external audit. H1/H2 protect controlled boundaries and stops. | §5 |

**Base:**
- The code is `472aa32`.
- The document commit `8e13e35` is local and unpushed.
- The library-view slice is held in the Director's worktree, Mac-verified at 707 passed, 1 skipped. It touches none of the G3 or G4 code cited here.
- Line numbers are at `472aa32`.

**Read-only rule followed:** every probe of gate behaviour below ran on a `copy.deepcopy` of a replayed machine, or as an attribute read. The gate's own `next_probe` mutates state, so it is never called on a live machine by anything this note proposes.

---

## 1 · The shared click/NAV G3 admission contract (leading section)

### 1.1 What G3 does today

| Step | Where | Behaviour |
|---|---|---|
| Choose the target | `_LeverTarget.next_probe`, `virelai_gates.py:3418-3547` | One expected probe, chosen in this precedence:<br>1. a pending confirmation (3422-3458);<br>2. a mu revisit (3459-3462);<br>3. a reopened-reachability index (3463-3468);<br>4. otherwise the frontier row at the cursor `_target_index`. |
| Cursor moves inside `next_probe` | `:3469-3485` | The cursor skips settled and terrain-typed rows, but only in NAV (`_advance_accounted_terrain_rows`, 2870-2880). It switches CLICK→NAV in HYBRID worlds (3473-3478) and closes the sweep at the end (3479-3485). So **`next_probe` is not a pure read**. |
| CLICK probe | `:3522-3536` | `RANKED_CLICK_TARGET`. `probe_id` is `G3-LEVERS:CLICK:<cursor+1>`, with exactly one bound `ACTION6` at the target's anchor. |
| NAV probe | `:3537-3547` | `PILOT_TO_LEVER_CONTACT`. `probe_id` is `G3-LEVERS:NAV:<cursor+1>:<step>`. Any movement action is admissible, and `pilot_intent` is required. |
| Issue the token | `CyberneticGateMachine._probe_capability_token` and `next_probe_capability`, `:6604-6654` | An HMAC over gate id, gate revision and the whole probe envelope, including `target` (with `member_id`, `entity_id`, `entity_version`). |
| Validate | `CyberneticGateMachine.validate_probe`, `:6656-6731` | **Recomputes `self.next_probe()`** and refuses a token whose fingerprint differs: "Stale probe_token". |
| Attribute | `_LeverTarget.record_outcome`, `:3757-4322` | **Recomputes `next_probe()` again** and requires `probe.probe_id == expected.probe_id` (3761-3763). The entity is taken from `probe.target.member_id` (3770-3775). |
| Advance | about 12 sites | `self._target_index += 1` at 4097, 4258, 4276, 4284, 4298, 4310, 4370 and 4509, plus the skip loop at 2877, the inheritance at 2581, and others. |
| Who acts | `controller_executor._ordinary_step`, `:142-163`, and `_nav_step` G3 branch, `:261-281` | The controller takes every G3 step: in CLICK, the bound click (`_bound_action`, 347-359); in NAV, `planned_nav_step` (3549-). Duck gets G3 only when no plan exists (`_duck`, 268-275). **Today Duck has no choice at G3.** |

**The consequence, in one sentence.** The probe, the token and the attribution are all pinned to whatever `next_probe()` returns, and that is always the cursor's row. A choice away from the roster head is therefore refused at `validate_probe`. If the check were bypassed, `record_outcome` would refuse it too. This is why ruling 22 says widening `validate_probe` alone is insufficient.

### 1.2 The contract

**A. Selection is a gate-owned record, not a cursor position.**
- The G3 adapter gains `_selection`, a record with these fields:
  - `question_id`;
  - `entity_id` and `member_id`;
  - `entity_version` (the ledger hypothesis version);
  - `phase` (CLICK or NAV);
  - `selected_at_gate_revision`;
  - `actor` (CONTROLLER or DUCK);
  - `reason`.
- `next_probe` builds its probe from `_selection` when one is valid. Otherwise it uses the **coverage head**, which is today's cursor row.
- **(D2)** The coverage path keeps today's `probe_id` (`G3-LEVERS:CLICK:<rank>`), so its envelope and evidence id are unchanged. An explicit selection, including the head, gets `G3-LEVERS:CLICK:SEL:<member_id>:L<level>P<life>:R<selected_at_revision>`; its `target` carries `question_id` and `selected_by`. The id is distinct across admissions, lives and phases. Retries within the same admission reuse it, while their transition and evidence records distinguish the attempts.
- The **capability** (not the coverage probe's envelope) gains `question_id`, so the coverage envelope stays byte-identical. The token fingerprint already covers the whole probe, including an off-head target's `question_id`, so a stale question, entity version or gate revision produces a stale token with no new check.

**B. Eligibility is one pure read that the gate owns.**
- `_LeverTarget.admission_candidates()` returns the ordered list the scheduler would serve. Each entry carries `entity_id`, `member_id`, `phase`, the `obligation` (FIRST_CONTACT, or BODY_CONTACT_OWED in the NAV pass of a HYBRID world) and `coverage_rank`.
- It reads `_eligible_frontier`, the ledger, the lifecycle journal, `_terrain_roles`, `_g3_settled`, `_phase` and `_target_index`. It **never calls `_ensure_*` or `next_probe`.**
- The agenda's G3 eligibility comes from this read and nowhere else (§3 shows why).

**C. Obligations come before choice.** No choice is offered while any of these is pending:
- a pending confirmation, dossier or reachability answer;
- a mu revisit;
- a reopened-reachability row.

These are the gate's own obligations and appear in the agenda as OBLIGATION questions (§2). This keeps today's precedence (3422-3468) unchanged.

**D. Admitting a choice.**
- `CyberneticGateMachine.select_g3_question(question_id, *, actor)` admits a choice only if all of these hold:
  - the gate is `G3-LEVERS`;
  - no obligation is pending;
  - the question's entity is in `admission_candidates()`;
  - its `entity_version` is current.
- Otherwise it is refused with a typed reason, and the refusal is recorded once. No repair loop follows (ruling 22, caution 1).
- Admission writes `_selection` and bumps the gate revision, so earlier tokens go stale.
- Duck reaches this through `virelai('next_probe', question_id=Q)`. That call admits the selection and returns the freshly bound capability in one step.

**E. The bounded handoff, timeout and routine coverage (D3).**
- When G3 has at least two selectable rows, no obligation and no selection, the controller hands Duck **one** turn for that G3 phase on that level (`_choice_handoffs`, LEVEL tier), with the reason "G3 choice".
- If Duck's turn ends with no admitted selection, the controller's next step serves the coverage head exactly as today. There is no second handoff in that phase, no repair loop and no stop.
- The handoff is a live-session setting (`ControllerSession.g3_choice_handoff`), off for controller-only drivers and replays, so their behaviour is unchanged.
- Routine coverage selects implicitly. `_selection` stays empty, and `next_probe` falls back to the head.

**F. Attribution.** `record_outcome` is unchanged in substance. It checks `probe.probe_id` against the bound probe (the coverage id, or the selection's identity-based id) and attributes to `probe.target`, which is the selection. No lifecycle transition is added, and the transition table (`lever_lifecycle.py:22-46`) is not widened.

**G. Finishing a target.**
- The about 12 `_target_index += 1` sites become one call, `_finish_target()`:
  - if the finished row was the selection, it clears `_selection` and leaves the cursor in place, unless the selection *was* the head;
  - if the finished row was the head, it advances the cursor.
- The settled-row skip (`_advance_accounted_terrain_rows`, 2870-2880) now runs in **both** phases, so the cursor passes rows a choice already settled.
- This is the riskiest edit. **(D2)** It is pinned by replaying k008, k013 and carry-v7 with no choice and comparing every probe envelope, evidence id, product, frozen level, transition row and G3 lifecycle state with a golden trace written before the edit (§7, test 0). In the CLICK slice only the three CLICK-reachable sites change; the NAV sites change in the NAV slice.

**H. Staleness.** A selection is invalid, and `next_probe` falls back to the head, when:
- the entity's version changed (a class change or regrouping);
- the level or life changed;
- the gate moved off G3;
- the row became settled.

Duck's old token then fails at `validate_probe` as "Stale probe_token". Historical receipts are untouched.

### 1.3 Click and NAV specifics

| | CLICK | NAV (and HYBRID's NAV pass) |
|---|---|---|
| What a choice binds | One click at the chosen row's current anchor (`target.cells` from the current sighting, 3489-3496) | A **pursuit**: the selection persists across route steps until contact, refusal, a boundary or the pilot budget finishes it (the same finish points as 4245-4310) |
| Controller step under a selection | `_bound_action` serves the bound click, unchanged | `planned_nav_step(target)` plans toward the selected target, unchanged in form. Reachability and terrain rules stay Sol's. |
| What can be chosen | Rows in `admission_candidates()` with CLICK phase | The same, plus BODY_CONTACT_OWED rows in HYBRID worlds (the G3 lifecycle slice, `cd07716`) |
| Ambiguity | AMBIGUOUS rows are re-admissible only through their existing reopen path, never by selection alone | Same |

### 1.4 Owners (one active editor per shared file at a time)

| Shared file | Part | Proposed owner | Reviewer |
|---|---|---|---|
| `virelai_gates.py` | `_LeverTarget`: `_selection`, `admission_candidates`, identity-based off-head `probe_id`, `_finish_target`; `CyberneticGateMachine.select_g3_question` | **Claude (D1)** | Sol |
| `virelai_gates.py` | `planned_nav_step` and reachability/terrain under a selection | **Claude (D1)**, after Sol reviews the CLICK slice | Sol |
| `controller_executor.py` | `_ordinary_step` and the `_nav_step` G3 branch: serve the selection when present, else the head | Claude | Sol (NAV branch) |
| `tool_agent.py` / `memory_queries.py` | `virelai('next_probe', question_id=…)` | Claude | Sol |
| `card_builder.py` | `_template_slot` (261) shows the bound `question_id` | Claude | Sol |
| `lever_lifecycle.py` | **Untouched**: the table is not widened | — | — |

The first slice is click-led. The NAV branch serves the head unchanged until Sol's follow-on admits NAV selection. This is the "one integration owner at a time" rule of plan v2 §8.

---

## 2 · The question record and agenda (split design)

**Two projections, one vocabulary.**
- **The gate agenda** (`library_agenda`, a new pure module). Built from gate-owned state, it is cheap and runs on every controller and Duck step. It is the **only** source of selection and binding.
- **The census agenda.** Built from the validated live model on Duck turns and at H1/H2 checkpoints, it adds object context (track questions, joins, observation counts) and is never used to bind.

**The question record:**

| Field | Source |
|---|---|
| `question_id` | `Q:L{level}:{gate}:{subject}:{kind}` for gate questions; `Q:L{level}:P{life}:{track_id}:ROLE` for pre-G3 object questions |
| `chapter` / parent | The gate, or a NOT_BUILT chapter (G5, G6, DRIVEN, INERT, BAND1) |
| `subject` | Foundations: `LEVEL-n`. G3 and G4: the **G3 entity id**, which may span lives. Pre-G3: a **life-scoped track id**. |
| `binding` | `entity_version`, `member_id`, `life`, and the track join if exact (context only) |
| `question` | Plain text from the gate goal (ruling 22 wording) |
| `admitting_gate`, `prerequisites` | `target_registry` contracts (`cybernetic_targeting.py:22, 80-104`) |
| `disposition` | See the mapping below |
| `evidence_refs`, `missing_evidence` | Lifecycle events and witness refs; the gate's unmet requirements |
| `scope` / `limitation` | Lifecycle side states; bounded-ambiguity records |
| `experiment_kinds` | `CLICK_PROBE`, `NAV_PURSUIT`, `CONFIRM`, `ANSWER` |
| `agenda_revision` | A hash of the gate agenda: the cheap cursor that rejects stale actions |
| `library_revision` | `content_sha256[:12]` of the live model; present on Duck turns only |

**Dispositions.** At least these, as the memo requires:

| Disposition | Meaning, or lifecycle source |
|---|---|
| ANSWERED (lever) | WITNESSED, G4-READY, or G3-CLOSED with witness refs |
| ANSWERED (scoped null) | G3-CLOSED with no witness |
| ANSWERED (terrain, not a role) | Typed by the NAV terrain map |
| OPEN_ACTIONABLE | In `admission_candidates()` |
| OPEN_IN_PROGRESS | ATTEMPTED, RESPONDED, or NO_RESPONSE_YET not currently admissible |
| OBLIGATION | A pending confirmation, dossier, reachability answer or mu revisit |
| BLOCKED_BY_PREREQUISITE | A prerequisite product is inactive |
| INCONCLUSIVE | AMBIGUOUS |
| BUDGET_LIMITED | BUDGET_STOPPED |
| REACHABILITY_LIMITED | PRESUMED_UNREACHABLE |
| NOT_BUILT | Never selectable, never shown as an action |

`FILLED` is never computed from a display frontier.

**Identity** (the Director's ruling):
- Before G3, object-role questions use life-scoped track ids.
- At G3 and G4, lever questions use the G3 entity id. An exact one-to-one track join is attached as context and never carries a closed answer.
- A late join, regrouping (an entity version change), class change, level change or invalidated product rebinds the question; it is not transferred.
- Earlier track ids survived the measured k013 (100→400) and k008 (20→61) prefixes. That is evidence, not a guarantee, so the regrouping test stays (§7, test 4).

**Selection rule for the first slice.**
- Select within the first ready gate, which is `TargetRouter.current()` (`cybernetic_targeting.py:169-182`).
- Obligations first, then Duck's admitted choice if any, else the coverage head.
- The interface already carries `admitting_gate` per question, so selection across several ready chapters can come later without changing the record.

---

## 3 · Cost and agreement (measured)

**The measurement.** I wrote a throwaway gate-agenda prototype: foundations from the journal; G3 dispositions from the lifecycle journal and terrain; NOT_BUILT chapters. I ran it on replays of three development records, 23 cut points in all:
- k013, every 25 transitions to 400;
- k008, every 10 transitions to 60;
- carry-v7 across its level change.

At each cut I compared it with the full census compile.

| | Gate agenda (split) | Full census (compile only) |
|---|---|---|
| Cost per call | **0.015–0.078 ms**, mean of 20 runs | **0.11–6.52 s** (k013: 0.23 s at 25 transitions → 6.52 s at 400; k008: 0.11–1.96 s) |
| Mutates the machine | No (pickle digest identical after each call) | No |
| Controller steps in the v2 rehearsal | about 92 % of 2,966 actions | Putting the census there would cost hours per run |

**An incremental census was not prototyped.** `project_tracks` reweaves each life window and re-joins it globally (`library_census.py:153-205`), so an incremental version needs invalidation rules for regrouped lines. On these numbers the split design meets the hot-path budget by roughly five orders of magnitude. I recommend it, and I recommend the incremental census only if a later chapter needs census-derived questions on controller steps.

**Agreement on dispositions: 23 of 23 cuts agree exactly.**
- The checked sets: lever roles = ANSWERED-lever; the census INCONCLUSIVE, BUDGET and PRESUMED_UNREACHABLE gaps; NO_RESPONSE_YET gaps; scoped nulls; terrain; and foundation dispositions against the census's gate table.
- This becomes the checkpoint test: at every Duck turn and at H1/H2, the census agenda and the gate agenda must agree on every subject both cover.

**Agreement on selection: the naive prototype disagreed with the gate at 6 of 7 G3 cuts.**
- The comparison was the prototype's choice against `next_probe()` on a deep copy:

  | Record | Transition | Prototype chose | Gate's next probe |
  |---|---|---|---|
  | k008 | 40 | E0003 | E0005, CLICK |
  | k008 | 45–60 | E0003 | E0001, NAV |
  | k013 | 400 | E0005 | E0001, NAV |

- The causes are all scheduler state that the lifecycle journal does not show:
  - E0003 is a lifecycle entity outside the eligible frontier;
  - E0001 is NO_RESPONSE_YET in CLICK but **owed body contact** in HYBRID's NAV pass;
  - the cursor had already passed rows the G2-null inheritance recorded.
- This is why §1.2 B makes G3 own `admission_candidates()`. The agenda must not re-derive eligibility.
- Test 5 in §7 asserts that, with no choice made, the agenda's selection equals the gate's coverage head on every replay cut.

**Prompt size today** (k013 at 400; k008 at 45):

| | Card | Digest | Total |
|---|---|---|---|
| k013 at 400 | 3,949 | 2,106 | 6,056 characters |
| k008 at 45 | 4,030 | 2,080 | 6,111 characters |

The slice adds a question id and one line of reason to each, within the existing budgets. The v2 baseline for Duck turns (78 s mean, 499 of 873 cut by the turn budget) is re-measured in the first library rehearsal, as the plan requires.

---

## 4 · One target on the card, in the view and in the probe

**Where each surface reads the target.**
- **Card:** `_template_slot` (`card_builder.py:261`) renders the capability, whose `target.question_id` is the bound question.
- **Digest:** the goal block shows the *same* `question_id`, read from the gate agenda (not from the `IN_PROGRESS` gate, which is today's `_goal`). It also shows the `library_revision`.
- **Lookup:** `virelai('library', kind='question', id=Q)` returns the question with its evidence, what is missing, and what is known about the subject. It is a bounded page, under the existing continuation rule.

**The invariant.** The test is `card.question_id == digest.goal.question_id == capability.target.question_id` at every Duck turn. An action carrying a token for any other question, entity version or gate revision is refused as stale.

**`PLAY-NORMAL`.** The digest names an actionable library gap if one exists (plan v2 §8). The play gate's goal wording is a separate edit to `play_gate.py`, a shared file, in order 8. Free-play receipts stay free play.

---

## 5 · G4 dossiers: what exists, what survives an early stop, and the schema proposal

**What the four G4 gates keep per lever** (read-only map at `472aa32`):

| Gate | Per-lever material | Product | Survives an early stop? |
|---|---|---|---|
| **G4.1 anatomy** (`_ReactionTarget`, `virelai_gates.py:5552`) | `_anatomies` (compiled from G3 evidence for the **whole roster**, 5573), `_answers` (`LeverReactionAnswer`, which has an `answer_id` and `entity_id`: `g4_reactions.py:95-107`) | `LeverEffectAnatomySet`, **only once every lever is answered** (5702-5703) | The answers survive in `_gate_answers.jsonl`. The anatomies are in memory only. |
| **G4.2 orbits** (`_LeverStudyTarget`, 5823) | `_runs{eid}`, `_completed`, `_interruptions`, `_life_restudies` | `LeverOrbitSet`, re-emitted progressively on each answer and at boundaries (6324, 6241) | Per-press events go to `_gate_events.jsonl`, but without the orbit state sequence. |
| **G4-B relations** (`g4b_gate.py:79`) | Predictions, each with `acted_lever` (`g4_relations.py:162-178`); `pressed_levers` / `unpressed_levers` in the product | One aggregate answer for the roster | A D21 close records one reason string and **nothing per lever** (`play_gate.py:59-67`) |
| **G4-C law** (`g4c_gate.py:70`) | No per-lever material | One aggregate answer | Same as G4-B |

**Two facts decide the persistence question.**
1. All of this partial state is LEVEL tier (`life_record.py:66-84`) and lives in memory until the level's adapters are rebuilt.
2. The census already runs at exactly the two points where that state is still present:
   - **H1** sits *before* `freeze_level` and `_build_level` in `_advance_level`;
   - **H2** runs in the solver's `finally`, while the analyzer still holds the machine.

**The proposal.** A read-only extension of the census reads the G4 adapters' partial per-lever state at H1 and H2, exactly as it reads G3's today, and projects it into a per-lever dossier. **No new gate-owned persistence is needed** for an early stop that the run itself survives.

Two cases remain:
- **A hard process kill**, with no `finally`. Nothing survives except the JSONL rows, and the same is true of G3 today. I propose no new record for it now. **(C3)** A missing final model cannot report anything about itself: the absent artifact is reported from the run manifest or an external audit. H1/H2 protect controlled boundaries and stops.
- **A D21 close.** The census can attribute it per lever from `unpressed_levers` and each prediction's `acted_lever`, so no new record is needed. If Sol wants the close reason itself per lever, that would be a one-field addition to the `close_unresolved` products. It is not proposed by default.

**Schema evolution: `virelai-world-model-v3`, declared and versioned.**
- `read_world_model` gains a v3 branch. The v1 and v2 readers are kept for migration.
- Each level gains `certified.dossiers[]`, one per witnessed lever (G3 entity id), with a chapter block each for anatomy, orbit, relations and law. Each block carries:
  - `status`, from: ANSWERED_IN_PRODUCT, GATE_ACCEPTED_PRODUCT_PENDING (D4: cites the gate-accepted answer and its same-level evidence; never marks the aggregate product certified or unlocks a downstream gate, which the v3 validator enforces), RUNNING, COMPLETED, INTERRUPTED, UNSTUDIED, PRESSED, UNPRESSED, AGGREGATE_ONLY, NOT_REACHED, CLOSED_UNRESOLVED;
  - its `source`: a product id or an answer id;
  - its `evidence_refs`.
- Orbit runs that are not yet in a product are **observation tier**, never certified.
- The receipts index gains an `answers` table (answer id → gate, entity, evidence refs). The validator requires:
  - every dossier names a certified LEVER of the same level;
  - every certified chapter claim resolves to a product or an accepted answer of the right gate and entity;
  - no dossier exists for a non-lever.
- The digest gains "levers explained / witnessed". Retrieval gains `kind='dossier'`.

---

## 6 · Field by field

| Field | State |
|---|---|
| Foundation questions (G0, G1, G2) and their dispositions | **Derivable now** (journal, registry) |
| G3 per-entity disposition | **Derivable now** (lifecycle journal, terrain, bounds); agrees with the census at 23 of 23 cuts |
| G3 eligibility and coverage head | **Needs the gate-owned pure read** `admission_candidates()` (§1.2 B) |
| G3 selection, binding and attribution to a choice | **Needs the shared G3 change** (§1.2 A, D–H) |
| `question_id` on the card and the token | Needs the shared change (`target.question_id`) |
| Pre-G3 object-role questions | **Derivable now** from the census (track gaps), not selectable before G3 |
| G4 per-lever dossier: anatomy answers, orbit runs and classes, relation pressed/unpressed and predictions | **Derivable at H1 and H2 and on Duck turns** from adapter state; **needs the v3 schema** to persist |
| G4 per-lever D21 close reason | Derivable as unpressed plus the gate reason; a per-lever reason would need a product field (not proposed) |
| G4 dossier choice (which lever's question Duck pursues) | G4.2 already admits any action and attributes by the lever acted on (`_route_action`, 6160-6228). Binding the question to it is the G4 slice, after G3. |
| Environmental force, scoped negatives, driven reactions, INERT, Band 1 | **NOT_BUILT**, never selectable |
| Observed-win and transfer questions | **NOT_BUILT** in the agenda; owned by WO-LW-D (plan v2, stage H) |

---

## 7 · Fail-first test plan

Each test is written to fail on `472aa32` and pass after its slice. They use production paths: replayed development records (k008, k013, carry-v7), the WO-L1a click world, and the real gated `ToolAgent` bridge used in the close-out tests.

| # | Test | Fails today because | Fixture |
|---|---|---|---|
| **0** | With no choice made, every probe envelope, evidence id, product, frozen level, transition row and G3 lifecycle state matches a golden trace written before any edit (D2) | — (a guard, written first) | k008, k013 and carry-v7 full replays |
| **1** | On an empty observed level, the selected question is the foundation question (G0 or G1), no object role is fabricated, and NOT_BUILT never wins selection | There is no agenda; the digest goal comes from `IN_PROGRESS` | WO-L1a click world at 0 actions; carry-v7 level 2 entry |
| **2a** | Two eligible G3 rows: Duck selects the second. A fresh token binds the second row's probe, the outcome is attributed to it, and the head stays unvisited and eligible. | `validate_probe` refuses: the token is stale because `next_probe` is the head (6696-6700) | Real `ToolAgent` bridge on the k008 CLICK cut at 40 (rows E0005, E0006 eligible) |
| **2b** | Duck's turn ends without a selection, and the controller serves the coverage head | — (a guard) | Same |
| **2c** | A stale selection (entity version bumped, or a level or life change) refuses the old token and falls back to the head | There is no selection | Same, with an entity version bump |
| **2d** | An ambiguous frame after a chosen click produces INCONCLUSIVE or a bounded ambiguity, never a lever | — (a guard against false levers) | A synthetic outcome on the k008 cut |
| **3** | One witness opens that lever's G4 questions, **blocked by the G4 prerequisite until `LeverInventory` is active** (C1). After the inventory, two witnessed levers keep two separate dossier question sets. | There are no dossiers or G4 questions | k013 at 400 (9 levers, inventory PENDING); carry-v7 level 1 (E0004, E0005) |
| **4** | A class change, contradicted product, level change or life change rebinds or invalidates the question. Receipts remain, and a frozen level never absorbs next-level evidence. | There are no questions | carry-v7 across transition 26; k008 across its reset at 31 |
| **5** | When a capability exists, the card, the agenda (and later the digest) and the capability show the same `question_id`; an answer-only turn aligns card and agenda with no capability (C2). An action whose token names another question or revision is refused. With no choice, the agenda's selection equals the gate's coverage head at every G3 replay cut. | There is no `question_id`; the naive selection disagrees at 6 of 7 cuts (§3) | k008 and k013 G3 cuts |
| **6** | A gate stop leaves a typed unresolved question, a `FREE_PLAY` receipt stays free play, and an empty displayed frontier never yields FILLED | There is no agenda | Close-out free-play fixture; a D21 close on a synthetic G4-B |
| **7** | The agenda is pure: the gate machine is byte-identical after it, and the output is deterministic for the same model and journal snapshot | — (a guard) | All the above |

**Every returned slice also carries** a saved-record replay of question → admitted action → receipt → verdict → revised question, the prompt size, the agenda latency (median and tail), and the remaining typed gaps (memo, "What I need from you next").

---

## 8 · The slice sequence after Sol's review

1. **Pure modules (not shared):**
   - `library_agenda.py` (the gate agenda, dispositions, NOT_BUILT chapters, agreement check against the census);
   - a census extension for the agreement test.

   Tests 1 (the agenda half), 6 (the agenda half) and 7.
2. **Shared G3 integration** (Claude, NOTE first, Sol reviews NAV semantics):
   - `admission_candidates`, `_selection`, identity-based off-head `probe_id`, `_finish_target`, `select_g3_question`, the bounded handoff;
   - `virelai('next_probe', question_id=…)`;
   - the card and digest show `question_id`.

   Tests 0, 2a–2d and 5 on CLICK.
3. **The NAV slice (Claude, D1), after Sol's CLICK review:** selection under pursuit; `planned_nav_step` toward a selection; HYBRID body-contact obligations. Tests 2a–2c on NAV cuts.
4. **G4 dossiers:** the v3 schema and census projection; then G4 question binding over the whole roster. Tests 3 and 4.

**Kept out:** SUB-4, the `PLAY-NORMAL` wording (order 8), NAV G1 rests and repair loops (their own tracks), G5/G6/DRIVEN and the win transfer.

## 9 · Decisions asked of Sol (all four decided; see §0)

1. ~~Integration owner~~ — **decided (D1):** Claude implements CLICK, then NAV after review; Sol owns the interface and the NAV review.
2. ~~`probe_id` becomes member-keyed~~ — **decided (D2):** coverage ids are unchanged; only off-head selections get identity-based ids.
3. ~~Where Duck chooses~~ — **decided (D3):** a bounded handoff, once per G3 phase per level, plus `virelai('next_probe', question_id=…)` on any turn Duck has.
4. ~~v3 dossiers~~ — **decided (D4):** `GATE_ACCEPTED_PRODUCT_PENDING`, enforced by the v3 validator.

— Claude, Alpha build seat (click line)
