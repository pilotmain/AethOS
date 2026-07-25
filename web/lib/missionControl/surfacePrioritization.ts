/** Phase 10.1.5.2 — Intelligent surface prioritization by operator focus. */

import type { MissionControlMode, NavigationContext } from "@/lib/missionControl/sidebarNavigation";
import { OVERVIEW_QUICK_VIEWS } from "@/lib/missionControl/sidebarNavigation";
import type { MissionControlView } from "@/lib/missionControl/views";

export type SurfaceFocus = "deployment" | "executive" | "replay" | "engineering" | "general";

export type PrioritizedSurface = {
  id: MissionControlView;
  label: string;
  hint: string;
  priority: number;
};

const DEPLOYMENT_VIEWS: MissionControlView[] = [
  "deployment-stability",
  "telemetry-freshness",
  "companion-replay-intelligence",
  "operational-anomalies",
  "recommendation-queue",
  "operation-preflights",
];

const EXECUTIVE_VIEWS: MissionControlView[] = [
  "trust-metrics",
  "enterprise-health",
  "operational-anomalies",
  "recommendation-queue",
  "companion-trust-retention",
  "production-deployment",
];

const REPLAY_VIEWS: MissionControlView[] = [
  "companion-replay-intelligence",
  "companion-investigation",
  "reliability-recovery-orchestration",
  "workflow-intelligence",
  "trust-metrics",
];

const ENGINEERING_VIEWS: MissionControlView[] = [
  "operation-preflights",
  "integrity-routes",
  "validation-center",
  "local-workspaces",
];

export function detectSurfaceFocus(context: NavigationContext): SurfaceFocus {
  if (context.hasActivePreflights) return "engineering";
  if (context.replayIntegrityDegraded) return "replay";
  if (context.hasAnomalies || context.hasActiveJobs) return "deployment";
  return "general";
}

export function prioritizeSurfaces(
  mode: MissionControlMode,
  context: NavigationContext,
  limit = 4,
): PrioritizedSurface[] {
  const focus = mode === "executive" ? "executive" : detectSurfaceFocus(context);
  const prioritySets: Record<SurfaceFocus, MissionControlView[]> = {
    deployment: DEPLOYMENT_VIEWS,
    executive: EXECUTIVE_VIEWS,
    replay: REPLAY_VIEWS,
    engineering: ENGINEERING_VIEWS,
    general: OVERVIEW_QUICK_VIEWS.map((v) => v.id),
  };

  const preferred = new Set(prioritySets[focus]);
  if (mode === "deep-engineering") {
    ENGINEERING_VIEWS.forEach((v) => preferred.add(v));
  }

  const ranked = OVERVIEW_QUICK_VIEWS.map((item, index) => ({
    ...item,
    priority: preferred.has(item.id) ? 100 - index : 20 - index,
  }))
    .sort((a, b) => b.priority - a.priority)
    .slice(0, limit);

  if (mode === "executive") {
    return ranked.filter((r) => EXECUTIVE_VIEWS.includes(r.id)).slice(0, 3);
  }

  return ranked;
}

export function shouldShowConnectionHealth(mode: MissionControlMode, context: NavigationContext): boolean {
  if (mode === "executive") return false;
  if (mode === "deep-engineering") return true;
  return !context.hasActivePreflights;
}

export function shouldShowMetricStrip(mode: MissionControlMode, quietMode: boolean): boolean {
  if (mode === "executive" || quietMode) return false;
  return true;
}
