/** Workspace suite — Calendar API (handoff §8). Local-first; CalDAV sync is readonly. */

import { apiBase, apiFetch } from "@/lib/api";

export type CalendarMeta = { name: string; color: string };

export type CalendarEvent = {
  id: string;
  uid?: string;
  summary: string;
  start: string;
  end?: string;
  description?: string;
  calendar: string;
  source?: string;
  created_at?: number;
};

export type EventsResponse = {
  ok: boolean;
  error?: string;
  calendars?: CalendarMeta[];
  event_count?: number;
  events: CalendarEvent[];
};

const base = () => `${apiBase()}/api/v1/human/workspace/calendar`;

export async function listEvents(limit = 200): Promise<EventsResponse> {
  const res = await apiFetch(`${base()}/events?limit=${limit}`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}`, events: [] };
  return res.json();
}

export async function addEvent(input: {
  summary: string;
  start: string;
  end?: string;
  description?: string;
  calendar?: string;
}): Promise<{ ok: boolean; error?: string; event?: CalendarEvent }> {
  const res = await apiFetch(`${base()}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      summary: input.summary,
      start: input.start,
      end: input.end || "",
      description: input.description || "",
      calendar: input.calendar || "default",
    }),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function deleteEvent(eventId: string): Promise<{ ok: boolean }> {
  const res = await apiFetch(`${base()}/events/${encodeURIComponent(eventId)}`, { method: "DELETE" });
  if (!res.ok) return { ok: false };
  return res.json();
}

export async function importIcs(icsText: string, calendar = "imported"): Promise<{ ok: boolean; error?: string; imported?: number }> {
  const res = await apiFetch(`${base()}/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({ ics_text: icsText, calendar }),
  });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function exportIcs(): Promise<{ ok: boolean; error?: string; ics?: string; event_count?: number }> {
  const res = await apiFetch(`${base()}/export`, { cache: "no-store", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}

export async function caldavSync(): Promise<{ ok: boolean; error?: string; hint?: string; readonly?: boolean }> {
  const res = await apiFetch(`${base()}/sync`, { method: "POST", headers: { Accept: "application/json" } });
  if (!res.ok) return { ok: false, error: `http_${res.status}` };
  return res.json();
}
