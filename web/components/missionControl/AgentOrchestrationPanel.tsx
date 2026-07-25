"use client";

import { type ReactNode, useCallback, useEffect, useMemo, useRef, useState } from "react";

import type { AgentArtifact, AgentSpec, CoordinationEvent } from "@/lib/missionControl/agentsApi";
import { delegateAgentSpawn } from "@/lib/missionControl/agentsApi";
import {
  fetchSubagentSessions,
  pickLatestOutput,
  type SubagentSessionRow,
} from "@/lib/missionControl/subagentSessionsApi";
import {
  mcAlpha,
  mcButtonPrimaryStyle,
  mcButtonSecondaryStyle,
  mcColors,
  mcGradientTextStyle,
  mcInputStyle,
  mcPanelSectionStyle,
  mcStatusColor,
} from "@/lib/missionControl/layout";

/** §7 — map a raw session status to a board lane state + colour. Colours come
 * from the shared status vocabulary (mcStatusColor) so ok/warn/danger/running
 * mean the same thing on every page. */
function laneState(status?: string): { label: string; color: string } {
  const s = (status || "").toLowerCase();
  if (["complete", "done", "succeeded"].some((x) => s.includes(x)))
    return { label: "done", color: mcStatusColor("ok") };
  if (["fail", "error"].some((x) => s.includes(x)))
    return { label: "failed", color: mcStatusColor("danger") };
  if (["block", "needs", "await", "approval", "pending", "input"].some((x) => s.includes(x)))
    return { label: "needs approval / input", color: mcStatusColor("warn") };
  if (["active", "run", "think"].some((x) => s.includes(x)))
    return { label: "running", color: mcStatusColor("running") };
  return { label: s || "idle", color: mcStatusColor("idle") };
}

type Props = {
  agents: AgentSpec[];
  artifacts: AgentArtifact[];
  events: CoordinationEvent[];
  parentSessionId?: string;
  onRefresh: () => void;
};

const STATUS_COLOR: Record<string, string> = {
  completed: mcColors.green,
  running: mcColors.cyan,
  failed: mcColors.red,
  blocked: mcColors.amber,
};

