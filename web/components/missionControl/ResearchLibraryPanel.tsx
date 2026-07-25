"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import Link from "next/link";

import {
  fetchResearchArtifacts,
  type ResearchArtifact,
} from "@/lib/missionControl/researchApi";
import { buildResearchReplayUrl } from "@/lib/missionControl/deepLinks";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function ResearchLibraryPanel() {
  const [history, setHistory] = useState<ResearchArtifact[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchResearchArtifacts(60);
      setHistory((res.artifacts ?? []).filter((a) => a.artifact_type === "research_replay"));
    } catch {
      setHistory([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (!q) return history;
    return history.filter((row) => {
      const query = String(row.payload?.query ?? "").toLowerCase();
      const replayId = String(row.payload?.replay_id ?? row.artifact_id).toLowerCase();
      return query.includes(q) || replayId.includes(q);
    });
  }, [filter, history]);

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Research library</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Saved replays with search — open any run in Deep Research.
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle} disabled={loading}>
          Refresh
        </button>
      </div>
      <input
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Filter by query or replay id…"
        style={{
          width: "100%",
          boxSizing: "border-box",
          marginTop: 14,
          padding: "10px 12px",
          borderRadius: 10,
          border: `1px solid ${mcColors.borderSubtle}`,
          background: "rgba(0,0,0,0.35)",
          color: mcColors.text,
          fontSize: 13,
        }}
      />
      <div style={{ marginTop: 14 }}>
        {filtered.length === 0 ? (
          <p style={{ fontSize: 13, color: mcColors.textMuted }}>No replays match.</p>
        ) : (
          filtered.slice(0, 20).map((row) => {
            const replayId = String(row.payload?.replay_id ?? row.artifact_id);
            const q = String(row.payload?.query ?? "Untitled");
            return (
              <div
                key={replayId}
                style={{
                  padding: "10px 0",
                  borderBottom: `1px solid ${mcColors.borderSubtle}`,
                  display: "flex",
                  justifyContent: "space-between",
                  gap: 12,
                  alignItems: "center",
                }}
              >
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 13, color: mcColors.text }}>{q.slice(0, 120)}</div>
                  <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>{replayId}</div>
                </div>
                <Link href={buildResearchReplayUrl(replayId)} style={{ fontSize: 12, color: mcColors.cyan, flexShrink: 0 }}>
                  Open →
                </Link>
              </div>
            );
          })
        )}
      </div>
    </section>
  );
}
