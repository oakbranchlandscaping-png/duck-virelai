# Mining: agent memory prior art — a small working card over a large gate-certified memory

**Type:** `MINE_AGENT_MEMORY_PRIOR_ART` · **v1** · **2026-09-28**
**Author:** Claude (Alpha build seat), signed
**Mode:** read-only mining (WO-00 discipline: PORT default, INVENT justified). This document builds
nothing and changes no ruling.
**Question (Director, 2026-09-28):** "We must have a large memory ability for the agent. That is
the only way our internal world model can exist. The agent must live in the moment with enough
tokens to reason while still having access to its entire accumulated memory based on the gates it
has passed."
**Trigger:** the ft09 guided v2 crash (`REVIEW_G4_FT09_GUIDED_KAGGLE_V2_2026-09-28.md`). The G3
card grew about 3,200 characters per confirmed lever, mostly history of earlier levers, and hit
the 24,000-character guard at the fifth lever. Duck made **zero** recall queries in 121 actions.

Web sources were gathered on 2026-09-28 by two research sub-agents. Their fetches were checked
against the pages they cite. Items marked **[unverified]** could not be confirmed from a primary
source. Vendor benchmark numbers are self-reported and sometimes conflict.

---

## 1 · Internal prior art first (PORT default)

We have been here before. **This is the fourth card-overflow crash, and each one was fixed by
trimming the field that overflowed:**

| When | Where | Size | Fix |
|---|---|---|---|
| 2026-09-23 | vc33 G3 entry | 277,963-character prompt (258,706-character entity ledger) | compact roster, compact confirmations |
| 2026-09-25 | vc33 v6 completion | 24,632 | completion card |
| 2026-09-28 | ft09 guided v1, G3 entry | 67,939 | R9-R04 windowed roster |
| 2026-09-28 | ft09 guided v2, fifth lever | 25,502 | *(pending)* |

The institutional-knowledge register already names this pattern: *"When fix attempts share a
structural pattern, stop fixing and consult. Repeated failures with the same shape mean the model
is insufficient, not that the next fix is closer."* (`INSTITUTIONAL_KNOWLEDGE_v2_2026-07-13`, §6)

**What we already wrote down, and only partly built:**

- **`BUILD_SPEC_G3_CONTEXT_COMPACTION_v1_2026-09-23` (the Duck Turn Contract).**
  - It states the principle: "**The prompt is a view, never the store.**"
  - Duck's turn surface is "three cards and one ask": the goal card, the subject entity's dossier
    card, and the compact last transition. "Everything else lives in persistent storage behind
    focused queries."
  - It sets **per-section budgets as packager constants with a stated sum**. In tokens: goal card
    ≤ 1k, roster ≤ 4k, subject dossier ≤ 2k, last transition ≤ 1.5k, template ≤ 1k, query
    reserve ≤ 4k, plus an explicit output reserve.
  - It asks for a packager preflight on the worst-case request, and a runtime rule that a section
    over its budget "compacts *by rule* … and says so".
  - It asks for a production-shaped **retrieval delivery test**.
  - It forbids model summarization: "compaction is deterministic projection of structured state,
    never paraphrase."
  - **Only the roster and confirmation compaction were built.** The per-section budgets, the
    worst-case preflight and the delivery test were deferred ("remain separate acceptance work").
    The card is still built by copying the whole snapshot and trimming named fields, which is why
    every new record type has leaked onto it.
- **`BUILD_PLAN_RING8_PERSISTENT_WORLD_MODEL_v1_2026-09-10`.**
  - "Virelai converts the lossless interaction record into one persistent, evidence-grounded,
    world-specific physics grammar. Duck consults that model."
  - Laws: "The canonical world model is the only semantic source of truth"; "every claim has a
    discrete status, counts, scope, and evidence references"; "the same evidence boundary must
    serialize to identical bytes".
  - Rung 7: "callable world, diff, object, mechanic, and evidence views".
  - Rung 8: an "automatic transition briefing sourced only from the canonical model".
- **Ring 8 expandable memory card**
  (`COLLABORATOR_UPDATE_RING8_MEMORY_CARD_DELIVERY_FIX_2026-09-13`).
  - Progressive disclosure: one bounded card is presented automatically, with "focused expansion
    handles", and nothing prescribes Duck's action.
  - **Duck recalled voluntarily when it mattered.** Even with the card silently undelivered, Duck
    later called the prior-level `lesson`, `win` and `carry` views on its own.
  - The first build also showed the delivery failure class: a card that is "computed but omitted
    from the model-visible prompt".
