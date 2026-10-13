"""Shared record-replay checkpoints for tests: one build per process, an independent copy per consumer.

Author: Claude (Alpha build seat), 2026-10-13. WO-1 (test-runtime infrastructure), Sol's rules: "Do not accept a
cached state without returning a fresh, isolated copy to each test ... cache key includes the record identity,
record content hash, cut, replay options and any input that changes the resulting machine ... failed or partial
construction never populates the cache." The design is ``NOTE_SHARED_FILE_WO_TEST_TIERS_2026-10-13``.

- ``checkpoint(path, max_steps=..., answer_source=..., measure=...)`` returns a freshly unpickled
  ``ReplayResult``; ``checkpoint_bytes`` returns the immutable pickled bytes it is built from.
- The key is the resolved path, the sha256 of the record file's bytes, the replay options and the
  production-code fingerprint: while any loaded ``inference.*`` function or class attribute differs from the
  object first seen (a monkeypatch), a call builds a fresh replay, returns it and caches nothing.
- The cache is filled only after the replay returns and pickles; a raised build stores nothing.
- In-process only: there is no disk cache to go stale.

Use it only where a replay is a test's precondition. A test whose subject is the replay itself (determinism,
concurrency, fidelity, a traced or patched replay) keeps calling ``record_replay.replay`` directly.
"""
from __future__ import annotations

import hashlib
import inspect
import pickle
import sys
from pathlib import Path
from typing import Any

_CACHE: dict[tuple, bytes] = {}
_SEEN: dict[tuple[str, str, str], Any] = {}  # (module, owner, attribute) -> the object first seen (kept alive)
_STATS = {"builds": 0, "hits": 0, "bypasses": 0, "failures": 0}


def _attributes(module: Any) -> list[tuple[str, str, Any]]:
    """Every callable bound in a production module's namespace (its own or imported), and every attribute of
    the classes it defines: whatever a monkeypatch could replace."""
    found: list[tuple[str, str, Any]] = []
    for name, value in list(vars(module).items()):
        if inspect.ismodule(value) or not callable(value):
            continue
        found.append(("", name, value))
        if inspect.isclass(value) and getattr(value, "__module__", None) == module.__name__:
            found.extend((name, attr, member) for attr, member in list(vars(value).items())
                         if callable(member) or isinstance(member, (staticmethod, classmethod, property)))
    return found


def production_patched() -> bool:
    """True while any loaded ``inference.*`` attribute is not the object first seen. The first sighting is the
    baseline: this module takes it when imported (at collection) and again when collection finishes
    (``tests/conftest.py``), before any test can patch; a module first loaded later is baselined on sight."""
    patched = False
    for module_name, module in list(sys.modules.items()):
        if module is None or not module_name.startswith("inference."):
            continue
        for owner, attr, value in _attributes(module):
            first = _SEEN.setdefault((module_name, owner, attr), value)
            patched = patched or first is not value
    return patched


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _build(path: Path, max_steps: int | None, answer_source: str, measure: bool) -> Any:
    from inference.framework.record_replay import load_record, replay

    return replay(load_record(path), max_steps=max_steps, answer_source=answer_source, measure=measure)


def checkpoint_bytes(path: str | Path, *, max_steps: int | None = None, answer_source: str = "view",
                     measure: bool = False) -> bytes:
    """The pickled ``ReplayResult`` of ``path`` replayed with these options (built once per process)."""
    resolved = Path(path).resolve()
    if production_patched():
        _STATS["bypasses"] += 1
        return pickle.dumps(_build(resolved, max_steps, answer_source, measure))
    key = (str(resolved), _file_sha(resolved), max_steps, answer_source, bool(measure))
    if key in _CACHE:
        _STATS["hits"] += 1
        return _CACHE[key]
    try:
        blob = pickle.dumps(_build(resolved, max_steps, answer_source, measure))
    except BaseException:
        _STATS["failures"] += 1
        raise
    _STATS["builds"] += 1
    _CACHE[key] = blob
    return blob


def checkpoint(path: str | Path, *, max_steps: int | None = None, answer_source: str = "view",
               measure: bool = False) -> Any:
    """A fresh, independent ``ReplayResult``: every call unpickles its own copy."""
    return pickle.loads(checkpoint_bytes(path, max_steps=max_steps, answer_source=answer_source, measure=measure))


import inference.framework.record_replay  # noqa: E402,F401  the replay path, loaded unpatched at collection

production_patched()  # the import-time baseline


def checkpoint_stats() -> dict[str, int]:
    return {**_STATS, "entries": len(_CACHE)}


__all__ = ["checkpoint", "checkpoint_bytes", "checkpoint_stats", "production_patched"]
