# Mining: cross-death memory ("Groundhog Day") and cross-level carry ("learn how to win")

**Date:** 2026-09-30
**Author:** Claude (Alpha build seat), signed
**Kind:** read-only mining inquiry (WO-00 discipline). It makes no rulings and changes no code.
**Feeds:** stage M-6 of `DESIGN_VIRELAI_MEMORY_v2_2026-09-29` ("Design document for G9 carry and cross-level memory").

**What was mined:**
- the full repo snapshot (rings 6 to 8.0 `virelai_v4`, all ring8 Duck-hybrid stages);
- `virelai-golden`;
- the top-level docs;
- Ring 9 at R9-R15.

**Citation convention:**
- `v4:` means `variants/ring8.0/ARC3-Inference/virelai_v4/`. The cited files are byte-identical in ring6 to ring8.0, except `context.py`.
- `R9:` means `variants/ring9-cybernetic-gates/ARC3-Inference/`.

## 1. Bottom line

- **The prior art is real code with no live proof.**
  - On cross-death, V4's persistence design is careful and portable.
  - On cross-level, the capture and identity-matching code is solid.
- **No document shows any of it measurably helping on a later level.**
  - The best case was one ring8 run with "one level-1 win… no level-2 win".
  - The ontology run of 25 games scored "no game completed level two".
- **Two prior rulings already set the shape:**
  - V4 WO-LB-01: carry *seeds, never verdicts*. An inherited belief is a suspicion until a probe re-earns it.
  - Memory design v2, M9: a level's model persists across lives on that level, freezes at level end, and carries as hypotheses until G9 re-confirms them.
- **Ring 9 already runs half of "learn how to win" on every level win, and nothing reads it.** At each win it writes a win capsule and a level lesson. The gate machine never consumes either.

## 2. Cross-death: what exists

### V4 "Groundhog Day"

**The mechanism is persistence by not resetting.**
- One `VirelaiContext` lives for the whole game.
- Every field is assigned to one of four tiers (`v4:context.py:12-42`, `735-816`):
  - lives and levels;
  - lives, reset at a new level;
  - per life;
  - per frame.
- On GAME_OVER, the code clears only the per-life tier (`reset_for_new_life`, `v4:context.py:937`).

**Survivors are keyed by:**
- the masked board hash (`v4:cybernetic/state_tracker.py`);
- the spawn region (`v4:library/library_sync.py`).

**What it changes after a reset:**
- Already-probed objects are skipped.
- Untested actions are preferred.
- A masked state graph (`record`, `untried`, `open_set`, `plan_to_frontier`; `state_tracker.py:125-345`) walks recorded edges back to the frontier, one action per frame, verifying each step.

**Life boundaries are excluded from evidence.** A death is not evidence about a button (`v4:weave/action_roster.py:65-110`, `life_boundary_edges`).

**Status:**
- Role evidence accumulating across 5 lives was proven offline only (`WO_GROUNDHOG_DAY_01_AUDIT_RETURN`).
- The frontier return is unit-tested only.
- The serializer has no callers.

### Golden

The record covers the whole game and is never wiped inside a game. Each node carries `life` (`vg:golden/substrate/record.py:1-25`, `146`), and the sweeps derive "already tried" from the record.

### Ring 9 today

**What it has:**
- harness resets reach the G3 ledger (`R9:virelai_gates.py:5113`);
- identity carry by exact spawn match;
- ruling D4: a lever study cut off by a death on the same level is re-studied up to 2 times (`R9:g4_guided.py:53-67`), proven live twice on ft09.

**What a reset loses:**
1. **Resets before G2 are dropped.** `observe_system_reset` returns `None` if there is no counter product.
2. **Resets never become a recorded row.** The memory store has no `life` field, so recall cannot say "last life, this happened".
3. **No state graph and no frontier.** `MaskedStateArchive` (`R9:masked_world_state.py:97`) has no (state, action) edges.
4. **Death-crossing edges count as evidence.** G1 ego coverage and the G4 limits/relations do not exclude them.
5. **No declared persistence tiers.** What the gate machine keeps across a life or a level is implicit.

## 3. Cross-level: what exists

**Win capsule** (`R9:virelai_win_capsule.py:20-97`; written at `R9:virelai_runtime.py:678-691`).
- **What it records:** an observed win, holding the level root, attempt root, pre-win frame, winning render and successor spawn, each by reference and SHA.
- **What it refuses:** to infer a cause.
- **vc33 exit run:** written correctly. It credited the actor as DUCK, which was a provenance bug, fixed in R9-R15 (F-R3).

**Level lesson** (`R9:virelai_lessons.py:111-215`).
- **What it records:**
  - the winning action;
  - the cell rewrites;
  - the earlier uses of the same action that did not win;
  - supported or untested hypotheses.
- **vc33:** the same action failed 7 times before it won, so "the win needs context beyond the action" is SUPPORTED.
- **Not persisted:** the enrichment, which holds the object-level separator and type matches, runs in a background thread and is never saved.

**"Learn how to win"** (`_minimal_separator`, `R9:tools/compile_post_win_grammars.py:101-111`).
- **What it finds:** the smallest set of up to 3 regions whose state tells the winning moment apart from every earlier failure of the same action.
- **How it is hedged:** "a candidate necessary context, not a proven cause".
- **What it never did:** produce a tested, forward-looking predicate.
- **Audit verdict:** "MINE contracts; new evidence-linked compiler required".

