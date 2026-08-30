"""
virelai_v4/library/plan_construction.py — Plan construction helpers (WO-CAMPAIGN2-02).

Factory functions that build plan instances from current context state.
Separated from `library/plan.py` to keep that file at its WO-01-closure
NBLNC count (476, comfortably Green); plan_construction.py grows
independently as more plan types' construction logic lands.

WO-02 SCOPE

Only `construct_nav_plan` ships in WO-02. It returns a NavPlan with
EMPTY actions / expected_positions — the BFS pathfinding that populates
those fields ships with WO-03. Per WO Step 3a:

    > A NavPlan with empty actions is_complete() returns True immediately
    > (cursor 0 >= len 0). This is intentional for WO-02: the dispatch
    > layer can be tested by constructing such a plan, observing it tear
    > down on the next frame, and confirming reactive mode resumes.

Construction site (which reactive handler decides "I need a plan now"?)
is deferred to WO-03 alongside BFS path computation.

WO-02 ships the helper but does NOT call it from any reactive handler.
That means in WO-02's canary, ``current_plan`` stays None throughout —
the dispatch layer is exercised by tests, not live game runs. The
canary verifies non-regression. Live exercise is WO-03's canary
criterion.

CYCLEPROBEPLAN AND TRAVERSALPLAN CONSTRUCTION HELPERS

Out of WO-02 scope. CycleProbePlan construction (when discovery decides
to characterize a lever) ships with Campaign 3. TraversalPlan
construction (when a FINITE_SEARCH world is identified) also ships with
Campaign 3.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Tuple

from virelai_v4.library.plan import NavPlan

if TYPE_CHECKING:
    from virelai_v4.context import VirelaiContext


def construct_nav_plan(
    ctx: "VirelaiContext",
    target: Tuple[int, int],
    source_hypothesis_id: str,
) -> NavPlan:
    """Construct a NavPlan to navigate ego to ``target``.

    WO-CAMPAIGN2-02 PROVISIONAL IMPLEMENTATION

    Returns a NavPlan with empty ``actions`` and ``expected_positions``
    lists. The BFS pathfinding that populates those fields ships with
    WO-03.

    A NavPlan with empty actions has ``is_complete()`` return True
    immediately (cursor 0 >= len 0). This is intentional — the WO-02
    dispatch layer tears such a plan down on the next frame and resumes
    reactive mode.

    Provisional fields populated:
      - source_hypothesis_id: traceability to the construction-site
        decision that justified this plan
      - compiled_at_step:     ctx.step_count (used for stale-plan
        detection in future WOs)
      - target:               the navigation target coordinate
      - actions:              [] (WO-03 populates via BFS)
      - expected_positions:   [] (WO-03 populates per BFS step)
      - cursor:               0 (PlanBase default)
      - stuck_counter:        0
      - aborted:              False

    Args:
        ctx: VirelaiContext — read for ``step_count`` to populate
            ``compiled_at_step``. Not mutated.
        target: (row, col) coordinate the plan will navigate to. Stored
            on the plan; the BFS in WO-03 consumes this when computing
            the path.
        source_hypothesis_id: traceability string. Examples:
            ``"lever_candidate_R12"`` (V4-internal hypothesis IDs are
            free-form strings; concrete naming convention emerges with
            the construction-site WO).

    Returns:
        NavPlan with the provisional empty-actions stub.
    """
    return NavPlan(
        source_hypothesis_id=source_hypothesis_id,
        compiled_at_step=ctx.step_count,
        target=target,
        actions=[],
        expected_positions=[],
        stuck_counter=0,
        aborted=False,
    )
