# BUILD SLICE: WO-PE-03A revision 2, two integrity changes (2026-10-15)

**Seat:** Claude, Alpha build seat (Ring 9)
**Base:** `ring9-unified` at `0779858`
**Supersedes:** `BUILD_SLICE_WO_PE_03A_SCHEMA_V5_PRODUCT_CONTENT_v1_2026-10-15`, for the revision-2 delta only. Everything else in v1 stands as reviewed.
**Directive:** Sol's PE-03A review. The architecture is accepted, and revision 2 makes only these two integrity changes.
**State:** T2 and the commit are held for Sol. Nothing is committed or pushed.

## 1 · Result at a glance

| Check | Result |
|---|---|
| Fail-first on revision 1 (production byte-identical to the parked rev1 slice) | 8 failed (`DID NOT RAISE`), 1 guard passed |
| Focused v5 suite | 35 passed (26 from rev1 and 9 new) |
| T0 `provenance-v5` | 53 passed (rev1: 44) |
| T1 `paper-evidence` | 364 passed (rev1: 355) |
| Manifest `--check` | exit 0; T2 is exactly the snapshot |
| T2 snapshot | 1074 tests: +9 against rev1, 0 removed against rev1, 0 removed against `0779858` |
| Files changed rev1→rev2 | 3: `product_content.py`, the v5 test file and `T2_collected.txt` |

## 2 · Change 1: strict JSON rejects non-string mapping keys

`product_content._strict(value, path)` runs recursively before `json.dumps` in `canonical_json`. It enforces four rules:

- every mapping key is a `str`;
- every value is `None`, `str`, `int`, `bool`, a finite `float`, a list or tuple, or a mapping;
- NaN and ±infinity are refused, as before, and the error now names the path;
- a tuple is walked as a list, and `json.dumps` emits it as one, so tuples still normalise to lists.

A refusal raises `ProductContentError` naming the offending key or type and its path (for example `non-string mapping key 1 at $.outer`).

`entry()` already turns that error into an `UNREPRESENTABLE` entry with the typed gap `PRODUCT_CONTENT_UNREPRESENTABLE` and no partial payload. So a product whose payload has such a key seals as a declared gap. It is never stored under a collapsed key.

Fail-first cases cover integer, `None` and `bool` keys at the top level, integer and `None` keys nested, and a float key inside a list inside a mapping. Each must fail in three ways: `digest_record` raises with "key" in the message, `canonical_json` raises, and `entry` returns `UNREPRESENTABLE`. A guard test checks that every JSON primitive, a nested tuple and an empty list still serialise exactly as `json.dumps` would serialise the list form.

## 3 · Change 2: duplicate active product IDs fail closed

`capture(machine)` first collects `(gate_id, product)` for every active contract. Before it builds any entry, it checks the product IDs. On the first repeated ID it raises:

```
ProductContentError: duplicate active product id 'G0-replay': gate G0-ACTION-METADATA (ActionSurface, revision 2) and gate G1-EGO (EgoLaw, revision 99)
```

The message names the ID, both gates, both product types and both revisions.

The error goes through the existing channels. No new handler was added. In every case, no model claims a complete capture:

| Census | Behaviour (demonstrated in sandbox, `h1_demo.txt`) |
|---|---|
| H1 freeze | `freeze_census_or_failure` records `{"level": L, "census_failed": "ProductContentError: duplicate …"}`. The level is listed in `manifest.census_failures` and is absent from `levels`. |
| H2 / interim write | `compile_world_model` raises, and the solver writes `WORLD_MODEL_V2_COMPILE_FAILED` with the message. No model is written by that call. |
| Live view | `library_view.live_model` raises `ProductContentError`. |

Pre-existing limit, unchanged: if an H2 compile fails, a model already written by an earlier interim write stays on disk. That is the same for every compile failure since L2A.

There are two fail-first tests:

- a stub machine with two active contracts sharing `P-SAME` (types `LeverEffectAnatomySet` and `LeverOrbitSet`, revisions 3 and 7); every part of the message is asserted;
- a real `start_g4b` machine where G1 presents the G0 product's ID; `compile_level` (via `_compiled`) must raise with that ID.

## 4 · Fail-first record (`failfirst_pe03a_r2_on_rev1.txt`)

The tests were written and run against revision 1 before any production edit:

```
8 failed, 1 passed, 26 deselected
```

- The 6 key cases and the 2 duplicate cases fail with `DID NOT RAISE`.
- The primitives guard passes; it is a guard, not a fail-first test.

## 5 · Ratchet (non-blank, non-comment lines; `product_content.py` only)

| Function | rev1 | rev2 |
|---|---|---|
| `_strict` (new) | n/a | 14 |
| `canonical_json` | 5 | 6 |
| `capture` | 7 | 12 |
| largest function in the file | `_validate_entry` 21 | `_validate_entry` 21 (unchanged) |

The file grows from 100 to 126 lines by this count (130 to 159 raw lines). No other production file changed in revision 2. `library_census.py` stays at the accepted +1.

## 6 · Tier results

All runs are sandbox runs with `--jobs 4`. T2 was not run.

| Run | Result |
|---|---|
| focused `tests/test_world_model_v5_product_content.py` | 35 passed |
| T0 `provenance-v5` | 53 passed in 135.5 s |
| T1 `paper-evidence` | 364 passed in 498.4 s (rev1: 355) |
| `tools/test_tiers.py --check` | exit 0; "T2: 1074 tests, exactly the snapshot"; every tier manifest resolves |

## 7 · For Sol: one finding, not fixed (outside "only these integrity changes")

`answer_shapes.canonical_json` (PE-02, committed at `e158057`) has the same weakness that change 1 closes here. It feeds `sha16`, the expectation values and the `absent_ok` default comparison. In the sandbox, `answer_shapes.canonical_json({1: "x"}) == answer_shapes.canonical_json({"1": "x"})`, and both give `{"1":"x"}`.

Answer fields with integer-keyed mappings would therefore hash identically to their string-keyed twins. No test currently exercises that case.

Proposed routing: a one-function follow-up in the WO-G4-DOSSIER-A line, or a PE-02 amendment, at Sol's ruling. It could reuse `product_content._strict` or a shared strict module. This was left untouched because revision 2 is scoped to product content.

## 8 · Package (`runs/_cowork_xfer/pe03a2/`)

- `WO_PE_03A_r1_to_r2.patch`: the revision delta for review. It covers 3 files (+115/−7) and applies cleanly to the rev1 slice.
- `WO_PE_03A_0779858.patch`: the cumulative patch to apply. It covers 13 files (+642/−20) and applies cleanly to `0779858`'s files, which are byte-identical to the tree afterwards.
- `WO_PE_03A_slice.tar` and `SLICE_SHA256SUMS`: the 13 files. Ten are identical to the reviewed rev1 slice; the 3 named above changed.
- `failfirst_pe03a_r2_on_rev1.txt` and `h1_demo.txt`.
- the tier run logs and results JSON;
- `PACKAGE_SHA256SUMS`.
