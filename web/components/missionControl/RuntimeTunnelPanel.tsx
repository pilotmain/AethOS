"use client";

import { useCallback, useEffect, useState } from "react";

import {
  fetchTunnelStatus,
  restartTunnel,
  startTunnel,
  stopTunnel,
  type TunnelStatusResponse,
} from "@/lib/missionControl/engineeringApi";
import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

function formatTs(ts?: number) {
  if (!ts) return "—";
  return new Date(ts * 1000).toLocaleString();
}

export function RuntimeTunnelPanel() {
  const [data, setData] = useState<TunnelStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      setData(await fetchTunnelStatus());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load tunnel status");
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const action = async (fn: () => Promise<TunnelStatusResponse>) => {
    setBusy(true);
    try {
      setData(await fn());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Tunnel action failed");
    } finally {
      setBusy(false);
    }
  };

  const tunnel = data?.tunnel;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>Runtime Tunnel</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Managed ngrok tunnel for Telegram webhooks — disabled unless TELEGRAM_TUNNEL_ENABLED=true.
          </p>
        </div>
        <button type="button" onClick={load} style={mcButtonSecondaryStyle} disabled={busy}>
          Refresh
        </button>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      <div
        style={{
          marginTop: 16,
          padding: "12px 14px",
          borderRadius: 10,
          border: `1px solid ${mcColors.borderSubtle}`,
          background: "rgba(0,0,0,0.18)",
          fontSize: 13,
        }}
      >
        <div>
          <strong>Provider:</strong> {tunnel?.provider || "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Status:</strong> {tunnel?.status || "stopped"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Local port:</strong> {tunnel?.local_port ?? "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Public URL:</strong> {tunnel?.public_url || "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Webhook URL:</strong> {tunnel?.webhook_url || data?.telegram?.webhook?.url || "—"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Telegram webhook:</strong> {tunnel?.telegram_webhook_status || "unknown"}
        </div>
        <div style={{ marginTop: 6 }}>
          <strong>Last started:</strong> {formatTs(tunnel?.last_started_at)}
        </div>
        {tunnel?.last_error ? (
          <div style={{ marginTop: 6, color: mcColors.amber }}>
            <strong>Last error:</strong> {tunnel.last_error}
          </div>
        ) : null}
      </div>

      <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
        <button type="button" disabled={busy} onClick={() => action(startTunnel)} style={mcButtonSecondaryStyle}>
          Start
        </button>
        <button type="button" disabled={busy} onClick={() => action(stopTunnel)} style={mcButtonSecondaryStyle}>
          Stop
        </button>
        <button type="button" disabled={busy} onClick={() => action(restartTunnel)} style={mcButtonSecondaryStyle}>
          Restart
        </button>
      </div>
    </section>
  );
}
