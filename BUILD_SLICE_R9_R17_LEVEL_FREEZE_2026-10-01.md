# Build slice R9-R17: the level freeze, then the ladder runs again on the next level

**Revision label:** `R9-R17`
**Date:** 2026-10-01
**Author:** Claude (Alpha build seat), signed
**Base:** `40fdcb2` (R9-R16).

**Governing rulings (Director, 2026-10-01):**
- Carry only hypotheses across a level: G0–G2 run again on each level, and nothing carried is a verdict.
- "Learn how to win" is recorded only.

**Sources:**
- `MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1` §4, L1;
- `DESIGN_VIRELAI_MEMORY_v2` M9 ("when a level ends, its model is frozen as a finished level model");
- the port precedent, virelai_v4 `library/substrate/level_advance.py` (snapshot, then rebuild from the new level's spawn).

**Altitude:**
- **Code-level:** the freeze and the rebuild.
- **Architectural, flagged for the Chief Engineer:** a level change no longer ends the run.

## What it does, in plain terms

When a level ends, the machine freezes everything it established about that level into `LevelModel(L)`. It then starts the ladder from G0 on the new level's board.

Before this slice, a level change ended the run ("cross-level work (G9) is not built"). That is how the live vc33 run stopped after winning level 1.

The new level starts empty. Only two things show the previous level:
- **On the card:** one line marked *unconfirmed here*;
- **In memory:** the `levels` query.

Matching the previous level's levers on the new board and re-confirming them is G9, which is R9-R18.

## The freeze (`inference/framework/level_model.py`, new)

`freeze_level` builds the frozen model from the gate machine's own certified products and record. It does not use the observer's win capsule; the belief state is the only brain. The model holds:

- **Every certified product of the level, whole:** G0 through G4-C, whatever was reached.
- **A lever roster:** each lever's click, effect channels, orbit class, and study status (EXPLAINED, INTERRUPTED or NOT_STUDIED).
- **Each lever's G4-A study as it stood:** runs, states and status. This is what G9 will re-confirm against.
- **The level's lives, and Duck's uncertified notes.**
- **The win, if the level was won:**
  - the winning transition, action and probe;
  - the lever whose click it was;
  - every earlier use of the same action on that level that did not win.

  If such earlier uses exist, the win needed more than the action, so the model records the hypothesis WIN_NEEDS_CONTEXT_BEYOND_THE_ACTION with status **UNTESTED**. Nothing seeks it (ruling: record only).

**On vc33, from its own record:**
- E0005's click at (32,60) won level 1 at transition 26.
- The same click had not won 7 times before: at transitions 9, 10 and 21–25.

That matches the observer's independent level lesson for the same run.

## The rebuild (`virelai_gates.py`)

**Two new methods:**
- `_build_level` is extracted from `__init__`. It builds every LEVEL-tier field (R9-R16's table) fresh. `__init__` calls it once; a level change calls it again.
- `_advance_level`, triggered from `record_outcome` when a transition changes the level:
  1. freezes the level into `machine.levels`;
  2. rebuilds the ladder from the new level's board (the lossless after-board of that transition).

**What survives a level change:** the GAME-tier fields: the whole-game record, the lives, the frozen levels, the capability secret, and the protocol.

**Guard:** without a lossless after-board, nothing is rebuilt, and `ladder_end` stops the run as before.

## Memory and card

- **`virelai('memory', kind='levels')`:** each frozen level, compact (no whole products), marked "UNCONFIRMED on this level".
- **Site and subject recall cover the current level only.** A level-1 object is not the level-2 object at the same cell; the ring8 audit records this lesson. The whole-game record (`kind='transitions'`) still lists every level.
- **The digest's first line on level 2**, verbatim from vc33:

  `[prior] level 1 (frozen, unconfirmed here): E0004 ABSORBING, E0005 interrupted; G4 reached G4.2-LEVER-ORBITS; won at t26 by ACTION6(32,60) on E0005, same action failed 7x before (context mattered, UNTESTED)`

- **Controller refusals are per level.** The refusal key is (gate, revision, level), so a refusal on level 1 cannot block the same gate and revision on level 2.

## Replay (`record_replay.py`)

**The gap:** live, Duck explains a finished lever while G4-A still has probes to run. Replay held every such answer until the gate demanded one. So on vc33 the replayed level froze *before* E0004's explanation, while the live run had it at transition 20.

**The fix:** `_submit_ready_answers` answers a lever as soon as the gate offers that lever's template, as Duck does live.

## Changed

| File | Change |
|---|---|
| `inference/framework/level_model.py` (new) | `freeze_level`, `level_line`, `compact` |
| `inference/framework/virelai_gates.py` | `_build_level` (extracted), `_advance_level`, `levels`. Five calls were folded. |
| `inference/framework/life_record.py` | Tiers for `levels` and the rebuilt fields; a game starts on level 1 |
| `inference/framework/memory_store.py` | The `levels` query; site and subject recall cover the current level |
| `inference/framework/card_builder.py` | Prior-level lines in the digest |
| `inference/framework/record_replay.py` | `_submit_ready_answers` |
| `inference/framework/controller_executor.py`, `inference/agent/controller_turn.py` | The refusal key includes the level |
| `tests/test_r9_r17_level_freeze.py` (new) | 6 tests (below) |
| `tests/test_g4_phase1_boundary.py`, `tests/test_no_legal_move.py`, `tests/test_r9_r15_replay_fidelity.py` | Updated: the level-1 study is read from the frozen level, and the ladder is on level 2. The old "closed, asks nothing" state is kept as the guard path. |

**New tests, all on the live vc33 exit record:**
1. Level 1 is frozen from the machine's own record. It holds the 6 products, E0004 EXPLAINED as ABSORBING, and E0005 INTERRUPTED at (32,60).
2. The win is recorded: t26, E0005, 7 earlier failures, an UNTESTED hypothesis.
3. The run does not stop. The machine is on level 2 at G0, the controller owns the next step, nothing from level 1 is carried as a product, and every field is declared.
4. Level 2 runs G0 to G3 on its own board. A stand-in world is used, because the real level 2 exists only live. The controller certifies G0, G1 and G2 and sweeps level 2's objects in G3; every row is tagged level 2.
5. Memory:
   - the `levels` query returns the frozen level;
   - a level-1 site has no level-2 recall;
   - the whole record keeps all 26 transitions;
   - the card shows the prior-level line within budget.
6. ft09, which has no level change, freezes nothing and stops through G4-C as before.

**Fail-first check:** with the code reverted to `40fdcb2`, all 6 failed. Test 6 failed only because `machine.levels` did not exist yet; it pins unchanged behaviour.

**Suite:** cloud **503 passed, 1 skipped** (504 tests). Ruff is clean on every changed file. **Mac expected: 504 passed.**

## Ratchet (non-blank, non-comment lines)

| File | R9-R16 | R9-R17 |
|---|---|---|
| `virelai_gates.py` | 5,422 | **5,417** |
| `tool_agent.py` | 2,781 | 2,781 |
| `memory_store.py` | 268 | 277 |
| `record_replay.py` | 229 | 244 |
| `level_model.py` | — | 96 (new) |

## Live behaviour this changes (for review before the next run)

1. **A level change no longer ends the run.** On vc33 the run would continue on level 2:
   - G0 to G2 again, with zero model calls;
   - G3 sweeping level 2's objects;
   - G4 studying its levers;

   all within the same 200-action and 10,800-second budget per world. This is architectural, and I'm flagging it to the Chief Engineer: it is the intended consequence of building toward G9, but it changes what a run spends.
2. **The boundary wake gives Duck one turn at the new level's G0.** The level change is a boundary event, so Duck sees the prior-level line once. That costs one Duck turn per level change.
3. **Level 2 can be won by accident too.** The same G4-A study can complete level 2, which would freeze it and start level 3. That is the design (study, freeze, move on). It also means the score can rise with no win-seeking, and the review must not credit that to the model.

## What this does not do

- **No carry, no matching, no re-confirmation.** That is R9-R18: match level L's levers on level L+1 by type signature, then re-confirm each with one press.
- **No win-seeking.** The win is a recorded, untested hypothesis.
- **The vc33 hard-coded tool:** the next package's packager leaves it out (ruling 2026-10-01).

— Claude, Alpha build seat, 2026-10-01
