# Variant: ring3 — the frontier made explicit

**Created:** 2026-08-26 · **From:** `variants/ring25` (91 files at copy) · **Design:**
`DESIGN.md` · **Ruling basis:** the Director's grounding note (the win lives in unseen
states — mechanized here) · Rung 3.5 fence (Director's amendment: NO reachability
claims — routes are replays of WALKED edges only, no terrain assumed) · canon 2 §6.2
(LEVER is existential: one witness proves, silence never retracts) · the ring2
motion-coupled-drain finding (mechanized as the [DRAIN] seal) · one-run cadence.

## The one variable (vs ring25)

The frontier stack: [FRONTIER] navigator (untried census + shortest KNOWN route by BFS
over recorded edges, advisory, loud truncation), the [DRAIN] ego-coupled seal, and
[LEVER] click-attribution (CLICK-scope; NAV lever attribution named for a later ring,
not attempted).

## Diff surface

| file | change |
|---|---|
| `virelai_ledger.py` | v5: `_frontier_line` (untried = roster−tried per visited state, labeled as roster-derived; BFS route over most-recent observed dests; "frontier exhausted" is stated as a finding); `_evaluate_drains` (≥2 ego-MOVE edges all ticking ∧ ≥2 non-move edges all holding; counter-sealed and ego cells excluded; recomputed; one violation kills); `_lever_witness` (located click on component O + world change elsewhere = ∃-seal; effect summarized); snapshot gains `drains`/`levers`; old untried-here line folded into [FRONTIER] |
| `virelai_weave.py` | Worldline gains footprint trail (`at`) and `moved_at` (edge indices where it MOVEd — recorded from the verb at stitch time, never inferred from the current footprint: past moves happened at past positions, the defect the unit battery caught) |
| `prompts.py` | contract gains [FRONTIER] (record-grade) and [DRAIN]/[LEVER] (sealed reads); `virelai` docs gain drains/levers |

Prompt: 2513 → 2603 words (+90). Health-metric note: growth is again sealed-read
vocabulary for new machinery; no coaching re-entered. The trend (2464→2513→2603) is
now flagged for the directing chamber: contract growth is real even when coaching
shrinks — a compaction pass on the contract block is a named candidate for ring 4.

## Verification at creation (cloud, 2026-08-26)

py_compile ×3; solver imports. Battery PASS: frontier-here and frontier-route lines
(BFS over walked edges); DRAIN seals on the ls20-sim (4 move edges ticked / 2 blocked
held) and its two negative controls — counter-sealed regions never drain-seal; CLICK
worlds mint no ego and no drain; LEVER seals on one located witness, no-effect clicks
mint nothing. One defect found AND fixed in-battery: ego-motion edges were initially
classified against the CURRENT footprint (wrong altitude for a per-edge fact) —
replaced by `moved_at` recorded from the verb at stitch time. **Live behavior
NOT_MEASURED until the single validation run.** Fixtures in DESIGN.md; the number this
ring targets: cn04's 526 wandering actions.
