"use client";

import type { ConnectionsCatalogResponse } from "@/lib/missionControl/connectionsCatalog";
import { connectionStateLabel, transportHealthLabel } from "@/lib/missionControl/connectionsCatalog";
import { methodLabel } from "@/lib/missionControl/connectionsApi";

import { ProviderHealthBadge } from "./ProviderHealthBadge";

type Props = {
  catalog: ConnectionsCatalogResponse | null;
};

function HealthRow({
  name,
  label,
  state,
  detail,
}: {
  name: string;
  label: string;
  state?: string;
  detail?: string;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "start",
        gap: 12,
        padding: "8px 0",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      <div>
        <div style={{ fontSize: 13, fontWeight: 600 }}>{label}</div>
        <div style={{ fontSize: 11, color: "var(--aethos-text-dim)", marginTop: 2 }}>{name}</div>
        {detail ? <div style={{ fontSize: 11, color: "var(--aethos-text-muted)", marginTop: 4 }}>{detail}</div> : null}
      </div>
      <ProviderHealthBadge state={state} />
    </div>
  );
}

export function ConnectionsHealthOverview({ catalog }: Props) {
  if (!catalog) {
    return <p style={{ color: "var(--aethos-text-muted)", fontSize: 13 }}>Loading operator overview…</p>;
  }

  const connectedProviders = catalog.connected_providers ?? [];
  const availableProviders = catalog.available_providers ?? [];
  const connectedChannels = catalog.connected_channels ?? [];
  const availableChannels = catalog.available_channels ?? [];
  const zeroConnections = connectedProviders.length === 0 && connectedChannels.length === 0;

  if (zeroConnections) {
    return (
      <section
        style={{
          marginBottom: 16,
          padding: 18,
          borderRadius: 12,
          border: "1px solid rgba(129,140,248,0.35)",
          background: "linear-gradient(135deg, rgba(99,102,241,0.12), rgba(15,23,42,0.4))",
        }}
      >
        <h2 style={{ margin: "0 0 6px", fontSize: 16, fontWeight: 600 }}>Connect your stack</h2>
        <p style={{ margin: "0 0 12px", fontSize: 13, color: "var(--aethos-text-dim)", lineHeight: 1.5 }}>
          Nothing is wired yet — that is normal for a fresh tenant. Open <strong>Settings → Connections</strong> to
          link Railway, GitHub, Vercel, or channels. Each card shows real status once credentials are saved; nothing here
          is a placeholder action.
        </p>
        <p style={{ margin: 0, fontSize: 12, color: "var(--aethos-text-muted)" }}>
          {availableProviders.length} providers and {availableChannels.length} channels are ready to connect.
        </p>
      </section>
    );
  }

  return (
    <section
      style={{
        marginBottom: 16,
        padding: 14,
        borderRadius: 12,
        border: "1px solid rgba(255,255,255,0.1)",
        background: "rgba(255,255,255,0.03)",
      }}
    >
      <h2 style={{ margin: "0 0 4px", fontSize: 15, fontWeight: 600 }}>Operator overview</h2>
      <p style={{ margin: "0 0 12px", fontSize: 12, color: "var(--aethos-text-dim)" }}>
        Provider and channel health at a glance — drill down in Settings → Connections.
      </p>

      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text)", marginBottom: 6 }}>
          Providers · {connectedProviders.length} connected · {availableProviders.length} available
        </div>
        {connectedProviders.map((p) => (
          <HealthRow
            key={p.name}
            name={p.name}
            label={p.label}
            state={p.connection_state}
            detail={`Auth ${methodLabel(p.connected_methods?.api_token ?? "missing")} · ${p.capability_summary?.readonly ?? 0} read-only enabled`}
          />
        ))}
        {availableProviders.map((p) => (
          <HealthRow
            key={p.name}
            name={p.name}
            label={p.label}
            state={p.connection_state ?? "coming_soon"}
            detail={connectionStateLabel(p.connection_state)}
          />
        ))}
      </div>

      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: "var(--aethos-text)", marginBottom: 6 }}>
          Channels · {connectedChannels.length} connected · {availableChannels.length} available
        </div>
        {connectedChannels.map((c) => (
          <HealthRow
            key={c.name}
            name={c.name}
            label={c.label}
            state={c.connection_state}
            detail={transportHealthLabel(c.transport_health)}
          />
        ))}
        {availableChannels.map((c) => (
          <HealthRow
            key={c.name}
            name={c.name}
            label={c.label}
            state={c.connection_state ?? "coming_soon"}
            detail={connectionStateLabel(c.connection_state)}
          />
        ))}
      </div>
    </section>
  );
}
