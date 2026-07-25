// SPDX-License-Identifier: Apache-2.0
// Live multi-agent communication — animated graph of agents talking to each other.
"use client";

import { useEffect, useMemo, useRef, useState } from "react";

import { apiBase } from "@/lib/api";
import { mcButtonPrimaryStyle, mcColors, mcGradientTextStyle, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import { agentAvatar, AVATAR_STYLES, type AvatarStyle } from "@/lib/missionControl/agentAvatars";

interface CommEvent {
  seq: number;
  ts: number;
  from: string;
  to: string;
  type: "dispatch" | "report" | "handoff" | string;
  summary: string;
}
interface AgentNode {
  id: string;
  label: string;
  role: string;
}
interface Comms {
  agents: AgentNode[];
  events: CommEvent[];
  goal?: string;
}

const TYPE_COLOR: Record<string, string> = {
  dispatch: "#22d3ee", // cyan — orchestrator → agent
  report: "#34d399", // green — agent → orchestrator
  handoff: "#a78bfa", // violet — agent → agent
};

export function AgentCommsPanel() {
  const [goal, setGoal] = useState("");
  const [comms, setComms] = useState<Comms | null>(null);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [avatarStyle, setAvatarStyle] = useState<AvatarStyle>("emoji");
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const poll = useRef<ReturnType<typeof setInterval> | null>(null);

  async function run() {
    if (!goal.trim()) return;
    setBusy(true);
    setComms(null);
    setStep(0);
    setPlaying(false);
    if (poll.current) clearInterval(poll.current);
    // Start the run in the background and poll its comms so the team animates LIVE as it
    // works — big teams no longer block or time out.
    const res = await fetch(`${apiBase()}/api/v1/agents/coordination/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goal: goal.trim() }),
    });
    const { session_id } = await res.json();
    if (!session_id) {
      setBusy(false);
      return;
    }
    poll.current = setInterval(async () => {
      try {
        const r = await fetch(`${apiBase()}/api/v1/agents/comms/${encodeURIComponent(session_id)}`, { cache: "no-store" });
        const d = await r.json();
        const c = d.comms as Comms & { status?: string };
        if (c) {
          setComms(c);
          setStep(Math.max(0, (c.events?.length ?? 1) - 1)); // follow the latest message live
          if (c.status === "done") {
            if (poll.current) clearInterval(poll.current);
            setBusy(false);
          }
        }
      } catch {
        /* keep polling */
      }
    }, 1000);
  }

  useEffect(() => {
    return () => {
      if (poll.current) clearInterval(poll.current);
    };
  }, []);

  // Replay the recorded comms as an animation.
  useEffect(() => {
    if (timer.current) clearInterval(timer.current);
    if (!playing || !comms || comms.events.length === 0) return;
    timer.current = setInterval(() => {
      setStep((s) => {
        if (s >= comms.events.length - 1) {
          setPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, 900);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [playing, comms]);

  const positions = useMemo(() => {
    const map: Record<string, { x: number; y: number }> = {};
    if (!comms) return map;
    const cx = 320;
    const cy = 200;
    map["orchestrator"] = { x: cx, y: cy };
    const peers = comms.agents.filter((a) => a.id !== "orchestrator");
    peers.forEach((a, i) => {
      const angle = (2 * Math.PI * i) / Math.max(1, peers.length) - Math.PI / 2;
      map[a.id] = { x: cx + 170 * Math.cos(angle), y: cy + 150 * Math.sin(angle) };
    });
    return map;
  }, [comms]);

  const active = comms && comms.events[step] ? comms.events[step] : null;
  const labelFor = (id: string) =>
    comms?.agents.find((a) => a.id === id)?.label || (id === "orchestrator" ? "Orchestrator" : id);

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 22, fontWeight: 750, letterSpacing: "-0.02em", width: "fit-content", ...mcGradientTextStyle }}>
        Multi-Agent Live
      </h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
        Watch the team work: the orchestrator dispatches each specialist, they report back, and they
        hand off context to each other — animated in real time. Read-only coordination (a plan, no
        mutations).
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
        <input
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="orchestrate a team: a marketing lead, a writer, an analyst and a researcher to plan our product launch campaign"
          style={{
            flex: 1,
            minWidth: 280,
            padding: "8px 12px",
            borderRadius: 8,
            border: `1px solid ${mcColors.borderSubtle}`,
            background: "rgba(0,0,0,0.35)",
            color: mcColors.text,
            fontSize: 13,
          }}
        />
        <button type="button" onClick={run} disabled={busy} style={mcButtonPrimaryStyle}>
          {busy ? "Running team…" : "Run team"}
        </button>
      </div>

      {comms && comms.agents.length > 1 ? (
        <>
          <svg viewBox="0 0 640 400" style={{ width: "100%", maxWidth: 880, height: "auto", display: "block", margin: "0 auto" }} role="img" aria-label="Agent communication graph">
            <defs>
              {/* Cyan→violet edge gradient + soft glow — the AethOS signature look. */}
              <linearGradient id="aethos-edge-grad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor="#22d3ee" />
                <stop offset="100%" stopColor="#a78bfa" />
              </linearGradient>
              <filter id="aethos-node-glow" x="-60%" y="-60%" width="220%" height="220%">
                <feGaussianBlur stdDeviation="3.4" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>

            {/* Oversight motif — a calm "eye" above the team. The run is read-only:
                AethOS coordinates a plan; you keep oversight. */}
            <g opacity={0.9}>
              <ellipse cx={320} cy={26} rx={20} ry={11} fill="none" stroke="#a78bfa" strokeWidth={1.4} filter="url(#aethos-node-glow)" />
              <circle cx={320} cy={26} r={4.5} fill="#22d3ee" />
              <text x={320} y={50} textAnchor="middle" fontSize="9" fill={mcColors.textDim} letterSpacing="0.08em">
                OVERSIGHT · READ-ONLY
              </text>
            </g>

            {/* edges */}
            {comms.agents
              .filter((a) => a.id !== "orchestrator")
              .map((a) => {
                const p = positions[a.id];
                const o = positions["orchestrator"];
                if (!p || !o) return null;
                return <line key={`e-${a.id}`} x1={o.x} y1={o.y} x2={p.x} y2={p.y} stroke={mcColors.borderSubtle} strokeWidth={1} />;
              })}
            {/* active message edge (animated) */}
            {active && positions[active.from] && positions[active.to] ? (
              <line
                x1={positions[active.from].x}
                y1={positions[active.from].y}
                x2={positions[active.to].x}
                y2={positions[active.to].y}
                stroke="url(#aethos-edge-grad)"
                strokeWidth={3}
                strokeLinecap="round"
                filter="url(#aethos-node-glow)"
              >
                <animate attributeName="opacity" values="0.3;1;0.3" dur="0.9s" repeatCount="indefinite" />
              </line>
            ) : null}
            {/* traveling message packet along the active edge */}
            {active && positions[active.from] && positions[active.to] ? (
              <circle r={5} fill={TYPE_COLOR[active.type] || mcColors.cyan} filter="url(#aethos-node-glow)">
                <animate attributeName="cx" values={`${positions[active.from].x};${positions[active.to].x}`} dur="0.9s" repeatCount="indefinite" />
                <animate attributeName="cy" values={`${positions[active.from].y};${positions[active.to].y}`} dur="0.9s" repeatCount="indefinite" />
                <animate attributeName="opacity" values="0;1;1;0" dur="0.9s" repeatCount="indefinite" />
              </circle>
            ) : null}
            {/* nodes — per-role avatars */}
            {comms.agents.map((a) => {
              const p = positions[a.id];
              if (!p) return null;
              const isActive = Boolean(active && (active.from === a.id || active.to === a.id));
              const isOrch = a.id === "orchestrator";
              const av = agentAvatar(`${labelFor(a.id)} ${a.role || ""}`);
              const r = isOrch ? 36 : 29;
              return (
                <g key={a.id}>
                  {isActive ? (
                    <circle cx={p.x} cy={p.y} r={r + 6} fill="none" stroke={av.color} strokeWidth={2} opacity={0.5}>
                      <animate attributeName="r" values={`${r};${r + 12}`} dur="0.9s" repeatCount="indefinite" />
                      <animate attributeName="opacity" values="0.6;0" dur="0.9s" repeatCount="indefinite" />
                    </circle>
                  ) : null}
                  {/* faint outer ring — gives every node the demo's double-ring depth */}
                  <circle cx={p.x} cy={p.y} r={r + 4} fill="none" stroke={av.color} strokeWidth={1} opacity={0.18} />
                  <circle
                    cx={p.x}
                    cy={p.y}
                    r={r}
                    fill={isActive ? `${av.color}2e` : "rgba(11,15,26,0.95)"}
                    stroke={av.color}
                    strokeWidth={isActive ? 3 : 1.8}
                    filter={isActive ? "url(#aethos-node-glow)" : undefined}
                  />
                  {avatarStyle === "emoji" ? (
                    <text x={p.x} y={p.y + 8} textAnchor="middle" fontSize={isOrch ? 28 : 23}>
                      {av.glyph}
                    </text>
                  ) : avatarStyle === "initials" ? (
                    <text x={p.x} y={p.y + 6} textAnchor="middle" fontSize="16" fontWeight={700} fill={av.color}>
                      {av.initials}
                    </text>
                  ) : (
                    <circle cx={p.x} cy={p.y} r={6} fill={av.color} />
                  )}
                  <text x={p.x} y={p.y + r + 16} textAnchor="middle" fontSize="12" fontWeight={600} fill={mcColors.text}>
                    {labelFor(a.id)}
                  </text>
                </g>
              );
            })}
          </svg>

          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap", margin: "4px 0 8px" }}>
            <span style={{ fontSize: 11, color: mcColors.textMuted }}>Symbols:</span>
            {AVATAR_STYLES.map((s) => (
              <button
                key={s.id}
                type="button"
                onClick={() => setAvatarStyle(s.id)}
                style={{
                  padding: "3px 10px",
                  borderRadius: 999,
                  fontSize: 11,
                  cursor: "pointer",
                  border: `1px solid ${avatarStyle === s.id ? mcColors.cyan : mcColors.borderSubtle}`,
                  background: avatarStyle === s.id ? "rgba(34,211,238,0.12)" : "transparent",
                  color: avatarStyle === s.id ? mcColors.cyan : mcColors.textMuted,
                }}
              >
                {s.label}
              </button>
            ))}
            <span style={{ marginLeft: 8, fontSize: 11, color: mcColors.textDim }}>
              <span style={{ color: TYPE_COLOR.dispatch }}>●</span> dispatch{"  "}
              <span style={{ color: TYPE_COLOR.report }}>●</span> report{"  "}
              <span style={{ color: TYPE_COLOR.handoff }}>●</span> handoff
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "8px 0" }}>
            <button type="button" onClick={() => { setStep(0); setPlaying(true); }} style={{ ...mcButtonPrimaryStyle, padding: "4px 12px" }}>
              ▶ Replay
            </button>
            <span style={{ fontSize: 12, color: mcColors.textMuted }}>
              {active ? (
                <>
                  <strong style={{ color: TYPE_COLOR[active.type] || mcColors.cyan }}>{labelFor(active.from)}</strong>
                  {" → "}
                  <strong style={{ color: TYPE_COLOR[active.type] || mcColors.cyan }}>{labelFor(active.to)}</strong>
                  {`  (${active.type})`}
                </>
              ) : (
                "Run a team to see the agents communicate."
              )}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 220, overflowY: "auto", marginTop: 8 }}>
            {comms.events.map((e, i) => (
              <div
                key={e.seq}
                style={{
                  padding: "6px 10px",
                  borderRadius: 6,
                  fontSize: 11,
                  background: i === step ? "rgba(34,211,238,0.12)" : "rgba(15,23,42,0.5)",
                  border: `1px solid ${i === step ? mcColors.cyan : mcColors.borderSubtle}`,
                  color: mcColors.textMuted,
                }}
              >
                <span style={{ color: TYPE_COLOR[e.type] || mcColors.textMuted }}>●</span> {labelFor(e.from)} → {labelFor(e.to)}{" "}
                <span style={{ color: mcColors.textDim }}>· {e.type}</span> — {e.summary}
              </div>
            ))}
          </div>

          {/* Team output — report-type events are the substantive work each agent delivers */}
          {comms.events.filter((e) => e.type === "report").length > 0 && (
            <div style={{ marginTop: 20, borderTop: `1px solid ${mcColors.borderSubtle}`, paddingTop: 16 }}>
              <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 10, color: mcColors.text }}>
                Team output{busy ? " · in progress…" : ""}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {comms.events
                  .filter((e) => e.type === "report")
                  .map((e, i) => (
                    <div
                      key={i}
                      style={{
                        padding: "10px 14px",
                        borderRadius: 10,
                        border: `1px solid ${mcColors.borderSubtle}`,
                        background: "rgba(52,211,153,0.07)",
                      }}
                    >
                      <div style={{ fontSize: 11, fontWeight: 700, color: "#34d399", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>
                        {labelFor(e.from)}
                      </div>
                      <p style={{ margin: 0, fontSize: 13, color: mcColors.text, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
                        {e.summary}
                      </p>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
          {busy ? "Coordinating…" : "Enter a team goal and Run to watch the agents collaborate."}
        </p>
      )}
    </section>
  );
}
