"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchResearchStatus, type ResearchStatus } from "@/lib/missionControl/researchApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function ResearchConfigPanel() {
  const [data, setData] = useState<ResearchStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setData(await fetchResearchStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load research status");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Research Config</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Loaded web research settings — no raw API keys. Restart API after editing `.env`.
          </p>
        </div>
        <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      <div
        style={{
          marginTop: 16,
          padding: "12px 14px",
          borderRadius: 10,
          border: `1px solid ${mcColors.borderSubtle}`,
          background: "rgba(0,0,0,0.18)",
          fontSize: 13,
        }}
      >
        <div>
          <strong>Enabled:</strong> {data ? String(data.enabled) : "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Provider:</strong> {data?.provider ?? "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>API key configured:</strong> {data ? String(data.api_key_configured) : "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>API key preview:</strong> {data?.api_key_preview ?? "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Max results:</strong> {data?.max_results ?? "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Artifact directory:</strong> {data?.artifacts_dir ?? "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Configured:</strong> {data ? String(data.configured) : "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Config source:</strong> {data?.config_source ?? "—"}
        </div>
        {data?.restart_required_hint ? (
          <div style={{ marginTop: 6, color: mcColors.textMuted }}>{data.restart_required_hint}</div>
        ) : null}
      </div>

      {data?.errors?.length ? (
        <div style={{ marginTop: 12 }}>
          <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600, color: mcColors.amber }}>Errors</h3>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: mcColors.amber }}>
            {data.errors.map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
