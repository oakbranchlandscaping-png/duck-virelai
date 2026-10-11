# State of the Duck build (Cybernetic Duck, Ring 9): Duck can read the library

**Type:** `STATE_OF_THE_DUCK_BUILD` · **v4** · **2026-10-11**. Supersedes v3 (same day). v1–v3 stay in place as history.

**True as of:**
- Local `ring9-unified` = `8e13e35` (the directed-exploration build plan v2 and execution plan v2); local `main` = `origin/main` = `origin/ring9-unified` = `472aa32`. The Director pushed both remote branches on 2026-10-11; `8e13e35` has not been pushed.
- The committed Mac floor at `472aa32` is 683 passed, 1 skipped.

**Working tree:** the close-out and library-view slice (`BUILD_SLICE_WO_L2A_LIBRARY_VIEW_2026-10-11`, revision 2, with bounds enforced after Sol's review) is **Mac-verified on 2026-10-11**: 84 focused tests passed, and the floor is 707 passed, 1 skipped, equal to the cloud. It awaits a separate commit before the G3 CLICK slice, whose first revision is also present in the working tree but is outside this status snapshot. Untracked files from other seats are not this build's:
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
| **[W]** | Built in the cloud and Mac-verified in the Director's worktree (707 passed, 1 skipped), awaiting its separate commit |
| **[B]** | Believed, with what would settle it |

**What changed since v3:**
- Sol ruled that canonical v2 writing stays in gated mode; a test pins it [W].
- The push is recorded.
- The hooks floor is committed.
- Sol ruled on the three hooks findings (§4).
- The library view Duck reads is built [W].

---

## 1 · The cursor (what is open now)

| Rung | Exit observable (plan §5) | Owner | Gated by (§5) |
|---|---|---|---|
| **C. Minimal live library** (WO-L2a) | Every started game writes a schema-valid, canonically hashed `world_model.json` at run end and at level boundaries. A level-entry replay and an early-stop replay each produce every observed worldline, supported roles and typed gaps. Duck sees the current goal, a compact library revision and retrieval handles. | Claude builds; Sol reviews | L-5, L-6 |
| **A/B. Foundation reliability and bounded refusal** (WO-L1a-NAV, WO-NO-REPAIR-LOOPS, then the v3 reliability rehearsal) | The v2 rehearsal's G1 cases and both G3 lifecycle sequences replay with no contract loop, crash or unsupported product. Each answer is checked once. A stuck gate closes explicitly UNRESOLVED. Full floor. | Sol for the NAV paths; Claude for click | L-1, L-2 |

**Where C stands:**

| Part | State |
|---|---|
| Schema and census | [C] `7df657e` |
| H1 and H2 hooks | [C] `472aa32` |
| `CONTROLLED_STOP` end reason; live free play verified | [W] |
| **Digest and retrieval from the validated live library** | [W]: the current goal, compact certified findings, typed open gaps and six retrieval page kinds. The digest section fits 2,500 characters whole; every page fits 3,000 and names its `next` call. |
| World/run manifest, human report renderer, "changed since" delta, continuity cross-check | Owed |

Exit C's observable on a live rehearsal: it is LOCAL until a packaged run executes it.

## 2 · Open questions for the receiving seat

1. **Director: the first scored submission.**
   - D-4's target is about 12 October. No scored submission is recorded in the repo.
   - Sol's guidance (2026-10-11): if none has been made, submit a rehearsed package (v1 `419f4fd` or v2 `fc152e6`) rather than waiting for the library work.
2. **Sol: review revision 2's bounds.**
   - Sol accepted the wiring: the separate section after the card, the amended M0 pin, and `LIVE_VIEW` validated but never written.
   - He also ruled that transition rows need no `receipt` field.
   - His two bound faults are fixed and tested on a deliberately large library (`BUILD_SLICE_WO_L2A_LIBRARY_VIEW` revision 2).
3. **Sol and the NAV line: the shared G3 admission design** (plan stage D). It must be agreed before either line edits `virelai_gates.py`. Claude's next slice is the design draft. SUB-4 stays behind it.
4. **Director: package timing.** When should a v3 rehearsal carry the G1 and G3 repairs, the hooks and the library view? It would turn all four LOCAL rows (§6) into live evidence.

## 3 · Horizon

**Short.**
- Commit the close-out and library-view slice when the Director releases the hold. It is already Mac-verified at 707 passed, 1 skipped.
- Draft the shared G3 admission design (directed G3) with fail-first cases: a model choice away from the roster head, a stale selection, a timeout coverage choice, and no false witness after an ambiguous frame.
- Finish C's remainder: the world/run manifest, the report rendered from the validated JSON, the "changed since" delta, and the continuity cross-check.
- In parallel, Sol's WO-L1a-NAV, and no repair loops.
- Then the v3 reliability rehearsal against the v2 baseline: 12 G1 gate stops, 1 crash, 168/168 receipts.

**Medium.**
- **D:** directed G3, after the design review.
- **E:** WO-L2b, the full census, and WO-L3b, G6 scoped negatives and coverage certificates.
- **The first library-package rehearsal:** census coverage on every played level, Duck action yield, and controller fallback.
- **H:** SUB-4.

**Long.**
- F and G: forces, driven laws, and typed and grounded grammar with prospective checks.
- Two 25-game paper evidence runs, which need separate authorization and committed answer keys.

| Date | Event |
|---|---|
| ~12 Oct | Scored submission (D-4), unrecorded |
| 20 Oct | WO-LW-D due |
| 27–30 Oct | Code freeze |
| 2 Nov | Deadline |
| 8 Nov | Paper |

## 4 · Recent frictions (this cycle, ranked)

| Friction | Altitude | Disposition |
|---|---|---|
| "Free play goes unrecorded" (hooks finding 1) was inferred from a development-record replay that stops at its last recorded gate answer | code: an evidence error in the build seat's own finding | **Resolved by test, no code change** [W]. Sol required a live-path reproduction first. Live free play is recorded, receipted and ACCOUNTED, and the row needs no `receipt` field. Lesson: a replay's stop is not a live run's record. |
| The library view's first version promised bounds it did not enforce: a 50,702-character digest and a 237,607-character object page on a large library | code | **Resolved** [W] in revision 2, before any Mac run (Sol's review) |
| A controlled stop that ended the run was persisted as `RUN_END` | code | **Resolved** [W]: `CONTROLLED_STOP` when a turn ends the run; a stop that rests the gates resumes and is not the end reason (Sol, ruling 3) |
| G3 lifecycle crash in HYBRID worlds; click-only G1 contract loop | code | **Resolved locally** [C] `cd07716`, `dcb6ce5`; live pending |
| `world_model.json` absent in most v2 games; legacy overwrite | code | **Resolved** [C] `472aa32`; live pending |

