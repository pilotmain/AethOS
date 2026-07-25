/** Workspace suite — Notes & Tasks API (handoff §8). Scheduled tasks never auto-execute. */

import { apiBase, apiFetch } from "@/lib/api";

export type WorkspaceNote = {
  id: string;
  text: string;
  created_at?: number;
};

export type WorkspaceTask = {
  id: string;
  text: string;
  done: boolean;
  scheduled_for?: string | null;
  auto_execute?: boolean;
  created_at?: number;
  updated_at?: number;
};

const base = () => `${apiBase()}/api/v1/human/workspace`;

async function jsonOrError<T>(res: Response, fallback: T): Promise<T> {
  if (!res.ok) return fallback;
  return res.json() as Promise<T>;
}

export async function listNotes(limit = 100): Promise<{ ok: boolean; error?: string; notes: WorkspaceNote[] }> {
  const res = await apiFetch(`${base()}/notes?limit=${limit}`, { cache: "no-store", headers: { Accept: "application/json" } });
  return jsonOrError(res, { ok: false, error: `http_${res.status}`, notes: [] });
}

export async function addNote(text: string): Promise<{ ok: boolean; error?: string; note?: WorkspaceNote }> {
  const res = await apiFetch(`${base()}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ text }),
  });
  return jsonOrError(res, { ok: false, error: `http_${res.status}` });
}

export async function deleteNote(noteId: string): Promise<{ ok: boolean }> {
  const res = await apiFetch(`${base()}/notes/${encodeURIComponent(noteId)}`, { method: "DELETE" });
  return jsonOrError(res, { ok: false });
}

export async function listTasks(limit = 200): Promise<{ ok: boolean; error?: string; tasks: WorkspaceTask[] }> {
  const res = await apiFetch(`${base()}/tasks?limit=${limit}`, { cache: "no-store", headers: { Accept: "application/json" } });
  return jsonOrError(res, { ok: false, error: `http_${res.status}`, tasks: [] });
}

export async function addTask(text: string, scheduledFor?: string): Promise<{ ok: boolean; error?: string; task?: WorkspaceTask }> {
  const res = await apiFetch(`${base()}/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ text, scheduled_for: scheduledFor || null }),
  });
  return jsonOrError(res, { ok: false, error: `http_${res.status}` });
}

export async function setTaskDone(taskId: string, done: boolean): Promise<{ ok: boolean; task?: WorkspaceTask }> {
  const res = await apiFetch(`${base()}/tasks/${encodeURIComponent(taskId)}/done`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ done }),
  });
  return jsonOrError(res, { ok: false });
}

export async function deleteTask(taskId: string): Promise<{ ok: boolean }> {
  const res = await apiFetch(`${base()}/tasks/${encodeURIComponent(taskId)}`, { method: "DELETE" });
  return jsonOrError(res, { ok: false });
}
