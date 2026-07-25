/** FIX 168 — bounded multi-agent delivery work packages (package cognition). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type BoundedDeliveryWorkPackagesResponse = {
  ok: boolean;
  read_only: boolean;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  automatic_policy_mutation_enabled: boolean;
  autonomous_execution_enabled: boolean;
  autonomous_approval_enabled: boolean;
  code_write_enabled: boolean;
  pr_action_enabled: boolean;
  merge_deploy_enabled: boolean;
  railway_mutation_enabled: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  bounded_delivery_work_packages?: Record<string, unknown>;
  markdown?: string;
};

export type BoundedDeliveryWorkPackagesRecordResponse = {
  ok: boolean;
  schema_version: string;
  session_id: string;
  record?: Record<string, unknown>;
  mutation_performed: boolean;
  governance_mutation_performed: boolean;
  executable: boolean;
  bounded_delivery_work_packages_memory_only: boolean;
  detail?: string;
};

export const fetchMissionControlBoundedDeliveryWorkPackages = (
  sessionId = "default",
  format: "json" | "markdown" | "both" = "both",
) =>
  mcFetch<BoundedDeliveryWorkPackagesResponse>(
    `/api/v1/mission-control/bounded-delivery-work-packages?session_id=${encodeURIComponent(sessionId)}&format=${format}`,
  );

export const appendMissionControlBoundedDeliveryWorkPackagesRecord = (
  sessionId: string,
  kind: string,
  content: string,
  author = "operator",
) =>
  mcFetch<BoundedDeliveryWorkPackagesRecordResponse>(
    `/api/v1/mission-control/bounded-delivery-work-packages/record`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, kind, content, author }),
    },
  );
