# REVIEW — RING 6.3 ENGINEERING BUILD PLAN
**Type:** REVIEW_RING63_PLAN · **Version:** v1 · **Date:** 2026-08-30
**Reviewer:** Duck-Virelai Hybrid seat (reviewer role, not builder)
**Object under review:** "Ring 6.3 Engineering Build Plan" (proposed, unimplemented), base `variants/ring6.2/`
**Ground:** every load-bearing claim verified by direct read of the ring6.2 tree at HEAD (POLICY_DIRECT_READ). File:line citations are to `variants/ring6.2/ARC3-Inference/inference/` unless noted.

## VERDICT

**APPROVE WITH AMENDMENTS.** The plan's aim, proof boundary, evidence contract, and freeze discipline are correct and its central factual claims are all confirmed at code level. Four findings are blocking; one of them (F1) is an architectural question that should be ruled explicitly, not decided inside a transport ring. None of the blocking items invalidates the ring's design — they narrow it.

## WHAT THE PLAN GETS RIGHT (verified, not assumed)

- The defect description is exact. `solver.py:302–331` gates on `analysis_step == 1` and passes `virelai_card=None` on later turns; `tool_agent.py:1248–1257` nests the card append inside `if action_num == 0:`. Composition of two individually plausible gates, exactly as stated.
- The cited functions exist. `build_chat_payload` (imported tool_agent.py:35, called :1305) and `requests.post(..., json=request_payload)` (:1319, inside `_chat_completion`) are real. No phantom citations found.
- The proof boundary — final provider payload immediately before the network post — is the correct lesson from `CARD_INJECTED` (emitted at solver.py:307, before any prompt exists, on card *existence*). The marker contract (markers name completed facts; separate rendered/persisted/attached/accepted) is the right immune response.
- Fail-open observer, `HANDOFF_NOT_REQUIRED`, the freeze list (§3), the three-layer grading, and the interpretation matrix are all sound.
- The duplication worry is real, and I confirmed the exact path (F2). The plan was right to treat retry/yield as the dangerous surface.

## BLOCKING FINDINGS

### F1 — History sanitization (§6.2.C) is a semantic intervention smuggled into a transport ring. ESCALATE FOR RULING.

Measured behavior of the base: each `analyze()` call builds `messages = [system, *self._history_messages, new user message]` (tool_agent.py:1787–1791), and on a completed turn the user message — card included — is persisted into `_history_messages` (:2045–2046 via `_persistent_history_messages`, :1680). `_PERSISTENT_HISTORY_ASSISTANT_TURNS = 30` (:152). **So the harness's natural behavior is that the turn-1 user message, with the card, remains visible in Duck's context for up to 30 assistant turns before trimming drops it.**

The plan's sanitization would strip the card from stored history after turn 1. Three consequences:

1. **It changes what Duck sees on turns 2+ relative to both natural harness behavior and ring 6.2's design intent** (the solver comment at :323–328 governs fresh *insertion*, not history retention). That is a prompt-content change — §3 froze "normal prompt wording" and excluded "field-card shortening, reordering" — so the plan violates its own isolation clause.
2. **It confounds Layer B.** A model that saw the card once, 25 turns and one context-trim ago, and no longer references it is not "ignoring" the card — it forgot it. Under sanitization, "Ignored" stops being evidence about card quality and becomes partly evidence about memory horizon. The plan's own interpretation matrix (row 2) then misroutes the next ring.
3. **It is the riskiest code in the plan.** A sanitizer that mutates stored history can corrupt every later turn of every game — a strictly worse failure class than the one-line bug being repaired, introduced in the ring whose thesis is "change as little as possible."

There is also an internal contradiction: §6.2.C bullet 1 says *every* turn-1 request contains one copy; bullet 4 says *no more than* one. Context trimming (`_trim_messages_for_context` runs before every request, :1820) can legitimately drop the first user message late in a long turn-1 tool loop, so "every request contains one" is not enforceable and the tests will flap.

**Recommendation:** redefine one-shot as **"freshly inserted exactly once, into the first Duck analysis turn."** Let stored history behave naturally; record per-payload exact-occurrence counts in `handoff_audit/` as diagnostics; gate the run on the *first* outbound request containing exactly one copy. Delete the sanitizer entirely. If turn-1-only visibility is genuinely wanted, that is an architectural choice about the model's information environment — it belongs to a ruling, made deliberately, ideally as its own arm later (it is a cheap, clean A/B once transport is proven).

