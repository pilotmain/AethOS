// SPDX-License-Identifier: Apache-2.0
// Daily Digest — preview the morning briefing, deliver it now, view the latest.
"use client";

import { useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import { mcButtonPrimaryStyle, mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

interface Digest {
  generated_at: number;
  text: string;
}

export function DailyDigestPanel() {
  const [digest, setDigest] = useState<Digest | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  async function load(kind: "preview" | "latest") {
    setBusy(true);
    setNote("");
    try {
      const res = await fetch(`${apiBase()}/api/v1/digest/${kind}`, { cache: "no-store" });
      const data = await res.json();
      setDigest(data.digest ?? null);
      if (!data.digest && kind === "latest") setNote("No digest delivered yet — try Preview.");
    } finally {
      setBusy(false);
    }
  }

  async function deliver() {
    setBusy(true);
    setNote("");
    try {
      const res = await fetch(`${apiBase()}/api/v1/digest/deliver`, { method: "POST" });
      const data = await res.json();
      setDigest(data.digest ?? null);
      setNote(`Delivered to: ${(data.delivered_to ?? []).join(", ")}`);
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load("latest");
  }, []);

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Daily Digest</h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
        A morning briefing assembled from deploys, jobs, pending approvals, monitors and social.
        Delivered automatically at the configured hour (set <code>DIGEST_ENABLED=true</code>); push to
        Telegram with <code>DIGEST_TELEGRAM_CHAT</code>.
      </p>

      <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
        <button type="button" onClick={() => void load("preview")} disabled={busy} style={mcButtonSecondaryStyle}>
          Preview now
        </button>
        <button type="button" onClick={deliver} disabled={busy} style={mcButtonPrimaryStyle}>
          {busy ? "Working…" : "Deliver now"}
        </button>
      </div>
      {note && <div style={{ fontSize: 12, color: mcColors.green, marginBottom: 10 }}>{note}</div>}

      {digest ? (
        <pre
          style={{
            whiteSpace: "pre-wrap",
            fontSize: 13,
            lineHeight: 1.6,
            color: mcColors.text,
            background: "rgba(0,0,0,0.4)",
            padding: "14px 16px",
            borderRadius: 8,
            border: `1px solid ${mcColors.borderSubtle}`,
          }}
        >
          {digest.text}
        </pre>
      ) : (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>Click Preview to generate a digest.</p>
      )}
    </section>
  );
}
