/** FIX 316 — Post-launch operations baseline (baseline ≠ operational authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PostLaunchOperationsBaselineResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_execution_performed: boolean;
  post_launch_operations_compose_artifacts_only: boolean;
  post_launch_operations_authority: boolean;
  automatic_operational_execution_enabled: boolean;
  automatic_customer_contact_enabled: boolean;
  automatic_incident_response_enabled: boolean;
  trust_mutation_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  post_launch_operations_baseline?: Record<string, unknown>;
  markdown?: string;
};

export type PostLaunchOperationsBaselineRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  post_launch_operations_baseline_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlPostLaunchOperationsBaseline = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PostLaunchOperationsBaselineResponse>(
    `/api/v1/mission-control/post-launch-operations-baseline?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPostLaunchOperationsBaselineRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<PostLaunchOperationsBaselineRecordResponse>(
    `/api/v1/mission-control/post-launch-operations-baseline`,
    {
      method: "POST",
      body: JSON.stringify({
        session_id: sessionId,
        kind,
        content,
        domain,
      }),
    },
  );

export type PostLaunchOperationsBaselineFocus =
  | "post_launch_operations_dashboard"
  | "platform_health_baseline"
  | "customer_health_baseline"
  | "governance_health_baseline"
  | "incident_baseline"
  | "commercial_baseline"
  | "operations_baseline_registry";

export const POST_LAUNCH_OPERATIONS_BASELINE_FOCUS_BY_VIEW: Record<
  string,
  PostLaunchOperationsBaselineFocus
> = {
  "post-launch-operations": "post_launch_operations_dashboard",
  "post-launch-platform-health": "platform_health_baseline",
  "post-launch-customer-health": "customer_health_baseline",
  "post-launch-governance-health": "governance_health_baseline",
  "post-launch-incident-health": "incident_baseline",
  "post-launch-commercial-health": "commercial_baseline",
  "post-launch-operations-dashboard": "post_launch_operations_dashboard",
};
