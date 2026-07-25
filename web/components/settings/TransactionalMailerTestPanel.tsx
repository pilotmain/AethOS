"use client";

import { useCallback, useState } from "react";

import { sendMailerTest } from "@/lib/auth/transactionalMailerApi";

type Props = {
  defaultTo?: string;
};

export function TransactionalMailerTestPanel({ defaultTo = "" }: Props) {
  const [to, setTo] = useState(defaultTo);
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<Awaited<ReturnType<typeof sendMailerTest>> | null>(null);

  const run = useCallback(async () => {
    setBusy(true);
    setResult(null);
    try {
      setResult(await sendMailerTest(to));
    } finally {
      setBusy(false);
    }
  }, [to]);

  return (
    <section
      style={{
        marginTop: 20,
        padding: 14,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
      }}
    >
      <h3 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 600 }}>Transactional mailer test</h3>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: "var(--aethos-text-dim)" }}>
        Send a diagnostic email (same pipeline as signup verification). Shows the provider&apos;s real response,
        redacted.
      </p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <input
          type="email"
          value={to}
          onChange={(e) => setTo(e.target.value)}
          placeholder="operator@yourdomain.com"
          style={{
            flex: "1 1 200px",
            minWidth: 200,
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.12)",
            background: "rgba(0,0,0,0.25)",
            color: "var(--aethos-text)",
            fontSize: 13,
          }}
        />
        <button
          type="button"
          disabled={busy || !to.trim()}
          onClick={() => void run()}
          style={{
            padding: "8px 14px",
            borderRadius: 8,
            border: "none",
            background: "var(--aethos-accent)",
            color: "#0b0f14",
            fontWeight: 600,
            fontSize: 13,
            cursor: busy ? "default" : "pointer",
            opacity: busy || !to.trim() ? 0.6 : 1,
          }}
        >
          {busy ? "Sending…" : "Send test email"}
        </button>
      </div>
      {result ? (
        <div
          style={{
            marginTop: 12,
            padding: 10,
            borderRadius: 8,
            fontSize: 12,
            lineHeight: 1.45,
            background: result.ok ? "rgba(0,200,140,0.08)" : "rgba(255,120,80,0.08)",
            border: `1px solid ${result.ok ? "rgba(0,200,140,0.25)" : "rgba(255,120,80,0.25)"}`,
          }}
        >
          <div style={{ fontWeight: 600 }}>{result.ok ? "Sent" : "Failed"}</div>
          {result.provider ? <div>Provider: {result.provider}</div> : null}
          {result.status != null ? <div>Status: {result.status}</div> : null}
          {result.detail ? <div style={{ marginTop: 4 }}>{result.detail}</div> : null}
          {result.hint ? (
            <div style={{ marginTop: 6, color: "var(--aethos-text-muted)" }}>{result.hint}</div>
          ) : null}
          {result.error && !result.detail ? <div>{result.error}</div> : null}
        </div>
      ) : null}
    </section>
  );
}
