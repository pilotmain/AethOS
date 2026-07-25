/** Runtime actions API — Mission Control Jobs tab only. */

import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeActionRecord = {
  id: string;
  action_type: string;
  status: string;
  summary: string;
  params?: Record<string, unknown>;
  source?: string;
  result?: string | null;
  error?: string | null;
};

export type ActionsGrouped = {
  pending: RuntimeActionRecord[];
  approved: RuntimeActionRecord[];
  completed: RuntimeActionRecord[];
  failed: RuntimeActionRecord[];
  denied: RuntimeActionRecord[];
};

export const fetchActionsGrouped = () =>
  mcFetch<{ actions: ActionsGrouped; count: number }>("/api/v1/actions");

export const approveAction = (actionId: string) =>
  mcFetch<RuntimeActionRecord>(`/api/v1/actions/${encodeURIComponent(actionId)}/approve`, {
    method: "POST",
    body: "{}",
  });

export const denyAction = (actionId: string) =>
  mcFetch<RuntimeActionRecord>(`/api/v1/actions/${encodeURIComponent(actionId)}/deny`, {
    method: "POST",
    body: "{}",
  });

export function emptyActionsGrouped(): ActionsGrouped {
  return { pending: [], approved: [], completed: [], failed: [], denied: [] };
}

export function normalizeActionsGrouped(input: unknown): ActionsGrouped {
  const o = input as Partial<ActionsGrouped> | null;
  if (!o || typeof o !== "object") return emptyActionsGrouped();
  return {
    pending: Array.isArray(o.pending) ? o.pending : [],
    approved: Array.isArray(o.approved) ? o.approved : [],
    completed: Array.isArray(o.completed) ? o.completed : [],
    failed: Array.isArray(o.failed) ? o.failed : [],
    denied: Array.isArray(o.denied) ? o.denied : [],
  };
}

export function actionControlHint(status: string): string {
  switch (status) {
    case "pending":
      return "Waiting for approval";
    case "approved":
      return "Approved — executing";
    case "completed":
      return "Completed";
    case "failed":
      return "Failed";
    case "denied":
      return "Denied by operator";
    default:
      return status;
  }
}
