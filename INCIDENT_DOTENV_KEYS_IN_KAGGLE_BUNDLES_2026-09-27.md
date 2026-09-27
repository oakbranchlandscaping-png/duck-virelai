# Incident: API keys shipped inside Kaggle source bundles

**Date found:** 2026-09-27
**Author:** Claude (Alpha build seat) — signed
**Severity:** credential exposure to a third-party store (private scope, not confirmed public)
**Status:** OPEN until both keys are rotated and the affected datasets are deleted or confirmed
private. Recurrence is prevented for new packages.

## Summary

`variants/ring9-cybernetic-gates/ARC3-Inference/.env` holds two live credentials:
`OPENROUTER_API_KEY` and `ARC_API_KEY`. The file is gitignored and has never been committed. The
G3-era packagers copied the working tree into each Kaggle bundle and did not exclude it, so the file
was packaged — both as `src/ARC3-Inference/.env` and inside `src.zip` — in these bundles:

| Package | `.env` listed in its source manifest | Uploaded to Kaggle |
|---|---|---|
| `ring9-g3-qwen36-compatibility-v1` | yes | yes (notebook versions 1 and 2 ran) |
| `ring9-g3-vc33-closure-v1` | yes | yes (submitted; superseded before review) |
| `ring9-g3-vc33-closure-v2` | yes | yes (reviewed run) |
| `ring9-g3-vc33-closure-v3` | yes | yes (ran 2026-09-24) |

The G0, G1 and G2 packages do not list it. Key values were never printed in this investigation;
only key names were read.

## Exposure

- **Kaggle:** the datasets (or dataset versions) created for the four packages above were uploaded
  with the key inside; closure v1 and v2 may share one slug as successive versions. Their `dataset-metadata.json`
  records no privacy field; the CLI default is private and the deploy targets say `public: False`,
  so they are most likely private to the owner's account. That is not confirmed from here.
- **Git:** not exposed as far as verified. `.env` is gitignored, and `kaggle/ring9-g3-vc33-closure-v3/`
  was verified untracked on 2026-09-27; confirm the other affected package directories with
  `git status` before staging anything under `kaggle/`. Tracked files contain only placeholders
  (`README.md`: `<your-openrouter-api-key>`; `scripts/configure_openrouter_key.sh`: `%s`).
- **Local disk:** the four package directories still contain the key, including inside their
  `src.zip` files. `.gitignore` catches a loose `.env` but cannot see inside a zip, so
  `git add kaggle/` or `git add -A` **would commit the key.**

## Root cause

The packagers built the bundle from the working tree with an ignore list covering caches, virtual
environments, tests and runs, but not dotenv files. Nothing checked the finished bundle for secrets.
It was found during G4 packaging, when a file-list comparison between the bundle and the committed
tree showed untracked files shipping.

## Containment done (2026-09-27)

- The first G4 build, which also carried the key, was deleted on the Mac before upload and never
  committed.
- The G4 packager was rebuilt to export source only from the committed tree (`git archive`) and to
  run a secret guard over every file and every `src.zip` entry; it deletes its own output on a hit.
- `tools/verify_kaggle_package.py` repeats the secret scan as a stand-alone pre-upload check and
  exits non-zero on a hit.
- Transfer archives on the Mac (`runs/_cowork_xfer/`) were deleted; every copy in the cloud
  workspace was purged and re-scanned clean.
- The uploaded G4 dataset (`ring9-g4-phase1-drain-v1`) was scanned clean before upload.

## Actions remaining (owner: Director)

1. Rotate the OpenRouter key and the ARC key. Put the new OpenRouter key back with
   `scripts/configure_openrouter_key.sh` so local runs keep working.
2. Delete the affected Kaggle datasets or dataset versions (all four packages), or at minimum
   confirm each is private.
3. Never stage `kaggle/` wholesale. If those package directories are to be kept, scrub the `.env`
   from both their `src/` trees and their `src.zip` files first; their manifests and receipts will
   then no longer match, which is acceptable for historical records but should be noted beside them.

## Prevention

Any future packager should copy the G4 packager's `_committed_source` and `_secret_guard`, and
every upload should be preceded by `tools/verify_kaggle_package.py`.

— Claude, Alpha build seat, 2026-09-27
