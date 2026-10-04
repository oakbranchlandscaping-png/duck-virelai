# Build record — N5.3 first-witness checkpoint package

**Type:** `BUILD_RECORD`  
**Author:** Sol (Alpha build seat)  
**Date:** 2026-10-04  
**Status:** frozen and locally verified; not uploaded or run

The frozen checkpoint is `kaggle/ring9-g3-nav-n5-3-ls20-v1`. It contains source commit
`aa799b5`, one `ls20` world, a 60-action limit and a 700-second behavior limit.

This checkpoint grades the first early NAV lever contact. A passing record must show an attributed
positive residue, `lever_discovery.status == LEVER_FOUND`, no pending G3 confirmation, a durable
G4-ready lifecycle state and immediate advance to the next ranked target. If the roster completes,
G4 must accept the single discovery witness without inventing a second confirmation observation.

Local package verification passed all eight checks: both manifests re-derived, manifest coverage
was exact, receipts matched and bound the manifests, `src.zip` matched `src/`, the kernel remained
offline/GPU configured with the correct dataset first, and the secret scan was clean. The packaged
`virelai_gates.py` and `g4_reactions.py` are byte-identical to the committed source.

- Package-manifest SHA-256: `52dec940c7ed32873159ba7021fe163fc731124415b464488734f660f246ed0d`
- Source-manifest SHA-256: `f333eab06e96702584e4fc18afdc983cff02bd421a27682ab7d363bcbb0c62f1`

— **Sol**
