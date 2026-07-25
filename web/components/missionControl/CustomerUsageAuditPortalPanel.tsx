"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlCustomerUsageAuditPortal,
  type CustomerUsageAuditPortalResponse,
} from "@/lib/missionControl/missionControlCustomerUsageAuditPortalApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function CustomerUsageAuditPortalPanel() {
  const [payload, setPayload] = useState<CustomerUsageAuditPortalResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlCustomerUsageAuditPortal("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load customer usage & audit portal");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.customer_usage_audit_portal as
    | { sections?: Record<string, Array<Record<string, unknown>>>; requester_role?: string }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.customer_audit_dashboard ?? [{}])[0] as {
    activity_entry_count?: number;
    governance_entry_count?: number;
    usage_entry_count?: number;
    audit_registry_entry_count?: number;
    billing_plan?: string;
    audit_health?: string;
  };
  const activity = (sections.activity_timeline ?? [{}])[0] as {
    entries?: Array<{ who?: string; what?: string; when?: string }>;
  };
  const evidence = (sections.evidence_explorer ?? [{}])[0] as {
    trust_freezes?: Array<{ kind?: string; recorded_at?: string }>;
    governance_evidence?: Array<{ kind?: string }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Usage & Audit Portal</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Operational transparency — immutable audit visibility without mutation or governance bypass.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Audit dashboard</strong>
            <div>Activity: {dashboard.activity_entry_count ?? 0}</div>
            <div>Governance: {dashboard.governance_entry_count ?? 0}</div>
            <div>Usage: {dashboard.usage_entry_count ?? 0}</div>
            <div>Registry: {dashboard.audit_registry_entry_count ?? 0}</div>
            <div>Plan: {dashboard.billing_plan}</div>
            <div style={{ color: mcColors.textMuted }}>{dashboard.audit_health}</div>
          </div>

          <div style={cardStyle}>
            <strong>Recent activity</strong>
            {(activity.entries ?? []).slice(0, 5).map((entry, index) => (
              <div key={`${entry.when}-${index}`}>
                {entry.when}: {entry.who} — {entry.what}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Evidence explorer</strong>
            {(evidence.trust_freezes ?? []).slice(0, 3).map((item, index) => (
              <div key={`trust-${index}`}>Trust: {item.kind}</div>
            ))}
            {(evidence.governance_evidence ?? []).slice(0, 3).map((item, index) => (
              <div key={`gov-${index}`}>Governance: {item.kind}</div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            audit_authority: {String(payload.audit_authority)} · audit_mutation_enabled:{" "}
            {String(payload.audit_mutation_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
