# Build slice R9-R18 (G9-A): carried levers, graded by the next level

**Revision label:** `R9-R18`
**Date:** 2026-10-01
**Author:** Claude (Alpha build seat), signed
**Base:** `e4371e7` (R9-R17).

**Governing rulings (Director, 2026-10-01):**
- Carry hypotheses only.
- G0–G2 run again on each level.
- Each carried lever is re-confirmed by a probe.

**Sources:** `MINE_CROSS_LEVEL_AND_CROSS_DEATH_v1` §4, L2 and L3. Ported from virelai_v4 `library/cross_level_identity.py`:
- type identity, never instance or position;
- the scale-normalized shape;
- "a type-matched carry is trusted only after one behavioural re-confirmation probe".

**Altitude:** code-level. One design choice is flagged for the Chief Engineer below: the re-confirmation probe is G3's own click, not an extra press.

## What it does, in plain terms

1. **Freeze.** When a level ends, each lever's *type* is frozen with it, along with *where its reaction landed*:
   - the type is its integer plus its shape with scale removed;
   - the reaction is on the lever itself (LOCAL), elsewhere on the board (REMOTE), or both.
2. **Predict at entry.** On the next level, at entry and before anything is clicked, the machine finds every object of a carried type and freezes a prediction for each: clicking it changes the counter-masked board, in the same place as before.
3. **Grade.** The level's own probes grade those predictions, at no extra action. The first click on a candidate, once G2 has certified this level's counter mask, gives:
   - **RECONFIRMED** if the board changed, in the carried locality;
   - **FALSIFIED** if nothing changed, or it changed somewhere else.

Clicks before the mask exists, and clicks on a transition that ends a life or a level, are not evidence (R9-R16, D3).

**What it does not do: it certifies no lever.** G3 still witnesses every lever on its own evidence. The carry is a test of whether the previous level's knowledge transfers, and is graded as one.

## On the live vc33 record

- **Level 1's two levers** (E0004 and E0005) are one type: solid squares of integer 9, each click rewriting cells elsewhere.
- **Level 2's spawn board**, recorded in the winning transition, holds **four** objects of that type.
- **Four predictions** are frozen at transition 26, all UNCONFIRMED.

The card's second line on level 2, verbatim:

`[carry] level 1 levers E0004, E0005 -> 4 same-type objects here (4 UNCONFIRMED); not found: none`

Level 2 was never played, so the grading is shown on a stand-in world. There, two of the squares rewrite a block elsewhere and two do nothing. Run end to end:
- the controller certifies G0–G2 on level 2;
- G3's sweep grades the four candidates: 2 RECONFIRMED (REMOTE, as carried) and 2 FALSIFIED (no masked change);
- G3 certifies the two responsive squares as levers on its own evidence;
- the ladder reaches G4-A.

## Changed

| File | Change |
|---|---|
| `inference/framework/carry.py` (new) | `scale_normalized_shape` (ported), `type_signature`, `lever_signatures`, `CarryLedger` (candidates, `observe`, `view`, `line`) |
| `inference/framework/level_model.py` | Each frozen lever carries its `signatures` (every type it showed on its level, so a lever that recolours is matched in each state) and its reaction `locality` |
| `inference/framework/virelai_gates.py` | `_build_level` builds `carry` from the level just frozen; `record_outcome` lets it grade each transition under this level's mask. Four calls folded. |
| `inference/framework/life_record.py` | `carry` is LEVEL tier |
| `inference/framework/card_builder.py` | The `[carry]` digest line |
| `inference/framework/memory_store.py` | `virelai('memory', kind='carry')` |
| `tests/test_r9_r18_carry.py` (new) | 6 tests (below) |

**Tests:**
1. Type identity ignores position and scale, but not shape.
2. The frozen vc33 level carries each lever's type and reaction.
3. Level 2 freezes 4 predictions at transition 26, before any click. They appear on the card and through the `carry` query.
4. The stand-in level 2, run end to end:
   - 2 RECONFIRMED and 2 FALSIFIED, each graded after it was frozen;
   - G3 certifies the 2 responsive squares itself;
   - the ladder reaches G4-A.
5. A click before the mask, or on a death, grades nothing.
6. The first level carries nothing, and shows no `[carry]` line.

**Fail-first check:** with the wiring reverted to `e4371e7` and `carry.py` kept, 5 of 6 failed. The shape-function test passes either way, because it tests the new module directly.

**Suite:** cloud **509 passed, 1 skipped** (510 tests). Ruff is clean on every changed file. **Mac expected: 510 passed.**

## Ratchet (non-blank, non-comment lines)

| File | R9-R17 | R9-R18 |
|---|---|---|
| `virelai_gates.py` | 5,417 | **5,413** |
| `tool_agent.py` | 2,781 | 2,781 |
| `carry.py` | — | 125 (new) |
| `level_model.py` | 96 | 98 |
| `memory_store.py` | 277 | 281 |

## For the Chief Engineer

1. **The re-confirmation probe is G3's own click.**
   - **Why:** this honours the ruling's "re-confirmed by a probe" at zero extra actions, and keeps G3 the only certifier.
   - **The cost:** a candidate G3 never clicks stays UNCONFIRMED.
   - **The alternative:** a dedicated controller press per candidate before G3. That costs one action each, and duplicates G3's own sweep.
2. **A type match can be one-to-many.** On vc33, 2 levers became 4 candidates, because the type is "solid square of integer 9" and level 2 has four of them. The prediction is per object, so each object is graded on its own.
   - **Known weakness:** this type is coarse. A single cell of integer 9 would match too.
3. **Locality is the only property carried.** Carrying exact cell counts or effect channels would have to survive level-specific geometry, and the first level-2 board shows how different that can be.
   - Orbit class (toggle, absorbing) is a candidate for R9-R19, through Duck's predictions, not the controller's.

## Next: R9-R19, G9-B (shape only)

On level L+1, Duck freezes predictions drawn from level L's description and open hypotheses, for example vc33's "E0005 undoes E0004". They are graded there, and L+1's G4-B and G4-C then close.

That slice needs a live run first: the first real level-2 board, and how the carry actually grades on it, decide its shape. My recommendation is to package R9-R18 for a live vc33 run before building R9-R19.

— Claude, Alpha build seat, 2026-10-01
