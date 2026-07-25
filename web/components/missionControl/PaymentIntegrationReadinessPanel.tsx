"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlPaymentIntegrationReadiness,
  type PaymentIntegrationReadinessResponse,
} from "@/lib/missionControl/missionControlPaymentIntegrationReadinessApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function PaymentIntegrationReadinessPanel() {
  const [payload, setPayload] = useState<PaymentIntegrationReadinessResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlPaymentIntegrationReadiness("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load payment integration readiness");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.payment_integration_readiness as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.payment_readiness_dashboard ?? [{}])[0] as {
    provider_readiness?: string;
    subscription_readiness?: string;
    invoice_readiness?: string;
    usage_readiness?: string;
  };
  const providers = (sections.payment_provider_registry ?? [{}])[0] as {
    providers?: Array<{ provider?: string; integration_status?: string; configured?: boolean }>;
  };
  const upgrades = (sections.upgrade_path_registry ?? [{}])[0] as {
    current_plan?: string;
    eligible_paths?: Array<{ from_plan?: string; to_plan?: string }>;
  };
  const lifecycle = (sections.subscription_lifecycle_registry ?? [{}])[0] as {
    current_state?: string;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Payment Integration Readiness</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Future payment architecture modeled — readiness only, no charging or card storage.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Readiness dashboard</strong>
            <div>Providers: {dashboard.provider_readiness}</div>
            <div>Subscription: {lifecycle.current_state ?? dashboard.subscription_readiness}</div>
            <div>Invoice: {dashboard.invoice_readiness}</div>
            <div>Usage: {dashboard.usage_readiness}</div>
          </div>

          <div style={cardStyle}>
            <strong>Payment providers</strong>
            {(providers.providers ?? []).map((row) => (
              <div key={row.provider}>
                {row.provider}: {row.integration_status} (configured={String(row.configured)})
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Upgrade paths</strong>
            <div>Current plan: {upgrades.current_plan}</div>
            {(upgrades.eligible_paths ?? []).map((path) => (
              <div key={`${path.from_plan}-${path.to_plan}`}>
                {path.from_plan} → {path.to_plan}
              </div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            payment_processing_enabled: {String(payload.payment_processing_enabled)} ·
            credit_card_storage_enabled: {String(payload.credit_card_storage_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
