"use client";

import { useCallback, useEffect, useState } from "react";

import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  fetchMissionControlPublicProductExperience,
  PUBLIC_EXPERIENCE_FOCUS_BY_VIEW,
  type PublicExperienceFocus,
  type PublicProductExperienceResponse,
} from "@/lib/missionControl/missionControlPublicProductExperienceApi";

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
  focus?: PublicExperienceFocus;
  title?: string;
};

export function PublicProductExperiencePanel({
  viewId = "public-product-experience",
  focus,
  title = "Public Product Experience",
}: Props) {
  const resolvedFocus = focus ?? PUBLIC_EXPERIENCE_FOCUS_BY_VIEW[viewId] ?? "public_product_dashboard";
  const [payload, setPayload] = useState<PublicProductExperienceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      setPayload(await fetchMissionControlPublicProductExperience("default", "json"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load public product experience");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const board = payload?.public_product_experience as
    | { sections?: Record<string, Array<Record<string, unknown>>> }
    | undefined;
  const sections = board?.sections ?? {};
  const dashboard = (sections.public_product_dashboard ?? [{}])[0] as {
    proven_capability_count?: number;
    trust_baseline_count?: number;
    plan_count?: number;
    overall_launch_status?: string;
    getting_started?: string[];
  };
  const landing = (sections.public_landing_experience ?? [{}])[0] as {
    headline?: string;
    governance_points?: string[];
  };
  const capability = (sections.capability_explorer ?? [{}])[0] as {
    proven?: Array<{ label?: string }>;
    experimental?: Array<{ label?: string }>;
  };
  const trust = (sections.trust_explorer ?? [{}])[0] as {
    baselines?: Array<{ label?: string; fix?: string }>;
  };
  const tour = (sections.guided_product_tour ?? [{}])[0] as {
    steps?: Array<{ title?: string; detail?: string }>;
  };
  const journey = (sections.customer_journey_explorer ?? [{}])[0] as {
    paths?: Array<{ title?: string; detail?: string }>;
  };
  const education = (sections.public_education_center ?? [{}])[0] as {
    faqs?: Array<{ question?: string; answer?: string }>;
  };

  return (
    <div style={mcPanelSectionStyle}>
      <h2 style={{ marginTop: 0 }}>{title}</h2>
      <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
        Public-facing product layer — explain and guide without bypassing governance.
      </p>

      {error ? <div style={{ color: mcColors.red }}>{error}</div> : null}

      {payload ? (
        <>
          {resolvedFocus === "public_product_dashboard" && (
            <div style={cardStyle}>
              <strong>{landing.headline ?? "Governed autonomous platform"}</strong>
              <div style={{ marginTop: 8 }}>
                Proven capabilities: {dashboard.proven_capability_count ?? 0} · Trust baselines:{" "}
                {dashboard.trust_baseline_count ?? 0} · Launch status: {dashboard.overall_launch_status ?? "—"}
              </div>
            </div>
          )}

          {resolvedFocus === "capability_explorer" && (
            <div style={cardStyle}>
              <strong>Capabilities</strong>
              {(capability.proven ?? []).slice(0, 5).map((row) => (
                <div key={row.label}>Proven: {row.label}</div>
              ))}
              {(capability.experimental ?? []).slice(0, 3).map((row) => (
                <div key={row.label} style={{ color: mcColors.amber }}>
                  Experimental: {row.label}
                </div>
              ))}
            </div>
          )}

          {resolvedFocus === "trust_explorer" && (
            <div style={cardStyle}>
              <strong>Trust baselines</strong>
              {(trust.baselines ?? []).map((baseline) => (
                <div key={baseline.fix}>
                  {baseline.label} ({baseline.fix})
                </div>
              ))}
            </div>
          )}

          {resolvedFocus === "guided_product_tour" && (
            <div style={cardStyle}>
              <strong>Product tour</strong>
              {(tour.steps ?? []).map((step) => (
                <div key={step.title}>
                  <strong>{step.title}</strong>: {step.detail}
                </div>
              ))}
            </div>
          )}

          {resolvedFocus === "customer_journey_explorer" && (
            <div style={cardStyle}>
              <strong>Customer journey</strong>
              {(journey.paths ?? []).map((path) => (
                <div key={path.title}>
                  <strong>{path.title}</strong>: {path.detail}
                </div>
              ))}
            </div>
          )}

          {resolvedFocus === "public_education_center" && (
            <div style={cardStyle}>
              <strong>Education center</strong>
              {(education.faqs ?? []).map((faq) => (
                <div key={faq.question} style={{ marginBottom: 8 }}>
                  <strong>{faq.question}</strong>
                  <div>{faq.answer}</div>
                </div>
              ))}
            </div>
          )}

          {resolvedFocus === "public_product_dashboard" && (
            <div style={cardStyle}>
              <strong>Getting started</strong>
              {(dashboard.getting_started ?? []).map((item) => (
                <div key={item}>{item}</div>
              ))}
            </div>
          )}

          <div style={{ fontSize: 12, color: mcColors.textMuted }}>
            public_product_authority: {String(payload.public_product_authority)} ·
            automatic_customer_onboarding_enabled: {String(payload.automatic_customer_onboarding_enabled)}
          </div>
        </>
      ) : null}
    </div>
  );
}
