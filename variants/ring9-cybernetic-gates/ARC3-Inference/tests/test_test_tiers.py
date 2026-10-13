"""The tier runner's contract (WO-1, test-runtime infrastructure; hazard 7 and the runner's honesty).

Author: Claude (Alpha build seat), 2026-10-13. A tier is only trustworthy if it cannot silently shrink: a named
test that no longer collects fails the run, every collected test is accounted for exactly once across parallel
processes, and the runner returns pytest's own failure status.
"""
from __future__ import annotations

import importlib.util
import shutil
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _runner():
    spec = importlib.util.spec_from_file_location("test_tiers_runner", ROOT / "tools" / "test_tiers.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def probe_dir():
    """A throwaway test file under the project root (outside ``tests/``, so no tier collects it by accident)."""
    directory = ROOT / f".tiers-selftest-{uuid.uuid4().hex[:8]}"
    directory.mkdir()
    (directory / "probe_cases.py").write_text(
        "import pytest\n\n"
        "def test_passes():\n    assert True\n\n"
        "def test_fails():\n    assert False, 'a planted failure'\n\n"
        "@pytest.mark.parametrize('n', [1, 2])\n"
        "def test_param(n):\n    assert n in (1, 2)\n"
    )
    try:
        yield directory.relative_to(ROOT).as_posix()
    finally:
        shutil.rmtree(directory)


def _manifest(tests: list[str]) -> dict:
    return {"schema": "virelai-test-tiers-v1", "weights": "tests/tiers/file_weights.json",
            "T0": {"probe": {"tests": tests}}, "T2": {"paths": ["tests"], "snapshot": "tests/tiers/T2_collected.txt"}}


def test_7_a_manifest_naming_a_missing_test_fails(probe_dir):
    runner = _runner()
    missing = f"{probe_dir}/probe_cases.py::test_that_was_removed"
    with pytest.raises(runner.ManifestError):
        runner.run("T0", "probe", jobs=1, timing=False, manifest=_manifest([f"{probe_dir}/probe_cases.py::test_passes",
                                                                           missing]))
    with pytest.raises(runner.ManifestError):
        runner.collect([f"{probe_dir}/no_such_file.py"])


def test_7_the_t2_snapshot_fails_when_one_of_its_tests_no_longer_collects(tmp_path):
    runner = _runner()
    manifest = runner.load_manifest()
    snapshot = (ROOT / manifest["T2"]["snapshot"]).read_text().splitlines()
    gone = snapshot[0] + "_renamed_away"
    fake = tmp_path / "snapshot.txt"
    fake.write_text("\n".join([*snapshot, gone]) + "\n")
    with pytest.raises(runner.ManifestError, match="no longer collect"):  # an absolute snapshot path is used as is
        runner.check_t2_snapshot({**manifest, "T2": {**manifest["T2"], "snapshot": str(fake)}}, snapshot)
    assert runner.check_t2_snapshot(manifest, snapshot) is None  # the real snapshot against itself


def test_the_runner_returns_pytests_failure_status_and_accounts_for_every_test(probe_dir, capsys):
    runner = _runner()
    manifest = _manifest([f"{probe_dir}/probe_cases.py"])
    assert runner.run("T0", "probe", jobs=1, timing=False, manifest=manifest) == 1
    out = capsys.readouterr().out
    assert "4 tests collected" in out and "3 passed, 1 failed" in out


def test_parallel_processes_account_for_every_test_exactly_once(probe_dir, capsys):
    runner = _runner()
    manifest = _manifest([f"{probe_dir}/probe_cases.py::test_passes", f"{probe_dir}/probe_cases.py::test_param"])
    assert runner.run("T0", "probe", jobs=3, timing=True, manifest=manifest) == 0
    out = capsys.readouterr().out
    assert "3 tests collected" in out and "3 passed in" in out and "do not account" not in out
    assert "slowest tests" in out


def test_the_checked_in_manifest_names_only_tests_that_collect():
    runner = _runner()
    manifest = runner.load_manifest()
    for tier in ("T0", "T1"):
        for name in manifest[tier]:
            targets, _ = runner.tier_targets(manifest, tier, name)
            assert runner.collect(targets), (tier, name)


# ---- revision 2 (Sol's ruling, 2026-10-13): no duplicate coverage, an exact T2 snapshot, reaped workers -----

def _manifest_error(runner, manifest: dict, tier: str = "T0", name: str = "probe") -> str:
    with pytest.raises(runner.ManifestError) as error:
        runner.run(tier, name, jobs=1, timing=False, manifest=manifest)
    return str(error.value)


def test_r2_a_selector_listed_twice_is_rejected(probe_dir):
    runner = _runner()
    selector = f"{probe_dir}/probe_cases.py::test_passes"
    message = _manifest_error(runner, _manifest([selector, f"{probe_dir}/probe_cases.py::test_param", selector]))
    assert "T0 probe" in message and repr(selector) in message and "2 times" in message


@pytest.mark.parametrize("overlap", ["file", "parametrized"])
def test_r2_overlapping_file_and_node_selectors_are_rejected(probe_dir, overlap):
    runner = _runner()
    path = f"{probe_dir}/probe_cases.py"
    broad, narrow = ((path, f"{path}::test_passes") if overlap == "file"
                     else (f"{path}::test_param", f"{path}::test_param[1]"))
    node = f"{path}::test_passes" if overlap == "file" else f"{path}::test_param[1]"
    message = _manifest_error(runner, _manifest([broad, narrow]))
    assert "T0 probe" in message and node in message and repr(broad) in message and repr(narrow) in message


def _snapshot_manifest(runner, tmp_path, rows: list[str]) -> dict:
    manifest = runner.load_manifest()
    fake = tmp_path / "snapshot.txt"
    fake.write_text("\n".join(rows) + "\n")
    return {**manifest, "T2": {**manifest["T2"], "snapshot": str(fake)}}


def test_r2_a_duplicated_t2_snapshot_row_is_rejected(tmp_path):
    runner = _runner()
    rows = (ROOT / runner.load_manifest()["T2"]["snapshot"]).read_text().splitlines()
    manifest = _snapshot_manifest(runner, tmp_path, [*rows, rows[3]])
    with pytest.raises(runner.ManifestError) as error:
        runner.check_t2_snapshot(manifest, rows)
    assert "T2" in str(error.value) and rows[3] in str(error.value) and "2 times" in str(error.value)


def test_r2_a_collected_test_absent_from_the_t2_snapshot_is_rejected(tmp_path):
    runner = _runner()
    rows = (ROOT / runner.load_manifest()["T2"]["snapshot"]).read_text().splitlines()
    manifest = _snapshot_manifest(runner, tmp_path, rows[:-1])
    with pytest.raises(runner.ManifestError) as error:
        runner.check_t2_snapshot(manifest, rows)
    assert "T2" in str(error.value) and rows[-1] in str(error.value) and "not in the snapshot" in str(error.value)


def _toml_manifest(tmp_path, tests: list[str]) -> Path:
    path = tmp_path / "tiers.toml"
    listed = ", ".join(f'"{test}"' for test in tests)
    path.write_text('schema = "virelai-test-tiers-v1"\nweights = "tests/tiers/file_weights.json"\n'
                    f'[T2]\npaths = ["tests"]\nsnapshot = "tests/tiers/T2_collected.txt"\n'
                    f'[T0.probe]\ntests = [{listed}]\n')
    return path


@pytest.mark.parametrize("jobs", ["0", "-2"])
def test_r2_fewer_than_one_worker_is_a_usage_error(probe_dir, tmp_path, jobs):
    runner = _runner()
    manifest = _toml_manifest(tmp_path, [f"{probe_dir}/probe_cases.py::test_passes"])
    with pytest.raises(SystemExit) as error:
        runner.main(["T0", "probe", "--jobs", jobs, "--manifest", str(manifest)])
    assert error.value.code == 2


@pytest.fixture
def slow_probe_dir():
    directory = ROOT / f".tiers-selftest-{uuid.uuid4().hex[:8]}"
    directory.mkdir()
    (directory / "probe_a.py").write_text("import time\n\ndef test_sleeps():\n    time.sleep(120)\n")
    (directory / "probe_b.py").write_text("import time\n\ndef test_sleeps():\n    time.sleep(120)\n")
    try:
        yield directory.relative_to(ROOT).as_posix()
    finally:
        shutil.rmtree(directory)


def _workers(marker: str) -> list[int]:
    """Live processes whose command line names ``marker`` (the runner's private scratch folder)."""
    import subprocess

    listing = subprocess.run(["ps", "-ww", "-eo", "pid=,stat=,args="], capture_output=True, text=True).stdout
    found = []
    for line in listing.splitlines():
        pid, stat, args = (line.strip().split(None, 2) + ["", ""])[:3]
        if marker in args and "pytest" in args and not stat.startswith("Z"):
            found.append(int(pid))
    return found


@pytest.mark.parametrize("signum", ["SIGTERM", "SIGINT"])
def test_r2_terminating_only_the_runner_reaps_every_worker_and_publishes_nothing(slow_probe_dir, tmp_path, signum):
    import os
    import signal
    import subprocess
    import sys
    import time

    number = getattr(signal, signum)
    manifest = _toml_manifest(tmp_path, [f"{slow_probe_dir}/probe_a.py", f"{slow_probe_dir}/probe_b.py"])
    scratch_parent = tmp_path / "scratch"
    scratch_parent.mkdir()
    results = tmp_path / "results.json"
    env = {**os.environ, "TMPDIR": str(scratch_parent)}
    runner = subprocess.Popen([sys.executable, str(ROOT / "tools" / "test_tiers.py"), "T0", "probe", "--jobs", "2",
                               "--manifest", str(manifest), "--results", str(results)],
                              cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pids: list[int] = []
    try:
        deadline = time.monotonic() + 90
        while len(pids) < 2 and time.monotonic() < deadline and runner.poll() is None:
            time.sleep(0.5)
            pids = _workers(str(scratch_parent))
        assert len(pids) == 2, "the runner did not start two workers"
        os.kill(runner.pid, number)  # the runner only, never its workers
        status = runner.wait(timeout=60)
        deadline = time.monotonic() + 30
        while _workers(str(scratch_parent)) and time.monotonic() < deadline:
            time.sleep(0.5)
        assert _workers(str(scratch_parent)) == [], "a worker outlived the runner"
        assert status == 128 + number
        assert list(scratch_parent.iterdir()) == []  # the scratch folder went after its workers
        assert not results.exists()  # an interrupted tier publishes no result map
    finally:
        if runner.poll() is None:
            runner.kill()
        for pid in _workers(str(scratch_parent)):
            os.kill(pid, signal.SIGKILL)
