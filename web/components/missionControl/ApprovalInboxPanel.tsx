"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import {
  executeMissionControlApproval,
  executeMissionControlMutationApproval,
  executeMissionControlOperationalDeploymentApproval,
  executeMissionControlServeApproval,
  executeMissionControlTerminalApproval,
  fetchMissionControlActionSafetyReview,
  fetchMissionControlApprovalAudit,
  rejectMissionControlOperationalDeploymentApproval,
  type ApprovalAuditRecord,
} from "@/lib/missionControl/missionControlApprovalExecutionApi";
import {
  fetchMissionControlApprovalInbox,
  operationalDeploymentApprovalUiState,
  type ApprovalInboxGroup,
  type ApprovalInboxItem,
  type ApprovalInboxResponse,
} from "@/lib/missionControl/missionControlApprovalInboxApi";
import { laneDisplayTitle } from "@/lib/missionControl/crossLaneLaneNavigation";
import { attachJobToChatSession, trackJobId } from "@/lib/chat/jobLifecycleBridge";
import { removeThreadJob } from "@/lib/chat/chatThreads";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { buildOperatorContext, useOperatorSession } from "@/lib/missionControl/operatorSession";
import { ReplayDeepLinkButton } from "@/components/missionControl/ReplayDeepLinkButton";
import { buildAuditLinkRef, type ReplayDeepLinkTarget } from "@/lib/missionControl/missionControlReplayDeepLink";
import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";

type Props = {
  sessionId?: string;
  operatorMode?: MissionControlMode;
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
};

type LoadState = "idle" | "loading" | "loaded" | "error";

export function ApprovalInboxPanel({
  sessionId: sessionIdProp,
  operatorMode = "operator",
  onOpenReplayDeepLink,
}: Props) {
  const { context: operatorContext, hydrated } = useOperatorSession(sessionIdProp);
  const sessionId = operatorContext?.sessionId ?? sessionIdProp ?? "default";
  const operatorCtx = operatorContext ?? buildOperatorContext(sessionId, operatorMode);

  const [inbox, setInbox] = useState<ApprovalInboxResponse | null>(null);
  const [loadState, setLoadState] = useState<LoadState>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [audits, setAudits] = useState<ApprovalAuditRecord[]>([]);
  const [safetyOk, setSafetyOk] = useState<boolean | null>(null);

  const load = useCallback(async () => {
    if (!hydrated) return;
    try {
      setLoadState("loading");
      setErrorMessage(null);
      const [inboxRes, auditRes, safetyRes] = await Promise.all([
        fetchMissionControlApprovalInbox(sessionId),
        fetchMissionControlApprovalAudit(sessionId),
        fetchMissionControlActionSafetyReview(),
      ]);
      setInbox(inboxRes);
      setAudits(auditRes.audits ?? []);
      setSafetyOk(safetyRes.ok);
      setLoadState("loaded");
    } catch (e) {
      setErrorMessage(e instanceof Error ? e.message : "Failed to load approval inbox");
      setInbox(null);
      setAudits([]);
      setLoadState("error");
    }
  }, [sessionId, hydrated]);

  useEffect(() => {
    void load();
  }, [load]);

  const total = inbox?.summary?.total_pending ?? 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <section style={mcPanelSectionStyle}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
          <div>
            <h2 style={{ margin: "0 0 6px", fontSize: 20, fontWeight: 600 }}>Approval inbox</h2>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted, maxWidth: 640 }}>
              What needs your decision right now. Eligible items can be approved via governed chat routing — the UI injects
              exact phrases; it never bypasses lane contracts or performs direct mutations.
            </p>
          </div>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexShrink: 0 }}>
            <GovernedBadge />
            <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()} disabled={loadState === "loading"}>
              Refresh
            </button>
          </div>
        </div>

        <OperatorStrip context={operatorCtx} total={total} safetyOk={safetyOk} />

        {loadState === "loading" && !inbox ? (
          <p style={{ margin: "14px 0 0", fontSize: 13, color: mcColors.textMuted }}>Loading pending approvals…</p>
        ) : null}

        {loadState === "error" && errorMessage ? (
          <div style={{ marginTop: 14, padding: 12, borderRadius: 8, border: `1px solid ${mcColors.red}`, background: "rgba(239,68,68,0.08)" }}>
            <p style={{ margin: "0 0 8px", color: mcColors.red, fontSize: 13 }}>{errorMessage}</p>
            <button type="button" style={mcButtonSecondaryStyle} onClick={() => void load()}>
              Retry
            </button>
          </div>
        ) : null}

        {loadState === "loaded" && inbox && total === 0 ? (
          <div style={{ marginTop: 14, padding: 14, borderRadius: 10, border: `1px solid ${mcColors.border}`, background: "rgba(0,0,0,0.2)" }}>
            <p style={{ margin: 0, fontSize: 13, color: mcColors.green }}>No pending approval gates for session {sessionId}.</p>
            <p style={{ margin: "8px 0 0", fontSize: 12, color: mcColors.textMuted }}>
              When a governed gate requires an exact phrase, it will appear here grouped by lane and severity.
            </p>
          </div>
        ) : null}

        {loadState === "loaded" && inbox && total > 0 ? (
          <SeveritySummary bySeverity={inbox.summary.by_severity} />
        ) : null}
      </section>

      {loadState === "loaded" && inbox?.groups.map((group) => (
        <LaneGroup
          key={group.lane}
          group={group}
          sessionId={sessionId}
          expandedId={expandedId}
          onToggle={(id) => setExpandedId((cur) => (cur === id ? null : id))}
          onExecuted={() => void load()}
        />
      ))}

      {loadState === "loaded" ? <ApprovalAuditHistory audits={audits} /> : null}
    </div>
  );
}

