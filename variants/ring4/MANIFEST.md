# Variant: ring4 — the field card

**Created:** 2026-08-27 · **From:** `variants/ring3` assembled tree (3 files copied,
byte-verified before edit) · **Design:** `DESIGN.md` (harvest table, conjuncts, fixtures)
**Ruling basis:** Director 2026-08-26 (the card is the reading surface the library owes
the model) · Director 2026-08-27 (**the card's input is observed, not concluded**) ·
STRATEGY.md §6 constraints 1–5 · R-C · R-E / FRICTION-004.

## The one variable (vs ring3)

A **field card** — `virelai_card()` — rendered **inside the sandbox** from the `virelai`
snapshot the harness already ships, plus the three observed snapshot fields it needs and
the prompt prose it earns the right to delete.

## Diff surface

| file | change |
|---|---|
| `inference/framework/virelai_card.py` | **new**, 236 lines, **zero imports** (sandbox-safe). `render_card(snapshot) -> str`. Sections SITUATION / OBJECTS / UNKNOWNS / ACTIONS AT THIS STATE / EXPLORATION / CAUSAL MAP / **GAPS always**. Shape transcribed from `virelai_v4/library/field_card.py` with citations in the docstring; its confidence floats, efficiency percentage and three unobservable sections refused. |
| `inference/agent/python_tool_sandbox.py` | `__VIRELAI_CARD_SOURCE__` spliced by `inspect.getsource`, mirroring `__SEGMENTATION_SOURCE__`; `runtime_globals["virelai_card"]` bound in `_refresh_state` |
| `inference/framework/virelai_ledger.py` | snapshot gains `here`, `level`, `untried_here`; ego entries gain `moves_seen` — four observed fields, no new computation |
| `inference/agent/prompts.py` | **lockstep deletion**: RECORD FACTS / [FRONTIER] / SEALED READS bullets removed — the card now carries them *with their evidence*. THE MENU **kept** (the card does not replace menu pruning). One pointer line added. |

**Prompt: 807 → 668 words on `VIRELAI_WORLD_ADDENDUM`; 2,720 → 2,626 across all addenda
(−94).** Ring 4 is the first ring whose health metric FALLS, as chartered.

## Laws honored

- **Constraint 1** — the card renders in-sandbox from the already-shipped dict. **Zero**
  bytes added to any payload. Unread means unrendered.
- **Constraint 2** — a view may not compute. The card is a pure function of a dict; it
  cannot reach the ledger, and it holds no state.
- **Constraint 3** — GAPS is typed silence, not a backlog. Untried actions are FRONTIER;
  gaps name the *mechanism* of each blindness. RESET is excluded from "never tried" (G11:
  a back-edge is never recorded as an action).
- **Constraint 4** — the fixtures measure the reader, not the render (DESIGN §4).
- **Constraint 5** — **observed, not concluded.** Every sealed read renders the
  observation, its count, and its falsifier. Battery asserts: no "is YOU", no doubt
  prohibition, no confidence floats, no percentages, ≥4 falsifiers.
- Firewall — the card reads only hashes, class ids, bboxes and counts. No world name,
  colour or content crosses out.

## Verification at creation (device, 2026-08-27)

`py_compile` ×4. **Unit battery: 36 checks, all PASS** — positives (each section renders
its observation and count), constraint-5 assertions, **negative controls** (empty
snapshot → no OBJECTS but GAPS still present; no seals → OBJECTS and CAUSAL MAP omitted
and GAPS names each absence; CLICK world → "no ego expected", never "no ego sealed"), and
splice integrity (bootstrap carries `render_card` source, no unreplaced placeholder,
segmentation splice intact).

**Two defects the negative controls caught and killed:** the LEVER line shipped with no
falsifier (now: *one witness cannot separate a lever from a coincidence — click it again*),
and RESET was being reported as a never-tried roster action.

**End-to-end behaviour NOT_MEASURED until the validation run.**

## Declared deviations (METHODOLOGY §7 — declared is a finding, discovered is a defect)

1. **The bundle was assembled by hand, not by `make kaggle-duck`.** The device VM's
   session disk is **100 % full** (9.8 G, 0 available — the 13 G ARC_3_BETA mount) and
   carries no venv, so Tufa's pipeline could not run. The bundle was built by copying
   ring3's verified bundle, overlaying the four ring4 files, and relabelling. **It was
   then verified by CONTENT** per §3.6: overlay byte-identical to the variant, implants
   present, this ring's and all prior rings' deletions absent, kernel metadata correct,
   unique dataset slug, preamble config byte-identical to ring3 after label
   normalisation, file count verified (77 = 77, −PUSH +card).
2. **`benchmark_initial.pkl` and `deploy_target.pkl` were byte-patched, not regenerated**
   — they cannot be unpickled outside a Kaggle session (`arcengine`). `ring3`→`ring4` is
   equal-length, so pickle structure is untouched; both files are byte-for-byte the same
   size and carry zero residual `ring3` references. The executed code comes from the
   dataset's `src/`, not the pickle.
3. **`__pycache__` was found INSIDE ring3's shipped bundle** (3 directories) and in one
   earlier ring's. Stripped from ring4 and counted. **This is the freeze-defect lesson
   recurring in shipped bundles and it is owed a check on every prior ring.**

## Not done

The ego seal's discriminator (self vs driven object) — unfixed, owed a ruling. The
digest's `is YOU / never doubt` wording — a second variable, its own ring. Verb retention
in `thread()` — changes the record, its own variable. Terrain, reachability,
destructibility — GAPS lines, not sections. `snapshot()` remains uncapped (D2).
