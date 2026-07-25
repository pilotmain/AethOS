import type { CatalogChannelEntry } from "@/lib/missionControl/connectionsCatalog";
import {
  connectionStateLabel,
  formatActivityTimestamp,
  transportHealthLabel,
} from "@/lib/missionControl/connectionsCatalog";
import { tokenSourceLabel } from "@/lib/missionControl/channelsApi";

import { ChannelCredentialPanel } from "./ChannelCredentialPanel";
import { ProviderHealthBadge } from "./ProviderHealthBadge";
import { TelegramConnectionsPanel } from "./TelegramConnectionsPanel";

type Props = {
  channel: CatalogChannelEntry;
  onRefresh?: () => void;
};

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 12 }}>
      <span style={{ color: "var(--aethos-text-dim)" }}>{label}</span>
      <span style={{ color: "var(--aethos-text)", textAlign: "right" }}>{value}</span>
    </div>
  );
}

export function ChannelCard({ channel, onRefresh }: Props) {
  const isTelegram = channel.name === "telegram";

  return (
    <article
      style={{
        padding: 14,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 8, alignItems: "start" }}>
        <div>
          <h4 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>{channel.label}</h4>
          <p style={{ margin: "4px 0 0", fontSize: 11, color: "var(--aethos-text-dim)" }}>Channel · {channel.category}</p>
        </div>
        <ProviderHealthBadge state={channel.connection_state} />
      </div>

      {isTelegram ? (
        <div style={{ marginTop: 12, display: "flex", flexDirection: "column", gap: 6 }}>
          <DetailRow label="Enabled" value={channel.enabled ? "Yes" : "No"} />
          <DetailRow label="Token configured" value={channel.token_configured ? "Yes" : "No"} />
          <DetailRow label="Token source" value={tokenSourceLabel(channel.token_source)} />
          <DetailRow label="Transport" value={transportHealthLabel(channel.transport_health)} />
          {channel.webhook_path ? <DetailRow label="Webhook path" value={channel.webhook_path} /> : null}
          {channel.webhook?.url ? <DetailRow label="Webhook registered" value="Yes" /> : null}
          <DetailRow label="Last received" value={formatActivityTimestamp(channel.last_received_at)} />
          <DetailRow label="Last sent" value={formatActivityTimestamp(channel.last_sent_at)} />
          <DetailRow label="Active chats" value={String(channel.active_chats_count ?? 0)} />
          {channel.delivery_success_rate != null ? (
            <DetailRow label="Delivery success" value={`${channel.delivery_success_rate}%`} />
          ) : null}
          {channel.active_sessions && channel.active_sessions.length > 0 ? (
            <div style={{ marginTop: 6 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text)", marginBottom: 4 }}>
                Recent sessions
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 11, color: "var(--aethos-text-muted)" }}>
                {channel.active_sessions.slice(0, 5).map((s) => (
                  <li key={s.session_id}>
                    {s.session_id}
                    {s.last_operation ? ` · ${s.last_operation}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <TelegramConnectionsPanel onChanged={onRefresh} />
        </div>
      ) : (
        <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 4 }}>
          <p style={{ margin: 0, fontSize: 12, color: "var(--aethos-text-dim)" }}>
            {channel.configured
              ? "Connected — governed transport, same orchestration brain."
              : channel.host_requirement
                ? `${connectionStateLabel(channel.connection_state)} — ${channel.host_requirement}.`
                : `${connectionStateLabel(channel.connection_state)} — add credentials in Connections to enable this channel.`}
          </p>
          {channel.capabilities ? (
            <DetailRow
              label="Capabilities"
              value={[
                channel.capabilities.inbound ? "inbound" : null,
                channel.capabilities.outbound ? "outbound" : null,
              ]
                .filter(Boolean)
                .join(" · ") || "transport"}
            />
          ) : null}
          {channel.connection_state !== "unavailable_on_this_host" ? (
            <ChannelCredentialPanel channelId={channel.name} onChanged={onRefresh} />
          ) : null}
        </div>
      )}
    </article>
  );
}
