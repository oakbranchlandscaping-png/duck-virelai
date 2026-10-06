# Review — Ring 9 unified ls20 v1 Kaggle canary

**Type:** `EXECUTION_REVIEW`  
**Run:** `stephenkaskin/taaf-virelai-ring9-unified-ls20-v1`  
**Package commit:** `232a502`  
**World:** `ls20-9607627b`  
**Model:** `vrfai/Qwen3.6-27B-FP8`  
**Reviewer:** Sol, Alpha build seat (NAV line)  
**Date:** 2026-10-06

## Verdict

The notebook completed cleanly, verified the package, and closed G1 and G2. It did not execute a G3 action. The run therefore validates the pinned Qwen3.6 serving stack and the G0–G2 handoff, but it supplies no live evidence for first-witness lever discovery, target release, reopening, roster completion, or G4 opening.

The blocking fault is at the G1-to-G3 machine boundary. G1 accepted correct prose movement laws while retaining an empty `action_law_specs` map. The deterministic NAV controller consequently had no certified bearing. Its one-request fallback asked Qwen3.6 for a forced Python action with `max_output_tokens=256`; the model consumed all 256 tokens, returned `finish_reason=length`, and emitted neither visible content nor a tool call. The route checkpoint then stopped the run exactly as configured.

This is not evidence that E0001 is unreachable, that the target roster is wrong, or that ls20 lacks a lever. No contact was attempted.

## Direct observations

- Kaggle status: `COMPLETE`.
- Behavior interval: 5 minutes 43 seconds.
- Result: 0/7 levels, score 0.00, 12 environment actions.
- Source manifest verified: 230 files.
- Downloaded execution receipt is byte-identical to the packaged receipt: SHA-256 `722a9d515e9b7112e32b9a9d10d9afa35ba4849861bbe8b439bb80dc6cc12d50`.
- The pinned Python 3.12 wheelhouse installed 174 wheels; vLLM 0.19.0 served `vrfai/Qwen3.6-27B-FP8` from the Director's dataset with a 65,536-token model window.
- G1 used eight controller actions, then Duck supplied an embodied-ego explanation and a prospective demonstration. The demonstration closed G1 at transition 9.
- G1's accepted answer described all four motions as exact five-cell translations, but its stored `action_law_specs` was `{}`.
- G2 found the 84-cell two-row counter footprint, observed `11->3` at two cells per transition, demonstrated the prediction, locked the counter as the mask baseline, and closed at transition 12.
- G3 enumerated an eligible roster of 16 and bound rank-one target E0001/M0009 at `[32,20]`.
- G3 recorded zero navigation steps, zero contacts, zero accepted evidence, and 20 untouched ledger entities.
- The final request used `tool_choice=required`, thinking disabled, and a 256-token output cap. It returned `finish_reason=length`, 256 generated tokens, zero tool calls, and no action.
- The run emitted `G3_ROUTE_RETRY_EXHAUSTED` and ended under the controlled-stop path. It did not enter PLAY-NORMAL.

## Preregistered G3 grades

| Criterion | Grade | Evidence |
|---|---|---|
| N-1: first positive contact immediately emits `LEVER_FOUND` | **UNGRADED** | No G3 contact occurred. |
| N-2: accepted releases become bounded `PRESUMED_UNREACHABLE` | **UNGRADED** | No reachability release occurred. |
| N-3: release reopens only after a relevant signature change | **UNGRADED** | No release or reopening occurred. |
| N-4: roster completes within the canary budget | **FAIL** | G3 stopped with every ledger entity untouched. |
| N-5: accepted inventory opens G4 | **FAIL** | `g4_legal_open=false`; final gate was G3. |
| N-6: no PLAY-NORMAL caused by an unbounded released target | **PASS, VACUOUS** | PLAY-NORMAL was never entered, but no target was released. |

N-1 through N-3 must not be called failures because their triggering events never occurred. N-6 confirms the stop discipline, not reachability handling.

## Infrastructure grades

- **I0 PASS (package preflight):** the package manifest contains neither `live_level_carry_gate.py` nor an executable ls20 world-name dependency.
- **I2 PASS:** packaged and downloaded execution receipts are byte-identical.
- **I3 PASS:** turn ledger, gate answers, probe envelopes, probe outcomes, and gate events were written.
- **I5 PASS:** the setup log identifies the Director's wheelhouse and Qwen3.6 model datasets and the served model name.
- **I8 PASS:** the pinned Python 3.12 environment installed successfully.
- **I11 PASS:** the gate did not idle. The bounded route checkpoint stopped after its configured single failed request.
- **U-SRC PASS:** the log reports `source manifest verified (230 files)`.

## Supported diagnosis

The live failure exposes a contract mismatch:

1. `_answer_from_mapping` permits `action_laws` as a mapping of action names to prose.
2. `_normalize_action_law_specs` only creates structured specs when `action_laws` is a list of objects containing fields such as `displacement`.
3. G1 can close with prose laws and no structured specs.
4. `compile_nav_control_map` requires structured displacement or a uniquely recoverable translation from lossless outcomes.
5. The live prospective prediction scoped only two representative ego cells. That partial pattern was insufficient for unique recovery in the repeated-color body.
6. Synthetic NAV foundation tests provide structured `action_law_specs`, so they did not exercise the production answer shape that failed here.

The 256-token route fallback is a second fault. It converted a recoverable missing-bearing condition into an immediate run stop. The prompt was only 7,154 tokens, far below the context window; context exhaustion is not supported. Output exhaustion is directly observed.

## Recommended next slice

Repair the certified control boundary before another Kaggle run:

1. deterministically compile the four observed G1 displacements from the opening probe evidence and persist them as structured action-law specs;
2. require a nonempty certified bearing map before G1 may hand a NAV world to G3, or keep the controller in G1 until that machine-readable product exists;
3. add a regression fixture using the exact live Qwen3.6 answer shape, with prose `action_laws` and no prefilled structured specs;
4. verify that the controller selects the first G3 approach action without a Duck call;
5. retain the route checkpoint only for genuinely ambiguous navigation, and give that fallback enough output budget to emit one tool call rather than treating a 256-token truncation as evidence about the world.

The next canary should remain ls20 and stop after proving that G3 executes the rank-one target through at least one real approach/contact disposition. A full roster sweep is unnecessary until this boundary is repaired.

— Sol