- **The Virelai canon.**
  - "The belief state is the only brain" (project law).
  - "The belief state is an accumulator, not a whiteboard" (`INSTITUTIONAL_KNOWLEDGE_v2` §3).
  - "Perfect memory is within-encounter" (doctrine 4).

  The internal world model the Director names is the controller's certified belief state, not
  Duck's context window. Duck's card is a *view* of it.
- **Duck's native form** (Tufa Labs). Observations live as Python variables in a REPL, and the
  conversation is kept short by evicting the oldest messages ("infinite play via eviction").
  https://arcprize.org/blog/arc-prize-2026-milestone-1 · https://tufalabs.ai/research/duck-harness/
  Duck's own conversation is therefore **short-term by design**. Anything it must keep knowing has
  to be re-presented by the controller, or be retrievable from Python.

**Reading:** the architecture the Director describes is already our stated design (Ring 8
persistent model, the Duck Turn Contract). What failed is that the card was never *built* to that
design. Trimming was substituted for construction.

---

## 2 · External prior art

### 2.1 Tiered memory: a small working set over a large store

- **MemGPT / Letta.**
  - Tiers: "main context" (system prompt, a fixed-size read/write working context, a FIFO queue
    with a recursive summary); **recall storage** (the full message history); **archival storage**
    (arbitrary records, searched on demand).
  - The harness warns at 70% of context and evicts at 100%.
  - Memory blocks carry a label, a value, a **character limit** and a description.
  - Deep-memory retrieval: GPT-4 32.1% → 92.5% with MemGPT.
  - Failure: "will often stop paging through retriever results before exhausting the retriever
    database"; weaker models fail the self-directed paging.
  - https://arxiv.org/html/2310.08560v2 · https://docs.letta.com/guides/agents/memory-blocks ·
    https://github.com/letta-ai/letta
- **Generative Agents.**
  - A complete memory stream sits out of context. The prompt takes the "top-ranked memories that
    fit within the language model's context window", ranked by recency + importance + relevance.
  - Reflection is triggered by the harness.
  - The prompt is **filled up to a budget**, not trimmed down from the store.
  - Ablation: full architecture 29.89 against 21.21 without memory, reflection and planning.
  - https://arxiv.org/pdf/2304.03442
- **CoALA** (a framework, not code).
  - "On each LLM call, the LLM input is synthesized from a subset of working memory."
  - Long-term memory is episodic, semantic and procedural. Retrieval and learning are explicit
    actions.
  - https://arxiv.org/pdf/2309.02427
- **Zep / Graphiti.** A temporal knowledge graph. Old facts are "invalidated — not deleted", and
  you can query what was true at any time. https://arxiv.org/abs/2501.13956 ·
  https://github.com/getzep/graphiti
- **Mem0, A-MEM, LangMem, HippoRAG.** Harness-driven extraction and consolidation into vector or
  graph stores, with top-k injection. https://arxiv.org/abs/2504.19413 ·
  https://arxiv.org/html/2502.12110 · https://github.com/langchain-ai/langmem ·
  https://arxiv.org/abs/2502.14802

### 2.2 Keeping the working set lean: deterministic beats paraphrase

- **Anthropic, "Effective context engineering for AI agents".**
  - Aim for "the smallest set of high-signal tokens".
  - Context rot and a finite "attention budget".
  - Just-in-time retrieval through lightweight identifiers; structured notes kept outside the
    context; compaction.
  - https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- **Context rot (Chroma).** 18 models, including Qwen3. Focused prompts of about 300 tokens beat
  full prompts of about 113k: "significantly higher performance on focused prompts".
  https://www.trychroma.com/research/context-rot
- **"The Complexity Trap" (JetBrains; tested on Qwen3 and Gemini 2.5 Flash).**
  - Simple observation masking with a 10-turn window "halves cost" and matches or beats LLM
    summarization.
  - Summarization made runs 15% longer, because summaries hide signs that the agent should stop.
  - https://arxiv.org/abs/2508.21433
