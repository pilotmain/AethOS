# SPDX-License-Identifier: Apache-2.0
"""FIX 129 — Mission Control cross-lane read-only API for web UI."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["mission-control"])


class ApprovalInboxExecuteIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    inbox_id: str = Field(min_length=1, max_length=128)


class GovernanceDeliberationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceCollaborationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    reviewer_name: str = Field(default="", max_length=64)
    reviewer_role: str = Field(default="", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceDoctrineRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernancePolicyInterpretationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceCoherenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceResilienceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceEvolutionRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InstitutionalIdentityRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InstitutionalExternalRelationsRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InstitutionalExistentialRiskRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstitutionalEthicsRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstitutionalAuditRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstitutionalLegitimacyRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstitutionalPluralismRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConstitutionalSynthesisRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MissionPlanningRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MissionPlanningDeliberationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HumanDecisionBoardRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionHandoffCoordinationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BoundedDeliveryWorkPackagesRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkPackageReadinessLaneAdmissionRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MissionAuthorizationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BoundedExecutionParticipationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedTaskExecutionCoordinationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GateRoutedPackageOutcomeReviewRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedLaneEntryRecommendationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedLaneReadinessBoardRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class HumanLaneAdmissionDecisionRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GateRoutedLaneEntryHandoffRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FrozenGateIntakePreviewRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FrozenGateExecutionRequestAdapterRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedChatCommandInvocationFromHandoffRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedChatCommandInvocationFromHandoffInvokeIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)


class EndToEndRepoDevelopmentPilotHarnessRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class EndToEndRepoDevelopmentPilotHarnessRunIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    repo_issue: str | None = Field(default=None, max_length=128)


class RepoPilotReadinessDashboardRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PilotValidationTrustBoardRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IssueIntentAlignmentRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DogfoodPilotTrustReportFreezeRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndependentRepositoryTrustExpansionRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    repository: str = Field(default="", max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PilotosUiPilotArcOrchestratorRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    repo_issue: str = Field(default="", max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class PilotosUiPilotArcOrchestratorRunIn(BaseModel):
    pilot_number: int = Field(ge=1, le=3)
    session_id: str = Field(default="default", max_length=64)


class AtlasTraderPilotArcOrchestratorRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    repo_issue: str = Field(default="", max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AtlasTraderPilotArcOrchestratorRunIn(BaseModel):
    pilot_number: int = Field(ge=1, le=3)
    session_id: str = Field(default="default", max_length=64)


class NexoraPilotArcOrchestratorRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    repo_issue: str = Field(default="", max_length=128)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NexoraPilotArcOrchestratorRunIn(BaseModel):
    pilot_number: int = Field(ge=1, le=3)
    session_id: str = Field(default="default", max_length=64)


class BoundedMultiAgentDeliveryExecutionRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BoundedMultiAgentDeliveryExecutionRunIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    role_id: str = Field(default="", max_length=64)


class AgentExecutionQualityThroughputMetricsRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CrossRepositoryMultiAgentDeliveryValidationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    repository: str | None = Field(default=None, max_length=128)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedMergeLifecycleRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedMergeLifecycleHandoffIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)


class GovernedDeployLifecycleRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedDeployLifecycleHandoffIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)


class GovernedMonitoringLifecycleRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedMonitoringLifecycleEscalateIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)


class GovernedRollbackLifecycleRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedRollbackLifecycleHandoffIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)


class RepositoryKnowledgeGraphRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedApplicationGenerationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=8000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernedApplicationGenerationHandoffIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)


class MultiRepositoryEngineeringIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    repository: str | None = Field(default=None, max_length=128)
    source_repository: str | None = Field(default=None, max_length=128)
    target_repository: str | None = Field(default=None, max_length=128)
    relationship: str | None = Field(default=None, max_length=64)


class CrossRepositoryProductEvolutionIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    repository: str | None = Field(default=None, max_length=128)
    domain: str | None = Field(default=None, max_length=64)
    target_repository: str | None = Field(default=None, max_length=128)
    opportunity_id: str | None = Field(default=None, max_length=128)


class AutonomousProductStewardshipRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    repository: str | None = Field(default=None, max_length=128)
    domain: str | None = Field(default=None, max_length=64)
    opportunity_id: str | None = Field(default=None, max_length=128)


class AutonomousApplicationLifecycleManagementRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    lifecycle_stage: str | None = Field(default=None, max_length=64)
    opportunity_id: str | None = Field(default=None, max_length=128)


class AutonomousBusinessOperatingSystemRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    business_domain: str | None = Field(default=None, max_length=64)
    goal_id: str | None = Field(default=None, max_length=128)
    opportunity_id: str | None = Field(default=None, max_length=128)


class AutonomousCapabilityRegistryRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    capability_id: str | None = Field(default=None, max_length=128)
    capability_domain: str | None = Field(default=None, max_length=64)


class MultiTenantPlatformFoundationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    tenant_domain: str | None = Field(default=None, max_length=64)
    organization_id: str | None = Field(default=None, max_length=128)
    workspace_id: str | None = Field(default=None, max_length=128)
    project_id: str | None = Field(default=None, max_length=128)


class TenantOnboardingActivationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    onboarding_step: str | None = Field(default=None, max_length=64)
    organization_id: str | None = Field(default=None, max_length=128)
    workspace_id: str | None = Field(default=None, max_length=128)
    project_id: str | None = Field(default=None, max_length=128)


class IdentityAccessHardeningRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    organization_id: str | None = Field(default=None, max_length=128)
    user_id: str | None = Field(default=None, max_length=128)


class ProviderConnectionExperienceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    provider: str | None = Field(default=None, max_length=64)


class ChannelIntegrationFoundationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    channel: str | None = Field(default=None, max_length=64)


class BillingEntitlementsFoundationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    plan: str | None = Field(default=None, max_length=64)


class CustomerAdministrationConsoleRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class CustomerUsageAuditPortalRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class PaymentIntegrationReadinessRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    provider: str | None = Field(default=None, max_length=64)


class SaasLaunchReadinessAssessmentRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class CustomerSupportSuccessFoundationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)
    org_id: str | None = Field(default=None, max_length=64)


class PublicProductExperienceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class LimitedBetaLaunchProgramRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)
    cohort_id: str | None = Field(default=None, max_length=64)
    candidate_id: str | None = Field(default=None, max_length=64)


class LaunchOperationsCenterRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class PublicLaunchReadinessFreezeRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class LaunchDecisionPackageRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class PostLaunchOperationsBaselineRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class ContinuousProductImprovementRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class ProductAnalyticsFoundationRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class CustomerFeedbackIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class GrowthAdoptionIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class CustomerJourneyIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class ProductMarketFitIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class CustomerValueRealizationIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class StrategicPortfolioIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class ExecutiveDecisionIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class StrategicPlanningIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class EnterpriseProgramIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class OrganizationalEffectivenessIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class EnterpriseOperatingReviewIntelligenceRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class ExecutiveOperatingSystemDashboardRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    domain: str | None = Field(default=None, max_length=64)


class PilotosUiTrustReportFreezeRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AtlasTraderTrustReportFreezeRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NexoraTrustReportFreezeRecordIn(BaseModel):
    session_id: str = Field(default="default", max_length=64)
    kind: str = Field(min_length=1, max_length=64)
    content: str = Field(min_length=1, max_length=4000)
    author: str = Field(default="operator", max_length=64)
    metadata: dict[str, Any] = Field(default_factory=dict)


@router.get("/mission-control/cross-lane/snapshot")
def mission_control_cross_lane_snapshot_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.mission_control.cross_lane.cross_lane_contract import (
        MUTATION_PERFORMED_FIX_128,
        MISSION_CONTROL_ROUTE_ID,
    )
    from aethos_core.mission_control.cross_lane.snapshot_service import build_mission_control_snapshot

    result = build_mission_control_snapshot(session_id=session_id)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "snapshot_unavailable"},
        )
    return {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_128,
        "route_id": MISSION_CONTROL_ROUTE_ID,
        "detail": result.detail,
        "snapshot": result.snapshot,
    }


@router.get("/mission-control/cross-lane/lane/{lane_id}/drilldown")
def mission_control_lane_drilldown_api(lane_id: str, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.mission_control.cross_lane.lane_drilldown_contract import (
        LANE_DRILLDOWN_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_131,
    )
    from aethos_core.mission_control.cross_lane.lane_drilldown_service import build_lane_drilldown

    result = build_lane_drilldown(session_id=session_id, lane=lane_id)
    if not result.ok:
        raise HTTPException(
            status_code=404,
            detail={"blockers": result.blockers, "lane": lane_id},
        )
    return {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_131,
        "schema_version": LANE_DRILLDOWN_SCHEMA_VERSION,
        "lane": result.lane,
        "session_id": result.session_id,
        "detail": result.detail,
        "sections": result.sections,
    }


@router.get("/mission-control/approval-inbox")
def mission_control_approval_inbox_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.approval_inbox_contract import (
        APPROVAL_EXECUTION_ENABLED_FIX_133,
        MUTATION_PERFORMED_FIX_132,
    )
    from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload

    payload = approval_inbox_payload(session_id=session_id)
    if not payload.get("ok"):
        raise HTTPException(status_code=503, detail=payload)
    payload["mutation_performed"] = MUTATION_PERFORMED_FIX_132
    payload["approval_execution_enabled"] = APPROVAL_EXECUTION_ENABLED_FIX_133
    return payload


@router.post("/mission-control/approval-inbox/execute")
def mission_control_approval_inbox_execute_api(body: ApprovalInboxExecuteIn) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.approval_execution_contract import (
        APPROVAL_EXECUTION_SCHEMA_VERSION,
        CHAT_GOVERNANCE_REQUIRED,
        UI_APPROVAL_ORIGIN,
    )
    from aethos_core.mission_control.approval_inbox.approval_execution_service import execute_governed_ui_approval

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = execute_governed_ui_approval(session_id=sid, inbox_id=body.inbox_id.strip())
    if result.blockers and result.blockers[0] == "inbox_item_not_found":
        raise HTTPException(status_code=404, detail={"blockers": result.blockers})
    return {
        "ok": result.ok,
        "schema_version": APPROVAL_EXECUTION_SCHEMA_VERSION,
        "ui_origin": UI_APPROVAL_ORIGIN,
        "chat_governance_required": CHAT_GOVERNANCE_REQUIRED,
        "session_id": result.session_id,
        "inbox_id": result.inbox_id,
        "gate_id": result.gate_id,
        "chat_intent": result.chat_intent,
        "route_id": result.route_id,
        "reply": result.reply,
        "mutation_performed": result.mutation_performed,
        "audit_id": result.audit_id,
        "detail": result.detail,
        "blockers": result.blockers,
        "outcome": result.outcome,
        "replay_protected": result.replay_protected,
    }


@router.post("/mission-control/approval-inbox/execute-terminal")
def mission_control_approval_inbox_execute_terminal_api(body: ApprovalInboxExecuteIn) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.terminal_approval_execution_service import (
        execute_terminal_preflight_from_inbox,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = execute_terminal_preflight_from_inbox(session_id=sid, inbox_id=body.inbox_id.strip())
    if result.blockers and result.blockers[0] == "inbox_item_not_found":
        raise HTTPException(status_code=404, detail={"blockers": result.blockers})
    return {
        "ok": result.ok,
        "session_id": result.session_id,
        "inbox_id": result.inbox_id,
        "preflight_id": result.preflight_id,
        "execution_status": result.execution_status,
        "output": result.output,
        "exit_code": result.exit_code,
        "subagent_session_keys": result.subagent_session_keys,
        "agent_send_results": result.agent_send_results,
        "audit_id": result.audit_id,
        "detail": result.detail,
        "blockers": result.blockers,
    }


@router.post("/mission-control/approval-inbox/execute-mutation")
def mission_control_approval_inbox_execute_mutation_api(body: ApprovalInboxExecuteIn) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.mutation_approval_execution_service import (
        execute_mutation_preflight_from_inbox,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = execute_mutation_preflight_from_inbox(session_id=sid, inbox_id=body.inbox_id.strip())
    if result.blockers and result.blockers[0] == "inbox_item_not_found":
        raise HTTPException(status_code=404, detail={"blockers": result.blockers})
    return {
        "ok": result.ok,
        "session_id": result.session_id,
        "inbox_id": result.inbox_id,
        "preflight_job_id": result.preflight_job_id,
        "execution_job_id": result.execution_job_id,
        "audit_id": result.audit_id,
        "detail": result.detail,
        "blockers": result.blockers,
        "replay_protected": result.replay_protected,
    }


@router.post("/mission-control/approval-inbox/execute-serve")
def mission_control_approval_inbox_execute_serve_api(body: ApprovalInboxExecuteIn) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.serve_approval_execution_service import (
        execute_serve_preflight_from_inbox,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = execute_serve_preflight_from_inbox(session_id=sid, inbox_id=body.inbox_id.strip())
    if result.blockers and result.blockers[0] == "inbox_item_not_found":
        raise HTTPException(status_code=404, detail={"blockers": result.blockers})
    return {
        "ok": result.ok,
        "session_id": result.session_id,
        "inbox_id": result.inbox_id,
        "serve_request_id": result.serve_request_id,
        "model_id": result.model_id,
        "endpoint": result.endpoint,
        "catalog_id": result.catalog_id,
        "execution_status": result.execution_status,
        "audit_id": result.audit_id,
        "detail": result.detail,
        "blockers": result.blockers,
    }


@router.post("/mission-control/approval-inbox/execute-operational-deployment")
def mission_control_approval_inbox_execute_operational_deployment_api(body: ApprovalInboxExecuteIn) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.operational_deployment_approval_execution_service import (
        execute_operational_deployment_approval_from_inbox,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = execute_operational_deployment_approval_from_inbox(session_id=sid, inbox_id=body.inbox_id.strip())
    if result.blockers and result.blockers[0] == "inbox_item_not_found":
        raise HTTPException(status_code=404, detail={"blockers": result.blockers})
    return {
        "ok": result.ok,
        "session_id": result.session_id,
        "inbox_id": result.inbox_id,
        "job_id": result.job_id,
        "preflight_id": result.preflight_id,
        "orchestration_job_id": result.orchestration_job_id,
        "audit_id": result.audit_id,
        "detail": result.detail,
        "reply": result.reply,
        "route_id": result.route_id,
        "blockers": result.blockers,
        "replay_protected": result.replay_protected,
    }


@router.post("/mission-control/approval-inbox/reject-operational-deployment")
def mission_control_approval_inbox_reject_operational_deployment_api(body: ApprovalInboxExecuteIn) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.operational_deployment_approval_execution_service import (
        reject_operational_deployment_approval_from_inbox,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = reject_operational_deployment_approval_from_inbox(session_id=sid, inbox_id=body.inbox_id.strip())
    if result.blockers and result.blockers[0] == "inbox_item_not_found":
        raise HTTPException(status_code=404, detail={"blockers": result.blockers})
    return {
        "ok": result.ok,
        "session_id": result.session_id,
        "inbox_id": result.inbox_id,
        "job_id": result.job_id,
        "audit_id": result.audit_id,
        "detail": result.detail,
        "route_id": result.route_id,
        "blockers": result.blockers,
    }


@router.get("/mission-control/approval-inbox/audit")
def mission_control_approval_audit_api(session_id: str = "default", limit: int = 40) -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.approval_audit_service import audit_history_payload

    sid = (session_id or "default").strip()[:64] or "default"
    payload = audit_history_payload(session_id=sid, limit=min(limit, 100))
    payload["read_only"] = True
    return payload


@router.get("/mission-control/action-safety/review")
def mission_control_action_safety_review_api() -> dict[str, Any]:
    from aethos_core.mission_control.approval_inbox.action_safety_review import review_mission_control_ui_action_safety

    return review_mission_control_ui_action_safety()


@router.get("/mission-control/evidence-bundle")
def mission_control_evidence_bundle_api(
    session_id: str = "default",
    job_id: str | None = None,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.evidence_bundle.evidence_bundle_contract import (
        EVIDENCE_BUNDLE_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_136,
    )
    from aethos_core.mission_control.evidence_bundle.evidence_bundle_renderer import render_evidence_bundle_markdown
    from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle

    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_evidence_bundle(session_id=sid, job_id=focus)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "evidence_bundle_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_136,
        "schema_version": EVIDENCE_BUNDLE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "job_id": focus,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["bundle"] = result.bundle
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_evidence_bundle_markdown(result.bundle)
    return payload


@router.get("/mission-control/job-replay")
def mission_control_job_replay_api(
    session_id: str = "default",
    job_id: str | None = None,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.job_replay.job_replay_contract import (
        JOB_REPLAY_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_137,
    )
    from aethos_core.mission_control.job_replay.job_replay_renderer import render_job_replay_summary
    from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay

    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "summary", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_job_replay(session_id=sid, job_id=focus)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "job_replay_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_137,
        "schema_version": JOB_REPLAY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "job_id": focus,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["replay"] = result.replay
    if fmt in {"summary", "both"}:
        payload["summary_markdown"] = render_job_replay_summary(result.replay)
    return payload


@router.get("/mission-control/job-replay/resolve")
def mission_control_job_replay_resolve_api(
    session_id: str = "default",
    link: str = "",
    link_key: str = "",
    link_ref: str = "",
    job_id: str | None = None,
) -> dict[str, Any]:
    from aethos_core.mission_control.job_replay.job_replay_service import resolve_job_replay_link

    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None
    needle = (link or link_key or link_ref or "").strip()
    if not needle:
        raise HTTPException(status_code=400, detail={"blockers": ["missing_link"]})

    resolved = resolve_job_replay_link(session_id=sid, link=needle, job_id=focus)
    if not resolved.get("ok"):
        raise HTTPException(status_code=404, detail=resolved)
    return resolved


@router.get("/mission-control/rerun-plan")
def mission_control_rerun_plan_api(
    session_id: str = "default",
    job_id: str | None = None,
    from_step: int | None = None,
    link_key: str | None = None,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.rerun_planning.rerun_plan_contract import (
        MUTATION_PERFORMED_FIX_138,
        RERUN_EXECUTION_ENABLED_FIX_138,
        RERUN_PLAN_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.rerun_planning.rerun_plan_renderer import render_governed_rerun_plan
    from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan

    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None
    link = (link_key or "").strip() or None
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_rerun_plan(
        session_id=sid,
        job_id=focus,
        from_step=from_step,
        link_key=link,
    )
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "rerun_plan_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_138,
        "rerun_execution_enabled": RERUN_EXECUTION_ENABLED_FIX_138,
        "schema_version": RERUN_PLAN_SCHEMA_VERSION,
        "session_id": result.session_id,
        "job_id": focus,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["plan"] = result.plan
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_rerun_plan(result.plan)
    return payload


@router.get("/mission-control/operational-memory")
def mission_control_operational_memory_api(
    session_id: str = "default",
    job_id: str | None = None,
    include_replay: bool = True,
    include_rerun_plan: bool = True,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.operational_memory.operational_memory_contract import (
        AUTONOMOUS_ADAPTATION_ENABLED_FIX_139,
        MUTATION_PERFORMED_FIX_139,
        OPERATIONAL_MEMORY_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.operational_memory.operational_memory_renderer import (
        render_operational_memory_graph,
    )
    from aethos_core.mission_control.operational_memory.operational_memory_service import (
        build_operational_memory_graph,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_operational_memory_graph(
        session_id=sid,
        job_id=focus,
        include_replay=include_replay,
        include_rerun_plan=include_rerun_plan,
    )
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "operational_memory_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_139,
        "autonomous_adaptation_enabled": AUTONOMOUS_ADAPTATION_ENABLED_FIX_139,
        "schema_version": OPERATIONAL_MEMORY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "job_id": focus,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["graph"] = result.graph
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_operational_memory_graph(result.graph)
    return payload


@router.get("/mission-control/operational-memory/cross-session")
def mission_control_cross_session_memory_api(
    session_id: str = "default",
    ingest_current: bool = True,
    limit: int = 200,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_contract import (
        AUTONOMOUS_ADAPTATION_ENABLED_FIX_140,
        AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140,
        CROSS_SESSION_MEMORY_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_140,
    )
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_renderer import (
        render_cross_session_operational_memory,
    )
    from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
        build_cross_session_operational_memory,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_cross_session_operational_memory(
        session_id=sid,
        ingest_current=ingest_current,
        limit=max(1, min(int(limit), 500)),
    )
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "cross_session_memory_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_140,
        "autonomous_adaptation_enabled": AUTONOMOUS_ADAPTATION_ENABLED_FIX_140,
        "autonomous_optimization_enabled": AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140,
        "schema_version": CROSS_SESSION_MEMORY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["memory"] = result.memory
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_cross_session_operational_memory(result.memory)
    return payload


@router.get("/mission-control/knowledge-spaces/search")
def mission_control_knowledge_spaces_search_api(
    session_id: str = "default",
    q: str = "",
    query: str = "",
    space_id: str | None = None,
    category: str | None = None,
    ingest_current: bool = True,
    limit: int = 20,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_contract import (
        AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141,
        AUTONOMOUS_ACTION_ENABLED_FIX_141,
        KNOWLEDGE_SPACES_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_141,
    )
    from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_renderer import (
        render_knowledge_spaces_search,
    )
    from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_service import (
        search_mission_knowledge_spaces,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    needle = (q or query or "").strip()
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})
    if not needle:
        raise HTTPException(status_code=400, detail={"blockers": ["missing_query"]})

    result = search_mission_knowledge_spaces(
        session_id=sid,
        query=needle,
        space_id=(space_id or "").strip() or None,
        category=(category or "").strip() or None,
        ingest_current=ingest_current,
        limit=max(1, min(int(limit), 50)),
    )
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "knowledge_spaces_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_141,
        "autonomous_action_enabled": AUTONOMOUS_ACTION_ENABLED_FIX_141,
        "automatic_mutation_planning_enabled": AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141,
        "schema_version": KNOWLEDGE_SPACES_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["search"] = result.payload
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_knowledge_spaces_search(result.payload)
    return payload


@router.get("/mission-control/operator-guidance")
def mission_control_operator_guidance_api(
    session_id: str = "default",
    focus: str | None = None,
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.operator_guidance.operator_guidance_contract import (
        AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_142,
        OPERATOR_GUIDANCE_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_142,
    )
    from aethos_core.mission_control.operator_guidance.operator_guidance_renderer import render_operator_guidance
    from aethos_core.mission_control.operator_guidance.operator_guidance_service import (
        build_operator_contextual_guidance,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_operator_contextual_guidance(
        session_id=sid,
        focus=(focus or "").strip() or None,
    )
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "operator_guidance_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_142,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_142,
        "automatic_mutation_planning_enabled": AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142,
        "schema_version": OPERATOR_GUIDANCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["guidance"] = result.guidance
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_operator_guidance(result.guidance)
    return payload


@router.get("/mission-control/governance-insights")
def mission_control_governance_insights_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_insights.governance_insights_contract import (
        AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143,
        GOVERNANCE_INSIGHTS_SCHEMA_VERSION,
        GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143,
        MUTATION_PERFORMED_FIX_143,
        POLICY_AUTO_TUNING_ENABLED_FIX_143,
    )
    from aethos_core.mission_control.governance_insights.governance_insights_renderer import (
        render_governance_insights,
    )
    from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_insights(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_insights_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_143,
        "policy_auto_tuning_enabled": POLICY_AUTO_TUNING_ENABLED_FIX_143,
        "governance_self_modification_enabled": GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143,
        "autonomous_optimization_enabled": AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143,
        "schema_version": GOVERNANCE_INSIGHTS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["insights"] = result.insights
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_insights(result.insights)
    return payload


@router.get("/mission-control/governance-simulation")
def mission_control_governance_simulation_api(
    session_id: str = "default",
    scenarios: str = "all",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_simulation.governance_simulation_contract import (
        AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144,
        AUTO_POLICY_UPDATE_ENABLED_FIX_144,
        DEFAULT_SCENARIO_IDS,
        GOVERNANCE_SIMULATION_SCHEMA_VERSION,
        LIVE_POLICY_MUTATION_ENABLED_FIX_144,
        MUTATION_PERFORMED_FIX_144,
    )
    from aethos_core.mission_control.governance_simulation.governance_simulation_renderer import (
        render_governance_simulation,
    )
    from aethos_core.mission_control.governance_simulation.governance_simulation_service import (
        run_governance_simulation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    raw = (scenarios or "all").strip().lower()
    scenario_ids = list(DEFAULT_SCENARIO_IDS) if raw in {"", "all"} else [s.strip() for s in raw.split(",") if s.strip()]

    result = run_governance_simulation(session_id=sid, scenario_ids=scenario_ids)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_simulation_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "simulation_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_144,
        "live_policy_mutation_enabled": LIVE_POLICY_MUTATION_ENABLED_FIX_144,
        "auto_policy_update_enabled": AUTO_POLICY_UPDATE_ENABLED_FIX_144,
        "automatic_governance_tuning_enabled": AUTOMATIC_GOVERNANCE_TUNING_ENABLED_FIX_144,
        "schema_version": GOVERNANCE_SIMULATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["simulation"] = result.simulation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_simulation(result.simulation)
    return payload


@router.get("/mission-control/mission-strategy")
def mission_control_mission_strategy_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_strategy.mission_strategy_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_145,
        AUTONOMOUS_PLANNING_ENABLED_FIX_145,
        AUTONOMOUS_REPRIORITIZATION_ENABLED_FIX_145,
        MISSION_STRATEGY_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_145,
        ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145,
    )
    from aethos_core.mission_control.mission_strategy.mission_strategy_renderer import render_mission_strategy
    from aethos_core.mission_control.mission_strategy.mission_strategy_service import build_mission_strategy

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_mission_strategy(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "mission_strategy_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_145,
        "autonomous_planning_enabled": AUTONOMOUS_PLANNING_ENABLED_FIX_145,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_145,
        "autonomous_reprioritization_enabled": AUTONOMOUS_REPRIORITIZATION_ENABLED_FIX_145,
        "organizational_self_direction_enabled": ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145,
        "schema_version": MISSION_STRATEGY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["strategy"] = result.strategy
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_mission_strategy(result.strategy)
    return payload


@router.get("/mission-control/mission-orchestration")
def mission_control_mission_orchestration_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_orchestration.mission_orchestration_contract import (
        AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146,
        AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146,
        AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146,
        AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146,
        MISSION_ORCHESTRATION_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_146,
    )
    from aethos_core.mission_control.mission_orchestration.mission_orchestration_renderer import (
        render_mission_orchestration,
    )
    from aethos_core.mission_control.mission_orchestration.mission_orchestration_service import (
        build_mission_orchestration,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_mission_orchestration(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "mission_orchestration_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_146,
        "autonomous_orchestration_enabled": AUTONOMOUS_ORCHESTRATION_ENABLED_FIX_146,
        "autonomous_sequencing_execution_enabled": AUTONOMOUS_SEQUENCING_EXECUTION_ENABLED_FIX_146,
        "autonomous_approval_batching_enabled": AUTONOMOUS_APPROVAL_BATCHING_ENABLED_FIX_146,
        "autonomous_promotion_deploy_enabled": AUTONOMOUS_PROMOTION_DEPLOY_ENABLED_FIX_146,
        "schema_version": MISSION_ORCHESTRATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["orchestration"] = result.orchestration
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_mission_orchestration(result.orchestration)
    return payload


@router.get("/mission-control/mission-readiness-review")
def mission_control_mission_readiness_review_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_contract import (
        AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147,
        AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147,
        EXECUTION_AUTHORITY_DELEGATED_FIX_147,
        HUMAN_REVIEW_REQUIRED_FIX_147,
        MISSION_READINESS_REVIEW_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_147,
    )
    from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_renderer import (
        render_mission_readiness_review,
    )
    from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
        build_mission_readiness_review,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_mission_readiness_review(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "mission_readiness_review_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_147,
        "human_review_required": HUMAN_REVIEW_REQUIRED_FIX_147,
        "autonomous_go_no_go_execution_enabled": AUTONOMOUS_GO_NO_GO_EXECUTION_ENABLED_FIX_147,
        "autonomous_readiness_decision_enabled": AUTONOMOUS_READINESS_DECISION_ENABLED_FIX_147,
        "execution_authority_delegated": EXECUTION_AUTHORITY_DELEGATED_FIX_147,
        "schema_version": MISSION_READINESS_REVIEW_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["review"] = result.review
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_mission_readiness_review(result.review)
    return payload


@router.get("/mission-control/governance-deliberation")
def mission_control_governance_deliberation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_contract import (
        AUTOMATIC_APPROVAL_ENABLED_FIX_148,
        AUTOMATIC_REJECTION_ENABLED_FIX_148,
        AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148,
        DELEGATED_AUTHORITY_ENABLED_FIX_148,
        GOVERNANCE_DELIBERATION_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_148,
        MUTATION_PERFORMED_FIX_148,
    )
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_renderer import (
        render_governance_deliberation,
    )
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
        build_governance_deliberation_workspace,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_deliberation_workspace(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_deliberation_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_148,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_148,
        "automatic_approval_enabled": AUTOMATIC_APPROVAL_ENABLED_FIX_148,
        "automatic_rejection_enabled": AUTOMATIC_REJECTION_ENABLED_FIX_148,
        "autonomous_policy_evolution_enabled": AUTONOMOUS_POLICY_EVOLUTION_ENABLED_FIX_148,
        "delegated_authority_enabled": DELEGATED_AUTHORITY_ENABLED_FIX_148,
        "schema_version": GOVERNANCE_DELIBERATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["workspace"] = result.workspace
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_deliberation(result.workspace)
    return payload


@router.post("/mission-control/governance-deliberation/record")
def mission_control_governance_deliberation_record_api(
    body: GovernanceDeliberationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_contract import (
        AUTOMATIC_APPROVAL_ENABLED_FIX_148,
        AUTOMATIC_REJECTION_ENABLED_FIX_148,
        GOVERNANCE_DELIBERATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_148,
        MUTATION_PERFORMED_FIX_148,
    )
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
        append_governance_deliberation_record,
    )
    from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
        build_mission_readiness_review,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    readiness = build_mission_readiness_review(session_id=sid)
    review = readiness.review if readiness.ok else {}
    record, blockers = append_governance_deliberation_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(review.get("plan_id") or "") or None,
        correlation_id=str(review.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_DELIBERATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_148,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_148,
        "automatic_approval_performed": AUTOMATIC_APPROVAL_ENABLED_FIX_148,
        "automatic_rejection_performed": AUTOMATIC_REJECTION_ENABLED_FIX_148,
        "deliberation_memory_only": True,
        "detail": "Deliberation record persisted (institutional governance memory only).",
    }


@router.get("/mission-control/governance-collaboration")
def mission_control_governance_collaboration_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_collaboration.governance_collaboration_contract import (
        AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149,
        AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
        AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149,
        DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149,
        GOVERNANCE_COLLABORATION_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_149,
        MUTATION_PERFORMED_FIX_149,
    )
    from aethos_core.mission_control.governance_collaboration.governance_collaboration_renderer import (
        render_governance_collaboration,
    )
    from aethos_core.mission_control.governance_collaboration.governance_collaboration_service import (
        build_governance_collaboration_workspace,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_collaboration_workspace(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_collaboration_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_149,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_149,
        "delegated_execution_authority_enabled": DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_149,
        "automatic_quorum_approval_enabled": AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
        "automatic_merge_deploy_enabled": AUTOMATIC_MERGE_DEPLOY_ENABLED_FIX_149,
        "autonomous_organizational_decisions_enabled": AUTONOMOUS_ORGANIZATIONAL_DECISIONS_ENABLED_FIX_149,
        "schema_version": GOVERNANCE_COLLABORATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["collaboration"] = result.collaboration
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_collaboration(result.collaboration)
    return payload


@router.post("/mission-control/governance-collaboration/record")
def mission_control_governance_collaboration_record_api(
    body: GovernanceCollaborationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_collaboration.governance_collaboration_contract import (
        AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
        GOVERNANCE_COLLABORATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_149,
        MUTATION_PERFORMED_FIX_149,
    )
    from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
        append_governance_collaboration_record,
    )
    from aethos_core.mission_control.governance_deliberation.governance_deliberation_service import (
        build_governance_deliberation_workspace,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    deliberation = build_governance_deliberation_workspace(session_id=sid)
    workspace = deliberation.workspace if deliberation.ok else {}
    record, blockers = append_governance_collaboration_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        reviewer_name=body.reviewer_name.strip(),
        reviewer_role=body.reviewer_role.strip(),
        plan_id=str(workspace.get("plan_id") or "") or None,
        correlation_id=str(workspace.get("correlation_id") or "") or None,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_COLLABORATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_149,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_149,
        "automatic_quorum_approval_performed": AUTOMATIC_QUORUM_APPROVAL_ENABLED_FIX_149,
        "collaboration_memory_only": True,
        "detail": "Collaboration record persisted (institutional continuity only).",
    }


@router.get("/mission-control/governance-role-architecture")
def mission_control_governance_role_architecture_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_contract import (
        AUTOMATIC_APPROVAL_ENABLED_FIX_150,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150,
        AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150,
        DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150,
        GOVERNANCE_MUTATION_PERFORMED_FIX_150,
        GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_150,
    )
    from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_renderer import (
        render_governance_role_architecture,
    )
    from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
        build_governance_role_architecture,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_role_architecture(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_role_architecture_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_150,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_150,
        "delegated_execution_authority_enabled": DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150,
        "automatic_approval_enabled": AUTOMATIC_APPROVAL_ENABLED_FIX_150,
        "autonomous_role_elevation_enabled": AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150,
        "schema_version": GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["architecture"] = result.architecture
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_role_architecture(result.architecture)
    return payload


@router.get("/mission-control/governance-doctrine")
def mission_control_governance_doctrine_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
        AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151,
        GOVERNANCE_DOCTRINE_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_151,
        MUTATION_PERFORMED_FIX_151,
        SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151,
    )
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_renderer import render_governance_doctrine
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_doctrine(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_doctrine_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_151,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_151,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
        "autonomous_doctrine_evolution_enabled": AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151,
        "self_modifying_governance_enabled": SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151,
        "schema_version": GOVERNANCE_DOCTRINE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["doctrine"] = result.doctrine
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_doctrine(result.doctrine)
    return payload


@router.post("/mission-control/governance-doctrine/record")
def mission_control_governance_doctrine_record_api(
    body: GovernanceDoctrineRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_contract import (
        AMENDMENT_PROPOSAL_EXECUTABLE,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
        GOVERNANCE_DOCTRINE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_151,
        MUTATION_PERFORMED_FIX_151,
    )
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import append_governance_doctrine_record
    from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
        build_governance_role_architecture,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    architecture = build_governance_role_architecture(session_id=sid)
    arch = architecture.architecture if architecture.ok else {}
    record, blockers = append_governance_doctrine_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(arch.get("plan_id") or "") or None,
        correlation_id=str(arch.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_DOCTRINE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_151,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_151,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
        "executable": AMENDMENT_PROPOSAL_EXECUTABLE,
        "doctrine_memory_only": True,
        "detail": "Doctrine record persisted (amendment proposals only).",
    }


@router.get("/mission-control/governance-policy-interpretation")
def mission_control_governance_policy_interpretation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_contract import (
        AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
        AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152,
        GOVERNANCE_MUTATION_PERFORMED_FIX_152,
        GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_152,
    )
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_renderer import (
        render_governance_policy_interpretation,
    )
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
        build_governance_policy_interpretation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_policy_interpretation(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "governance_policy_interpretation_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_152,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_152,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
        "automatic_doctrine_enforcement_enabled": AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152,
        "autonomous_governance_rulings_enabled": AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152,
        "schema_version": GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["interpretation"] = result.interpretation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_policy_interpretation(result.interpretation)
    return payload


@router.post("/mission-control/governance-policy-interpretation/record")
def mission_control_governance_policy_interpretation_record_api(
    body: GovernancePolicyInterpretationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
        GOVERNANCE_MUTATION_PERFORMED_FIX_152,
        GOVERNANCE_POLICY_INTERPRETATION_RECORD_SCHEMA_VERSION,
        INTERPRETATION_EXECUTABLE,
        MUTATION_PERFORMED_FIX_152,
    )
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
        append_governance_policy_interpretation_record,
    )
    from aethos_core.mission_control.governance_doctrine.governance_doctrine_service import build_governance_doctrine

    sid = (body.session_id or "default").strip()[:64] or "default"
    doctrine = build_governance_doctrine(session_id=sid)
    doc = doctrine.doctrine if doctrine.ok else {}
    record, blockers = append_governance_policy_interpretation_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(doc.get("plan_id") or "") or None,
        correlation_id=str(doc.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_POLICY_INTERPRETATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_152,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_152,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152,
        "executable": INTERPRETATION_EXECUTABLE,
        "interpretation_memory_only": True,
        "detail": "Interpretation record persisted (assistance only — no enforcement).",
    }


@router.get("/mission-control/governance-coherence")
def mission_control_governance_coherence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_coherence.governance_coherence_contract import (
        AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
        AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153,
        CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153,
        GOVERNANCE_COHERENCE_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_153,
        MUTATION_PERFORMED_FIX_153,
        SELF_HEALING_GOVERNANCE_ENABLED_FIX_153,
    )
    from aethos_core.mission_control.governance_coherence.governance_coherence_renderer import (
        render_governance_coherence,
    )
    from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_coherence(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_coherence_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_153,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_153,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
        "automatic_doctrine_enforcement_enabled": AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153,
        "autonomous_governance_correction_enabled": AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153,
        "self_healing_governance_enabled": SELF_HEALING_GOVERNANCE_ENABLED_FIX_153,
        "constitutional_override_authority_enabled": CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153,
        "schema_version": GOVERNANCE_COHERENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["coherence"] = result.coherence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_coherence(result.coherence)
    return payload


@router.post("/mission-control/governance-coherence/record")
def mission_control_governance_coherence_record_api(
    body: GovernanceCoherenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_coherence.governance_coherence_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
        COHERENCE_RECOMMENDATION_EXECUTABLE,
        GOVERNANCE_COHERENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_153,
        MUTATION_PERFORMED_FIX_153,
    )
    from aethos_core.mission_control.governance_coherence.governance_coherence_store import (
        append_governance_coherence_record,
    )
    from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
        build_governance_policy_interpretation,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    interpretation = build_governance_policy_interpretation(session_id=sid)
    interp = interpretation.interpretation if interpretation.ok else {}
    record, blockers = append_governance_coherence_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(interp.get("plan_id") or "") or None,
        correlation_id=str(interp.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_COHERENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_153,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_153,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153,
        "executable": COHERENCE_RECOMMENDATION_EXECUTABLE,
        "coherence_memory_only": True,
        "detail": "Coherence record persisted (recommendation-only — no correction).",
    }


@router.get("/mission-control/governance-resilience")
def mission_control_governance_resilience_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_resilience.governance_resilience_contract import (
        AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
        AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154,
        GOVERNANCE_MUTATION_PERFORMED_FIX_154,
        GOVERNANCE_RESILIENCE_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_154,
        OVERRIDE_AUTHORITY_ENABLED_FIX_154,
        SELF_HEALING_GOVERNANCE_ENABLED_FIX_154,
    )
    from aethos_core.mission_control.governance_resilience.governance_resilience_renderer import (
        render_governance_resilience,
    )
    from aethos_core.mission_control.governance_resilience.governance_resilience_service import (
        build_governance_resilience,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_resilience(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_resilience_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "simulation_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_154,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_154,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
        "automatic_governance_adaptation_enabled": AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154,
        "autonomous_resilience_correction_enabled": AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154,
        "self_healing_governance_enabled": SELF_HEALING_GOVERNANCE_ENABLED_FIX_154,
        "override_authority_enabled": OVERRIDE_AUTHORITY_ENABLED_FIX_154,
        "schema_version": GOVERNANCE_RESILIENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["resilience"] = result.resilience
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_resilience(result.resilience)
    return payload


@router.post("/mission-control/governance-resilience/record")
def mission_control_governance_resilience_record_api(
    body: GovernanceResilienceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_resilience.governance_resilience_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
        GOVERNANCE_MUTATION_PERFORMED_FIX_154,
        GOVERNANCE_RESILIENCE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_154,
        RESILIENCE_SIMULATION_EXECUTABLE,
    )
    from aethos_core.mission_control.governance_resilience.governance_resilience_store import (
        append_governance_resilience_record,
    )
    from aethos_core.mission_control.governance_coherence.governance_coherence_service import build_governance_coherence

    sid = (body.session_id or "default").strip()[:64] or "default"
    coherence = build_governance_coherence(session_id=sid)
    coh = coherence.coherence if coherence.ok else {}
    record, blockers = append_governance_resilience_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(coh.get("plan_id") or "") or None,
        correlation_id=str(coh.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_RESILIENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_154,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_154,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154,
        "executable": RESILIENCE_SIMULATION_EXECUTABLE,
        "simulation_only": True,
        "resilience_memory_only": True,
        "detail": "Resilience record persisted (simulation-only — no adaptation).",
    }


@router.get("/mission-control/governance-evolution")
def mission_control_governance_evolution_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_evolution.governance_evolution_contract import (
        AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
        AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155,
        GOVERNANCE_EVOLUTION_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_155,
        MUTATION_PERFORMED_FIX_155,
        POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155,
        SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155,
    )
    from aethos_core.mission_control.governance_evolution.governance_evolution_renderer import (
        render_governance_evolution,
    )
    from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governance_evolution(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "governance_evolution_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_155,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_155,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
        "autonomous_governance_evolution_enabled": AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155,
        "self_directed_institutional_transformation_enabled": SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155,
        "automatic_doctrine_migration_enabled": AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155,
        "policy_mutation_authority_enabled": POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155,
        "schema_version": GOVERNANCE_EVOLUTION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["evolution"] = result.evolution
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governance_evolution(result.evolution)
    return payload


@router.post("/mission-control/governance-evolution/record")
def mission_control_governance_evolution_record_api(
    body: GovernanceEvolutionRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_evolution.governance_evolution_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
        EVOLUTION_RECOMMENDATION_EXECUTABLE,
        GOVERNANCE_EVOLUTION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_155,
        MUTATION_PERFORMED_FIX_155,
    )
    from aethos_core.mission_control.governance_evolution.governance_evolution_store import (
        append_governance_evolution_record,
    )
    from aethos_core.mission_control.governance_resilience.governance_resilience_service import build_governance_resilience

    sid = (body.session_id or "default").strip()[:64] or "default"
    resilience = build_governance_resilience(session_id=sid)
    res = resilience.resilience if resilience.ok else {}
    record, blockers = append_governance_evolution_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(res.get("plan_id") or "") or None,
        correlation_id=str(res.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNANCE_EVOLUTION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_155,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_155,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155,
        "executable": EVOLUTION_RECOMMENDATION_EXECUTABLE,
        "evolution_memory_only": True,
        "detail": "Evolution record persisted (recommendation-only — no migration).",
    }


@router.get("/mission-control/institutional-identity")
def mission_control_institutional_identity_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.institutional_identity.institutional_identity_contract import (
        AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
        AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156,
        GOVERNANCE_MUTATION_PERFORMED_FIX_156,
        GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156,
        INSTITUTIONAL_IDENTITY_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_156,
        SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156,
    )
    from aethos_core.mission_control.institutional_identity.institutional_identity_renderer import (
        render_institutional_identity,
    )
    from aethos_core.mission_control.institutional_identity.institutional_identity_service import (
        build_institutional_identity,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_institutional_identity(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "institutional_identity_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_156,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_156,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
        "autonomous_institutional_redirection_enabled": AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156,
        "self_authored_mission_changes_enabled": SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156,
        "automatic_constitutional_rewriting_enabled": AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156,
        "governance_sovereignty_delegated": GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156,
        "schema_version": INSTITUTIONAL_IDENTITY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["identity"] = result.identity
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_institutional_identity(result.identity)
    return payload


@router.post("/mission-control/institutional-identity/record")
def mission_control_institutional_identity_record_api(
    body: InstitutionalIdentityRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governance_evolution.governance_evolution_service import build_governance_evolution
    from aethos_core.mission_control.institutional_identity.institutional_identity_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
        GOVERNANCE_MUTATION_PERFORMED_FIX_156,
        IDENTITY_RECOMMENDATION_EXECUTABLE,
        INSTITUTIONAL_IDENTITY_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_156,
    )
    from aethos_core.mission_control.institutional_identity.institutional_identity_store import (
        append_institutional_identity_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    evolution = build_governance_evolution(session_id=sid)
    evo = evolution.evolution if evolution.ok else {}
    record, blockers = append_institutional_identity_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(evo.get("plan_id") or "") or None,
        correlation_id=str(evo.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": INSTITUTIONAL_IDENTITY_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_156,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_156,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156,
        "executable": IDENTITY_RECOMMENDATION_EXECUTABLE,
        "identity_memory_only": True,
        "detail": "Identity record persisted (recommendation-only — no redirection).",
    }


@router.get("/mission-control/institutional-external-relations")
def mission_control_institutional_external_relations_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
        AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157,
        AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157,
        GOVERNANCE_MUTATION_PERFORMED_FIX_157,
        INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_157,
        SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157,
        SOVEREIGNTY_DELEGATION_ENABLED_FIX_157,
    )
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_renderer import (
        render_institutional_external_relations,
    )
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
        build_institutional_external_relations,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_institutional_external_relations(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "institutional_external_relations_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_157,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_157,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
        "autonomous_external_negotiation_enabled": AUTONOMOUS_EXTERNAL_NEGOTIATION_ENABLED_FIX_157,
        "autonomous_provider_alignment_enabled": AUTONOMOUS_PROVIDER_ALIGNMENT_ENABLED_FIX_157,
        "self_directed_institutional_diplomacy_enabled": SELF_DIRECTED_INSTITUTIONAL_DIPLOMACY_ENABLED_FIX_157,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_157,
        "schema_version": INSTITUTIONAL_EXTERNAL_RELATIONS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["external_relations"] = result.external_relations
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_institutional_external_relations(result.external_relations)
    return payload


@router.post("/mission-control/institutional-external-relations/record")
def mission_control_institutional_external_relations_record_api(
    body: InstitutionalExternalRelationsRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
        EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
        GOVERNANCE_MUTATION_PERFORMED_FIX_157,
        INSTITUTIONAL_EXTERNAL_RELATIONS_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_157,
    )
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_store import (
        append_institutional_external_relations_record,
    )
    from aethos_core.mission_control.institutional_identity.institutional_identity_service import build_institutional_identity

    sid = (body.session_id or "default").strip()[:64] or "default"
    identity = build_institutional_identity(session_id=sid)
    ident = identity.identity if identity.ok else {}
    record, blockers = append_institutional_external_relations_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ident.get("plan_id") or "") or None,
        correlation_id=str(ident.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": INSTITUTIONAL_EXTERNAL_RELATIONS_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_157,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_157,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_157,
        "executable": EXTERNAL_RELATIONS_RECOMMENDATION_EXECUTABLE,
        "external_relations_memory_only": True,
        "detail": "External relations record persisted (recommendation-only — no negotiation).",
    }


@router.get("/mission-control/institutional-existential-risk")
def mission_control_institutional_existential_risk_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
        AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158,
        AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158,
        CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158,
        GOVERNANCE_MUTATION_PERFORMED_FIX_158,
        INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION,
        INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158,
        MUTATION_PERFORMED_FIX_158,
    )
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_renderer import (
        render_institutional_existential_risk,
    )
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
        build_institutional_existential_risk,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_institutional_existential_risk(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "institutional_existential_risk_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_158,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_158,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
        "autonomous_self_preservation_enabled": AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158,
        "autonomous_continuity_enforcement_enabled": AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158,
        "constitutional_override_authority_enabled": CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158,
        "institutional_self_defense_authority_enabled": INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158,
        "schema_version": INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["existential_risk"] = result.existential_risk
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_institutional_existential_risk(result.existential_risk)
    return payload


@router.post("/mission-control/institutional-existential-risk/record")
def mission_control_institutional_existential_risk_record_api(
    body: InstitutionalExistentialRiskRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
        EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
        GOVERNANCE_MUTATION_PERFORMED_FIX_158,
        INSTITUTIONAL_EXISTENTIAL_RISK_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_158,
    )
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_store import (
        append_institutional_existential_risk_record,
    )
    from aethos_core.mission_control.institutional_external_relations.institutional_external_relations_service import (
        build_institutional_external_relations,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    external = build_institutional_external_relations(session_id=sid)
    ext = external.external_relations if external.ok else {}
    record, blockers = append_institutional_existential_risk_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ext.get("plan_id") or "") or None,
        correlation_id=str(ext.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": INSTITUTIONAL_EXISTENTIAL_RISK_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_158,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_158,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
        "executable": EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
        "existential_risk_memory_only": True,
        "detail": "Existential risk record persisted (recommendation-only — no self-preservation).",
    }


@router.get("/mission-control/constitutional-ethics")
def mission_control_constitutional_ethics_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
        AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159,
        CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159,
        CONSTITUTIONAL_ETHICS_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_159,
        MUTATION_PERFORMED_FIX_159,
        SELF_AUTHORED_ETHICS_ENABLED_FIX_159,
        VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159,
    )
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_renderer import (
        render_constitutional_ethics,
    )
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import (
        build_constitutional_ethics,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_constitutional_ethics(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "constitutional_ethics_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_159,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_159,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
        "autonomous_moral_authority_enabled": AUTONOMOUS_MORAL_AUTHORITY_ENABLED_FIX_159,
        "self_authored_ethics_enabled": SELF_AUTHORED_ETHICS_ENABLED_FIX_159,
        "constitutional_override_authority_enabled": CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_159,
        "value_enforcement_authority_enabled": VALUE_ENFORCEMENT_AUTHORITY_ENABLED_FIX_159,
        "schema_version": CONSTITUTIONAL_ETHICS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["constitutional_ethics"] = result.constitutional_ethics
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_constitutional_ethics(result.constitutional_ethics)
    return payload


@router.post("/mission-control/constitutional-ethics/record")
def mission_control_constitutional_ethics_record_api(
    body: ConstitutionalEthicsRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
        ETHICS_RECOMMENDATION_EXECUTABLE,
        CONSTITUTIONAL_ETHICS_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_159,
        MUTATION_PERFORMED_FIX_159,
    )
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_store import (
        append_constitutional_ethics_record,
    )
    from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
        build_institutional_existential_risk,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    existential = build_institutional_existential_risk(session_id=sid)
    ex = existential.existential_risk if existential.ok else {}
    record, blockers = append_constitutional_ethics_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ex.get("plan_id") or "") or None,
        correlation_id=str(ex.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": CONSTITUTIONAL_ETHICS_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_159,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_159,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_159,
        "executable": ETHICS_RECOMMENDATION_EXECUTABLE,
        "constitutional_ethics_memory_only": True,
        "detail": "Constitutional ethics record persisted (recommendation-only — no moral authority).",
    }


@router.get("/mission-control/constitutional-audit")
def mission_control_constitutional_audit_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
        AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160,
        CONSTITUTIONAL_AUDIT_SCHEMA_VERSION,
        GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160,
        GOVERNANCE_MUTATION_PERFORMED_FIX_160,
        MUTATION_PERFORMED_FIX_160,
        PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160,
    )
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_renderer import (
        render_constitutional_audit,
    )
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import (
        build_constitutional_audit,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_constitutional_audit(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "constitutional_audit_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_160,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_160,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
        "autonomous_disclosure_enabled": AUTONOMOUS_DISCLOSURE_ENABLED_FIX_160,
        "public_communication_authority_enabled": PUBLIC_COMMUNICATION_AUTHORITY_ENABLED_FIX_160,
        "governance_enforcement_enabled": GOVERNANCE_ENFORCEMENT_ENABLED_FIX_160,
        "schema_version": CONSTITUTIONAL_AUDIT_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["constitutional_audit"] = result.constitutional_audit
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_constitutional_audit(result.constitutional_audit)
    return payload


@router.post("/mission-control/constitutional-audit/record")
def mission_control_constitutional_audit_record_api(
    body: ConstitutionalAuditRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_contract import (
        AUDIT_RECOMMENDATION_EXECUTABLE,
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
        CONSTITUTIONAL_AUDIT_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_160,
        MUTATION_PERFORMED_FIX_160,
    )
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_store import (
        append_constitutional_audit_record,
    )
    from aethos_core.mission_control.constitutional_ethics.constitutional_ethics_service import build_constitutional_ethics

    sid = (body.session_id or "default").strip()[:64] or "default"
    ethics = build_constitutional_ethics(session_id=sid)
    eth = ethics.constitutional_ethics if ethics.ok else {}
    record, blockers = append_constitutional_audit_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(eth.get("plan_id") or "") or None,
        correlation_id=str(eth.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": CONSTITUTIONAL_AUDIT_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_160,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_160,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_160,
        "executable": AUDIT_RECOMMENDATION_EXECUTABLE,
        "constitutional_audit_memory_only": True,
        "detail": "Constitutional audit record persisted (recommendation-only — no disclosure authority).",
    }


@router.get("/mission-control/constitutional-legitimacy")
def mission_control_constitutional_legitimacy_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
        AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161,
        CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161,
        CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_161,
        MUTATION_PERFORMED_FIX_161,
        PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161,
        SOVEREIGNTY_DELEGATION_ENABLED_FIX_161,
    )
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_renderer import (
        render_constitutional_legitimacy,
    )
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
        build_constitutional_legitimacy,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_constitutional_legitimacy(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "constitutional_legitimacy_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_161,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_161,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
        "autonomous_legitimacy_enforcement_enabled": AUTONOMOUS_LEGITIMACY_ENFORCEMENT_ENABLED_FIX_161,
        "public_trust_manipulation_enabled": PUBLIC_TRUST_MANIPULATION_ENABLED_FIX_161,
        "constitutional_authority_expansion_enabled": CONSTITUTIONAL_AUTHORITY_EXPANSION_ENABLED_FIX_161,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_161,
        "schema_version": CONSTITUTIONAL_LEGITIMACY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["constitutional_legitimacy"] = result.constitutional_legitimacy
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_constitutional_legitimacy(result.constitutional_legitimacy)
    return payload


@router.post("/mission-control/constitutional-legitimacy/record")
def mission_control_constitutional_legitimacy_record_api(
    body: ConstitutionalLegitimacyRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_audit.constitutional_audit_service import build_constitutional_audit
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
        GOVERNANCE_MUTATION_PERFORMED_FIX_161,
        CONSTITUTIONAL_LEGITIMACY_RECORD_SCHEMA_VERSION,
        LEGITIMACY_RECOMMENDATION_EXECUTABLE,
        MUTATION_PERFORMED_FIX_161,
    )
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_store import (
        append_constitutional_legitimacy_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    audit = build_constitutional_audit(session_id=sid)
    aud = audit.constitutional_audit if audit.ok else {}
    record, blockers = append_constitutional_legitimacy_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(aud.get("plan_id") or "") or None,
        correlation_id=str(aud.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": CONSTITUTIONAL_LEGITIMACY_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_161,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_161,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_161,
        "executable": LEGITIMACY_RECOMMENDATION_EXECUTABLE,
        "constitutional_legitimacy_memory_only": True,
        "detail": "Constitutional legitimacy record persisted (recommendation-only — no trust manipulation).",
    }


@router.get("/mission-control/constitutional-pluralism")
def mission_control_constitutional_pluralism_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
        AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162,
        AUTONOMOUS_CONSTITUTIONAL_ARBITRATION_ENABLED_FIX_162,
        CONSTITUTIONAL_PLURALISM_SCHEMA_VERSION,
        ENFORCED_IDEOLOGICAL_ALIGNMENT_ENABLED_FIX_162,
        GOVERNANCE_MUTATION_PERFORMED_FIX_162,
        MUTATION_PERFORMED_FIX_162,
        SOVEREIGNTY_DELEGATION_ENABLED_FIX_162,
    )
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_renderer import (
        render_constitutional_pluralism,
    )
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
        build_constitutional_pluralism,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_constitutional_pluralism(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "constitutional_pluralism_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_162,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_162,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
        "authoritative_worldview_selection_enabled": AUTHORITATIVE_WORLDVIEW_SELECTION_ENABLED_FIX_162,
        "autonomous_constitutional_arbitration_enabled": AUTONOMOUS_CONSTITUTIONAL_ARBITRATION_ENABLED_FIX_162,
        "enforced_ideological_alignment_enabled": ENFORCED_IDEOLOGICAL_ALIGNMENT_ENABLED_FIX_162,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_162,
        "schema_version": CONSTITUTIONAL_PLURALISM_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["constitutional_pluralism"] = result.constitutional_pluralism
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_constitutional_pluralism(result.constitutional_pluralism)
    return payload


@router.post("/mission-control/constitutional-pluralism/record")
def mission_control_constitutional_pluralism_record_api(
    body: ConstitutionalPluralismRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_legitimacy.constitutional_legitimacy_service import (
        build_constitutional_legitimacy,
    )
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
        CONSTITUTIONAL_PLURALISM_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_162,
        MUTATION_PERFORMED_FIX_162,
        PLURALISM_RECOMMENDATION_EXECUTABLE,
    )
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_store import (
        append_constitutional_pluralism_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    legitimacy = build_constitutional_legitimacy(session_id=sid)
    leg = legitimacy.constitutional_legitimacy if legitimacy.ok else {}
    record, blockers = append_constitutional_pluralism_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(leg.get("plan_id") or "") or None,
        correlation_id=str(leg.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": CONSTITUTIONAL_PLURALISM_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_162,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_162,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_162,
        "executable": PLURALISM_RECOMMENDATION_EXECUTABLE,
        "constitutional_pluralism_memory_only": True,
        "detail": "Constitutional pluralism record persisted (recommendation-only — no arbitration authority).",
    }


@router.get("/mission-control/constitutional-synthesis")
def mission_control_constitutional_synthesis_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
        AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163,
        CONSTITUTIONAL_SYNTHESIS_SCHEMA_VERSION,
        DOCTRINE_ENFORCEMENT_ENABLED_FIX_163,
        GOVERNANCE_MUTATION_PERFORMED_FIX_163,
        LEGITIMACY_ARBITRATION_ENABLED_FIX_163,
        MUTATION_PERFORMED_FIX_163,
        SOVEREIGNTY_DELEGATION_ENABLED_FIX_163,
        WORLDVIEW_SELECTION_ENABLED_FIX_163,
    )
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_renderer import (
        render_constitutional_synthesis,
    )
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
        build_constitutional_synthesis,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_constitutional_synthesis(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "constitutional_synthesis_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_163,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_163,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
        "autonomous_constitutional_decisions_enabled": AUTONOMOUS_CONSTITUTIONAL_DECISIONS_ENABLED_FIX_163,
        "doctrine_enforcement_enabled": DOCTRINE_ENFORCEMENT_ENABLED_FIX_163,
        "legitimacy_arbitration_enabled": LEGITIMACY_ARBITRATION_ENABLED_FIX_163,
        "worldview_selection_enabled": WORLDVIEW_SELECTION_ENABLED_FIX_163,
        "sovereignty_delegation_enabled": SOVEREIGNTY_DELEGATION_ENABLED_FIX_163,
        "schema_version": CONSTITUTIONAL_SYNTHESIS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["constitutional_synthesis"] = result.constitutional_synthesis
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_constitutional_synthesis(result.constitutional_synthesis)
    return payload


@router.post("/mission-control/constitutional-synthesis/record")
def mission_control_constitutional_synthesis_record_api(
    body: ConstitutionalSynthesisRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_pluralism.constitutional_pluralism_service import (
        build_constitutional_pluralism,
    )
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
        CONSTITUTIONAL_SYNTHESIS_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_163,
        MUTATION_PERFORMED_FIX_163,
        SYNTHESIS_RECOMMENDATION_EXECUTABLE,
    )
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_store import (
        append_constitutional_synthesis_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    pluralism = build_constitutional_pluralism(session_id=sid)
    pl = pluralism.constitutional_pluralism if pluralism.ok else {}
    record, blockers = append_constitutional_synthesis_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(pl.get("plan_id") or "") or None,
        correlation_id=str(pl.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": CONSTITUTIONAL_SYNTHESIS_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_163,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_163,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_163,
        "executable": SYNTHESIS_RECOMMENDATION_EXECUTABLE,
        "constitutional_synthesis_memory_only": True,
        "detail": "Constitutional synthesis record persisted (recommendation-only — no constitutional authority).",
    }


@router.get("/mission-control/mission-planning")
def mission_control_mission_planning_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_planning.mission_planning_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
        AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_164,
        AUTO_PATH_SELECTION_ENABLED_FIX_164,
        GOVERNANCE_MUTATION_PERFORMED_FIX_164,
        MERGE_DEPLOY_RESTART_ENABLED_FIX_164,
        MISSION_PLANNING_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_164,
        PR_OPEN_ENABLED_FIX_164,
        RAILWAY_MUTATION_ENABLED_FIX_164,
    )
    from aethos_core.mission_control.mission_planning.mission_planning_renderer import render_mission_planning
    from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_mission_planning(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "mission_planning_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_164,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_164,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
        "autonomous_action_execution_enabled": AUTONOMOUS_ACTION_EXECUTION_ENABLED_FIX_164,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_164,
        "auto_path_selection_enabled": AUTO_PATH_SELECTION_ENABLED_FIX_164,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_164,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_164,
        "merge_deploy_restart_enabled": MERGE_DEPLOY_RESTART_ENABLED_FIX_164,
        "schema_version": MISSION_PLANNING_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["mission_planning"] = result.mission_planning
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_mission_planning(result.mission_planning)
    return payload


@router.post("/mission-control/mission-planning/record")
def mission_control_mission_planning_record_api(
    body: MissionPlanningRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.constitutional_synthesis.constitutional_synthesis_service import (
        build_constitutional_synthesis,
    )
    from aethos_core.mission_control.mission_planning.mission_planning_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
        GOVERNANCE_MUTATION_PERFORMED_FIX_164,
        MISSION_PLANNING_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_164,
        PLANNING_RECOMMENDATION_EXECUTABLE,
    )
    from aethos_core.mission_control.mission_planning.mission_planning_store import append_mission_planning_record

    sid = (body.session_id or "default").strip()[:64] or "default"
    synthesis = build_constitutional_synthesis(session_id=sid)
    syn = synthesis.constitutional_synthesis if synthesis.ok else {}
    record, blockers = append_mission_planning_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(syn.get("plan_id") or "") or None,
        correlation_id=str(syn.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": MISSION_PLANNING_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_164,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_164,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_164,
        "executable": PLANNING_RECOMMENDATION_EXECUTABLE,
        "mission_planning_memory_only": True,
        "detail": "Mission planning record persisted (recommendation-only — no execution authority).",
    }


@router.get("/mission-control/mission-planning-deliberation")
def mission_control_mission_planning_deliberation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_165,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_165,
        AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165,
        AUTONOMOUS_MERGE_ENABLED_FIX_165,
        AUTONOMOUS_PR_CREATION_ENABLED_FIX_165,
        AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165,
        GOVERNANCE_MUTATION_PERFORMED_FIX_165,
        MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_165,
    )
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_renderer import (
        render_mission_planning_deliberation,
    )
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
        build_mission_planning_deliberation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_mission_planning_deliberation(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "mission_planning_deliberation_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_165,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_165,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_165,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_165,
        "autonomous_lane_selection_enabled": AUTONOMOUS_LANE_SELECTION_ENABLED_FIX_165,
        "autonomous_pr_creation_enabled": AUTONOMOUS_PR_CREATION_ENABLED_FIX_165,
        "autonomous_railway_mutation_enabled": AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_165,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_165,
        "schema_version": MISSION_PLANNING_DELIBERATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["mission_planning_deliberation"] = result.mission_planning_deliberation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_mission_planning_deliberation(result.mission_planning_deliberation)
    return payload


@router.post("/mission-control/mission-planning-deliberation/record")
def mission_control_mission_planning_deliberation_record_api(
    body: MissionPlanningDeliberationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_planning.mission_planning_service import build_mission_planning
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
        DELIBERATION_RECOMMENDATION_EXECUTABLE,
        GOVERNANCE_MUTATION_PERFORMED_FIX_165,
        MISSION_PLANNING_DELIBERATION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_165,
    )
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_store import (
        append_mission_planning_deliberation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    planning = build_mission_planning(session_id=sid)
    mp = planning.mission_planning if planning.ok else {}
    record, blockers = append_mission_planning_deliberation_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(mp.get("plan_id") or "") or None,
        correlation_id=str(mp.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": MISSION_PLANNING_DELIBERATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_165,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_165,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_165,
        "executable": DELIBERATION_RECOMMENDATION_EXECUTABLE,
        "mission_planning_deliberation_memory_only": True,
        "detail": "Mission planning deliberation record persisted (analysis-only — no execution authority).",
    }


@router.get("/mission-control/human-decision-board")
def mission_control_human_decision_board_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.human_decision_board.human_decision_board_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_166,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_166,
        AUTONOMOUS_MERGE_ENABLED_FIX_166,
        AUTONOMOUS_PR_CREATION_ENABLED_FIX_166,
        AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166,
        AUTONOMOUS_SELECTION_ENABLED_FIX_166,
        GOVERNANCE_MUTATION_PERFORMED_FIX_166,
        HUMAN_DECISION_BOARD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_166,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_renderer import (
        render_human_decision_board,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_service import (
        build_human_decision_board,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_human_decision_board(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "human_decision_board_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_166,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_166,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
        "autonomous_selection_enabled": AUTONOMOUS_SELECTION_ENABLED_FIX_166,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_166,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_166,
        "autonomous_pr_creation_enabled": AUTONOMOUS_PR_CREATION_ENABLED_FIX_166,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_166,
        "autonomous_railway_mutation_enabled": AUTONOMOUS_RAILWAY_MUTATION_ENABLED_FIX_166,
        "schema_version": HUMAN_DECISION_BOARD_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["human_decision_board"] = result.human_decision_board
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_human_decision_board(result.human_decision_board)
    return payload


@router.post("/mission-control/human-decision-board/record")
def mission_control_human_decision_board_record_api(
    body: HumanDecisionBoardRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.human_decision_board.human_decision_board_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
        DECISION_BOARD_EXECUTABLE,
        GOVERNANCE_MUTATION_PERFORMED_FIX_166,
        HUMAN_DECISION_BOARD_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_166,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_store import (
        append_human_decision_board_record,
    )
    from aethos_core.mission_control.mission_planning_deliberation.mission_planning_deliberation_service import (
        build_mission_planning_deliberation,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    deliberation = build_mission_planning_deliberation(session_id=sid)
    delib = deliberation.mission_planning_deliberation if deliberation.ok else {}
    record, blockers = append_human_decision_board_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(delib.get("plan_id") or "") or None,
        correlation_id=str(delib.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": HUMAN_DECISION_BOARD_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_166,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_166,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_166,
        "executable": DECISION_BOARD_EXECUTABLE,
        "human_decision_board_memory_only": True,
        "detail": "Human decision board record persisted (human choice only — no autonomous selection).",
    }


@router.get("/mission-control/execution-handoff-coordination")
def mission_control_execution_handoff_coordination_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_167,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_167,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167,
        EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_167,
        MERGE_DEPLOY_ENABLED_FIX_167,
        MUTATION_PERFORMED_FIX_167,
        PR_OPEN_ENABLED_FIX_167,
        RAILWAY_MUTATION_ENABLED_FIX_167,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_renderer import (
        render_execution_handoff_coordination,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
        build_execution_handoff_coordination,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_execution_handoff_coordination(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "execution_handoff_coordination_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_167,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_167,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_167,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_167,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_167,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_167,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_167,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_167,
        "schema_version": EXECUTION_HANDOFF_COORDINATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["execution_handoff_coordination"] = result.execution_handoff_coordination
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_execution_handoff_coordination(result.execution_handoff_coordination)
    return payload


@router.post("/mission-control/execution-handoff-coordination/record")
def mission_control_execution_handoff_coordination_record_api(
    body: ExecutionHandoffCoordinationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
        GOVERNANCE_MUTATION_PERFORMED_FIX_167,
        EXECUTION_HANDOFF_COORDINATION_RECORD_SCHEMA_VERSION,
        HANDOFF_RECOMMENDATION_EXECUTABLE,
        MUTATION_PERFORMED_FIX_167,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_store import (
        append_execution_handoff_coordination_record,
    )
    from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board

    sid = (body.session_id or "default").strip()[:64] or "default"
    decision = build_human_decision_board(session_id=sid)
    board = decision.human_decision_board if decision.ok else {}
    record, blockers = append_execution_handoff_coordination_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": EXECUTION_HANDOFF_COORDINATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_167,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_167,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_167,
        "executable": HANDOFF_RECOMMENDATION_EXECUTABLE,
        "execution_handoff_coordination_memory_only": True,
        "detail": "Execution handoff record persisted (handoff coordination only — no execution authority).",
    }


@router.get("/mission-control/bounded-delivery-work-packages")
def mission_control_bounded_delivery_work_packages_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_168,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_168,
        BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION,
        CODE_WRITE_ENABLED_FIX_168,
        GOVERNANCE_MUTATION_PERFORMED_FIX_168,
        MERGE_DEPLOY_ENABLED_FIX_168,
        MUTATION_PERFORMED_FIX_168,
        PR_ACTION_ENABLED_FIX_168,
        RAILWAY_MUTATION_ENABLED_FIX_168,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_renderer import (
        render_bounded_delivery_work_packages,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
        build_bounded_delivery_work_packages,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_bounded_delivery_work_packages(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "bounded_delivery_work_packages_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_168,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_168,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_168,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_168,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_168,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_168,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_168,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_168,
        "schema_version": BOUNDED_DELIVERY_WORK_PACKAGES_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["bounded_delivery_work_packages"] = result.bounded_delivery_work_packages
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_bounded_delivery_work_packages(result.bounded_delivery_work_packages)
    return payload


@router.post("/mission-control/bounded-delivery-work-packages/record")
def mission_control_bounded_delivery_work_packages_record_api(
    body: BoundedDeliveryWorkPackagesRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
        BOUNDED_DELIVERY_WORK_PACKAGES_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_168,
        MUTATION_PERFORMED_FIX_168,
        WORK_PACKAGES_RECOMMENDATION_EXECUTABLE,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_store import (
        append_bounded_delivery_work_packages_record,
    )
    from aethos_core.mission_control.execution_handoff_coordination.execution_handoff_coordination_service import (
        build_execution_handoff_coordination,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    handoff = build_execution_handoff_coordination(session_id=sid)
    handoff_payload = handoff.execution_handoff_coordination if handoff.ok else {}
    record, blockers = append_bounded_delivery_work_packages_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(handoff_payload.get("plan_id") or "") or None,
        correlation_id=str(handoff_payload.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": BOUNDED_DELIVERY_WORK_PACKAGES_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_168,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_168,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_168,
        "executable": WORK_PACKAGES_RECOMMENDATION_EXECUTABLE,
        "bounded_delivery_work_packages_memory_only": True,
        "detail": "Work package record persisted (package scoping only — no execution authority).",
    }


@router.get("/mission-control/work-package-readiness-lane-admission")
def mission_control_work_package_readiness_lane_admission_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_169,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_169,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169,
        CODE_WRITE_ENABLED_FIX_169,
        GOVERNANCE_MUTATION_PERFORMED_FIX_169,
        MERGE_DEPLOY_ENABLED_FIX_169,
        MUTATION_PERFORMED_FIX_169,
        PR_ACTION_ENABLED_FIX_169,
        RAILWAY_MUTATION_ENABLED_FIX_169,
        WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_renderer import (
        render_work_package_readiness_lane_admission,
    )
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_service import (
        build_work_package_readiness_lane_admission,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_work_package_readiness_lane_admission(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "work_package_readiness_lane_admission_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_169,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_169,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_169,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_169,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_169,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_169,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_169,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_169,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_169,
        "schema_version": WORK_PACKAGE_READINESS_LANE_ADMISSION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["work_package_readiness_lane_admission"] = result.work_package_readiness_lane_admission
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_work_package_readiness_lane_admission(result.work_package_readiness_lane_admission)
    return payload


@router.post("/mission-control/work-package-readiness-lane-admission/record")
def mission_control_work_package_readiness_lane_admission_record_api(
    body: WorkPackageReadinessLaneAdmissionRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
        build_bounded_delivery_work_packages,
    )
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
        GOVERNANCE_MUTATION_PERFORMED_FIX_169,
        LANE_ADMISSION_RECOMMENDATION_EXECUTABLE,
        MUTATION_PERFORMED_FIX_169,
        WORK_PACKAGE_READINESS_LANE_ADMISSION_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.work_package_readiness_lane_admission.work_package_readiness_lane_admission_store import (
        append_work_package_readiness_lane_admission_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    wp = build_bounded_delivery_work_packages(session_id=sid)
    wp_payload = wp.bounded_delivery_work_packages if wp.ok else {}
    record, blockers = append_work_package_readiness_lane_admission_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(wp_payload.get("plan_id") or "") or None,
        correlation_id=str(wp_payload.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": WORK_PACKAGE_READINESS_LANE_ADMISSION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_169,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_169,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_169,
        "executable": LANE_ADMISSION_RECOMMENDATION_EXECUTABLE,
        "work_package_readiness_lane_admission_memory_only": True,
        "detail": "Lane admission record persisted (readiness evaluation only — no execution authority).",
    }


@router.get("/mission-control/mission-authorization")
def mission_control_mission_authorization_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.mission_authorization.mission_authorization_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_170,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_170,
        AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170,
        GATE_BYPASS_ENABLED_FIX_170,
        GOVERNANCE_MUTATION_PERFORMED_FIX_170,
        MERGE_DEPLOY_ENABLED_FIX_170,
        MISSION_AUTHORIZATION_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_170,
        PR_OPEN_ENABLED_FIX_170,
        RAILWAY_MUTATION_ENABLED_FIX_170,
        TIER_ESCALATION_ENABLED_FIX_170,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_renderer import (
        render_mission_authorization,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_service import (
        build_mission_authorization,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_mission_authorization(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={"blockers": result.blockers, "message": result.detail or "mission_authorization_unavailable"},
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_170,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_170,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_170,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_170,
        "autonomous_lane_expansion_enabled": AUTONOMOUS_LANE_EXPANSION_ENABLED_FIX_170,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_170,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_170,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_170,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_170,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_170,
        "schema_version": MISSION_AUTHORIZATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["mission_authorization"] = result.mission_authorization
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_mission_authorization(result.mission_authorization)
    return payload


@router.post("/mission-control/mission-authorization/record")
def mission_control_mission_authorization_record_api(body: MissionAuthorizationRecordIn) -> dict[str, Any]:
    from aethos_core.mission_control.human_decision_board.human_decision_board_service import build_human_decision_board
    from aethos_core.mission_control.mission_authorization.mission_authorization_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
        GOVERNANCE_MUTATION_PERFORMED_FIX_170,
        MISSION_AUTHORIZATION_EXECUTABLE,
        MISSION_AUTHORIZATION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_170,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_store import (
        append_mission_authorization_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    decision = build_human_decision_board(session_id=sid)
    board = decision.human_decision_board if decision.ok else {}
    record, blockers = append_mission_authorization_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": MISSION_AUTHORIZATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_170,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_170,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_170,
        "executable": MISSION_AUTHORIZATION_EXECUTABLE,
        "mission_authorization_memory_only": True,
        "detail": "Mission authorization record persisted (bounded envelope — existing gates remain enforced).",
    }


@router.get("/mission-control/bounded-execution-participation")
def mission_control_bounded_execution_participation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_171,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_171,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
        BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION,
        GATE_BYPASS_ENABLED_FIX_171,
        GOVERNANCE_MUTATION_PERFORMED_FIX_171,
        MERGE_DEPLOY_ENABLED_FIX_171,
        MUTATION_PERFORMED_FIX_171,
        PR_OPEN_ENABLED_FIX_171,
        RAILWAY_MUTATION_ENABLED_FIX_171,
        TIER_ESCALATION_ENABLED_FIX_171,
    )
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_renderer import (
        render_bounded_execution_participation,
    )
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
        build_bounded_execution_participation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_bounded_execution_participation(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "bounded_execution_participation_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_171,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_171,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_171,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_171,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_171,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_171,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_171,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_171,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_171,
        "schema_version": BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["bounded_execution_participation"] = result.bounded_execution_participation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_bounded_execution_participation(result.bounded_execution_participation)
    return payload


@router.post("/mission-control/bounded-execution-participation/record")
def mission_control_bounded_execution_participation_record_api(
    body: BoundedExecutionParticipationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
        BOUNDED_EXECUTION_PARTICIPATION_EXECUTABLE,
        BOUNDED_EXECUTION_PARTICIPATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_171,
        MUTATION_PERFORMED_FIX_171,
    )
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
        append_bounded_execution_participation_record,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_service import build_mission_authorization

    sid = (body.session_id or "default").strip()[:64] or "default"
    auth = build_mission_authorization(session_id=sid)
    board = auth.mission_authorization if auth.ok else {}
    record, blockers = append_bounded_execution_participation_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": BOUNDED_EXECUTION_PARTICIPATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_171,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_171,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
        "executable": BOUNDED_EXECUTION_PARTICIPATION_EXECUTABLE,
        "bounded_execution_participation_memory_only": True,
        "detail": "Bounded execution participation record persisted (envelope-scoped — existing gates remain enforced).",
    }


@router.get("/mission-control/bounded-multi-agent-delivery-execution")
def mission_control_bounded_multi_agent_delivery_execution_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
        AGENT_EXECUTION_AUTHORITY_FIX_189,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_189,
        BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION,
        BOUNDED_WORK_PERFORMED_FIX_189,
        DEPLOY_AUTHORITY_FIX_189,
        GATE_BYPASS_ENABLED_FIX_189,
        GOVERNANCE_MUTATION_PERFORMED_FIX_189,
        MERGE_AUTHORITY_FIX_189,
        MUTATION_PERFORMED_FIX_189,
        PROVIDER_AUTHORITY_FIX_189,
        RAILWAY_AUTHORITY_FIX_189,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_renderer import (
        render_bounded_multi_agent_delivery_execution,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
        build_bounded_multi_agent_delivery_execution,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_bounded_multi_agent_delivery_execution(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_189,
        "bounded_work_performed": BOUNDED_WORK_PERFORMED_FIX_189,
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_189,
        "merge_authority": MERGE_AUTHORITY_FIX_189,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_189,
        "railway_authority": RAILWAY_AUTHORITY_FIX_189,
        "provider_authority": PROVIDER_AUTHORITY_FIX_189,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_189,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_189,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_189,
        "schema_version": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["bounded_multi_agent_delivery_execution"] = result.bounded_multi_agent_delivery_execution
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_bounded_multi_agent_delivery_execution(
            result.bounded_multi_agent_delivery_execution
        )
    return payload


@router.post("/mission-control/bounded-multi-agent-delivery-execution/record")
def mission_control_bounded_multi_agent_delivery_execution_record_api(
    body: BoundedMultiAgentDeliveryExecutionRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
        BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_EXECUTABLE,
        BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_189,
        MUTATION_PERFORMED_FIX_189,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        append_bounded_multi_agent_delivery_execution_record,
    )
    from aethos_core.mission_control.mission_authorization.mission_authorization_service import (
        build_mission_authorization,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    auth = build_mission_authorization(session_id=sid)
    board = auth.mission_authorization if auth.ok else {}
    record, blockers = append_bounded_multi_agent_delivery_execution_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_189,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_189,
        "executable": BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_EXECUTABLE,
        "bounded_multi_agent_delivery_execution_memory_only": True,
        "detail": "Bounded multi-agent delivery execution record persisted (agents work — gates decide).",
    }


@router.post("/mission-control/bounded-multi-agent-delivery-execution/run")
def mission_control_bounded_multi_agent_delivery_execution_run_api(
    body: BoundedMultiAgentDeliveryExecutionRunIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
        AGENT_EXECUTION_AUTHORITY_FIX_189,
        BOUNDED_WORK_PERFORMED_FIX_189,
        MERGE_AUTHORITY_FIX_189,
        PROVIDER_AUTHORITY_FIX_189,
        RAILWAY_AUTHORITY_FIX_189,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
        run_bounded_multi_agent_delivery_execution,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    role = (body.role_id or "").strip() or "__pipeline__"
    outcome = run_bounded_multi_agent_delivery_execution(session_id=sid, role_id=role)
    if outcome.blockers and not outcome.agent_outputs:
        raise HTTPException(
            status_code=400,
            detail={"blockers": outcome.blockers, "message": outcome.detail or "agent_execution_blocked"},
        )

    return {
        "ok": outcome.ok,
        "session_id": outcome.session_id,
        "role_id": outcome.role_id,
        "pipeline": outcome.pipeline,
        "agent_outputs": outcome.agent_outputs,
        "pipeline_state": outcome.pipeline_state,
        "blockers": outcome.blockers,
        "bounded_work_performed": BOUNDED_WORK_PERFORMED_FIX_189,
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_189,
        "merge_authority": MERGE_AUTHORITY_FIX_189,
        "railway_authority": RAILWAY_AUTHORITY_FIX_189,
        "provider_authority": PROVIDER_AUTHORITY_FIX_189,
        "detail": outcome.detail,
    }


@router.get("/mission-control/agent-execution-quality-throughput-metrics")
def mission_control_agent_execution_quality_throughput_metrics_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
        AGENT_EXECUTION_AUTHORITY_FIX_190,
        AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION,
        AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_190,
        DEPLOY_AUTHORITY_FIX_190,
        EXECUTION_PERFORMED_FIX_190,
        GATE_BYPASS_ENABLED_FIX_190,
        GOVERNANCE_MUTATION_PERFORMED_FIX_190,
        MERGE_AUTHORITY_FIX_190,
        METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190,
        MUTATION_PERFORMED_FIX_190,
        PROVIDER_AUTHORITY_FIX_190,
        RAILWAY_AUTHORITY_FIX_190,
    )
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_renderer import (
        render_agent_execution_quality_throughput_metrics,
    )
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_service import (
        build_agent_execution_quality_throughput_metrics,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_agent_execution_quality_throughput_metrics(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_190,
        "execution_performed": EXECUTION_PERFORMED_FIX_190,
        "metrics_compose_receipts_only": METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190,
        "agent_metrics_grant_authority": AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
        "agent_execution_authority": AGENT_EXECUTION_AUTHORITY_FIX_190,
        "merge_authority": MERGE_AUTHORITY_FIX_190,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_190,
        "railway_authority": RAILWAY_AUTHORITY_FIX_190,
        "provider_authority": PROVIDER_AUTHORITY_FIX_190,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_190,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_190,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_190,
        "schema_version": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["agent_execution_quality_throughput_metrics"] = (
            result.agent_execution_quality_throughput_metrics
        )
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_agent_execution_quality_throughput_metrics(
            result.agent_execution_quality_throughput_metrics
        )
    return payload


@router.post("/mission-control/agent-execution-quality-throughput-metrics/record")
def mission_control_agent_execution_quality_throughput_metrics_record_api(
    body: AgentExecutionQualityThroughputMetricsRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
        AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_EXECUTABLE,
        AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_190,
        MUTATION_PERFORMED_FIX_190,
    )
    from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
        append_agent_execution_quality_throughput_metrics_record,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
        build_bounded_multi_agent_delivery_execution,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    execution = build_bounded_multi_agent_delivery_execution(session_id=sid)
    board = execution.bounded_multi_agent_delivery_execution if execution.ok else {}
    record, blockers = append_agent_execution_quality_throughput_metrics_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_190,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_190,
        "executable": AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_EXECUTABLE,
        "agent_execution_quality_throughput_metrics_memory_only": True,
        "detail": "Agent execution quality and throughput metrics record persisted (metrics ≠ authority).",
    }


@router.get("/mission-control/cross-repository-multi-agent-delivery-validation")
def mission_control_cross_repository_multi_agent_delivery_validation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
        CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
        CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION,
        DEPLOY_AUTHORITY_FIX_191,
        EXECUTION_PERFORMED_FIX_191,
        GATE_BYPASS_ENABLED_FIX_191,
        GOVERNANCE_MUTATION_PERFORMED_FIX_191,
        MERGE_AUTHORITY_FIX_191,
        MUTATION_PERFORMED_FIX_191,
        PROVIDER_AUTHORITY_FIX_191,
        RAILWAY_AUTHORITY_FIX_191,
        TRUST_TRANSFER_ENABLED_FIX_191,
        VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191,
    )
    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_renderer import (
        render_cross_repository_multi_agent_delivery_validation,
    )
    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
        build_cross_repository_multi_agent_delivery_validation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_cross_repository_multi_agent_delivery_validation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_191,
        "execution_performed": EXECUTION_PERFORMED_FIX_191,
        "validation_compose_artifacts_only": VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191,
        "cross_repo_validation_grants_trust": CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_191,
        "merge_authority": MERGE_AUTHORITY_FIX_191,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_191,
        "railway_authority": RAILWAY_AUTHORITY_FIX_191,
        "provider_authority": PROVIDER_AUTHORITY_FIX_191,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_191,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_191,
        "schema_version": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["cross_repository_multi_agent_delivery_validation"] = (
            result.cross_repository_multi_agent_delivery_validation
        )
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_cross_repository_multi_agent_delivery_validation(
            result.cross_repository_multi_agent_delivery_validation
        )
    return payload


@router.post("/mission-control/cross-repository-multi-agent-delivery-validation/record")
def mission_control_cross_repository_multi_agent_delivery_validation_record_api(
    body: CrossRepositoryMultiAgentDeliveryValidationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
        CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_EXECUTABLE,
        CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_191,
        MUTATION_PERFORMED_FIX_191,
    )
    from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_store import (
        append_cross_repository_multi_agent_delivery_validation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_cross_repository_multi_agent_delivery_validation_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        repository=body.repository,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_191,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_191,
        "executable": CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_EXECUTABLE,
        "cross_repository_multi_agent_delivery_validation_memory_only": True,
        "detail": "Cross-repository validation record persisted (validation ≠ trust granting).",
    }


@router.get("/mission-control/governed-merge-lifecycle")
def mission_control_governed_merge_lifecycle_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
        APPROVAL_BYPASS_ENABLED_FIX_200,
        AUTONOMOUS_MERGE_ENABLED_FIX_200,
        DEPLOY_AUTHORITY_FIX_200,
        EXECUTION_PERFORMED_FIX_200,
        GATE_BYPASS_ENABLED_FIX_200,
        GOVERNANCE_MUTATION_PERFORMED_FIX_200,
        GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200,
        GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION,
        HIDDEN_MERGE_PATH_ENABLED_FIX_200,
        MERGE_AUTHORITY_FIX_200,
        MERGE_EXECUTION_PERFORMED_FIX_200,
        MUTATION_PERFORMED_FIX_200,
        PROVIDER_AUTHORITY_FIX_200,
        RAILWAY_AUTHORITY_FIX_200,
    )
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_renderer import (
        render_governed_merge_lifecycle,
    )
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
        build_governed_merge_lifecycle,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_merge_lifecycle(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_200,
        "execution_performed": EXECUTION_PERFORMED_FIX_200,
        "merge_execution_performed": MERGE_EXECUTION_PERFORMED_FIX_200,
        "merge_lifecycle_compose_evidence_only": GOVERNED_MERGE_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_200,
        "merge_authority": MERGE_AUTHORITY_FIX_200,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_200,
        "approval_bypass_enabled": APPROVAL_BYPASS_ENABLED_FIX_200,
        "hidden_merge_path_enabled": HIDDEN_MERGE_PATH_ENABLED_FIX_200,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_200,
        "railway_authority": RAILWAY_AUTHORITY_FIX_200,
        "provider_authority": PROVIDER_AUTHORITY_FIX_200,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_200,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_200,
        "schema_version": GOVERNED_MERGE_LIFECYCLE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_merge_lifecycle"] = result.governed_merge_lifecycle
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_merge_lifecycle(result.governed_merge_lifecycle)
    return payload


@router.post("/mission-control/governed-merge-lifecycle/record")
def mission_control_governed_merge_lifecycle_record_api(
    body: GovernedMergeLifecycleRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_200,
        GOVERNED_MERGE_LIFECYCLE_EXECUTABLE,
        GOVERNED_MERGE_LIFECYCLE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_200,
    )
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
        append_governed_merge_lifecycle_record,
    )
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    sid = (body.session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "") or None
    record, blockers = append_governed_merge_lifecycle_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=plan_id,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_MERGE_LIFECYCLE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_200,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_200,
        "executable": GOVERNED_MERGE_LIFECYCLE_EXECUTABLE,
        "governed_merge_lifecycle_memory_only": True,
        "detail": "Governed merge lifecycle record persisted (merge_authority ≠ autonomous_merge).",
    }


@router.post("/mission-control/governed-merge-lifecycle/handoff")
def mission_control_governed_merge_lifecycle_handoff_api(
    body: GovernedMergeLifecycleHandoffIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
        AUTONOMOUS_MERGE_ENABLED_FIX_200,
        GOVERNED_MERGE_HANDOFF_EXECUTABLE,
        GOVERNED_MERGE_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
        MERGE_AUTHORITY_FIX_200,
        MERGE_EXECUTION_PERFORMED_FIX_200,
    )
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
        prepare_governed_merge_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = prepare_governed_merge_handoff(session_id=sid)
    if not result.ok:
        raise HTTPException(status_code=400, detail={"blockers": result.blockers or ["handoff_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_MERGE_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
        "session_id": result.session_id,
        "merge_handoff": result.merge_handoff,
        "merge_authority": MERGE_AUTHORITY_FIX_200,
        "autonomous_merge_enabled": AUTONOMOUS_MERGE_ENABLED_FIX_200,
        "merge_execution_performed": MERGE_EXECUTION_PERFORMED_FIX_200,
        "executable": GOVERNED_MERGE_HANDOFF_EXECUTABLE,
        "detail": result.detail,
    }


@router.get("/mission-control/governed-deploy-lifecycle")
def mission_control_governed_deploy_lifecycle_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
        APPROVAL_BYPASS_ENABLED_FIX_210,
        AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
        AWS_AUTHORITY_FIX_210,
        DEPLOY_AUTHORITY_FIX_210,
        EXECUTION_PERFORMED_FIX_210,
        GATE_BYPASS_ENABLED_FIX_210,
        GOVERNANCE_MUTATION_PERFORMED_FIX_210,
        GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210,
        GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION,
        HIDDEN_WORKFLOW_EXECUTION_ENABLED_FIX_210,
        KUBERNETES_AUTHORITY_FIX_210,
        MERGE_AUTHORITY_FIX_210,
        MUTATION_PERFORMED_FIX_210,
        PROVIDER_AUTHORITY_FIX_210,
        RAILWAY_AUTHORITY_FIX_210,
        VERCEL_AUTHORITY_FIX_210,
        WORKFLOW_EXECUTION_PERFORMED_FIX_210,
    )
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_renderer import (
        render_governed_deploy_lifecycle,
    )
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
        build_governed_deploy_lifecycle,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_deploy_lifecycle(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_210,
        "execution_performed": EXECUTION_PERFORMED_FIX_210,
        "workflow_execution_performed": WORKFLOW_EXECUTION_PERFORMED_FIX_210,
        "deploy_lifecycle_compose_evidence_only": GOVERNED_DEPLOY_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_210,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_210,
        "autonomous_deploy_enabled": AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
        "approval_bypass_enabled": APPROVAL_BYPASS_ENABLED_FIX_210,
        "hidden_workflow_execution_enabled": HIDDEN_WORKFLOW_EXECUTION_ENABLED_FIX_210,
        "merge_authority": MERGE_AUTHORITY_FIX_210,
        "railway_authority": RAILWAY_AUTHORITY_FIX_210,
        "vercel_authority": VERCEL_AUTHORITY_FIX_210,
        "aws_authority": AWS_AUTHORITY_FIX_210,
        "kubernetes_authority": KUBERNETES_AUTHORITY_FIX_210,
        "provider_authority": PROVIDER_AUTHORITY_FIX_210,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_210,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_210,
        "schema_version": GOVERNED_DEPLOY_LIFECYCLE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_deploy_lifecycle"] = result.governed_deploy_lifecycle
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_deploy_lifecycle(result.governed_deploy_lifecycle)
    return payload


@router.post("/mission-control/governed-deploy-lifecycle/record")
def mission_control_governed_deploy_lifecycle_record_api(
    body: GovernedDeployLifecycleRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_210,
        GOVERNED_DEPLOY_LIFECYCLE_EXECUTABLE,
        GOVERNED_DEPLOY_LIFECYCLE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_210,
    )
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_store import (
        append_governed_deploy_lifecycle_record,
    )
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    sid = (body.session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "") or None
    record, blockers = append_governed_deploy_lifecycle_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=plan_id,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_DEPLOY_LIFECYCLE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_210,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_210,
        "executable": GOVERNED_DEPLOY_LIFECYCLE_EXECUTABLE,
        "governed_deploy_lifecycle_memory_only": True,
        "detail": "Governed deploy lifecycle record persisted (deploy_authority ≠ autonomous_deploy).",
    }


@router.post("/mission-control/governed-deploy-lifecycle/handoff")
def mission_control_governed_deploy_lifecycle_handoff_api(
    body: GovernedDeployLifecycleHandoffIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_contract import (
        AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
        DEPLOY_AUTHORITY_FIX_210,
        GOVERNED_DEPLOY_HANDOFF_EXECUTABLE,
        GOVERNED_DEPLOY_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
        WORKFLOW_EXECUTION_PERFORMED_FIX_210,
    )
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
        prepare_governed_deploy_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = prepare_governed_deploy_handoff(session_id=sid)
    if not result.ok:
        raise HTTPException(status_code=400, detail={"blockers": result.blockers or ["handoff_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_DEPLOY_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
        "session_id": result.session_id,
        "deploy_handoff": result.deploy_handoff,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_210,
        "autonomous_deploy_enabled": AUTONOMOUS_DEPLOY_ENABLED_FIX_210,
        "workflow_execution_performed": WORKFLOW_EXECUTION_PERFORMED_FIX_210,
        "executable": GOVERNED_DEPLOY_HANDOFF_EXECUTABLE,
        "detail": result.detail,
    }


@router.get("/mission-control/governed-monitoring-lifecycle")
def mission_control_governed_monitoring_lifecycle_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
        AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
        DEPLOY_AUTHORITY_FIX_220,
        EXECUTION_PERFORMED_FIX_220,
        GATE_BYPASS_ENABLED_FIX_220,
        GOVERNANCE_MUTATION_PERFORMED_FIX_220,
        GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220,
        GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION,
        INCIDENT_RESPONSE_AUTHORITY_FIX_220,
        MERGE_AUTHORITY_FIX_220,
        MONITORING_AUTHORITY_FIX_220,
        MUTATION_PERFORMED_FIX_220,
        OBSERVATION_PERFORMED_FIX_220,
        PROVIDER_MUTATION_AUTHORITY_FIX_220,
        RAILWAY_AUTHORITY_FIX_220,
        ROLLBACK_AUTHORITY_FIX_220,
        WORKFLOW_EXECUTION_AUTHORITY_FIX_220,
    )
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_renderer import (
        render_governed_monitoring_lifecycle,
    )
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
        build_governed_monitoring_lifecycle,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_monitoring_lifecycle(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_220,
        "execution_performed": EXECUTION_PERFORMED_FIX_220,
        "observation_performed": OBSERVATION_PERFORMED_FIX_220,
        "monitoring_compose_evidence_only": GOVERNED_MONITORING_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_220,
        "monitoring_authority": MONITORING_AUTHORITY_FIX_220,
        "incident_response_authority": INCIDENT_RESPONSE_AUTHORITY_FIX_220,
        "autonomous_remediation_enabled": AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_220,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_220,
        "workflow_execution_authority": WORKFLOW_EXECUTION_AUTHORITY_FIX_220,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_220,
        "merge_authority": MERGE_AUTHORITY_FIX_220,
        "railway_authority": RAILWAY_AUTHORITY_FIX_220,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_220,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_220,
        "schema_version": GOVERNED_MONITORING_LIFECYCLE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_monitoring_lifecycle"] = result.governed_monitoring_lifecycle
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_monitoring_lifecycle(result.governed_monitoring_lifecycle)
    return payload


@router.post("/mission-control/governed-monitoring-lifecycle/record")
def mission_control_governed_monitoring_lifecycle_record_api(
    body: GovernedMonitoringLifecycleRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_220,
        GOVERNED_MONITORING_LIFECYCLE_EXECUTABLE,
        GOVERNED_MONITORING_LIFECYCLE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_220,
    )
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_store import (
        append_governed_monitoring_lifecycle_record,
    )
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    sid = (body.session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "") or None
    record, blockers = append_governed_monitoring_lifecycle_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=plan_id,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_MONITORING_LIFECYCLE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_220,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_220,
        "executable": GOVERNED_MONITORING_LIFECYCLE_EXECUTABLE,
        "governed_monitoring_lifecycle_memory_only": True,
        "detail": "Governed monitoring lifecycle record persisted (monitoring ≠ operational authority).",
    }


@router.post("/mission-control/governed-monitoring-lifecycle/escalate")
def mission_control_governed_monitoring_lifecycle_escalate_api(
    body: GovernedMonitoringLifecycleEscalateIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_contract import (
        AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
        GOVERNED_MONITORING_ESCALATION_EXECUTABLE,
        GOVERNED_MONITORING_LIFECYCLE_ESCALATION_SCHEMA_VERSION,
        INCIDENT_RESPONSE_AUTHORITY_FIX_220,
        MONITORING_AUTHORITY_FIX_220,
    )
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
        prepare_governed_monitoring_escalation,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = prepare_governed_monitoring_escalation(session_id=sid)
    if not result.ok:
        raise HTTPException(status_code=400, detail={"blockers": result.blockers or ["escalation_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_MONITORING_LIFECYCLE_ESCALATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "incident_escalation": result.incident_escalation,
        "monitoring_authority": MONITORING_AUTHORITY_FIX_220,
        "incident_response_authority": INCIDENT_RESPONSE_AUTHORITY_FIX_220,
        "autonomous_remediation_enabled": AUTONOMOUS_REMEDIATION_ENABLED_FIX_220,
        "executable": GOVERNED_MONITORING_ESCALATION_EXECUTABLE,
        "detail": result.detail,
    }


@router.get("/mission-control/governed-rollback-lifecycle")
def mission_control_governed_rollback_lifecycle_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
        AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
        DATABASE_MUTATION_AUTHORITY_FIX_230,
        DEPLOY_AUTHORITY_FIX_230,
        EXECUTION_PERFORMED_FIX_230,
        GATE_BYPASS_ENABLED_FIX_230,
        GOVERNANCE_MUTATION_PERFORMED_FIX_230,
        GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230,
        GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION,
        HIDDEN_RECOVERY_PATH_ENABLED_FIX_230,
        MERGE_AUTHORITY_FIX_230,
        MONITORING_AUTHORITY_FIX_230,
        MUTATION_PERFORMED_FIX_230,
        PROVIDER_MUTATION_AUTHORITY_FIX_230,
        RAILWAY_AUTHORITY_FIX_230,
        ROLLBACK_AUTHORITY_FIX_230,
        WORKFLOW_EXECUTION_PERFORMED_FIX_230,
    )
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_renderer import (
        render_governed_rollback_lifecycle,
    )
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
        build_governed_rollback_lifecycle,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_rollback_lifecycle(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_230,
        "execution_performed": EXECUTION_PERFORMED_FIX_230,
        "rollback_compose_evidence_only": GOVERNED_ROLLBACK_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_230,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_230,
        "autonomous_rollback_enabled": AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
        "workflow_execution_performed": WORKFLOW_EXECUTION_PERFORMED_FIX_230,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_230,
        "database_mutation_authority": DATABASE_MUTATION_AUTHORITY_FIX_230,
        "hidden_recovery_path_enabled": HIDDEN_RECOVERY_PATH_ENABLED_FIX_230,
        "monitoring_authority": MONITORING_AUTHORITY_FIX_230,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_230,
        "merge_authority": MERGE_AUTHORITY_FIX_230,
        "railway_authority": RAILWAY_AUTHORITY_FIX_230,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_230,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_230,
        "schema_version": GOVERNED_ROLLBACK_LIFECYCLE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_rollback_lifecycle"] = result.governed_rollback_lifecycle
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_rollback_lifecycle(result.governed_rollback_lifecycle)
    return payload


@router.post("/mission-control/governed-rollback-lifecycle/record")
def mission_control_governed_rollback_lifecycle_record_api(
    body: GovernedRollbackLifecycleRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_230,
        GOVERNED_ROLLBACK_LIFECYCLE_EXECUTABLE,
        GOVERNED_ROLLBACK_LIFECYCLE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_230,
    )
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_store import (
        append_governed_rollback_lifecycle_record,
    )
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session

    sid = (body.session_id or "default").strip()[:64] or "default"
    plan = load_issue_plan_for_session(session_id=sid)
    plan_id = str((plan or {}).get("plan_id") or "") or None
    record, blockers = append_governed_rollback_lifecycle_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=plan_id,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_ROLLBACK_LIFECYCLE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_230,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_230,
        "executable": GOVERNED_ROLLBACK_LIFECYCLE_EXECUTABLE,
        "governed_rollback_lifecycle_memory_only": True,
        "detail": "Governed rollback lifecycle record persisted (rollback ≠ autonomous rollback).",
    }


@router.post("/mission-control/governed-rollback-lifecycle/handoff")
def mission_control_governed_rollback_lifecycle_handoff_api(
    body: GovernedRollbackLifecycleHandoffIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_contract import (
        AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
        GOVERNED_ROLLBACK_HANDOFF_EXECUTABLE,
        GOVERNED_ROLLBACK_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
        ROLLBACK_AUTHORITY_FIX_230,
        WORKFLOW_EXECUTION_PERFORMED_FIX_230,
    )
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
        prepare_governed_rollback_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = prepare_governed_rollback_handoff(session_id=sid)
    if not result.ok:
        raise HTTPException(status_code=400, detail={"blockers": result.blockers or ["handoff_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_ROLLBACK_LIFECYCLE_HANDOFF_SCHEMA_VERSION,
        "session_id": result.session_id,
        "rollback_handoff": result.rollback_handoff,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_230,
        "autonomous_rollback_enabled": AUTONOMOUS_ROLLBACK_ENABLED_FIX_230,
        "workflow_execution_performed": WORKFLOW_EXECUTION_PERFORMED_FIX_230,
        "executable": GOVERNED_ROLLBACK_HANDOFF_EXECUTABLE,
        "detail": result.detail,
    }


@router.get("/mission-control/repository-knowledge-graph")
def mission_control_repository_knowledge_graph_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_contract import (
        CODE_MODIFICATION_AUTHORITY_FIX_240,
        CROSS_REPO_AUTHORITY_FIX_240,
        DEPLOY_AUTHORITY_FIX_240,
        EXECUTION_PERFORMED_FIX_240,
        GATE_BYPASS_ENABLED_FIX_240,
        GOVERNANCE_MUTATION_PERFORMED_FIX_240,
        KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
        MERGE_AUTHORITY_FIX_240,
        MUTATION_PERFORMED_FIX_240,
        REPOSITORY_AUTHORITY_FIX_240,
        REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240,
        REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION,
        ROLLBACK_AUTHORITY_FIX_240,
    )
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_renderer import (
        render_repository_knowledge_graph,
    )
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_service import (
        build_repository_knowledge_graph,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_repository_knowledge_graph(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_240,
        "execution_performed": EXECUTION_PERFORMED_FIX_240,
        "repository_compose_evidence_only": REPOSITORY_KNOWLEDGE_GRAPH_COMPOSES_EVIDENCE_ONLY_FIX_240,
        "repository_authority": REPOSITORY_AUTHORITY_FIX_240,
        "code_modification_authority": CODE_MODIFICATION_AUTHORITY_FIX_240,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_240,
        "knowledge_graph_execution": KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
        "merge_authority": MERGE_AUTHORITY_FIX_240,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_240,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_240,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_240,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_240,
        "schema_version": REPOSITORY_KNOWLEDGE_GRAPH_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["repository_knowledge_graph"] = result.repository_knowledge_graph
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_repository_knowledge_graph(result.repository_knowledge_graph)
    return payload


@router.post("/mission-control/repository-knowledge-graph/record")
def mission_control_repository_knowledge_graph_record_api(
    body: RepositoryKnowledgeGraphRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_240,
        MUTATION_PERFORMED_FIX_240,
        REPOSITORY_KNOWLEDGE_GRAPH_EXECUTABLE,
        REPOSITORY_KNOWLEDGE_GRAPH_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_service import (
        build_repository_knowledge_graph,
    )
    from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_store import (
        append_repository_knowledge_graph_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    graph = build_repository_knowledge_graph(session_id=sid)
    repository_id = str(graph.repository_knowledge_graph.get("repository_id") or "") or None
    record, blockers = append_repository_knowledge_graph_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        repository_id=repository_id,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": REPOSITORY_KNOWLEDGE_GRAPH_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_240,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_240,
        "executable": REPOSITORY_KNOWLEDGE_GRAPH_EXECUTABLE,
        "repository_knowledge_graph_memory_only": True,
        "detail": "Repository knowledge graph record persisted (intelligence ≠ authority).",
    }


@router.get("/mission-control/governed-application-generation")
def mission_control_governed_application_generation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
        APPLICATION_GENERATION_AUTHORITY_FIX_250,
        CODE_GENERATION_AUTHORITY_FIX_250,
        DEPLOYMENT_AUTHORITY_FIX_250,
        EXECUTION_PERFORMED_FIX_250,
        GATE_BYPASS_ENABLED_FIX_250,
        GOVERNANCE_MUTATION_PERFORMED_FIX_250,
        GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250,
        GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION,
        GITHUB_MUTATION_AUTHORITY_FIX_250,
        MERGE_AUTHORITY_FIX_250,
        MUTATION_PERFORMED_FIX_250,
        PROVIDER_AUTHORITY_FIX_250,
        REPOSITORY_CREATION_AUTHORITY_FIX_250,
        ROLLBACK_AUTHORITY_FIX_250,
    )
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_renderer import (
        render_governed_application_generation,
    )
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
        build_governed_application_generation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_application_generation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_250,
        "execution_performed": EXECUTION_PERFORMED_FIX_250,
        "generation_compose_evidence_only": GOVERNED_APPLICATION_GENERATION_COMPOSES_EVIDENCE_ONLY_FIX_250,
        "application_generation_authority": APPLICATION_GENERATION_AUTHORITY_FIX_250,
        "repository_creation_authority": REPOSITORY_CREATION_AUTHORITY_FIX_250,
        "github_mutation_authority": GITHUB_MUTATION_AUTHORITY_FIX_250,
        "provider_authority": PROVIDER_AUTHORITY_FIX_250,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_250,
        "code_generation_authority": CODE_GENERATION_AUTHORITY_FIX_250,
        "merge_authority": MERGE_AUTHORITY_FIX_250,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_250,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_250,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_250,
        "schema_version": GOVERNED_APPLICATION_GENERATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_application_generation"] = result.governed_application_generation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_application_generation(result.governed_application_generation)
    return payload


@router.post("/mission-control/governed-application-generation/record")
def mission_control_governed_application_generation_record_api(
    body: GovernedApplicationGenerationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_250,
        GOVERNED_APPLICATION_GENERATION_EXECUTABLE,
        GOVERNED_APPLICATION_GENERATION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_250,
    )
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_store import (
        append_governed_application_generation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_governed_application_generation_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_APPLICATION_GENERATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_250,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_250,
        "executable": GOVERNED_APPLICATION_GENERATION_EXECUTABLE,
        "governed_application_generation_memory_only": True,
        "detail": "Governed application generation record persisted (generation ≠ authority).",
    }


@router.post("/mission-control/governed-application-generation/handoff")
def mission_control_governed_application_generation_handoff_api(
    body: GovernedApplicationGenerationHandoffIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_contract import (
        APPLICATION_GENERATION_AUTHORITY_FIX_250,
        GOVERNED_APPLICATION_GENERATION_HANDOFF_EXECUTABLE,
        GOVERNED_APPLICATION_GENERATION_HANDOFF_SCHEMA_VERSION,
        REPOSITORY_CREATION_AUTHORITY_FIX_250,
    )
    from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
        prepare_governed_application_generation_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    result = prepare_governed_application_generation_handoff(session_id=sid)
    if not result.ok:
        raise HTTPException(status_code=400, detail={"blockers": result.blockers or ["handoff_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_APPLICATION_GENERATION_HANDOFF_SCHEMA_VERSION,
        "session_id": result.session_id,
        "delivery_pipeline_handoff": result.delivery_pipeline_handoff,
        "application_generation_authority": APPLICATION_GENERATION_AUTHORITY_FIX_250,
        "repository_creation_authority": REPOSITORY_CREATION_AUTHORITY_FIX_250,
        "executable": GOVERNED_APPLICATION_GENERATION_HANDOFF_EXECUTABLE,
        "detail": result.detail,
    }


@router.get("/mission-control/multi-repository-engineering-intelligence")
def mission_control_multi_repository_engineering_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
        CROSS_REPO_AUTHORITY_FIX_260,
        DEPLOY_AUTHORITY_FIX_260,
        EXECUTION_PERFORMED_FIX_260,
        GATE_BYPASS_ENABLED_FIX_260,
        GOVERNANCE_MUTATION_PERFORMED_FIX_260,
        MERGE_AUTHORITY_FIX_260,
        MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260,
        MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_260,
        PORTFOLIO_AUTHORITY_FIX_260,
        PROGRAM_DELIVERY_AUTHORITY_FIX_260,
        PROVIDER_MUTATION_AUTHORITY_FIX_260,
    )
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_renderer import (
        render_multi_repository_engineering_intelligence,
    )
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
        build_multi_repository_engineering_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_multi_repository_engineering_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_260,
        "execution_performed": EXECUTION_PERFORMED_FIX_260,
        "intelligence_compose_artifacts_only": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260,
        "portfolio_authority": PORTFOLIO_AUTHORITY_FIX_260,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_260,
        "program_delivery_authority": PROGRAM_DELIVERY_AUTHORITY_FIX_260,
        "merge_authority": MERGE_AUTHORITY_FIX_260,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_260,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_260,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_260,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_260,
        "schema_version": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["multi_repository_engineering_intelligence"] = (
            result.multi_repository_engineering_intelligence
        )
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_multi_repository_engineering_intelligence(
            result.multi_repository_engineering_intelligence
        )
    return payload


@router.post("/mission-control/multi-repository-engineering-intelligence/record")
def mission_control_multi_repository_engineering_intelligence_record_api(
    body: MultiRepositoryEngineeringIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_260,
        MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_EXECUTABLE,
        MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_260,
    )
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_store import (
        append_multi_repository_engineering_intelligence_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_multi_repository_engineering_intelligence_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            repository=body.repository,
            source_repository=body.source_repository,
            target_repository=body.target_repository,
            relationship=body.relationship,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_260,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_260,
        "executable": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_EXECUTABLE,
        "multi_repository_engineering_intelligence_memory_only": True,
        "detail": "Multi-repository engineering intelligence record persisted (portfolio ≠ authority).",
    }


@router.get("/mission-control/cross-repository-product-evolution-intelligence")
def mission_control_cross_repository_product_evolution_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
        AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
        CROSS_REPO_EXECUTION_ENABLED_FIX_261,
        CROSS_REPOSITORY_PRODUCT_EVOLUTION_COMPOSES_EVIDENCE_ONLY_FIX_261,
        CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION,
        DEPLOY_AUTHORITY_FIX_261,
        EXECUTION_PERFORMED_FIX_261,
        GATE_BYPASS_ENABLED_FIX_261,
        GOVERNANCE_MUTATION_PERFORMED_FIX_261,
        MERGE_AUTHORITY_FIX_261,
        MUTATION_PERFORMED_FIX_261,
        PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
        PROVIDER_MUTATION_AUTHORITY_FIX_261,
        REPOSITORY_MUTATION_AUTHORITY_FIX_261,
        TRUST_MUTATION_AUTHORITY_FIX_261,
    )
    from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_renderer import (
        render_cross_repository_product_evolution_intelligence,
    )
    from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
        build_cross_repository_product_evolution_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_cross_repository_product_evolution_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_261,
        "execution_performed": EXECUTION_PERFORMED_FIX_261,
        "intelligence_compose_artifacts_only": CROSS_REPOSITORY_PRODUCT_EVOLUTION_COMPOSES_EVIDENCE_ONLY_FIX_261,
        "product_evolution_authority": PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
        "automatic_improvement_enabled": AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
        "cross_repo_execution_enabled": CROSS_REPO_EXECUTION_ENABLED_FIX_261,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_261,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_261,
        "merge_authority": MERGE_AUTHORITY_FIX_261,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_261,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_261,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_261,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_261,
        "schema_version": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["cross_repository_product_evolution_intelligence"] = (
            result.cross_repository_product_evolution_intelligence
        )
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_cross_repository_product_evolution_intelligence(
            result.cross_repository_product_evolution_intelligence
        )
    return payload


@router.post("/mission-control/cross-repository-product-evolution-intelligence/record")
def mission_control_cross_repository_product_evolution_intelligence_record_api(
    body: CrossRepositoryProductEvolutionIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
        CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_EXECUTABLE,
        CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_261,
        MUTATION_PERFORMED_FIX_261,
    )
    from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_store import (
        append_cross_repository_product_evolution_intelligence_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_cross_repository_product_evolution_intelligence_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            repository=body.repository,
            domain=body.domain,
            target_repository=body.target_repository,
            opportunity_id=body.opportunity_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_261,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_261,
        "executable": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_EXECUTABLE,
        "cross_repository_product_evolution_intelligence_memory_only": True,
        "detail": "Cross-repository product evolution intelligence record persisted (evolution ≠ execution).",
    }


@router.get("/mission-control/autonomous-product-stewardship")
def mission_control_autonomous_product_stewardship_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
        AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
        AUTONOMOUS_PRODUCT_STEWARDSHIP_COMPOSES_EVIDENCE_ONLY_FIX_270,
        AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION,
        CROSS_REPO_EXECUTION_ENABLED_FIX_270,
        DEPLOYMENT_AUTHORITY_FIX_270,
        EXECUTION_PERFORMED_FIX_270,
        GATE_BYPASS_ENABLED_FIX_270,
        GOVERNANCE_MUTATION_PERFORMED_FIX_270,
        MERGE_AUTHORITY_FIX_270,
        MUTATION_PERFORMED_FIX_270,
        PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
        PROVIDER_MUTATION_AUTHORITY_FIX_270,
        REPOSITORY_MUTATION_AUTHORITY_FIX_270,
        TRUST_MUTATION_AUTHORITY_FIX_270,
    )
    from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_renderer import (
        render_autonomous_product_stewardship,
    )
    from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_service import (
        build_autonomous_product_stewardship,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_autonomous_product_stewardship(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_270,
        "execution_performed": EXECUTION_PERFORMED_FIX_270,
        "stewardship_compose_artifacts_only": AUTONOMOUS_PRODUCT_STEWARDSHIP_COMPOSES_EVIDENCE_ONLY_FIX_270,
        "product_stewardship_authority": PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
        "automatic_improvement_enabled": AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
        "cross_repo_execution_enabled": CROSS_REPO_EXECUTION_ENABLED_FIX_270,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_270,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_270,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_270,
        "merge_authority": MERGE_AUTHORITY_FIX_270,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_270,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_270,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_270,
        "schema_version": AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["autonomous_product_stewardship"] = result.autonomous_product_stewardship
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_autonomous_product_stewardship(result.autonomous_product_stewardship)
    return payload


@router.post("/mission-control/autonomous-product-stewardship/record")
def mission_control_autonomous_product_stewardship_record_api(
    body: AutonomousProductStewardshipRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
        AUTONOMOUS_PRODUCT_STEWARDSHIP_EXECUTABLE,
        AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_270,
        MUTATION_PERFORMED_FIX_270,
    )
    from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_store import (
        append_autonomous_product_stewardship_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_autonomous_product_stewardship_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            repository=body.repository,
            domain=body.domain,
            opportunity_id=body.opportunity_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": AUTONOMOUS_PRODUCT_STEWARDSHIP_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_270,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_270,
        "executable": AUTONOMOUS_PRODUCT_STEWARDSHIP_EXECUTABLE,
        "autonomous_product_stewardship_memory_only": True,
        "detail": "Autonomous product stewardship record persisted (stewardship ≠ execution).",
    }


@router.get("/mission-control/autonomous-application-lifecycle-management")
def mission_control_autonomous_application_lifecycle_management_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
        AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
        AUTONOMOUS_APPLICATION_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_280,
        AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION,
        DEPLOYMENT_AUTHORITY_FIX_280,
        EXECUTION_PERFORMED_FIX_280,
        GATE_BYPASS_ENABLED_FIX_280,
        GOVERNANCE_MUTATION_PERFORMED_FIX_280,
        LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
        MERGE_AUTHORITY_FIX_280,
        MUTATION_PERFORMED_FIX_280,
        PROVIDER_MUTATION_AUTHORITY_FIX_280,
        REPOSITORY_MUTATION_AUTHORITY_FIX_280,
        ROLLBACK_AUTHORITY_FIX_280,
        TRUST_MUTATION_AUTHORITY_FIX_280,
    )
    from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_renderer import (
        render_autonomous_application_lifecycle_management,
    )
    from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_service import (
        build_autonomous_application_lifecycle_management,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_autonomous_application_lifecycle_management(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_280,
        "execution_performed": EXECUTION_PERFORMED_FIX_280,
        "lifecycle_compose_artifacts_only": AUTONOMOUS_APPLICATION_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_280,
        "lifecycle_management_authority": LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
        "automatic_lifecycle_execution_enabled": AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_280,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_280,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_280,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_280,
        "merge_authority": MERGE_AUTHORITY_FIX_280,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_280,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_280,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_280,
        "schema_version": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["autonomous_application_lifecycle_management"] = (
            result.autonomous_application_lifecycle_management
        )
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_autonomous_application_lifecycle_management(
            result.autonomous_application_lifecycle_management
        )
    return payload


@router.post("/mission-control/autonomous-application-lifecycle-management/record")
def mission_control_autonomous_application_lifecycle_management_record_api(
    body: AutonomousApplicationLifecycleManagementRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
        AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_EXECUTABLE,
        AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_280,
        MUTATION_PERFORMED_FIX_280,
    )
    from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_store import (
        append_autonomous_application_lifecycle_management_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_autonomous_application_lifecycle_management_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            lifecycle_stage=body.lifecycle_stage,
            opportunity_id=body.opportunity_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_280,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_280,
        "executable": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_EXECUTABLE,
        "autonomous_application_lifecycle_management_memory_only": True,
        "detail": "Autonomous application lifecycle management record persisted (lifecycle ≠ execution).",
    }


@router.get("/mission-control/autonomous-business-operating-system")
def mission_control_autonomous_business_operating_system_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
        AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
        AUTONOMOUS_BUSINESS_OPERATING_COMPOSES_EVIDENCE_ONLY_FIX_290,
        AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION,
        BILLING_AUTHORITY_FIX_290,
        BUSINESS_AUTHORITY_FIX_290,
        CUSTOMER_MUTATION_AUTHORITY_FIX_290,
        DEPLOYMENT_AUTHORITY_FIX_290,
        EXECUTION_PERFORMED_FIX_290,
        GATE_BYPASS_ENABLED_FIX_290,
        GOVERNANCE_MUTATION_PERFORMED_FIX_290,
        MERGE_AUTHORITY_FIX_290,
        MUTATION_PERFORMED_FIX_290,
        PROVIDER_MUTATION_AUTHORITY_FIX_290,
        REPOSITORY_MUTATION_AUTHORITY_FIX_290,
        ROLLBACK_AUTHORITY_FIX_290,
        TRUST_MUTATION_AUTHORITY_FIX_290,
    )
    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_renderer import (
        render_autonomous_business_operating_system,
    )
    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_service import (
        build_autonomous_business_operating_system,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_autonomous_business_operating_system(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_290,
        "execution_performed": EXECUTION_PERFORMED_FIX_290,
        "business_compose_artifacts_only": AUTONOMOUS_BUSINESS_OPERATING_COMPOSES_EVIDENCE_ONLY_FIX_290,
        "business_authority": BUSINESS_AUTHORITY_FIX_290,
        "automatic_business_execution_enabled": AUTOMATIC_BUSINESS_EXECUTION_ENABLED_FIX_290,
        "customer_mutation_authority": CUSTOMER_MUTATION_AUTHORITY_FIX_290,
        "billing_authority": BILLING_AUTHORITY_FIX_290,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_290,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_290,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_290,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_290,
        "merge_authority": MERGE_AUTHORITY_FIX_290,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_290,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_290,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_290,
        "schema_version": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["autonomous_business_operating_system"] = result.autonomous_business_operating_system
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_autonomous_business_operating_system(
            result.autonomous_business_operating_system
        )
    return payload


@router.post("/mission-control/autonomous-business-operating-system/record")
def mission_control_autonomous_business_operating_system_record_api(
    body: AutonomousBusinessOperatingSystemRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_contract import (
        AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_EXECUTABLE,
        AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_290,
        MUTATION_PERFORMED_FIX_290,
    )
    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_store import (
        append_autonomous_business_operating_system_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_autonomous_business_operating_system_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            business_domain=body.business_domain,
            goal_id=body.goal_id,
            opportunity_id=body.opportunity_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_290,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_290,
        "executable": AUTONOMOUS_BUSINESS_OPERATING_SYSTEM_EXECUTABLE,
        "autonomous_business_operating_system_memory_only": True,
        "detail": "Autonomous business operating system record persisted (business ≠ authority).",
    }


@router.get("/mission-control/autonomous-capability-registry")
def mission_control_autonomous_capability_registry_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
        AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
        AUTONOMOUS_CAPABILITY_REGISTRY_COMPOSES_EVIDENCE_ONLY_FIX_295,
        AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION,
        CAPABILITY_AUTHORITY_FIX_295,
        DEPLOYMENT_AUTHORITY_FIX_295,
        EXECUTION_PERFORMED_FIX_295,
        GATE_BYPASS_ENABLED_FIX_295,
        GOVERNANCE_MUTATION_PERFORMED_FIX_295,
        MERGE_AUTHORITY_FIX_295,
        MUTATION_PERFORMED_FIX_295,
        PROVIDER_MUTATION_AUTHORITY_FIX_295,
        REPOSITORY_MUTATION_AUTHORITY_FIX_295,
        ROLLBACK_AUTHORITY_FIX_295,
        SELF_AUTHORITY_GRANTING_ENABLED_FIX_295,
        TRUST_MUTATION_AUTHORITY_FIX_295,
    )
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_renderer import (
        render_autonomous_capability_registry,
    )
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
        build_autonomous_capability_registry,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_autonomous_capability_registry(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_295,
        "execution_performed": EXECUTION_PERFORMED_FIX_295,
        "capability_compose_artifacts_only": AUTONOMOUS_CAPABILITY_REGISTRY_COMPOSES_EVIDENCE_ONLY_FIX_295,
        "capability_authority": CAPABILITY_AUTHORITY_FIX_295,
        "self_authority_granting_enabled": SELF_AUTHORITY_GRANTING_ENABLED_FIX_295,
        "automatic_capability_promotion_enabled": AUTOMATIC_CAPABILITY_PROMOTION_ENABLED_FIX_295,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_295,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_295,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_295,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_295,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_295,
        "merge_authority": MERGE_AUTHORITY_FIX_295,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_295,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_295,
        "schema_version": AUTONOMOUS_CAPABILITY_REGISTRY_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["autonomous_capability_registry"] = result.autonomous_capability_registry
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_autonomous_capability_registry(result.autonomous_capability_registry)
    return payload


@router.post("/mission-control/autonomous-capability-registry/record")
def mission_control_autonomous_capability_registry_record_api(
    body: AutonomousCapabilityRegistryRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_contract import (
        AUTONOMOUS_CAPABILITY_REGISTRY_EXECUTABLE,
        AUTONOMOUS_CAPABILITY_REGISTRY_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_295,
        MUTATION_PERFORMED_FIX_295,
    )
    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_store import (
        append_autonomous_capability_registry_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_autonomous_capability_registry_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            capability_id=body.capability_id,
            capability_domain=body.capability_domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": AUTONOMOUS_CAPABILITY_REGISTRY_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_295,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_295,
        "executable": AUTONOMOUS_CAPABILITY_REGISTRY_EXECUTABLE,
        "autonomous_capability_registry_memory_only": True,
        "detail": "Autonomous capability registry record persisted (capability awareness ≠ authority).",
    }


@router.get("/mission-control/multi-tenant-platform-foundation")
def mission_control_multi_tenant_platform_foundation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
        AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
        CROSS_TENANT_ACCESS_ENABLED_FIX_300,
        CROSS_TENANT_TRUST_ENABLED_FIX_300,
        DEPLOYMENT_AUTHORITY_FIX_300,
        EXECUTION_PERFORMED_FIX_300,
        GATE_BYPASS_ENABLED_FIX_300,
        GOVERNANCE_MUTATION_PERFORMED_FIX_300,
        MERGE_AUTHORITY_FIX_300,
        MULTI_TENANT_PLATFORM_COMPOSES_EVIDENCE_ONLY_FIX_300,
        MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_300,
        PERMISSION_ESCALATION_ENABLED_FIX_300,
        PROVIDER_MUTATION_AUTHORITY_FIX_300,
        REPOSITORY_MUTATION_AUTHORITY_FIX_300,
        ROLLBACK_AUTHORITY_FIX_300,
        TENANT_AUTHORITY_FIX_300,
        TRUST_MUTATION_AUTHORITY_FIX_300,
    )
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_renderer import (
        render_multi_tenant_platform_foundation,
    )
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
        build_multi_tenant_platform_foundation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_multi_tenant_platform_foundation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_300,
        "execution_performed": EXECUTION_PERFORMED_FIX_300,
        "tenant_compose_artifacts_only": MULTI_TENANT_PLATFORM_COMPOSES_EVIDENCE_ONLY_FIX_300,
        "tenant_authority": TENANT_AUTHORITY_FIX_300,
        "automatic_tenant_creation_enabled": AUTOMATIC_TENANT_CREATION_ENABLED_FIX_300,
        "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_300,
        "cross_tenant_trust_enabled": CROSS_TENANT_TRUST_ENABLED_FIX_300,
        "permission_escalation_enabled": PERMISSION_ESCALATION_ENABLED_FIX_300,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_300,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_300,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_300,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_300,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_300,
        "merge_authority": MERGE_AUTHORITY_FIX_300,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_300,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_300,
        "schema_version": MULTI_TENANT_PLATFORM_FOUNDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["multi_tenant_platform_foundation"] = result.multi_tenant_platform_foundation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_multi_tenant_platform_foundation(result.multi_tenant_platform_foundation)
    return payload


@router.post("/mission-control/multi-tenant-platform-foundation/record")
def mission_control_multi_tenant_platform_foundation_record_api(
    body: MultiTenantPlatformFoundationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_300,
        MULTI_TENANT_PLATFORM_FOUNDATION_EXECUTABLE,
        MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_300,
    )
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_store import (
        append_multi_tenant_platform_foundation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_multi_tenant_platform_foundation_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            tenant_domain=body.tenant_domain,
            organization_id=body.organization_id,
            workspace_id=body.workspace_id,
            project_id=body.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": MULTI_TENANT_PLATFORM_FOUNDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_300,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_300,
        "executable": MULTI_TENANT_PLATFORM_FOUNDATION_EXECUTABLE,
        "multi_tenant_platform_foundation_memory_only": True,
        "detail": "Multi-tenant platform foundation record persisted (multi-tenant ≠ governance bypass).",
    }


@router.get("/mission-control/tenant-onboarding-activation")
def mission_control_tenant_onboarding_activation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
        AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301,
        AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
        CROSS_TENANT_ACCESS_ENABLED_FIX_301,
        EXECUTION_PERFORMED_FIX_301,
        GOVERNANCE_MUTATION_PERFORMED_FIX_301,
        MUTATION_PERFORMED_FIX_301,
        ONBOARDING_AUTHORITY_FIX_301,
        PROVIDER_MUTATION_AUTHORITY_FIX_301,
        SECRET_COLLECTION_ENABLED_FIX_301,
        TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION,
        TENANT_ONBOARDING_COMPOSES_EVIDENCE_ONLY_FIX_301,
        TRUST_MUTATION_AUTHORITY_FIX_301,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_renderer import (
        render_tenant_onboarding_activation,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
        build_tenant_onboarding_activation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_tenant_onboarding_activation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_301,
        "execution_performed": EXECUTION_PERFORMED_FIX_301,
        "onboarding_compose_artifacts_only": TENANT_ONBOARDING_COMPOSES_EVIDENCE_ONLY_FIX_301,
        "onboarding_authority": ONBOARDING_AUTHORITY_FIX_301,
        "automatic_provisioning_enabled": AUTOMATIC_PROVISIONING_ENABLED_FIX_301,
        "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_301,
        "secret_collection_enabled": SECRET_COLLECTION_ENABLED_FIX_301,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_301,
        "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_301,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_301,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_301,
        "schema_version": TENANT_ONBOARDING_ACTIVATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["tenant_onboarding_activation"] = result.tenant_onboarding_activation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_tenant_onboarding_activation(result.tenant_onboarding_activation)
    return payload


@router.post("/mission-control/tenant-onboarding-activation/record")
def mission_control_tenant_onboarding_activation_record_api(
    body: TenantOnboardingActivationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_301,
        MUTATION_PERFORMED_FIX_301,
        TENANT_ONBOARDING_ACTIVATION_EXECUTABLE,
        TENANT_ONBOARDING_ACTIVATION_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
        append_tenant_onboarding_activation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_tenant_onboarding_activation_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            onboarding_step=body.onboarding_step,
            organization_id=body.organization_id,
            workspace_id=body.workspace_id,
            project_id=body.project_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": TENANT_ONBOARDING_ACTIVATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_301,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_301,
        "executable": TENANT_ONBOARDING_ACTIVATION_EXECUTABLE,
        "tenant_onboarding_activation_memory_only": True,
        "detail": "Tenant onboarding activation record persisted (onboarding guidance ≠ platform authority).",
    }


@router.get("/mission-control/identity-access-hardening")
def mission_control_identity_access_hardening_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
        AUTHORIZATION_AUTHORITY_FIX_302,
        AUTHORIZATION_BYPASS_ENABLED_FIX_302,
        AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
        AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302,
        CROSS_TENANT_ACCESS_ENABLED_FIX_302,
        EXECUTION_PERFORMED_FIX_302,
        GOVERNANCE_MUTATION_PERFORMED_FIX_302,
        IDENTITY_ACCESS_COMPOSES_EVIDENCE_ONLY_FIX_302,
        IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_302,
    )
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_renderer import (
        render_identity_access_hardening,
    )
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
        build_identity_access_hardening,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_identity_access_hardening(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_302,
        "execution_performed": EXECUTION_PERFORMED_FIX_302,
        "identity_access_compose_artifacts_only": IDENTITY_ACCESS_COMPOSES_EVIDENCE_ONLY_FIX_302,
        "authorization_authority": AUTHORIZATION_AUTHORITY_FIX_302,
        "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
        "automatic_role_escalation_enabled": AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302,
        "cross_tenant_access_enabled": CROSS_TENANT_ACCESS_ENABLED_FIX_302,
        "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_302,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_302,
        "schema_version": IDENTITY_ACCESS_HARDENING_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["identity_access_hardening"] = result.identity_access_hardening
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_identity_access_hardening(result.identity_access_hardening)
    return payload


@router.post("/mission-control/identity-access-hardening/record")
def mission_control_identity_access_hardening_record_api(
    body: IdentityAccessHardeningRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_302,
        IDENTITY_ACCESS_HARDENING_EXECUTABLE,
        IDENTITY_ACCESS_HARDENING_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_302,
    )
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_store import (
        append_identity_access_hardening_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_identity_access_hardening_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            organization_id=body.organization_id,
            user_id=body.user_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": IDENTITY_ACCESS_HARDENING_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_302,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_302,
        "executable": IDENTITY_ACCESS_HARDENING_EXECUTABLE,
        "identity_access_hardening_memory_only": True,
        "detail": "Identity access hardening record persisted (enforcement ≠ escalation).",
    }


@router.get("/mission-control/provider-connection-experience")
def mission_control_provider_connection_experience_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
        AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
        EXECUTION_PERFORMED_FIX_303,
        GOVERNANCE_MUTATION_PERFORMED_FIX_303,
        MUTATION_PERFORMED_FIX_303,
        PERMISSION_ESCALATION_ENABLED_FIX_303,
        PROVIDER_CONNECTION_AUTHORITY_FIX_303,
        PROVIDER_CONNECTION_COMPOSES_EVIDENCE_ONLY_FIX_303,
        PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION,
        PROVIDER_MUTATION_AUTHORITY_FIX_303,
        SECRET_COLLECTION_ENABLED_FIX_303,
    )
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_renderer import (
        render_provider_connection_experience,
    )
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
        build_provider_connection_experience,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_provider_connection_experience(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_303,
        "execution_performed": EXECUTION_PERFORMED_FIX_303,
        "provider_connection_compose_artifacts_only": PROVIDER_CONNECTION_COMPOSES_EVIDENCE_ONLY_FIX_303,
        "provider_connection_authority": PROVIDER_CONNECTION_AUTHORITY_FIX_303,
        "automatic_provider_connection_enabled": AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_303,
        "secret_collection_enabled": SECRET_COLLECTION_ENABLED_FIX_303,
        "permission_escalation_enabled": PERMISSION_ESCALATION_ENABLED_FIX_303,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_303,
        "schema_version": PROVIDER_CONNECTION_EXPERIENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["provider_connection_experience"] = result.provider_connection_experience
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_provider_connection_experience(result.provider_connection_experience)
    return payload


@router.post("/mission-control/provider-connection-experience/record")
def mission_control_provider_connection_experience_record_api(
    body: ProviderConnectionExperienceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_303,
        MUTATION_PERFORMED_FIX_303,
        PROVIDER_CONNECTION_EXPERIENCE_EXECUTABLE,
        PROVIDER_CONNECTION_EXPERIENCE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
        append_provider_connection_experience_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_provider_connection_experience_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            provider=body.provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": PROVIDER_CONNECTION_EXPERIENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_303,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_303,
        "executable": PROVIDER_CONNECTION_EXPERIENCE_EXECUTABLE,
        "provider_connection_experience_memory_only": True,
        "detail": "Provider connection experience record persisted (guidance ≠ mutation).",
    }


@router.get("/mission-control/channel-integration-foundation")
def mission_control_channel_integration_foundation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
        AUTHORIZATION_BYPASS_ENABLED_FIX_304,
        AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
        CHANNEL_AUTHORITY_FIX_304,
        CHANNEL_INTEGRATION_COMPOSES_EVIDENCE_ONLY_FIX_304,
        CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION,
        CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
        CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
        EXECUTION_PERFORMED_FIX_304,
        GOVERNANCE_MUTATION_PERFORMED_FIX_304,
        MUTATION_PERFORMED_FIX_304,
    )
    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_renderer import (
        render_channel_integration_foundation,
    )
    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
        build_channel_integration_foundation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_channel_integration_foundation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_304,
        "execution_performed": EXECUTION_PERFORMED_FIX_304,
        "channel_integration_compose_artifacts_only": CHANNEL_INTEGRATION_COMPOSES_EVIDENCE_ONLY_FIX_304,
        "channel_authority": CHANNEL_AUTHORITY_FIX_304,
        "automatic_channel_provisioning_enabled": AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
        "cross_channel_identity_bypass_enabled": CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
        "cross_tenant_channel_access_enabled": CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
        "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_304,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_304,
        "schema_version": CHANNEL_INTEGRATION_FOUNDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["channel_integration_foundation"] = result.channel_integration_foundation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_channel_integration_foundation(result.channel_integration_foundation)
    return payload


@router.post("/mission-control/channel-integration-foundation/record")
def mission_control_channel_integration_foundation_record_api(
    body: ChannelIntegrationFoundationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
        CHANNEL_INTEGRATION_FOUNDATION_EXECUTABLE,
        CHANNEL_INTEGRATION_FOUNDATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_304,
        MUTATION_PERFORMED_FIX_304,
    )
    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_store import (
        append_channel_integration_foundation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_channel_integration_foundation_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            channel=body.channel,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CHANNEL_INTEGRATION_FOUNDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_304,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_304,
        "executable": CHANNEL_INTEGRATION_FOUNDATION_EXECUTABLE,
        "channel_integration_foundation_memory_only": True,
        "detail": "Channel integration foundation record persisted (integration ≠ duplication).",
    }


@router.get("/mission-control/billing-entitlements-foundation")
def mission_control_billing_entitlements_foundation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
        AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305,
        AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
        AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305,
        BILLING_AUTHORITY_FIX_305,
        BILLING_ENTITLEMENTS_COMPOSES_EVIDENCE_ONLY_FIX_305,
        BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_305,
        GOVERNANCE_MUTATION_PERFORMED_FIX_305,
        MUTATION_PERFORMED_FIX_305,
        PAYMENT_PROCESSING_ENABLED_FIX_305,
    )
    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_renderer import (
        render_billing_entitlements_foundation,
    )
    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
        build_billing_entitlements_foundation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_billing_entitlements_foundation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_305,
        "execution_performed": EXECUTION_PERFORMED_FIX_305,
        "billing_entitlements_compose_artifacts_only": BILLING_ENTITLEMENTS_COMPOSES_EVIDENCE_ONLY_FIX_305,
        "billing_authority": BILLING_AUTHORITY_FIX_305,
        "automatic_subscription_creation_enabled": AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305,
        "automatic_plan_upgrade_enabled": AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
        "automatic_plan_downgrade_enabled": AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305,
        "payment_processing_enabled": PAYMENT_PROCESSING_ENABLED_FIX_305,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_305,
        "schema_version": BILLING_ENTITLEMENTS_FOUNDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["billing_entitlements_foundation"] = result.billing_entitlements_foundation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_billing_entitlements_foundation(result.billing_entitlements_foundation)
    return payload


@router.post("/mission-control/billing-entitlements-foundation/record")
def mission_control_billing_entitlements_foundation_record_api(
    body: BillingEntitlementsFoundationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
        BILLING_ENTITLEMENTS_FOUNDATION_EXECUTABLE,
        BILLING_ENTITLEMENTS_FOUNDATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_305,
        MUTATION_PERFORMED_FIX_305,
    )
    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_store import (
        append_billing_entitlements_foundation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_billing_entitlements_foundation_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            plan=body.plan,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": BILLING_ENTITLEMENTS_FOUNDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_305,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_305,
        "executable": BILLING_ENTITLEMENTS_FOUNDATION_EXECUTABLE,
        "billing_entitlements_foundation_memory_only": True,
        "detail": "Billing entitlements foundation record persisted (entitlements ≠ authority).",
    }


@router.get("/mission-control/customer-administration-console")
def mission_control_customer_administration_console_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
        ADMINISTRATION_AUTHORITY_FIX_306,
        AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306,
        AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
        BILLING_MUTATION_AUTHORITY_FIX_306,
        CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306,
        CUSTOMER_ADMINISTRATION_COMPOSES_EVIDENCE_ONLY_FIX_306,
        CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_306,
        GOVERNANCE_MUTATION_PERFORMED_FIX_306,
        MUTATION_PERFORMED_FIX_306,
        TRUST_MUTATION_AUTHORITY_FIX_306,
    )
    from aethos_core.mission_control.customer_administration_console.customer_administration_console_renderer import (
        render_customer_administration_console,
    )
    from aethos_core.mission_control.customer_administration_console.customer_administration_console_service import (
        build_customer_administration_console,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_customer_administration_console(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_306,
        "execution_performed": EXECUTION_PERFORMED_FIX_306,
        "customer_administration_compose_artifacts_only": CUSTOMER_ADMINISTRATION_COMPOSES_EVIDENCE_ONLY_FIX_306,
        "administration_authority": ADMINISTRATION_AUTHORITY_FIX_306,
        "automatic_user_creation_enabled": AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
        "automatic_permission_granting_enabled": AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306,
        "cross_tenant_administration_enabled": CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_306,
        "billing_mutation_authority": BILLING_MUTATION_AUTHORITY_FIX_306,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_306,
        "schema_version": CUSTOMER_ADMINISTRATION_CONSOLE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["customer_administration_console"] = result.customer_administration_console
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_customer_administration_console(result.customer_administration_console)
    return payload


@router.post("/mission-control/customer-administration-console/record")
def mission_control_customer_administration_console_record_api(
    body: CustomerAdministrationConsoleRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
        CUSTOMER_ADMINISTRATION_CONSOLE_EXECUTABLE,
        CUSTOMER_ADMINISTRATION_CONSOLE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_306,
        MUTATION_PERFORMED_FIX_306,
    )
    from aethos_core.mission_control.customer_administration_console.customer_administration_console_store import (
        append_customer_administration_console_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_customer_administration_console_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CUSTOMER_ADMINISTRATION_CONSOLE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_306,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_306,
        "executable": CUSTOMER_ADMINISTRATION_CONSOLE_EXECUTABLE,
        "customer_administration_console_memory_only": True,
        "detail": "Customer administration console record persisted (visibility ≠ authority).",
    }


@router.get("/mission-control/customer-usage-audit-portal")
def mission_control_customer_usage_audit_portal_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
        AUDIT_AUTHORITY_FIX_307,
        AUDIT_MUTATION_ENABLED_FIX_307,
        AUTHORIZATION_BYPASS_ENABLED_FIX_307,
        CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
        CUSTOMER_USAGE_AUDIT_COMPOSES_EVIDENCE_ONLY_FIX_307,
        CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION,
        EVIDENCE_MUTATION_ENABLED_FIX_307,
        EXECUTION_PERFORMED_FIX_307,
        GOVERNANCE_MUTATION_PERFORMED_FIX_307,
        MUTATION_PERFORMED_FIX_307,
    )
    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_renderer import (
        render_customer_usage_audit_portal,
    )
    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
        build_customer_usage_audit_portal,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_customer_usage_audit_portal(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_307,
        "execution_performed": EXECUTION_PERFORMED_FIX_307,
        "customer_usage_audit_compose_artifacts_only": CUSTOMER_USAGE_AUDIT_COMPOSES_EVIDENCE_ONLY_FIX_307,
        "audit_authority": AUDIT_AUTHORITY_FIX_307,
        "audit_mutation_enabled": AUDIT_MUTATION_ENABLED_FIX_307,
        "evidence_mutation_enabled": EVIDENCE_MUTATION_ENABLED_FIX_307,
        "cross_tenant_audit_access_enabled": CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
        "authorization_bypass_enabled": AUTHORIZATION_BYPASS_ENABLED_FIX_307,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_307,
        "schema_version": CUSTOMER_USAGE_AUDIT_PORTAL_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["customer_usage_audit_portal"] = result.customer_usage_audit_portal
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_customer_usage_audit_portal(result.customer_usage_audit_portal)
    return payload


@router.post("/mission-control/customer-usage-audit-portal/record")
def mission_control_customer_usage_audit_portal_record_api(
    body: CustomerUsageAuditPortalRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
        CUSTOMER_USAGE_AUDIT_PORTAL_EXECUTABLE,
        CUSTOMER_USAGE_AUDIT_PORTAL_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_307,
        MUTATION_PERFORMED_FIX_307,
    )
    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_store import (
        append_customer_usage_audit_portal_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_customer_usage_audit_portal_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CUSTOMER_USAGE_AUDIT_PORTAL_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_307,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_307,
        "executable": CUSTOMER_USAGE_AUDIT_PORTAL_EXECUTABLE,
        "customer_usage_audit_portal_memory_only": True,
        "detail": "Customer usage audit portal record persisted (visibility ≠ authority).",
    }


@router.get("/mission-control/payment-integration-readiness")
def mission_control_payment_integration_readiness_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
        AUTOMATIC_CHARGING_ENABLED_FIX_308,
        AUTOMATIC_REFUND_ENABLED_FIX_308,
        CREDIT_CARD_STORAGE_ENABLED_FIX_308,
        EXECUTION_PERFORMED_FIX_308,
        GOVERNANCE_MUTATION_PERFORMED_FIX_308,
        MUTATION_PERFORMED_FIX_308,
        PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION,
        PAYMENT_PROCESSING_ENABLED_FIX_308,
        PAYMENT_READINESS_COMPOSES_EVIDENCE_ONLY_FIX_308,
        SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308,
    )
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_renderer import (
        render_payment_integration_readiness,
    )
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
        build_payment_integration_readiness,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_payment_integration_readiness(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_308,
        "execution_performed": EXECUTION_PERFORMED_FIX_308,
        "payment_readiness_compose_artifacts_only": PAYMENT_READINESS_COMPOSES_EVIDENCE_ONLY_FIX_308,
        "payment_processing_enabled": PAYMENT_PROCESSING_ENABLED_FIX_308,
        "credit_card_storage_enabled": CREDIT_CARD_STORAGE_ENABLED_FIX_308,
        "automatic_charging_enabled": AUTOMATIC_CHARGING_ENABLED_FIX_308,
        "automatic_refund_enabled": AUTOMATIC_REFUND_ENABLED_FIX_308,
        "subscription_mutation_authority": SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_308,
        "schema_version": PAYMENT_INTEGRATION_READINESS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["payment_integration_readiness"] = result.payment_integration_readiness
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_payment_integration_readiness(result.payment_integration_readiness)
    return payload


@router.post("/mission-control/payment-integration-readiness/record")
def mission_control_payment_integration_readiness_record_api(
    body: PaymentIntegrationReadinessRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_308,
        MUTATION_PERFORMED_FIX_308,
        PAYMENT_INTEGRATION_READINESS_EXECUTABLE,
        PAYMENT_INTEGRATION_READINESS_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_store import (
        append_payment_integration_readiness_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_payment_integration_readiness_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            provider=body.provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": PAYMENT_INTEGRATION_READINESS_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_308,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_308,
        "executable": PAYMENT_INTEGRATION_READINESS_EXECUTABLE,
        "payment_integration_readiness_memory_only": True,
        "detail": "Payment integration readiness record persisted (readiness ≠ processing).",
    }


@router.get("/mission-control/saas-launch-readiness-assessment")
def mission_control_saas_launch_readiness_assessment_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
        AUTOMATIC_LAUNCH_ENABLED_FIX_309,
        AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309,
        CUSTOMER_PROVISIONING_AUTHORITY_FIX_309,
        EXECUTION_PERFORMED_FIX_309,
        GOVERNANCE_MUTATION_PERFORMED_FIX_309,
        LAUNCH_ASSESSMENT_COMPOSES_EVIDENCE_ONLY_FIX_309,
        LAUNCH_AUTHORITY_FIX_309,
        MUTATION_PERFORMED_FIX_309,
        SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION,
        TRUST_MUTATION_AUTHORITY_FIX_309,
    )
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_renderer import (
        render_saas_launch_readiness_assessment,
    )
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
        build_saas_launch_readiness_assessment,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_saas_launch_readiness_assessment(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_309,
        "execution_performed": EXECUTION_PERFORMED_FIX_309,
        "launch_assessment_compose_artifacts_only": LAUNCH_ASSESSMENT_COMPOSES_EVIDENCE_ONLY_FIX_309,
        "launch_authority": LAUNCH_AUTHORITY_FIX_309,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_309,
        "automatic_readiness_promotion_enabled": AUTOMATIC_READINESS_PROMOTION_ENABLED_FIX_309,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_309,
        "customer_provisioning_authority": CUSTOMER_PROVISIONING_AUTHORITY_FIX_309,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_309,
        "schema_version": SAAS_LAUNCH_READINESS_ASSESSMENT_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["saas_launch_readiness_assessment"] = result.saas_launch_readiness_assessment
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_saas_launch_readiness_assessment(result.saas_launch_readiness_assessment)
    return payload


@router.post("/mission-control/saas-launch-readiness-assessment/record")
def mission_control_saas_launch_readiness_assessment_record_api(
    body: SaasLaunchReadinessAssessmentRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_309,
        MUTATION_PERFORMED_FIX_309,
        SAAS_LAUNCH_READINESS_ASSESSMENT_EXECUTABLE,
        SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_store import (
        append_saas_launch_readiness_assessment_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_saas_launch_readiness_assessment_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": SAAS_LAUNCH_READINESS_ASSESSMENT_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_309,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_309,
        "executable": SAAS_LAUNCH_READINESS_ASSESSMENT_EXECUTABLE,
        "saas_launch_readiness_assessment_memory_only": True,
        "detail": "SaaS launch readiness assessment record persisted (assessment ≠ launch authority).",
    }


@router.get("/mission-control/customer-support-success-foundation")
def mission_control_customer_support_success_foundation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
        AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
        AUTOMATIC_ESCALATION_ENABLED_FIX_310,
        AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310,
        AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310,
        CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
        CUSTOMER_SUPPORT_COMPOSES_EVIDENCE_ONLY_FIX_310,
        CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_310,
        GOVERNANCE_MUTATION_PERFORMED_FIX_310,
        MUTATION_PERFORMED_FIX_310,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_renderer import (
        render_customer_support_success_foundation,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
        build_customer_support_success_foundation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_customer_support_success_foundation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_310,
        "execution_performed": EXECUTION_PERFORMED_FIX_310,
        "customer_support_compose_artifacts_only": CUSTOMER_SUPPORT_COMPOSES_EVIDENCE_ONLY_FIX_310,
        "customer_support_authority": CUSTOMER_SUPPORT_AUTHORITY_FIX_310,
        "automatic_customer_contact_enabled": AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_310,
        "automatic_escalation_enabled": AUTOMATIC_ESCALATION_ENABLED_FIX_310,
        "automatic_support_resolution_enabled": AUTOMATIC_SUPPORT_RESOLUTION_ENABLED_FIX_310,
        "automatic_plan_upgrade_enabled": AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_310,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_310,
        "schema_version": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["customer_support_success_foundation"] = result.customer_support_success_foundation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_customer_support_success_foundation(
            result.customer_support_success_foundation
        )
    return payload


@router.post("/mission-control/customer-support-success-foundation")
def mission_control_customer_support_success_foundation_record_api(
    body: CustomerSupportSuccessFoundationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_contract import (
        CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_EXECUTABLE,
        CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_310,
        MUTATION_PERFORMED_FIX_310,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_store import (
        append_customer_support_success_foundation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_customer_support_success_foundation_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
            org_id=body.org_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_310,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_310,
        "executable": CUSTOMER_SUPPORT_SUCCESS_FOUNDATION_EXECUTABLE,
        "customer_support_success_foundation_memory_only": True,
        "detail": "Customer support success foundation record persisted (visibility ≠ authority).",
    }


@router.get("/mission-control/public-product-experience")
def mission_control_public_product_experience_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
        AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
        EXECUTION_PERFORMED_FIX_311,
        GOVERNANCE_MUTATION_PERFORMED_FIX_311,
        MUTATION_PERFORMED_FIX_311,
        PROVIDER_MUTATION_AUTHORITY_FIX_311,
        PUBLIC_PRODUCT_AUTHORITY_FIX_311,
        PUBLIC_PRODUCT_COMPOSES_EVIDENCE_ONLY_FIX_311,
        PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION,
        TENANT_MUTATION_AUTHORITY_FIX_311,
        TRUST_MUTATION_AUTHORITY_FIX_311,
    )
    from aethos_core.mission_control.public_product_experience.public_product_experience_renderer import (
        render_public_product_experience,
    )
    from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
        build_public_product_experience,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_public_product_experience(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_311,
        "execution_performed": EXECUTION_PERFORMED_FIX_311,
        "public_product_compose_artifacts_only": PUBLIC_PRODUCT_COMPOSES_EVIDENCE_ONLY_FIX_311,
        "public_product_authority": PUBLIC_PRODUCT_AUTHORITY_FIX_311,
        "automatic_customer_onboarding_enabled": AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_311,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_311,
        "tenant_mutation_authority": TENANT_MUTATION_AUTHORITY_FIX_311,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_311,
        "schema_version": PUBLIC_PRODUCT_EXPERIENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["public_product_experience"] = result.public_product_experience
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_public_product_experience(result.public_product_experience)
    return payload


@router.post("/mission-control/public-product-experience")
def mission_control_public_product_experience_record_api(
    body: PublicProductExperienceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_311,
        MUTATION_PERFORMED_FIX_311,
        PUBLIC_PRODUCT_EXPERIENCE_EXECUTABLE,
        PUBLIC_PRODUCT_EXPERIENCE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.public_product_experience.public_product_experience_store import (
        append_public_product_experience_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_public_product_experience_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": PUBLIC_PRODUCT_EXPERIENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_311,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_311,
        "executable": PUBLIC_PRODUCT_EXPERIENCE_EXECUTABLE,
        "public_product_experience_memory_only": True,
        "detail": "Public product experience record persisted (experience ≠ platform authority).",
    }


@router.get("/mission-control/limited-beta-launch-program")
def mission_control_limited_beta_launch_program_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
        AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312,
        AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
        AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312,
        AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312,
        BETA_AUTHORITY_FIX_312,
        BETA_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_312,
        EXECUTION_PERFORMED_FIX_312,
        GOVERNANCE_MUTATION_PERFORMED_FIX_312,
        LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_312,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_renderer import (
        render_limited_beta_launch_program,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
        build_limited_beta_launch_program,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_limited_beta_launch_program(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_312,
        "execution_performed": EXECUTION_PERFORMED_FIX_312,
        "beta_program_compose_artifacts_only": BETA_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_312,
        "beta_authority": BETA_AUTHORITY_FIX_312,
        "automatic_user_admission_enabled": AUTOMATIC_USER_ADMISSION_ENABLED_FIX_312,
        "automatic_customer_provisioning_enabled": AUTOMATIC_CUSTOMER_PROVISIONING_ENABLED_FIX_312,
        "automatic_plan_assignment_enabled": AUTOMATIC_PLAN_ASSIGNMENT_ENABLED_FIX_312,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_312,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_312,
        "schema_version": LIMITED_BETA_LAUNCH_PROGRAM_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["limited_beta_launch_program"] = result.limited_beta_launch_program
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_limited_beta_launch_program(result.limited_beta_launch_program)
    return payload


@router.post("/mission-control/limited-beta-launch-program")
def mission_control_limited_beta_launch_program_record_api(
    body: LimitedBetaLaunchProgramRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_312,
        LIMITED_BETA_LAUNCH_PROGRAM_EXECUTABLE,
        LIMITED_BETA_LAUNCH_PROGRAM_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_312,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
        append_limited_beta_launch_program_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_limited_beta_launch_program_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
            cohort_id=body.cohort_id,
            candidate_id=body.candidate_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": LIMITED_BETA_LAUNCH_PROGRAM_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_312,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_312,
        "executable": LIMITED_BETA_LAUNCH_PROGRAM_EXECUTABLE,
        "limited_beta_launch_program_memory_only": True,
        "detail": "Limited beta launch program record persisted (management ≠ provisioning authority).",
    }


@router.get("/mission-control/launch-operations-center")
def mission_control_launch_operations_center_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
        AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313,
        AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313,
        AUTOMATIC_LAUNCH_ENABLED_FIX_313,
        AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313,
        EXECUTION_PERFORMED_FIX_313,
        GOVERNANCE_MUTATION_PERFORMED_FIX_313,
        LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
        LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION,
        LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_313,
        MUTATION_PERFORMED_FIX_313,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_renderer import (
        render_launch_operations_center,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
        build_launch_operations_center,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_launch_operations_center(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_313,
        "execution_performed": EXECUTION_PERFORMED_FIX_313,
        "launch_operations_compose_artifacts_only": LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_313,
        "launch_operations_authority": LAUNCH_OPERATIONS_AUTHORITY_FIX_313,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_313,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_313,
        "automatic_customer_admission_enabled": AUTOMATIC_CUSTOMER_ADMISSION_ENABLED_FIX_313,
        "automatic_provider_mutation_enabled": AUTOMATIC_PROVIDER_MUTATION_ENABLED_FIX_313,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_313,
        "schema_version": LAUNCH_OPERATIONS_CENTER_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["launch_operations_center"] = result.launch_operations_center
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_launch_operations_center(result.launch_operations_center)
    return payload


@router.post("/mission-control/launch-operations-center")
def mission_control_launch_operations_center_record_api(
    body: LaunchOperationsCenterRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_313,
        LAUNCH_OPERATIONS_CENTER_EXECUTABLE,
        LAUNCH_OPERATIONS_CENTER_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_313,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_store import (
        append_launch_operations_center_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_launch_operations_center_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": LAUNCH_OPERATIONS_CENTER_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_313,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_313,
        "executable": LAUNCH_OPERATIONS_CENTER_EXECUTABLE,
        "launch_operations_center_memory_only": True,
        "detail": "Launch operations center record persisted (visibility ≠ launch authority).",
    }


@router.get("/mission-control/public-launch-readiness-freeze")
def mission_control_public_launch_readiness_freeze_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
        AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314,
        AUTOMATIC_LAUNCH_ENABLED_FIX_314,
        EXECUTION_PERFORMED_FIX_314,
        GOVERNANCE_MUTATION_PERFORMED_FIX_314,
        LAUNCH_DECISION_AUTHORITY_FIX_314,
        LAUNCH_FREEZE_AUTHORITY_FIX_314,
        LAUNCH_READINESS_FREEZE_COMPOSES_EVIDENCE_ONLY_FIX_314,
        MUTATION_PERFORMED_FIX_314,
        PILOT_REEXECUTION_PERFORMED_FIX_314,
        PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION,
        TRUST_MUTATION_AUTHORITY_FIX_314,
    )
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_renderer import (
        render_public_launch_readiness_freeze,
    )
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
        build_public_launch_readiness_freeze,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_public_launch_readiness_freeze(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_314,
        "execution_performed": EXECUTION_PERFORMED_FIX_314,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_314,
        "launch_readiness_freeze_compose_artifacts_only": LAUNCH_READINESS_FREEZE_COMPOSES_EVIDENCE_ONLY_FIX_314,
        "launch_freeze_authority": LAUNCH_FREEZE_AUTHORITY_FIX_314,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_314,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_314,
        "launch_decision_authority": LAUNCH_DECISION_AUTHORITY_FIX_314,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_314,
        "schema_version": PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["public_launch_readiness_freeze"] = result.public_launch_readiness_freeze
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_public_launch_readiness_freeze(result.public_launch_readiness_freeze)
    return payload


@router.post("/mission-control/public-launch-readiness-freeze")
def mission_control_public_launch_readiness_freeze_record_api(
    body: PublicLaunchReadinessFreezeRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_314,
        MUTATION_PERFORMED_FIX_314,
        PUBLIC_LAUNCH_READINESS_FREEZE_EXECUTABLE,
        PUBLIC_LAUNCH_READINESS_FREEZE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
        append_public_launch_readiness_freeze_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_public_launch_readiness_freeze_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": PUBLIC_LAUNCH_READINESS_FREEZE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_314,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_314,
        "executable": PUBLIC_LAUNCH_READINESS_FREEZE_EXECUTABLE,
        "public_launch_readiness_freeze_memory_only": True,
        "detail": "Public launch readiness freeze record persisted (freeze ≠ launch authority).",
    }


@router.get("/mission-control/launch-decision-package")
def mission_control_launch_decision_package_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
        AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315,
        AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315,
        AUTOMATIC_LAUNCH_ENABLED_FIX_315,
        EXECUTION_PERFORMED_FIX_315,
        GOVERNANCE_MUTATION_PERFORMED_FIX_315,
        LAUNCH_DECISION_AUTHORITY_FIX_315,
        LAUNCH_DECISION_PACKAGE_COMPOSES_EVIDENCE_ONLY_FIX_315,
        LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_315,
        PILOT_EXECUTION_PERFORMED_FIX_315,
        TRUST_MUTATION_AUTHORITY_FIX_315,
    )
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_renderer import (
        render_launch_decision_package,
    )
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
        build_launch_decision_package,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_launch_decision_package(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_315,
        "execution_performed": EXECUTION_PERFORMED_FIX_315,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_315,
        "launch_decision_package_compose_artifacts_only": LAUNCH_DECISION_PACKAGE_COMPOSES_EVIDENCE_ONLY_FIX_315,
        "launch_decision_authority": LAUNCH_DECISION_AUTHORITY_FIX_315,
        "automatic_launch_approval_enabled": AUTOMATIC_LAUNCH_APPROVAL_ENABLED_FIX_315,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_315,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_315,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_315,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_315,
        "schema_version": LAUNCH_DECISION_PACKAGE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["launch_decision_package"] = result.launch_decision_package
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_launch_decision_package(result.launch_decision_package)
    return payload


@router.post("/mission-control/launch-decision-package")
def mission_control_launch_decision_package_record_api(
    body: LaunchDecisionPackageRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_315,
        LAUNCH_DECISION_PACKAGE_EXECUTABLE,
        LAUNCH_DECISION_PACKAGE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_315,
    )
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_store import (
        append_launch_decision_package_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_launch_decision_package_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": LAUNCH_DECISION_PACKAGE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_315,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_315,
        "executable": LAUNCH_DECISION_PACKAGE_EXECUTABLE,
        "launch_decision_package_memory_only": True,
        "detail": "Launch decision package record persisted (package ≠ launch decision).",
    }


@router.get("/mission-control/post-launch-operations-baseline")
def mission_control_post_launch_operations_baseline_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
        AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316,
        AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316,
        AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
        EXECUTION_PERFORMED_FIX_316,
        GOVERNANCE_MUTATION_PERFORMED_FIX_316,
        MUTATION_PERFORMED_FIX_316,
        PILOT_EXECUTION_PERFORMED_FIX_316,
        POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
        POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION,
        POST_LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_316,
        TRUST_MUTATION_AUTHORITY_FIX_316,
    )
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_renderer import (
        render_post_launch_operations_baseline,
    )
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_service import (
        build_post_launch_operations_baseline,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_post_launch_operations_baseline(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_316,
        "execution_performed": EXECUTION_PERFORMED_FIX_316,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_316,
        "post_launch_operations_compose_artifacts_only": POST_LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_316,
        "post_launch_operations_authority": POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
        "automatic_operational_execution_enabled": AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
        "automatic_customer_contact_enabled": AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316,
        "automatic_incident_response_enabled": AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_316,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_316,
        "schema_version": POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["post_launch_operations_baseline"] = result.post_launch_operations_baseline
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_post_launch_operations_baseline(result.post_launch_operations_baseline)
    return payload


@router.post("/mission-control/post-launch-operations-baseline")
def mission_control_post_launch_operations_baseline_record_api(
    body: PostLaunchOperationsBaselineRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_316,
        MUTATION_PERFORMED_FIX_316,
        POST_LAUNCH_OPERATIONS_BASELINE_EXECUTABLE,
        POST_LAUNCH_OPERATIONS_BASELINE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_store import (
        append_post_launch_operations_baseline_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_post_launch_operations_baseline_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": POST_LAUNCH_OPERATIONS_BASELINE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_316,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_316,
        "executable": POST_LAUNCH_OPERATIONS_BASELINE_EXECUTABLE,
        "post_launch_operations_baseline_memory_only": True,
        "detail": "Post-launch operations baseline record persisted (baseline ≠ operational authority).",
    }


@router.get("/mission-control/continuous-product-improvement")
def mission_control_continuous_product_improvement_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
        AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317,
        AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317,
        AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317,
        CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317,
        CONTINUOUS_IMPROVEMENT_COMPOSES_EVIDENCE_ONLY_FIX_317,
        CONTINUOUS_PRODUCT_IMPROVEMENT_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_317,
        GOVERNANCE_MUTATION_PERFORMED_FIX_317,
        MUTATION_PERFORMED_FIX_317,
    )
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_renderer import (
        render_continuous_product_improvement,
    )
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_service import (
        build_continuous_product_improvement,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_continuous_product_improvement(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_317,
        "execution_performed": EXECUTION_PERFORMED_FIX_317,
        "continuous_improvement_compose_artifacts_only": CONTINUOUS_IMPROVEMENT_COMPOSES_EVIDENCE_ONLY_FIX_317,
        "continuous_improvement_authority": CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317,
        "automatic_backlog_creation_enabled": AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317,
        "automatic_feature_creation_enabled": AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_317,
        "automatic_product_mutation_enabled": AUTOMATIC_PRODUCT_MUTATION_ENABLED_FIX_317,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_317,
        "schema_version": CONTINUOUS_PRODUCT_IMPROVEMENT_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["continuous_product_improvement"] = result.continuous_product_improvement
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_continuous_product_improvement(result.continuous_product_improvement)
    return payload


@router.post("/mission-control/continuous-product-improvement")
def mission_control_continuous_product_improvement_record_api(
    body: ContinuousProductImprovementRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
        CONTINUOUS_PRODUCT_IMPROVEMENT_EXECUTABLE,
        CONTINUOUS_PRODUCT_IMPROVEMENT_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_317,
        MUTATION_PERFORMED_FIX_317,
    )
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_store import (
        append_improvement_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_improvement_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CONTINUOUS_PRODUCT_IMPROVEMENT_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_317,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_317,
        "executable": CONTINUOUS_PRODUCT_IMPROVEMENT_EXECUTABLE,
        "continuous_product_improvement_memory_only": True,
        "detail": "Continuous product improvement record persisted (recommendations ≠ automatic execution).",
    }


@router.get("/mission-control/product-analytics-foundation")
def mission_control_product_analytics_foundation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
        ANALYTICS_AUTHORITY_FIX_318,
        AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318,
        AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318,
        AUTOMATIC_USER_TARGETING_ENABLED_FIX_318,
        EXECUTION_PERFORMED_FIX_318,
        GOVERNANCE_MUTATION_PERFORMED_FIX_318,
        MUTATION_PERFORMED_FIX_318,
        PRODUCT_ANALYTICS_COMPOSES_EVIDENCE_ONLY_FIX_318,
        PRODUCT_ANALYTICS_FOUNDATION_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_renderer import (
        render_product_analytics_foundation,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
        build_product_analytics_foundation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_product_analytics_foundation(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_318,
        "execution_performed": EXECUTION_PERFORMED_FIX_318,
        "product_analytics_compose_artifacts_only": PRODUCT_ANALYTICS_COMPOSES_EVIDENCE_ONLY_FIX_318,
        "analytics_authority": ANALYTICS_AUTHORITY_FIX_318,
        "automatic_behavior_modification_enabled": AUTOMATIC_BEHAVIOR_MODIFICATION_ENABLED_FIX_318,
        "automatic_user_targeting_enabled": AUTOMATIC_USER_TARGETING_ENABLED_FIX_318,
        "automatic_plan_mutation_enabled": AUTOMATIC_PLAN_MUTATION_ENABLED_FIX_318,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_318,
        "schema_version": PRODUCT_ANALYTICS_FOUNDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["product_analytics_foundation"] = result.product_analytics_foundation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_product_analytics_foundation(result.product_analytics_foundation)
    return payload


@router.post("/mission-control/product-analytics-foundation")
def mission_control_product_analytics_foundation_record_api(
    body: ProductAnalyticsFoundationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_318,
        MUTATION_PERFORMED_FIX_318,
        PRODUCT_ANALYTICS_FOUNDATION_EXECUTABLE,
        PRODUCT_ANALYTICS_FOUNDATION_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_store import (
        append_analytics_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_analytics_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": PRODUCT_ANALYTICS_FOUNDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_318,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_318,
        "executable": PRODUCT_ANALYTICS_FOUNDATION_EXECUTABLE,
        "product_analytics_foundation_memory_only": True,
        "detail": "Product analytics record persisted (analytics ≠ surveillance; no behavior modification).",
    }


@router.get("/mission-control/customer-feedback-intelligence")
def mission_control_customer_feedback_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
        AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319,
        AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319,
        AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319,
        CUSTOMER_FEEDBACK_COMPOSES_EVIDENCE_ONLY_FIX_319,
        CUSTOMER_FEEDBACK_INTELLIGENCE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_319,
        FEEDBACK_AUTHORITY_FIX_319,
        GOVERNANCE_MUTATION_PERFORMED_FIX_319,
        MUTATION_PERFORMED_FIX_319,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_renderer import (
        render_customer_feedback_intelligence,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service import (
        build_customer_feedback_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_customer_feedback_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_319,
        "execution_performed": EXECUTION_PERFORMED_FIX_319,
        "customer_feedback_compose_artifacts_only": CUSTOMER_FEEDBACK_COMPOSES_EVIDENCE_ONLY_FIX_319,
        "feedback_authority": FEEDBACK_AUTHORITY_FIX_319,
        "automatic_feature_creation_enabled": AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_319,
        "automatic_backlog_creation_enabled": AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_319,
        "automatic_customer_contact_enabled": AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_319,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_319,
        "schema_version": CUSTOMER_FEEDBACK_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["customer_feedback_intelligence"] = result.customer_feedback_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_customer_feedback_intelligence(result.customer_feedback_intelligence)
    return payload


@router.post("/mission-control/customer-feedback-intelligence")
def mission_control_customer_feedback_intelligence_record_api(
    body: CustomerFeedbackIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_contract import (
        CUSTOMER_FEEDBACK_INTELLIGENCE_EXECUTABLE,
        CUSTOMER_FEEDBACK_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_319,
        MUTATION_PERFORMED_FIX_319,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
        append_feedback_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_feedback_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CUSTOMER_FEEDBACK_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_319,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_319,
        "executable": CUSTOMER_FEEDBACK_INTELLIGENCE_EXECUTABLE,
        "customer_feedback_intelligence_memory_only": True,
        "detail": "Customer feedback record persisted (feedback informs decisions; no automatic work creation).",
    }


@router.get("/mission-control/growth-adoption-intelligence")
def mission_control_growth_adoption_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
        AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320,
        AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320,
        AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320,
        AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320,
        EXECUTION_PERFORMED_FIX_320,
        GOVERNANCE_MUTATION_PERFORMED_FIX_320,
        GROWTH_ADOPTION_COMPOSES_EVIDENCE_ONLY_FIX_320,
        GROWTH_ADOPTION_INTELLIGENCE_SCHEMA_VERSION,
        GROWTH_AUTHORITY_FIX_320,
        MUTATION_PERFORMED_FIX_320,
    )
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_renderer import (
        render_growth_adoption_intelligence,
    )
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service import (
        build_growth_adoption_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_growth_adoption_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_320,
        "execution_performed": EXECUTION_PERFORMED_FIX_320,
        "growth_adoption_compose_artifacts_only": GROWTH_ADOPTION_COMPOSES_EVIDENCE_ONLY_FIX_320,
        "growth_authority": GROWTH_AUTHORITY_FIX_320,
        "automatic_customer_outreach_enabled": AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_320,
        "automatic_plan_upgrade_enabled": AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_320,
        "automatic_customer_targeting_enabled": AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_320,
        "automatic_growth_execution_enabled": AUTOMATIC_GROWTH_EXECUTION_ENABLED_FIX_320,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_320,
        "schema_version": GROWTH_ADOPTION_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["growth_adoption_intelligence"] = result.growth_adoption_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_growth_adoption_intelligence(result.growth_adoption_intelligence)
    return payload


@router.post("/mission-control/growth-adoption-intelligence")
def mission_control_growth_adoption_intelligence_record_api(
    body: GrowthAdoptionIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_320,
        GROWTH_ADOPTION_INTELLIGENCE_EXECUTABLE,
        GROWTH_ADOPTION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_320,
    )
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_store import (
        append_growth_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_growth_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": GROWTH_ADOPTION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_320,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_320,
        "executable": GROWTH_ADOPTION_INTELLIGENCE_EXECUTABLE,
        "growth_adoption_intelligence_memory_only": True,
        "detail": "Growth record persisted (growth intelligence identifies opportunities; humans decide actions).",
    }


@router.get("/mission-control/customer-journey-intelligence")
def mission_control_customer_journey_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
        AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321,
        AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321,
        AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321,
        CUSTOMER_JOURNEY_COMPOSES_EVIDENCE_ONLY_FIX_321,
        CUSTOMER_JOURNEY_INTELLIGENCE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_321,
        GOVERNANCE_MUTATION_PERFORMED_FIX_321,
        JOURNEY_AUTHORITY_FIX_321,
        MUTATION_PERFORMED_FIX_321,
    )
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_renderer import (
        render_customer_journey_intelligence,
    )
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_service import (
        build_customer_journey_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_customer_journey_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_321,
        "execution_performed": EXECUTION_PERFORMED_FIX_321,
        "customer_journey_compose_artifacts_only": CUSTOMER_JOURNEY_COMPOSES_EVIDENCE_ONLY_FIX_321,
        "journey_authority": JOURNEY_AUTHORITY_FIX_321,
        "automatic_customer_targeting_enabled": AUTOMATIC_CUSTOMER_TARGETING_ENABLED_FIX_321,
        "automatic_customer_intervention_enabled": AUTOMATIC_CUSTOMER_INTERVENTION_ENABLED_FIX_321,
        "automatic_journey_modification_enabled": AUTOMATIC_JOURNEY_MODIFICATION_ENABLED_FIX_321,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_321,
        "schema_version": CUSTOMER_JOURNEY_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["customer_journey_intelligence"] = result.customer_journey_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_customer_journey_intelligence(result.customer_journey_intelligence)
    return payload


@router.post("/mission-control/customer-journey-intelligence")
def mission_control_customer_journey_intelligence_record_api(
    body: CustomerJourneyIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_contract import (
        CUSTOMER_JOURNEY_INTELLIGENCE_EXECUTABLE,
        CUSTOMER_JOURNEY_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_321,
        MUTATION_PERFORMED_FIX_321,
    )
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_store import (
        append_journey_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_journey_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CUSTOMER_JOURNEY_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_321,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_321,
        "executable": CUSTOMER_JOURNEY_INTELLIGENCE_EXECUTABLE,
        "customer_journey_intelligence_memory_only": True,
        "detail": "Journey record persisted (journey intelligence observes paths; humans decide improvements).",
    }


@router.get("/mission-control/product-market-fit-intelligence")
def mission_control_product_market_fit_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
        AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322,
        AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322,
        AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322,
        EXECUTION_PERFORMED_FIX_322,
        GOVERNANCE_MUTATION_PERFORMED_FIX_322,
        MUTATION_PERFORMED_FIX_322,
        PMF_AUTHORITY_FIX_322,
        PRODUCT_MARKET_FIT_COMPOSES_EVIDENCE_ONLY_FIX_322,
        PRODUCT_MARKET_FIT_INTELLIGENCE_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_renderer import (
        render_product_market_fit_intelligence,
    )
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_service import (
        build_product_market_fit_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_product_market_fit_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_322,
        "execution_performed": EXECUTION_PERFORMED_FIX_322,
        "product_market_fit_compose_artifacts_only": PRODUCT_MARKET_FIT_COMPOSES_EVIDENCE_ONLY_FIX_322,
        "pmf_authority": PMF_AUTHORITY_FIX_322,
        "automatic_product_strategy_enabled": AUTOMATIC_PRODUCT_STRATEGY_ENABLED_FIX_322,
        "automatic_feature_creation_enabled": AUTOMATIC_FEATURE_CREATION_ENABLED_FIX_322,
        "automatic_pricing_changes_enabled": AUTOMATIC_PRICING_CHANGES_ENABLED_FIX_322,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_322,
        "schema_version": PRODUCT_MARKET_FIT_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["product_market_fit_intelligence"] = result.product_market_fit_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_product_market_fit_intelligence(result.product_market_fit_intelligence)
    return payload


@router.post("/mission-control/product-market-fit-intelligence")
def mission_control_product_market_fit_intelligence_record_api(
    body: ProductMarketFitIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_322,
        MUTATION_PERFORMED_FIX_322,
        PRODUCT_MARKET_FIT_INTELLIGENCE_EXECUTABLE,
        PRODUCT_MARKET_FIT_INTELLIGENCE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
        append_pmf_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_pmf_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": PRODUCT_MARKET_FIT_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_322,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_322,
        "executable": PRODUCT_MARKET_FIT_INTELLIGENCE_EXECUTABLE,
        "product_market_fit_intelligence_memory_only": True,
        "detail": "PMF record persisted (PMF intelligence evaluates evidence; humans decide strategy).",
    }


@router.get("/mission-control/customer-value-realization-intelligence")
def mission_control_customer_value_realization_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
        AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323,
        AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323,
        AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323,
        CUSTOMER_VALUE_REALIZATION_COMPOSES_EVIDENCE_ONLY_FIX_323,
        CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_323,
        GOVERNANCE_MUTATION_PERFORMED_FIX_323,
        MUTATION_PERFORMED_FIX_323,
        VALUE_REALIZATION_AUTHORITY_FIX_323,
    )
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_renderer import (
        render_customer_value_realization_intelligence,
    )
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_service import (
        build_customer_value_realization_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_customer_value_realization_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_323,
        "execution_performed": EXECUTION_PERFORMED_FIX_323,
        "customer_value_realization_compose_artifacts_only": CUSTOMER_VALUE_REALIZATION_COMPOSES_EVIDENCE_ONLY_FIX_323,
        "value_realization_authority": VALUE_REALIZATION_AUTHORITY_FIX_323,
        "automatic_customer_success_enabled": AUTOMATIC_CUSTOMER_SUCCESS_ENABLED_FIX_323,
        "automatic_customer_outreach_enabled": AUTOMATIC_CUSTOMER_OUTREACH_ENABLED_FIX_323,
        "automatic_goal_modification_enabled": AUTOMATIC_GOAL_MODIFICATION_ENABLED_FIX_323,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_323,
        "schema_version": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["customer_value_realization_intelligence"] = result.customer_value_realization_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_customer_value_realization_intelligence(result.customer_value_realization_intelligence)
    return payload


@router.post("/mission-control/customer-value-realization-intelligence")
def mission_control_customer_value_realization_intelligence_record_api(
    body: CustomerValueRealizationIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_contract import (
        CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_EXECUTABLE,
        CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_323,
        MUTATION_PERFORMED_FIX_323,
    )
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_store import (
        append_value_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_value_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_323,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_323,
        "executable": CUSTOMER_VALUE_REALIZATION_INTELLIGENCE_EXECUTABLE,
        "customer_value_realization_intelligence_memory_only": True,
        "detail": "Value record persisted (value realization measures outcomes; humans decide customer strategy).",
    }


@router.get("/mission-control/strategic-portfolio-intelligence")
def mission_control_strategic_portfolio_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
        AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324,
        AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324,
        AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324,
        AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324,
        EXECUTION_PERFORMED_FIX_324,
        GOVERNANCE_MUTATION_PERFORMED_FIX_324,
        MUTATION_PERFORMED_FIX_324,
        STRATEGIC_AUTHORITY_FIX_324,
        STRATEGIC_PORTFOLIO_COMPOSES_EVIDENCE_ONLY_FIX_324,
        STRATEGIC_PORTFOLIO_INTELLIGENCE_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_renderer import (
        render_strategic_portfolio_intelligence,
    )
    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_service import (
        build_strategic_portfolio_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_strategic_portfolio_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_324,
        "execution_performed": EXECUTION_PERFORMED_FIX_324,
        "strategic_portfolio_compose_artifacts_only": STRATEGIC_PORTFOLIO_COMPOSES_EVIDENCE_ONLY_FIX_324,
        "strategic_authority": STRATEGIC_AUTHORITY_FIX_324,
        "automatic_budget_allocation_enabled": AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_324,
        "automatic_project_creation_enabled": AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_324,
        "automatic_resource_reallocation_enabled": AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_324,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_324,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_324,
        "schema_version": STRATEGIC_PORTFOLIO_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["strategic_portfolio_intelligence"] = result.strategic_portfolio_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_strategic_portfolio_intelligence(result.strategic_portfolio_intelligence)
    return payload


@router.post("/mission-control/strategic-portfolio-intelligence")
def mission_control_strategic_portfolio_intelligence_record_api(
    body: StrategicPortfolioIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_324,
        MUTATION_PERFORMED_FIX_324,
        STRATEGIC_PORTFOLIO_INTELLIGENCE_EXECUTABLE,
        STRATEGIC_PORTFOLIO_INTELLIGENCE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_store import (
        append_strategic_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_strategic_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": STRATEGIC_PORTFOLIO_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_324,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_324,
        "executable": STRATEGIC_PORTFOLIO_INTELLIGENCE_EXECUTABLE,
        "strategic_portfolio_intelligence_memory_only": True,
        "detail": "Strategic record persisted (portfolio intelligence evaluates evidence; humans decide investment).",
    }


@router.get("/mission-control/executive-decision-intelligence")
def mission_control_executive_decision_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
        AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325,
        AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325,
        AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325,
        AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325,
        EXECUTION_PERFORMED_FIX_325,
        EXECUTIVE_AUTHORITY_FIX_325,
        EXECUTIVE_DECISION_COMPOSES_EVIDENCE_ONLY_FIX_325,
        EXECUTIVE_DECISION_INTELLIGENCE_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_325,
        MUTATION_PERFORMED_FIX_325,
    )
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_renderer import (
        render_executive_decision_intelligence,
    )
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
        build_executive_decision_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_executive_decision_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_325,
        "execution_performed": EXECUTION_PERFORMED_FIX_325,
        "executive_decision_compose_artifacts_only": EXECUTIVE_DECISION_COMPOSES_EVIDENCE_ONLY_FIX_325,
        "executive_authority": EXECUTIVE_AUTHORITY_FIX_325,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_325,
        "automatic_resource_reallocation_enabled": AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_325,
        "automatic_budget_allocation_enabled": AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_325,
        "automatic_decision_execution_enabled": AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_325,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_325,
        "schema_version": EXECUTIVE_DECISION_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["executive_decision_intelligence"] = result.executive_decision_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_executive_decision_intelligence(result.executive_decision_intelligence)
    return payload


@router.post("/mission-control/executive-decision-intelligence")
def mission_control_executive_decision_intelligence_record_api(
    body: ExecutiveDecisionIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
        EXECUTIVE_DECISION_INTELLIGENCE_EXECUTABLE,
        EXECUTIVE_DECISION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_325,
        MUTATION_PERFORMED_FIX_325,
    )
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_store import (
        append_executive_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_executive_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": EXECUTIVE_DECISION_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_325,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_325,
        "executable": EXECUTIVE_DECISION_INTELLIGENCE_EXECUTABLE,
        "executive_decision_intelligence_memory_only": True,
        "detail": "Executive record persisted (AethOS recommends; humans decide).",
    }


@router.get("/mission-control/strategic-planning-intelligence")
def mission_control_strategic_planning_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
        AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326,
        AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326,
        AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326,
        AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326,
        EXECUTION_PERFORMED_FIX_326,
        GOVERNANCE_MUTATION_PERFORMED_FIX_326,
        MUTATION_PERFORMED_FIX_326,
        STRATEGIC_PLANNING_AUTHORITY_FIX_326,
        STRATEGIC_PLANNING_COMPOSES_EVIDENCE_ONLY_FIX_326,
        STRATEGIC_PLANNING_INTELLIGENCE_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_renderer import (
        render_strategic_planning_intelligence,
    )
    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_service import (
        build_strategic_planning_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_strategic_planning_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_326,
        "execution_performed": EXECUTION_PERFORMED_FIX_326,
        "strategic_planning_compose_artifacts_only": STRATEGIC_PLANNING_COMPOSES_EVIDENCE_ONLY_FIX_326,
        "strategic_planning_authority": STRATEGIC_PLANNING_AUTHORITY_FIX_326,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_326,
        "automatic_project_creation_enabled": AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_326,
        "automatic_budget_allocation_enabled": AUTOMATIC_BUDGET_ALLOCATION_ENABLED_FIX_326,
        "automatic_resource_assignment_enabled": AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_326,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_326,
        "schema_version": STRATEGIC_PLANNING_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["strategic_planning_intelligence"] = result.strategic_planning_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_strategic_planning_intelligence(result.strategic_planning_intelligence)
    return payload


@router.post("/mission-control/strategic-planning-intelligence")
def mission_control_strategic_planning_intelligence_record_api(
    body: StrategicPlanningIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_326,
        MUTATION_PERFORMED_FIX_326,
        STRATEGIC_PLANNING_INTELLIGENCE_EXECUTABLE,
        STRATEGIC_PLANNING_INTELLIGENCE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_store import (
        append_planning_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_planning_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": STRATEGIC_PLANNING_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_326,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_326,
        "executable": STRATEGIC_PLANNING_INTELLIGENCE_EXECUTABLE,
        "strategic_planning_intelligence_memory_only": True,
        "detail": "Planning record persisted (AethOS generates options; humans choose plans).",
    }


@router.get("/mission-control/enterprise-program-intelligence")
def mission_control_enterprise_program_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
        AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327,
        AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327,
        AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327,
        AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327,
        ENTERPRISE_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_327,
        ENTERPRISE_PROGRAM_INTELLIGENCE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_327,
        GOVERNANCE_MUTATION_PERFORMED_FIX_327,
        MUTATION_PERFORMED_FIX_327,
        PROGRAM_AUTHORITY_FIX_327,
    )
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_renderer import (
        render_enterprise_program_intelligence,
    )
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_service import (
        build_enterprise_program_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_enterprise_program_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_327,
        "execution_performed": EXECUTION_PERFORMED_FIX_327,
        "enterprise_program_compose_artifacts_only": ENTERPRISE_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_327,
        "program_authority": PROGRAM_AUTHORITY_FIX_327,
        "automatic_project_creation_enabled": AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327,
        "automatic_program_execution_enabled": AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327,
        "automatic_resource_assignment_enabled": AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327,
        "automatic_dependency_resolution_enabled": AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_327,
        "schema_version": ENTERPRISE_PROGRAM_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["enterprise_program_intelligence"] = result.enterprise_program_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_enterprise_program_intelligence(result.enterprise_program_intelligence)
    return payload


@router.post("/mission-control/enterprise-program-intelligence")
def mission_control_enterprise_program_intelligence_record_api(
    body: EnterpriseProgramIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
        ENTERPRISE_PROGRAM_INTELLIGENCE_EXECUTABLE,
        ENTERPRISE_PROGRAM_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_327,
        MUTATION_PERFORMED_FIX_327,
    )
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_store import (
        append_program_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_program_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": ENTERPRISE_PROGRAM_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_327,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_327,
        "executable": ENTERPRISE_PROGRAM_INTELLIGENCE_EXECUTABLE,
        "enterprise_program_intelligence_memory_only": True,
        "detail": "Program record persisted (AethOS evaluates programs; humans execute programs).",
    }


@router.get("/mission-control/organizational-effectiveness-intelligence")
def mission_control_organizational_effectiveness_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
        AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328,
        AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328,
        AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328,
        AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328,
        EXECUTION_PERFORMED_FIX_328,
        GOVERNANCE_MUTATION_PERFORMED_FIX_328,
        MUTATION_PERFORMED_FIX_328,
        ORGANIZATIONAL_AUTHORITY_FIX_328,
        ORGANIZATIONAL_EFFECTIVENESS_COMPOSES_EVIDENCE_ONLY_FIX_328,
        ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_renderer import (
        render_organizational_effectiveness_intelligence,
    )
    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_service import (
        build_organizational_effectiveness_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_organizational_effectiveness_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_328,
        "execution_performed": EXECUTION_PERFORMED_FIX_328,
        "organizational_effectiveness_compose_artifacts_only": ORGANIZATIONAL_EFFECTIVENESS_COMPOSES_EVIDENCE_ONLY_FIX_328,
        "organizational_authority": ORGANIZATIONAL_AUTHORITY_FIX_328,
        "automatic_role_changes_enabled": AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328,
        "automatic_governance_changes_enabled": AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328,
        "automatic_resource_reallocation_enabled": AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328,
        "automatic_organizational_changes_enabled": AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_328,
        "schema_version": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["organizational_effectiveness_intelligence"] = result.organizational_effectiveness_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_organizational_effectiveness_intelligence(
            result.organizational_effectiveness_intelligence
        )
    return payload


@router.post("/mission-control/organizational-effectiveness-intelligence")
def mission_control_organizational_effectiveness_intelligence_record_api(
    body: OrganizationalEffectivenessIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_328,
        MUTATION_PERFORMED_FIX_328,
        ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_EXECUTABLE,
        ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_store import (
        append_organizational_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_organizational_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_328,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_328,
        "executable": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_EXECUTABLE,
        "organizational_effectiveness_intelligence_memory_only": True,
        "detail": "Organization record persisted (AethOS evaluates effectiveness; humans manage organizations).",
    }


@router.get("/mission-control/enterprise-operating-review-intelligence")
def mission_control_enterprise_operating_review_intelligence_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
        AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329,
        AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329,
        AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329,
        AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329,
        ENTERPRISE_OPERATING_REVIEW_COMPOSES_EVIDENCE_ONLY_FIX_329,
        ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_329,
        GOVERNANCE_MUTATION_PERFORMED_FIX_329,
        MUTATION_PERFORMED_FIX_329,
        OPERATING_REVIEW_AUTHORITY_FIX_329,
    )
    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_renderer import (
        render_enterprise_operating_review_intelligence,
    )
    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_service import (
        build_enterprise_operating_review_intelligence,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_enterprise_operating_review_intelligence(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_329,
        "execution_performed": EXECUTION_PERFORMED_FIX_329,
        "enterprise_operating_review_compose_artifacts_only": ENTERPRISE_OPERATING_REVIEW_COMPOSES_EVIDENCE_ONLY_FIX_329,
        "operating_review_authority": OPERATING_REVIEW_AUTHORITY_FIX_329,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_329,
        "automatic_program_execution_enabled": AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_329,
        "automatic_organizational_changes_enabled": AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_329,
        "automatic_decision_execution_enabled": AUTOMATIC_DECISION_EXECUTION_ENABLED_FIX_329,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_329,
        "schema_version": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["enterprise_operating_review_intelligence"] = result.enterprise_operating_review_intelligence
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_enterprise_operating_review_intelligence(
            result.enterprise_operating_review_intelligence
        )
    return payload


@router.post("/mission-control/enterprise-operating-review-intelligence")
def mission_control_enterprise_operating_review_intelligence_record_api(
    body: EnterpriseOperatingReviewIntelligenceRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_contract import (
        ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_EXECUTABLE,
        ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_329,
        MUTATION_PERFORMED_FIX_329,
    )
    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_store import (
        append_operating_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_operating_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_329,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_329,
        "executable": ENTERPRISE_OPERATING_REVIEW_INTELLIGENCE_EXECUTABLE,
        "enterprise_operating_review_intelligence_memory_only": True,
        "detail": "Operating review record persisted (AethOS synthesizes evidence; humans make decisions).",
    }


@router.get("/mission-control/executive-operating-system-dashboard")
def mission_control_executive_operating_system_dashboard_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
        AUTOMATIC_DECISION_ENABLED_FIX_330,
        AUTOMATIC_EXECUTION_ENABLED_FIX_330,
        AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330,
        AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330,
        EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330,
        EXECUTIVE_DASHBOARD_COMPOSES_EVIDENCE_ONLY_FIX_330,
        EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_330,
        GOVERNANCE_MUTATION_PERFORMED_FIX_330,
        MUTATION_PERFORMED_FIX_330,
    )
    from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_renderer import (
        render_executive_operating_system_dashboard,
    )
    from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_service import (
        build_executive_operating_system_dashboard_board,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_executive_operating_system_dashboard_board(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_330,
        "execution_performed": EXECUTION_PERFORMED_FIX_330,
        "executive_dashboard_compose_artifacts_only": EXECUTIVE_DASHBOARD_COMPOSES_EVIDENCE_ONLY_FIX_330,
        "executive_dashboard_authority": EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330,
        "automatic_execution_enabled": AUTOMATIC_EXECUTION_ENABLED_FIX_330,
        "automatic_decision_enabled": AUTOMATIC_DECISION_ENABLED_FIX_330,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330,
        "automatic_operational_execution_enabled": AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_330,
        "schema_version": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["executive_operating_system_dashboard"] = result.executive_operating_system_dashboard
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_executive_operating_system_dashboard(
            result.executive_operating_system_dashboard
        )
    return payload


@router.post("/mission-control/executive-operating-system-dashboard")
def mission_control_executive_operating_system_dashboard_record_api(
    body: ExecutiveOperatingSystemDashboardRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
        EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_EXECUTABLE,
        EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_330,
        MUTATION_PERFORMED_FIX_330,
    )
    from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_store import (
        append_dashboard_review_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    try:
        record = append_dashboard_review_record(
            kind=body.kind,
            content=body.content,
            session_id=sid,
            domain=body.domain,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"blockers": [str(exc)]}) from exc

    return {
        "ok": True,
        "schema_version": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_330,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_330,
        "executable": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_EXECUTABLE,
        "executive_operating_system_dashboard_memory_only": True,
        "detail": "Dashboard review record persisted (The dashboard summarizes; humans decide).",
    }


@router.get("/mission-control/pilotos-ui-trust-report-freeze")
def mission_control_pilotos_ui_trust_report_freeze_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_contract import (
        AUTOMATIC_EXPANSION_ENABLED_FIX_192,
        CROSS_REPO_AUTHORITY_FIX_192,
        EXECUTION_PERFORMED_FIX_192,
        GATE_BYPASS_ENABLED_FIX_192,
        GOVERNANCE_MUTATION_PERFORMED_FIX_192,
        MUTATION_PERFORMED_FIX_192,
        PILOTOS_UI_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        PILOT_EXECUTION_AUTHORITY_FIX_192,
        PILOT_REEXECUTION_PERFORMED_FIX_192,
        TRUST_GRANTING_AUTHORITY_FIX_192,
        TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_192,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_renderer import (
        render_pilotos_ui_trust_report_freeze,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
        build_pilotos_ui_trust_report_freeze,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_pilotos_ui_trust_report_freeze(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "pilotos_ui_trust_report_freeze_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_192,
        "execution_performed": EXECUTION_PERFORMED_FIX_192,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_192,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_192,
        "pilot_execution_authority": PILOT_EXECUTION_AUTHORITY_FIX_192,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_192,
        "automatic_expansion_enabled": AUTOMATIC_EXPANSION_ENABLED_FIX_192,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_192,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_192,
        "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_192,
        "schema_version": PILOTOS_UI_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["pilotos_ui_trust_report_freeze"] = result.pilotos_ui_trust_report_freeze
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_pilotos_ui_trust_report_freeze(result.pilotos_ui_trust_report_freeze)
    return payload


@router.post("/mission-control/pilotos-ui-trust-report-freeze/record")
def mission_control_pilotos_ui_trust_report_freeze_record_api(
    body: PilotosUiTrustReportFreezeRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_192,
        MUTATION_PERFORMED_FIX_192,
        PILOTOS_UI_TRUST_REPORT_FREEZE_EXECUTABLE,
        PILOTOS_UI_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
        append_pilotos_ui_trust_report_freeze_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_pilotos_ui_trust_report_freeze_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": PILOTOS_UI_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_192,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_192,
        "executable": PILOTOS_UI_TRUST_REPORT_FREEZE_EXECUTABLE,
        "pilotos_ui_trust_report_freeze_memory_only": True,
        "detail": "PilotOS UI trust report freeze record persisted (trust_freeze ≠ trust_granting).",
    }


@router.get("/mission-control/governed-task-execution-coordination")
def mission_control_governed_task_execution_coordination_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_172,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_172,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172,
        CODE_WRITE_ENABLED_FIX_172,
        EXECUTION_PERFORMED_FIX_172,
        GATE_BYPASS_ENABLED_FIX_172,
        GOVERNANCE_MUTATION_PERFORMED_FIX_172,
        GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION,
        MERGE_DEPLOY_ENABLED_FIX_172,
        MUTATION_PERFORMED_FIX_172,
        PR_ACTION_ENABLED_FIX_172,
        RAILWAY_MUTATION_ENABLED_FIX_172,
        TIER_ESCALATION_ENABLED_FIX_172,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_renderer import (
        render_governed_task_execution_coordination,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_service import (
        build_governed_task_execution_coordination,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_task_execution_coordination(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "governed_task_execution_coordination_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_172,
        "execution_performed": EXECUTION_PERFORMED_FIX_172,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_172,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_172,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_172,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_172,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_172,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_172,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_172,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_172,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_172,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_172,
        "schema_version": GOVERNED_TASK_EXECUTION_COORDINATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_task_execution_coordination"] = result.governed_task_execution_coordination
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_task_execution_coordination(
            result.governed_task_execution_coordination
        )
    return payload


@router.post("/mission-control/governed-task-execution-coordination/record")
def mission_control_governed_task_execution_coordination_record_api(
    body: GovernedTaskExecutionCoordinationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_service import (
        build_bounded_execution_participation,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
        GOVERNANCE_MUTATION_PERFORMED_FIX_172,
        GOVERNED_TASK_EXECUTION_COORDINATION_EXECUTABLE,
        GOVERNED_TASK_EXECUTION_COORDINATION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_172,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_store import (
        append_governed_task_execution_coordination_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    participation = build_bounded_execution_participation(session_id=sid)
    board = participation.bounded_execution_participation if participation.ok else {}
    record, blockers = append_governed_task_execution_coordination_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_TASK_EXECUTION_COORDINATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_172,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_172,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_172,
        "executable": GOVERNED_TASK_EXECUTION_COORDINATION_EXECUTABLE,
        "governed_task_execution_coordination_memory_only": True,
        "detail": "Governed task execution coordination record persisted (coordinate without executing).",
    }


@router.get("/mission-control/gate-routed-package-outcome-review")
def mission_control_gate_routed_package_outcome_review_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_173,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_173,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173,
        CODE_WRITE_ENABLED_FIX_173,
        EXECUTION_PERFORMED_FIX_173,
        GATE_BYPASS_ENABLED_FIX_173,
        GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_173,
        MERGE_DEPLOY_ENABLED_FIX_173,
        MUTATION_PERFORMED_FIX_173,
        PR_ACTION_ENABLED_FIX_173,
        RAILWAY_MUTATION_ENABLED_FIX_173,
        TIER_ESCALATION_ENABLED_FIX_173,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_renderer import (
        render_gate_routed_package_outcome_review,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
        build_gate_routed_package_outcome_review,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_gate_routed_package_outcome_review(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "gate_routed_package_outcome_review_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_173,
        "execution_performed": EXECUTION_PERFORMED_FIX_173,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_173,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_173,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_173,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_173,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_173,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_173,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_173,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_173,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_173,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_173,
        "schema_version": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["gate_routed_package_outcome_review"] = result.gate_routed_package_outcome_review
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_gate_routed_package_outcome_review(
            result.gate_routed_package_outcome_review
        )
    return payload


@router.post("/mission-control/gate-routed-package-outcome-review/record")
def mission_control_gate_routed_package_outcome_review_record_api(
    body: GateRoutedPackageOutcomeReviewRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
        GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_EXECUTABLE,
        GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_173,
        MUTATION_PERFORMED_FIX_173,
    )
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_store import (
        append_gate_routed_package_outcome_review_record,
    )
    from aethos_core.mission_control.governed_task_execution_coordination.governed_task_execution_coordination_service import (
        build_governed_task_execution_coordination,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    coordination = build_governed_task_execution_coordination(session_id=sid)
    board = coordination.governed_task_execution_coordination if coordination.ok else {}
    record, blockers = append_gate_routed_package_outcome_review_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_173,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_173,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_173,
        "executable": GATE_ROUTED_PACKAGE_OUTCOME_REVIEW_EXECUTABLE,
        "gate_routed_package_outcome_review_memory_only": True,
        "detail": "Gate-routed package outcome review record persisted (review before lane action — existing gates decide).",
    }


@router.get("/mission-control/governed-lane-entry-recommendation")
def mission_control_governed_lane_entry_recommendation_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_174,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_174,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174,
        CODE_WRITE_ENABLED_FIX_174,
        EXECUTION_PERFORMED_FIX_174,
        GATE_BYPASS_ENABLED_FIX_174,
        GOVERNANCE_MUTATION_PERFORMED_FIX_174,
        GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION,
        LANE_ADMISSION_PERFORMED_FIX_174,
        MERGE_DEPLOY_ENABLED_FIX_174,
        MUTATION_PERFORMED_FIX_174,
        PR_ACTION_ENABLED_FIX_174,
        RAILWAY_MUTATION_ENABLED_FIX_174,
        TIER_ESCALATION_ENABLED_FIX_174,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_renderer import (
        render_governed_lane_entry_recommendation,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
        build_governed_lane_entry_recommendation,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_lane_entry_recommendation(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "governed_lane_entry_recommendation_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_174,
        "execution_performed": EXECUTION_PERFORMED_FIX_174,
        "lane_admission_performed": LANE_ADMISSION_PERFORMED_FIX_174,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_174,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_174,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_174,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_174,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_174,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_174,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_174,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_174,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_174,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_174,
        "schema_version": GOVERNED_LANE_ENTRY_RECOMMENDATION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_lane_entry_recommendation"] = result.governed_lane_entry_recommendation
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_lane_entry_recommendation(
            result.governed_lane_entry_recommendation
        )
    return payload


@router.post("/mission-control/governed-lane-entry-recommendation/record")
def mission_control_governed_lane_entry_recommendation_record_api(
    body: GovernedLaneEntryRecommendationRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.gate_routed_package_outcome_review.gate_routed_package_outcome_review_service import (
        build_gate_routed_package_outcome_review,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
        GOVERNANCE_MUTATION_PERFORMED_FIX_174,
        GOVERNED_LANE_ENTRY_RECOMMENDATION_EXECUTABLE,
        GOVERNED_LANE_ENTRY_RECOMMENDATION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_174,
    )
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_store import (
        append_governed_lane_entry_recommendation_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    review = build_gate_routed_package_outcome_review(session_id=sid)
    board = review.gate_routed_package_outcome_review if review.ok else {}
    record, blockers = append_governed_lane_entry_recommendation_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_LANE_ENTRY_RECOMMENDATION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_174,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_174,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_174,
        "executable": GOVERNED_LANE_ENTRY_RECOMMENDATION_EXECUTABLE,
        "governed_lane_entry_recommendation_memory_only": True,
        "detail": "Governed lane entry recommendation record persisted (recommendation ≠ admission — frozen gates decide).",
    }


@router.get("/mission-control/governed-lane-readiness-board")
def mission_control_governed_lane_readiness_board_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_175,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_175,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175,
        CODE_WRITE_ENABLED_FIX_175,
        EXECUTION_PERFORMED_FIX_175,
        GATE_BYPASS_ENABLED_FIX_175,
        GOVERNANCE_MUTATION_PERFORMED_FIX_175,
        GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION,
        LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
        LANE_ADMISSION_PERFORMED_FIX_175,
        MERGE_DEPLOY_ENABLED_FIX_175,
        MUTATION_PERFORMED_FIX_175,
        PR_ACTION_ENABLED_FIX_175,
        RAILWAY_MUTATION_ENABLED_FIX_175,
        TIER_ESCALATION_ENABLED_FIX_175,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_renderer import (
        render_governed_lane_readiness_board,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
        build_governed_lane_readiness_board,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_lane_readiness_board(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "governed_lane_readiness_board_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_175,
        "execution_performed": EXECUTION_PERFORMED_FIX_175,
        "lane_admission_performed": LANE_ADMISSION_PERFORMED_FIX_175,
        "lane_admission_decision_performed": LANE_ADMISSION_DECISION_PERFORMED_FIX_175,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_175,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_175,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_175,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_175,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_175,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_175,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_175,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_175,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_175,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_175,
        "schema_version": GOVERNED_LANE_READINESS_BOARD_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_lane_readiness_board"] = result.governed_lane_readiness_board
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_lane_readiness_board(result.governed_lane_readiness_board)
    return payload


@router.post("/mission-control/governed-lane-readiness-board/record")
def mission_control_governed_lane_readiness_board_record_api(
    body: GovernedLaneReadinessBoardRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_lane_entry_recommendation.governed_lane_entry_recommendation_service import (
        build_governed_lane_entry_recommendation,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
        GOVERNANCE_MUTATION_PERFORMED_FIX_175,
        GOVERNED_LANE_READINESS_BOARD_EXECUTABLE,
        GOVERNED_LANE_READINESS_BOARD_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_175,
    )
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_store import (
        append_governed_lane_readiness_board_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    recommendation = build_governed_lane_entry_recommendation(session_id=sid)
    board = recommendation.governed_lane_entry_recommendation if recommendation.ok else {}
    record, blockers = append_governed_lane_readiness_board_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(board.get("plan_id") or "") or None,
        correlation_id=str(board.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_LANE_READINESS_BOARD_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_175,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_175,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_175,
        "executable": GOVERNED_LANE_READINESS_BOARD_EXECUTABLE,
        "governed_lane_readiness_board_memory_only": True,
        "detail": "Governed lane readiness board record persisted (board ≠ admission decision — human decides in FIX 176).",
    }


@router.get("/mission-control/human-lane-admission-decision")
def mission_control_human_lane_admission_decision_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_176,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_176,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176,
        CODE_WRITE_ENABLED_FIX_176,
        EXECUTION_PERFORMED_FIX_176,
        GATE_BYPASS_ENABLED_FIX_176,
        GOVERNANCE_MUTATION_PERFORMED_FIX_176,
        HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION,
        LANE_ADMISSION_EXECUTED_FIX_176,
        LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
        MERGE_DEPLOY_ENABLED_FIX_176,
        MUTATION_PERFORMED_FIX_176,
        PR_ACTION_ENABLED_FIX_176,
        RAILWAY_MUTATION_ENABLED_FIX_176,
        TIER_ESCALATION_ENABLED_FIX_176,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_renderer import (
        render_human_lane_admission_decision,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
        build_human_lane_admission_decision,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_human_lane_admission_decision(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "human_lane_admission_decision_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_176,
        "execution_performed": EXECUTION_PERFORMED_FIX_176,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_176,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_176,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_176,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_176,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_176,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_176,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_176,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_176,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_176,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_176,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_176,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_176,
        "schema_version": HUMAN_LANE_ADMISSION_DECISION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["human_lane_admission_decision"] = result.human_lane_admission_decision
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_human_lane_admission_decision(result.human_lane_admission_decision)
    return payload


@router.post("/mission-control/human-lane-admission-decision/record")
def mission_control_human_lane_admission_decision_record_api(
    body: HumanLaneAdmissionDecisionRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_lane_readiness_board.governed_lane_readiness_board_service import (
        build_governed_lane_readiness_board,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
        GOVERNANCE_MUTATION_PERFORMED_FIX_176,
        HUMAN_LANE_ADMISSION_DECISION_EXECUTABLE,
        HUMAN_LANE_ADMISSION_DECISION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_176,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_store import (
        append_human_lane_admission_decision_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    board = build_governed_lane_readiness_board(session_id=sid)
    ctx = board.governed_lane_readiness_board if board.ok else {}
    record, blockers = append_human_lane_admission_decision_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": HUMAN_LANE_ADMISSION_DECISION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_176,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_176,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_176,
        "executable": HUMAN_LANE_ADMISSION_DECISION_EXECUTABLE,
        "human_lane_admission_decision_memory_only": True,
        "detail": "Human lane admission decision record persisted (decision ≠ lane entry execution).",
    }


@router.get("/mission-control/gate-routed-lane-entry-handoff")
def mission_control_gate_routed_lane_entry_handoff_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_177,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_177,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177,
        CODE_WRITE_ENABLED_FIX_177,
        EXECUTION_PERFORMED_FIX_177,
        GATE_BYPASS_ENABLED_FIX_177,
        GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_177,
        LANE_ADMISSION_EXECUTED_FIX_177,
        LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
        MERGE_DEPLOY_ENABLED_FIX_177,
        MUTATION_PERFORMED_FIX_177,
        PR_ACTION_ENABLED_FIX_177,
        RAILWAY_MUTATION_ENABLED_FIX_177,
        TIER_ESCALATION_ENABLED_FIX_177,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_renderer import (
        render_gate_routed_lane_entry_handoff,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
        build_gate_routed_lane_entry_handoff,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_gate_routed_lane_entry_handoff(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "gate_routed_lane_entry_handoff_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_177,
        "execution_performed": EXECUTION_PERFORMED_FIX_177,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_177,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_177,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_177,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_177,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_177,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_177,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_177,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_177,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_177,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_177,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_177,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_177,
        "schema_version": GATE_ROUTED_LANE_ENTRY_HANDOFF_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["gate_routed_lane_entry_handoff"] = result.gate_routed_lane_entry_handoff
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_gate_routed_lane_entry_handoff(result.gate_routed_lane_entry_handoff)
    return payload


@router.post("/mission-control/gate-routed-lane-entry-handoff/record")
def mission_control_gate_routed_lane_entry_handoff_record_api(
    body: GateRoutedLaneEntryHandoffRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
        GATE_ROUTED_LANE_ENTRY_HANDOFF_EXECUTABLE,
        GATE_ROUTED_LANE_ENTRY_HANDOFF_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_177,
        MUTATION_PERFORMED_FIX_177,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_store import (
        append_gate_routed_lane_entry_handoff_record,
    )
    from aethos_core.mission_control.human_lane_admission_decision.human_lane_admission_decision_service import (
        build_human_lane_admission_decision,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    decision = build_human_lane_admission_decision(session_id=sid)
    ctx = decision.human_lane_admission_decision if decision.ok else {}
    record, blockers = append_gate_routed_lane_entry_handoff_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GATE_ROUTED_LANE_ENTRY_HANDOFF_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_177,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_177,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_177,
        "executable": GATE_ROUTED_LANE_ENTRY_HANDOFF_EXECUTABLE,
        "gate_routed_lane_entry_handoff_memory_only": True,
        "detail": "Gate-routed lane entry handoff record persisted (handoff ≠ lane entry execution).",
    }


@router.get("/mission-control/frozen-gate-intake-preview")
def mission_control_frozen_gate_intake_preview_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_178,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_178,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178,
        CODE_WRITE_ENABLED_FIX_178,
        EXECUTION_PERFORMED_FIX_178,
        FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION,
        GATE_BYPASS_ENABLED_FIX_178,
        GATE_EXECUTION_PERFORMED_FIX_178,
        GOVERNANCE_MUTATION_PERFORMED_FIX_178,
        LANE_ADMISSION_EXECUTED_FIX_178,
        LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
        MERGE_DEPLOY_ENABLED_FIX_178,
        MUTATION_PERFORMED_FIX_178,
        PR_ACTION_ENABLED_FIX_178,
        RAILWAY_MUTATION_ENABLED_FIX_178,
        TIER_ESCALATION_ENABLED_FIX_178,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_renderer import (
        render_frozen_gate_intake_preview,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
        build_frozen_gate_intake_preview,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_frozen_gate_intake_preview(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "frozen_gate_intake_preview_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_178,
        "execution_performed": EXECUTION_PERFORMED_FIX_178,
        "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_178,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_178,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_178,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_178,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_178,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_178,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_178,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_178,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_178,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_178,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_178,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_178,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_178,
        "schema_version": FROZEN_GATE_INTAKE_PREVIEW_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["frozen_gate_intake_preview"] = result.frozen_gate_intake_preview
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_frozen_gate_intake_preview(result.frozen_gate_intake_preview)
    return payload


@router.post("/mission-control/frozen-gate-intake-preview/record")
def mission_control_frozen_gate_intake_preview_record_api(
    body: FrozenGateIntakePreviewRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
        FROZEN_GATE_INTAKE_PREVIEW_EXECUTABLE,
        FROZEN_GATE_INTAKE_PREVIEW_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_178,
        MUTATION_PERFORMED_FIX_178,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_store import (
        append_frozen_gate_intake_preview_record,
    )
    from aethos_core.mission_control.gate_routed_lane_entry_handoff.gate_routed_lane_entry_handoff_service import (
        build_gate_routed_lane_entry_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    handoff = build_gate_routed_lane_entry_handoff(session_id=sid)
    ctx = handoff.gate_routed_lane_entry_handoff if handoff.ok else {}
    record, blockers = append_frozen_gate_intake_preview_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": FROZEN_GATE_INTAKE_PREVIEW_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_178,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_178,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_178,
        "executable": FROZEN_GATE_INTAKE_PREVIEW_EXECUTABLE,
        "frozen_gate_intake_preview_memory_only": True,
        "detail": "Frozen gate intake preview record persisted (intake preview ≠ gate execution).",
    }


@router.get("/mission-control/frozen-gate-execution-request-adapter")
def mission_control_frozen_gate_execution_request_adapter_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_179,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_179,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179,
        CODE_WRITE_ENABLED_FIX_179,
        COMMAND_EXECUTION_PERFORMED_FIX_179,
        EXECUTION_PERFORMED_FIX_179,
        FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION,
        GATE_BYPASS_ENABLED_FIX_179,
        GATE_EXECUTION_PERFORMED_FIX_179,
        GOVERNANCE_MUTATION_PERFORMED_FIX_179,
        LANE_ADMISSION_EXECUTED_FIX_179,
        LANE_ENTRY_EXECUTION_PERFORMED_FIX_179,
        MERGE_DEPLOY_ENABLED_FIX_179,
        MUTATION_PERFORMED_FIX_179,
        PR_ACTION_ENABLED_FIX_179,
        RAILWAY_MUTATION_ENABLED_FIX_179,
        TIER_ESCALATION_ENABLED_FIX_179,
    )
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_renderer import (
        render_frozen_gate_execution_request_adapter,
    )
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
        build_frozen_gate_execution_request_adapter,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_frozen_gate_execution_request_adapter(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "frozen_gate_execution_request_adapter_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_179,
        "execution_performed": EXECUTION_PERFORMED_FIX_179,
        "command_execution_performed": COMMAND_EXECUTION_PERFORMED_FIX_179,
        "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_179,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_179,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_179,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_179,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_179,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_179,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_179,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_179,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_179,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_179,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_179,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_179,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_179,
        "schema_version": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["frozen_gate_execution_request_adapter"] = result.frozen_gate_execution_request_adapter
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_frozen_gate_execution_request_adapter(
            result.frozen_gate_execution_request_adapter
        )
    return payload


@router.post("/mission-control/frozen-gate-execution-request-adapter/record")
def mission_control_frozen_gate_execution_request_adapter_record_api(
    body: FrozenGateExecutionRequestAdapterRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
        FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_EXECUTABLE,
        FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_179,
        MUTATION_PERFORMED_FIX_179,
    )
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_store import (
        append_frozen_gate_execution_request_adapter_record,
    )
    from aethos_core.mission_control.frozen_gate_intake_preview.frozen_gate_intake_preview_service import (
        build_frozen_gate_intake_preview,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    preview = build_frozen_gate_intake_preview(session_id=sid)
    ctx = preview.frozen_gate_intake_preview if preview.ok else {}
    record, blockers = append_frozen_gate_execution_request_adapter_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_179,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_179,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_179,
        "executable": FROZEN_GATE_EXECUTION_REQUEST_ADAPTER_EXECUTABLE,
        "frozen_gate_execution_request_adapter_memory_only": True,
        "detail": "Frozen gate execution request record persisted (execution request ≠ execution).",
    }


@router.get("/mission-control/governed-chat-command-invocation-from-handoff")
def mission_control_governed_chat_command_invocation_from_handoff_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
        AUTONOMOUS_APPROVAL_ENABLED_FIX_180,
        AUTONOMOUS_EXECUTION_ENABLED_FIX_180,
        AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180,
        CHAT_GOVERNANCE_REQUIRED_FIX_180,
        CODE_WRITE_ENABLED_FIX_180,
        DIRECT_EXECUTION_PERFORMED_FIX_180,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
        EXECUTION_PERFORMED_FIX_180,
        GATE_BYPASS_ENABLED_FIX_180,
        GATE_EXECUTION_PERFORMED_FIX_180,
        GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_180,
        HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180,
        LANE_ADMISSION_EXECUTED_FIX_180,
        LANE_ENTRY_EXECUTION_PERFORMED_FIX_180,
        MERGE_DEPLOY_ENABLED_FIX_180,
        MUTATION_PERFORMED_FIX_180,
        PR_ACTION_ENABLED_FIX_180,
        RAILWAY_MUTATION_ENABLED_FIX_180,
        TIER_ESCALATION_ENABLED_FIX_180,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_renderer import (
        render_governed_chat_command_invocation_from_handoff,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
        build_governed_chat_command_invocation_from_handoff,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_governed_chat_command_invocation_from_handoff(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "governed_chat_command_invocation_from_handoff_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_180,
        "execution_performed": EXECUTION_PERFORMED_FIX_180,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_180,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
        "gate_execution_performed": GATE_EXECUTION_PERFORMED_FIX_180,
        "hidden_command_execution_performed": HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_180,
        "lane_entry_execution_performed": LANE_ENTRY_EXECUTION_PERFORMED_FIX_180,
        "lane_admission_executed": LANE_ADMISSION_EXECUTED_FIX_180,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_180,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_180,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_180,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_180,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_180,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_180,
        "code_write_enabled": CODE_WRITE_ENABLED_FIX_180,
        "pr_action_enabled": PR_ACTION_ENABLED_FIX_180,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_180,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_180,
        "chat_governance_required": CHAT_GOVERNANCE_REQUIRED_FIX_180,
        "schema_version": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["governed_chat_command_invocation_from_handoff"] = (
            result.governed_chat_command_invocation_from_handoff
        )
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_governed_chat_command_invocation_from_handoff(
            result.governed_chat_command_invocation_from_handoff
        )
    return payload


@router.post("/mission-control/governed-chat-command-invocation-from-handoff/record")
def mission_control_governed_chat_command_invocation_from_handoff_record_api(
    body: GovernedChatCommandInvocationFromHandoffRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.frozen_gate_execution_request_adapter.frozen_gate_execution_request_adapter_service import (
        build_frozen_gate_execution_request_adapter,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
        AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
        GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_EXECUTABLE,
        GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_180,
        MUTATION_PERFORMED_FIX_180,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_store import (
        append_governed_chat_command_invocation_from_handoff_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    adapter = build_frozen_gate_execution_request_adapter(session_id=sid)
    ctx = adapter.frozen_gate_execution_request_adapter if adapter.ok else {}
    record, blockers = append_governed_chat_command_invocation_from_handoff_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_180,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_180,
        "automatic_policy_mutation_performed": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_180,
        "executable": GOVERNED_CHAT_COMMAND_INVOCATION_FROM_HANDOFF_EXECUTABLE,
        "governed_chat_command_invocation_from_handoff_memory_only": True,
        "detail": "Governed chat command invocation record persisted (invocation ≠ direct execution).",
    }


@router.post("/mission-control/governed-chat-command-invocation-from-handoff/invoke")
def mission_control_governed_chat_command_invocation_from_handoff_invoke_api(
    body: GovernedChatCommandInvocationFromHandoffInvokeIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_contract import (
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
        HANDOFF_INVOCATION_CHANNEL,
        HANDOFF_INVOCATION_ORIGIN,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
        invoke_governed_chat_command_from_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    outcome = invoke_governed_chat_command_from_handoff(session_id=sid)
    if not outcome.ok:
        raise HTTPException(status_code=400, detail={"blockers": outcome.blockers or ["invoke_failed"]})

    return {
        "ok": True,
        "session_id": sid,
        "frozen_chat_command": outcome.frozen_chat_command,
        "governed_chat_message": outcome.governed_chat_message,
        "chat_intent": outcome.chat_intent,
        "route_id": outcome.route_id,
        "reply": outcome.reply,
        "audit_id": outcome.audit_id,
        "chat_governance_routed": outcome.chat_governance_routed,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_180,
        "handoff_invocation_origin": HANDOFF_INVOCATION_ORIGIN,
        "handoff_invocation_channel": HANDOFF_INVOCATION_CHANNEL,
        "detail": outcome.detail,
    }


@router.get("/mission-control/end-to-end-repo-development-pilot-harness")
def mission_control_end_to_end_repo_development_pilot_harness_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
        AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
        CHAT_GOVERNANCE_REQUIRED_FIX_181,
        DEPLOY_ENABLED_FIX_181,
        DIRECT_EXECUTION_PERFORMED_FIX_181,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
        END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_181,
        GATE_BYPASS_ENABLED_FIX_181,
        GOVERNANCE_MUTATION_PERFORMED_FIX_181,
        MERGE_ENABLED_FIX_181,
        MUTATION_PERFORMED_FIX_181,
        PRODUCTION_COUPLING_ENABLED_FIX_181,
        RAILWAY_MUTATION_ENABLED_FIX_181,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_renderer import (
        render_end_to_end_repo_development_pilot_harness,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        build_end_to_end_repo_development_pilot_harness,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "end_to_end_repo_development_pilot_harness_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_181,
        "execution_performed": EXECUTION_PERFORMED_FIX_181,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_181,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
        "autonomous_pipeline_execution_enabled": AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_181,
        "merge_enabled": MERGE_ENABLED_FIX_181,
        "deploy_enabled": DEPLOY_ENABLED_FIX_181,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_181,
        "production_coupling_enabled": PRODUCTION_COUPLING_ENABLED_FIX_181,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_181,
        "chat_governance_required": CHAT_GOVERNANCE_REQUIRED_FIX_181,
        "schema_version": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["end_to_end_repo_development_pilot_harness"] = result.end_to_end_repo_development_pilot_harness
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_end_to_end_repo_development_pilot_harness(
            result.end_to_end_repo_development_pilot_harness
        )
    return payload


@router.post("/mission-control/end-to-end-repo-development-pilot-harness/record")
def mission_control_end_to_end_repo_development_pilot_harness_record_api(
    body: EndToEndRepoDevelopmentPilotHarnessRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
        END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_EXECUTABLE,
        END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_181,
        MUTATION_PERFORMED_FIX_181,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
        append_end_to_end_repo_development_pilot_harness_record,
    )
    from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
        build_governed_chat_command_invocation_from_handoff,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    invocation = build_governed_chat_command_invocation_from_handoff(session_id=sid)
    ctx = invocation.governed_chat_command_invocation_from_handoff if invocation.ok else {}
    record, blockers = append_end_to_end_repo_development_pilot_harness_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_181,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_181,
        "executable": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_EXECUTABLE,
        "end_to_end_repo_development_pilot_harness_memory_only": True,
        "detail": "End-to-end pilot harness record persisted (pilot ≠ autonomous execution).",
    }


@router.post("/mission-control/end-to-end-repo-development-pilot-harness/run")
def mission_control_end_to_end_repo_development_pilot_harness_run_api(
    body: EndToEndRepoDevelopmentPilotHarnessRunIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
        AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
        PILOT_HARNESS_CHANNEL,
        PILOT_HARNESS_ORIGIN,
    )
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        run_end_to_end_repo_development_pilot,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    outcome = run_end_to_end_repo_development_pilot(
        session_id=sid,
        repo_issue=body.repo_issue.strip() if body.repo_issue else None,
    )

    return {
        "ok": outcome.ok,
        "session_id": sid,
        "repo_issue": outcome.repo_issue,
        "stages_completed": outcome.stages_completed,
        "chat_steps": outcome.chat_steps,
        "pilot_report": outcome.pilot_report,
        "audit_id": outcome.audit_id,
        "blockers": outcome.blockers,
        "chat_governance_routed": outcome.chat_governance_routed,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
        "autonomous_pipeline_execution_enabled": AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
        "pilot_harness_origin": PILOT_HARNESS_ORIGIN,
        "pilot_harness_channel": PILOT_HARNESS_CHANNEL,
        "detail": outcome.detail,
    }


@router.get("/mission-control/repo-pilot-readiness-dashboard")
def mission_control_repo_pilot_readiness_dashboard_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_contract import (
        AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182,
        DIRECT_EXECUTION_PERFORMED_FIX_182,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182,
        EXECUTION_PERFORMED_FIX_182,
        GATE_BYPASS_ENABLED_FIX_182,
        GOVERNANCE_MUTATION_PERFORMED_FIX_182,
        MUTATION_PERFORMED_FIX_182,
        PILOT_EXECUTION_PERFORMED_FIX_182,
        READINESS_VISIBILITY_ONLY_FIX_182,
        REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_renderer import (
        render_repo_pilot_readiness_dashboard,
    )
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
        build_repo_pilot_readiness_dashboard,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_repo_pilot_readiness_dashboard(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "repo_pilot_readiness_dashboard_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_182,
        "execution_performed": EXECUTION_PERFORMED_FIX_182,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_182,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_182,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_182,
        "autonomous_readiness_mutation_enabled": AUTONOMOUS_READINESS_MUTATION_ENABLED_FIX_182,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_182,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_182,
        "readiness_visibility_only": READINESS_VISIBILITY_ONLY_FIX_182,
        "schema_version": REPO_PILOT_READINESS_DASHBOARD_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["repo_pilot_readiness_dashboard"] = result.repo_pilot_readiness_dashboard
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_repo_pilot_readiness_dashboard(result.repo_pilot_readiness_dashboard)
    return payload


@router.post("/mission-control/repo-pilot-readiness-dashboard/record")
def mission_control_repo_pilot_readiness_dashboard_record_api(
    body: RepoPilotReadinessDashboardRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        build_end_to_end_repo_development_pilot_harness,
    )
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_182,
        MUTATION_PERFORMED_FIX_182,
        REPO_PILOT_READINESS_DASHBOARD_EXECUTABLE,
        REPO_PILOT_READINESS_DASHBOARD_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_store import (
        append_repo_pilot_readiness_dashboard_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    harness = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    ctx = harness.end_to_end_repo_development_pilot_harness if harness.ok else {}
    record, blockers = append_repo_pilot_readiness_dashboard_record(
        session_id=sid,
        kind=body.kind.strip(),
        content=body.content.strip(),
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author.strip(),
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": REPO_PILOT_READINESS_DASHBOARD_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_182,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_182,
        "executable": REPO_PILOT_READINESS_DASHBOARD_EXECUTABLE,
        "repo_pilot_readiness_dashboard_memory_only": True,
        "detail": "Repo pilot readiness dashboard record persisted (readiness ≠ execution).",
    }


@router.get("/mission-control/pilot-validation-trust-board")
def mission_control_pilot_validation_trust_board_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_contract import (
        AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183,
        DIRECT_EXECUTION_PERFORMED_FIX_183,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183,
        EXECUTION_PERFORMED_FIX_183,
        GATE_BYPASS_ENABLED_FIX_183,
        GOVERNANCE_MUTATION_PERFORMED_FIX_183,
        MUTATION_PERFORMED_FIX_183,
        PILOT_REEXECUTION_PERFORMED_FIX_183,
        PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION,
        VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183,
    )
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_renderer import (
        render_pilot_validation_trust_board,
    )
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
        build_pilot_validation_trust_board,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_pilot_validation_trust_board(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "pilot_validation_trust_board_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_183,
        "execution_performed": EXECUTION_PERFORMED_FIX_183,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_183,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_183,
        "autonomous_validation_execution_enabled": AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_183,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_183,
        "validation_composes_audits_only": VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183,
        "schema_version": PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["pilot_validation_trust_board"] = result.pilot_validation_trust_board
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_pilot_validation_trust_board(result.pilot_validation_trust_board)
    return payload


@router.post("/mission-control/pilot-validation-trust-board/record")
def mission_control_pilot_validation_trust_board_record_api(
    body: PilotValidationTrustBoardRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        build_end_to_end_repo_development_pilot_harness,
    )
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_183,
        MUTATION_PERFORMED_FIX_183,
        PILOT_VALIDATION_TRUST_BOARD_EXECUTABLE,
        PILOT_VALIDATION_TRUST_BOARD_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_store import (
        append_pilot_validation_trust_board_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    harness = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    ctx = harness.end_to_end_repo_development_pilot_harness if harness.ok else {}
    record, blockers = append_pilot_validation_trust_board_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": PILOT_VALIDATION_TRUST_BOARD_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_183,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_183,
        "executable": PILOT_VALIDATION_TRUST_BOARD_EXECUTABLE,
        "pilot_validation_trust_board_memory_only": True,
        "detail": "Pilot validation trust board record persisted (validation ≠ re-execution).",
    }


@router.get("/mission-control/issue-intake-scope-fidelity")
def mission_control_issue_intake_scope_fidelity_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.software_delivery.issue_intake_scope_fidelity_contract import (
        ISSUE_INTAKE_SCOPE_FIDELITY_SCHEMA_VERSION,
    )
    from aethos_core.software_delivery.issue_intake_scope_fidelity_service import (
        build_issue_intake_scope_fidelity_snapshot,
    )

    snapshot = build_issue_intake_scope_fidelity_snapshot(session_id=session_id)
    if not snapshot.get("ok"):
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": snapshot.get("blockers") or ["issue_intake_scope_fidelity_unavailable"],
                "message": snapshot.get("detail") or "issue_intake_scope_fidelity_unavailable",
            },
        )
    snapshot["schema_version"] = ISSUE_INTAKE_SCOPE_FIDELITY_SCHEMA_VERSION
    return snapshot


@router.get("/mission-control/issue-intent-alignment")
def mission_control_issue_intent_alignment_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
        ALIGNMENT_VALIDATION_PERFORMED_FIX_184,
        AUTONOMOUS_AUTHORITY_ENABLED_FIX_184,
        AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184,
        AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184,
        DIRECT_EXECUTION_PERFORMED_FIX_184,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184,
        EXECUTION_PERFORMED_FIX_184,
        GATE_BYPASS_ENABLED_FIX_184,
        GOVERNANCE_MUTATION_PERFORMED_FIX_184,
        ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_184,
        PATCH_EXECUTION_PERFORMED_FIX_184,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_renderer import (
        render_issue_intent_alignment,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
        build_issue_intent_alignment,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_issue_intent_alignment(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "issue_intent_alignment_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_184,
        "execution_performed": EXECUTION_PERFORMED_FIX_184,
        "patch_execution_performed": PATCH_EXECUTION_PERFORMED_FIX_184,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_184,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_184,
        "autonomous_scope_expansion_enabled": AUTONOMOUS_SCOPE_EXPANSION_ENABLED_FIX_184,
        "autonomous_file_selection_override_enabled": AUTONOMOUS_FILE_SELECTION_OVERRIDE_ENABLED_FIX_184,
        "autonomous_authority_enabled": AUTONOMOUS_AUTHORITY_ENABLED_FIX_184,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_184,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_184,
        "alignment_validation_performed": ALIGNMENT_VALIDATION_PERFORMED_FIX_184,
        "schema_version": ISSUE_INTENT_ALIGNMENT_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["issue_intent_alignment"] = result.issue_intent_alignment
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_issue_intent_alignment(result.issue_intent_alignment)
    return payload


@router.post("/mission-control/issue-intent-alignment/record")
def mission_control_issue_intent_alignment_record_api(
    body: IssueIntentAlignmentRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_service import (
        build_end_to_end_repo_development_pilot_harness,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_184,
        ISSUE_INTENT_ALIGNMENT_EXECUTABLE,
        ISSUE_INTENT_ALIGNMENT_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_184,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        append_issue_intent_alignment_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    harness = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    ctx = harness.end_to_end_repo_development_pilot_harness if harness.ok else {}
    record, blockers = append_issue_intent_alignment_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        plan_id=str(ctx.get("plan_id") or "") or None,
        correlation_id=str(ctx.get("correlation_id") or "") or None,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": ISSUE_INTENT_ALIGNMENT_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_184,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_184,
        "executable": ISSUE_INTENT_ALIGNMENT_EXECUTABLE,
        "issue_intent_alignment_memory_only": True,
        "detail": "Issue intent alignment record persisted (validation ≠ patch execution).",
    }


@router.get("/mission-control/dogfood-pilot-trust-report-freeze")
def mission_control_dogfood_pilot_trust_report_freeze_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
        AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186,
        DIRECT_EXECUTION_PERFORMED_FIX_186,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186,
        DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        EXECUTION_PERFORMED_FIX_186,
        GATE_BYPASS_ENABLED_FIX_186,
        GOVERNANCE_MUTATION_PERFORMED_FIX_186,
        MUTATION_PERFORMED_FIX_186,
        PILOT_REEXECUTION_PERFORMED_FIX_186,
        TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186,
    )
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_renderer import (
        render_dogfood_pilot_trust_report_freeze,
    )
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
        build_dogfood_pilot_trust_report_freeze,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_dogfood_pilot_trust_report_freeze(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "dogfood_pilot_trust_report_freeze_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_186,
        "execution_performed": EXECUTION_PERFORMED_FIX_186,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_186,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_186,
        "autonomous_trust_report_execution_enabled": AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_186,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_186,
        "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186,
        "schema_version": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["dogfood_pilot_trust_report_freeze"] = result.dogfood_pilot_trust_report_freeze
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_dogfood_pilot_trust_report_freeze(result.dogfood_pilot_trust_report_freeze)
    return payload


@router.post("/mission-control/dogfood-pilot-trust-report-freeze/record")
def mission_control_dogfood_pilot_trust_report_freeze_record_api(
    body: DogfoodPilotTrustReportFreezeRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
        DOGFOOD_PILOT_TRUST_REPORT_FREEZE_EXECUTABLE,
        DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_186,
        MUTATION_PERFORMED_FIX_186,
    )
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
        append_dogfood_pilot_trust_report_freeze_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_dogfood_pilot_trust_report_freeze_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_186,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_186,
        "executable": DOGFOOD_PILOT_TRUST_REPORT_FREEZE_EXECUTABLE,
        "dogfood_pilot_trust_report_freeze_memory_only": True,
        "detail": "Dogfood pilot trust report freeze record persisted (trust_report_freeze ≠ pilot_execution).",
    }


@router.get("/mission-control/dogfood-pilot-gate-closure")
def mission_control_dogfood_pilot_gate_closure_api(session_id: str = "default") -> dict[str, Any]:
    from aethos_core.mission_control.dogfood_pilot_gate_closure.dogfood_pilot_gate_closure_contract import (
        DOGFOOD_PILOT_GATE_CLOSURE_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.dogfood_pilot_gate_closure.dogfood_pilot_gate_closure_service import (
        build_dogfood_pilot_gate_closure,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    result = build_dogfood_pilot_gate_closure(session_id=sid)
    return {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": False,
        "execution_performed": False,
        "pilot_reexecution_performed": False,
        "schema_version": DOGFOOD_PILOT_GATE_CLOSURE_SCHEMA_VERSION,
        "session_id": sid,
        "blockers": list(result.blockers),
        "detail": result.detail,
        "dogfood_pilot_gate_closure": result.dogfood_pilot_gate_closure,
    }


@router.get("/mission-control/independent-repository-trust-expansion")
def mission_control_independent_repository_trust_expansion_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
        AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187,
        AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187,
        CROSS_REPO_AUTHORITY_ENABLED_FIX_187,
        DIRECT_EXECUTION_PERFORMED_FIX_187,
        DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187,
        EXECUTION_PERFORMED_FIX_187,
        GATE_BYPASS_ENABLED_FIX_187,
        GOVERNANCE_MUTATION_PERFORMED_FIX_187,
        INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_187,
        PILOT_EXECUTION_PERFORMED_FIX_187,
        TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187,
        TRUST_TRANSFER_ENABLED_FIX_187,
    )
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_renderer import (
        render_independent_repository_trust_expansion,
    )
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_service import (
        build_independent_repository_trust_expansion,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_independent_repository_trust_expansion(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "independent_repository_trust_expansion_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": True,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_187,
        "execution_performed": EXECUTION_PERFORMED_FIX_187,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_187,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_187,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_187,
        "autonomous_trust_expansion_enabled": AUTONOMOUS_TRUST_EXPANSION_ENABLED_FIX_187,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_187,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_187,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_187,
        "automatic_repo_trust_inheritance_enabled": AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187,
        "cross_repo_authority_enabled": CROSS_REPO_AUTHORITY_ENABLED_FIX_187,
        "trust_expansion_composes_artifacts_only": TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187,
        "schema_version": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["independent_repository_trust_expansion"] = result.independent_repository_trust_expansion
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_independent_repository_trust_expansion(
            result.independent_repository_trust_expansion
        )
    return payload


@router.post("/mission-control/independent-repository-trust-expansion/record")
def mission_control_independent_repository_trust_expansion_record_api(
    body: IndependentRepositoryTrustExpansionRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_187,
        INDEPENDENT_REPOSITORY_TRUST_EXPANSION_EXECUTABLE,
        INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_SCHEMA_VERSION,
        MUTATION_PERFORMED_FIX_187,
    )
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
        append_independent_repository_trust_expansion_record,
    )
    from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_service import (
        clear_independent_repository_trust_expansion_cache_for_tests,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_independent_repository_trust_expansion_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        repository=body.repository or None,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    clear_independent_repository_trust_expansion_cache_for_tests()

    return {
        "ok": True,
        "schema_version": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_187,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_187,
        "executable": INDEPENDENT_REPOSITORY_TRUST_EXPANSION_EXECUTABLE,
        "independent_repository_trust_expansion_memory_only": True,
        "detail": "Independent repository trust expansion record persisted (trust is non-transferable).",
    }


@router.get("/mission-control/pilotos-ui-pilot-arc-orchestrator")
def mission_control_pilotos_ui_pilot_arc_orchestrator_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
        AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
        DEPLOY_ENABLED_FIX_188,
        GATE_BYPASS_ENABLED_FIX_188,
        GOVERNANCE_MUTATION_PERFORMED_FIX_188,
        MERGE_ENABLED_FIX_188,
        MUTATION_PERFORMED_FIX_188,
        PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        RAILWAY_MUTATION_ENABLED_FIX_188,
        TRUST_TRANSFER_ENABLED_FIX_188,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_renderer import (
        render_pilotos_ui_pilot_arc_orchestrator,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_service import (
        build_pilotos_ui_pilot_arc_orchestrator,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_pilotos_ui_pilot_arc_orchestrator(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_188,
        "execution_performed": False,
        "pilot_execution_performed": False,
        "automatic_trust_granting_enabled": AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_188,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_188,
        "merge_enabled": MERGE_ENABLED_FIX_188,
        "deploy_enabled": DEPLOY_ENABLED_FIX_188,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_188,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_188,
        "schema_version": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["pilotos_ui_pilot_arc_orchestrator"] = result.pilotos_ui_pilot_arc_orchestrator
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_pilotos_ui_pilot_arc_orchestrator(result.pilotos_ui_pilot_arc_orchestrator)
    return payload


@router.post("/mission-control/pilotos-ui-pilot-arc-orchestrator/record")
def mission_control_pilotos_ui_pilot_arc_orchestrator_record_api(
    body: PilotosUiPilotArcOrchestratorRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_188,
        MUTATION_PERFORMED_FIX_188,
        PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_service import (
        build_pilotos_ui_pilot_arc_orchestrator,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
        append_pilotos_ui_pilot_arc_orchestrator_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    kind = body.kind.strip().lower()
    if kind == "pilot_arc_trust_decision":
        arc = build_pilotos_ui_pilot_arc_orchestrator(session_id=sid)
        arc_state = str(arc.pilotos_ui_pilot_arc_orchestrator.get("arc_state") or "")
        if arc_state != "TRUST_REVIEW_PENDING":
            raise HTTPException(
                status_code=400,
                detail={
                    "blockers": [f"trust_decision_requires_trust_review_pending:{arc_state}"],
                    "message": "Pilot completion does not auto-grant trust.",
                },
            )

    record, blockers = append_pilotos_ui_pilot_arc_orchestrator_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        repo_issue=body.repo_issue or None,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers or ["record_failed"]})

    return {
        "ok": True,
        "schema_version": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_188,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_188,
        "executable": PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        "pilotos_ui_pilot_arc_orchestrator_memory_only": True,
        "detail": "PilotOS UI pilot arc record persisted (pilot arc orchestration ≠ trust granting).",
    }


@router.post("/mission-control/pilotos-ui-pilot-arc-orchestrator/run")
def mission_control_pilotos_ui_pilot_arc_orchestrator_run_api(
    body: PilotosUiPilotArcOrchestratorRunIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
        AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
        PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188,
        TRUST_TRANSFER_ENABLED_FIX_188,
    )
    from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_service import (
        run_pilotos_ui_pilot_arc_pilot,
    )

    outcome = run_pilotos_ui_pilot_arc_pilot(pilot_number=body.pilot_number)
    if outcome.blockers and not outcome.audit_id:
        raise HTTPException(
            status_code=400,
            detail={"blockers": outcome.blockers, "message": outcome.detail or "pilot_arc_run_blocked"},
        )

    return {
        "ok": outcome.ok,
        "pilot_number": outcome.pilot_number,
        "session_id": outcome.session_id,
        "audit_id": outcome.audit_id,
        "stages_completed": outcome.stages_completed,
        "blockers": outcome.blockers,
        "automatic_trust_granting_enabled": AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
        "trust_transfer_enabled": TRUST_TRANSFER_ENABLED_FIX_188,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188,
        "detail": outcome.detail,
    }


@router.get("/mission-control/atlas-trader-pilot-arc-orchestrator")
def mission_control_atlas_trader_pilot_arc_orchestrator_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
        ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        CROSS_REPO_AUTHORITY_FIX_193,
        DEPLOY_AUTHORITY_FIX_193,
        GATE_BYPASS_ENABLED_FIX_193,
        GOVERNANCE_MUTATION_PERFORMED_FIX_193,
        MERGE_AUTHORITY_FIX_193,
        MUTATION_PERFORMED_FIX_193,
        PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
        RAILWAY_MUTATION_ENABLED_FIX_193,
        ROLLBACK_AUTHORITY_FIX_193,
        TRUST_GRANTING_AUTHORITY_FIX_193,
        TRUST_INHERITANCE_ENABLED_FIX_193,
    )
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_renderer import (
        render_atlas_trader_pilot_arc_orchestrator,
    )
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_service import (
        build_atlas_trader_pilot_arc_orchestrator,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_atlas_trader_pilot_arc_orchestrator(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_193,
        "execution_performed": False,
        "pilot_execution_performed": False,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_193,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_193,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_193,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_193,
        "merge_authority": MERGE_AUTHORITY_FIX_193,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_193,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_193,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_193,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_193,
        "schema_version": ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["atlas_trader_pilot_arc_orchestrator"] = result.atlas_trader_pilot_arc_orchestrator
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_atlas_trader_pilot_arc_orchestrator(
            result.atlas_trader_pilot_arc_orchestrator
        )
    return payload


@router.post("/mission-control/atlas-trader-pilot-arc-orchestrator/record")
def mission_control_atlas_trader_pilot_arc_orchestrator_record_api(
    body: AtlasTraderPilotArcOrchestratorRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
        ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_193,
        MUTATION_PERFORMED_FIX_193,
    )
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
        append_atlas_trader_pilot_arc_orchestrator_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_atlas_trader_pilot_arc_orchestrator_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        repo_issue=body.repo_issue or None,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers, "message": "record_blocked"})

    return {
        "ok": True,
        "schema_version": ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_193,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_193,
        "executable": ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        "atlas_trader_pilot_arc_orchestrator_memory_only": True,
        "detail": "Atlas Trader pilot arc orchestrator record persisted (pilot arc orchestration ≠ trust granting).",
    }


@router.post("/mission-control/atlas-trader-pilot-arc-orchestrator/run")
def mission_control_atlas_trader_pilot_arc_orchestrator_run_api(
    body: AtlasTraderPilotArcOrchestratorRunIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
        CROSS_REPO_AUTHORITY_FIX_193,
        PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
        TRUST_GRANTING_AUTHORITY_FIX_193,
        TRUST_INHERITANCE_ENABLED_FIX_193,
    )
    from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_service import (
        run_atlas_trader_pilot_arc_pilot,
    )

    outcome = run_atlas_trader_pilot_arc_pilot(pilot_number=body.pilot_number)
    if outcome.blockers and not outcome.audit_id:
        raise HTTPException(
            status_code=400,
            detail={"blockers": outcome.blockers, "message": outcome.detail or "atlas_pilot_arc_run_blocked"},
        )

    return {
        "ok": outcome.ok,
        "pilot_number": outcome.pilot_number,
        "session_id": outcome.session_id,
        "audit_id": outcome.audit_id,
        "stages_completed": outcome.stages_completed,
        "blockers": outcome.blockers,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_193,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_193,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_193,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
        "detail": outcome.detail,
    }


@router.get("/mission-control/atlas-trader-trust-report-freeze")
def mission_control_atlas_trader_trust_report_freeze_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_contract import (
        AUTOMATIC_EXPANSION_ENABLED_FIX_194,
        CROSS_REPO_AUTHORITY_FIX_194,
        EXECUTION_PERFORMED_FIX_194,
        GATE_BYPASS_ENABLED_FIX_194,
        GOVERNANCE_MUTATION_PERFORMED_FIX_194,
        MUTATION_PERFORMED_FIX_194,
        ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        PILOT_EXECUTION_AUTHORITY_FIX_194,
        PILOT_REEXECUTION_PERFORMED_FIX_194,
        TRUST_GRANTING_AUTHORITY_FIX_194,
        TRUST_INHERITANCE_ENABLED_FIX_194,
        TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194,
    )
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_renderer import (
        render_atlas_trader_trust_report_freeze,
    )
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
        build_atlas_trader_trust_report_freeze,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_atlas_trader_trust_report_freeze(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "atlas_trader_trust_report_freeze_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_194,
        "execution_performed": EXECUTION_PERFORMED_FIX_194,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_194,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_194,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_194,
        "pilot_execution_authority": PILOT_EXECUTION_AUTHORITY_FIX_194,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_194,
        "automatic_expansion_enabled": AUTOMATIC_EXPANSION_ENABLED_FIX_194,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_194,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_194,
        "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194,
        "schema_version": ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["atlas_trader_trust_report_freeze"] = result.atlas_trader_trust_report_freeze
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_atlas_trader_trust_report_freeze(
            result.atlas_trader_trust_report_freeze
        )
    return payload


@router.post("/mission-control/atlas-trader-trust-report-freeze/record")
def mission_control_atlas_trader_trust_report_freeze_record_api(
    body: AtlasTraderTrustReportFreezeRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_contract import (
        ATLAS_TRADER_TRUST_REPORT_FREEZE_EXECUTABLE,
        ATLAS_TRADER_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        GOVERNANCE_MUTATION_PERFORMED_FIX_194,
        MUTATION_PERFORMED_FIX_194,
    )
    from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
        append_atlas_trader_trust_report_freeze_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_atlas_trader_trust_report_freeze_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers, "message": "record_blocked"})

    return {
        "ok": True,
        "schema_version": ATLAS_TRADER_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_194,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_194,
        "executable": ATLAS_TRADER_TRUST_REPORT_FREEZE_EXECUTABLE,
        "atlas_trader_trust_report_freeze_memory_only": True,
        "detail": "Atlas Trader trust report freeze record persisted (trust_freeze ≠ trust_granting).",
    }


@router.get("/mission-control/nexora-pilot-arc-orchestrator")
def mission_control_nexora_pilot_arc_orchestrator_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
        CROSS_REPO_AUTHORITY_FIX_195,
        DEPLOY_AUTHORITY_FIX_195,
        GATE_BYPASS_ENABLED_FIX_195,
        GOVERNANCE_MUTATION_PERFORMED_FIX_195,
        MERGE_AUTHORITY_FIX_195,
        MUTATION_PERFORMED_FIX_195,
        NEXORA_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195,
        PROVIDER_AUTHORITY_FIX_195,
        ROLLBACK_AUTHORITY_FIX_195,
        TRUST_GRANTING_AUTHORITY_FIX_195,
        TRUST_INHERITANCE_ENABLED_FIX_195,
    )
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_renderer import (
        render_nexora_pilot_arc_orchestrator,
    )
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_service import (
        build_nexora_pilot_arc_orchestrator,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_nexora_pilot_arc_orchestrator(session_id=sid)
    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_195,
        "execution_performed": False,
        "pilot_execution_performed": False,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_195,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_195,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_195,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_195,
        "merge_authority": MERGE_AUTHORITY_FIX_195,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_195,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_195,
        "provider_authority": PROVIDER_AUTHORITY_FIX_195,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_195,
        "schema_version": NEXORA_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
        "session_id": result.session_id,
        "blockers": result.blockers,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["nexora_pilot_arc_orchestrator"] = result.nexora_pilot_arc_orchestrator
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_nexora_pilot_arc_orchestrator(result.nexora_pilot_arc_orchestrator)
    return payload


@router.post("/mission-control/nexora-pilot-arc-orchestrator/record")
def mission_control_nexora_pilot_arc_orchestrator_record_api(
    body: NexoraPilotArcOrchestratorRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_195,
        MUTATION_PERFORMED_FIX_195,
        NEXORA_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        NEXORA_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
        append_nexora_pilot_arc_orchestrator_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_nexora_pilot_arc_orchestrator_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        repo_issue=body.repo_issue or None,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers, "message": "record_blocked"})

    return {
        "ok": True,
        "schema_version": NEXORA_PILOT_ARC_ORCHESTRATOR_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_195,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_195,
        "executable": NEXORA_PILOT_ARC_ORCHESTRATOR_EXECUTABLE,
        "nexora_pilot_arc_orchestrator_memory_only": True,
        "detail": "Nexora pilot arc orchestrator record persisted (pilot arc orchestration ≠ trust granting).",
    }


@router.post("/mission-control/nexora-pilot-arc-orchestrator/run")
def mission_control_nexora_pilot_arc_orchestrator_run_api(
    body: NexoraPilotArcOrchestratorRunIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
        CROSS_REPO_AUTHORITY_FIX_195,
        PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195,
        TRUST_GRANTING_AUTHORITY_FIX_195,
        TRUST_INHERITANCE_ENABLED_FIX_195,
    )
    from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_service import (
        run_nexora_pilot_arc_pilot,
    )

    outcome = run_nexora_pilot_arc_pilot(pilot_number=body.pilot_number)
    if outcome.blockers and not outcome.audit_id:
        raise HTTPException(
            status_code=400,
            detail={"blockers": outcome.blockers, "message": outcome.detail or "nexora_pilot_arc_run_blocked"},
        )

    return {
        "ok": outcome.ok,
        "pilot_number": outcome.pilot_number,
        "session_id": outcome.session_id,
        "audit_id": outcome.audit_id,
        "stages_completed": outcome.stages_completed,
        "blockers": outcome.blockers,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_195,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_195,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_195,
        "pilot_arc_routes_through_fix_181": PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195,
        "detail": outcome.detail,
    }


@router.get("/mission-control/nexora-trust-report-freeze")
def mission_control_nexora_trust_report_freeze_api(
    session_id: str = "default",
    format: str = "json",
) -> dict[str, Any]:
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_contract import (
        AUTOMATIC_EXPANSION_ENABLED_FIX_196,
        CROSS_REPO_AUTHORITY_FIX_196,
        EXECUTION_PERFORMED_FIX_196,
        GATE_BYPASS_ENABLED_FIX_196,
        GOVERNANCE_MUTATION_PERFORMED_FIX_196,
        MUTATION_PERFORMED_FIX_196,
        NEXORA_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        PILOT_EXECUTION_AUTHORITY_FIX_196,
        PILOT_REEXECUTION_PERFORMED_FIX_196,
        TRUST_GRANTING_AUTHORITY_FIX_196,
        TRUST_INHERITANCE_ENABLED_FIX_196,
        TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_196,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_renderer import (
        render_nexora_trust_report_freeze,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
        build_nexora_trust_report_freeze,
    )

    sid = (session_id or "default").strip()[:64] or "default"
    fmt = (format or "json").strip().lower()
    if fmt not in {"json", "markdown", "both"}:
        raise HTTPException(status_code=400, detail={"blockers": [f"unsupported_format:{fmt}"]})

    result = build_nexora_trust_report_freeze(session_id=sid)
    if not result.ok:
        raise HTTPException(
            status_code=503,
            detail={
                "blockers": result.blockers,
                "message": result.detail or "nexora_trust_report_freeze_unavailable",
            },
        )

    payload: dict[str, Any] = {
        "ok": result.ok,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_196,
        "execution_performed": EXECUTION_PERFORMED_FIX_196,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_196,
        "trust_granting_authority": TRUST_GRANTING_AUTHORITY_FIX_196,
        "trust_inheritance_enabled": TRUST_INHERITANCE_ENABLED_FIX_196,
        "pilot_execution_authority": PILOT_EXECUTION_AUTHORITY_FIX_196,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_196,
        "automatic_expansion_enabled": AUTOMATIC_EXPANSION_ENABLED_FIX_196,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_196,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_196,
        "trust_report_composes_artifacts_only": TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_196,
        "schema_version": NEXORA_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
    }
    if fmt in {"json", "both"}:
        payload["nexora_trust_report_freeze"] = result.nexora_trust_report_freeze
    if fmt in {"markdown", "both"}:
        payload["markdown"] = render_nexora_trust_report_freeze(result.nexora_trust_report_freeze)
    return payload


@router.post("/mission-control/nexora-trust-report-freeze/record")
def mission_control_nexora_trust_report_freeze_record_api(
    body: NexoraTrustReportFreezeRecordIn,
) -> dict[str, Any]:
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_contract import (
        GOVERNANCE_MUTATION_PERFORMED_FIX_196,
        MUTATION_PERFORMED_FIX_196,
        NEXORA_TRUST_REPORT_FREEZE_EXECUTABLE,
        NEXORA_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
    )
    from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
        append_nexora_trust_report_freeze_record,
    )

    sid = (body.session_id or "default").strip()[:64] or "default"
    record, blockers = append_nexora_trust_report_freeze_record(
        session_id=sid,
        kind=body.kind,
        content=body.content,
        author=body.author,
        metadata=body.metadata,
    )
    if blockers or not record:
        raise HTTPException(status_code=400, detail={"blockers": blockers, "message": "record_blocked"})

    return {
        "ok": True,
        "schema_version": NEXORA_TRUST_REPORT_FREEZE_RECORD_SCHEMA_VERSION,
        "session_id": sid,
        "record": record,
        "mutation_performed": MUTATION_PERFORMED_FIX_196,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_196,
        "executable": NEXORA_TRUST_REPORT_FREEZE_EXECUTABLE,
        "nexora_trust_report_freeze_memory_only": True,
        "detail": "Nexora trust report freeze record persisted (trust_freeze ≠ trust_granting).",
    }
