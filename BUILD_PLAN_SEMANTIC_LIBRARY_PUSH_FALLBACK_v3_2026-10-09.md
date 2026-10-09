# Build plan: the semantic library first, the Push deferred (v3, 2026-10-09)

**Type:** `BUILD_PLAN_SEMANTIC_LIBRARY_PUSH_FALLBACK` · **v3** · **2026-10-09**
**Status:** final draft for execution, subject to the Apex rulings in §8. It supersedes v2 (same day); v1 and v2 stay in place as history.
**Author:** Claude, Alpha build seat (click line), signed.

**What v3 incorporates:**
- the team review of v2, with its four corrections (§0);
- my reading of Directive v3 §4, golden `push/search.py` and the `SPEC_PHYSICS_GRAMMAR_v3` draft.

**Read against:** `ring9-unified` @ `7dfabaf`. Its runtime is SUB-3 `fc152e6`, with a floor of 630 passed, 1 skipped.

**Canon:**
- `CONCEPT_VIRELAI_SOLVER_v2` §4–5;
- `SPEC_SOLVER_LOOPS_v2` §6–7;
- `NESTED_TAXONOMY_SPEC_v5` and `FOUNDATIONAL_ARCHETYPES_v2` (in `docs/canon/`);
- `RULING_PUSH_ORACLE_v1`;
- `SYNTHESIS_AUD_CAMPAIGN_v1` W5;
- `SPEC_PHYSICS_GRAMMAR_v2` (ratified) and v3 (draft);
- `RULINGS_PORT_AND_PILLARS_v1` (R-2, R-7);
- `RULING_G4_CONTROLLER_FIRST_v2` (G-5);
- `RULINGS_CONSOLIDATION_v2` (rulings 6, 10 and 13);
- `DIRECTIVE_COMPETITION_ENDGAME_v3` §4.

**Game-free.** No world's mechanics or win condition appears here.

---

## 0 · What changed from v2

Each of the review's four corrections was checked against source before it was accepted.

| # | Review finding | Checked against | v3 change |
|---|---|---|---|
| 1 | L1 cannot simply skip an unresolved G1. | `cybernetic_targeting.py:175-182`: `TargetRouter.current()` opens a target only when every prerequisite has an **ACTIVE** product. `TargetJournal.put` refuses a product whose prerequisites are inactive. An unidentified ego contaminates counter and lever attribution; this is canon's order law. | **L1 is split.** L1a is ruling 6. L1b measures what remains. L1c allows diagnostic observation downstream with **no certified products**. The "conditional stamp" is withdrawn. |
| 2 | The census needs role sets and two meanings of "complete". | `NESTED_TAXONOMY_SPEC_v5` §2: the role tag is set-valued (ego plus lever is legal); INERT excludes every other role; the tag depends on the object's class signature and is revoked when that changes. Band 1 (STATIC or REACTIVE) is the parent tag. Six archetypes, including **REACTIVE-DRIVEN** and **ENVIRONMENTAL FORCE**. UNKNOWN is the absence of evidence, never a leaf. `FOUNDATIONAL_ARCHETYPES_v2` §6: INERT can be asserted only on a coverage certificate. | **L2 is rewritten.** Every observed worldline gets a Band-1 tag and a supported role set. Unknowns become explicit, typed gaps. Two milestones replace one "full": M1, the inventory accounted for, and M2, the library ready for the Push. |
| 3 | L4's acceptance uses the wrong referee. | The v3 draft §4: the referee grades **win** sentences against observed wins and comparable non-wins. It cannot certify an ego law or a force. Ratified v2 states sentence forms in prose, and the typed subset exists only in the v3 draft. | **L4 is split into three checks:** typed form, grounding in cited transitions, and a prospective law test. The win referee applies to win sentences only. |
| 4 | The delivery promise is smaller than the goal. | The v2 calendar | **Milestones M1–M3**, each with exit criteria and owners (§2). |

**Two more changes, from my own reading:**
- **L5 is kept, as a passive map.** The review supports building the walked map before the Push acts, and canon keeps the map "throughout play". But golden's Push machine is assigned to `ACT_ON_GOAL` (R-7, `BUILD_PLAN_PORTS_AND_PILLARS_v1` A-1), and Directive v3 §4 defers further ports. So L5 needs a narrow Apex carve-out (§8).
- **The census baseline uses development records** until the Director's answer keys are committed. That avoids the ruling-10 question about save-run output.

## 1 · The decision

The mission is the full physics grammar and semantic library for each level. In canon's terms: every object roled, dossiered and characterized, bounded by budget.

**The Push as an actor is deferred** until the library can constrain it. Canon fires it on a complete library, and the library prunes its frontier. When it returns, it may prune only actions predicted by a law that was certified, with its witnesses, and frozen strictly before the decision (v3 draft §4).

Free play stays the fallback when no gate can act. Every action keeps its GATED or FREE_PLAY receipt, and wins are observed, never sought.

## 2 · Milestones: what "complete" means, and when

Three different claims, never conflated.

