/** Phase 10.2.0 — Workflow-first Mission Control navigation (5–7 operational surfaces). */

import {
  SIDEBAR_SECTIONS,
  VIEW_LABELS,
  type MissionControlView,
  type SidebarSection,
} from "@/lib/missionControl/views";

export type WorkflowSurfaceId =
  | "workspaces"
  | "operations"
  | "infrastructure"
  | "intelligence"
  | "settings";

export type WorkflowPrimaryItem = {
  id: MissionControlView;
  label: string;
  hint: string;
};

export type WorkflowSurface = {
  id: WorkflowSurfaceId;
  label: string;
  description: string;
  hubView: MissionControlView;
  primaryItems: WorkflowPrimaryItem[];
  /** Legacy sidebar sections — advanced diagnostics only. */
  legacySectionTitles: string[];
};

export const WORKFLOW_HUB_VIEWS = [
  "workflow-workspaces",
  "workflow-operations",
  "workflow-infrastructure",
  "workflow-intelligence",
  "workflow-settings",
] as const;

export type WorkflowHubView = (typeof WORKFLOW_HUB_VIEWS)[number];

export const WORKFLOW_SURFACES: WorkflowSurface[] = [
  {
    id: "workspaces",
    label: "Workspaces",
    description: "Human and agent collaboration",
    hubView: "workflow-workspaces",
    primaryItems: [
      { id: "companion-investigation", label: "Active investigations", hint: "What agents are exploring" },
      { id: "agent-orchestration", label: "Orchestration", hint: "Agent pipeline and session threads" },
      { id: "workspace-active", label: "Workspaces", hint: "Active operational workspaces" },
      { id: "cog-durable-jobs-active", label: "Background jobs", hint: "Durable agent jobs in flight" },
      { id: "engineering-execution", label: "Engineering execution", hint: "Preflights and deliverables" },
    ],
    legacySectionTitles: [
      "Multi-Agent Runtime",
      "Workspace Operations",
      "Engineering",
      "Runtime Integrity",
      "Human-Centered OS",
      "Living Intelligence",
      "Operational Presence",
      "Conversational Grounding (11.7)",
    ],
  },
  {
    id: "operations",
    label: "Operations",
    description: "Live runtime awareness",
    hubView: "workflow-operations",
    primaryItems: [
      { id: "reliability-recovery-orchestration", label: "Recovery monitoring", hint: "Did recovery hold?" },
      { id: "operational-anomalies", label: "Active issues", hint: "What needs attention now" },
      { id: "deployment-stability", label: "Deployments", hint: "Release and deployment health" },
      { id: "reliability-providers", label: "Provider status", hint: "Connectivity and readiness" },
      { id: "runtime-actions", label: "Runtime actions", hint: "Operational actions in flight" },
      { id: "recommendation-queue", label: "Recommendations", hint: "Prioritized guidance" },
    ],
    legacySectionTitles: [
      "Runtime",
      "Operational Intelligence",
      "Production Reliability",
      "Operational Reliability",
      "Operational Truth",
      "Production Reality",
      "Runtime Truth",
      "Runtime Truth Evolution",
      "Convergence Cognition",
      "Recovery Continuity",
      "Resilience Cognition",
      "Operational Resilience (11.6.3)",
      "Predictive Cognition",
      "Runtime Fragility (11.6.4)",
      "Long-Tail Forecasting (11.4.7)",
      "Long-Tail Runtime Cognition (11.6.5)",
    ],
  },
  {
    id: "infrastructure",
    label: "Infrastructure",
    description: "Advanced operational visibility",
    hubView: "workflow-infrastructure",
    primaryItems: [
      { id: "infra-container-intelligence", label: "Containers", hint: "Docker and container runtime" },
      { id: "infra-kubernetes-runtime", label: "Kubernetes", hint: "Cluster runtime state" },
      { id: "infra-runtime-topology", label: "Topology", hint: "Runtime topology map" },
      { id: "infra-infrastructure-health", label: "Cluster health", hint: "Infrastructure diagnostics" },
      { id: "production-deployment", label: "Production topology", hint: "Deployment topology overview" },
    ],
    legacySectionTitles: ["Infrastructure Intelligence", "Production Infrastructure", "Browser"],
  },
  {
    id: "intelligence",
    label: "Intelligence",
    description: "Explainability and reasoning",
    hubView: "workflow-intelligence",
    primaryItems: [
      { id: "companion-operational-reasoning", label: "Operational reasoning", hint: "Why the system believes this" },
      { id: "companion-replay-intelligence", label: "Replay continuity", hint: "Long-session continuity" },
      { id: "trust-metrics", label: "Trust and confidence", hint: "Operational trust signals" },
      { id: "synthesis-recommendations", label: "Synthesis", hint: "Recommendation quality" },
      { id: "human-explainability", label: "Explainability", hint: "Human-readable reasoning" },
      { id: "conv-reliability", label: "Conversational quality", hint: "Interaction reliability" },
      { id: "arbiter-panel", label: "Multi-model arbiter", hint: "Parallel dispatch, critique, and consensus across models" },
    ],
    legacySectionTitles: [
      "Operational Trust",
      "Synthesis Intelligence",
      "Conversational Reliability",
      "Interaction Convergence",
      "Presence Quality",
      "Companion Intelligence",
    ],
  },
  {
    id: "settings",
    label: "Settings",
    description: "Administration and system management",
    hubView: "workflow-settings",
    primaryItems: [
      { id: "settings", label: "Settings", hint: "System preferences" },
      { id: "credential-center", label: "Credentials", hint: "Provider credentials" },
      { id: "integrations", label: "Integrations", hint: "Connected services" },
      { id: "production-orgs", label: "Organizations", hint: "Org and tenant setup" },
      { id: "enterprise-setup-wizard", label: "Setup wizard", hint: "Onboarding and readiness" },
      { id: "system-health", label: "System health", hint: "Platform health summary" },
    ],
    legacySectionTitles: ["Providers", "System", "Enterprise Readiness"],
  },
];

