"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchCalmPresence,
  fetchCompanionBrief,
  fetchHumanIntuition,
  fetchLivingExplainability,
  fetchOperationalTimeline,
  fetchPresenceQuality,
  fetchRestraintStatus,
} from "@/lib/missionControl/humanApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const titles: Record<string, string> = {
  "presence-attention-quality": "Attention Quality",
  "presence-interruption-budget": "Interruption Budget",
  "presence-continuity-accuracy": "Continuity Accuracy",
  "presence-operational-narrative": "Operational Narrative",
  "presence-calm-intelligence": "Calm Intelligence",
  "presence-trust-signals": "Trust Signals",
  "presence-collaboration-quality": "Collaboration Quality",
};

export function PresenceQualityPanel({ view }: Props) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "presence-attention-quality") setData(await fetchHumanIntuition());
      else if (view === "presence-interruption-budget") setData(await fetchCalmPresence());
      else if (view === "presence-continuity-accuracy") setData(await fetchPresenceQuality());
      else if (view === "presence-operational-narrative") setData(await fetchOperationalTimeline());
      else if (view === "presence-calm-intelligence") setData(await fetchRestraintStatus());
      else if (view === "presence-trust-signals") setData(await fetchLivingExplainability());
      else if (view === "presence-collaboration-quality") setData(await fetchCompanionBrief());
      else setData(await fetchPresenceQuality());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const metrics = (data?.metrics as Record<string, number>) ?? {};

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 16, color: mcColors.textBright }}>{titles[view] ?? "Presence Quality"}</h2>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {view === "presence-attention-quality" && data ? (
        <>
          <div style={cardStyle}>{String(data.guidance ?? "")}</div>
          <div style={cardStyle}>
            Highest impact: {String((data.attention as Record<string, unknown>)?.highest_impact_unresolved ?? "—")}
          </div>
        </>
      ) : null}

      {view === "presence-interruption-budget" && data ? (
        <div style={cardStyle}>
          Budget remaining: {String(data.interruption_budget_remaining ?? "—")} — Quiet mode:{" "}
          {String(data.quiet_mode_recommended ?? false)}
        </div>
      ) : null}

      {view === "presence-continuity-accuracy" && data ? (
        <div style={cardStyle}>
          Overall: {String(data.overall_score ?? "—")} — Continuity accuracy:{" "}
          {String(metrics.continuity_accuracy ?? "—")}
        </div>
      ) : null}

      {view === "presence-operational-narrative" && data ? (
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>{String(data.story ?? "")}</pre>
      ) : null}

      {view === "presence-calm-intelligence" && data ? (
        <div style={cardStyle}>{String(data.principle ?? "")}</div>
      ) : null}

      {view === "presence-trust-signals" && data ? (
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>{String(data.summary ?? "")}</pre>
      ) : null}

      {view === "presence-collaboration-quality" && data ? (
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>
          {String(data.brief ?? data.brief_core ?? "")}
        </pre>
      ) : null}

      {!data && !error ? <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading…</p> : null}
    </section>
  );
}
