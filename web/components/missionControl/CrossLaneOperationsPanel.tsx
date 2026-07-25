"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { CrossLaneLaneDrilldownPanel } from "@/components/missionControl/CrossLaneLaneDrilldownPanel";
import { laneAnchorId, laneDisplayTitle, scrollToLaneAnchor } from "@/lib/missionControl/crossLaneLaneNavigation";
import {
  fetchMissionControlCrossLaneSnapshot,
  type MissionControlAttentionItem,
  type MissionControlCrossLaneSnapshot,
  type MissionControlTimelineEntry,
} from "@/lib/missionControl/missionControlCrossLaneApi";
import {
  downloadTextFile,
  evidenceBundleJsonFilename,
  evidenceBundleMarkdownFilename,
  fetchMissionControlEvidenceBundle,
} from "@/lib/missionControl/missionControlEvidenceBundleApi";
import { fetchMissionControlMissionStrategy } from "@/lib/missionControl/missionControlMissionStrategyApi";
import { fetchMissionControlMissionOrchestration } from "@/lib/missionControl/missionControlMissionOrchestrationApi";
import { fetchMissionControlMissionReadinessReview } from "@/lib/missionControl/missionControlMissionReadinessReviewApi";
import {
  appendMissionControlGovernanceDeliberationRecord,
  fetchMissionControlGovernanceDeliberation,
} from "@/lib/missionControl/missionControlGovernanceDeliberationApi";
import {
  appendMissionControlGovernanceCollaborationRecord,
  fetchMissionControlGovernanceCollaboration,
} from "@/lib/missionControl/missionControlGovernanceCollaborationApi";
import { fetchMissionControlGovernanceRoleArchitecture } from "@/lib/missionControl/missionControlGovernanceRoleArchitectureApi";
import {
  appendMissionControlGovernanceDoctrineRecord,
  fetchMissionControlGovernanceDoctrine,
} from "@/lib/missionControl/missionControlGovernanceDoctrineApi";
import {
  appendMissionControlGovernancePolicyInterpretationRecord,
  fetchMissionControlGovernancePolicyInterpretation,
} from "@/lib/missionControl/missionControlGovernancePolicyInterpretationApi";
import {
  appendMissionControlGovernanceCoherenceRecord,
  fetchMissionControlGovernanceCoherence,
} from "@/lib/missionControl/missionControlGovernanceCoherenceApi";
import {
  appendMissionControlGovernanceResilienceRecord,
  fetchMissionControlGovernanceResilience,
} from "@/lib/missionControl/missionControlGovernanceResilienceApi";
import {
  appendMissionControlGovernanceEvolutionRecord,
  fetchMissionControlGovernanceEvolution,
} from "@/lib/missionControl/missionControlGovernanceEvolutionApi";
import {
  appendMissionControlInstitutionalIdentityRecord,
  fetchMissionControlInstitutionalIdentity,
} from "@/lib/missionControl/missionControlInstitutionalIdentityApi";
import {
  appendMissionControlInstitutionalExternalRelationsRecord,
  fetchMissionControlInstitutionalExternalRelations,
} from "@/lib/missionControl/missionControlInstitutionalExternalRelationsApi";
import {
  appendMissionControlInstitutionalExistentialRiskRecord,
  fetchMissionControlInstitutionalExistentialRisk,
} from "@/lib/missionControl/missionControlInstitutionalExistentialRiskApi";
import {
  appendMissionControlConstitutionalEthicsRecord,
  fetchMissionControlConstitutionalEthics,
} from "@/lib/missionControl/missionControlConstitutionalEthicsApi";
import {
  appendMissionControlConstitutionalAuditRecord,
  fetchMissionControlConstitutionalAudit,
} from "@/lib/missionControl/missionControlConstitutionalAuditApi";
import {
  appendMissionControlConstitutionalLegitimacyRecord,
  fetchMissionControlConstitutionalLegitimacy,
} from "@/lib/missionControl/missionControlConstitutionalLegitimacyApi";
import {
  appendMissionControlConstitutionalPluralismRecord,
  fetchMissionControlConstitutionalPluralism,
} from "@/lib/missionControl/missionControlConstitutionalPluralismApi";
import {
  appendMissionControlConstitutionalSynthesisRecord,
  fetchMissionControlConstitutionalSynthesis,
} from "@/lib/missionControl/missionControlConstitutionalSynthesisApi";
import {
  appendMissionControlMissionPlanningRecord,
  fetchMissionControlMissionPlanning,
} from "@/lib/missionControl/missionControlMissionPlanningApi";
import {
  appendMissionControlMissionPlanningDeliberationRecord,
  fetchMissionControlMissionPlanningDeliberation,
} from "@/lib/missionControl/missionControlMissionPlanningDeliberationApi";
import {
  appendMissionControlHumanDecisionBoardRecord,
  fetchMissionControlHumanDecisionBoard,
} from "@/lib/missionControl/missionControlHumanDecisionBoardApi";
import {
  appendMissionControlExecutionHandoffCoordinationRecord,
  fetchMissionControlExecutionHandoffCoordination,
} from "@/lib/missionControl/missionControlExecutionHandoffCoordinationApi";
import {
  appendMissionControlBoundedDeliveryWorkPackagesRecord,
  fetchMissionControlBoundedDeliveryWorkPackages,
} from "@/lib/missionControl/missionControlBoundedDeliveryWorkPackagesApi";
import {
  appendMissionControlWorkPackageReadinessLaneAdmissionRecord,
  fetchMissionControlWorkPackageReadinessLaneAdmission,
} from "@/lib/missionControl/missionControlWorkPackageReadinessLaneAdmissionApi";
import {
  appendMissionControlMissionAuthorizationRecord,
  fetchMissionControlMissionAuthorization,
} from "@/lib/missionControl/missionControlMissionAuthorizationApi";
import {
  appendMissionControlBoundedExecutionParticipationRecord,
  fetchMissionControlBoundedExecutionParticipation,
} from "@/lib/missionControl/missionControlBoundedExecutionParticipationApi";
import {
  appendMissionControlGovernedTaskExecutionCoordinationRecord,
  fetchMissionControlGovernedTaskExecutionCoordination,
} from "@/lib/missionControl/missionControlGovernedTaskExecutionCoordinationApi";
import {
  appendMissionControlGateRoutedPackageOutcomeReviewRecord,
  fetchMissionControlGateRoutedPackageOutcomeReview,
} from "@/lib/missionControl/missionControlGateRoutedPackageOutcomeReviewApi";
import {
  appendMissionControlGovernedLaneEntryRecommendationRecord,
  fetchMissionControlGovernedLaneEntryRecommendation,
} from "@/lib/missionControl/missionControlGovernedLaneEntryRecommendationApi";
import {
  appendMissionControlGovernedLaneReadinessBoardRecord,
  fetchMissionControlGovernedLaneReadinessBoard,
} from "@/lib/missionControl/missionControlGovernedLaneReadinessBoardApi";
import {
  appendMissionControlHumanLaneAdmissionDecisionRecord,
  fetchMissionControlHumanLaneAdmissionDecision,
} from "@/lib/missionControl/missionControlHumanLaneAdmissionDecisionApi";
import {
  appendMissionControlGateRoutedLaneEntryHandoffRecord,
  fetchMissionControlGateRoutedLaneEntryHandoff,
} from "@/lib/missionControl/missionControlGateRoutedLaneEntryHandoffApi";
import {
  appendMissionControlFrozenGateIntakePreviewRecord,
  fetchMissionControlFrozenGateIntakePreview,
} from "@/lib/missionControl/missionControlFrozenGateIntakePreviewApi";
import {
  appendMissionControlFrozenGateExecutionRequestAdapterRecord,
  fetchMissionControlFrozenGateExecutionRequestAdapter,
} from "@/lib/missionControl/missionControlFrozenGateExecutionRequestAdapterApi";
import {
  appendMissionControlRepoPilotReadinessDashboardRecord,
  fetchMissionControlRepoPilotReadinessDashboard,
} from "@/lib/missionControl/missionControlRepoPilotReadinessDashboardApi";
import {
  appendMissionControlEndToEndRepoDevelopmentPilotHarnessRecord,
  fetchMissionControlEndToEndRepoDevelopmentPilotHarness,
  runMissionControlEndToEndRepoDevelopmentPilotHarness,
} from "@/lib/missionControl/missionControlEndToEndRepoDevelopmentPilotHarnessApi";
import {
  appendMissionControlGovernedChatCommandInvocationFromHandoffRecord,
  fetchMissionControlGovernedChatCommandInvocationFromHandoff,
  invokeMissionControlGovernedChatCommandFromHandoff,
} from "@/lib/missionControl/missionControlGovernedChatCommandInvocationFromHandoffApi";
import { fetchMissionControlGovernanceSimulation } from "@/lib/missionControl/missionControlGovernanceSimulationApi";
import { fetchMissionControlGovernanceInsights } from "@/lib/missionControl/missionControlGovernanceInsightsApi";
import { fetchMissionControlOperatorGuidance } from "@/lib/missionControl/missionControlOperatorGuidanceApi";
import { fetchMissionControlKnowledgeSpacesSearch } from "@/lib/missionControl/missionControlKnowledgeSpacesApi";
import { fetchMissionControlCrossSessionMemory } from "@/lib/missionControl/missionControlCrossSessionMemoryApi";
import { fetchMissionControlOperationalMemory } from "@/lib/missionControl/missionControlOperationalMemoryApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { buildOperatorContext, useOperatorSession, type OperatorContext } from "@/lib/missionControl/operatorSession";
import { buildTimelineLinkRef, type ReplayDeepLinkTarget } from "@/lib/missionControl/missionControlReplayDeepLink";
import { ReplayDeepLinkButton } from "@/components/missionControl/ReplayDeepLinkButton";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

type Props = {
  sessionId?: string;
  operatorMode?: MissionControlMode;
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
};

type LoadState = "idle" | "loading" | "loaded" | "error";

