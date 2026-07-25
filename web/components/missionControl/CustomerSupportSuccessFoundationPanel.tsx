"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlCustomerSupportSuccessFoundation,
  type CustomerSupportSuccessFoundationResponse,
} from "@/lib/missionControl/missionControlCustomerSupportSuccessFoundationApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function CustomerSupportSuccessFoundationPanel() {
  const [payload, setPayload] = useState<CustomerSupportSuccessFoundationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlCustomerSupportSuccessFoundation("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load customer support foundation");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.customer_support_success_foundation as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.customer_support_success_dashboard ?? [{}])[0] as {
    healthy_count?: number;
    at_risk_count?: number;
    new_customer_count?: number;
    high_value_count?: number;
    risk_count?: number;
    open_escalation_count?: number;
    opportunity_count?: number;
    evidence_coverage?: { fix_300_309_composed?: number; fix_300_309_total?: number };
  };
  const risks = (sections.customer_risk_registry ?? [{}])[0] as {
    risks?: Array<{ detail?: string; org_name?: string; level?: string }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Customer Support & Success</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Customer health and support visibility — humans remain responsible for support actions.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Customer health</strong>
            <div>Healthy: {dashboard.healthy_count ?? 0}</div>
            <div>At risk: {dashboard.at_risk_count ?? 0}</div>
            <div>New: {dashboard.new_customer_count ?? 0}</div>
            <div>High value: {dashboard.high_value_count ?? 0}</div>
            <div style={{ color: mcColors.textMuted }}>
              Evidence coverage: {dashboard.evidence_coverage?.fix_300_309_composed ?? 0} /{" "}
              {dashboard.evidence_coverage?.fix_300_309_total ?? 10}
            </div>
          </div>

          <div style={cardStyle}>
            <strong>Support signals</strong>
            <div>Open escalations: {dashboard.open_escalation_count ?? 0}</div>
            <div>Total risks: {dashboard.risk_count ?? 0}</div>
            <div>Opportunities: {dashboard.opportunity_count ?? 0}</div>
          </div>

          <div style={cardStyle}>
            <strong>Top risks</strong>
            {(risks.risks ?? []).slice(0, 4).map((risk) => (
              <div key={risk.detail} style={{ color: mcColors.amber }}>
                [{risk.level}] {risk.org_name}: {risk.detail}
              </div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            customer_support_authority: {String(payload.customer_support_authority)} ·
            automatic_customer_contact_enabled: {String(payload.automatic_customer_contact_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
