# SPDX-License-Identifier: Apache-2.0
"""Self-organizing memory: derive topics, group entries by topic, compress a topic —
a read/organize layer over the vector store that never changes how memories are written."""

from __future__ import annotations

from unittest.mock import patch

import aethos_core.memory.self_organizing as som

_ROWS = [
    {"id": "1", "text": "Railway deploy restarted twice after the migration", "tags": ["railway"]},
    {"id": "2", "text": "Railway service is healthy again now", "tags": ["railway"]},
    {"id": "3", "text": "Stripe webhook signature verification uses HMAC SHA256", "tags": []},
    {"id": "4", "text": "The customer prefers concise answers without preamble", "tags": ["preferences"]},
]


def test_topic_for_prefers_tag_then_keyword():
    assert som.topic_for("anything", ["MyTag"]) == "mytag"
    assert som.topic_for("Railway deploy railway restart railway", []) == "railway"
    assert som.topic_for("", []) == "general"


def test_organize_groups_by_topic():
    with patch.object(som, "_rows", return_value=_ROWS):
        groups = som.organize_memories()
    topics = {g["topic"]: g["count"] for g in groups}
    assert topics.get("railway") == 2  # two railway-tagged entries grouped
    assert "preferences" in topics
    # Sorted by count desc → railway (2) is first.
    assert groups[0]["topic"] == "railway"


def test_overview_counts():
    with patch.object(som, "_rows", return_value=_ROWS):
        ov = som.memory_overview()
    assert ov["entry_count"] == 4
    assert ov["topic_count"] >= 3


def test_compress_topic_deterministic_join():
    with patch.object(som, "_rows", return_value=_ROWS):
        out = som.compress_topic("railway", use_llm=False)
    assert out["ok"] and out["topic"] == "railway" and out["count"] == 2
    assert "restarted twice" in out["digest"] and "healthy again" in out["digest"]


def test_compress_unknown_topic():
    with patch.object(som, "_rows", return_value=_ROWS):
        out = som.compress_topic("does-not-exist", use_llm=False)
    assert out["ok"] is False
