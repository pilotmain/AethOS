"use client";

import { useCallback, useEffect, useState } from "react";

import { formatConnectionSaveError } from "@/lib/missionControl/connectionErrors";
import {
  fetchTelegramConnection,
  fetchTelegramStatus,
  registerTelegramProductionWebhook,
  registerTelegramWebhookLocal,
  revokeTelegramCredential,
  sendTelegramTestMessage,
  storeTelegramBotToken,
  telegramWebhookUrl,
  testTelegramCredential,
  tokenSourceLabel,
  type TelegramChannelStatus,
  type TelegramConnection,
} from "@/lib/missionControl/channelsApi";
import { fetchConnectionDiagnostics, vaultReadyLabel } from "@/lib/missionControl/connectionsApi";

type Props = {
  onChanged?: () => void;
};

export function TelegramConnectionsPanel({ onChanged }: Props) {
  const [connection, setConnection] = useState<TelegramConnection | null>(null);
  const [status, setStatus] = useState<TelegramChannelStatus | null>(null);
  const [label, setLabel] = useState("Telegram bot");
  const [token, setToken] = useState("");
  const [testChatId, setTestChatId] = useState("");
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");
  const [vaultLabel, setVaultLabel] = useState("");

  const refresh = useCallback(async () => {
    const [conn, st] = await Promise.all([fetchTelegramConnection(), fetchTelegramStatus()]);
    setConnection(conn);
    setStatus(st);
  }, []);

  useEffect(() => {
    void (async () => {
      try {
        const diag = await fetchConnectionDiagnostics();
        setVaultLabel(vaultReadyLabel(diag.credential_vault));
        await refresh();
      } catch {
        setVaultLabel("Diagnostics unavailable");
      }
    })();
  }, [refresh]);

  const onSave = async () => {
    if (!token.trim()) return;
    setBusy("save");
    setMessage("");
    try {
      const out = await storeTelegramBotToken({ label, token: token.trim() });
      setToken("");
      setMessage(
        out.test?.ok
          ? `Saved — ${out.test.detail ?? "bot verified."}`
          : "Saved — token stored. Connection test did not pass; retry Test.",
      );
      await refresh();
      onChanged?.();
    } catch (e) {
      setMessage(formatConnectionSaveError(e).message);
    } finally {
      setBusy("");
    }
  };

  const onTest = async (credentialId: string) => {
    setBusy(`test-${credentialId}`);
    setMessage("");
    try {
      const out = await testTelegramCredential(credentialId);
      setMessage(out.test?.ok ? out.test.detail ?? "Bot verified." : out.test?.detail ?? "Test failed.");
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
      await revokeTelegramCredential(credentialId);
      setMessage("Bot token revoked.");
      await refresh();
      onChanged?.();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Revoke failed.");
    } finally {
      setBusy("");
    }
  };

  const onRegisterProductionWebhook = async () => {
    setBusy("register-production-webhook");
    setMessage("");
    try {
      const out = await registerTelegramProductionWebhook();
      if (out.ok) {
        setMessage(
          `Production webhook verified at ${out.webhook_url ?? out.registered_webhook_url ?? "canonical URL"}.`,
        );
      } else {
        setMessage(out.detail || out.error || "Production webhook registration failed.");
      }
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Production webhook registration failed.");
    } finally {
      setBusy("");
    }
  };

  const onRegisterLocalWebhook = async () => {
    setBusy("register-local-webhook");
    setMessage("");
    try {
      const out = await registerTelegramWebhookLocal();
      if (out.ok) {
        setMessage(`Local dev webhook registered at ${out.webhook_url ?? "tunnel URL"}.`);
      } else {
        setMessage(out.detail || out.error || "Local webhook registration failed.");
      }
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Local webhook registration failed.");
    } finally {
      setBusy("");
    }
  };

  const onTestSend = async () => {
    if (!testChatId.trim()) return;
    setBusy("test-send");
    setMessage("");
    try {
      const out = await sendTelegramTestMessage({ chat_id: testChatId.trim() });
      setMessage(out.detail || "Test message sent.");
      await refresh();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Test send failed.");
    } finally {
      setBusy("");
    }
  };

  const creds = connection?.credentials ?? [];
  const sessions = status?.active_sessions ?? [];
  const canonicalWebhookUrl = status?.expected_webhook_url || telegramWebhookUrl();
  const registeredWebhookUrl = status?.webhook?.url;
  const webhookMismatch = Boolean(status?.webhook_mismatch);

  return (
    <section style={{ marginTop: 12, paddingTop: 12, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
      <h5 style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600 }}>Manage Telegram</h5>
      <p style={{ margin: "0 0 8px", fontSize: 12, color: "var(--aethos-text-dim)" }}>
        Credential vault: {vaultLabel || "Checking…"} · Token source: {tokenSourceLabel(status?.token_source)}
      </p>
      {status && !status.channel_gateway_enabled ? (
        <p style={{ margin: "0 0 8px", fontSize: 12, color: "var(--aethos-warn)" }}>
          The channel gateway is turned off for this deployment — ask AethOS in chat how to enable it so inbound
          Telegram updates are processed.
        </p>
      ) : null}

          {status ? (
        <dl style={{ margin: "0 0 10px", fontSize: 12, lineHeight: 1.6 }}>
          <dt style={{ color: "var(--aethos-text-dim)" }}>Inbound</dt>
          <dd style={{ margin: "0 0 6px" }}>
            Last received: {status.last_received_at ? new Date(status.last_received_at * 1000).toLocaleString() : "Never"}
          </dd>
          <dt style={{ color: "var(--aethos-text-dim)" }}>Outbound</dt>
          <dd style={{ margin: "0 0 6px" }}>
            Last sent: {status.last_sent_at ? new Date(status.last_sent_at * 1000).toLocaleString() : "Never"}
            {status.last_send_ok === false ? " · last send failed" : ""}
          </dd>
          <dt style={{ color: "var(--aethos-text-dim)" }}>Production webhook URL</dt>
          <dd style={{ margin: "0 0 6px", wordBreak: "break-all" }}>
            <code>{canonicalWebhookUrl}</code>{" "}
            <button
              type="button"
              disabled={Boolean(busy)}
              onClick={() => void navigator.clipboard.writeText(canonicalWebhookUrl)}
            >
              Copy
            </button>
            <button type="button" disabled={Boolean(busy)} onClick={() => void onRegisterProductionWebhook()}>
              Register production webhook
            </button>
          </dd>
          {registeredWebhookUrl ? (
            <>
              <dt style={{ color: "var(--aethos-text-dim)" }}>Registered webhook</dt>
              <dd style={{ margin: "0 0 6px", wordBreak: "break-all" }}>{registeredWebhookUrl}</dd>
            </>
          ) : null}
          {webhookMismatch ? (
            <p style={{ margin: "0 0 8px", fontSize: 12, color: "var(--aethos-warn)" }}>
              Registered webhook points elsewhere — re-register the production webhook so Telegram delivers to this
              deploy.
            </p>
          ) : null}
          <dt style={{ color: "var(--aethos-text-dim)" }}>Local dev (ngrok tunnel)</dt>
          <dd style={{ margin: "0 0 6px" }}>
            <button type="button" disabled={Boolean(busy)} onClick={() => void onRegisterLocalWebhook()}>
              Register local webhook (dev only)
            </button>
          </dd>
          {status.delivery_success_rate != null ? (
            <>
              <dt style={{ color: "var(--aethos-text-dim)" }}>Delivery success</dt>
              <dd style={{ margin: "0 0 6px" }}>{status.delivery_success_rate}%</dd>
            </>
          ) : null}
          {status.last_send_error ? (
            <>
              <dt style={{ color: "var(--aethos-text-dim)" }}>Last send error</dt>
              <dd style={{ margin: "0 0 6px", color: "var(--aethos-warn)" }}>{status.last_send_error}</dd>
            </>
          ) : null}
        </dl>
      ) : null}

      {creds.length > 0 && (
        <ul style={{ margin: "0 0 10px", paddingLeft: 18, fontSize: 12 }}>
          {creds.map((c) => (
            <li key={c.credential_id} style={{ marginBottom: 8 }}>
              <code>{c.masked_identifier || c.credential_id}</code> · {c.label}
              <div style={{ marginTop: 6, display: "flex", gap: 8 }}>
                <button type="button" disabled={Boolean(busy)} onClick={() => void onTest(c.credential_id)}>
                  Test bot
                </button>
                <button type="button" disabled={Boolean(busy)} onClick={() => void onRevoke(c.credential_id)}>
                  Revoke
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <div style={{ marginBottom: 10 }}>
        <label style={{ display: "block", fontSize: 12, color: "var(--aethos-text-muted)", marginBottom: 4 }} htmlFor="tg-bot-label">
          Label
        </label>
        <input
          id="tg-bot-label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          style={{ width: "100%", marginBottom: 6, padding: 8, borderRadius: 8 }}
        />
        <label style={{ display: "block", fontSize: 12, color: "var(--aethos-text-muted)", marginBottom: 4 }} htmlFor="tg-bot-token">
          Bot token
        </label>
        <input
          id="tg-bot-token"
          type="password"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          placeholder="Paste bot token from @BotFather"
          autoComplete="off"
          style={{ width: "100%", marginBottom: 6, padding: 8, borderRadius: 8 }}
        />
        <button type="button" disabled={busy === "save" || !token.trim()} onClick={() => void onSave()}>
          {busy === "save" ? "Saving…" : "Save bot token"}
        </button>
      </div>

      <div style={{ marginBottom: 10 }}>
        <label style={{ display: "block", fontSize: 12, color: "var(--aethos-text-muted)", marginBottom: 4 }} htmlFor="tg-test-chat">
          Test send — chat ID
        </label>
        <input
          id="tg-test-chat"
          value={testChatId}
          onChange={(e) => setTestChatId(e.target.value)}
          placeholder="Your Telegram chat id"
          style={{ width: "100%", marginBottom: 6, padding: 8, borderRadius: 8 }}
        />
        <button type="button" disabled={busy === "test-send" || !testChatId.trim()} onClick={() => void onTestSend()}>
          {busy === "test-send" ? "Sending…" : "Send test message"}
        </button>
      </div>

      {sessions.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 6 }}>Active Telegram chats</div>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 12, color: "var(--aethos-text-muted)" }}>
            {sessions.map((s) => (
              <li key={s.session_id} style={{ marginBottom: 6 }}>
                Session <code>{s.session_id}</code>
                {s.chat_id_masked ? ` · chat ${s.chat_id_masked}` : ""}
                {s.last_operation ? ` · ${s.last_operation}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {message ? (
        <p style={{ margin: "10px 0 0", fontSize: 12, color: "var(--aethos-text-muted)" }} role="status">
          {message}
        </p>
      ) : null}
    </section>
  );
}
