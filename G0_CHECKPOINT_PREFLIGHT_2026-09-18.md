# G0 checkpoint preflight

> **Historical preflight with completed outcome:** A later G0 v2 Kaggle run confirmed this gate on
> vc33, ft09, and ls20. Use `CURRENT_STATUS_AND_FULL_BUILD_PLAN_2026-09-20.md` for the evidence and
> current build frontier.

The G0 action-metadata checkpoint is locally complete and frozen at `kaggle/ring9-g0-checkpoint/`.

- Worlds: vc33, ft09, ls20.
- Model: the existing Kaggle Qwen3.6-27B-FP8 snapshot.
- Execution: one pass, sequential, one environment action per world.
- Gate: Duck must exactly acknowledge the current opaque action inventory and coordinate requirements, make no semantic action claims, and state that effects remain unknown before G1 opens.
- Validation: 181 tests pass; 136 uploaded files are covered by the source manifest; every hash verifies; required mount metadata is present.
- Egress audit: no private-key, OpenAI-key, Kaggle-key-field, or bearer-token patterns were found in the 2.4 MB package.
- Claim limit: a pass validates G0 compliance and ordered entry into the first G1 probe. It does not validate ego discovery.

The intended external destinations are the private Kaggle dataset `stephenkaskin/taaf-duck-virelai-ring9-g0-checkpoint` and private notebook `stephenkaskin/taaf-virelai-ring9-g0-checkpoint`. It is not a competition submission.
