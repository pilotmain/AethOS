"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  BETA_PROGRAM_FOCUS_BY_VIEW,
  fetchMissionControlLimitedBetaLaunchProgram,
  type BetaProgramFocus,
  type LimitedBetaLaunchProgramResponse,
} from "@/lib/missionControl/missionControlLimitedBetaLaunchProgramApi";

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
  focus?: BetaProgramFocus;
  title?: string;
};

export function LimitedBetaLaunchProgramPanel({
  viewId = "beta-launch-program",
  focus,
  title = "Beta Launch Program",
}: Props) {
  const resolvedFocus = focus ?? BETA_PROGRAM_FOCUS_BY_VIEW[viewId] ?? "beta_operations_dashboard";
  const [payload, setPayload] = useState<LimitedBetaLaunchProgramResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlLimitedBetaLaunchProgram("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load beta launch program");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.limited_beta_launch_program as
    | {
        beta_launch_recommendation?: string;
        sections?: Record<string, Array<Record<string, unknown>>>;
      }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.beta_operations_dashboard ?? [{}])[0] as {
    active_cohort_count?: number;
    active_participant_count?: number;
    open_risk_count?: number;
    activation_rate?: number;
    customer_health_score?: number;
  };
  const cohorts = (sections.beta_cohort_registry ?? [{}])[0] as {
    cohorts?: Array<{ cohort_name?: string; status?: string; current_size?: number; target_size?: number }>;
  };
  const feedback = (sections.beta_feedback_registry ?? [{}])[0] as {
    feedback_items?: Array<{ category?: string; content?: string }>;
  };
  const metrics = (sections.beta_success_metrics ?? [{}])[0] as {
    activation_rate?: number;
    onboarding_completion?: number;
    provider_connection_completion?: number;
    workflow_completion?: number;
    customer_health_score?: number;
  };
  const recommendation = (sections.beta_launch_recommendation ?? [{}])[0] as {
    recommendation?: string;
    rationale?: string;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Governed beta framework — humans remain responsible for admissions, not AethOS.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Beta launch recommendation</strong>
            <div>{board?.beta_launch_recommendation ?? recommendation.recommendation ?? "—"}</div>
            <div style={{ color: mcColors.textMuted, marginTop: 6 }}>
              {recommendation.rationale ?? "Derived from evidence only — no automatic launch."}
            </div>
          </div>

          {(resolvedFocus === "beta_operations_dashboard" || resolvedFocus === "beta_cohort_registry") && (
            <div style={cardStyle}>
              <strong>Cohorts</strong>
              {(cohorts.cohorts ?? []).map((cohort) => (
                <div key={cohort.cohort_name}>
                  {cohort.cohort_name} ({cohort.status}): {cohort.current_size}/{cohort.target_size}
                </div>
              ))}
              <div style={{ color: mcColors.textMuted, marginTop: 6 }}>
                Active participants: {dashboard.active_participant_count ?? 0} · Open risks:{" "}
                {dashboard.open_risk_count ?? 0}
              </div>
            </div>
          )}

          {resolvedFocus === "beta_feedback_registry" && (
            <div style={cardStyle}>
              <strong>Feedback</strong>
              {(feedback.feedback_items ?? []).slice(0, 5).map((item) => (
                <div key={item.content}>
                  [{item.category}] {item.content}
                </div>
              ))}
            </div>
          )}

          {resolvedFocus === "beta_success_metrics" && (
            <div style={cardStyle}>
              <strong>Success metrics</strong>
              <div>Activation: {metrics.activation_rate ?? 0}%</div>
              <div>Onboarding: {metrics.onboarding_completion ?? 0}%</div>
              <div>Provider connection: {metrics.provider_connection_completion ?? 0}%</div>
              <div>Customer health: {metrics.customer_health_score ?? 0}</div>
            </div>
          )}

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            beta_authority: {String(payload.beta_authority)} · automatic_customer_provisioning_enabled:{" "}
            {String(payload.automatic_customer_provisioning_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
