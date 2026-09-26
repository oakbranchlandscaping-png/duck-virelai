import pytest

from inference.framework.checkpoint_runtime import (
    bind_benchmark_deadline,
    plan_checkpoint_runtime,
)


def test_rejects_the_impossible_completed_v2_three_world_schedule():
    plan = plan_checkpoint_runtime(
        worlds=("vc33", "ft09", "ls20"),
        passes=1,
        concurrency=1,
        requested_runtime_seconds_per_world=1800,
        deployment_runtime_seconds=2100,
        non_benchmark_reserve_seconds=600,
    )
    assert plan.feasible is False
    assert plan.execution_waves == 3
    assert plan.required_benchmark_seconds == 5400
    assert plan.benchmark_soft_budget_seconds == 1500
    assert plan.max_feasible_runtime_seconds_per_world == 500
    with pytest.raises(ValueError, match="Impossible checkpoint runtime allocation"):
        plan.require_feasible()


def test_single_world_checkpoint_binds_a_realizable_soft_budget():
    plan = plan_checkpoint_runtime(
        worlds=("ls20",),
        passes=1,
        concurrency=1,
        requested_runtime_seconds_per_world=1200,
        deployment_runtime_seconds=2100,
        non_benchmark_reserve_seconds=600,
    ).require_feasible()
    assert plan.feasible is True
    assert plan.execution_waves == 1
    assert plan.max_feasible_runtime_seconds_per_world == 1500
    receipt = plan.receipt_fields()
    assert receipt["benchmark_soft_budget_seconds"] == 1500
    assert receipt["required_benchmark_seconds"] == 1200


def test_benchmark_deadline_starts_when_solver_starts_not_when_notebook_starts():
    deadline = bind_benchmark_deadline(
        notebook_start_epoch=1000.0,
        benchmark_start_epoch=1562.6,
        requested_benchmark_seconds=1200,
        deployment_runtime_seconds=2100,
        minimum_tail_seconds=120,
    )
    assert deadline == pytest.approx(2762.6)
    assert deadline - 1562.6 == pytest.approx(1200.0)


def test_benchmark_deadline_rejects_setup_that_consumed_promised_allowance():
    with pytest.raises(ValueError, match="Measured setup leaves insufficient"):
        bind_benchmark_deadline(
            notebook_start_epoch=1000.0,
            benchmark_start_epoch=1900.0,
            requested_benchmark_seconds=1200,
            deployment_runtime_seconds=2100,
            minimum_tail_seconds=120,
        )
