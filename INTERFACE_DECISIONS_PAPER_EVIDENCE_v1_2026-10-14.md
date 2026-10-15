# Proposed interface decisions: paper-evidence layer

**Type:** `INTERFACE_DECISIONS_PAPER_EVIDENCE` · v1 · 2026-10-14 · proposal only
**Author:** Claude (Alpha build seat)
**Source:** `PRIOR_ART_PAPER_EVIDENCE_PROVENANCE_GRADING_v1_2026-10-14.md` §8. Evidence and citations are in that document's §2-§7.
**Base:** `ring9-unified` at `a925d7f`

Nothing here is decided. Each row names what must be ruled before a WO-PE interface can be written, the options found, and what the sweep showed. No answer key is authored here.

## Decisions for Sol's rulings

| # | Decision | Options mapped | What the sweep shows | Altitude / owner |
|---|---|---|---|---|
| D1 | Provenance storage | A (schema-v4 chapter), B (hashed append-only record), C (reconstruct), A+B | C cannot recover refusals (§4). A alone loses everything since the last write on a hard kill. B alone splits authority unless the model stamps the record's hash. | architecture / Sol |
| D2 | Event vocabulary | Reuse G3's (ADMITTED / REFUSED / HANDOFF / …), or one vocabulary across gates (PROPOSED / ADMITTED / REFUSED / EXECUTED / ANSWER_ACCEPTED / ANSWER_REFUSED / …) | Only G3 has a structured vocabulary today. Answers and probes have none for refusals. | architecture / Sol |
| D3 | Interception points | <ul><li>Duck probe: `tool_agent.py:2340-2348`</li><li>controller probe: `controller_turn.py:215-224`</li><li>Duck answer: `tool_agent.py:2622-2663`</li><li>controller answer: `controller_turn.py:179-190`</li><li>G3 choice: `g3_selection.py:105-133` and `virelai_gates.py:6733-6736`</li><li>notes: `annotation_lane.py:75-104`</li></ul> | These are the six places admission is decided. On refusal:<ul><li>Duck probe, Duck answer, controller answer and notes record nothing structured.</li><li>A controller probe writes only a ledger `outcome` of `controller_refused`, with no reason (`controller_turn.py:220-224`).</li><li>G3 records REFUSED, except on the non-G3-gate path.</li></ul> | code / AC, once D1-D2 are ruled |
| D4 | Field-level authorship of accepted Duck answers | Record the raw submission beside the filled answer; record a diff; or declare per-schema authorship | `fill_certified_fields` merges the two today. | architecture / Sol |
| D5 | Claim unit and predicate families | §6 families; how DESC-B patterns and multi-field answers split | Pattern sentences and G1/G2 answers are multi-proposition. | architecture / Sol |
| D6 | `claim_id` formula | Hash of the semantic tuple without evidence (stable as evidence grows); with scope; or with level only | `P-` / `Q-` ids already exclude counts. `answer_id` and `note_id` are not unique. | architecture / Sol |
| D7 | Epistemic status enum and mixed-status claims | Split claims by status, or keep counts on one claim | Patterns mix statuses (k013 counter shrink: 217 NOT_COVERED, 6 G3_WITNESS_RESIDUE). | architecture / Sol |
| D8 | Executor / admission enums | {CONTROLLER, DUCK, SYSTEM} × {ADMITTED, REFUSED, NOT_APPLICABLE, UNCERTIFIED} | SYSTEM_RESET already exists as a runtime actor. The lifecycle `actor` field holds component names (for example `G3_ROUTER`, `NAV_TERRAIN_MAP`), not an executor enum, and it hardcodes DUCK on a controller-capable path. | architecture / Sol |
| D9 | Key format and authorship | Structured, the same tuple as claims; with `construction`, `frozen_on` and recording hashes; required vs optional items; accepted alternatives | Prior art in the real continuity key. **Authored by the Director, not by this seat.** | plan / Director |
| D10 | Join strategy | Exact tuple; id; grain mapping (EXACT / COMPOSITE / UNMATCHED) with human confirmation | Key and solver individuation differ (v4 doctrine). | architecture / Sol |
| D11 | Category definitions | §7 open questions 1-3 | No existing tool defines them. | plan-level wording (thesis C2) / Apex, via the Director; operational rules / Sol |
| D12 | Historical runs | Grade only new runs; or partially reconstruct accepted work from old runs | Old runs lack refusals and selection events (§4). | plan / Director |
| D13 | Compatibility | The v3 reader stays; a v4 reader is added; the report renders "no provenance" for v3 | `read_world_model` already dispatches v1, v2 and v3 (`world_model_v2.py:286-302`). | architecture / Sol |
| D14 | Report shape | Keep the DESC-B semantic library report and add the paper report (self · time · response · players · model · value), or extend one renderer | `THESIS_v1` requires the fixed six sections and three line kinds. | architecture / Sol, against the thesis |

---

— Claude, Alpha build seat, 2026-10-14
