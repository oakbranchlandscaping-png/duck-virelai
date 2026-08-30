# Ring 6.3 Engineering Build Plan

**Status:** proposed for peer review; not yet implemented  
**Base:** `variants/ring6.2/`  
**Purpose:** prove the Captain-to-Duck information boundary before changing either side of it

## 1. Decision statement

Ring 6.3 is a handshake canary, not a solver-tuning ring.

Its single required behavioral change is:

> The exact Virelai Captain report produced after the bounded probe must be present exactly
> once in the first outbound Duck model request, even when the Captain has already taken
> nonzero game actions.

Ring 6.3 must also leave enough durable evidence to prove this after Kaggle has finished.
It is not sufficient to prove that the report was rendered, passed as a Python argument, or
mentioned by a marker. The proof boundary is the final request payload immediately before it
is sent to the model endpoint.

This ring can prove that the endpoint accepted a request containing the report. It cannot
inspect the model's private attention or prove semantic understanding. Understanding is
graded separately from the model's response and actions after transport passes.

## 2. Why Ring 6.3 is necessary

Ring 6.2 successfully ran the Captain in all 25 games and rendered 25 reports, but delivered
none of those reports to Duck.

The failure is the composition of two individually plausible conditions:

1. `solver.py` passes `virelai_card` only when `analysis_step == 1`. This correctly means the
   first Duck analysis turn.
2. `tool_agent.py::_build_user_prompt()` appends the card only when `action_num == 0`. This
   means the first action of the whole game.

Captain actions are real game actions and increment `self.action_count`. Every Ring 6.2
Captain took at least six actions. Therefore the first Duck turn had `analysis_step == 1`
but `action_num > 0`, and the report was discarded during prompt construction.

The `CARD_INJECTED` marker did not prove delivery. It was emitted in `solver.py` before prompt
construction because a report argument existed. It measured intent to inject, not presence
in the model request.

Current anchors in the Ring 6.2 base:

- `inference/framework/solver.py`, approximately lines 302-332: early marker and analyzer
  call.
- `inference/agent/tool_agent.py`, approximately lines 1164-1257: prompt construction and
  the incorrect `action_num == 0` gate.
- `inference/agent/tool_agent.py`, approximately lines 1736-1847: final message construction,
  context trimming, request snapshot, and model call.

## 3. Experimental isolation

Ring 6.3 must freeze all variables unrelated to transport:

- the V4 Captain source and targeting policy;
- Captain limits: two lives, 320 actions, and 480 seconds;
- the action compatibility bridge introduced in Ring 6.2;
- level/life boundary handling and snapshot policy;
- the V3.5 seven-section field-card renderer and its wording;
- the ARC Grid Multiverse Ontology;
- the Duck model, decoding settings, tools, and normal prompt wording;
- the separate Duck live ledger;
- benchmark game set, pass count, concurrency, and Kaggle hardware.

Specifically excluded from Ring 6.3:

- Captain NAV, collision, counter, ego, lever, or information-value tuning;
- field-card shortening, reordering, or rewriting;
- ontology refinement;
- seeding Duck's live ledger from Captain state;
- win-analysis or Captain-return logic;
- level-2 transfer changes.

These are valuable later changes, but combining them with the handshake repair would make a
successful or failed run ambiguous.

## 4. Required information flow

For every game that reaches Duck, the intended path is:

```text
Captain probe ends
  -> exact report is rendered in memory
  -> exact UTF-8 report bytes are saved per game
  -> solver passes the report on Duck analysis step 1
  -> ToolAgent appends it without consulting global action count
  -> ToolAgent builds and context-trims the real request messages
  -> provider-specific request payload is built
  -> final payload is inspected without mutation
  -> exact report is found once and its digest matches
  -> payload is sent
  -> model endpoint returns a response
  -> Duck takes control and acts
```

Each arrow must be independently observable. No upstream event may stand in for a later one.

## 5. Source layout and release identity

Ring 6.2 remains immutable as the failed-transport control.

The Ring 6.3 build will use:

- source variant: `variants/ring6.3/ARC3-Inference/`;
- variant tests and documents: `variants/ring6.3/`;
- assembled bundle: `kaggle/ring6.3/`;
- runtime benchmark label: `duck-virelai-ring6.3`;
- dataset version message prefix: `ring6.3:`;
- downloaded run: `runs/kaggle-ring6.3-run1/kaggle-output/`;
- evaluation memo: `runs/kaggle-ring6.3-run1/EVALUATION.md`.