| Milestone | Meaning | Exit criteria, per level | Target |
|---|---|---|---|
| **M1 · Inventory accounted for** | Every observed worldline is in the census, with what the library supports about it and what it does not know | 1. Every worldline observed on the level (present or departed) appears exactly once, with its class signature and its Band-1 tag (STATIC, REACTIVE, or "not yet settled"). 2. Each has a supported role set (possibly empty), with evidence references for every role. 3. Each gap is typed and named: the archetype question not yet answered, and why (not reached, budget, foundation unresolved, class changed). 4. Every gate's disposition is recorded. 5. The share of observed changes explained, and the unexplained residual, are reported. | **Every level of every world, by 2 Nov.** This is the competition deliverable and the paper's evidence. |
| **M2 · Library ready for the Push** | The library is complete enough to constrain a frontier | 1. The foundations are certified, not conditional: EGO (or ego with no body on the grid) and COUNTER (or certified absent). 2. Every worldline has a non-empty supported role set, or INERT backed by its coverage certificate; **no open gaps.** 3. Every LEVER's question tree is closed or bounded-stopped: type, cycle of states, relations. 4. No recurring unexplained residual; any remaining one-off changes are listed. 5. Every certified law passes L4's three checks. 6. No product is built on an unresolved foundation. | **Measured on development levels by 2 Nov.** No promise for hidden worlds. |
| **M3 · Full semantic library** | The thesis target | M2, plus the full archetype question trees, forces, REACTIVE-DRIVEN relays and their driver laws, conditional mechanics, and the typed role and mechanic-law compilers (LW-B) | **After the competition.** Owners named here, built on the paper's timeline. |

**A census full of gaps satisfies M1 and never M2.** M2 is the only handoff condition for the Push.

## 3 · The evidence behind the order

From the rehearsal of `ring9-submission-v1` (36 of 110 clones played, every one of the 25 worlds at least once):
- 23 of 36 games reached free play.
- Of 19 rests to free play after a controlled stop, **12 were at G1**.
- Two of those G1 stops came at action 0: Duck's explanation was rejected before any evidence had been gathered.
- Only 2 games closed their whole ladder normally.

So the library is cut short most often at G1, and partly because Duck is asked to explain before it has gathered evidence. Ruling 6 removes that cause directly. That is why L1a comes first and is measured before anything else changes.

## 4 · The slices

