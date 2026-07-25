"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AppNav } from "@/components/AppNav";
import { fetchCanvasState, type CanvasState, type CanvasView } from "@/lib/canvas/canvasApi";
import { getActiveSessionId, subscribeActiveChatSessionId } from "@/lib/chat/chatThreads";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { missionControlHref } from "@/lib/missionControl/deepLinks";

const VIEW_BADGES: Record<string, string> = {
  status: "Status",
  diff: "Diff",
  research_report: "Research",
  job_timeline: "Job timeline",
  table: "Table",
  markdown: "Markdown",
};

function asRecord(data: unknown): Record<string, unknown> {
  return data && typeof data === "object" && !Array.isArray(data) ? (data as Record<string, unknown>) : {};
}

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? (value as T[]) : [];
}

function statusColor(status: string): string {
  const low = status.toLowerCase();
  if (["failed", "error", "crashed", "cancelled", "canceled"].some((s) => low.includes(s))) return "#f87171";
  if (["running", "success", "ready", "healthy", "completed", "active"].some((s) => low.includes(s))) return "#34d399";
  if (["pending", "queued", "building", "deploying"].some((s) => low.includes(s))) return "#fbbf24";
  return mcColors.textMuted;
}

function JobTimelineView({ data }: { data: Record<string, unknown> }) {
  const events = asArray<Record<string, unknown>>(data.events);
  const rows = events.length ? events : asArray<Record<string, unknown>>(data.rows);
  if (!rows.length) {
    return <p style={{ fontSize: 13, color: mcColors.textMuted }}>No timeline events in this view.</p>;
  }
  return (
    <ol style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
      {rows.map((row, idx) => {
        const label = String(row.label ?? row.name ?? row.title ?? row.id ?? `Event ${idx + 1}`);
        const status = String(row.status ?? row.state ?? row.phase ?? "—");
        const when = String(row.timestamp ?? row.time ?? row.created_at ?? row.duration ?? "");
        const detail = String(row.detail ?? row.message ?? row.description ?? "");
        return (
          <li
            key={`${label}-${idx}`}
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(0, 1fr) auto",
              gap: 8,
              padding: "10px 12px",
              borderRadius: 10,
              background: "rgba(0,0,0,0.35)",
              border: `1px solid ${mcColors.border}`,
            }}
          >
            <div>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{label}</div>
              {detail ? <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>{detail}</div> : null}
              {when ? <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>{when}</div> : null}
            </div>
            <span style={{ fontSize: 11, fontWeight: 700, color: statusColor(status), alignSelf: "start" }}>{status}</span>
          </li>
        );
      })}
    </ol>
  );
}

function normalizeKey(s: string): string {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "");
}

/** Resolve a column header against a row whose keys may differ in case/spacing/punctuation
 * (e.g. column "Project / Service" vs row key "project_service" or "service"). */
function cellForColumn(row: Record<string, unknown>, col: string): string {
  if (col in row && row[col] != null && row[col] !== "") return String(row[col]);
  const target = normalizeKey(col);
  for (const [k, v] of Object.entries(row)) {
    if (normalizeKey(k) === target && v != null && v !== "") return String(v);
  }
  // Fall back to a token-overlap match (e.g. "Project / Service" → "service").
  for (const [k, v] of Object.entries(row)) {
    const nk = normalizeKey(k);
    if (nk && (target.includes(nk) || nk.includes(target)) && v != null && v !== "") return String(v);
  }
  return "—";
}

