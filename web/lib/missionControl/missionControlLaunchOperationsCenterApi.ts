/** FIX 313 — Launch operations center (visibility ≠ launch authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type LaunchOperationsCenterResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  launch_operations_compose_artifacts_only: boolean;
  launch_operations_authority: boolean;
  automatic_launch_enabled: boolean;
  automatic_beta_expansion_enabled: boolean;
  automatic_customer_admission_enabled: boolean;
  automatic_provider_mutation_enabled: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  launch_operations_center?: Record<string, unknown>;
  markdown?: string;
};

export type LaunchOperationsCenterRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  launch_operations_center_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlLaunchOperationsCenter = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<LaunchOperationsCenterResponse>(
    `/api/v1/mission-control/launch-operations-center?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlLaunchOperationsCenterRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<LaunchOperationsCenterRecordResponse>(`/api/v1/mission-control/launch-operations-center`, {
    method: "POST",
    body: JSON.stringify({
      session_id: sessionId,
      kind,
      content,
      domain,
    }),
  });

export type LaunchOperationsFocus =
  | "launch_operations_dashboard"
  | "launch_status_registry"
  | "launch_blocker_registry"
  | "launch_risk_dashboard"
  | "beta_operations_monitor"
  | "customer_operations_monitor"
  | "launch_evidence_registry";

export const LAUNCH_OPERATIONS_FOCUS_BY_VIEW: Record<string, LaunchOperationsFocus> = {
  "launch-operations-center": "launch_operations_dashboard",
  "launch-dashboard": "launch_operations_dashboard",
  "launch-risks": "launch_risk_dashboard",
  "launch-blockers": "launch_blocker_registry",
  "launch-evidence": "launch_evidence_registry",
  "beta-operations": "beta_operations_monitor",
  "customer-operations": "customer_operations_monitor",
};
