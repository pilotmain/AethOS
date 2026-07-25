"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchAttentionAwareness,
  fetchCompanionNarrative,
  fetchCompanionQuality,
  fetchDeepReplay,
  fetchEmotionalRealism,
  fetchInvestigationCompanion,
  fetchOperationalReasoning,
  fetchPartnerBrief,
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
  "companion-operational-reasoning": "Operational Reasoning",
  "companion-investigation": "Investigation Companion",
  "companion-replay-intelligence": "Replay Intelligence",
  "companion-emotional-realism": "Emotional Realism",
  "companion-attention-awareness": "Attention Awareness",
  "companion-narrative-evolution": "Narrative Evolution",
  "companion-trust-retention": "Trust Retention",
};

export function CompanionIntelligencePanel({ view }: Props) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "companion-operational-reasoning") setData(await fetchOperationalReasoning());
      else if (view === "companion-investigation") setData(await fetchInvestigationCompanion());
      else if (view === "companion-replay-intelligence") setData(await fetchDeepReplay());
      else if (view === "companion-emotional-realism") setData(await fetchEmotionalRealism());
      else if (view === "companion-attention-awareness") setData(await fetchAttentionAwareness());
      else if (view === "companion-narrative-evolution") setData(await fetchCompanionNarrative());
      else if (view === "companion-trust-retention") setData(await fetchCompanionQuality());
      else setData(await fetchPartnerBrief());
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
        <h2 style={{ margin: 0, fontSize: 16, color: mcColors.text }}>{titles[view] ?? "Companion Intelligence"}</h2>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {view === "companion-operational-reasoning" && data ? (
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>{String(data.synthesis ?? "")}</pre>
      ) : null}

      {view === "companion-investigation" && data ? (
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>{String(data.narrative ?? "")}</pre>
      ) : null}

      {view === "companion-replay-intelligence" && data ? (
        <>
          <div style={cardStyle}>{String(data.compressed_summary ?? data.narrative ?? "")}</div>
          <div style={cardStyle}>Integrity: {String((data.stitched as Record<string, unknown>)?.integrity_score ?? "—")}</div>
        </>
      ) : null}

      {view === "companion-emotional-realism" && data ? (
        <>
          <div style={cardStyle}>{String(data.tone_narrative ?? "")}</div>
          <div style={cardStyle}>{String(data.invariant ?? "")}</div>
        </>
      ) : null}

      {view === "companion-attention-awareness" && data ? (
        <div style={cardStyle}>
          Fatigue: {String(data.fatigue_level ?? "—")} — Depth: {String(data.depth_control ?? "—")}
          <pre style={{ whiteSpace: "pre-wrap", marginTop: 8, fontSize: 12, color: mcColors.textDim }}>
            {String(data.narrative ?? "")}
          </pre>
        </div>
      ) : null}

      {view === "companion-narrative-evolution" && data ? (
        <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textDim }}>{String(data.narrative ?? "")}</pre>
      ) : null}

      {view === "companion-trust-retention" && data ? (
        <div style={cardStyle}>
          Overall: {String(data.overall_score ?? "—")} — Trust retention: {String(metrics.trust_retention ?? "—")}
        </div>
      ) : null}

      {!data && !error ? <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading…</p> : null}
    </section>
  );
}
