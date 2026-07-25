"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlPublicLaunchReadinessFreeze,
  LAUNCH_READINESS_FREEZE_FOCUS_BY_VIEW,
  type LaunchReadinessFreezeFocus,
  type PublicLaunchReadinessFreezeResponse,
} from "@/lib/missionControl/missionControlPublicLaunchReadinessFreezeApi";

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
  focus?: LaunchReadinessFreezeFocus;
  title?: string;
};

export function PublicLaunchReadinessFreezePanel({
  viewId = "launch-readiness-freeze",
  focus,
  title = "Public Launch Readiness Freeze",
}: Props) {
  const resolvedFocus =
    focus ?? LAUNCH_READINESS_FREEZE_FOCUS_BY_VIEW[viewId] ?? "launch_readiness_freeze_dashboard";
  const [payload, setPayload] = useState<PublicLaunchReadinessFreezeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlPublicLaunchReadinessFreeze("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load launch readiness freeze");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.public_launch_readiness_freeze as
    | {
        launch_recommendation_freeze?: string;
        sections?: Record<string, Array<Record<string, unknown>>>;
      }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.launch_readiness_freeze_dashboard ?? [{}])[0] as {
    blocker_count?: number;
    risk_count?: number;
    trust_baseline_count?: number;
    proven_capability_count?: number;
    unproven_capability_count?: number;
    platform_healthy?: boolean;
    proven_items?: string[];
    unproven_items?: string[];
  };
  const recommendation = (sections.launch_recommendation_freeze ?? [{}])[0] as {
    recommendation?: string;
    rationale?: string;
  };
  const timeline = (sections.launch_evidence_timeline ?? [{}])[0] as {
    events?: Array<{ fix?: string; detail?: string }>;
  };
  const trust = (sections.launch_trust_baseline_summary ?? [{}])[0] as {
    baselines?: Array<{ product?: string; fix?: string; trust_state?: string }>;
  };
  const blockers = (sections.launch_blocker_freeze ?? [{}])[0] as {
    blockers?: Array<{ source?: string; detail?: string }>;
  };
  const risks = (sections.launch_risk_freeze ?? [{}])[0] as {
    risks?: Array<{ level?: string; detail?: string }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Official launch evidence baseline — freeze ≠ launch authority. Humans decide launch.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Launch recommendation freeze</strong>
            <div>{board?.launch_recommendation_freeze ?? recommendation.recommendation ?? "—"}</div>
            <div style={{ color: mcColors.textMuted, marginTop: 6 }}>
              {recommendation.rationale ?? "Derived from frozen evidence only — no launch execution."}
            </div>
          </div>

          {resolvedFocus === "launch_readiness_freeze_dashboard" ||
          resolvedFocus === "launch_evidence_timeline" ? (
            <div style={cardStyle}>
              <strong>Launch evidence timeline</strong>
              {(timeline.events ?? []).slice(0, 6).map((event, idx) => (
                <div key={`${event.fix}-${idx}`} style={{ marginTop: 6 }}>
                  [{event.fix}] {event.detail}
                </div>
              ))}
            </div>
          ) : null}

          {resolvedFocus === "launch_readiness_freeze_dashboard" ? (
            <>
              <div style={cardStyle}>
                <strong>Frozen baseline summary</strong>
                <div>Trust baselines: {dashboard.trust_baseline_count ?? 0}</div>
                <div>Proven capabilities: {dashboard.proven_capability_count ?? 0}</div>
                <div>Unproven capabilities: {dashboard.unproven_capability_count ?? 0}</div>
                <div>Blockers frozen: {dashboard.blocker_count ?? 0}</div>
                <div>Risks frozen: {dashboard.risk_count ?? 0}</div>
                <div>Platform healthy: {dashboard.platform_healthy ? "yes" : "no"}</div>
              </div>
              <div style={cardStyle}>
                <strong>Trust baselines</strong>
                {(trust.baselines ?? []).map((row) => (
                  <div key={row.product} style={{ marginTop: 6 }}>
                    {row.product} ({row.fix}): {row.trust_state}
                  </div>
                ))}
              </div>
            </>
          ) : null}

          {resolvedFocus === "launch_recommendation_freeze" ? (
            <>
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

          {resolvedFocus === "launch_blocker_freeze" ? (
            <div style={cardStyle}>
              <strong>Launch blockers (frozen)</strong>
              {(blockers.blockers ?? []).slice(0, 8).map((row, idx) => (
                <div key={`${row.source}-${idx}`} style={{ marginTop: 6 }}>
                  [{row.source}] {row.detail}
                </div>
              ))}
            </div>
          ) : null}

          {resolvedFocus === "launch_risk_freeze" ? (
            <div style={cardStyle}>
              <strong>Launch risks (frozen)</strong>
              {(risks.risks ?? []).slice(0, 8).map((row, idx) => (
                <div key={`${row.level}-${idx}`} style={{ marginTop: 6 }}>
                  [{row.level}] {row.detail}
                </div>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
