# Prior art: world description and physics grammar

**Date:** 2026-10-12
**Purpose:** direct the future world-description build to existing repo machinery without reviving a second belief writer
**Accepted runtime base:** `b635fb9`
**Status:** read-only survey; no runtime decision or code change

## 1. Finding

The repository already contains most of the lower-level machinery needed to describe a world:

- a game-free visual verb alphabet;
- conservative object continuity and exact pixel arithmetic;
- archetype nouns and their nested question trees;
- action-indexed effect channels and transformation typing;
- G4 products for anatomy, orbit, relations, and tested law descriptions;
- an older player-facing grammar renderer;
- a typed executable sentence engine in an unaccepted draft;
- an actor-independent win capsule and post-win comparison tools.

The missing accepted capability is the bridge into the canonical v2 library. The build should extend that artifact to v3. It must not revive the old query-triggered model or shadow semantic library as an authority.

## 2. Read order for Claude

### A. Start with the accepted canonical path

1. `inference/framework/world_model_v2.py`
   - schema and single-writer boundary at lines 35–52;
   - validation at lines 98–237;
   - current certified roles are deliberately limited to EGO, COUNTER, and LEVER.
2. `inference/framework/library_census.py`
   - observation/certification split in the module header;
   - track projection at line 153;
   - gate-backed roles at line 323;
   - level compilation at line 496.
3. `inference/framework/virelai_continuity.py`
   - accepted runtime verb set at line 28;
   - exact component sightings at line 79;
   - lossless pixel arithmetic at line 224;
   - adjacent-frame matching at line 386;
   - worldline weaving at line 497.
4. `inference/framework/library_view.py`
   - bounded page surface at lines 51 and 372;
   - current findings renderer at line 172;
   - digest budget path at line 278.

These files define where the new description belongs and how Duck may read it.

### B. Read the observation language

1. `virelai_golden/weave/verbs.py`
   - `Verb` at line 27: `STILL`, `RECOLOR`, `MOVE`, `GROW`, `SHRINK`, `BIRTH`, `DEATH`, `DEFORM`, `AMBIGUOUS`;
   - `TransitionSignature` at line 40;
   - cell-level signature and verb derivation at lines 74 and 101.
2. `virelai_golden/weave/edge.py`
   - site → class → residual matching;
   - exact deltas for recolor, growth, shrinkage, and translation;
   - its anchor-first correspondence rule is explicitly interim and must not be promoted into doctrine.
3. `virelai_golden/weave/worldline.py`
   - persistent object construction;
   - continuation versus birth/death/deform behavior.
4. `inference/framework/virelai_continuity.py`
   - this is the accepted runtime port and should be reused instead of importing a second matcher.

The verb is descriptive: it states what a matched visual object did. It does not state why.

### C. Read the noun and subtree design

1. `docs/canon/FOUNDATIONAL_ARCHETYPES_v2_2026-07-22.md`
   - the six nouns at line 18: EGO, COUNTER, LEVER, ENVIRONMENTAL FORCE, REACTIVE-DRIVEN, INERT;
   - each noun's observable, exclusions, and subtree at lines 22–99.
2. `docs/canon/NESTED_TAXONOMY_SPEC_v5_2026-07-22.md`
   - Band 1 STATIC/REACTIVE at line 22;
   - set-valued Band 2 roles at line 34;
   - transient animation law at line 48;
   - tag → children → subtrees at line 63.
3. `virelai_golden/roles/infer.py`
   - old executable Band-1 and role ladder at lines 41–123.

The two canon files are marked draft/reconstruction. Their six-noun vocabulary is adopted by the current build plan, but their old statistical thresholds and detector results are not certification authority. `roles/infer.py` is prior art for predicates and data shapes only.

### D. Read the effect and causal machinery

1. `inference/framework/g4_reactions.py`
   - `EffectChannel`, `LeverEffectAnatomy`, compilation, and answer validation at lines 52–284.
2. `inference/framework/virelai_gates.py`
   - G4 gate IDs at lines 128–133;
   - `LeverEffectAnatomySet` product around line 5759;
   - `LeverOrbitSet` product around line 6317.
3. `inference/framework/g4_relations.py`
   - frozen predictions at line 162;
   - grading at line 232;
   - outcome records and relations answer at lines 261 and 301.
4. `inference/framework/g4c_gate.py`
   - prospective lever-law gate at lines 70–335;
   - the product distinguishes supported, unresolved, and boundary-closed descriptions.

These products may promote a descriptive transformation into a scoped causal sentence. Raw grid adjacency may not.

### E. Mine the older semantic pipeline, without restoring its writer

1. `inference/framework/virelai_semantic/compiler.py`
   - object deltas at line 340;
   - joint action deltas at line 384;
   - semantic entities at line 433;
   - full shadow compilation at line 586.
2. `inference/framework/virelai_semantic/mechanics.py`
   - effect-channel grouping at line 143;
   - lever mechanics at line 243.
3. `inference/framework/virelai_semantic/typing.py`
   - evidence-bounded channel typing at line 25.
4. `inference/framework/virelai_semantic/joint_transform.py`
   - component rewrites and joint transformation compilation at lines 32–128.
