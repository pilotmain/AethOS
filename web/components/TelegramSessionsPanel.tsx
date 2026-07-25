"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchTelegramPreferences,
  fetchTelegramSessions,
  fetchTelegramStatus,
  setTelegramNotifyMode,
  type TelegramChannelStatus,
  type TelegramSessionEntry,
} from "@/lib/missionControl/channelsApi";
import { formatActivityTimestamp } from "@/lib/missionControl/connectionsCatalog";
import { formatMcPanelError } from "@/lib/missionControl/panelError";

function sessionStateLabel(state: string | undefined): string {
  switch (state) {
    case "awaiting_approval":
      return "Awaiting approval";
    case "active":
      return "Active";
    default:
      return "Idle";
  }
}

export function TelegramSessionsPanel() {
  const [sessions, setSessions] = useState<TelegramSessionEntry[]>([]);
  const [status, setStatus] = useState<TelegramChannelStatus | null>(null);
  const [defaultMode, setDefaultMode] = useState("calm");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  const inFlightRef = useRef(false);
  const mountedRef = useRef(true);

  const load = useCallback(async () => {
    if (inFlightRef.current) return;
    inFlightRef.current = true;
    setLoading(true);
    setError("");
    try {
      const [sess, prefs, st] = await Promise.all([
        fetchTelegramSessions(),
        fetchTelegramPreferences(),
        fetchTelegramStatus(),
      ]);
      if (!mountedRef.current) return;
      setSessions(sess.sessions ?? []);
      setStatus(st);
      setDefaultMode(String(prefs.default_mode ?? "calm"));
    } catch (e) {
      if (!mountedRef.current) return;
      setError(formatMcPanelError(e instanceof Error ? e.message : "Load failed"));
    } finally {
      inFlightRef.current = false;
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    void load();
    return () => {
      mountedRef.current = false;
    };
  }, [load]);

  const onModeChange = async (mode: string) => {
    if (mode === defaultMode || busy === "mode") return;
    setBusy("mode");
    setError("");
    try {
      await setTelegramNotifyMode({ mode });
      setDefaultMode(mode);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not update notification mode.");
    } finally {
      setBusy("");
    }
  };

  return (
    <section
      style={{
        marginBottom: 16,
        padding: 14,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
        <h2 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>Active Telegram sessions</h2>
        <button type="button" disabled={loading} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      <p style={{ margin: "6px 0 12px", fontSize: 12, color: "var(--aethos-text-dim)" }}>
        Channel transport sessions — approvals remain in Mission Control → Jobs.
      </p>

      {status?.typing ? (
        <div
          style={{
            marginBottom: 12,
            padding: 10,
            borderRadius: 10,
            border: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(0,0,0,0.12)",
            fontSize: 12,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Typing & progress</div>
          <div>Typing enabled: {String(status.typing.typing_enabled ?? false)}</div>
          <div>Progress messages: {String(status.typing.progress_messages_enabled ?? false)}</div>
          <div>
            Last typing sent: {formatActivityTimestamp(status.typing.last_typing_sent_at ?? undefined)}
          </div>
          <div>Webhook: {status.webhook?.configured ? "configured" : "not configured"}</div>
          <div>Telegram API: {status.telegram_api_status ?? status.transport_health ?? "—"}</div>
          {status.typing.last_typing_error ? (
            <div style={{ color: "var(--aethos-warn)", marginTop: 4 }}>Typing error: {status.typing.last_typing_error}</div>
          ) : null}
        </div>
      ) : null}

      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Notification mode</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {(["calm", "verbose", "completion_only"] as const).map((mode) => (
            <button
              key={mode}
              type="button"
              disabled={busy === "mode"}
              onClick={() => void onModeChange(mode)}
              style={{
                borderRadius: 8,
                padding: "6px 10px",
                fontSize: 12,
                border: defaultMode === mode ? "1px solid rgba(34,211,238,0.5)" : "1px solid rgba(255,255,255,0.12)",
                background: defaultMode === mode ? "rgba(34,211,238,0.12)" : "transparent",
                color: defaultMode === mode ? "var(--aethos-text-strong)" : "var(--aethos-text-muted)",
              }}
            >
              {mode.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <p style={{ color: "var(--aethos-warn)", fontSize: 12 }} role="status">
          {error}
          {" "}
          <button type="button" disabled={loading} onClick={() => void load()} style={{ marginLeft: 6 }}>
            Retry
          </button>
        </p>
      ) : null}

      {loading && sessions.length === 0 && !error ? (
        <p style={{ color: "var(--aethos-text-muted)", fontSize: 13 }}>Loading sessions…</p>
      ) : sessions.length === 0 ? (
        <p style={{ color: "var(--aethos-text-dim)", fontSize: 13 }}>No Telegram sessions yet.</p>
      ) : (
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 10 }}>
          {sessions.map((s) => (
            <li
              key={s.session_id}
              style={{
                padding: 12,
                borderRadius: 10,
                border: "1px solid rgba(255,255,255,0.08)",
                background: "rgba(255,255,255,0.02)",
                fontSize: 12,
              }}
            >
              <div style={{ fontWeight: 600 }}>
                <code>{s.session_id}</code>
                {s.chat_id_masked ? ` · chat ${s.chat_id_masked}` : ""}
              </div>
              <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
                State: {sessionStateLabel(s.session_state)}
                {s.pending_approval_job_id ? ` · pending job ${s.pending_approval_job_id}` : ""}
              </div>
              {s.last_operation ? (
                <div style={{ color: "var(--aethos-text-dim)", marginTop: 4 }}>Last operation: {s.last_operation}</div>
              ) : null}
              {s.last_message_preview ? (
                <div style={{ color: "var(--aethos-text-dim)", marginTop: 4 }}>Last message: {s.last_message_preview}</div>
              ) : null}
              <div style={{ color: "var(--aethos-text-dim)", marginTop: 4, fontSize: 11 }}>
                Received: {formatActivityTimestamp(s.last_received_at)} · Sent:{" "}
                {formatActivityTimestamp(s.last_sent_at)}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
