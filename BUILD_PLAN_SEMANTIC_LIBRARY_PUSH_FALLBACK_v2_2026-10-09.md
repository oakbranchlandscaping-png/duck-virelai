# Build plan: the full semantic library first, the Push deferred (v2, 2026-10-09)

**Type:** `BUILD_PLAN_SEMANTIC_LIBRARY_PUSH_FALLBACK` · **v2** · **2026-10-09**
**Status:** proposal for the build team and Apex. It is not a ruling. It supersedes v1 (same day), which stays in place as history.
**Author:** Claude, Alpha build seat (click line), signed. Written at the Director's request: "I want the full physics grammar and semantic library."
**Read against:** `ring9-unified` @ `e917f75`. Its runtime is SUB-3 `fc152e6`, with a floor of 630 passed, 1 skipped. The plan also uses:
- the v1 rehearsal of `ring9-submission-v1` (2026-10-08);
- the review of v1 given to the Director on 2026-10-09.

**Canon read for this plan:**
- `CONCEPT_VIRELAI_SOLVER_v2` §4–5;
- `SPEC_SOLVER_LOOPS_v2` §6–7;
- `RULING_PUSH_ORACLE_v1`;
- `SYNTHESIS_AUD_CAMPAIGN_v1` (W5);
- `BUILD_PLAN_PORTS_AND_PILLARS_v1` (A-1);
- `RULINGS_PORT_AND_PILLARS_v1` (R-2, R-7);
- `RULING_G4_CONTROLLER_FIRST_v2` (G-5);
- `RULINGS_CONSOLIDATION_v2` (rulings 6, 10 and 13).

**Game-free.** No world's mechanics or win condition appears here. Where a world is named, it is named only as the source of a measured count.

---

## 0 · In one paragraph

The mission is the full physics grammar and semantic library for each level. Canon defines "full" exactly: every present object roled, dossiered and characterized, bounded by budget. The Push comes after that, as canon requires. It fires on a complete library, and the library is what prunes its frontier.

This version therefore defers the Push as an actor. It builds four things toward a full library, in order of how much each adds:
1. **L1:** a gate that gets stuck closes on its own (`UNRESOLVED`, with what it tested), and the ladder moves on. Today the whole level drops to free play.
2. **L2:** a census of every object on the board, each with a role status and its evidence. This makes "full" a number.
3. **L3:** the missing chapters of the library: environmental forces (G5) and scoped negative knowledge (G6).
4. **L4:** every certified product is written as a typed grammar sentence.

**L5**, recording the walked map passively, is a later port. The Push returns when the census says a level's library is full.

## 1 · What "full" means, and how it is measured

**The definition.** A level's library is full when every object present on the board has three things:
1. a **role status**, with its evidence;
2. a **dossier** of what it was observed to do;
3. its **mechanics stated as grammar sentences**: effects, couplings, forces, and scoped negatives.

Every gate on the ladder must also have closed with a stated disposition. Canon bounds this by budget, so the honest form of "full" includes the gaps: an object never reached is listed as `UNKNOWN` with a reason, never left out.

"Full" does not mean physics that was never observed. A level whose library stops short says where, and why.

**The measure.** The census (L2) turns this into numbers per level:
- objects roled, out of objects present;
- objects `UNKNOWN`, with their reasons;
- gates closed, by disposition;
- the share of observed cell changes that the library explains: by the agent's action, the counter, a lever, or a force;
- the remaining unexplained residual, as a count of cells and events.

A claim that a library is full cites these numbers, or it is not made. This is the guard against the project's characteristic failure: prose that runs ahead of evidence.

## 2 · What changes from v1

| v1 element | v2 decision | Reason |
|---|---|---|
| Gated Push (`PUSH-FRONTIER`) after "current obligations bounded" | **Deferred** | Canon fires the Push on a complete library, and the library prunes its frontier. v1 had no pruning step. Under v1's own readiness rule, the Push would have started on about 3 of the 36 games in the rehearsal. |
| Ranking untried actions by the open question they test | **Dropped** | Proven prior art (golden `push/`) orders by coverage and shortest route. This would be an untested replacement for it. |
| Route following, bounded resets, completeness certificates (P4) | **Deferred**, with the Push | Needed only when the Push acts |
| P3, "complete semantic capability", gating everything live | **Split into L2–L4** | Each slice runs live as it lands; none waits for all the others |
| P2, the map as an observation | **Kept as L5**, a later port | Canon keeps the walked map "throughout play". It belongs to the library and only reads the record. The source to port exists: `virelai-golden` `golden/push/machine.py` (207 lines) and `search.py` (120 lines), commit `511a6bf`. The duck-virelai copy is an empty placeholder. |
| Amend R-2 / G-5 (Push before free play) | **Not requested now** | Free play stays the fallback. L1 asks a narrower change (§6). |
| Split R-7 (the Push before learn-to-win) | **Not requested now** | Unnecessary while the Push is deferred |
| P0, repair free-play feedback | **Done** | SUB-3 `fc152e6`, Mac floor 630 passed, 1 skipped |

