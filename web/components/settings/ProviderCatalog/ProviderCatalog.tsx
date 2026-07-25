"use client";

import { useCallback, useEffect, useState } from "react";

import { ConnectionsPanel } from "@/components/ConnectionsPanel";
import { TransactionalMailerTestPanel } from "@/components/settings/TransactionalMailerTestPanel";
import { EmailCredentialPanel } from "@/components/workspace/EmailCredentialPanel";
import { fetchConnectionDiagnostics, vaultReadyLabel } from "@/lib/missionControl/connectionsApi";
import type { ProviderConnection } from "@/lib/missionControl/connectionsApi";
import {
  fetchConnectionsCatalog,
  type CatalogChannelEntry,
  type CatalogProviderEntry,
  type ConnectionsCatalogResponse,
} from "@/lib/missionControl/connectionsCatalog";
import { formatMcPanelError } from "@/lib/missionControl/panelError";
import { mcColors } from "@/lib/missionControl/layout";
import { providerSupportsCredentialManagement } from "@/lib/missionControl/providerCredentialConfig";

import { ChannelCard } from "./ChannelCard";
import { ProviderCard } from "./ProviderCard";

type Props = {
  providerConnections: Record<string, ProviderConnection | null>;
  onRefresh?: () => void;
  mode?: "full" | "channels";
  onNavigateView?: (viewId: string) => void;
};

// §3 — grouped Connections: one collapsible card per group (Model / Cloud /
// Channels / Services) so providers are fast to find. Reuses the existing
// per-provider connect/test/revoke flow underneath (ProviderCard + ConnectionsPanel).
function CollapsibleGroup({
  title,
  hint,
  count,
  defaultOpen,
  children,
}: {
  title: string;
  hint?: string;
  count: number;
  defaultOpen: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <section
      style={{
        marginBottom: 14,
        border: `1px solid ${mcColors.borderSubtle}`,
        borderRadius: 12,
        overflow: "hidden",
      }}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        style={{
          width: "100%",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "14px 16px",
          background: "rgba(0,0,0,0.2)",
          border: "none",
          cursor: "pointer",
          color: "var(--aethos-text)",
          textAlign: "left",
        }}
      >
        <span style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <span style={{ fontSize: 14, fontWeight: 600 }}>
            {title} <span style={{ color: mcColors.textDim, fontWeight: 400 }}>({count})</span>
          </span>
          {hint ? <span style={{ fontSize: 11, color: mcColors.textMuted }}>{hint}</span> : null}
        </span>
        <span style={{ fontSize: 18, color: mcColors.textMuted, lineHeight: 1 }}>{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <div style={{ display: "flex", flexDirection: "column", gap: 12, padding: 16 }}>{children}</div>
      ) : null}
    </section>
  );
}

type ProviderGroupId = "model" | "cloud" | "services";

function providerGroup(category: string | undefined): ProviderGroupId {
  if (category === "model") return "model";
  if (category === "cloud" || category === "code") return "cloud";
  return "services";
}

