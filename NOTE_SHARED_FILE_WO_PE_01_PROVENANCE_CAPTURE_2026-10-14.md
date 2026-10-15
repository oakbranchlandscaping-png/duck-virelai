# Shared-file note: WO-PE-01, provenance capture (2026-10-14)

**Filed by:** Claude, Alpha build seat, **before any shared edit**
**Base:** `ring9-unified` at `a925d7f`
**Interface:** `INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v1_2026-10-14`
**Integration owner:** Claude, for every file below

| File | Function | Planned change |
|---|---|---|
| `inference/framework/provenance.py` (**new, neutral**) | <ul><li>`ProvenanceJournal`</li><li>`read_journal`</li><li>`validate_rows`</li><li>`translate_g3_event`</li><li>`field_sources`</li></ul> | The journal contract |
| `inference/agent/provenance_capture.py` (**new**) | one function per capture point | Agent-side glue. It never raises. |
| `inference/agent/tool_agent.py` | <ul><li>`__init__` (a new `provenance_enabled` keyword, default `False`)</li><li>`_gate_probe_begin`</li><li>the gated `action()` handler</li><li>`gate_answer` dispatch</li></ul> | <ul><li>ADMISSION rows on admit or refusal.</li><li>EXECUTION rows.</li><li>The answer is split as prepare, then submit.</li></ul> |
| `inference/agent/controller_turn.py` | <ul><li>`_controller_answer`</li><li>`_controller_action`</li></ul> | <ul><li>The answer is split, with `executor=CONTROLLER` passed to the gate.</li><li>EXECUTED or NOT_ATTEMPTED after the environment call.</li></ul> |
| `inference/agent/memory_queries.py` | <ul><li>`_chosen_probe`</li><li>`_submit`</li></ul> | <ul><li>The G3 refusal raised before `select`.</li><li>Note submissions.</li></ul> |
| `inference/framework/virelai_gates.py` | <ul><li>`CyberneticGateMachine.submit_answer`</li><li>new `prepare_answer` and `submit_prepared`</li><li>`_LeverTarget.submit_answer`</li><li>`_submit_reachability`</li></ul> | <ul><li>The behaviour-preserving split.</li><li>The real executor reaches the lifecycle actor (defect 2).</li></ul> |
| `inference/framework/solver.py` | <ul><li>`_make_analyzer` (the `ToolAgent` construction)</li><li>`play`'s `finally`</li><li>new `_close_provenance`</li></ul> | <ul><li>`VIRELAI_PROVENANCE` (default on).</li><li>Flush G3 events, drain, seal, warn (defect 1).</li></ul> |
| `tests/test_provenance_capture.py` (new), `tests/tiers/test_tiers.toml`, `tests/tiers/T2_collected.txt` | — | <ul><li>The fail-first suite.</li><li>T0 `provenance`.</li><li>T1 `paper-evidence`.</li><li>The snapshot gains its ids.</li></ul> |

**Unchanged:**
- `world_model_v2.py`, `library_census.py`, `descriptive_events.py`, `world_description.py` and `world_report.py`;
- `g3_selection.py`, `annotation_lane.py` and `card_builder.py`;
- every gate admission rule, the scheduler, targeting and action choice;
- every accepted test and golden.
