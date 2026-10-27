# Community post drafts

## Reddit

**Suggested title:** We open-sourced Virelai: an evidence-first world model for an ARC-AGI-3 agent

I spent the last few months building an ARC-AGI-3 agent around a question that ended up being more interesting than
the score: **what would it look like for an agent to maintain a detailed, auditable internal model of a world rather
than relying on prompt history and prose notes?**

The result is Virelai / Cybernetic Duck, and I have now made the full repository public:

https://github.com/oakbranchlandscaping-png/duck-virelai

The architecture splits exploration between a deterministic controller and a language model. The controller handles
routine coverage and records exact receipts. The model chooses among bounded, gate-admitted experiments when judgment
is useful. A persistent semantic library stores object tracks, observational transformations, per-lever mechanics
dossiers, provenance, gaps, open questions, and observed wins.

The gate ladder asks, in order:

1. What does the agent control?
2. Which changes are global or automatic counters?
3. Which objects are interactive levers?
4. What does each lever affect, and what persists, reverses, or cycles?

The repository includes the complete development history, including failed approaches and superseded designs. The
current implementation has an exact 1,487-test snapshot, strict model validation, hash-chained provenance, bounded
runtime recovery, human-readable reports, and offline claim/key/grading tools.

Honest status: this is a research prototype, not a state of the art result, and it did not become the full paper I had
planned. It does not yet show reliable general puzzle solving or a controlled score improvement. I am releasing it
because I think the architecture, evidence discipline, and failures are useful material for the community.

I would particularly value criticism on:

- whether a hand-designed gate ladder is useful or too rigid;
- how object identity should survive resets, deaths, and scene changes;
- what belongs in deterministic infrastructure versus model judgment;
- how to evaluate invented or unverifiable claims when a human key cannot cover everything; and
- whether this kind of structured memory helps smaller models.

Start with the README and community release note. Issues, counterexamples, and ports are welcome.

## Discord

I’ve open-sourced **Virelai / Cybernetic Duck**, an ARC-AGI-3 research prototype for evidence-backed world modeling:

https://github.com/oakbranchlandscaping-png/duck-virelai

The basic idea is to give an agent a persistent semantic library instead of relying on prompt history. Deterministic
code performs routine coverage and records receipts; the language model chooses among bounded experiments; validated
records accumulate object tracks, transformations, lever dossiers, provenance, gaps, and observed wins.

The repo includes the full build history, failed routes, Kaggle packages, strict validators, and a 1,487-test
acceptance snapshot. Honest caveat: it is a research prototype, not a SOTA result, and it did not become the full paper
I originally planned.

I’d love feedback on the gate-based study ladder, identity across resets, deterministic versus model-owned reasoning,
and whether this kind of structured memory could help smaller agents. Critical reviews and counterexamples are very
welcome.