- **ACE (Agentic Context Engineering).**
  - Repeated LLM rewriting of the context caused "context collapse": 18,282 tokens → 122, and
    accuracy fell below baseline.
  - The fix: itemized bullets with IDs, merged by **non-LLM** logic.
  - https://arxiv.org/html/2510.04618
- **OpenAI cookbook.** Summaries risk "context poisoning". https://developers.openai.com/cookbook/examples/agents_sdk/session_memory
- **OpenHands condenser / SWE-agent history processors.** Keep the first events and the recent N;
  mask older output with placeholders; no LLM.
  https://docs.openhands.dev/sdk/guides/context-condenser ·
  https://swe-agent.com/latest/reference/history_processor_config/
- **Aider repo map.** A ranked table of contents shown **every turn** under a 1k-token budget.
  "The LLM can ask to see these specific files." https://aider.chat/docs/repomap.html

### 2.3 Will the agent recall on its own? Mostly not; scaffold it.

- MemGPT stops paging early (above).
- Models "have difficulty knowing they do not possess certain knowledge", so they under-retrieve.
  https://arxiv.org/abs/2402.11457
- Retrieval quality, not the agent's use of what it retrieved, explains most memory accuracy
  (r = 0.98 with retrieval precision). https://arxiv.org/html/2603.02473v2
- **Selective, harness-injected recall beats both agent-initiated recall and always-on
  injection.** A proactive memory agent injects a reminder or stays silent, +8.3 pp on
  Terminal-Bench. https://arxiv.org/abs/2607.08716
