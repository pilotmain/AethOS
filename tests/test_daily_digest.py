# SPDX-License-Identifier: Apache-2.0
"""Daily Digest: deterministic briefing assembled from existing signals, delivered once
per day at the configured hour, resilient to any single signal source failing."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import aethos_core.digest.runtime as digest
from aethos_core.tenancy import tenant_scope


def test_build_digest_is_deterministic_and_has_sections():
    with tenant_scope("alice@example.com"):
        d = digest.build_digest(use_llm=False)
    titles = [s["title"] for s in d["sections"]]
    assert {"Deployments", "Jobs", "Approvals", "Monitors", "Social"} <= set(titles)
    assert "AethOS Daily Digest" in d["text"]


def test_build_digest_survives_a_failing_signal():
    # A broken subsystem must degrade to a graceful line, not crash the digest.
    with patch.object(digest, "_jobs_section", side_effect=RuntimeError("boom")):
        try:
            with tenant_scope("alice@example.com"):
                digest.build_digest(use_llm=False)
            crashed = False
        except Exception:
            crashed = True
    # _jobs_section itself catches internally; even if patched to raise, build should
    # not propagate because each gatherer is defensive. If it does, that's a regression.
    assert crashed is False


def test_deliver_persists_latest():
    with tenant_scope("alice@example.com"):
        res = digest.deliver_digest()
        assert res["ok"] and "stored" in res["delivered_to"]
        latest = digest.latest_digest()
        assert latest and "AethOS Daily Digest" in latest["text"]


class _FakeSettings:
    def __init__(self, enabled, hour):
        self.digest_enabled = enabled
        self.digest_hour = hour
        self.digest_llm = False
        self.digest_telegram_chat = ""


def test_run_due_disabled_skips():
    with tenant_scope("alice@example.com"), patch.object(digest, "get_settings", return_value=_FakeSettings(False, 8)):
        r = digest.run_due_digests(force=False)
    assert r["delivered"] is False and r["reason"] == "disabled"


def test_run_due_not_digest_hour_skips():
    wrong_hour = (datetime.now().hour + 1) % 24
    with tenant_scope("alice@example.com"), patch.object(digest, "get_settings", return_value=_FakeSettings(True, wrong_hour)):
        r = digest.run_due_digests(force=False)
    assert r["delivered"] is False and r["reason"] == "not_digest_hour"


def test_run_due_force_delivers():
    with tenant_scope("alice@example.com"), patch.object(digest, "get_settings", return_value=_FakeSettings(False, 8)):
        r = digest.run_due_digests(force=True)
    assert r["delivered"] is True