export function ProviderCatalog({ providerConnections, onRefresh, mode = "full", onNavigateView }: Props) {
  const [catalog, setCatalog] = useState<ConnectionsCatalogResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [vaultLabel, setVaultLabel] = useState("Ready");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setCatalog(await fetchConnectionsCatalog());
      try {
        const diag = await fetchConnectionDiagnostics();
        setVaultLabel(vaultReadyLabel(diag.credential_vault));
      } catch {
        setVaultLabel("Checking…");
      }
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Catalog load failed"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const refreshAll = useCallback(async () => {
    await load();
    onRefresh?.();
  }, [load, onRefresh]);

  if (loading && !catalog) {
    return <p style={{ color: "var(--aethos-text-muted)", fontSize: 13 }}>Loading connections catalog…</p>;
  }

  const connected = catalog?.connected_providers ?? [];
  const available = catalog?.available_providers ?? [];
  const backendReady = catalog?.backend_ready_providers ?? [];
  const connectedChannels = catalog?.connected_channels ?? [];
  const availableChannels = catalog?.available_channels ?? [];

  // §3 — merge every provider (connected first, so verified ones surface), dedupe
  // by name, then partition into the Model / Cloud / Services groups.
  const seenProviders = new Set<string>();
  const allProviders: CatalogProviderEntry[] = [...connected, ...backendReady, ...available].filter((p) => {
    if (seenProviders.has(p.name)) return false;
    seenProviders.add(p.name);
    return true;
  });
  const groupedProviders: Array<{
    id: ProviderGroupId;
    title: string;
    hint: string;
    defaultOpen: boolean;
    providers: CatalogProviderEntry[];
  }> = [
    {
      id: "model",
      title: "🧠 Model providers",
      hint: "OpenAI, Anthropic, Gemini, Mistral, Groq, xAI, DeepSeek, Cohere, Together, Fireworks, Perplexity, OpenRouter.",
      defaultOpen: true,
      providers: allProviders.filter((p) => providerGroup(p.category) === "model"),
    },
    {
      id: "cloud",
      title: "☁️ Cloud / deployment",
      hint: "Railway, Vercel, GitHub, Render, Fly, AWS, GCP, Cloudflare, Supabase, Netlify, …",
      defaultOpen: true,
      providers: allProviders.filter((p) => providerGroup(p.category) === "cloud"),
    },
    {
      id: "services",
      title: "🧩 Services",
      hint: "Stripe, Resend, Twilio, Datadog, Sentry, and other service integrations.",
      defaultOpen: false,
      providers: allProviders.filter((p) => providerGroup(p.category) === "services"),
    },
  ];

  return (
    <div style={{ marginBottom: 16, width: "100%" }}>
      <header style={{ marginBottom: 20 }}>
        <h2 style={{ margin: "0 0 6px", fontSize: 20, fontWeight: 600 }}>
          {mode === "channels" ? "Integrations" : "Provider inventory"}
        </h2>
        <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
          {mode === "channels"
            ? "Channel integrations — Telegram and transport connections."
            : "Provider and channel control center — capabilities from the backend registry."}
        </p>
      </header>

      {error ? (
        <p style={{ color: "var(--aethos-warn)", fontSize: 13 }} role="status">
          {error}
        </p>
      ) : null}

      {mode !== "channels" && groupedProviders.map((group) =>
        group.providers.length > 0 ? (
          <CollapsibleGroup
            key={group.id}
            title={group.title}
            hint={group.hint}
            count={group.providers.length}
            defaultOpen={group.defaultOpen}
          >
            {group.providers.map((p: CatalogProviderEntry) => (
              <ProviderCard
                key={p.name}
                provider={p}
                vaultLabel={vaultLabel}
                onOpenEngineeringView={onNavigateView}
                manageSlot={
                  providerSupportsCredentialManagement(p.credential_ui) ? (
                    <ConnectionsPanel
                      provider={p.name}
                      credentialUi={p.credential_ui}
                      initial={providerConnections[p.name] ?? null}
                      onChanged={() => void refreshAll()}
                      compact
                    />
                  ) : undefined
                }
              />
            ))}
          </CollapsibleGroup>
        ) : null,
      )}

      {(connectedChannels.length > 0 || availableChannels.length > 0) && (
        <CollapsibleGroup
          title="💬 Channels"
          hint="Telegram, Slack, Discord, Email, Teams, SMS, Voice — every registered transport, with honest status."
          count={connectedChannels.length + availableChannels.length}
          defaultOpen={mode === "channels"}
        >
          {connectedChannels.map((c: CatalogChannelEntry) => (
            <ChannelCard key={c.name} channel={c} onRefresh={() => void refreshAll()} />
          ))}
          {availableChannels.map((c) => (
            <ChannelCard key={c.name} channel={c} onRefresh={() => void refreshAll()} />
          ))}
        </CollapsibleGroup>
      )}

      {mode !== "channels" ? (
        <CollapsibleGroup
          title="📧 Email (IMAP/SMTP)"
          hint="Per-account inbox for Workspace → Email triage — vault-backed, not a shared global inbox."
          count={1}
          defaultOpen={false}
        >
          <div
            style={{
              padding: 14,
              borderRadius: 12,
              border: `1px solid ${mcColors.borderSubtle}`,
              background: "rgba(0,0,0,0.15)",
            }}
          >
            <EmailCredentialPanel compact />
          </div>
        </CollapsibleGroup>
      ) : null}

      {mode !== "channels" ? <TransactionalMailerTestPanel /> : null}
    </div>
  );
}
