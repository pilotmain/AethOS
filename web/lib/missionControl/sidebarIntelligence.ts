/** Phase 10.2.0 — Sidebar intelligence for workflow surfaces. */

import type { AttentionLevel } from "@/lib/missionControl/spatialHierarchy";
import {
  WORKFLOW_SURFACES,
  workflowBadge,
  workflowUrgent,
  type NavigationContext,
  type WorkflowSurface,
  type WorkflowSurfaceId,
} from "@/lib/missionControl/workflowNavigation";

export function suggestExpandedDomain(context: NavigationContext): WorkflowSurfaceId | null {
  if (context.replayIntegrityDegraded) return "intelligence";
  if (context.hasActivePreflights) return "workspaces";
  if (context.hasAnomalies || context.hasActiveJobs) return "operations";
  if ((context.pendingRecommendations ?? 0) > 0) return "operations";
  return null;
}

export function domainAttentionLevel(
  domain: WorkflowSurface,
  context: NavigationContext,
): AttentionLevel {
  if (domain.id === "operations" && context.hasAnomalies) return "urgent";
  if (domain.id === "intelligence" && context.replayIntegrityDegraded) return "elevated";
  if (domain.id === "workspaces" && context.hasActivePreflights) return "informational";
  if (domain.id === "operations" && (context.pendingRecommendations ?? 0) > 0) return "informational";
  if (domain.id === "operations" && context.hasActiveJobs) return "informational";
  return "passive";
}

export function shouldDimDomain(
  domain: WorkflowSurface,
  activeDomain: WorkflowSurfaceId | "overview",
  context: NavigationContext,
  focusMode: boolean,
): boolean {
  if (focusMode) return domain.id !== activeDomain && activeDomain !== "overview";
  if (activeDomain === domain.id) return false;
  if (workflowUrgent(domain, context)) return false;
  return domainAttentionLevel(domain, context) === "passive";
}

export function resolveExpandedDomain(
  saved: WorkflowSurfaceId | null,
  context: NavigationContext,
  activeDomain: WorkflowSurfaceId | "overview",
): WorkflowSurfaceId | null {
  if (saved) return saved;
  if (activeDomain !== "overview") return activeDomain;
  return suggestExpandedDomain(context);
}

export function groupedDomainLabel(domainId: WorkflowSurfaceId): string {
  return WORKFLOW_SURFACES.find((surface) => surface.id === domainId)?.label ?? domainId;
}

/** @deprecated Use groupedDomainLabel */
export function groupedWorkflowLabel(surfaceId: WorkflowSurfaceId): string {
  return groupedDomainLabel(surfaceId);
}

export { workflowBadge as domainBadge, workflowUrgent as domainUrgent };
