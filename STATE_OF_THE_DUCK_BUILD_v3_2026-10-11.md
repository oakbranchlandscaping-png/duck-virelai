# State of the Duck build (Cybernetic Duck, Ring 9): the semantic library begins to write

**Type:** `STATE_OF_THE_DUCK_BUILD` · **v3** · **2026-10-11**. Supersedes v2 (2026-10-07). v1 and v2 stay in place as history.

**True as of:**
- Local `ring9-unified` is at `7df657e`, the WO-L2a pure modules. The Director committed it on 2026-10-11.
- The worktree's remote-tracking refs still read `cd07716` for `origin/ring9-unified` and `origin/main`, so the push of `099aef9` and `7df657e` is **not recorded**.
- Local `main` is at `cd07716`.

**Working tree:** the WO-L2a hooks slice is copied in and Mac-verified (683 passed, 1 skipped) but **not committed**. Untracked files from other seats are present and are not this build's:
- the physics-grammar draft, its code and its contract test;
- the root `WO_L2A_CENSUS_INTERFACE_NOTE_v1`;
- `kaggle/`.

**Author:** Claude (Alpha build seat, click line), signed
**Reader:** any project, any new collaborator

**Game-free:**
- Worlds appear only as run labels (`kNNN`, vc33 and so on), never with their mechanics.
- This document compresses the repo. Where they disagree, the repo wins.

**Tags:**

| Tag | Meaning |
|---|---|
| **[C]** | Committed, at a cited commit or file |
| **[M]** | Mac-verified in the Director's worktree, but uncommitted |
| **[B]** | Believed, with what would settle it |

**What changed since v2.** The build's destination changed. `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v1` (Director-adopted 2026-10-10) makes the product a versioned, evidence-backed **semantic library for each world and each level**. It shelves the Push and win-seeking action selection. Ruling 22 redefines the model's role: the gate defines the admissible experiments, the controller takes the routine steps, Duck chooses only where judgment is needed, and certification comes from the record alone.

---

## 1 · The cursor (what is open now)

| Rung | Exit observable (plan §5) | Owner | Gated by (§5) |
|---|---|---|---|
| **C. Minimal live library** (WO-L2a) | Every started game writes a schema-valid, canonically hashed `world_model.json` at run end and at level boundaries. A level-entry replay and an early-stop replay each produce every observed worldline, supported roles and typed gaps. Duck sees the current goal, a compact library revision and retrieval handles. | Claude builds; Sol reviews | L-5, L-6, L-7 |
| **A/B. Foundation reliability and bounded refusal** (WO-L1a-NAV, WO-NO-REPAIR-LOOPS, then the v3 reliability rehearsal) | The v2 rehearsal's G1 cases and both G3 lifecycle sequences replay with no contract loop, crash or unsupported product. Each answer is checked once. A stuck gate closes explicitly UNRESOLVED. Full floor. | Sol for the NAV paths; Claude for click | L-1, L-2 |

**Where C stands:**

| Part | State |
|---|---|
| Schema and census | [C] at `7df657e` |
| H1 freeze and H2 reconcile-and-write hooks | [M]: Mac floor 683/1; commit pending |
| Card digest, retrieval handles, world/run manifest, human report renderer | Owed |

## 2 · Open questions for the receiving seat

1. **Director: the first scored submission.** D-4's target is about 12 October, which is tomorrow.
   - The repo records no scored submission. `REVIEW_PAPER_ALIGNMENT_v1` (2026-10-10) recommends submitting a rehearsed package now: v2, or v1, which had no crash in its rehearsal.
   - Has either been submitted? If not, that is a Director decision, and it is the only item here with a hard deadline.
2. **Director: the push.** Push `ring9-unified`, which carries `099aef9`, `7df657e` and the hooks commit once it is made. Then fast-forward `main`.
3. **Sol: unrecorded play** (`BUILD_SLICE_WO_L2A_HOOKS` §4, finding 1).
   - Gate rows exist only for gate probes and resets, so free-play actions reach H2 as `missing`.
   - Effect: the last level ends NOT_ACCOUNTED with RECORD_MISMATCH, and its observation tier stops at the last gate row.
   - Question: is free play a gap reason of its own, an accounting state, or rows the record should carry?
4. **Sol: scope of the v2 model.** It is written only in `gated` mode. Since the legacy writer became opt-in, the `observe`, `tool` and `controller` modes write no `world_model.json`. Confirm this, or name the modes that need it.
5. **Sol: the next Alpha slice.** Options:
   - finish C (the card digest and retrieval);
   - start the shared G3 admission design for D, which must be agreed before either line edits `virelai_gates.py`;
   - or SUB-4.

   Also, who owns the click side of G5 and the REACTIVE-DRIVEN chapter (plan §8)?

## 3 · Horizon

