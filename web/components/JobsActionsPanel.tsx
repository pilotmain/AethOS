"use client";

import { useCallback, useState } from "react";

import {
  actionControlHint,
  approveAction,
  denyAction,
  normalizeActionsGrouped,
  type ActionsGrouped,
  type RuntimeActionRecord,
} from "@/lib/missionControl/actions";
import { formatMcPanelError } from "@/lib/missionControl/panelError";
import { browserActionDetail, isBrowserActionType } from "@/lib/settings/browserCapability";

type Props = {
  actions: ActionsGrouped;
  onRefresh: () => void;
};

const btnBase = {
  marginTop: 8,
  borderRadius: 8,
  padding: "6px 12px",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};

function ActionList({
  title,
  items,
  pendingControls,
  busyId,
  onApprove,
  onDeny,
}: {
  title: string;
  items: RuntimeActionRecord[];
  pendingControls?: boolean;
  busyId: string | null;
  onApprove?: (id: string) => void;
  onDeny?: (id: string) => void;
}) {
  if (items.length === 0) return null;
  return (
    <div style={{ marginBottom: 16 }}>
      <h3 style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600, color: "var(--aethos-text)" }}>{title}</h3>
      <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
        {items.map((a) => (
          <li
            key={a.id}
            style={{
              padding: 12,
              borderRadius: 12,
              border: "1px solid rgba(255,255,255,0.1)",
              background: "rgba(255,255,255,0.03)",
              fontSize: 13,
            }}
          >
            <div style={{ fontWeight: 600 }}>
              {isBrowserActionType(a.action_type) ? "Browser job proposal" : a.summary}
            </div>
            {isBrowserActionType(a.action_type) && (
              <div style={{ color: "var(--aethos-text-muted)", marginTop: 4, fontSize: 12 }}>{a.summary}</div>
            )}
            <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>
              {actionControlHint(a.status)} · {a.action_type} · <code>{a.id}</code>
            </div>
            {browserActionDetail(a) && (
              <div style={{ color: "var(--aethos-accent)", marginTop: 4, fontSize: 12 }}>{browserActionDetail(a)}</div>
            )}
            {a.result && (
              <pre
                style={{
                  marginTop: 8,
                  whiteSpace: "pre-wrap",
                  fontSize: 12,
                  color: "var(--aethos-ok)",
                }}
              >
                {a.result}
              </pre>
            )}
            {a.error && (
              <pre style={{ marginTop: 8, whiteSpace: "pre-wrap", fontSize: 12, color: "var(--aethos-danger)" }}>
                {a.error}
              </pre>
            )}
            {pendingControls && onApprove && onDeny && (
              <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button
                  type="button"
                  onClick={() => onApprove(a.id)}
                  disabled={busyId === a.id}
                  style={{
                    ...btnBase,
                    border: "1px solid rgba(34,211,238,0.35)",
                    background: "rgba(34,211,238,0.12)",
                    color: "var(--aethos-text-strong)",
                  }}
                >
                  {busyId === a.id ? "Working…" : "Approve"}
                </button>
                <button
                  type="button"
                  onClick={() => onDeny(a.id)}
                  disabled={busyId === a.id}
                  style={{
                    ...btnBase,
                    border: "1px solid rgba(248,113,113,0.35)",
                    background: "rgba(248,113,113,0.1)",
                    color: "var(--aethos-danger)",
                  }}
                >
                  Deny
                </button>
              </div>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function JobsActionsPanel({ actions, onRefresh }: Props) {
  const [busyId, setBusyId] = useState<string | null>(null);
  const [panelError, setPanelError] = useState("");

  const runControl = useCallback(
    async (id: string, fn: (actionId: string) => Promise<RuntimeActionRecord>) => {
      setBusyId(id);
      setPanelError("");
      try {
        await fn(id);
        onRefresh();
      } catch (e) {
        setPanelError(formatMcPanelError(e instanceof Error ? e.message : "Action control failed"));
      } finally {
        setBusyId(null);
      }
    },
    [onRefresh],
  );

  const grouped = normalizeActionsGrouped(actions);
  const empty =
    grouped.pending.length +
      grouped.approved.length +
      grouped.completed.length +
      grouped.failed.length +
      grouped.denied.length ===
    0;

  return (
    <div>
      <h2 style={{ margin: "0 0 8px", fontSize: 15, fontWeight: 600 }}>Runtime actions</h2>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <p style={{ margin: 0, fontSize: 13, color: "var(--aethos-text-muted)" }}>
          Proposed → approved → executed. Chat never auto-runs actions. Pending runtime actions can be{" "}
          <strong>approved</strong> or <strong>denied</strong>.
        </p>
        <button
          type="button"
          onClick={onRefresh}
          style={{
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "transparent",
            color: "var(--aethos-text-muted)",
            padding: "4px 10px",
            fontSize: 12,
            cursor: "pointer",
            flexShrink: 0,
          }}
        >
          Refresh
        </button>
      </div>

      {panelError && (
        <p style={{ color: "var(--aethos-warn)", fontSize: 13, marginBottom: 12 }} role="status">
          {panelError}
        </p>
      )}

      {empty && (
        <p style={{ color: "var(--aethos-text-muted)", fontSize: 13 }}>No actions yet. Ask in chat, e.g. “can you check Vercel CLI?”</p>
      )}

      <ActionList
        title="Pending"
        items={grouped.pending}
        pendingControls
        busyId={busyId}
        onApprove={(id) => void runControl(id, approveAction)}
        onDeny={(id) => void runControl(id, denyAction)}
      />
      <ActionList title="Approved" items={grouped.approved} busyId={null} />
      <ActionList title="Completed" items={grouped.completed} busyId={null} />
      <ActionList title="Failed" items={grouped.failed} busyId={null} />
      <ActionList title="Denied" items={grouped.denied} busyId={null} />
    </div>
  );
}
