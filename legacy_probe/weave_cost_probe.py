"""WO-1 Task C — v4 weave per-frame cost probe (read-only over legacy code).

Measures, on a real recording, at prefix lengths n:
  T_full(n)      : the production per-turn path exactly as v4 runs it each turn —
                   coverage_sweep.compute_current_weave_state(prefix_log) —
                   ledger_from_capture (full prefix) + weave_window + re_join + infer_roles.
  T_marginal(n)  : what a prefix-incremental variant would pay for ONE new frame at
                   depth n: reconstruct+scan_grid for the new node only, plus one
                   weave_edge(prev_regions, now_regions) for the new pair.

The full-vs-marginal gap at growing n IS the rebuilt-index curve.
Origin: virelai_v4.weave.{worldline,edge,coverage_sweep}, capture.ledger_build —
transcribed nothing; calls the legacy units as-is (instrument ruling 2026-08-22).
"""
import json
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, "/home/claude/probe")

from virelai_v4.capture.ledger_build import (  # noqa: E402
    load_capture,
    ledger_from_capture,
    load_node_actions_from_log,
)
from virelai_v4.weave.coverage_sweep import compute_current_weave_state  # noqa: E402
from virelai_v4.weave.edge import weave_edge  # noqa: E402


class PrefixLog:
    """Duck-typed prefix view of a FrameRecordLog: .records sliced, reconstruct delegated."""

    def __init__(self, log, n):
        self._log = log
        self._n = n

    @property
    def records(self):
        return self._log.records[: self._n]

    def reconstruct(self, node_index):
        return self._log.reconstruct(node_index)

    def __len__(self):
        return self._n


def time_full(log, n, reps=3):
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter()
        cuts, node_actions, worldlines, verdicts = compute_current_weave_state(PrefixLog(log, n))
        best = min(best, time.perf_counter() - t0)
    return best, len(cuts), len(worldlines)


def time_marginal(log, n, reps=5):
    """Cost of processing only the newest node at depth n: single-node ledger + one edge."""
    # cuts for nodes n-2 and n-1 (prev, now) computed once outside the clock for the
    # edge input; the timed section re-does the NEW node's ledger work + the new edge,
    # which is exactly the marginal work an incremental threader pays.
    prev_cuts = ledger_from_capture(PrefixLog(log, n))
    prev_regions = prev_cuts[-2].regions
    best = float("inf")
    for _ in range(reps):
        t0 = time.perf_counter()
        new_cut = ledger_from_capture(SingleNodeView(log, n - 1))[0]
        edges = weave_edge(prev_regions, new_cut.regions)
        best = min(best, time.perf_counter() - t0)
    return best, len(new_cut.regions), len(edges)


class SingleNodeView:
    """One-record view: the newest node only (ledger loop runs once)."""

    def __init__(self, log, idx):
        self._log = log
        self._idx = idx

    @property
    def records(self):
        return self._log.records[self._idx : self._idx + 1]

    def reconstruct(self, node_index):
        return self._log.reconstruct(node_index)


def main():
    results = []
    for path, depths in [
        ("recordings/vc33-5430563c.virelai.1f7b305c-264c-435d-af5f-7475bc944c01.recording.jsonl", [25, 51]),
        ("recordings/ls20-9607627b.virelai.889276ef-e036-416b-bb38-e5c91238396c.recording.jsonl", [50, 76]),
        ("recordings/vc33-long-head450.recording.jsonl", [50, 100, 200, 300, 400, 450]),
    ]:
        try:
            log = load_capture(path)
        except Exception as exc:
            results.append({"recording": path, "error": f"{type(exc).__name__}: {exc}"})
            continue
        total = len(log)
        for n in depths:
            if n > total:
                continue
            tf, ncuts, nwl = time_full(log, n)
            tm, nreg, nedg = time_marginal(log, n)
            row = {
                "recording": path.split("/")[-1],
                "n_nodes": n,
                "t_full_s": round(tf, 4),
                "t_marginal_s": round(tm, 4),
                "worldlines": nwl,
                "regions_at_tail": nreg,
                "edges_at_tail": nedg,
            }
            results.append(row)
            print(json.dumps(row), flush=True)
    with open("/home/claude/probe/weave_cost_results.json", "w") as fh:
        json.dump(results, fh, indent=2)


if __name__ == "__main__":
    main()
