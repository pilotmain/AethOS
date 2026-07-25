/** Phase 10.2.0 — Workflow-first sidebar navigation (re-exports + compatibility). */

import {
  EXECUTIVE_VIEWS,
  DEEP_ENGINEERING_ONLY_VIEWS,
  OVERVIEW_QUICK_VIEWS,
  WORKFLOW_SURFACES,
  filterLegacySectionsForMode,
  isViewVisibleInWorkflow,
  legacySectionsForSurface,
  orderWorkflowSurfaces,
  workflowBadge,
  workflowForView,
  workflowUrgent,
  type NavigationContext,
  type WorkflowSurface,
  type WorkflowSurfaceId,
} from "@/lib/missionControl/workflowNavigation";
import type { MissionControlView, SidebarSection } from "@/lib/missionControl/views";

export type MissionControlMode = "executive" | "operator" | "deep-engineering";

/** @deprecated Use WorkflowSurfaceId — kept for persisted sidebar state migration. */
export type NavigationDomainId = WorkflowSurfaceId;

export type NavigationDomain = WorkflowSurface;

/** Workflow surfaces replace the prior five operational domains. */
export const NAV_DOMAINS = WORKFLOW_SURFACES;

export {
  EXECUTIVE_VIEWS,
  DEEP_ENGINEERING_ONLY_VIEWS,
  OVERVIEW_QUICK_VIEWS,
  type NavigationContext,
};

export function sectionsForDomain(domain: NavigationDomain): SidebarSection[] {
  return legacySectionsForSurface(domain);
}

export function domainForView(view: MissionControlView): NavigationDomainId | "overview" {
  return workflowForView(view);
}

export function isViewVisibleInMode(view: MissionControlView, mode: MissionControlMode): boolean {
  return isViewVisibleInWorkflow(view, mode);
}

export function filterSectionsForMode(
  sections: SidebarSection[],
  mode: MissionControlMode,
): SidebarSection[] {
  return filterLegacySectionsForMode(sections, mode);
}

export function orderDomains(
  domains: NavigationDomain[],
  context: NavigationContext,
): NavigationDomain[] {
  return orderWorkflowSurfaces(domains, context);
}

export function domainBadge(
  domain: NavigationDomain,
  context: NavigationContext,
): number | undefined {
  return workflowBadge(domain, context);
}

export function domainUrgent(domain: NavigationDomain, context: NavigationContext): boolean {
  return workflowUrgent(domain, context);
}

export { executiveNavigationItems } from "@/lib/missionControl/workflowNavigation";
