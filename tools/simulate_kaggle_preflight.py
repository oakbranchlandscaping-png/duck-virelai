#!/usr/bin/env python3
"""Run a packaged Ring 9 notebook's real pre-run code against a simulated Kaggle mount.

Author: Claude (Alpha build seat), 2026-09-27.

Executes the package notebook's own cells 2, 6, 8, 10 and 12, then cell 14 up to (not
including) the benchmark launch, against a fake /kaggle tree. This exercises the exact
startup gates Kaggle will run: bundle discovery, src.zip mount handling, source-manifest
verification, the checkpoint world allowlist, and the execution-receipt comparison.

Stubbed, because they need Kaggle hardware or competition data:
  * the setup command (vLLM install and server start) is replaced by writing the
    environment block that command persists, parsed from the bundle's own
    setup_commands.json;
  * the offline competition game list is replaced by the benchmark pickle's own games.

LAYOUT selects how the source reaches the notebook:
  nested  Kaggle expanded src.zip into src/src/... (observed on Kaggle for -r skip uploads)
  zip     src.zip delivered unexpanded; the notebook extracts it
  direct  src/ mounted as a plain tree

Requirements: Linux (the notebook hard-codes /kaggle, so this writes and then removes a
/kaggle tree and needs permission to do so), Python 3.12, and the TAAF runtime
dependencies (arc_agi, arcengine, numpy, scipy, matplotlib, imageio, python-dotenv,
requests). The bundled source supplies taaf and inference. Assumes the notebook layout
derived from ring9-g3-vc33-closure-v3 (cell indices as above).

Usage:
  python3 tools/simulate_kaggle_preflight.py kaggle/<package> {nested,zip,direct}
"""
from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import sys
import sysconfig
import zipfile
from pathlib import Path


def main() -> int:
    package = Path(sys.argv[1]).resolve()
    layout = sys.argv[2]
    notebook = json.loads((package / "kernel" / "taaf_kaggle_run_share.ipynb").read_text())

    def cell(index: int) -> str:
        return "".join(notebook["cells"][index]["source"])

    dataset_id = json.loads((package / "source-dataset" / "dataset-metadata.json").read_text())["id"]
    root = Path("/kaggle")
    shutil.rmtree(root, ignore_errors=True)
    mount = root / "input" / dataset_id.split("/", 1)[1]
    mount.mkdir(parents=True)
    source_dataset = package / "source-dataset"
    for path in source_dataset.iterdir():
        if path.name not in ("src", "src.zip", "dataset-metadata.json"):
            shutil.copy2(path, mount / path.name)
    if layout == "nested":
        with zipfile.ZipFile(source_dataset / "src.zip") as archive:
            archive.extractall(mount / "src")
    elif layout == "zip":
        shutil.copy2(source_dataset / "src.zip", mount / "src.zip")
    elif layout == "direct":
        shutil.copytree(source_dataset / "src", mount / "src")
    else:
        raise SystemExit(f"unknown layout {layout!r}")

    pth = Path(sysconfig.get_paths()["purelib"]) / "taaf_kaggle_sources.pth"
    scope: dict = {"__name__": "__main__"}
    try:
        exec(compile(cell(2), "cell2", "exec"), scope)
        exec(compile(cell(6), "cell6", "exec"), scope)

        cell8 = cell(8)
        exec(compile(cell8[: cell8.index("# Solver setup commands")], "cell8-pre", "exec"), scope)
        command = json.loads((scope["BUNDLE_DIR"] / "setup_commands.json").read_text())[0]
        block = re.search(r"\nsetup_env = (\{.*?\n\})\n", command, re.S).group(1)
        persisted = eval(block, {
            "SITE_PACKAGES": Path("/kaggle/working/vllm-site-packages"),
            "VLLM_BASE_URL": "http://127.0.0.1:1234/v1",
            "SERVED_MODEL_NAME": re.search(r"SERVED_MODEL_NAME = '([^']+)'", command).group(1),
            "ANALYZER_CONTEXT_WINDOW": int(re.search(r"ANALYZER_CONTEXT_WINDOW = (\d+)", command).group(1)),
            "os": os, "str": str,
        })
        env = json.loads(scope["SETUP_ENV_PATH"].read_text())
        env.update(persisted)
        scope["SETUP_ENV_PATH"].write_text(json.dumps(env))
        os.environ.update({k: str(v) for k, v in env.items()})

        exec(compile(cell(10), "cell10", "exec"), scope)
        exec(compile(cell(12), "cell12", "exec"), scope)

        cell14 = cell(14)
        stop = cell14.index("soft_end = datetime.now()")
        offline = "bm.games = _offline_games(competition_env_files, expected_worlds)"
        pre = cell14[:stop]
        if pre.count(offline) != 1:
            raise SystemExit("notebook layout changed: offline game line not found exactly once")
        pre = pre.replace(offline, "bm.games = [g for g in bm.games if g.env_name in expected_worlds]")
        exec(compile(pre, "cell14-pre", "exec"), scope)

        solver = scope["bm"].solver
        gates = importlib.import_module("inference.framework.virelai_gates")
        print("deadline:", cell14[stop:].splitlines()[0].strip())
        print(f"RESULT layout={layout} label={scope['bm'].label} actions={solver.max_actions_per_game} "
              f"runtime={solver.max_runtime_s_per_game} mode={solver.virelai_mode} "
              f"model={os.environ.get('LOCAL_ANALYZER_MODEL_ID')}")
        print("solver source loaded from:", gates.__file__)
        return 0
    finally:
        shutil.rmtree(root, ignore_errors=True)
        pth.unlink(missing_ok=True)


if __name__ == "__main__":
    sys.exit(main())