**Identity across levels.**
- **What it matches on:** type only, the pair (integer class, scale-normalized shape) (`v4:library/cross_level_identity.py:70-112`).
- **What it does not match:** instances or positions.
- **V4 level advance** (`v4:library/substrate/level_advance.py`):
  1. snapshot the beliefs;
  2. rebuild from the new level's starting board;
  3. seed matched types at a clamped prior (sigmoid 0.7), strictly below "typed";
  4. leave role and mechanism to be re-earned by probing.

**Ring 9 wiring.**
- **Still running:**
  - the win capsule and the lesson are written on every level win;
  - query handlers exist for them.
- **Never consumed:**
  - the gate machine reads neither;
  - in gated mode the automatic card is empty (`R9:tool_agent.py:1551-1556`);
  - `ladder_end` stops the run on the first turn after a level change.

**Firewall finding (for you).** `R9:tools/live_level_carry_gate.py:23-29` hard-codes a winning click sequence for one named world.
- **What I checked:** no solver code imports it (grep), so the live vc33 win did not come from it.
- **The risk:** it ships in every Kaggle bundle's `src/`, and it is game-specific content inside the shipped tree.
- **Recommendation:** remove it from the shipped tree in the next package.

## 4. PORT candidates, smallest first (none contains world content)

| # | Mechanism | Source | Ring 9 seam | Risk |
|---|---|---|---|---|
| D1 | A reset as a recorded row with a `life` index | golden `record.py:146` | `observe_system_reset` plus the memory store's transition index | Double counting when a re-derivation reads the whole record (the Groundhog Day audit's lesson) |
| D2 | Resets delivered before G2 as a life boundary | v4 `virelai.py:876-964` | `observe_system_reset` (drop the G2 guard; only G3 needs the counter) | Low |
| D3 | Death-crossing edges excluded from evidence | v4 `action_roster.py:65-110` | G1 coverage, `g4_limits`, `g4_relations` | Low |
| D4 | A persistence-tier table plus a test that checks every field is listed | v4 `context.py:735-816`, `937` | The gate machine's and the G4 targets' mutable fields | It is an audit, not a feature; it must not invent new carry |
| D5 | Masked state graph and a verified walk back to the frontier | v4 `state_tracker.py:125-345` | Built on the G2 mask; the walk is a controller procedure | Costs actions; hidden state; never proven live |
| L1 | Freeze `LevelModel(L)` at a level change | M9; v4 `level_advance.py:98-130` | A new G9 target, opened where `ladder_end` stops today | It must not carry verdicts |
| L2 | Match by type signature to the next level's starting board, giving carry candidates marked UNCONFIRMED | v4 `cross_level_identity.py:70-112` | `EntitySighting.integer/cells` over the frozen lever products | One type can match several objects |
| L3 | Re-confirmation probe: one press, then compare the reaction with the carried anatomy and orbit class | v4 `cross_level_identity.py:114-122` (its 20-cell threshold replaced) | `controller_executor.next_owned_step` | Each probe costs one action |
| L4 | Win context candidate (minimal separator over Ring 9's own lever regions) | `compile_post_win_grammars.py:101-111` | Read from the frozen `LevelModel` plus the capsule | It must stay a hypothesis, never a goal |

## 5. Proposed slice ladder (firmness falls with distance)

- **R9-R16, the life record (cross-death foundation).** D1 + D2 + D3 + D4.
  - **Exit:** the ft09 exit record replays with a life-2 boundary at transition 88, recall can say what happened in the last life, and G1 and the G4 limits/relations evidence exclude the death-crossing edge.
  - Everything is offline; no live run is needed.
- **R9-R17, level freeze.** L1.
  - At a level change, the G4 products, the capsule and the lesson freeze into `LevelModel(L)` in the target journal.
  - `ladder_end` hands over to G9 instead of stopping.
  - **Exit:** the vc33 exit record replays to a frozen level-1 model.
- **R9-R18, G9-A carry candidates.** L2 + L3.
  - The controller re-confirms each carried lever on level L+1 with one press.
  - **Exit:** on vc33's level-2 starting board, carried levers are matched or reported NOT_FOUND, and each match is RECONFIRMED or FALSIFIED.
  - This needs a live run, because the level-2 board exists only live.
- **R9-R19, G9-B carried relations (shape only).**
  - Duck freezes predictions on L+1 derived from L's description or open hypotheses, for example vc33's "E0005 is E0004's inverse".
  - They are graded there, and then L+1's G4-B and G4-C close.
- **Later:** D5 (frontier walk) and L4 (win context candidate). The firmness of these is low.

## 6. Rulings this needs (for you, and Apex where marked)

1. **Order.** My lean: R9-R16 (life record) first. It is small, it needs no live run, and both directions need boundaries as recorded rows. G9 follows.
2. **What carries across a level** (for the Chief Engineer). Only hypotheses (M9, "seeds never verdicts"). G0 to G2 re-run on each level, with carried products as candidates. This matters because golden records the counter's refill value changing at a level-up.
3. **G9's store** (for the Chief Engineer). The gate machine rebuilds `LevelModel` from its own record and reads the runtime's capsule only as a cross-check. That fits phase sovereignty: the belief state is the brain, and the runtime is an observer.
4. **"Learn how to win" in this campaign** (plan level; Apex). It records a falsifiable win-context hypothesis only. Seeking the win stays behind the win wall.
5. **A new exit, preregistered before any run** (plan level). For example: on each world, the first level whose G4 completes yields a COMPLETE law set, and at least one carried relation is graded on the next level.

— Claude, Alpha build seat, 2026-09-30
