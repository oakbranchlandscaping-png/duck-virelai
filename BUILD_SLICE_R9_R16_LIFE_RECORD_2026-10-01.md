# Build slice R9-R16: the life record (cross-death memory, part 1)

**Revision label:** `R9-R16`
**Date:** 2026-10-01
**Author:** Claude (Alpha build seat), signed
**Base:** `f733333` (R9-R15).

**Governing rulings (Director, 2026-10-01):**
- Build the life record first.
- Carry only hypotheses across a level.
- Leave `tools/live_level_carry_gate.py` out of the shipped bundle.
- "Learn how to win" is recorded only.

**Source:** `MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1_2026-09-30.md` §4, port candidates D1 to D4.
**Altitude:** code-level. D3 applies an existing rule, G1's handling of a terminal transition, to G4-B and G4-C (see §D3).

## What it does, in plain terms

A death now forgets nothing and is remembered:
- every recorded transition knows which life and level it belongs to;
- a reset is a row in the record;
- a test cut off by a death (or a level change) no longer counts as evidence;
- every piece of the gate machine's state is declared as either kept for the whole game, kept for one level, or in flight.

## D1: a reset is a recorded row, and every row knows its life and level

**New module, `inference/framework/life_record.py`:**
- `LifeRecord` tags each transition-index row with `kind` (PROBE or RESET), `life` and `level`.
- It notes when a life ends by GAME_OVER, and any level change in a life.
- It records each harness reset as a `RESET` row, which opens the next life.
- It also holds the machine's high-water transition. That replaces `_high_step` from R9-R14.

**Duck can see it:**
- **The `lives` query:** `virelai('memory', kind='lives')` lists each life: its level, its transitions, how it ended, and its reset.
- **Recalled facts:** after a death, each fact in the recall slot says which life it is from.
- **The budgets on the card:** they now show the current `life`.

## D2: every reset is delivered once, from G0 on

**The defect:** `observe_system_reset` returned `None` before G2 had certified a counter. The agent marks a reset delivered only when the return value is not `None`. So a reset before G2:
- was delivered again every turn;
- reached G3's ledger late, once G2 closed.

**The fix:** the first delivery always records the row and returns it. G3's ledger still receives the reset only when G2 is certified. A repeat delivery returns `None`.

## D3: a G4-B or G4-C test cut off by a death or a level change is not evidence

**The defect:** a prediction taken on a transition that ended a life or a level was graded anyway:
- on a level change, against the *next level's* board, which shows up as about 2,800 cells changing "elsewhere";
- then recorded toward missing conditions.

G1 already treats such a transition as indeterminate (`ego_verification._indeterminate_boundary`). G4-B and G4-C did not.

**This matters now, not later.** R9-R17 freezes level L's record and carries it forward. A contradiction graded against level L+1's board would then become a false falsification.

**The fix:**
- **The status:** such a prediction is **INDETERMINATE**. It is neither graded nor noted, and it does not count toward the rule that every lever must be pressed in a graded prediction.
- **The card:** it lists the prediction under `cut_off_by_death_or_level`.
- **Duck:** may predict the same press again.
- **G4-C:** an indeterminate law test neither certifies nor reopens G4-B. A level change still closes the study, as before.

## D4: every field has a declared persistence tier

`PERSISTENCE` in `life_record.py` declares every attribute of the gate machine and of all eight gate targets as one of three tiers:

| Tier | Meaning |
|---|---|
| **GAME** | The whole game, across lives and levels |
| **LEVEL** | One level, across its lives. Frozen as the level's model at a level change (R9-R17) and carried only as hypotheses (ruling 2026-10-01). |
| **TRANSIENT** | An in-flight probe or answer, resolved by its own outcome or boundary |

A test fails if any field is undeclared. This is the table R9-R17 freezes from.

The declaration describes behaviour that already holds: the machine lives for the whole game, and a reset clears nothing. It invents no new carry.

## Changed

| File | Change |
|---|---|
| `inference/framework/life_record.py` (new) | `LifeRecord`, `PERSISTENCE`, `undeclared` |
| `inference/framework/virelai_gates.py` | `self.lives` replaces `_high_step`; rows are tagged; `observe_system_reset` delivers once (D2). Three statements were folded. |
| `inference/framework/memory_store.py` | The `lives` query; transitions show `kind`, `life` and `level` |
| `inference/framework/recall.py` | Recalled outcomes carry `life` after a death |
| `inference/framework/card_builder.py` | Budgets show `life` |
| `inference/framework/g4_relations.py` | `INDETERMINATE`, `void` |
| `inference/framework/g4b_gate.py` | `take` voids a terminal transition (D3); the card lists voided predictions |
| `inference/framework/g4c_gate.py` | Only a CONTRADICTED law test reopens G4-B |
| `tests/test_r9_r16_life_record.py` (new) | 6 tests (below) |

**Tests:**
1. A reset before G2 is recorded once and opens life 2 (D2).
2. On the live ft09 record (D1):
   - the death at 88 and the reset at 89 split life 1 from life 2;
   - life 1 ended by GAME_OVER;
   - the `lives` query and the card's budgets show life 2;
   - recall of E0056, the lever pressed in both lives, shows facts from life 1 and life 2.
3. On the live vc33 record, its level change at 26 is recorded (D1).
4. A G4-B prediction taken on a death is INDETERMINATE (D3):
   - it is not noted toward a missing condition;
   - it is listed on the card;
   - it does not count as pressing its lever;
   - re-predicting the same press is accepted and SUPPORTED.
5. A G4-C law test cut off by a death neither certifies the law set nor reopens G4-B; the same test then certifies it (D3).
6. Every field of the gate machine and of its eight targets has a declared tier (D4).

**Fail-first check:** with the seven changed files reverted to `f733333`, all 6 tests failed. With them restored, all 6 pass.

**Suite:** cloud **497 passed, 1 skipped** (498 tests). Ruff is clean on every changed file. **Mac expected: 498 passed.**

## Ratchet (non-blank, non-comment lines)

| File | R9-R15 | R9-R16 |
|---|---|---|
| `virelai_gates.py` | 5,425 | **5,422** |
| `tool_agent.py` | 2,781 | 2,781 |
| `memory_store.py` | 258 | 268 |
| `g4b_gate.py` | 361 | 366 |
| `g4_relations.py` | 300 | 307 |
| `life_record.py` | — | 112 (new) |

## What this does not do

- **No masked state graph and no walk back to the frontier (D5).** These cost actions and were never proven live. They are left for later, by plan.
- **No level freeze.** That is R9-R17.
- **No live run needed.** Everything here is proven on the two live exit records.
- **The packaging ruling waits for the next package.** That package's packager leaves `tools/live_level_carry_gate.py` out of the shipped source and checks that it is absent.

— Claude, Alpha build seat, 2026-10-01
