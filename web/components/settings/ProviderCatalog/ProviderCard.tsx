"use client";

import { useState, type ReactNode } from "react";

import type { CatalogProviderEntry } from "@/lib/missionControl/connectionsCatalog";
import { categoryLabel } from "@/lib/missionControl/connectionsCatalog";
import { readonlyCapabilityCount } from "@/lib/missionControl/providerCatalog";
import { mcCardStyle, mcColors, mcButtonSecondaryStyle } from "@/lib/missionControl/layout";

import { ProviderAuthMethods } from "./ProviderAuthMethods";
import { ProviderCapabilityGrid } from "./ProviderCapabilityGrid";
import { ProviderHealthBadge } from "./ProviderHealthBadge";
import { ProviderModelSelector } from "./ProviderModelSelector";

type Props = {
  provider: CatalogProviderEntry;
  manageSlot?: ReactNode;
  vaultLabel?: string;
  onOpenEngineeringView?: (viewId: string) => void;
};

// Provider avatar accents. Most map to the shared token palette; the two
// purple/blue brand hues have no token equivalent and stay as literal rgb()
// (external brand identities, intentionally outside the design-token system).
const PROVIDER_AVATAR: Record<string, string> = {
  github: "var(--aethos-text)",
  railway: "rgb(167, 139, 250)",
  vercel: "var(--aethos-text)",
  aws: "var(--aethos-warn)",
  gcp: "rgb(96, 165, 250)",
  cloudflare: "var(--aethos-warn)",
};

function ProviderAvatar({ name }: { name: string }) {
  const color = PROVIDER_AVATAR[name] ?? mcColors.cyan;
  return (
    <div
      style={{
        width: 40,
        height: 40,
        borderRadius: 12,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        fontWeight: 700,
        fontSize: 16,
        color: "var(--aethos-bg)",
        background: color,
        flexShrink: 0,
      }}
    >
      {name.slice(0, 1).toUpperCase()}
    </div>
  );
}

export function ProviderCard({ provider, manageSlot, vaultLabel, onOpenEngineeringView }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [credentialsOpen, setCredentialsOpen] = useState(false);
  const summary = provider.capability_summary;
  const readonlyCount = readonlyCapabilityCount(provider);
  const isModelProvider = provider.category === "model";
  const isConnectedModelProvider =
    provider.category === "model" && provider.connection_state === "connected";

  return (
    <article
      style={{
        ...mcCardStyle,
        padding: "20px 22px",
        width: "100%",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "start" }}>
        <div style={{ display: "flex", gap: 14, alignItems: "start", flex: 1 }}>
          <ProviderAvatar name={provider.name} />
          <div style={{ flex: 1 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}>
              <h3 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{provider.label}</h3>
              <ProviderHealthBadge state={provider.connection_state} />
            </div>
            <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textDim }}>
              {categoryLabel(provider.category)} · {provider.name}
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
          style={{
            ...mcButtonSecondaryStyle,
            padding: "6px 10px",
            fontSize: 12,
          }}
        >
          {expanded ? "▾" : "▸"}
        </button>
      </div>

      <div
        style={{
          marginTop: 14,
          display: "flex",
          flexWrap: "wrap",
          gap: 16,
          fontSize: 13,
          color: mcColors.textMuted,
        }}
      >
        <span>
          Read-only ops: <strong style={{ color: mcColors.text }}>{readonlyCount}</strong>
        </span>
        {summary ? (
          <span>
            Mutations: <strong style={{ color: mcColors.text }}>{summary.mutation}</strong>{" "}
            <span style={{ color: mcColors.textDim }}>(disabled)</span>
          </span>
        ) : null}
        <span>
          {provider.mutations_enabled ? (
            <span style={{ color: mcColors.green }}>Mutation layer enabled</span>
          ) : (
            "Read-only execution enabled · mutations deferred"
          )}
        </span>
      </div>

      <ProviderAuthMethods
        preferredMethod={provider.preferred_method}
        connectedMethods={provider.connected_methods}
      />

      {manageSlot ? (
        <div
          style={{
            marginTop: 16,
            paddingTop: 14,
            borderTop: `1px solid ${mcColors.borderSubtle}`,
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 12 }}>
            <div style={{ fontSize: 13, color: mcColors.textMuted }}>
              Credential vault:{" "}
              <span style={{ color: mcColors.text }}>{vaultLabel || "Ready"}</span>
            </div>
            <button
              type="button"
              onClick={() => setCredentialsOpen((v) => !v)}
              style={mcButtonSecondaryStyle}
            >
              {credentialsOpen ? "Hide credentials" : "Manage credentials"}
            </button>
          </div>
          {credentialsOpen ? <div style={{ marginTop: 14 }}>{manageSlot}</div> : null}
        </div>
      ) : null}

      {isModelProvider ? (
        <div
          style={{
            marginTop: 16,
            paddingTop: 14,
            borderTop: `1px solid ${mcColors.borderSubtle}`,
          }}
        >
          {!isConnectedModelProvider ? (
            <p style={{ margin: "0 0 10px", fontSize: 11, color: mcColors.textMuted }}>
              Add an API key above to unlock this provider&apos;s models — all flagship models
              enable by default; you can deselect any you don&apos;t want.
            </p>
          ) : null}
          <ProviderModelSelector provider={provider.name} previewOnly={!isConnectedModelProvider} />
        </div>
      ) : null}

      {expanded ? (
        <details open style={{ marginTop: 14 }}>
          <summary style={{ cursor: "pointer", fontSize: 13, color: mcColors.textMuted, fontWeight: 600 }}>
            Capabilities
          </summary>
          <ProviderCapabilityGrid capabilities={provider.capabilities} />
        </details>
      ) : null}

      {provider.connection_state === "coming_soon" ? (
        <p style={{ margin: "12px 0 0", fontSize: 12, color: mcColors.textDim }}>
          Coming soon — registry slot reserved.
        </p>
      ) : null}

      {provider.connection_state === "backend_ready" ? (
        <div style={{ marginTop: 14, display: "flex", flexWrap: "wrap", gap: 10, alignItems: "center" }}>
          <p style={{ margin: 0, fontSize: 12, color: mcColors.textMuted, flex: 1 }}>
            Backend ready — register workspaces and run readonly analysis in Engineering.
          </p>
          {onOpenEngineeringView && (provider as CatalogProviderEntry & { engineering_view?: string }).engineering_view ? (
            <button
              type="button"
              style={mcButtonSecondaryStyle}
              onClick={() =>
                onOpenEngineeringView(
                  String((provider as CatalogProviderEntry & { engineering_view?: string }).engineering_view)
                )
              }
            >
              Open Local Workspaces
            </button>
          ) : null}
        </div>
      ) : null}
    </article>
  );
}