## 5 · Honest ledger (known wrong or incomplete)

- **L-1** [C]. Nine v2 G1 rests in movement-capable worlds are undiagnosed. WO-L1a-NAV is open with Sol.
- **L-2** [C]. Repair loops are still possible; WO-NO-REPAIR-LOOPS is unbuilt.
- **L-3** [C]. No complete win. In v2, 5 levels were cleared across 4 games, with a score of 0.00. vc33's best live result is 1.51.
- **L-4** [C]. No scored submission is recorded.
- **L-5** [C]/[W]. The v2 world model and the library view have never run on Kaggle. The G1, G3, hooks and view work is all LOCAL.
- **L-6** [C]. Census coverage is partial:
  - roles: EGO, COUNTER and LEVER only;
  - INERT, force, driven reactions, scoped negatives and Band 1 are `NOT_BUILT` gaps;
  - lives are never joined;
  - there is no report renderer;
  - the digest shows the revision but not yet what changed.
- **L-7** [C]. G3's choice is bound to the roster head. Directed G3 is unbuilt; its design is next.
- **L-8** [C]. In v2, 57 % of Duck turns ended on the turn budget, and the kernel log has 38 analyzer timeouts. The causes are not broken down. The library view adds 1–5 s to a Duck turn after the record changes [W, measured on development records].
- **L-9** [B]. Output size for a full-length run has not been projected against Kaggle's disk.
- **L-10** [C]. `level_record.presses()` is click-shaped, so G4-B on NAV falls back to Duck.
- **L-11** [C]. `SPEC_PHYSICS_GRAMMAR_v3` and its code are untracked and unaccepted.
- **L-12** [B]. The rotation of the dotenv-incident keys is unrecorded.
- **L-13** [C]. Exposures are declared as in v2 L-10.

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
| Harness, packaging, verification, mount simulation | BUILT | Every package |
| Submission mode | BUILT\* | Two rehearsals; scored status unrecorded |
| G0 action surface; G2 counter; G4 CLICK; memory and replay | BUILT | Live |
| G1 ego, CLICK | BUILT; pointer contract fix LOCAL | `dcb6ce5` |
| G1 ego, NAV | BUILT\* | L-1 |
| G3 levers, CLICK | BUILT\* | Roster-head binding (L-7) |
| G3 NAV and HYBRID lifecycle | PARTIAL; crash fix LOCAL | `cd07716` |
| G4 NAV | PARTIAL | L-10 |
| `PLAY-NORMAL` free play with receipts | BUILT | v2: 168 of 168 receipts. Live-path recording into the census is verified [W]. |
| v2 schema and single writer | LOCAL | [C] `7df657e`; `LIVE_VIEW` [W] |
| Level census | PARTIAL | [C] `7df657e`; L-6 |
| H1 and H2 hooks; legacy writer opt-in; gated-only writing | LOCAL | [C] `472aa32` |
| `CONTROLLED_STOP` end reason | LOCAL | [W] |
| **Library digest and retrieval** (the current goal, certified findings, typed gaps, six page kinds) | LOCAL | [W] `library_view.py` |
| World/run manifest; report renderer; revision delta | SPECIFIED | Plan stage C |
| Directed G3; no repair loops | SPECIFIED | Plan stages B and D |
| G5, G6, driven laws; typed grammar | SPECIFIED | Plan stages E–G |
| SUB-4 | SPECIFIED | Ruling 24 |
| G9 cross-level transfer | PARTIAL | Lever carry and level freeze |
| Push, win-seeking selection, `ACT_ON_GOAL` | SHELVED | Plan §1 |

