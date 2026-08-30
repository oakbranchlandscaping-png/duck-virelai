# REVIEW — RING 6.3 BUILD AS CONSTRUCTED
**Type:** REVIEW_RING63_BUILD · **Version:** v1 · **Date:** 2026-08-30
**Reviewer:** Duck-Virelai Hybrid seat (reviewer role, not builder)
**Object:** `variants/ring6.3/` as found on disk 2026-08-30 ~15:47 (untracked; no anchor commit)
**Method:** direct read of the full diff against the executed Ring 6.2 base, plus independent re-execution of the entire test battery on this machine with a dependency-free runner. Nothing below is taken from the MANIFEST's word.

## HEADLINE

The build implements the amended plan faithfully. The diff against the executed base is exactly three code files — `tool_agent.py` and `solver.py` modified, `virelai_handoff_v63.py` added — plus tests and documentation. The F1 sanitizer is absent, the F2 containment fix is in and behavior-tested, the observer sits at the correct boundary, and **all 34 tests pass under my own independent runner (14 ring6.3 + 20 inherited ring6 contract tests), not just under the builder's**. Two defects and one missing promised test are owed before bundle assembly; none touches the core transport fix.

## VERIFIED CORRECT (each checked at code level, most also behaviorally)

1. **Seed provenance (F3): implemented as accepted.** `diff -rq` between `kaggle/ring6.2/source-dataset/src/ARC3-Inference` and the 6.3 tree shows only the three intended code deltas (plus local `__pycache__`, see D4). The four space-suffixed duplicate dirs (`capture 2`, `contracts 2`, `cybernetic 2`, `library 2`) present in the executed base were excluded from the seed; historical Ring 6.2 was left untouched. `BASE_PROVENANCE.md` states all of this accurately.
2. **The core gate fix.** The card append is un-nested from `action_num == 0`; insertion is controlled solely by the explicit `virelai_card` argument, which the solver passes only on `analysis_step == 1`. Pinned by an AST-based test (not a bare grep — the methodology lesson was honored).
3. **F2 containment: exactly the accepted design.** `history_contains_report()` suppresses a fresh append when retained user history already carries the exact report (yield-resume path); a request failure restores prior history and the report is re-offered. Both directions behavior-tested (`test_retained_yield_style_history_prevents_fresh_duplicate`, `test_request_failure_restores_history_and_retry_reoffers_one_report`) — I re-ran both, they pass.
4. **No sanitizer anywhere (F1).** No history-mutation code exists in the diff. Natural retention preserved.
5. **Observer at the true proof boundary.** `prepared` fires after `build_chat_payload()` and before `requests.post` (AST test asserts the ordering); the observer receives a *detached* `json.loads(json.dumps(...))` copy, so mutation of the live payload is structurally impossible; callback exceptions are swallowed with a warning and the post proceeds — the fail-open test passes with a deliberately raising observer, and I watched its warning fire in my run. `completed`/`failed` events correlate by request id.
6. **Request ids (F11): audit metadata only**, never injected into the payload. Format `a{step}-i{invocation}-r{turn}`; the invocation counter increments per `analyze()` call (reset per game in `_ensure_session`), the turn counter increments per request — so yield-resumes AND context-overflow retries each get fresh ids (verified by reading the overflow path at tool_agent.py:1932–1948, which `continue`s into a new `turn_count`).
7. **Marker contract (F9).** `CARD_INJECTED` is gone from the source (test-pinned). `_ring6_marker` prefixes `RING6_` uniformly; RENDERED / PERSISTED / ATTACHED / REQUEST_ACCEPTED plus the failure family and `HANDOFF_NOT_REQUIRED` (emitted on `_is_run_complete` after the probe) all exist. `REPORT_ATTACHED` is emitted only from inside the prepared-event verification — exact user-role occurrence count == 1 and fingerprint match — and the first verified payload is saved whole to `handoff_requests/`. Assistant-role quoting of the report cannot fail the gate (user-role filter), which is the right call.
8. **Persistence (F10/§6.1.C).** Atomic temp-file + `os.replace` with fsync, no added newline, and — a nice touch beyond the plan — the persisted file is re-read and re-fingerprinted, with a mismatch downgrading to `REPORT_PERSIST_FAILED` rather than a false PERSISTED.
9. **Artifacts (F12)** land under the job root beside `transcripts/` and `artifacts/`, the layout verified to survive Kaggle collection.
10. **Boundary invariant (F7, partially).** An AST test asserts `_execute_auto_reset` and `_virelai_opening` never assign `analysis_step`. Static rather than behavioral, and narrower than the accepted wording — see D6.
11. **Fallback accounting (F8).** `fallback` and `captain_fault` flags ride the fingerprint metadata into every marker and artifact.

