"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlIdentityAccessHardening,
  type IdentityAccessHardeningResponse,
} from "@/lib/missionControl/missionControlIdentityAccessHardeningApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function IdentityAccessHardeningPanel() {
  const [payload, setPayload] = useState<IdentityAccessHardeningResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlIdentityAccessHardening("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load identity access hardening");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.identity_access_hardening as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const identity = (sections.identity_resolution_report ?? [{}])[0] as {
    user_id?: string;
    role?: string;
    organization_id?: string;
  };
  const permission = (sections.permission_evaluation_report ?? [{}])[0] as {
    evaluations?: Array<{ permission?: string; allowed?: boolean }>;
  };
  const boundary = (sections.tenant_boundary_audit ?? [{}])[0] as {
    audits?: Array<{ target_organization_name?: string; access_allowed?: boolean }>;
  };
  const governance = (sections.governance_action_report ?? [{}])[0] as {
    actions?: Array<{ action?: string; allowed?: boolean }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Identity & Access Hardening</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Centralized authorization evaluation — enforcement only, no permission self-granting.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Identity resolution</strong>
            <div>
              User {identity.user_id} · Role {identity.role} · Org {identity.organization_id}
            </div>
          </div>

          <div style={cardStyle}>
            <strong>Permission evaluation</strong>
            {(permission.evaluations ?? []).map((row) => (
              <div key={row.permission} style={{ color: row.allowed ? mcColors.cyan : mcColors.amber }}>
                {row.permission}: {row.allowed ? "allowed" : "denied"}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Tenant boundary audit</strong>
            {(boundary.audits ?? []).map((row) => (
              <div key={row.target_organization_name}>
                {row.target_organization_name}: {row.access_allowed ? "in-tenant" : "blocked"}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Governance action controls</strong>
            {(governance.actions ?? []).map((row) => (
              <div key={row.action} style={{ color: row.allowed ? mcColors.cyan : mcColors.amber }}>
                {row.action}: {row.allowed ? "allowed" : "denied"}
              </div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            authorization_authority: {String(payload.authorization_authority)} · cross_tenant_access_enabled:{" "}
            {String(payload.cross_tenant_access_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
