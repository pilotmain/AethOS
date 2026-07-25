"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchObservabilitySlo } from "@/lib/missionControl/productionApi";
import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

type SloRow = {
  slo?: string;
  target_max?: number;
  target_min?: number;
  actual?: number;
  samples?: number;
  ok?: boolean;
  severity?: string;
};

export function SloPanel() {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      setData(await fetchObservabilitySlo());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load SLO panel");
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const slos = (data?.slos as SloRow[]) ?? [];
  const alerts = (data?.alerts as SloRow[]) ?? [];

  return (
    <section style={{ ...mcPanelSectionStyle, marginTop: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
        <div>
          <h2 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>Release SLOs</h2>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>
            First paint &lt; 2s warm · chat first token &lt; 3s · job-progress events &lt; 1s (telemetry-backed).
          </p>
        </div>
        <button type="button" onClick={() => refresh()} style={{ fontSize: 12, cursor: "pointer" }}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ marginTop: 12, color: mcColors.warning, fontSize: 12 }}>{error}</p> : null}
      {!data && !error ? <p style={{ marginTop: 12, fontSize: 12, color: mcColors.textMuted }}>Loading SLO signals…</p> : null}
      {slos.length > 0 ? (
        <div style={{ marginTop: 12, display: "grid", gap: 8 }}>
          {slos.map((row) => (
            <div
              key={row.slo}
              style={{
                padding: 10,
                borderRadius: 8,
                border: `1px solid ${row.ok ? "rgba(72,187,120,0.35)" : "rgba(245,101,101,0.45)"}`,
                background: row.ok ? "rgba(72,187,120,0.08)" : "rgba(245,101,101,0.1)",
              }}
            >
              <div style={{ fontSize: 13, fontWeight: 600 }}>{row.slo}</div>
              <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>
                actual {row.actual ?? "—"}
                {row.target_max != null ? ` · target ≤ ${row.target_max}` : ""}
                {row.target_min != null ? ` · target ≥ ${row.target_min}` : ""}
                {row.samples != null ? ` · samples ${row.samples}` : ""}
              </div>
            </div>
          ))}
        </div>
      ) : null}
      {alerts.length > 0 ? (
        <p style={{ marginTop: 12, fontSize: 12, color: mcColors.warning }}>
          {alerts.length} SLO breach(es) — wire alerts via OTEL / error sink (see docs/E2_SLO_ALERTING.md).
        </p>
      ) : null}
    </section>
  );
}
