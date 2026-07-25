"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import {
  appendMissionControlIndependentRepositoryTrustExpansionRecord,
  fetchMissionControlIndependentRepositoryTrustExpansion,
} from "@/lib/missionControl/missionControlIndependentRepositoryTrustExpansionApi";
import {
  fetchMissionControlCrossRepositoryMultiAgentDeliveryValidation,
} from "@/lib/missionControl/missionControlCrossRepositoryMultiAgentDeliveryValidationApi";
import {
  fetchMissionControlAgentExecutionQualityThroughputMetrics,
} from "@/lib/missionControl/missionControlAgentExecutionQualityThroughputMetricsApi";
import {
  fetchMissionControlBoundedMultiAgentDeliveryExecution,
} from "@/lib/missionControl/missionControlBoundedMultiAgentDeliveryExecutionApi";
import {
  fetchMissionControlAtlasTraderPilotArcOrchestrator,
} from "@/lib/missionControl/missionControlAtlasTraderPilotArcOrchestratorApi";
import {
  fetchMissionControlNexoraPilotArcOrchestrator,
} from "@/lib/missionControl/missionControlNexoraPilotArcOrchestratorApi";
import {
  appendMissionControlPilotosUiPilotArcOrchestratorRecord,
  fetchMissionControlPilotosUiPilotArcOrchestrator,
  runMissionControlPilotosUiPilotArcOrchestrator,
} from "@/lib/missionControl/missionControlPilotosUiPilotArcOrchestratorApi";

type Props = { sessionId?: string };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const sectionTitle = { fontWeight: 600, marginBottom: 8, color: mcColors.cyan } as const;

function errMsg(e: unknown, fallback: string) {
  return e instanceof Error ? e.message : fallback;
}

const PHASE2_REPOS = [
  "pilotmain/pilot-os-ui",
  "pilotmain/atlas-trader",
  "pilotmain/nexora-monorepo-starter",
] as const;

