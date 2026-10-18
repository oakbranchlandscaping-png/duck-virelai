# Shared-file note, amendment 1: WO-G4-DOSSIER-A revision 2 (2026-10-17)

**Filed by:** Claude, Alpha build seat, before any revision-2 shared edit.
**Amends:** `NOTE_SHARED_FILE_WO_G4_DOSSIER_A_2026-10-16.md`.
**Base:** the revision-1 slice on `e8984c2`.
**Authority:** Sol's revision-2 directive.

## New files

Production, under `inference/framework/`:

- `lever_dossier_links.py`: pure. Computes each anatomy channel's exact observed events and its affected subject from the level's stored description (blockers 3 and 4).
- `lever_dossier_provenance.py`: pure. Covers the facts that depend on provenance (blocker 1, blocker 2 and the scope correction): the activation's executor, the relation set's submitter, and a receipt that an execution contradicts. `reconcile` runs once per seal.

Tests:

- `tests/dossier_provenance_fixtures.py`: committed synthetic fixtures. Each is the minimal lever model plus a real, hash-chained synthetic journal.
- `tests/test_world_model_v6_dossier_records.py`: the full-record semantic cases, moved from the v6 suite into T1 (the T0 runtime blocker).

## Shared files edited again

| File | Change |
|---|---|
| `world_model_v2.py` | `seal` runs `lever_dossier_provenance.reconcile` after `provenance_chapter.attach`, before the strict check and the hash. v6 validation now checks dossiers after the provenance chapter and passes that chapter to the dossier validator. Net: +1 executable line. |
| `world_description.py` | The anatomy channel lines (`dossier_channels`). The identity summary gains chooser and executor; the relations summary gains submitter and certifier. |
| `world_report.py` | One claim line per anatomy channel, citing the event ids and the joined track. |
| `tests/tiers/test_tiers.toml` | T0 `g4-dossier` keeps only the pure dossier file. The records file joins T1 `description` and T1 `paper-evidence`. |
| `tests/tiers/T2_collected.txt` | 28 ids moved to the records file, 26 added, 0 removed. |

## Still unchanged

- `provenance_hooks.py`, `provenance_chapter.py` and `audit_journal.py`. The dossier reads the chapter that `seal` already attaches; no hook changed.
- `library_census.py`. No revision-2 line; it stays at revision 1's +1.
- `library_view.py`.
- Every gate, agenda, selection and controller module, and the frozen G4 product payloads. `certified_by` is normalized only in the dossier projection.
