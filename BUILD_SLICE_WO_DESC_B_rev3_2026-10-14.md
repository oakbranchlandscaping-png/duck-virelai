# Build slice: WO-DESC-B, revision 3

**Date:** 2026-10-14
**Author:** Claude (Alpha build seat)
**Responds to:** Sol's review of revision 2 (one blocker: zero-action and later-level scene references)
**Base:** `ring9-unified` at `66b91cb`
**Revision 2:** `slice_wo_desc_b_rev2.tar.gz` (`4b47b51b…`)
**Status:** accepted by Sol after source review and the local tier floor. See §0a.

## 0a. Sol acceptance on the Mac

Sol reviewed revisions 1–3, applied the revision-3 archive, and verified all eleven slice-file hashes against
`SLICE_SHA256SUMS_WO_DESC_B_rev3.txt`. `git diff --check` was clean before staging.

| Local gate | Result | Wall time |
|---|---:|---:|
| T2, four workers in the managed sandbox | 923 passed, 1 skipped, 2 environment failures | 586.7 s |
| T0 `test-tiers`, two workers with local process inspection | 24 passed | 14.6 s |

The two T2 failures were the runner's SIGTERM and SIGINT cleanup tests. Both failed only because the managed
sandbox denied their use of `ps` (`PermissionError: [Errno 1] Operation not permitted`). Both passed in the
authorized local-process rerun. No product, description, report, census, gate, navigation, lifecycle, replay, or
library-view test failed. The accepted effective floor is **925 passed, 1 skipped**.

## 1. What changed

Four files changed since revision 2: `world_report.py`, `library_view.py`, `tests/test_world_description.py` and the T2 snapshot.

### The rule (`world_report._scene_basis`)

| Case | Scene line reads | It cites |
|---|---|---|
| No verified action (`as_of_transition` is `None`) | `as of level entry` | `levels[i].entry` and `levels[i].description.scene`. **No range.** |
| After actions | `as of transition N` | `levels[i].entry`, `levels[i].description.scene` and `t{entry_node+1}-t{N}`. Only this level's own transitions; the initial level starts at `t1`. |

- **Both scene claims follow the rule.** The integrity claim also cites `levels[i].description.integrity`.
- **The census line's range** was already scoped to the level: it is the level's own verified transitions.
- **The digest scene line** (`library_view._scene_line`) reads `as of level entry, life L: …` when no action is verified. Neither surface renders `None`, `tNone` or `t0`.
- **The report header** now omits a manifest field the model lacks. The validator requires only `status` and `persist_reason`, and the synthetic two-level test exposed a header that would otherwise render `None`. Real census manifests carry all four fields, so the acceptance records are unchanged.

### Report changes on the acceptance records

On k008, carry t20 and k013 t401, **exactly the two scene lines changed**:
- `t0-tN` became `t1-tN`;
- `levels[0].entry` was added to the references.

## 2. The reference test, strengthened

`_assert_report_refs(model, text)` now tracks the current `## Level N` section (and `### Appendix, level N`). For each claim:

- **A path** `levels[i]…` must name the level of the section it sits in.
- **A range** must satisfy `entry_node + 1 ≤ A ≤ B ≤` that level's last recorded transition. A level with no recorded transition accepts no range.
- **Outside every level section,** no path and no range resolves.
- **The whole report** must contain no `None`, `null`, `tNone` or `t0`.

The test also confirms the resolver refuses:
- `levels[1].entry` inside level 1;
- `t0-t1`;
- a range past the level.

## 3. Fail-first, on revision 2 (`failfirst_descB_rev3_on_rev2.txt`)

The revision-3 test file was run against revision 2's production code: **6 failed, 58 passed.**

| Test | Revision 2's output |
|---|---|
| Strengthened reference test (k008, k013, carry) | `t0` in each scene line |
| **Observed board, zero actions** (the cancelled-run fixture, the 77-world shape) | `as of transition None` and `t0-tNone` |
| **The open second level** (the existing carry boundary fixture: level 1 frozen at t26, level 2 at its entry with no action) | `as of transition None` and `t0-tNone` |
| **A later level after actions** (synthetic: entered after t3, transitions 4-6 verified) | `t0-t6` instead of `t4-t6` |

The carry boundary fixture replays the record the way `test_library_census` does, and is built once per module (about 6 s). The zero-action test also requires that the report written beside the model equals a fresh render, and checks the digest scene line.

## 4. Tiers and the snapshot

`library_view.py` changed, and T1 `g3-directed` imports it, so all three tiers were rerun.

| Check | Result |
|---|---|
| T0 `desc-b` | **78 passed** |
| T1 `description` | **204 passed** |
| T1 `g3-directed` | **143 passed** (unchanged) |
| Snapshot | 923 → 926: **+3 new tests, none removed**; `--check` is exact |

## 5. The ratchet

| File | Change |
|---|---|
| `world_report.py` | 177 → 186 lines. New: `_scene_basis` (6). `_scene_lines` 20 → 19, `_header` 13 → 12. |
| `library_view.py` | 513 → 514 lines. `_scene_line` 6 → 7. |

## 6. Files in `runs/_cowork_xfer/l2a/descB/rev3/`

- **The slice:**
  - `slice_wo_desc_b_rev3.tar.gz` (`7be88952…`, the same 11 paths as revision 2);
  - `SLICE_SHA256SUMS_WO_DESC_B_rev3.txt`;
  - `diff_rev2_to_rev3.patch`;
  - `diff_descB_rev3_vs_66b91cb.patch`.
- **Evidence:**
  - `failfirst_descB_rev3_on_rev2.txt`;
  - the T0 and T1 run logs and their results JSON;
  - a copy of the test file;
  - this report.
- **Example reports:**
  - `EXAMPLE_world_report_observed_never_acted.md` (zero actions);
  - `EXAMPLE_world_report_carry_boundary_two_levels.md` (level 2 at its entry);
  - the k008, carry t20 and k013 t401 reports.

## 7. Noted, not changed

- **Empty lists in the digest.** On a world with no patterns, the digest world block carries `"patterns": []` and `"questions": []`. That is truthful but empty, and it is left for Sol's call.
- **Library pages.** The scene page is JSON and still carries `as_of_transition: null` for an entry-state scene. The ruling named the report and the digest scene line. The page is the stored field, not prose.
