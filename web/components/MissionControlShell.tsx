"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { RuntimeActionsPanel } from "@/components/missionControl/RuntimeActionsPanel";
import { JobsTrackedWorkPanel } from "@/components/JobsTrackedWorkPanel";
import { BrowserCapabilityCard } from "@/components/BrowserCapabilityCard";
import { WorkspaceDiagnosticsCard } from "@/components/WorkspaceDiagnosticsCard";
import { BrowserEvidencePanel } from "@/components/BrowserEvidencePanel";
import { WebIntelligencePanel } from "@/components/WebIntelligencePanel";
import { BrowserProfilesPanel } from "@/components/BrowserProfilesPanel";
import { BrowserSessionsPanel } from "@/components/BrowserSessionsPanel";
import { TelegramSessionsPanel } from "@/components/TelegramSessionsPanel";
import { SloPanel } from "@/components/missionControl/SloPanel";
import { JobTraceReplayPanel } from "@/components/missionControl/JobTraceReplayPanel";
import { ConnectionsHealthOverview } from "@/components/settings/ProviderCatalog/ConnectionsHealthOverview";
import { ProviderCatalog } from "@/components/settings/ProviderCatalog/ProviderCatalog";
import { ProviderCredentialCenter } from "@/components/settings/ProviderCatalog/ProviderCredentialCenter";
import { ProviderSettingsCard } from "@/components/ProviderSettingsCard";
import { MissionControlHeader } from "@/components/missionControl/MissionControlHeader";
import { GovernanceFastPathBanner } from "@/components/missionControl/GovernanceFastPathBanner";
import { GovernanceKillSwitchPanel } from "@/components/missionControl/GovernanceKillSwitchPanel";
import { MissionControlSidebar } from "@/components/missionControl/MissionControlSidebar";
import { CrossProviderCorrelationPanel } from "@/components/missionControl/CrossProviderCorrelationPanel";
import { OperationalIntelligencePanel } from "@/components/missionControl/OperationalIntelligencePanel";
import { EngineeringExecutionPanel } from "@/components/missionControl/EngineeringExecutionPanel";
import { ResearchConfigPanel } from "@/components/missionControl/ResearchConfigPanel";
import { ResearchIntelligencePanel } from "@/components/missionControl/ResearchIntelligencePanel";
import { RuntimeTunnelPanel } from "@/components/missionControl/RuntimeTunnelPanel";
import { RuntimeSettingsPanel } from "@/components/missionControl/RuntimeSettingsPanel";
import { PresenceOperationsPanel } from "@/components/missionControl/PresenceOperationsPanel";
import { EnterpriseOperationsPanel } from "@/components/missionControl/EnterpriseOperationsPanel";
import { DogfoodPilotChainPanel } from "@/components/missionControl/DogfoodPilotChainPanel";
import { MultiRepoPilotProgramPanel } from "@/components/missionControl/MultiRepoPilotProgramPanel";
import { PilotValidationTrustBoardPanel } from "@/components/missionControl/PilotValidationTrustBoardPanel";
import { ProductionInfrastructurePanel } from "@/components/missionControl/ProductionInfrastructurePanel";
import { HumanCenteredPanel } from "@/components/missionControl/HumanCenteredPanel";
import { PresenceQualityPanel } from "@/components/missionControl/PresenceQualityPanel";
import { CompanionIntelligencePanel } from "@/components/missionControl/CompanionIntelligencePanel";
import { ApprovalInboxPanel } from "@/components/missionControl/ApprovalInboxPanel";
import { JobReplayPanel } from "@/components/missionControl/JobReplayPanel";
import {
  buildReplayNavigationTarget,
  readOperatorUrlState,
  writeOperatorUrlState,
  type ReplayDeepLinkTarget,
} from "@/lib/missionControl/missionControlReplayDeepLink";
import { CrossLaneOperationsPanel } from "@/components/missionControl/CrossLaneOperationsPanel";
import { SimpleOverviewPanel } from "@/components/missionControl/SimpleOverviewPanel";
import { WorkflowHubPanel } from "@/components/missionControl/WorkflowHubPanel";
import { RuntimeIntegrityPanel } from "@/components/missionControl/RuntimeIntegrityPanel";
import { DurableJobsPanel } from "@/components/missionControl/DurableJobsPanel";
import { ConversationalGroundingPanel } from "@/components/missionControl/ConversationalGroundingPanel";
import { LongTailRuntimePanel } from "@/components/missionControl/LongTailRuntimePanel";
import { LongTailForecastingPanel } from "@/components/missionControl/LongTailForecastingPanel";
import { RuntimeFragilityPanel } from "@/components/missionControl/RuntimeFragilityPanel";
import { PredictiveCognitionPanel } from "@/components/missionControl/PredictiveCognitionPanel";
import { OperationalResiliencePanel } from "@/components/missionControl/OperationalResiliencePanel";
import { ResilienceCognitionPanel } from "@/components/missionControl/ResilienceCognitionPanel";
import { RecoveryContinuityPanel } from "@/components/missionControl/RecoveryContinuityPanel";
import { ConvergenceCognitionPanel } from "@/components/missionControl/ConvergenceCognitionPanel";
import { RuntimeTruthEvolutionPanel } from "@/components/missionControl/RuntimeTruthEvolutionPanel";
import { RuntimeTruthPanel } from "@/components/missionControl/RuntimeTruthPanel";
import { ProductionRealityPanel } from "@/components/missionControl/ProductionRealityPanel";
import { ProductionReliabilityPanel } from "@/components/missionControl/ProductionReliabilityPanel";
import { InfrastructureIntelligencePanel } from "@/components/missionControl/InfrastructureIntelligencePanel";
import { OperationalReliabilityPanel } from "@/components/missionControl/OperationalReliabilityPanel";
import { SynthesisIntelligencePanel } from "@/components/missionControl/SynthesisIntelligencePanel";
import { ConversationalConvergencePanel } from "@/components/missionControl/ConversationalConvergencePanel";
import { ConversationalReliabilityPanel } from "@/components/missionControl/ConversationalReliabilityPanel";
import { OperationalTruthPanel } from "@/components/missionControl/OperationalTruthPanel";
import { TrustOperationsPanel } from "@/components/missionControl/TrustOperationsPanel";
import { TenantOnboardingActivationPanel } from "@/components/missionControl/TenantOnboardingActivationPanel";
import { IdentityAccessHardeningPanel } from "@/components/missionControl/IdentityAccessHardeningPanel";
import { PlatformOwnerPanel } from "@/components/missionControl/PlatformOwnerPanel";
import { UsersRolesPanel } from "@/components/missionControl/UsersRolesPanel";
import { ProviderConnectionExperiencePanel } from "@/components/missionControl/ProviderConnectionExperiencePanel";
import { ChannelIntegrationFoundationPanel } from "@/components/missionControl/ChannelIntegrationFoundationPanel";
import { BillingEntitlementsFoundationPanel } from "@/components/missionControl/BillingEntitlementsFoundationPanel";
import { CustomerAdministrationConsolePanel } from "@/components/missionControl/CustomerAdministrationConsolePanel";
import { CustomerUsageAuditPortalPanel } from "@/components/missionControl/CustomerUsageAuditPortalPanel";
import { PaymentIntegrationReadinessPanel } from "@/components/missionControl/PaymentIntegrationReadinessPanel";
import { LaunchOperationsCenterPanel } from "@/components/missionControl/LaunchOperationsCenterPanel";
import { PublicLaunchReadinessFreezePanel } from "@/components/missionControl/PublicLaunchReadinessFreezePanel";
import { LaunchDecisionPackagePanel } from "@/components/missionControl/LaunchDecisionPackagePanel";
import { PostLaunchOperationsBaselinePanel } from "@/components/missionControl/PostLaunchOperationsBaselinePanel";
import { LimitedBetaLaunchProgramPanel } from "@/components/missionControl/LimitedBetaLaunchProgramPanel";
import { PublicProductExperiencePanel } from "@/components/missionControl/PublicProductExperiencePanel";
import { CustomerSupportSuccessFoundationPanel } from "@/components/missionControl/CustomerSupportSuccessFoundationPanel";
import { SaasLaunchReadinessAssessmentPanel } from "@/components/missionControl/SaasLaunchReadinessAssessmentPanel";
import { WorkspaceOperationsPanel } from "@/components/missionControl/WorkspaceOperationsPanel";
import { LocalWorkspacesPanel } from "@/components/missionControl/LocalWorkspacesPanel";
import { AgentOrchestrationPanel } from "@/components/missionControl/AgentOrchestrationPanel";
import { DeepResearchPanel } from "@/components/missionControl/DeepResearchPanel";
import { BrowserEvidenceGalleryPanel } from "@/components/missionControl/BrowserEvidenceGalleryPanel";
import { ResearchLibraryPanel } from "@/components/missionControl/ResearchLibraryPanel";
import { BlindModelEvalPanel } from "@/components/missionControl/BlindModelEvalPanel";
import { ArbiterPanel } from "@/components/ArbiterPanel";
import { MonitorsPanel } from "@/components/missionControl/MonitorsPanel";
import { DailyDigestPanel } from "@/components/missionControl/DailyDigestPanel";
import { MemoryViewerPanel } from "@/components/missionControl/MemoryViewerPanel";
import { ProactiveSuggestionsPanel } from "@/components/missionControl/ProactiveSuggestionsPanel";
import { AgentCommsPanel } from "@/components/missionControl/AgentCommsPanel";
import { ChannelToolPolicyPanel } from "@/components/missionControl/ChannelToolPolicyPanel";
import { CronGovernedJobsPanel } from "@/components/missionControl/CronGovernedJobsPanel";
import { ProactiveAutomationPanel } from "@/components/missionControl/ProactiveAutomationPanel";
import { GovernedSandboxPanel } from "@/components/missionControl/GovernedSandboxPanel";
import { McpBridgePanel } from "@/components/missionControl/McpBridgePanel";
import { MultiAgentPanel } from "@/components/missionControl/MultiAgentPanel";
import { SubagentSessionsPanel } from "@/components/missionControl/SubagentSessionsPanel";
import { MutationAuditPanel } from "@/components/missionControl/MutationAuditPanel";
import { swrFetch } from "@/lib/clientDataCache";
import { fetchMissionControlApprovalInbox } from "@/lib/missionControl/missionControlApprovalInboxApi";
import {
  fetchActionsGrouped,
  fetchMcSettings,
  fetchProviderReadiness,
  fetchRuntimeStatus,
  fetchTrackedJobs,
} from "@/lib/missionControl/api";
import { hasActiveTrackedJobs } from "@/lib/missionControl/trackedJobs";
import {
  fetchBrowserEvidenceArtifacts,
  fetchBrowserEvidenceAudit,
  type BrowserEvidenceArtifact,
  type BrowserEvidenceAuditEvent,
} from "@/lib/missionControl/browserEvidenceApi";
import { fetchArbiterSessions } from "@/lib/missionControl/phase4Api";
import {
  fetchResearchArtifacts,
  type ResearchArtifact,
} from "@/lib/missionControl/researchApi";
import {
  fetchBrowserProfiles,
  type BrowserProfilesResponse,
} from "@/lib/missionControl/browserProfiles";
import {
  fetchBrowserSessions,
  type BrowserSessionsResponse,
} from "@/lib/missionControl/browserSessions";
import { emptyActionsGrouped, type ActionsGrouped } from "@/lib/missionControl/actions";
import { emptyJobsGrouped, type JobsGrouped } from "@/lib/missionControl/trackedJobs";
import { formatMcPanelError } from "@/lib/missionControl/panelError";
import {
  normalizeBrowserCapability,
  type BrowserCapabilityViewModel,
} from "@/lib/settings/browserCapability";
import {
  fetchConnections,
  type ProviderConnection,
} from "@/lib/missionControl/connectionsApi";
import {
  fetchConnectionsCatalog,
  type ConnectionsCatalogResponse,
} from "@/lib/missionControl/connectionsCatalog";
import {
  normalizeProviderSettings,
  type ProviderSettingsViewModel,
} from "@/lib/settings/providerSettings";
import {
  MISSION_CONTROL_SCROLL_MAIN_ATTR,
  MISSION_CONTROL_SCROLL_ROOT_ATTR,
  missionControlAppShellStyle,
  missionControlContentCanvasStyle,
  missionControlMainColumnStyle,
  missionControlScrollMainStyle,
  mcPanelSectionStyle,
  mcColors,
} from "@/lib/missionControl/layout";
import {
  fetchAgents,
  type AgentArtifact,
  type AgentSpec,
  type CoordinationEvent,
} from "@/lib/missionControl/agentsApi";
import {
  fetchWorkspaces,
  type EngineeringMemory,
  type WorkspaceArtifact,
  type WorkspaceRecord,
} from "@/lib/missionControl/localWorkspaceApi";
import {
  MISSION_CONTROL_VIEWS,
  viewDataGroup,
  type MissionControlDataGroup,
  type MissionControlView,
} from "@/lib/missionControl/views";
import {
  domainForView,
  type NavigationContext,
  type NavigationDomainId,
} from "@/lib/missionControl/sidebarNavigation";
import { suggestExpandedDomain } from "@/lib/missionControl/sidebarIntelligence";
import { computeCognitiveSanctuary } from "@/lib/missionControl/cognitiveSanctuary";
import { rhythmClassNames } from "@/lib/missionControl/livingRhythm";
import { useMissionControlTheme } from "@/lib/missionControl/theme";
import {
  loadExpandedDomain,
  loadFocusMode,
  loadNavMode,
  loadQuietMode,
  saveExpandedDomain,
  saveFocusMode,
  saveNavMode,
  saveQuietMode,
} from "@/lib/missionControl/sidebarPreferences";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";
import {
  isFlatNavReachableView,
  isNavVisibleInMode,
} from "@/lib/missionControl/flatNavigation";
import { useAuthScope } from "@/lib/auth/AuthScopeContext";
import { OnboardingTour } from "@/components/onboarding/OnboardingTour";
import { TOUR_ANCHORS } from "@/lib/onboarding/walkthrough";

