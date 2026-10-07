# Upload status: Ring 9 unified ls20 cell-site canary v1

**Type:** `UPLOAD_STATUS`

**Date:** 2026-10-07

**Author:** Sol (Alpha build seat), signed

**Purpose:** bounded live proof of the repaired G1-to-G3 cell-site targeting handoff

## Identity

| Field | Value |
|---|---|
| Source commit | `4cd7a28c5c2108dacacb88826a923aaeee67514a` |
| Targeting implementation | `4970953` |
| Package | `kaggle/ring9-unified-ls20-cellsite-v1` |
| Package manifest sha256 | `958bc1ea3dd8e75ba01f3acdab4053e1b47c7275c445ad13972f45b557315546` |
| Source manifest sha256 | `92a04903577f5af6f5ce3df872678267fc730f69abb5f454e4c06e55da3448ee` |
| World | `ls20-9607627b` |
| Model | `vrfai/Qwen3.6-27B-FP8` from the Director's private model dataset |
| Image | pinned Python 3.12 Kaggle image |
| Budget | 48 environment actions; 1,200 behavior seconds; one pass; concurrency 1 |
| Dataset | `stephenkaskin/taaf-duck-virelai-ring9-unified-ls20-cellsite-v1` |
| Notebook | `stephenkaskin/taaf-virelai-ring9-unified-ls20-cellsite-v1` |

The source commit contains the tested targeting repair and the `ls20-cellsite` packager profile. Its only descendant after `4970953` that is inside the runtime source is none; `c5e8ff6` is a planning document and `4cd7a28` changes the packager. The frozen runtime therefore tests the code reviewed at `4970953`.

## Preregistered scope

This is not a roster-completion, level-clear, score, or generalisation run. The run asks whether the repaired controller can begin and advance the cell-site targeting loop:

1. G1 recovers all four repeated opaque movement bearings and the complete 25-site composite ego rather than Duck's two representative sites.
2. G3 opens with a nonempty, accounting-complete counter-masked roster.
3. The active stable entity identity resolves to its current complete `EntityLedger` sighting.
4. The controller, rather than Duck, chooses computable `APPROACH` and `CONTACT_ATTEMPT` actions.
5. Route planning refreshes ego and target sites after each observed frame.
6. At least one ranked target receives a terminal G3 result and the roster advances when that disposition permits it.

The full wording is frozen in `source-dataset/checkpoint-preflight.json` as CS-1 through CS-5 and CS-R.

## Local verification

| Check | Result |
|---|---|
| Targeting-focused tests | 63 passed |
| Full repository floor before the packager-only change | 619 passed, 1 skipped |
| Static package verifier with committed source export | 9/9 passed |
| Source difference from commit export | 0 files |
| Secret scan, including `src.zip` | clean |
| Package manifest | 237 files, re-derived |
| Source manifest | 230 files, re-derived |
| `src.zip` | 221 files, byte-identical to `src/` |

The optional local mount simulator could not run because macOS exposed `/kaggle` as a read-only root-volume path. It failed before executing the notebook cells. This is a host limitation, not a passing mount simulation. The package's manifest, mount metadata, source archive, receipt binding, and notebook dataset identity passed the static verifier.

## Upload log

| Step | Direct result |
|---|---|
| Private dataset upload | Twelve files uploaded; `src.zip` 967 KB; Kaggle returned “being created” |
| Dataset status | `ready` |
| Kernel push | `Kernel version 1 successfully pushed` |
| Initial kernel status | `KernelWorkerStatus.QUEUED` |

The Kaggle CLI reported that version 2.0.0 is older than 2.2.2. No upgrade was needed for either successful upload.

## Review procedure after completion

Download the output and grade artifact state, not notebook prose:

- verify the downloaded execution receipt against this package;
- reconstruct or read the G1 control product and report its bearings, unresolved actions, ego-site count, and binding source;
- enumerate the G3 roster and compare every active target's emitted sites with its current entity sighting;
- list all G3 transitions with owner, pilot intent, target entity, entity version, and geometry source;
- identify the first terminal target result and whether the roster advanced;
- report the final gate and exact stop reason;
- keep roster completion, level completion, and score outside this slice's pass judgment.

— **Sol**, Alpha build seat, 2026-10-07