const sectionByTitle = new Map<string, SidebarSection>(
  SIDEBAR_SECTIONS.map((section) => [section.title, section]),
);

const primaryViewIds = new Set(
  WORKFLOW_SURFACES.flatMap((surface) => surface.primaryItems.map((item) => item.id)),
);

/** Views that belong to a workflow surface (including hub and primary items). */
export function workflowForView(view: MissionControlView): WorkflowSurfaceId | "overview" {
  if (view === "overview" || view === "observability" || view === "activity-feed") {
    return "overview";
  }

  for (const surface of WORKFLOW_SURFACES) {
    if (surface.hubView === view) return surface.id;
    if (surface.primaryItems.some((item) => item.id === view)) return surface.id;
    const sections = legacySectionsForSurface(surface);
    if (sections.some((section) => section.items.some((item) => item.id === view))) {
      return surface.id;
    }
  }

  return "operations";
}

export function surfaceForView(view: MissionControlView): WorkflowSurface | null {
  const id = workflowForView(view);
  if (id === "overview") return null;
  return WORKFLOW_SURFACES.find((surface) => surface.id === id) ?? null;
}

export function legacySectionsForSurface(surface: WorkflowSurface): SidebarSection[] {
  return surface.legacySectionTitles
    .map((title) => sectionByTitle.get(title))
    .filter((section): section is SidebarSection => Boolean(section));
}

export function primaryItemsForSurface(
  surface: WorkflowSurface,
  mode: "executive" | "operator" | "deep-engineering",
): WorkflowPrimaryItem[] {
  const items = surface.primaryItems.filter((item) => isViewVisibleInWorkflow(item.id, mode));
  if (mode === "executive") return items.slice(0, 3);
  return items;
}

export function isPrimaryWorkflowView(view: MissionControlView): boolean {
  return primaryViewIds.has(view);
}

export function isWorkflowHubView(view: MissionControlView): view is WorkflowHubView {
  return WORKFLOW_HUB_VIEWS.includes(view as WorkflowHubView);
}

export function hubViewForSurface(surfaceId: WorkflowSurfaceId): MissionControlView {
  return WORKFLOW_SURFACES.find((surface) => surface.id === surfaceId)?.hubView ?? "overview";
}

export function labelForView(view: MissionControlView): string {
  if (view.startsWith("workflow-")) {
    const surface = WORKFLOW_SURFACES.find((item) => item.hubView === view);
    return surface?.label ?? view;
  }
  return VIEW_LABELS[view] ?? view;
}

/** Advanced legacy panels hidden from primary sidebar unless deep-engineering or explicitly expanded. */
export const DEEP_ENGINEERING_ONLY_VIEWS = new Set<MissionControlView>([
  "integrity-routes",
  "integrity-features",
  "integrity-ui-alignment",
  "integrity-orphans",
  "integrity-diagnostics",
  "companion-replay-intelligence",
  "workspace-replay",
  "evidence-graph",
  "validation-center",
  "diff-explorer",
  "operational-replay",
  "engineering-audit",
]);

export const EXECUTIVE_VIEWS: MissionControlView[] = [
  "overview",
  "operational-anomalies",
  "recommendation-queue",
  "trust-metrics",
  "enterprise-health",
  "system-health",
];

