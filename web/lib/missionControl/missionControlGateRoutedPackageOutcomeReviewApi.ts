/** FIX 173 — gate-routed package outcome review (review before lane action). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type GateRoutedPackageOutcomeReviewResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  execution_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_lane_entry_enabled: boolean;
  autonomous_approval_enabled: boolean;
  tier_escalation_enabled: boolean;
  gate_bypass_enabled: boolean;
  code_write_enabled: boolean;
  pr_action_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  gate_routed_package_outcome_review?: Record<string, unknown>;
  markdown?: string;
};

export type GateRoutedPackageOutcomeReviewRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  gate_routed_package_outcome_review_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlGateRoutedPackageOutcomeReview = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<GateRoutedPackageOutcomeReviewResponse>(
    `/api/v1/mission-control/gate-routed-package-outcome-review?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlGateRoutedPackageOutcomeReviewRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<GateRoutedPackageOutcomeReviewRecordResponse>(
    `/api/v1/mission-control/gate-routed-package-outcome-review/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
