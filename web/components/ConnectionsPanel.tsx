"use client";

import { useCallback, useEffect, useState } from "react";

import { formatConnectionSaveError, isDevConnectionsDebug } from "@/lib/missionControl/connectionErrors";
import {
  fetchConnectionDiagnostics,
  fetchProviderConnection,
  methodLabel,
  providerCredentialsSaveUrl,
  revokeCredential,
  setPreferredAuth,
  storeProviderApiToken,
  testCredential,
  vaultReadyLabel,
  type ProviderConnection,
} from "@/lib/missionControl/connectionsApi";
import {
  resolveCredentialConfig,
  type ApiCredentialUi,
  type ProviderCredentialConfig,
} from "@/lib/missionControl/providerCredentialConfig";
import {
  mcButtonDangerStyle,
  mcButtonPrimaryStyle,
  mcButtonSecondaryStyle,
  mcColors,
  mcInputStyle,
} from "@/lib/missionControl/layout";

type Props = {
  provider: string;
  initial: ProviderConnection | null;
  credentialUi?: ApiCredentialUi | null;
  onChanged?: () => void;
  compact?: boolean;
};

type SaveState = "idle" | "saving" | "saved" | "failed";

export function ConnectionsPanel({ provider, initial, credentialUi, onChanged, compact = false }: Props) {
  const config: ProviderCredentialConfig | null = resolveCredentialConfig(provider, credentialUi);
  const [connection, setConnection] = useState<ProviderConnection | null>(initial);
  const [label, setLabel] = useState(config?.defaultCredLabel ?? `${provider} account`);
  const [token, setToken] = useState("");
  const [busy, setBusy] = useState("");
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [message, setMessage] = useState("");
  const [errorDebug, setErrorDebug] = useState("");
  const [vaultLabel, setVaultLabel] = useState("");

  useEffect(() => {
    setConnection(initial);
  }, [initial]);

  useEffect(() => {
    if (config?.defaultCredLabel) {
      setLabel(config.defaultCredLabel);
    }
  }, [config?.defaultCredLabel, provider]);

  useEffect(() => {
    void (async () => {
      try {
        const diag = await fetchConnectionDiagnostics();
        setVaultLabel(vaultReadyLabel(diag.credential_vault));
      } catch {
        setVaultLabel("Diagnostics unavailable");
      }
    })();
  }, [connection?.credentials?.length]);

  useEffect(() => {
    if (initial) return;
    void fetchProviderConnection(provider)
      .then(setConnection)
      .catch(() => undefined);
  }, [initial, provider]);

  const refresh = useCallback(async () => {
    const next = await fetchProviderConnection(provider);
    setConnection(next);
    if (next.credential_vault) {
      setVaultLabel(vaultReadyLabel(next.credential_vault));
    }
    onChanged?.();
  }, [onChanged, provider]);

  const onSaveToken = async () => {
    if (!token.trim() || saveState === "saving") return;
    setBusy("save");
    setSaveState("saving");
    setMessage("");
    setErrorDebug("");
    try {
      const out = await storeProviderApiToken(provider, { label, token: token.trim() });
      setToken("");
      setSaveState("saved");
      setMessage(
        out.test?.ok
          ? out.test?.detail || "Token saved — connection verified."
          : "Token saved — stored in vault. Connection test did not pass; you can retry Test.",
      );
      await refresh();
    } catch (e) {
      setSaveState("failed");
      const formatted = formatConnectionSaveError(e, { requestUrl: providerCredentialsSaveUrl(provider) });
      setMessage(formatted.message);
      if (isDevConnectionsDebug() && formatted.debug) {
        setErrorDebug(
          `Request URL: ${formatted.debug.requestUrl}\n` +
            `API base: ${formatted.debug.apiBase}\n` +
            (formatted.debug.httpStatus ? `HTTP status: ${formatted.debug.httpStatus}\n` : "") +
            (formatted.debug.errorCode ? `Error code: ${formatted.debug.errorCode}` : ""),
        );
      }
    } finally {
      setBusy("");
    }
  };

  const onTest = async (credentialId: string) => {
    setBusy(`test-${credentialId}`);
    setMessage("");
    try {
      const out = await testCredential(provider, credentialId);
      setMessage(out.test?.ok ? "Connection test passed." : out.test?.detail || "Connection test failed.");
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Test failed.");
    } finally {
      setBusy("");
    }
  };

  const onRevoke = async (credentialId: string) => {
    setBusy(`revoke-${credentialId}`);
    setMessage("");
    try {
      await revokeCredential(provider, credentialId);
      setMessage("Credential revoked.");
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Revoke failed.");
    } finally {
      setBusy("");
    }
  };

  const onPreferred = async (method: string) => {
    setBusy(`pref-${method}`);
    try {
      await setPreferredAuth(provider, method);
      await refresh();
    } finally {
      setBusy("");
    }
  };

  if (!config) {
    return null;
  }

  const methods = connection?.connected_methods;
  const creds = connection?.credentials ?? [];
  const saving = saveState === "saving" || busy === "save";
  const inputId = `${provider}-cred`;

  return (
    <section
      style={{
        padding: compact ? 0 : 16,
        borderRadius: compact ? 0 : 12,
        border: compact ? "none" : `1px solid ${mcColors.borderSubtle}`,
        background: compact ? "transparent" : "rgba(0,0,0,0.2)",
        marginBottom: compact ? 0 : 16,
      }}
    >
      {!compact && (
        <>
          <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>Connections</h2>
          <p style={{ margin: "0 0 12px", fontSize: 13, color: mcColors.textMuted }}>
            Provider credentials — secure local storage; add tokens here, not in chat.
          </p>
        </>
      )}

      {compact ? null : (
        <>
          <h3 style={{ margin: "0 0 8px", fontSize: 14, fontWeight: 600 }}>{config.label}</h3>
          <p style={{ margin: "0 0 8px", fontSize: 12, color: mcColors.textMuted, lineHeight: 1.5 }}>
            {config.description}
          </p>
        </>
      )}
      {!compact && (
        <p style={{ margin: "0 0 12px", fontSize: 12, color: mcColors.textMuted }}>
          Credential vault: {vaultLabel || "Checking…"}
        </p>
      )}
      {methods && (
        <dl style={{ margin: "0 0 12px", fontSize: 13, lineHeight: 1.7 }}>
          <dt style={{ color: "var(--aethos-text-muted)" }}>API token</dt>
          <dd style={{ margin: "0 0 6px" }}>{methodLabel(methods.api_token)}</dd>
          {config.supportsPreferredAuth ? (
            <>
              <dt style={{ color: "var(--aethos-text-muted)" }}>Browser session</dt>
              <dd style={{ margin: "0 0 6px" }}>{methodLabel(methods.browser_session)}</dd>
              <dt style={{ color: "var(--aethos-text-muted)" }}>CLI auth</dt>
              <dd style={{ margin: "0 0 6px" }}>{methodLabel(methods.cli_auth)}</dd>
              <dt style={{ color: "var(--aethos-text-muted)" }}>Preferred method</dt>
              <dd style={{ margin: "0 0 6px" }}>{connection?.preferred_method ?? "ask"}</dd>
            </>
          ) : null}
        </dl>
      )}

      {config.supportsPreferredAuth && (
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
          {(["api_token", "browser", "cli", "ask"] as const).map((m) => (
            <button
              key={m}
              type="button"
              disabled={Boolean(busy)}
              onClick={() => void onPreferred(m)}
              style={{
                ...(connection?.preferred_method === m ? mcButtonPrimaryStyle : mcButtonSecondaryStyle),
                padding: "6px 10px",
                fontSize: 12,
              }}
            >
              Prefer {m.replace(/_/g, " ")}
            </button>
          ))}
        </div>
      )}

      {creds.length > 0 && (
        <ul style={{ margin: "0 0 12px", paddingLeft: 18, fontSize: 13 }}>
          {creds.map((c) => (
            <li key={c.credential_id} style={{ marginBottom: 8 }}>
              <code>{c.masked_identifier || c.credential_id}</code> · {c.label}
              {c.last_test_ok === true ? " · verified" : c.last_test_ok === false ? " · test failed" : ""}
              <div style={{ marginTop: 6, display: "flex", gap: 8 }}>
                <button
                  type="button"
                  disabled={Boolean(busy)}
                  onClick={() => void onTest(c.credential_id)}
                  style={mcButtonSecondaryStyle}
                >
                  Test
                </button>
                <button
                  type="button"
                  disabled={Boolean(busy)}
                  onClick={() => void onRevoke(c.credential_id)}
                  style={mcButtonDangerStyle}
                >
                  Forget
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div style={{ marginTop: 8 }}>
        <p style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 600, color: "var(--aethos-text)" }}>Add API token</p>
        <label style={{ display: "block", fontSize: 12, color: "var(--aethos-text-muted)", marginBottom: 4 }} htmlFor={`${inputId}-label`}>
          Label
        </label>
        <input
          id={`${inputId}-label`}
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          placeholder={config.defaultCredLabel}
          style={{ ...mcInputStyle, marginBottom: 4 }}
        />
        <p style={{ margin: "0 0 8px", fontSize: 11, color: "var(--aethos-text-dim)" }}>
          Local name only — not your secret.
        </p>
        <label style={{ display: "block", fontSize: 12, color: "var(--aethos-text-muted)", marginBottom: 4 }} htmlFor={`${inputId}-token`}>
          {config.tokenFieldLabel}
        </label>
        <input
          id={`${inputId}-token`}
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder={config.tokenPlaceholder || "Paste token here"}
          autoComplete="off"
          style={{ ...mcInputStyle, marginBottom: 4 }}
        />
        <p style={{ margin: "0 0 8px", fontSize: 11, color: mcColors.textDim }}>{config.securityNote}</p>
        <button
          type="button"
          disabled={saving || !token.trim()}
          onClick={() => void onSaveToken()}
          style={mcButtonPrimaryStyle}
        >
          {saving ? "Saving…" : saveState === "failed" ? "Retry save" : "Save token"}
        </button>
      </div>

      {message ? (
        <p
          style={{ margin: "12px 0 0", fontSize: 12, color: saveState === "failed" ? "var(--aethos-warn)" : "var(--aethos-text-muted)" }}
          role="status"
        >
          {message}
        </p>
      ) : null}
      {errorDebug ? (
        <pre
          style={{
            margin: "8px 0 0",
            fontSize: 11,
            color: "var(--aethos-text-dim)",
            whiteSpace: "pre-wrap",
          }}
        >
          {errorDebug}
        </pre>
      ) : null}
    </section>
  );
}
