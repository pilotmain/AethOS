// SPDX-License-Identifier: Apache-2.0
// Memory Viewer — browse self-organized memory topics and compress a topic into a digest.
"use client";

import { useEffect, useState } from "react";

import { apiBase } from "@/lib/api";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

interface Entry {
  id: string;
  text: string;
  tags: string[];
}
interface Topic {
  topic: string;
  count: number;
  entries: Entry[];
}

export function MemoryViewerPanel() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [enabled, setEnabled] = useState<boolean>(false);
  const [entryCount, setEntryCount] = useState(0);
  const [digest, setDigest] = useState<{ topic: string; digest: string } | null>(null);
  const [busy, setBusy] = useState(false);

  function refresh() {
    void fetch(`${apiBase()}/api/v1/memory/overview`, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        setEnabled(Boolean(d.enabled));
        setEntryCount(Number(d.entry_count) || 0);
      });
    void fetch(`${apiBase()}/api/v1/memory/topics`, { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => setTopics(d.topics ?? []));
  }
  useEffect(refresh, []);

  async function compress(topic: string) {
    setBusy(true);
    setDigest(null);
    try {
      const res = await fetch(`${apiBase()}/api/v1/memory/compress/${encodeURIComponent(topic)}`, {
        method: "POST",
      });
      const d = await res.json();
      if (d.ok) setDigest({ topic: d.topic, digest: d.digest });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={mcPanelSectionStyle}>
      <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Memory</h2>
      <p style={{ margin: "8px 0 16px", fontSize: 13, color: mcColors.textMuted, maxWidth: 620 }}>
        Self-organizing memory grouped by topic. {entryCount} memories across {topics.length} topics.
        {enabled ? "" : " (Vector memory is off — set VECTOR_MEMORY_ENABLED=true to capture new memories.)"}
      </p>

      {topics.length === 0 ? (
        <p style={{ color: mcColors.textMuted, fontSize: 13 }}>No memories yet.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {topics.map((t) => (
            <div
              key={t.topic}
              style={{
                padding: "12px 14px",
                borderRadius: 8,
                border: `1px solid ${mcColors.borderSubtle}`,
                background: "rgba(15,23,42,0.5)",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontWeight: 600, fontSize: 13, color: mcColors.text }}>
                  {t.topic} <span style={{ color: mcColors.textDim, fontWeight: 400 }}>· {t.count}</span>
                </span>
                <button type="button" onClick={() => compress(t.topic)} disabled={busy} style={mcButtonSecondaryStyle}>
                  Compress
                </button>
              </div>
              <ul style={{ margin: "8px 0 0", paddingLeft: 16, fontSize: 11, color: mcColors.textMuted }}>
                {t.entries.slice(0, 5).map((e) => (
                  <li key={e.id} style={{ marginBottom: 2 }}>
                    {e.text}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}

      {digest && (
        <div
          style={{
            marginTop: 16,
            padding: "12px 14px",
            borderRadius: 8,
            border: `1px solid ${mcColors.cyan}`,
            background: "rgba(8,145,178,0.12)",
          }}
        >
          <div style={{ fontWeight: 600, fontSize: 12, color: mcColors.text, marginBottom: 6 }}>
            Digest — {digest.topic}
          </div>
          <pre style={{ whiteSpace: "pre-wrap", fontSize: 12, color: mcColors.textMuted, margin: 0 }}>
            {digest.digest}
          </pre>
        </div>
      )}
    </section>
  );
}
