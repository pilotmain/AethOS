"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchConversationalConvergenceState,
  type ConversationalConvergenceState,
} from "@/lib/missionControl/conversationalConvergenceApi";

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
  if (tier === "production conversational" || tier === "mature") return mcColors.green;
  if (tier === "converging" || tier === "premium") return mcColors.cyan;
  return mcColors.amber;
};

const titles: Record<string, string> = {
  "conv-convergence": "Interaction Convergence",
  "conv-interaction-layers": "Interaction Layers",
  "conv-trust-maturity": "Trust Maturity",
  "conv-synthesis-consistency": "Synthesis Consistency",
  "conv-production-interaction": "Production Interaction",
  "conv-maturity-profile": "Maturity Profile",
  "conv-surface-integrity": "Surface Integrity",
  "conv-trust-threshold": "Trust Threshold",
};

export function ConversationalConvergencePanel({ view }: Props) {
  const [state, setState] = useState<ConversationalConvergenceState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setState(await fetchConversationalConvergenceState());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load conversational convergence");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const profile = state?.maturity_profile?.profile;
  const layers = state?.interaction_layers?.layers;
  const checks = state?.production_interaction?.checks;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Interaction Convergence"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Human trust maturity and production interaction quality — convergence of synthesis, reliability, and surface integrity.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {view === "conv-convergence" && state ? (
        <>
          <div style={cardStyle}>
            <span style={{ color: maturityColor(state.qualification_tier), fontWeight: 600 }}>
              {state.converged ? "Converged" : "Converging"} — {state.qualification_tier}
            </span>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>{state.summary}</p>
          </div>
          {state.reliability?.reply ? (
            <div style={cardStyle}>
              <span style={{ fontWeight: 600, fontSize: 12, color: mcColors.textDim }}>Convergence sample</span>
              <pre style={{ margin: "10px 0 0", whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>
                {state.reliability.reply}
              </pre>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "conv-interaction-layers" && layers ? (
        Object.entries(layers).map(([key, layer]) => (
          <div key={key} style={{ ...cardStyle, display: "grid", gap: 4 }}>
            <span style={{ fontWeight: 600 }}>{layer.label}</span>
            <span style={{ color: mcColors.textMuted, fontSize: 12 }}>{layer.behavior}</span>
            <span style={{ fontSize: 11, color: mcColors.textDim }}>
              Telemetry: {layer.telemetry_allowed ? "allowed" : "suppressed"} · Artifacts:{" "}
              {layer.artifacts_visible ? "visible" : "hidden"}
            </span>
          </div>
        ))
      ) : null}

      {view === "conv-trust-maturity" && state?.trust_maturity ? (
        <div style={cardStyle}>
          <span style={{ color: maturityColor(state.trust_maturity.trust_maturity_level), fontWeight: 600 }}>
            Trust maturity: {state.trust_maturity.trust_maturity_level} ({state.trust_maturity.trust_maturity_score})
          </span>
          <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>{state.trust_maturity.summary}</p>
        </div>
      ) : null}

      {view === "conv-synthesis-consistency" && state?.synthesis_consistency ? (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>
            Consistency score: {state.synthesis_consistency.consistency_score}
          </span>
          <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
            {state.synthesis_consistency.summary}
          </p>
        </div>
      ) : null}

      {view === "conv-production-interaction" && checks ? (
        Object.entries(checks).map(([key, passed]) => (
          <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
            <span>{key.replace(/_/g, " ")}</span>
            <span style={{ color: passed ? mcColors.green : mcColors.amber }}>{passed ? "pass" : "pending"}</span>
          </div>
        ))
      ) : null}

      {view === "conv-maturity-profile" && profile ? (
        Object.entries(profile).map(([key, val]) => (
          <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
            <span>{key.replace(/_/g, " ")}</span>
            <span style={{ color: maturityColor(val) }}>{val}</span>
          </div>
        ))
      ) : null}

      {view === "conv-surface-integrity" && state?.interaction_layers ? (
        <div style={cardStyle}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.interaction_layers.principle}</p>
          <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.green }}>
            Surface separation enforced across {Object.keys(state.interaction_layers.layers ?? {}).length} layers.
          </p>
        </div>
      ) : null}

      {view === "conv-trust-threshold" && state?.principles ? (
        Object.entries(state.principles).map(([key, val]) => (
          <div key={key} style={cardStyle}>
            <span style={{ fontWeight: 600, fontSize: 12 }}>{key.replace(/_/g, " ")}</span>
            <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textMuted }}>{val}</p>
          </div>
        ))
      ) : null}
    </div>
  );
}
