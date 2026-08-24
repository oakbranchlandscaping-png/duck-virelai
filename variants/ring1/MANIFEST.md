# Variant: ring1 — the Virelai ledger insert

**Created:** 2026-08-24 · **From:** `baseline/` (66-file freeze, agg md5 `0e8c547a…`),
copied and verified at 66 files before edit · **Ruling basis:** R-H1 (rebuild-fresh),
CHAMBER_BOOTSTRAP Ring 1 (threader + digest + Tier-A), Director's sequencing ruling
2026-08-24 (Ring 1 before Ring E).

## The one variable

A per-game walked-edge ledger recording `(state-hash, action) → (state-hash, changed?)`
each turn; from it, per node: a ≤100-token `[MAP]` digest injected beside the menu, and
Tier-A subtraction of actions proven no-op at the current state. Disable with
`VIRELAI_RING1=0` (byte-path equivalent to baseline behavior).

## Diff surface (vs frozen baseline)

| file | change |
|---|---|
| `ARC3-Inference/inference/framework/virelai_ledger.py` | **new** — ledger, Tier-A seal, digest (stdlib only; design origins cited in module docstring: induced_map node key/untried, frontier_tag label shape — read, not copied, per R-C) |
| `ARC3-Inference/inference/framework/solver.py` | +1 import; `previous_level` capture; ~15-line Ring 1 block at end of `_execute_action`; `_virelai()` lazy accessor |
| `ARC3-Inference/inference/agent/tool_agent.py` | `_compact_action_result` carries `virelai_digest`; `_build_user_prompt` renders it (one line, above the menu) |

Delivery path: the solver prunes `payload["valid_actions"]` → flows unchanged into the
prompt's "Valid actions right now" line AND the sandbox runtime state (both read the
payload). Subtraction, never annotation; the digest is the single sanctioned surface.

## Laws honored

- Tier A is ratio-free: tried-and-never-changed-board at THIS node; recomputed every
  turn; a later observed change un-seals. MOUSE and RESET never pruned (per-coordinate
  is a later rung). Fail-open when pruning would leave no playable non-RESET action.
- Post-RESET amnesia: dissolved by the node key itself (RESET lands on a known hash).
- Budget: measured 2026-08-24 in cloud workspace — record 0.285 ms/edge (incl. sha256),
  menu+digest 0.007 ms; MATCH on this container's clock, NOT_MEASURED on Kaggle.
- Firewall: keys are hashes; no world name/colour/content leaves the game; ledger dies
  with the GameSolver.

## Verification at creation

`py_compile` clean on all three touched files; solver imports against the baseline venv
(arcengine present); unit scenario covers seal, un-seal, fail-open, RESET-reattach.
**End-to-end behavior NOT_MEASURED until a Kaggle run.** Verdict protocol: first public
run is a smoke + directional read against run #1 (1.2225 all-25); a bootstrap-grade
verdict needs ≥2 runs per arm.
