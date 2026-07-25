"use client";

import { useEffect, useState } from "react";

import {
  fetchSubagentSessions,
  type SubagentSessionRow,
} from "@/lib/missionControl/subagentSessionsApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type Props = {
  parentSessionId?: string;
  onRefresh?: () => void;
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

/** Legacy archive view — primary surface is Orchestration. */
export function SubagentSessionsPanel({ parentSessionId = "operator", onRefresh }: Props) {
  const [sessions, setSessions] = useState<SubagentSessionRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchSubagentSessions(parentSessionId);
      setSessions(res.sessions ?? []);
      onRefresh?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, [parentSessionId]);

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div>
          <div style={{ fontSize: 16, fontWeight: 700, color: mcColors.text }}>Session archive</div>
          <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>
            Raw session log · parent {parentSessionId} · use Orchestration for day-to-day work
          </div>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {loading && <div style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading…</div>}
      {error && <div style={{ color: mcColors.red, fontSize: 13 }}>{error}</div>}

      {!loading && sessions.length === 0 && (
        <div style={{ color: mcColors.textMuted, fontSize: 13 }}>
          No sessions yet. In chat: <code>agent_spawn</code> with a goal, then follow up with <code>agent_send</code>.
        </div>
      )}

      {sessions.map((row) => (
        <div
          key={row.session_key}
          style={{
            padding: "10px 12px",
            marginBottom: 8,
            borderRadius: 8,
            border: `1px solid ${mcColors.border}`,
            background: mcColors.panelInset,
          }}
        >
          <button
            type="button"
            onClick={() => setExpanded(expanded === row.session_key ? null : row.session_key)}
            style={{
              all: "unset",
              cursor: "pointer",
              display: "block",
              width: "100%",
            }}
          >
            <div style={{ fontWeight: 600, fontSize: 13, color: mcColors.text }}>{row.session_key}</div>
            <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>
              {row.status ?? "unknown"} · runs: {row.run_count ?? 0} · {formatTs(row.updated_at)}
            </div>
            <div style={{ fontSize: 12, color: mcColors.text, marginTop: 6 }}>{(row.goal ?? "").slice(0, 160)}</div>
          </button>
          {expanded === row.session_key && (
            <div style={{ marginTop: 10, fontSize: 12, color: mcColors.textMuted }}>
              <div>plan_id: {row.plan_id ?? "—"}</div>
              <div>spawn_id: {row.spawn_id ?? "—"}</div>
              {(row.terminal_preflight_ids ?? []).length > 0 && (
                <div>terminal preflights: {(row.terminal_preflight_ids ?? []).join(", ")}</div>
              )}
              {(row.messages ?? []).slice(-6).map((m, i) => (
                <div key={i} style={{ marginTop: 6, paddingLeft: 8, borderLeft: `2px solid ${mcColors.border}` }}>
                  <strong>{m.role}</strong>
                  {m.source_tool ? ` · ${m.source_tool}` : ""}: {(m.content ?? "").slice(0, 200)}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
