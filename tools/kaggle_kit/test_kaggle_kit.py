"""Tests for the self-hosting kit (run: python3 -m pytest -q tools/kaggle_kit).

Author: Claude (Alpha build seat), 2026-10-01.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parent
ROOT = KIT.parents[1]
CARRY = ROOT / "kaggle" / "ring9-carry-vc33-v1"
CARRY_V2 = ROOT / "kaggle" / "ring9-carry-vc33-v2"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"kit_{name}", KIT / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    return module


wheelhouse = _load("build_wheelhouse")
deps = _load("dependencies")
mirror = _load("mirror_model")


def test_the_v3_lock_is_the_exit_runs_174_wheels_in_order_with_pypi_digests():
    lock = json.loads((KIT / "wheelhouse_v3.lock.json").read_text())
    files = (KIT / "wheelhouse_v3_files.txt").read_text().split()
    assert [row["filename"] for row in sorted(lock["wheels"], key=lambda r: r["line"])] == files
    assert len(files) == 174 and all(len(row["sha256"]) == 64 for row in lock["wheels"])
    lines = wheelhouse.requirement_lines(lock)
    assert "vllm==0.19.0" in lines and "torch==2.10.0" in lines and "flashinfer_python==0.6.6" in lines
    assert lock["stamp"] == "vllm==0.19.0 torch==2.10.0 flashinfer==0.6.6\n"


def test_a_wheel_whose_bytes_differ_from_the_pin_is_refused(tmp_path, monkeypatch):
    good, bad = b"wheel-bytes", b"tampered"
    row = {"line": 1, "filename": "x-1.0-py3-none-any.whl", "name": "x", "version": "1.0", "size": len(good),
           "sha256": hashlib.sha256(good).hexdigest(), "url": "https://example.invalid/x.whl"}

    class Response:
        def __init__(self, data):
            self.data = [data]

        def read(self, _n):
            return self.data.pop() if self.data else b""

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(wheelhouse.time, "sleep", lambda _s: None)
    monkeypatch.setattr(wheelhouse.urllib.request, "urlopen", lambda *_a, **_k: Response(bad))
    with pytest.raises(ValueError, match="sha256 mismatch"):
        wheelhouse.fetch(row, tmp_path)
    assert not list(tmp_path.iterdir())
    monkeypatch.setattr(wheelhouse.urllib.request, "urlopen", lambda *_a, **_k: Response(good))
    report = wheelhouse.build({"wheels": [row], "stamp": "s", "source": "t"}, tmp_path)
    assert report["all_digests_verified"] and (tmp_path / "requirements.lock").read_text() == "x==1.0\n"


def _setup_and_kernel():
    command = json.loads((CARRY / "source-dataset" / "setup_commands.json").read_text())
    meta = json.loads((CARRY / "kernel" / "kernel-metadata.json").read_text())
    return command, meta


@pytest.mark.skipif(not CARRY.is_dir(), reason="needs the committed ring9-carry-vc33-v1 package")
def test_retarget_points_both_the_mounts_and_the_setup_at_the_self_hosted_datasets():
    command, meta = _setup_and_kernel()
    new_command, new_meta = deps.retarget(command, meta, deps.THIRD_PARTY_V3, deps.SELF_HOSTED_V3)
    assert new_meta["dataset_sources"] == [
        meta["dataset_sources"][0], "stephenkaskin/virelai-vllm-wheelhouse-v3", "stephenkaskin/virelai-qwen3-6-27b-fp8",
    ]
    text = new_command[0]
    assert "driessmit1" not in text and "driessmit1" not in json.dumps(new_meta)
    assert "WHEELHOUSE_OWNER = 'stephenkaskin'" in text and "MODEL_SLUG = 'virelai-qwen3-6-27b-fp8'" in text
    assert "SERVED_MODEL_NAME = 'vrfai/Qwen3.6-27B-FP8'" in text  # same model, same served name
    # Everything else in the command is untouched.
    assert len(text.splitlines()) == len(command[0].splitlines())
    changed = [a for a, b in zip(command[0].splitlines(), text.splitlines()) if a != b]
    assert len(changed) == 4  # the two owners and the two slugs


@pytest.mark.skipif(not CARRY.is_dir(), reason="needs the committed ring9-carry-vc33-v1 package")
def test_a_model_swap_is_one_record_and_a_wrong_shape_is_refused():
    command, meta = _setup_and_kernel()
    swap = deps.Dependencies(wheelhouse="stephenkaskin/w", model="stephenkaskin/m", served_model_name="Org/New-Model",
                             max_model_len=131072, tool_call_parser="qwen3_xml")
    text = deps.retarget(command, meta, deps.THIRD_PARTY_V3, swap)[0][0]
    assert "VLLM_MAX_MODEL_LEN = 131072" in text and "ANALYZER_CONTEXT_WINDOW = 131072" in text
    assert "'--tool-call-parser',\n        'qwen3_xml'" in text and "'--reasoning-parser',\n        'qwen3'" in text
    with pytest.raises(ValueError, match="exactly one"):
        deps.retarget_setup(text.replace("MODEL_SLUG", "MODEL_NAME"), swap)
    with pytest.raises(ValueError, match="does not mount"):
        deps.retarget(command, {**meta, "dataset_sources": meta["dataset_sources"][:1]}, deps.THIRD_PARTY_V3, swap)


def _fake_hub(monkeypatch, files: dict[str, bytes], digests: dict[str, str] | None = None):
    hub = types.ModuleType("huggingface_hub")

    class Info:
        sha = "a" * 40
        card_data = {"license": "apache-2.0"}
        siblings = [types.SimpleNamespace(rfilename=name, size=len(data),
                                          lfs={"sha256": (digests or {}).get(name, hashlib.sha256(data).hexdigest())})
                    for name, data in files.items()]

    class HfApi:
        def model_info(self, repo, revision, files_metadata):
            return Info()

    def snapshot_download(repo_id, revision, local_dir, allow_patterns):
        for name in allow_patterns:
            path = Path(local_dir) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(files[name])

    hub.HfApi, hub.snapshot_download = HfApi, snapshot_download
    monkeypatch.setitem(sys.modules, "huggingface_hub", hub)


def test_the_mirror_pins_the_commit_skips_excluded_files_and_verifies_every_digest(tmp_path, monkeypatch):
    files = {"config.json": b"{}", "model-00001.safetensors": b"weights", "original/consolidated.pth": b"dup"}
    _fake_hub(monkeypatch, files)
    assert mirror.main(["--repo", "org/m", "--out", str(tmp_path / "m"), "--dataset", "me/m-mirror",
                        "--exclude", "original/*"]) == 0
    record = json.loads((tmp_path / "m" / "MIRROR.json").read_text())
    assert record["commit"] == "a" * 40 and record["license"] == "apache-2.0"
    assert [item["path"] for item in record["files"]] == ["config.json", "model-00001.safetensors"]
    assert not (tmp_path / "m" / "original").exists()


def test_the_mirror_refuses_a_file_whose_digest_differs(tmp_path, monkeypatch):
    _fake_hub(monkeypatch, {"model.safetensors": b"weights"}, digests={"model.safetensors": "0" * 64})
    with pytest.raises(SystemExit, match="sha256 mismatch"):
        mirror.main(["--repo", "org/m", "--out", str(tmp_path / "m"), "--dataset", "me/m-mirror"])


@pytest.mark.skipif(not CARRY_V2.is_dir(), reason="needs the committed ring9-carry-vc33-v2 package")
def test_the_self_hosted_package_mounts_and_records_only_the_directors_datasets():
    old_owner = deps.THIRD_PARTY_V3.wheelhouse.split("/")[0].encode()
    source = CARRY_V2 / "source-dataset" / "src"
    read_by_machine = [
        path for path in CARRY_V2.rglob("*")
        if path.is_file() and source not in path.parents and path.name not in {"src.zip", "RUN.md"}
    ]
    assert read_by_machine and not [p.name for p in read_by_machine if old_owner in p.read_bytes()]
    meta = json.loads((CARRY_V2 / "kernel" / "kernel-metadata.json").read_text())
    assert meta["dataset_sources"][1:] == [deps.SELF_HOSTED_V3.wheelhouse, deps.SELF_HOSTED_V3.model]
    for receipt in (CARRY_V2 / "execution_receipt.json", CARRY_V2 / "source-dataset" / "execution_receipt.json"):
        assert json.loads(receipt.read_text())["dependencies"] == deps.SELF_HOSTED_V3.record()
