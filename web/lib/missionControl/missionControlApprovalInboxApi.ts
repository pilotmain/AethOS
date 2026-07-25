/** FIX 132 — Mission Control approval inbox API (view-only). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ApprovalInboxItem = {
  inbox_id: string;
  lane: string;
  gate_id: string;
  title: string;
  severity: string;
  required_phrases: string[];
  unlocks: string[];
  remains_forbidden: string[];
  risk_tier: string;
  blast_radius: Record<string, unknown>;
  approval_surface: string;
  ui_approval_eligible: boolean;
  copy_phrase_text?: string;
  approval_execution_enabled: boolean;
  execution_mode: string;
  mutation_performed: boolean;
  terminal_execution_enabled?: boolean;
  mutation_inbox_execution_enabled?: boolean;
  serve_execution_enabled?: boolean;
  deployment_execution_enabled?: boolean;
  deployment_execution_hint?: string;
  deployment_inbox_execution_enabled?: boolean;
  context?: Record<string, unknown>;
};

export function operationalDeploymentApprovalUiState(item: ApprovalInboxItem): {
  showsApproveButton: boolean;
  approveDisabled: boolean;
  disabledHint: string;
} {
  const isDeployment =
    item.deployment_inbox_execution_enabled ||
    item.lane === "operational_deployment" ||
    item.execution_mode === "operational_deployment_approve";
  if (!isDeployment) {
    return { showsApproveButton: false, approveDisabled: true, disabledHint: "" };
  }
  const enabled = Boolean(item.deployment_execution_enabled);
  return {
    showsApproveButton: true,
    approveDisabled: !enabled,
    disabledHint: item.deployment_execution_hint || "Enable Railway greenfield execution to deploy.",
  };
}

export type ApprovalInboxGroup = {
  lane: string;
  severity: string;
  count: number;
  items: ApprovalInboxItem[];
};

export type ApprovalInboxResponse = {
  ok: boolean;
  read_only: boolean;
  schema_version: string;
  session_id: string;
  detail?: string;
  summary: {
    total_pending: number;
    by_severity: Record<string, number>;
    lanes_with_pending: number;
    mutation_performed: boolean;
    approval_execution_enabled: boolean;
    ui_eligible_count: number;
  };
  items: ApprovalInboxItem[];
  groups: ApprovalInboxGroup[];
  mutation_performed: boolean;
  approval_execution_enabled: boolean;
};

export const fetchMissionControlApprovalInbox = (sessionId = "default") =>
  mcFetch<ApprovalInboxResponse>(
    `/api/v1/mission-control/approval-inbox?session_id=${encodeURIComponent(sessionId)}`,
  );
