# Shared-file note, 2026-10-11 (WO-L2a close-out and the library view)

**Filed by:** Claude, Alpha build seat (click line), **before any shared edit** (ruling 9).
**Directive:** Sol's rulings on the three hooks findings, relayed by the Director on 2026-10-11, and the next slice:
1. close the live free-play check and controlled-stop labelling;
2. then build the card digest and retrieval from the validated library.

**Base:** `main` = `ring9-unified` = `472aa32` (pushed). The Mac floor there is 683 passed, 1 skipped.

| File | Function | Change |
|---|---|---|
| `inference/framework/solver.py` | `_HarnessGameSession.play`, at the turn-end `break` (`:595-596`) | One call that records why the run ended, at the moment a turn ends the game. A controlled stop that rests the gates goes through `_rest_after_controlled_stop` (`:593`) and never reaches this line. |
| same | `_l2a_persist_reason` (`:349-360`) | The recorded `CONTROLLED_STOP` comes after CRASH and CANCELLED and before the budget test. |
| same | new field `_l2a_end_reason` | Holds that reason |
| `inference/agent/tool_agent.py` | `ToolAgent._gate_context_update` (`:1527-1539`) | Appends the library digest after the binding card, in Duck's per-turn prompt only. Neither the controller path nor `build_card` (used by replay measurement) compiles the census. The 24,000-character guard on the card is unchanged; the digest has its own budget. |
| same | new module-level `_library_digest_section(machine)` | The digest text, or a one-line "unavailable this turn" if the census fails. It never raises. |
| `tests/test_memory_m0.py` | `test_the_harness_measures_the_production_renderer` | Its byte-equality becomes "the card comes first, unchanged; the library section follows". The replay harness still measures the card bytes exactly. |
| `inference/agent/memory_queries.py` | `gated_memory_query` (`:50-92`) | New read operation, `virelai('library', kind=…, id=…, reason=…, subject=…, level=…, part=…, offset=…, limit=…)`, answered from the validated live library. Every reply is bounded, and a partial reply names its `next` call (revision 2, after Sol's review). |

**Not shared** (mine):
- `library_census.py`, `world_model_v2.py`, and `PERSIST_REASONS` gaining `LIVE_VIEW` for the in-memory view, which is never written to disk;
- the new `library_view.py`;
- new tests.

**Untouched:**
- the recording path (`record_outcome`, `transition_index_row`), because the live free-play test passes without a change (see the build note);
- `virelai_gates.py`, `life_record.py`, `virelai_runtime.py`, `card_builder.py`;
- the shared G3 admission path, which stays for its separately reviewed design;
- SUB-4.
