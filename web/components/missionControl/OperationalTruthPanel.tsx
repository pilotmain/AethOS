"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchCapabilityAudit,
  fetchCapabilityMatrix,
  fetchConfidenceIntegrity,
  fetchOperationalTruthFull,
  fetchOperationalTruthState,
  fetchProviderReadiness,
  fetchRealityHarnessState,
  runRealityHarnessCycle,
  type CapabilityTruthRow,
  type OperationalTruthFull,
} from "@/lib/missionControl/operationalTruthApi";
import {
  fetchRailwayInventory,
  providerTopologyFromInventory,
  providerTopologyLabel,
  type ProviderInventoryPayload,
} from "@/lib/missionControl/providerDiscovery";

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
  if (tier === "production-ready" || tier === "stable") return mcColors.green;
  if (tier === "beta") return mcColors.cyan;
  if (tier === "alpha") return mcColors.amber;
  return mcColors.textMuted;
};

const titles: Record<string, string> = {
  "truth-capability-matrix": "Capability Matrix",
  "truth-provider-readiness": "Provider Readiness",
  "truth-verification-coverage": "Verification Coverage",
  "truth-mutation-reliability": "Mutation Reliability",
  "truth-operational-honesty": "Operational Honesty",
  "truth-runtime-validation": "Runtime Validation",
  "truth-reality-harness": "Reality Harness",
  "truth-production-readiness": "Production Readiness",
};