### F2 — The duplication path is real and confirmed — but it has a two-line fix, not a history-mutation subsystem.

Confirmed at code level: on a **yield**, `preserve_history` remains True (it is set False only on request errors :2010, analyzer exceptions :2028, and mid-tool-call breaks :1996/:2001), so the `finally` block persists the card-bearing user message (:2045–2046). The solver then retries the same `analysis_step` (`yielded_control` → `retry_analysis_step`, solver.py:351–353) and passes the card again (:329–331). The resumed `analyze()` prepends the old card-bearing message from history *and* builds a fresh card-bearing prompt → **two exact copies in one payload.** (On a `retryable_failure`, `preserve_history` is False, history is restored, and the retry carries exactly one copy — that path is already correct.)

**Recommendation:** fix the yield path narrowly — either skip appending the card when the incoming history already contains it (one containment check at the append site), or set `preserve_history = False` when a turn-1 attempt yields. Either is a few lines, confined to the known-bad path, and testable by §9.2.5 as written. This removes the last justification for the F1 sanitizer.

### F3 — "Copy the variant as a complete Ring 6.2 tree" is impossible as written: `variants/ring6.2/` is a partial tree.

Verified: `variants/ring6.2/ARC3-Inference/inference/` contains only `framework/` and `agent/`. `inference/utils/openai_compat.py` — which tool_agent.py imports at :35 — exists only in the assembled bundle, at `kaggle/ring6.2/source-dataset/src/ARC3-Inference/inference/utils/openai_compat.py`. A builder who copies the variant believing it complete produces a 6.3 tree that cannot run, and the packaging step is then forced back into overlay-assembly — the exact `rsync --delete` failure class of friction #1. §9.4's "verify the complete V4 trees are byte-identical between variant and bundle" is likewise unsatisfiable against the current variant.

**Recommendation:** name the copy source precisely. The tree that actually executed ring 6.2 is `kaggle/ring6.2/source-dataset/src/ARC3-Inference/` — seed `variants/ring6.3/ARC3-Inference/` from **that**, byte-verified, caches excluded, then apply the 6.3 diffs. State it in §5 so the builder never faces the choice.

### F4 — Contamination found during this review, in scope for §9.4's hygiene gate.

Finder-style duplicate directories exist inside shipped and to-be-copied areas: `variants/ring6.2/ARC3-Inference/virelai_v4/contracts 2` and `library 2`; `kaggle/ring6.2/source-dataset 3`; also `ring6/source-dataset 2` in the workspace. Names with spaces cannot shadow imports, but they ride into copies and bundles, bloat the dataset, and corrupt provenance reads — same family as the `__pycache__` scar.

**Recommendation:** extend every §9.4 hygiene check to reject space-suffixed duplicate directories (`* 2` / `* 3`) alongside `__pycache__`/`.pyc`, in both variant and bundle; exclude them in the F3 copy step; and sweep the existing ring6.2 areas so 6.3 inherits a clean base.

## MAJOR FINDINGS (address before build; not gate-blocking alone)

### F5 — Observer placement is right, but the context-length retry inside the request path must emit its own event.

`_chat_completion` builds the payload (:1305) then posts (:1319) — the hook belongs between them, as §6.2.B says. But `analyze()` catches `_is_context_length_error` and re-trims and re-posts within the same request attempt (:1867+). Each actual post must produce its own `prepared` event, and the re-trim on that path is precisely where the card could be silently dropped after a first verification passed. §9.2.8 must cover *this* path explicitly, not only ordinary pre-request trimming.

### F6 — The plan builds a parallel audit trail beside one that already exists. Reconcile or absorb.

`_append_request_snapshot` (:1844–1868) already records `event="request"`/`"response"` with deep-copied post-trim messages, `analysis_step`, and `request_index_within_turn`, gated by `_save_request_logs`. Two near-duplicate audit stores that can disagree is how this program's next false reading happens. Either extend this machinery to the post-`build_chat_payload` boundary, or keep the new observer and state in the evaluation how the two records join and which is authoritative. Also: check whether `_save_request_logs` was enabled in the ring 6.2 Kaggle config — if yes, the ring 6.2 downloaded output may already contain per-request message records that retro-confirm the 0/25 from a second, independent source. Cheap and worth doing.

### F7 — Missing regression test: level and life boundaries never re-trigger delivery.

