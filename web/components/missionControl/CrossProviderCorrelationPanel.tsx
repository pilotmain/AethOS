"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchCrossProviderCorrelationState,
  type CrossProviderCorrelationState,
} from "@/lib/missionControl/crossProviderCorrelationApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function CrossProviderCorrelationPanel() {
  const [state, setState] = useState<CrossProviderCorrelationState | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setState(await fetchCrossProviderCorrelationState());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load correlation state");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const corr = state?.cross_provider_correlation;
  const diagnosis = state?.diagnosis;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h2 style={{ margin: 0, fontSize: 18, color: mcColors.text }}>Cross-provider correlation</h2>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>
      {error ? <p style={{ color: mcColors.red }}>{error}</p> : null}
      {!corr ? (
        <p style={{ color: mcColors.textMuted }}>No correlation evidence published yet.</p>
      ) : (
        <div style={{ display: "grid", gap: 10, fontSize: 13 }}>
          <Row label="GitHub commit" value={corr.github_commit ? `\`${corr.github_commit.slice(0, 12)}\`` : "—"} />
          <Row label="GitHub repo" value={corr.github_repo || "—"} />
          <Row label="Vercel deployment" value={corr.vercel_project ? `${corr.vercel_project} / ${corr.vercel_deployment?.slice(0, 12) || "—"}` : "—"} />
          <Row label="Railway runtime" value={corr.railway_service || "—"} />
          <Row label="Matched commit" value={corr.matched_commit ? `\`${corr.matched_commit.slice(0, 12)}\`` : "—"} />
          <Row label="Failure boundary" value={corr.failure_boundary || "unknown"} highlight />
          <Row label="Confidence" value={corr.confidence || "low"} />
          {diagnosis?.conclusion || corr.conclusion ? (
            <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>{diagnosis?.conclusion || corr.conclusion}</p>
          ) : null}
          {corr.needs_binding ? (
            <p style={{ margin: 0, color: mcColors.amber }}>Source binding required to strengthen correlation.</p>
          ) : null}
        </div>
      )}
    </section>
  );
}

function Row({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
      <span style={{ color: mcColors.textMuted }}>{label}</span>
      <span style={{ color: highlight ? mcColors.cyan : mcColors.text, fontWeight: highlight ? 600 : 400 }}>{value}</span>
    </div>
  );
}