v1 got these right, and they carry forward unchanged:
- gates close as `NOT_APPLICABLE` or `UNRESOLVED` with their tested scope, never with a manufactured law;
- a different result from the same action in the same state raises an alarm and is never averaged;
- every action is receipted GATED or FREE_PLAY;
- the only wins are observed ones;
- the definition of "full" excludes physics never seen.

## 3 · The evidence behind the order

From the rehearsal of `ring9-submission-v1`: 36 of 110 clones played, every one of the 25 worlds at least once.

| Measure | Count |
|---|---|
| Games that reached free play | 23 of 36 |
| Rests to free play after a controlled stop (D-3) | 19, in 18 games |
| … of which at G1 | **12** |
| … at G2, G3, G4.2, G4-C | 2, 2, 2, 1 |
| Games whose whole ladder closed normally into free play | 2 |
| Levels cleared | 6, on 5 clones. In 3 of the clears (2 newly cleared worlds, plus the first level of the world that was already clearing), the level was finished in free play after a rest. |

**The reading.** The library is most often cut short at G1. Duck's explanation turn loops; the stop rests the whole level in free play; and G2 to G4 never run. That loses the counter, the levers and their laws for that level.

So no amount of capability added at G5–G7 helps a level that never gets past G1. Getting more levels through the ladder (L1) adds more to the library than any new gate does, and it comes first.

## 4 · The slices

| Slice | Deliverable | Exit evidence | Owner (proposed) | Size |
|---|---|---|---|---|
| **L0** | SUB-3: free play reports its outcome to Duck; the sandbox host logs what it hides | Done: `fc152e6`, floor 630/1. The v2 rehearsal is grading it now (S-3). | Claude Alpha | done |
| **L1** | **A stuck gate closes and the ladder moves on.** A controlled stop at gate Gk (contract repair loop, no-progress loop, route retries exhausted) closes Gk `UNRESOLVED`. It keeps the products and the tested scope Gk has so far, and the ladder advances to the next gate. Free play takes the level only when no gate can act. This includes **ruling 6**: G1's explanation never holds up the first action; the controller's G1 probes run first. | Fail-first tests replaying the rehearsal's G1 loops, at 0 actions and after some actions: the ladder reaches G2 with G1 recorded `UNRESOLVED`. A second stop on the same level still ends in bounded free play. Every downstream product carries the caveat in §6. A canary on development worlds against v2, on the same clones. | Claude Alpha (click gates G0–G4.x). Shared files need a `NOTE_SHARED_FILE` first. | 3–4 days |
| **L2** | **The object census.** One product per level: every object on the board, each with exactly one status (EGO, COUNTER, LEVER with its type, INERT with tested scope, AMBIGUOUS in the mu bucket, or UNKNOWN with a reason), its evidence references, and the §1 numbers. It reads the products the gates already make. | Every roster object appears exactly once, with a status. The totals add up. A planted unreached object shows as `UNKNOWN`, not missing. The counts are deterministic on replay of development records. | Claude Alpha, with Sol for NAV objects | about 2 days |
| **L3a** | **G5, forces, read from the record.** Cell changes that the agent's action, the counter and the levers do not explain become force candidates. A candidate is certified only when the same pattern recurs under the same recorded conditions. It reads fields the record already carries (`remote_changes`, `unscoped_changed_cell_count`, the NAV residue attribution). | Planted toy worlds: a scheduled change is certified, a one-off is not, and a lever's effect is never counted as a force. Replay of records: the share of explained changes is reported per level. | Apex to assign (not in the ownership table) | 3–5 days for record-only |
| **L3b** | **G6, scoped negatives.** What was shown not to happen, and under which conditions, as formal products. The scoped nulls of the G3 inventory are the first source. | Each negative names its scope (board, action, conditions) and its evidence. None is stated beyond what was tested. | Apex to assign | 2–3 days |
| **L4** | **Grammar sentences.** Each certified product (ego, counter, lever type, orbit, relation, law, force, negative) is emitted in `SPEC_PHYSICS_GRAMMAR_v2`'s typed form at the moment it is certified. | Every product in a replayed level has a sentence that the grammar's referee admits. A product without a sentence is a failing test. | The grammar, compiler and world report belong to the learn-to-win chamber. The emitting hooks are Claude Alpha's ("report hooks"). | Depends on the compiler's delivery |
| **L5** | **The walked map, passively.** First a read-only mining pass (WO-00) over golden `push/` and v4's `state_tracker` and `push_fallback` (with their 22-test grader). Then a port onto Ring 9's masked addresses. Clicks are keyed by the object that owned the clicked cell, never by coordinate. Deaths, level-ups and resets are recorded as events, not moves. It never selects an action. | Deterministic nodes and edges on replay. Counter ticks create no new states. The same click on two objects makes two edges. A different result from the same action raises an alarm. No game's data mixes with another's. | Apex to assign | about 3 days |

