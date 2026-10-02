# Ring 9 cross-level, vc33 (v2: self-hosted dependencies)

Source commit `fbbc7f4a9f1decc669d2aa599dc37903a4431e90` (R9-R06 to R9-R18). This private diagnostic runs the gated agent on `vc33-5430563c`, one pass, with at most 200 environment actions and 10800 seconds of behaviour time after model setup. Same model and per-world budget as `ring9-g4-exit-v1`.

v2 differs from `ring9-carry-vc33-v1` only in where the vLLM wheelhouse and the model come from. v1 stopped in setup because `driessmit1/arc3-vllm-h100-wheelhouse-v3` and `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot` became unreadable; v2 mounts the Director's own `stephenkaskin/virelai-vllm-wheelhouse-v3` (the same 174 wheels, PyPI digests) and `stephenkaskin/virelai-qwen3-6-27b-fp8` (`vrfai/Qwen3.6-27B-FP8` at commit 70462b01; the weights have one version). Served model name, context length, parsers and install stamp are unchanged. Dependency record: `{"chat_template_kwargs": "{\"preserve_thinking\": true}", "max_model_len": 65536, "model": "stephenkaskin/virelai-qwen3-6-27b-fp8", "reasoning_parser": "qwen3", "served_model_name": "vrfai/Qwen3.6-27B-FP8", "stamp": "vllm==0.19.0 torch==2.10.0 flashinfer==0.6.6\n", "tool_call_parser": "qwen3_coder", "wheelhouse": "stephenkaskin/virelai-vllm-wheelhouse-v3"}`.

The question: when a level ends, does the machine freeze what it established, restart its ladder on the next level's board, and test what it carried there, without carrying any verdict? In `ring9-g4-exit-v1`, vc33's G4-A study completed level 1 at transition 26 and the run stopped (cross-level work was not built).

## Preregistered grading (from artifact state, not prose)

- Gate criteria are graded only when the run reaches that gate; a stall earlier leaves them ungraded, not failed. All measurements come from artifact state (turn ledger, gate events, gate answers, probe envelopes, annotations), not from prose.
- One world, vc33. Level-1 criteria repeat the exit run's; the new criteria are X (cross-level) and L (lives).
- M5-1 (axiom A6): no binding card exceeds the 16,200-character slot budget, and the 24,000 guard never fires. M5-2: G0 through G4.1 close with zero model calls on each level; Duck's first turn on each level is the orientation, accepted within 2 turns.
- G2/G3 (level 1): as in ring9-g4-exit-v1 (counter EVERY_TRANSITION, 2 levers witnessed). On level 2: a counter model and mask certified again (ruling: G0-G2 run again), and G3's levers witnessed on level 2's own evidence.
- A (G4-A): every lever ends CONFIRMED or DIVERGED with an accepted explanation, or interrupted; the LeverOrbitSet COMPLETE or CLOSED_BY_LEVEL_BOUNDARY.
- X-1 (level freeze, R9-R17): if level 1 ends, LevelModel(1) is frozen at that transition from the gate machine's own record, with its products, lever roster and, if won, the win record (action, acted lever, earlier same-action failures, hypothesis UNTESTED). The run does not stop: the ladder restarts at G0 on level 2, and every later row is tagged level 2.
- X-2 (carry, R9-R18): at level-2 entry, every carry candidate is frozen (declared_at_transition = the entry transition) before any level-2 click; each is graded only by a level-2 click after level 2's counter mask is certified, never on a terminal transition; RECONFIRMED means a masked change with the carried locality. Grades re-derive from the frames. Reported: candidates, RECONFIRMED, FALSIFIED, UNCONFIRMED (never clicked), not found.
- X-3 (no verdict carried): no level-2 product exists before level 2's own gate certifies it; G3 certifies level-2 levers on level-2 evidence, whatever the carry says.
- L-1 (life record, R9-R16): every death is a RESET row that opens the next life; a G4-B or G4-C prediction taken on a transition that ends a life or a level is INDETERMINATE, not graded.
- B/C (G4-B, G4-C), if reached on any level: as in ring9-g4-exit-v1.
- E: the run ends with solver_note 'planned_stop:' (ladder through G4-C, or a level change with no lossless board), or by the action or time budget; never crashed. No model request after a planned stop.
- N-1 (axiom A2): no gate idles without a legal move.
- R (reported, not graded): actions and Duck time per level; level-2 lever count, classes and types versus level 1; the carry line Duck saw; whether a second level was won and by whom (controller or Duck); the level-1 win record verbatim. A level won by the G4-A study is the study's, not the model's: the review must not credit it to the model.
- I0: the shipped source holds no tools/live_level_carry_gate.py and no world name in the solver's executable code other than the harness's public game roster (packager guard).
- I1: G0 assigns CLICK/God Mode from metadata, and the controller executor is on (probe envelopes carry executor CONTROLLER and the protocol stamp g3_inherits_g2_nulls true).
- I2: the downloaded execution receipt is byte-identical to the package receipt.
- I3: the run writes the memory artifacts: turn ledger, gate answers with executor, and annotations if Duck oriented.
- I4: with the counter masked, G4-A runs record nulls and recurrences without counter contamination.
- I5 (self-hosted dependencies, v2): the setup log names the wheelhouse and model paths under stephenkaskin's two datasets, pip installs from the wheelhouse with no index, and vLLM serves vrfai/Qwen3.6-27B-FP8, its weights taking about 33.7 GiB as in ring9-g4-exit-v1.
- I6 (comparability, v2): until Duck's first action of its own, vc33 level 1 repeats the ring9-g4-exit-v1 actions in order; a difference before Duck acts is attributed to the environment and named in the review, never read as Duck's behaviour.

Baseline for behaviour only: `ring9-g4-exit-v1` vc33 (26 actions, level 1 won by the G4-A study of E0005, 7 earlier same-click failures). The controller is deterministic until Duck acts on its own turn, so level 1 should repeat that run unless Duck intervenes.

Request preflight (T10): worst case 33158 tokens against a 65536-token window, for one request.

Dataset: `stephenkaskin/taaf-duck-virelai-ring9-carry-vc33-v2`  
Notebook: `stephenkaskin/taaf-virelai-ring9-carry-vc33-v2`

The notebook verifies the mounted source manifest and execution receipt before the benchmark starts. This is not a score comparison or competition submission.
