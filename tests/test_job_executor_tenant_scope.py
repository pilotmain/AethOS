# SPDX-License-Identifier: Apache-2.0
"""Background jobs must re-enter their stamped tenant scope so owner-scoped credentials
(Vercel/Railway) resolve — otherwise read-only provider diagnostics fall back to the
uninstalled browser path."""

from __future__ import annotations

from aethos_core.runtime.job_executor import JobExecutor


def test_execute_one_scoped_enters_job_tenant(monkeypatch):
    seen = {}

    class _Job:
        params = {"tenant_id": "rayameha@gmail.com"}

    import aethos_core.runtime.jobs as jobs_mod

    monkeypatch.setattr(jobs_mod.job_store, "get", lambda jid: _Job())

    # Capture the tenant active when _execute_one runs.
    ex = JobExecutor()

    def _fake_execute_one(job_id):
        from aethos_core.tenancy import get_current_tenant

        seen["tenant"] = get_current_tenant()

    monkeypatch.setattr(ex, "_execute_one", _fake_execute_one)
    ex._execute_one_scoped("job-x")
    assert seen["tenant"] == "rayameha@gmail.com"


def test_execute_one_scoped_no_tenant_is_safe(monkeypatch):
    class _Job:
        params = {}

    import aethos_core.runtime.jobs as jobs_mod

    monkeypatch.setattr(jobs_mod.job_store, "get", lambda jid: _Job())
    ex = JobExecutor()
    called = {}
    monkeypatch.setattr(ex, "_execute_one", lambda jid: called.setdefault("ran", True))
    ex._execute_one_scoped("job-y")
    assert called.get("ran") is True
