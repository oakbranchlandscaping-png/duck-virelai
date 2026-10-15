# Build slice: WO-PE-01 provenance capture, revision 4 (2026-10-14)

**Seat:** Claude, Alpha build seat. **Reviewer:** Sol. **Executor of record:** the Director.
**Base:** revision 3, on `ring9-unified` at `a925d7f`. This archive **replaces revision 3** for extraction.
**Governing:** the revision-4 correction order, which restores the controller probe boundary. `INTERFACE_WO_PE_01_PROVENANCE_CAPTURE_v3_2026-10-14` remains the current interface; revision 4 changes no contract.
**Status:** parked. **Not committed. Cloud T2 not run**; the Director runs the Mac T2 floor after applying revision 4.

---

## 1. The correction (one production line)

In `inference/agent/controller_turn.py` `_controller_action`, the explicit `submitted=` keyword is removed from the `_gate_probe_begin` call. The locally built `decision` is kept, and the call returns to the established controller shape:

```
agent._gate_probe_begin(state_path, machine, decision, [step.action], executor=CONTROLLER)
```

`_gate_probe_begin` already builds the same proposal, `{"actions": normalized_actions, "decision": decision}`, when `submitted` is absent. For the controller, `normalized_actions` is `[step.action]`, so the journaled `submitted` value is unchanged.

Duck's path is untouched. It still passes `submitted=` explicitly, which keeps the representation as it crossed the tool boundary.

## 2. Fail-first and focused results

**Fail-first:** the existing T2 case `tests/test_sub2_submission_hardening.py::test_d2_a_refused_controller_probe_rests_the_level_instead_of_spinning`. On revision 3 it **failed** with `assert 0 == 1` on `calls["step_env"]`, reproduced in the cloud with the tree verified as the revision-3 slice (10 of 10 hashes). No test was added and the snapshot is unchanged. `failfirst_pe01_rev4_t2_case.txt` holds the output.

| Check (revision 4) | Result |
|---|---|
| That case | **1 passed** (the whole file: 8 passed) |
| Full provenance test file | **49 passed** |
| T0 `provenance` | **76 passed** (61.4 s) |
| T1 `paper-evidence` | **265 passed** (371.5 s) |
| Manifest exactness | T2 975 tests, **exactly the snapshot**, unchanged from revision 3 |
| Cloud T2 | not run, as directed |

## 3. Journal bytes are unchanged

`JOURNAL_BYTES_rev3_vs_rev4.txt` holds the comparison.

- **Controller fixture**, run to Duck's first turn (67 environment calls, fixed capability secret, capture on): every artifact, **including the provenance journal (`7b5a8f3f0171f013`)**, is byte-identical between revision 3 and revision 4.
- **Capture off:** revision 4 is still identical to `a925d7f` across environment calls and every artifact.
- **Examples:** all of them, and `READS.json`, regenerated on revision 4 are byte-identical to revision 3's. That includes `example_refused.jsonl`, whose refused **controller** probe admission row, `submitted = {"actions":[{"action":"ACTION1"}],"decision":{"probe_token":"CAPABILITY:NOT_ISSUED"}}`, is the row this path writes on refusal.

## 4. Changed files and hashes

Revision 3 → revision 4 changes **one file and one line**. The ratchet improves by one line: `_controller_action` NCNB goes from 60 to 59.

| File | vs revision 3 | sha256 (revision-4 slice) |
|---|---|---|
| `inference/agent/controller_turn.py` | **−1 line** | `6e63d180329cd8e37632aac7fd3f6d58851221ee3692b0de07a7cee8a5630e41` |
| `inference/framework/audit_journal.py` | unchanged | `b360d5d23a77c1c44c9ad106ab726f94d68ef9a06c6f332b66f06223bba6809b` |
| `inference/agent/provenance_capture.py` | unchanged | `7496a4c595eb2201b9891e0eae302fa84fa4670f488234382d8d27a146d7a6e4` |
| `inference/agent/tool_agent.py` | unchanged | `375c9c033afc548909b5de687e97d8cbd78ddc26605e9c152bbc4f23583b542c` |
| `inference/agent/memory_queries.py` | unchanged | `e70098fac4ebc11d2041812a0b3dc7e144b87102e87b1bd6434a5349ebc11f7e` |
| `inference/framework/virelai_gates.py` | unchanged | `c97a0f4ed7dcf6264de3a7a0430f9d365d7a55dd24dcdb57452e43926ccd64b0` |
| `inference/framework/solver.py` | unchanged | `70f0394505734b4d7b8e6c7ee7835403b719d2012dc616a3fd10ebf6d3395409` |
| `tests/test_provenance_capture.py` | unchanged | `6d5e49b9f17ac0b574286383d0844990fe9973289292afe2724c4d277f6e1406` |
| `tests/tiers/test_tiers.toml` | unchanged | `5cc3ae7ff57712bdf5b2e5cd36864b0ea14d33fbc9daec428890d8bb40c108d9` |
| `tests/tiers/T2_collected.txt` | unchanged | `e83413fd4db0f621e00d75516a041931b2ac228a9c155980f5db504a78c4f50a` |

**Packaging:**

| File | sha256 |
|---|---|
| `WO_PE_01_REV4_slice.tar.gz` (the ten files; `SLICE_SHA256SUMS` lists them) | `5c15e17a646078fd6ebd10e3a1d2f5c69af6f0eed8f0ae7842afdc632142f364` |
| `WO_PE_01_REV4_a925d7f.diff` (the full slice against `a925d7f`) | `bced8acaf73a45c894f8dd40adfcaac86c65e0191a927c8510d2f2c0ddf4f24a` |
| `REVISION_4_DELTA_rev3_to_rev4.diff` | `186e6e707a138f0ac0cd4b0c1c354145062ba087efd11d6dbd798e2948be6cf7` |

All three apply paths reproduce the ten hashes in the cloud:
- extracting the tarball;
- applying the full diff to the `a925d7f` base;
- applying the delta to the revision-3 slice.

## 5. Everything else

Everything else stands as reported in revision 3: the seal's run identity, cross-run reopening, admission joins, strict JSON, the finalization order, the performance figure (≤ 0.534 s per 400 operations) and the examples.

**The other two Mac T2 failures** were sandbox-only. That rests on the Director's evidence: both process-cleanup cases passed outside the restricted sandbox, 2 passed in 1.62 s. Revision 4 does not touch them.

## 6. Parked files

All are under `runs/_cowork_xfer/pe01r4/`:
- this report;
- `WO_PE_01_REV4_slice.tar.gz`, `SLICE_SHA256SUMS`, `WO_PE_01_REV4_a925d7f.diff` and `REVISION_4_DELTA_rev3_to_rev4.diff`;
- `failfirst_pe01_rev4_t2_case.txt`, `T0_provenance_*`, `T1_paper_evidence_*` and `packaging_recheck.txt`;
- `JOURNAL_BYTES_rev3_vs_rev4.txt`;
- `examples/`, byte-identical to revision 3's.

**Extract only revision 4.**
