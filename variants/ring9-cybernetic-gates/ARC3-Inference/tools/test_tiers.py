#!/usr/bin/env python3
"""Run a test tier from the checked-in manifest (WO-1, test-runtime infrastructure).

Author: Claude (Alpha build seat), 2026-10-13. Usage, from ARC3-Inference:

    python tools/test_tiers.py T0 g3-directed            # change-focused: fail-first tests and nearest guards
    python tools/test_tiers.py T1 g3-directed --jobs 4   # the slice floor
    python tools/test_tiers.py T2 --jobs 4               # the acceptance floor (the whole suite)
    python tools/test_tiers.py T2 --jobs 1               # the same floor in one pytest process
    python tools/test_tiers.py --check                   # every manifest entry still names a test
    python tools/test_tiers.py T1 g3-directed --results out.json   # every test's outcome, to compare two runs
    python tools/test_tiers.py --write-snapshot          # an intentional T2 snapshot update (after adding a test)

The manifest is ``tests/tiers/test_tiers.toml``. Every entry is checked by collection before anything runs: a
named test or file that no longer collects fails the run, and so does duplicate coverage (a selector listed twice,
or two selectors that cover the same collected test). The T2 snapshot is exact: a duplicated row, a snapshot test
that no longer collects, and a collected test missing from the snapshot all fail (revision 2, Sol's ruling). ``--jobs N`` runs N independent pytest
processes over whole files (each with its own ``--basetemp`` and junit report), then requires exactly one
result for every collected test. ``--timing`` lists the slowest tests. Only pytest's built-in junit writer is
used: no plugins, no network. The exit status is pytest's: the single process's, or the first non-zero shard's;
1 when the shard results do not account for the collection, 4 when the manifest is wrong, 2 for a usage error.
Workers run in their own sessions inside a cleanup boundary: on SIGINT, SIGTERM or an internal error the runner
terminates every worker still running, waits a bounded grace period, kills and reaps the rest, then removes its
scratch folder; an interrupted run returns 128 + the signal number and publishes no result map.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import tempfile
import time
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "tiers" / "test_tiers.toml"
MISSING_TEST = 4  # pytest's own "usage error" status, which it also returns for a node id that is not found
GRACE_SECONDS = 5.0  # how long terminated workers get before they are killed


class ManifestError(RuntimeError):
    """The manifest names a test, file or node that does not collect."""


def load_manifest(path: Path = MANIFEST) -> dict:
    manifest = tomllib.loads(path.read_text())
    if manifest.get("schema") != "virelai-test-tiers-v1":
        raise ManifestError(f"{path}: unknown schema {manifest.get('schema')!r}")
    return manifest


def _python() -> str:
    return sys.executable


def _env() -> dict[str, str]:
    env = dict(os.environ)
    paths = [".", "tests", str(ROOT.parent / "tufa-arc-agi-framework" / "src")]
    if env.get("PYTHONPATH"):
        paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def _pytest(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    command = [_python(), "-m", "pytest", "-p", "no:cacheprovider", "-W", "ignore", *args]
    return subprocess.run(command, cwd=ROOT, env=_env(), text=True, **kwargs)


def _covers(target: str, node: str) -> bool:
    if "::" in target:
        return node == target or node.startswith(target + "::") or node.startswith(target + "[")
    base = target.rstrip("/")
    return node.startswith(base + "::") or node.startswith(base + "/")


def collect(targets: list[str], ignore: list[str] = (), *, label: str = "") -> list[str]:
    """The node ids pytest collects for ``targets``; ``ManifestError`` if any target collects nothing."""
    done = _pytest(["--collect-only", "-q", *[f"--ignore={item}" for item in ignore], *targets], capture_output=True)
    nodes = [line.strip() for line in done.stdout.splitlines() if "::" in line and not line.startswith(" ")]
    if done.returncode != 0:
        tail = "\n".join((done.stdout + done.stderr).strip().splitlines()[-8:])
        raise ManifestError(f"collection failed (pytest status {done.returncode}):\n{tail}")
    for target in targets:
        if not any(_covers(target, node) for node in nodes):
            raise ManifestError(f"{label + ': ' if label else ''}the manifest names {target!r}, which collects no test")
    return nodes


def check_coverage(label: str, selectors: list[str], nodes: list[str]) -> None:
    """Every collected test is covered by exactly one selector, and no selector is listed twice."""
    repeated = sorted({selector for selector in selectors if selectors.count(selector) > 1})
    if repeated:
        raise ManifestError("; ".join(f"{label}: the selector {selector!r} is listed {selectors.count(selector)} times"
                                      for selector in repeated))
    overlaps = []
    for node in nodes:
        covering = [selector for selector in selectors if _covers(selector, node)]
        if len(covering) > 1:
            overlaps.append(f"{node} is covered by {len(covering)} selectors: {covering!r}")
    if overlaps:
        raise ManifestError(f"{label}: duplicate coverage: " + "; ".join(overlaps[:10])
                            + (f" (and {len(overlaps) - 10} more)" if len(overlaps) > 10 else ""))


def tier_targets(manifest: dict, tier: str, name: str | None) -> tuple[list[str], list[str]]:
    """(targets, ignores) for a tier; T0 and T1 name a set, T2 is the whole suite less its held exclusions."""
    if tier == "T2":
        spec = manifest["T2"]
        return list(spec["paths"]), list(spec.get("exclude", []))
    sets = manifest.get(tier, {})
    if name not in sets:
        raise ManifestError(f"{tier} has no set {name!r}; it has {sorted(sets)}")
    return list(sets[name]["tests"]), []


def check_t2_snapshot(manifest: dict, nodes: list[str]) -> None:
    """The checked-in T2 snapshot is exactly the collection: no duplicated row, no snapshot test that no longer
    collects, and no collected test missing from it (a new test needs an intentional ``--write-snapshot``)."""
    snapshot = ROOT / manifest["T2"]["snapshot"]
    rows = [line.strip() for line in snapshot.read_text().splitlines() if line.strip()]
    problems = []
    repeated = sorted({row for row in rows if rows.count(row) > 1})
    if repeated:
        problems.append("rows listed more than once: " + ", ".join(f"{row} ({rows.count(row)} times)" for row in repeated[:10]))
    gone = sorted(set(rows) - set(nodes))
    if gone:
        problems.append(f"{len(gone)} snapshot test(s) no longer collect: {gone[:10]}")
    new = sorted(set(nodes) - set(rows))
    if new:
        problems.append(f"{len(new)} collected test(s) are not in the snapshot: {new[:10]}")
    if problems:
        raise ManifestError(f"T2 ({snapshot.name}): " + "; ".join(problems))


def write_snapshot(manifest: dict) -> int:
    """The intentional T2 snapshot update: the current collection, one node id per line."""
    targets, ignores = tier_targets(manifest, "T2", None)
    nodes = collect(targets, ignores)
    (ROOT / manifest["T2"]["snapshot"]).write_text("\n".join(nodes) + "\n")
    print(f"[tiers] T2 snapshot written: {len(nodes)} tests")
    return 0


def _junit_key(nodeid: str) -> tuple[str, str]:
    parts = nodeid.split("::")
    module = parts[0][:-3].replace("/", ".") if parts[0].endswith(".py") else parts[0]
    return ".".join([module, *parts[1:-1]]), parts[-1]


def _junit_results(path: Path) -> dict[tuple[str, str], tuple[str, float]]:
    results: dict[tuple[str, str], tuple[str, float]] = {}
    if not path.exists():
        return results
    for case in ET.parse(path).getroot().iter("testcase"):
        key = (case.get("classname", ""), case.get("name", ""))
        kinds = {child.tag for child in case}
        outcome = ("failed" if "failure" in kinds else "error" if "error" in kinds
                   else "skipped" if "skipped" in kinds else "passed")
        if key in results and results[key][0] != "passed":
            continue  # a teardown error is reported as a second testcase; keep the worst
        results[key] = (outcome, float(case.get("time") or 0.0))
    return results


def _shards(nodes: list[str], jobs: int, manifest: dict) -> list[list[str]]:
    """Whole files (their collected node ids), files sharing expensive checkpoints kept together, balanced by
    measured seconds. The weights and affinities change only speed, never which tests run."""
    weights = json.loads((ROOT / manifest["weights"]).read_text())
    files: dict[str, list[str]] = {}
    for node in nodes:
        files.setdefault(node.split("::")[0], []).append(node)
    affinity = {member: group for group, members in manifest.get("affinity", {}).items() for member in members}
    groups: dict[str, list[str]] = {}
    for path in files:
        groups.setdefault(affinity.get(path, path), []).append(path)
    cost = {group: sum(weights.get(path, 5.0) for path in members) for group, members in groups.items()}
    shards: list[list[str]] = [[] for _ in range(max(1, jobs))]
    load = [0.0] * len(shards)
    for group in sorted(groups, key=lambda g: (-cost[g], g)):
        index = load.index(min(load))
        load[index] += cost[group]
        for path in sorted(groups[group]):
            shards[index].extend(files[path])
    return [shard for shard in shards if shard]


def _launch(index: int, args: list[str], scratch: Path) -> tuple[subprocess.Popen, Path, Path]:
    junit, log = scratch / f"shard{index}.xml", scratch / f"shard{index}.log"
    command = [_python(), "-m", "pytest", "-p", "no:cacheprovider", "-W", "ignore", "-q",
               f"--junitxml={junit}", f"--basetemp={scratch / f'tmp{index}'}", *args]
    with log.open("w") as handle:
        process = subprocess.Popen(command, cwd=ROOT, env=_env(), stdout=handle, stderr=subprocess.STDOUT,
                                   start_new_session=True)  # its own process group: the runner alone stops it
    return process, junit, log


class Interrupted(Exception):
    def __init__(self, signum: int) -> None:
        super().__init__(signal.Signals(signum).name)
        self.signum = signum


def _raise_interrupted(signum: int, _frame) -> None:
    raise Interrupted(signum)


def reap(processes: list[subprocess.Popen], grace: float = GRACE_SECONDS) -> None:
    """Terminate every worker still running (its whole process group), wait ``grace`` seconds, then kill and
    reap whatever remains. Safe to call twice; never raises for a worker that has already gone."""
    def signal_group(process: subprocess.Popen, signum: int) -> None:
        try:
            os.killpg(process.pid, signum)
        except (ProcessLookupError, PermissionError):
            pass

    running = [process for process in processes if process.poll() is None]
    for process in running:
        signal_group(process, signal.SIGTERM)
    deadline = time.monotonic() + grace
    for process in running:
        try:
            process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            pass
    for process in processes:
        if process.poll() is None:
            signal_group(process, signal.SIGKILL)
        process.wait()
        signal_group(process, signal.SIGKILL)  # anything the worker itself left behind in its group


def resolve(manifest: dict, tier: str, name: str | None) -> tuple[list[str], list[str], list[str]]:
    """(targets, ignores, collected node ids), with every manifest check applied."""
    targets, ignores = tier_targets(manifest, tier, name)
    label = tier + (f" {name}" if name else "")
    nodes = collect(targets, ignores, label=label)
    if tier == "T2":
        check_t2_snapshot(manifest, nodes)
    else:
        check_coverage(label, targets, nodes)
    return targets, ignores, nodes


def _publish(results_path: Path, outcomes: dict[str, str]) -> None:
    """Write the result map whole or not at all."""
    partial = results_path.with_name(results_path.name + ".partial")
    partial.write_text(json.dumps(outcomes, indent=0, sort_keys=True) + "\n")
    partial.replace(results_path)


def run(tier: str, name: str | None, *, jobs: int, timing: bool, manifest: dict, results_path: Path | None = None) -> int:
    if jobs < 1:
        raise ValueError(f"jobs must be at least 1, not {jobs}")
    started = time.monotonic()
    label = tier + (f" {name}" if name else "")
    previous = {signum: signal.signal(signum, _raise_interrupted) for signum in (signal.SIGINT, signal.SIGTERM)}
    launched: list[tuple[subprocess.Popen, Path, Path]] = []
    try:
        targets, ignores, nodes = resolve(manifest, tier, name)  # an interrupted collection is killed by run()
        print(f"[tiers] {label}: {len(nodes)} tests collected", flush=True)
        with tempfile.TemporaryDirectory(prefix="test-tiers-") as scratch:
            try:
                scratch_path = Path(scratch)
                if jobs > 1:
                    shard_args = [list(shard) for shard in _shards(nodes, jobs, manifest)]
                else:  # one process over the manifest's own targets: pytest's own status
                    shard_args = [[*[f"--ignore={item}" for item in ignores], *targets]]
                for index, args in enumerate(shard_args):
                    launched.append(_launch(index, args, scratch_path))
                    print(f"[tiers] worker {index}: pid {launched[-1][0].pid}", flush=True)
                statuses = [process.wait() for process, _junit, _log in launched]
                return _report(label, nodes, launched, statuses, started, timing, results_path)
            finally:  # every exit, normal or not: no worker outlives the runner or its scratch folder
                for signum in previous:  # a second signal must not cut the bounded cleanup short
                    signal.signal(signum, signal.SIG_IGN)
                reap([process for process, _junit, _log in launched])
    except Interrupted as interrupt:
        print(f"[tiers] {label}: interrupted by {interrupt}; every worker was stopped and reaped; "
              f"no results were published", file=sys.stderr, flush=True)
        return 128 + interrupt.signum
    finally:
        for signum, handler in previous.items():
            signal.signal(signum, handler)


def _report(label: str, nodes: list[str], launched: list, statuses: list[int], started: float, timing: bool,
            results_path: Path | None) -> int:
    """Account for every collected test once, print the summary, and publish the result map."""
    results: dict[tuple[str, str], tuple[str, float]] = {}
    duplicates = 0
    for _process, junit, _log in launched:
        for key, value in _junit_results(junit).items():
            duplicates += key in results
            results[key] = value
    expected = {_junit_key(node): node for node in nodes}
    unaccounted = sorted(node for key, node in expected.items() if key not in results)
    unexpected = sorted(f"{a}::{b}" for (a, b) in results if (a, b) not in expected)
    counts: dict[str, int] = {}
    for key in expected:
        if key in results:
            counts[results[key][0]] = counts.get(results[key][0], 0) + 1
    if results_path is not None:  # every collected test's outcome, to compare two runs
        _publish(results_path, {node: results.get(key, ("unaccounted", 0.0))[0] for key, node in expected.items()})
    summary = ", ".join(f"{counts[k]} {k}" for k in ("passed", "skipped", "failed", "error") if k in counts)
    processes = f"{len(launched)} process{'es' if len(launched) > 1 else ''}"
    print(f"[tiers] {label}: {summary} in {time.monotonic() - started:.1f}s ({processes})", flush=True)
    if timing:
        slowest = sorted(((results[key][1], node) for key, node in expected.items() if key in results),
                         reverse=True)[:30]
        print("[tiers] slowest tests (setup + call + teardown, seconds):")
        for seconds, node in slowest:
            print(f"  {seconds:8.2f}  {node}")
    failing = [status for status in statuses if status != 0]
    for index, (_process, _junit, log) in enumerate(launched):
        if statuses[index] != 0:
            print(f"[tiers] process {index} exited {statuses[index]}; the end of its log:")
            print("\n".join(log.read_text().splitlines()[-40:]))
    if unaccounted or unexpected or duplicates:
        print(f"[tiers] the results do not account for the collection: {len(unaccounted)} unaccounted "
              f"{unaccounted[:10]}, {len(unexpected)} unexpected {unexpected[:10]}, {duplicates} duplicated")
        return failing[0] if failing else 1
    return failing[0] if failing else 0


def check(manifest: dict) -> int:
    for tier in ("T0", "T1"):
        for name in sorted(manifest.get(tier, {})):
            print(f"[tiers] {tier} {name}: {len(resolve(manifest, tier, name)[2])} tests")
    print(f"[tiers] T2: {len(resolve(manifest, 'T2', None)[2])} tests, exactly the snapshot")
    return 0


def _workers(value: str) -> int:
    jobs = int(value)
    if jobs < 1:
        raise argparse.ArgumentTypeError(f"--jobs must be at least 1, not {jobs}")
    return jobs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("tier", nargs="?", choices=("T0", "T1", "T2"))
    parser.add_argument("name", nargs="?", help="the T0/T1 set (see the manifest)")
    parser.add_argument("--jobs", type=_workers, default=1, help="independent pytest processes over whole files (default 1)")
    parser.add_argument("--timing", action="store_true", help="list the slowest tests")
    parser.add_argument("--check", action="store_true", help="only verify that every manifest entry collects")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--results", type=Path, help="write every collected test's outcome to this JSON file")
    parser.add_argument("--write-snapshot", action="store_true", help="rewrite the T2 snapshot from the collection")
    options = parser.parse_args(argv)
    try:
        manifest = load_manifest(options.manifest)
        if options.check:
            return check(manifest)
        if options.write_snapshot:
            return write_snapshot(manifest)
        if options.tier is None:
            parser.error("name a tier, or pass --check")
        return run(options.tier, options.name, jobs=options.jobs, timing=options.timing, manifest=manifest,
                   results_path=options.results)
    except ManifestError as error:
        print(f"[tiers] manifest error: {error}", file=sys.stderr)
        return MISSING_TEST


if __name__ == "__main__":
    sys.exit(main())