`analysis_step` is monotonic per game (dataclass field solver.py:188, incremented only in the run loop; `_ensure_session` resets agent history only on a runtime-dir change, :979–988; GAME_OVER auto-reset and level advances do not touch it). So no level-2 resend exists today — but nothing pins it. Add to §9.2: a sequence with a level advance and an auto-reset asserts zero further card insertions and a never-reset `analysis_step`. This is the class of invariant that silently breaks in a later ring.

### F8 — Fallback-report games need their own lane in the denominator.

§8 handles the Captain-wins-everything case. It does not say how a Captain-fault game (honest fallback report, near-empty content) is counted. It is handoff-eligible — transport must still pass — but its Layer B grade is meaningless as card evidence. Keep fallback games in the transport denominator, tag them (`fallback: true` already exists in the fingerprint), exclude them from Layer B aggregation, and report them separately.

## MINOR FINDINGS

- **F9 · Marker naming drift.** §8 shows `RING6_`-prefixed names; §6 uses bare names. Align, and state the 6.2→6.3 marker mapping (`CARD_INJECTED` → retired/`REPORT_OFFERED`) in the evaluation template so cross-ring audit scripts cannot conflate them.
- **F10 · Verbatim append invariant.** The card enters the prompt via a plain `lines.append` and join (:1256–1257). Exact-substring matching depends on nothing ever `.strip()`ing or re-wrapping it. Add a one-line unit assertion: prompt contains the report byte-for-byte as fingerprinted.
- **F11 · Request-id must not touch the payload.** §6.1.F wants ids correlating prepared↔completed; §6.2.B forbids payload mutation. State explicitly that the id lives only in observer/audit records (correlation by call sequence or object identity), never as an injected payload field.
- **F12 · Artifact survivability is checkable now, not at review time.** §15.6 asks whether Kaggle preserves the new artifact dirs. Answer it pre-build by inspecting the ring 6.2 downloaded output layout and writing `captain_reports/` etc. under the same preserved root. Move this from peer-review question to §9.4 pre-check.
- **F13 · Concurrency.** If games run sequentially in one kernel (the 2h14m ring 6.2 window suggests so), the atomic-write/collision machinery is cheap insurance rather than a live risk — keep it, but don't let it grow.

## SCOPE ASSESSMENT

With F1's sanitizer removed and F2's narrow yield fix in its place, the ring reduces to: un-nest one append (tool_agent.py:1248), fix one yield path, retire one false marker, add fingerprint + persist + a post-payload verification hook, artifacts, and tests. That is the right size for a handshake canary. As currently drafted, the plan's largest single component (history sanitization plus its enforcement and tests) serves a semantics question the campaign has not actually ruled on — that is the one place this plan repeats the program's characteristic failure of building beyond its evidence.

## REVIEW ANSWERS TO §15

1. Prepared-observer placement: correct at `_chat_completion` post-`build_chat_payload` — with the F5 context-length-retry caveat.
2. Zero/two-copy paths: two-copy path confirmed real (yield, F2); zero-copy path exists via trimming late in turn 1 (F1 contradiction) — resolve by gating on the first request only.
3. Sanitization scope: moot if F1 is accepted; as drafted, it also risks natural-history divergence beyond the report.
4. Audit code throwing/blocking: the fail-open stance is right; add F5's retry path to the guarded surface.
5. Stable ids: yes, if F11's placement rule is adopted.
6. Artifact preservation: resolvable pre-build (F12).
7. Accidental non-transport change: **yes — the sanitizer itself (F1).** That is the review's central catch.
8. Test realism: §9.2.9/§9.2.10 are the right tests; ensure the mocked post captures the `build_chat_payload` output, not `latest_request_messages`.

## CONDITIONS FOR PROCEEDING

1. F1 ruled explicitly (recommended: natural history, insertion-once semantics, sanitizer deleted).
2. F2's narrow yield fix specified in §6.2.
3. F3's copy source named as the executed bundle tree.
4. F4's hygiene extension added to §9.4 and the base swept.
5. F7's boundary regression test added.

With those amendments, this reviewer supports execution. The plan's core instinct — that the proof boundary is the final outbound payload and everything else is intent — is the correct generalization of every instrument failure this program has paid for.

*Filed by the reviewer seat, 2026-08-30. All file:line citations read directly from the workspace at review time; the committed repo outranks this document.*
