"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import {
  fetchResearchArtifacts,
  fetchResearchReplay,
  fetchResearchStatus,
  postResearchQuery,
  type ResearchArtifact,
  type ResearchStatus,
} from "@/lib/missionControl/researchApi";
import { readMissionControlReplayId } from "@/lib/missionControl/deepLinks";
import { mcAlpha, mcButtonPrimaryStyle, mcButtonSecondaryStyle, mcColors, mcGradientTextStyle, mcPanelSectionStyle } from "@/lib/missionControl/layout";

const STEP_LABELS: Record<string, string> = {
  plan: "Planning",
  retrieve: "Gathering sources",
  confidence: "Scoring evidence",
  synthesis: "Writing report",
  complete: "Done",
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

function formatDuration(start?: number, end?: number) {
  if (!start || !end) return "";
  const sec = Math.max(0, Math.round(end - start));
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function DeepResearchPanel({ embedded = false }: { embedded?: boolean }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<ResearchStatus | null>(null);
  const [history, setHistory] = useState<ResearchArtifact[]>([]);
  const [activeReplayId, setActiveReplayId] = useState<string | null>(null);
  const [activeTimeline, setActiveTimeline] = useState<{ step?: string; detail?: string; at?: number; source_count?: number }[]>([]);
  const [activeReport, setActiveReport] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetchResearchArtifacts(40);
      const replays = (res.artifacts ?? []).filter((a) => a.artifact_type === "research_replay");
      setHistory(replays);
    } catch {
      setHistory([]);
    }
  }, []);

  useEffect(() => {
    fetchResearchStatus()
      .then(setStatus)
      .catch(() => setStatus(null));
    void loadHistory();
  }, [loadHistory]);

  const startResearch = async () => {
    const message = query.trim();
    if (message.length < 8) {
      setError("Enter a question or comparison (at least 8 characters).");
      return;
    }
    setError(null);
    setLoading(true);
    setActiveReport(null);
    setActiveTimeline([]);
    try {
      const result = await postResearchQuery(message);
      setActiveReplayId(result.replay_id);
      const replay = await fetchResearchReplay(result.replay_id);
      setActiveTimeline(replay.replay?.payload?.timeline ?? []);
      setActiveReport(result.reply ?? "");
      setQuery("");
      await loadHistory();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Research failed");
    } finally {
      setLoading(false);
    }
  };

  const openReplay = useCallback(async (replayId: string) => {
    setActiveReplayId(replayId);
    setActiveReport(null);
    try {
      const data = await fetchResearchReplay(replayId);
      setActiveTimeline(data.replay?.payload?.timeline ?? []);
      const synth = history.find(
        (h) => h.payload?.replay_id === replayId && h.artifact_type === "research_synthesis",
      );
      if (synth?.payload?.synthesis) {
        setActiveReport("Open chat or re-run to view full markdown — synthesis artifact saved.");
      }
    } catch {
      setActiveTimeline([]);
    }
  }, [history]);

  useEffect(() => {
    const deepLinkReplay = readMissionControlReplayId();
    if (!deepLinkReplay) return;
    void openReplay(deepLinkReplay);
  }, [openReplay]);

  const activeStep = useMemo(() => {
    if (loading) return "retrieve";
    const last = activeTimeline[activeTimeline.length - 1];
    return last?.step ?? "";
  }, [activeTimeline, loading]);

  const sourceCount = useMemo(() => {
    const synth = activeTimeline.find((s) => s.step === "synthesis");
    return synth?.source_count ?? activeTimeline.find((s) => s.step === "retrieve")?.detail?.match(/(\d+)/)?.[1];
  }, [activeTimeline]);

  const card = {
    padding: "14px 16px",
    borderRadius: 14,
    border: `1px solid ${mcColors.borderSubtle}`,
    background: "rgba(0,0,0,0.22)",
    marginBottom: 12,
  } as const;

  return (
    <section style={embedded ? { marginBottom: 0 } : mcPanelSectionStyle}>
      {!embedded ? (
        <div style={{ marginBottom: 20 }}>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 750, letterSpacing: "-0.02em", width: "fit-content", ...mcGradientTextStyle }}>
            Research
          </h2>
        <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted, maxWidth: 560 }}>
          Compare ideas, build evidence-backed wikis, and replay sources — not just chat text.
        </p>
        {status && !status.configured ? (
          <p style={{ marginTop: 10, fontSize: 12, color: mcColors.amber }}>
            Web research is not fully configured. Set `WEB_RESEARCH_ENABLED=true` and Tavily key in `.env`, then restart.
          </p>
        ) : null}
      </div>
      ) : null}

      <div style={card}>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Compare GBrain by Garry Tan to Kaparthay's LLM wiki idea — which is best for a personal second brain?"
          rows={3}
          style={{
            width: "100%",
            boxSizing: "border-box",
            padding: "12px 14px",
            borderRadius: 10,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: "rgba(0,0,0,0.35)",
            color: mcColors.text,
            fontSize: 14,
            resize: "vertical",
          }}
        />
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 10 }}>
          <button type="button" style={mcButtonPrimaryStyle} disabled={loading} onClick={() => void startResearch()}>
            {loading ? "Researching…" : "Start research"}
          </button>
        </div>
        {error ? <p style={{ color: mcColors.red, fontSize: 12, marginTop: 8 }}>{error}</p> : null}
      </div>

      {(loading || activeTimeline.length > 0) && (
        <div style={{ ...card, borderColor: loading ? mcColors.cyan : mcColors.borderSubtle }}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 8 }}>
            {loading ? "Active research" : "Latest run"}
            {activeReplayId ? (
              <span style={{ fontWeight: 400, color: mcColors.textMuted, fontSize: 11, marginLeft: 8 }}>
                {activeReplayId}
              </span>
            ) : null}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, marginBottom: 12 }}>
            {Object.entries(STEP_LABELS).map(([key, label]) => {
              const done = activeTimeline.some((s) => s.step === key);
              const current = activeStep === key || (loading && key === "retrieve");
              return (
                <span
                  key={key}
                  style={{
                    fontSize: 11,
                    padding: "4px 10px",
                    borderRadius: 999,
                    border: `1px solid ${current ? mcColors.cyan : mcColors.borderSubtle}`,
                    background: done ? mcAlpha(mcColors.cyan, 8) : "transparent",
                    color: current ? mcColors.cyan : done ? mcColors.text : mcColors.textMuted,
                  }}
                >
                  {label}
                </span>
              );
            })}
          </div>
          {sourceCount ? (
            <div style={{ fontSize: 13, color: mcColors.text, marginBottom: 8 }}>
              Writing report — <strong>{sourceCount}</strong> sources
            </div>
          ) : null}
          {activeTimeline.length > 0 ? (
            <ResearchNodeGraph timeline={activeTimeline} loading={loading} />
          ) : null}
          {activeReport ? (
            <pre
              style={{
                margin: 0,
                padding: 12,
                borderRadius: 10,
                background: "rgba(0,0,0,0.35)",
                fontSize: 12,
                lineHeight: 1.55,
                whiteSpace: "pre-wrap",
                maxHeight: 420,
                overflow: "auto",
                color: mcColors.textMuted,
              }}
            >
              {activeReport}
            </pre>
          ) : null}
        </div>
      )}

      <div style={card}>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Past research</div>
        {history.length === 0 ? (
          <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>No saved runs yet.</p>
        ) : (
          history.slice(0, 12).map((row) => {
            const replayId = String(row.payload?.replay_id ?? row.artifact_id);
            const q = String(row.payload?.query ?? "Untitled");
            const timeline = (row.payload?.timeline as { at?: number }[]) ?? [];
            const started = timeline[0]?.at;
            const ended = timeline[timeline.length - 1]?.at;
            const failed = timeline.some((t) => (t as { step?: string }).step === "config_check");
            return (
              <button
                key={replayId}
                type="button"
                onClick={() => void openReplay(replayId)}
                style={{
                  all: "unset",
                  cursor: "pointer",
                  display: "block",
                  width: "100%",
                  padding: "10px 0",
                  borderBottom: `1px solid ${mcColors.borderSubtle}`,
                }}
              >
                <div style={{ fontSize: 13, color: mcColors.text }}>{q.slice(0, 100)}{q.length > 100 ? "…" : ""}</div>
                <div style={{ fontSize: 11, color: failed ? mcColors.amber : mcColors.textMuted, marginTop: 4 }}>
                  {failed ? "no results — check search config" : "completed"} · {formatDuration(started, ended) || formatTs(row.created_at)}
                </div>
              </button>
            );
          })
        )}
      </div>
    </section>
  );
}