function roleLabel(capability?: string, explicit?: string): string {
  const named = (explicit || "").trim();
  if (named) return named;
  const cap = (capability || "").trim();
  if (!cap) return "Agent";
  return cap.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function latestCoordPayload(artifacts: AgentArtifact[]) {
  const coord = artifacts.find((a) => a.artifact_type === "agent_coordination");
  if (!coord?.payload) return null;
  return coord.payload as {
    graph?: {
      nodes?: { id: string; label: string; type?: string; status?: string }[];
      replay?: { step: string; label: string }[];
    };
    merged?: { status?: string; confidence?: { level?: string } };
    plan?: { plan_id?: string; goal?: string };
  };
}

/** Inline render of **bold** and `code` spans within one report line. */
function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g).map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) {
      return (
        <strong key={i} style={{ color: mcColors.text, fontWeight: 700 }}>
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (/^`[^`]+`$/.test(part)) {
      return (
        <code key={i} style={{ fontFamily: "ui-monospace, monospace", fontSize: 12, color: mcColors.cyan }}>
          {part.slice(1, -1)}
        </code>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

/** Minimal markdown renderer for the agent report — headings, bullets, bold labels.
 * The reports are short, well-formed markdown; this keeps them readable without a
 * full markdown dependency. Capped by line count so the callout stays compact. */
function MarkdownLite({ text, maxLines = 26 }: { text: string; maxLines?: number }) {
  const all = text.split("\n");
  const lines = all.slice(0, maxLines);
  const truncated = all.length > maxLines;
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {lines.map((line, i) => {
        const t = line.trim();
        if (!t) return <div key={i} style={{ height: 3 }} />;
        // Sub-headings (### and deeper) — e.g. each agent's name in the report.
        if (t.startsWith("### ")) {
          return (
            <div key={i} style={{ fontSize: 13, fontWeight: 700, color: mcColors.text, marginTop: 6 }}>
              {renderInline(t.replace(/^#+\s+/, ""))}
            </div>
          );
        }
        if (t.startsWith("## ")) {
          return (
            <div key={i} style={{ fontSize: 11, fontWeight: 700, color: mcColors.textMuted, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 5 }}>
              {t.slice(3)}
            </div>
          );
        }
        if (t.startsWith("# ")) {
          return (
            <div key={i} style={{ fontSize: 14, fontWeight: 700, color: mcColors.text, marginBottom: 2 }}>
              {t.slice(2)}
            </div>
          );
        }
        if (t.startsWith("- ")) {
          return (
            <div key={i} style={{ fontSize: 13, color: mcColors.textMuted, paddingLeft: 12, lineHeight: 1.5 }}>
              • {renderInline(t.slice(2))}
            </div>
          );
        }
        return (
          <div key={i} style={{ fontSize: 13, color: mcColors.textMuted, lineHeight: 1.55 }}>
            {renderInline(t)}
          </div>
        );
      })}
      {truncated ? <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>… open the session below for the full report</div> : null}
    </div>
  );
}

function CopyChip({ value, label }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    void navigator.clipboard.writeText(value).then(() => {
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    });
  };
  return (
    <button
      type="button"
      onClick={copy}
      title={label ?? "Copy"}
      style={{
        fontFamily: "ui-monospace, monospace",
        fontSize: 11,
        padding: "4px 8px",
        borderRadius: 6,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.25)",
        color: copied ? mcColors.green : mcColors.cyan,
        cursor: "pointer",
      }}
    >
      {copied ? "Copied" : value.length > 42 ? `${value.slice(0, 40)}…` : value}
    </button>
  );
}

export function AgentOrchestrationPanel({
  agents: _staticRosterUnused,
  artifacts,
  events,
  parentSessionId = "all",
  onRefresh,
}: Props) {
  const [sessions, setSessions] = useState<SubagentSessionRow[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [expandedSession, setExpandedSession] = useState<string | null>(null);
  const autoExpandedRef = useRef(false);
  const [delegateGoal, setDelegateGoal] = useState("");
  const [delegateBusy, setDelegateBusy] = useState(false);
  const [delegateNote, setDelegateNote] = useState<string | null>(null);

  const spawnedRoleChips = useMemo(() => {
    const seen = new Set<string>();
    const chips: string[] = [];
    for (const row of sessions) {
      const primary = roleLabel(row.capability, row.role_label);
      if (!seen.has(primary)) {
        seen.add(primary);
        chips.push(primary);
      }
      for (const step of row.transcript ?? []) {
        const label = roleLabel(step.capability ?? step.agent_id, step.role_label);
        if (!seen.has(label)) {
          seen.add(label);
          chips.push(label);
        }
      }
    }
    return chips;
  }, [sessions]);

  const coord = useMemo(() => latestCoordPayload(artifacts), [artifacts]);
  const replay = coord?.graph?.replay ?? [];
  const nodes = coord?.graph?.nodes ?? [];
  const status = coord?.merged?.status ?? "idle";
  const confidence = coord?.merged?.confidence?.level;

  const loadSessions = useCallback(async () => {
    setLoadingSessions(true);
    try {
      const res = await fetchSubagentSessions(parentSessionId);
      setSessions(res.sessions ?? []);
    } catch {
      setSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  }, [parentSessionId]);

  useEffect(() => {
    void loadSessions();
  }, [loadSessions]);

  // Auto-expand the most recently updated session once on first load.
  useEffect(() => {
    if (!autoExpandedRef.current && sessions.length > 0) {
      autoExpandedRef.current = true;
      const latest = [...sessions].sort((a, b) => (b.updated_at ?? 0) - (a.updated_at ?? 0))[0];
      if (latest) setExpandedSession(latest.session_key);
    }
  }, [sessions]);

  // The substantive deliverable from the most recent completed session (the
  // coordination report, not spawn/skills plumbing). See pickLatestOutput.
  const latestOutput = useMemo(() => pickLatestOutput(sessions), [sessions]);

  const refreshAll = () => {
    onRefresh();
    void loadSessions();
  };

  const delegate = useCallback(async () => {
    const goal = delegateGoal.trim();
    if (goal.length < 8 || delegateBusy) return;
    setDelegateBusy(true);
    setDelegateNote(null);
    try {
      const res = await delegateAgentSpawn(goal, parentSessionId === "all" ? "operator" : parentSessionId);
      if (res.ok) {
        setDelegateGoal("");
        setDelegateNote(`Delegated — spawned ${res.agent_count ?? 1} agent(s). Watch the board below.`);
        void loadSessions();
      } else {
        setDelegateNote(res.hint || res.error || "Delegation unavailable.");
      }
    } catch (e) {
      setDelegateNote(e instanceof Error ? e.message : "Delegation failed.");
    } finally {
      setDelegateBusy(false);
    }
  }, [delegateGoal, delegateBusy, parentSessionId, loadSessions]);

  const card = {
    padding: "14px 16px",
    borderRadius: 12,
    border: `1px solid ${mcColors.borderSubtle}`,
    background: "rgba(0,0,0,0.2)",
    marginBottom: 12,
  } as const;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12, flexWrap: "wrap" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, fontWeight: 750, letterSpacing: "-0.02em", width: "fit-content", ...mcGradientTextStyle }}>
            Orchestration
          </h2>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: mcColors.textMuted, maxWidth: 520 }}>
            See who ran, follow session threads, and copy keys for chat follow-ups.
          </p>
        </div>
        <button type="button" onClick={refreshAll} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      {/* Latest output — the final answer from the most recently completed agent run */}
      {latestOutput && (
        <div style={{ ...card, marginTop: 20, background: "rgba(52,211,153,0.06)", borderColor: mcColors.green }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
            <span style={{ width: 8, height: 8, borderRadius: "50%", background: mcColors.green, flexShrink: 0 }} />
            <span style={{ fontSize: 12, fontWeight: 700, color: mcColors.green, textTransform: "uppercase", letterSpacing: "0.04em" }}>
              Latest output
            </span>
            <span style={{ fontSize: 11, color: mcColors.textDim, marginLeft: 4 }}>
              {(latestOutput.goal).slice(0, 64)}{latestOutput.goal.length > 64 ? "…" : ""}
            </span>
          </div>
          <MarkdownLite text={latestOutput.content} />
        </div>
      )}

      {/* Live pipeline */}
      <div style={{ ...card, marginTop: latestOutput ? 12 : 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: STATUS_COLOR[status] ?? mcColors.textMuted,
              boxShadow: status === "running" ? `0 0 8px ${mcColors.cyan}` : undefined,
            }}
          />
          <span style={{ fontWeight: 600, fontSize: 14 }}>Latest run</span>
          <span style={{ fontSize: 12, color: mcColors.textMuted }}>
            {status}
            {confidence ? ` · confidence ${confidence}` : ""}
          </span>
        </div>

        {replay.length > 0 ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
            {replay.map((step, i) => (
              <div key={step.step} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                {i > 0 && <span style={{ color: mcColors.textDim, fontSize: 12 }}>→</span>}
                <span
                  style={{
                    fontSize: 12,
                    padding: "6px 10px",
                    borderRadius: 999,
                    background: mcAlpha(mcColors.cyan, 9),
                    border: `1px solid ${mcColors.borderSubtle}`,
                    color: mcColors.text,
                  }}
                >
                  {step.label}
                </span>
              </div>
            ))}
          </div>
        ) : nodes.length > 0 ? (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {nodes
              .filter((n) => n.type !== "planner")
              .slice(0, 6)
              .map((n) => (
                <span
                  key={n.id}
                  style={{
                    fontSize: 12,
                    padding: "6px 10px",
                    borderRadius: 999,
                    border: `1px solid ${mcColors.borderSubtle}`,
                    color: mcColors.textMuted,
                  }}
                >
                  {n.label}
                </span>
              ))}
          </div>
        ) : (
          <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
            No coordination yet. In chat:{" "}
            <code style={{ fontSize: 12 }}>agent_spawn analyze why the latest deployment failed</code>
          </p>
        )}
      </div>

      {/* §7 Orchestration board — one lane per active/recent agent */}
      <div style={card}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, marginBottom: 10, flexWrap: "wrap" }}>
          <div style={{ fontWeight: 600, fontSize: 14 }}>Agent board</div>
          <span style={{ fontSize: 11, color: mcColors.textDim }}>
            {sessions.length} lane(s) · live from agent sessions
          </span>
        </div>

        {/* Delegate a task — spawns an on-demand agent (flag-gated server-side) */}
        <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap" }}>
          <input
            value={delegateGoal}
            onChange={(e) => setDelegateGoal(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void delegate();
            }}
            placeholder="Delegate a task to a new on-demand agent…"
            aria-label="Delegate a task"
            style={{ ...mcInputStyle, flex: 1, minWidth: 240, padding: "8px 12px", fontSize: 13 }}
          />
          <button
            type="button"
            onClick={() => void delegate()}
            disabled={delegateBusy || delegateGoal.trim().length < 8}
            style={{ ...mcButtonPrimaryStyle, padding: "8px 18px" }}
          >
            {delegateBusy ? "Delegating…" : "Delegate"}
          </button>
        </div>
        {delegateNote && (
          <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>{delegateNote}</p>
        )}

        {loadingSessions && <p style={{ fontSize: 13, color: mcColors.textMuted, margin: 0 }}>Loading…</p>}
        {!loadingSessions && sessions.length === 0 && (
          <p style={{ fontSize: 13, color: mcColors.textMuted, margin: 0 }}>
            No agents yet. Delegate a task above, or ask AethOS a multi-part request in chat —
            spawned agents appear here as live lanes.
          </p>
        )}

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 12 }}>
          {sessions.map((row) => {
            const open = expandedSession === row.session_key;
            const state = laneState(row.status);
            const msgs = row.messages ?? [];
            const lastTool = [...msgs].reverse().find((m) => m.role !== "user" && m.source_tool);
            const currentStep = lastTool
              ? `${lastTool.source_tool}: ${(lastTool.content ?? "").slice(0, 160)}`
              : (msgs[msgs.length - 1]?.content ?? "").slice(0, 160) || "—";
            return (
              <div
                key={row.session_key}
                style={{
                  padding: "12px 14px",
                  borderRadius: 12,
                  border: `1px solid ${open ? state.color : mcColors.borderSubtle}`,
                  background: open ? mcAlpha(state.color, 6) : "rgba(0,0,0,0.18)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      background: state.color,
                      boxShadow: state.label === "running" ? `0 0 8px ${state.color}` : undefined,
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ fontSize: 11, fontWeight: 700, color: state.color, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {state.label}
                  </span>
                  <span style={{ marginLeft: "auto", fontSize: 11, color: mcColors.textDim }}>
                    {msgs.length} steps · {row.run_count ?? 0} run(s)
                  </span>
                </div>

                <div style={{ fontSize: 13, fontWeight: 600, color: mcColors.text }}>
                  {(row.goal ?? "Untitled").slice(0, 90)}
                  {(row.goal ?? "").length > 90 ? "…" : ""}
                </div>

                <div style={{ fontSize: 11, color: mcColors.textMuted }}>
                  <span style={{ color: mcColors.textDim }}>current: </span>
                  {currentStep}
                </div>

                {(() => {
                  // §4 — show each agent in this lane as a DISTINCT specialist
                  // (role · live status · what it's doing) instead of one generic
                  // card, so a multi-part task reads as different agents at work.
                  const steps = row.transcript ?? [];
                  if (steps.length === 0) return null;
                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      <span style={{ fontSize: 10, color: mcColors.textDim }}>agents:</span>
                      {steps.slice(0, 5).map((step, i) => {
                        const st = laneState(step.status);
                        const skills = (step.attached_skills ?? []).slice(0, 3).join(", ");
                        return (
                          <div key={`${step.agent_id}-${i}`} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <span style={{ width: 6, height: 6, borderRadius: "50%", background: st.color, flexShrink: 0 }} />
                            <span style={{ fontSize: 11, fontWeight: 600, color: mcColors.text }}>{roleLabel(step.capability ?? step.agent_id, step.role_label)}</span>
                            <span style={{ fontSize: 10, color: st.color }}>{st.label}</span>
                            {skills ? <span style={{ fontSize: 10, color: mcColors.textDim, marginLeft: "auto" }}>{skills}</span> : null}
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}

                {(() => {
                  // §4 — inline coordination feed: show the latest agent↔agent /
                  // AethOS↔agent messages without making the operator click into
                  // each lane. The full thread stays behind the expander below.
                  const recent = msgs.slice(-2);
                  if (recent.length === 0) return null;
                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: 3, borderTop: `1px solid ${mcColors.borderSubtle}`, paddingTop: 6 }}>
                      <span style={{ fontSize: 10, color: mcColors.textDim }}>coordination:</span>
                      {recent.map((m, i) => (
                        <div key={i} style={{ fontSize: 11, color: mcColors.textMuted, lineHeight: 1.4 }}>
                          <span style={{ color: mcColors.text, fontWeight: 600 }}>{m.role}</span>
                          {m.source_tool ? <span style={{ color: mcColors.textDim }}> · {m.source_tool}</span> : null}
                          : {(m.content ?? "").slice(0, 240)}
                        </div>
                      ))}
                    </div>
                  );
                })()}

                <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                  <button
                    type="button"
                    onClick={() => setExpandedSession(open ? null : row.session_key)}
                    style={{
                      ...mcButtonSecondaryStyle,
                      fontSize: 11,
                      padding: "4px 10px",
                    }}
                  >
                    {open ? "Hide full thread" : "Full thread"}
                  </button>
                  <CopyChip value={row.session_key} label="Copy session key" />
                  <span style={{ fontSize: 11, color: mcColors.textDim, marginLeft: "auto" }}>
                    {formatTs(row.updated_at)}
                  </span>
                </div>

                {open && (
                  <div style={{ fontSize: 12, color: mcColors.textMuted, borderTop: `1px solid ${mcColors.borderSubtle}`, paddingTop: 8 }}>
                    {msgs.length === 0 ? (
                      <span>No messages yet.</span>
                    ) : (
                      msgs.slice(-8).map((m, i) => (
                        <div
                          key={i}
                          style={{
                            marginTop: 6,
                            paddingLeft: 10,
                            borderLeft: `2px solid ${m.role === "user" ? mcColors.cyan : mcColors.border}`,
                          }}
                        >
                          <span style={{ color: mcColors.text, fontWeight: 600 }}>{m.role}</span>
                          {m.source_tool ? <span style={{ color: mcColors.textDim }}> · {m.source_tool}</span> : null}
                          : {(m.content ?? "").slice(0, 400)}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Compact roster + recent events */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))", gap: 12 }}>
        <div style={card}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Spawned agents</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {spawnedRoleChips.length === 0 ? (
              <span style={{ fontSize: 12, color: mcColors.textMuted }}>
                On-demand only — agents appear here after chat creation or delegation.
              </span>
            ) : (
              spawnedRoleChips.slice(0, 8).map((label) => (
                <span
                  key={label}
                  style={{
                    fontSize: 11,
                    padding: "4px 8px",
                    borderRadius: 6,
                    background: "rgba(255,255,255,0.04)",
                    border: `1px solid ${mcColors.borderSubtle}`,
                    color: mcColors.textMuted,
                  }}
                >
                  {label}
                </span>
              ))
            )}
          </div>
        </div>
        <div style={card}>
          <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10 }}>Recent goals</div>
          {events.length === 0 ? (
            <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted }}>No events yet.</p>
          ) : (
            <ul style={{ margin: 0, padding: 0, listStyle: "none" }}>
              {events.slice(0, 5).map((ev, i) => (
                <li key={`${ev.plan_id}-${i}`} style={{ fontSize: 12, color: mcColors.textMuted, marginBottom: 6 }}>
                  {(ev.goal ?? ev.plan_id ?? "—").slice(0, 64)} · {formatTs(ev.at)}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  );
}
