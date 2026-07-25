"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchEmailConnection,
  revokeEmailCredential,
  storeEmailCredentials,
  testEmailCredential,
  type EmailConnection,
} from "@/lib/workspace/emailApi";
import { mcColors } from "@/lib/missionControl/layout";
import { formatMcPanelError } from "@/lib/missionControl/panelError";

type Props = {
  onChanged?: () => void;
  compact?: boolean;
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

export function EmailCredentialPanel({ onChanged, compact = false }: Props) {
  const [conn, setConn] = useState<EmailConnection | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [label, setLabel] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = useCallback(async () => {
    try {
      const next = await fetchEmailConnection();
      setConn(next);
      if (!label && next.schema?.default_label) setLabel(next.schema.default_label);
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Could not load email connection"));
    }
  }, [label]);

  useEffect(() => {
    void load();
  }, [load]);

  if (!conn?.schema) return null;

  const schema = conn.schema;

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
      const res = await storeEmailCredentials({ label: label.trim() || schema.label, fields: values });
      if (!res.ok) {
        setError(res.test?.detail || "Save failed");
        return;
      }
      setValues({});
      if (res.test?.ok) {
        setNotice("Connected and IMAP test passed.");
      } else if (res.test?.detail) {
        setNotice(`Saved — test failed: ${res.test.detail}`);
      } else {
        setNotice("Connected. Credentials stored in the encrypted vault.");
      }
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
      const res = await testEmailCredential(credentialId);
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
      await revokeEmailCredential(credentialId);
      setNotice("Credential revoked.");
      await load();
      onChanged?.();
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Revoke failed"));
    } finally {
      setBusy(false);
    }
  };

  const statusLabel = conn.configured ? "Connected" : "Not configured";
  const statusColor = conn.configured ? "var(--aethos-ok)" : mcColors.textMuted;

  return (
    <div
      style={{
        marginTop: compact ? 0 : 12,
        display: "flex",
        flexDirection: "column",
        gap: 8,
        padding: compact ? 0 : 14,
        borderRadius: compact ? 0 : 12,
        border: compact ? "none" : `1px solid ${mcColors.borderSubtle}`,
        background: compact ? "transparent" : "rgba(0,0,0,0.15)",
      }}
    >
      {!compact ? (
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 8 }}>
          <h2 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Connect inbox (IMAP)</h2>
          <span style={{ fontSize: 11, color: statusColor, fontWeight: 600 }}>{statusLabel}</span>
        </div>
      ) : null}

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
          {conn.configured ? "Update credentials" : "Connect inbox"}
        </button>
        <span style={{ fontSize: 10, color: mcColors.textMuted }}>Vault-encrypted · per account · never shown again</span>
      </div>

      {error ? <p style={{ margin: 0, fontSize: 11, color: "var(--aethos-warn)" }} role="status">{error}</p> : null}
      {notice ? <p style={{ margin: 0, fontSize: 11, color: "var(--aethos-ok)" }} role="status">{notice}</p> : null}
    </div>
  );
}
