import { apiBase } from "@/lib/api";

export interface MonitorObservation {
  at: number;
  summary: string;
  signature: string;
  alert: boolean;
  monitor_id?: string;
  monitor_name?: string;
}

export interface Monitor {
  monitor_id: string;
  tenant_id: string;
  name: string;
  kind: string;
  target: string;
  interval_sec: number;
  notify: string;
  enabled: boolean;
  last_run_at: number | null;
  last_summary: string | null;
  observations: MonitorObservation[];
}

export interface MonitorKind {
  kind: string;
  label: string;
  hint: string;
}

export async function fetchMonitors(): Promise<{ monitors: Monitor[]; kinds: MonitorKind[] }> {
  const res = await fetch(`${apiBase()}/api/v1/monitors`, { cache: "no-store" });
  if (!res.ok) return { monitors: [], kinds: [] };
  return res.json();
}

export async function createMonitor(body: {
  name: string;
  kind: string;
  target: string;
  interval_sec: number;
}): Promise<Monitor | null> {
  const res = await fetch(`${apiBase()}/api/v1/monitors`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error((await res.text()) || `Create failed (${res.status})`);
  return (await res.json()).monitor;
}

export async function runMonitor(id: string): Promise<MonitorObservation | Record<string, unknown>> {
  const res = await fetch(`${apiBase()}/api/v1/monitors/${encodeURIComponent(id)}/run`, { method: "POST" });
  return res.json();
}

export async function deleteMonitor(id: string): Promise<boolean> {
  const res = await fetch(`${apiBase()}/api/v1/monitors/${encodeURIComponent(id)}`, { method: "DELETE" });
  return res.ok;
}

export async function setMonitorEnabled(id: string, enabled: boolean): Promise<boolean> {
  const res = await fetch(`${apiBase()}/api/v1/monitors/${encodeURIComponent(id)}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ enabled }),
  });
  return res.ok;
}
