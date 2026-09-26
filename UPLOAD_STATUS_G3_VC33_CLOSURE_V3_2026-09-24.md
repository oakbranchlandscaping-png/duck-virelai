# Ring 9 G3 vc33 reset-continuity v3 upload status

**Prepared:** 2026-09-24  
**Status:** notebook version 1 completed; output downloaded and reviewed; G3 checkpoint failed with two confirmed lever discoveries

- Dataset: `stephenkaskin/taaf-duck-virelai-ring9-g3-vc33-closure-v3`
- Notebook: `stephenkaskin/taaf-virelai-ring9-g3-vc33-closure-v3`
- Package manifest SHA-256: `dc32fd3391daaf6be3fd42a1bdf39c4f24e7fc42e15cb428a55b4241af85cab8`
- Source manifest SHA-256: `c2a764e61a2760ea40121862511571aa683ce810236a2b61d4d1130be480e9c0`
- Model: `vrfai/Qwen3.6-27B-FP8`
- World: `vc33-5430563c`
- Budget: 96 environment actions and 2,700 seconds after model setup
- Validation: 333 complete tests, 54 focused tests, changed-file lint, 192 source hashes,
  199 package hashes, receipt equality, notebook identity, and source-archive presence

The v1 and v2 package and execution directories remain unchanged. After explicit authorization
for this exact payload, the private dataset was created and reported `ready`; notebook version 1
was pushed and completed successfully. The downloaded receipt is byte-identical to the frozen
receipt.

Behavioral result: G3 found and prospectively confirmed two remote levers at ranks 4 and 5, then
looped for 31 actions on rank 6, the already identified counter object. The gate remained active,
ranks 7 through 11 were not attempted, and no aggregate inventory was produced. This is a G3 exit
failure, not a level-play result. See
`runs/kaggle-ring9-g3-vc33-closure-v3/REVIEW_2026-09-24.md` and the generated certificate in the
downloaded output.

- Dataset: <https://www.kaggle.com/datasets/stephenkaskin/taaf-duck-virelai-ring9-g3-vc33-closure-v3>
- Notebook: <https://www.kaggle.com/code/stephenkaskin/taaf-virelai-ring9-g3-vc33-closure-v3>
