/** FIX 314 — Public launch readiness freeze (freeze ≠ launch authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type PublicLaunchReadinessFreezeResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  pilot_reexecution_performed: boolean;
  launch_readiness_freeze_compose_artifacts_only: boolean;
  launch_freeze_authority: boolean;
  automatic_launch_enabled: boolean;
  automatic_beta_expansion_enabled: boolean;
  trust_mutation_authority: boolean;
  launch_decision_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  public_launch_readiness_freeze?: Record<string, unknown>;
  markdown?: string;
};

export type PublicLaunchReadinessFreezeRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  public_launch_readiness_freeze_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlPublicLaunchReadinessFreeze = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<PublicLaunchReadinessFreezeResponse>(
    `/api/v1/mission-control/public-launch-readiness-freeze?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlPublicLaunchReadinessFreezeRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<PublicLaunchReadinessFreezeRecordResponse>(
    `/api/v1/mission-control/public-launch-readiness-freeze`,
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

export type LaunchReadinessFreezeFocus =
  | "launch_readiness_freeze_dashboard"
  | "launch_evidence_timeline"
  | "launch_recommendation_freeze"
  | "launch_blocker_freeze"
  | "launch_risk_freeze";

export const LAUNCH_READINESS_FREEZE_FOCUS_BY_VIEW: Record<string, LaunchReadinessFreezeFocus> = {
  "launch-readiness-freeze": "launch_readiness_freeze_dashboard",
  "launch-baseline": "launch_readiness_freeze_dashboard",
  "launch-evidence-freeze": "launch_evidence_timeline",
  "launch-recommendation-freeze": "launch_recommendation_freeze",
  "launch-freeze-blockers": "launch_blocker_freeze",
  "launch-freeze-risks": "launch_risk_freeze",
};