| Slice | Deliverable | Exit evidence | Owner | Size |
|---|---|---|---|---|
| **L0** | SUB-3: free play reports its outcome to Duck; the sandbox host logs what it hides | Done: `fc152e6`. The v2 rehearsal grades S-3. | Claude Alpha | done |
| **L1a** | **Ruling 6:** evidence comes before Duck's explanation. The controller's G1 probes run before Duck is asked to explain G1, and Duck's explanation can never be a precondition for the first action. | Fail-first tests replaying the rehearsal's zero-action G1 stops: the controller's probes execute before the first explanation turn, and no G1 contract loop can occur at 0 actions. Floor run. | Claude Alpha (click gates). `NOTE_SHARED_FILE` first. | 2 days |
| **L1b** | **Measure.** Which G1 stops remain after L1a, by cause | A rehearsal (package v3) graded on G1 dispositions: stops by cause, actions before the stop, and the share of levels reaching G2 compared with v2 | Claude Alpha | the rehearsal |
| **L1c** | **Diagnostic observation past an unresolved foundation.** When G1 (or G2) closes UNRESOLVED, later gates may *observe*: record transitions, sightings and residuals as evidence. They may **not** put products into the journal, and they certify no law. The router is unchanged; diagnostic evidence lives beside the journal. It can be promoted only by re-derivation after the foundation is established. | Router tests: no target opens on an inactive prerequisite. Diagnostic records carry their missing-foundation reason. A later ACTIVE foundation re-derives from them, and nothing is promoted silently. | Claude Alpha. The architecture is ruled by Apex (§8). | 3 days |
| **L2** | **The census** (M1's instrument). Per level: every observed worldline, present or departed, with its class signature, Band-1 tag, supported role set, evidence references and typed gaps. INERT only with a coverage certificate, and it excludes every other role. A class change revokes and re-derives the role set. The census is also the **read-only feed** that the v3 draft §3 requires from the gate's entity ledger: one product, two consumers, no second belief writer. | Replay of development records: every worldline appears exactly once; overlapping roles are represented; INERT without a certificate is refused; a planted unreached object shows as a typed gap; the counts are deterministic. The baseline is on development records (§0). | Claude Alpha, with Sol for NAV worldlines | 2–3 days |
| **L3a** | **ENVIRONMENTAL FORCE (G5), read from the record.** Changes not explained by the ego, the counter or a lever become force candidates on the worldline that changed. A candidate is certified only on recurrence under the same recorded conditions, and becomes a role tag in the census. | Toy worlds: a scheduled change is certified, a one-off is not, and a lever's effect never counts as a force. On replay, the explained share is reported per level. | Apex to assign | 3–5 days |
| **L3b** | **Scoped negatives (G6) and coverage certificates.** What was shown not to happen, with its scope. The coverage certificate that INERT requires: which actions were tried, and when. | Every negative names its board, action, conditions and evidence. Every INERT in the census cites a certificate. | Apex to assign | 2–3 days |
| **L4a** | **Typed representation.** Every certified product is expressed in the typed form: the v3 draft's subset where it applies, and the role and mechanic-law compilers when LW-B delivers them | A product with no typed form is a failing test, until its form is named as owed by LW-B | The learn-to-win chamber (LW-B). Claude Alpha supplies the gate-side feed (L2). | depends on LW-B |
| **L4b** | **Grounding.** Every law cites the transitions that earned it, and every cited transition exists in the record | Each law is traced to the record; a dangling citation fails | Claude Alpha (gate side) | 2 days |
| **L4c** | **The prospective law test.** A law is frozen with its inputs before a decision. Later transitions grade it; they never edit it. A miss kills it. | Toy and replay: a frozen law is graded on the next comparable transition; a misfire is killed with its transition cited | Shared: learn-to-win chamber and Claude Alpha | 3 days |
| **L5** | **The walked map, passive.** First a read-only mining pass (WO-00) over golden `push/` (`machine.py`, `search.py`) and v4's `state_tracker` and `push_fallback`. Then a re-implementation over Ring 9's entities, not a copy: golden's version rests on its own object tracking, role inference and counter mask. Clicks are keyed by the worldline that owned the cell before the press. Deaths, level-ups and resets are events, not edges. It never selects an action. | Deterministic nodes and edges on replay. Counter ticks create no new states. The same click on two worldlines makes two edges. Contradictions are reported, never averaged. No cross-game mixing. | Apex to assign, after the carve-out (§8) | 3–4 days |

**The win referee** (`win_referee.py`, learn-to-win chamber) applies only to win sentences, and only after an observed win.

**Deferred:**
- the G7 Push as an actor;
- route following and bounded resets;
- the completeness certificate;
- the W5 amendment to `RULING_PUSH_ORACLE`.

They return when M2 holds on a meaningful share of development levels and L5 is in place.

## 5 · The submission line

| Package | Contents | Timing |
|---|---|---|
| v2 | Being rehearsed now | Submitted on a pass |
| v3 | L1a and L2 (the census written as an artifact) | Its rehearsal is L1b's measurement |
| v4 | L1c and the first L3/L4b pieces | If they land before the freeze |

Every package is built from a commit export, verified 9/9, and rehearsed against its own preregistered criteria.

## 6 · Measurement

**Reported per level, from v3 on:**
- the M1 numbers;
- the M2 criteria met and missed, by criterion;
- gate dispositions;
- diagnostic-only evidence (L1c), with its missing foundation;
- the free-play share of actions, with reasons;
- levels cleared, actions per cleared level, and the mode of each clear.

The score is a lagging indicator. Each slice is judged by the M1 and M2 numbers it moves.

## 7 · Calendar (one click-line builder; estimates)

| Window | Work |
|---|---|
| Oct 9–10 | The v2 rehearsal is graded and v2 submitted. Apex rules on §8. L1a fail-first tests. |
| Oct 10–12 | L1a built and floor run |
| Oct 12–15 | L2 built and floor run. Package v3, its rehearsal (= L1b) and its submission. |
| Oct 15–19 | L1c |
| Oct 19–24 | L4b; L4c with the learn-to-win chamber; the L3a/L3b owners' work in parallel |
| Oct 24–26 | Package v4, if ready |
| Oct 27–30 | Freeze |
| Nov 2 | Final code. **M1 on every level; M2 measured on development levels.** |
| Nov 8 | Paper |

**L5** runs in parallel only if Apex grants the carve-out and assigns an owner. **M3** continues after the competition.

## 8 · Rulings needed (Apex, Director)

1. **Adopt v3** as the build plan.
2. **L1c's architecture.** Downstream gates may observe after an unresolved foundation, but put no products into the journal and certify no laws. Their evidence is promoted only by re-derivation once the foundation is ACTIVE.
3. **The L5 carve-out from R-7.** The walked map may be recorded passively, before `ACT_ON_GOAL` opens, with no action selection. Its activation as the G7 Push stays under R-7.
4. **Owners:** L3a, L3b, L5, and the learn-to-win chamber's LW-B delivery date for L4a.
5. **One-tree friction.** The learn-to-win chamber's uncommitted grammar files (`physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, `test_physics_grammar_contract.py`) sit in the shared worktree. They should be committed or held on a short-lived branch, so that floor runs need no hand exclusions.
6. **`RULING_PUSH_ORACLE_v1`'s status.** Its header says DRAFT; its footer says Director-ruled. To be settled before the Push returns.

## 9 · Seams

**Shared files L1a is expected to touch:** `virelai_gates.py` (G1 ordering), `controller_executor.py` (step ownership) and `controller_turn.py`. The exact functions are confirmed at file:line before a `NOTE_SHARED_FILE` is filed. The work is scheduled around Sol's open slice.

**L1c's router guarantee** is a test, not a promise: `TargetRouter.current()` and `TargetJournal.put` are unchanged.

— Claude, Alpha build seat (click line), 2026-10-09
