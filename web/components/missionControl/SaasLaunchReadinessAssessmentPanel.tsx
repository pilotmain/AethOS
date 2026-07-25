"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlSaasLaunchReadinessAssessment,
  type SaasLaunchReadinessAssessmentResponse,
} from "@/lib/missionControl/missionControlSaasLaunchReadinessAssessmentApi";

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

export function SaasLaunchReadinessAssessmentPanel() {
  const [payload, setPayload] = useState<SaasLaunchReadinessAssessmentResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlSaasLaunchReadinessAssessment("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load SaaS launch readiness assessment");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.saas_launch_readiness_assessment as
    | {
        overall_launch_status?: string;
        sections?: Record<string, Array<Record<string, unknown>>>;
      }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.launch_readiness_dashboard ?? [{}])[0] as {
    overall_status?: string;
    domain_scores?: Record<string, string>;
    blockers?: string[];
    risk_count?: number;
    evidence_coverage?: { fix_300_308_composed?: number; fix_300_308_total?: number };
  };
  const risks = (sections.launch_risk_registry ?? [{}])[0] as {
    high?: Array<{ detail?: string; domain?: string }>;
    medium?: Array<{ detail?: string; domain?: string }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>SaaS Launch Readiness</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Evidence-backed launch assessment — humans decide launch readiness, not AethOS.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          <div style={cardStyle}>
            <strong>Overall launch status</strong>
            <div>{board?.overall_launch_status ?? dashboard.overall_status}</div>
            <div style={{ color: mcColors.textMuted }}>
              Evidence coverage: {dashboard.evidence_coverage?.fix_300_308_composed ?? 0} /{" "}
              {dashboard.evidence_coverage?.fix_300_308_total ?? 9}
            </div>
          </div>

          <div style={cardStyle}>
            <strong>Domain scores</strong>
            {Object.entries(dashboard.domain_scores ?? {}).map(([domain, score]) => (
              <div key={domain}>
                {domain}: {score}
              </div>
            ))}
          </div>

          <div style={cardStyle}>
            <strong>Blockers & risks</strong>
            {(dashboard.blockers ?? []).slice(0, 4).map((blocker) => (
              <div key={blocker}>{blocker}</div>
            ))}
            {(risks.high ?? []).slice(0, 3).map((risk) => (
              <div key={risk.detail} style={{ color: mcColors.amber }}>
                [{risk.domain}] {risk.detail}
              </div>
            ))}
            <div style={{ color: mcColors.textMuted }}>Total risks: {dashboard.risk_count ?? 0}</div>
          </div>

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            launch_authority: {String(payload.launch_authority)} · automatic_launch_enabled:{" "}
            {String(payload.automatic_launch_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
