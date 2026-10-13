"""Test-session hooks (WO-1, test-runtime infrastructure, 2026-10-13; author: Claude, Alpha build seat).

One hook only: once collection has imported every test module, and before any test can monkeypatch production
code, ``replay_checkpoints`` records the production attributes it will compare against. A checkpoint call
made while one of them is patched builds a fresh replay and caches nothing.
"""
from __future__ import annotations


def pytest_collection_finish(session) -> None:
    import replay_checkpoints

    replay_checkpoints.production_patched()
