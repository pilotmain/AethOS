"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlLaunchOperationsCenter,
  LAUNCH_OPERATIONS_FOCUS_BY_VIEW,
  type LaunchOperationsFocus,
  type LaunchOperationsCenterResponse,
} from "@/lib/missionControl/missionControlLaunchOperationsCenterApi";

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
  focus?: LaunchOperationsFocus;
  title?: string;
};

export function LaunchOperationsCenterPanel({
  viewId = "launch-operations-center",
  focus,
  title = "Launch Operations Center",
}: Props) {
  const resolvedFocus = focus ?? LAUNCH_OPERATIONS_FOCUS_BY_VIEW[viewId] ?? "launch_operations_dashboard";
  const [payload, setPayload] = useState<LaunchOperationsCenterResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlLaunchOperationsCenter("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load launch operations center");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.launch_operations_center as
    | {
        current_launch_phase?: string;
        launch_recommendation?: string;
        sections?: Record<string, Array<Record<string, unknown>>>;
      }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.launch_operations_dashboard ?? [{}])[0] as {
    blocker_count?: number;
    critical_risk_count?: number;
    platform_healthy?: boolean;
    healthy_count?: number;
    at_risk_count?: number;
  };
  const status = (sections.launch_status_registry ?? [{}])[0] as {
    readiness_status?: string;
    beta_status?: string;
    review_status?: string;
  };
  const blockers = (sections.launch_blocker_registry ?? [{}])[0] as {
    blockers?: Array<{ source?: string; detail?: string }>;
  };
  const risks = (sections.launch_risk_dashboard ?? [{}])[0] as {
    product?: Array<{ level?: string; detail?: string }>;
    operational?: Array<{ level?: string; detail?: string }>;
  };
  const beta = (sections.beta_operations_monitor ?? [{}])[0] as {
    active_cohort_count?: number;
    feedback_count?: number;
    activation_rate?: number;
  };
  const customer = (sections.customer_operations_monitor ?? [{}])[0] as {
    healthy_count?: number;
    at_risk_count?: number;
    open_escalation_count?: number;
  };
  const evidence = (sections.launch_evidence_registry ?? [{}])[0] as {
    readiness_evidence?: Record<string, unknown>;
    beta_evidence?: Record<string, unknown>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Unified launch command center — observe and assess, never launch automatically.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Launch state</strong>
            <div>Phase: {board?.current_launch_phase ?? "—"}</div>
            <div>Recommendation: {board?.launch_recommendation ?? "—"}</div>
            <div style={{ color: mcColors.textMuted }}>
              Readiness: {status.readiness_status ?? "—"} · Beta: {status.beta_status ?? "—"}
            </div>
          </div>

          {(resolvedFocus === "launch_operations_dashboard" ||
            resolvedFocus === "launch_blocker_registry") && (
            <div style={cardStyle}>
              <strong>Blockers ({dashboard.blocker_count ?? 0})</strong>
              {(blockers.blockers ?? []).slice(0, 4).map((row) => (
                <div key={row.detail}>
                  [{row.source}] {row.detail}
                </div>
              ))}
            </div>
          )}

          {(resolvedFocus === "launch_operations_dashboard" || resolvedFocus === "launch_risk_dashboard") && (
            <div style={cardStyle}>
              <strong>Risks</strong>
              {[...(risks.product ?? []), ...(risks.operational ?? [])].slice(0, 4).map((row) => (
                <div key={row.detail} style={{ color: mcColors.amber }}>
                  [{row.level}] {row.detail}
                </div>
              ))}
              <div style={{ color: mcColors.textMuted }}>
                Critical: {dashboard.critical_risk_count ?? 0}
              </div>
            </div>
          )}

          {resolvedFocus === "beta_operations_monitor" && (
            <div style={cardStyle}>
              <strong>Beta operations</strong>
              <div>Active cohorts: {beta.active_cohort_count ?? 0}</div>
              <div>Feedback: {beta.feedback_count ?? 0}</div>
              <div>Activation: {beta.activation_rate ?? 0}%</div>
            </div>
          )}

          {resolvedFocus === "customer_operations_monitor" && (
            <div style={cardStyle}>
              <strong>Customer operations</strong>
              <div>Healthy: {customer.healthy_count ?? 0}</div>
              <div>At risk: {customer.at_risk_count ?? 0}</div>
              <div>Escalations: {customer.open_escalation_count ?? 0}</div>
            </div>
          )}

          {resolvedFocus === "launch_evidence_registry" && (
            <div style={cardStyle}>
              <strong>Evidence</strong>
              <div>Launch: {String((evidence.readiness_evidence as { launch_status?: string })?.launch_status)}</div>
              <div>Beta: {String((evidence.beta_evidence as { beta_recommendation?: string })?.beta_recommendation)}</div>
            </div>
          )}

          {resolvedFocus === "launch_operations_dashboard" && (
            <div style={cardStyle}>
              <strong>Health summary</strong>
              <div>Platform healthy: {String(dashboard.platform_healthy ?? false)}</div>
              <div>Customers healthy/at-risk: {dashboard.healthy_count ?? 0}/{dashboard.at_risk_count ?? 0}</div>
            </div>
          )}

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            launch_operations_authority: {String(payload.launch_operations_authority)} · automatic_launch_enabled:{" "}
            {String(payload.automatic_launch_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
