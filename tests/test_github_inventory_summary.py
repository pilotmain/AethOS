# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.github_readonly_inspector import (
    build_chat_summary,
    build_inventory_error_summary,
    distinct_owner_logins,
)


def test_distinct_owner_logins_uses_full_inventory():
    items = [{"owner": "acme"} for _ in range(12)] + [{"owner": "other-labs"}]
    assert len(distinct_owner_logins(items)) == 2


def test_build_chat_summary_counts_all_repositories():
    items = [{"full_name": f"acme/repo-{i}", "owner": "acme", "visibility": "public"} for i in range(10)]
    summary = build_chat_summary(items)
    assert "10" in summary
    assert "+ 2 more repositories" in summary


def test_build_inventory_error_summary_is_safe():
    summary = build_inventory_error_summary("HTTP 401 Unauthorized")
    assert "401" in summary
    assert "GitHub inventory could not retrieve" in summary
