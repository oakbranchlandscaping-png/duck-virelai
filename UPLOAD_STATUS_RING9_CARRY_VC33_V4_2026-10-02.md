# Upload status: ring9-carry-vc33-v4 (v3 pinned to v2's Kaggle image)

**Date:** 2026-10-02
**Author:** Claude (Alpha build seat), signed
**Packager:** `tools/package_ring9_carry_vc33_v4.py`

## Why v4 exists: v3 failed in setup, and the cause was Kaggle's, not ours

v3 (`taaf-virelai-ring9-carry-vc33-v3`, version 1) stopped while installing the wheelhouse:

```
ERROR: Could not find a version that satisfies the requirement aiohttp==3.13.5 (from versions: none)
```

Everything before that worked:
- both self-hosted datasets resolved under `/kaggle/input/datasets/stephenkaskin/…`;
- the GPU check passed (`NVIDIA RTX PRO 6000 Blackwell Server Edition`).

**The cause: Kaggle's notebook image changed between v2 and v3.**
- v2's log (earlier on 2026-10-02) shows only `python3.12` paths.
- v3's log shows `/usr/lib/python3.13/…` and `/usr/local/lib/python3.13/dist-packages/…`.
- The wheelhouse is the exit run's, built for Python 3.12. 42 of its 174 wheels are compiled for cp312. pip on 3.13 rejects them, and `aiohttp` is the first one in lock order.

**This is an infrastructure fault, not a code or plan fault.** It affects every Ring 9 package pushed without a pin, the NAV seat's included.

## The fix in v4: pin the image v2 ran on

`kaggle kernels pull stephenkaskin/taaf-virelai-ring9-carry-vc33-v2 -m` returned v2's image:

```
docker_image: gcr.io/kaggle-private-byod/python@sha256:37c64f7dd9c54116ecd1bcc88817c5469b88387388fade02bfa8bf3fc647d461
machine_shape: NvidiaRtxPro6000
```

v4's notebook metadata sets that `docker_image` and `docker_image_pinning_type: "original"`. The Kaggle CLI (2.0.0) sends both with the push. The checkpoint and both receipts record the environment.

**Everything else is v3's:**
- source `fbea80c` (`fbbc7f4` plus R9-R20);
- the self-hosted wheelhouse and model;
- the world, budgets and criteria.

File by file against v3, no source file differs; only identities, the notebook metadata, the docs and the digests do.

**New preregistered criterion, I8:** the log shows Python 3.12 paths and the 174-wheel install succeeds. A Python 3.13 path means the pin was not honoured.

## Verification (cloud)

| Check | Result |
|---|---|
| `verify_kaggle_package.py --source-export` (fbea80c) | **8/8** |
| Mount simulation, three layouts | **All pass** |
| Level-entry pre-flight on the shipped source | **G0, then G1, then G2 first click, all by the controller (exit 0)** |

| Field | Value |
|---|---|
| Package manifest sha256 | `b2f402666b270b591b73d8df52ac602e8fd3051c70d7a48cfb7ef8dcde019ade` |
| Source manifest sha256 | `522740a73470a6afda42b1e8a90eae8372d380fdf70209cc2688b5f3d5f03e8c` |

## Risks

1. **Kaggle may refuse the pin.** The image is a `kaggle-private-byod` image, and the API says the image "must be one of the Kaggle-provided, known images". It is the image Kaggle itself assigned to v2 this morning, so I expect it to be accepted.
   - If the push is refused, or the log still shows 3.13, the fallback is the wheelhouse hardening already checked: the same 174 versions resolve on Python 3.13, and only the 42 compiled wheels need cp313 builds, all on PyPI.
   - That fallback also needs the solver tested on 3.13, which it never has been.
2. **"original" pinning:** "original" pinning keeps this image for later versions of this notebook. Whether Kaggle eventually retires old images is unknown.

## Director's steps

1. Put the package in place (I'll do it); `verify_kaggle_package.py` on the Mac.
2. Commit on `main`, staging explicit paths.
3. `kaggle datasets create -p kaggle/ring9-carry-vc33-v4/source-dataset -r skip`, then `status` until it says `ready`.
4. `kaggle kernels push -p kaggle/ring9-carry-vc33-v4/kernel`

— Claude, Alpha build seat, 2026-10-02
