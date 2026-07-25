"use client";

import type { ConnectionsCatalogResponse } from "@/lib/missionControl/connectionsCatalog";
import { mcAlpha, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";

type Props = {
  catalog: ConnectionsCatalogResponse | null;
  onNavigate: (view: MissionControlView) => void;
  pendingApprovals?: number;
};

function ActionCard({
  title,
  description,
  onClick,
  accent,
}: {
  title: string;
  description: string;
  onClick: () => void;
  accent?: string;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      style={{
        all: "unset",
        cursor: "pointer",
        display: "block",
        padding: "16px 18px",
        borderRadius: 14,
        border: `1px solid ${mcColors.borderSubtle}`,
        background: "rgba(0,0,0,0.22)",
        transition: "border-color 0.15s ease, background 0.15s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = accent ?? mcColors.cyan;
        e.currentTarget.style.background = mcAlpha(accent ?? mcColors.cyan, 5);
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = mcColors.borderSubtle;
        e.currentTarget.style.background = "rgba(0,0,0,0.22)";
      }}
    >
      <div style={{ fontSize: 15, fontWeight: 600, color: mcColors.text }}>{title}</div>
      <div style={{ fontSize: 13, color: mcColors.textMuted, marginTop: 6, lineHeight: 1.45 }}>{description}</div>
    </button>
  );
}

export function SimpleOverviewPanel({ catalog, onNavigate, pendingApprovals = 0 }: Props) {
  const connected = catalog?.connected_providers?.length ?? 0;
  const channels = catalog?.connected_channels?.length ?? 0;

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ marginBottom: 24 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>Home</h2>
        <p style={{ margin: "8px 0 0", fontSize: 14, color: mcColors.textMuted, maxWidth: 520 }}>
          Connect providers, run agents in chat, approve changes here. Everything else stays out of the way until you
          need it.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
          gap: 10,
          marginBottom: 24,
        }}
      >
        {[
          { label: "Providers", value: connected, hint: "connected" },
          { label: "Channels", value: channels, hint: "linked" },
          { label: "Approvals", value: pendingApprovals, hint: "pending" },
        ].map((stat) => (
          <div
            key={stat.label}
            style={{
              padding: "12px 14px",
              borderRadius: 12,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.18)",
            }}
          >
            <div style={{ fontSize: 22, fontWeight: 700, color: mcColors.text }}>{stat.value}</div>
            <div style={{ fontSize: 12, color: mcColors.textMuted, marginTop: 2 }}>
              {stat.label} {stat.hint}
            </div>
          </div>
        ))}
      </div>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: 12,
          marginBottom: 20,
        }}
      >
        <ActionCard
          title="Provider tokens"
          description="Add API keys for GitHub, Vercel, Railway, and the rest."
          onClick={() => onNavigate("provider-inventory")}
          accent={mcColors.green}
        />
        <ActionCard
          title="Research"
          description="Compare ideas with sources — saved wikis, not chat-only answers."
          onClick={() => onNavigate("deep-research")}
        />
        <ActionCard
          title="Agents"
          description="See who ran, copy session keys, follow orchestration threads."
          onClick={() => onNavigate("agent-orchestration")}
        />
        <ActionCard
          title="Approvals"
          description="Mutations and terminal jobs wait here until you approve."
          onClick={() => onNavigate("approval-inbox")}
          accent={pendingApprovals > 0 ? mcColors.amber : undefined}
        />
      </div>

      {connected === 0 ? (
        <div
          style={{
            padding: "14px 16px",
            borderRadius: 12,
            border: `1px dashed ${mcAlpha(mcColors.amber, 40)}`,
            background: mcAlpha(mcColors.amber, 4),
            fontSize: 13,
            color: mcColors.textMuted,
          }}
        >
          <strong style={{ color: mcColors.text }}>Start here:</strong> open{" "}
          <button
            type="button"
            onClick={() => onNavigate("provider-inventory")}
            style={{
              all: "unset",
              cursor: "pointer",
              color: mcColors.cyan,
              fontWeight: 600,
            }}
          >
            Provider tokens
          </button>{" "}
          and connect at least GitHub plus your deploy target (Vercel or Railway).
        </div>
      ) : null}
    </section>
  );
}
