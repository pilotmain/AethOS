"use client";

import { useMemo } from "react";

import type { AgentArtifact, AgentSpec, CoordinationEvent } from "@/lib/missionControl/agentsApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  view: MissionControlView;
  agents: AgentSpec[];
  artifacts: AgentArtifact[];
  events: CoordinationEvent[];
  onRefresh: () => void;
};

type CoordPayload = {
  merged?: {
    correlation?: {
      temporal?: { detail?: string }[];
      structural?: { detail?: string }[];
      operational?: { detail?: string }[];
      correlation_count?: number;
    };
    deployment_intelligence?: {
      latest_deployment?: { id?: string; state?: string; started_label?: string };
      previous_deployment?: { id?: string; state?: string };
    };
    confidence?: { level?: string; reasons?: string[]; gaps?: string[] };
    recurring_patterns?: string[];
    pr_proposal?: { title?: string; risk_level?: string; phased_migration?: string[] };
    report_mode?: string;
  };
  graph?: {
    nodes?: { id: string; label: string; type?: string; status?: string }[];
    edges?: { from: string; to: string; label?: string; kind?: string; task?: string }[];
    replay?: { step: string; label: string }[];
  };
};

const SEVERITY_COLOR: Record<string, string> = {
  critical: mcColors.red,
  high: mcColors.amber,
  medium: "var(--aethos-accent)",
  low: mcColors.green,
  neutral: mcColors.textMuted,
};

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

function latestCoordPayload(artifacts: AgentArtifact[]): CoordPayload | null {
  const coord = artifacts.find((a) => a.artifact_type === "agent_coordination");
  if (!coord) return null;
  const payload = (coord as AgentArtifact & { payload?: CoordPayload }).payload;
  return payload ?? null;
}

