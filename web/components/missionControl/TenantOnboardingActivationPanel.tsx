"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlTenantOnboardingActivation,
  type TenantOnboardingActivationResponse,
} from "@/lib/missionControl/missionControlTenantOnboardingActivationApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const statusColor = (status?: string) => {
  if (status === "activation_ready" || status === "review_recorded" || status === "ready") {
    return mcColors.cyan;
  }
  if (status === "awaiting_onboarding_decision") return mcColors.amber;
  return mcColors.textMuted;
};

export function TenantOnboardingActivationPanel() {
  const [payload, setPayload] = useState<TenantOnboardingActivationResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlTenantOnboardingActivation("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tenant onboarding activation");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.tenant_onboarding_activation as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const progress = (sections.onboarding_progress_registry ?? [{}])[0] as {
    steps?: Array<{ label?: string; status?: string }>;
    completed_step_count?: number;
    total_step_count?: number;
  };
  const capability = (sections.capability_discovery_report ?? [{}])[0] as {
    what_can_you_do?: string[];
    what_cannot_you_do?: string[];
  };
  const trust = (sections.trust_explanation_report ?? [{}])[0] as {
    human_approval_model?: string[];
  };
  const provider = (sections.provider_connection_checklist ?? [{}])[0] as {
    targets?: Array<{ provider?: string; status?: string; readiness?: string }>;
  };
  const activation = (sections.first_mission_control_activation_packet ?? [{}])[0] as {
    status?: string;
    guided_actions?: string[];
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>Tenant Onboarding & Activation</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Guided first-run experience — review artifacts only. Onboarding guidance ≠ platform authority.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Progress</strong>
            <div>
              {progress.completed_step_count ?? 0} / {progress.total_step_count ?? 0} steps
            </div>
            <div style={{ marginTop: 8 }}>
              {(progress.steps ?? []).map((step) => (
                <div key={step.label} style={{ color: statusColor(step.status) }}>
                  {step.label}: {step.status}
                </div>
              ))}
            </div>
          </div>

          <div style={cardStyle}>
            <strong>Organization, workspace, and project setup</strong>
            <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
              Record review notes via Mission Control chat — no automatic provisioning buttons.
            </p>
          </div>

          <div style={cardStyle}>
            <strong>Provider connection</strong>
            {(provider.targets ?? []).map((target) => (
              <div key={target.provider}>
                {target.provider}: {target.status} ({target.readiness}) — manual setup in Settings → Connections
              </div>
            ))}
            <div style={{ marginTop: 8, color: mcColors.amber }}>Never paste secrets into chat.</div>
          </div>

          <div style={cardStyle}>
            <strong>Capability discovery</strong>
            {(capability.what_can_you_do ?? []).slice(0, 4).map((item) => (
              <div key={item}>Can: {item}</div>
            ))}
            {(capability.what_cannot_you_do ?? []).slice(0, 3).map((item) => (
              <div key={item} style={{ color: mcColors.textMuted }}>
                Cannot: {item}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Trust explanation</strong>
            {(trust.human_approval_model ?? []).map((item) => (
              <div key={item}>{item}</div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>First governed workflow</strong>
            <div style={{ color: statusColor(activation.status) }}>Status: {activation.status}</div>
            {(activation.guided_actions ?? []).map((action) => (
              <div key={action}>{action}</div>
            ))}
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            automatic_provisioning_enabled: {String(payload.automatic_provisioning_enabled)} · secret_collection_enabled:{" "}
            {String(payload.secret_collection_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
