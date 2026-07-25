# SPDX-License-Identifier: Apache-2.0
"""Manual-QA regression (2026-06-18): deploying a repo that can't be resolved must give an
honest 'I can't resolve that repo — give me owner/repo' message, not a generic
'needs information' preflight summary."""

from __future__ import annotations

import pytest

from aethos_core.operations.mutations.preflight import compose_unresolved_deploy_repo_summary as f


def test_nonexistent_repo_name_is_named_and_asks_for_owner_repo():
    s = f("railway", "Deploy a repo called totally-does-not-exist-123 to Railway")
    assert "totally-does-not-exist-123" in s
    assert "owner/repo" in s.lower()
    assert "no deploy from git was performed" in s.lower()


def test_owner_repo_reference_is_treated_as_access_check():
    s = f("railway", "Deploy pilotmain/AethOS to Railway")
    assert "pilotmain/AethOS" in s
    assert "no deploy from git was performed" in s.lower()


@pytest.mark.parametrize("req", ["deploy my app from git", "deploy the repo", "deploy from github"])
def test_filler_words_do_not_become_a_fake_repo_name(req):
    s = f("vercel", req)
    # must not echo a stopword like "my"/"the"/"app" as the repo name
    assert "**my**" not in s and "**the**" not in s and "**app**" not in s
    assert "owner/repo" in s.lower()
