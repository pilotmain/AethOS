// SPDX-License-Identifier: Apache-2.0
// Proactive suggestions — read-only proposals AethOS surfaces from current signals.
"use client";

import { useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

interface Suggestion {
  id: string;
  source: string;
  title: string;
  detail: string;
  severity: "high" | "medium" | "low" | string;
  action_hint: string;
}

const SEV_COLOR: Record<string, string> = { high: "#fca5a5", medium: "#fcd34d", low: "#93c5fd" };

export function ProactiveSuggestionsPanel() {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [busy, setBusy] = useState(false);

  function refresh() {
    void fetch(`${apiBase()}/api/v1/proactive/suggestions`, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => setSuggestions(d.suggestions ?? []));
  }
  useEffect(refresh, []);

  async function scan() {
    setBusy(true);
    try {
      await fetch(`${apiBase()}/api/v1/proactive/scan`, { method: "POST" });
      refresh();
    } finally {
      setBusy(false);
    }
  }

  async function dismiss(id: string) {
    await fetch(`${apiBase()}/api/v1/proactive/suggestions/${encodeURIComponent(id)}/dismiss`, { method: "POST" });
    refresh();
  }

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Proactive Suggestions</h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
        Things AethOS noticed and thinks you might want to act on — surfaced from monitors,
        recurring failures, approvals and skills. These are <strong>proposals only</strong>; nothing runs
        automatically. Enable with <code>PROACTIVE_SUGGESTIONS_ENABLED=true</code>.
      </p>

      <button type="button" onClick={scan} disabled={busy} style={{ ...mcButtonSecondaryStyle, marginBottom: 14 }}>
        {busy ? "Scanning…" : "Scan now"}
      </button>

      {suggestions.length === 0 ? (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>
          Nothing to suggest right now (or the feature is disabled).
        </p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {suggestions.map((s) => (
            <div
              key={s.id}
              style={{
                padding: "12px 14px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                borderLeft: `3px solid ${SEV_COLOR[s.severity] || mcColors.borderSubtle}`,
                background: "rgba(15,23,42,0.5)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                <span style={{ fontWeight: 600, fontSize: 13, color: mcColors.text }}>
                  {s.title}{" "}
                  <span style={{ color: SEV_COLOR[s.severity] || mcColors.textDim, fontSize: 11 }}>
                    · {s.severity}
                  </span>
                </span>
                <button type="button" onClick={() => dismiss(s.id)} style={mcButtonSecondaryStyle}>
                  Dismiss
                </button>
              </div>
              <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 4 }}>{s.detail}</div>
              <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 4 }}>→ {s.action_hint}</div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