**Short (this week).**
- Commit and push the hooks slice.
- Finish C: the card digest and retrieval handles; the world/run manifest; the report rendered from the validated JSON; a cross-check of the census projection against the runtime's continuity tracks.
- In parallel, Sol's WO-L1a-NAV, and no repair loops on both lines.
- Then the v3 reliability rehearsal, graded against the v2 baseline: 12 G1 gate stops, 1 crash, 168/168 free-play receipts. Ruling 16's 15 % test is evaluated in that rehearsal.

**Medium.**
- **D, directed G3:** the shared admission contract. A model choice away from the roster head, and a timeout coverage choice, each become a bound one-action probe with no old-head contamination.
- **E, the full census and scoped negatives:** WO-L2b and WO-L3b (G6, coverage certificates, INERT only with a certificate).
- **The first library-package rehearsal:** graded on census coverage and gap types on every played level, Duck action yield, and controller fallback.
- **H, SUB-4:** bounded restarts in submission mode only.

**Long.**
- F and G: G5 forces, driven laws, and typed and grounded grammar with prospective checks.
- Two paper evidence runs of 25 public games each, which need separate authorization and committed answer keys (ruling 10).

| Date | Event |
|---|---|
| ~12 Oct | First scored submission (D-4), unrecorded |
| 20 Oct | The learn-to-win chamber's WO-LW-D replay-prospective result is due (claim C3) |
| 27–30 Oct | Code freeze |
| 2 Nov | Deadline |
| 8 Nov | Paper |

The minimum competition artifact is **ACCOUNTED** per played level. FILLED is the research deliverable.

## 4 · Recent frictions (this cycle, ranked)

