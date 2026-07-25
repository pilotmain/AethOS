/** FIX 309 — SaaS launch readiness assessment (assessment ≠ launch authority). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type SaasLaunchReadinessAssessmentResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  launch_assessment_compose_artifacts_only: boolean;
  launch_authority: boolean;
  automatic_launch_enabled: boolean;
  automatic_readiness_promotion_enabled: boolean;
  trust_mutation_authority: boolean;
  customer_provisioning_authority: boolean;
  governance_mutation_performed: boolean;
  schema_version: string;
  session_id: string;
  blockers?: string[];
  detail?: string;
  saas_launch_readiness_assessment?: Record<string, unknown>;
  markdown?: string;
};

export type SaasLaunchReadinessAssessmentRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  saas_launch_readiness_assessment_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlSaasLaunchReadinessAssessment = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<SaasLaunchReadinessAssessmentResponse>(
    `/api/v1/mission-control/saas-launch-readiness-assessment?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlSaasLaunchReadinessAssessmentRecord = (
  sessionId: string,
  kind: string,
  content: string,
  domain?: string,
) =>
  mcFetch<SaasLaunchReadinessAssessmentRecordResponse>(
    `/api/v1/mission-control/saas-launch-readiness-assessment/record`,
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
