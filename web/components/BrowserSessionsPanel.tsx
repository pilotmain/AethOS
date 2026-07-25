"use client";

import { useCallback, useState } from "react";

import { SaveBrowserSessionPrompt } from "@/components/SaveBrowserSessionPrompt";
import {
  cancelBrowserSession,
  terminateBrowserSession,
  type BrowserSessionRecord,
  type BrowserSessionsResponse,
} from "@/lib/missionControl/browserSessions";
import { formatMcPanelError } from "@/lib/missionControl/panelError";

type Props = {
  data: BrowserSessionsResponse | null;
  onRefresh: () => void;
};

const btnBase = {
  marginTop: 8,
  borderRadius: 8,
  padding: "6px 12px",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};

function SessionCard({
  session,
  busyId,
  onTerminate,
  onCancel,
  onProfileSaved,
  dismissedSave,
  onDismissSave,
}: {
  session: BrowserSessionRecord;
  busyId: string | null;
  onTerminate: (id: string) => void;
  onCancel: (id: string) => void;
  onProfileSaved: () => void;
  dismissedSave: boolean;
  onDismissSave: (id: string) => void;
}) {
  const active = ["launching", "running", "waiting_for_operator"].includes(session.status);
  return (
    <li
      style={{
        padding: 12,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
        fontSize: 13,
      }}
    >
      <div style={{ fontWeight: 600 }}>{session.target}</div>
      <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
        Status: {session.status} · Mode: {session.mode ?? "supervised"}
      </div>
      <div style={{ color: "var(--aethos-text-muted)", marginTop: 4, fontSize: 12 }}>
        {session.url}
      </div>
      <div style={{ color: "var(--aethos-text-dim)", marginTop: 4, fontSize: 11 }}>
        <code>{session.id}</code>
        {session.heartbeat_age_sec != null && ` · heartbeat ${session.heartbeat_age_sec}s ago`}
        {session.browser_pid != null && ` · pid ${session.browser_pid}`}
      </div>
      {active && !dismissedSave && (
        <SaveBrowserSessionPrompt
          session={session}
          onSaved={onProfileSaved}
          onDismiss={() => onDismissSave(session.id)}
        />
      )}
      {active && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginTop: 8 }}>
          <button
            type="button"
            disabled={busyId === session.id}
            onClick={() => onTerminate(session.id)}
            style={{
              ...btnBase,
              border: "1px solid rgba(248,113,113,0.35)",
              background: "rgba(248,113,113,0.1)",
              color: "var(--aethos-danger)",
            }}
          >
            {busyId === session.id ? "Working…" : "Terminate"}
          </button>
          {session.status === "launching" && (
            <button
              type="button"
              disabled={busyId === session.id}
              onClick={() => onCancel(session.id)}
              style={{
                ...btnBase,
                border: "1px solid rgba(251,191,36,0.35)",
                background: "rgba(251,191,36,0.08)",
                color: "var(--aethos-warn)",
              }}
            >
              Cancel
            </button>
          )}
        </div>
      )}
    </li>
  );
}

export function BrowserSessionsPanel({ data, onRefresh }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [panelError, setPanelError] = useState("");
  const [dismissedSave, setDismissedSave] = useState<Set<string>>(() => new Set());

  const run = useCallback(
    async (id: string, fn: (id: string) => Promise<unknown>) => {
      setBusyId(id);
      setPanelError("");
      try {
        await fn(id);
        onRefresh();
      } catch (e) {
        setPanelError(formatMcPanelError(e instanceof Error ? e.message : "Request failed"));
      } finally {
        setBusyId(null);
      }
    },
    [onRefresh],
  );

  const sessions = data?.sessions ?? [];

  return (
    <section style={{ marginBottom: 16 }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>Browser sessions</h2>
        <button
          type="button"
          onClick={onRefresh}
          style={{
            ...btnBase,
            marginTop: 0,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "transparent",
            color: "var(--aethos-text-muted)",
          }}
        >
          Refresh
        </button>
      </div>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: "var(--aethos-text-muted)" }}>
        Supervised only — no credentials stored. Active: {data?.active_session_count ?? 0}
      </p>
      {panelError && (
        <p style={{ color: "var(--aethos-warn)", fontSize: 12, marginBottom: 8 }} role="status">
          {panelError}
        </p>
      )}
      {sessions.length === 0 ? (
        <p style={{ color: "var(--aethos-text-dim)", fontSize: 13 }}>No browser sessions yet.</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
          {sessions.map((s) => (
            <SessionCard
              key={s.id}
              session={s}
              busyId={busyId}
              onTerminate={(id) => void run(id, terminateBrowserSession)}
              onCancel={(id) => void run(id, cancelBrowserSession)}
              onProfileSaved={onRefresh}
              dismissedSave={dismissedSave.has(s.id)}
              onDismissSave={(id) =>
                setDismissedSave((prev) => new Set(prev).add(id))
              }
            />
          ))}
        </ul>
      )}
    </section>
  );
}