| Friction | Altitude | Disposition |
|---|---|---|
| G3 lifecycle crash in HYBRID worlds (k008 `G3-CLOSED → AMBIGUOUS`; k013 hidden `→ PRESUMED_UNREACHABLE`): a premature CLICK-pass close, the NAV pass re-pursuing settled rows, and a stale terrain bound | code (ruling 23: release blocker) | **Resolved locally** [C] `cd07716`. Both replays complete with no crash or false lever, and the transition table is unchanged. Live confirmation is pending. |
| Click-only G1: the template explained every action as a pointer, while the validator accepts ACTION6 alone, causing zero-action contract loops (k022, k023) | code | **Resolved** [C] `dcb6ce5`, with synthetic contract tests. Live confirmation is pending. |
| `world_model.json` existed in 8 of the 33 active v2 games and 0 of the 77 that never acted; legacy queries could overwrite it | code | **Resolved** [M] by the hooks. The zero-action path and the no-overwrite rule are tested on the real `play()` path. Live confirmation is pending. |
| H1 first censused the wrong level (the life record had already moved to the next level) | code (Sol's review) | **Resolved** [C] `7df657e`: an explicit `level_before`, with a boundary replay test |
| Unrecorded free play shows as a record mismatch at H2 | architecture | **Escalated** to Sol (§2 Q3) |

## 5 · Honest ledger (known wrong or incomplete)

- **L-1** [C]. Nine v2 G1 rests in movement-capable worlds (k001, k002, k007, k014, k016, k026–k029) are undiagnosed. WO-L1a-NAV is open with Sol; its state since 2026-10-10 is not in the repo.
- **L-2** [C]. A rejected answer can still become a repair loop. WO-NO-REPAIR-LOOPS is unbuilt. In v2, 19 gate stops sent play away from the active gate.
- **L-3** [C]. No complete win. The v2 rehearsal cleared 5 levels across 4 games, with a final score of 0.00 everywhere. vc33's best live result is still 1.51 (2 of 7 levels).
- **L-4** [C]. **No scored submission is recorded.** Two packages are rehearsed (v1 at `419f4fd`, v2 at `fc152e6`).
- **L-5** [M]. The v2 world model has never run on Kaggle. The repairs to G1, G3 and the hooks are all local.
- **L-6** [M]. Census coverage is partial:
  - Certified roles are EGO, COUNTER and LEVER only.
  - INERT, environmental force, driven reactions, scoped negatives and Band 1 are `NOT_BUILT` gaps.
  - Lives are never joined.
  - There is no human report, card digest or retrieval tool yet.
  - Free-play transitions are outside the census's observation tier (§2 Q3).
- **L-7** [C]. G3's choice is bound to the roster head: `next_probe` and `validate_probe` admit one expected probe. Directed G3 is unbuilt.
- **L-8** [C]. In v2, 499 of 873 Duck turns (57 %) ended on the turn budget. The kernel log has 38 analyzer timeouts, and the mean turn was 78 s. The causes are not broken down.
- **L-9** [B]. Output size: about 2.3 GB for a two-hour rehearsal. A full-length run has not been projected against Kaggle's working disk.
- **L-10** [C]. `level_record.presses()` is click-shaped, so G4-B on NAV falls back to Duck.
- **L-11** [C]. `SPEC_PHYSICS_GRAMMAR_v3` and its code are untracked and unaccepted. The ratified v2 grammar is the baseline.
- **L-12** [B]. `INCIDENT_DOTENV_KEYS_IN_KAGGLE_BUNDLES_2026-09-27` was OPEN at v2. Its rotation is still unrecorded here.
- **L-13** [C]. Exposures are declared as in v2 L-10. vc33 results show the machinery works, never that it generalises.

## 6 · Build status (the Solver Totality, compressed)

**Tags:**

| Tag | Meaning |
|---|---|
| BUILT | Live-confirmed in a reviewed run |
| BUILT\* | Live, but with a known incomplete representation |
| LOCAL | Implemented and floor-tested, never run live |
| PARTIAL | Partly implemented |
| SPECIFIED | Designed, not built |
| NAMED-ONLY | Named, not designed |
| SHELVED | Set aside by the plan |

| Subsystem | Status | Evidence |
|---|---|---|
| Harness, packaging, verification, mount simulation | BUILT | Every package; v1 and v2 rehearsals |
| Submission mode (10 concurrent games, slices, caps, deadline) | BUILT\* | Two rehearsals; scored status unrecorded (L-4) |
| G0 action surface | BUILT | Live |
| G1 ego, CLICK | BUILT; pointer contract fix LOCAL | `dcb6ce5` |
| G1 ego, NAV | BUILT\* | Nine v2 rests undiagnosed (L-1) |
| G2 counter (find, label, mask, ignore) | BUILT | Live |
| G3 levers, CLICK (first witness) | BUILT\* | Live. Choice bound to the roster head (L-7). |
| G3 levers, NAV and HYBRID lifecycle | PARTIAL; crash fix LOCAL | `cd07716` replays |
| G4 CLICK (anatomy, orbits, relations, laws) | BUILT | Live on vc33 v8 |
| G4 NAV | PARTIAL | Waits on L-10 |
| `PLAY-NORMAL` free play with receipts (SUB-3) | BUILT | v2: 168 of 168 receipts match |
| Memory: transition record, life record, level freeze, carry, replay | BUILT | Live; replay fixtures |
| **v2 world-model schema and single writer** | LOCAL | [C] `7df657e` |
| **Level census** (tracks by level and life; EGO, COUNTER and LEVER through receipts; typed gaps; `record_check`) | PARTIAL | [C] `7df657e`; see L-6 |
| **H1 freeze and H2 reconcile-and-write hooks; legacy writer opt-in** | LOCAL | [M] hooks slice |
| Card digest, retrieval, report renderer, world/run manifest | SPECIFIED | Plan stage C |
| Directed G3 (ruling 22) | SPECIFIED | Plan stage D |
| No repair loops | SPECIFIED | Plan stage B |
| G5 forces, G6 scoped negatives and coverage, driven laws | SPECIFIED | Plan stages E and F |
| Typed grammar, grounding, prospective checks | SPECIFIED | Plan stage G; grammar v3 undecided (L-11) |
| SUB-4 bounded restart | SPECIFIED | Ruling 24 |
| G9 cross-level transfer | PARTIAL | Lever carry and level freeze are built |
| Push, win-seeking selection, `ACT_ON_GOAL` | SHELVED | Plan §1 |

**Read of the proportions.** The investigative ladder through G4 is built for CLICK and partial for NAV. The submission and evidence machinery is built. The library is now real in code: a schema, a census and the hooks. It has never run live and covers three of the role chapters. Everything that makes the library *full* is specified, not built.

## 7 · The floor

**Tests:**

| Commit | Result | Tag |
|---|---|---|
| `fc152e6` | 630 passed, 1 skipped | [C] |
| `7df657e` | 668 passed, 1 skipped, 4 xfailed (Mac, 2026-10-11) | [C] |
| The hooks slice, uncommitted | **683 passed, 1 skipped**, 0 xfailed (Mac, 2026-10-11) | [M] |

These Mac floors exclude `tests/test_physics_grammar_contract.py`.

**Best live score** [C]: vc33 1.51, 2 of 7 levels.

**v2 rehearsal** [C]: 2,966 actions, 33 active games, 5 levels cleared, 0 complete wins. It was not scored.

**No scored competition submission is recorded.**

## 8 · The Solver in one paragraph

**What it is.** The Cybernetic Duck carries the Virelai thesis onto Tufa Labs' open Duck harness. The thesis: intelligence is the efficient reduction of uncertainty about an unknown world through structured interaction.

**How it works.** A deterministic controller runs a gated ladder:
- action surface;
- ego (the control locus);
- counter;
- levers;
- lever dossiers.

The active gate names one knowledge gap and the experiments it will admit. The controller takes the routine steps. Duck, a self-hosted language model, chooses a bounded experiment only where judgment helps (ruling 22). Every transition is recorded losslessly, and only deterministic code certifies from that record.

**The product.** A per-world, per-level semantic library: every observed object, its supported roles, its dossier and laws, and every typed gap, written as one validated `world_model.json`.

**What done means in this phase:**
- **ACCOUNTED** on every played level for the competition;
- **FILLED** on development worlds for the research.

A level clear is an observation, never the criterion.

**Where to start reading:**
- `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v1_2026-10-10.md`;
- `RULINGS_CONSOLIDATION_v4_2026-10-10.md`.

— Claude, Alpha build seat (click line), 2026-10-11