## DEFECTS OWED BEFORE BUNDLE ASSEMBLY

### D1 (major) — Control arms will emit false `REPORT_ATTACH_FAILED`.
The observer is installed unconditionally in `play()`, but `VIRELAI_RING6=0` returns from `_virelai_opening` at solver.py:1127 **before** `_ring63_finalize_report` runs. In a no-probe control arm: report is `""`, `verified` is False, and the game's first prepared event fires `REPORT_ATTACH_FAILED` (`first_request_missing_or_nonunique`) with empty metadata, plus `handoff_audit/` files, in an arm where no handoff was ever intended. Ring 6.3 itself always probes, but the flag exists precisely for control arms, and a marker that lies in one configuration is this program's signature defect. **Fix:** make the observer a no-op (or skip installation) when no report was finalized — one guard on `_ring63_report_meta`.

### D2 (major) — The promised honest fallback report does not exist on the render-failure path.
If `render_probe_report` **raises**, the `except` at solver.py:1286–1289 logs and moves on without ever setting `self._virelai_card`. Consequences: `_ring63_finalize_report` fingerprints and persists an empty string; the solver's getattr guard passes `None` on turn 1 so nothing is inserted; the first prepared event fires `REPORT_ATTACH_FAILED`. The review response committed to "Captain failure still degrades to an honest fallback report without blocking Duck" — Duck is not blocked, but the fallback text is absent and the game is mislabeled a transport failure instead of a fallback delivery. This gap is inherited from the 6.2 base, but 6.3's acceptance gate makes it load-bearing now. **Fix:** in the except branch, assign a minimal honest fallback string (probe stats + "report unavailable: <error class>") so transport can still be proven on renderer-failure games.

### D3 (moderate) — The accepted F5 test is missing.
The response accepted "an explicit mocked context-overflow test that captures both posted payloads." No such test exists in the roster. The overflow path is correct by my reading (new request id per re-post, each post independently prepared-inspected), but the one retry path that rebuilds the message list after a server rejection is exactly where a card can vanish between a passed check and the request the model actually answers. Write the test before calling the battery complete.

### D4 (hygiene) — The 6.3 tree currently violates its own hygiene gate.
`__pycache__` directories exist right now in `tests/` and in `ARC3-Inference/inference/`, `agent/`, `framework/`, `utils/` — byproducts of local test runs, post-seed. The gate rejects them "in source or bundle" and they are in source. Sweep before assembly, and run local tests with `PYTHONDONTWRITEBYTECODE=1` so they stop regrowing.

### D5 (process) — Nothing is committed.
The entire 6.3 variant — and for that matter ring6.2, both plan documents, the response, and the run directories — is untracked; the last commit is Ring 6 DESIGN (`a667dfa`, pre-6.1). "Ground truth is the committed state" and the anchor commit is part of every definition of done. The provenance hashing in BASE_PROVENANCE cannot bind to anything until the seeded base and the transport diff are committed. Commit before bundle assembly, not after the run.

### D6 (minor) — F7 landed weaker than accepted.
The accepted disposition promised regression tests that level advance, descent, GAME_OVER, and auto-reset "do not reset `analysis_step` or freshly insert the fixed report again." What exists is a static assert on two functions' assignment targets. It passes, and the property holds by my reading, but a behavioral test (drive analyze() across a simulated boundary; assert zero fresh insertions) is the durable form — the static test cannot catch a future path that resets the counter from a third function.

## WHAT REMAINS UNBUILT (owed, not defective)

The `kaggle/ring6.3/` bundle and its checks (label `duck-virelai-ring6.3`, variant↔bundle hash comparison, V4-tree byte-identity, hygiene at bundle time); the D3 test; the run and its EVALUATION. The local acceptance gate is otherwise substantively met: nonzero-action delivery, verbatim-once insertion, observer-sees-posted-payload, fail-open, retry re-offer, and yield dedup are all green under independent execution.

## VERDICT

**Build quality is high and matches the accepted plan — including the restraint the review asked for.** Clear to proceed to bundle assembly once D1, D2, and D4 are fixed and D3's test is written; D5's commit should happen at the same time so the bundle hashes bind to an anchor. None of the fixes touches the transport semantics already tested, so the existing battery remains valid; D1 and D2 each deserve one new test of their own (control-arm silence; renderer-exception fallback delivery).

*Filed by the reviewer seat, 2026-08-30. Test results in this document were produced by the reviewer's own runner on the linked machine; all code claims are from direct reads of the diff against `kaggle/ring6.2/source-dataset/src/ARC3-Inference/`. The committed repo — once these trees are committed — outranks this document.*