type SettingsLoadState = "idle" | "loading" | "loaded" | "error";

function JsonBlock({ data }: { data: unknown }) {
  return (
    <pre
      style={{
        margin: 0,
        padding: 12,
        borderRadius: 12,
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.08)",
        fontSize: 12,
        lineHeight: 1.5,
        overflow: "auto",
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}

function buildNavigationContext(tracked: JobsGrouped): NavigationContext {
  const pending = [...tracked.queued, ...tracked.running];
  const hasPreflights = pending.some((j) => j.job_type.toLowerCase().includes("preflight"));
  return {
    hasActiveJobs: hasActiveTrackedJobs(tracked),
    hasActivePreflights: hasPreflights,
    hasAnomalies: tracked.failed.length > 0,
    replayIntegrityDegraded: true,
    pendingRecommendations: pending.length > 0 ? Math.min(pending.length, 9) : undefined,
  };
}

export function MissionControlShell() {
  const { colors, resolvedTheme, accessibilityMode, reducedMotion } = useMissionControlTheme();
  const { session, email, authEnabled } = useAuthScope();
  const [view, setView] = useState<MissionControlView>("overview");
  const [replayDeepLink, setReplayDeepLink] = useState<ReplayDeepLinkTarget | null>(null);
  const [navMode, setNavMode] = useState<MissionControlMode>("operator");
  const [tourActiveAnchor, setTourActiveAnchor] = useState<string | undefined>(undefined);
  const [expandedDomain, setExpandedDomain] = useState<NavigationDomainId | null>(null);
  const [quietMode, setQuietMode] = useState(false);
  const [focusMode, setFocusMode] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [panelError, setPanelError] = useState("");
  const [runtime, setRuntime] = useState<unknown>(null);
  const [connectionsCatalog, setConnectionsCatalog] = useState<ConnectionsCatalogResponse | null>(null);
  const [jobsActions, setJobsActions] = useState<ActionsGrouped>(emptyActionsGrouped());
  const [trackedJobs, setTrackedJobs] = useState<JobsGrouped>(emptyJobsGrouped());
  const [deploymentSettings, setDeploymentSettings] = useState<unknown>(null);
  const [providerVm, setProviderVm] = useState<ProviderSettingsViewModel | null>(null);
  const [browserVm, setBrowserVm] = useState<BrowserCapabilityViewModel | null>(null);
  const [browserSessions, setBrowserSessions] = useState<BrowserSessionsResponse | null>(null);
  const [browserProfiles, setBrowserProfiles] = useState<BrowserProfilesResponse | null>(null);
  const [browserEvidence, setBrowserEvidence] = useState<BrowserEvidenceArtifact[]>([]);
  const [browserEvidenceAudit, setBrowserEvidenceAudit] = useState<BrowserEvidenceAuditEvent[]>([]);
  const [arbiterAudit, setArbiterAudit] = useState<Record<string, unknown>[]>([]);
  const [arbiterDeepLink, setArbiterDeepLink] = useState<string | null>(null);
  const [researchArtifacts, setResearchArtifacts] = useState<ResearchArtifact[]>([]);
  const [providerConnections, setProviderConnections] = useState<Record<string, ProviderConnection | null>>({});
  const [workspaces, setWorkspaces] = useState<WorkspaceRecord[]>([]);
  const [workspaceHosted, setWorkspaceHosted] = useState(false);
  const [workspaceArtifacts, setWorkspaceArtifacts] = useState<WorkspaceArtifact[]>([]);
  const [engineeringMemory, setEngineeringMemory] = useState<EngineeringMemory>({ events: [] });
  const [agents, setAgents] = useState<AgentSpec[]>([]);
  const [agentArtifacts, setAgentArtifacts] = useState<AgentArtifact[]>([]);
  const [coordinationEvents, setCoordinationEvents] = useState<CoordinationEvent[]>([]);
  const [settingsState, setSettingsState] = useState<SettingsLoadState>("idle");
  const [loadedGroups, setLoadedGroups] = useState<Set<MissionControlDataGroup>>(new Set());
  const [pendingApprovalCount, setPendingApprovalCount] = useState(0);
  const [navPrefsHydrated, setNavPrefsHydrated] = useState(false);
  const savedDomainRef = useRef<NavigationDomainId | null | "unset">("unset");

  useEffect(() => {
    const saved = loadExpandedDomain();
    savedDomainRef.current = saved;
    setNavMode(loadNavMode());
    setExpandedDomain(saved);
    setQuietMode(loadQuietMode());
    setFocusMode(loadFocusMode());
    setNavPrefsHydrated(true);
  }, []);

  useEffect(() => {
    saveNavMode(navMode);
  }, [navMode]);

  // Keep the surface honest with the chosen mode: if the active view is a known
  // nav destination that this mode hides, fall back to Home (visible in every
  // mode) so the user is never stranded on a panel the mode claims not to show.
  useEffect(() => {
    if (!navPrefsHydrated) return;
    if (isFlatNavReachableView(view) && !isNavVisibleInMode(view, navMode)) {
      setView("overview");
    }
  }, [navMode, view, navPrefsHydrated]);

  useEffect(() => {
    saveExpandedDomain(expandedDomain);
  }, [expandedDomain]);

  useEffect(() => {
    saveQuietMode(quietMode);
  }, [quietMode]);

  useEffect(() => {
    saveFocusMode(focusMode);
  }, [focusMode]);

  useEffect(() => {
    const domain = domainForView(view);
    if (domain !== "overview") {
      setExpandedDomain(domain);
    }
  }, [view]);

  const navigationContext = buildNavigationContext(trackedJobs);

  const cognitiveSanctuary = useMemo(
    () =>
      computeCognitiveSanctuary(navigationContext, {
        mode: navMode,
        quietMode,
        focusMode,
        recentlyResolved: false,
        resolvedTheme,
        accessibilityMode,
      }),
    [navigationContext, navMode, quietMode, focusMode, resolvedTheme, accessibilityMode],
  );
  const operationalConsciousness = cognitiveSanctuary.ops;

  useEffect(() => {
    if (!navPrefsHydrated || savedDomainRef.current) return;
    if (view !== "overview" || expandedDomain) return;
    const suggested = suggestExpandedDomain(navigationContext);
    if (suggested) setExpandedDomain(suggested);
  }, [navigationContext, navPrefsHydrated, view, expandedDomain]);

  useEffect(() => {
    const url = readOperatorUrlState();
    if (url.view && (MISSION_CONTROL_VIEWS as readonly string[]).includes(url.view)) {
      setView(url.view as MissionControlView);
    }
    if (url.view === "mission-job-replay" && (url.link || url.stepIndex != null || url.jobId)) {
      setReplayDeepLink({
        link: url.link,
        linkRef: url.linkRef,
        linkKey: url.linkKey,
        stepIndex: url.stepIndex,
        jobId: url.jobId,
      });
    }
  }, []);

  // Surface arbiter judgments in the global Audit Logs view (where operators instinctively
  // look), alongside the browser-evidence trail.
  useEffect(() => {
    if (view !== "audit-logs") return;
    void fetchArbiterSessions(25).then((d) => setArbiterAudit(d.sessions ?? []));
  }, [view]);

  const openReplayDeepLink = useCallback((target: ReplayDeepLinkTarget) => {
    setReplayDeepLink(target);
    setView("mission-job-replay");
    setMobileNavOpen(false);
    writeOperatorUrlState(buildReplayNavigationTarget(target));
  }, []);

  const handleNavigate = useCallback((next: MissionControlView) => {
    setView(next);
    setMobileNavOpen(false);
    writeOperatorUrlState({ view: next });
  }, []);

  const loadGroup = useCallback(async (group: MissionControlDataGroup) => {
    setLoading(true);
    setPanelError("");
    try {
      if (group === "overview") {
        const [runtimeData, catalog, inbox] = await Promise.all([
          swrFetch("mc:runtime-status", () => fetchRuntimeStatus(), {
            ttlMs: 25_000,
            onRevalidate: (d) => setRuntime(d),
          }),
          swrFetch("mc:connections-catalog", () => fetchConnectionsCatalog(), {
            ttlMs: 25_000,
            onRevalidate: (d) => setConnectionsCatalog(d),
          }),
          swrFetch("mc:approval-inbox", () => fetchMissionControlApprovalInbox("operator"), {
            ttlMs: 15_000,
            onRevalidate: (d) => setPendingApprovalCount(d.summary?.total_pending ?? 0),
          }),
        ]);
        setRuntime(runtimeData);
        setConnectionsCatalog(catalog);
        setPendingApprovalCount(inbox.summary?.total_pending ?? 0);
      } else if (group === "browser") {
        const [sessions, profiles, evidence, audit, research] = await Promise.all([
          fetchBrowserSessions(),
          fetchBrowserProfiles(),
          fetchBrowserEvidenceArtifacts(),
          fetchBrowserEvidenceAudit(),
          fetchResearchArtifacts(),
        ]);
        setBrowserSessions(sessions);
        setBrowserProfiles(profiles);
        setBrowserEvidence(evidence.artifacts ?? []);
        setBrowserEvidenceAudit(audit.events ?? []);
        setResearchArtifacts(research.artifacts ?? []);
      } else if (group === "jobs") {
        const [actionsData, trackedData] = await Promise.all([
          fetchActionsGrouped(),
          fetchTrackedJobs(),
        ]);
        setJobsActions(actionsData.actions ?? emptyActionsGrouped());
        setTrackedJobs(trackedData.grouped ?? emptyJobsGrouped());
      } else if (group === "engineering") {
        const data = await fetchWorkspaces();
        setWorkspaces(data.workspaces ?? []);
        setWorkspaceHosted(Boolean(data.hosted));
        setWorkspaceArtifacts(data.artifacts ?? []);
        setEngineeringMemory(data.engineering_memory ?? { events: [] });
      } else if (group === "agents") {
        const data = await fetchAgents();
        setAgents(data.agents ?? []);
        setAgentArtifacts(data.artifacts ?? []);
        setCoordinationEvents(data.coordination_memory?.coordination_events ?? []);
      } else if (group === "settings") {
        setSettingsState("loading");
        setProviderVm(null);
        setBrowserVm(null);
        setDeploymentSettings(null);

        const [summaryResult, providerResult, connectionsResult] = await Promise.allSettled([
          fetchMcSettings(),
          fetchProviderReadiness(),
          fetchConnections(),
        ]);

        if (summaryResult.status === "fulfilled") {
          const summary = summaryResult.value as {
            browser_capability?: unknown;
            browser_automation_enabled?: boolean;
          };
          setDeploymentSettings(summaryResult.value);
          setBrowserVm(normalizeBrowserCapability(summary.browser_capability ?? summary));
        } else if (providerResult.status === "fulfilled") {
          try {
            const { fetchBrowserStatus } = await import("@/lib/missionControl/browserSessions");
            setBrowserVm(normalizeBrowserCapability(await fetchBrowserStatus()));
          } catch {
            setBrowserVm(
              normalizeBrowserCapability({
                enabled: true,
                execution_ready: false,
                user_message: "Browser diagnostics could not load.",
              }),
            );
          }
        }

        if (connectionsResult.status === "fulfilled") {
          const providers = connectionsResult.value.providers ?? {};
          setProviderConnections({
            vercel: providers.vercel ?? null,
            railway: providers.railway ?? null,
            github: providers.github ?? null,
          });
        } else {
          setProviderConnections({});
        }

        if (providerResult.status === "fulfilled") {
          setProviderVm(normalizeProviderSettings(providerResult.value));
          setSettingsState("loaded");
        } else {
          setProviderVm(normalizeProviderSettings(undefined));
          setSettingsState("error");
          setPanelError("Provider readiness is unavailable right now. Chat remains available.");
        }

        if (summaryResult.status === "rejected" && providerResult.status === "rejected") {
          setPanelError(formatMcPanelError("Settings panels could not load."));
        }
      }
      setLoadedGroups((prev) => new Set(prev).add(group));
    } catch (e) {
      setPanelError(formatMcPanelError(e instanceof Error ? e.message : "Load failed"));
      if (group === "settings") {
        setProviderVm(normalizeProviderSettings(undefined));
        setSettingsState("error");
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const group = viewDataGroup(view);
    void loadGroup(group);
  }, [view, loadGroup]);

  useEffect(() => {
    if (!loadedGroups.has("jobs")) {
      void loadGroup("jobs");
    }
  }, [loadedGroups, loadGroup]);

  const refreshAll = useCallback(async () => {
    setLoadedGroups(new Set());
    await loadGroup(viewDataGroup(view));
  }, [view, loadGroup]);

  const refreshJobs = useCallback(() => {
    void loadGroup("jobs");
  }, [loadGroup]);

  const refreshBrowser = useCallback(() => {
    void loadGroup("browser");
  }, [loadGroup]);

  const refreshSettings = useCallback(() => {
    void loadGroup("settings");
  }, [loadGroup]);

  const refreshEngineering = useCallback(() => {
    void loadGroup("engineering");
  }, [loadGroup]);

  const refreshAgents = useCallback(() => {
    void loadGroup("agents");
  }, [loadGroup]);

  const engineeringPanel = (
    <LocalWorkspacesPanel
      view={view}
      hosted={workspaceHosted}
      workspaces={workspaces}
      artifacts={workspaceArtifacts}
      engineeringMemory={engineeringMemory}
      onRefresh={refreshEngineering}
    />
  );

  const multiAgentPanel = (
    <MultiAgentPanel
      view={view}
      agents={agents}
      artifacts={agentArtifacts}
      events={coordinationEvents}
      onRefresh={refreshAgents}
    />
  );

  const hasActiveJobs = viewDataGroup(view) === "jobs" && hasActiveTrackedJobs(trackedJobs);

  useEffect(() => {
    if (!hasActiveJobs) return;
    let timer: number | null = null;

    const tick = () => {
      if (document.visibilityState !== "visible") return;
      void loadGroup("jobs");
    };

    const schedule = () => {
      if (timer !== null) window.clearInterval(timer);
      if (document.visibilityState !== "visible") return;
      timer = window.setInterval(tick, 3000);
    };

    tick();
    schedule();

    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        tick();
        schedule();
      } else if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
    };

    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      if (timer !== null) window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [hasActiveJobs, loadGroup]);

  const showSettingsPanel = settingsState !== "loading" && loadedGroups.has("settings");
  const showProviderPanel = showSettingsPanel && providerVm != null;
  const showBrowserPanel = showSettingsPanel && browserVm != null;

  const renderView = () => {
    switch (view) {
      case "cross-lane-operations":
        return <CrossLaneOperationsPanel operatorMode={navMode} onOpenReplayDeepLink={openReplayDeepLink} />;
      case "pilot-validation-trust-board":
        return <PilotValidationTrustBoardPanel sessionId="operator" />;
      case "dogfood-pilot-chain":
        return <DogfoodPilotChainPanel sessionId="operator" />;
      case "multi-repo-pilot-program":
        return <MultiRepoPilotProgramPanel sessionId="operator" />;
      case "approval-inbox":
        return <ApprovalInboxPanel operatorMode={navMode} onOpenReplayDeepLink={openReplayDeepLink} />;
      case "mission-job-replay":
        return (
          <JobReplayPanel
            operatorMode={navMode}
            deepLinkTarget={replayDeepLink}
            onDeepLinkConsumed={() => setReplayDeepLink(null)}
          />
        );
      case "overview":
        return (
          <SimpleOverviewPanel
            catalog={connectionsCatalog}
            onNavigate={handleNavigate}
            pendingApprovals={pendingApprovalCount}
          />
        );
      case "workflow-workspaces":
        return <WorkflowHubPanel surfaceId="workspaces" onNavigate={handleNavigate} mode={navMode} />;
      case "workflow-operations":
        return <WorkflowHubPanel surfaceId="operations" onNavigate={handleNavigate} mode={navMode} />;
      case "workflow-infrastructure":
        return <WorkflowHubPanel surfaceId="infrastructure" onNavigate={handleNavigate} mode={navMode} />;
      case "workflow-intelligence":
        return <WorkflowHubPanel surfaceId="intelligence" onNavigate={handleNavigate} mode={navMode} />;
      case "workflow-settings":
        return <WorkflowHubPanel surfaceId="settings" onNavigate={handleNavigate} mode={navMode} />;
      case "observability":
        return (
          <>
            <ConnectionsHealthOverview catalog={connectionsCatalog} />
            <SloPanel />
            <JobTraceReplayPanel sessionId="default" />
            {runtime != null && (
              <section style={{ ...mcPanelSectionStyle, marginTop: 16 }}>
                <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>Runtime observability</h2>
                <JsonBlock data={runtime} />
              </section>
            )}
          </>
        );
      case "activity-feed":
        return (
          <>
            <TelegramSessionsPanel />
            {runtime != null && (
              <details style={{ marginTop: 16 }}>
                <summary style={{ cursor: "pointer", fontSize: 12, color: mcColors.textMuted }}>
                  System activity snapshot
                </summary>
                <div style={{ marginTop: 8 }}>
                  <JsonBlock data={runtime} />
                </div>
              </details>
            )}
          </>
        );
      case "runtime-actions":
        return <RuntimeActionsPanel actions={jobsActions} jobs={trackedJobs} onRefresh={refreshJobs} />;
      case "tracked-work":
        return <JobsTrackedWorkPanel jobs={trackedJobs} onRefresh={refreshJobs} mode="tracked" />;
      case "operation-preflights":
        return <JobsTrackedWorkPanel jobs={trackedJobs} onRefresh={refreshJobs} mode="preflights" />;
      case "mutation-audit":
        return <MutationAuditPanel jobs={trackedJobs} />;
      case "agent-orchestration":
        return (
          <AgentOrchestrationPanel
            agents={agents}
            artifacts={agentArtifacts}
            events={coordinationEvents}
            parentSessionId="all"
            onRefresh={refreshAgents}
          />
        );
      case "deep-research":
        return <DeepResearchPanel />;
      case "evidence-gallery":
        return (
          <BrowserEvidenceGalleryPanel
            artifacts={browserEvidence}
            onRefresh={refreshBrowser}
          />
        );
      case "research-library":
        return <ResearchLibraryPanel />;
      case "blind-model-eval":
        return <BlindModelEvalPanel />;
      case "arbiter-panel":
        return <ArbiterPanel initialSessionId={arbiterDeepLink} />;
      case "monitors":
        return <MonitorsPanel />;
      case "daily-digest":
        return <DailyDigestPanel />;
      case "memory-viewer":
        return <MemoryViewerPanel />;
      case "proactive-suggestions":
        return <ProactiveSuggestionsPanel />;
      case "agent-comms":
        return <AgentCommsPanel />;
      case "channel-tool-policy":
        return <ChannelToolPolicyPanel />;
      case "cron-governed-jobs":
        return <CronGovernedJobsPanel />;
      case "proactive-automation":
        return <ProactiveAutomationPanel />;
      case "governed-sandbox":
        return <GovernedSandboxPanel />;
      case "mcp-bridge":
        return <McpBridgePanel />;
      case "active-agents":
      case "agent-timelines":
      case "coordination-graph":
      case "evidence-merge":
      case "operational-intelligence":
      case "operational-replay":
      case "evidence-graph":
      case "engineering-proposals":
      case "agent-evidence":
      case "agent-policies":
      case "delegated-tasks":
        return multiAgentPanel;
      case "subagent-sessions":
        return <SubagentSessionsPanel parentSessionId="operator" onRefresh={refreshAgents} />;
      case "engineering-execution":
      case "sandbox-executions":
      case "validation-center":
      case "diff-explorer":
      case "pr-drafts-center":
      case "rollback-snapshots":
      case "engineering-audit":
      case "operational-reality":
        return <EngineeringExecutionPanel view={view} />;
      case "cross-provider-correlation":
        return <CrossProviderCorrelationPanel />;
      case "operational-anomalies":
      case "operational-drift":
      case "deployment-stability":
      case "workflow-health":
      case "dependency-risk":
      case "recommendation-queue":
      case "telemetry-freshness":
      case "intelligence-replay":
        return <OperationalIntelligencePanel view={view} />;
      case "credential-center":
        return showSettingsPanel ? (
          <>
            <ProviderCredentialCenter />
            <GovernanceKillSwitchPanel />
          </>
        ) : (
          <p style={{ color: mcColors.textMuted }}>Loading…</p>
        );
      case "provider-inventory":
        return showSettingsPanel ? (
          <ProviderCatalog
            providerConnections={providerConnections}
            onRefresh={refreshSettings}
            onNavigateView={(viewId) => handleNavigate(viewId as MissionControlView)}
          />
        ) : (
          <p style={{ color: mcColors.textMuted }}>Loading…</p>
        );
      case "integrations":
        return showSettingsPanel ? (
          <ProviderCatalog providerConnections={providerConnections} onRefresh={refreshSettings} mode="channels" />
        ) : (
          <p style={{ color: mcColors.textMuted }}>Loading…</p>
        );
      case "browser-evidence":
        return (
          <BrowserEvidencePanel
            artifacts={browserEvidence}
            auditEvents={browserEvidenceAudit}
            onRefresh={refreshBrowser}
          />
        );
      case "web-intelligence":
        return <WebIntelligencePanel artifacts={researchArtifacts} onRefresh={refreshBrowser} />;
      case "research-intelligence":
        return <ResearchIntelligencePanel artifacts={researchArtifacts} onRefresh={refreshBrowser} />;
      case "browser-profiles":
        return (
          <>
            <BrowserProfilesPanel data={browserProfiles} onRefresh={refreshBrowser} />
            <BrowserSessionsPanel data={browserSessions} onRefresh={refreshBrowser} />
          </>
        );
      case "audit-logs":
        return (
          <section style={mcPanelSectionStyle}>
            <h2 style={{ margin: "0 0 8px", fontSize: 18, fontWeight: 600 }}>Audit logs</h2>

            <h3 style={{ margin: "4px 0 8px", fontSize: 14, fontWeight: 600, color: mcColors.text }}>
              Arbiter judgments
            </h3>
            <p style={{ margin: "0 0 10px", fontSize: 13, color: mcColors.textMuted }}>
              Multi-model consensus runs — agreement score, winner, and status. Open the Arbiter
              panel for the full scorecard and debate timeline.
            </p>
            {arbiterAudit.length === 0 ? (
              <p style={{ color: mcColors.textMuted, fontSize: 13, marginBottom: 20 }}>
                No arbiter runs yet.
              </p>
            ) : (
              <ul style={{ margin: "0 0 24px", padding: 0, listStyle: "none", fontSize: 13 }}>
                {arbiterAudit.slice(0, 25).map((s, i) => {
                  const consensus = s.consensus as Record<string, unknown> | null;
                  const reached = Boolean(consensus?.reached);
                  const score = Math.round((Number(consensus?.agreement_score) || 0) * 100);
                  const debate = Number(s.debate_round_count) || 0;
                  return (
                    <li key={String(s.session_id ?? i)} style={{ marginBottom: 8 }}>
                      <button
                        type="button"
                        onClick={() => {
                          setArbiterDeepLink(String(s.session_id ?? ""));
                          handleNavigate("arbiter-panel");
                        }}
                        style={{
                          width: "100%",
                          textAlign: "left",
                          padding: "10px 12px",
                          borderRadius: 10,
                          border: `1px solid ${reached ? "rgba(5,150,105,0.4)" : mcColors.borderSubtle}`,
                          background: "rgba(0,0,0,0.2)",
                          color: "inherit",
                          cursor: "pointer",
                        }}
                      >
                        <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
                          <span style={{ color: mcColors.text, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {String(s.prompt_preview ?? "(no prompt)").slice(0, 70)}
                          </span>
                          <span style={{ color: reached ? "#6ee7b7" : mcColors.textMuted, whiteSpace: "nowrap" }}>
                            {consensus ? (reached ? `✓ ${score}%` : `⚠ ${score}%`) : String(s.status ?? "—")}
                          </span>
                        </div>
                        <div style={{ color: mcColors.textDim, fontSize: 12, marginTop: 4 }}>
                          {String(s.status ?? "—")}
                          {debate > 0 ? ` · ${debate} debate round${debate > 1 ? "s" : ""}` : ""}
                          {" · "}
                          {s.duration_ms ? `${Math.round(Number(s.duration_ms) / 1000)}s` : "—"}
                        </div>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}

            <h3 style={{ margin: "4px 0 8px", fontSize: 14, fontWeight: 600, color: mcColors.text }}>
              Browser evidence
            </h3>
            <p style={{ margin: "0 0 12px", fontSize: 13, color: mcColors.textMuted }}>
              Browser evidence audit trail — governed capture events.
            </p>
            {browserEvidenceAudit.length === 0 ? (
              <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No audit events yet.</p>
            ) : (
              <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
                {browserEvidenceAudit.slice(0, 40).map((ev, i) => (
                  <li
                    key={`${ev.at}-${i}`}
                    style={{
                      padding: "10px 12px",
                      marginBottom: 8,
                      borderRadius: 10,
                      border: `1px solid ${mcColors.borderSubtle}`,
                      background: "rgba(0,0,0,0.2)",
                    }}
                  >
                    <div style={{ color: mcColors.text }}>{ev.action ?? "—"}</div>
                    <div style={{ color: mcColors.textDim, fontSize: 12, marginTop: 4 }}>
                      {ev.detail || "—"} · {ev.at ? new Date(ev.at * 1000).toLocaleString() : "—"}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        );
      case "system-health":
        return (
          <>
            {showSettingsPanel && deploymentSettings != null && (
              <WorkspaceDiagnosticsCard
                workspace={(deploymentSettings as { workspace?: object }).workspace as object}
                build={(deploymentSettings as { build?: object }).build as object}
              />
            )}
            {showBrowserPanel && browserVm != null && <BrowserCapabilityCard viewModel={browserVm} />}
          </>
        );
      case "tenant-onboarding":
        return <TenantOnboardingActivationPanel />;
      case "identity-access-hardening":
        return <IdentityAccessHardeningPanel />;
      case "users-roles":
        return <UsersRolesPanel />;
      case "platform-owner":
        return <PlatformOwnerPanel />;
      case "provider-connections":
        return <ProviderConnectionExperiencePanel />;
      case "channel-integration":
        return <ChannelIntegrationFoundationPanel />;
      case "billing-entitlements":
        return <BillingEntitlementsFoundationPanel />;
      case "customer-administration":
        return <CustomerAdministrationConsolePanel />;
      case "customer-audit-portal":
        return <CustomerUsageAuditPortalPanel />;
      case "payment-integration-readiness":
        return <PaymentIntegrationReadinessPanel />;
      case "saas-launch-readiness":
        return <SaasLaunchReadinessAssessmentPanel />;
      case "customer-support-success":
        return <CustomerSupportSuccessFoundationPanel />;
      case "public-product-experience":
        return <PublicProductExperiencePanel viewId="public-product-experience" title="Public Experience" />;
      case "public-capability-explorer":
        return <PublicProductExperiencePanel viewId="public-capability-explorer" title="Capability Explorer" />;
      case "public-trust-explorer":
        return <PublicProductExperiencePanel viewId="public-trust-explorer" title="Trust Explorer" />;
      case "public-product-tour":
        return <PublicProductExperiencePanel viewId="public-product-tour" title="Product Tour" />;
      case "public-customer-journey":
        return <PublicProductExperiencePanel viewId="public-customer-journey" title="Customer Journey" />;
      case "public-education-center":
        return <PublicProductExperiencePanel viewId="public-education-center" title="Education Center" />;
      case "beta-launch-program":
        return <LimitedBetaLaunchProgramPanel viewId="beta-launch-program" title="Beta Launch Program" />;
      case "beta-cohorts":
        return <LimitedBetaLaunchProgramPanel viewId="beta-cohorts" title="Beta Cohorts" />;
      case "beta-feedback":
        return <LimitedBetaLaunchProgramPanel viewId="beta-feedback" title="Beta Feedback" />;
      case "beta-success-metrics":
        return <LimitedBetaLaunchProgramPanel viewId="beta-success-metrics" title="Beta Success Metrics" />;
      case "beta-operations-dashboard":
        return (
          <LimitedBetaLaunchProgramPanel viewId="beta-operations-dashboard" title="Beta Operations Dashboard" />
        );
      case "launch-operations-center":
        return <LaunchOperationsCenterPanel viewId="launch-operations-center" title="Launch Operations Center" />;
      case "launch-dashboard":
        return <LaunchOperationsCenterPanel viewId="launch-dashboard" title="Launch Dashboard" />;
      case "launch-risks":
        return <LaunchOperationsCenterPanel viewId="launch-risks" title="Launch Risks" />;
      case "launch-blockers":
        return <LaunchOperationsCenterPanel viewId="launch-blockers" title="Launch Blockers" />;
      case "launch-evidence":
        return <LaunchOperationsCenterPanel viewId="launch-evidence" title="Launch Evidence" />;
      case "launch-beta-operations":
        return <LaunchOperationsCenterPanel viewId="beta-operations" title="Beta Operations" />;
      case "launch-customer-operations":
        return <LaunchOperationsCenterPanel viewId="customer-operations" title="Customer Operations" />;
      case "launch-readiness-freeze":
        return (
          <PublicLaunchReadinessFreezePanel viewId="launch-readiness-freeze" title="Launch Readiness Freeze" />
        );
      case "launch-baseline":
        return <PublicLaunchReadinessFreezePanel viewId="launch-baseline" title="Launch Baseline" />;
      case "launch-evidence-freeze":
        return (
          <PublicLaunchReadinessFreezePanel viewId="launch-evidence-freeze" title="Launch Evidence Freeze" />
        );
      case "launch-recommendation-freeze":
        return (
          <PublicLaunchReadinessFreezePanel
            viewId="launch-recommendation-freeze"
            title="Launch Recommendation Freeze"
          />
        );
      case "launch-freeze-blockers":
        return (
          <PublicLaunchReadinessFreezePanel viewId="launch-freeze-blockers" title="Launch Freeze Blockers" />
        );
      case "launch-freeze-risks":
        return <PublicLaunchReadinessFreezePanel viewId="launch-freeze-risks" title="Launch Freeze Risks" />;
      case "launch-decision-package":
        return <LaunchDecisionPackagePanel viewId="launch-decision-package" title="Launch Decision Package" />;
      case "launch-executive-summary":
        return <LaunchDecisionPackagePanel viewId="launch-executive-summary" title="Executive Summary" />;
      case "launch-recommendation-package":
        return (
          <LaunchDecisionPackagePanel viewId="launch-recommendation-package" title="Launch Recommendation" />
        );
      case "launch-decision-dashboard":
        return <LaunchDecisionPackagePanel viewId="launch-decision-dashboard" title="Decision Dashboard" />;
      case "launch-decision-history":
        return <LaunchDecisionPackagePanel viewId="launch-decision-history" title="Decision History" />;
      case "post-launch-operations":
        return (
          <PostLaunchOperationsBaselinePanel viewId="post-launch-operations" title="Post Launch Operations" />
        );
      case "post-launch-platform-health":
        return (
          <PostLaunchOperationsBaselinePanel viewId="post-launch-platform-health" title="Platform Health" />
        );
      case "post-launch-customer-health":
        return (
          <PostLaunchOperationsBaselinePanel viewId="post-launch-customer-health" title="Customer Health" />
        );
      case "post-launch-governance-health":
        return (
          <PostLaunchOperationsBaselinePanel
            viewId="post-launch-governance-health"
            title="Governance Health"
          />
        );
      case "post-launch-incident-health":
        return (
          <PostLaunchOperationsBaselinePanel viewId="post-launch-incident-health" title="Incident Health" />
        );
      case "post-launch-commercial-health":
        return (
          <PostLaunchOperationsBaselinePanel viewId="post-launch-commercial-health" title="Commercial Health" />
        );
      case "post-launch-operations-dashboard":
        return (
          <PostLaunchOperationsBaselinePanel
            viewId="post-launch-operations-dashboard"
            title="Operations Dashboard"
          />
        );
      case "settings":
        return (
          <>
            <RuntimeSettingsPanel />
            {showProviderPanel && <ProviderSettingsCard viewModel={providerVm} />}
            {showSettingsPanel && deploymentSettings != null && (
              <details style={{ marginTop: 8 }}>
                <summary style={{ cursor: "pointer", fontSize: 12, color: mcColors.textMuted }}>
                  Raw deployment settings
                </summary>
                <div style={{ marginTop: 8 }}>
                  <JsonBlock data={deploymentSettings} />
                </div>
              </details>
            )}
          </>
        );
      case "runtime-tunnel":
        return <RuntimeTunnelPanel />;
      case "research-config":
        return <ResearchConfigPanel />;
      case "local-workspaces":
      case "repo-diagnostics":
      case "architecture-maps":
      case "git-activity":
      case "dependency-health":
      case "test-intelligence":
      case "pr-proposals":
        return engineeringPanel;
      case "workspace-active":
      case "workspace-desktop":
      case "workspace-terminal":
      case "workspace-evidence":
      case "workspace-replay":
      case "workspace-files":
      case "workspace-sandbox":
      case "workspace-memory":
        return <WorkspaceOperationsPanel view={view} />;
      case "presence-feed":
      case "presence-attention":
      case "presence-timeline":
      case "presence-focus":
      case "presence-collaboration":
      case "presence-recommendations":
      case "presence-watch":
      case "presence-memory":
        return <PresenceOperationsPanel view={view} />;
      case "trust-authority":
      case "trust-replay":
      case "trust-governance":
      case "trust-confidence":
      case "trust-signal-quality":
      case "trust-correlation":
      case "trust-metrics":
      case "trust-recovery":
        return <TrustOperationsPanel view={view} />;
      case "truth-capability-matrix":
      case "truth-provider-readiness":
      case "truth-verification-coverage":
      case "truth-mutation-reliability":
      case "truth-operational-honesty":
      case "truth-runtime-validation":
      case "truth-reality-harness":
      case "truth-production-readiness":
        return <OperationalTruthPanel view={view} />;
      case "reliability-providers":
      case "reliability-deployment-verification":
      case "reliability-recovery-runtime":
      case "reliability-mutation-reconciliation":
      case "reliability-rollback-integrity":
      case "reliability-runtime-stabilization":
      case "reliability-operational-confidence":
      case "reliability-reality-validation":
        return <ProductionReliabilityPanel view={view} />;
      case "infra-container-intelligence":
      case "infra-kubernetes-runtime":
      case "infra-runtime-topology":
      case "infra-infrastructure-health":
      case "infra-resource-pressure":
      case "infra-drift-detection":
      case "infra-cluster-recovery":
      case "infra-infrastructure-truth":
        return <InfrastructureIntelligencePanel view={view} />;
      case "reliability-continuous-verification":
      case "reliability-recovery-orchestration":
      case "reliability-drift-intelligence":
      case "reliability-predictive-operations":
      case "reliability-production-confidence":
      case "reliability-reliability-memory":
      case "reliability-operational-trajectory":
      case "reliability-confidence-forecasting":
        return <OperationalReliabilityPanel view={view} />;
      case "synthesis-quality":
      case "synthesis-recommendations":
      case "synthesis-conversational-trust":
      case "synthesis-presentation-safety":
      case "synthesis-response-elegance":
      case "synthesis-human-trust":
      case "synthesis-recommendation-replay":
      case "synthesis-conversational-recovery":
        return <SynthesisIntelligencePanel view={view} />;
      case "conv-reliability":
      case "conv-recommendation-quality":
      case "conv-trust-calibration":
      case "conv-presentation-integrity":
      case "conv-interaction-elegance":
      case "conv-conversational-replay":
      case "conv-recommendation-intelligence":
      case "conv-human-trust-signals":
        return <ConversationalReliabilityPanel view={view} />;
      case "conv-convergence":
      case "conv-interaction-layers":
      case "conv-trust-maturity":
      case "conv-synthesis-consistency":
      case "conv-production-interaction":
      case "conv-maturity-profile":
      case "conv-surface-integrity":
      case "conv-trust-threshold":
        return <ConversationalConvergencePanel view={view} />;
      case "prod-deployment-truth":
      case "prod-rollback-integrity":
      case "prod-runtime-stabilization":
      case "prod-topology-recovery":
      case "prod-operational-decay":
      case "prod-production-qualification":
      case "prod-sustained-verification":
      case "prod-recovery-confidence":
        return <ProductionRealityPanel view={view} />;
      case "rt-reconciliation":
      case "rt-operational-patience":
      case "rt-runtime-decay":
      case "rt-sustained-verification":
      case "rt-recovery-truth":
      case "rt-replay-stability":
      case "rt-topology-alignment":
      case "rt-operational-windows":
        return <RuntimeTruthPanel view={view} />;
      case "rtc-runtime-truth":
      case "rtc-stability-windows":
      case "rtc-replay-convergence":
      case "rtc-dependency-stability":
      case "rtc-topology-truth":
      case "rtc-operational-decay":
      case "rtc-sustained-confidence":
      case "rtc-recovery-continuity":
        return <RuntimeTruthEvolutionPanel view={view} />;
      case "ccg-convergence-cognition":
      case "ccg-infrastructure-intuition":
      case "ccg-temporal-confidence":
      case "ccg-kubernetes-convergence":
      case "ccg-replay-continuity":
      case "ccg-long-tail-stability":
      case "ccg-operational-memory":
      case "ccg-runtime-trajectories":
        return <ConvergenceCognitionPanel view={view} />;
      case "rci-recovery-continuity":
      case "rci-temporal-trust":
      case "rci-infrastructure-convergence":
      case "rci-replay-persistence":
      case "rci-adaptive-verification":
      case "rci-long-tail-stability":
      case "rci-topology-resilience":
      case "rci-recovery-memory":
        return <RecoveryContinuityPanel view={view} />;
      case "rsc-operational-resilience":
      case "rsc-infrastructure-fragility":
      case "rsc-temporal-trust-evolution":
      case "rsc-kubernetes-resilience":
      case "rsc-replay-resilience":
      case "rsc-long-tail-stability":
      case "rsc-recovery-durability":
      case "rsc-operational-trajectories":
        return <ResilienceCognitionPanel view={view} />;
      case "ors-operational-resilience":
      case "ors-runtime-fragility":
      case "ors-sustained-trust":
      case "ors-kubernetes-durability":
      case "ors-replay-resilience":
      case "ors-long-tail-stability":
      case "ors-recovery-durability":
      case "ors-operational-trajectories":
        return <OperationalResiliencePanel view={view} />;
      case "poc-predictive-stability":
      case "poc-fragility-acceleration":
      case "poc-replay-forecasting":
      case "poc-topology-forecasting":
      case "poc-operational-fatigue":
      case "poc-stability-projection":
      case "poc-recovery-forecasting":
      case "poc-predictive-memory":
        return <PredictiveCognitionPanel view={view} />;
      case "rfi-runtime-fragility":
      case "rfi-degradation-acceleration":
      case "rfi-replay-erosion":
      case "rfi-topology-fragility":
      case "rfi-operational-fatigue":
      case "rfi-predictive-stability":
      case "rfi-recovery-fragility":
      case "rfi-fragility-memory":
        return <RuntimeFragilityPanel view={view} />;
      case "ltf-long-tail-forecasting":
      case "ltf-operational-survivability":
      case "ltf-replay-longevity":
      case "ltf-topology-sustainability":
      case "ltf-resilience-exhaustion":
      case "ltf-stability-endurance":
      case "ltf-autonomous-stability":
      case "ltf-forecasting-trajectories":
      case "ltf-forecasting-memory":
        return <LongTailForecastingPanel view={view} />;
      case "ltr-long-tail-cognition":
      case "ltr-runtime-survivability":
      case "ltr-operational-endurance":
      case "ltr-replay-continuity":
      case "ltr-topology-endurance":
      case "ltr-resilience-exhaustion":
      case "ltr-runtime-persistence":
      case "ltr-cognition-memory":
        return <LongTailRuntimePanel view={view} />;
      case "cog-operational-grounding":
      case "cog-continuity-reconstruction":
      case "cog-operational-context":
      case "cog-governance-restraint":
      case "cog-conversational-realism":
      case "cog-telegram-persistence":
      case "cog-partner-presence":
      case "cog-cross-surface-convergence":
      case "cog-live-operational-grounding":
      case "cog-durable-jobs":
      case "cog-durable-jobs-active":
      case "cog-durable-jobs-artifacts":
      case "cog-grounding-memory":
        if (view.startsWith("cog-durable-jobs")) {
          return <DurableJobsPanel view={view} />;
        }
        return <ConversationalGroundingPanel view={view} />;
      case "enterprise-doctor":
      case "enterprise-setup-wizard":
      case "enterprise-config":
      case "enterprise-health":
      case "enterprise-demo":
        return <EnterpriseOperationsPanel view={view} />;
      case "production-deployment":
      case "production-cluster":
      case "production-orgs":
      case "production-plugins":
      case "production-observability":
      case "production-metering":
      case "production-upgrade":
      case "production-security":
        return <ProductionInfrastructurePanel view={view} />;
      case "human-overview":
      case "human-relational":
      case "human-voice":
      case "human-channels":
      case "human-life":
      case "human-actions":
      case "human-ambient":
      case "human-collaboration":
      case "human-trust":
      case "human-marketplace":
      case "human-mobile":
      case "human-living":
      case "human-live-presence":
      case "human-conversation":
      case "human-copilot":
      case "human-personal":
      case "human-explainability":
      case "human-thinking":
      case "human-multimodal-voice":
      case "human-continuity":
      case "human-trust-controls":
        return <HumanCenteredPanel view={view} />;
      case "integrity-routes":
      case "integrity-features":
      case "integrity-ui-alignment":
      case "integrity-orphans":
      case "integrity-diagnostics":
        return <RuntimeIntegrityPanel view={view} />;
      case "presence-attention-quality":
      case "presence-interruption-budget":
      case "presence-continuity-accuracy":
      case "presence-operational-narrative":
      case "presence-calm-intelligence":
      case "presence-trust-signals":
      case "presence-collaboration-quality":
        return <PresenceQualityPanel view={view} />;
      case "companion-operational-reasoning":
      case "companion-investigation":
      case "companion-replay-intelligence":
      case "companion-emotional-realism":
      case "companion-attention-awareness":
      case "companion-narrative-evolution":
      case "companion-trust-retention":
        return <CompanionIntelligencePanel view={view} />;
      default:
        return null;
    }
  };

  const tourScope = email || (authEnabled ? "anon" : "local");
  const tourName = session?.user?.name?.trim() || email?.split("@")[0] || undefined;
  // Show to a signed-in user, or to anyone when auth is disabled (solo/local mode);
  // never on the logged-out screen (auth on but no email yet).
  const tourEnabled = authEnabled ? Boolean(email) : true;
  // Reveal the Advanced tray when the tour spotlights a panel that lives inside it.
  const forceAdvancedForTour = tourActiveAnchor === TOUR_ANCHORS.navAudit;

  return (
    <div
      style={{
        ...missionControlAppShellStyle,
        ...operationalConsciousness.cognition.partnership.intelligence.presence.environment.shellStyle,
        background: colors.shellGradient,
        color: colors.text,
      }}
      className={`mc-ambient-shell mc-cognitive-sanctuary ${cognitiveSanctuary.sanctuaryClassName} ${rhythmClassNames(operationalConsciousness.cognition.partnership.intelligence.presence.environment.rhythm)} ${reducedMotion ? "mc-reduced-motion" : ""}`}
      data-mc-theme={resolvedTheme}
      data-mc-a11y={accessibilityMode}
      data-mc-ambient={operationalConsciousness.cognition.partnership.intelligence.presence.environment.mood}
      data-mc-atmosphere={operationalConsciousness.cognition.partnership.intelligence.presence.environment.atmosphere}
      data-mc-rhythm={operationalConsciousness.cognition.partnership.intelligence.presence.environment.rhythm.tempo}
      data-mc-cognitive={operationalConsciousness.cognition.partnership.intelligence.presence.cognitive.loadLevel}
      data-mc-flow={operationalConsciousness.cognition.ambientFlow.flowState}
      data-mc-consciousness={operationalConsciousness.consciousness.consciousnessState}
      data-mc-sanctuary={cognitiveSanctuary.sanctuary.sanctuaryState}
      data-mc-serenity={cognitiveSanctuary.sanctuaryImmersion ? "true" : undefined}
      data-mc-deep-focus={cognitiveSanctuary.sanctuaryImmersion ? "true" : undefined}
      data-mc-whisper={cognitiveSanctuary.atmosphereLevel}
      data-mc-attention={cognitiveSanctuary.sanctuaryAttention}
      {...{ [MISSION_CONTROL_SCROLL_ROOT_ATTR]: "" }}
    >
      {mobileNavOpen ? (
        <button
          type="button"
          className="mc-mobile-nav-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}
      <MissionControlSidebar
        active={view}
        onNavigate={handleNavigate}
        mode={navMode}
        forceAdvancedOpen={forceAdvancedForTour}
        mobileOpen={mobileNavOpen}
        onCloseMobile={() => setMobileNavOpen(false)}
      />
      <div style={missionControlMainColumnStyle}>
        <MissionControlHeader
          activeView={view}
          onRefreshAll={() => void refreshAll()}
          refreshing={loading}
          onToggleMobileNav={() => setMobileNavOpen((v) => !v)}
          mode={navMode}
          onModeChange={setNavMode}
          quietMode={quietMode}
          onQuietModeChange={setQuietMode}
          focusMode={focusMode}
          onFocusModeChange={setFocusMode}
          mobileNavOpen={mobileNavOpen}
        />
        <GovernanceFastPathBanner />
        <main style={missionControlScrollMainStyle} {...{ [MISSION_CONTROL_SCROLL_MAIN_ATTR]: "" }}>
          <div style={missionControlContentCanvasStyle}>
            {panelError ? (
              <p style={{ color: mcColors.amber, fontSize: 13, marginBottom: 12 }} role="status">
                {panelError}
              </p>
            ) : null}
            {loading && !loadedGroups.has(viewDataGroup(view)) ? (
              <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading…</p>
            ) : null}
            {renderView()}
          </div>
        </main>
      </div>
      <OnboardingTour
        scope={tourScope}
        displayName={tourName}
        enabled={tourEnabled}
        onActiveAnchorChange={setTourActiveAnchor}
      />
    </div>
  );
}
