"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlCustomerAdministrationConsole,
  type CustomerAdministrationConsoleResponse,
} from "@/lib/missionControl/missionControlCustomerAdministrationConsoleApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function CustomerAdministrationConsolePanel() {
  const [payload, setPayload] = useState<CustomerAdministrationConsoleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlCustomerAdministrationConsole("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load customer administration console");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.customer_administration_console as
    | { sections?: Record<string, Array<Record<string, unknown>>>; requester_role?: string }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.customer_administration_dashboard ?? [{}])[0] as {
    organization_health?: string;
    user_health?: string;
    provider_health?: string;
    channel_health?: string;
    billing_health?: string;
    governance_health?: string;
    admin_access_allowed?: boolean;
  };
  const organization = (sections.organization_administration_report ?? [{}])[0] as {
    organization_name?: string;
    workspace_count?: number;
    project_count?: number;
    subscription_status?: string;
  };
  const users = (sections.user_administration_report ?? [{}])[0] as {
    users?: Array<{ user_id?: string; role?: string }>;
  };
  const billing = (sections.billing_administration_report ?? [{}])[0] as {
    plan?: string;
    entitlements?: string[];
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Customer Administration Console</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Unified administration visibility — no authority escalation or automatic mutations.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Organization health</strong>
            <div>{organization.organization_name}</div>
            <div>
              Workspaces {organization.workspace_count ?? 0} · Projects {organization.project_count ?? 0} ·
              Subscription {organization.subscription_status}
            </div>
            <div style={{ color: mcColors.textMuted }}>
              Role: {board?.requester_role} · Admin access: {String(dashboard.admin_access_allowed ?? false)}
            </div>
          </div>

          <div style={cardStyle}>
            <strong>Dashboard health</strong>
            <div>Users: {dashboard.user_health}</div>
            <div>Providers: {dashboard.provider_health}</div>
            <div>Channels: {dashboard.channel_health}</div>
            <div>Billing: {dashboard.billing_health}</div>
            <div>Governance: {dashboard.governance_health}</div>
          </div>

          <div style={cardStyle}>
            <strong>Users</strong>
            {(users.users ?? []).map((user) => (
              <div key={user.user_id}>
                {user.user_id}: {user.role}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Billing</strong>
            <div>Plan: {billing.plan}</div>
            {(billing.entitlements ?? []).slice(0, 4).map((item) => (
              <div key={item} style={{ color: mcColors.textMuted }}>
                → {item}
              </div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            administration_authority: {String(payload.administration_authority)} ·
            automatic_user_creation_enabled: {String(payload.automatic_user_creation_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
