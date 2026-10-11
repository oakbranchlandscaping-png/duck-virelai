# WO-L2a interface note, amended (v4)

**Type:** `INTERFACE_WO_L2A_WORLD_MODEL_V2` · **v4** · **2026-10-11**. It supersedes v3. v1–v3 stay in place as history.
**Changed from v3:** only §6 and §7, and the new §0a. They now agree on Sol's ruling of 2026-10-11: **execution-journal verification is deferred at H1 and reconciled at H2.** v3's pure modules passed the Mac floor (`BUILD_SLICE_WO_L2A_PURE_MODULES_2026-10-11`).
**Author:** Claude (Alpha build seat, click line), signed
**Governs:**
- Sol's approval of v3, 2026-10-11, which rules deferred journal verification at H1;
- Sol's review of WO-L2a v2, relayed by the Director on 2026-10-10: H1's level, `INCONCLUSIVE`, resolvable receipts, a unique temporary file, and duplicate transition IDs;
- `REVIEW_WO_L2A_INTERFACE_2026-10-10` (Sol): its answers to Q1–Q3 and its six corrections;
- `REVIEW_WO_L2_00_CENSUS_ARCHITECTURE_2026-10-10`.

**Base:** `ring9-unified` @ `099aef9`. Its code equals `cd07716`.
**This slice:** the pure schema and census modules, with their tests. **No shared file is edited.** The hooks slice files its `NOTE_SHARED_FILE` first (§6).

**The unrelated root note** `WO_L2A_CENSUS_INTERFACE_NOTE_v1_2026-10-10.md` is left in place, as asked. Its status is resolved separately.

## 0 · Changes from v2 (Sol's review findings)

| Finding | Fix | Fail-first evidence on the v2 modules |
|---|---|---|
| **H1 censused the wrong level.** `LifeRecord.tag` moves `machine.lives.level` to `level_after` before `_advance_level` runs. | `compile_level(..., state="FROZEN", level=...)` takes the boundary's `level_before` explicitly; a `FROZEN` call without it raises `ValueError`. The open-level census still reads `machine.lives.level`, which is correct after a boundary. | On the boundary of the carry-v7 record fixture (transition 26), v2's frozen census reported **level 2, 0 rows, with level 1's entry board**. The new boundary test fails on v2 ("DID NOT RAISE"). |
| **AMBIGUOUS is not "not reached".** | New gap reason `INCONCLUSIVE` for G3 `AMBIGUOUS`. `NOT_REACHED` stays for an experiment not performed: an untried object, a route that could not be completed (`PRESUMED_UNREACHABLE`), or a body pass still owed. | The test fails on v2: the four ambiguous k013 objects read `NOT_REACHED`. |
| **Validation checked a certificate's shape, not its source.** | Each level carries `receipts`, as described below. Every role must resolve against them: EGO and COUNTER through their `product_id`, to a product of their own gate; LEVER through each `witness_ref`, to a witness of the **same entity**; every `evidence_ref` to some receipt. Every evidence receipt must sit on a recorded transition, and every witness on its evidence's transition. Refs the index cannot resolve, such as `G0-ACTION-METADATA` or discovery record IDs, are kept in `unverified_refs` and never count as certification. | The forged-witness test fails on v2 (no receipts); the schema tests refuse forged and mismatched refs. |
| **The writer used a fixed temporary name.** | `tempfile.mkstemp` in the same directory, then fsync, then `os.replace`. The temporary file is removed on failure. A stray fixed-name file is neither used nor clobbered. | New schema test |
| **Duplicate transition IDs collapsed silently.** | `record_check` reports `duplicated`. A duplicate is a `RECORD_MISMATCH`, so the level is `NOT_ACCOUNTED`, and any role cited on it drops to a gap. | The test fails on v2 (`KeyError: 'duplicated'`) |

**The receipt index** has three parts:
- `evidence`: each recorded transition of the level that carries a gate evidence ID;
- `products`: each active gate product, with its gate, type, revision and payload SHA-256;
- `witnesses`: each G3 witness, with the entity its member binds to, its evidence ID and its transition.

**What validation now proves, and what it does not** (also stated in the module docstring):
- **It proves** that every certified role resolves against the artifact's own receipt index, with the right gate and entity, and that every receipt sits on a recorded transition. That transition is in turn checked against the execution journal.
- **It does not prove** that the index came from the gate machine. That rests on the compiler, which reads gate state only, and on a later cross-check against the run's `gate_events.jsonl`. I no longer claim that validation alone proves gate certification.

