# Build plan: a semantic library for each novel world

**Date:** 2026-10-10  
**Status:** Director-adopted build directive, 2026-10-10; no runtime change is made by this document  
**Supersedes in priority:** `BUILD_PLAN_SEMANTIC_LIBRARY_PUSH_FALLBACK_v3_2026-10-09.md` and its `EXECUTION_PLAN_SEMANTIC_LIBRARY_v1_2026-10-09.md`. They remain the history and source of work-order detail.  
**Binding decisions already recorded:** `RULINGS_CONSOLIDATION_v4_2026-10-10.md` (15–24), especially 22–24; R-1 and R-2 in `RULINGS_PORT_AND_PILLARS_v1_2026-10-04.md`.  
**Baseline:** Ring 9 SUB-3 (`fc152e6`); Kaggle save rehearsal `ring9-submission-v2`. No scored result is inferred from it.
**Paper-alignment input:** `REVIEW_PAPER_ALIGNMENT_v1_2026-10-10.md` in the main checkout. Its proposed rulings 23–27 are requests, not recorded decisions; numbers 23 and 24 already belong to the ratified consolidation.

**Operating split (Director, 2026-10-10):** Sol supervises the build, sets slice boundaries and reviews evidence against this plan. Claude Alpha performs granular coding and test execution. The owner names in the workstream table retain accountability and subject expertise under existing rulings; where a row names Sol, Claude implements under Sol's review unless the Director assigns another coder. A shared file still has one active editor at a time. Sol does not accept a slice on a builder summary alone: the changed code, fail-first evidence, relevant replay and artifact integrity must be inspected. This assignment leaves the ratified technical constraints of rulings 22–24 intact.

## 1. Destination and operating rule

The product is a **versioned, evidence-backed semantic library for each novel world and each level observed in it**. The canonical persisted artifact is the per-game `world_model.json` governed by `virelai_world_model.py`; `world_report.md` is a human rendering of that same model, never a second belief store. The gate record remains the sole certified-belief source, and the live card is a bounded projection. The library must identify the observed objects, assign supported roles, characterize their dynamics and causal relations, and state precisely what remains unknown. Its value is independent of a level clear. A win, when observed, becomes a recorded outcome and an additional source of questions; it is not the criterion for a filled library.

The Push as an actor, win-seeking action selection, and the Push handoff are **shelved**. Passive record analysis may continue where it directly improves the library. `PLAY-NORMAL` remains a bounded fallback when no gate can act, with `FREE_PLAY` receipts. No free-play transition is promoted into gated evidence by relabelling it later. R-2's paper-evidence boundary remains in force.

**Control loop:** the active gate names one knowledge gap; the controller takes routine evidence-gathering steps; Duck chooses a bounded experiment only where judgment helps; the gate admits and binds that experiment before execution; Virelai records the result; deterministic code certifies only supported conclusions; Duck reads the updated library. The model may propose a hypothesis or action, but its assertion never writes certified belief.

G1 asks for the control locus. G2 asks for the counter and its trigger, including action-dependent changes. G3 asks for levers. G4 grows each lever's dossier. G5/G6 and the remaining taxonomy cover forces, driven reactions and scoped negatives. The earliest **actionable** gate is the current goal; a missing prerequisite never becomes a certified downstream product.

## 2. What the library contains

One per-world manifest names the world identity and every independent run; evidence stays scoped to its game, level and life. Use an authoritative world ID when the runner supplies one. Otherwise, group exact opening-board and action-roster matches under a **provisional** fingerprint for reporting only; identical openings do not prove identical mechanics. A clone may suggest a hypothesis for another run, but it cannot donate that run's verdict. Each level has a frozen library revision at its boundary and a current revision while play continues.

