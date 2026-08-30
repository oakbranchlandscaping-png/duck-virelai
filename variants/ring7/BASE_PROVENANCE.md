# Ring 7 base provenance

Ring 7 is the MINIMAL HYBRID: the pristine baseline Duck plus the Captain
probe and the Ring 6.3 handshake — nothing else.

ARC base: seeded from the exact executed tree of the frozen-baseline r0 run
(`duck-virelai-r0-dryrun`, mean 1.22 / total ~30.5, 2026-08-23):

`kaggle/dryrun-r0/source-dataset/src/ARC3-Inference/`

Grafted from `variants/ring6.3/ARC3-Inference` (anchor f36c149, transport
proven 25/25 in runs/kaggle-ring6.3-run1):

- `virelai_v4/` (whole package, unchanged) + pyproject include line;
- `inference/framework/virelai_handoff_v63.py`, `virelai_field_card_v6.py`,
  `virelai_probe_contract.py`;
- solver.py: `_virelai_opening`, `_ring6_marker`, `_ring63_*` audit/persist
  methods, `_frame_data`, `_card_dict_from_captain` + its four `_ring6_*`
  render helpers + regex constants, `_atomic_write_*`, the two `play()`
  hunks (probe call; card + observer kwargs), the `DUCK_FIRST_ACTION`
  marker in `_execute_action`, and a module logger;
- tool_agent.py: `virelai_card`/`request_observer` params, invocation
  counter, yield-resume containment via `history_contains_report`,
  card append gated ONLY on the explicit argument, request-id context,
  observer-instrumented `_chat_completion` (6.3's verbatim).

DELIBERATELY ABSENT (the whole point of the ring): the ARC Grid Multiverse
Ontology; ring 1–5 machinery (ledger, [MAP] digest, counter seal, weave,
`virelai`/`virelai_card()` runtime views, `_virelai_state`); every prompt
edit — `inference/agent/prompts.py` and `python_tool_sandbox.py` are
byte-identical to the r0 baseline (asserted by test).

Excluded during seeding: `__pycache__`, `*.pyc`, `* 2`/`* 3` duplicates.
Battery: 37/37 (ring6.3 suite; ontology test replaced by the ring 7 prompt-
purity contract). One variable vs r0: the Captain report in Duck's first
user turn.