## 0a · Deferred verification (v4)

**The rule.** The gate machine never receives harness execution history. H1 freezes the ended level from gate state alone. H2, which runs in the solver and holds the history, reconciles **every** level, frozen and open, before it writes the final model.

**H1 freezes the census with the check still pending.** A new pure function, `library_census.freeze_level_census(machine, *, level_before)`, takes no execution record. It keeps the ended level's:
- entry board and observation tracks;
- gate receipts, roles and gaps.

Its `record.journal_check` is `{"status": "PENDING"}`, and its accounting is `NOT_ACCOUNTED` with `missing: ["JOURNAL_CHECK_PENDING"]`. **A frozen census never claims `ACCOUNTED`.** The entry's `valid_actions` come from the ended level's G0 affordances, which are gate state.

**H2 reconciles.** A new pure function, `library_census.reconcile(levels, machine, execution) -> levels`, works in four steps:

1. **One global comparison.** It compares the full `execution.executed` against **all** of `machine.transition_index`, using the existing `record_check` (missing, extra, duplicated, renamed).
2. **Each mismatched ID goes to the level that owns it.** A recorded row goes to its row's `level`. A missing ID (executed but never recorded) goes to the level whose recorded span contains it, or, if it falls between spans, to the next level's span. An ID after the last recorded transition goes to the open level.
3. **Each level becomes `{"status": "CHECKED", ...}` with its own IDs.**
   - **A clean level** recomputes its accounting from the remaining `missing`. Only now can it become `ACCOUNTED`.
   - **A level with mismatched IDs** gets a `RECORD_MISMATCH` gap listing them, and stays `NOT_ACCOUNTED`. **Every role whose receipts place a cited evidence or witness on an unmatched transition is removed** and replaced by a gap. The roles are judged through that level's own receipt index.
4. **The final model.** H2 writes `compile_world_model(machine, execution, frozen_levels=reconciled)`. The open level is compiled with the full record check at that moment.

**Validator additions:**
- `journal_check.status` must be `PENDING` or `CHECKED`.
- `PENDING` requires `NOT_ACCOUNTED`, with `JOURNAL_CHECK_PENDING` among the missing.
- A `CHECKED` level with any mismatch must be `NOT_ACCOUNTED`, and must carry a `RECORD_MISMATCH` gap naming the same IDs.

**Interim persistence (decided here, changing v3):** a model written between H1 and H2 carries the pending checks. It can never claim more than the final model. The solver, not `gate_artifacts.py`, writes it after an analyzer turn in which `machine.level_censuses` grew, because the solver holds the paths. That drops `gate_artifacts.py` from the shared files. If the process dies before H2, the interim model on disk is honest: every frozen level is `NOT_ACCOUNTED`, check pending.

## 1 · Answers adopted

