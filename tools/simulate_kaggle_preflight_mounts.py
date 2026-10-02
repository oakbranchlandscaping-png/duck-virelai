#!/usr/bin/env python3
"""Run a packaged Ring 9 notebook's real pre-run code against a simulated Kaggle mount,
including the attached dependency datasets and the setup command's own path resolution.

Author: Claude (Alpha build seat), 2026-09-27; dependency mounts added 2026-10-02 for
ring9-carry-vc33-v2 (self-hosted wheelhouse and model).

Executes the package notebook's own cells 2, 6, 8, 10 and 12, then cell 14 up to (not
including) the benchmark launch, against a fake /kaggle tree. Between cells 8 and 10 it runs
the setup command's own Python up to (not including) the vLLM server start: the dataset path
resolution and the "Missing attached dataset path(s)" check that stopped ring9-carry-vc33-v1.

Stubbed, because they need Kaggle hardware or competition data:
  * the GPU check, wheel install and vLLM server (the setup command's environment block is
    written from the bundle's own setup_commands.json);
  * the offline competition game list: each allowlisted world is the benchmark pickle's game
    (a copy renamed to the world when the pickle holds a different one);
  * dependency datasets: SIM_DEPENDENCY_MOUNTS=OWNER/SLUG,... are mounted at Kaggle's
    /kaggle/input/datasets/OWNER/SLUG layout holding only requirements.lock and config.json.

LAYOUT: nested (src.zip expanded into src/src/...), zip (src.zip unexpanded), direct (src/).
Needs Linux with permission to create and remove /kaggle, Python 3.12, and the TAAF runtime
dependencies (arcengine and friends).

Usage:
  SIM_DEPENDENCY_MOUNTS=a/b,c/d python3 tools/simulate_kaggle_preflight_mounts.py kaggle/<package> LAYOUT
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

    deps = os.environ.get("SIM_DEPENDENCY_MOUNTS", "")  # comma-separated OWNER/SLUG mounted (Kaggle's datasets/ layout)
    for ref in filter(None, deps.split(",")):
        owner, slug = ref.split("/")
        dep = root / "input" / "datasets" / owner / slug
        dep.mkdir(parents=True)
        (dep / "requirements.lock").write_text("vllm==0.19.0\n")
        (dep / "config.json").write_text("{}")

    pth = Path(sysconfig.get_paths()["purelib"]) / "taaf_kaggle_sources.pth"
    scope: dict = {"__name__": "__main__"}
    try:
        exec(compile(cell(2), "cell2", "exec"), scope)
        exec(compile(cell(6), "cell6", "exec"), scope)

        cell8 = cell(8)
        exec(compile(cell8[: cell8.index("# Solver setup commands")], "cell8-pre", "exec"), scope)
        command = json.loads((scope["BUNDLE_DIR"] / "setup_commands.json").read_text())[0]
        saved_env = dict(os.environ)
        os.environ.update(scope["_command_env"]())  # what the notebook hands the setup subprocess
        body = command.split("<<'PYSETUP'\n", 1)[1].rsplit("\nPYSETUP", 1)[0]
        cut = "start_vllm_server()\nrun_vllm_api_smoke_test()"
        if body.count(cut) != 1 or body.count("\nassert_expected_cuda_gpu()\n") != 1:
            raise SystemExit("setup command layout changed")
        body = body.split(cut)[0].replace("\nassert_expected_cuda_gpu()\n", "\n")
        setup_scope: dict = {"__name__": "__setup__"}
        exec(compile(body, "setup-pre-server", "exec"), setup_scope)
        print("SETUP wheelhouse:", setup_scope["WHEELHOUSE"], "lock:", (setup_scope["WHEELHOUSE"] / "requirements.lock").is_file())
        print("SETUP model:", setup_scope["MODEL_PATH"], "config:", (setup_scope["MODEL_PATH"] / "config.json").is_file())
        print("SETUP input map:", os.environ["TAAF_KAGGLE_INPUT_PATHS"])
        os.environ.clear()
        os.environ.update(saved_env)
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
        pre = pre.replace(offline, "import copy as _c; _by={g.env_name:g for g in bm.games}; _t=next(iter(_by.values())); bm.games=[_by[w] if w in _by else (lambda x:(setattr(x,'env_name',w),x)[1])(_c.deepcopy(_t)) for w in expected_worlds]")
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