| Library component | Minimum content | Source and rule |
|---|---|---|
| Object census | Every observed worldline, present or departed, once; sightings, class signature and change history | Read-only projection of the entity ledger and level record, including early-stop paths; compiled into `world_model.json` |
| Parent and roles | Band-1 STATIC, REACTIVE or unsettled; set-valued roles among EGO, COUNTER, LEVER, ENVIRONMENTAL FORCE, REACTIVE-DRIVEN and INERT | Each role has evidence and scope. A class change revokes the old role set. INERT is exclusive and needs a coverage certificate. UNKNOWN is a gap, never a role. |
| Dossiers | For every supported role: witnessed states, interventions, outcomes, conditions, limitations, contradictions and next questions | G1/G2 products and G3–G6 records. One attributed activation with masked residue enters a lever at G3; G4 adds repeat behavior, orbit, mechanism and conditions. |
| Laws | Typed, immutable sentence; subject/class; conditions; predicted or explained change; evidence references; test status | Prose renders the typed claim. Grounding and prospective checks are distinct; the win referee grades win sentences only. |
| Gaps and residuals | Unanswered archetype questions, why open, budget and reachability limits, unexplained changes | Explicitly distinguishes not tested, inconclusive, contradicted and impossible to test under the current scope. |
| Provenance | Action chooser, admitting gate, GATED/FREE_PLAY receipt, bound target, before/action/result frames, level/life and source transition IDs | Certification checks provenance before using a transition. No cross-game or cross-level evidence leak. |

The card shows a compact **library digest**, not the full artifact: active goal; current admissible choice when Duck is needed; newly certified findings; contradictions and top open gaps; remaining budget. A bounded retrieval tool serves the full object, dossier and evidence pages. A new library revision is shown after a change; unchanged prose is not repeated on every turn. The canonical JSON has one schema and validator; if Band-1 tags, typed gaps or coverage fields cannot fit schema v1 without weakening it, version the schema explicitly in the same slice and retain a migration reader. Render the human report from the validated JSON.

## 3. Honest completion states

These statuses are emitted per level and aggregated per novel world. They are not synonyms.

1. **ACCOUNTED:** every observed worldline appears in the census, every gate has a disposition, and each missing role or law is a typed gap. This is the old M1. It is useful even when the level is interrupted.
2. **CHARACTERIZED:** foundations are certified (or their absence is certified); every worldline has a supported role set or a scoped, evidenced unresolved status; lever dossiers and every recurring change have a causal explanation or a named unresolved residual; all current findings are grounded. Open gaps remain visible. This is a progress measure, not a claim of fullness.
3. **FILLED:** every observed worldline has a supported role set or coverage-certified INERT; no open archetype question remains in the declared observation scope; the six archetype chapters and applicable mechanic subtrees are covered; every recurring change is explained by a supported law or bounded with a falsifiable exception; all certified laws have typed form, grounding and a prospective status. A budget stop or an unresolved foundation cannot be FILLED.

The artifact declares its **scope**: observed boards, actions available, probe classes covered, conditions tested, level and life boundaries, and remaining unseen frontier. A coverage certificate states which declared classes and conditions it exhausted; it does not assert that every conceivable coordinate or hidden state was tried. FILLED is a claim about that declared scope, never about unobserved hidden states. A later contradictory observation reopens the affected dossier and changes the status. The per-world summary reports each level's status, rather than calling a world filled because one level was filled.

## 4. Starting point and gaps

The v2 rehearsal executed 2,966 environment actions in 33 active games. The controller executed about 92% of actions, while 873 Duck turns averaged about 78 seconds; 499 ended on the turn budget and only 217 executed a Duck step. Deterministic work is therefore valuable, and model calls are scarce. SUB-3 repaired free-play feedback: 168 Duck free-play steps match 168 execution receipts. The run cleared five levels across four games but produced no complete win; none of these counts measures library fullness.

The path to the library is blocked at several points:

