# WO-L2a interface note, amended (v2)

**Type:** `INTERFACE_WO_L2A_WORLD_MODEL_V2` · **v2** · **2026-10-10**. It supersedes v1. v1 stays in place as history.
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- `REVIEW_WO_L2A_INTERFACE_2026-10-10` (Sol): its answers to Q1–Q3 and its six corrections;
- `REVIEW_WO_L2_00_CENSUS_ARCHITECTURE_2026-10-10`.

**Base:** `ring9-unified` @ `099aef9`. Its code equals `cd07716`.
**This slice:** the pure schema and census modules, with their tests. **No shared file is edited.** The hooks slice files its `NOTE_SHARED_FILE` first (§6).

**A second interface note exists in the worktree root:** `WO_L2A_CENSUS_INTERFACE_NOTE_v1_2026-10-10.md`. It is untracked, it is not this one, and Sol did not review it. It is a different type-name, so the version chain does not cover it. It counts the 77 zero-action games as never started; the evidence in §5 contradicts that. I recommend the Director archive it, or rule which note binds. This v2 is the reviewed line.

## 1 · Answers adopted

| Question | Adopted answer |
|---|---|
| Q1: a G3 witness | **LEVER is certified by its G3 witness** before the inventory, with its witness and discovery refs. `inventory_status` (`PENDING` or `ACCEPTED`) is a separate field. The role itself is never "pending". No mechanism, repetition or condition is inferred from the one witness. |
| Q2: gap reasons | **`IDENTITY_UNRESOLVED` and `RECORD_MISMATCH` are added.** A record mismatch makes the level `NOT_ACCOUNTED` and lists the missing, extra and renamed IDs. A role whose evidence lies on an unmatched transition drops to a gap. |
| Q3: the path | **`virelai/<run_stem>/world_model.json` is the only canonical path.** The old compiler serves queries **in memory and writes no file by default.** It is renamed `_observer_world_model()` in the hooks slice. A v1 file written by it exists only through an explicit opt-in diagnostic, `world_model_legacy_v1.json`, and never overwrites v2. Existing v1 files stay readable through `world_model_v2.read_world_model`. |

## 2 · Corrections adopted

### Life identity

- Track IDs are `O-L{level}-P{life}-{E|R<t>|T<t>}-{sha12(class, cells)}`, so every track belongs to exactly one level and one life.
- A track reborn at a reset carries `possible_correspondence`: the earlier-life tracks with identical spawn pixels. **It is never joined to them.** It also carries an `IDENTITY_UNRESOLVED` gap.
- Level boundaries carry no identity.

### Counter identity

- COUNTER is the certified **mask** (`subject: "MASK"`, its law version and cell count, with witness and demonstration refs).
- An observation track binds to it only when **one** track's sighting at a **mask witness transition** has exactly the mask footprint. Otherwise the identity is `UNRESOLVED`, with a gap.
- Objects that merely overlap the mask never become COUNTER. A multi-component mask has no object identity.

### Entry provenance

- The entry board is `{"source": "INITIAL_FRAME"}`, or `{"source": "LEVEL_ENTRY", "after_transition": t}` after a level change.
- The validator refuses a `transition_id` on the entry, transition 0 as a receipt, and any sighting that cites an unrecorded transition.

### Gate state and identity joins

- **The census never changes gate state.** It does not call G3's `_ensure_*`, `snapshot()`, `inventory_view()` or `next_probe*`. The embodied ego binding is computed on a shallow copy, because `compile_nav_control_map` memoizes onto the ego (`nav_control.py:266`). The tests show that call does mutate the original.
- **A track joins a G3 entity only on an exact, one-to-one match** of `(time, integer, cells)`. The time is G3's seed point (`counter.observed_through_step`) for seeds, and the birth transition otherwise. Ambiguous ledger entities abstain.

### Write ownership

- `world_model_v2.write_canonical` is the only writer. It validates, seals, writes a sibling file and replaces atomically, and it **never raises**.
- On failure it returns `ok=False` with the error, removes its temporary file and leaves the previous file untouched. The caller records `WORLD_MODEL_V2_WRITE_FAILED` without masking the original exception.
- Frozen levels and the open level go in one artifact (`compile_world_model(..., frozen_levels=...)`).

### Other items

- **Duck's footprint:** `DUCK_DECLARED_SCOPE_FALLBACK` is shown as `binding_source`. EGO identity stays `UNRESOLVED`, with a gap; the validator refuses an exact join on it.
- **G4-B:** the graded predictions are cited, not `certified_by`. G4 is out of this slice's role fields.

## 3 · What the modules hold (built in this slice)

**`inference/framework/world_model_v2.py`** holds:
- `SCHEMA = virelai-world-model-v2`;
- `validate`, `seal`, `content_sha256`, `canonical_bytes`;
- `read_world_model`, which dispatches v1 to the existing reader and validator, v2 to its own, and refuses anything else;
- `write_canonical`.

Certified roles in this slice are EGO, COUNTER and LEVER only. INERT, force, driven reactions, scoped negatives and Band 1 are `NOT_BUILT` gaps, and Band 1 is always `UNSETTLED`.

**`inference/framework/library_census.py`** holds `ExecutionRecord` (the explicit inputs: entry board, entry level, valid actions, executed action names) and these functions:

| Function | What it does |
|---|---|
| `board_cut` | The runtime weave's cut, computed from a grid |
| `project_tracks` | Rebuilds every board of the level from the entry board and the level's `transition_index` rows, one weave window per life, threaded with `weave_window` then `re_join` unchanged. Consecutive identical sightings collapse into segments. |
| `record_check` | Compares the gate record with what was executed: missing, extra and renamed IDs |
| `compile_level` | The census of one level |
| `compile_world_model` | Frozen levels plus the open level; with no machine, a level-entry census from the observed board |

**Measured on the replays** (at the cut points the tests use):
- **k008, early G1 stop (28 transitions recorded):** nothing is gate-certified yet. G1 is still in progress, so every track's role gap is `FOUNDATION_UNRESOLVED`.
- **k008 at the G2 close (37 transitions, two lives):** 18 tracks, 9 of them reborn after the reset. EGO and COUNTER identities are honestly unresolved: the ego is multi-component, and the mask footprint matches no single track.
- **k013 (400 transitions, 8 lives):** 201 tracks. The census certifies exactly the 9 live pointer levers, all `PENDING`. 23 one-to-one joins, no INERT. About 7 s per compile.

## 4 · Tests: fail-first evidence

| File | Present-tree failure (observable) | Now |
|---|---|---|
| `tests/test_wo_l2a_census_paths.py` | (1) The real `_HarnessGameSession.play` path, with the stop already set: one board observed, no turn, no action, `cancelled`, and **no `world_model.json`** (`FileNotFoundError`). (2) After a v2 file exists, a legacy `controller`, `intent` or `agenda` query **rewrites it as v1**. Both were run with `--runxfail` and failed. A premise test confirms the path reproduces the 77-game shape. | 1 passed (premise), 4 **strict** xfail until the hooks land |
| `tests/test_world_model_v2.py` | New module, so it cannot import; each test is a contract refusal | 9 passed |
| `tests/test_library_census.py` | New module, so it cannot import. Each test pins a premise that holds on the present tree, such as "G3's ledger is `None` at an early stop", so no census exists for it. | 9 passed |

The census tests cover:
- the zero-action click level entry, with ACTION5/ACTION7 gaps and G3 left uninitialized;
- the no-machine observed board;
- the early G1 stop;
- lives never joined, and departed and life-ended objects kept;
- the counter as a mask;
- the G3 witness with inventory `PENDING`;
- record mismatch (extra and renamed);
- determinism;
- the Duck footprint as a hint.

Every census call asserts the machine is **byte-identical** (a pickle digest) before and after.

**Full cloud suite** (Python 3.12, 94 files, ignoring `test_physics_grammar_contract.py`): **661 passed, 1 skipped, 4 xfailed**, 0 failed. That is the 641 floor plus 9, 9 and 1 new tests; the 4 xfails are the strict hook-pending tests.

## 5 · The concrete no-machine caller, for the hooks slice

For the 77 games, the path is `_HarnessGameSession.play` (`solver.py:464-588`):

1. `_observe_virelai_initial()` at `:472` writes the one frame.
2. `while not self.should_stop()` at `:478` never runs, so the analyzer and gate machine never exist (the machine is built on the first turn, `tool_agent.py:1435-1448`).
3. `finally:` at `:542` → `_finish_if_needed()` at `:585` (state `cancelled`) → `_close_game_observer()` at `:586`.

**H2 goes between `:585` and `:586`.** Its inputs are explicit:
- `ExecutionRecord(entry_board, 1, valid_actions, executed)`. The entry board, level and actions are captured in a new session field at `:472`, from `self.current_frame()` and `_engine_action_names(self.game)`. `executed` comes from `self.game.game_run.history`.
- `machine = getattr(self.analyzer, "_gate_machine", None)`.

**A game whose initial observation never happened gets no census, only an event.** That covers observer construction failing, or `play()` never reaching `:472`. v2's output had none.

## 6 · Hooks slice, next, after the floor

**Shared files to declare** in `NOTE_SHARED_FILE_WO_L2A_HOOKS`, before any edit:

| File | Change |
|---|---|
| `virelai_gates.py` | `_advance_level`: `level_censuses.append(compile_level(..., state="FROZEN"))` **before** `freeze_level` (H1, compute only) |
| `life_record.py` | `level_censuses` at GAME tier |
| `gate_artifacts.py` | Write after `record_outcome` when `level_censuses` grew |
| `solver.py` | The entry capture at `:472`, and H2 at `:585-586`, wrapped so a failure is recorded and never raised |
| `virelai_runtime.py` | `_canonical_world_model` → `_observer_world_model`, with no file write by default |

The hooks slice removes the strict-xfail marks. It adds a level-boundary test on the carry-v7 record fixture, an H1+H2 query-overwrite test, and a cross-check of the projection against the runtime's `continuity_tracks.json` on saved v2 records. Mismatches become listed gaps.

## 7 · Open item for Sol

**AMBIGUOUS has no reason of its own in WO-L2's vocabulary.** A G3 `AMBIGUOUS` row (attribution unresolved) is a gap with reason `NOT_REACHED`, and its source text keeps `G3 AMBIGUOUS: <disposition>`. If Sol wants it distinguished, a reason such as `INCONCLUSIVE` would be a third addition.

— Claude, Alpha build seat (click line), 2026-10-10
