# RING 4 DESIGN — THE FIELD CARD
**v1 · 2026-08-27 · Chamber: Cowork (interim)**
**Ruling basis:** Director 2026-08-26 (the field card is the reading surface the library
owes the model) · Director 2026-08-27 (**the card's input is observed, not concluded**) ·
STRATEGY.md §6 constraints 1-5 · METHODOLOGY §1-§3 · R-C (transcribe with provenance) ·
R-E / FRICTION-004 (name the consumer before the producer).

## 0 · The one variable

A **field card**: a natural-language dossier over the library, rendered **inside the
sandbox** from the `virelai` snapshot the harness already ships, callable by the model as
`virelai_card()`. Plus the snapshot fields it needs, and the prompt prose it earns the
right to delete.

Baseline arm = frozen r0. Prior arm = ring3.

## 1 · Harvest table (read end-to-end, cited per R-C)

Source: `ARC_3_BETA/arc-prize-2026-arc-agi-3/ARC-AGI-3-Agents/virelai_v4/library/field_card.py`
(617 lines) and `GRAMMAR_AUDIT/04_reactivity_topology_semantic/QSPI_v1.0.md` §3 (the WIB).

| v4 / QSPI source | lesson taken | disposition |
|---|---|---|
| `field_card.py` docstring | "A VIEW, not data. It reads the library. It does not modify it. It produces a string. The string is not stored in the library." | **carried as law** (constraint 2) |
| `render_field_card` assembler | ordered sections; **optional sections omitted when empty**; **GAPS always present** | **carried** |
| `_render_gaps` | blindness rendered as an enumerated section; `"No gaps."` when empty | **carried**; contents re-derived from the WIB difference (`claude/wib-vs-ring3-field-audit-2026-08-26.md`) |
| `_render_situation` | one pipe-delimited header line: level, actions, world, ego | carried **minus its confidence floats** (`{conf:.2f}` = banned epistemology) |
| `_render_objects` | canonical order (cell count ASC, class ASC); role rendered **inline as a property**; header carries counts | **carried** |
| `_render_unknowns` | flat aggregate — count, cells, class ids. Explicitly **no zone grouping**: "zone is not a classification input" | **carried, including the refusal** |
| `_render_causal_map` | causal line carries `observation_count` | **carried** — this is constraint 5's shape, already in v4 |
| `_render_exploration` | unique / repeated states | carried as **counts**; its `efficiency:.1%` dropped |
| `_render_background`, `_render_captain_target`, `_render_plan_status` | exist in code though the docstring says "seven sections" | **NOT carried** — no observed basis hybrid-side. Each becomes a GAPS line, per "an exclusion is a finding". |
| WIB §3 A-G block list | what a bounded LLM brief contains; "No raw grid. No pixel coordinates. No SDK internals. Everything must be frame-derived." | **carried as the firewall on the card's input** |
| WIB §G friction snapshot (goal entropy, mean Fpx/Fobj/Ftopo) | — | **REFUSED** — confidence scalars, banned epistemology. Port the brief, not the ratchet. |
| `python_tool_sandbox.py` `__SEGMENTATION_SOURCE__` + `inspect.getsource` | the in-sandbox source-splice mechanism | **transcribed exactly** — the card ships by the same proven route |

## 2 · Mechanism, as conjuncts (counts and quantifiers only)

`virelai_card()` is a pure function of the `virelai` dict. It holds no state, imports
nothing, touches no ledger, and returns a string.

**A section renders iff its evidence exists.** GAPS renders unconditionally.

| section | renders iff | each line states |
|---|---|---|
| SITUATION | always | world type + the roster it was derived from; level; states walked; moves recorded; resets; current state key |
| OBJECTS | ≥1 sealed role exists | the observation and its count — never a verdict alone |
| UNKNOWNS | threaded worldlines > sealed roles | count of worldlines carrying no sealed role |
| ACTIONS | ≥1 action tried at the current state | per label: tries, board-changes, distinct outcomes; then the untried list |
| EXPLORATION | states > 0 | states walked, moves recorded, revisits, resets |
| CAUSAL MAP | ≥1 lever witnessed | lever → cells changed elsewhere, with witness count |
| GAPS | **always** | one line per named blindness, each naming its mechanism |

**Constraint 5 in force — every role line is an observation plus its falsifier:**

```
EGO   the 4-cell class-14 shape at rows 40-41 x cols 10-11
      observed: UP->(-1,0) over 3 presses; DOWN->(+1,0) over 2 presses
      this is what the record shows moved with which press. It is not a
      guarantee. Falsified if another shape shows the same signature, or if
      this one moves when you press nothing.
```

No line says "is YOU". No line says "never doubt". The reader concludes.

**GAPS enumeration (fixed list, each with its mechanism):**
- terrain unmeasured — no ground or wall labels exist, so no reachability claim is made
- destructibility unmeasured — BIRTH/DEATH verbs are computed and discarded, not retained
- N worldlines carry no sealed role
- N roster actions have never been tried anywhere
- no win has been observed yet in this game *(or: a win was observed at state X; its
  description is not yet computed)*

## 3 · Diff surface (vs ring3)

| file | change |
|---|---|
| `inference/framework/virelai_card.py` | **new** — stdlib-only pure renderer, `render_card(snapshot) -> str`. Citations in the module docstring per R-C. |
| `inference/agent/python_tool_sandbox.py` | `__VIRELAI_CARD_SOURCE__` spliced via `inspect.getsource`, mirroring `__SEGMENTATION_SOURCE__`; `runtime_globals["virelai_card"]` bound in `_refresh_state` |
| `inference/framework/virelai_ledger.py` | snapshot gains **`here`** (current state key), **`untried_here`**, **`level`** — the three observed fields the card needs and cannot derive |
| `inference/agent/prompts.py` | **lockstep deletion**: the four-bullet "What you are handed, and how much to trust it" block (the sealed-read contract explanation) is replaced by one line naming `virelai_card()`. The card now carries that explanation, with evidence. |

## 4 · Pre-registered fixtures — they measure the READER, not the render

Baselines measured from `runs/kaggle-ring3/` on 2026-08-27.

| # | fixture | ring3 baseline | ring4 prediction |
|---|---|---|---|
| F1 | `virelai_card` called at least once | n/a (did not exist) | **≥15 of 25 games** |
| F2 | raw-snapshot fumbling falls: `"not subscriptable"` | **1,666** across 25 games | **falls** |
| F3 | `"is an int, not a"` schema errors | **29** in 16 games | **falls** |
| F4 | rendered system prompt shrinks | `VIRELAI_WORLD_ADDENDUM` **807 w**; all addenda **2,720 w** | **both fall** — the ring's charter |
| F5 | world model sharpens after a card call | — | in ≥1 game the stated world model names a role it had not named before the first call |
| F6 | **negative control** — a game with zero sealed roles | — | card renders SITUATION + EXPLORATION + GAPS **only**, and GAPS states the absences |

**Acceptance criterion, v4's own words (FRICTION-004):** *"Does this change what the solver
does on at least one game?" If not, don't ship it.* A card that renders perfectly and is
never called is FRICTION-004 one layer up.

## 5 · Pre-registered limitations, stated as limitations

1. **The card cannot fix a false seal.** sp80's 80-cell "ego" would still be rendered — but
   as an observation with its bearings and its falsifier, not as "YOU, never doubt". The
   ego conjunct's inability to separate a self from a driven object is **unfixed and owed
   a ruling**; this ring does not touch it.
2. **The digest is unchanged.** `[EGO] sealed: ... is YOU ... BLOCKED, not doubt` still
   fires per-turn. Ring 4 changes only what the *card* renders. Removing the doubt
   prohibition is a second variable and is owed its own ring. The card's falsifier line is
   the lockstep-safe partial remedy, and the mismatch is deliberate and named.
3. **Terrain, reachability and destructibility stay unrenderable** — they are GAPS lines,
   not sections. Destructibility is one small change away (`thread()` discards eight of
   nine verbs) but that changes the *record* and is its own variable.
4. **D2 is not closed.** `snapshot()` remains uncapped. Ring 4 adds **zero** serialization —
   the card renders from the dict already shipped — but it does not bound it.
5. **The card is on demand.** If the model never calls it, this ring does nothing. That is
   F1, and it is the honest risk.

## 6 · Failure shapes filed in advance

- The model calls `virelai_card()` every turn and burns tokens on a dossier that changed by
  one line. Mitigation: none in code — the prompt names it as a *dossier to consult when
  the picture is unclear*, not a per-turn read. If it happens, F2/F3 will improve while
  token-per-decided-action worsens; that is the signature to look for.
- The card's GAPS section reads as a to-do list and the model tries to *close* the gaps
  rather than route around them — spending presses on terrain it cannot measure. Signature:
  actions rise on games with many GAPS lines.
- A false ego seal, now rendered with evidence, is *more* persuasive rather than less
  because it looks measured. This is the inverse of the intended effect and it is the one
  I would most want the transcripts checked for.