export function MultiAgentPanel({ view, agents, artifacts, events, onRefresh }: Props) {
  const title = useMemo(() => {
    const labels: Partial<Record<MissionControlView, string>> = {
      "active-agents": "Active Agents",
      "agent-timelines": "Agent Timelines",
      "coordination-graph": "Coordination Graph",
      "evidence-merge": "Evidence Merge",
      "operational-intelligence": "Operational Intelligence",
      "operational-replay": "Replay Center",
      "evidence-graph": "Evidence Graph",
      "agent-evidence": "Agent Evidence",
      "engineering-proposals": "Engineering Proposals",
      "agent-policies": "Agent Policies",
      "delegated-tasks": "Delegated Tasks",
    };
    return labels[view] ?? "Multi-Agent Runtime";
  }, [view]);

  const coordArtifacts = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "agent_coordination" || a.artifact_type === "agent_summary"),
    [artifacts],
  );
  const deepEvidence = useMemo(
    () =>
      artifacts.filter((a) =>
        [
          "agent_evidence",
          "agent_execution",
          "agent_provider_diagnostics",
          "agent_browser_evidence",
          "agent_root_cause_analysis",
          "agent_operational_report",
          "engineering_architecture_graph",
          "engineering_dependency_risk",
          "engineering_git_hotspots",
          "engineering_pr_proposal",
        ].includes(a.artifact_type),
      ),
    [artifacts],
  );
  const confidenceArtifacts = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "agent_confidence_summary"),
    [artifacts],
  );
  const proposalArtifacts = useMemo(
    () => artifacts.filter((a) => a.artifact_type === "engineering_pr_proposal"),
    [artifacts],
  );
  const coordPayload = useMemo(() => latestCoordPayload(artifacts), [artifacts]);
  const failures = useMemo(() => {
    const merged = coordPayload?.merged;
    if (merged && Array.isArray((merged as { failures?: unknown[] }).failures)) {
      return (merged as { failures: unknown[] }).failures;
    }
    return [];
  }, [coordPayload]);

  const cardStyle = {
    padding: "10px 12px",
    marginBottom: 8,
    borderRadius: 10,
    border: `1px solid ${mcColors.borderSubtle}`,
    background: "rgba(0,0,0,0.18)",
  } as const;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Operational intelligence — correlated evidence, deployment timelines, and governed engineering proposals.
          </p>
        </div>
        <button type="button" onClick={onRefresh} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {(view === "active-agents" || view === "agent-policies") && (
        <div style={{ marginTop: 16 }}>
          <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>
            AethOS keeps no standing specialist roster. Agents spawn on demand from chat or the
            orchestration board — live lanes and inter-agent messages appear in{" "}
            <strong>Orchestration</strong>.
          </p>
          {agents.length === 0 && (
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
              No static agent catalog. Delegate a task or ask AethOS to create role-specific agents in chat.
            </p>
          )}
          {agents.map((agent) => {
            const execCount = artifacts.filter(
              (a) => a.agent_id === agent.agent_id && a.artifact_type === "agent_execution",
            ).length;
            return (
              <article
                key={agent.agent_id}
                style={{
                  padding: 14,
                  borderRadius: 12,
                  border: `1px solid ${mcColors.borderSubtle}`,
                  background: "rgba(0,0,0,0.22)",
                  marginBottom: 10,
                }}
              >
                <div style={{ fontWeight: 600, fontSize: 14 }}>{agent.label}</div>
                <div style={{ fontSize: 12, color: mcColors.textDim, marginTop: 4 }}>{agent.purpose}</div>
                <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 8 }}>
                  Executions tracked: {execCount}
                </div>
                {view === "agent-policies" && (
                  <>
                    <div style={{ fontSize: 11, color: mcColors.textMuted, marginTop: 8 }}>
                      Allowed: {agent.allowed.join(" · ")}
                    </div>
                    <div style={{ fontSize: 11, color: "var(--aethos-danger)", marginTop: 4 }}>
                      Blocked: {agent.blocked.join(" · ")}
                    </div>
                  </>
                )}
              </article>
            );
          })}
        </div>
      )}

      {(view === "agent-timelines" || view === "delegated-tasks") && (
        <div style={{ marginTop: 16 }}>
          {events.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              No coordination events yet. Try:{" "}
              <code style={{ fontSize: 12 }}>analyze why the latest Railway deployment failed</code>
            </p>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
              {events.slice(0, 25).map((ev, i) => (
                <li key={`${ev.plan_id}-${i}`} style={cardStyle}>
                  <div style={{ color: mcColors.text }}>{ev.goal || ev.plan_id}</div>
                  <div style={{ color: mcColors.textDim, fontSize: 12, marginTop: 4 }}>
                    {ev.status} · {formatTs(ev.at)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {view === "coordination-graph" && (
        <div style={{ marginTop: 16, fontFamily: "monospace", fontSize: 12, color: mcColors.textMuted, lineHeight: 1.7 }}>
          {(coordPayload?.graph?.nodes ?? []).length > 0 ? (
            coordPayload?.graph?.nodes?.map((node) => {
              const color = SEVERITY_COLOR[node.type === "planner" ? "neutral" : "low"] ?? mcColors.textMuted;
              return (
                <div key={node.id} style={{ paddingLeft: 16, borderLeft: `2px solid ${color}`, marginBottom: 8 }}>
                  <div style={{ color: mcColors.text }}>
                    {node.type === "planner" ? "Orchestration Planner" : node.label}
                    {node.status ? ` · ${node.status}` : ""}
                  </div>
                </div>
              );
            })
          ) : (
            <>
              <div style={{ color: mcColors.text, marginBottom: 8 }}>Orchestration Planner</div>
              {agents.slice(0, 6).map((a) => (
                <div key={a.agent_id} style={{ paddingLeft: 16, borderLeft: `2px solid ${mcColors.textMuted}`, marginBottom: 8 }}>
                  <div style={{ color: mcColors.text }}>├── {a.agent_id}</div>
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {view === "operational-replay" && (
        <div style={{ marginTop: 16 }}>
          {(coordPayload?.graph?.replay ?? []).length > 0 ? (
            <ol style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: mcColors.textMuted }}>
              {coordPayload?.graph?.replay?.map((step) => (
                <li key={step.step} style={{ marginBottom: 8 }}>
                  <strong style={{ color: mcColors.text }}>{step.step}</strong> → {step.label}
                </li>
              ))}
            </ol>
          ) : (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              Run a multi-agent coordination prompt to populate replay timeline.
            </p>
          )}
        </div>
      )}

      {view === "evidence-graph" && (
        <div style={{ marginTop: 16, fontFamily: "monospace", fontSize: 12 }}>
          {(coordPayload?.graph?.edges ?? []).filter((e) => e.kind === "evidence").length > 0 ? (
            coordPayload?.graph?.edges
              ?.filter((e) => e.kind === "evidence")
              .map((edge, i) => (
                <div key={`${edge.from}-${edge.to}-${i}`} style={{ ...cardStyle, fontSize: 12 }}>
                  {edge.from} ↔ {edge.to}
                  {edge.label ? ` · ${edge.label}` : ""}
                </div>
              ))
          ) : (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              Evidence graph edges appear after correlation engine runs during deployment analysis.
            </p>
          )}
        </div>
      )}

      {view === "operational-intelligence" && (
        <div style={{ marginTop: 16, fontSize: 13 }}>
          {coordPayload?.merged ? (
            <>
              {coordPayload.merged.deployment_intelligence?.latest_deployment?.id ? (
                <div style={cardStyle}>
                  <div style={{ fontWeight: 600, color: mcColors.text }}>Deployment timeline</div>
                  <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                    Latest: {coordPayload.merged.deployment_intelligence.latest_deployment.id} ·{" "}
                    {coordPayload.merged.deployment_intelligence.latest_deployment.state}
                  </div>
                </div>
              ) : null}
              {(coordPayload.merged.correlation?.temporal?.length ?? 0) > 0 ||
              (coordPayload.merged.correlation?.operational?.length ?? 0) > 0 ? (
                <div style={cardStyle}>
                  <div style={{ fontWeight: 600, color: mcColors.text }}>Correlations</div>
                  {[
                    ...(coordPayload.merged.correlation?.temporal ?? []),
                    ...(coordPayload.merged.correlation?.structural ?? []),
                    ...(coordPayload.merged.correlation?.operational ?? []),
                  ].map((row, i) => (
                    <div key={i} style={{ color: mcColors.textMuted, marginTop: 4 }}>
                      {row.detail}
                    </div>
                  ))}
                </div>
              ) : null}
              {coordPayload.merged.confidence ? (
                <div style={cardStyle}>
                  <div style={{ fontWeight: 600, color: mcColors.text }}>
                    Confidence: {coordPayload.merged.confidence.level}
                  </div>
                  {(coordPayload.merged.confidence.gaps ?? []).map((g, i) => (
                    <div key={i} style={{ color: mcColors.amber, marginTop: 4, fontSize: 12 }}>
                      Gap: {g}
                    </div>
                  ))}
                </div>
              ) : null}
              {(coordPayload.merged.recurring_patterns ?? []).map((p, i) => (
                <div key={i} style={{ ...cardStyle, color: mcColors.textMuted }}>
                  {p}
                </div>
              ))}
            </>
          ) : (
            <p style={{ color: mcColors.textMuted }}>No operational intelligence yet — run a deployment or architecture analysis prompt.</p>
          )}
        </div>
      )}

      {view === "engineering-proposals" && (
        <div style={{ marginTop: 16 }}>
          {proposalArtifacts.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              No PR proposals yet. Try:{" "}
              <code style={{ fontSize: 12 }}>prepare a PR proposal for dependency modernization</code>
            </p>
          ) : (
            proposalArtifacts.slice(0, 10).map((art) => (
              <div key={art.artifact_id} style={cardStyle}>
                <div style={{ fontWeight: 600, color: mcColors.text }}>{art.summary || "PR proposal"}</div>
                <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
                  {art.artifact_id} · {formatTs(art.created_at)}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {view === "evidence-merge" && (
        <div style={{ marginTop: 16 }}>
          {confidenceArtifacts.length > 0 ? (
            <div style={{ ...cardStyle, fontSize: 12 }}>
              <div style={{ fontWeight: 600, color: mcColors.text, marginBottom: 4 }}>Latest confidence summary</div>
              {confidenceArtifacts.slice(0, 2).map((art) => (
                <div key={art.artifact_id} style={{ color: mcColors.textMuted, marginTop: 4 }}>
                  {art.summary || art.artifact_id}
                </div>
              ))}
            </div>
          ) : null}
          {coordArtifacts.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No merged evidence yet.</p>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
              {coordArtifacts.slice(0, 10).map((art) => (
                <li key={art.artifact_id} style={cardStyle}>
                  <div>
                    {art.artifact_type} · {art.summary || art.artifact_id}
                  </div>
                  <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
                    {art.plan_id || "—"} · {formatTs(art.created_at)}
                  </div>
                </li>
              ))}
            </ul>
          )}
          {failures.length > 0 && (
            <p style={{ color: mcColors.amber, fontSize: 12, marginTop: 12 }}>
              {failures.length} isolated agent failure(s) — successful evidence preserved.
            </p>
          )}
        </div>
      )}

      {view === "agent-evidence" && (
        <div style={{ marginTop: 16 }}>
          {deepEvidence.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              No deep evidence artifacts yet. Run a multi-agent prompt to populate provider, browser, and engineering evidence.
            </p>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 13 }}>
              {deepEvidence.slice(0, 30).map((art) => (
                <li key={art.artifact_id} style={cardStyle}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
                    <span style={{ color: mcColors.text }}>{art.artifact_type.replace(/_/g, " ")}</span>
                    <code style={{ fontSize: 10, color: mcColors.textDim }}>{art.artifact_id}</code>
                  </div>
                  <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>{art.summary || "—"}</div>
                  <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
                    {art.agent_id || "coordination"} · {formatTs(art.created_at)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
