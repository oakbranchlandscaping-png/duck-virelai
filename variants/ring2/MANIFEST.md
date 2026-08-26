# Variant: ring2 — the COUNTER: seal, mask, teach

**Created:** 2026-08-26 · **From:** `variants/ring11` (minus venv/scratch; 87→ files) ·
**Design:** `DESIGN.md` (this dir) — step-zero v4 harvest table, the four seal conjuncts,
the world grain, pre-registered limitation and fixtures. **Ruling basis:** Memo №3 §5
Ring-2 row (lockstep deletions) · R-H1a shapes (iii) counter-witness, (v) world grain ·
port-source posture (Director 2026-08-25) · single-run feedback cadence (2026-08-26).

## The one variable (vs ring11)

The counter subsystem: behavioral COUNTER seal over churn regions → counter-masked
world-grain node identity → `world_changed` → sealed-read teaching → Ring-2 prose
deletions. Everything else byte-inherited from ring11.

## Diff surface

| file | change |
|---|---|
| `virelai_ledger.py` | **v3 rewrite**: append-only raw record (grids stored per node — derived-but-retained; per-edge changed-cell sets + click coords); the 4-conjunct COUNTER seal (every-press ∀, ≥2 labels, stable magnitude, not-acted-member click witness REQUIRED when located clicks exist; one held press kills; recomputed each turn); masked world keys + world-map fold (recompute-on-mask-change, cached); RESET root on world view; overlap-based seal announcements (a sweeping counter grows silently); digest reads world map; snapshot gains `counter` block |
| `solver.py` | ledger call passes grids/levels/click-coord; payload gains `world_changed`; batch account reports last WORLD change |
| `tool_agent.py` | `world_changed` in compact action result (falls back to board_changed when absent) |
| `prompts.py` | Ring-2 lockstep DELETIONS: timer-bar description, "DON'T DO THIS!" paragraph, after-every-action HUD verification ritual, background-hypothesis coaching, countdown-bar clause. IMPLANTS: [COUNTER] sealed-read contract line, `world_changed` docs, `virelai.counter` docs, axiom-5 grounding note ("every state on the map is PROVEN not the win; the win lives in the untried") |

Prompt length: 2501 → 2464 words — the Memo №3 health metric holds (shorter as smarter).

## Verification at creation (cloud, 2026-08-26)

py_compile ×4 clean; solver imports in venv. Unit battery PASS: synthetic counter world
seals (1 cell/press, 4 labels, click witness), blocked press reads world_changed=False
under the seal, world map converges (5 edges → 2 world-states where raw minted 6),
held-press unseals loudly, blocked-ego world never seals, clicked-on strip never seals
(witness enforced), RESET root on world keys, cached read ~0ms/turn. Announcement noise:
1 seal + 1 transient (the pre-registered 2-press ego transient, self-corrected — by
design, filed). System prompt: all implants present; ring1 AND ring2 deletion targets
verified absent. **End-to-end NOT_MEASURED until the single validation run** (per the
one-run feedback cadence; run only on the Director's go). Fixtures pre-registered in
DESIGN.md: counter worlds (ls20, tn36-class) show seals + revisit recognition + falling
waste; still-board worlds must never seal.
