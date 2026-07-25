"use client";

import { useCallback, useEffect, useState } from "react";

import {
  approveEngineeringPreflight,
  denyEngineeringPreflight,
  fetchEngineeringState,
  fetchRealityLoop,
  type EngineeringPreflightCard,
  type EngineeringStateResponse,
  type PatchArtifact,
} from "@/lib/missionControl/engineeringApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  view: MissionControlView;
};

const cardStyle = {
  padding: "10px 12px",
  marginBottom: 8,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.18)",
  fontSize: 13,
} as const;

const severityColor = (sev?: string) => {
  if (sev === "high") return mcColors.amber;
  if (sev === "medium") return "var(--aethos-warn)";
  return mcColors.green ?? "var(--aethos-ok)";
};

function isProposalOnly(tier?: string) {
  return (tier || "").startsWith("E1");
}

function DiffBlock({ artifact }: { artifact: PatchArtifact }) {
  const diffs = artifact.unified_diffs ?? [];
  const intel = artifact.diff_intelligence;
  if (diffs.length === 0) {
    return <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No unified diffs stored for this artifact.</p>;
  }
  return (
    <div>
      {intel ? (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
          <span
            style={{
              fontSize: 11,
              padding: "2px 8px",
              borderRadius: 999,
              background: "rgba(255,255,255,0.06)",
              color: severityColor(intel.severity),
            }}
          >
            severity: {intel.severity || "low"}
          </span>
          {(intel.warnings ?? []).slice(0, 3).map((w, i) => (
            <span key={i} style={{ fontSize: 11, color: mcColors.amber }}>
              ⚠ {w}
            </span>
          ))}
        </div>
      ) : null}
      {diffs.map((d, i) => (
        <div key={i} style={{ ...cardStyle, padding: 0, overflow: "hidden" }}>
          <div
            style={{
              padding: "8px 12px",
              borderBottom: `1px solid ${mcColors.borderSubtle}`,
              fontFamily: "ui-monospace, monospace",
              fontSize: 12,
              color: mcColors.text,
            }}
          >
            {d.file}
            {d.lines_changed ? (
              <span style={{ color: mcColors.textDim, marginLeft: 8 }}>±{d.lines_changed} lines</span>
            ) : null}
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 0, maxHeight: 280, overflow: "auto" }}>
            <pre
              style={{
                margin: 0,
                padding: 10,
                fontSize: 11,
                lineHeight: 1.45,
                background: "rgba(239,68,68,0.06)",
                color: "var(--aethos-danger)",
                borderRight: `1px solid ${mcColors.borderSubtle}`,
              }}
            >
              {(d.diff || "")
                .split("\n")
                .filter((line) => line.startsWith("-") || line.startsWith("---"))
                .slice(0, 40)
                .join("\n") || "—"}
            </pre>
            <pre
              style={{
                margin: 0,
                padding: 10,
                fontSize: 11,
                lineHeight: 1.45,
                background: "rgba(34,197,94,0.06)",
                color: "var(--aethos-ok)",
              }}
            >
              {(d.diff || "")
                .split("\n")
                .filter((line) => line.startsWith("+") || line.startsWith("+++"))
                .slice(0, 40)
                .join("\n") || "—"}
            </pre>
          </div>
        </div>
      ))}
    </div>
  );
}

