"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  addNote,
  addTask,
  deleteNote,
  deleteTask,
  listNotes,
  listTasks,
  setTaskDone,
  type WorkspaceNote,
  type WorkspaceTask,
} from "@/lib/workspace/notesApi";
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

export function NotesTasksPanel() {
  const [notes, setNotes] = useState<WorkspaceNote[]>([]);
  const [tasks, setTasks] = useState<WorkspaceTask[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [noteText, setNoteText] = useState("");
  const [taskText, setTaskText] = useState("");
  const [schedule, setSchedule] = useState("");

  const refresh = useCallback(async () => {
    const [n, t] = await Promise.all([listNotes(), listTasks()]);
    if (!n.ok) setError(n.error || "load_failed");
    else if (!t.ok) setError(t.error || "load_failed");
    else setError(null);
    setNotes(n.notes || []);
    setTasks(t.tasks || []);
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const submitNote = useCallback(async () => {
    if (!noteText.trim()) return;
    await addNote(noteText.trim());
    setNoteText("");
    await refresh();
  }, [noteText, refresh]);

  const submitTask = useCallback(async () => {
    if (!taskText.trim()) return;
    await addTask(taskText.trim(), schedule.trim() || undefined);
    setTaskText("");
    setSchedule("");
    await refresh();
  }, [taskText, schedule, refresh]);

  return (
    <div style={{ minHeight: "100vh", background: "var(--aethos-bg)", color: mcColors.text, padding: "24px 20px" }}>
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS · WORKSPACE</div>
            <h1 style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>Notes &amp; Tasks</h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
              Quick notes and checklist tasks, local-first. Scheduled tasks are{" "}
              <strong>recorded only</strong> — they never auto-run; any action requires your approval first.
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

        <WorkspaceNav active="notes" />

        {error ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12, borderColor: "color-mix(in srgb, var(--aethos-danger) 45%, transparent)" }}>
            <p style={{ margin: 0, fontSize: 13, color: "var(--aethos-danger)" }}>
              {error === "workspace_suite_disabled"
                ? "The workspace suite is turned off for this deployment. Ask AethOS in chat how to enable it."
                : `Error: ${error}`}
            </p>
          </section>
        ) : null}

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <section style={mcPanelSectionStyle}>
            <h2 style={{ margin: "0 0 10px", fontSize: 15 }}>Tasks</h2>
            <div style={{ display: "flex", gap: 8, marginBottom: 6 }}>
              <input
                value={taskText}
                onChange={(e) => setTaskText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void submitTask()}
                placeholder="New task…"
                style={{ ...inputStyle, flex: 1 }}
              />
            </div>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <input
                value={schedule}
                onChange={(e) => setSchedule(e.target.value)}
                placeholder="Schedule hint (optional, e.g. daily 9am)"
                style={{ ...inputStyle, flex: 1 }}
              />
              <button type="button" onClick={() => void submitTask()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
                Add
              </button>
            </div>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
              {tasks.map((t) => (
                <li
                  key={t.id}
                  style={{
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: `1px solid ${mcColors.border}`,
                    background: "rgba(0,0,0,0.2)",
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                  }}
                >
                  <input
                    type="checkbox"
                    checked={t.done}
                    onChange={(e) => void setTaskDone(t.id, e.target.checked).then(refresh)}
                  />
                  <div style={{ flex: 1, fontSize: 13, textDecoration: t.done ? "line-through" : "none", color: t.done ? mcColors.textDim : mcColors.text }}>
                    {t.text}
                    {t.scheduled_for ? (
                      <span style={{ marginLeft: 8, fontSize: 11, color: mcColors.cyan }}>⏰ {t.scheduled_for} (recorded only)</span>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    onClick={() => void deleteTask(t.id).then(refresh)}
                    aria-label="Delete task"
                    style={{ background: "none", border: "none", color: mcColors.textDim, cursor: "pointer", fontSize: 14 }}
                  >
                    ×
                  </button>
                </li>
              ))}
              {tasks.length === 0 ? <li style={{ fontSize: 12, color: mcColors.textMuted }}>No tasks yet.</li> : null}
            </ul>
          </section>

          <section style={mcPanelSectionStyle}>
            <h2 style={{ margin: "0 0 10px", fontSize: 15 }}>Notes</h2>
            <div style={{ display: "flex", gap: 8, marginBottom: 12 }}>
              <input
                value={noteText}
                onChange={(e) => setNoteText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && void submitNote()}
                placeholder="Quick note…"
                style={{ ...inputStyle, flex: 1 }}
              />
              <button type="button" onClick={() => void submitNote()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
                Pin
              </button>
            </div>
            <ul style={{ listStyle: "none", margin: 0, padding: 0, display: "flex", flexDirection: "column", gap: 6 }}>
              {notes.map((n) => (
                <li
                  key={n.id}
                  style={{
                    padding: "8px 10px",
                    borderRadius: 8,
                    border: `1px solid ${mcColors.border}`,
                    background: "rgba(0,0,0,0.2)",
                    display: "flex",
                    alignItems: "flex-start",
                    gap: 8,
                  }}
                >
                  <div style={{ flex: 1, fontSize: 13, whiteSpace: "pre-wrap" }}>{n.text}</div>
                  <button
                    type="button"
                    onClick={() => void deleteNote(n.id).then(refresh)}
                    aria-label="Delete note"
                    style={{ background: "none", border: "none", color: mcColors.textDim, cursor: "pointer", fontSize: 14 }}
                  >
                    ×
                  </button>
                </li>
              ))}
              {notes.length === 0 ? <li style={{ fontSize: 12, color: mcColors.textMuted }}>No notes yet.</li> : null}
            </ul>
          </section>
        </div>
      </div>
    </div>
  );
}
