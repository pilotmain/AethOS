/** FIX 315 — Launch decision package (package ≠ launch decision). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type LaunchDecisionPackageResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_execution_performed: boolean;
  launch_decision_package_compose_artifacts_only: boolean;
  launch_decision_authority: boolean;
  automatic_launch_approval_enabled: boolean;
  automatic_launch_enabled: boolean;
  automatic_beta_expansion_enabled: boolean;
  trust_mutation_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  launch_decision_package?: Record<string, unknown>;
  markdown?: string;
};

export type LaunchDecisionPackageRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  launch_decision_package_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlLaunchDecisionPackage = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<LaunchDecisionPackageResponse>(
    `/api/v1/mission-control/launch-decision-package?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlLaunchDecisionPackageRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<LaunchDecisionPackageRecordResponse>(`/api/v1/mission-control/launch-decision-package`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      kind,
      content,
      domain,
    }),
  });

export type LaunchDecisionPackageFocus =
  | "launch_decision_dashboard"
  | "launch_executive_summary"
  | "launch_recommendation_package"
  | "launch_decision_registry";

export const LAUNCH_DECISION_PACKAGE_FOCUS_BY_VIEW: Record<string, LaunchDecisionPackageFocus> = {
  "launch-decision-package": "launch_decision_dashboard",
  "launch-executive-summary": "launch_executive_summary",
  "launch-recommendation-package": "launch_recommendation_package",
  "launch-decision-dashboard": "launch_decision_dashboard",
  "launch-decision-history": "launch_decision_registry",
};