export function EngineeringExecutionPanel({ view }: Props) {
  const [state, setState] = useState<EngineeringStateResponse | null>(null);
  const [realityReport, setRealityReport] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [selectedArtifact, setSelectedArtifact] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const data = await fetchEngineeringState();
      setState(data);
      if (!selectedArtifact && (data.patch_artifacts ?? []).length > 0) {
        setSelectedArtifact(data.patch_artifacts![0].artifact_id ?? null);
      }
      if (view === "operational-reality") {
        const loop = await fetchRealityLoop();
        setRealityReport(loop.report || "");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load engineering state");
    }
  }, [view, selectedArtifact]);

  useEffect(() => {
    load();
  }, [load]);

  const onApprove = async (preflightId: string) => {
    setBusyId(preflightId);
    try {
      await approveEngineeringPreflight(preflightId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Approval failed");
    } finally {
      setBusyId(null);
    }
  };

  const onDeny = async (preflightId: string) => {
    setBusyId(preflightId);
    try {
      await denyEngineeringPreflight(preflightId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Deny failed");
    } finally {
      setBusyId(null);
    }
  };

  const titles: Record<string, string> = {
    "engineering-execution": "Pending Preflights",
    "sandbox-executions": "Sandbox Executions",
    "validation-center": "Validation Center",
    "diff-explorer": "Diff Explorer",
    "pr-drafts-center": "PR Drafts",
    "rollback-snapshots": "Rollback Snapshots",
    "engineering-audit": "Engineering Audit",
    "operational-reality": "Operational Reality",
  };
  const title = titles[view] ?? "Governed Engineering";

  const pending = state?.pending_preflights ?? [];
  const approved = state?.approved_preflights ?? [];
  const workspaces = state?.mutation_workspaces ?? [];
  const executions = state?.executions ?? [];
  const prDrafts = state?.pr_drafts ?? [];
  const artifacts = state?.patch_artifacts ?? [];
  const validations = state?.validations ?? [];
  const snapshots = state?.rollback_snapshots ?? [];
  const selected = artifacts.find((a) => a.artifact_id === selectedArtifact) ?? artifacts[0];

  const renderPreflightCard = (pf: EngineeringPreflightCard, showActions: boolean) => {
    const id = pf.preflight_id || "";
    const files = pf.patch_plan?.affected_files || pf.patch_proposal?.files_affected || [];
    const intel = pf.patch_proposal?.diff_intelligence;
    return (
      <div key={id} style={cardStyle}>
        <div style={{ fontWeight: 600, color: mcColors.text }}>{pf.task?.title || "Engineering preflight"}</div>
        <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
          {id} · {pf.risk_tier} · {pf.target_workspace}
        </div>
        <div style={{ color: mcColors.textMuted, marginTop: 6 }}>{pf.task?.problem_summary}</div>
        {intel ? (
          <div style={{ marginTop: 6, fontSize: 11, color: severityColor(intel.severity) }}>
            Blast radius: {intel.severity} — {(pf.patch_proposal?.blast_radius?.surfaces ?? []).join(", ") || "bounded"}
          </div>
        ) : null}
        {files.length > 0 ? (
          <div style={{ marginTop: 6, fontSize: 12, color: mcColors.textMuted }}>
            Files: {files.slice(0, 4).join(", ")}
          </div>
        ) : null}
        {pf.patch_plan?.validation_steps?.length ? (
          <div style={{ marginTop: 4, fontSize: 12, color: mcColors.textDim }}>
            Validation: {pf.patch_plan.validation_steps.slice(0, 3).join(" · ")}
          </div>
        ) : null}
        {pf.patch_plan?.rollback_strategy ? (
          <div style={{ marginTop: 4, fontSize: 11, color: mcColors.textDim }}>Rollback: {pf.patch_plan.rollback_strategy}</div>
        ) : null}
        {showActions ? (
          <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
            <button
              type="button"
              disabled={busyId === id}
              onClick={() => onApprove(id)}
              style={{ ...mcButtonSecondaryStyle, fontSize: 12 }}
            >
              {isProposalOnly(pf.risk_tier) ? "Generate governed PR draft" : "Approve governed execution"}
            </button>
            <button
              type="button"
              disabled={busyId === id}
              onClick={() => onDeny(id)}
              style={{ ...mcButtonSecondaryStyle, fontSize: 12, color: mcColors.amber }}
            >
              Deny
            </button>
          </div>
        ) : null}
      </div>
    );
  };

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{title}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Governed patch lifecycle — sandbox execution, validation, PR drafts. No auto-merge.
          </p>
        </div>
        <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {view === "engineering-execution" && (
        <div style={{ marginTop: 16 }}>
          <h3 style={{ fontSize: 14, margin: "0 0 8px" }}>Pending engineering preflights</h3>
          {pending.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
              No pending approvals. Try: <code style={{ fontSize: 12 }}>Fix the GitHub workflow rerun issue in AethOS</code>
            </p>
          ) : (
            pending.map((pf) => renderPreflightCard(pf, true))
          )}
          <h3 style={{ fontSize: 14, margin: "16px 0 8px" }}>Approved / completed</h3>
          {approved.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No approved engineering work yet.</p>
          ) : (
            approved.slice(0, 8).map((pf) => renderPreflightCard(pf, false))
          )}
        </div>
      )}

      {view === "sandbox-executions" && (
        <div style={{ marginTop: 16 }}>
          {workspaces.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Sandbox workspaces appear after E2+ execution approval.</p>
          ) : (
            workspaces.map((ws) => (
              <div key={ws.workspace_id} style={cardStyle}>
                <div style={{ fontWeight: 600 }}>{ws.branch || ws.workspace_id}</div>
                <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                  Files modified: {(ws.files_modified ?? []).length} · Validation: {ws.validation_status || "pending"}
                </div>
                <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
                  Rollback: {ws.rollback_snapshot || "—"}
                </div>
              </div>
            ))
          )}
          <h3 style={{ fontSize: 14, margin: "16px 0 8px" }}>Executions</h3>
          {executions.map((ex) => (
            <div key={ex.execution_id} style={cardStyle}>
              <div style={{ fontWeight: 600 }}>{ex.pr_draft?.title || ex.execution_id}</div>
              <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                {ex.status} {ex.branch ? `· branch ${ex.branch}` : ""}
              </div>
              {ex.merge_enabled === false ? (
                <div style={{ fontSize: 11, color: mcColors.green, marginTop: 4 }}>Auto-merge blocked</div>
              ) : null}
            </div>
          ))}
        </div>
      )}

      {view === "validation-center" && (
        <div style={{ marginTop: 16 }}>
          {validations.length === 0 && approved.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Validation runs appear after governed engineering approval.</p>
          ) : (
            (validations.length ? validations : approved.map((pf) => ({ preflight_id: pf.preflight_id, validation: pf.execution?.validation }))).map(
              (row, i) => (
                <div key={i} style={cardStyle}>
                  <div style={{ fontWeight: 600 }}>
                    Validation — {row.preflight_id || ("execution_id" in row ? row.execution_id : undefined) || "—"}
                  </div>
                  <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                    Status: {row.validation?.validation_status || "pending"}
                    {row.validation?.pass_count != null ? ` · passed ${row.validation.pass_count}` : ""}
                  </div>
                  <span
                    style={{
                      display: "inline-block",
                      marginTop: 6,
                      fontSize: 11,
                      padding: "2px 8px",
                      borderRadius: 999,
                      background: row.validation?.ok ? "rgba(34,197,94,0.15)" : "rgba(239,68,68,0.15)",
                      color: row.validation?.ok ? "var(--aethos-ok)" : "var(--aethos-danger)",
                    }}
                  >
                    {row.validation?.ok ? "passed" : row.validation?.validation_status || "pending"}
                  </span>
                </div>
              ),
            )
          )}
        </div>
      )}

      {view === "diff-explorer" && (
        <div style={{ marginTop: 16 }}>
          {artifacts.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Diff artifacts appear after governed patch execution.</p>
          ) : (
            <>
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
                {artifacts.map((a) => (
                  <button
                    key={a.artifact_id}
                    type="button"
                    onClick={() => setSelectedArtifact(a.artifact_id ?? null)}
                    style={{
                      ...mcButtonSecondaryStyle,
                      fontSize: 11,
                      borderColor: selected?.artifact_id === a.artifact_id ? mcColors.green : mcColors.borderSubtle,
                    }}
                  >
                    {a.artifact_id}
                  </button>
                ))}
              </div>
              {selected ? <DiffBlock artifact={selected} /> : null}
            </>
          )}
        </div>
      )}

      {view === "pr-drafts-center" && (
        <div style={{ marginTop: 16 }}>
          {prDrafts.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>PR drafts appear after preflight approval.</p>
          ) : (
            prDrafts.map((d, i) => (
              <div key={d.draft_id || i} style={cardStyle}>
                <div style={{ fontWeight: 600 }}>{d.title}</div>
                <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>{d.status}</div>
                <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>{d.governance_statement}</div>
                {d.body ? (
                  <pre style={{ marginTop: 8, fontSize: 11, color: mcColors.textMuted, whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>
                    {d.body.slice(0, 1200)}
                  </pre>
                ) : null}
              </div>
            ))
          )}
        </div>
      )}

      {view === "rollback-snapshots" && (
        <div style={{ marginTop: 16 }}>
          {snapshots.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Rollback snapshots are created during sandbox execution.</p>
          ) : (
            snapshots.map((s) => (
              <div key={s.snapshot_id} style={cardStyle}>
                <div style={{ fontWeight: 600 }}>{s.snapshot_id}</div>
                <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                  Branch: {s.branch} · Files: {(s.files_modified ?? []).length}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {view === "engineering-audit" && (
        <div style={{ marginTop: 16 }}>
          {executions.length === 0 ? (
            <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Audit trail populates after executions.</p>
          ) : (
            executions.map((ex) => (
              <div key={ex.execution_id} style={cardStyle}>
                <div style={{ fontWeight: 600 }}>{ex.execution_id}</div>
                <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
                  {ex.status} · preflight {ex.audit?.preflight_id || "—"}
                </div>
                <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
                  auto_merge: {String(ex.audit?.auto_merge ?? false)} · merge_enabled: {String(ex.merge_enabled ?? false)}
                </div>
              </div>
            ))
          )}
          {(state?.engineering_memory?.total_events ?? 0) > 0 ? (
            <p style={{ marginTop: 12, fontSize: 12, color: mcColors.textDim }}>
              Engineering memory events: {state?.engineering_memory?.total_events}
            </p>
          ) : null}
        </div>
      )}

      {view === "operational-reality" && (
        <div style={{ marginTop: 16 }}>
          {(state?.reality_loop?.recurring_patterns ?? []).map((p, i) => (
            <div key={i} style={cardStyle}>
              {p}
            </div>
          ))}
          {realityReport ? (
            <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>{realityReport}</pre>
          ) : null}
        </div>
      )}
    </section>
  );
}
