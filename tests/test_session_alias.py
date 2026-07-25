# SPDX-License-Identifier: Apache-2.0

from aethos_core.channels.session_alias import (
    get_session_group,
    link_session_ids,
    resolve_canonical_session_id,
    session_ids_for_lookup,
)
from aethos_core.research.research_session_memory import get_last_research_run, remember_research_run


def test_link_session_ids_prefers_web_canonical(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = link_session_ids(session_ids=["tg-123-456", "sess-web1"])
    assert out["ok"] is True
    assert out["canonical_session_id"] == "sess-web1"
    assert "tg-123-456" in out["linked_session_ids"]
    assert resolve_canonical_session_id("tg-123-456") == "sess-web1"
    assert resolve_canonical_session_id("sess-web1") == "sess-web1"


def test_research_memory_merges_linked_sessions(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RESEARCH_ARTIFACTS_DIR", str(tmp_path / "research_artifacts"))
    link_session_ids(session_ids=["sess-a", "tg-99"])
    remember_research_run(
        session_id="tg-99",
        replay_id="rrun-tg",
        query="telegram compare",
        comparison=True,
    )
    row = get_last_research_run("sess-a")
    assert row is not None
    assert row.get("replay_id") == "rrun-tg"
    assert "sess-a" in session_ids_for_lookup("tg-99")
    group = get_session_group("sess-a")
    assert group["canonical_session_id"] == "sess-a"