export function isViewVisibleInWorkflow(
  view: MissionControlView,
  mode: "executive" | "operator" | "deep-engineering",
): boolean {
  if (mode === "executive") {
    return EXECUTIVE_VIEWS.includes(view) || view.startsWith("workflow-");
  }
  if (mode === "operator") {
    return !DEEP_ENGINEERING_ONLY_VIEWS.has(view);
  }
  return true;
}

export function filterLegacySectionsForMode(
  sections: SidebarSection[],
  mode: "executive" | "operator" | "deep-engineering",
): SidebarSection[] {
  return sections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => isViewVisibleInWorkflow(item.id, mode)),
    }))
    .filter((section) => section.items.length > 0);
}

export type NavigationContext = {
  hasActivePreflights?: boolean;
  hasActiveJobs?: boolean;
  hasAnomalies?: boolean;
  replayIntegrityDegraded?: boolean;
  truthStateDegraded?: boolean;
  pendingRecommendations?: number;
};

export function orderWorkflowSurfaces(
  surfaces: WorkflowSurface[],
  context: NavigationContext,
): WorkflowSurface[] {
  const score = (surface: WorkflowSurface): number => {
    let value = 0;
    if (context.hasActivePreflights && surface.id === "workspaces") value += 100;
    if (context.hasActiveJobs && surface.id === "operations") value += 90;
    if (context.hasAnomalies && surface.id === "operations") value += 80;
    if (context.truthStateDegraded && surface.id === "operations") value += 85;
    if (context.replayIntegrityDegraded && surface.id === "intelligence") value += 70;
    if ((context.pendingRecommendations ?? 0) > 0 && surface.id === "operations") value += 60;
    return value;
  };
  return [...surfaces].sort((a, b) => score(b) - score(a));
}

export function workflowBadge(
  surface: WorkflowSurface,
  context: NavigationContext,
): number | undefined {
  if (surface.id === "workspaces" && context.hasActivePreflights) return 1;
  if (
    surface.id === "operations" &&
    (context.hasAnomalies || context.hasActiveJobs || context.truthStateDegraded)
  ) {
    return 1;
  }
  if (surface.id === "intelligence" && context.replayIntegrityDegraded) return 1;
  if (surface.id === "operations" && (context.pendingRecommendations ?? 0) > 0) {
    return Math.min(context.pendingRecommendations ?? 0, 9);
  }
  return undefined;
}

export function workflowUrgent(surface: WorkflowSurface, context: NavigationContext): boolean {
  if (surface.id === "operations" && context.hasAnomalies) return true;
  if (surface.id === "operations" && context.truthStateDegraded) return true;
  if (surface.id === "intelligence" && context.replayIntegrityDegraded) return true;
  return false;
}

export const OVERVIEW_QUICK_VIEWS: { id: MissionControlView; label: string; hint: string }[] = [
  { id: "operational-anomalies", label: "Active issues", hint: "What needs attention" },
  { id: "recommendation-queue", label: "Recommendations", hint: "Prioritized guidance" },
  { id: "companion-investigation", label: "Investigations", hint: "Collaborative debugging" },
  { id: "companion-replay-intelligence", label: "Replay continuity", hint: "Long-session continuity" },
  { id: "cog-durable-jobs-active", label: "Background jobs", hint: "Durable agent work" },
  { id: "reliability-recovery-orchestration", label: "Recovery monitoring", hint: "Did recovery hold?" },
  { id: "agent-orchestration", label: "Orchestration", hint: "Agent pipeline and session threads" },
  { id: "deployment-stability", label: "Deployments", hint: "Release health" },
  { id: "trust-metrics", label: "Trust metrics", hint: "Operational confidence" },
  { id: "integrity-routes", label: "Route health", hint: "Runtime integrity" },
  { id: "workflow-operations", label: "Operations hub", hint: "Runtime awareness" },
  { id: "workflow-workspaces", label: "Workspaces hub", hint: "Continue collaboration" },
];

export function executiveNavigationItems(): { id: MissionControlView; label: string }[] {
  return EXECUTIVE_VIEWS.map((id) => ({ id, label: labelForView(id) }));
}

/** Count visible primary sidebar destinations (excluding advanced diagnostics). */
export function visiblePrimaryNavCount(mode: "executive" | "operator" | "deep-engineering"): number {
  const overview = 1;
  const hubs = mode === "executive" ? 0 : WORKFLOW_SURFACES.length;
  const primary = mode === "executive" ? EXECUTIVE_VIEWS.length - 1 : 0;
  return overview + hubs + primary;
}