- **Production scaffolds that make recall a harness step:**
  - Anthropic's memory tool injects "ALWAYS VIEW YOUR MEMORY DIRECTORY BEFORE DOING ANYTHING
    ELSE". https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool
  - Google ADK offers `preload_memory` (automatic, every turn) against `load_memory` ("when your
    agent decides"). https://adk.dev/sessions/memory/
  - Anthropic reports memory tool plus context editing at +39% over baseline.
    https://www.anthropic.com/news/context-management
- **The counter-case.** Letta argues that agents searching iteratively do well: 74% on LoCoMo,
  with frontier models. https://www.letta.com/blog/benchmarking-ai-agent-memory . Our own Ring 8
  evidence agrees in part: Duck voluntarily recalled prior-level lessons.

### 2.4 Game and world-model agents

- **Claude Plays Pokémon** [partly secondary].
  - A self-edited knowledge base in the prompt, plus "accordion" summarization.
  - Documented failures: it "deleted all its notes on Mt. Moon routing… mistakenly concluded that
    it had already beaten Mt. Moon"; notes were lost in "overzealous memory cleanups"; it looped.
  - https://www.lesswrong.com/posts/HyD3khBjnBhvsp8Gb/so-how-well-is-claude-playing-pokemon ·
    https://www.lesswrong.com/posts/sehJYg5Yny9fvpbpt/a-year-late-claude-finally-beats-pokemon
  - **The failure is the LLM writing its own memory.**
- **Gemini Plays Pokémon.** A notepad, a JSON tile map, summaries every 100 turns. It fell into a
  "pattern-repeating mode" past about 100k tokens.
  https://blog.jcz.dev/the-making-of-gemini-plays-pokemon
- **Voyager.** Procedural memory as a code skill library, with the top 5 retrieved per task.
  **Skills are committed only after self-verification.** Removing the library: 29 vs 21
  iterations, and no diamond tools. https://ar5iv.labs.arxiv.org/html/2305.16291
- **GITM.** After N verified successes, a sub-goal's plans are summarized into one reference plan.
  Memory raised ObtainDiamond from 57.5% to 67.5%. https://ar5iv.labs.arxiv.org/html/2305.17144
- **Optimus-1.** A knowledge graph plus an experience pool. Keeping failures is worth about 10%.
  https://arxiv.org/html/2408.03615v2
- **WALL-E.** Rules induced from prediction failures and pruned to a minimal set. Language rules go
  in the prompt; code rules **check the LLM's proposal**. https://arxiv.org/html/2410.07484v1
- **ARC-AGI-3.**
  - The technical report says "maintaining a naive rolling window of observations quickly exhausts
    a model's context budget". One harness lets the model run Python to "selectively retrieve and
    transform information from its action history". An orchestrator design sends only compressed
    sub-agent summaries upward. On one environment a harness took a model from 0.0% to 97.1%.
    https://arxiv.org/html/2603.24621v1
  - Preview winners keep controller-owned state graphs, with no LLM memory.
    https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings
  - "Executable World Models" verifies its world model by **replay against recorded observations**,
    the closest external analogue to our lossless record plus gates. Failure: "premature
    commitment". https://arxiv.org/html/2605.05138v2
  - Milestone 1: "hand-crafted tools actually hurt the model" (Duck); the winning forge
    configuration "disabled extra machinery". https://arcprize.org/blog/arc-prize-2026-milestone-1
- **No surveyed system has a named, multi-stage certification ladder** like our gates. Voyager
  (verify, then commit), GITM (N successes, then summarize), WALL-E (keep only rules that fix
  failures) and Executable World Models (replay-verify) are the nearest patterns.

---

## 3 · Synthesis: what the prior art says our memory should be

This maps the evidence onto Virelai's own terms. It is a reading, not a ruling.

| Tier | Virelai name | Prior-art analogue | Who writes | What reaches Duck |
|---|---|---|---|---|
| **Record** | the lossless transition record (`snapshot()`, gate artifacts) | MemGPT recall storage; the Generative Agents memory stream; Zep invalidate-not-delete | controller only | nothing by default; recalled by query |
| **World model** | the belief state: gate-certified products (EgoLaw, CounterModel and mask, LeverInventory, lever anatomies, orbits, and later laws) | Letta core blocks; CoALA semantic memory; Voyager verified skills; ACE itemized bullets; WALL-E rules | controller, **only after a gate certifies** | **a compact digest pinned on every card**, one line per product with its ID and a query handle |
| **Card** | Duck's working memory for this turn | CoALA "synthesized from a subset of working memory"; the Generative Agents budget fill; Aider's budgeted map | a card *builder* with named slots and per-slot budgets | goal and target, the current subject, the last transition, the answer template, the world-model digest, and an index of what can be recalled |

**Movement between tiers, following the evidence:**

1. **Controller-injected recall first.** When the current step touches something the world model
   or record knows, the controller puts that item in a recall slot. Examples: the lever being
   pressed has a certified anatomy; the object clicked was already a scoped null. A 27B model will
   not reliably ask (MemGPT, retrieval-overconfidence, the proactive-memory results), and ours
   made zero recall queries.
2. **Agent pull second.** Duck can query anything through Python with `virelai(...)`, which is
   Duck's native REPL form and matches the ARC harness that "selectively retrieves… from its
   action history". It is kept as one small, stable interface, because hand-crafted tools hurt
   this model.
3. **Deterministic projection only.** Nothing is summarized by a model. Compaction renders counts,
   windows, IDs and placeholders from structured state (the Complexity Trap, ACE collapse,
   context poisoning, and our own mythology guard).
4. **The controller is the sole writer.** Duck proposes; gates certify; the controller writes.
   This avoids the best-documented game-agent memory failure (Claude deleting true notes, false
   "done"). It is also our clearest difference from the field.
5. **Promotion is gated.** Knowledge enters the pinned digest only when a gate closes (Voyager,
   GITM, Executable World Models). Refutations and nulls are kept (Optimus-1, WALL-E) but live in
   the record and are recalled, not pinned.

**What this means for "a large memory ability":** the large memory already exists and is
lossless. That is the record, and the certified products are in the target journal. What is
missing is:
- **(a)** the certified world model shown to Duck as a first-class, always-present digest across
  gates;
- **(b)** a card *built from slots with budgets* instead of trimmed from state;
- **(c)** recall the controller injects when relevant, not only recall Duck must think to ask for.

With those, card size depends on the slot budgets, not on world size or on how much has been
found. Duck keeps most of its context for reasoning while having everything it has earned within
one query, or already on the card when it matters.

## 4 · Open questions for the Director

1. **Is the Duck Turn Contract** (`BUILD_SPEC_G3_CONTEXT_COMPACTION_v1`) **the governing card
   design across all gates**, with its unbuilt parts (per-section budgets, worst-case preflight,
   delivery test) completed as the next revision instead of another field trim?
2. **Should the certified world-model digest be pinned on every card from G1 onward** ("based on
   the gates it has passed"), with a fixed budget, one line per product?
3. **What sets the injected-recall policy?** The controller alone, deterministic and matched to
   the current subject? Or a separate selector?

— Claude, Alpha build seat, 2026-09-28
