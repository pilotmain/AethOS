"use client";

import { useCallback, useEffect, useState } from "react";

import {
  channelWebhookUrl,
  fetchChannelConnection,
  revokeChannelCredential,
  storeChannelCredentials,
  testChannelCredential,
  type ChannelConnection,
} from "@/lib/missionControl/channelsApi";
import { mcColors } from "@/lib/missionControl/layout";
import { formatMcPanelError } from "@/lib/missionControl/panelError";

type Props = {
  channelId: string;
  onChanged?: () => void;
};

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "8px 10px",
  borderRadius: 8,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.25)",
  color: "var(--aethos-text)",
  fontSize: 12,
};

const buttonStyle: React.CSSProperties = {
  padding: "8px 12px",
  borderRadius: 8,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "var(--aethos-accent, #3b82f6)",
  color: "#fff",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
};

export function ChannelCredentialPanel({ channelId, onChanged }: Props) {
  const [conn, setConn] = useState<ChannelConnection | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [copied, setCopied] = useState(false);

  const load = useCallback(async () => {
    try {
      const next = await fetchChannelConnection(channelId);
      setConn(next);
      if (!label && next.schema?.default_label) setLabel(next.schema.default_label);
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Could not load channel"));
    }
  }, [channelId, label]);

  useEffect(() => {
    void load();
  }, [load]);

  // §4 — honest: no credential box for an unimplemented adapter.
  if (conn && !conn.supports_credentials) return null;
  if (!conn?.schema) return null;

  const schema = conn.schema;
  const webhookUrl = channelWebhookUrl(conn.webhook_path);

  const save = async () => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const missing = schema.fields.filter((f) => f.required && !(values[f.id] || "").trim());
      if (missing.length > 0) {
        setError(`Required: ${missing.map((f) => f.label).join(", ")}`);
        return;
      }
      const res = await storeChannelCredentials(channelId, { label: label.trim() || schema.label, fields: values });
      if (!res.ok) {
        setError(res.test?.detail || "Save failed");
        return;
      }
      setValues({});
      setNotice("Connected. Credentials stored in the encrypted vault.");
      await load();
      onChanged?.();
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Save failed"));
    } finally {
      setBusy(false);
    }
  };

  const onTest = async (credentialId: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      const res = await testChannelCredential(channelId, credentialId);
      setNotice(res.test?.ok ? `Test OK — ${res.test?.detail ?? "credential valid"}` : res.test?.detail || "Test failed");
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Test failed"));
    } finally {
      setBusy(false);
    }
  };

  const onRevoke = async (credentialId: string) => {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await revokeChannelCredential(channelId, credentialId);
      setNotice("Credential revoked.");
      await load();
      onChanged?.();
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Revoke failed"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 8 }}>
      {conn.credentials.length > 0 ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {conn.credentials.map((c) => (
            <div
              key={c.credential_id}
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8, fontSize: 12 }}
            >
              <span style={{ color: "var(--aethos-text)" }}>
                {c.label || schema.label}{" "}
                <span style={{ color: mcColors.textMuted }}>· {c.masked_identifier || "stored"}</span>
              </span>
              <span style={{ display: "flex", gap: 6 }}>
                <button type="button" disabled={busy} onClick={() => void onTest(c.credential_id)} style={{ ...buttonStyle, background: "transparent", color: "var(--aethos-text)" }}>
                  Test
                </button>
                <button type="button" disabled={busy} onClick={() => void onRevoke(c.credential_id)} style={{ ...buttonStyle, background: "transparent", color: "var(--aethos-warn)" }}>
                  Revoke
                </button>
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {schema.description ? (
        <p style={{ margin: 0, fontSize: 11, color: mcColors.textMuted }}>{schema.description}</p>
      ) : null}

      <input
        type="text"
        value={label}
        placeholder={`${schema.label} connection`}
        onChange={(e) => setLabel(e.target.value)}
        style={inputStyle}
        aria-label="Credential label"
      />
      {schema.fields.map((f) => (
        <label key={f.id} style={{ display: "flex", flexDirection: "column", gap: 3, fontSize: 11, color: "var(--aethos-text-dim)" }}>
          {f.label}
          {f.required ? <span style={{ color: "var(--aethos-warn)" }}> *</span> : <span> (optional)</span>}
          <input
            type={f.secret ? "password" : "text"}
            autoComplete="off"
            value={values[f.id] ?? ""}
            placeholder={f.placeholder || ""}
            onChange={(e) => setValues((v) => ({ ...v, [f.id]: e.target.value }))}
            style={inputStyle}
          />
          {f.help ? <span style={{ color: mcColors.textMuted, fontSize: 10 }}>{f.help}</span> : null}
        </label>
      ))}

      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button type="button" disabled={busy} onClick={() => void save()} style={buttonStyle}>
          {conn.configured ? "Update credentials" : "Connect"}
        </button>
        <span style={{ fontSize: 10, color: mcColors.textMuted }}>Stored in the encrypted vault · never shown again</span>
      </div>

      {webhookUrl ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 4 }}>
          <span style={{ fontSize: 11, color: "var(--aethos-text-dim)" }}>
            Webhook URL — paste into the provider&apos;s dashboard:
          </span>
          <div style={{ display: "flex", gap: 6 }}>
            <code
              style={{
                flex: 1,
                fontSize: 11,
                padding: "6px 8px",
                borderRadius: 6,
                background: "rgba(0,0,0,0.3)",
                color: "var(--aethos-text)",
                overflowX: "auto",
              }}
            >
              {webhookUrl}
            </code>
            <button
              type="button"
              style={{ ...buttonStyle, background: "transparent", color: "var(--aethos-text)" }}
              onClick={() => {
                void navigator.clipboard?.writeText(webhookUrl);
                setCopied(true);
                setTimeout(() => setCopied(false), 1500);
              }}
            >
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
        </div>
      ) : null}

      {error ? <p style={{ margin: 0, fontSize: 11, color: "var(--aethos-warn)" }} role="status">{error}</p> : null}
      {notice ? <p style={{ margin: 0, fontSize: 11, color: "var(--aethos-ok)" }} role="status">{notice}</p> : null}
    </div>
  );
}
