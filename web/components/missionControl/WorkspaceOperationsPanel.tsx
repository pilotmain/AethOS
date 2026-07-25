"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  fetchWorkspaceAudit,
  fetchWorkspaceMemory,
  fetchWorkspaceProcesses,
  fetchWorkspaceRuntimeArtifacts,
  fetchWorkspaceRuntimeStatus,
  fetchWorkspaceSessions,
  fetchWorkspaceWindows,
  runWorkspaceDiagnostics,
  terminalExecute,
  terminalPreflight,
  type TerminalPreflight,
  type WorkspaceRuntimeArtifact,
} from "@/lib/missionControl/workspaceApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const titles: Record<string, string> = {
  "workspace-active": "Active Workspaces",
  "workspace-desktop": "Desktop Awareness",
  "workspace-terminal": "Terminal Sessions",
  "workspace-evidence": "Workspace Evidence",
  "workspace-replay": "Runtime Replay",
  "workspace-files": "File Intelligence",
  "workspace-sandbox": "Sandbox Sessions",
  "workspace-memory": "Workspace Memory",
};

export function WorkspaceOperationsPanel({ view }: Props) {
  const [status, setStatus] = useState<Awaited<ReturnType<typeof fetchWorkspaceRuntimeStatus>> | null>(null);
  const [windows, setWindows] = useState<unknown>(null);
  const [processes, setProcesses] = useState<unknown>(null);
  const [sessions, setSessions] = useState<TerminalPreflight[]>([]);
  const [artifacts, setArtifacts] = useState<WorkspaceRuntimeArtifact[]>([]);
  const [audit, setAudit] = useState<unknown[]>([]);
  const [memory, setMemory] = useState<Record<string, unknown> | null>(null);
  const [command, setCommand] = useState("git status");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [lastPreflight, setLastPreflight] = useState<TerminalPreflight | null>(null);
  const [lastOutput, setLastOutput] = useState<string>("");

  const load = useCallback(async () => {
    try {
      setError(null);
      const st = await fetchWorkspaceRuntimeStatus("aethos");
      setStatus(st);
      if (view === "workspace-desktop") {
        setWindows((await fetchWorkspaceWindows()).windows);
        setProcesses((await fetchWorkspaceProcesses()).processes);
      }
      if (view === "workspace-terminal" || view === "workspace-sandbox") {
        const sess = await fetchWorkspaceSessions();
        setSessions(sess.terminal_preflights ?? []);
      }
      if (view === "workspace-evidence" || view === "workspace-replay" || view === "workspace-files") {
        setArtifacts((await fetchWorkspaceRuntimeArtifacts()).artifacts ?? []);
      }
      if (view === "workspace-replay") setAudit((await fetchWorkspaceAudit()).audit ?? []);
      if (view === "workspace-memory") setMemory((await fetchWorkspaceMemory()).memory ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workspace runtime");
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  const onPreflight = async () => {
    setBusy(true);
    try {
      const res = await terminalPreflight(command);
      setLastPreflight(res.preflight ?? null);
      if (res.preflight?.status === "policy_denied") {
        setError(res.preflight.policy?.reason ?? "Policy denied");
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Preflight failed");
    } finally {
      setBusy(false);
    }
  };

  const onExecute = async () => {
    if (!lastPreflight?.preflight_id) return;
    setBusy(true);
    try {
      const res = await terminalExecute(lastPreflight.preflight_id);
      setLastOutput(res.execution?.output ?? res.execution?.status ?? "");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Execution failed");
    } finally {
      setBusy(false);
    }
  };

  const onDiagnostics = async () => {
    setBusy(true);
    try {
      await runWorkspaceDiagnostics("Analyze failing tests in AethOS");
      await load();
    } finally {
      setBusy(false);
    }
  };

  const replayArtifacts = artifacts.filter((a) => a.artifact_type?.includes("replay"));

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{titles[view] ?? "Workspace Operations"}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Governed workspace control — approval, sandboxing, audit. No unrestricted shell.
          </p>
        </div>
        <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {view === "workspace-active" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>Runtime status</div>
            <div style={{ color: mcColors.textMuted, marginTop: 4 }}>
              Path: {status?.status?.path ?? "—"} · Registered: {String(status?.status?.registered ?? false)}
            </div>
            <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>
              Workspaces: {(status?.runtime?.workspaces as unknown[])?.length ?? 0} · Auto-exec blocked
            </div>
          </div>
          <button type="button" disabled={busy} onClick={onDiagnostics} style={{ ...mcButtonSecondaryStyle, marginTop: 8 }}>
            Run diagnostics
          </button>
        </div>
      )}

      {view === "workspace-desktop" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>Active application</div>
            <pre style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 8, whiteSpace: "pre-wrap" }}>
              {JSON.stringify(windows, null, 2)}
            </pre>
          </div>
          <div style={cardStyle}>
            <div style={{ fontWeight: 600 }}>Process summary</div>
            <pre style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 8, whiteSpace: "pre-wrap" }}>
              {JSON.stringify(processes, null, 2)}
            </pre>
          </div>
          <p style={{ fontSize: 11, color: mcColors.textDim }}>Governed observation only — no stealth surveillance.</p>
        </div>
      )}

      {view === "workspace-terminal" && (
        <div style={{ marginTop: 16 }}>
          <div style={cardStyle}>
            <label style={{ display: "block", fontSize: 12, color: mcColors.textDim, marginBottom: 6 }}>Governed command</label>
            <input
              value={command}
              onChange={(e) => setCommand(e.target.value)}
              style={{ width: "100%", padding: "8px 10px", borderRadius: 8, border: `1px solid ${mcColors.borderSubtle}`, background: "rgba(0,0,0,0.3)", color: mcColors.text }}
            />
            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <button type="button" disabled={busy} onClick={onPreflight} style={mcButtonSecondaryStyle}>
                Preflight
              </button>
              <button type="button" disabled={busy || !lastPreflight?.preflight_id || lastPreflight.status === "policy_denied"} onClick={onExecute} style={mcButtonSecondaryStyle}>
                Approve &amp; execute
              </button>
            </div>
            {lastPreflight ? (
              <div style={{ marginTop: 10, fontSize: 12, color: mcColors.textMuted }}>
                Status: {lastPreflight.status} · Tier: {lastPreflight.policy?.error ? "blocked" : "allowlisted"}
              </div>
            ) : null}
            {lastOutput ? (
              <pre style={{ marginTop: 10, fontSize: 11, color: mcColors.green, whiteSpace: "pre-wrap", maxHeight: 200, overflow: "auto" }}>{lastOutput}</pre>
            ) : null}
          </div>
          {sessions.map((s) => (
            <div key={s.preflight_id} style={cardStyle}>
              <div style={{ fontWeight: 600 }}>{s.command}</div>
              <div style={{ color: mcColors.textMuted, marginTop: 4 }}>{s.status}</div>
            </div>
          ))}
        </div>
      )}

      {(view === "workspace-evidence" || view === "workspace-files") && (
        <div style={{ marginTop: 16 }}>
          {artifacts.length === 0 ? (
            <p style={{ color: mcColors.textMuted }}>No workspace artifacts yet.</p>
          ) : (
            artifacts.map((a) => (
              <div key={a.artifact_id} style={cardStyle}>
                <div style={{ fontWeight: 600 }}>{a.artifact_type}</div>
                <div style={{ color: mcColors.textMuted, marginTop: 4 }}>{a.summary}</div>
                <div style={{ fontSize: 11, color: mcColors.textDim }}>{a.artifact_id}</div>
              </div>
            ))
          )}
        </div>
      )}

      {view === "workspace-replay" && (
        <div style={{ marginTop: 16 }}>
          {replayArtifacts.map((a) => (
            <div key={a.artifact_id} style={cardStyle}>
              <div style={{ fontWeight: 600 }}>Replay — {a.artifact_id}</div>
              <div style={{ color: mcColors.textMuted, marginTop: 4 }}>{a.summary}</div>
            </div>
          ))}
          {audit.map((row, i) => (
            <div key={i} style={{ ...cardStyle, fontSize: 12 }}>
              <pre style={{ margin: 0, whiteSpace: "pre-wrap", color: mcColors.textDim }}>{JSON.stringify(row, null, 2)}</pre>
            </div>
          ))}
        </div>
      )}

      {view === "workspace-sandbox" && (
        <div style={{ marginTop: 16 }}>
          <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
            Engineering sandbox sessions appear under Governed Engineering → Sandbox Executions.
          </p>
          <p style={{ fontSize: 12, color: mcColors.textDim }}>Terminal sessions: {sessions.length}</p>
        </div>
      )}

      {view === "workspace-memory" && memory && (
        <div style={{ marginTop: 16 }}>
          <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted }}>{JSON.stringify(memory, null, 2)}</pre>
        </div>
      )}
    </section>
  );
}
