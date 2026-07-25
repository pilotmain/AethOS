# SPDX-License-Identifier: Apache-2.0

from aethos_core.memory.vector_store import memory_snapshot, remember


def test_memory_snapshot_disabled(monkeypatch):
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "false")
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    snap = memory_snapshot(limit=3)
    assert snap["enabled"] is False
    get_settings.cache_clear()


def test_memory_snapshot_with_entries(monkeypatch, tmp_path):
    monkeypatch.setenv("VECTOR_MEMORY_ENABLED", "true")
    from aethos_core.config import get_settings
    import aethos_core.memory.vector_store as vs

    get_settings.cache_clear()
    monkeypatch.setattr(vs, "_memory_path", lambda: tmp_path / "vector_memory.json")
    remember(text="aethos deployment status", tags=["ops"])
    snap = memory_snapshot(limit=5)
    assert snap["enabled"] is True
    assert snap["entry_count"] == 1
    assert snap["recent"][0]["text"].startswith("aethos")
    get_settings.cache_clear()
