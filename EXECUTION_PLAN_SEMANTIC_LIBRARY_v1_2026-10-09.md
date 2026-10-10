# Execution plan: the semantic library, from plan to committed code (v1, 2026-10-09)

**Type:** `EXECUTION_PLAN_SEMANTIC_LIBRARY` · **v1** · **2026-10-09**
**Status:** for the build team. It executes `BUILD_PLAN_SEMANTIC_LIBRARY_PUSH_FALLBACK_v3_2026-10-09` (committed at `d69b89e`). Work orders marked **BLOCKED** wait on the Apex ruling named in §2. Everything else may start.
**Author:** Claude, Alpha build seat (click line), signed.
**Base:** `ring9-unified` = `main` @ `d69b89e`. Its runtime is SUB-3 `fc152e6`, with a floor of 630 passed, 1 skipped.
**Game-free.** A world is named only as the source of a measured count. No mechanic or win condition appears.

**How to use this document.** Each work order (§5) stands on its own:
- its owner and dependencies;
- the premises to verify at file:line before any code;
- fail-first tests;
- exit evidence;
- the shared files it touches;
- what it must not do.

The milestones and their exit criteria are plan v3 §2. They are not repeated here, except as each work order's target.

---

## 1 · Who does what

| Seat | Owns in this plan | Does not touch |
|---|---|---|
| **Director** | Every terminal command, git commit and push, Mac floor, Kaggle action and answer key. Rulings via Apex. | — |
| **Apex** | The rulings in §2. Assigning L3a, L3b and L5. Grading each slice's return against its exit evidence. | Building |
| **Claude Alpha (click line)** | WO-L1a, WO-L1b, WO-L1c, WO-L2-00, WO-L2, WO-L4b, the click half of WO-L4c, the packages and rehearsals | NAV internals; LW-0 to LW-D |
| **Sol (NAV line)** | WO-L1a-NAV (the HYBRID and NAV G1 stops, §3), the NAV worldlines in WO-L2, the NAV half of WO-L3a if assigned | Click gates |
| **Learn-to-win chamber** | LW-B (the role and mechanic-law compilers, for WO-L4a), the grammar files, the win referee, half of WO-L4c, the world-report compiler | Runtime gates |
| **Unassigned until Apex rules** | WO-L3a, WO-L3b, WO-L5-00, WO-L5 | — |

## 2 · Rulings, and what each one blocks

| # | Ruling (plan v3 §8) | Blocks | Does not block |
|---|---|---|---|
| R1 | Adopt plan v3 | Nothing yet. Work proceeds on the plan's priority. | — |
| R2 | L1c architecture: downstream gates observe only, with no journal products | **WO-L1c** | WO-L1a, WO-L1b, WO-L2 |
| R3 | L5 carve-out from R-7: passive map recording | **WO-L5-00, WO-L5** | everything else |
| R4 | Owners for L3a, L3b, L5; LW-B delivery date | **WO-L3a, WO-L3b, WO-L4a** | WO-L4b, which runs on existing products |
| R5 | The learn-to-win chamber's uncommitted files in the shared worktree | Clean floor runs. Until it is settled, every floor run uses `--ignore=tests/test_physics_grammar_contract.py`. | — |
| R6 | `RULING_PUSH_ORACLE_v1`'s status | Only the Push's return | everything in this plan |

**New for Apex (§3):** the 9 G1 stops in HYBRID worlds belong to the NAV line. That makes WO-L1a-NAV Sol's.

## 3 · New finding: the root cause of the zero-action G1 stops

Plan v3 attributed the two G1 stops at action 0 partly to Duck explaining before it had evidence. The source and the rehearsal artifacts show a narrower cause: **a contract defect.**

**The template and the validator disagree:**
- `virelai_gates.py:7049-7056`: in a click-only world (`pointer_exit`), G1's `answer_template` writes `action_laws` for **every** available action, each as "selects the supplied grid coordinate".
- `virelai_gates.py:728-730`: `submit_answer` refuses any answer unless `set(answer.action_laws) == {"ACTION6"}`.