5. `tools/render_semantic_library.py` and `tools/render_physics_grammar.py`
   - useful human presentation and naming patterns;
   - explicit unknown sections;
   - older output schemas that must not become canonical.
6. `tests/test_semantic_library_shadow.py`
   - strong fixtures for exact entered/departed sites, effect grouping, state transitions, and refusal to invent hidden variables.

This path was passive shadow analysis with unvalidated role detectors. Reuse pure algorithms and tests. Do not reuse `semantic_library.json` as a writer or accept its role claims.

### F. Inspect the legacy model only for data-shape lessons

`inference/framework/virelai_world_model.py` contains `MechanicRule` at line 82, `WinRecord` at line 119, observed mechanics at line 728, and deterministic rendering helpers near line 1054. It compiled raw/shadow observations independently and once competed for `world_model.json`. Its useful ideas are explicit evidence, limitations, states, mechanic rules, and level diffs. The accepted build has moved canonical ownership to `world_model_v2.py`; do not call the legacy compiler from the new path.

### G. Keep win machinery downstream

1. `inference/framework/virelai_win_capsule.py`
   - `WinCapsule` at line 21;
   - actor-independent observed boundary capture at line 65.
2. `tools/compile_post_win_grammars.py`
   - observed-win attachment at line 20;
   - minimal recorded separator at line 114;
   - human rendering at line 178.
3. `tools/freeze_win_corpus.py`
   - immutable win corpus preparation.

The capsule correctly records a win without claiming its cause. The older post-win compiler can suggest presentation and comparison tests, but it uses regions rather than the accepted certified noun/verb language.

### H. Treat the executable grammar as an unaccepted draft

The worktree currently contains untracked `inference/framework/physics_grammar.py`, `physics_grammar_bridge.py`, `win_referee.py`, `tests/test_physics_grammar_contract.py`, and `SPEC_PHYSICS_GRAMMAR_v3_2026-10-08.md`.

The draft has valuable structures:

- immutable `Subject`, `Entity`, `Board`, `Event`, and expression nodes;
- three-valued evaluation;
- deterministic serialization and hashes;
- separation between sentence evaluation and the observed win label;
- prospective evaluability and referee misfires.

It is not accepted source. Review it as a candidate vocabulary after the descriptive world model is built. Do not stage it accidentally and do not let its bridge write beliefs.

## 3. Recommended reuse boundary

### Reuse directly

- the accepted `virelai_continuity` tracks, edge verbs, deltas, and pixel arithmetic;
- the canonical census's transition IDs, tracks, receipts, joins, and certified roles;
- G4 products and accepted answer receipts;
- the library view's hard budgets and paging pattern;
- win capsules as factual boundary records.

### Port as pure logic with new tests

- effect-channel grouping and transformation typing from `virelai_semantic`;
- human rendering patterns from the semantic and physics renderers;
- typed sentence serialization/evaluation ideas from the draft grammar;
- old world-model structures for limitations, state variables, mechanics, and level diffs.

### Do not reuse as authority

- shadow or golden role verdicts;
- the legacy `virelai_world_model.py` writer;
- raw proximity or coincidence as causality;
- reconstructed canon thresholds;
- post-win separators as proven causes;
- the untracked grammar modules until their own interface is accepted.

## 4. First build slice this survey supports

The first world-description slice should extend the canonical schema to v3 with a **descriptive event ledger**. For every recorded transition it should emit:

- subject track ID and life/level scope;
- certified archetype noun when one exists, otherwise `UNRESOLVED_OBJECT`;
- one observation verb from the accepted continuity result;
- exact before/after class, footprint, anchor, size, and delta where available;
- transition and receipt references;
- correspondence confidence or ambiguity;
- explicit `OBSERVED`, never `CAUSED`, status.

It should also emit a deterministic scene summary: objects present, certified roles, current states, departed objects, and unexplained transformations.

G4 then promotes selected observed events into scoped causal sentences by citing a gate product and its receipts. Later G5/G6 products do the same for forces, driven responses, and negatives. An observed win may be described only with nouns and verbs already present in the frozen pre-win library.

## 5. Fail-first cases to preserve

1. MOVE, RECOLOR, GROW, SHRINK, BIRTH, DEATH, DEFORM, and AMBIGUOUS render distinctly.
2. A moved object retains identity only through the accepted continuity result.
3. A class change records the transformation and reopens role typing.
4. A transient that settles back does not automatically flip Band 1.
5. One transition may describe several object transformations without calling any one of them causal.
6. Counter and ego changes remain visible in the description while G3 masks them for lever attribution.
7. A G4 witness can promote a scoped cause; a coincident unbound change cannot.
8. Every rendered noun, verb, and causal relation resolves to canonical receipts.
9. The same model renders byte-identically twice.
10. No description module mutates a gate or writes a second canonical artifact.
11. A winning transition can be described from a frozen pre-win vocabulary; an unknown object or relation remains an explicit gap.

## 6. Instruction summary for the builder

Build outward from `world_model_v2.py` and `library_census.py`. Use `virelai_continuity.py` as the only observation matcher. Use the golden weave and old semantic pipeline as test and algorithm sources. Use gate products as the only causal promotion path. Render from the validated v3 artifact through `library_view.py`. Keep the win capsule and referee downstream until ordinary non-winning levels receive a useful detailed description.
