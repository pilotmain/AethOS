/** Operator-visible Mission Control navigation — Phase 10.2.0 workflow truth. */

import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

export const OPERATOR_VISIBLE_OPERATIONS = [
  "Operations hub",
  "Recovery monitoring",
  "Active issues",
  "Deployments",
  "Provider status",
  "Runtime actions",
  "Recommendations",
] as const;

export const OPERATOR_VISIBLE_WORKSPACES = [
  "Workspaces hub",
  "Active investigations",
  "Agent work",
  "Workspaces",
  "Collaboration",
  "Background jobs",
  "Engineering execution",
] as const;

export const HIDDEN_INTERNAL_PANELS = [
  "Operation Preflights",
  "JobsTrackedWorkPanel",
  "Runtime Fragility Intelligence",
  "Recovery Continuity Intelligence",
  "Durable Agent Jobs",
  "tracked-work",
  "operation-preflights",
] as const;

export const OPERATOR_APPROVAL_INBOX_PATH = "Mission Control → Approvals";

const INTERNAL_TO_VISIBLE_OPERATOR: Record<string, string> = {
  "Operation Preflights": OPERATOR_APPROVAL_INBOX_PATH,
  JobsTrackedWorkPanel: OPERATOR_APPROVAL_INBOX_PATH,
  "Mission Control → Jobs": OPERATOR_APPROVAL_INBOX_PATH,
  "Durable Agent Jobs": "Mission Control → Workspaces → Background jobs",
};

const INTERNAL_TO_VISIBLE_DEEP: Record<string, string> = {
  "Operation Preflights": "Mission Control → Operations → Operation Preflights",
  JobsTrackedWorkPanel: "Mission Control → Operations → Operation Preflights",
  "Mission Control → Jobs": "Mission Control → Operations → Operation Preflights",
  "Durable Agent Jobs": "Mission Control → Workspaces → Durable Agent Jobs",
};

export function resolveVisibleNavigationPath(
  internalSurface: string,
  mode: MissionControlMode = "operator",
): string {
  const table = mode === "deep-engineering" ? INTERNAL_TO_VISIBLE_DEEP : INTERNAL_TO_VISIBLE_OPERATOR;
  if (table[internalSurface]) return table[internalSurface];
  for (const [key, path] of Object.entries(table)) {
    if (internalSurface.toLowerCase().includes(key.toLowerCase())) return path;
  }
  return internalSurface;
}

export function containsHiddenNavigationLeakage(text: string, mode: MissionControlMode = "operator"): boolean {
  if (mode === "deep-engineering") return false;
  const lower = text.toLowerCase();
  for (const label of HIDDEN_INTERNAL_PANELS) {
    if (lower.includes(label.toLowerCase())) return true;
  }
  if (lower.includes("mission control → jobs")) return true;
  return false;
}

export function visibleNavigationRegistry(mode: MissionControlMode = "operator") {
  return {
    mode,
    operatorVisible: [...OPERATOR_VISIBLE_OPERATIONS, ...OPERATOR_VISIBLE_WORKSPACES],
    hiddenInternalPanels: [...HIDDEN_INTERNAL_PANELS],
    mutationApprovalPath: resolveVisibleNavigationPath("Operation Preflights", mode),
    durableApprovalPath: resolveVisibleNavigationPath("Durable Agent Jobs", mode),
  };
}