**Read of the proportions.** The library now writes itself and can be read by Duck, in code. None of it has run live, and it covers three of the role chapters. The next value comes from directed G3, which makes Duck's reading of the library change what it does, and from a rehearsal that turns the LOCAL rows into evidence.

## 7 · The floor

**Tests:**

| Commit | Result | Tag |
|---|---|---|
| `472aa32` | **683 passed, 1 skipped** (Mac, 2026-10-11, excluding `test_physics_grammar_contract.py`) | [C] |
| The close-out and library-view slice, revision 2 | **707 passed, 1 skipped** (Mac and cloud, 2026-10-11) | [W]; separate commit pending |

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

The active gate names one knowledge gap and the experiments it will admit. The controller takes the routine steps. Duck chooses a bounded experiment only where judgment helps (ruling 22). Every transition, gated or free, is recorded losslessly, and only deterministic code certifies from that record.

**The product.** A per-world, per-level semantic library, written as one validated `world_model.json`. Duck reads it each turn as a compact digest, with paged retrieval.

**What done means in this phase:**
- **ACCOUNTED** on every played level for the competition;
- **FILLED** on development worlds for the research.

**Where to start reading:**
- `BUILD_PLAN_SEMANTIC_LIBRARY_DIRECTED_EXPLORATION_v2_2026-10-11.md`;
- `EXECUTION_PLAN_SEMANTIC_LIBRARY_v2_2026-10-11.md`;
- `RULINGS_CONSOLIDATION_v4_2026-10-10.md`.

— Claude, Alpha build seat (click line), 2026-10-11
