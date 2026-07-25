/** FIX 133 — governed UI approval execution via chat routes. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type ApprovalExecutionResponse = {
  ok: boolean;
  schema_version: string;
  ui_origin: string;
  chat_governance_required: boolean;
  session_id: string;
  inbox_id: string;
  gate_id: string;
  chat_intent: string;
  route_id: string;
  reply: string;
  mutation_performed: boolean;
  audit_id: string;
  detail?: string;
  blockers?: string[];
  outcome?: string;
  replay_protected?: boolean;
};

export type ApprovalAuditRecord = {
  approval_id: string;
  session_id?: string;
  inbox_id?: string;
  gate_id?: string;
  lane?: string;
  outcome?: string;
  gate_satisfied?: boolean;
  chat_intent?: string;
  route_id?: string;
  mutation_performed?: boolean;
  direct_provider_mutation?: boolean;
  blockers?: string[];
  failure_reason?: string;
  replay_protected?: boolean;
  copy_phrase_text?: string;
  recorded_at?: string;
  reply_excerpt?: string;
};

export type ApprovalAuditHistoryResponse = {
  ok: boolean;
  read_only: boolean;
  session_id: string;
  count: number;
  audits: ApprovalAuditRecord[];
};

export const fetchMissionControlApprovalAudit = (sessionId = "default", limit = 40) =>
  mcFetch<ApprovalAuditHistoryResponse>(
    `/api/v1/mission-control/approval-inbox/audit?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`,
  );

export type ActionSafetyReviewResponse = {
  ok: boolean;
  schema_version: string;
  invariant: string;
  chat_governance_entrypoint: string;
  execution_path_violations: string[];
  api_route_violations: string[];
  forbidden_ui_controls: string[];
};

export const fetchMissionControlActionSafetyReview = () =>
  mcFetch<ActionSafetyReviewResponse>("/api/v1/mission-control/action-safety/review");

export const executeMissionControlApproval = (inboxId: string, sessionId = "default") =>
  mcFetch<ApprovalExecutionResponse>("/api/v1/mission-control/approval-inbox/execute", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, inbox_id: inboxId }),
  });

export type TerminalApprovalExecutionResponse = {
  ok: boolean;
  session_id: string;
  inbox_id: string;
  preflight_id: string;
  execution_status: string;
  output: string;
  exit_code?: number | null;
  subagent_session_keys: string[];
  agent_send_results: { session_key: string; ok: boolean; error?: string }[];
  audit_id: string;
  detail?: string;
  blockers?: string[];
};

export const executeMissionControlTerminalApproval = (inboxId: string, sessionId = "default") =>
  mcFetch<TerminalApprovalExecutionResponse>("/api/v1/mission-control/approval-inbox/execute-terminal", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, inbox_id: inboxId }),
  });

export type MutationApprovalExecutionResponse = {
  ok: boolean;
  session_id: string;
  inbox_id: string;
  preflight_job_id: string;
  execution_job_id: string;
  audit_id: string;
  detail?: string;
  blockers?: string[];
  replay_protected?: boolean;
};

export const executeMissionControlMutationApproval = (inboxId: string, sessionId = "default") =>
  mcFetch<MutationApprovalExecutionResponse>("/api/v1/mission-control/approval-inbox/execute-mutation", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, inbox_id: inboxId }),
  });

export type ServeApprovalExecutionResponse = {
  ok: boolean;
  session_id: string;
  inbox_id: string;
  serve_request_id: string;
  model_id: string;
  endpoint: string;
  catalog_id: string;
  execution_status: string;
  audit_id: string;
  detail?: string;
  blockers?: string[];
};

export const executeMissionControlServeApproval = (inboxId: string, sessionId = "default") =>
  mcFetch<ServeApprovalExecutionResponse>("/api/v1/mission-control/approval-inbox/execute-serve", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, inbox_id: inboxId }),
  });

export type OperationalDeploymentApprovalExecutionResponse = {
  ok: boolean;
  session_id: string;
  inbox_id: string;
  job_id: string;
  preflight_id: string;
  orchestration_job_id: string;
  audit_id: string;
  detail?: string;
  reply?: string;
  route_id?: string;
  blockers?: string[];
  replay_protected?: boolean;
};

export const executeMissionControlOperationalDeploymentApproval = (inboxId: string, sessionId = "default") =>
  mcFetch<OperationalDeploymentApprovalExecutionResponse>(
    "/api/v1/mission-control/approval-inbox/execute-operational-deployment",
    {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, inbox_id: inboxId }),
    },
  );

export const rejectMissionControlOperationalDeploymentApproval = (inboxId: string, sessionId = "default") =>
  mcFetch<OperationalDeploymentApprovalExecutionResponse>(
    "/api/v1/mission-control/approval-inbox/reject-operational-deployment",
    {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, inbox_id: inboxId }),
    },
  );