- **G1 contract and NAV loops:** 12 G1 gate stops in v2; three click-only rests arise from a pointer-template/validator mismatch, two before any action. The other nine require a NAV-path diagnosis. WO-L1a and WO-L1a-NAV address them.
- **G3 lifecycle:** `k008` crashed on `G3-CLOSED -> AMBIGUOUS`; the saved log also shows `G3-CLOSED -> PRESUMED_UNREACHABLE` in the NAV reachability path. Ruling 23 assigns the repair to Sol; the existing transition table must retain its invariants.
- **G3 choice is currently bound to the roster head:** `next_probe` supplies one expected probe, and `validate_probe` rejects other actions. To give Duck meaningful bounded choice, candidate selection, binding, validation and outcome attribution must change together.
- **No complete library feed:** the G3 entity ledger and memory store exist, but there is no per-level census from level entry through early stop, no compact live library digest, and no full G5/G6 chapters or typed grammar feed in the live path. `virelai_runtime.py` already has a `world_model.json` compiler/write path, yet only 8 of the 33 active v2 game artifact folders contain that file. The write must be invoked and verified for every game that actually begins; the current per-game human renderer is still owed.
- **Recovery and throughput:** a failed answer can become a repair loop; a free-play controlled stop currently ends the game on its second occurrence. Ruling 24 permits a bounded Duck-context restart in submission mode. The large card and long model turns must be measured, then reduced without dropping evidence.

The draft `SPEC_PHYSICS_GRAMMAR_v3` and its local code files are not yet an accepted live contract. Use the ratified v2 grammar as the baseline and integrate the draft subset only after its own tests and version decision. The gate remains the sole certified-belief writer; the census, card and grammar bridge are projections.

## 5. Workstream order and exit evidence

The table orders dependencies. Independent owners may work in parallel, but no package is called ready merely because its files compile.

| Stage | Work and owner | Dependency | Evidence to close |
|---|---|---|---|
| **A. Foundation reliability** | **WO-L1a** click-only G1, Alpha; **WO-L1a-NAV**, Sol; **R23 G3 lifecycle**, Sol with click consultation | None | Replay v2's zero-action G1 cases and both G3 lifecycle sequences. No contract loop or crash; no unsupported product. Full floor. |
| **B. Bounded refusal** | **WO-NO-REPAIR-LOOPS**, Alpha for click, Sol for NAV paths | A's failure reproductions | Each answer is checked once. Refusal is recorded; controller can supply a certified answer or gate closes explicitly UNRESOLVED after its bounded process. No rejected wording is treated as a hypothesis or as proof. No inactive prerequisite receives a downstream product. |
| **C. Minimal live library** | **WO-L2-00** source map, then **WO-L2a** census shell, world/run manifest, canonical `world_model.json` hook and card digest, Alpha with Sol on NAV identities | G1/G2 data contracts | A level-entry and early-stop replay each produce every observed worldline, supported roles and typed gaps. The shell reads the level-entry board before the lazy G3 ledger exists and reconciles later IDs without a second belief writer. Every started game writes a schema-valid, canonically hashed `world_model.json` at run end and level boundaries; the same data renders a human report. An uncertain world fingerprint never merges run verdicts. Duck sees the current goal, a compact library revision and retrieval handles. |
| **D. Directed G3** | **WO-G3-DIRECTED**, Sol for NAV admission, Alpha for click admission; single shared G3 contract | C's object IDs and A's lifecycle repair | Read-only design check first. A model choice away from the roster head and a timeout coverage choice become newly bound one-action probes before execution. `record_outcome` attributes each result to that choice, with no old-head contamination, false lever or changed GATED receipt. Routine coverage never waits for Duck. |
| **E. Full census and scoped negatives** | **WO-L2b** full per-level census, Alpha/Sol; **WO-L3b** G6 scoped negatives and coverage certificates, Alpha | C; D for model-chosen provenance | Present and departed worldlines, class changes, role overlaps and gaps are deterministic on replay. INERT without complete coverage is refused. Each negative names its board, action, conditions and evidence. |
| **F. Remaining causal chapters** | **WO-L3a** G5 force (Sol NAV, click owner to assign); **WO-DRIVEN** relay/driver laws; complete G4 lever dossiers | E and reliable G3 witnesses | A lever's effect cannot be called an environmental force. A force needs repeated, source-specific evidence under comparable conditions and a checked rival explanation; recurrence alone is a candidate. Driven laws identify both the driver and the responsive worldline. Exceptions stay scoped. |
| **G. Typed, testable grammar** | **WO-L4a** typed forms and compilers, learn-to-win chamber; **WO-L4b** grounding, Alpha; **WO-L4c** prospective checks, shared | E/F evidence and an accepted grammar version | Every certified finding has a typed sentence or an explicit owed form. Every citation resolves to this level's record. Predictions are frozen before a comparable action; a misfire kills or narrows the claim. The win referee is used only for win sentences. |
| **H. Bounded fallback** | **SUB-4**, Alpha | A/B release safety; lower priority than C–G | Submission-mode controlled PLAY-NORMAL loops may restart Duck's conversation up to three times per level only with time for another turn. Same world/library, fresh card, preserved receipts; reason and subsequent useful action recorded. Non-submission behavior remains as before. |

