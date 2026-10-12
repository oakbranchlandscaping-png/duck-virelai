# Shared-file note, 2026-10-11 (WO-G3 reset continuity: G3's entity ledger sees every reset since its seed)

**Filed by:** Claude, Alpha build seat, **before any shared edit** (ruling 9).
**Authority:**
- Sol's directive (relayed by the Director): implement option A of `DIAGNOSTIC_G3_LEDGER_FRAME_SYNC_v1_2026-10-11`.
  - Start G2 from the latest observed board, including any G1 reset.
  - When G3 builds its ledger, supply the resets since that seed, in transition order, alongside G2's outcomes.
  - Reconstruct and verify every full before and after board from the level-entry record.
  - Reject or report a broken record; never silently resynchronise.
  - Keep the work off the per-action controller path.

**Base:** `2a79081` (`ring9-unified`, local). The device worktree's `virelai_gates.py`, `entity_observation.py`, `controller_executor.py`, `life_record.py`, `tool_agent.py`, `record_replay.py`, the hybrid test and the golden fixture were verified byte-equal to the cloud tree before this edit.

| File | Function | Change |
|---|---|---|
| `inference/framework/level_board.py` (new, mine, pure) | `board_through`, `reset_frames`, `BrokenBoardRecord` | Rebuilds a full board from the level-entry board plus the level's `transition_index` rows (sparse changed cells), applied in transition order. **Every cell's recorded `before` is checked** against the rebuilt board. A missing, duplicated or contradicted row raises `BrokenBoardRecord` naming the transition and the cell. `reset_frames` returns each RESET after a given transition as a verified full lossless outcome (`site_transitions` covering the whole board), the form `EntityLedger.observe_reset` needs. |
| `inference/framework/virelai_gates.py` | `CounterGateMachine.__init__` (`:956-`) | Two new attributes: `seed_transition` (the transition its `initial_grid` is the board after) and `seed_limitations` (a broken record found while seeding). |
| same | `CyberneticGateMachine._prepare_counter_from_ego` (`:6564-6579`) | Seeds `initial_grid` with `level_board.board_through(...)`, the latest observed board including any reset, instead of `ego.current_grid()`. On `BrokenBoardRecord` it falls back to `ego.current_grid()` and records the break in `seed_limitations`. It does **not** resynchronise. |
| same | `_LeverTarget._ensure_entity_ledger` (`:3124-3150`) | After seeding the ledger from `counter.initial_grid`, it merges G2's outcomes with `level_board.reset_frames(...)` (RESETs after `counter.seed_transition`) in transition order: `observe` for outcomes, `observe_reset` for resets. On `BrokenBoardRecord` no reset is threaded; the break is appended to `ledger.limitations` and the ledger keeps the current behaviour. The new logic lives in an extracted helper; the function body is not interleaved (the ratchet). |

**Off the per-action path:** the seed runs once per level, when G2 is prepared. The merge runs once per level, when G3's ledger is first built. Neither runs per action or in the controller.

**Unchanged:**
- `entity_observation.py`: `EntityLedger.observe` still refuses a mismatched frame, so a frame mismatch is never treated as evidence and never resynchronises.
- The lifecycle and its transition table; `observe_system_reset`'s forwarding rule; the controller; NAV selection and the NAV handoff (still held); the replay compatibility guard (`2a79081`); `life_record.py` (`CounterGateMachine` is not in `PERSISTENCE`).

**Not shared** (mine): `level_board.py`; the new test file `tests/test_g3_ledger_frame_sync.py`.

## Amendment 1, 2026-10-11 (filed after the edit, in the same working session)

**`CounterGateMachine.__init__` is not changed after all** (the ratchet: it is 83 NCNB lines).
- `seed_transition` and `seed_limitations` are set on the counter only by `_prepare_counter_from_ego`, right after construction.
- `_observe_seed_stream` reads them with defaults:
  - **seed transition:** a counter built at level entry (a CLICK world, or `update_action_metadata`) has the level-entry board as its seed, so its default seed transition is `machine.carry.entry`;
  - **limitations:** none.