**What that does.** In a click-only world that also offers actions other than ACTION6:
1. The controller submits the template verbatim (`controller_executor.py:372-375`).
2. G1 refuses it.
3. The controller hands the turn to Duck.
4. Duck copies the same template.
5. G1 refuses it again, which is a contract loop at 0 actions.

**The evidence.** `k022` (actions ACTION5, ACTION6, ACTION7):
- transcript line 5: "G1-EGO refused the controller's answer: Click-only G1 must explain ACTION6 as the site-selecting control locus";
- line 177: the template's three `action_laws`;
- `k023` (ACTION6, ACTION7) shows the same.

Click-only worlds with ACTION6 alone close G1 cleanly (`k000`, `k010`, `k017`). The template also makes a false claim: it says ACTION5 and ACTION7 select a grid coordinate.

**What this changes:**
- **WO-L1a** becomes a contract fix with a fail-first test, plus a check that ruling 6 holds. G1 for a pointer ego closes on the interface axiom without any Duck explanation, which is ruling 6's intent.
- **The 12 G1 rests break down as 3 + 9.** Three are this defect: `k022`, and `k023` twice (its second rest is at the start of level 2, where G1 reopens on the new level). The other 9 happened in HYBRID worlds (movement plus pointer) after 26–52 controller actions: `k001`, `k002`, `k012`, `k013`, `k016`, `k026`, `k027`, `k028`, `k033`. There, evidence already came before the explanation; Duck's explanation turn looped afterwards. These run through `_nav_step` (`controller_executor.py:133-134`), so they are the **NAV line's** (WO-L1a-NAV, Sol).
- **A library gap surfaces.** Click-world non-pointer actions (ACTION5, ACTION7) are explained by no gate today. WO-L1a records them as open obligations, and WO-L2-00 checks whether any gate studies them.

## 4 · Order and calendar

**Order of the work.** Click line (one builder), in sequence:
1. WO-L1a, then package v3, whose rehearsal is WO-L1b.
2. WO-L2-00, then WO-L2, which also goes in package v3.
3. WO-L1c, when R2 is ruled.
4. WO-L4b.
5. WO-L4c, with the learn-to-win chamber.
6. Package v4.

**In parallel:**
- WO-L1a-NAV (Sol).
- WO-L3a and WO-L3b (once R4 assigns owners).
- WO-L5-00, then WO-L5 (once R3 grants the carve-out and R4 assigns an owner).
- LW-B, then WO-L4a.

**Package v3** = WO-L1a + WO-L2, plus WO-L1a-NAV if it lands first. **Package v4** = WO-L1c + WO-L4b + whatever of L3 and L4c has landed.

| Date (estimate) | Click line | Others |
|---|---|---|
| Oct 9–10 | v2 rehearsal graded; v2 submitted. WO-L1a premises and fail-first tests. | Apex rules R1 to R6 |
| Oct 10–11 | WO-L1a built; floor run | Sol: WO-L1a-NAV diagnosis |
| Oct 11–13 | WO-L2-00 (read-only), then WO-L2 | Owners for L3a and L3b start the record-only readers |
| Oct 14 | Package v3 built, verified and pushed; rehearsal (WO-L1b) | — |
| Oct 15 | WO-L1b graded; v3 submitted if it passes | — |
| Oct 15–19 | WO-L1c (if R2 is ruled) | L3a, L3b; LW-B |
| Oct 19–23 | WO-L4b; WO-L4c with the learn-to-win chamber | L5 if assigned |
| Oct 24–26 | Package v4: built, rehearsed, submitted | — |
| Oct 27–30 | **Freeze.** Floors, reports, nothing new. | — |
| Nov 2 | Final code. M1 on every level; M2 measured on development levels. | — |

## 5 · Work orders

### WO-L1a · The pointer-ego G1 contract (click line)

**Owner:** Claude Alpha. **Depends on:** nothing. **Target:** no G1 stop at 0 actions in a click-only world.

