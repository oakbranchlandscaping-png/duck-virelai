# Community release — 27 October 2026

## Why release this now

Virelai did not mature into the full paper we originally planned. The implementation nevertheless contains ideas we
want other researchers and builders to inspect, challenge, reuse, or simplify. Releasing the whole repository also
keeps the failed routes and engineering evidence visible rather than presenting a cleaned-up retrospective.

## The contribution we think is worth discussing

The core proposal is an **evidence-first semantic library for interactive agents**:

- decompose world learning into typed questions;
- admit bounded experiments rather than unconstrained exploration;
- let deterministic code handle routine coverage;
- let a language model choose only where judgment adds value;
- store every action and conclusion with an auditable receipt;
- keep open questions and identity gaps visible;
- produce a compact live view without allowing that view to rewrite the record.

This turns “agent memory” into a small, validated world model with explicit epistemic states.

## Pieces that may be independently useful

1. **Gate ladder.** Control, counter, entity inventory, and lever mechanics become separate studies with explicit
   admission and closure rules.
2. **Observational grammar.** Changes are described through nouns, tracks, regions, and verbs before mechanistic
   explanations are attempted.
3. **Per-object dossiers.** Each certified lever carries anatomy, orbit, limits, relations, law, evidence, and open
   items rather than one prose summary.
4. **Provenance by construction.** Accepted and refused work, executor identity, product origin, model hashes, and
   report hashes are reconciled at seal time.
5. **Fail-closed recovery.** Timeouts and interface failures do not become claims about world mechanics.
6. **Offline grading contract.** Model content can be projected into atomic claims, mapped to independently authored
   keys, and graded without feeding reports back to the agent.

## What the repository demonstrates

- A working schema-v11 semantic model and report pipeline.
- Deterministic compilation and strict validation over saved fixtures.
- Library-directed G3/G4 studies and bounded controller fallback.
- Observed-win episodes separated from causal claims.
- A 1,487-test acceptance snapshot, with 1,486 passing and one skipped on the final Mac run.

## What it does not demonstrate

- A statistically controlled improvement in ARC-AGI-3 score.
- Reliable transfer from a learned world model to winning future levels.
- Complete noun continuity or a complete physics grammar.
- A finished 25-world keyed evaluation.
- A result strong enough to support the full paper originally envisioned.

## Questions for the community

- Is a gate ladder a useful way to control active world-model learning, or is it too hand-designed?
- Which parts belong in deterministic infrastructure, and which should remain model judgment?
- How should an agent represent identity through deaths, resets, and scene changes without inventing continuity?
- What is the smallest useful mechanics dossier?
- How should “invented”, “wrong”, “missed”, and “unverifiable” be measured when the key cannot cover every claim?
- Can this evidence discipline improve a much smaller agent, where prompt history is especially scarce?

Issues, counterexamples, ports, and negative results are welcome.