The existing Kaggle Ring 6 dataset and kernel slugs may be versioned again; the local source,
bundle, runtime label, version message, and downloaded output must all say 6.3. The runtime
label is authoritative when identifying the executed solver.

The variant must be copied as a complete Ring 6.2 tree with cache files excluded. It must not
be installed as a partial overlay using a deletion-capable synchronization step.

## 6. Code changes

### 6.1 `inference/framework/solver.py`

#### A. Retire the false-positive marker

Remove the current pre-call `CARD_INJECTED` event. It fires before the prompt exists and must
not remain as a success signal.

If compatibility with old audit scripts is necessary, it may be emitted only as a deprecated
intent event named `REPORT_OFFERED`. It must never be counted as proof of attachment.

#### B. Fingerprint the final report

After the probe has stopped and the final report or honest fallback report has been selected,
compute over the exact in-memory string:

- SHA-256 of `report.encode("utf-8")`;
- Python character count;
- UTF-8 byte count;
- snapshot count;
- whether the report is the fallback;
- game id and pass index.

No whitespace normalization is allowed. The string fingerprinted here must be the string
passed to ToolAgent and written to disk.

#### C. Persist one exact report per game

Write the report with no added terminal newline to:

`captain_reports/<run_stem>.txt`

Use a temporary file in the same directory followed by an atomic replacement. Concurrent
games cannot share filenames. A report-write failure must be recorded but must not prevent
Duck from playing with the in-memory report.

Emit `REPORT_RENDERED` after the final in-memory value exists. Emit `REPORT_PERSISTED` only
after the durable file is complete. Both carry the same digest and size metadata.

#### D. Pass by Duck turn, not game action

Continue passing `virelai_card` only when `analysis_step == 1`. Do not change this condition
to `action_count == 0`, and do not reset or reinterpret `action_count` after the Captain.

The analyzer call must also receive a read-only request observer on every Duck analysis turn.
The observer retains the expected report digest so it can detect both missing first-turn
reports and accidental later duplicates.

#### E. Verify the final outbound request

The solver-side observer receives an event from ToolAgent after the provider-specific payload
has been built and immediately before the network call. It must:

1. examine only textual message blocks, never image/base64 data;
2. count exact, contiguous occurrences of the complete report;
3. locate the message index, role, and text-block index of each occurrence;
4. verify that the matched substring has the expected SHA-256 and character/byte counts;
5. save the first report-bearing outbound payload as a per-game audit artifact;
6. emit `REPORT_ATTACHED` only when all checks pass and the occurrence count is exactly one;
7. emit `REPORT_ATTACH_FAILED` with a reason and occurrence count otherwise.

The observer must not mutate the request payload. Observer or audit-file failures are
fail-open for gameplay: they make the canary fail, but Duck must still receive a request.

#### F. Correlate accepted responses

Every outbound request receives a unique request id containing at least game/pass,
`analysis_step`, and request index within the turn. After the endpoint returns a valid model
response, ToolAgent reports a completion event for the same id.

Emit `REPORT_REQUEST_ACCEPTED` only when that completed request previously passed exact
attachment verification. This closes the gap between “we assembled a payload” and “the
endpoint returned a response to it.”

Keep the existing `DUCK_FIRST_ACTION` marker. It proves that control passed through the model
loop into a Duck action, not that the report was attached.

### 6.2 `inference/agent/tool_agent.py`

#### A. Correct the prompt gate

In `_build_user_prompt()`, append the report whenever the explicit `virelai_card` argument is
present. Do not nest report insertion under `action_num == 0`.

The global action number may still choose ordinary “first frame” versus “recent change”
guidance. It must have no authority over the Captain report.

#### B. Add an optional request observer

Add a default-`None` callback parameter through `analyze()` to the model-call boundary. The
callback must receive structured events, not parse logs. At minimum:

- `prepared`: the exact provider payload immediately before `requests.post(..., json=payload)`;
- `completed`: the matching request id and parsed response metadata;
- `failed`: the matching request id and bounded failure class/detail.

