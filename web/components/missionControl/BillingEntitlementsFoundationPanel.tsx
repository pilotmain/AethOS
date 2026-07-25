"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlBillingEntitlementsFoundation,
  type BillingEntitlementsFoundationResponse,
} from "@/lib/missionControl/missionControlBillingEntitlementsFoundationApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function BillingEntitlementsFoundationPanel() {
  const [payload, setPayload] = useState<BillingEntitlementsFoundationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlBillingEntitlementsFoundation("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load billing & entitlements foundation");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.billing_entitlements_foundation as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.billing_dashboard ?? [{}])[0] as {
    plan?: string;
    org_plan_raw?: string;
    upgrade_opportunities?: Array<{ from_plan?: string; to_plan?: string }>;
  };
  const entitlements = (sections.entitlement_registry ?? [{}])[0] as {
    features?: string[];
    enterprise_only_blocked?: string[];
  };
  const usageLimits = (sections.usage_limit_report ?? [{}])[0] as {
    consumption?: { limits?: Array<{ metric?: string; current?: number; maximum?: number | null }> };
  };
  const subscription = (sections.subscription_registry ?? [{}])[0] as {
    status?: string;
    trial_status?: string;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Billing & Entitlements</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Entitlements control access — not governance. No payment collection or automatic plan mutation.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Plan & subscription</strong>
            <div>
              Commercial plan: {dashboard.plan} (org: {dashboard.org_plan_raw})
            </div>
            <div>
              Status: {subscription.status} · Trial: {subscription.trial_status}
            </div>
          </div>

          <div style={cardStyle}>
            <strong>Entitlements</strong>
            {(entitlements.features ?? []).map((feature) => (
              <div key={feature}>{feature}</div>
            ))}
            {(entitlements.enterprise_only_blocked ?? []).length > 0 ? (
              <div style={{ color: mcColors.amber, marginTop: 6 }}>
                Enterprise-only blocked: {(entitlements.enterprise_only_blocked ?? []).join(", ")}
              </div>
            ) : null}
          </div>

          <div style={cardStyle}>
            <strong>Usage limits</strong>
            {(usageLimits.consumption?.limits ?? []).map((row) => (
              <div key={row.metric}>
                {row.metric}: {row.current} / {row.maximum ?? "unlimited"}
              </div>
            ))}
          </div>

          {(dashboard.upgrade_opportunities ?? []).length > 0 ? (
            <div style={cardStyle}>
              <strong>Upgrade opportunities (advisory)</strong>
              {(dashboard.upgrade_opportunities ?? []).map((opp) => (
                <div key={`${opp.from_plan}-${opp.to_plan}`}>
                  {opp.from_plan} → {opp.to_plan}
                </div>
              ))}
            </div>
          ) : null}

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            billing_authority: {String(payload.billing_authority)} · payment_processing_enabled:{" "}
            {String(payload.payment_processing_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
