"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  addEvent,
  caldavSync,
  deleteEvent,
  exportIcs,
  importIcs,
  listEvents,
  type CalendarEvent,
  type CalendarMeta,
} from "@/lib/workspace/calendarApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";
import { WorkspaceNav } from "@/components/workspace/WorkspaceNav";

const inputStyle = {
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${mcColors.border}`,
  background: "rgba(0,0,0,0.3)",
  color: mcColors.text,
  fontSize: 13,
} as const;

export function CalendarPanel() {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [calendars, setCalendars] = useState<CalendarMeta[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [info, setInfo] = useState<string | null>(null);
  const [summary, setSummary] = useState("");
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [ics, setIcs] = useState("");

  const colorFor = useCallback(
    (name: string) => calendars.find((c) => c.name === name)?.color || mcColors.cyan,
    [calendars],
  );

  const refresh = useCallback(async () => {
    const res = await listEvents();
    if (!res.ok) setError(res.error || "load_failed");
    else {
      setError(null);
      setEvents(res.events);
      setCalendars(res.calendars || []);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const submitEvent = useCallback(async () => {
    if (!summary.trim() || !start.trim()) return;
    const res = await addEvent({ summary: summary.trim(), start: start.trim(), end: end.trim() });
    if (res.ok) {
      setSummary("");
      setStart("");
      setEnd("");
      await refresh();
    } else setError(res.error || "add_failed");
  }, [summary, start, end, refresh]);

  const doImport = useCallback(async () => {
    if (!ics.trim()) return;
    const res = await importIcs(ics.trim());
    setInfo(res.ok ? `Imported ${res.imported} event(s).` : `Import failed: ${res.error}`);
    setIcs("");
    await refresh();
  }, [ics, refresh]);

  const doExport = useCallback(async () => {
    const res = await exportIcs();
    if (res.ok && res.ics) {
      await navigator.clipboard?.writeText(res.ics).catch(() => undefined);
      setInfo(`Exported ${res.event_count} event(s) as .ics (copied to clipboard).`);
    } else setInfo(`Export failed: ${res.error}`);
  }, []);

  const doSync = useCallback(async () => {
    const res = await caldavSync();
    setInfo(res.ok ? "CalDAV readonly sync complete." : res.hint || `Sync: ${res.error}`);
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS · WORKSPACE</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>Calendar</h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
              Local-first calendar with <code style={{ fontSize: 12 }}>.ics</code> import/export and
              per-calendar colors. CalDAV sync is <strong>read-only</strong> — it imports from remote
              calendars but doesn&apos;t write back to them.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
            <Link href="/" style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              ← Chat
            </Link>
            <Link href={missionControlHref("home")} style={{ ...mcButtonSecondaryStyle, textDecoration: "none", fontSize: 12 }}>
              Mission Control
            </Link>
          </div>
        </div>

        <WorkspaceNav active="calendar" />

        {error ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12, borderColor: "color-mix(in srgb, var(--aethos-danger) 45%, transparent)" }}>
            <p style={{ margin: 0, fontSize: 13, color: "var(--aethos-danger)" }}>
              {error === "workspace_suite_disabled"
                ? "The workspace suite is turned off for this deployment. Ask AethOS in chat how to enable it."
                : `Error: ${error}`}
            </p>
          </section>
        ) : null}

        {info ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12 }}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.cyan }}>{info}</p>
          </section>
        ) : null}

        <section style={{ ...mcPanelSectionStyle, marginBottom: 16, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <input value={summary} onChange={(e) => setSummary(e.target.value)} placeholder="Event title" style={{ ...inputStyle, flex: 2, minWidth: 160 }} />
          <input value={start} onChange={(e) => setStart(e.target.value)} placeholder="Start (20260604T090000Z)" style={{ ...inputStyle, flex: 1, minWidth: 140 }} />
          <input value={end} onChange={(e) => setEnd(e.target.value)} placeholder="End (optional)" style={{ ...inputStyle, flex: 1, minWidth: 140 }} />
          <button type="button" onClick={() => void submitEvent()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
            Add event
          </button>
          <button type="button" onClick={() => void doExport()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
            Export .ics
          </button>
          <button type="button" onClick={() => void doSync()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
            CalDAV sync (readonly)
          </button>
        </section>

        <div style={{ display: "grid", gridTemplateColumns: "1fr minmax(240px, 360px)", gap: 16 }}>
          <section style={mcPanelSectionStyle}>
            <h2 style={{ margin: "0 0 10px", fontSize: 14 }}>Events ({events.length})</h2>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
              {events.map((e) => (
                <li key={e.id} style={{ padding: "8px 10px", borderRadius: 8, border: `1px solid ${mcColors.border}`, background: "rgba(0,0,0,0.2)", display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ width: 10, height: 10, borderRadius: 999, background: colorFor(e.calendar), flexShrink: 0 }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>{e.summary}</div>
                    <div style={{ fontSize: 11, color: mcColors.textDim }}>
                      {e.start}{e.end ? ` → ${e.end}` : ""} · {e.calendar}
                    </div>
                  </div>
                  <button type="button" onClick={() => void deleteEvent(e.id).then(refresh)} aria-label="Delete event" style={{ background: "none", border: "none", color: mcColors.textDim, cursor: "pointer", fontSize: 14 }}>
                    ×
                  </button>
                </li>
              ))}
              {events.length === 0 ? <li style={{ fontSize: 12, color: mcColors.textMuted }}>No events yet.</li> : null}
            </ul>
          </section>

          <section style={mcPanelSectionStyle}>
            <h2 style={{ margin: "0 0 10px", fontSize: 14 }}>Import .ics</h2>
            <textarea
              value={ics}
              onChange={(e) => setIcs(e.target.value)}
              placeholder="Paste .ics text…"
              style={{ ...inputStyle, width: "100%", minHeight: 160, fontFamily: "ui-monospace, monospace", resize: "vertical", marginBottom: 8 }}
            />
            <button type="button" onClick={() => void doImport()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
              Import
            </button>
          </section>
        </div>
      </div>
    </div>
  );
}