Callback execution must be guarded. Logging or audit code cannot block the model call.

The `prepared` event belongs after all message construction and context trimming and after
`build_chat_payload()`. Calling it earlier would recreate Ring 6.2's false proof.

#### C. Define one-shot and retry behavior explicitly

The fixed report is a one-shot handoff, with these exact semantics:

- Every outbound request made during the first Duck analysis attempt contains one copy.
- An analyzer request failure may cause analysis step 1 to be retried; the retry contains one
  copy.
- A yielded first analysis turn may also be resumed; the resumed request contains one copy.
- Multiple model/tool exchanges inside the same analysis turn may carry the original user
  message in request history, but each outbound payload contains no more than one exact copy.
- After the first analysis turn is persisted, the fixed report is removed from the stored
  user-message history. Analysis step 2 and later receive no exact copy.
- Duck's own summary or assistant response is not censored if the model independently quotes
  or paraphrases report content.

To enforce this, sanitize only the copy of user messages being stored as persistent history.
Do not alter the messages used by the active request. Remove the exact report only from user
text blocks, and leave the rest of the first-turn prompt intact.

This avoids two opposite errors: losing the report on a failed first request, and silently
duplicating it when a yielded first turn resumes with preserved history.

### 6.3 New pure audit helper

Place hashing, exact-occurrence counting, and persistent-history sanitization in a small
standard-library-only module, for example:

`inference/framework/virelai_handoff_v63.py`

It should expose pure functions with no ARC engine, NumPy, SciPy, TAAF, network, or model
dependencies. This allows the core transport rules to be tested locally even when the full
Kaggle runtime is unavailable.

Suggested responsibilities:

- fingerprint exact UTF-8 text;
- enumerate text blocks in OpenAI-style message content;
- count and locate exact report occurrences;
- make a sanitized history copy without the fixed report;
- build the machine-readable audit record.

It must not know Captain strategy or field-card meaning.

## 7. Durable evidence contract

Ring 6.3 adds these per-game artifacts under the job directory:

### `captain_reports/<run_stem>.txt`

The exact report bytes. No wrapper, metadata header, or added newline.

### `handoff_requests/<run_stem>.json`

The first exact provider payload containing the report, plus a small audit envelope. It may
include the existing image block because this is the payload actually sent. It must not
include HTTP headers, API keys, environment variables, or credentials.

Required envelope fields:

```json
{
  "schema": "ring6.3-handoff-v1",
  "game_id": "...",
  "pass_index": 0,
  "analysis_step": 1,
  "global_action_count": 37,
  "request_id": "...",
  "request_index_within_turn": 1,
  "report_path": "captain_reports/...txt",
  "report_sha256": "...",
  "report_characters": 3704,
  "report_utf8_bytes": 3712,
  "exact_occurrences": 1,
  "locations": [{"message_index": 1, "role": "user", "text_block_index": 0}],
  "provider_payload": {}
}
```

### `handoff_audit/<run_stem>.jsonl`

One compact record per prepared/completed/failed request. Later requests need metadata and
occurrence counts, not duplicate full payloads. This file establishes that later completed
Duck turns did not receive the fixed report again.

The existing transcript remains the human-readable authority for the exact user prompt,
Duck response, tool calls, and actions. The new artifacts make the one-shot transport
mechanically auditable without relying on the overwritten `prompts/*.log` snapshot.

## 8. Marker contract

The expected successful sequence for a handoff-eligible game is:

```text
RING6_PROBE_START
RING6_PROBE_END
RING6_REPORT_RENDERED
RING6_REPORT_PERSISTED
RING6_REPORT_ATTACHED
RING6_REPORT_REQUEST_ACCEPTED
RING6_DUCK_FIRST_ACTION
```

Markers must contain machine-readable JSON and share the report digest/request id needed to
join them. Marker names describe completed facts:

- `REPORT_RENDERED`: final in-memory report exists;
- `REPORT_PERSISTED`: exact bytes are durable;
- `REPORT_ATTACHED`: exact report occurs once in the final outbound payload;
- `REPORT_REQUEST_ACCEPTED`: the endpoint returned a response to that exact request;
- `DUCK_FIRST_ACTION`: Duck executed its first environment action.