function OperatorStrip({
  context,
  total,
  safetyOk,
}: {
  context: ReturnType<typeof buildOperatorContext>;
  total: number;
  safetyOk: boolean | null;
}) {
  return (
    <div
      style={{
        marginTop: 12,
        padding: "10px 12px",
        borderRadius: 8,
        border: `1px solid ${mcColors.borderSubtle}`,
        fontSize: 12,
        display: "flex",
        flexWrap: "wrap",
        gap: 16,
      }}
    >
      <span>
        Session: <code style={{ color: mcColors.cyan }}>{context.sessionId}</code>
      </span>
      <span>Mode: {context.operatorMode}</span>
      <span style={{ color: total > 0 ? mcColors.amber : mcColors.green }}>Pending: {total}</span>
      {safetyOk != null ? (
        <span style={{ color: safetyOk ? mcColors.green : mcColors.red }}>
          Safety review: {safetyOk ? "no direct provider APIs in UI path" : "FAILED"}
        </span>
      ) : null}
    </div>
  );
}

function ApprovalAuditHistory({
  audits,
  onOpenReplayDeepLink,
}: {
  audits: ApprovalAuditRecord[];
  onOpenReplayDeepLink?: (target: ReplayDeepLinkTarget) => void;
}) {
  if (!audits.length) {
    return (
      <section style={mcPanelSectionStyle}>
        <h3 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>UI approval audit</h3>
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>No UI-originated approval attempts recorded for this session yet.</p>
      </section>
    );
  }
  return (
    <section style={mcPanelSectionStyle}>
      <h3 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>UI approval audit</h3>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>
        Execution history from Mission Control — route, intent, gate cleared, and failure reasons.
      </p>
      <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12, maxHeight: 320, overflowY: "auto" }}>
        {audits.map((a) => (
          <li
            key={a.approval_id}
            style={{
              marginBottom: 8,
              padding: 10,
              borderRadius: 8,
              border: `1px solid ${mcColors.border}`,
              background: "rgba(0,0,0,0.2)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", gap: 8 }}>
              <span style={{ fontWeight: 600, color: outcomeColor(a.outcome) }}>{a.outcome ?? "—"}</span>
              <span style={{ color: mcColors.textDim }}>{a.recorded_at ?? ""}</span>
            </div>
            <div style={{ marginTop: 4 }}>
              {a.gate_id} · {a.inbox_id}
            </div>
            <div style={{ marginTop: 4, color: mcColors.textMuted }}>
              Route: {a.route_id || "—"} · Intent: {a.chat_intent || "—"}
            </div>
            <div style={{ marginTop: 4 }}>
              Gate cleared: {a.gate_satisfied ? "yes" : "no"} · Direct provider mutation:{" "}
              {a.direct_provider_mutation ? "yes" : "no"}
            </div>
            {a.failure_reason || (a.blockers && a.blockers.length) ? (
              <div style={{ marginTop: 4, color: mcColors.amber }}>
                {a.failure_reason || a.blockers?.join(", ")}
              </div>
            ) : null}
            {onOpenReplayDeepLink && a.approval_id ? (
              <ReplayDeepLinkButton
                onClick={() => onOpenReplayDeepLink({ linkRef: buildAuditLinkRef(a) })}
              />
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

function outcomeColor(outcome?: string): string {
  if (outcome === "success" || outcome === "gate_already_cleared" || outcome === "replay_protected") {
    return mcColors.green;
  }
  if (outcome === "failed") return mcColors.red;
  return mcColors.textMuted;
}

function SeveritySummary({ bySeverity }: { bySeverity: Record<string, number> }) {
  return (
    <div style={{ marginTop: 12, display: "flex", gap: 10, flexWrap: "wrap" }}>
      {Object.entries(bySeverity).map(([sev, count]) => (
        <span
          key={sev}
          style={{
            fontSize: 11,
            fontWeight: 600,
            textTransform: "uppercase",
            padding: "4px 10px",
            borderRadius: 999,
            border: `1px solid ${severityColor(sev)}`,
            color: severityColor(sev),
          }}
        >
          {sev}: {count}
        </span>
      ))}
    </div>
  );
}

function LaneGroup({
  group,
  sessionId,
  expandedId,
  onToggle,
  onExecuted,
}: {
  group: ApprovalInboxGroup;
  sessionId: string;
  expandedId: string | null;
  onToggle: (id: string) => void;
  onExecuted: () => void;
}) {
  return (
    <section style={mcPanelSectionStyle}>
      <h3 style={{ margin: "0 0 4px", fontSize: 16, fontWeight: 600 }}>
        {laneDisplayTitle(group.lane)} <span style={{ color: mcColors.textMuted, fontWeight: 400 }}>({group.count})</span>
      </h3>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: severityColor(group.severity) }}>
        Top severity: {group.severity}
      </p>
      <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
        {group.items.map((item) => (
          <ApprovalCard
            key={item.inbox_id}
            item={item}
            sessionId={sessionId}
            expanded={expandedId === item.inbox_id}
            onToggle={() => onToggle(item.inbox_id)}
            onExecuted={onExecuted}
          />
        ))}
      </ul>
    </section>
  );
}

function ApprovalCard({
  item,
  sessionId,
  expanded,
  onToggle,
  onExecuted,
}: {
  item: ApprovalInboxItem;
  sessionId: string;
  expanded: boolean;
  onToggle: () => void;
  onExecuted: () => void;
}) {
  return (
    <li style={{ marginBottom: 10 }}>
      <div
        style={{
          width: "100%",
          padding: "12px 14px",
          borderRadius: 10,
          border: `1px solid ${expanded ? mcColors.cyan : mcColors.border}`,
          background: expanded ? "rgba(34,211,238,0.06)" : "rgba(0,0,0,0.22)",
        }}
      >
        <button
          type="button"
          data-tour="approval-item"
          onClick={onToggle}
          style={{
            width: "100%",
            textAlign: "left",
            border: "none",
            background: "transparent",
            color: "inherit",
            cursor: "pointer",
            padding: 0,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "flex-start" }}>
            <div>
              <span style={{ fontSize: 10, fontWeight: 700, color: severityColor(item.severity), textTransform: "uppercase" }}>
                {item.severity} · {item.risk_tier}
              </span>
              <div style={{ marginTop: 4, fontWeight: 600, fontSize: 14 }}>{item.title}</div>
              <div style={{ marginTop: 4, fontSize: 12, color: mcColors.textMuted }}>{item.gate_id}</div>
            </div>
            <span style={{ fontSize: 11, color: mcColors.textDim }}>{expanded ? "▲" : "▼"}</span>
          </div>
        </button>
        {expanded ? <ApprovalDetail item={item} sessionId={sessionId} onExecuted={onExecuted} /> : null}
      </div>
    </li>
  );
}

function ApprovalDetail({
  item,
  sessionId,
  onExecuted,
}: {
  item: ApprovalInboxItem;
  sessionId: string;
  onExecuted: () => void;
}) {
  const [executing, setExecuting] = useState(false);
  const [execError, setExecError] = useState<string | null>(null);
  const [execResult, setExecResult] = useState<string | null>(null);
  const deploymentUi = operationalDeploymentApprovalUiState(item);

  const handleApprove = async () => {
    try {
      setExecuting(true);
      setExecError(null);
      setExecResult(null);
      if (item.terminal_execution_enabled) {
        const res = await executeMissionControlTerminalApproval(item.inbox_id, sessionId);
        if (res.ok) {
          const keys = (res.subagent_session_keys ?? []).join(", ") || "none";
          setExecResult(
            `Terminal executed (${res.execution_status}) · audit ${res.audit_id}. ` +
              `Output forwarded to: ${keys}.`,
          );
        } else {
          setExecResult(res.detail || res.blockers?.join(", ") || "Execution failed.");
        }
        if (res.ok) onExecuted();
        return;
      }
      if (item.serve_execution_enabled) {
        const res = await executeMissionControlServeApproval(item.inbox_id, sessionId);
        if (res.ok) {
          setExecResult(
            res.execution_status === "already_served"
              ? `Already served — ${res.model_id} on ${res.endpoint}. Pick it in the chat model dropdown.`
              : `Serving ${res.model_id} on ${res.endpoint} · audit ${res.audit_id}. ` +
                `It now appears in the chat model picker.`,
          );
        } else {
          setExecResult(res.detail || res.blockers?.join(", ") || "Serve execution failed.");
        }
        if (res.ok) onExecuted();
        return;
      }
      if (item.mutation_inbox_execution_enabled) {
        const res = await executeMissionControlMutationApproval(item.inbox_id, sessionId);
        if (res.replay_protected) {
          setExecResult(`Replay protected (${res.audit_id}).`);
        } else if (res.ok) {
          if (res.execution_job_id) trackJobId(res.execution_job_id);
          setExecResult(
            `Mutation approved — execution job \`${res.execution_job_id || "enqueued"}\` · audit ${res.audit_id}. ` +
              `Watch chat for execution progress.`,
          );
        } else {
          setExecResult(res.detail || res.blockers?.join(", ") || "Mutation approval failed.");
        }
        if (res.ok) onExecuted();
        return;
      }
      if (item.deployment_inbox_execution_enabled || deploymentUi.showsApproveButton) {
        const res = await executeMissionControlOperationalDeploymentApproval(item.inbox_id, sessionId);
        if (res.replay_protected) {
          setExecResult(`Replay protected (${res.audit_id}).`);
        } else if (res.ok) {
          if (res.orchestration_job_id) {
            attachJobToChatSession(sessionId, res.orchestration_job_id);
            if (res.job_id && res.job_id !== res.orchestration_job_id) {
              removeThreadJob(res.job_id);
            }
          } else if (res.job_id) {
            attachJobToChatSession(sessionId, res.job_id);
          }
          setExecResult(
            `Deployment approved via governed route · audit ${res.audit_id}. ` +
              (res.orchestration_job_id ? `Orchestration job \`${res.orchestration_job_id}\`.` : ""),
          );
        } else {
          const parts = [res.detail, res.reply, res.blockers?.join(", ")].filter(Boolean);
          setExecResult(parts.join("\n\n") || "Deployment approval failed.");
        }
        if (res.ok) onExecuted();
        return;
      }
      const res = await executeMissionControlApproval(item.inbox_id, sessionId);
      if (res.replay_protected) {
        setExecResult(`Replay protected (${res.audit_id}).`);
      } else if (res.ok) {
        setExecResult(`Approved via chat — ${res.outcome} (${res.audit_id}).`);
      } else {
        const parts = [res.detail, res.reply, res.blockers?.join(", ")].filter(Boolean);
        setExecResult(parts.join("\n\n") || "Gate not satisfied.");
      }
      if (res.ok) onExecuted();
    } catch (e) {
      setExecError(e instanceof Error ? e.message : "Approval execution failed");
    } finally {
      setExecuting(false);
    }
  };

  const handleReject = async () => {
    if (!deploymentUi.showsApproveButton) return;
    try {
      setExecuting(true);
      setExecError(null);
      setExecResult(null);
      const res = await rejectMissionControlOperationalDeploymentApproval(item.inbox_id, sessionId);
      if (res.ok) {
        setExecResult(res.detail || "Deployment approval rejected.");
        onExecuted();
      } else {
        setExecResult(res.detail || res.blockers?.join(", ") || "Reject failed.");
      }
    } catch (e) {
      setExecError(e instanceof Error ? e.message : "Reject failed");
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div style={{ marginTop: 12, paddingTop: 12, borderTop: `1px solid ${mcColors.borderSubtle}`, fontSize: 12 }}>
      <DetailBlock title={item.deployment_inbox_execution_enabled || deploymentUi.showsApproveButton ? "Or approve via chat" : "Required phrase(s) — use in chat"}>
        {item.copy_phrase_text ? (
          <button
            type="button"
            style={{ ...mcButtonSecondaryStyle, marginBottom: 8, fontSize: 11 }}
            onClick={() => void navigator.clipboard.writeText(item.copy_phrase_text ?? "")}
          >
            Copy phrase for chat
          </button>
        ) : null}
        {item.required_phrases.map((phrase) => (
          <blockquote
            key={phrase}
            style={{
              margin: "6px 0",
              padding: "8px 10px",
              borderLeft: `3px solid ${mcColors.cyan}`,
              background: "rgba(0,0,0,0.25)",
              color: mcColors.text,
              fontStyle: "italic",
            }}
          >
            {phrase}
          </blockquote>
        ))}
      </DetailBlock>

      <DetailBlock title="Blast radius">
        <BlastRadius blast={item.blast_radius} />
      </DetailBlock>

      <DetailBlock title="Approval unlocks">
        <TagList items={item.unlocks} color={mcColors.green} />
      </DetailBlock>

      <DetailBlock title="Remains forbidden">
        <TagList items={item.remains_forbidden} color={mcColors.red} />
      </DetailBlock>

      <div style={{ marginTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
        {item.terminal_execution_enabled ? (
          <>
            <button
              type="button"
              style={{
                ...mcButtonSecondaryStyle,
                borderColor: mcColors.green,
                color: mcColors.green,
                alignSelf: "flex-start",
              }}
              disabled={executing}
              onClick={() => void handleApprove()}
            >
              {executing ? "Executing…" : "Approve & execute terminal"}
            </button>
            <p style={{ margin: 0, fontSize: 11, color: mcColors.textMuted }}>
              Runs the allowlisted command after approval; output is sent to linked subagent sessions via agent_send.
            </p>
          </>
        ) : item.serve_execution_enabled ? (
          <>
            <button
              type="button"
              style={{
                ...mcButtonSecondaryStyle,
                borderColor: mcColors.green,
                color: mcColors.green,
                alignSelf: "flex-start",
              }}
              disabled={executing}
              onClick={() => void handleApprove()}
            >
              {executing ? "Serving…" : "Approve & serve locally"}
            </button>
            <p style={{ margin: 0, fontSize: 11, color: mcColors.textMuted }}>
              Verifies the local runtime + model are present (no auto-download), then registers the model in the chat picker.
            </p>
          </>
        ) : item.mutation_inbox_execution_enabled ? (
          <>
            <button
              type="button"
              style={{
                ...mcButtonSecondaryStyle,
                borderColor: mcColors.green,
                color: mcColors.green,
                alignSelf: "flex-start",
              }}
              disabled={executing}
              onClick={() => void handleApprove()}
            >
              {executing ? "Approving…" : "Approve governed mutation"}
            </button>
            <p style={{ margin: 0, fontSize: 11, color: mcColors.textMuted }}>
              Enqueues governed mutation execution after preflight review — same path as Mission Control jobs approval.
            </p>
          </>
        ) : item.deployment_inbox_execution_enabled || deploymentUi.showsApproveButton ? (
          <>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button
                type="button"
                style={{
                  ...mcButtonSecondaryStyle,
                  borderColor: mcColors.green,
                  color: mcColors.green,
                }}
                disabled={executing || deploymentUi.approveDisabled}
                onClick={() => void handleApprove()}
              >
                {executing ? "Approving…" : "Approve deployment"}
              </button>
              <button
                type="button"
                style={{
                  ...mcButtonSecondaryStyle,
                  borderColor: mcColors.red,
                  color: mcColors.red,
                }}
                disabled={executing}
                onClick={() => void handleReject()}
              >
                Reject
              </button>
            </div>
            {deploymentUi.approveDisabled ? (
              <p style={{ margin: 0, fontSize: 11, color: mcColors.amber }}>{deploymentUi.disabledHint}</p>
            ) : (
              <p style={{ margin: 0, fontSize: 11, color: mcColors.textMuted }}>
                Routes approval through the same governed chat path as typing the approve phrase.
              </p>
            )}
          </>
        ) : item.ui_approval_eligible ? (
          <>
            <button
              type="button"
              style={{
                ...mcButtonSecondaryStyle,
                borderColor: mcColors.green,
                color: mcColors.green,
                alignSelf: "flex-start",
              }}
              disabled={executing}
              onClick={() => void handleApprove()}
            >
              {executing ? "Routing to chat…" : "Approve (governed chat)"}
            </button>
            <p style={{ margin: 0, fontSize: 11, color: mcColors.textMuted }}>
              Submits the exact phrase(s) through the same chat governance route — not a direct mutation.
            </p>
          </>
        ) : (
          <p style={{ margin: 0, fontSize: 11, color: mcColors.amber }}>
            {item.execution_mode === "prerequisites_required"
              ? "Complete prerequisite chat steps before this gate can be approved from the inbox."
              : item.execution_mode === "view_only_chat_required"
                ? "Chat required: this gate couples approval to a governed mutation step (branch push / PR open) or is outside UI scope."
                : "Chat required: use chat with the phrase(s) above."}
          </p>
        )}
        {execError ? <p style={{ margin: 0, color: mcColors.red, fontSize: 12 }}>{execError}</p> : null}
        {execResult ? <p style={{ margin: 0, color: mcColors.green, fontSize: 12 }}>{execResult}</p> : null}
      </div>

      <p style={{ margin: "10px 0 0", color: mcColors.textDim, fontSize: 11 }}>
        Surface: {item.approval_surface} · Mode: {item.execution_mode}
      </p>
    </div>
  );
}

function BlastRadius({ blast }: { blast: Record<string, unknown> }) {
  const entries = Object.entries(blast).filter(([, v]) => v != null && v !== "");
  if (!entries.length) return <p style={{ margin: 0, color: mcColors.textMuted }}>—</p>;
  return (
    <ul style={{ margin: 0, paddingLeft: 16 }}>
      {entries.map(([k, v]) => (
        <li key={k} style={{ marginBottom: 4 }}>
          <span style={{ color: mcColors.textMuted }}>{k.replace(/_/g, " ")}: </span>
          <span>{typeof v === "object" ? JSON.stringify(v) : String(v)}</span>
        </li>
      ))}
    </ul>
  );
}

function DetailBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ fontWeight: 600, color: mcColors.cyan, marginBottom: 4 }}>{title}</div>
      {children}
    </div>
  );
}

function TagList({ items, color }: { items: string[]; color: string }) {
  if (!items.length) return <p style={{ margin: 0, color: mcColors.textMuted }}>—</p>;
  return (
    <ul style={{ margin: 0, paddingLeft: 16, color }}>
      {items.map((t) => (
        <li key={t} style={{ marginBottom: 2 }}>
          {t}
        </li>
      ))}
    </ul>
  );
}

function severityColor(severity: string): string {
  if (severity === "critical") return mcColors.red;
  if (severity === "high") return mcColors.amber;
  if (severity === "medium") return mcColors.cyan;
  return mcColors.textMuted;
}

function GovernedBadge() {
  return (
    <span
      style={{
        fontSize: 11,
        fontWeight: 600,
        letterSpacing: "0.04em",
        textTransform: "uppercase",
        padding: "4px 10px",
        borderRadius: 999,
        border: `1px solid ${mcColors.green}`,
        color: mcColors.green,
        background: "rgba(34,197,94,0.08)",
      }}
    >
      Chat-governed
    </span>
  );
}
