# SPDX-License-Identifier: Apache-2.0
"""FIX 135 — static freeze review for Mission Control operator console."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from aethos_core.mission_control.mission_control_ui_freeze_contract import (
    ALLOWED_MC_OPERATOR_HTTP_ROUTES,
    FORBIDDEN_UI_BUTTON_LABEL_PATTERNS,
    FROZEN_UI_COMPONENT_PATHS,
    FROZEN_WEB_API_CLIENT_PATHS,
    MISSION_CONTROL_OPERATOR_API_MODULE,
    MISSION_CONTROL_UI_FREEZE_FIX,
    MISSION_CONTROL_UI_SCHEMA_VERSION,
)

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _repo_path(rel: str) -> Path:
    return _REPO_ROOT / rel


def review_frozen_ui_components() -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    scanned: list[str] = []
    for rel in FROZEN_UI_COMPONENT_PATHS:
        path = _repo_path(rel)
        scanned.append(rel)
        if not path.is_file():
            violations.append({"path": rel, "reason": "missing_frozen_component"})
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_UI_BUTTON_LABEL_PATTERNS:
            if pattern.search(text):
                violations.append({"path": rel, "reason": f"forbidden_button_label:{pattern.pattern}"})
    return {
        "ok": len(violations) == 0,
        "scanned": scanned,
        "violations": violations,
    }


def review_frozen_web_api_clients() -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    scanned: list[str] = []
    for rel in FROZEN_WEB_API_CLIENT_PATHS:
        path = _repo_path(rel)
        scanned.append(rel)
        if not path.is_file():
            violations.append({"path": rel, "reason": "missing_api_client"})
            continue
        text = path.read_text(encoding="utf-8")
        posts = re.findall(r'method:\s*"POST"', text)
        if rel.endswith("missionControlApprovalExecutionApi.ts"):
            governed_endpoints = (
                "/approval-inbox/execute",
                "/approval-inbox/execute-terminal",
                "/approval-inbox/execute-mutation",
                "/approval-inbox/execute-serve",
                "/approval-inbox/execute-operational-deployment",
                "/approval-inbox/reject-operational-deployment",
            )
            if len(posts) != len(governed_endpoints):
                violations.append(
                    {
                        "path": rel,
                        "reason": f"expected_{len(governed_endpoints)}_governed_posts_found_{len(posts)}",
                    }
                )
            for endpoint in governed_endpoints:
                if endpoint not in text:
                    violations.append({"path": rel, "reason": f"missing_governed_endpoint:{endpoint}"})
        elif rel.endswith("missionControlGovernanceDeliberationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-deliberation/record" not in text:
                violations.append({"path": rel, "reason": "missing_deliberation_record_endpoint"})
        elif rel.endswith("missionControlGovernanceCollaborationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-collaboration/record" not in text:
                violations.append({"path": rel, "reason": "missing_collaboration_record_endpoint"})
        elif rel.endswith("missionControlGovernanceDoctrineApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-doctrine/record" not in text:
                violations.append({"path": rel, "reason": "missing_doctrine_record_endpoint"})
        elif rel.endswith("missionControlGovernancePolicyInterpretationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-policy-interpretation/record" not in text:
                violations.append({"path": rel, "reason": "missing_interpretation_record_endpoint"})
        elif rel.endswith("missionControlGovernanceCoherenceApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-coherence/record" not in text:
                violations.append({"path": rel, "reason": "missing_coherence_record_endpoint"})
        elif rel.endswith("missionControlGovernanceResilienceApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-resilience/record" not in text:
                violations.append({"path": rel, "reason": "missing_resilience_record_endpoint"})
        elif rel.endswith("missionControlGovernanceEvolutionApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governance-evolution/record" not in text:
                violations.append({"path": rel, "reason": "missing_evolution_record_endpoint"})
        elif rel.endswith("missionControlInstitutionalIdentityApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/institutional-identity/record" not in text:
                violations.append({"path": rel, "reason": "missing_identity_record_endpoint"})
        elif rel.endswith("missionControlInstitutionalExternalRelationsApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/institutional-external-relations/record" not in text:
                violations.append({"path": rel, "reason": "missing_external_relations_record_endpoint"})
        elif rel.endswith("missionControlInstitutionalExistentialRiskApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/institutional-existential-risk/record" not in text:
                violations.append({"path": rel, "reason": "missing_existential_risk_record_endpoint"})
        elif rel.endswith("missionControlConstitutionalEthicsApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/constitutional-ethics/record" not in text:
                violations.append({"path": rel, "reason": "missing_constitutional_ethics_record_endpoint"})
        elif rel.endswith("missionControlConstitutionalAuditApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/constitutional-audit/record" not in text:
                violations.append({"path": rel, "reason": "missing_constitutional_audit_record_endpoint"})
        elif rel.endswith("missionControlConstitutionalLegitimacyApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/constitutional-legitimacy/record" not in text:
                violations.append({"path": rel, "reason": "missing_constitutional_legitimacy_record_endpoint"})
        elif rel.endswith("missionControlConstitutionalPluralismApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/constitutional-pluralism/record" not in text:
                violations.append({"path": rel, "reason": "missing_constitutional_pluralism_record_endpoint"})
        elif rel.endswith("missionControlConstitutionalSynthesisApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/constitutional-synthesis/record" not in text:
                violations.append({"path": rel, "reason": "missing_constitutional_synthesis_record_endpoint"})
        elif rel.endswith("missionControlMissionPlanningApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/mission-planning/record" not in text:
                violations.append({"path": rel, "reason": "missing_mission_planning_record_endpoint"})
        elif rel.endswith("missionControlMissionPlanningDeliberationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/mission-planning-deliberation/record" not in text:
                violations.append({"path": rel, "reason": "missing_mission_planning_deliberation_record_endpoint"})
        elif rel.endswith("missionControlHumanDecisionBoardApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/human-decision-board/record" not in text:
                violations.append({"path": rel, "reason": "missing_human_decision_board_record_endpoint"})
        elif rel.endswith("missionControlExecutionHandoffCoordinationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/execution-handoff-coordination/record" not in text:
                violations.append({"path": rel, "reason": "missing_execution_handoff_coordination_record_endpoint"})
        elif rel.endswith("missionControlBoundedDeliveryWorkPackagesApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/bounded-delivery-work-packages/record" not in text:
                violations.append({"path": rel, "reason": "missing_bounded_delivery_work_packages_record_endpoint"})
        elif rel.endswith("missionControlWorkPackageReadinessLaneAdmissionApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/work-package-readiness-lane-admission/record" not in text:
                violations.append({"path": rel, "reason": "missing_work_package_readiness_lane_admission_record_endpoint"})
        elif rel.endswith("missionControlMissionAuthorizationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/mission-authorization/record" not in text:
                violations.append({"path": rel, "reason": "missing_mission_authorization_record_endpoint"})
        elif rel.endswith("missionControlBoundedExecutionParticipationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/bounded-execution-participation/record" not in text:
                violations.append({"path": rel, "reason": "missing_bounded_execution_participation_record_endpoint"})
        elif rel.endswith("missionControlGovernedTaskExecutionCoordinationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governed-task-execution-coordination/record" not in text:
                violations.append({"path": rel, "reason": "missing_governed_task_execution_coordination_record_endpoint"})
        elif rel.endswith("missionControlGateRoutedPackageOutcomeReviewApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/gate-routed-package-outcome-review/record" not in text:
                violations.append({"path": rel, "reason": "missing_gate_routed_package_outcome_review_record_endpoint"})
        elif rel.endswith("missionControlGovernedLaneEntryRecommendationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governed-lane-entry-recommendation/record" not in text:
                violations.append({"path": rel, "reason": "missing_governed_lane_entry_recommendation_record_endpoint"})
        elif rel.endswith("missionControlGovernedLaneReadinessBoardApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/governed-lane-readiness-board/record" not in text:
                violations.append({"path": rel, "reason": "missing_governed_lane_readiness_board_record_endpoint"})
        elif rel.endswith("missionControlHumanLaneAdmissionDecisionApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/human-lane-admission-decision/record" not in text:
                violations.append({"path": rel, "reason": "missing_human_lane_admission_decision_record_endpoint"})
        elif rel.endswith("missionControlGateRoutedLaneEntryHandoffApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/gate-routed-lane-entry-handoff/record" not in text:
                violations.append({"path": rel, "reason": "missing_gate_routed_lane_entry_handoff_record_endpoint"})
        elif rel.endswith("missionControlFrozenGateIntakePreviewApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/frozen-gate-intake-preview/record" not in text:
                violations.append({"path": rel, "reason": "missing_frozen_gate_intake_preview_record_endpoint"})
        elif rel.endswith("missionControlFrozenGateExecutionRequestAdapterApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/frozen-gate-execution-request-adapter/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_frozen_gate_execution_request_adapter_record_endpoint"}
                )
        elif rel.endswith("missionControlGovernedChatCommandInvocationFromHandoffApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/governed-chat-command-invocation-from-handoff/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_chat_command_invocation_from_handoff_record_endpoint"}
                )
            if "/governed-chat-command-invocation-from-handoff/invoke" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_chat_command_invocation_from_handoff_invoke_endpoint"}
                )
        elif rel.endswith("missionControlEndToEndRepoDevelopmentPilotHarnessApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/end-to-end-repo-development-pilot-harness/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_end_to_end_repo_development_pilot_harness_record_endpoint"}
                )
            if "/end-to-end-repo-development-pilot-harness/run" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_end_to_end_repo_development_pilot_harness_run_endpoint"}
                )
        elif rel.endswith("missionControlBoundedMultiAgentDeliveryExecutionApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/bounded-multi-agent-delivery-execution/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_bounded_multi_agent_delivery_execution_record_endpoint"}
                )
            if "/bounded-multi-agent-delivery-execution/run" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_bounded_multi_agent_delivery_execution_run_endpoint"}
                )
        elif rel.endswith("missionControlAgentExecutionQualityThroughputMetricsApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/agent-execution-quality-throughput-metrics/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_agent_execution_quality_throughput_metrics_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlCrossRepositoryMultiAgentDeliveryValidationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/cross-repository-multi-agent-delivery-validation/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_cross_repository_multi_agent_delivery_validation_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlGovernedMergeLifecycleApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/governed-merge-lifecycle/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_merge_lifecycle_record_endpoint"}
                )
            if "/governed-merge-lifecycle/handoff" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_merge_lifecycle_handoff_endpoint"}
                )
        elif rel.endswith("missionControlGovernedDeployLifecycleApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/governed-deploy-lifecycle/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_deploy_lifecycle_record_endpoint"}
                )
            if "/governed-deploy-lifecycle/handoff" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_deploy_lifecycle_handoff_endpoint"}
                )
        elif rel.endswith("missionControlGovernedMonitoringLifecycleApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/governed-monitoring-lifecycle/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_monitoring_lifecycle_record_endpoint"}
                )
            if "/governed-monitoring-lifecycle/escalate" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_monitoring_lifecycle_escalate_endpoint"}
                )
        elif rel.endswith("missionControlGovernedRollbackLifecycleApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/governed-rollback-lifecycle/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_rollback_lifecycle_record_endpoint"}
                )
            if "/governed-rollback-lifecycle/handoff" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_rollback_lifecycle_handoff_endpoint"}
                )
        elif rel.endswith("missionControlRepositoryKnowledgeGraphApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/repository-knowledge-graph/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_repository_knowledge_graph_record_endpoint"}
                )
        elif rel.endswith("missionControlGovernedApplicationGenerationApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/governed-application-generation/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_application_generation_record_endpoint"}
                )
            if "/governed-application-generation/handoff" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_governed_application_generation_handoff_endpoint"}
                )
        elif rel.endswith("missionControlMultiRepositoryEngineeringIntelligenceApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/multi-repository-engineering-intelligence/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_multi_repository_engineering_intelligence_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlCrossRepositoryProductEvolutionIntelligenceApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/cross-repository-product-evolution-intelligence/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_cross_repository_product_evolution_intelligence_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlAutonomousProductStewardshipApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/autonomous-product-stewardship/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_autonomous_product_stewardship_record_endpoint"}
                )
        elif rel.endswith("missionControlAutonomousApplicationLifecycleManagementApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/autonomous-application-lifecycle-management/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_autonomous_application_lifecycle_management_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlAutonomousBusinessOperatingSystemApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/autonomous-business-operating-system/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_autonomous_business_operating_system_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlAutonomousCapabilityRegistryApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/autonomous-capability-registry/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_autonomous_capability_registry_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlMultiTenantPlatformFoundationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/multi-tenant-platform-foundation/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_multi_tenant_platform_foundation_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlTenantOnboardingActivationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/tenant-onboarding-activation/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_tenant_onboarding_activation_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlIdentityAccessHardeningApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/identity-access-hardening/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_identity_access_hardening_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlProviderConnectionExperienceApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/provider-connection-experience/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_provider_connection_experience_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlChannelIntegrationFoundationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/channel-integration-foundation/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_channel_integration_foundation_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlBillingEntitlementsFoundationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/billing-entitlements-foundation/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_billing_entitlements_foundation_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlCustomerAdministrationConsoleApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/customer-administration-console/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_customer_administration_console_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlCustomerUsageAuditPortalApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/customer-usage-audit-portal/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_customer_usage_audit_portal_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlPaymentIntegrationReadinessApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/payment-integration-readiness/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_payment_integration_readiness_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlSaasLaunchReadinessAssessmentApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/saas-launch-readiness-assessment/record" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_saas_launch_readiness_assessment_record_endpoint",
                    }
                )
        elif rel.endswith("missionControlCustomerSupportSuccessFoundationApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/customer-support-success-foundation" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_customer_support_success_foundation_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlPublicProductExperienceApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/public-product-experience" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_public_product_experience_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlLimitedBetaLaunchProgramApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/limited-beta-launch-program" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_limited_beta_launch_program_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlLaunchOperationsCenterApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/launch-operations-center" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_launch_operations_center_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlPublicLaunchReadinessFreezeApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/public-launch-readiness-freeze" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_public_launch_readiness_freeze_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlLaunchDecisionPackageApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/launch-decision-package" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_launch_decision_package_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlPostLaunchOperationsBaselineApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/post-launch-operations-baseline" not in text:
                violations.append(
                    {
                        "path": rel,
                        "reason": "missing_post_launch_operations_baseline_post_endpoint",
                    }
                )
        elif rel.endswith("missionControlPilotosUiTrustReportFreezeApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/pilotos-ui-trust-report-freeze/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_pilotos_ui_trust_report_freeze_record_endpoint"}
                )
        elif rel.endswith("missionControlAtlasTraderTrustReportFreezeApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/atlas-trader-trust-report-freeze/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_atlas_trader_trust_report_freeze_record_endpoint"}
                )
        elif rel.endswith("missionControlNexoraPilotArcOrchestratorApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/nexora-pilot-arc-orchestrator/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_nexora_pilot_arc_orchestrator_record_endpoint"}
                )
            if "/nexora-pilot-arc-orchestrator/run" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_nexora_pilot_arc_orchestrator_run_endpoint"}
                )
        elif rel.endswith("missionControlNexoraTrustReportFreezeApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/nexora-trust-report-freeze/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_nexora_trust_report_freeze_record_endpoint"}
                )
        elif rel.endswith("missionControlRepoPilotReadinessDashboardApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/repo-pilot-readiness-dashboard/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_repo_pilot_readiness_dashboard_record_endpoint"}
                )
        elif rel.endswith("missionControlPilotValidationTrustBoardApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/pilot-validation-trust-board/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_pilot_validation_trust_board_record_endpoint"}
                )
        elif rel.endswith("missionControlIssueIntentAlignmentApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/issue-intent-alignment/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_issue_intent_alignment_record_endpoint"}
                )
        elif rel.endswith("missionControlDogfoodPilotTrustReportFreezeApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/dogfood-pilot-trust-report-freeze/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_dogfood_pilot_trust_report_freeze_record_endpoint"}
                )
        elif rel.endswith("missionControlIndependentRepositoryTrustExpansionApi.ts"):
            if len(posts) != 1:
                violations.append({"path": rel, "reason": f"expected_single_post_found_{len(posts)}"})
            if "/independent-repository-trust-expansion/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_independent_repository_trust_expansion_record_endpoint"}
                )
        elif rel.endswith("missionControlPilotosUiPilotArcOrchestratorApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/pilotos-ui-pilot-arc-orchestrator/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_pilotos_ui_pilot_arc_orchestrator_record_endpoint"}
                )
            if "/pilotos-ui-pilot-arc-orchestrator/run" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_pilotos_ui_pilot_arc_orchestrator_run_endpoint"}
                )
        elif rel.endswith("missionControlAtlasTraderPilotArcOrchestratorApi.ts"):
            if len(posts) != 2:
                violations.append({"path": rel, "reason": f"expected_two_posts_found_{len(posts)}"})
            if "/atlas-trader-pilot-arc-orchestrator/record" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_atlas_trader_pilot_arc_orchestrator_record_endpoint"}
                )
            if "/atlas-trader-pilot-arc-orchestrator/run" not in text:
                violations.append(
                    {"path": rel, "reason": "missing_atlas_trader_pilot_arc_orchestrator_run_endpoint"}
                )
        elif posts:
            violations.append({"path": rel, "reason": f"unexpected_post_in_readonly_client:{len(posts)}"})
    return {
        "ok": len(violations) == 0,
        "scanned": scanned,
        "violations": violations,
    }


def _parse_mc_operator_routes(source: str) -> list[tuple[str, str]]:
    routes: list[tuple[str, str]] = []
    for match in re.finditer(
        r'@router\.(get|post|put|patch|delete)\("([^"]+)"\)',
        source,
        re.IGNORECASE,
    ):
        method = match.group(1).upper()
        path = match.group(2)
        if not path.startswith("/mission-control/"):
            continue
        routes.append((method, path))
    return routes


def review_mission_control_operator_api_surface() -> dict[str, Any]:
    path = _repo_path(MISSION_CONTROL_OPERATOR_API_MODULE)
    if not path.is_file():
        return {"ok": False, "reason": "missing_api_module", "routes": [], "violations": ["api_module_missing"]}
    source = path.read_text(encoding="utf-8")
    routes = _parse_mc_operator_routes(source)
    allowed = {tuple(r) for r in ALLOWED_MC_OPERATOR_HTTP_ROUTES}
    found = set(routes)
    extra = sorted(found - allowed)
    missing = sorted(allowed - found)
    violations: list[str] = []
    if extra:
        violations.extend(f"unexpected_route:{m}:{p}" for m, p in extra)
    if missing:
        violations.extend(f"missing_route:{m}:{p}" for m, p in missing)
    for method, _path in routes:
        if method not in ("GET", "POST"):
            violations.append(f"forbidden_http_method:{method}")
    post_routes = sorted(p for m, p in routes if m == "POST")
    # Keep one machine-readable route allowlist. Duplicating a second POST-only
    # tuple made the freeze review silently stale as governed endpoints evolved.
    allowed_posts = sorted(p for method, p in ALLOWED_MC_OPERATOR_HTTP_ROUTES if method == "POST")
    if post_routes != allowed_posts:
        violations.append(f"post_routes_not_frozen:{post_routes}")
    return {
        "ok": len(violations) == 0,
        "routes": [{"method": m, "path": p} for m, p in routes],
        "violations": violations,
    }


def review_mission_control_ui_freeze() -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.action_safety_review import (
        review_mission_control_ui_action_safety,
    )

    ui = review_frozen_ui_components()
    clients = review_frozen_web_api_clients()
    api = review_mission_control_operator_api_surface()
    safety = review_mission_control_ui_action_safety()
    ok = ui["ok"] and clients["ok"] and api["ok"] and safety.get("ok") is True
    return {
        "ok": ok,
        "schema_version": MISSION_CONTROL_UI_SCHEMA_VERSION,
        "fix": MISSION_CONTROL_UI_FREEZE_FIX,
        "frozen_ui": ui,
        "frozen_web_clients": clients,
        "operator_api": api,
        "action_safety": safety,
        "invariant": "mission_control_operator_console_read_only_plus_governed_approval_only",
    }