Failure events are explicit: `REPORT_PERSIST_FAILED`, `REPORT_ATTACH_FAILED`,
`REPORT_REQUEST_FAILED`, and `REPORT_AUDIT_FAULT`. None may crash the game.

If the Captain completes the entire game before Duck is needed, emit
`HANDOFF_NOT_REQUIRED` with the terminal reason. Such a game is excluded from the transport
denominator rather than mislabeled as a handshake failure. Any other game that reaches the
Duck phase is handoff-eligible.

## 9. Test plan

### 9.1 Pure unit tests

Add `variants/ring6.3/tests/test_ring63_handoff_audit.py` covering:

1. ASCII and Unicode reports produce stable character, byte, and SHA-256 values.
2. A string-content user message yields one exact occurrence.
3. A multimodal user message yields one occurrence in its text block and ignores image data.
4. Prefixes, suffixes, and embedded newlines do not change the matched report hash.
5. Zero occurrences fail attachment.
6. Two occurrences fail attachment.
7. History sanitization removes the report from user text only.
8. History sanitization does not mutate the active request or remove assistant-authored text.
9. Missing, empty, or malformed report input returns an auditable failure rather than
   raising into gameplay.

### 9.2 Prompt-boundary regression tests

Add `variants/ring6.3/tests/test_ring63_prompt_delivery.py` covering:

1. `analysis_step == 1`, `action_num == 0`: report is present once.
2. `analysis_step == 1`, `action_num > 0`: report is present once. This is the primary Ring
   6.2 regression.
3. `analysis_step > 1`: solver passes no report.
4. First-turn request failure followed by retry: each outbound payload contains one copy.
5. First-turn yield followed by resume: each outbound payload contains one copy, never two.
6. Multiple tool calls inside the first turn: each request payload contains at most one copy.
7. First completed turn followed by analysis step 2: the later payload contains zero exact
   copies.
8. Context trimming cannot remove the current first-turn report before the request observer.
9. The observer sees the same payload object/content passed to the mocked network post.
10. A callback exception does not prevent the mocked model call.

Use a fake model endpoint or patched post function to capture the actual `json` payload. A
test that inspects `_build_user_prompt()` alone is necessary but not sufficient.

### 9.3 Existing regression suite

All Ring 6.2 tests must remain green, including:

- action-data compatibility for simple actions and MOUSE;
- probe failure containment;
- two-life/action/time limits;
- level advance versus descent semantics;
- complete-game WIN stop;
- seven-section renderer fallbacks;
- internal-id/color firewall;
- V4 package topology and imports.

No Ring 6.2 test should be weakened merely to allow the new build.

### 9.4 Static and bundle checks

Before Kaggle:

- parse every Python file in source and tests;
- run all dependency-free tests;
- run the mocked outbound-payload test;
- compare hashes for every touched source file between variant and assembled bundle;
- verify the complete V4 trees are byte-identical between variant and bundle;
- verify runtime benchmark label `duck-virelai-ring6.3` in the packaged benchmark and
  notebook override;
- verify the bundle imports `virelai_v4` from the sibling package;
- find zero `__pycache__` directories and zero `.pyc` files in source and bundle;
- confirm Ring 6.2 source and bundle hashes did not change.

## 10. Local acceptance gate

Ring 6.3 is not pushed until a captured fake outbound request proves all of the following:

- Captain/global `action_num` is nonzero;
- Duck `analysis_step` is one;
- the final provider payload contains the full report exactly once;
- saved report bytes and payload substring have identical SHA-256, character count, and byte
  count;
- the attachment marker is emitted after payload construction;
- a mocked accepted response is correlated to the same request id;
- a later completed Duck turn contains zero exact report copies;
- a failed/yielded first turn can retry with exactly one copy;
- fallback report and audit failures do not block Duck;
- no Captain policy or report wording changed.

## 11. Kaggle run acceptance gate

The primary denominator is every benchmark game that reaches Duck. Ring 6.3 passes only if
every handoff-eligible game satisfies:

1. exactly one final report artifact exists;
2. its stored SHA-256 and measured bytes agree;
3. the first outbound Duck request contains that report exactly once;
4. `analysis_step == 1` even though Captain/global action count may be nonzero;
5. `REPORT_ATTACHED` refers to the same digest and request id;
6. the endpoint returns a response for a verified report-bearing request;
7. no completed later Duck analysis turn receives a second fixed report;
8. no `REPORT_ATTACH_FAILED`, `REPORT_AUDIT_FAULT`, or unexplained missing artifact occurs;
9. Duck remains able to act after the handoff.

