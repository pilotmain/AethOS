# SPDX-License-Identifier: Apache-2.0
"""GitHub inventory must render repositories, not 'projects (0)'."""

from __future__ import annotations

from aethos_core.chat.provider_inventory_format import (
    format_provider_inventory_table,
    normalize_github_inventory_rows,
)
from aethos_core.chat.provider_read_intent import _compose_inventory_body

_GH_INVENTORY = {
    "provider": "github",
    "repository_count": 143,
    "repositories": [
        {"full_name": "pilotmain/AethOS", "owner": "pilotmain", "private": True,
         "default_branch": "main", "html_url": "https://github.com/pilotmain/AethOS",
         "updated_at": "2026-06-17T18:03:21Z"},
        {"full_name": "pilotmain/killit", "owner": "pilotmain", "private": True,
         "default_branch": "main", "html_url": "https://github.com/pilotmain/killit",
         "updated_at": "2026-06-06T10:00:00Z"},
    ],
}


def test_github_rows_normalized():
    rows = normalize_github_inventory_rows(_GH_INVENTORY)
    assert len(rows) == 2
    assert rows[0]["repository"] == "pilotmain/AethOS"
    assert rows[0]["visibility"] == "private"
    assert rows[0]["branch"] == "main"


def test_github_inventory_table_lists_repos():
    table = format_provider_inventory_table("github", _GH_INVENTORY)
    assert "pilotmain/AethOS" in table
    assert "pilotmain/killit" in table
    assert "No inventory rows returned" not in table


def test_github_inventory_body_counts_repositories():
    body = _compose_inventory_body("github", _GH_INVENTORY)
    assert "**Github repositories** (143)" in body
    assert "pilotmain/killit" in body
    assert "projects** (0)" not in body