function ResearchNodeGraph({
  timeline,
  loading,
}: {
  timeline: { step?: string; detail?: string; at?: number; source_count?: number }[];
  loading: boolean;
}) {
  const nodes = timeline.filter((t) => t.step && t.step !== "config_check");
  if (nodes.length === 0) return null;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 0,
        marginBottom: 12,
        overflowX: "auto",
        padding: "8px 4px",
      }}
    >
      {nodes.map((node, idx) => {
        const label = STEP_LABELS[node.step ?? ""] ?? node.step ?? "step";
        const isLast = idx === nodes.length - 1;
        const active = loading && isLast;
        return (
          <div key={`${node.step}-${idx}`} style={{ display: "flex", alignItems: "center", flexShrink: 0 }}>
            <div
              style={{
                minWidth: 88,
                padding: "10px 12px",
                borderRadius: 10,
                border: `1px solid ${active ? mcColors.cyan : mcColors.borderSubtle}`,
                background: active ? mcAlpha(mcColors.cyan, 9) : "rgba(0,0,0,0.35)",
                textAlign: "center",
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 600, color: active ? mcColors.cyan : mcColors.text }}>
                {label}
              </div>
              {node.detail ? (
                <div style={{ fontSize: 10, color: mcColors.textMuted, marginTop: 4, maxWidth: 120 }}>
                  {(node.detail || "").slice(0, 40)}
                  {(node.detail || "").length > 40 ? "…" : ""}
                </div>
              ) : null}
            </div>
            {!isLast ? (
              <div
                style={{
                  width: 28,
                  height: 2,
                  background: mcColors.borderSubtle,
                  margin: "0 4px",
                }}
              />
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
