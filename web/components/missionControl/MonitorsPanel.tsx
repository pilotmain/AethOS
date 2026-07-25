// SPDX-License-Identifier: Apache-2.0
// Continuous Monitor agents — create stateful watchers and see their observation log.
"use client";

import { useEffect, useState } from "react";

import {
  createMonitor,
  deleteMonitor,
  fetchMonitors,
  runMonitor,
  setMonitorEnabled,
  type Monitor,
  type MonitorKind,
} from "@/lib/missionControl/monitorsApi";
import { mcButtonPrimaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function MonitorsPanel() {
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [kinds, setKinds] = useState<MonitorKind[]>([]);
  const [name, setName] = useState("");
  const [kind, setKind] = useState("url");
  const [target, setTarget] = useState("");
  const [interval, setInterval] = useState(300);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  function refresh() {
    void fetchMonitors().then((d) => {
      setMonitors(d.monitors ?? []);
      setKinds(d.kinds ?? []);
    });
  }
  useEffect(() => {
    refresh();
  }, []);

  async function add() {
    if (!name.trim() || !target.trim()) return;
    setBusy(true);
    setErr("");
    try {
      await createMonitor({ name: name.trim(), kind, target: target.trim(), interval_sec: interval });
      setName("");
      setTarget("");
      refresh();
    } catch (e: unknown) {
      setErr(e instanceof Error ? e.message : "Create failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Monitors</h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
        Continuous watchers that keep state between runs and record an observation whenever the
        signal changes — a deploy, an endpoint, a competitor&apos;s site. Read-only perception; nothing
        is mutated.
      </p>

      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: 8,
          alignItems: "flex-end",
          marginBottom: 16,
          padding: 12,
          borderRadius: 8,
          border: `1px solid ${mcColors.borderSubtle}`,
          background: "rgba(0,0,0,0.2)",
        }}
      >
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Name
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Prod API uptime" style={inp} />
        </label>
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Kind
          <select value={kind} onChange={(e) => setKind(e.target.value)} style={inp}>
            {kinds.map((k) => (
              <option key={k.kind} value={k.kind}>
                {k.label}
              </option>
            ))}
          </select>
        </label>
        <label style={{ fontSize: 11, color: mcColors.textMuted, flex: 1, minWidth: 220 }}>
          Target
          <input
            value={target}
            onChange={(e) => setTarget(e.target.value)}
            placeholder={kind === "url" ? "https://example.com" : "railway pilotos-api"}
            style={{ ...inp, width: "100%" }}
          />
        </label>
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Every (s)
          <input
            type="number"
            value={interval}
            min={60}
            onChange={(e) => setInterval(Number(e.target.value))}
            style={{ ...inp, width: 90 }}
          />
        </label>
        <button type="button" onClick={add} disabled={busy} style={mcButtonPrimaryStyle}>
          {busy ? "Adding…" : "Add monitor"}
        </button>
      </div>
      {err && <div style={{ color: "#fca5a5", fontSize: 12, marginBottom: 12 }}>{err}</div>}

      {monitors.length === 0 ? (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No monitors yet. Add one above.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {monitors.map((m) => (
            <div
              key={m.monitor_id}
              style={{
                padding: "12px 14px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(15,23,42,0.5)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 13, color: mcColors.text }}>
                  {m.name}{" "}
                  <span style={{ color: mcColors.textDim, fontWeight: 400 }}>
                    · {m.kind} · {m.target} · every {m.interval_sec}s
                  </span>
                </span>
                <span style={{ display: "flex", gap: 6 }}>
                  <button type="button" onClick={() => void runMonitor(m.monitor_id).then(refresh)} style={btn}>
                    Run now
                  </button>
                  <button
                    type="button"
                    onClick={() => void setMonitorEnabled(m.monitor_id, !m.enabled).then(refresh)}
                    style={btn}
                  >
                    {m.enabled ? "Pause" : "Resume"}
                  </button>
                  <button type="button" onClick={() => void deleteMonitor(m.monitor_id).then(refresh)} style={btn}>
                    Delete
                  </button>
                </span>
              </div>
              <div style={{ fontSize: 11, color: m.enabled ? "#6ee7b7" : mcColors.textDim, marginTop: 4 }}>
                {m.enabled ? "● active" : "○ paused"} · {m.last_summary || "not run yet"}
              </div>
              {m.observations.length > 0 && (
                <details style={{ marginTop: 6 }}>
                  <summary style={{ cursor: "pointer", fontSize: 11, color: mcColors.textMuted }}>
                    {m.observations.length} observation{m.observations.length > 1 ? "s" : ""}
                  </summary>
                  <ul style={{ margin: "6px 0 0", paddingLeft: 16, fontSize: 11, color: mcColors.textMuted }}>
                    {m.observations.slice(0, 10).map((o, i) => (
                      <li key={i} style={{ marginBottom: 2, color: o.alert ? "#fca5a5" : undefined }}>
                        {new Date(o.at * 1000).toLocaleString()} — {o.summary}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

const inp: React.CSSProperties = {
  display: "block",
  marginTop: 4,
  padding: "6px 8px",
  borderRadius: 6,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.35)",
  color: mcColors.text,
  fontSize: 12,
};

const btn: React.CSSProperties = {
  padding: "4px 10px",
  borderRadius: 6,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.3)",
  color: mcColors.textMuted,
  cursor: "pointer",
  fontSize: 11,
};
