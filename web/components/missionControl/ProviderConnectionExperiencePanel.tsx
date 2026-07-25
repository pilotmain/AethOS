"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlProviderConnectionExperience,
  type ProviderConnectionExperienceResponse,
} from "@/lib/missionControl/missionControlProviderConnectionExperienceApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function ProviderConnectionExperiencePanel() {
  const [payload, setPayload] = useState<ProviderConnectionExperienceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlProviderConnectionExperience("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load provider connection experience");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.provider_connection_experience as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.provider_connection_dashboard ?? [{}])[0] as {
    connected_provider_count?: number;
    phase_1_providers?: string[];
    readiness_summary?: Array<{ provider?: string; readiness?: string; status?: string }>;
    permission_gaps?: Array<{ provider?: string; gap?: string }>;
  };
  const unlocks = (sections.provider_capability_unlock_matrix ?? [{}])[0] as {
    providers?: Array<{ provider?: string; capability_unlocks?: string[] }>;
  };
  const trust = (sections.provider_trust_explanation ?? [{}])[0] as {
    what_aethos_cannot_access?: string[];
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Provider Connection Experience</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Guided provider onboarding — connect manually in Settings. Never paste secrets into chat.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Provider health</strong>
            <div>
              Connected {dashboard.connected_provider_count ?? 0} /{" "}
              {dashboard.phase_1_providers?.length ?? 0} Phase 1 providers
            </div>
            {(dashboard.readiness_summary ?? []).map((row) => (
              <div key={row.provider}>
                {row.provider}: {row.readiness} ({row.status})
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Capability unlocks</strong>
            {(unlocks.providers ?? []).map((row) => (
              <div key={row.provider}>
                <div>{row.provider}</div>
                {(row.capability_unlocks ?? []).slice(0, 3).map((u) => (
                  <div key={u} style={{ color: mcColors.textMuted }}>
                    → {u}
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Trust boundaries</strong>
            {(trust.what_aethos_cannot_access ?? []).map((item) => (
              <div key={item}>{item}</div>
            ))}
            {(dashboard.permission_gaps ?? []).map((gap) => (
              <div key={gap.provider} style={{ color: mcColors.amber }}>
                Gap: {gap.provider} — {gap.gap}
              </div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            automatic_provider_connection_enabled: {String(payload.automatic_provider_connection_enabled)} ·
            secret_collection_enabled: {String(payload.secret_collection_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
