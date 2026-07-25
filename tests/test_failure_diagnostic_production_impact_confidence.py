# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.execution.failure_diagnostic_artifact import derive_production_impact


def test_failure_diagnostic_production_impact_confidence_field():
    summary, confidence, state = derive_production_impact(
        failed_dep={"target": "unknown", "state": "error"},
        last_prod={"id": "dpl_ok", "state": "ready", "target": "production"},
        reachability={"reachable": True, "url": "https://app.vercel.app"},
        prod_url="https://app.vercel.app",
    )
    assert confidence == "insufficient_evidence"
    assert state == "ready"
    assert "Unclear" in summary