| Question | Adopted answer |
|---|---|
| Q1: a G3 witness | **LEVER is certified by its G3 witness** before the inventory, with its witness and discovery refs. `inventory_status` (`PENDING` or `ACCEPTED`) is a separate field. The role itself is never "pending". No mechanism, repetition or condition is inferred from the one witness. |
| Q2: gap reasons | **`IDENTITY_UNRESOLVED`, `RECORD_MISMATCH` and (from Sol's v2 review) `INCONCLUSIVE` are added.** A record mismatch makes the level `NOT_ACCOUNTED` and lists the missing, extra, duplicated and renamed IDs. A role whose evidence lies on an unmatched transition drops to a gap. |
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

- `world_model_v2.write_canonical` is the only writer. It validates, seals, writes a **unique** same-directory temporary file (`mkstemp`, then fsync), replaces atomically, and **never raises**.
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
- `write_canonical`;
- the receipt validation described in §0.

Certified roles in this slice are EGO, COUNTER and LEVER only. INERT, force, driven reactions, scoped negatives and Band 1 are `NOT_BUILT` gaps, and Band 1 is always `UNSETTLED`.

**`inference/framework/library_census.py`** holds `ExecutionRecord` (the explicit inputs: entry board, entry level, valid actions, executed action names) and these functions:

| Function | What it does |
|---|---|
| `board_cut` | The runtime weave's cut, computed from a grid |
| `project_tracks` | Rebuilds every board of the level from the entry board and the level's `transition_index` rows, one weave window per life, threaded with `weave_window` then `re_join` unchanged. Consecutive identical sightings collapse into segments. |
| `record_check` | Compares the gate record with what was executed: missing, extra, duplicated and renamed IDs |
| `compile_level` | The census of one level. A `FROZEN` call requires an explicit `level`, the boundary's `level_before`. The output includes the level's `receipts`. |
| `compile_world_model` | Frozen levels plus the open level; with no machine, a level-entry census from the observed board |

**Measured on the replays** (at the cut points the tests use):
- **k008, early G1 stop (28 transitions recorded):** nothing is gate-certified yet. G1 is still in progress, so every track's role gap is `FOUNDATION_UNRESOLVED`.
- **k008 at the G2 close (37 transitions, two lives):** 18 tracks, 9 of them reborn after the reset. EGO and COUNTER identities are honestly unresolved: the ego is multi-component, and the mask footprint matches no single track.
- **k013 (400 transitions, 8 lives):** 201 tracks. The census certifies exactly the 9 live pointer levers, all `PENDING`. 23 one-to-one joins, no INERT. About 7 s per compile.

## 4 · Tests: fail-first evidence

| File | Present-tree failure (observable) | Now |
|---|---|---|
| `tests/test_wo_l2a_census_paths.py` | (1) The real `_HarnessGameSession.play` path, with the stop already set: one board observed, no turn, no action, `cancelled`, and **no `world_model.json`** (`FileNotFoundError`). (2) After a v2 file exists, a legacy `controller`, `intent` or `agenda` query **rewrites it as v1**. Both were run with `--runxfail` and failed. A premise test confirms the path reproduces the 77-game shape. | 1 passed (premise), 4 **strict** xfail until the hooks land |
| `tests/test_world_model_v2.py` | New module, so it cannot import; each test is a contract refusal. v3 adds forged and mismatched references, receipts on unrecorded transitions, `INCONCLUSIVE`, and a unique temporary file. | 12 passed |
| `tests/test_library_census.py` | New module, so it cannot import. Each test pins a premise that holds on the present tree. v3 adds four tests, and **each was run against the v2 modules and failed** (§0): the frozen level at the boundary, `INCONCLUSIVE`, the forged witness, and the duplicated transition. | 13 passed |

The census tests cover:
- the zero-action click level entry, with ACTION5/ACTION7 gaps and G3 left uninitialized;
- the no-machine observed board;
- the early G1 stop;
- lives never joined, and departed and life-ended objects kept;
- the counter as a mask;
- the G3 witness with inventory `PENDING`;
- record mismatch (extra and renamed);
- determinism;
- the Duck footprint as a hint;
- **(v3)** a frozen census at a real level boundary, proven to be the ended level's. Its number, entry board, all 26 rows and its gate products (the same set `freeze_level` froze) all belong to level 1, while `machine.lives.level` already reads 2. The open level 2 then enters at `LEVEL_ENTRY`, after transition 26, on its own board, and shares no track with level 1.
- **(v3)** `INCONCLUSIVE` for the four ambiguous k013 objects, kept distinct from `NOT_REACHED` for untried ones;
- **(v3)** a forged LEVER witness on a real census fails validation;
- **(v3)** a duplicated transition is a mismatch.

Every census call asserts the machine is **byte-identical** (a pickle digest) before and after.

**Full cloud suite** (Python 3.12, 94 files, ignoring `test_physics_grammar_contract.py`): **668 passed, 1 skipped, 4 xfailed**, 0 failed. That is the 642 base (the floor after the G3 lifecycle slice) plus 13, 12 and 1 new tests; the 4 xfails are the strict hook-pending tests. A correction to v2: it reported its 661 as "641 plus 9, 9 and 1". The base was 642 there too, and the total was right..

## 5 · The concrete no-machine caller, for the hooks slice

For the 77 games, the path is `_HarnessGameSession.play` (`solver.py:464-588`):

1. `_observe_virelai_initial()` at `:472` writes the one frame.
2. `while not self.should_stop()` at `:478` never runs, so the analyzer and gate machine never exist (the machine is built on the first turn, `tool_agent.py:1435-1448`).
3. `finally:` at `:542` → `_finish_if_needed()` at `:585` (state `cancelled`) → `_close_game_observer()` at `:586`.

**H2 goes between `:585` and `:586`.** Its inputs are explicit:
- `ExecutionRecord(entry_board, 1, valid_actions, executed)`. The entry board, level and actions are captured in a new session field at `:472`, from `self.current_frame()` and `_engine_action_names(self.game)`. `executed` comes from `self.game.game_run.history`.
- `machine = getattr(self.analyzer, "_gate_machine", None)`.

**A game whose initial observation never happened gets no census, only an event.** That covers observer construction failing, or `play()` never reaching `:472`. v2's output had none.

## 6 · Hooks slice: what changes and where

Declared in `NOTE_SHARED_FILE_WO_L2A_HOOKS_2026-10-11.md`, filed before any edit.

| File | Function | Change |
|---|---|---|
| `inference/framework/virelai_gates.py` | `CyberneticGateMachine.__init__` | Adds `self.level_censuses: list[dict] = []` (GAME tier) |
| same | `CyberneticGateMachine._advance_level` | **H1**, before `freeze_level`: `self.level_censuses.append(freeze_level_census(self, level_before=boundary["level_before"]))`. Compute only. **No execution record and no harness state enters the machine.** A census failure is caught and recorded as an `L2A_CENSUS_FAILED` row on the census list; the level advance always proceeds. |
| `inference/framework/life_record.py` | `PERSISTENCE["CyberneticGateMachine"]` | `"level_censuses": GAME` |
| `inference/framework/solver.py` | `_HarnessGameSession._observe_virelai_initial` | Captures `self._l2a_entry` = (board, level, valid actions) from `self.current_frame()` and `_engine_action_names(self.game)`, only when the observation succeeds |
| same | `_HarnessGameSession.play`, the loop body | Interim write after an analyzer turn in which `machine.level_censuses` grew (pending checks) |
| same | `_HarnessGameSession.play`, `finally` (between `_finish_if_needed`, `:585`, and `_close_game_observer`, `:586`) | **H2:** build `ExecutionRecord` from `self._l2a_entry` and `self.game.game_run.history`; `reconcile` every frozen census; compile the open level; `write_canonical` to `job_dir/virelai/<run_stem>/`. Wrapped so a failure becomes an event and never raises or masks the original exception. With no `_l2a_entry` (never observed), nothing is written except a `WORLD_MODEL_NOT_OBSERVED` warning. |
| `inference/framework/virelai_runtime.py` | `_canonical_world_model` and its 7 query callers | Renamed `_observer_world_model`. It keeps its in-memory cache and **writes no file by default**. An opt-in environment flag writes `world_model_legacy_v1.json` only. |

My own pure modules also grow (`freeze_level_census`, `reconcile`, and the validator rules in §0a). They are not shared.

**Tests in the hooks slice, each fail-first:**
1. The 4 strict xfails in `test_wo_l2a_census_paths.py` pass, and their marks are removed. Both the zero-action cancellation write and the legacy query overwrite run through the real hooks.
2. **Level advance, then finalization** (carry-v7 record fixture, real `_advance_level`):
   - **(a)** With a matching execution history, H1's frozen level-1 census is `PENDING` and `NOT_ACCOUNTED`. After H2 it is `CHECKED`, and accounted from its remaining gaps alone.
   - **(b)** With **a mismatch on the frozen level** (one level-1 action renamed in the history), level 1 is `NOT_ACCOUNTED`, with a `RECORD_MISMATCH` gap naming that ID, and any role citing that transition is removed. The open level 2 is unaffected.
   - **(c)** A missing ID that falls between the levels goes to the next level's span, as §0a step 2 states.
3. The interim model written between H1 and H2 validates, and claims nothing `ACCOUNTED` for a frozen level.
4. A census failure inside H1 is recorded, and the level still advances (the existing level-change replays stay green).
5. The real `play()` path with a crash injected after H1: the final write still happens, with `persist_reason: CRASH`, and the original exception text is still recorded in `run.solver_note`.

## 7 · Open items

1. **Settled by Sol, 2026-10-11:** deferred verification at H1, reconciled at H2 (§0a, §6). v3's §7 proposal is adopted.
2. **The open v2 item was settled earlier:** `INCONCLUSIVE` for G3 `AMBIGUOUS`.
3. **Still pending, after the hooks:** a cross-check of the observation projection against the runtime's `continuity_tracks.json` on saved v2 records. Mismatches become listed gaps.

— Claude, Alpha build seat (click line), 2026-10-11
