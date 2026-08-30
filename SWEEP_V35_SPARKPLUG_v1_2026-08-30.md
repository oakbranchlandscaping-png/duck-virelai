# SWEEP — V3.5'S QWEN SPARK PLUG AND THE REPORT-USE PROBLEM
**Type:** SWEEP_V35_SPARKPLUG · **Version:** v1 · **Date:** 2026-08-30
**Sources (read directly):** `Universal_Solver_v3_5/qwen/*` (539 lines),
`crucible/qspi/qspi_loop.py`, `crucible/qspi/qspi_handler.py`,
`data/system_prompts/qspi_curiosity.md`,
`docs/CAMPAIGN_QWEN_CORRECTION_NORTH_STAR.md`,
`WO_FIELDCARD_00_REPORT.md`, `WO_FIELDCARD_03_DRAFT.md`,
`virelai-resource/README.md`.

## 1 · What the spark plug is

Two generations. First, `qwen/` — the V3-heritage escalation interface: Qwen as
a Tier 3–4 hypothesis generator returning bounded JSON. Second, QSPI — the
"Qwen Spark Plug Interface," later re-derived as "Qwen Steered Probe
Iteration": the designed Phase-2 curiosity loop. The model reads a bounded
FieldCard projection of the world model, proposes exactly ONE probe as strict
JSON, deterministic logic validates and executes it, the world model absorbs
the measured result, and the loop repeats until saturation or budget. The
name is the architecture: the model is a spark plug — a small, bounded
ignition inside a deterministic engine. It is never the driveshaft.

## 2 · The catastrophe that named the laws (Campaign CORRECTION, 2026-03-18)

Qwen was once given veto authority inside Phase 4 execution. Measured result:
it consistently said NO to correct deterministic directives, returned
coordinate-free JSON, the parser defaulted missing coordinates to (0,0), and
every online run navigated to the top-left corner after every abort. The
north star's verdict, verbatim: "The deterministic decision tree has been
producing correct directives the entire time. Qwen has been destroying them."
And the deeper audit: **every scoreboard improvement in v3.5's history traced
to deterministic code only.** The correction was codified as law: an authority
order with QSPI dead last; Law 15 (Subordination — Qwen proposes,
deterministic logic decides); Law 10 (Prompt Constancy — the system prompt is
hash-verified on every call, `PromptHashMismatch` is a hard error); Law 1
(Determinism — temperature 0); strict JSON parse with NO auto-repair and a
typed `is_fallback=True` proposal on any failure — never a defaulted value.

## 3 · How v3.5 made the model use the report — the Director's question, answered by prior art

1. **Use is structural, not requested.** The QSPI system prompt's key rule:
   "Never invent class IDs not present in the field card." The model's only
   legal output is a SELECTION FROM THE REPORT'S OWN CONTENTS. You cannot
   ignore a report that is your entire output vocabulary.
2. **The card is a bounded projection, refreshed — never an archive.**
   1,500-char ceiling (legacy) / 6,000-char narrative ceiling, "overwritten
   each cycle, never appended." Durability was achieved by RE-PROJECTION
   each call, not by hoping conversation history retained anything. v3.5
   never fought context trimming; it made every call fresh.
3. **Two libraries, two cards.** Library A (empirical, volatile,
   world-specific) projected as the FieldCard; Library B (curated, stable,
   game-agnostic mechanism vocabulary and strategy heuristics) projected as
   an Action Card. The hybrid today ships only Library A's analog.
4. **Behavioral grading was built into the loop.** A probe's value was
   measured by delta novelty (delta_hash, `novel` flag, EntropySidecar
   entropy ratio; exit on `entropy_zero`) — never by the model's stated
   reasoning (capped at 80 chars precisely so it could not become the
   product). This is the in-house precedent for the outsider bootstrap's Q5:
   grade use by world-information terms, not words.
5. **Referability.** WO-FIELDCARD-03's fixes: stride as a number, grouped
   same-class objects, ordinal labels (Lever A, Lever B) so a reader can
   refer back to a specific fact. Facts with stable handles get used; facts
   without handles get paraphrased and lost.

## 4 · Mapping to duck-virelai — the inversion, and what transfers

v3.5 and the hybrid are mirror images: there the deterministic engine owned
the loop and consulted the model; here the model (Duck) owns the loop and the
deterministic engine (Captain) is consulted once. Direct transfers:

- **Q1 durability:** v3.5's answer is re-projection, not retention. The
  ring 1–5 per-turn digest TRIED this and failed by projecting invented,
  unbounded content into a degraded prompt; v3.5's worked because the
  projection was verified, bounded, and overwritten. If ring 7 shows use
  decaying with turns, the remedy with prior art behind it is a bounded,
  refreshed projection (tool-served or single-line), not a bigger first-turn
  card. To be weighed against the revelation's warning about re-wrapping.
- **Q2 method adoption:** constrain Duck's declared goal/prediction to
  selections from the report (a named gap, a briefed claim) — the "never
  invent class IDs" pattern applied to Ring 6.6's contract fields.
- **Q3 calibrated trust:** where we cannot subordinate the decider, we can
  still VALIDATE its declarations deterministically (does the named target
  exist; was the named gap actually in the card) — advisory checks, logged
  not vetoing, given finding 5's compliance hazard.
- **Q5 measurement:** delta-novelty grading over reasoning-text grading,
  verbatim precedent.

## 5 · The tension both archives leave us

v3.5's final evidence says: at this model scale, the model placed in
authority destroyed value, and every improvement was deterministic. The r0
baseline says: the model in its OWN native harness is worth 30.5 — five times
our best wrapped variant. These do not contradict; together they say the
model is powerful in its native loop and destructive when jammed into ours.
That is the ring 7 thesis stated from the other side of the mirror: don't
wrap the model, and don't put it in charge of your machinery — feed each side
what the other measured. The spark plug and the minimal hybrid are the same
design philosophy applied in opposite directions.

*Committed repo outranks this sweep; the cited v3.5 files outrank my
compression of them.*
