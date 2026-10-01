"""Receipt-bound runtime feasibility for sequential Kaggle checkpoints."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Sequence


@dataclass(frozen=True)
class CheckpointRuntimePlan:
    deployment_runtime_seconds: int
    non_benchmark_reserve_seconds: int
    benchmark_soft_budget_seconds: int
    world_count: int
    passes: int
    concurrency: int
    execution_waves: int
    requested_runtime_seconds_per_world: int
    required_benchmark_seconds: int
    max_feasible_runtime_seconds_per_world: int
    feasible: bool

    def receipt_fields(self) -> dict[str, int | bool]:
        return asdict(self)

    def require_feasible(self) -> "CheckpointRuntimePlan":
        if self.feasible:
            return self
        raise ValueError(
            "Impossible checkpoint runtime allocation: "
            f"{self.execution_waves} execution waves × "
            f"{self.requested_runtime_seconds_per_world}s requested per world requires "
            f"{self.required_benchmark_seconds}s, but the deployment leaves only "
            f"{self.benchmark_soft_budget_seconds}s after its non-benchmark reserve. "
            "Split the worlds, increase concurrency, or lower the per-world allowance."
        )


def plan_checkpoint_runtime(
    *,
    worlds: Sequence[str],
    passes: int,
    concurrency: int,
    requested_runtime_seconds_per_world: int,
    deployment_runtime_seconds: int,
    non_benchmark_reserve_seconds: int,
) -> CheckpointRuntimePlan:
    """Compute the schedule that the notebook must bind into its receipt."""
    world_count = len(tuple(worlds))
    passes = int(passes)
    concurrency = int(concurrency)
    requested = int(requested_runtime_seconds_per_world)
    deployment = int(deployment_runtime_seconds)
    reserve = int(non_benchmark_reserve_seconds)
    if world_count <= 0 or passes <= 0 or concurrency <= 0:
        raise ValueError("worlds, passes, and concurrency must all be positive")
    if requested <= 0 or deployment <= 0 or reserve < 0:
        raise ValueError("runtime values must be positive and reserve cannot be negative")
    benchmark_budget = deployment - reserve
    if benchmark_budget <= 0:
        raise ValueError("non-benchmark reserve consumes the full deployment runtime")
    waves = ceil(world_count / concurrency) * passes
    required = waves * requested
    feasible_per_world = benchmark_budget // waves
    return CheckpointRuntimePlan(
        deployment_runtime_seconds=deployment,
        non_benchmark_reserve_seconds=reserve,
        benchmark_soft_budget_seconds=benchmark_budget,
        world_count=world_count,
        passes=passes,
        concurrency=concurrency,
        execution_waves=waves,
        requested_runtime_seconds_per_world=requested,
        required_benchmark_seconds=required,
        max_feasible_runtime_seconds_per_world=feasible_per_world,
        feasible=required <= benchmark_budget,
    )


def bind_benchmark_deadline(
    *,
    notebook_start_epoch: float,
    benchmark_start_epoch: float,
    requested_benchmark_seconds: int,
    deployment_runtime_seconds: int,
    minimum_tail_seconds: int = 120,
) -> float:
    """Give the benchmark its promised time or fail before starting it.

    Setup time is measured rather than silently deducted from the model's
    allowance.  A checkpoint that starts too late is rejected instead of
    producing a misleading shortened behavioral run.
    """
    notebook_start = float(notebook_start_epoch)
    benchmark_start = float(benchmark_start_epoch)
    requested = int(requested_benchmark_seconds)
    deployment = int(deployment_runtime_seconds)
    tail = int(minimum_tail_seconds)
    if benchmark_start < notebook_start:
        raise ValueError("benchmark start cannot precede notebook start")
    if requested <= 0 or deployment <= 0 or tail < 0:
        raise ValueError("runtime values must be positive and tail cannot be negative")
    deadline = benchmark_start + requested
    latest_safe_deadline = notebook_start + deployment - tail
    if deadline > latest_safe_deadline:
        setup_elapsed = benchmark_start - notebook_start
        available = max(0.0, latest_safe_deadline - benchmark_start)
        raise ValueError(
            "Measured setup leaves insufficient benchmark time: "
            f"setup used {setup_elapsed:.1f}s and only {available:.1f}s remain, "
            f"but the checkpoint promises {requested}s plus a {tail}s teardown tail."
        )
    return deadline
