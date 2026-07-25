"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchHumanRoutes,
  fetchHumanRuntimeReplay,
  fetchRuntimeIntegrity,
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

const statusColor = (s?: string) => {
  if (s === "pass" || s === "healthy") return mcColors.cyan;
  if (s === "warn" || s === "degraded") return mcColors.amber;
  if (s === "fail") return mcColors.red;
  return mcColors.textMuted;
};

const titles: Record<string, string> = {
  "integrity-routes": "Route Health",
  "integrity-features": "Feature Wiring",
  "integrity-ui-alignment": "UI ↔ API Alignment",
  "integrity-orphans": "Orphan Systems",
  "integrity-diagnostics": "Runtime Diagnostics",
};

export function RuntimeIntegrityPanel({ view }: Props) {
  const [routes, setRoutes] = useState<Record<string, unknown> | null>(null);
  const [integrity, setIntegrity] = useState<Record<string, unknown> | null>(null);
  const [replay, setReplay] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "integrity-routes") setRoutes(await fetchHumanRoutes());
      else if (view === "integrity-diagnostics") setReplay(await fetchHumanRuntimeReplay());
      else setIntegrity(await fetchRuntimeIntegrity());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const cards = (integrity?.cards as Array<{ status?: string; label?: string }>) ?? [];

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 16, color: mcColors.textBright }}>{titles[view] ?? "Runtime Integrity"}</h2>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {view === "integrity-routes" && routes ? (
        <>
          <div style={cardStyle}>
            Health: <span style={{ color: statusColor(String(routes.health)) }}>{String(routes.health)}</span>
            {" — "}
            Missing: {String((routes.missing_routes as unknown[])?.length ?? 0)}
          </div>
          {((routes.mounted_routes as Array<Record<string, unknown>>) ?? []).slice(0, 14).map((r) => (
            <div key={String(r.path)} style={cardStyle}>
              {String(r.method)} {String(r.path)} — {String(r.purpose)}
            </div>
          ))}
        </>
      ) : null}

      {(view === "integrity-features" || view === "integrity-ui-alignment" || view === "integrity-orphans") && integrity ? (
        <>
          <div style={cardStyle}>
            Overall: <span style={{ color: statusColor(String(integrity.health)) }}>{String(integrity.health)}</span>
          </div>
          {cards.map((c, i) => (
            <div key={i} style={cardStyle}>
              <span style={{ color: statusColor(c.status) }}>{c.status === "pass" ? "✅" : c.status === "warn" ? "⚠" : "❌"}</span>{" "}
              {c.label}
            </div>
          ))}
          {view === "integrity-ui-alignment" ? (
            <pre style={{ fontSize: 11, color: mcColors.textDim, whiteSpace: "pre-wrap" }}>
              {JSON.stringify(integrity.ui_alignment ?? {}, null, 2)}
            </pre>
          ) : null}
          {view === "integrity-orphans" ? (
            <pre style={{ fontSize: 11, color: mcColors.textDim, whiteSpace: "pre-wrap" }}>
              {JSON.stringify(integrity.orphans ?? {}, null, 2)}
            </pre>
          ) : null}
        </>
      ) : null}

      {view === "integrity-diagnostics" && replay ? (
        <div style={cardStyle}>
          Artifacts: {Object.keys((replay.artifacts as Record<string, unknown>) ?? {}).join(", ")}
        </div>
      ) : null}

      {!routes && !integrity && !replay && !error ? (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Loading…</p>
      ) : null}
    </section>
  );
}
