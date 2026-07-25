"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlPostLaunchOperationsBaseline,
  POST_LAUNCH_OPERATIONS_BASELINE_FOCUS_BY_VIEW,
  type PostLaunchOperationsBaselineFocus,
  type PostLaunchOperationsBaselineResponse,
} from "@/lib/missionControl/missionControlPostLaunchOperationsBaselineApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

type Props = {
  viewId?: string;
  focus?: PostLaunchOperationsBaselineFocus;
  title?: string;
};

export function PostLaunchOperationsBaselinePanel({
  viewId = "post-launch-operations",
  focus,
  title = "Post-Launch Operations Baseline",
}: Props) {
  const resolvedFocus =
    focus ??
    POST_LAUNCH_OPERATIONS_BASELINE_FOCUS_BY_VIEW[viewId] ??
    "post_launch_operations_dashboard";
  const [payload, setPayload] = useState<PostLaunchOperationsBaselineResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlPostLaunchOperationsBaseline("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load post-launch operations baseline");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.post_launch_operations_baseline as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.post_launch_operations_dashboard ?? [{}])[0] as {
    platform_health_status?: string;
    customer_health_status?: string;
    governance_health_status?: string;
    incident_count?: number;
    trust_baseline_count?: number;
    proven_capability_count?: number;
    commercial_plan_count?: number;
    platform_healthy?: boolean;
  };
  const platform = (sections.platform_health_baseline ?? [{}])[0] as {
    deployment_health?: boolean;
    monitoring_health?: boolean;
    operational_stability?: boolean;
    health_status?: string;
  };
  const customer = (sections.customer_health_baseline ?? [{}])[0] as {
    healthy_count?: number;
    at_risk_count?: number;
    beta_participants?: number;
    health_status?: string;
  };
  const governance = (sections.governance_health_baseline ?? [{}])[0] as {
    authorization_effective?: boolean;
    audit_integrity?: boolean;
    review_count?: number;
    health_status?: string;
  };
  const incident = (sections.incident_baseline ?? [{}])[0] as {
    incident_count?: number;
    escalation_frequency?: number;
    recovery_trend?: string;
  };
  const commercial = (sections.commercial_baseline ?? [{}])[0] as {
    plan_count?: number;
    payment_readiness?: string;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Canonical post-launch operating baseline — observe and assess only, no operational execution.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Operations health summary</strong>
            <div>Platform: {dashboard.platform_health_status ?? platform.health_status ?? "—"}</div>
            <div>Customers: {dashboard.customer_health_status ?? customer.health_status ?? "—"}</div>
            <div>Governance: {dashboard.governance_health_status ?? governance.health_status ?? "—"}</div>
          </div>

          {resolvedFocus === "platform_health_baseline" ||
          resolvedFocus === "post_launch_operations_dashboard" ? (
            <div style={cardStyle}>
              <strong>Platform health</strong>
              <div>Deployment: {platform.deployment_health ? "healthy" : "needs attention"}</div>
              <div>Monitoring: {platform.monitoring_health ? "healthy" : "needs attention"}</div>
              <div>Stability: {platform.operational_stability ? "stable" : "unstable"}</div>
            </div>
          ) : null}

          {resolvedFocus === "customer_health_baseline" ||
          resolvedFocus === "post_launch_operations_dashboard" ? (
            <div style={cardStyle}>
              <strong>Customer health</strong>
              <div>Healthy: {customer.healthy_count ?? 0}</div>
              <div>At risk: {customer.at_risk_count ?? 0}</div>
              <div>Beta participants: {customer.beta_participants ?? 0}</div>
            </div>
          ) : null}

          {resolvedFocus === "governance_health_baseline" ||
          resolvedFocus === "post_launch_operations_dashboard" ? (
            <div style={cardStyle}>
              <strong>Governance health</strong>
              <div>Authorization effective: {governance.authorization_effective ? "yes" : "no"}</div>
              <div>Audit integrity: {governance.audit_integrity ? "yes" : "no"}</div>
              <div>Reviews tracked: {governance.review_count ?? 0}</div>
            </div>
          ) : null}

          {resolvedFocus === "incident_baseline" ||
          resolvedFocus === "post_launch_operations_dashboard" ? (
            <div style={cardStyle}>
              <strong>Incident baseline</strong>
              <div>Incidents: {incident.incident_count ?? dashboard.incident_count ?? 0}</div>
              <div>Escalations: {incident.escalation_frequency ?? 0}</div>
              <div>Recovery trend: {incident.recovery_trend ?? "—"}</div>
            </div>
          ) : null}

          {resolvedFocus === "commercial_baseline" ||
          resolvedFocus === "post_launch_operations_dashboard" ? (
            <div style={cardStyle}>
              <strong>Commercial baseline</strong>
              <div>Plans tracked: {commercial.plan_count ?? dashboard.commercial_plan_count ?? 0}</div>
              <div>Payment readiness: {commercial.payment_readiness ?? "—"}</div>
            </div>
          ) : null}

          {resolvedFocus === "post_launch_operations_dashboard" ? (
            <div style={cardStyle}>
              <strong>Unified baseline</strong>
              <div>Trust baselines: {dashboard.trust_baseline_count ?? 0}</div>
              <div>Proven capabilities: {dashboard.proven_capability_count ?? 0}</div>
              <div>Platform healthy: {dashboard.platform_healthy ? "yes" : "no"}</div>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
