"use client";

import { useState } from "react";

import { useMissionControlTheme } from "@/lib/missionControl/theme";
import { mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  WORKFLOW_SURFACES,
  filterLegacySectionsForMode,
  legacySectionsForSurface,
  primaryItemsForSurface,
  type WorkflowSurfaceId,
} from "@/lib/missionControl/workflowNavigation";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  surfaceId: WorkflowSurfaceId;
  onNavigate: (view: MissionControlView) => void;
  mode?: MissionControlMode;
};

export function WorkflowHubPanel({ surfaceId, onNavigate, mode = "operator" }: Props) {
  const { colors } = useMissionControlTheme();
  const [advancedOpen, setAdvancedOpen] = useState(mode === "deep-engineering");

  const activeSurface = WORKFLOW_SURFACES.find((item) => item.id === surfaceId);
  if (!activeSurface) return null;

  const primaryItems = primaryItemsForSurface(activeSurface, mode);
  const legacySections = filterLegacySectionsForMode(
    legacySectionsForSurface(activeSurface),
    mode,
  );
  const legacyPanelCount = legacySections.reduce((count, section) => count + section.items.length, 0);

  return (
    <div data-mc-workflow-hub={surfaceId}>
      <header style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 22, fontWeight: 600, color: colors.text }}>
          {activeSurface.label}
        </h1>
        <p style={{ margin: "8px 0 0", fontSize: 14, color: colors.textMuted, maxWidth: 640 }}>
          {activeSurface.description}. Intelligence runs behind these workflows — open a surface to
          continue work or drill into diagnostics when needed.
        </p>
      </header>

      <section style={mcPanelSectionStyle}>
        <h2
          style={{
            margin: "0 0 12px",
            fontSize: 13,
            fontWeight: 700,
            letterSpacing: "0.06em",
            textTransform: "uppercase",
            color: colors.textMuted,
          }}
        >
          Primary workflows
        </h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))",
            gap: 12,
          }}
        >
          {primaryItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => onNavigate(item.id)}
              style={{
                textAlign: "left",
                padding: "14px 16px",
                borderRadius: 12,
                border: `1px solid ${colors.borderSubtle}`,
                background: "rgba(255,255,255,0.03)",
                cursor: "pointer",
                color: colors.text,
              }}
            >
              <div style={{ fontSize: 14, fontWeight: 600 }}>{item.label}</div>
              <div style={{ fontSize: 12, color: colors.textMuted, marginTop: 6 }}>{item.hint}</div>
            </button>
          ))}
        </div>
      </section>

      {legacySections.length > 0 ? (
        <section style={{ ...mcPanelSectionStyle, marginTop: 16 }}>
          <button
            type="button"
            onClick={() => setAdvancedOpen((open) => !open)}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: 0,
              border: "none",
              background: "transparent",
              cursor: "pointer",
              color: colors.textMuted,
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            <span>{advancedOpen ? "▼" : "▶"}</span>
            Advanced diagnostics
            <span style={{ fontWeight: 400, opacity: 0.8 }}>({legacyPanelCount} panels)</span>
          </button>

          {advancedOpen ? (
            <div style={{ marginTop: 14 }}>
              {legacySections.map((section) => (
                <div key={section.title} style={{ marginBottom: 16 }}>
                  <div
                    style={{
                      fontSize: 10,
                      fontWeight: 700,
                      letterSpacing: "0.05em",
                      textTransform: "uppercase",
                      color: colors.textMuted,
                      marginBottom: 6,
                    }}
                  >
                    {section.title}
                  </div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                    {section.items.map((item) => (
                      <button
                        key={item.id}
                        type="button"
                        onClick={() => onNavigate(item.id)}
                        style={{
                          padding: "6px 10px",
                          borderRadius: 8,
                          border: `1px solid ${colors.borderSubtle}`,
                          background: "rgba(255,255,255,0.02)",
                          color: colors.textNavInactive,
                          fontSize: 12,
                          cursor: "pointer",
                        }}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ margin: "10px 0 0", fontSize: 12, color: colors.textDim }}>
              Internal intelligence panels stay available here — hidden from the primary sidebar to
              reduce cognitive load.
            </p>
          )}
        </section>
      ) : null}
    </div>
  );
}
