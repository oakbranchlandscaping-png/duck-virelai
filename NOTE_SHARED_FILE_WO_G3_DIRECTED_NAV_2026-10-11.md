# Shared-file note, 2026-10-11 (WO-G3-DIRECTED, NAV slice, piece 1: the HYBRID CLICK pass)

**Filed by:** Claude, Alpha build seat, **before any shared edit** (ruling 9).
**Authority:**
- Sol's ruling on CLICK revision 2: HYBRID may offer at most one choice in CLICK and one in NAV. Repair the HYBRID CLICK pass first; enable the NAV handoff only once NAV selection and pursuit are built.
- Sol's instruction for this piece: the repair only, with `db8a657` as the fail-first baseline.

**Implementation owner:** Claude (D1). There are no concurrent edits to `controller_executor.py`.

**Base:** `db8a657` (`ring9-unified`, local). It holds the CLICK slice, accepted, with a Mac floor of 755 passed, 1 skipped.

| File | Function | Change |
|---|---|---|
| `inference/framework/controller_executor.py` | `next_owned_step` (`:119-141`) | Passes `g3_choice_handoff` to `_nav_step` too. Before this, only the CLICK world received it. |
| same | `_nav_step` (`:185-300`) | Gains the keyword `g3_choice_handoff=False`. In the G3 branch, a `RANKED_CLICK_TARGET` capability goes to a new extracted helper instead of being returned to Duck. Every other branch is unchanged. |
| same | new `_g3_click_step(machine, capability, g3_choice_handoff)` | Applies the CLICK handoff (`_g3_choice_due`, at most once per phase per level), then serves the capability's single bound click through `_bound_action`, owned by the controller. It is the same ownership `_ordinary_step` gives a CLICK world. |

**Unchanged:**
- **The NAV handoff stays off.** `g3_selection.admission_candidates` marks NAV rows unselectable, so `choice_handoff_due` is false in NAV. The NAV pursuit branch (`PILOT_TO_LEVER_CONTACT`, `CONFIRM_LEVER_WITNESS`) never calls `_g3_choice_due`.
- Untouched files: `virelai_gates.py`, `g3_selection.py`, `library_agenda.py`, `lever_lifecycle.py` and the lifecycle table, `planned_nav_step`, reachability, terrain, and every G4 gate.
- The no-choice golden traces. They replay through `record_like_live`, not through `next_owned_step`.

**Not shared** (mine): the new test file `tests/test_g3_hybrid_click_pass.py`.

## Amendment 1, 2026-10-11 (filed after the ratchet edit, in the same working session; not before it)

The repair grew `_nav_step` from 111 to 113 NCNB lines. To compensate, a new `_bound_step(machine, capability)` takes the bound-action tail that `_nav_step`'s G1 branch and its G2 non-pilot branch both repeated, **moved unchanged**. `_g3_click_step` calls it too. `_ordinary_step` is left as it was.