**Premises to verify at file:line:**
- `virelai_gates.py:7036-7056`, the pointer `answer_template`;
- `:712-737`, `submit_answer`'s pointer branch;
- `controller_executor.py:372-375`, the controller's G1 answer;
- `:284-294`, the refusal and handoff;
- `control_archetype_prior` (`virelai_gates.py:292-322`), how world types are classified;
- where `ego_law_from_interface` consumes `action_laws`;
- which downstream reader expects ACTION6 alone.

**Build:**
1. In the pointer template, `action_laws` names ACTION6 only. Its mechanism stays as "selects the pointer locus coordinate".
2. Every other available action is listed in the template's `limitations` as "not explained by the interface axiom; its effect is an open obligation for later gates". The template no longer claims that ACTION5 or ACTION7 select a coordinate.
3. The validator is unchanged. It already says what the axiom covers.
4. The open non-pointer actions are carried on the G1 product, so the census (WO-L2) can report them as typed gaps.

**Fail-first tests** (new file `tests/test_l1a_pointer_g1_contract.py`):
- A click-only world offering {ACTION6, ACTION7}: the controller's template answer is accepted; G1 closes at 0 actions; the router opens G2. **This fails at `d69b89e`.**
- The same with {ACTION5, ACTION6, ACTION7}. **Fails at `d69b89e`.**
- {ACTION6} alone: unchanged, still passes.
- The G1 product lists the non-pointer actions as open obligations, and no `action_law` claims a coordinate for them.
- Ruling 6: in no click-only world does Duck receive a G1 turn before the first action.

**Exit evidence:**
- Replaying the `k022` and `k023` opening (0 actions, G1) closes G1 without any Duck turn.
- The floor shows 630 + n passed, 1 skipped.

**Shared files:** `virelai_gates.py` (G1 template and product). File `NOTE_SHARED_FILE_<date>.md` before the commit, naming the functions.

**Must not:**
- touch `_nav_step` or HYBRID G1;
- change the validator's meaning;
- assign any semantic meaning to ACTION5 or ACTION7.

**Size:** about 1 day.

### WO-L1a-NAV · HYBRID G1 explanation loops (NAV line)

**Owner:** Sol, subject to Apex confirming (§2). **Depends on:** nothing. **Target:** fewer HYBRID games resting at G1.

**Diagnostic first.** Per HYBRID world in the rehearsal (the 9 listed in §3):
- the controller actions taken in G1;
- the last G1 gate view;
- what Duck was asked;
- the rejection or no-progress reason;
- whether G1 had enough evidence to close from the record.

**Then:** a fix, under Sol's own fail-first discipline. Possible fixes include a record-derived G1 answer the controller can own, or closing G1 `UNRESOLVED` with a typed reason.

**Exit evidence:** HYBRID G1 stops by cause, before and after the fix, measured in WO-L1b.

**Shared files:** per Sol's own `NOTE_SHARED_FILE`. **Must not:** change click-world G1 (WO-L1a).

### WO-L1b · Measure the G1 stops that remain

**Owner:** Claude Alpha. **Depends on:** WO-L1a, and package v3. **Target:** the decision whether WO-L1c is needed, and where.

**Rehearsal criteria for package v3 (added to its `RUN.md`):**
- **G1-a:** no G1 stop at 0 actions in a click-only world.
- **G1-b (reported):** G1 dispositions per world type: closed, `UNRESOLVED` with its reason, or a controlled stop with its cause.
- **G1-c (reported):** the share of games reaching G2, against v2 on the same clone indices.
- All of v2's criteria, unchanged.

**Exit evidence:** a graded review listing every remaining G1 stop by cause and line (click or NAV).

### WO-L1c · Diagnostic observation past an unresolved foundation (BLOCKED on R2)

**Owner:** Claude Alpha. **Depends on:** R2, and WO-L1b showing that stops remain. **Target:** the library keeps gathering evidence on levels where a foundation stays unresolved, without certifying anything on it.

**Premises to verify at file:line:**
- `cybernetic_targeting.py:169-182`: `TargetRouter.current` opens a target only when its prerequisites are ACTIVE;
- `:116-140`: `TargetJournal.put` refuses inactive prerequisites;
- `solver.py`, `_rest_after_controlled_stop` (SUB-2);
- `play_gate.rest_in_play`;
- the mu return (`mu_return.py:73`);
- how the gate machine reaches the next gate's probe capability.