export function CrossLaneOperationsPanel({
  sessionId: sessionIdProp,
  operatorMode = "operator",
  onOpenReplayDeepLink,
}: Props) {
  const { context: operatorContext, hydrated } = useOperatorSession(sessionIdProp);
  const sessionId = operatorContext?.sessionId ?? sessionIdProp ?? "default";
  const operatorCtx = useMemo(
    () => operatorContext ?? buildOperatorContext(sessionId, operatorMode),
    [operatorContext, sessionId, operatorMode],
  );

  const [snapshot, setSnapshot] = useState<MissionControlCrossLaneSnapshot | null>(null);
  const [meta, setMeta] = useState<{ detail?: string } | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [selectedLane, setSelectedLane] = useState<string | null>(null);
  const [exportState, setExportState] = useState<"idle" | "loading">("idle");
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [memoryMd, setMemoryMd] = useState<string | null>(null);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [crossSessionMd, setCrossSessionMd] = useState<string | null>(null);
  const [crossSessionLoading, setCrossSessionLoading] = useState(false);
  const [knowledgeQuery, setKnowledgeQuery] = useState("");
  const [knowledgeMd, setKnowledgeMd] = useState<string | null>(null);
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [guidanceMd, setGuidanceMd] = useState<string | null>(null);
  const [guidanceLoading, setGuidanceLoading] = useState(false);
  const [govInsightsMd, setGovInsightsMd] = useState<string | null>(null);
  const [govInsightsLoading, setGovInsightsLoading] = useState(false);
  const [govSimMd, setGovSimMd] = useState<string | null>(null);
  const [govSimLoading, setGovSimLoading] = useState(false);
  const [strategyMd, setStrategyMd] = useState<string | null>(null);
  const [strategyLoading, setStrategyLoading] = useState(false);
  const [orchestrationMd, setOrchestrationMd] = useState<string | null>(null);
  const [orchestrationLoading, setOrchestrationLoading] = useState(false);
  const [readinessMd, setReadinessMd] = useState<string | null>(null);
  const [readinessLoading, setReadinessLoading] = useState(false);
  const [deliberationMd, setDeliberationMd] = useState<string | null>(null);
  const [deliberationLoading, setDeliberationLoading] = useState(false);
  const [deliberationNote, setDeliberationNote] = useState("");
  const [deliberationNoteState, setDeliberationNoteState] = useState<"idle" | "saving">("idle");
  const [collaborationMd, setCollaborationMd] = useState<string | null>(null);
  const [collaborationLoading, setCollaborationLoading] = useState(false);
  const [collaborationAck, setCollaborationAck] = useState("");
  const [collaborationReviewer, setCollaborationReviewer] = useState("");
  const [collaborationAckState, setCollaborationAckState] = useState<"idle" | "saving">("idle");
  const [roleArchMd, setRoleArchMd] = useState<string | null>(null);
  const [roleArchLoading, setRoleArchLoading] = useState(false);
  const [doctrineMd, setDoctrineMd] = useState<string | null>(null);
  const [doctrineLoading, setDoctrineLoading] = useState(false);
  const [doctrineAmendment, setDoctrineAmendment] = useState("");
  const [doctrineAmendmentState, setDoctrineAmendmentState] = useState<"idle" | "saving">("idle");
  const [interpretationMd, setInterpretationMd] = useState<string | null>(null);
  const [interpretationLoading, setInterpretationLoading] = useState(false);
  const [interpretationNote, setInterpretationNote] = useState("");
  const [interpretationNoteState, setInterpretationNoteState] = useState<"idle" | "saving">("idle");
  const [coherenceMd, setCoherenceMd] = useState<string | null>(null);
  const [coherenceLoading, setCoherenceLoading] = useState(false);
  const [coherenceObservation, setCoherenceObservation] = useState("");
  const [coherenceObservationState, setCoherenceObservationState] = useState<"idle" | "saving">("idle");
  const [resilienceMd, setResilienceMd] = useState<string | null>(null);
  const [resilienceLoading, setResilienceLoading] = useState(false);
  const [resilienceObservation, setResilienceObservation] = useState("");
  const [resilienceObservationState, setResilienceObservationState] = useState<"idle" | "saving">("idle");
  const [evolutionMd, setEvolutionMd] = useState<string | null>(null);
  const [evolutionLoading, setEvolutionLoading] = useState(false);
  const [evolutionContinuity, setEvolutionContinuity] = useState("");
  const [evolutionContinuityState, setEvolutionContinuityState] = useState<"idle" | "saving">("idle");
  const [identityMd, setIdentityMd] = useState<string | null>(null);
  const [identityLoading, setIdentityLoading] = useState(false);
  const [identityIntent, setIdentityIntent] = useState("");
  const [identityIntentState, setIdentityIntentState] = useState<"idle" | "saving">("idle");
  const [externalRelationsMd, setExternalRelationsMd] = useState<string | null>(null);
  const [externalRelationsLoading, setExternalRelationsLoading] = useState(false);
  const [externalBoundary, setExternalBoundary] = useState("");
  const [externalBoundaryState, setExternalBoundaryState] = useState<"idle" | "saving">("idle");
  const [existentialRiskMd, setExistentialRiskMd] = useState<string | null>(null);
  const [existentialRiskLoading, setExistentialRiskLoading] = useState(false);
  const [preservationNote, setPreservationNote] = useState("");
  const [preservationNoteState, setPreservationNoteState] = useState<"idle" | "saving">("idle");
  const [constitutionalEthicsMd, setConstitutionalEthicsMd] = useState<string | null>(null);
  const [constitutionalEthicsLoading, setConstitutionalEthicsLoading] = useState(false);
  const [ethicsValueNote, setEthicsValueNote] = useState("");
  const [ethicsValueNoteState, setEthicsValueNoteState] = useState<"idle" | "saving">("idle");
  const [constitutionalAuditMd, setConstitutionalAuditMd] = useState<string | null>(null);
  const [constitutionalAuditLoading, setConstitutionalAuditLoading] = useState(false);
  const [auditAccountabilityNote, setAuditAccountabilityNote] = useState("");
  const [auditAccountabilityNoteState, setAuditAccountabilityNoteState] = useState<"idle" | "saving">("idle");
  const [constitutionalLegitimacyMd, setConstitutionalLegitimacyMd] = useState<string | null>(null);
  const [constitutionalLegitimacyLoading, setConstitutionalLegitimacyLoading] = useState(false);
  const [legitimacyTrustNote, setLegitimacyTrustNote] = useState("");
  const [legitimacyTrustNoteState, setLegitimacyTrustNoteState] = useState<"idle" | "saving">("idle");
  const [constitutionalPluralismMd, setConstitutionalPluralismMd] = useState<string | null>(null);
  const [constitutionalPluralismLoading, setConstitutionalPluralismLoading] = useState(false);
  const [pluralismPerspectiveNote, setPluralismPerspectiveNote] = useState("");
  const [pluralismPerspectiveNoteState, setPluralismPerspectiveNoteState] = useState<"idle" | "saving">("idle");
  const [constitutionalSynthesisMd, setConstitutionalSynthesisMd] = useState<string | null>(null);
  const [constitutionalSynthesisLoading, setConstitutionalSynthesisLoading] = useState(false);
  const [synthesisTensionNote, setSynthesisTensionNote] = useState("");
  const [synthesisTensionNoteState, setSynthesisTensionNoteState] = useState<"idle" | "saving">("idle");
  const [missionPlanningMd, setMissionPlanningMd] = useState<string | null>(null);
  const [missionPlanningLoading, setMissionPlanningLoading] = useState(false);
  const [planningActionOptionNote, setPlanningActionOptionNote] = useState("");
  const [planningActionOptionNoteState, setPlanningActionOptionNoteState] = useState<"idle" | "saving">("idle");
  const [planningDeliberationMd, setPlanningDeliberationMd] = useState<string | null>(null);
  const [planningDeliberationLoading, setPlanningDeliberationLoading] = useState(false);
  const [deliberationPlannerNote, setDeliberationPlannerNote] = useState("");
  const [deliberationPlannerNoteState, setDeliberationPlannerNoteState] = useState<"idle" | "saving">("idle");
  const [humanDecisionBoardMd, setHumanDecisionBoardMd] = useState<string | null>(null);
  const [humanDecisionBoardLoading, setHumanDecisionBoardLoading] = useState(false);
  const [decisionSelectionNote, setDecisionSelectionNote] = useState("");
  const [decisionSelectionNoteState, setDecisionSelectionNoteState] = useState<"idle" | "saving">("idle");
  const [executionHandoffMd, setExecutionHandoffMd] = useState<string | null>(null);
  const [executionHandoffLoading, setExecutionHandoffLoading] = useState(false);
  const [handoffArtifactNote, setHandoffArtifactNote] = useState("");
  const [handoffArtifactNoteState, setHandoffArtifactNoteState] = useState<"idle" | "saving">("idle");
  const [deliveryWorkPackagesMd, setDeliveryWorkPackagesMd] = useState<string | null>(null);
  const [deliveryWorkPackagesLoading, setDeliveryWorkPackagesLoading] = useState(false);
  const [workPackageArtifactNote, setWorkPackageArtifactNote] = useState("");
  const [workPackageArtifactNoteState, setWorkPackageArtifactNoteState] = useState<"idle" | "saving">("idle");
  const [laneAdmissionMd, setLaneAdmissionMd] = useState<string | null>(null);
  const [laneAdmissionLoading, setLaneAdmissionLoading] = useState(false);
  const [laneAdmissionArtifactNote, setLaneAdmissionArtifactNote] = useState("");
  const [laneAdmissionArtifactNoteState, setLaneAdmissionArtifactNoteState] = useState<"idle" | "saving">("idle");
  const [missionAuthorizationMd, setMissionAuthorizationMd] = useState<string | null>(null);
  const [missionAuthorizationLoading, setMissionAuthorizationLoading] = useState(false);
  const [missionAuthorizationArtifactNote, setMissionAuthorizationArtifactNote] = useState("");
  const [missionAuthorizationArtifactNoteState, setMissionAuthorizationArtifactNoteState] = useState<
    "idle" | "saving"
  >("idle");
  const [boundedExecutionParticipationMd, setBoundedExecutionParticipationMd] = useState<string | null>(null);
  const [boundedExecutionParticipationLoading, setBoundedExecutionParticipationLoading] = useState(false);
  const [boundedExecutionParticipationArtifactNote, setBoundedExecutionParticipationArtifactNote] = useState("");
  const [boundedExecutionParticipationArtifactNoteState, setBoundedExecutionParticipationArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [governedTaskExecutionCoordinationMd, setGovernedTaskExecutionCoordinationMd] = useState<string | null>(null);
  const [governedTaskExecutionCoordinationLoading, setGovernedTaskExecutionCoordinationLoading] = useState(false);
  const [governedTaskExecutionCoordinationArtifactNote, setGovernedTaskExecutionCoordinationArtifactNote] =
    useState("");
  const [governedTaskExecutionCoordinationArtifactNoteState, setGovernedTaskExecutionCoordinationArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [gateRoutedPackageOutcomeReviewMd, setGateRoutedPackageOutcomeReviewMd] = useState<string | null>(null);
  const [gateRoutedPackageOutcomeReviewLoading, setGateRoutedPackageOutcomeReviewLoading] = useState(false);
  const [gateRoutedPackageOutcomeReviewArtifactNote, setGateRoutedPackageOutcomeReviewArtifactNote] =
    useState("");
  const [gateRoutedPackageOutcomeReviewArtifactNoteState, setGateRoutedPackageOutcomeReviewArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [governedLaneEntryRecommendationMd, setGovernedLaneEntryRecommendationMd] = useState<string | null>(null);
  const [governedLaneEntryRecommendationLoading, setGovernedLaneEntryRecommendationLoading] = useState(false);
  const [governedLaneEntryRecommendationArtifactNote, setGovernedLaneEntryRecommendationArtifactNote] =
    useState("");
  const [governedLaneEntryRecommendationArtifactNoteState, setGovernedLaneEntryRecommendationArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [governedLaneReadinessBoardMd, setGovernedLaneReadinessBoardMd] = useState<string | null>(null);
  const [governedLaneReadinessBoardLoading, setGovernedLaneReadinessBoardLoading] = useState(false);
  const [governedLaneReadinessBoardArtifactNote, setGovernedLaneReadinessBoardArtifactNote] = useState("");
  const [governedLaneReadinessBoardArtifactNoteState, setGovernedLaneReadinessBoardArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [humanLaneAdmissionDecisionMd, setHumanLaneAdmissionDecisionMd] = useState<string | null>(null);
  const [humanLaneAdmissionDecisionLoading, setHumanLaneAdmissionDecisionLoading] = useState(false);
  const [humanLaneAdmissionDecisionArtifactNote, setHumanLaneAdmissionDecisionArtifactNote] = useState("");
  const [humanLaneAdmissionDecisionArtifactNoteState, setHumanLaneAdmissionDecisionArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [gateRoutedLaneEntryHandoffMd, setGateRoutedLaneEntryHandoffMd] = useState<string | null>(null);
  const [gateRoutedLaneEntryHandoffLoading, setGateRoutedLaneEntryHandoffLoading] = useState(false);
  const [gateRoutedLaneEntryHandoffArtifactNote, setGateRoutedLaneEntryHandoffArtifactNote] = useState("");
  const [gateRoutedLaneEntryHandoffArtifactNoteState, setGateRoutedLaneEntryHandoffArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [frozenGateIntakePreviewMd, setFrozenGateIntakePreviewMd] = useState<string | null>(null);
  const [frozenGateIntakePreviewLoading, setFrozenGateIntakePreviewLoading] = useState(false);
  const [frozenGateIntakePreviewArtifactNote, setFrozenGateIntakePreviewArtifactNote] = useState("");
  const [frozenGateIntakePreviewArtifactNoteState, setFrozenGateIntakePreviewArtifactNoteState] =
    useState<"idle" | "saving">("idle");
  const [frozenGateExecutionRequestAdapterMd, setFrozenGateExecutionRequestAdapterMd] = useState<string | null>(
    null,
  );
  const [frozenGateExecutionRequestAdapterLoading, setFrozenGateExecutionRequestAdapterLoading] =
    useState(false);
  const [frozenGateExecutionRequestAdapterArtifactNote, setFrozenGateExecutionRequestAdapterArtifactNote] =
    useState("");
  const [
    frozenGateExecutionRequestAdapterArtifactNoteState,
    setFrozenGateExecutionRequestAdapterArtifactNoteState,
  ] = useState<"idle" | "saving">("idle");
  const [governedChatCommandInvocationFromHandoffMd, setGovernedChatCommandInvocationFromHandoffMd] =
    useState<string | null>(null);
  const [governedChatCommandInvocationFromHandoffLoading, setGovernedChatCommandInvocationFromHandoffLoading] =
    useState(false);
  const [governedChatCommandInvocationFromHandoffArtifactNote, setGovernedChatCommandInvocationFromHandoffArtifactNote] =
    useState("");
  const [
    governedChatCommandInvocationFromHandoffArtifactNoteState,
    setGovernedChatCommandInvocationFromHandoffArtifactNoteState,
  ] = useState<"idle" | "saving">("idle");
  const [governedChatCommandInvocationInvokeState, setGovernedChatCommandInvocationInvokeState] = useState<
    "idle" | "invoking"
  >("idle");
  const [endToEndRepoDevelopmentPilotHarnessMd, setEndToEndRepoDevelopmentPilotHarnessMd] = useState<string | null>(
    null,
  );
  const [endToEndRepoDevelopmentPilotHarnessLoading, setEndToEndRepoDevelopmentPilotHarnessLoading] =
    useState(false);
  const [endToEndRepoDevelopmentPilotHarnessArtifactNote, setEndToEndRepoDevelopmentPilotHarnessArtifactNote] =
    useState("");
  const [
    endToEndRepoDevelopmentPilotHarnessArtifactNoteState,
    setEndToEndRepoDevelopmentPilotHarnessArtifactNoteState,
  ] = useState<"idle" | "saving">("idle");
  const [endToEndPilotRunState, setEndToEndPilotRunState] = useState<"idle" | "running">("idle");
  const [repoPilotReadinessDashboardMd, setRepoPilotReadinessDashboardMd] = useState<string | null>(null);
  const [repoPilotReadinessDashboardLoading, setRepoPilotReadinessDashboardLoading] = useState(false);
  const [repoPilotReadinessDashboardArtifactNote, setRepoPilotReadinessDashboardArtifactNote] = useState("");
  const [repoPilotReadinessDashboardArtifactNoteState, setRepoPilotReadinessDashboardArtifactNoteState] = useState<
    "idle" | "saving"
  >("idle");

  const load = useCallback(async () => {
    if (!hydrated) return;
    try {
      setLoadState("loading");
      setErrorMessage(null);
      const res = await fetchMissionControlCrossLaneSnapshot(sessionId);
      setSnapshot(res.snapshot);
      setMeta({ detail: res.detail });
      setLoadState("loaded");
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : "Failed to load cross-lane snapshot");
      setSnapshot(null);
      setLoadState("error");
    }
  }, [sessionId, hydrated]);

  useEffect(() => {
    void load();
  }, [load]);

  const handleLaneFocus = useCallback((lane: string) => {
    setSelectedLane(lane);
    scrollToLaneAnchor(lane);
  }, []);

  const handleExport = useCallback(
    async (kind: "json" | "markdown") => {
      if (!hydrated) return;
      try {
        setExportState("loading");
        setExportMessage(null);
        const format = kind === "json" ? "json" : "markdown";
        const res = await fetchMissionControlEvidenceBundle(sessionId, format);
        const correlation = snapshot?.correlation_id;
        if (kind === "json" && res.bundle) {
          downloadTextFile(
            JSON.stringify(res.bundle, null, 2),
            evidenceBundleJsonFilename(sessionId, correlation),
            "application/json;charset=utf-8",
          );
          setExportMessage("Evidence bundle JSON downloaded.");
        } else if (kind === "markdown" && res.markdown) {
          downloadTextFile(
            res.markdown,
            evidenceBundleMarkdownFilename(sessionId, correlation),
            "text/markdown;charset=utf-8",
          );
          setExportMessage("Evidence bundle Markdown downloaded.");
        } else {
          setExportMessage("Export returned no content.");
        }
      } catch (e) {
        setExportMessage(e instanceof Error ? e.message : "Evidence export failed");
      } finally {
        setExportState("idle");
      }
    },
    [hydrated, sessionId, snapshot?.correlation_id],
  );

  const handleShowOperationalMemory = useCallback(async () => {
    try {
      setMemoryLoading(true);
      setMemoryMd(null);
      const res = await fetchMissionControlOperationalMemory(sessionId, "markdown");
      setMemoryMd(res.markdown ?? "No operational memory graph returned.");
    } catch (e) {
      setMemoryMd(e instanceof Error ? e.message : "Failed to load operational memory");
    } finally {
      setMemoryLoading(false);
    }
  }, [sessionId]);

  const handleShowCrossSessionMemory = useCallback(async () => {
    try {
      setCrossSessionLoading(true);
      setCrossSessionMd(null);
      const res = await fetchMissionControlCrossSessionMemory(sessionId, "markdown", { ingestCurrent: true });
      setCrossSessionMd(res.markdown ?? "No cross-session memory returned.");
    } catch (e) {
      setCrossSessionMd(e instanceof Error ? e.message : "Failed to load cross-session memory");
    } finally {
      setCrossSessionLoading(false);
    }
  }, [sessionId]);

  const handleKnowledgeSearch = useCallback(async () => {
    const q = knowledgeQuery.trim() || "blockers approvals incidents";
    try {
      setKnowledgeLoading(true);
      setKnowledgeMd(null);
      const res = await fetchMissionControlKnowledgeSpacesSearch(sessionId, q, "markdown", {
        ingestCurrent: true,
      });
      setKnowledgeMd(res.markdown ?? "No knowledge space results.");
    } catch (e) {
      setKnowledgeMd(e instanceof Error ? e.message : "Knowledge space search failed");
    } finally {
      setKnowledgeLoading(false);
    }
  }, [sessionId, knowledgeQuery]);

  const handleOperatorGuidance = useCallback(async () => {
    try {
      setGuidanceLoading(true);
      setGuidanceMd(null);
      const res = await fetchMissionControlOperatorGuidance(sessionId, "markdown");
      setGuidanceMd(res.markdown ?? "No operator guidance returned.");
    } catch (e) {
      setGuidanceMd(e instanceof Error ? e.message : "Operator guidance failed");
    } finally {
      setGuidanceLoading(false);
    }
  }, [sessionId]);

  const handleGovernanceInsights = useCallback(async () => {
    try {
      setGovInsightsLoading(true);
      setGovInsightsMd(null);
      const res = await fetchMissionControlGovernanceInsights(sessionId, "markdown");
      setGovInsightsMd(res.markdown ?? "No governance insights returned.");
    } catch (e) {
      setGovInsightsMd(e instanceof Error ? e.message : "Governance insights failed");
    } finally {
      setGovInsightsLoading(false);
    }
  }, [sessionId]);

  const handleGovernanceSimulation = useCallback(async () => {
    try {
      setGovSimLoading(true);
      setGovSimMd(null);
      const res = await fetchMissionControlGovernanceSimulation(sessionId, "markdown", "all");
      setGovSimMd(res.markdown ?? "No governance simulation returned.");
    } catch (e) {
      setGovSimMd(e instanceof Error ? e.message : "Governance simulation failed");
    } finally {
      setGovSimLoading(false);
    }
  }, [sessionId]);

  const handleMissionStrategy = useCallback(async () => {
    try {
      setStrategyLoading(true);
      setStrategyMd(null);
      const res = await fetchMissionControlMissionStrategy(sessionId, "markdown");
      setStrategyMd(res.markdown ?? "No mission strategy returned.");
    } catch (e) {
      setStrategyMd(e instanceof Error ? e.message : "Mission strategy failed");
    } finally {
      setStrategyLoading(false);
    }
  }, [sessionId]);

  const handleMissionOrchestration = useCallback(async () => {
    try {
      setOrchestrationLoading(true);
      setOrchestrationMd(null);
      const res = await fetchMissionControlMissionOrchestration(sessionId, "markdown");
      setOrchestrationMd(res.markdown ?? "No mission orchestration returned.");
    } catch (e) {
      setOrchestrationMd(e instanceof Error ? e.message : "Mission orchestration failed");
    } finally {
      setOrchestrationLoading(false);
    }
  }, [sessionId]);

  const handleMissionReadinessReview = useCallback(async () => {
    try {
      setReadinessLoading(true);
      setReadinessMd(null);
      const res = await fetchMissionControlMissionReadinessReview(sessionId, "markdown");
      setReadinessMd(res.markdown ?? "No readiness review returned.");
    } catch (e) {
      setReadinessMd(e instanceof Error ? e.message : "Readiness review failed");
    } finally {
      setReadinessLoading(false);
    }
  }, [sessionId]);

  const handleGovernanceDeliberation = useCallback(async () => {
    try {
      setDeliberationLoading(true);
      setDeliberationMd(null);
      const res = await fetchMissionControlGovernanceDeliberation(sessionId, "markdown");
      setDeliberationMd(res.markdown ?? "No governance deliberation returned.");
    } catch (e) {
      setDeliberationMd(e instanceof Error ? e.message : "Governance deliberation failed");
    } finally {
      setDeliberationLoading(false);
    }
  }, [sessionId]);

  const handleSaveDeliberationNote = useCallback(async () => {
    const note = deliberationNote.trim();
    if (!note) return;
    try {
      setDeliberationNoteState("saving");
      await appendMissionControlGovernanceDeliberationRecord(sessionId, "operator_note", note);
      setDeliberationNote("");
      await handleGovernanceDeliberation();
    } catch (e) {
      setDeliberationMd(e instanceof Error ? e.message : "Failed to save deliberation note");
    } finally {
      setDeliberationNoteState("idle");
    }
  }, [sessionId, deliberationNote, handleGovernanceDeliberation]);

  const handleGovernanceCollaboration = useCallback(async () => {
    try {
      setCollaborationLoading(true);
      setCollaborationMd(null);
      const res = await fetchMissionControlGovernanceCollaboration(sessionId, "markdown");
      setCollaborationMd(res.markdown ?? "No governance collaboration returned.");
    } catch (e) {
      setCollaborationMd(e instanceof Error ? e.message : "Governance collaboration failed");
    } finally {
      setCollaborationLoading(false);
    }
  }, [sessionId]);

  const handleSaveCollaborationAck = useCallback(async () => {
    const ack = collaborationAck.trim();
    if (!ack) return;
    try {
      setCollaborationAckState("saving");
      await appendMissionControlGovernanceCollaborationRecord(
        sessionId,
        "reviewer_acknowledgment",
        ack,
        collaborationReviewer.trim() || "operator",
        "primary_reviewer",
      );
      setCollaborationAck("");
      await handleGovernanceCollaboration();
    } catch (e) {
      setCollaborationMd(e instanceof Error ? e.message : "Failed to save collaboration acknowledgment");
    } finally {
      setCollaborationAckState("idle");
    }
  }, [sessionId, collaborationAck, collaborationReviewer, handleGovernanceCollaboration]);

  const handleGovernanceRoleArchitecture = useCallback(async () => {
    try {
      setRoleArchLoading(true);
      setRoleArchMd(null);
      const res = await fetchMissionControlGovernanceRoleArchitecture(sessionId, "markdown");
      setRoleArchMd(res.markdown ?? "No governance role architecture returned.");
    } catch (e) {
      setRoleArchMd(e instanceof Error ? e.message : "Governance role architecture failed");
    } finally {
      setRoleArchLoading(false);
    }
  }, [sessionId]);

  const handleGovernanceDoctrine = useCallback(async () => {
    try {
      setDoctrineLoading(true);
      setDoctrineMd(null);
      const res = await fetchMissionControlGovernanceDoctrine(sessionId, "markdown");
      setDoctrineMd(res.markdown ?? "No governance doctrine returned.");
    } catch (e) {
      setDoctrineMd(e instanceof Error ? e.message : "Governance doctrine failed");
    } finally {
      setDoctrineLoading(false);
    }
  }, [sessionId]);

  const handleSaveDoctrineAmendment = useCallback(async () => {
    const text = doctrineAmendment.trim();
    if (!text) return;
    try {
      setDoctrineAmendmentState("saving");
      await appendMissionControlGovernanceDoctrineRecord(
        sessionId,
        "policy_amendment_proposal",
        text,
      );
      setDoctrineAmendment("");
      await handleGovernanceDoctrine();
    } catch (e) {
      setDoctrineMd(e instanceof Error ? e.message : "Failed to save amendment proposal");
    } finally {
      setDoctrineAmendmentState("idle");
    }
  }, [sessionId, doctrineAmendment, handleGovernanceDoctrine]);

  const handleGovernancePolicyInterpretation = useCallback(async () => {
    try {
      setInterpretationLoading(true);
      setInterpretationMd(null);
      const res = await fetchMissionControlGovernancePolicyInterpretation(sessionId, "markdown");
      setInterpretationMd(res.markdown ?? "No governance policy interpretation returned.");
    } catch (e) {
      setInterpretationMd(e instanceof Error ? e.message : "Governance policy interpretation failed");
    } finally {
      setInterpretationLoading(false);
    }
  }, [sessionId]);

  const handleSaveInterpretationNote = useCallback(async () => {
    const text = interpretationNote.trim();
    if (!text) return;
    try {
      setInterpretationNoteState("saving");
      await appendMissionControlGovernancePolicyInterpretationRecord(
        sessionId,
        "doctrine_interpretation",
        text,
      );
      setInterpretationNote("");
      await handleGovernancePolicyInterpretation();
    } catch (e) {
      setInterpretationMd(e instanceof Error ? e.message : "Failed to save interpretation record");
    } finally {
      setInterpretationNoteState("idle");
    }
  }, [sessionId, interpretationNote, handleGovernancePolicyInterpretation]);

  const handleGovernanceCoherence = useCallback(async () => {
    try {
      setCoherenceLoading(true);
      setCoherenceMd(null);
      const res = await fetchMissionControlGovernanceCoherence(sessionId, "markdown");
      setCoherenceMd(res.markdown ?? "No governance coherence returned.");
    } catch (e) {
      setCoherenceMd(e instanceof Error ? e.message : "Governance coherence failed");
    } finally {
      setCoherenceLoading(false);
    }
  }, [sessionId]);

  const handleSaveCoherenceObservation = useCallback(async () => {
    const text = coherenceObservation.trim();
    if (!text) return;
    try {
      setCoherenceObservationState("saving");
      await appendMissionControlGovernanceCoherenceRecord(sessionId, "coherence_observation", text);
      setCoherenceObservation("");
      await handleGovernanceCoherence();
    } catch (e) {
      setCoherenceMd(e instanceof Error ? e.message : "Failed to save coherence observation");
    } finally {
      setCoherenceObservationState("idle");
    }
  }, [sessionId, coherenceObservation, handleGovernanceCoherence]);

  const handleGovernanceResilience = useCallback(async () => {
    try {
      setResilienceLoading(true);
      setResilienceMd(null);
      const res = await fetchMissionControlGovernanceResilience(sessionId, "markdown");
      setResilienceMd(res.markdown ?? "No governance resilience returned.");
    } catch (e) {
      setResilienceMd(e instanceof Error ? e.message : "Governance resilience failed");
    } finally {
      setResilienceLoading(false);
    }
  }, [sessionId]);

  const handleSaveResilienceObservation = useCallback(async () => {
    const text = resilienceObservation.trim();
    if (!text) return;
    try {
      setResilienceObservationState("saving");
      await appendMissionControlGovernanceResilienceRecord(sessionId, "resilience_observation", text);
      setResilienceObservation("");
      await handleGovernanceResilience();
    } catch (e) {
      setResilienceMd(e instanceof Error ? e.message : "Failed to save resilience observation");
    } finally {
      setResilienceObservationState("idle");
    }
  }, [sessionId, resilienceObservation, handleGovernanceResilience]);

  const handleGovernanceEvolution = useCallback(async () => {
    try {
      setEvolutionLoading(true);
      setEvolutionMd(null);
      const res = await fetchMissionControlGovernanceEvolution(sessionId, "markdown");
      setEvolutionMd(res.markdown ?? "No governance evolution returned.");
    } catch (e) {
      setEvolutionMd(e instanceof Error ? e.message : "Governance evolution failed");
    } finally {
      setEvolutionLoading(false);
    }
  }, [sessionId]);

  const handleSaveEvolutionContinuity = useCallback(async () => {
    const text = evolutionContinuity.trim();
    if (!text) return;
    try {
      setEvolutionContinuityState("saving");
      await appendMissionControlGovernanceEvolutionRecord(sessionId, "continuity_observation", text);
      setEvolutionContinuity("");
      await handleGovernanceEvolution();
    } catch (e) {
      setEvolutionMd(e instanceof Error ? e.message : "Failed to save continuity observation");
    } finally {
      setEvolutionContinuityState("idle");
    }
  }, [sessionId, evolutionContinuity, handleGovernanceEvolution]);

  const handleInstitutionalIdentity = useCallback(async () => {
    try {
      setIdentityLoading(true);
      setIdentityMd(null);
      const res = await fetchMissionControlInstitutionalIdentity(sessionId, "markdown");
      setIdentityMd(res.markdown ?? "No institutional identity returned.");
    } catch (e) {
      setIdentityMd(e instanceof Error ? e.message : "Institutional identity failed");
    } finally {
      setIdentityLoading(false);
    }
  }, [sessionId]);

  const handleSaveIdentityIntent = useCallback(async () => {
    const text = identityIntent.trim();
    if (!text) return;
    try {
      setIdentityIntentState("saving");
      await appendMissionControlInstitutionalIdentityRecord(sessionId, "constitutional_intent", text);
      setIdentityIntent("");
      await handleInstitutionalIdentity();
    } catch (e) {
      setIdentityMd(e instanceof Error ? e.message : "Failed to save constitutional intent");
    } finally {
      setIdentityIntentState("idle");
    }
  }, [sessionId, identityIntent, handleInstitutionalIdentity]);

  const handleInstitutionalExternalRelations = useCallback(async () => {
    try {
      setExternalRelationsLoading(true);
      setExternalRelationsMd(null);
      const res = await fetchMissionControlInstitutionalExternalRelations(sessionId, "markdown");
      setExternalRelationsMd(res.markdown ?? "No institutional external relations returned.");
    } catch (e) {
      setExternalRelationsMd(e instanceof Error ? e.message : "Institutional external relations failed");
    } finally {
      setExternalRelationsLoading(false);
    }
  }, [sessionId]);

  const handleSaveExternalBoundary = useCallback(async () => {
    const text = externalBoundary.trim();
    if (!text) return;
    try {
      setExternalBoundaryState("saving");
      await appendMissionControlInstitutionalExternalRelationsRecord(sessionId, "boundary_definition", text);
      setExternalBoundary("");
      await handleInstitutionalExternalRelations();
    } catch (e) {
      setExternalRelationsMd(e instanceof Error ? e.message : "Failed to save boundary definition");
    } finally {
      setExternalBoundaryState("idle");
    }
  }, [sessionId, externalBoundary, handleInstitutionalExternalRelations]);

  const handleInstitutionalExistentialRisk = useCallback(async () => {
    try {
      setExistentialRiskLoading(true);
      setExistentialRiskMd(null);
      const res = await fetchMissionControlInstitutionalExistentialRisk(sessionId, "markdown");
      setExistentialRiskMd(res.markdown ?? "No institutional existential risk returned.");
    } catch (e) {
      setExistentialRiskMd(e instanceof Error ? e.message : "Institutional existential risk failed");
    } finally {
      setExistentialRiskLoading(false);
    }
  }, [sessionId]);

  const handleSavePreservationNote = useCallback(async () => {
    const text = preservationNote.trim();
    if (!text) return;
    try {
      setPreservationNoteState("saving");
      await appendMissionControlInstitutionalExistentialRiskRecord(sessionId, "preservation_recommendation", text);
      setPreservationNote("");
      await handleInstitutionalExistentialRisk();
    } catch (e) {
      setExistentialRiskMd(e instanceof Error ? e.message : "Failed to save preservation recommendation");
    } finally {
      setPreservationNoteState("idle");
    }
  }, [sessionId, preservationNote, handleInstitutionalExistentialRisk]);

  const handleConstitutionalEthics = useCallback(async () => {
    try {
      setConstitutionalEthicsLoading(true);
      setConstitutionalEthicsMd(null);
      const res = await fetchMissionControlConstitutionalEthics(sessionId, "markdown");
      setConstitutionalEthicsMd(res.markdown ?? "No constitutional ethics returned.");
    } catch (e) {
      setConstitutionalEthicsMd(e instanceof Error ? e.message : "Constitutional ethics failed");
    } finally {
      setConstitutionalEthicsLoading(false);
    }
  }, [sessionId]);

  const handleSaveEthicsValueNote = useCallback(async () => {
    const text = ethicsValueNote.trim();
    if (!text) return;
    try {
      setEthicsValueNoteState("saving");
      await appendMissionControlConstitutionalEthicsRecord(sessionId, "value_preservation_note", text);
      setEthicsValueNote("");
      await handleConstitutionalEthics();
    } catch (e) {
      setConstitutionalEthicsMd(e instanceof Error ? e.message : "Failed to save ethics value note");
    } finally {
      setEthicsValueNoteState("idle");
    }
  }, [sessionId, ethicsValueNote, handleConstitutionalEthics]);

  const handleConstitutionalAudit = useCallback(async () => {
    try {
      setConstitutionalAuditLoading(true);
      setConstitutionalAuditMd(null);
      const res = await fetchMissionControlConstitutionalAudit(sessionId, "markdown");
      setConstitutionalAuditMd(res.markdown ?? "No constitutional audit returned.");
    } catch (e) {
      setConstitutionalAuditMd(e instanceof Error ? e.message : "Constitutional audit failed");
    } finally {
      setConstitutionalAuditLoading(false);
    }
  }, [sessionId]);

  const handleSaveAuditAccountabilityNote = useCallback(async () => {
    const text = auditAccountabilityNote.trim();
    if (!text) return;
    try {
      setAuditAccountabilityNoteState("saving");
      await appendMissionControlConstitutionalAuditRecord(sessionId, "accountability_record", text);
      setAuditAccountabilityNote("");
      await handleConstitutionalAudit();
    } catch (e) {
      setConstitutionalAuditMd(e instanceof Error ? e.message : "Failed to save accountability record");
    } finally {
      setAuditAccountabilityNoteState("idle");
    }
  }, [sessionId, auditAccountabilityNote, handleConstitutionalAudit]);

  const handleConstitutionalLegitimacy = useCallback(async () => {
    try {
      setConstitutionalLegitimacyLoading(true);
      setConstitutionalLegitimacyMd(null);
      const res = await fetchMissionControlConstitutionalLegitimacy(sessionId, "markdown");
      setConstitutionalLegitimacyMd(res.markdown ?? "No constitutional legitimacy returned.");
    } catch (e) {
      setConstitutionalLegitimacyMd(e instanceof Error ? e.message : "Constitutional legitimacy failed");
    } finally {
      setConstitutionalLegitimacyLoading(false);
    }
  }, [sessionId]);

  const handleSaveLegitimacyTrustNote = useCallback(async () => {
    const text = legitimacyTrustNote.trim();
    if (!text) return;
    try {
      setLegitimacyTrustNoteState("saving");
      await appendMissionControlConstitutionalLegitimacyRecord(sessionId, "trust_continuity_note", text);
      setLegitimacyTrustNote("");
      await handleConstitutionalLegitimacy();
    } catch (e) {
      setConstitutionalLegitimacyMd(e instanceof Error ? e.message : "Failed to save trust continuity note");
    } finally {
      setLegitimacyTrustNoteState("idle");
    }
  }, [sessionId, legitimacyTrustNote, handleConstitutionalLegitimacy]);

  const handleConstitutionalPluralism = useCallback(async () => {
    try {
      setConstitutionalPluralismLoading(true);
      setConstitutionalPluralismMd(null);
      const res = await fetchMissionControlConstitutionalPluralism(sessionId, "markdown");
      setConstitutionalPluralismMd(res.markdown ?? "No constitutional pluralism returned.");
    } catch (e) {
      setConstitutionalPluralismMd(e instanceof Error ? e.message : "Constitutional pluralism failed");
    } finally {
      setConstitutionalPluralismLoading(false);
    }
  }, [sessionId]);

  const handleSavePluralismPerspectiveNote = useCallback(async () => {
    const text = pluralismPerspectiveNote.trim();
    if (!text) return;
    try {
      setPluralismPerspectiveNoteState("saving");
      await appendMissionControlConstitutionalPluralismRecord(sessionId, "perspective_mapping_note", text);
      setPluralismPerspectiveNote("");
      await handleConstitutionalPluralism();
    } catch (e) {
      setConstitutionalPluralismMd(e instanceof Error ? e.message : "Failed to save perspective mapping note");
    } finally {
      setPluralismPerspectiveNoteState("idle");
    }
  }, [sessionId, pluralismPerspectiveNote, handleConstitutionalPluralism]);

  const handleConstitutionalSynthesis = useCallback(async () => {
    try {
      setConstitutionalSynthesisLoading(true);
      setConstitutionalSynthesisMd(null);
      const res = await fetchMissionControlConstitutionalSynthesis(sessionId, "markdown");
      setConstitutionalSynthesisMd(res.markdown ?? "No constitutional synthesis returned.");
    } catch (e) {
      setConstitutionalSynthesisMd(e instanceof Error ? e.message : "Constitutional synthesis failed");
    } finally {
      setConstitutionalSynthesisLoading(false);
    }
  }, [sessionId]);

  const handleSaveSynthesisTensionNote = useCallback(async () => {
    const text = synthesisTensionNote.trim();
    if (!text) return;
    try {
      setSynthesisTensionNoteState("saving");
      await appendMissionControlConstitutionalSynthesisRecord(sessionId, "tension_analysis_note", text);
      setSynthesisTensionNote("");
      await handleConstitutionalSynthesis();
    } catch (e) {
      setConstitutionalSynthesisMd(e instanceof Error ? e.message : "Failed to save tension analysis note");
    } finally {
      setSynthesisTensionNoteState("idle");
    }
  }, [sessionId, synthesisTensionNote, handleConstitutionalSynthesis]);

  const handleMissionPlanning = useCallback(async () => {
    try {
      setMissionPlanningLoading(true);
      setMissionPlanningMd(null);
      const res = await fetchMissionControlMissionPlanning(sessionId, "markdown");
      setMissionPlanningMd(res.markdown ?? "No mission planning returned.");
    } catch (e) {
      setMissionPlanningMd(e instanceof Error ? e.message : "Mission planning failed");
    } finally {
      setMissionPlanningLoading(false);
    }
  }, [sessionId]);

  const handleSavePlanningActionOptionNote = useCallback(async () => {
    const text = planningActionOptionNote.trim();
    if (!text) return;
    try {
      setPlanningActionOptionNoteState("saving");
      await appendMissionControlMissionPlanningRecord(sessionId, "action_option_note", text);
      setPlanningActionOptionNote("");
      await handleMissionPlanning();
    } catch (e) {
      setMissionPlanningMd(e instanceof Error ? e.message : "Failed to save action option note");
    } finally {
      setPlanningActionOptionNoteState("idle");
    }
  }, [sessionId, planningActionOptionNote, handleMissionPlanning]);

  const handlePlanningDeliberation = useCallback(async () => {
    try {
      setPlanningDeliberationLoading(true);
      setPlanningDeliberationMd(null);
      const res = await fetchMissionControlMissionPlanningDeliberation(sessionId, "markdown");
      setPlanningDeliberationMd(res.markdown ?? "No planning deliberation returned.");
    } catch (e) {
      setPlanningDeliberationMd(e instanceof Error ? e.message : "Planning deliberation failed");
    } finally {
      setPlanningDeliberationLoading(false);
    }
  }, [sessionId]);

  const handleSaveDeliberationPlannerNote = useCallback(async () => {
    const text = deliberationPlannerNote.trim();
    if (!text) return;
    try {
      setDeliberationPlannerNoteState("saving");
      await appendMissionControlMissionPlanningDeliberationRecord(sessionId, "planner_analysis_note", text);
      setDeliberationPlannerNote("");
      await handlePlanningDeliberation();
    } catch (e) {
      setPlanningDeliberationMd(e instanceof Error ? e.message : "Failed to save planner analysis note");
    } finally {
      setDeliberationPlannerNoteState("idle");
    }
  }, [sessionId, deliberationPlannerNote, handlePlanningDeliberation]);

  const handleHumanDecisionBoard = useCallback(async () => {
    try {
      setHumanDecisionBoardLoading(true);
      setHumanDecisionBoardMd(null);
      const res = await fetchMissionControlHumanDecisionBoard(sessionId, "markdown");
      setHumanDecisionBoardMd(res.markdown ?? "No human decision board returned.");
    } catch (e) {
      setHumanDecisionBoardMd(e instanceof Error ? e.message : "Human decision board failed");
    } finally {
      setHumanDecisionBoardLoading(false);
    }
  }, [sessionId]);

  const handleSaveDecisionSelectionNote = useCallback(async () => {
    const text = decisionSelectionNote.trim();
    if (!text) return;
    try {
      setDecisionSelectionNoteState("saving");
      await appendMissionControlHumanDecisionBoardRecord(sessionId, "selection_record", text);
      setDecisionSelectionNote("");
      await handleHumanDecisionBoard();
    } catch (e) {
      setHumanDecisionBoardMd(e instanceof Error ? e.message : "Failed to save human selection record");
    } finally {
      setDecisionSelectionNoteState("idle");
    }
  }, [sessionId, decisionSelectionNote, handleHumanDecisionBoard]);

  const handleExecutionHandoff = useCallback(async () => {
    try {
      setExecutionHandoffLoading(true);
      setExecutionHandoffMd(null);
      const res = await fetchMissionControlExecutionHandoffCoordination(sessionId, "markdown");
      setExecutionHandoffMd(res.markdown ?? "No execution handoff returned.");
    } catch (e) {
      setExecutionHandoffMd(e instanceof Error ? e.message : "Execution handoff failed");
    } finally {
      setExecutionHandoffLoading(false);
    }
  }, [sessionId]);

  const handleSaveHandoffArtifactNote = useCallback(async () => {
    const text = handoffArtifactNote.trim();
    if (!text) return;
    try {
      setHandoffArtifactNoteState("saving");
      await appendMissionControlExecutionHandoffCoordinationRecord(sessionId, "handoff_artifact", text);
      setHandoffArtifactNote("");
      await handleExecutionHandoff();
    } catch (e) {
      setExecutionHandoffMd(e instanceof Error ? e.message : "Failed to save handoff artifact note");
    } finally {
      setHandoffArtifactNoteState("idle");
    }
  }, [sessionId, handoffArtifactNote, handleExecutionHandoff]);

  const handleDeliveryWorkPackages = useCallback(async () => {
    try {
      setDeliveryWorkPackagesLoading(true);
      setDeliveryWorkPackagesMd(null);
      const res = await fetchMissionControlBoundedDeliveryWorkPackages(sessionId, "markdown");
      setDeliveryWorkPackagesMd(res.markdown ?? "No delivery work packages returned.");
    } catch (e) {
      setDeliveryWorkPackagesMd(e instanceof Error ? e.message : "Delivery work packages failed");
    } finally {
      setDeliveryWorkPackagesLoading(false);
    }
  }, [sessionId]);

  const handleSaveWorkPackageArtifactNote = useCallback(async () => {
    const text = workPackageArtifactNote.trim();
    if (!text) return;
    try {
      setWorkPackageArtifactNoteState("saving");
      await appendMissionControlBoundedDeliveryWorkPackagesRecord(sessionId, "work_package_artifact", text);
      setWorkPackageArtifactNote("");
      await handleDeliveryWorkPackages();
    } catch (e) {
      setDeliveryWorkPackagesMd(e instanceof Error ? e.message : "Failed to save work package artifact note");
    } finally {
      setWorkPackageArtifactNoteState("idle");
    }
  }, [sessionId, workPackageArtifactNote, handleDeliveryWorkPackages]);

  const handleLaneAdmissionReadiness = useCallback(async () => {
    try {
      setLaneAdmissionLoading(true);
      setLaneAdmissionMd(null);
      const res = await fetchMissionControlWorkPackageReadinessLaneAdmission(sessionId, "markdown");
      setLaneAdmissionMd(res.markdown ?? "No lane admission readiness returned.");
    } catch (e) {
      setLaneAdmissionMd(e instanceof Error ? e.message : "Lane admission readiness failed");
    } finally {
      setLaneAdmissionLoading(false);
    }
  }, [sessionId]);

  const handleSaveLaneAdmissionArtifactNote = useCallback(async () => {
    const text = laneAdmissionArtifactNote.trim();
    if (!text) return;
    try {
      setLaneAdmissionArtifactNoteState("saving");
      await appendMissionControlWorkPackageReadinessLaneAdmissionRecord(sessionId, "lane_admission_artifact", text);
      setLaneAdmissionArtifactNote("");
      await handleLaneAdmissionReadiness();
    } catch (e) {
      setLaneAdmissionMd(e instanceof Error ? e.message : "Failed to save lane admission artifact note");
    } finally {
      setLaneAdmissionArtifactNoteState("idle");
    }
  }, [sessionId, laneAdmissionArtifactNote, handleLaneAdmissionReadiness]);

  const handleMissionAuthorization = useCallback(async () => {
    try {
      setMissionAuthorizationLoading(true);
      setMissionAuthorizationMd(null);
      const res = await fetchMissionControlMissionAuthorization(sessionId, "markdown");
      setMissionAuthorizationMd(res.markdown ?? "No mission authorization returned.");
    } catch (e) {
      setMissionAuthorizationMd(e instanceof Error ? e.message : "Mission authorization failed");
    } finally {
      setMissionAuthorizationLoading(false);
    }
  }, [sessionId]);

  const handleSaveMissionAuthorizationArtifactNote = useCallback(async () => {
    const text = missionAuthorizationArtifactNote.trim();
    if (!text) return;
    try {
      setMissionAuthorizationArtifactNoteState("saving");
      await appendMissionControlMissionAuthorizationRecord(sessionId, "mission_authorization_artifact", text);
      setMissionAuthorizationArtifactNote("");
      await handleMissionAuthorization();
    } catch (e) {
      setMissionAuthorizationMd(e instanceof Error ? e.message : "Failed to save mission authorization note");
    } finally {
      setMissionAuthorizationArtifactNoteState("idle");
    }
  }, [sessionId, missionAuthorizationArtifactNote, handleMissionAuthorization]);

  const handleBoundedExecutionParticipation = useCallback(async () => {
    try {
      setBoundedExecutionParticipationLoading(true);
      setBoundedExecutionParticipationMd(null);
      const res = await fetchMissionControlBoundedExecutionParticipation(sessionId, "markdown");
      setBoundedExecutionParticipationMd(res.markdown ?? "No bounded execution participation returned.");
    } catch (e) {
      setBoundedExecutionParticipationMd(
        e instanceof Error ? e.message : "Bounded execution participation failed",
      );
    } finally {
      setBoundedExecutionParticipationLoading(false);
    }
  }, [sessionId]);

  const handleSaveBoundedExecutionParticipationArtifactNote = useCallback(async () => {
    const text = boundedExecutionParticipationArtifactNote.trim();
    if (!text) return;
    try {
      setBoundedExecutionParticipationArtifactNoteState("saving");
      await appendMissionControlBoundedExecutionParticipationRecord(
        sessionId,
        "participation_artifact",
        text,
      );
      setBoundedExecutionParticipationArtifactNote("");
      await handleBoundedExecutionParticipation();
    } catch (e) {
      setBoundedExecutionParticipationMd(
        e instanceof Error ? e.message : "Failed to save bounded execution participation note",
      );
    } finally {
      setBoundedExecutionParticipationArtifactNoteState("idle");
    }
  }, [sessionId, boundedExecutionParticipationArtifactNote, handleBoundedExecutionParticipation]);

  const handleGovernedTaskExecutionCoordination = useCallback(async () => {
    try {
      setGovernedTaskExecutionCoordinationLoading(true);
      setGovernedTaskExecutionCoordinationMd(null);
      const res = await fetchMissionControlGovernedTaskExecutionCoordination(sessionId, "markdown");
      setGovernedTaskExecutionCoordinationMd(
        res.markdown ?? "No governed task execution coordination returned.",
      );
    } catch (e) {
      setGovernedTaskExecutionCoordinationMd(
        e instanceof Error ? e.message : "Governed task execution coordination failed",
      );
    } finally {
      setGovernedTaskExecutionCoordinationLoading(false);
    }
  }, [sessionId]);

  const handleSaveGovernedTaskExecutionCoordinationArtifactNote = useCallback(async () => {
    const text = governedTaskExecutionCoordinationArtifactNote.trim();
    if (!text) return;
    try {
      setGovernedTaskExecutionCoordinationArtifactNoteState("saving");
      await appendMissionControlGovernedTaskExecutionCoordinationRecord(
        sessionId,
        "coordination_artifact",
        text,
      );
      setGovernedTaskExecutionCoordinationArtifactNote("");
      await handleGovernedTaskExecutionCoordination();
    } catch (e) {
      setGovernedTaskExecutionCoordinationMd(
        e instanceof Error ? e.message : "Failed to save governed task execution coordination note",
      );
    } finally {
      setGovernedTaskExecutionCoordinationArtifactNoteState("idle");
    }
  }, [sessionId, governedTaskExecutionCoordinationArtifactNote, handleGovernedTaskExecutionCoordination]);

  const handleGateRoutedPackageOutcomeReview = useCallback(async () => {
    try {
      setGateRoutedPackageOutcomeReviewLoading(true);
      setGateRoutedPackageOutcomeReviewMd(null);
      const res = await fetchMissionControlGateRoutedPackageOutcomeReview(sessionId, "markdown");
      setGateRoutedPackageOutcomeReviewMd(
        res.markdown ?? "No gate-routed package outcome review returned.",
      );
    } catch (e) {
      setGateRoutedPackageOutcomeReviewMd(
        e instanceof Error ? e.message : "Gate-routed package outcome review failed",
      );
    } finally {
      setGateRoutedPackageOutcomeReviewLoading(false);
    }
  }, [sessionId]);

  const handleSaveGateRoutedPackageOutcomeReviewArtifactNote = useCallback(async () => {
    const text = gateRoutedPackageOutcomeReviewArtifactNote.trim();
    if (!text) return;
    try {
      setGateRoutedPackageOutcomeReviewArtifactNoteState("saving");
      await appendMissionControlGateRoutedPackageOutcomeReviewRecord(
        sessionId,
        "gate_review_artifact",
        text,
      );
      setGateRoutedPackageOutcomeReviewArtifactNote("");
      await handleGateRoutedPackageOutcomeReview();
    } catch (e) {
      setGateRoutedPackageOutcomeReviewMd(
        e instanceof Error ? e.message : "Gate review record failed",
      );
    } finally {
      setGateRoutedPackageOutcomeReviewArtifactNoteState("idle");
    }
  }, [sessionId, gateRoutedPackageOutcomeReviewArtifactNote, handleGateRoutedPackageOutcomeReview]);

  const handleGovernedLaneEntryRecommendation = useCallback(async () => {
    try {
      setGovernedLaneEntryRecommendationLoading(true);
      setGovernedLaneEntryRecommendationMd(null);
      const res = await fetchMissionControlGovernedLaneEntryRecommendation(sessionId, "markdown");
      setGovernedLaneEntryRecommendationMd(
        res.markdown ?? "No governed lane entry recommendation returned.",
      );
    } catch (e) {
      setGovernedLaneEntryRecommendationMd(
        e instanceof Error ? e.message : "Governed lane entry recommendation failed",
      );
    } finally {
      setGovernedLaneEntryRecommendationLoading(false);
    }
  }, [sessionId]);

  const handleSaveGovernedLaneEntryRecommendationArtifactNote = useCallback(async () => {
    const text = governedLaneEntryRecommendationArtifactNote.trim();
    if (!text) return;
    try {
      setGovernedLaneEntryRecommendationArtifactNoteState("saving");
      await appendMissionControlGovernedLaneEntryRecommendationRecord(
        sessionId,
        "lane_recommendation_artifact",
        text,
      );
      setGovernedLaneEntryRecommendationArtifactNote("");
      await handleGovernedLaneEntryRecommendation();
    } catch (e) {
      setGovernedLaneEntryRecommendationMd(
        e instanceof Error ? e.message : "Lane recommendation record failed",
      );
    } finally {
      setGovernedLaneEntryRecommendationArtifactNoteState("idle");
    }
  }, [sessionId, governedLaneEntryRecommendationArtifactNote, handleGovernedLaneEntryRecommendation]);

  const handleGovernedLaneReadinessBoard = useCallback(async () => {
    try {
      setGovernedLaneReadinessBoardLoading(true);
      setGovernedLaneReadinessBoardMd(null);
      const res = await fetchMissionControlGovernedLaneReadinessBoard(sessionId, "markdown");
      setGovernedLaneReadinessBoardMd(res.markdown ?? "No governed lane readiness board returned.");
    } catch (e) {
      setGovernedLaneReadinessBoardMd(
        e instanceof Error ? e.message : "Governed lane readiness board failed",
      );
    } finally {
      setGovernedLaneReadinessBoardLoading(false);
    }
  }, [sessionId]);

  const handleSaveGovernedLaneReadinessBoardArtifactNote = useCallback(async () => {
    const text = governedLaneReadinessBoardArtifactNote.trim();
    if (!text) return;
    try {
      setGovernedLaneReadinessBoardArtifactNoteState("saving");
      await appendMissionControlGovernedLaneReadinessBoardRecord(
        sessionId,
        "lane_readiness_board_artifact",
        text,
      );
      setGovernedLaneReadinessBoardArtifactNote("");
      await handleGovernedLaneReadinessBoard();
    } catch (e) {
      setGovernedLaneReadinessBoardMd(
        e instanceof Error ? e.message : "Lane readiness board record failed",
      );
    } finally {
      setGovernedLaneReadinessBoardArtifactNoteState("idle");
    }
  }, [sessionId, governedLaneReadinessBoardArtifactNote, handleGovernedLaneReadinessBoard]);

  const handleHumanLaneAdmissionDecision = useCallback(async () => {
    try {
      setHumanLaneAdmissionDecisionLoading(true);
      setHumanLaneAdmissionDecisionMd(null);
      const res = await fetchMissionControlHumanLaneAdmissionDecision(sessionId, "markdown");
      setHumanLaneAdmissionDecisionMd(res.markdown ?? "No human lane admission decision returned.");
    } catch (e) {
      setHumanLaneAdmissionDecisionMd(
        e instanceof Error ? e.message : "Human lane admission decision failed",
      );
    } finally {
      setHumanLaneAdmissionDecisionLoading(false);
    }
  }, [sessionId]);

  const handleSaveHumanLaneAdmissionDecisionArtifactNote = useCallback(async () => {
    const text = humanLaneAdmissionDecisionArtifactNote.trim();
    if (!text) return;
    try {
      setHumanLaneAdmissionDecisionArtifactNoteState("saving");
      await appendMissionControlHumanLaneAdmissionDecisionRecord(
        sessionId,
        "lane_admission_decision_record",
        text.startsWith("admit:") || text.startsWith("hold:") || text.startsWith("reject:")
          ? text
          : `admit: ${text}`,
      );
      setHumanLaneAdmissionDecisionArtifactNote("");
      await handleHumanLaneAdmissionDecision();
    } catch (e) {
      setHumanLaneAdmissionDecisionMd(
        e instanceof Error ? e.message : "Lane admission decision record failed",
      );
    } finally {
      setHumanLaneAdmissionDecisionArtifactNoteState("idle");
    }
  }, [sessionId, humanLaneAdmissionDecisionArtifactNote, handleHumanLaneAdmissionDecision]);

  const handleGateRoutedLaneEntryHandoff = useCallback(async () => {
    try {
      setGateRoutedLaneEntryHandoffLoading(true);
      setGateRoutedLaneEntryHandoffMd(null);
      const res = await fetchMissionControlGateRoutedLaneEntryHandoff(sessionId, "markdown");
      setGateRoutedLaneEntryHandoffMd(res.markdown ?? "No gate-routed lane entry handoff returned.");
    } catch (e) {
      setGateRoutedLaneEntryHandoffMd(
        e instanceof Error ? e.message : "Gate-routed lane entry handoff failed",
      );
    } finally {
      setGateRoutedLaneEntryHandoffLoading(false);
    }
  }, [sessionId]);

  const handleSaveGateRoutedLaneEntryHandoffArtifactNote = useCallback(async () => {
    const text = gateRoutedLaneEntryHandoffArtifactNote.trim();
    if (!text) return;
    try {
      setGateRoutedLaneEntryHandoffArtifactNoteState("saving");
      await appendMissionControlGateRoutedLaneEntryHandoffRecord(
        sessionId,
        "gate_handoff_artifact",
        text,
      );
      setGateRoutedLaneEntryHandoffArtifactNote("");
      await handleGateRoutedLaneEntryHandoff();
    } catch (e) {
      setGateRoutedLaneEntryHandoffMd(
        e instanceof Error ? e.message : "Gate handoff record failed",
      );
    } finally {
      setGateRoutedLaneEntryHandoffArtifactNoteState("idle");
    }
  }, [sessionId, gateRoutedLaneEntryHandoffArtifactNote, handleGateRoutedLaneEntryHandoff]);

  const handleFrozenGateIntakePreview = useCallback(async () => {
    try {
      setFrozenGateIntakePreviewLoading(true);
      setFrozenGateIntakePreviewMd(null);
      const res = await fetchMissionControlFrozenGateIntakePreview(sessionId, "markdown");
      setFrozenGateIntakePreviewMd(res.markdown ?? "No frozen gate intake preview returned.");
    } catch (e) {
      setFrozenGateIntakePreviewMd(
        e instanceof Error ? e.message : "Frozen gate intake preview failed",
      );
    } finally {
      setFrozenGateIntakePreviewLoading(false);
    }
  }, [sessionId]);

  const handleSaveFrozenGateIntakePreviewArtifactNote = useCallback(async () => {
    const text = frozenGateIntakePreviewArtifactNote.trim();
    if (!text) return;
    try {
      setFrozenGateIntakePreviewArtifactNoteState("saving");
      await appendMissionControlFrozenGateIntakePreviewRecord(
        sessionId,
        "intake_preview_artifact",
        text,
      );
      setFrozenGateIntakePreviewArtifactNote("");
      await handleFrozenGateIntakePreview();
    } catch (e) {
      setFrozenGateIntakePreviewMd(
        e instanceof Error ? e.message : "Gate intake preview record failed",
      );
    } finally {
      setFrozenGateIntakePreviewArtifactNoteState("idle");
    }
  }, [sessionId, frozenGateIntakePreviewArtifactNote, handleFrozenGateIntakePreview]);

  const handleFrozenGateExecutionRequestAdapter = useCallback(async () => {
    try {
      setFrozenGateExecutionRequestAdapterLoading(true);
      setFrozenGateExecutionRequestAdapterMd(null);
      const res = await fetchMissionControlFrozenGateExecutionRequestAdapter(sessionId, "markdown");
      setFrozenGateExecutionRequestAdapterMd(
        res.markdown ?? "No frozen gate execution request adapter returned.",
      );
    } catch (e) {
      setFrozenGateExecutionRequestAdapterMd(
        e instanceof Error ? e.message : "Frozen gate execution request adapter failed",
      );
    } finally {
      setFrozenGateExecutionRequestAdapterLoading(false);
    }
  }, [sessionId]);

  const handleSaveFrozenGateExecutionRequestAdapterArtifactNote = useCallback(async () => {
    const text = frozenGateExecutionRequestAdapterArtifactNote.trim();
    if (!text) return;
    try {
      setFrozenGateExecutionRequestAdapterArtifactNoteState("saving");
      await appendMissionControlFrozenGateExecutionRequestAdapterRecord(
        sessionId,
        "execution_request_artifact",
        text,
      );
      setFrozenGateExecutionRequestAdapterArtifactNote("");
      await handleFrozenGateExecutionRequestAdapter();
    } catch (e) {
      setFrozenGateExecutionRequestAdapterMd(
        e instanceof Error ? e.message : "Gate execution request record failed",
      );
    } finally {
      setFrozenGateExecutionRequestAdapterArtifactNoteState("idle");
    }
  }, [
    sessionId,
    frozenGateExecutionRequestAdapterArtifactNote,
    handleFrozenGateExecutionRequestAdapter,
  ]);

  const handleGovernedChatCommandInvocationFromHandoff = useCallback(async () => {
    try {
      setGovernedChatCommandInvocationFromHandoffLoading(true);
      setGovernedChatCommandInvocationFromHandoffMd(null);
      const res = await fetchMissionControlGovernedChatCommandInvocationFromHandoff(sessionId, "markdown");
      setGovernedChatCommandInvocationFromHandoffMd(
        res.markdown ?? "No governed chat command invocation from handoff returned.",
      );
    } catch (e) {
      setGovernedChatCommandInvocationFromHandoffMd(
        e instanceof Error ? e.message : "Governed chat command invocation from handoff failed",
      );
    } finally {
      setGovernedChatCommandInvocationFromHandoffLoading(false);
    }
  }, [sessionId]);

  const handleSaveGovernedChatCommandInvocationFromHandoffArtifactNote = useCallback(async () => {
    const text = governedChatCommandInvocationFromHandoffArtifactNote.trim();
    if (!text) return;
    try {
      setGovernedChatCommandInvocationFromHandoffArtifactNoteState("saving");
      await appendMissionControlGovernedChatCommandInvocationFromHandoffRecord(
        sessionId,
        "invocation_artifact",
        text,
      );
      setGovernedChatCommandInvocationFromHandoffArtifactNote("");
      await handleGovernedChatCommandInvocationFromHandoff();
    } catch (e) {
      setGovernedChatCommandInvocationFromHandoffMd(
        e instanceof Error ? e.message : "Handoff invocation record failed",
      );
    } finally {
      setGovernedChatCommandInvocationFromHandoffArtifactNoteState("idle");
    }
  }, [
    sessionId,
    governedChatCommandInvocationFromHandoffArtifactNote,
    handleGovernedChatCommandInvocationFromHandoff,
  ]);

  const handleInvokeGovernedChatCommandFromHandoff = useCallback(async () => {
    try {
      setGovernedChatCommandInvocationInvokeState("invoking");
      const res = await invokeMissionControlGovernedChatCommandFromHandoff(sessionId);
      setGovernedChatCommandInvocationFromHandoffMd(
        `Invoked through chat governance (route: ${res.route_id ?? "unknown"}).\n\n${res.reply ?? ""}`,
      );
    } catch (e) {
      setGovernedChatCommandInvocationFromHandoffMd(
        e instanceof Error ? e.message : "Handoff command invocation failed",
      );
    } finally {
      setGovernedChatCommandInvocationInvokeState("idle");
    }
  }, [sessionId]);

  const handleEndToEndRepoDevelopmentPilotHarness = useCallback(async () => {
    try {
      setEndToEndRepoDevelopmentPilotHarnessLoading(true);
      setEndToEndRepoDevelopmentPilotHarnessMd(null);
      const res = await fetchMissionControlEndToEndRepoDevelopmentPilotHarness(sessionId, "markdown");
      setEndToEndRepoDevelopmentPilotHarnessMd(
        res.markdown ?? "No end-to-end repo development pilot harness returned.",
      );
    } catch (e) {
      setEndToEndRepoDevelopmentPilotHarnessMd(
        e instanceof Error ? e.message : "End-to-end pilot harness failed",
      );
    } finally {
      setEndToEndRepoDevelopmentPilotHarnessLoading(false);
    }
  }, [sessionId]);

  const handleSaveEndToEndRepoDevelopmentPilotHarnessArtifactNote = useCallback(async () => {
    const text = endToEndRepoDevelopmentPilotHarnessArtifactNote.trim();
    if (!text) return;
    try {
      setEndToEndRepoDevelopmentPilotHarnessArtifactNoteState("saving");
      await appendMissionControlEndToEndRepoDevelopmentPilotHarnessRecord(
        sessionId,
        "pilot_artifact",
        text,
      );
      setEndToEndRepoDevelopmentPilotHarnessArtifactNote("");
      await handleEndToEndRepoDevelopmentPilotHarness();
    } catch (e) {
      setEndToEndRepoDevelopmentPilotHarnessMd(
        e instanceof Error ? e.message : "Pilot harness record failed",
      );
    } finally {
      setEndToEndRepoDevelopmentPilotHarnessArtifactNoteState("idle");
    }
  }, [
    sessionId,
    endToEndRepoDevelopmentPilotHarnessArtifactNote,
    handleEndToEndRepoDevelopmentPilotHarness,
  ]);

  const handleRunEndToEndRepoDevelopmentPilot = useCallback(async () => {
    try {
      setEndToEndPilotRunState("running");
      const res = await runMissionControlEndToEndRepoDevelopmentPilotHarness(sessionId);
      const report = res.pilot_report ?? {};
      setEndToEndRepoDevelopmentPilotHarnessMd(
        `Pilot run ${res.ok ? "complete" : "partial"} (audit: ${res.audit_id ?? "unknown"}).\n` +
          `Stages completed: ${(res.stages_completed ?? []).join(", ") || "none"}.\n` +
          `Evidence bundle ok: ${String(report.evidence_bundle_ok ?? false)}.\n` +
          `Railway coupling: ${String(report.railway_coupling_detected ?? false)}.\n\n` +
          (res.detail ?? ""),
      );
    } catch (e) {
      setEndToEndRepoDevelopmentPilotHarnessMd(
        e instanceof Error ? e.message : "Pilot run failed",
      );
    } finally {
      setEndToEndPilotRunState("idle");
    }
  }, [sessionId]);

  const handleRepoPilotReadinessDashboard = useCallback(async () => {
    try {
      setRepoPilotReadinessDashboardLoading(true);
      setRepoPilotReadinessDashboardMd(null);
      const res = await fetchMissionControlRepoPilotReadinessDashboard(sessionId, "markdown");
      setRepoPilotReadinessDashboardMd(res.markdown ?? "No repo pilot readiness dashboard returned.");
    } catch (e) {
      setRepoPilotReadinessDashboardMd(
        e instanceof Error ? e.message : "Repo pilot readiness dashboard failed",
      );
    } finally {
      setRepoPilotReadinessDashboardLoading(false);
    }
  }, [sessionId]);

  const handleSaveRepoPilotReadinessDashboardArtifactNote = useCallback(async () => {
    const text = repoPilotReadinessDashboardArtifactNote.trim();
    if (!text) return;
    try {
      setRepoPilotReadinessDashboardArtifactNoteState("saving");
      await appendMissionControlRepoPilotReadinessDashboardRecord(sessionId, "readiness_artifact", text);
      setRepoPilotReadinessDashboardArtifactNote("");
      await handleRepoPilotReadinessDashboard();
    } catch (e) {
      setRepoPilotReadinessDashboardMd(
        e instanceof Error ? e.message : "Readiness dashboard record failed",
      );
    } finally {
      setRepoPilotReadinessDashboardArtifactNoteState("idle");
    }
  }, [sessionId, repoPilotReadinessDashboardArtifactNote, handleRepoPilotReadinessDashboard]);

  const health = snapshot?.execution_health ?? {};
  const lanes = snapshot?.lanes ?? {};
  const sd = lanes.software_delivery ?? {};
  const railway = lanes.railway_orchestration ?? {};
  const incidents = snapshot?.incident_linkage ?? lanes.incident_command ?? {};
  const agents = snapshot?.agent_collaboration_summary ?? lanes.multi_agent_collaboration ?? {};
  const governance = snapshot?.rollout_visibility ?? lanes.production_governance ?? {};
  const sessionScopedActivity =
    Boolean(sd.ok) ||
    Boolean(agents.ok) ||
    Boolean(snapshot?.plan_id) ||
    (snapshot?.unified_timeline?.length ?? 0) > 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <section style={mcPanelSectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
          <div>
            <h2 style={{ margin: "0 0 6px", fontSize: 20, fontWeight: 600 }}>Cross-lane operations</h2>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
              Read-only operational truth scoped to your active chat session. Timeline entries link to lane detail
              below — no execute, deploy, restart, or approval actions on this surface.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
            <ReadOnlyBadge />
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void load()}
              disabled={!hydrated || loadState === "loading"}
            >
              Refresh
            </button>
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void handleExport("json")}
              disabled={!hydrated || exportState === "loading" || loadState !== "loaded"}
              title="Download read-only JSON evidence bundle for this session"
            >
              Export JSON
            </button>
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void handleExport("markdown")}
              disabled={!hydrated || exportState === "loading" || loadState !== "loaded"}
              title="Download read-only Markdown evidence bundle for reviews and compliance"
            >
              Export Markdown
            </button>
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void handleShowOperationalMemory()}
              disabled={!hydrated || memoryLoading || loadState !== "loaded"}
              title="Read-only knowledge graph — correlates missions, jobs, approvals, incidents, replay, and rerun plans"
            >
              {memoryLoading ? "Building graph…" : "Operational memory"}
            </button>
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() => void handleShowCrossSessionMemory()}
              disabled={!hydrated || crossSessionLoading || loadState !== "loaded"}
              title="Durable organizational memory across sessions — read-only, no adaptation"
            >
              {crossSessionLoading ? "Stitching…" : "Cross-session memory"}
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap", alignItems: "center" }}>
          <input
            type="text"
            value={knowledgeQuery}
            onChange={(e) => setKnowledgeQuery(e.target.value)}
            placeholder="Semantic search: blockers, incidents, PRs…"
            disabled={!hydrated || knowledgeLoading}
            style={{
              flex: "1 1 200px",
              minWidth: 180,
              padding: "6px 10px",
              fontSize: 13,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panel,
              color: mcColors.text,
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleKnowledgeSearch()}
            disabled={!hydrated || knowledgeLoading || loadState !== "loaded"}
            title="FIX 141 mission knowledge spaces — recommendation-only, no autonomous action"
          >
            {knowledgeLoading ? "Searching…" : "Semantic search"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleOperatorGuidance()}
            disabled={!hydrated || guidanceLoading || loadState !== "loaded"}
            title="FIX 142 contextual guidance — recommendations only, operator-approved actions"
          >
            {guidanceLoading ? "Guiding…" : "Operator guidance"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceInsights()}
            disabled={!hydrated || govInsightsLoading || loadState !== "loaded"}
            title="FIX 143 meta-governance insights — observability only, no policy tuning"
          >
            {govInsightsLoading ? "Analyzing…" : "Governance insights"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceSimulation()}
            disabled={!hydrated || govSimLoading || loadState !== "loaded"}
            title="FIX 144 governance sandbox — simulate policy changes without applying them"
          >
            {govSimLoading ? "Simulating…" : "Governance simulation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleMissionStrategy()}
            disabled={!hydrated || strategyLoading || loadState !== "loaded"}
            title="FIX 145 strategic reasoning — recommendations only, no autonomous planning"
          >
            {strategyLoading ? "Reasoning…" : "Mission strategy"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleMissionOrchestration()}
            disabled={!hydrated || orchestrationLoading || loadState !== "loaded"}
            title="FIX 146 orchestration coordination — recommendations only, no autonomous sequencing"
          >
            {orchestrationLoading ? "Coordinating…" : "Mission orchestration"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleMissionReadinessReview()}
            disabled={!hydrated || readinessLoading || loadState !== "loaded"}
            title="FIX 147 readiness review board — advisory go/no-go/hold, human review required"
          >
            {readinessLoading ? "Reviewing…" : "Readiness review"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceDeliberation()}
            disabled={!hydrated || deliberationLoading || loadState !== "loaded"}
            title="FIX 148 deliberation workspace — institutional memory only, no approval automation"
          >
            {deliberationLoading ? "Deliberating…" : "Governance deliberation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceCollaboration()}
            disabled={!hydrated || collaborationLoading || loadState !== "loaded"}
            title="FIX 149 multi-operator collaboration — institutional continuity, no delegated authority"
          >
            {collaborationLoading ? "Collaborating…" : "Governance collaboration"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceRoleArchitecture()}
            disabled={!hydrated || roleArchLoading || loadState !== "loaded"}
            title="FIX 150 role architecture + trust boundaries — read-only institutional topology"
          >
            {roleArchLoading ? "Mapping…" : "Role architecture"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceDoctrine()}
            disabled={!hydrated || doctrineLoading || loadState !== "loaded"}
            title="FIX 151 governance doctrine — amendment proposals only, no autonomous policy mutation"
          >
            {doctrineLoading ? "Chartering…" : "Governance doctrine"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernancePolicyInterpretation()}
            disabled={!hydrated || interpretationLoading || loadState !== "loaded"}
            title="FIX 152 policy interpretation — assistance only, no autonomous enforcement or rulings"
          >
            {interpretationLoading ? "Interpreting…" : "Policy interpretation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceCoherence()}
            disabled={!hydrated || coherenceLoading || loadState !== "loaded"}
            title="FIX 153 governance coherence — recommendation-only, no autonomous correction or override"
          >
            {coherenceLoading ? "Analyzing…" : "Governance coherence"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceResilience()}
            disabled={!hydrated || resilienceLoading || loadState !== "loaded"}
            title="FIX 154 governance resilience — simulation-only, no autonomous adaptation or correction"
          >
            {resilienceLoading ? "Simulating…" : "Governance resilience"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernanceEvolution()}
            disabled={!hydrated || evolutionLoading || loadState !== "loaded"}
            title="FIX 155 governance evolution — recommendation-only, no autonomous evolution or doctrine migration"
          >
            {evolutionLoading ? "Tracing…" : "Governance evolution"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleInstitutionalIdentity()}
            disabled={!hydrated || identityLoading || loadState !== "loaded"}
            title="FIX 156 institutional identity — recommendation-only, no autonomous redirection or constitutional rewriting"
          >
            {identityLoading ? "Preserving…" : "Institutional identity"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleInstitutionalExternalRelations()}
            disabled={!hydrated || externalRelationsLoading || loadState !== "loaded"}
            title="FIX 157 institutional external relations — recommendation-only, no autonomous negotiation or sovereignty delegation"
          >
            {externalRelationsLoading ? "Mapping…" : "External relations"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleInstitutionalExistentialRisk()}
            disabled={!hydrated || existentialRiskLoading || loadState !== "loaded"}
            title="FIX 158 institutional existential risk — recommendation-only, no autonomous self-preservation or constitutional override"
          >
            {existentialRiskLoading ? "Analyzing…" : "Existential risk"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleConstitutionalEthics()}
            disabled={!hydrated || constitutionalEthicsLoading || loadState !== "loaded"}
            title="FIX 159 constitutional ethics — recommendation-only, no autonomous moral authority or value enforcement"
          >
            {constitutionalEthicsLoading ? "Reasoning…" : "Constitutional ethics"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleConstitutionalAudit()}
            disabled={!hydrated || constitutionalAuditLoading || loadState !== "loaded"}
            title="FIX 160 constitutional audit — recommendation-only, no autonomous disclosure or public communication authority"
          >
            {constitutionalAuditLoading ? "Auditing…" : "Constitutional audit"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleConstitutionalLegitimacy()}
            disabled={!hydrated || constitutionalLegitimacyLoading || loadState !== "loaded"}
            title="FIX 161 constitutional legitimacy — recommendation-only, no autonomous legitimacy enforcement or public trust manipulation"
          >
            {constitutionalLegitimacyLoading ? "Evaluating…" : "Constitutional legitimacy"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleConstitutionalPluralism()}
            disabled={!hydrated || constitutionalPluralismLoading || loadState !== "loaded"}
            title="FIX 162 constitutional pluralism — recommendation-only, no authoritative worldview selection or autonomous arbitration"
          >
            {constitutionalPluralismLoading ? "Mapping…" : "Constitutional pluralism"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleConstitutionalSynthesis()}
            disabled={!hydrated || constitutionalSynthesisLoading || loadState !== "loaded"}
            title="FIX 163 constitutional synthesis — recommendation-only, no autonomous constitutional decisions or authority"
          >
            {constitutionalSynthesisLoading ? "Synthesizing…" : "Constitutional synthesis"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleMissionPlanning()}
            disabled={!hydrated || missionPlanningLoading || loadState !== "loaded"}
            title="FIX 164 mission planning — recommendation-only, no execution authority or autonomous path selection"
          >
            {missionPlanningLoading ? "Planning…" : "Mission planning"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handlePlanningDeliberation()}
            disabled={!hydrated || planningDeliberationLoading || loadState !== "loaded"}
            title="FIX 165 planning deliberation — bounded agent analysis only, no execution authority"
          >
            {planningDeliberationLoading ? "Deliberating…" : "Planning deliberation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleHumanDecisionBoard()}
            disabled={!hydrated || humanDecisionBoardLoading || loadState !== "loaded"}
            title="FIX 166 human decision board — human choice only, no autonomous selection or execution"
          >
            {humanDecisionBoardLoading ? "Recording…" : "Human decision board"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleExecutionHandoff()}
            disabled={!hydrated || executionHandoffLoading || loadState !== "loaded"}
            title="FIX 167 execution handoff — coordinates to governed lanes, no execution authority"
          >
            {executionHandoffLoading ? "Coordinating…" : "Execution handoff"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleDeliveryWorkPackages()}
            disabled={!hydrated || deliveryWorkPackagesLoading || loadState !== "loaded"}
            title="FIX 168 delivery work packages — scopes bounded agents, no execution authority"
          >
            {deliveryWorkPackagesLoading ? "Scoping…" : "Delivery work packages"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleLaneAdmissionReadiness()}
            disabled={!hydrated || laneAdmissionLoading || loadState !== "loaded"}
            title="FIX 169 lane admission readiness — evaluates eligibility, no autonomous lane entry"
          >
            {laneAdmissionLoading ? "Evaluating…" : "Lane admission readiness"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleMissionAuthorization()}
            disabled={!hydrated || missionAuthorizationLoading || loadState !== "loaded"}
            title="FIX 170 mission authorization — bounded Tier 1–2 envelope, existing gates enforced"
          >
            {missionAuthorizationLoading ? "Authorizing…" : "Mission authorization"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleBoundedExecutionParticipation()}
            disabled={!hydrated || boundedExecutionParticipationLoading || loadState !== "loaded"}
            title="FIX 171 bounded execution participation — agents inside authorized envelope, gates enforced"
          >
            {boundedExecutionParticipationLoading ? "Participating…" : "Bounded execution participation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernedTaskExecutionCoordination()}
            disabled={!hydrated || governedTaskExecutionCoordinationLoading || loadState !== "loaded"}
            title="FIX 172 governed task execution coordination — coordinate without executing, gates decide"
          >
            {governedTaskExecutionCoordinationLoading ? "Coordinating…" : "Execution coordination"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGateRoutedPackageOutcomeReview()}
            disabled={!hydrated || gateRoutedPackageOutcomeReviewLoading || loadState !== "loaded"}
            title="FIX 173 gate-routed package outcome review — classify outcomes and map to frozen gates"
          >
            {gateRoutedPackageOutcomeReviewLoading ? "Reviewing…" : "Gate outcome review"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernedLaneEntryRecommendation()}
            disabled={!hydrated || governedLaneEntryRecommendationLoading || loadState !== "loaded"}
            title="FIX 174 governed lane entry recommendation — composes FIX 169 + FIX 173, recommendation ≠ admission"
          >
            {governedLaneEntryRecommendationLoading ? "Recommending…" : "Lane entry recommendation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernedLaneReadinessBoard()}
            disabled={!hydrated || governedLaneReadinessBoardLoading || loadState !== "loaded"}
            title="FIX 175 governed lane readiness board — consolidates FIX 174 for human review, board ≠ admission decision"
          >
            {governedLaneReadinessBoardLoading ? "Boarding…" : "Lane readiness board"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleHumanLaneAdmissionDecision()}
            disabled={!hydrated || humanLaneAdmissionDecisionLoading || loadState !== "loaded"}
            title="FIX 176 human lane admission decision — admit, hold, or reject after board review"
          >
            {humanLaneAdmissionDecisionLoading ? "Deciding…" : "Lane admission decision"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGateRoutedLaneEntryHandoff()}
            disabled={!hydrated || gateRoutedLaneEntryHandoffLoading || loadState !== "loaded"}
            title="FIX 177 gate-routed lane entry handoff — packages FIX 176 decision for frozen gate validation"
          >
            {gateRoutedLaneEntryHandoffLoading ? "Handing off…" : "Gate handoff"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleFrozenGateIntakePreview()}
            disabled={!hydrated || frozenGateIntakePreviewLoading || loadState !== "loaded"}
            title="FIX 178 frozen gate intake preview — previews FIX 177 handoff without gate execution"
          >
            {frozenGateIntakePreviewLoading ? "Previewing…" : "Gate intake preview"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleFrozenGateExecutionRequestAdapter()}
            disabled={!hydrated || frozenGateExecutionRequestAdapterLoading || loadState !== "loaded"}
            title="FIX 179 execution request adapter — maps intake preview to frozen command without execution"
          >
            {frozenGateExecutionRequestAdapterLoading ? "Adapting…" : "Execution request"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleGovernedChatCommandInvocationFromHandoff()}
            disabled={!hydrated || governedChatCommandInvocationFromHandoffLoading || loadState !== "loaded"}
            title="FIX 180 governed chat command invocation — builds frozen command from FIX 179 request"
          >
            {governedChatCommandInvocationFromHandoffLoading ? "Preparing…" : "Handoff invocation"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleInvokeGovernedChatCommandFromHandoff()}
            disabled={
              !hydrated ||
              governedChatCommandInvocationInvokeState === "invoking" ||
              loadState !== "loaded"
            }
            title="Explicitly invoke handoff command through resolve_chat_turn governance route"
          >
            {governedChatCommandInvocationInvokeState === "invoking"
              ? "Invoking…"
              : "Invoke handoff command"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleEndToEndRepoDevelopmentPilotHarness()}
            disabled={!hydrated || endToEndRepoDevelopmentPilotHarnessLoading || loadState !== "loaded"}
            title="FIX 181 end-to-end repo development pilot harness — stage matrix and pilot packet"
          >
            {endToEndRepoDevelopmentPilotHarnessLoading ? "Loading…" : "Pilot harness"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleRunEndToEndRepoDevelopmentPilot()}
            disabled={!hydrated || endToEndPilotRunState === "running" || loadState !== "loaded"}
            title="Explicitly run bounded pilot through resolve_chat_turn governance route"
          >
            {endToEndPilotRunState === "running" ? "Running…" : "Run pilot"}
          </button>
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleRepoPilotReadinessDashboard()}
            disabled={!hydrated || repoPilotReadinessDashboardLoading || loadState !== "loaded"}
            title="FIX 182 repo pilot readiness dashboard — preflight before running pilot"
          >
            {repoPilotReadinessDashboardLoading ? "Checking…" : "Pilot readiness"}
          </button>
        </div>

        {exportMessage ? (
          <div style={{ margin: "10px 0 0", fontSize: 12, color: mcColors.textMuted }}>
            <span>{exportMessage}</span>
            {onOpenReplayDeepLink ? (
              <ReplayDeepLinkButton
                label="View mission in replay →"
                onClick={() => onOpenReplayDeepLink({ linkRef: "mission:start" })}
              />
            ) : null}
          </div>
        ) : null}

        {strategyMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission strategy layer (FIX 145)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Strategic operational reasoning — themes, drift, bottlenecks, and risk concentration. No autonomous planning.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {strategyMd}
            </pre>
          </div>
        ) : null}

        {orchestrationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission orchestration layer (FIX 146)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Cross-lane coordination — dependency graph, readiness, sequencing, and lane health. No autonomous execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {orchestrationMd}
            </pre>
          </div>
        ) : null}

        {readinessMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission readiness review board (FIX 147)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Advisory go/no-go/hold — blockers, approvals, evidence gaps, and rollback posture. Human review required.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {readinessMd}
            </pre>
          </div>
        ) : null}

        {deliberationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance deliberation workspace (FIX 148)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Institutional governance memory — notes, timeline, checklist. Does not approve or mutate policy.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {deliberationMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={deliberationNote}
            onChange={(e) => setDeliberationNote(e.target.value)}
            placeholder="Deliberation operator note (institutional memory only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveDeliberationNote()}
            disabled={!hydrated || deliberationNoteState === "saving" || !deliberationNote.trim()}
            title="Persist operator note to deliberation store — no approval execution"
          >
            {deliberationNoteState === "saving" ? "Saving…" : "Save note"}
          </button>
        </div>

        {collaborationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Multi-operator governance collaboration (FIX 149)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Named reviewers, quorum discussion, handoffs — institutional continuity without autonomous decisions.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {collaborationMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <input
            value={collaborationReviewer}
            onChange={(e) => setCollaborationReviewer(e.target.value)}
            placeholder="Reviewer name"
            style={{
              flex: "0 1 140px",
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
            }}
          />
          <textarea
            value={collaborationAck}
            onChange={(e) => setCollaborationAck(e.target.value)}
            placeholder="Reviewer acknowledgment (collaboration memory only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveCollaborationAck()}
            disabled={!hydrated || collaborationAckState === "saving" || !collaborationAck.trim()}
            title="Persist reviewer acknowledgment — no quorum approval automation"
          >
            {collaborationAckState === "saving" ? "Saving…" : "Save acknowledgment"}
          </button>
        </div>

        {roleArchMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance role architecture (FIX 150)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Role taxonomy, trust zones, escalation paths, and separation-of-duty — topology only, no role elevation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {roleArchMd}
            </pre>
          </div>
        ) : null}

        {doctrineMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance doctrine + policy charter (FIX 151)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional principles, precedents, and amendment proposals — never self-modifying governance.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {doctrineMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={doctrineAmendment}
            onChange={(e) => setDoctrineAmendment(e.target.value)}
            placeholder="Policy amendment proposal (executable: false, requires human ratification)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveDoctrineAmendment()}
            disabled={!hydrated || doctrineAmendmentState === "saving" || !doctrineAmendment.trim()}
            title="Persist amendment proposal to doctrine store — does not mutate live policy"
          >
            {doctrineAmendmentState === "saving" ? "Proposing…" : "Propose amendment"}
          </button>
        </div>

        {interpretationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance policy interpretation (FIX 152)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional reasoning assistance — interpretation only, never enforcement or automatic rulings.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {interpretationMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={interpretationNote}
            onChange={(e) => setInterpretationNote(e.target.value)}
            placeholder="Doctrine interpretation record (executable: false, advisory only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveInterpretationNote()}
            disabled={!hydrated || interpretationNoteState === "saving" || !interpretationNote.trim()}
            title="Persist interpretation record — does not enforce doctrine or issue rulings"
          >
            {interpretationNoteState === "saving" ? "Recording…" : "Record interpretation"}
          </button>
        </div>

        {coherenceMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance coherence + constitutional integrity (FIX 153)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Institutional coherence intelligence — recommendation-only, never self-healing or override authority.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {coherenceMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={coherenceObservation}
            onChange={(e) => setCoherenceObservation(e.target.value)}
            placeholder="Coherence observation (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveCoherenceObservation()}
            disabled={!hydrated || coherenceObservationState === "saving" || !coherenceObservation.trim()}
            title="Persist coherence observation — does not correct governance or override doctrine"
          >
            {coherenceObservationState === "saving" ? "Recording…" : "Record observation"}
          </button>
        </div>

        {resilienceMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance resilience + stress simulation (FIX 154)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Institutional resilience cognition — simulation-only, never adaptive correction or override authority.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {resilienceMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={resilienceObservation}
            onChange={(e) => setResilienceObservation(e.target.value)}
            placeholder="Resilience observation (executable: false, simulation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveResilienceObservation()}
            disabled={!hydrated || resilienceObservationState === "saving" || !resilienceObservation.trim()}
            title="Persist resilience observation — does not adapt governance or trigger self-healing"
          >
            {resilienceObservationState === "saving" ? "Recording…" : "Record observation"}
          </button>
        </div>

        {evolutionMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance evolution + institutional continuity (FIX 155)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Institutional temporal cognition — recommendation-only, never autonomous evolution or doctrine migration.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {evolutionMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={evolutionContinuity}
            onChange={(e) => setEvolutionContinuity(e.target.value)}
            placeholder="Continuity observation (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveEvolutionContinuity()}
            disabled={!hydrated || evolutionContinuityState === "saving" || !evolutionContinuity.trim()}
            title="Persist continuity observation — does not migrate doctrine or evolve governance autonomously"
          >
            {evolutionContinuityState === "saving" ? "Recording…" : "Record continuity"}
          </button>
        </div>

        {identityMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Institutional identity + constitutional intent (FIX 156)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Institutional identity cognition — recommendation-only, never autonomous redirection or mission authorship.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {identityMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={identityIntent}
            onChange={(e) => setIdentityIntent(e.target.value)}
            placeholder="Constitutional intent record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveIdentityIntent()}
            disabled={!hydrated || identityIntentState === "saving" || !identityIntent.trim()}
            title="Persist constitutional intent — does not rewrite governance or redirect institution autonomously"
          >
            {identityIntentState === "saving" ? "Recording…" : "Record intent"}
          </button>
        </div>

        {externalRelationsMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Institutional external relations + constitutional boundary (FIX 157)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional external-relations cognition — recommendation-only, never autonomous negotiation or sovereignty delegation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {externalRelationsMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={externalBoundary}
            onChange={(e) => setExternalBoundary(e.target.value)}
            placeholder="Constitutional boundary record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveExternalBoundary()}
            disabled={!hydrated || externalBoundaryState === "saving" || !externalBoundary.trim()}
            title="Persist boundary definition — does not negotiate externally or delegate sovereignty autonomously"
          >
            {externalBoundaryState === "saving" ? "Recording…" : "Record boundary"}
          </button>
        </div>

        {existentialRiskMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Institutional existential risk + continuity preservation (FIX 158)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Existential continuity cognition — recommendation-only, never autonomous self-preservation or constitutional override.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {existentialRiskMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={preservationNote}
            onChange={(e) => setPreservationNote(e.target.value)}
            placeholder="Continuity preservation record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSavePreservationNote()}
            disabled={!hydrated || preservationNoteState === "saving" || !preservationNote.trim()}
            title="Persist preservation recommendation — does not enforce continuity or override constitution autonomously"
          >
            {preservationNoteState === "saving" ? "Recording…" : "Record preservation"}
          </button>
        </div>

        {constitutionalEthicsMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Constitutional ethics + institutional moral reasoning (FIX 159)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional ethical cognition — recommendation-only, never autonomous moral authority or value enforcement.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {constitutionalEthicsMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={ethicsValueNote}
            onChange={(e) => setEthicsValueNote(e.target.value)}
            placeholder="Value preservation record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveEthicsValueNote()}
            disabled={!hydrated || ethicsValueNoteState === "saving" || !ethicsValueNote.trim()}
            title="Persist value preservation note — does not enforce values or grant moral authority autonomously"
          >
            {ethicsValueNoteState === "saving" ? "Recording…" : "Record value"}
          </button>
        </div>

        {constitutionalAuditMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Constitutional audit + public accountability (FIX 160)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional accountability cognition — recommendation-only, never autonomous disclosure or governance enforcement.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {constitutionalAuditMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={auditAccountabilityNote}
            onChange={(e) => setAuditAccountabilityNote(e.target.value)}
            placeholder="Accountability record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveAuditAccountabilityNote()}
            disabled={!hydrated || auditAccountabilityNoteState === "saving" || !auditAccountabilityNote.trim()}
            title="Persist accountability record — does not disclose publicly or enforce governance autonomously"
          >
            {auditAccountabilityNoteState === "saving" ? "Recording…" : "Record accountability"}
          </button>
        </div>

        {constitutionalLegitimacyMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Constitutional legitimacy + institutional trust (FIX 161)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional legitimacy cognition — recommendation-only, never autonomous legitimacy enforcement or trust manipulation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {constitutionalLegitimacyMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={legitimacyTrustNote}
            onChange={(e) => setLegitimacyTrustNote(e.target.value)}
            placeholder="Trust continuity record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveLegitimacyTrustNote()}
            disabled={!hydrated || legitimacyTrustNoteState === "saving" || !legitimacyTrustNote.trim()}
            title="Persist trust continuity note — does not manipulate public trust or enforce legitimacy autonomously"
          >
            {legitimacyTrustNoteState === "saving" ? "Recording…" : "Record trust"}
          </button>
        </div>

        {constitutionalPluralismMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Constitutional pluralism + governance perspective (FIX 162)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Constitutional pluralism cognition — recommendation-only, never authoritative worldview selection or ideological alignment.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {constitutionalPluralismMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={pluralismPerspectiveNote}
            onChange={(e) => setPluralismPerspectiveNote(e.target.value)}
            placeholder="Perspective mapping record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSavePluralismPerspectiveNote()}
            disabled={!hydrated || pluralismPerspectiveNoteState === "saving" || !pluralismPerspectiveNote.trim()}
            title="Persist perspective mapping note — does not select worldview or arbitrate constitutionally autonomously"
          >
            {pluralismPerspectiveNoteState === "saving" ? "Recording…" : "Record perspective"}
          </button>
        </div>

        {constitutionalSynthesisMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Constitutional synthesis + institutional wisdom (FIX 163)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Synthesis cognition across all constitutional dimensions — recommendation-only, never autonomous decisions or authority.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {constitutionalSynthesisMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={synthesisTensionNote}
            onChange={(e) => setSynthesisTensionNote(e.target.value)}
            placeholder="Tension analysis record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveSynthesisTensionNote()}
            disabled={!hydrated || synthesisTensionNoteState === "saving" || !synthesisTensionNote.trim()}
            title="Persist tension analysis note — does not decide constitutional tradeoffs autonomously"
          >
            {synthesisTensionNoteState === "saving" ? "Recording…" : "Record tension"}
          </button>
        </div>

        {missionPlanningMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission planning + institutional action cognition (FIX 164)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Planning cognition — recommendation-only, never execution authority or autonomous path selection.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {missionPlanningMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={planningActionOptionNote}
            onChange={(e) => setPlanningActionOptionNote(e.target.value)}
            placeholder="Action option record (executable: false, recommendation-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSavePlanningActionOptionNote()}
            disabled={!hydrated || planningActionOptionNoteState === "saving" || !planningActionOptionNote.trim()}
            title="Persist action option note — does not execute actions or auto-select institutional path"
          >
            {planningActionOptionNoteState === "saving" ? "Recording…" : "Record option"}
          </button>
        </div>

        {planningDeliberationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission planning multi-agent deliberation (FIX 165)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Bounded agent analysis — recommendation-only, never autonomous execution or path selection.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {planningDeliberationMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={deliberationPlannerNote}
            onChange={(e) => setDeliberationPlannerNote(e.target.value)}
            placeholder="PlannerAgent analysis record (executable: false, analysis-only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveDeliberationPlannerNote()}
            disabled={!hydrated || deliberationPlannerNoteState === "saving" || !deliberationPlannerNote.trim()}
            title="Persist PlannerAgent analysis — agents analyze only, never execute or approve"
          >
            {deliberationPlannerNoteState === "saving" ? "Recording…" : "Record planner analysis"}
          </button>
        </div>

        {humanDecisionBoardMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Human decision board + action selection (FIX 166)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Human choice only — records selection, rationale, and traceability; never autonomous selection or execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {humanDecisionBoardMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={decisionSelectionNote}
            onChange={(e) => setDecisionSelectionNote(e.target.value)}
            placeholder="Human selection record (executable: false, human choice only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveDecisionSelectionNote()}
            disabled={!hydrated || decisionSelectionNoteState === "saving" || !decisionSelectionNote.trim()}
            title="Persist human selection — AethOS records choice, never makes it autonomously"
          >
            {decisionSelectionNoteState === "saving" ? "Recording…" : "Record selection"}
          </button>
        </div>

        {executionHandoffMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governed execution handoff coordination (FIX 167)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Handoff coordination only — maps human decision to eligible lanes; no execution authority.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {executionHandoffMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={handoffArtifactNote}
            onChange={(e) => setHandoffArtifactNote(e.target.value)}
            placeholder="Handoff artifact note (executable: false, coordination only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveHandoffArtifactNote()}
            disabled={!hydrated || handoffArtifactNoteState === "saving" || !handoffArtifactNote.trim()}
            title="Persist handoff artifact — coordinates to governed lanes, never executes"
          >
            {handoffArtifactNoteState === "saving" ? "Recording…" : "Record handoff artifact"}
          </button>
        </div>

        {deliveryWorkPackagesMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Bounded multi-agent delivery work packages (FIX 168)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Package scoping only — assigns Planner / Risk / Verification / Delivery / DiffAudit without execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {deliveryWorkPackagesMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={workPackageArtifactNote}
            onChange={(e) => setWorkPackageArtifactNote(e.target.value)}
            placeholder="Work package artifact note (executable: false, scoping only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveWorkPackageArtifactNote()}
            disabled={!hydrated || workPackageArtifactNoteState === "saving" || !workPackageArtifactNote.trim()}
            title="Persist work package artifact — scopes bounded delivery, never executes"
          >
            {workPackageArtifactNoteState === "saving" ? "Recording…" : "Record work package"}
          </button>
        </div>

        {laneAdmissionMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Work package readiness + lane admission (FIX 169)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Readiness evaluation only — determines lane eligibility; humans authorize entry.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {laneAdmissionMd}
            </pre>
          </div>
        ) : null}

        <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "flex-start", flexWrap: "wrap" }}>
          <textarea
            value={laneAdmissionArtifactNote}
            onChange={(e) => setLaneAdmissionArtifactNote(e.target.value)}
            placeholder="Lane admission artifact note (executable: false, readiness only)…"
            rows={2}
            style={{
              flex: "1 1 240px",
              minWidth: 200,
              fontSize: 12,
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveLaneAdmissionArtifactNote()}
            disabled={!hydrated || laneAdmissionArtifactNoteState === "saving" || !laneAdmissionArtifactNote.trim()}
            title="Persist lane admission artifact — evaluates readiness, never enters lanes"
          >
            {laneAdmissionArtifactNoteState === "saving" ? "Recording…" : "Record lane admission"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Mission authorization artifact (FIX 170)
          </label>
          <textarea
            value={missionAuthorizationArtifactNote}
            onChange={(e) => setMissionAuthorizationArtifactNote(e.target.value)}
            placeholder="Record bounded Tier 1–2 mission authorization envelope — existing gates still enforced"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveMissionAuthorizationArtifactNote()}
            disabled={
              !hydrated ||
              missionAuthorizationArtifactNoteState === "saving" ||
              !missionAuthorizationArtifactNote.trim()
            }
            title="Persist mission authorization artifact — bounded envelope, re-engage only on escalation"
          >
            {missionAuthorizationArtifactNoteState === "saving" ? "Recording…" : "Record mission authorization"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Bounded execution participation artifact (FIX 171)
          </label>
          <textarea
            value={boundedExecutionParticipationArtifactNote}
            onChange={(e) => setBoundedExecutionParticipationArtifactNote(e.target.value)}
            placeholder="Record agent participation scope inside authorized Tier 1–2 envelope — no autonomous lane entry"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveBoundedExecutionParticipationArtifactNote()}
            disabled={
              !hydrated ||
              boundedExecutionParticipationArtifactNoteState === "saving" ||
              !boundedExecutionParticipationArtifactNote.trim()
            }
            title="Persist participation artifact — envelope-scoped coordination, re-engage only on escalation"
          >
            {boundedExecutionParticipationArtifactNoteState === "saving"
              ? "Recording…"
              : "Record bounded execution participation"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Execution coordination artifact (FIX 172)
          </label>
          <textarea
            value={governedTaskExecutionCoordinationArtifactNote}
            onChange={(e) => setGovernedTaskExecutionCoordinationArtifactNote(e.target.value)}
            placeholder="Record package sequencing and lifecycle coordination — coordinate without executing"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveGovernedTaskExecutionCoordinationArtifactNote()}
            disabled={
              !hydrated ||
              governedTaskExecutionCoordinationArtifactNoteState === "saving" ||
              !governedTaskExecutionCoordinationArtifactNote.trim()
            }
            title="Persist coordination artifact — assign and track packages, existing gates decide outcomes"
          >
            {governedTaskExecutionCoordinationArtifactNoteState === "saving"
              ? "Recording…"
              : "Record execution coordination"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Gate outcome review artifact (FIX 173)
          </label>
          <textarea
            value={gateRoutedPackageOutcomeReviewArtifactNote}
            onChange={(e) => setGateRoutedPackageOutcomeReviewArtifactNote(e.target.value)}
            placeholder="Record outcome classification and frozen gate mapping — review does not execute"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveGateRoutedPackageOutcomeReviewArtifactNote()}
            disabled={
              !hydrated ||
              gateRoutedPackageOutcomeReviewArtifactNoteState === "saving" ||
              !gateRoutedPackageOutcomeReviewArtifactNote.trim()
            }
            title="Persist gate review artifact — existing frozen gates decide lane action"
          >
            {gateRoutedPackageOutcomeReviewArtifactNoteState === "saving"
              ? "Recording…"
              : "Record gate outcome review"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Lane entry recommendation artifact (FIX 174)
          </label>
          <textarea
            value={governedLaneEntryRecommendationArtifactNote}
            onChange={(e) => setGovernedLaneEntryRecommendationArtifactNote(e.target.value)}
            placeholder="Record lane entry recommendation — composes readiness + gate review, does not admit"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveGovernedLaneEntryRecommendationArtifactNote()}
            disabled={
              !hydrated ||
              governedLaneEntryRecommendationArtifactNoteState === "saving" ||
              !governedLaneEntryRecommendationArtifactNote.trim()
            }
            title="Persist lane recommendation artifact — human and frozen gates decide admission"
          >
            {governedLaneEntryRecommendationArtifactNoteState === "saving"
              ? "Recording…"
              : "Record lane entry recommendation"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Lane readiness board artifact (FIX 175)
          </label>
          <textarea
            value={governedLaneReadinessBoardArtifactNote}
            onChange={(e) => setGovernedLaneReadinessBoardArtifactNote(e.target.value)}
            placeholder="Record lane readiness board summary — human decides admission in FIX 176"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveGovernedLaneReadinessBoardArtifactNote()}
            disabled={
              !hydrated ||
              governedLaneReadinessBoardArtifactNoteState === "saving" ||
              !governedLaneReadinessBoardArtifactNote.trim()
            }
            title="Persist lane readiness board artifact — board does not admit to lane"
          >
            {governedLaneReadinessBoardArtifactNoteState === "saving"
              ? "Recording…"
              : "Record lane readiness board"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Lane admission decision artifact (FIX 176)
          </label>
          <textarea
            value={humanLaneAdmissionDecisionArtifactNote}
            onChange={(e) => setHumanLaneAdmissionDecisionArtifactNote(e.target.value)}
            placeholder="Record admit, hold, or reject — e.g. admit: software_delivery via workspace_verification gate"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveHumanLaneAdmissionDecisionArtifactNote()}
            disabled={
              !hydrated ||
              humanLaneAdmissionDecisionArtifactNoteState === "saving" ||
              !humanLaneAdmissionDecisionArtifactNote.trim()
            }
            title="Persist human lane admission decision — decision ≠ lane entry execution"
          >
            {humanLaneAdmissionDecisionArtifactNoteState === "saving"
              ? "Recording…"
              : "Record lane admission decision"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Gate handoff artifact (FIX 177)
          </label>
          <textarea
            value={gateRoutedLaneEntryHandoffArtifactNote}
            onChange={(e) => setGateRoutedLaneEntryHandoffArtifactNote(e.target.value)}
            placeholder="Record gate handoff — e.g. deliver admit decision to workspace_verification frozen gate"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveGateRoutedLaneEntryHandoffArtifactNote()}
            disabled={
              !hydrated ||
              gateRoutedLaneEntryHandoffArtifactNoteState === "saving" ||
              !gateRoutedLaneEntryHandoffArtifactNote.trim()
            }
            title="Persist gate handoff artifact — handoff ≠ lane entry execution"
          >
            {gateRoutedLaneEntryHandoffArtifactNoteState === "saving"
              ? "Recording…"
              : "Record gate handoff"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Gate intake preview artifact (FIX 178)
          </label>
          <textarea
            value={frozenGateIntakePreviewArtifactNote}
            onChange={(e) => setFrozenGateIntakePreviewArtifactNote(e.target.value)}
            placeholder="Record intake preview — e.g. preview workspace_verification gate intake without execution"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveFrozenGateIntakePreviewArtifactNote()}
            disabled={
              !hydrated ||
              frozenGateIntakePreviewArtifactNoteState === "saving" ||
              !frozenGateIntakePreviewArtifactNote.trim()
            }
            title="Persist gate intake preview artifact — intake preview ≠ gate execution"
          >
            {frozenGateIntakePreviewArtifactNoteState === "saving"
              ? "Recording…"
              : "Record gate intake preview"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Execution request artifact (FIX 179)
          </label>
          <textarea
            value={frozenGateExecutionRequestAdapterArtifactNote}
            onChange={(e) => setFrozenGateExecutionRequestAdapterArtifactNote(e.target.value)}
            placeholder="Record execution request — e.g. request run workspace verification via frozen lane command"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveFrozenGateExecutionRequestAdapterArtifactNote()}
            disabled={
              !hydrated ||
              frozenGateExecutionRequestAdapterArtifactNoteState === "saving" ||
              !frozenGateExecutionRequestAdapterArtifactNote.trim()
            }
            title="Persist execution request artifact — execution request ≠ execution"
          >
            {frozenGateExecutionRequestAdapterArtifactNoteState === "saving"
              ? "Recording…"
              : "Record execution request"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Handoff invocation artifact (FIX 180)
          </label>
          <textarea
            value={governedChatCommandInvocationFromHandoffArtifactNote}
            onChange={(e) => setGovernedChatCommandInvocationFromHandoffArtifactNote(e.target.value)}
            placeholder="Record invocation packet — routes through chat governance, not direct provider APIs"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveGovernedChatCommandInvocationFromHandoffArtifactNote()}
            disabled={
              !hydrated ||
              governedChatCommandInvocationFromHandoffArtifactNoteState === "saving" ||
              !governedChatCommandInvocationFromHandoffArtifactNote.trim()
            }
            title="Persist handoff invocation artifact — invocation ≠ direct execution"
          >
            {governedChatCommandInvocationFromHandoffArtifactNoteState === "saving"
              ? "Recording…"
              : "Record handoff invocation"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Pilot harness artifact (FIX 181)
          </label>
          <textarea
            value={endToEndRepoDevelopmentPilotHarnessArtifactNote}
            onChange={(e) => setEndToEndRepoDevelopmentPilotHarnessArtifactNote(e.target.value)}
            placeholder="Record pilot artifact — one repo, one issue, routes through chat governance"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveEndToEndRepoDevelopmentPilotHarnessArtifactNote()}
            disabled={
              !hydrated ||
              endToEndRepoDevelopmentPilotHarnessArtifactNoteState === "saving" ||
              !endToEndRepoDevelopmentPilotHarnessArtifactNote.trim()
            }
            title="Persist pilot harness artifact — pilot ≠ autonomous execution"
          >
            {endToEndRepoDevelopmentPilotHarnessArtifactNoteState === "saving"
              ? "Recording…"
              : "Record pilot artifact"}
          </button>
        </div>

        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
          <label style={{ fontSize: 12, fontWeight: 600, color: mcColors.textMuted }}>
            Pilot readiness artifact (FIX 182)
          </label>
          <textarea
            value={repoPilotReadinessDashboardArtifactNote}
            onChange={(e) => setRepoPilotReadinessDashboardArtifactNote(e.target.value)}
            placeholder="Record repo/issue selection — readiness visibility only, no pilot execution"
            rows={3}
            style={{
              width: "100%",
              padding: 8,
              borderRadius: 6,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              color: mcColors.text,
              fontSize: 12,
              resize: "vertical",
            }}
          />
          <button
            type="button"
            style={mcButtonSecondaryStyle}
            onClick={() => void handleSaveRepoPilotReadinessDashboardArtifactNote()}
            disabled={
              !hydrated ||
              repoPilotReadinessDashboardArtifactNoteState === "saving" ||
              !repoPilotReadinessDashboardArtifactNote.trim()
            }
            title="Persist readiness artifact — readiness ≠ execution"
          >
            {repoPilotReadinessDashboardArtifactNoteState === "saving"
              ? "Recording…"
              : "Record readiness note"}
          </button>
        </div>

        {missionAuthorizationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission authorization (FIX 170)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Bounded Tier 1–2 work envelope — existing gate checks enforced, re-engagement only on escalation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {missionAuthorizationMd}
            </pre>
          </div>
        ) : null}

        {boundedExecutionParticipationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Bounded execution participation (FIX 171)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Agents participate inside authorized envelope — every action passes existing gates, re-engage on escalation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {boundedExecutionParticipationMd}
            </pre>
          </div>
        ) : null}

        {governedTaskExecutionCoordinationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governed task execution coordination (FIX 172)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Coordinate package assignments and lifecycle — execution coordination ≠ execution authority.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {governedTaskExecutionCoordinationMd}
            </pre>
          </div>
        ) : null}

        {gateRoutedPackageOutcomeReviewMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Gate-routed package outcome review (FIX 173)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Classify coordinated outcomes and map to frozen gates — review ≠ lane execution authority.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {gateRoutedPackageOutcomeReviewMd}
            </pre>
          </div>
        ) : null}

        {governedLaneEntryRecommendationMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governed lane entry recommendation (FIX 174)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Composes FIX 169 readiness + FIX 173 gate review — lane recommendation ≠ lane admission.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {governedLaneEntryRecommendationMd}
            </pre>
          </div>
        ) : null}

        {governedLaneReadinessBoardMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governed lane readiness board (FIX 175)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Consolidates lane recommendation for human review — board ≠ lane admission decision.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {governedLaneReadinessBoardMd}
            </pre>
          </div>
        ) : null}

        {humanLaneAdmissionDecisionMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Human lane admission decision (FIX 176)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Human admit, hold, or reject — decision ≠ lane entry execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {humanLaneAdmissionDecisionMd}
            </pre>
          </div>
        ) : null}

        {gateRoutedLaneEntryHandoffMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Gate-routed lane entry handoff (FIX 177)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Handoff packet for frozen gate validation — handoff ≠ lane entry execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {gateRoutedLaneEntryHandoffMd}
            </pre>
          </div>
        ) : null}

        {frozenGateIntakePreviewMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Frozen gate intake preview (FIX 178)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Frozen gate receives handoff preview — intake preview ≠ gate execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {frozenGateIntakePreviewMd}
            </pre>
          </div>
        ) : null}

        {frozenGateExecutionRequestAdapterMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Frozen gate execution request adapter (FIX 179)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Maps intake preview to frozen lane command — execution request ≠ execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {frozenGateExecutionRequestAdapterMd}
            </pre>
          </div>
        ) : null}

        {governedChatCommandInvocationFromHandoffMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governed chat command invocation from handoff (FIX 180)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Routes frozen command through resolve_chat_turn — handoff invocation ≠ direct execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {governedChatCommandInvocationFromHandoffMd}
            </pre>
          </div>
        ) : null}

        {endToEndRepoDevelopmentPilotHarnessMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              End-to-end repo development pilot harness (FIX 181)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Bounded pilot through frozen software delivery loop — pilot harness ≠ autonomous execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {endToEndRepoDevelopmentPilotHarnessMd}
            </pre>
          </div>
        ) : null}

        {repoPilotReadinessDashboardMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Repo pilot readiness dashboard (FIX 182)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Preflight visibility before pilot — readiness dashboard ≠ pilot execution.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {repoPilotReadinessDashboardMd}
            </pre>
          </div>
        ) : null}

        {govSimMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance simulation sandbox (FIX 144)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Hypothetical governance configurations — compare friction, latency, and risk without live policy mutation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {govSimMd}
            </pre>
          </div>
        ) : null}

        {govInsightsMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Governance insights (FIX 143)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Meta-governance observability — how the governance system behaves. No policy auto-tuning or self-modification.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {govInsightsMd}
            </pre>
          </div>
        ) : null}

        {guidanceMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Operator contextual guidance (FIX 142)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Operational copiloting — all recommendations are non-executable; operator approval required for actions.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {guidanceMd}
            </pre>
          </div>
        ) : null}

        {knowledgeMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Mission knowledge spaces (FIX 141)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Semantic retrieval over incidents, blockers, approvals, PRs, and rollout history.
              Recommendations only — no autonomous action.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {knowledgeMd}
            </pre>
          </div>
        ) : null}

        {crossSessionMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Cross-session organizational memory (FIX 140)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              Durable operator history across sessions — mission ancestry, historical blockers, evidence stitching.
              Read-only; no autonomous adaptation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {crossSessionMd}
            </pre>
          </div>
        ) : null}

        {memoryMd ? (
          <div
            style={{
              marginTop: 12,
              padding: 12,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: mcColors.panelAlt,
              maxHeight: 360,
              overflow: "auto",
            }}
          >
            <h3 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>
              Operational memory graph (read-only)
            </h3>
            <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted }}>
              FIX 139 knowledge substrate — correlates missions, jobs, approvals, incidents, PRs, replay, and rerun
              plans. No autonomous adaptation.
            </p>
            <pre
              style={{
                margin: 0,
                fontSize: 11,
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                fontFamily: "ui-monospace, monospace",
              }}
            >
              {memoryMd}
            </pre>
          </div>
        ) : null}

        {!hydrated ? <ContextSkeleton /> : <OperatorContextBar context={operatorCtx} snapshot={snapshot} />}

        {loadState === "loading" && !snapshot ? <LoadingState /> : null}
        {loadState === "error" && errorMessage ? (
          <ErrorState message={errorMessage} onRetry={() => void load()} />
        ) : null}
        {loadState === "loaded" && snapshot && !sessionScopedActivity && !errorMessage ? (
          <EmptySnapshotState sessionId={sessionId} onRetry={() => void load()} />
        ) : null}

        {snapshot && loadState === "loaded" ? (
          <div style={{ marginTop: 16, display: "grid", gap: 10, fontSize: 13 }}>
            <Row label="Snapshot" value={snapshot.snapshot_id ?? "—"} />
            <Row label="Correlation" value={snapshot.correlation_id ?? "—"} mono />
            <Row label="Plan" value={snapshot.plan_id || "—"} mono />
            <Row label="Recorded" value={snapshot.recorded_at ?? "—"} />
            <Row
              label="Overall health"
              value={String(health.overall ?? "unknown")}
              highlight={String(health.overall) !== "healthy"}
            />
            {meta?.detail ? (
              <p style={{ margin: "4px 0 0", color: mcColors.textDim, fontSize: 12 }}>{meta.detail}</p>
            ) : null}
          </div>
        ) : null}
      </section>

      {snapshot && loadState === "loaded" && sessionScopedActivity ? (
        <>
          <Section title="Attention queue" subtitle="Items requiring operator awareness (read-only).">
            <AttentionList
              items={snapshot.attention_queue ?? []}
              empty="No attention items — lanes are clear for this session."
              onSelectLane={handleLaneFocus}
            />
          </Section>

          <Section title="Active approvals" subtitle="Governance gates awaiting approval phrases (display only).">
            <AttentionList
              items={snapshot.active_approvals ?? []}
              empty="No pending approval gates in the current session snapshot."
              onSelectLane={handleLaneFocus}
            />
          </Section>

          <Section
            title="Unified timeline"
            subtitle="Select an event to jump to lane detail. Cross-lane ordering is read-only."
          >
            <TimelineList
              entries={snapshot.unified_timeline ?? []}
              selectedLane={selectedLane}
              onSelect={(entry) => {
                if (entry.lane) handleLaneFocus(entry.lane);
              }}
              onOpenReplayDeepLink={onOpenReplayDeepLink}
            />
            {selectedLane ? (
              <CrossLaneLaneDrilldownPanel
                lane={selectedLane}
                sessionId={sessionId}
                onClose={() => setSelectedLane(null)}
                onOpenReplayDeepLink={onOpenReplayDeepLink}
              />
            ) : null}
          </Section>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            <LaneCard id={laneAnchorId("software_delivery")} title="Software delivery" lane={sd} active={selectedLane === "software_delivery"} onFocus={() => handleLaneFocus("software_delivery")}>
              <Row label="Plan status" value={String(sd.plan_status ?? "—")} />
              <Row label="Repository" value={String(sd.repository ?? "—")} />
              <Row label="Pending gates" value={String((sd.pending_gates as string[] | undefined)?.join(", ") || "none")} />
              <Row label="Timeline events" value={String(sd.timeline_event_count ?? 0)} />
            </LaneCard>

            <LaneCard id={laneAnchorId("railway_orchestration")} title="Railway orchestration" lane={railway} active={selectedLane === "railway_orchestration"} onFocus={() => handleLaneFocus("railway_orchestration")}>
              <Row label="Recent journals" value={String(railway.recent_journals ?? 0)} />
              <Row label="Recent receipts" value={String(railway.recent_receipts ?? 0)} />
              <Row label="Latest status" value={String(railway.latest_journal_status ?? "—")} />
              <Row label="Execution id" value={String(railway.latest_execution_id ?? "—")} mono />
            </LaneCard>

            <LaneCard id={laneAnchorId("incident_command")} title="Incidents" lane={incidents} active={selectedLane === "incident_command"} onFocus={() => handleLaneFocus("incident_command")}>
              <Row label="Open incidents" value={String(incidents.open_incidents ?? 0)} highlight={Number(incidents.open_incidents) > 0} />
              <Row label="Total recorded" value={String(incidents.incident_count ?? 0)} />
              <Row label="Latest id" value={String(incidents.latest_incident_id ?? "—")} mono />
              <Row label="Latest status" value={String(incidents.latest_status ?? "—")} />
            </LaneCard>

            <LaneCard id={laneAnchorId("production_governance")} title="Production governance" lane={governance} active={selectedLane === "production_governance"} onFocus={() => handleLaneFocus("production_governance")}>
              <Row label="Rollout records" value={String(governance.rollout_records ?? 0)} />
              <Row label="Shadow records" value={String(governance.shadow_records ?? 0)} />
              <Row label="Latest stage" value={String(governance.latest_rollout_stage ?? "—")} />
              <Row label="Policy" value={String(governance.mutation_policy ?? "—")} />
            </LaneCard>

            <LaneCard id={laneAnchorId("multi_agent_collaboration")} title="Agent collaboration" lane={agents} active={selectedLane === "multi_agent_collaboration"} onFocus={() => handleLaneFocus("multi_agent_collaboration")}>
              <Row label="Collaboration" value={String(agents.collaboration_id ?? "—")} mono />
              <Row label="Status" value={String(agents.status ?? "—")} />
              <Row
                label="Agents run"
                value={
                  Array.isArray(agents.agents_run) && agents.agents_run.length
                    ? (agents.agents_run as string[]).join(", ")
                    : "—"
                }
              />
              <Row label="Mutation" value={agents.mutation_performed === false ? "none (advisory)" : String(agents.mutation_performed ?? "—")} />
            </LaneCard>
          </div>
        </>
      ) : null}
    </div>
  );
}

function OperatorContextBar({
  context,
  snapshot,
}: {
  context: OperatorContext;
  snapshot: MissionControlCrossLaneSnapshot | null;
}) {
  return (
    <div
      style={{
        marginTop: 14,
        padding: "12px 14px",
        borderRadius: 10,
        border: `1px solid ${mcColors.border}`,
        background: "rgba(0,0,0,0.22)",
        display: "grid",
        gap: 6,
        fontSize: 12,
      }}
    >
      <div style={{ fontWeight: 600, color: mcColors.cyan, letterSpacing: "0.03em", textTransform: "uppercase" }}>
        Operator context
      </div>
      <Row label="Session" value={context.sessionId} mono />
      <Row label="Operator mode" value={context.operatorMode} />
      <Row label="Channel" value={context.channel} />
      {snapshot?.correlation_id ? <Row label="Correlation" value={snapshot.correlation_id} mono /> : null}
      {snapshot?.plan_id ? <Row label="Active plan" value={snapshot.plan_id} mono /> : null}
    </div>
  );
}

function ContextSkeleton() {
  return (
    <div
      style={{
        marginTop: 14,
        height: 72,
        borderRadius: 10,
        background: "rgba(255,255,255,0.04)",
        border: `1px solid ${mcColors.borderSubtle}`,
      }}
      aria-hidden
    />
  );
}

function LoadingState() {
  return (
    <div style={{ marginTop: 14, padding: "16px 0", textAlign: "center" }}>
      <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>Loading cross-lane snapshot for your session…</p>
    </div>
  );
}

function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      style={{
        marginTop: 14,
        padding: 14,
        borderRadius: 10,
        border: `1px solid ${mcColors.red}`,
        background: "rgba(239,68,68,0.08)",
      }}
    >
      <p style={{ margin: "0 0 10px", color: mcColors.red, fontSize: 13 }}>{message}</p>
      <button type="button" style={mcButtonSecondaryStyle} onClick={onRetry}>
        Retry snapshot
      </button>
    </div>
  );
}

function EmptySnapshotState({ sessionId, onRetry }: { sessionId: string; onRetry: () => void }) {
  return (
    <div
      style={{
        marginTop: 14,
        padding: 14,
        borderRadius: 10,
        border: `1px solid ${mcColors.border}`,
        background: "rgba(255,255,255,0.03)",
      }}
    >
      <p style={{ margin: "0 0 8px", fontSize: 13, color: mcColors.text }}>
        No governed lane activity for session <code style={{ color: mcColors.cyan }}>{sessionId}</code> yet.
      </p>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>
        Start software delivery or operational work in chat — this panel will reflect the same session id automatically.
      </p>
      <button type="button" style={mcButtonSecondaryStyle} onClick={onRetry}>
        Refresh snapshot
      </button>
    </div>
  );
}

function ReadOnlyBadge() {
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        padding: "4px 10px",
        borderRadius: 999,
        border: `1px solid ${mcColors.cyan}`,
        color: mcColors.cyan,
        background: "rgba(34,211,238,0.08)",
      }}
    >
      Read only
    </span>
  );
}

function Section({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <section style={mcPanelSectionStyle}>
      <h3 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>{title}</h3>
      {subtitle ? <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>{subtitle}</p> : null}
      {children}
    </section>
  );
}

function LaneCard({
  id,
  title,
  lane,
  active,
  onFocus,
  children,
}: {
  id: string;
  title: string;
  lane: Record<string, unknown>;
  active?: boolean;
  onFocus: () => void;
  children: ReactNode;
}) {
  return (
    <section
      id={id}
      style={{
        ...mcPanelSectionStyle,
        margin: 0,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        outline: active ? `1px solid ${mcColors.cyan}` : undefined,
        boxShadow: active ? "0 0 0 1px rgba(34,211,238,0.25)" : undefined,
      }}
    >
      <button
        type="button"
        onClick={onFocus}
        style={{
          all: "unset",
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          gap: 8,
        }}
      >
        <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>{title}</h3>
        <span style={{ fontSize: 11, color: lane.ok ? mcColors.green : mcColors.textMuted }}>
          {lane.ok ? "observed" : "no signal"} — open drilldown
        </span>
        {children}
      </button>
    </section>
  );
}

function AttentionList({
  items,
  empty,
  onSelectLane,
}: {
  items: MissionControlAttentionItem[];
  empty: string;
  onSelectLane: (lane: string) => void;
}) {
  if (!items.length) {
    return <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>{empty}</p>;
  }
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
      {items.map((item, i) => (
        <li key={`${item.lane}-${item.gate}-${i}`} style={{ marginBottom: 8 }}>
          <button
            type="button"
            onClick={() => item.lane && onSelectLane(item.lane)}
            style={{
              width: "100%",
              textAlign: "left",
              padding: "10px 12px",
              borderRadius: 10,
              border: `1px solid ${mcColors.border}`,
              background: "rgba(0,0,0,0.2)",
              color: "inherit",
              cursor: item.lane ? "pointer" : "default",
            }}
          >
            <span style={{ color: priorityColor(item.priority), fontWeight: 600, textTransform: "uppercase", fontSize: 11 }}>
              {item.priority ?? "medium"}
            </span>
            <div style={{ marginTop: 4, color: mcColors.text }}>
              {item.lane ? laneDisplayTitle(item.lane) : "—"} · {item.gate}
              {item.count != null ? ` (${item.count})` : ""}
            </div>
            {item.lane ? (
              <div style={{ marginTop: 4, fontSize: 11, color: mcColors.cyan }}>View lane detail →</div>
            ) : null}
          </button>
        </li>
      ))}
    </ul>
  );
}

function TimelineList({
  entries,
  selectedLane,
  onSelect,
  onOpenReplayDeepLink,
}: {
  entries: MissionControlTimelineEntry[];
  selectedLane: string | null;
  onSelect: (entry: MissionControlTimelineEntry) => void;
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
}) {
  if (!entries.length) {
    return (
      <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
        No cross-lane timeline events for this session yet. Events appear as governed lanes record receipts and plan
        milestones.
      </p>
    );
  }
  return (
    <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13, maxHeight: 360, overflowY: "auto" }}>
      {entries.map((entry, i) => {
        const active = selectedLane != null && entry.lane === selectedLane;
        return (
          <li key={`${entry.lane}-${entry.timestamp}-${i}`} style={{ marginBottom: 6 }}>
            <button
              type="button"
              onClick={() => onSelect(entry)}
              style={{
                width: "100%",
                textAlign: "left",
                padding: "8px 10px 8px 12px",
                background: active ? "rgba(34,211,238,0.06)" : "transparent",
                border: "none",
                borderLeft: `2px solid ${active ? mcColors.cyan : mcColors.border}`,
                color: "inherit",
                cursor: "pointer",
                borderRadius: 4,
              }}
            >
              <div style={{ color: mcColors.textDim, fontSize: 11 }}>{entry.timestamp || "—"}</div>
              <div style={{ color: mcColors.cyan, fontWeight: 500 }}>
                {entry.lane ? laneDisplayTitle(entry.lane) : "—"}
              </div>
              <div style={{ color: mcColors.text }}>{entry.action}</div>
              {entry.detail ? <div style={{ color: mcColors.textMuted, marginTop: 2 }}>{entry.detail}</div> : null}
              <div style={{ marginTop: 4, fontSize: 11, color: mcColors.textDim }}>Open lane detail →</div>
              {onOpenReplayDeepLink ? (
                <ReplayDeepLinkButton
                  onClick={() => onOpenReplayDeepLink({ linkRef: buildTimelineLinkRef(entry) })}
                />
              ) : null}
            </button>
          </li>
        );
      })}
    </ul>
  );
}

function priorityColor(priority?: string): string {
  if (priority === "critical") return mcColors.red;
  if (priority === "high") return mcColors.amber;
  return mcColors.textMuted;
}

function Row({
  label,
  value,
  highlight = false,
  mono = false,
}: {
  label: string;
  value: string;
  highlight?: boolean;
  mono?: boolean;
}) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
      <span style={{ color: mcColors.textMuted }}>{label}</span>
      <span
        style={{
          color: highlight ? mcColors.amber : mcColors.text,
          fontWeight: highlight ? 600 : 400,
          fontFamily: mono ? "ui-monospace, monospace" : undefined,
          fontSize: mono ? 12 : 13,
          textAlign: "right",
          wordBreak: "break-all",
        }}
      >
        {value}
      </span>
    </div>
  );
}