**L1c diagnostic observation** retains ruling 16's conditional trigger: build it if the first repaired-package rehearsal still shows at least 15% of played levels stopping at G1/G2. It stores downstream observations beside the journal, with their missing foundation; it certifies nothing until re-derived after that foundation is ACTIVE. The passive walked map remains after the freeze unless spare capacity exists, and it never selects actions.

## 6. Rehearsal and release gates

Use the same development records and clone indices as the baseline where possible. The save-run output may be inspected for runtime failures, while ruling 10 continues to govern use of answer keys and report compilation. A package has a predeclared `RUN.md` naming its criteria before the Kaggle run.

**Next reliability package:** WO-L1a, the available NAV G1 and G3 repairs, and no-repair-loop work. If an owner cannot land a slice in time, report it as open rather than silently including it. Grade G1 stops by world type and cause, actions before stop, share of played levels reaching G2/G3, G3 crashes and hidden exceptions, and all prior SUB-3 receipt checks. The v2 baseline is 12 G1 gate stops, one crash, and 168/168 free-play receipt matches. Ruling 16's 15% test is evaluated here.

**First library package:** census shell and readable card, then directed G3 only after its attribution tests. Grade census coverage and gap types on **every played level**, including early stops; model-turn latency and action yield; controller fallback on timeout; GATED action provenance; number and quality of G3 witnesses. A directed action must improve evidence without reducing coverage or inventing a lever.

**Grammar package:** G4/G5/G6 and typed grounding. Grade all six role chapters, coverage certificates, explained-change share, residuals, typed/grounded/prospectively graded law share, and ACCOUNTED/CHARACTERIZED/FILLED status by level. A no-win run can pass the library tests. A level clear cannot excuse a missing census or unsupported claim.

**Paper evidence run:** reserve two named 25-public-game, one-pass runs with full per-world slices: an early library check after WO-L1a/L2a, and a freeze run from the final evidence commit. Predeclare the exact manifest, time window, budget, source hash, grading table and expected artifact count. Commit the Director's answer keys before opening report outputs, as ruling 10 requires. The review estimates that a three-hour window and about 2.5 GPU-hours would suffice; confirm actual setup, disk and concurrency from a dry calculation before scheduling. The 110-clone, two-hour v2 rehearsal is a runtime test, not the 25-world paper sample. These runs require separate authorization and do not happen by writing this plan.

**Safety gates for every package:** exact-source export, existing verifier and floor, mount simulation, read-only artifact-integrity check, one Kaggle save rehearsal, and a graded review against the preregistered criteria. A canary for the submission-only restart must enable that mode explicitly. Keep a per-game manifest with `never_started`, `active_cancelled`, `gave_up` and `crashed`; do not count a never-started game as a failed library attempt.

## 7. Measurement and cut line

Report the following per novel world and level, then aggregate without mixing independent runs:

- objects seen; objects with supported roles; objects with typed gaps; INERT coverage certificates; departed and class-changed worldlines;
- completed, unresolved and diagnostic-only gate dispositions; GATED and FREE_PLAY action counts;
- levers witnessed, dossiers characterized, forces and driven relations supported; change-explanation share and recurring residuals;
- typed, grounded and prospectively tested laws; contradictions and reopenings;
- ACCOUNTED/CHARACTERIZED/FILLED status and the exact missing conditions;
- controller actions, Duck turns and executed actions, turn latency, time-budget cuts, restarts and time remaining.
- **Duck calls per level**, split by gate and by whether the call chose an admitted experiment, answered a semantic question, or produced no action.

