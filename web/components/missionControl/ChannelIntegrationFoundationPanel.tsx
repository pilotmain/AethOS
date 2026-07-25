"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlChannelIntegrationFoundation,
  type ChannelIntegrationFoundationResponse,
} from "@/lib/missionControl/missionControlChannelIntegrationFoundationApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function ChannelIntegrationFoundationPanel() {
  const [payload, setPayload] = useState<ChannelIntegrationFoundationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlChannelIntegrationFoundation("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load channel integration foundation");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.channel_integration_foundation as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.channel_dashboard ?? [{}])[0] as {
    connected_channels?: number;
    total_channels?: number;
    readiness_summary?: Array<{ channel?: string; readiness?: string; status?: string }>;
    ingress_model?: string;
  };
  const capability = (sections.channel_capability_matrix ?? [{}])[0] as {
    channels?: Array<{ channel?: string; supported_actions?: string[] }>;
  };
  const authorization = (sections.channel_authorization_report ?? [{}])[0] as {
    authorization_model?: string;
    tenant_isolation_enforced?: boolean;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Channel Integration Foundation</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Unified channel ingress into Mission Control — no channel-specific governance or cross-tenant routing.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Channel health</strong>
            <div>
              Connected {dashboard.connected_channels ?? 0} / {dashboard.total_channels ?? 0} channels
            </div>
            <div style={{ color: mcColors.textMuted }}>Ingress: {dashboard.ingress_model}</div>
            {(dashboard.readiness_summary ?? []).map((row) => (
              <div key={row.channel}>
                {row.channel}: {row.readiness} ({row.status})
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Capability support</strong>
            {(capability.channels ?? []).map((row) => (
              <div key={row.channel}>
                <div>{row.channel}</div>
                {(row.supported_actions ?? []).slice(0, 3).map((action) => (
                  <div key={action} style={{ color: mcColors.textMuted }}>
                    → {action}
                  </div>
                ))}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Authorization</strong>
            <div>Model: {authorization.authorization_model}</div>
            <div>
              Tenant isolation: {String(authorization.tenant_isolation_enforced ?? true)}
            </div>
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            channel_authority: {String(payload.channel_authority)} · automatic_channel_provisioning_enabled:{" "}
            {String(payload.automatic_channel_provisioning_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