**Build:**
1. A diagnostic lane beside the journal: a per-level store of `DiagnosticObservation` records. Each holds the transition, the sightings, the residuals, the gate whose probe *would* have applied, and `missing_foundation` (the unresolved target).
2. While a level rests after an unresolved G1 or G2, the controller may run the next gate's **observation** probes. They write diagnostic records only, and nothing is passed to `TargetJournal.put`.
3. When the foundation later becomes ACTIVE (a reopen, the mu return, or a new level), each downstream gate **re-derives** from the diagnostic records under its own validation. Nothing is promoted by copying.

**Fail-first tests:**
- Router invariant: no target opens on an inactive prerequisite, before and after the change.
- With G1 unresolved, a G2 observation is recorded as diagnostic, with `missing_foundation`, and no G2 product exists.
- After G1 becomes ACTIVE, G2 re-derives from those records and its product cites them.
- With no ACTIVE foundation, the census counts diagnostic evidence separately.

**Exit evidence:** the tests, the floor, and a package v4 rehearsal reporting diagnostic records per level.

**Shared files:** `virelai_gates.py`, `controller_executor.py`, `controller_turn.py` and `solver.py`, as confirmed at the premise step. `NOTE_SHARED_FILE` first, scheduled around Sol's open slice.

**Must not:** change `TargetRouter` or `TargetJournal`, or certify any law on an unresolved foundation.

**Size:** about 3 days.

### WO-L2-00 · Census inputs (read-only)

**Owner:** Claude Alpha. **Depends on:** nothing. **Target:** the exact sources for every census field, with no code.

**Questions, each answered at file:line:**
1. Which ledger records every observed worldline, including departed ones (the G3 `entity_ledger`, the NAV roster, `level_record`)? Does any discard departed worldlines?
2. Where each canon role is evidenced today:
   - EGO: the G1 product, including ego with no body on the grid;
   - COUNTER: the G2 product;
   - LEVER and its type: G3, G4.x;
   - INERT: the G3 scoped nulls, and whether any carry a coverage certificate;
   - REACTIVE-DRIVEN and ENVIRONMENTAL FORCE: expected to be absent; confirm.
3. Where a worldline's class signature lives, and whether a class change is detected.
4. Whether a Band-1 STATIC or REACTIVE read exists anywhere in Ring 9.
5. Whether any gate probes click-world non-pointer actions (the gap from §3).
6. What the v3 grammar draft's read-only projection needs (`physics_grammar_bridge.py`, uncommitted).

**Deliverable:** `WO_L2_00_CENSUS_INPUTS_RETURN_v1_<date>.md`: one table of census field → source at file:line → gap.

**Size:** half a day.

### WO-L2 · The census (M1's instrument)

**Owner:** Claude Alpha, with Sol for NAV worldlines. **Depends on:** WO-L2-00. **Target:** M1 exit criteria 1–5 (plan v3 §2).

**Build.** A new read-only module, `inference/framework/library_census.py`, and an artifact `kNNN_p0_census_L<level>.json` written at level end and run end. Per worldline:

| Field | Content |
|---|---|
| `worldline_id` | The worldline |
| `present_now` | Whether it is on the board now |
| `class_signature` | Its class signature |
| `band1` | STATIC, REACTIVE or `UNSETTLED` |
| `roles` | The set of supported roles, each with evidence references and its source gate |
| `inert_certificate` | Required when `roles == {INERT}`. INERT excludes every other role. |
| `gaps` | Typed open questions: `{archetype_question, reason}`, where reason is one of `NOT_REACHED`, `BUDGET`, `FOUNDATION_UNRESOLVED`, `CLASS_CHANGED`, `NOT_BUILT` |
| `diagnostic_only_evidence` | Count, from WO-L1c when present |

**Per level:**
- gate dispositions;
- the explained share of observed changes, and the unexplained residual;
- the click-world non-pointer actions still open;
- M1 met or not, and M2 met or not, with the M2 criteria missed, by number.

The census is also the read-only feed for the grammar draft's §3 (no second belief writer). The census reads products; it never writes a gate product.