**Deferred, and the condition for returning:**
- the G7 Push as an actor;
- route following and bounded resets;
- the completeness certificate;
- the `RULING_PUSH_ORACLE` W5 amendment.

They return when the census shows full libraries on a meaningful share of levels, and L5's map is in place. At that point the library prunes the map's frontier, as canon requires.

## 5 · Measurement

**Reported per level, in every run from L1 on:**
- the census numbers (§1);
- each gate's disposition: `SATISFIED`, `UNRESOLVED` with its scope, or `NOT_APPLICABLE`;
- which gates ran downstream of an `UNRESOLVED` one, and on what caveat;
- the free-play share of actions, and its reason;
- levels cleared, actions per cleared level, and the mode each clear happened in.

The score is a lagging indicator. Each slice is judged first by what it adds to the library:
- **L1:** more levels reach G2–G4.
- **L2:** fullness becomes measurable.
- **L3:** the explained share rises.
- **L4:** every product is a sentence.

**Baseline.** The census run on the v2 rehearsal's output, if Apex rules that ruling 10 allows it (§6). Otherwise, the census run on the existing development-world records.

## 6 · Decisions needed

1. **Adopt this plan in place of v1.** For the Director, through Apex.
2. **L1 changes how D-3 works** (Apex). A controlled stop closes the stuck gate `UNRESOLVED`, and the ladder continues. Today it rests the whole level in free play. Free play remains the fallback when no gate can act.

   **The architecture question inside it (CE / Apex):** canon's order of inquiry is law — ego, then counter, then levers — because an unidentified ego or counter masquerades as a lever's response. If G1 closes `UNRESOLVED`, may G2 run?

   My proposal: yes, under three conditions:
   - every product downstream of an `UNRESOLVED` gate is stamped "conditional on Gk UNRESOLVED";
   - it is never certified beyond that stamp;
   - the census counts it separately.

   This mirrors the built-depth stamp owed under `SYNTHESIS_AUD_CAMPAIGN_v1` W5. If Apex rules no, L1 reduces to ruling 6 alone.
3. **Ruling 10's scope** (Apex). Is the L2 census on save-run output a "report" that has to wait for the Director's answer keys?
4. **Owners for L3a, L3b and L5** (Apex). None is in the ownership table.
5. **`RULING_PUSH_ORACLE_v1`'s status.** Its header says "DRAFT, pending ratification"; its footer says "Director-ruled". This is not needed now, but it must be settled before the Push returns.

## 7 · Calendar (estimates)

| Window | Work |
|---|---|
| Oct 9–10 | The v2 rehearsal grades and v2 is submitted. Decisions 1–3. L1 design and fail-first tests. |
| Oct 11–14 | L1 is built, the floor is run, and L1 gets a canary on development worlds. |
| Oct 13–15 | L2 is built. |
| Oct 16–18 | Package v3 (L1 + L2), its rehearsal, and its submission |
| Oct 16–26 | L3a and L3b (first, record-only); L4 hooks once the compiler exists; L5 if an owner has time |
| Oct 27–30 | Freeze |
| Nov 2 | Final code |
| Nov 8 | Paper |

**What can be promised by 2 November:** every level of every world reports an honest census. L1 lets more levels reach G2–G4. A library that is full where the solver got through, and that says exactly where it stopped elsewhere. That is the thesis's own claim ("complete when the belief state is full, bounded by budget"), and the paper can defend it.

**What cannot be promised:** that every hidden world's library is full.

## 8 · Seams and ownership

**Shared files L1 is expected to touch.** I will confirm the exact functions at file:line before the note is filed:
- `virelai_gates.py`: the stop-to-close routing, and free play overriding everything while a level rests (`:6552`);
- `controller_executor.py`: who owns each step after a gate closes;
- `controller_turn.py`;
- `solver.py`: `_rest_after_controlled_stop`.

A `NOTE_SHARED_FILE` names each function before the commit. Work waits for Sol's open slice.

**The submission line:**
- v2 stays as packaged.
- L1 and L2 travel together in v3.
- Every package is built from a commit export and verified 9/9, with a rehearsal graded against its own preregistered criteria.

**Not read for this plan** (the device link dropped part-way): Directive v3 §4 (deferred items), the body of golden `search.py`, and the uncommitted `SPEC_PHYSICS_GRAMMAR_v3` draft. To be read before L1's design is filed.

— Claude, Alpha build seat (click line), 2026-10-09
