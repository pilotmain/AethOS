# SPDX-License-Identifier: Apache-2.0
"""Net policy egress tests (§B8)."""

from __future__ import annotations

from aethos_core.governance.net_policy import check_egress, load_policy


def test_deny_list_blocks_host():
    policy = load_policy("default")
    policy["deny"] = ["evil.example"]
    from aethos_core.governance import net_policy

    net_policy._store_path().parent.mkdir(parents=True, exist_ok=True)
    import json

    net_policy._store_path().write_text(json.dumps(policy), encoding="utf-8")
    allowed, reason = check_egress("https://evil.example/path", tenant_id="default")
    assert allowed is False
    assert reason == "denied_by_policy"


def test_strict_mode_blocks_unknown():
    from aethos_core.governance import net_policy

    policy = {"mode": "strict", "allow": ["api.github.com"], "deny": []}
    net_policy._store_path().write_text(__import__("json").dumps(policy), encoding="utf-8")
    allowed, reason = check_egress("https://unknown.host/foo", tenant_id="default")
    assert allowed is False
    assert reason == "strict_mode_unknown_host"