**Fail-first tests:**
- Every worldline in a fixture record appears exactly once, departed ones included.
- Overlapping roles are represented (ego plus lever).
- INERT without a certificate is refused, and INERT never appears together with another role.
- A class change revokes the role set.
- A planted unreached worldline shows as a gap, never missing.
- A census full of gaps reports M1 met and M2 not met.
- The output is deterministic on replay.

**Exit evidence:**
- **The baseline:** the census run on the development-world records (v7/v8 records and earlier canaries), not on save-run output, until the Director's answer keys are committed (ruling 10).
- Package v3 writes the census, and its rehearsal reports M1 per level.

**Shared files:** none expected. A hook at level end in `level_model.freeze_level` or the run end may be needed; that is confirmed at WO-L2-00, with `NOTE_SHARED_FILE` if so.

**Size:** 2–3 days.

### WO-L3a · ENVIRONMENTAL FORCE (G5), record-only (BLOCKED on R4)

**Owner:** per R4; the NAV part with Sol. **Target:** M2 criterion 4 (no recurring unexplained residual).

**Build:**
- Read `remote_changes`, `unscoped_changed_cell_count` and the NAV residue attribution from the probe outcomes.
- Group the unexplained changes by worldline and by recorded conditions.
- A candidate is certified only on recurrence under the same conditions, and is then a role on the census (ENVIRONMENTAL FORCE).
- No probing.

**Tests:**
- Toy worlds: a scheduled change is certified, a one-off is not, and a lever's effect is never counted as a force.
- Replay reports the explained share.

**Must not:** use any world's name, colour, position or mechanic.

### WO-L3b · Scoped negatives (G6) and coverage certificates (BLOCKED on R4)

**Owner:** per R4. **Target:** M2 criterion 2 (INERT only with a certificate).

**Build:** formal negative products: board, action, conditions, evidence. A coverage certificate: the actions tried at each worldline, and when. INERT is assertable only with a complete certificate.

**Tests:** INERT without a certificate is refused. Every negative states its scope, and none is stated beyond what was tested.

### WO-L4a · Typed representation (BLOCKED on LW-B; owner: the learn-to-win chamber)

Every certified product is expressed in the typed form: the v3 draft's subset where it applies, and LW-B's role and mechanic-law compilers. Until LW-B lands, a product with no typed form is listed as owed, not failed. The census (WO-L2) is its input.

### WO-L4b · Grounding (click line)

**Owner:** Claude Alpha. **Depends on:** WO-L2. **Target:** M2 criterion 5, first part.

**Build:** a check that runs across every certified product. Every law cites the transitions that earned it, and every cited transition exists in that level's record (`gate_events`, `probe_outcomes`).

**Tests:** a dangling citation fails, and a product with no citation fails. On replay of the development records, it reports the share of grounded products.

**Size:** about 2 days.

### WO-L4c · The prospective law test (click line with the learn-to-win chamber)

**Owner:** shared. **Depends on:** WO-L4b. **Target:** M2 criterion 5, second part.

**Build:**
- A law is frozen with its decision-time inputs before a comparable decision.
- The next comparable transition grades it as confirmed or killed, with the transition cited.
- Grading never edits the frozen law.
- The win referee is **not** used; it grades win sentences only.

**Tests:** a frozen law confirmed; a frozen law killed with its transition cited; an attempt to edit a frozen law refused.

### WO-L5-00 and WO-L5 · The walked map, passive (BLOCKED on R3 and R4)

**WO-L5-00 (read-only):** mine golden `push/machine.py` and `search.py` (`virelai-golden` @ `511a6bf`) and v4's `state_tracker` and `push_fallback` (with their 22-test grader). Return a table mapping each golden dependency (worldlines, `infer_roles`, the counter seal) to its Ring 9 equivalent, or to a gap.

**WO-L5:** a re-implementation over Ring 9's entities and masked addresses:
- clicks are keyed by the worldline that owned the cell before the press;
- deaths, level-ups and resets are events, not edges;
- contradictions are reported, never averaged;
- there is **no action selection**.