The v2 speed baseline is a 78-second mean Duck turn, 499/873 budget cuts, and 217 executed Duck steps. The next package must report all three again. Shorter cards and a bounded action/experiment turn are accepted only if evidence quality holds and the action yield or time distribution improves. No turn cap is chosen from the baseline alone; measure the effect of each reduction.

Keep the existing late-October competition freeze for changes intended for that submission. **Do not describe the competition cut as the full-library finish.** The minimum competition artifact is ACCOUNTED per played level, with explicit gaps; the research deliverable is FILLED on development worlds, then measured honestly on novel worlds. If the calendar slips, preserve A, C, E and grounding ahead of optional score-oriented work. Push, win-seeking action selection and passive-map activation remain outside this build.

## 8. Interfaces, ownership and decisions still needed

- **Shared G3 contract:** Sol and Alpha agree on the candidate/probe binding interface before either edits `virelai_gates.py`. The bound record includes candidate worldline and class version, action payload, pre-action board/mask address, gate revision, purpose and token. A stale candidate is refused and reselected; its result cannot certify another candidate. Sol owns NAV-specific admission and ruling 23; Alpha owns click-specific admission. One owner integrates the shared path at a time.
- **Library ownership:** the gate machine remains the sole certified-belief writer. `library_census.py`, card builder, retrieval, report compiler and grammar bridge read its products and raw record. A hypothesis from Duck may be stored separately as uncertified. Promotion requires the gate's independent derivation and a traceable source event.
- **Grammar decision:** resolve the status and test floor of `SPEC_PHYSICS_GRAMMAR_v3` and its uncommitted implementation before making it a live writer. LW-B must name its delivery date and the exact typed forms it covers; uncovered forms are reported as gaps.
- **Remaining owner:** assign the click side of G5 and the REACTIVE-DRIVEN chapter after the G3/census interface is settled. Ruling 18 already assigns G6 to Alpha and NAV G5 to Sol if capacity permits.
- **Paper claim C3:** the level-N win → level-(N+1) lifted, frozen and graded goal is separate from ordinary L4c mechanic-law prediction. The learn-to-win chamber should return an explicit replay-prospective WO-LW-D result by 20 October on its development records, with inputs restricted to level N before freezing. If it cannot, the paper must label C3 as specified but not demonstrated. This branch does not delay WO-L1a, census or G3 attribution work, and it does not reopen Push.
- **Paper and submission decisions:** update the thesis wording to match ruling 22: certification is deterministic, experiment choice may be shared, and the controller performs routine steps. The paper review recommends an early scored submission; that is a separate Director decision, not an action authorized by this plan. Verify the competition's current submission conditions before executing it. Any new rulings need unused numbers after 24 and must identify which earlier plan priority they amend.
- **Plan adoption (Director, 2026-10-10):** the library-first priority and completion language in this document are the formal build directive. This supersedes plan v3's priority order, while preserving rulings 15–24 and R-2. Push remains shelved; any future return requires a separate request and plan.

## 9. First concrete returns

1. Alpha returns WO-L1a's failing tests, fix and replay of the v2 click-only G1 openings. Sol returns ruling 23's two lifecycle replays and its source-level repair; both lines report shared-file ownership before changing shared code.
2. Alpha/Sol return a one-page G3 admission design and fail-first cases: model choice away from the roster head, stale selection, timeout coverage selection, and no false witness after an ambiguous frame.
3. WO-L2-00 maps each library field to its current record source and gaps. WO-L2a then writes a small live JSON artifact and card digest for level entry, one witnessed lever and an early stop. Duck can retrieve the full dossier without the whole library being pasted into its prompt.
4. The first repaired-package rehearsal reports the v2 comparison and ruling 16 threshold; the first library-package rehearsal reports coverage and Duck action yield. Each result updates this plan's next package content rather than silently moving its acceptance criteria.
