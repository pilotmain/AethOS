"use client";

import { useCallback, useEffect, useMemo, useState, type CSSProperties } from "react";

import { ConnectionsPanel } from "@/components/ConnectionsPanel";
import {
  fetchProviderConnection,
  type ProviderConnection,
} from "@/lib/missionControl/connectionsApi";
import {
  credentialManageableProviders,
  fetchConnectionsCatalog,
  providerHasStoredCredentials,
  type CatalogProviderEntry,
  type ConnectionsCatalogResponse,
} from "@/lib/missionControl/connectionsCatalog";
import {
  completeTenantOnboarding,
  fetchTenantOnboarding,
  setRuntimeFlag,
  type TenantOnboardingState,
} from "@/lib/onboarding/tenantSetup";

const cardShell: CSSProperties = {
  // The global app shell sets `body { height:100%; overflow:hidden }` for Mission
  // Control's internal scroll regions, which clips this taller setup card. Make the
  // wizard its OWN scroll container so the full form (and the Finish button) is
  // always reachable regardless of body overflow.
  height: "100dvh",
  overflowY: "auto",
  display: "flex",
  alignItems: "flex-start",
  justifyContent: "center",
  padding: "32px 24px",
  background: "var(--aethos-bg-deep)",
  color: "var(--aethos-text)",
};

const card: CSSProperties = {
  width: "100%",
  maxWidth: 640,
  background: "var(--aethos-surface-strong)",
  border: "1px solid var(--aethos-border)",
  borderRadius: 16,
  padding: "28px 26px",
  boxShadow: "0 24px 64px rgba(0,0,0,0.4)",
};

type Props = {
  onDone: () => void;
};

