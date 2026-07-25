# SPDX-License-Identifier: Apache-2.0
"""Phase 9.9 — Productionization and distribution."""

from __future__ import annotations

import pytest

from aethos_core.observability.metrics import clear_metrics_for_tests, increment, prometheus_text, snapshot_metrics
from aethos_core.observability.metering import clear_metering_for_tests, get_usage_summary, record_usage
from aethos_core.orgs.audit_attribution import clear_attributions_for_tests, record_attribution
from aethos_core.orgs.members import assign_role, get_member_role
from aethos_core.orgs.organizations import clear_orgs_for_tests, get_current_organization
from aethos_core.orgs.rbac import check_rbac
from aethos_core.orgs.workspaces import register_workspace
from aethos_core.production.deployment_topology import get_deployment_topology, validate_production_environment
from aethos_core.runtime.distributed.queue_backend import get_queue_backend, reset_queue_backend_for_tests
from aethos_core.runtime.distributed.retry_orchestration import plan_retry
from aethos_core.runtime.distributed.worker_leases import acquire_lease, clear_leases_for_tests, release_lease
from aethos_core.runtime.resilience.schema_migrations import clear_migrations_for_tests, run_pending_migrations
from aethos_core.runtime.resilience.upgrade_manager import check_upgrade_compatibility, rollback_upgrade, run_upgrade
from aethos_sdk.plugin_registry import clear_plugins_for_tests, list_plugins
from aethos_sdk.plugin_types import PluginManifest


@pytest.fixture(autouse=True)
def _clean():
    clear_orgs_for_tests()
    clear_attributions_for_tests()
    clear_leases_for_tests()
    clear_migrations_for_tests()
    clear_metrics_for_tests()
    clear_metering_for_tests()
    clear_plugins_for_tests()
    reset_queue_backend_for_tests()
    yield
    clear_orgs_for_tests()
    clear_attributions_for_tests()
    clear_leases_for_tests()
    clear_migrations_for_tests()
    clear_metrics_for_tests()
    clear_metering_for_tests()
    clear_plugins_for_tests()
    reset_queue_backend_for_tests()


def test_deployment_topology():
    topo = get_deployment_topology()
    assert topo.get("topology_version") == "9.9"
    assert "api" in (topo.get("services") or {})


def test_rbac_viewer_cannot_approve_e3():
    assign_role(user_id="viewer1", role="viewer")
    result = check_rbac(role=get_member_role(user_id="viewer1"), action="approve_e3")
    assert result.get("allowed") is False


def test_rbac_admin_can_approve_e3():
    result = check_rbac(role="admin", action="approve_e3")
    assert result.get("allowed") is True


def test_worker_lease_prevents_duplicate():
    first = acquire_lease(resource_key="job:test", worker_id="w1")
    second = acquire_lease(resource_key="job:test", worker_id="w2")
    assert first.get("ok") is True
    assert second.get("ok") is False
    release_lease(resource_key="job:test", worker_id="w1")


def test_bounded_retry_blocks_hidden_retries():
    result = plan_retry(domain="verification_retry", attempt=3)
    assert result.get("ok") is False
    assert result.get("autonomous_execution_blocked") is True


def test_schema_migration_and_rollback():
    mig = run_pending_migrations()
    assert mig.get("ok") is True
    upgrade = run_upgrade()
    assert upgrade.get("ok") is True
    rollback = rollback_upgrade()
    assert rollback.get("ok") is True


def test_plugin_governance_blocks_forbidden():
    from aethos_sdk.plugin_governance import validate_plugin_governance

    manifest = PluginManifest(
        plugin_id="bad",
        name="Bad",
        plugin_type="provider_adapter",
        version="0.0.1",
        capabilities=["unrestricted_shell"],
    )
    gov = validate_plugin_governance(manifest)
    assert gov.get("ok") is False


def test_observability_prometheus_export():
    increment("test.metric")
    text = prometheus_text()
    assert "aethos_test_metric" in text


def test_tenant_workspace_registration():
    org = get_current_organization()
    ws = register_workspace(name="Production", org_id=org.get("org_id"))
    assert ws.get("org_id") == org.get("org_id")


def test_audit_attribution_immutable():
    rec = record_attribution(actor_id="u1", actor_role="admin", action="approve", resource_type="preflight", resource_id="pf-1")
    assert rec.get("immutable") is True


def test_production_validation():
    result = validate_production_environment()
    assert "issues" in result


def test_queue_backend_snapshot():
    qb = get_queue_backend()
    qb.enqueue("job-1")
    assert qb.depth() >= 1