export function OperationalTruthPanel({ view }: Props) {
  const [state, setState] = useState<OperationalTruthFull | null>(null);
  const [matrix, setMatrix] = useState<CapabilityTruthRow[]>([]);
  const [audit, setAudit] = useState<{ category: string; status: string; coverage_pct: number; summary: string }[]>([]);
  const [providers, setProviders] = useState<Record<string, unknown>[]>([]);
  const [confidence, setConfidence] = useState<Record<string, unknown> | null>(null);
  const [harness, setHarness] = useState<Record<string, unknown> | null>(null);
  const [railwayInventory, setRailwayInventory] = useState<ProviderInventoryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "truth-capability-matrix") {
        const res = await fetchCapabilityMatrix();
        setMatrix(res.matrix);
        setState({ ok: true, matrix_summary: res.summary });
      } else if (view === "truth-provider-readiness") {
        const res = await fetchProviderReadiness();
        setProviders(res.providers);
        setRailwayInventory(await fetchRailwayInventory());
        setState({ ok: true, readiness: res.readiness });
      } else if (view === "truth-verification-coverage" || view === "truth-operational-honesty") {
        setState(await fetchOperationalTruthFull());
      } else if (view === "truth-runtime-validation") {
        const full = await fetchOperationalTruthFull();
        setState(full);
        setConfidence(await fetchConfidenceIntegrity());
      } else if (view === "truth-reality-harness") {
        setHarness(await fetchRealityHarnessState());
      } else if (view === "truth-production-readiness") {
        const snap = await fetchOperationalTruthState();
        const full = await fetchOperationalTruthFull();
        setState({ ...full, truth_state: snap.truth_state, truth_degraded: snap.truth_degraded });
      } else {
        const auditRes = await fetchCapabilityAudit();
        setAudit(auditRes.audit_categories ?? []);
        setState(await fetchOperationalTruthFull());
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load operational truth");
    }
  }, [view]);

  useEffect(() => {
    void load();
  }, [load]);

  const onRunHarness = async () => {
    setBusy(true);
    try {
      await runRealityHarnessCycle();
      setHarness(await fetchRealityHarnessState());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Harness cycle failed");
    } finally {
      setBusy(false);
    }
  };

  const title = titles[view] ?? "Operational Truth";

  return (
    <div style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted, fontSize: 13, maxWidth: 720 }}>
            Operational truth convergence — claimed capabilities vs verified production reality.
          </p>
        </div>
        <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.red, fontSize: 13 }}>{error}</p> : null}

      {(view === "truth-production-readiness" || view === "truth-mutation-reliability") && state ? (
        <div style={cardStyle}>
          <div style={{ fontSize: 11, color: mcColors.textDim, letterSpacing: "0.06em", textTransform: "uppercase" }}>
            System truth
          </div>
          <div style={{ marginTop: 8, fontSize: 16, color: state.truth_degraded ? mcColors.amber : mcColors.green }}>
            {state.truth_state?.replace(/_/g, " ") ?? "assessing"}
          </div>
          <p style={{ margin: "10px 0 0", color: mcColors.textMuted }}>{state.summary}</p>
          {state.readiness ? (
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textDim }}>
              Readiness: {String((state.readiness as { readiness_tier?: string }).readiness_tier ?? "—")} ·{" "}
              {String((state.readiness as { readiness_score?: number }).readiness_score ?? "—")}% composite
            </p>
          ) : null}
        </div>
      ) : null}

      {view === "truth-capability-matrix" ? (
        matrix.map((row) => (
          <div key={row.id} style={cardStyle}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
              <strong>{row.name}</strong>
              <span style={{ color: maturityColor(row.maturity), fontSize: 12 }}>{row.maturity}</span>
            </div>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              Claimed: {row.claimed ? "yes" : "no"} · Real: {row.real} · Verified: {row.verified} · Coverage:{" "}
              {row.verification_coverage_pct}%
            </p>
            <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textDim }}>{row.honest_summary}</p>
          </div>
        ))
      ) : null}

      {view === "truth-provider-readiness" ? (
        <>
          {providers.map((p) => (
            <div key={String(p.provider)} style={cardStyle}>
              <strong>{String(p.provider)}</strong>
              <span style={{ marginLeft: 8, fontSize: 11, color: mcColors.textDim }}>
                {String(p.tier)} · {String(p.priority)}
              </span>
              <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textMuted }}>
                Registered: {p.registered ? "yes" : "no"} · Status: {String(p.hardening_status)}
              </p>
            </div>
          ))}
          {state?.readiness ? (
            <div style={cardStyle}>
              <strong>Production readiness</strong>
              <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
                {String((state.readiness as { summary?: string }).summary ?? "")}
              </p>
            </div>
          ) : null}
          {providerTopologyFromInventory(railwayInventory) ? (
            <div style={cardStyle}>
              <strong>Railway topology</strong>
              <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
                {providerTopologyLabel(providerTopologyFromInventory(railwayInventory)!)}
              </p>
              {railwayInventory?.projects?.map((project) =>
                project.environments?.map((environment) => (
                  <div key={`${project.id}-${environment.id}`} style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 12, color: mcColors.textDim }}>
                      {project.name} / {environment.name}
                    </div>
                    <ul style={{ margin: "6px 0 0", paddingLeft: 18, fontSize: 12 }}>
                      {(environment.services ?? []).map((service) => (
                        <li key={service.id}>
                          {service.name} — {service.status ?? "unknown"}
                          {service.domain ? ` · ${service.domain}` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                )),
              )}
            </div>
          ) : null}
        </>
      ) : null}

      {(view === "truth-verification-coverage" || view === "truth-operational-honesty") && state ? (
        <>
          {state.execution_integrity ? (
            <div style={cardStyle}>
              <strong>Execution integrity</strong>
              <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
                {String((state.execution_integrity as { summary?: string }).summary ?? "")}
              </p>
            </div>
          ) : null}
          {state.operational_honesty ? (
            <div style={cardStyle}>
              <strong>Operational honesty</strong>
              <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>
                {String((state.operational_honesty as { recommended_phrasing?: string }).recommended_phrasing ?? "")}
              </p>
            </div>
          ) : null}
        </>
      ) : null}

      {view === "truth-runtime-validation" && confidence ? (
        <div style={cardStyle}>
          <strong>Confidence integrity: {String(confidence.integrity)}</strong>
          <p style={{ margin: "8px 0 0", color: mcColors.textMuted }}>{String(confidence.summary ?? "")}</p>
          <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textDim }}>
            Bounded confidence: {String(confidence.bounded_confidence ?? "—")}
          </p>
        </div>
      ) : null}

      {view === "truth-reality-harness" && harness ? (
        <>
          <div style={{ marginBottom: 12 }}>
            <button type="button" style={mcButtonSecondaryStyle} disabled={busy} onClick={() => void onRunHarness()}>
              {busy ? "Running cycle…" : "Run reality harness cycle"}
            </button>
          </div>
          {(harness.scenarios as { id: string; name: string; status: string; coverage_pct: number }[] | undefined)?.map(
            (s) => (
              <div key={s.id} style={cardStyle}>
                <strong>{s.name}</strong>
                <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textMuted }}>
                  Status: {s.status} · Coverage: {s.coverage_pct}%
                </p>
              </div>
            ),
          )}
        </>
      ) : null}

      {view === "truth-mutation-reliability" && audit.length > 0 ? (
        audit.map((a) => (
          <div key={a.category} style={cardStyle}>
            <strong>{a.category.replace(/_/g, " ")}</strong>
            <p style={{ margin: "6px 0 0", fontSize: 12, color: mcColors.textMuted }}>{a.summary}</p>
          </div>
        ))
      ) : null}
    </div>
  );
}
