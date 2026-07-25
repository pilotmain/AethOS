# SPDX-License-Identifier: Apache-2.0
"""Continuous Monitor agents: stateful watchers that record an observation only when
the watched signal changes, run across tenants on the scheduler, and never mutate."""

from __future__ import annotations

from unittest.mock import patch

import aethos_core.monitors.runtime as mon
from aethos_core.tenancy import tenant_scope


def _fake_probe_sequence(*signatures):
    """Return a probe callable that yields the given signatures on successive calls."""
    calls = {"i": 0}

    def _probe(target):
        i = min(calls["i"], len(signatures) - 1)
        calls["i"] += 1
        sig = signatures[i]
        return {"state": {"v": sig}, "summary": f"state={sig}", "signature": sig, "alert": sig.startswith("down")}

    return _probe


def _cleanup(monitor_id):
    mon.delete_monitor(monitor_id)


def test_create_list_scoped_to_tenant():
    with tenant_scope("alice@example.com"):
        m = mon.create_monitor(name="A", kind="url", target="https://example.com")
        assert m["monitor_id"].startswith("mon-")
        assert any(x["monitor_id"] == m["monitor_id"] for x in mon.list_monitors())
    with tenant_scope("bob@example.com"):
        # Bob must NOT see Alice's monitor.
        assert all(x["monitor_id"] != m["monitor_id"] for x in mon.list_monitors())
    _cleanup(m["monitor_id"])


def test_observation_recorded_only_on_change():
    with tenant_scope("alice@example.com"):
        m = mon.create_monitor(name="watch", kind="url", target="https://example.com", interval_sec=60)
    mid = m["monitor_id"]
    with patch.dict(mon._PROBES, {"url": _fake_probe_sequence("up:200", "up:200", "down:500")}):
        r1 = mon.run_monitor(mid, force=True)  # first run → observation
        r2 = mon.run_monitor(mid, force=True)  # unchanged → no new observation
        r3 = mon.run_monitor(mid, force=True)  # changed → observation
    assert r1["changed"] is True and r2["changed"] is False and r3["changed"] is True
    rec = mon.get_monitor(mid)
    assert len(rec["observations"]) == 2  # only the two changes
    assert rec["observations"][0]["signature"] == "down:500"
    _cleanup(mid)


def test_run_due_respects_interval_and_force():
    with tenant_scope("alice@example.com"):
        m = mon.create_monitor(name="x", kind="url", target="https://example.com", interval_sec=9999)
    mid = m["monitor_id"]
    with patch.dict(mon._PROBES, {"url": _fake_probe_sequence("up:200", "up:200")}):
        mon.run_monitor(mid, force=True)  # sets last_run_at now
        due = mon.run_due_monitors()  # interval huge → not due
        ran_ids = [r.get("monitor_id") for r in due["results"]]
        assert mid not in ran_ids
        forced = mon.run_due_monitors(force=True)  # force → runs
        assert any(r.get("monitor_id") == mid for r in forced["results"])
    _cleanup(mid)


def test_disabled_monitor_not_run():
    with tenant_scope("alice@example.com"):
        m = mon.create_monitor(name="off", kind="url", target="https://example.com", enabled=False, interval_sec=60)
    mid = m["monitor_id"]
    with patch.dict(mon._PROBES, {"url": _fake_probe_sequence("up:200")}):
        forced = mon.run_due_monitors(force=True)
    assert all(r.get("monitor_id") != mid for r in forced["results"])
    _cleanup(mid)


def test_unknown_kind_rejected():
    with tenant_scope("alice@example.com"):
        try:
            mon.create_monitor(name="bad", kind="nope", target="x")
            assert False, "should have raised"
        except ValueError:
            pass
