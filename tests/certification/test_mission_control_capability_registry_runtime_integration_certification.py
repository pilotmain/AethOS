"""Certification tests for FIX 296 — capability registry runtime integration."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_296_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_contract import (
    AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296,
    CAPABILITY_ANSWERING_AUTHORITY_FIX_296,
    CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX,
    PROVIDER_AUTHORITY_FIX_296,
    TRUST_MUTATION_AUTHORITY_FIX_296,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
    compose_capability_runtime_reply,
)

pytestmark = pytest.mark.certification


class TestMissionControlCapabilityRegistryRuntimeIntegrationCertification:
    def test_fix_296_contract(self) -> None:
        assert CAPABILITY_REGISTRY_RUNTIME_INTEGRATION_FIX == "FIX 296"
        assert CAPABILITY_ANSWERING_AUTHORITY_FIX_296 is False
        assert AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_296 is False
        assert TRUST_MUTATION_AUTHORITY_FIX_296 is False
        assert PROVIDER_AUTHORITY_FIX_296 is False

    def test_fix_296_certification_requirements(self) -> None:
        assert len(FIX_296_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_296_certification_composes_evidence_sources(self) -> None:
        result = build_capability_registry_runtime_integration(session_id="fix296-cert")
        payload = result.capability_registry_runtime_integration
        assert payload["self_awareness_report"]
        assert payload["sources"]["composes_fix_295_capability_registry"] is True
        assert payload["sources"]["composes_fix_300_multi_tenant_platform_foundation"] is True
        assert payload["capability_answering_authority"] is False

    def test_fix_296_certification_regression_what_can_you_do(self) -> None:
        reply = compose_capability_runtime_reply(session_id="fix296-cert-regression")
        lowered = reply.lower()
        for phrase in (
            "governed software delivery",
            "repository intelligence",
            "product evolution",
            "business operating system",
            "multi-tenant foundation",
            "provider capability matrix",
            "authority boundaries",
        ):
            assert phrase in lowered
