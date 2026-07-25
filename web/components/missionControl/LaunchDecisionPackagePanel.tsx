"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlLaunchDecisionPackage,
  LAUNCH_DECISION_PACKAGE_FOCUS_BY_VIEW,
  type LaunchDecisionPackageFocus,
  type LaunchDecisionPackageResponse,
} from "@/lib/missionControl/missionControlLaunchDecisionPackageApi";

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
  focus?: LaunchDecisionPackageFocus;
  title?: string;
};

export function LaunchDecisionPackagePanel({
  viewId = "launch-decision-package",
  focus,
  title = "Launch Decision Package",
}: Props) {
  const resolvedFocus =
    focus ?? LAUNCH_DECISION_PACKAGE_FOCUS_BY_VIEW[viewId] ?? "launch_decision_dashboard";
  const [payload, setPayload] = useState<LaunchDecisionPackageResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlLaunchDecisionPackage("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load launch decision package");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.launch_decision_package as
    | {
        launch_recommendation_package?: string;
        sections?: Record<string, Array<Record<string, unknown>>>;
      }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.launch_decision_dashboard ?? [{}])[0] as {
    open_blocker_count?: number;
    critical_risk_count?: number;
    trust_baseline_count?: number;
    platform_healthy?: boolean;
    proven_items?: string[];
    unproven_items?: string[];
    decision_options?: string[];
  };
  const executive = (sections.launch_executive_summary ?? [{}])[0] as {
    platform_summary?: string;
    readiness_summary?: string;
    trust_summary?: string;
    recommendation_summary?: string;
  };
  const recommendation = (sections.launch_recommendation_package ?? [{}])[0] as {
    recommendation?: string;
    rationale?: string;
    decision_options?: string[];
  };
  const registry = (sections.launch_decision_registry ?? [{}])[0] as {
    records?: Array<{ kind?: string; content?: string; recorded_at?: string }>;
    record_count?: number;
  };
  const blockers = (sections.launch_blocker_summary ?? [{}])[0] as {
    open?: Array<{ source?: string; detail?: string }>;
  };
  const risks = (sections.launch_risk_summary ?? [{}])[0] as {
    critical?: Array<{ detail?: string }>;
    high?: Array<{ detail?: string }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Final launch review package — package ≠ launch decision. Humans approve launch.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Launch recommendation package</strong>
            <div>{board?.launch_recommendation_package ?? recommendation.recommendation ?? "—"}</div>
            <div style={{ color: mcColors.textMuted, marginTop: 6 }}>
              {recommendation.rationale ?? "Derived from frozen evidence only — no launch approval."}
            </div>
          </div>

          {resolvedFocus === "launch_executive_summary" ||
          resolvedFocus === "launch_decision_dashboard" ? (
            <div style={cardStyle}>
              <strong>Executive summary</strong>
              <div style={{ marginTop: 6 }}>{executive.platform_summary}</div>
              <div style={{ marginTop: 6 }}>{executive.readiness_summary}</div>
              <div style={{ marginTop: 6 }}>{executive.trust_summary}</div>
              <div style={{ marginTop: 6 }}>{executive.recommendation_summary}</div>
            </div>
          ) : null}

          {resolvedFocus === "launch_decision_dashboard" ? (
            <>
              <div style={cardStyle}>
                <strong>Review package summary</strong>
                <div>Open blockers: {dashboard.open_blocker_count ?? 0}</div>
                <div>Critical risks: {dashboard.critical_risk_count ?? 0}</div>
                <div>Trust baselines: {dashboard.trust_baseline_count ?? 0}</div>
                <div>Platform healthy: {dashboard.platform_healthy ? "yes" : "no"}</div>
              </div>
              <div style={cardStyle}>
                <strong>Open blockers</strong>
                {(blockers.open ?? []).slice(0, 6).map((row, idx) => (
                  <div key={`${row.source}-${idx}`} style={{ marginTop: 6 }}>
                    [{row.source}] {row.detail}
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {resolvedFocus === "launch_recommendation_package" ? (
            <>
              <div style={cardStyle}>
                <strong>Decision options</strong>
                {(recommendation.decision_options ?? dashboard.decision_options ?? []).map((option) => (
                  <div key={option} style={{ marginTop: 6 }}>
                    {option}
                  </div>
                ))}
              </div>
              <div style={cardStyle}>
                <strong>What is proven</strong>
                {(dashboard.proven_items ?? []).map((item) => (
                  <div key={item} style={{ marginTop: 6 }}>
                    {item}
                  </div>
                ))}
              </div>
              <div style={cardStyle}>
                <strong>What remains unproven</strong>
                {(dashboard.unproven_items ?? []).map((item) => (
                  <div key={item} style={{ marginTop: 6 }}>
                    {item}
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {resolvedFocus === "launch_decision_registry" ? (
            <div style={cardStyle}>
              <strong>Decision history ({registry.record_count ?? 0})</strong>
              {(registry.records ?? []).slice().reverse().map((row, idx) => (
                <div key={`${row.kind}-${idx}`} style={{ marginTop: 6 }}>
                  [{row.kind}] {row.content}
                </div>
              ))}
            </div>
          ) : null}

          {resolvedFocus === "launch_decision_dashboard" &&
          (risks.critical?.length || risks.high?.length) ? (
            <div style={cardStyle}>
              <strong>Top risks</strong>
              {[...(risks.critical ?? []), ...(risks.high ?? [])].slice(0, 4).map((row, idx) => (
                <div key={`risk-${idx}`} style={{ marginTop: 6 }}>
                  {row.detail}
                </div>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