**Tests:** deterministic nodes and edges on replay; counter ticks create no new states; the same click on two worldlines makes two edges; no game's data mixes with another's.

## 6 · Packages and rehearsals

| Package | Contents | Rehearsal criteria added | Submit |
|---|---|---|---|
| v2 | SUB-3, cap 1,000, slice 2,550 s (running now) | S-3, W | On a pass |
| v3 | WO-L1a, WO-L2 (+ WO-L1a-NAV if landed) | G1-a, G1-b, G1-c (WO-L1b); census written for every level played, M1 reported | On a pass |
| v4 | WO-L1c, WO-L4b, any landed L3/L4c | Diagnostic records per level; grounding share; M2 criteria per level | On a pass, before Oct 27 |

**Every package:**
- built from the Director's export of a commit on `main`;
- verified 9/9 with `main`'s verifier;
- mount-simulated 5/5;
- rehearsed under the Kaggle save run;
- graded against its own preregistered criteria;
- submitted only on a pass. Two submissions per day are allowed, and a failed run doesn't count.

## 7 · Working protocol (binding on every work order)

- **Branch:** commit on `ring9-unified`. `main` fast-forwards only after a Mac floor. Packages come from `main`.
- **Shared files:** `NOTE_SHARED_FILE_<date>.md`, naming each function, is filed before the commit. One holder at a time; a builder who needs a held file waits or files a friction.
- **The index:** each builder's day ends with a signed line at the top of `DOCUMENTATION_INDEX_2026-09-20.md`: date · seat · commits · files touched (ruling 12).
- **Tests:**
  - fail-first, against the base commit;
  - the full floor in the cloud and on the Director's Mac;
  - `--ignore=tests/test_physics_grammar_contract.py` until R5 is settled.
- **Terminal discipline:**
  - the Director runs every command, one per block, with no comment lines;
  - stage explicit paths only; never `git add -A`, `.` or `kaggle/`;
  - never reset, clean or prune a worktree;
  - push with `-c http.version=HTTP/1.1 -c http.postBuffer=157286400`.
- **Ruling 10:** no report compiler on save-run output before the answer keys are committed. The census baseline uses development records.
- **Firewall:** no game name, colour, position or mechanic in solver code, tests' logic or work orders. Held-out worlds are reported in aggregate wherever a per-world row isn't needed for a fix. Replay movies are never downloaded.
- **Disk:** about 0.8 MB per action. Every new artifact states its size per level in the work order's return.

## 8 · Risks

| Risk | Where | Mitigation |
|---|---|---|
| WO-L1a's change breaks a downstream reader that assumes the old `action_laws` | `ego_law_from_interface`, card builders | Checked at the premise step; the floor run; replays of click-world records with ACTION6 only |
| The census needs fields no ledger keeps (departed worldlines, class signatures) | WO-L2 | WO-L2-00 finds them before code. A missing field is reported as `NOT_BUILT`, never invented. |
| A shared file is held by Sol when a work order needs it | L1a, L1c | Schedule in §4. Otherwise wait, or file a friction. |
| R2 is ruled "no" | WO-L1c | L1 reduces to WO-L1a plus WO-L1a-NAV; the census reports foundation gaps honestly |
| LW-B is not delivered before the freeze | WO-L4a | L4a's products are listed as owed; M2 criterion 5 stays unmet on those laws, and the report says so |
| The disk projection from v2's rehearsal is too high for a 1,000-action cap | packages v3, v4 | Lower the cap or slim the per-action records before v3; decided on v2's W criterion |
| The census becomes a second belief writer | WO-L2 | Read-only module; a test asserts it writes no gate product or journal entry |

## 9 · Reporting

**Each work order returns** a signed `<WO>_RETURN_v1_<date>.md`:
- the premises checked, at file:line;
- the tests, failing before and passing after;
- the floor;
- the exit evidence;
- the artifact sizes;
- anything found that belongs to another line or another altitude.

**Each rehearsal** gets a review graded against its criteria. **Each Friday,** and at the freeze, a `STATE_OF_THE_DUCK_BUILD` update carries M1 and M2 as numbers.

— Claude, Alpha build seat (click line), 2026-10-09
