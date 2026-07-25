"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchDockerRuntime,
  fetchInfrastructureConfidence,
  fetchInfrastructureHarness,
  fetchInfrastructureState,
  fetchKubernetesRuntime,
  type DockerRuntimeState,
  type InfrastructureHarnessState,
  type InfrastructureIntelligenceState,
  type KubernetesRuntimeState,
} from "@/lib/missionControl/infrastructureIntelligenceApi";

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
  "infra-container-intelligence": "Container Intelligence",
  "infra-kubernetes-runtime": "Kubernetes Runtime",
  "infra-runtime-topology": "Runtime Topology",
  "infra-infrastructure-health": "Infrastructure Health",
  "infra-resource-pressure": "Resource Pressure",
  "infra-drift-detection": "Drift Detection",
  "infra-cluster-recovery": "Cluster Recovery",
  "infra-infrastructure-truth": "Infrastructure Truth",
};

export function InfrastructureIntelligencePanel({ view }: Props) {
  const [state, setState] = useState<InfrastructureIntelligenceState | null>(null);
  const [docker, setDocker] = useState<DockerRuntimeState | null>(null);
  const [kubernetes, setKubernetes] = useState<KubernetesRuntimeState | null>(null);
  const [harness, setHarness] = useState<InfrastructureHarnessState | null>(null);
  const [narrative, setNarrative] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "infra-container-intelligence") {
        setDocker(await fetchDockerRuntime());
      } else if (view === "infra-kubernetes-runtime" || view === "infra-cluster-recovery") {
        setKubernetes(await fetchKubernetesRuntime());
      } else if (view === "infra-infrastructure-truth") {
        const conf = await fetchInfrastructureConfidence();
        setNarrative(conf.narrative || conf.summary);
        setState(await fetchInfrastructureState());
      } else if (view === "infra-runtime-topology" || view === "infra-drift-detection") {
        setState(await fetchInfrastructureState());
      } else {
        const [full, harnessState] = await Promise.all([
          fetchInfrastructureState(),
          fetchInfrastructureHarness(),
        ]);
        setState(full);
        setHarness(harnessState);
        if (view === "infra-infrastructure-health" || view === "infra-resource-pressure") {
          setDocker(full.docker);
        }
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load infrastructure intelligence");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const title = titles[view] ?? "Infrastructure Intelligence";

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Infrastructure-level operational intelligence — containers, clusters, topology, and verified runtime recovery.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {(view === "infra-container-intelligence" || view === "infra-resource-pressure" || view === "infra-infrastructure-health") &&
        (docker || state?.docker) && (
          <div style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <span style={{ fontWeight: 600 }}>Docker runtime</span>
              <span style={{ color: maturityColor((docker || state?.docker)?.maturity), fontSize: 12 }}>
                {(docker || state?.docker)?.maturity} · {(docker || state?.docker)?.verification_coverage_pct}%
              </span>
            </div>
            <pre style={{ margin: "10px 0 0", whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>
              {(docker || state?.docker)?.summary}
            </pre>
          </div>
        )}

      {(view === "infra-kubernetes-runtime" || view === "infra-cluster-recovery") && kubernetes && (
        <div style={cardStyle}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
            <span style={{ fontWeight: 600 }}>Kubernetes rollout</span>
            <span style={{ color: maturityColor(kubernetes.maturity), fontSize: 12 }}>
              {kubernetes.maturity} · {kubernetes.verification_coverage_pct}%
            </span>
          </div>
          <pre style={{ margin: "10px 0 0", whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>
            {kubernetes.summary}
          </pre>
        </div>
      )}

      {view === "infra-runtime-topology" && state?.topology && (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>Dependency graph</span>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 12 }}>
            {state.topology.summary || state.topology.graph?.summary}
          </p>
          <p style={{ margin: "6px 0 0", fontSize: 11, color: mcColors.textDim }}>
            Critical: {(state.topology.classifications?.critical || []).join(", ") || "—"}
          </p>
        </div>
      )}

      {view === "infra-drift-detection" && state?.kubernetes?.drift && (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>Drift detection</span>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 12 }}>
            {state.kubernetes.drift.summary}
          </p>
        </div>
      )}

      {view === "infra-infrastructure-truth" && (
        <div style={cardStyle}>
          <span style={{ fontWeight: 600 }}>Infrastructure confidence</span>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13 }}>{narrative || state?.summary}</p>
        </div>
      )}

      {state?.capabilities && view === "infra-infrastructure-health" && (
        <div style={{ marginTop: 8 }}>
          {Object.entries(state.capabilities).map(([key, val]) => (
            <div key={key} style={{ ...cardStyle, display: "flex", justifyContent: "space-between" }}>
              <span>{key.replace(/_/g, " ")}</span>
              <span style={{ color: maturityColor(val) }}>{val}</span>
            </div>
          ))}
        </div>
      )}

      {harness && view === "infra-infrastructure-health" && (
        <div style={{ ...cardStyle, marginTop: 12 }}>
          <span style={{ fontWeight: 600 }}>Infrastructure harness</span>
          <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
            {harness.verified_count}/{harness.scenario_count} scenarios verified · avg {harness.average_coverage_pct}%
          </p>
        </div>
      )}
    </div>
  );
}
