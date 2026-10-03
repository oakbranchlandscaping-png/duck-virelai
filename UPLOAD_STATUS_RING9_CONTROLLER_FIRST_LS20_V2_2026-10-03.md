# Upload status: Ring 9 controller ownership ls20 v2

**Author:** Sol (Alpha build seat), signed
**Date:** 2026-10-03
**Status:** VERIFIED LOCALLY; upload blocked before transfer by automatic approval review

## Frozen identities

- Source commit: `4e1be00f59c1c430391603c572bfd1dcaa4f87cb`
- Package: `kaggle/ring9-controller-first-ls20-v2`
- Package-manifest SHA-256: `b24e6bb6bdf1ae8180ec0ce4d57ee260a1593ac273b49936a97876d0889e2dd1`
- Source-manifest SHA-256: `807ce79c7cf65748168697de5555fe6337010ce6f0b12fbc9bf0a7c2bb4e29dd`
- Private dataset: `stephenkaskin/taaf-duck-virelai-ring9-controller-first-ls20-v2`
- Private notebook: `stephenkaskin/taaf-virelai-ring9-controller-first-ls20-v2`
- World: `ls20-9607627b`
- Model: pinned `Qwen/Qwen3.8-27B-FP8`
- Runtime: pinned successful Python 3.12 image
- Behavior limits: 16 actions, 1200 seconds, concurrency 1
- Inference limits: 4096 output tokens, 600-second request timeout, thinking enabled

## Verification

- Active source: 549 tests passed.
- Ownership-focused production and NAV suites: 47 tests passed.
- Package verification: 9/9 checks passed.
- Packaged source: byte-identical to the source-commit export.
- Source and package manifests: re-derived successfully.
- Inner and outer receipts: identical and bound to both manifests.
- `src.zip`: byte-identical to the expanded source tree.
- Notebook code cells: compiled by the packager.
- Kernel: private, offline, GPU-enabled, and led by the v2 dataset.
- Secret scan, including `src.zip`: clean.
- `dataset-metadata.json`: present in the source-dataset root and covered by the source manifest.

The three-layout mount simulator was attempted locally. It could not create `/kaggle` because the
Mac root filesystem is read-only. This is a host limitation before package code executes, not a
package pass or failure. The v2 notebook and mount logic are ported from the v1 package that ran on
Kaggle; the changed dataset identity is present in kernel metadata, notebook source, dataset
metadata, and the verified receipt-bound package.

## Preregistered live outcome

The canonical criteria remain in
`CHECKPOINT_CONTROLLER_OWNERSHIP_LS20_V2_2026-10-03.md`. In particular, notebook completion alone
does not pass the checkpoint. Downloaded artifacts must prove G3 entry and zero Duck-selected
environment actions.

## Upload attempt

The private-dataset creation command was submitted for the exact destination listed above. The
automatic approval reviewer rejected it before execution because uploading the source package to
an external Kaggle destination required more explicit authorization for this exact payload. No v2
dataset or notebook was created by this attempt, and no package bytes were transferred.

— Sol
