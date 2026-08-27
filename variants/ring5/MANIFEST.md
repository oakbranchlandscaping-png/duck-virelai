# Variant: ring5 — the ego seal, replaced

**Created:** 2026-08-27 · **From:** `variants/ring4` assembled tree · **Design:** `DESIGN.md`
**Ruling basis:** Director 2026-08-27 — Ring 5 fixes the ego; and *"an ego is something the
agent has DIRECT control over; a lever is something the agent's ego can move."*
**Adopted, named, non-precedential** (instrument ruling): `virelai_v4/weave/ego_field.py`.

## The one variable

The ego seal's **evidence class**. Own-stream bearing covariance → the field read.

## Diff surface

| file | change |
|---|---|
| `virelai_weave.py` | `_anchor` helper; `edge_label` recorded per edge; the own-stream test becomes **candidacy** and stops announcing; new `_fp_snapshots`, `_field`, `_moved_edges`, `field_seal`, `ego_candidates`, `egos` (verdict), `settle` |
| `virelai_ledger.py` | `weave.settle()` after threading; snapshot gains `ego_candidates` |
| `virelai_card.py` | GAPS reports refused candidates — *"Something the ego pushes is a lever, not a self."* |

## The four conjuncts

1. **A crossing** — cells gained were cells a persisting partner lost; nothing from nowhere.
2. **The exchange depends on WHICH button** — two labels, different cells from that partner.
3. **This one is displaced and the partner is not** — anchors over the footprint series, not
   the MOVE verb. More than one anchor, **no minimum count**.
4. **Direct control** — refuse any candidate whose anchor-change edges are a PROPER SUBSET
   of another worldline's. An ego moves alone; a driven object moves only when its driver
   does. Two tones of one body have EQUAL sets and both survive.

## Laws honored

No threshold, no ratio, no confidence number anywhere. Both sets exposed — the wide
candidate set (`nav_target`'s *"deliberately the wider set"*) and the verdict set — and the
card names the gap between them. The announcement is **observed, not concluded**: it states
the exchange, the buttons, the displacement asymmetry and its falsifier. No "is YOU", no
doubt prohibition.

## Verification at creation

`py_compile` ×3. Battery **10 tests, all PASS**, run under a dependency-free runner
(no pytest on the device's Python 3.14; the file is pytest-shaped for Kaggle's 3.10 —
declared, and the authoritative run is Kaggle's).

**Negative controls:** single observed action refuses · both partners displaced → both
refuse · stationary refuses · gains-from-nowhere refuses · **a driven box refuses while its
driver still seals** · two tones of one body both seal · a candidate absent from the verdict.

**A fixture defect the controls caught:** the first "both displaced" ground was not
displaced at all — `_anchor` is `(min row, min col)`, a bounding-box corner, and a ground
keeping any cell in row 0 and any in col 0 holds its anchor however much it churns. The
fixture is now derived from anchor arithmetic and asserts `disp[1] and disp[2]` before
testing the verdict.

**End-to-end NOT_MEASURED until the validation run.**

## Not done

Typing the refused mover as a LEVER — that is collision-as-attribution, listed as owed in
`STATE_OF_THE_CAMPAIGN_EGO` §5; it lands as an unclassified mover and GAPS says so.
Seal permanence unchanged. Verb retention (destructibility) is its own variable.