function TableView({ data }: { data: Record<string, unknown> }) {
  const rows = asArray<Record<string, unknown>>(data.rows);
  const columns = asArray<string>(data.columns);
  const inferredCols =
    columns.length > 0
      ? columns
      : rows.length > 0
        ? Object.keys(rows[0] ?? {}).slice(0, 8)
        : [];
  if (!rows.length) {
    return <p style={{ fontSize: 13, color: mcColors.textMuted }}>No table rows in this view.</p>;
  }
  return (
    <div style={{ overflowX: "auto" }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
        <thead>
          <tr>
            {inferredCols.map((col) => (
              <th
                key={col}
                style={{
                  textAlign: "left",
                  padding: "8px 10px",
                  borderBottom: `1px solid ${mcColors.border}`,
                  color: mcColors.textMuted,
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {inferredCols.map((col) => (
                <td key={col} style={{ padding: "8px 10px", borderBottom: `1px solid ${mcColors.border}` }}>
                  {cellForColumn(row, col)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function DiffView({ data }: { data: Record<string, unknown> }) {
  const hunks = asArray<Record<string, unknown>>(data.hunks);
  const lines = asArray<string>(data.lines);
  const before = data.before ?? data.old_text;
  const after = data.after ?? data.new_text;
  if (hunks.length) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {hunks.map((hunk, idx) => (
          <pre
            key={idx}
            style={{
              margin: 0,
              padding: 12,
              borderRadius: 8,
              background: "rgba(0,0,0,0.35)",
              fontSize: 12,
              whiteSpace: "pre-wrap",
            }}
          >
            {String(hunk.content ?? hunk.text ?? JSON.stringify(hunk))}
          </pre>
        ))}
      </div>
    );
  }
  if (lines.length) {
    return (
      <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
        {lines.join("\n")}
      </pre>
    );
  }
  if (before != null || after != null) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
        <div>
          <div style={{ fontSize: 11, color: mcColors.textDim, marginBottom: 6 }}>Before</div>
          <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap" }}>{String(before ?? "")}</pre>
        </div>
        <div>
          <div style={{ fontSize: 11, color: mcColors.textDim, marginBottom: 6 }}>After</div>
          <pre style={{ margin: 0, fontSize: 12, whiteSpace: "pre-wrap" }}>{String(after ?? "")}</pre>
        </div>
      </div>
    );
  }
  return <p style={{ fontSize: 13, color: mcColors.textMuted }}>No diff content in this view.</p>;
}

function MarkdownView({ data }: { data: Record<string, unknown> }) {
  const content = String(data.content ?? data.markdown ?? data.text ?? "");
  if (!content.trim()) {
    return <p style={{ fontSize: 13, color: mcColors.textMuted }}>Empty markdown view.</p>;
  }
  return (
    <pre style={{ margin: 0, fontSize: 13, lineHeight: 1.55, whiteSpace: "pre-wrap", color: mcColors.text }}>
      {content}
    </pre>
  );
}

function StatusView({ data }: { data: Record<string, unknown> }) {
  const items = asArray<Record<string, unknown>>(data.items ?? data.services ?? data.checks ?? data.rows);
  if (items.length) {
    return (
      <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
        {items.map((item, idx) => {
          const name = String(item.name ?? item.label ?? item.service ?? item.key ?? `Item ${idx + 1}`);
          const status = String(item.status ?? item.health ?? item.state ?? "—");
          return (
            <li
              key={idx}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 12,
                padding: "8px 10px",
                borderRadius: 8,
                background: "rgba(0,0,0,0.3)",
              }}
            >
              <span style={{ fontSize: 13 }}>{name}</span>
              <span style={{ fontSize: 12, color: statusColor(status) }}>{status}</span>
            </li>
          );
        })}
      </ul>
    );
  }
  const status = String(data.status ?? "");
  const fields = asRecord(data.fields);
  if (status || Object.keys(fields).length) {
    return (
      <div style={{ fontSize: 13 }}>
        {status ? <div style={{ marginBottom: 8 }}><strong>Status:</strong> {status}</div> : null}
        {Object.entries(fields).map(([k, v]) => (
          <div key={k} style={{ marginBottom: 4 }}>
            <span style={{ color: mcColors.textMuted }}>{k}: </span>{String(v)}
          </div>
        ))}
      </div>
    );
  }
  return <p style={{ fontSize: 13, color: mcColors.textMuted }}>No status fields in this view.</p>;
}

function ResearchReportView({ data }: { data: Record<string, unknown> }) {
  const sections = asArray<Record<string, unknown>>(data.sections ?? data.findings);
  if (sections.length) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
        {sections.map((section, idx) => (
          <div key={idx}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 4 }}>
              {String(section.title ?? section.heading ?? `Section ${idx + 1}`)}
            </div>
            <div style={{ fontSize: 13, color: mcColors.textMuted, lineHeight: 1.5 }}>
              {String(section.content ?? section.body ?? section.summary ?? "")}
            </div>
          </div>
        ))}
      </div>
    );
  }
  return <MarkdownView data={data} />;
}

function ViewBody({ view }: { view: CanvasView }) {
  const data = asRecord(view.data);
  switch (view.view_type) {
    case "job_timeline":
      return <JobTimelineView data={data} />;
    case "table":
      return <TableView data={data} />;
    case "diff":
      return <DiffView data={data} />;
    case "markdown":
      return <MarkdownView data={data} />;
    case "status":
      return <StatusView data={data} />;
    case "research_report":
      return <ResearchReportView data={data} />;
    default:
      return <MarkdownView data={data} />;
  }
}

function resolveInitialSession(): { sessionId: string; hasLive: boolean } {
  if (typeof window === "undefined") {
    return { sessionId: "default", hasLive: false };
  }
  try {
    const sid = getActiveSessionId();
    return { sessionId: sid, hasLive: Boolean(sid && sid.trim()) };
  } catch {
    return { sessionId: "default", hasLive: false };
  }
}

export function LiveCanvasPanel() {
  const initial = resolveInitialSession();
  const [sessionId, setSessionId] = useState(initial.sessionId);
  const [boundToChat, setBoundToChat] = useState(true);
  const [hasLiveSession, setHasLiveSession] = useState(initial.hasLive);
  const [state, setState] = useState<CanvasState | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!boundToChat) return;
    return subscribeActiveChatSessionId((sid) => {
      if (sid) {
        setSessionId(sid);
        setHasLiveSession(Boolean(sid.trim()));
      }
    });
  }, [boundToChat]);

  const load = useCallback(
    async (opts?: { silent?: boolean }) => {
      if (!opts?.silent) setLoading(true);
      try {
        const next = await fetchCanvasState(sessionId, 20, {
          revalidate: (fresh) => setState(fresh),
        });
        setState(next);
      } finally {
        if (!opts?.silent) setLoading(false);
      }
    },
    [sessionId],
  );

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!boundToChat) return;
    let timer: number | null = null;

    const schedule = () => {
      if (timer !== null) window.clearInterval(timer);
      if (document.visibilityState !== "visible") return;
      timer = window.setInterval(() => void load({ silent: true }), 2500);
    };

    const onVisibility = () => {
      if (document.visibilityState === "visible") {
        void load({ silent: true });
        schedule();
      } else if (timer !== null) {
        window.clearInterval(timer);
        timer = null;
      }
    };

    schedule();
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      if (timer !== null) window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [boundToChat, load]);

  const views = state?.views ?? [];
  const showingLatest = Boolean(state?.showing_latest_render);

  return (
    <div
      style={{
        // Global `body { overflow: hidden }` (for the chat SPA) means this panel must own
        // its own scroll, or tall renders get clipped with no way to scroll down.
        height: "100vh",
        overflowY: "auto",
        background: "var(--aethos-bg)",
        color: mcColors.text,
        padding: "24px 20px",
      }}
    >
      <div style={{ maxWidth: 1100, margin: "0 auto" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.08em", color: mcColors.textDim }}>AETHOS</div>
            <h1 className="aethos-gradient-text" style={{ margin: "6px 0 4px", fontSize: 22, fontWeight: 700 }}>Live Canvas</h1>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 560 }}>
              AethOS draws status views, timelines, diffs, and tables here when you ask it to
              render something to the canvas. It’s a view-only surface — AethOS can show things
              here but can’t run actions from it; governed actions stay in Mission Control.
            </p>
            <AppNav active="canvas" />
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

        <section style={{ ...mcPanelSectionStyle, marginBottom: 16, display: "flex", gap: 8, alignItems: "center" }}>
          <label style={{ fontSize: 12, color: mcColors.textMuted }}>
            Session {boundToChat ? <span style={{ color: mcColors.cyan }}>· live chat</span> : <span style={{ color: mcColors.textDim }}>· manual</span>}
          </label>
          <input
            value={sessionId}
            onChange={(e) => {
              setBoundToChat(false);
              setSessionId(e.target.value);
            }}
            style={{
              flex: 1,
              maxWidth: 280,
              padding: "8px 10px",
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: "rgba(0,0,0,0.3)",
              color: mcColors.text,
              fontSize: 13,
            }}
          />
          <button type="button" onClick={() => void load()} style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}>
            Refresh
          </button>
          {!boundToChat ? (
            <button
              type="button"
              onClick={() => setBoundToChat(true)}
              style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}
            >
              Use live chat session
            </button>
          ) : null}
          <span style={{ fontSize: 11, color: mcColors.textDim, marginLeft: "auto" }}>read-only</span>
        </section>

        {loading && !state ? <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading canvas…</p> : null}

        {showingLatest && views.length > 0 ? (
          <section style={{ ...mcPanelSectionStyle, marginBottom: 12, padding: "10px 14px" }}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.cyan }}>
              Showing your most recent render{state?.resolved_session ? ` (session ${state.resolved_session})` : ""}.
            </p>
          </section>
        ) : null}

        {boundToChat && !hasLiveSession && views.length === 0 ? (
          <section style={mcPanelSectionStyle}>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
              Waiting for a live chat session — open <strong>Chat</strong> and send a message, then ask
              AethOS to render here. The Canvas binds to the same session id the composer uses.
            </p>
          </section>
        ) : null}

        {!loading && views.length === 0 && (hasLiveSession || !boundToChat) ? (
          <section style={mcPanelSectionStyle}>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
              Nothing here yet. In chat, ask AethOS to draw something — e.g. “render a job timeline on the canvas”.
            </p>
          </section>
        ) : null}

        <div
          style={{
            // Let the page scroll naturally instead of trapping tall renders (research
            // reports, long timelines) inside a nested fixed-height scroll box.
            display: "flex",
            flexDirection: "column",
            gap: 12,
            paddingRight: 4,
            paddingBottom: 48,
          }}
        >
          {views.map((view) => (
            <section key={view.id} style={{ ...mcPanelSectionStyle, marginBottom: 0 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 8 }}>
                <h2 style={{ margin: 0, fontSize: 16 }}>{view.title}</h2>
                <span style={{ fontSize: 11, color: mcColors.cyan }}>{VIEW_BADGES[view.view_type] || view.view_type}</span>
              </div>
              <ViewBody view={view} />
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}
