"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchToolPolicyMatrix } from "@/lib/missionControl/phase4Api";
import {
  approvePairing,
  fetchPairingStatus,
  revokePairing,
  type PairingStatus,
} from "@/lib/missionControl/channelsApi";
import {
  mcAlpha,
  mcButtonDangerStyle,
  mcButtonPrimaryStyle,
  mcButtonSecondaryStyle,
  mcColors,
  mcPanelSectionStyle,
} from "@/lib/missionControl/layout";

function PendingPairingsPanel() {
  const [status, setStatus] = useState<PairingStatus | null>(null);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    try {
      setStatus(await fetchPairingStatus());
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Could not load pairing status.");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onApprove = async (channel: string, code: string) => {
    setBusy(`approve-${channel}-${code}`);
    setMessage("");
    try {
      const out = await approvePairing({ channel, code });
      setMessage(out.ok ? `Paired ${out.external_user_id ?? ""} on ${channel}.` : out.error ?? "Approve failed.");
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Approve failed.");
    } finally {
      setBusy("");
    }
  };

  const onReject = async (channel: string, externalUserId: string) => {
    setBusy(`reject-${channel}-${externalUserId}`);
    setMessage("");
    try {
      await revokePairing({ channel, external_user_id: externalUserId });
      setMessage(`Rejected pairing request from ${externalUserId} on ${channel}.`);
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Reject failed.");
    } finally {
      setBusy("");
    }
  };

  const onRevoke = async (channel: string, externalUserId: string) => {
    setBusy(`revoke-${channel}-${externalUserId}`);
    setMessage("");
    try {
      await revokePairing({ channel, external_user_id: externalUserId });
      setMessage(`Revoked ${externalUserId} on ${channel}.`);
      await load();
    } catch (e) {
      setMessage(e instanceof Error ? e.message : "Revoke failed.");
    } finally {
      setBusy("");
    }
  };

  const pending = status?.pending ?? [];
  const allowed = status?.allowed ?? [];
  const pendingCount = status?.pending_count ?? pending.length;
  const dmPolicy = status?.channel_dm_policy ?? "pairing";

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Pending pairings</h2>
            {pendingCount > 0 ? (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  padding: "2px 9px",
                  borderRadius: 999,
                  color: mcColors.amber,
                  background: mcAlpha(mcColors.amber, 14),
                  border: `1px solid ${mcAlpha(mcColors.amber, 40)}`,
                }}
              >
                {pendingCount} waiting
              </span>
            ) : null}
          </div>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Approve unknown senders on external channels. DM policy: <strong>{dmPolicy}</strong>
            {status?.channel_gateway_enabled === false ? " · gateway off (no pairing enforced)" : ""}
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>

      <div style={{ marginTop: 14 }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600, color: mcColors.textMuted }}>
          Waiting for approval
        </h3>
        {pending.length === 0 ? (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textDim }}>
            Nobody waiting. When a new sender messages an external channel, their pairing request shows here.
          </p>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 8 }}>
            {pending.map((row) => {
              const key = `${row.channel}-${row.code}`;
              return (
                <li
                  key={key}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    gap: 12,
                    padding: "10px 12px",
                    borderRadius: 10,
                    border: `1px solid ${mcColors.borderSubtle}`,
                    background: mcColors.panelInset,
                    flexWrap: "wrap",
                  }}
                >
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 13, fontWeight: 600 }}>
                      {row.channel} · {row.external_user_id}
                      <code
                        style={{
                          marginLeft: 8,
                          fontSize: 12,
                          color: mcColors.cyan,
                          background: mcAlpha(mcColors.cyan, 10),
                          padding: "1px 7px",
                          borderRadius: 6,
                        }}
                      >
                        {row.code}
                      </code>
                    </div>
                    {row.preview ? (
                      <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 3 }}>“{row.preview}”</div>
                    ) : null}
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      type="button"
                      disabled={Boolean(busy)}
                      onClick={() => void onApprove(row.channel, row.code)}
                      style={mcButtonPrimaryStyle}
                    >
                      Approve
                    </button>
                    <button
                      type="button"
                      disabled={Boolean(busy)}
                      onClick={() => void onReject(row.channel, row.external_user_id)}
                      style={mcButtonSecondaryStyle}
                    >
                      Reject
                    </button>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>

      <div style={{ marginTop: 16 }}>
        <h3 style={{ margin: "0 0 8px", fontSize: 13, fontWeight: 600, color: mcColors.textMuted }}>
          Paired senders ({allowed.length})
        </h3>
        {allowed.length === 0 ? (
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textDim }}>No paired senders yet.</p>
        ) : (
          <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 6 }}>
            {allowed.map((row) => (
              <li
                key={`${row.channel}-${row.external_user_id}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  gap: 12,
                  padding: "8px 12px",
                  borderRadius: 10,
                  border: `1px solid ${mcColors.borderSubtle}`,
                  fontSize: 12,
                }}
              >
                <span>
                  {row.channel} · {row.external_user_id}
                  {row.paired_at ? (
                    <span style={{ color: mcColors.textDim }}> · paired {row.paired_at}</span>
                  ) : null}
                </span>
                <button
                  type="button"
                  disabled={Boolean(busy)}
                  onClick={() => void onRevoke(row.channel, row.external_user_id)}
                  style={mcButtonDangerStyle}
                >
                  Revoke
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {message ? (
        <p style={{ margin: "12px 0 0", fontSize: 12, color: mcColors.textMuted }} role="status">
          {message}
        </p>
      ) : null}
    </section>
  );
}

export function ChannelToolPolicyPanel() {
  const [matrix, setMatrix] = useState<Awaited<ReturnType<typeof fetchToolPolicyMatrix>>>(null);
  const [channel, setChannel] = useState("telegram");

  const load = useCallback(async () => {
    setMatrix(await fetchToolPolicyMatrix());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const row = (matrix?.channels ?? []).find((c) => (c as { channel?: string }).channel === channel) as
    | { channel?: string; restricted_channel?: boolean; tools?: { name: string; allowed: boolean }[] }
    | undefined;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <PendingPairingsPanel />
      <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Channel tool policy</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Channel allowlists — external channels block terminal/mutation preflights.
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>
      <div style={{ marginTop: 14, display: "flex", gap: 8, flexWrap: "wrap" }}>
        {["chat", "telegram", "slack", "discord", "mcp"].map((ch) => (
          <button
            key={ch}
            type="button"
            onClick={() => setChannel(ch)}
            style={{
              padding: "6px 12px",
              borderRadius: 999,
              border: `1px solid ${channel === ch ? mcColors.cyan : mcColors.borderSubtle}`,
              background: channel === ch ? mcAlpha(mcColors.cyan, 9) : "transparent",
              color: channel === ch ? mcColors.cyan : mcColors.textMuted,
              fontSize: 12,
              cursor: "pointer",
            }}
          >
            {ch}
          </button>
        ))}
      </div>
      {row ? (
        <div style={{ marginTop: 14 }}>
          <p style={{ fontSize: 12, color: row.restricted_channel ? mcColors.amber : mcColors.green }}>
            {row.restricted_channel ? "Restricted channel — mutation tools blocked" : "Full operator channel"}
          </p>
          <ul style={{ margin: "8px 0 0", padding: 0, listStyle: "none", fontSize: 11, maxHeight: 360, overflow: "auto" }}>
            {(row.tools ?? []).map((tool) => (
              <li key={tool.name} style={{ padding: "4px 0", color: tool.allowed ? mcColors.textMuted : mcColors.red }}>
                {tool.allowed ? "✓" : "✗"} {tool.name}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      </section>
    </div>
  );
}
