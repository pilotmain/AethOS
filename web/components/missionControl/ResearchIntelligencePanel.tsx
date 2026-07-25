"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchResearchArtifacts,
  fetchResearchReplay,
  fetchResearchProviders,
  type ResearchArtifact,
  type ResearchReplay,
} from "@/lib/missionControl/researchApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type Props = {
  artifacts: ResearchArtifact[];
  onRefresh: () => void;
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function confidenceChip(score?: number) {
  if (score == null) return mcColors.textMuted;
  if (score >= 0.75) return "var(--aethos-ok)";
  if (score >= 0.5) return "var(--aethos-warn)";
  return "var(--aethos-danger)";
}

export function ResearchIntelligencePanel({ artifacts, onRefresh }: Props) {
  const [providers, setProviders] = useState<{ provider_id: string; role: string }[]>([]);
  const [replay, setReplay] = useState<ResearchReplay | null>(null);
  const [replayId, setReplayId] = useState("");

  const syntheses = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "research_synthesis"),
    [artifacts],
  );
  const evidenceSets = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "research_result_set"),
    [artifacts],
  );
  const contradictions = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "research_contradiction_report"),
    [artifacts],
  );
  const replays = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "research_replay"),
    [artifacts],
  );

  useEffect(() => {
    fetchResearchProviders()
      .then((d) => setProviders(d.providers ?? []))
      .catch(() => setProviders([]));
  }, []);

  const loadReplay = useCallback(async (id: string) => {
    if (!id.trim()) return;
    try {
      const data = await fetchResearchReplay(id.trim());
      setReplay(data.replay ?? null);
      setReplayId(id.trim());
    } catch {
      setReplay(null);
    }
  }, []);

  useEffect(() => {
    const latest = replays[0]?.payload?.replay_id ?? replays[0]?.artifact_id;
    if (latest && !replayId) {
      void loadReplay(String(latest));
    }
  }, [replays, replayId, loadReplay]);

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Research Intelligence</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Orchestrated retrieval, confidence scoring, contradictions, synthesis, and replay timeline.
          </p>
        </div>
        <button type="button" onClick={onRefresh} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {providers.length > 0 && (
        <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", gap: 8 }}>
          {providers.map((p) => (
            <span
              key={p.provider_id}
              style={{
                fontSize: 12,
                padding: "4px 10px",
                borderRadius: 999,
                background: "rgba(255,255,255,0.06)",
                border: `1px solid ${mcColors.borderSubtle}`,
              }}
            >
              {p.provider_id} · {p.role}
            </span>
          ))}
        </div>
      )}

      <div style={{ marginTop: 18, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        <div>
          <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Synthesized reports</h3>
          {syntheses.length === 0 ? (
            <p style={{ fontSize: 13, color: mcColors.textMuted }}>No syntheses yet.</p>
          ) : (
            syntheses.slice(0, 8).map((art) => {
              const payload = art.payload ?? {};
              const synthesis = (payload.synthesis as { summary?: string; bullets?: string[] }) ?? {};
              return (
                <div
                  key={art.artifact_id}
                  style={{
                    marginBottom: 10,
                    padding: 10,
                    borderRadius: 10,
                    background: "rgba(0,0,0,0.15)",
                    fontSize: 13,
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{String(payload.query ?? "—")}</div>
                  <div style={{ marginTop: 4, color: mcColors.textMuted }}>{synthesis.summary ?? "—"}</div>
                  <div style={{ marginTop: 4, fontSize: 12, color: mcColors.textMuted }}>
                    {formatTs(art.created_at)} · {art.artifact_id}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div>
          <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Evidence explorer</h3>
          {evidenceSets.length === 0 ? (
            <p style={{ fontSize: 13, color: mcColors.textMuted }}>No evidence sets yet.</p>
          ) : (
            evidenceSets.slice(0, 4).map((art) => {
              const evidence = ((art.payload as { evidence?: Record<string, unknown>[] })?.evidence ?? []).slice(0, 4);
              return (
                <div key={art.artifact_id} style={{ marginBottom: 10, fontSize: 12 }}>
                  <div style={{ fontWeight: 600, marginBottom: 4 }}>{String((art.payload as { query?: string })?.query ?? "—")}</div>
                  {evidence.map((ev) => (
                    <div
                      key={String(ev.citation_id)}
                      style={{
                        padding: "8px 10px",
                        marginBottom: 6,
                        borderRadius: 8,
                        background: "rgba(0,0,0,0.12)",
                      }}
                    >
                      <div>{String(ev.title ?? "—")}</div>
                      <div style={{ color: confidenceChip(Number(ev.confidence)), marginTop: 2 }}>
                        conf {Number(ev.confidence ?? 0).toFixed(2)} · fresh {Number(ev.freshness_score ?? 0).toFixed(2)}
                      </div>
                    </div>
                  ))}
                </div>
              );
            })
          )}
        </div>
      </div>

      {contradictions.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600, color: mcColors.amber }}>Contradictions</h3>
          {contradictions.slice(0, 4).map((art) => (
            <div key={art.artifact_id} style={{ fontSize: 12, color: mcColors.amber, marginBottom: 6 }}>
              {String((art.payload as { query?: string })?.query ?? art.artifact_id)}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: 18 }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>Research replay</h3>
        <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
          <input
            value={replayId}
            onChange={(e) => setReplayId(e.target.value)}
            placeholder="rrun-..."
            style={{
              flex: 1,
              padding: "8px 10px",
              borderRadius: 8,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.2)",
              color: "inherit",
              fontSize: 13,
            }}
          />
          <button type="button" style={mcButtonSecondaryStyle} onClick={() => loadReplay(replayId)}>
            Load
          </button>
        </div>
        {(replay?.payload?.timeline ?? []).length === 0 ? (
          <p style={{ fontSize: 13, color: mcColors.textMuted }}>Select a replay ID to view orchestration timeline.</p>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
            {(replay?.payload?.timeline ?? []).map((step, i) => (
              <li
                key={`${step.step}-${i}`}
                style={{
                  padding: "8px 10px",
                  marginBottom: 6,
                  borderRadius: 8,
                  background: "rgba(0,0,0,0.12)",
                }}
              >
                <strong>{step.step}</strong> — {step.detail ?? ""}{" "}
                <span style={{ color: mcColors.textMuted }}>({formatTs(step.at)})</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