Target: 25/25 unless a Captain completes a whole game and emits a justified
`HANDOFF_NOT_REQUIRED` event. A partial rate is diagnostic evidence, not a pass.

Score, levels, actions, tokens, Captain stop reasons, and analyzer timeouts are still
recorded, but none substitutes for the transport gate.

## 12. Post-run grading

Grade the run in three independent layers.

### Layer A: transport

Binary per game: exact report attached and accepted, or not. This is Ring 6.3's release gate.

### Layer B: Duck use

Read the saved report beside Duck's first response and first actions:

- **Direct:** Duck cites a specific report fact, gap, mechanism, or observed winning
  transition and uses it in its plan/action.
- **Partial:** Duck acknowledges specific evidence but substantially restarts discovery.
- **Ignored:** Duck behaves as though only the current frame was supplied.
- **Contradicted:** Duck reverses a report-supported fact without new contrary evidence.

This is behavioral evidence of use, not proof of internal cognition.

### Layer C: outcome

Record levels, game wins, action efficiency, tokens, and score. Compare cautiously with Ring
6.2, which is the closest natural control: Captain-altered world state with no report
delivery. One stochastic 25-game run can show direction and failure shapes; it is not a clean
causal estimate of score improvement.

## 13. Interpretation matrix

| Transport | Duck use | Outcome | Meaning |
|---|---|---|---|
| fail | unknown | any | interface remains the bottleneck; semantic conclusions invalid |
| pass | ignored/contradicted | any | card placement, clarity, authority, or model behavior is next |
| pass | direct/partial | poor | Captain evidence or field-card content is the next bottleneck |
| pass | direct/partial | better | first evidence that the full Virelai handoff helps |

Only the first row is answered by plumbing. Ring 6.3 is designed to make the rows separable.

## 14. Principal risks and controls

- **False-positive marker:** attachment is measured only in the final provider payload.
- **Global/local counter confusion:** report insertion is controlled solely by explicit
  `virelai_card` on Duck analysis step 1.
- **Retry duplication:** persistent-history sanitization and exact occurrence counting cap
  every payload at one report.
- **Retry loss:** failed or yielded step-1 attempts may receive the report again.
- **Latest-log overwrite:** immutable per-game report/request artifacts are primary evidence;
  `prompts/*.log` is not.
- **Unicode/hash disagreement:** digest exact UTF-8 bytes with no normalization or added
  newline.
- **Context trimming:** inspect the payload after trimming; do not infer from the pre-trim
  prompt.
- **Observer side effect:** callback is read-only and fail-open; it cannot mutate or veto the
  model request.
- **Concurrency collision:** all artifacts are named by game plus pass and written atomically.
- **Artifact leakage:** save payload content but never HTTP headers, keys, or environment.
- **Terminal Captain win:** classify as handoff not required instead of failure.
- **Label drift:** verify source, bundle, runtime label, version message, and output directory.
- **Bundle contamination:** reject any `__pycache__` or `.pyc` in variant or bundle.

## 15. Peer-review questions

The collaborator should specifically challenge:

1. Is the `prepared` observer truly after the last payload transformation and immediately
   before the network post?
2. Can any retry/yield path produce zero or two report copies?
3. Does persistent-history sanitization affect only the fixed user-supplied report?
4. Can audit code throw, block, or mutate gameplay?
5. Are report bytes, request payload, markers, and accepted response joined by stable ids?
6. Is every Kaggle artifact preserved in downloaded kernel output?
7. Is any non-transport behavior changing accidentally?
8. Does the test capture the actual mocked network payload rather than only an intermediate
   prompt string?

## 16. Completion definition

Ring 6.3 is complete when the local candidate and assembled bundle pass all transport tests,
the Kaggle run produces auditable per-game evidence, and every handoff-eligible game proves
that an endpoint-accepted Duck request contained the exact Captain report once.

At that point—and not before—the campaign may use Duck behavior to judge the field card,
Captain evidence, ontology, or the larger Virelai hypothesis.
