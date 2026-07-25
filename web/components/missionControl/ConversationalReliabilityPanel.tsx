"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchConversationalHarness,
  fetchConversationalReliabilityState,
  type ConversationalReliabilityState,
} from "@/lib/missionControl/conversationalReliabilityApi";

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
  if (tier === "production conversational" || tier === "production" || tier === "strong" || tier === "mature") {
    return mcColors.green;
  }
  if (tier === "premium" || tier === "emerging mature" || tier === "stable" || tier === "converging") {
    return mcColors.cyan;
  }
  return mcColors.amber;
};

const VIEW_DIMENSION: Partial<Record<string, string>> = {
  "conv-recommendation-quality": "recommendation_convergence",
  "conv-trust-calibration": "human_trust_language",
  "conv-presentation-integrity": "presentation_integrity",
  "conv-interaction-elegance": "conversational_elegance",
  "conv-recommendation-intelligence": "recommendation_convergence",
  "conv-human-trust-signals": "emotional_steadiness",
};

const titles: Record<string, string> = {
  "conv-reliability": "Conversational Reliability",
  "conv-recommendation-quality": "Recommendation Quality",
  "conv-trust-calibration": "Trust Calibration",
  "conv-presentation-integrity": "Presentation Integrity",
  "conv-interaction-elegance": "Interaction Elegance",
  "conv-conversational-replay": "Conversational Replay",
  "conv-recommendation-intelligence": "Recommendation Intelligence",
  "conv-human-trust-signals": "Human Trust Signals",
};

export function ConversationalReliabilityPanel({ view }: Props) {
  const [state, setState] = useState<ConversationalReliabilityState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const full = await fetchConversationalReliabilityState();
      if (view === "conv-reliability" || view === "conv-conversational-replay") {
        const harness = await fetchConversationalHarness();
        setState({ ...full, harness: harness ?? full.harness });
      } else {
        setState(full);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load conversational reliability");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const sample = state?.sample;
  const dimensionKey = VIEW_DIMENSION[view];
  const dimension = dimensionKey ? state?.qualification?.dimensions?.[dimensionKey] : undefined;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Conversational Reliability"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Production-qualified human interaction reliability — intent enforcement, trust integrity, and premium interaction discipline.
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
            {state.production_qualified ? "Production qualified" : "Qualifying"} — {state.qualification_tier}
          </span>
          {state.phase ? (
            <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.textDim }}>Phase {state.phase}</p>
          ) : null}
          {state.harness ? (
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              Harness {state.harness_version}: {state.harness.verified_count}/{state.harness.scenario_count} verified
            </p>
          ) : null}
        </div>
      ) : null}

      {view === "conv-reliability" && state?.qualification?.dimensions ? (
        <div style={{ marginTop: 8 }}>
          {Object.entries(state.qualification.dimensions).map(([key, val]) => (
            <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
              <span>{key.replace(/_/g, " ")}</span>
              <span style={{ color: val.passed ? mcColors.green : mcColors.amber }}>{val.status}</span>
            </div>
          ))}
        </div>
      ) : null}

      {dimension ? (
        <div style={cardStyle}>
          <span style={{ color: maturityColor(dimension.status), fontWeight: 600 }}>
            {dimensionKey?.replace(/_/g, " ")}: {dimension.status}
          </span>
          <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
            {dimension.passed ? "Qualification check passed." : "Qualification check converging."}
          </p>
        </div>
      ) : null}

      {view === "conv-trust-calibration" && state?.trust_integrity?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.trust_integrity.summary}</p>
        </div>
      ) : null}

      {view === "conv-human-trust-signals" && state?.human_interaction_reliability?.summary ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.human_interaction_reliability.summary}</p>
        </div>
      ) : null}

      {view === "conv-conversational-replay" && state?.strategic_position?.convergence_status ? (
        Object.entries(state.strategic_position.convergence_status).map(([key, val]) => (
          <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
            <span>{key.replace(/_/g, " ")}</span>
            <span style={{ color: maturityColor(val) }}>{val}</span>
          </div>
        ))
      ) : null}

      {sample?.reply && (view === "conv-reliability" || view === "conv-recommendation-quality") ? (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600, fontSize: 12, color: mcColors.textDim }}>Reliability sample</span>
          <pre style={{ margin: "10px 0 0", whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>
            {sample.reply}
          </pre>
          {sample.contract?.result_count ? (
            <p style={{ margin: "8px 0 0", fontSize: 11, color: mcColors.green }}>
              Intent contract honored: {sample.contract.result_count} results
            </p>
          ) : null}
        </div>
      ) : null}

      {state?.capabilities && view !== "conv-reliability" && !dimension ? (
        <div style={{ marginTop: 8 }}>
          {Object.entries(state.capabilities).map(([key, val]) => (
            <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
              <span>{key.replace(/_/g, " ")}</span>
              <span style={{ color: maturityColor(val) }}>{val}</span>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
