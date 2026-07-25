"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchProductionReliabilityState,
  fetchTier1Providers,
  type ProductionReliabilityState,
  type Tier1Provider,
} from "@/lib/missionControl/productionReliabilityApi";
import { fetchRealityHarnessState, type RealityScenario } from "@/lib/missionControl/operationalTruthApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const maturityColor = (tier?: string) => {
  if (tier === "stable" || tier === "production-ready") return mcColors.green;
  if (tier === "beta") return mcColors.cyan;
  return mcColors.amber;
};

const titles: Record<string, string> = {
  "reliability-providers": "Provider Reliability",
  "reliability-deployment-verification": "Deployment Verification",
  "reliability-recovery-runtime": "Recovery Runtime",
  "reliability-mutation-reconciliation": "Mutation Reconciliation",
  "reliability-rollback-integrity": "Rollback Integrity",
  "reliability-runtime-stabilization": "Runtime Stabilization",
  "reliability-operational-confidence": "Operational Confidence",
  "reliability-reality-validation": "Reality Validation",
};

export function ProductionReliabilityPanel({ view }: Props) {
  const [state, setState] = useState<ProductionReliabilityState | null>(null);
  const [providers, setProviders] = useState<Tier1Provider[]>([]);
  const [scenarios, setScenarios] = useState<RealityScenario[]>([]);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "reliability-providers") {
        const res = await fetchTier1Providers();
        setProviders(res.providers);
      } else if (view === "reliability-reality-validation") {
        const harness = await fetchRealityHarnessState();
        setScenarios(harness.scenarios ?? []);
      } else {
        setState(await fetchProductionReliabilityState());
        const res = await fetchTier1Providers();
        setProviders(res.providers);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load production reliability");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const title = titles[view] ?? "Production Reliability";
  const tier1Caps = state?.tier1_capabilities ?? [];

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Tier 1 provider hardening — verified execution and production reliability convergence.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {state?.harness_version ? (
        <div style={cardStyle}>
          <span style={{ fontSize: 11, color: mcColors.textDim }}>Harness {state.harness_version}</span>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
            Average verification coverage: {String(state.matrix_summary?.average_verification_coverage_pct ?? "—")}%
          </p>
        </div>
      ) : null}

      {(view === "reliability-providers" || view === "reliability-deployment-verification") &&
        providers.map((p) => (
          <div key={p.provider} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <strong>{p.provider}</strong>
              <span style={{ color: maturityColor(p.maturity), fontSize: 12 }}>{p.maturity}</span>
            </div>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              {p.capabilities.join(", ")} · {p.verification_coverage_pct}% verified · {p.hardening_status}
            </p>
          </div>
        ))}

      {(view === "reliability-mutation-reconciliation" ||
        view === "reliability-runtime-stabilization" ||
        view === "reliability-recovery-runtime") &&
        tier1Caps.map((cap) => (
          <div key={String(cap.id)} style={cardStyle}>
            <strong>{String(cap.name)}</strong>
            <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              {String(cap.maturity)} · {String(cap.verification_coverage_pct)}% · {String(cap.honest_summary)}
            </p>
          </div>
        ))}

      {view === "reliability-rollback-integrity" ? (
        <div style={cardStyle}>
          <strong>Rollback integrity</strong>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
            Rollback verification matures through reconciliation and health restoration checks across Tier 1 providers.
          </p>
        </div>
      ) : null}

      {view === "reliability-operational-confidence" && state?.matrix_summary ? (
        <div style={cardStyle}>
          <strong>Evidence-weighted operational confidence</strong>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
            Verified capabilities: {String(state.matrix_summary.verified_count)} / {String(state.matrix_summary.claimed_count)}
          </p>
        </div>
      ) : null}

      {view === "reliability-reality-validation" &&
        scenarios.map((s) => (
          <div key={s.id} style={cardStyle}>
            <strong>{s.name}</strong>
            <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              Status: {s.status} · Coverage: {s.coverage_pct}%
            </p>
          </div>
        ))}
    </div>
  );
}
