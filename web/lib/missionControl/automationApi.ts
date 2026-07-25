/** Proactive automation API — scheduled tasks and webhook triggers. */

import { apiBase } from "@/lib/api";

export interface ScheduledTask {
  task_id: string;
  name: string;
  prompt: string;
  schedule_kind: string;
  cron_expression?: string | null;
  interval_sec: number;
  action_kind: string;
  job_type?: string | null;
  delivery_channel: string;
  delivery_target: string;
  enabled: boolean;
  last_run_at?: number | null;
}

export interface WebhookTrigger {
  trigger_id: string;
  name: string;
  prompt: string;
  action_kind: string;
  job_type?: string | null;
  delivery_channel: string;
  delivery_target: string;
  allow_mutation: boolean;
  enabled: boolean;
  webhook_url_path?: string;
  secret?: string;
  fire_count?: number;
}

export async function fetchAutomationStatus() {
  const res = await fetch(`${apiBase()}/api/v1/automation/status`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json() as Promise<{
    ok: boolean;
    enabled: boolean;
    scheduler?: Record<string, unknown>;
    job_types?: { id: string; label: string }[];
  }>;
}

export async function fetchScheduledTasks() {
  const res = await fetch(`${apiBase()}/api/v1/automation/schedules`, { cache: "no-store" });
  if (!res.ok) return { ok: false, tasks: [] as ScheduledTask[] };
  return res.json() as Promise<{ ok: boolean; tasks: ScheduledTask[] }>;
}

export async function createScheduledTask(body: {
  name: string;
  prompt: string;
  schedule_kind?: string;
  cron_expression?: string;
  interval_sec?: number;
  action_kind?: string;
  job_type?: string;
  delivery_channel?: string;
  delivery_target?: string;
}) {
  const res = await fetch(`${apiBase()}/api/v1/automation/schedules`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function deleteScheduledTask(taskId: string) {
  const res = await fetch(`${apiBase()}/api/v1/automation/schedules/${encodeURIComponent(taskId)}`, {
    method: "DELETE",
  });
  return res.json();
}

export async function fetchWebhookTriggers() {
  const res = await fetch(`${apiBase()}/api/v1/automation/webhooks`, { cache: "no-store" });
  if (!res.ok) return { ok: false, triggers: [] as WebhookTrigger[] };
  return res.json() as Promise<{ ok: boolean; triggers: WebhookTrigger[] }>;
}

export async function createWebhookTrigger(body: {
  name: string;
  prompt: string;
  action_kind?: string;
  job_type?: string;
  delivery_channel?: string;
  delivery_target?: string;
  allow_mutation?: boolean;
}) {
  const res = await fetch(`${apiBase()}/api/v1/automation/webhooks`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });
  return res.json();
}

export async function deleteWebhookTrigger(triggerId: string) {
  const res = await fetch(`${apiBase()}/api/v1/automation/webhooks/${encodeURIComponent(triggerId)}`, {
    method: "DELETE",
  });
  return res.json();
}