export function MultiRepoPilotProgramPanel({ sessionId = "operator" }: Props) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [detail, setDetail] = useState<string | null>(null);
  const [fix187, setFix187] = useState<Record<string, unknown> | null>(null);
  const [fix188, setFix188] = useState<Record<string, unknown> | null>(null);
  const [fix193, setFix193] = useState<Record<string, unknown> | null>(null);
  const [fix195, setFix195] = useState<Record<string, unknown> | null>(null);
  const [fix189, setFix189] = useState<Record<string, unknown> | null>(null);
  const [fix190, setFix190] = useState<Record<string, unknown> | null>(null);
  const [fix191, setFix191] = useState<Record<string, unknown> | null>(null);
  const [pilotosIssue, setPilotosIssue] = useState("pilotmain/pilot-os-ui#1");

  const load = useCallback(async () => {
    setError(null);
    const results = await Promise.allSettled([
      fetchMissionControlIndependentRepositoryTrustExpansion(sessionId, "json"),
      fetchMissionControlPilotosUiPilotArcOrchestrator(sessionId, "json"),
      fetchMissionControlAtlasTraderPilotArcOrchestrator(sessionId, "json"),
      fetchMissionControlNexoraPilotArcOrchestrator(sessionId, "json"),
      fetchMissionControlBoundedMultiAgentDeliveryExecution(sessionId, "json"),
      fetchMissionControlAgentExecutionQualityThroughputMetrics(sessionId, "json"),
      fetchMissionControlCrossRepositoryMultiAgentDeliveryValidation(sessionId, "json"),
    ]);
    const [r187, r188, r193, r195, r189, r190, r191] = results;
    if (r187.status === "fulfilled")
      setFix187(r187.value.independent_repository_trust_expansion as Record<string, unknown>);
    if (r188.status === "fulfilled")
      setFix188(r188.value.pilotos_ui_pilot_arc_orchestrator as Record<string, unknown>);
    if (r193.status === "fulfilled")
      setFix193(r193.value.atlas_trader_pilot_arc_orchestrator as Record<string, unknown>);
    if (r195.status === "fulfilled")
      setFix195(r195.value.nexora_pilot_arc_orchestrator as Record<string, unknown>);
    if (r189.status === "fulfilled")
      setFix189(r189.value.bounded_multi_agent_delivery_execution as Record<string, unknown>);
    if (r190.status === "fulfilled")
      setFix190(r190.value.agent_execution_quality_throughput_metrics as Record<string, unknown>);
    if (r191.status === "fulfilled")
      setFix191(r191.value.cross_repository_multi_agent_delivery_validation as Record<string, unknown>);
  }, [sessionId]);

  useEffect(() => {
    void load();
  }, [load]);

  const onApproveRepo = async (repository: string) => {
    setBusy(true);
    setDetail(null);
    try {
      await appendMissionControlIndependentRepositoryTrustExpansionRecord(
        sessionId,
        "repo_expansion_approval",
        `Operator approves ${repository} for Phase 2 multi-repo pilot`,
        repository,
      );
      setDetail(`FIX 187: expansion approved for ${repository}`);
      await load();
    } catch (e) {
      setError(errMsg(e, "Failed to record expansion approval"));
    } finally {
      setBusy(false);
    }
  };

  const onRegisterPilotosIssue = async () => {
    const issue = pilotosIssue.trim();
    if (!issue) return;
    setBusy(true);
    try {
      await appendMissionControlPilotosUiPilotArcOrchestratorRecord(
        sessionId,
        "pilot_arc_issue_registered",
        issue,
        issue,
      );
      setDetail(`FIX 188: registered ${issue}`);
      await load();
    } catch (e) {
      setError(errMsg(e, "Failed to register PilotOS issue"));
    } finally {
      setBusy(false);
    }
  };

  const onRunPilot = async (pilotNumber: 1 | 2 | 3) => {
    setBusy(true);
    setDetail(null);
    try {
      const res = await runMissionControlPilotosUiPilotArcOrchestrator(pilotNumber, sessionId);
      setDetail(
        res.ok
          ? `Pilot ${pilotNumber} ok — audit ${res.audit_id || "n/a"}`
          : `Pilot ${pilotNumber} blocked: ${(res.blockers || []).join(", ") || res.detail}`,
      );
      await load();
    } catch (e) {
      setDetail(errMsg(e, `Pilot ${pilotNumber} failed`));
    } finally {
      setBusy(false);
    }
  };

  const registry = (fix187?.repository_trust_registry as Array<Record<string, unknown>>) || [];

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 600 }}>Multi-Repo Pilot Program</h2>
      <p style={{ margin: "0 0 16px", fontSize: 13, color: mcColors.textMuted }}>
        Phase 2 repos earn trust independently
      </p>

      {error && (
        <div style={{ ...cardStyle, borderColor: mcColors.warning, color: mcColors.warning }}>{error}</div>
      )}
      {detail && <div style={{ ...cardStyle, color: mcColors.textSecondary }}>{detail}</div>}

      <div style={cardStyle}>
        <div style={sectionTitle}>FIX 187 — Repository trust expansion</div>
        <div style={{ marginBottom: 8 }}>
          Trust transfer: {String(fix187?.trust_transfer_enabled ?? fix187 ? "disabled" : "—")}
        </div>
        <div style={{ marginBottom: 8 }}>
          Next Phase 2 repo: {String(fix187?.phase_2_next_repository ?? "—")}
        </div>
        <ul style={{ margin: "0 0 10px", paddingLeft: 18 }}>
          {registry.slice(0, 4).map((row) => (
            <li key={String(row.repository)}>
              {String(row.repository)} — {String(row.trust_state)}
              {row.expansion_approved ? " ✓ approved" : ""}
            </li>
          ))}
        </ul>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {PHASE2_REPOS.map((repo) => (
            <button
              key={repo}
              type="button"
              disabled={busy}
              style={mcButtonSecondaryStyle}
              onClick={() => void onApproveRepo(repo)}
            >
              Approve {repo.split("/")[1]}
            </button>
          ))}
        </div>
      </div>

      <div style={cardStyle}>
        <div style={sectionTitle}>FIX 188 — PilotOS UI pilot arc</div>
        <div style={{ marginBottom: 8 }}>Arc state: {String(fix188?.arc_state ?? "—")}</div>
        <input
          value={pilotosIssue}
          onChange={(e) => setPilotosIssue(e.target.value)}
          placeholder="pilotmain/pilot-os-ui#1"
          style={{ width: "100%", maxWidth: 360, marginBottom: 8, padding: "6px 8px", fontSize: 13 }}
        />
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          <button type="button" disabled={busy} style={mcButtonSecondaryStyle} onClick={() => void onRegisterPilotosIssue()}>
            Register issue
          </button>
          {([1, 2, 3] as const).map((n) => (
            <button
              key={n}
              type="button"
              disabled={busy}
              style={mcButtonSecondaryStyle}
              onClick={() => void onRunPilot(n)}
            >
              Run pilot {n}
            </button>
          ))}
        </div>
      </div>

      <div style={cardStyle}>
        <div style={sectionTitle}>FIX 193 / 195 — Atlas & Nexora arcs</div>
        <div>Atlas arc: {String(fix193?.arc_state ?? "—")}</div>
        <div>Nexora arc: {String(fix195?.arc_state ?? "—")}</div>
        <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
          Seed expansion via MC buttons above, then use chat or scripts/generate_atlas_operational_proof_reports.py
        </p>
      </div>

      <div style={cardStyle}>
        <div style={sectionTitle}>FIX 189–191 — Multi-agent delivery</div>
        <div>Bounded pipeline blockers: {((fix189?.blockers as string[]) || []).join(", ") || "none listed"}</div>
        <div>Throughput metrics ok: {fix190 ? "composed" : "—"}</div>
        <div>
          Cross-repo validation:{" "}
          {String(
            (fix191?.validation_status as string) ||
              (fix191 as Record<string, unknown> | null)?.cross_repository_validation_status ||
              "—",
          )}
        </div>
      </div>

      <button type="button" disabled={busy} style={mcButtonSecondaryStyle} onClick={() => void load()}>
        Refresh program state
      </button>
    </section>
  );
}