- **The table's `CounterGateMachine.__init__` row is withdrawn.**

**Also in `_latest_observed_board`:** G2 is prepared while G1's last outcome is being recorded, before that outcome's transition-index row is written. G1's retained outcomes after the last indexed transition are therefore applied, and verified, as in-flight rows; k008's transition 32 is one. Without them the seed is one transition stale.

## Amendment 2, 2026-10-11, filed before revision 2's edits (Sol's rulings on revision 1)

**Correction to the claim above.**
- The table said a "missing" row raises `BrokenBoardRecord`. **As built in revision 1 that was not reliable.** A missing row was caught only if a later row's recorded `before` happened to contradict the board; a missing transition whose cells no later row touches went undetected.
- Revision 2 adds a reliable check for gaps **inside** the level's record. A transition id is the game's history length (`solver.action_count = len(game_run.history)`, every executed action including RESET), so a level's executed transitions are contiguous from its entry. A gap between recorded ids is therefore an executed transition that was never recorded.
- **Still not detectable at seed time:** a trailing omission, meaning an executed transition after the last one the machine was given. Only H2's `record_check` against the execution history finds it, at the end of the run.

**Revision 2 shared edits:**

| File | Function | Change |
|---|---|---|
| `inference/framework/level_board.py` (mine) | `_level_rows`, `BrokenBoardRecord` | Rejects a gap in the level's transition ids. `BrokenBoardRecord` carries the transition id. |
| `inference/framework/virelai_gates.py` | `_latest_observed_board`, `_observe_seed_stream` | Breaks are recorded as structured items `{stage, transition_id, detail}`: `counter.seed_limitations` for the G2 seed, and a new `_LeverTarget._board_record_breaks` for the G3 reset replay. They are also written into `ledger.limitations`. |
| `inference/framework/life_record.py` | `PERSISTENCE["_LeverTarget"]` | `_board_record_breaks`: LEVEL |
| `inference/framework/library_census.py` | `compile_level` + a new helper | **Fail closed in the canonical library.** A board-record break becomes a typed `RECORD_MISMATCH` gap naming the stage and transition. Every role and scoped null resting on the stale board is moved out of `certified` into a `RECORD_MISMATCH` gap ("Is the … claim grounded?"): G2 and G3 for a seed break, G3 for a reset-replay break. Those gates' census disposition is `RECORD_MISMATCH`, not `CERTIFIED`, and accounting lists `BOARD_DISCONTINUITY`. The gate machine's own products are untouched. |
| `inference/framework/library_agenda.py` (CLICK slice, mine) | `_g3_questions`, `gate_agenda` | An untouched departed object (ledger ABSENT, lifecycle `UNTOUCHED`, no witness, no lifecycle event) is excluded from the actionable G3 agenda and counted in `departed_untouched`. One with a witness or any G3 work stays. The ledger and lifecycle keep every object. |
| `tests/test_g3_hybrid_lifecycle_replay.py` | `_drive`, the k008 fixture and tests | **Sol's ruling 2.** The k008 controller plan must equal the live action through T43. After T43 the saved actions play back as history, and the repaired planner is not held to them. A new test asserts that the T44 plan starts from the ego's true post-reset footprint. The no-crash and no-false-lever assertions through T61 are kept. k013 keeps step-by-step plan equality. |

## Amendment 3, 2026-10-11 (filed after the edits, in the same working session)

- **`library_census.compile_level`:** the accounting block (`missing`, the census's own discontinuity gap) moved **unchanged** into `_board_accounting`. This compensates the ratchet: `compile_level` goes from 64 to 61 NCNB lines. It also takes the reported breaks into account.
- **`tests/fixtures/g3_no_choice_golden.json`:** re-recorded with `tools/record_g3_no_choice_golden.py`, under Sol's ruling 1 (k008 and k013 approved in principle).
  - carry-v7's entry is unchanged, byte for byte.
  - k008 and k013 equal the repaired traces reviewed in revision 1.
  - The exact diff is `golden_diff.txt`.
