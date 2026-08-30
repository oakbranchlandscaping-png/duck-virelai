# Ring 6.3 evaluation

Run label: `duck-virelai-ring6.3` (verified in benchmark.json)
Run window: 2026-08-30 16:31:14–18:45:00 (2h13m45s)
Raw artifacts: `kaggle-output/`
Code anchor: `f36c149`; bundle anchor: `aee22f7`
Evaluator: Cowork (hybrid seat). Every transport number below was independently
recomputed from the raw artifacts — saved report bytes vs saved payloads —
never taken from markers alone.

## Verdict

**TRANSPORT PASSED, 25/25.** The exact Captain report — byte-identical to the
persisted `captain_reports/<stem>.txt`, SHA-256 verified — appears exactly once
in the user role of the first outbound Duck provider payload in every game,
at `analysis_step == 1`, with Captain/global action counts of 6–84 (nonzero in
all 25). The Ring 6.2 defect is repaired and the repair is proven at the
provider-payload boundary. **This is the first run in the program in which the
Virelai→Duck information handoff actually occurred.** The campaign's semantic
questions (card quality, ontology, Captain evidence) are unblocked.

## Layer A — transport (release gate)

| Check | Result |
|---|---|
| Exact report artifacts saved | 25/25, 1,833–8,295 chars |
| Report present exactly once in first Duck payload (recounted from bytes) | 25/25 |
| Stored sha256/chars/bytes agree with payload substring | 25/25 |
| Canonical marker sequence PROBE_START→…→DUCK_FIRST_ACTION in order | 25/25 |
| `REPORT_ATTACHED` exactly once / `REPORT_REQUEST_ACCEPTED` exactly once | 25/25 each |
| `REPORT_ATTACH_FAILED` / `REPORT_AUDIT_FAULT` / `REPORT_PERSIST_FAILED` | 0 |
| Fallback reports | 0 (all 25 rendered) |
| `HANDOFF_NOT_REQUIRED` | 0 (all games reached Duck) |
| Max exact user-copies in ANY of the 31–105 requests per game | 1 |
| Natural history retention into later turns (by design; no sanitizer) | 24/25 games |

Captain behavior, unchanged in shape from 6.2: 867 actions (min 6, median 32,
max 84), 0 faults, stop reasons 24 TIME_CAP / 1 TWO_LIVES_USED. Probe-phase
LEVEL ADVANCEs: 2 (vc33, ls20) — same credit rule as 6.2's vc33.

## Layer B — Duck use (behavioral evidence, not proof of cognition)

Measured over **model-authored text only** ([THINKING]/[ASSISTANT] sections of
the first analysis turn; USER PROMPT/system text excluded): **24/25 games
reference the report in the model's own first-turn reasoning.** Example (ls20,
verbatim): *"The Captain report gives me information about the world from the
probe phase. Key observations from the report: 1. I have a body that moves 5
pixels per step… 2. There's a counter in the bottom-left area that's growing…"*
— specific card facts, restated and used.

The one non-referencing game is ft09 — which scored highest. Reference is not
benefit and benefit is not reference; per-game direct/partial/ignored/
contradicted grading against each saved card remains the next human-read task.

METHODOLOGY NOTE (recorded per §5 discipline): a first Layer-B count of 25/25
was discarded as **prompt echo** — the system prompt says "the report" every
turn, and a naive transcript grep counts it. The 24/25 figure counts only
model-authored sections. Same trap as ring3's "compliance" and `falsif`×3757.

## Layer C — outcome (one stochastic pass; direction, not causal estimate)

Against Ring 6.2, the closest control (same Captain perturbation, NO delivery):

| | ring6.2 | ring6.3 | delta |
|---|---|---|---|
| total score | 4.550 | **13.970** | +207% |
| total ex-ft09 | 4.550 | **9.550** | +110% |
| levels | 8 | **12** | +4 |
| scoring games | 8 | **11** | +3 |
| Duck-phase actions | 2,935 | 2,884 | −2% |
| complete-game wins | 0 | 0 | — |

Per-game: 8 up, 4 down, 13 unchanged. Big movers up: ft09 0→4.42, tn36 0→3.57,
ls20 0→1.69, r11l 0→0.82. Down: sp80 0.80→0, lp85 2.01→1.39, ka59 0.31→0,
cn04 0.21→0. Also beats the ring6.0 no-Captain control (6.33 total).
**First ring in the program whose improvement survives removing ft09.** One
25-game pass per arm; LLM play is stochastic; treat as strong direction, not a
measured effect size. A repeat pass would firm the read.

## Anomalies

- **m0r0 token under-report:** summary says 583 tokens, but the transcript is
  1.4 MB across 55 analysis turns with zero analyzer errors and a full 7,920s
  budget. Accounting defect (likely usage propagation), NOT_MEASURED beyond
  this observation; does not affect transport. Owed a look before any
  token-based comparison uses this run.
- ft09 remains the variance monster (4.42 of the 13.97 total).

## What this run does NOT show

It does not prove the model *understood* the card (Layer B grading is proxy +
one read); it does not measure card quality (that comparison needs the now-
possible arms); and its score deltas are single-pass. Ring 6.2 stands as the
no-delivery control; ring 6.3 is the delivered arm.

## Next

1. Per-game Duck-use grading: each saved card beside the first response.
2. The unblocked ladder (recap §10): card format review, Captain tuning
   (24/25 TIME_CAP stops; NAV collision sweep), ontology arms, win analysis.
3. Optional: second 6.3 pass for variance before any semantic ruling.
