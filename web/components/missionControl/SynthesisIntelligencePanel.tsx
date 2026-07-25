"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchConversationalIntelligenceState,
  fetchSynthesisHarness,
  type ConversationalIntelligenceState,
} from "@/lib/missionControl/synthesisIntelligenceApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const maturityColor = (tier?: string) => {
  if (tier === "production conversational" || tier === "premium") return mcColors.green;
  if (tier === "stable") return mcColors.cyan;
  return mcColors.amber;
};

const titles: Record<string, string> = {
  "synthesis-quality": "Synthesis Quality",
  "synthesis-recommendations": "Recommendation Intelligence",
  "synthesis-conversational-trust": "Conversational Trust",
  "synthesis-presentation-safety": "Presentation Safety",
  "synthesis-response-elegance": "Response Elegance",
  "synthesis-human-trust": "Human Trust Signals",
  "synthesis-recommendation-replay": "Recommendation Replay",
  "synthesis-conversational-recovery": "Conversational Recovery",
};

export function SynthesisIntelligencePanel({ view }: Props) {
  const [state, setState] = useState<ConversationalIntelligenceState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "synthesis-recommendation-replay") {
        setState(await fetchConversationalIntelligenceState());
      } else if (view === "synthesis-quality") {
        const [full, harness] = await Promise.all([
          fetchConversationalIntelligenceState(),
          fetchSynthesisHarness(),
        ]);
        setState({ ...full, harness: harness ?? full.harness });
      } else {
        setState(await fetchConversationalIntelligenceState());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load synthesis intelligence");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const title = titles[view] ?? "Synthesis Intelligence";
  const sample = state?.sample_synthesis;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Human-centered synthesis quality — ranking discipline, confidence restraint, and premium conversational polish.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.qualification_tier ? (
        <div style={cardStyle}>
          <span style={{ color: maturityColor(state.qualification_tier), fontWeight: 600 }}>
            Qualification: {state.qualification_tier}
          </span>
          {state.harness ? (
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              Harness: {state.harness.verified_count}/{state.harness.scenario_count} verified · avg{" "}
              {state.harness.average_coverage_pct}%
            </p>
          ) : null}
        </div>
      ) : null}

      {(view === "synthesis-quality" || view === "synthesis-recommendations" || view === "synthesis-recommendation-replay") &&
        sample?.reply ? (
          <div style={cardStyle}>
            <span style={{ fontWeight: 600, fontSize: 12, color: mcColors.textDim }}>Sample synthesis preview</span>
            <pre style={{ margin: "10px 0 0", whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>
              {sample.reply}
            </pre>
            {sample.contract?.result_count ? (
              <p style={{ margin: "8px 0 0", fontSize: 11, color: mcColors.green }}>
                Intent contract: exactly {sample.contract.result_count} results
              </p>
            ) : null}
          </div>
        ) : null}

      {state?.capabilities &&
        (view === "synthesis-conversational-trust" ||
          view === "synthesis-presentation-safety" ||
          view === "synthesis-human-trust" ||
          view === "synthesis-response-elegance") && (
          <div style={{ marginTop: 8 }}>
            {Object.entries(state.capabilities).map(([key, val]) => (
              <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
                <span>{key.replace(/_/g, " ")}</span>
                <span style={{ color: maturityColor(val) }}>{val}</span>
              </div>
            ))}
          </div>
        )}

      {view === "synthesis-conversational-recovery" ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, color: mcColors.textMuted, fontSize: 13 }}>
            Graceful uncertainty narratives replace raw telemetry when confidence is limited. Follow-up suggestions guide
            users toward narrower, more answerable requests.
          </p>
        </div>
      ) : null}
    </div>
  );
}
