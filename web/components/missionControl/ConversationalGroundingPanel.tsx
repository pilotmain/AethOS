"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchConversationalGroundingState,
  fetchConversationalRealism,
  fetchContinuityReconstruction,
  fetchGovernanceRestraint,
  fetchOperationalContext,
  fetchCrossSurfaceConvergence,
  fetchLiveOperationalGrounding,
  fetchPartnerPresence,
  fetchTelegramPersistence,
  type ConversationalGroundingState,
} from "@/lib/missionControl/conversationalGroundingApi";

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
  "cog-operational-grounding": "Operational Grounding",
  "cog-continuity-reconstruction": "Continuity Reconstruction",
  "cog-operational-context": "Operational Context",
  "cog-governance-restraint": "Governance Restraint",
  "cog-conversational-realism": "Conversational Realism",
  "cog-telegram-persistence": "Telegram Persistence",
  "cog-partner-presence": "Partner Presence",
  "cog-cross-surface-convergence": "Cross-Surface Convergence",
  "cog-live-operational-grounding": "Live Operational Grounding",
  "cog-grounding-memory": "Grounding Memory",
};

export function ConversationalGroundingPanel({ view }: Props) {
  const [state, setState] = useState<ConversationalGroundingState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "cog-continuity-reconstruction") {
        const thread = await fetchContinuityReconstruction();
        setState({ ok: true, phase: "11.7", continuity_thread: thread });
      } else if (view === "cog-operational-context") {
        const context = await fetchOperationalContext();
        setState({ ok: true, phase: "11.7", operational_grounding: { summary: context.primary_subject, grounded: context.has_memory } });
      } else if (view === "cog-governance-restraint") {
        const restraint = await fetchGovernanceRestraint();
        setState({ ok: true, phase: "11.7", governance_restraint: restraint });
      } else if (view === "cog-conversational-realism") {
        const realism = await fetchConversationalRealism();
        setState({ ok: true, phase: "11.7", conversational_realism: realism });
      } else if (view === "cog-telegram-persistence") {
        const telegram = await fetchTelegramPersistence();
        setState({ ok: true, phase: "11.7", telegram_persistence: telegram });
      } else if (view === "cog-partner-presence") {
        const partner = await fetchPartnerPresence();
        setState({ ok: true, phase: "11.7", operational_partner: partner });
      } else if (view === "cog-cross-surface-convergence") {
        const convergence = await fetchCrossSurfaceConvergence();
        setState({ ok: true, phase: "11.7.4", cross_surface_convergence: convergence });
      } else if (view === "cog-live-operational-grounding") {
        const live = await fetchLiveOperationalGrounding();
        setState({ ok: true, phase: "11.7.5", live_operational_grounding: live });
      } else {
        setState(await fetchConversationalGroundingState());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load conversational grounding");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const grounding = state?.operational_grounding;

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{titles[view] ?? "Conversational Grounding"}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Conversational operational grounding — continuity reconstruction, governance restraint, and anti-generic realism.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.phase ? (
        <div style={cardStyle}>
          <span style={{ color: state.converged ? mcColors.green : mcColors.cyan, fontWeight: 600 }}>
            {state.converged ? "Grounding qualified" : "Grounding active"} — Phase {state.phase}
          </span>
        </div>
      ) : null}

      {view === "cog-operational-grounding" && state?.summary ? (
        <>
          <div style={cardStyle}>
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.summary}</p>
            {state.narrative ? <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textDim }}>{state.narrative}</p> : null}
          </div>
        </>
      ) : null}

      {view === "cog-continuity-reconstruction" && state?.continuity_thread?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.continuity_thread.summary}</p></div>
      ) : null}

      {view === "cog-operational-context" && grounding?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{grounding.summary}</p></div>
      ) : null}

      {view === "cog-governance-restraint" && state?.governance_restraint?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.governance_restraint.summary}</p></div>
      ) : null}

      {view === "cog-conversational-realism" && state?.conversational_realism?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.conversational_realism.summary}</p></div>
      ) : null}

      {view === "cog-telegram-persistence" && state?.telegram_persistence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.telegram_persistence.summary}</p></div>
      ) : null}

      {view === "cog-partner-presence" && state?.operational_partner?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.operational_partner.summary}</p></div>
      ) : null}

      {view === "cog-cross-surface-convergence" && state?.cross_surface_convergence?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.cross_surface_convergence.summary}</p></div>
      ) : null}

      {view === "cog-live-operational-grounding" && state?.live_operational_grounding?.summary ? (
        <div style={cardStyle}><p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>{state.live_operational_grounding.summary}</p></div>
      ) : null}

      {state?.strategic_position && view === "cog-operational-grounding" ? (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>Strategic position</span>
          <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 12, color: mcColors.textMuted }}>
            {Object.entries(state.strategic_position).map(([key, value]) => (
              <li key={key}>{key.replace(/_/g, " ")}: {value}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