export function TenantSetupWizard({ onDone }: Props) {
  const [state, setState] = useState<TenantOnboardingState | null>(null);
  const [catalog, setCatalog] = useState<ConnectionsCatalogResponse | null>(null);
  const [provider, setProvider] = useState("anthropic");
  const [connections, setConnections] = useState<Record<string, ProviderConnection | null>>({});
  const [busy, setBusy] = useState(false);
  const [catalogError, setCatalogError] = useState("");

  const credentialProviders = useMemo(
    () => (catalog ? credentialManageableProviders(catalog) : []),
    [catalog],
  );

  const configuredProviders = useMemo(
    () => credentialProviders.filter(providerHasStoredCredentials),
    [credentialProviders],
  );

  const selectedEntry = useMemo(
    () => credentialProviders.find((p) => p.name === provider) ?? null,
    [credentialProviders, provider],
  );

  const loadCatalog = useCallback(async () => {
    try {
      const next = await fetchConnectionsCatalog();
      setCatalog(next);
      setCatalogError("");
      setProvider((current) => {
        const providers = credentialManageableProviders(next);
        if (providers.length > 0 && !providers.some((p) => p.name === current)) {
          return providers[0].name;
        }
        return current;
      });
    } catch (e) {
      setCatalogError(e instanceof Error ? e.message : "Failed to load provider registry");
    }
  }, []);

  const refresh = useCallback(async () => {
    const next = await fetchTenantOnboarding();
    if (next) setState(next);
    await loadCatalog();
    return next;
  }, [loadCatalog]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  // NOTE: do NOT auto-exit when the server marks onboarding complete. On hosted,
  // LLM reasoning is already on, so saving the FIRST key would flip `complete` and
  // kick the user straight into Mission Control before they could add a second
  // provider for the arbiter. The user leaves only by clicking Finish below.

  useEffect(() => {
    if (!provider) return;
    void fetchProviderConnection(provider)
      .then((conn) => setConnections((prev) => ({ ...prev, [provider]: conn })))
      .catch(() => undefined);
  }, [provider]);

  const steps = state?.steps ?? [];
  const progress = Math.round((state?.progress ?? 0) * 100);

  const onEnableLlm = async () => {
    setBusy(true);
    const ok = await setRuntimeFlag("USE_REAL_LLM", true);
    if (!ok) return;
    await refresh();
    setBusy(false);
  };

  const onFinish = async () => {
    setBusy(true);
    await completeTenantOnboarding();
    setBusy(false);
    onDone();
  };

  const credDone = steps.find((s) => s.id === "credentials")?.completed;
  const featuresDone = steps.find((s) => s.id === "features")?.completed;
  const canFinish = Boolean(credDone && featuresDone);

  const onCredentialChanged = () => {
    void fetchProviderConnection(provider)
      .then((conn) => setConnections((prev) => ({ ...prev, [provider]: conn })))
      .catch(() => undefined);
    void refresh();
  };

  return (
    <div style={cardShell}>
      <div style={card}>
        <div style={{ fontSize: 11, letterSpacing: "0.18em", fontWeight: 700, color: "var(--aethos-text-dim)" }}>
          AETHOS SETUP
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 700, margin: "8px 0 4px" }}>Bring your own keys</h1>
        <p style={{ fontSize: 13, color: "var(--aethos-text-muted)", margin: "0 0 16px" }}>
          Add provider credentials to your encrypted vault, enable intelligence, and run chat on your billing.
          Progress: {progress}%
        </p>
        {!credDone ? (
          <p style={{ fontSize: 12, color: "var(--aethos-warn)", margin: "0 0 12px" }}>
            Paste an API key below and click Save token — add as many providers as you need, then enable LLM
            reasoning to finish.
          </p>
        ) : null}

        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 15, margin: "0 0 8px" }}>1. Provider credentials</h2>
          <p style={{ fontSize: 12, color: "var(--aethos-text-muted)", margin: "0 0 10px" }}>
            Keys stay in the vault — same records as Mission Control → Connections. Add multiple providers for
            arbiter and failover.
          </p>

          {catalogError ? (
            <p style={{ fontSize: 12, color: "var(--aethos-warn)", marginBottom: 10 }}>{catalogError}</p>
          ) : null}

          {configuredProviders.length > 0 ? (
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: "var(--aethos-text-dim)", marginBottom: 6 }}>
                Configured in vault
              </div>
              <ul style={{ margin: 0, padding: 0, listStyle: "none", fontSize: 12 }}>
                {configuredProviders.map((p: CatalogProviderEntry) => (
                  <li key={p.name} style={{ marginBottom: 4, color: "var(--aethos-ok)" }}>
                    ✓ {p.label}
                    {(p.credentials_count ?? 0) > 1 ? ` (${p.credentials_count} key(s))` : ""}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          <label style={{ display: "block", fontSize: 12, color: "var(--aethos-text-muted)", marginBottom: 12 }}>
            Provider
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              disabled={credentialProviders.length === 0}
              style={{
                width: "100%",
                marginTop: 6,
                padding: "8px 10px",
                borderRadius: 8,
                border: "1px solid var(--aethos-border)",
                background: "var(--aethos-surface)",
                color: "var(--aethos-text)",
                fontSize: 13,
              }}
            >
              {credentialProviders.map((p) => (
                <option key={p.name} value={p.name}>
                  {p.label}
                  {providerHasStoredCredentials(p) ? " — configured" : ""}
                </option>
              ))}
            </select>
          </label>

          {selectedEntry ? (
            <ConnectionsPanel
              provider={selectedEntry.name}
              credentialUi={selectedEntry.credential_ui}
              initial={connections[selectedEntry.name] ?? null}
              compact
              onChanged={onCredentialChanged}
            />
          ) : (
            <p style={{ fontSize: 12, color: "var(--aethos-text-muted)" }}>Loading providers…</p>
          )}
        </section>

        <section style={{ marginBottom: 24 }}>
          <h2 style={{ fontSize: 15, margin: "0 0 8px" }}>2. Enable intelligence</h2>
          <p style={{ fontSize: 12, color: "var(--aethos-text-muted)", margin: "0 0 10px" }}>
            Turns on LLM reasoning for chat and the arbiter (billed to your provider account).
          </p>
          <button
            type="button"
            disabled={busy || featuresDone}
            onClick={() => void onEnableLlm()}
            style={{
              padding: "9px 14px",
              borderRadius: 10,
              border: "none",
              background: featuresDone ? "var(--aethos-border)" : "var(--aethos-accent)",
              color: featuresDone ? "var(--aethos-text-muted)" : "var(--aethos-bg)",
              fontWeight: 600,
              fontSize: 13,
              cursor: featuresDone ? "default" : "pointer",
            }}
          >
            {featuresDone ? "LLM reasoning enabled" : "Enable LLM reasoning"}
          </button>
        </section>

        <section
          style={{
            marginBottom: 24,
            padding: "12px 14px",
            borderRadius: 10,
            border: "1px solid var(--aethos-border)",
            background: "var(--aethos-surface)",
          }}
        >
          <h2 style={{ fontSize: 15, margin: "0 0 6px" }}>
            3. Multi-model arbiter{" "}
            {configuredProviders.length >= 2
              ? `(${configuredProviders.length} providers ready ✓)`
              : `(${configuredProviders.length}/2 providers)`}
          </h2>
          {configuredProviders.length >= 2 ? (
            <p style={{ fontSize: 12, color: "var(--aethos-text-muted)", margin: 0 }}>
              Ready. After you finish, ask in chat:{" "}
              <code style={{ color: "var(--aethos-text)" }}>arbiter: which database fits a local-first app?</code>{" "}
              (or start any message with <code style={{ color: "var(--aethos-text)" }}>compare models:</code>) and
              AethOS runs your question across providers and reconciles the answers.
            </p>
          ) : (
            <p style={{ fontSize: 12, color: "var(--aethos-text-muted)", margin: 0 }}>
              To compare models side by side, add a <strong>second</strong> provider above: save this key, then
              switch the <strong>Provider</strong> dropdown to another (e.g. OpenAI or Google) and save its key too.
              With 2+ providers you can run the arbiter from chat after login. One provider is enough to finish setup.
            </p>
          )}
        </section>

        <p style={{ fontSize: 12, color: "var(--aethos-text-muted)", margin: "0 0 10px" }}>
          Saving a key keeps you on this page — add as many providers as you want, then click below to
          continue. You won't be taken to Mission Control until you do.
        </p>
        <button
          type="button"
          disabled={!canFinish || busy}
          onClick={() => void onFinish()}
          style={{
            width: "100%",
            padding: "11px 14px",
            borderRadius: 10,
            border: "none",
            background: canFinish ? "var(--aethos-accent)" : "var(--aethos-border)",
            color: canFinish ? "var(--aethos-bg)" : "var(--aethos-text-muted)",
            fontSize: 14,
            fontWeight: 700,
            cursor: canFinish ? "pointer" : "not-allowed",
            opacity: busy ? 0.7 : 1,
          }}
        >
          {busy ? "Saving…" : "Finish & open Mission Control"}
        </button>
        {!canFinish ? (
          <p style={{ fontSize: 11, color: "var(--aethos-text-dim)", margin: "8px 0 0", textAlign: "center" }}>
            Save at least one provider key{featuresDone ? "" : " and enable LLM reasoning"} to continue.
          </p>
        ) : null}
      </div>
    </div>
  );
}
