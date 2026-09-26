# Virelai–Duck Hybrid: Governing North Star

**Status:** Governing architectural intent. Later build notes and local optimizations must be interpreted under this document.

## Core objective

Build a Virelai–Duck cognitive architecture in which **Virelai governs the investigative workflow and maintains an evolving, evidence-grounded world model, while Duck reasons and selects actions within that workflow.**

Virelai exists to make Duck follow our method of learning a novel environment. Preserving Duck's original investigative policy is not a requirement. Changing that policy is an intended part of the hybrid.

The architecture turns gameplay into a compact internal physics grammar supporting prediction, experimentation, planning, win explanation, and cross-level transfer.

## Division of responsibility

- **Virelai governs learning:** it organizes observations, maintains persistent entities and relationships, supplies relevant memory, identifies unresolved questions, records experiments, evaluates predictions, and updates investigative focus.
- **Duck reasons and acts:** it proposes explanations, designs discriminating interventions, selects actions, interprets outcomes, challenges representations, and plans with the accumulated model.
- **The environment establishes evidence:** neither Duck's assertion nor an architectural expectation establishes a fact. Observations remain intact while interpretations evolve.

## Intended progression

1. Establish the control channel and ego.
2. Identify counters and autonomous processes.
3. Discover meaningful interactions, controls, dependencies, and constraints.
4. Open role-specific questions about mappings, reachability, conditions, magnitude, recurrence, boundaries, reversibility, and coupled effects.
5. Construct and test the world's physics grammar.
6. Discover the first win through structured exploration and mechanics-guided search.
7. Explain the observed win in the learned language.
8. Transfer prior rules provisionally and deepen the model as new mechanics appear.

This is an attention policy, not an assumption that every role exists or a rigid ban on returning to earlier questions.

## Required decision contract

For each decision cycle:

1. Virelai supplies the current focus, relevant evidence, applicable rules, and unresolved alternatives.
2. Duck selects an action with an identifiable purpose: investigation, navigation, testing a rule, or pursuing an evidence-grounded win hypothesis.
3. The runtime atomically records that decision with the executed interaction.
4. Virelai evaluates the scoped consequence and revises persistent understanding.
5. The next decision reflects the revision.

Duck may propose a different focus, but the change must be represented explicitly. Navigation does not require a formal prediction. A claim of prospective validation does.

The architecture enforces participation in the process. It does not force a predetermined conclusion, require a role to exist, or prescribe Duck's exact move.

## Persistent understanding

The semantic library must connect observations, persistent entities, revisable groupings, state variables, dependencies, proposed mechanics, applicability conditions, prospective predictions, outcomes, contradictions, exceptions, revision lineage, win explanations, alternatives, and cross-level bindings.

Hypotheses may motivate a reconsideration of object correspondence, but may never rewrite observations to make an explanation fit. Representation gaps remain explicit investigation targets.

## Standard of success

The central acceptance trace is:

**observation → structured model → question → prospective prediction → matched intervention → scoped comparison → persistent revision → later reuse**

Tool-call counts, summaries, and isolated wins are supporting measurements. They do not alone establish the intended learning process.

## Governing instruction

**Build Virelai as the controller of Duck's investigative workflow. Keep Duck responsible for reasoning and action selection within that workflow. Preserve evidence, make uncertainty explicit, and ensure that learning changes persistent understanding and later behavior.**

Incremental delivery is required, but an incremental rung must not redefine Virelai as merely an optional memory aid or unchanged Duck behavior as the final standard.
