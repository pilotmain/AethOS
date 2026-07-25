"use client";

import { Fragment, useCallback, useEffect, useState } from "react";

import {
  fetchCredentialCenter,
  fetchDeploymentEnvContext,
  hydrateCredentials,
  revalidateCredential,
  storeDeploymentEnvValues,
  type CredentialCenterProvider,
  type DeploymentEnvContext,
} from "@/lib/missionControl/credentialCenterApi";
import { formatMcPanelError } from "@/lib/missionControl/panelError";
import { mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

function statusColor(status: string): string {
  if (status === "validated") return "var(--aethos-ok)";
  if (status === "configured") return "var(--aethos-warn)";
  if (status === "reconnect_required") return "var(--aethos-warn)";
  if (status === "persistence_failed") return "var(--aethos-danger)";
  if (status === "missing") return "var(--aethos-text-dim)";
  return "var(--aethos-danger)";
}

function statusLabel(row: CredentialCenterProvider): string {
  return row.credential_state || row.status;
}

function canRevalidate(row: CredentialCenterProvider): boolean {
  if (!row.credential_id) return false;
  if (row.actions_allowed?.revalidate === false) return false;
  if (row.auth_source === "metadata_only") return false;
  if (row.credential_state === "reconnect_required" || row.credential_state === "persistence_failed") return false;
  return true;
}

function formatRelative(ts: number | null | undefined): string {
  if (!ts) return "—";
  const delta = Math.max(0, Math.floor(Date.now() / 1000 - ts));
  if (delta < 60) return `${delta}s ago`;
  if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
  if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
  return `${Math.floor(delta / 86400)}d ago`;
}

export function ProviderCredentialCenter() {
  const [providers, setProviders] = useState<CredentialCenterProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await fetchCredentialCenter();
      setProviders(data.providers ?? []);
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Credential center unavailable"));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const onHydrate = async () => {
    setBusy("hydrate");
    try {
      await hydrateCredentials();
      await load();
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Hydration failed"));
    } finally {
      setBusy("");
    }
  };

  const onRevalidate = async (provider: string, credentialId: string) => {
    setBusy(`${provider}-${credentialId}`);
    try {
      await revalidateCredential(provider, credentialId);
      await load();
    } catch (e) {
      setError(formatMcPanelError(e instanceof Error ? e.message : "Revalidation failed"));
    } finally {
      setBusy("");
    }
  };

  if (loading && providers.length === 0) {
    return <p style={{ color: "var(--aethos-text-muted)", fontSize: 13 }}>Loading credential center…</p>;
  }

  return (
    <section style={mcPanelSectionStyle}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "start", gap: 12 }}>
        <div>
          <h2 style={{ margin: "0 0 4px", fontSize: 18, fontWeight: 600 }}>Credential center</h2>
          <p style={{ margin: 0, fontSize: 13, color: mcColors.textMuted }}>
            Provider auth state after encrypted persistence — masked previews only, never raw tokens.
          </p>
        </div>
        <button
          type="button"
          disabled={busy === "hydrate"}
          onClick={() => void onHydrate()}
          style={{
            fontSize: 12,
            padding: "6px 10px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.15)",
            background: "rgba(255,255,255,0.06)",
            color: "var(--aethos-text)",
            cursor: busy ? "wait" : "pointer",
          }}
        >
          {busy === "hydrate" ? "Re-hydrating…" : "Re-hydrate all"}
        </button>
      </header>

      {error ? (
        <p style={{ color: "var(--aethos-warn)", fontSize: 13, marginTop: 10 }} role="status">
          {error}
        </p>
      ) : null}

      <table style={{ width: "100%", marginTop: 12, fontSize: 12, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ color: "var(--aethos-text-muted)", textAlign: "left" }}>
            <th style={{ padding: "6px 4px" }}>Provider</th>
            <th style={{ padding: "6px 4px" }}>Status</th>
            <th style={{ padding: "6px 4px" }}>Last validated</th>
            <th style={{ padding: "6px 4px" }}>Scope</th>
            <th style={{ padding: "6px 4px" }}>Preview</th>
            <th style={{ padding: "6px 4px" }} />
          </tr>
        </thead>
        <tbody>
          {providers.map((row) => (
            <Fragment key={row.provider}>
              <tr style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                <td style={{ padding: "8px 4px", fontWeight: 600, textTransform: "capitalize" }}>{row.provider}</td>
                <td style={{ padding: "8px 4px", color: statusColor(statusLabel(row)) }}>
                  {statusLabel(row)}
                  {row.auth_source && row.auth_source !== "encrypted_vault" ? (
                    <span style={{ display: "block", fontSize: 10, color: "var(--aethos-text-dim)" }}>auth: {row.auth_source}</span>
                  ) : null}
                  {row.failure_class ? (
                    <span style={{ display: "block", fontSize: 10, color: "var(--aethos-text-dim)" }}>{row.failure_class}</span>
                  ) : null}
                  {row.credential_state === "reconnect_required" || row.auth_source === "metadata_only" ? (
                    <span style={{ display: "block", fontSize: 10, color: "var(--aethos-warn)", marginTop: 2 }}>
                      Reconnect required — encrypted secret missing
                    </span>
                  ) : null}
                </td>
                <td style={{ padding: "8px 4px", color: "var(--aethos-text-muted)" }}>{formatRelative(row.last_validated_at)}</td>
                <td style={{ padding: "8px 4px", color: "var(--aethos-text-muted)" }}>{row.scope || "—"}</td>
                <td style={{ padding: "8px 4px", fontFamily: "monospace", color: "var(--aethos-text-dim)" }}>
                  {row.masked_preview || "—"}
                </td>
                <td style={{ padding: "8px 4px" }}>
                  {row.credential_id && canRevalidate(row) ? (
                    <button
                      type="button"
                      disabled={busy === `${row.provider}-${row.credential_id}`}
                      onClick={() => void onRevalidate(row.provider, row.credential_id!)}
                      style={{
                        fontSize: 11,
                        padding: "4px 8px",
                        borderRadius: 6,
                        border: "1px solid rgba(255,255,255,0.12)",
                        background: "transparent",
                        color: "var(--aethos-text)",
                        cursor: busy ? "wait" : "pointer",
                      }}
                    >
                      Revalidate
                    </button>
                  ) : row.actions_allowed?.reconnect ? (
                    <span style={{ fontSize: 10, color: "var(--aethos-warn)" }}>Reconnect in Connections</span>
                  ) : null}
                </td>
              </tr>
              {row.validation_diagnostics && Object.keys(row.validation_diagnostics).length > 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: "0 4px 10px", color: "var(--aethos-text-dim)", fontSize: 11 }}>
                    <details>
                      <summary style={{ cursor: "pointer" }}>Validation diagnostics</summary>
                      <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                        {row.validation_diagnostics.credential_id_tested ? (
                          <li>Credential: {String(row.validation_diagnostics.credential_id_tested)}</li>
                        ) : null}
                        {row.validation_diagnostics.auth_source ? (
                          <li>Auth source: {String(row.validation_diagnostics.auth_source)}</li>
                        ) : null}
                        {row.validation_diagnostics.endpoint ? (
                          <li>Endpoint: {String(row.validation_diagnostics.endpoint)}</li>
                        ) : null}
                        {row.validation_diagnostics.graphql_operation ? (
                          <li>GraphQL op: {String(row.validation_diagnostics.graphql_operation)}</li>
                        ) : null}
                        {row.validation_diagnostics.http_status != null ? (
                          <li>HTTP status: {String(row.validation_diagnostics.http_status)}</li>
                        ) : null}
                        {row.validation_diagnostics.readonly_inventory_ok != null ? (
                          <li>
                            Readonly inventory:{" "}
                            {row.validation_diagnostics.readonly_inventory_ok ? "ok" : "failed"}
                            {row.validation_diagnostics.readonly_inventory_service_count != null
                              ? ` (${String(row.validation_diagnostics.readonly_inventory_service_count)} services)`
                              : ""}
                          </li>
                        ) : null}
                        {Array.isArray(row.validation_diagnostics.graphql_errors) &&
                        row.validation_diagnostics.graphql_errors.length > 0 ? (
                          <li>GraphQL errors: {row.validation_diagnostics.graphql_errors.join("; ")}</li>
                        ) : null}
                        {row.validation_diagnostics.hydrated_at ? (
                          <li>Hydrated: {formatRelative(Number(row.validation_diagnostics.hydrated_at))}</li>
                        ) : null}
                      </ul>
                    </details>
                  </td>
                </tr>
              ) : null}
            </Fragment>
          ))}
        </tbody>
      </table>

      <DeploymentEnvValuesSection />
    </section>
  );
}

function DeploymentEnvValuesSection() {
  const [repo, setRepo] = useState("");
  const [project, setProject] = useState("pilotos");
  const [environment, setEnvironment] = useState("staging");
  const [serviceName, setServiceName] = useState("");
  const [requiredNames, setRequiredNames] = useState("");
  const [context, setContext] = useState<DeploymentEnvContext | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  const loadContext = async () => {
    setLoading(true);
    setMessage("");
    try {
      const names = requiredNames
        .split(/[,\n]/)
        .map((s) => s.trim())
        .filter(Boolean);
      const data = await fetchDeploymentEnvContext({
        repo,
        project,
        environment,
        service_name: serviceName,
        required_names: names,
      });
      setContext(data);
      const nextValues: Record<string, string> = {};
      for (const row of data.required ?? []) {
        if (!row.resolved) nextValues[row.name] = values[row.name] ?? "";
      }
      setValues(nextValues);
    } catch (e) {
      setMessage(formatMcPanelError(e instanceof Error ? e.message : "Failed to load deployment env context"));
    } finally {
      setLoading(false);
    }
  };

  const onSave = async () => {
    if (!context) return;
    const payload = Object.fromEntries(
      Object.entries(values).filter(([, v]) => String(v || "").trim()),
    );
    if (Object.keys(payload).length === 0) {
      setMessage("Enter at least one secret value to store.");
      return;
    }
    setSaving(true);
    setMessage("");
    try {
      const res = await storeDeploymentEnvValues({
        target_key: context.target_key,
        repo: context.repo,
        project: context.project,
        environment: context.environment,
        service_name: context.service_name,
        values: payload,
      });
      setMessage(
        `Stored ${res.count ?? 0} encrypted value(s): ${(res.registered_names ?? []).join(", ")}. Re-run the deploy in chat.`,
      );
      setValues({});
      await loadContext();
    } catch (e) {
      setMessage(formatMcPanelError(e instanceof Error ? e.message : "Failed to store deployment env values"));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ marginTop: 24, paddingTop: 16, borderTop: "1px solid rgba(255,255,255,0.08)" }}>
      <h3 style={{ margin: "0 0 6px", fontSize: 15, fontWeight: 600 }}>Deployment env values</h3>
      <p style={{ margin: "0 0 12px", fontSize: 13, color: mcColors.textMuted }}>
        Paste your app&apos;s secret env vars for a specific Railway deploy target. Values are encrypted and never shown
        again. Provider keys in Connections auto-resolve (e.g. Anthropic → <code>ANTHROPIC_API_KEY</code>).
      </p>
      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}>
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Repo
          <input
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="pilotmain/killit"
            style={{ width: "100%", marginTop: 4, padding: 6, borderRadius: 6, border: "1px solid rgba(255,255,255,0.12)" }}
          />
        </label>
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Project
          <input
            value={project}
            onChange={(e) => setProject(e.target.value)}
            style={{ width: "100%", marginTop: 4, padding: 6, borderRadius: 6, border: "1px solid rgba(255,255,255,0.12)" }}
          />
        </label>
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Environment
          <input
            value={environment}
            onChange={(e) => setEnvironment(e.target.value)}
            style={{ width: "100%", marginTop: 4, padding: 6, borderRadius: 6, border: "1px solid rgba(255,255,255,0.12)" }}
          />
        </label>
        <label style={{ fontSize: 11, color: mcColors.textMuted }}>
          Service name
          <input
            value={serviceName}
            onChange={(e) => setServiceName(e.target.value)}
            placeholder="killit-api"
            style={{ width: "100%", marginTop: 4, padding: 6, borderRadius: 6, border: "1px solid rgba(255,255,255,0.12)" }}
          />
        </label>
      </div>
      <label style={{ display: "block", marginTop: 10, fontSize: 11, color: mcColors.textMuted }}>
        Required var names (comma or newline — from deploy preflight)
        <textarea
          value={requiredNames}
          onChange={(e) => setRequiredNames(e.target.value)}
          rows={3}
          placeholder="STRIPE_SECRET_KEY, CRON_SECRET, …"
          style={{
            width: "100%",
            marginTop: 4,
            padding: 8,
            borderRadius: 6,
            border: "1px solid rgba(255,255,255,0.12)",
            fontFamily: "monospace",
            fontSize: 12,
          }}
        />
      </label>
      <button
        type="button"
        disabled={loading}
        onClick={() => void loadContext()}
        style={{
          marginTop: 10,
          fontSize: 12,
          padding: "6px 10px",
          borderRadius: 8,
          border: "1px solid rgba(255,255,255,0.15)",
          background: "rgba(255,255,255,0.06)",
          color: "var(--aethos-text)",
          cursor: loading ? "wait" : "pointer",
        }}
      >
        {loading ? "Loading…" : "Load required variables"}
      </button>

      {context ? (
        <div style={{ marginTop: 14 }}>
          <p style={{ fontSize: 12, color: mcColors.textMuted }}>
            Target <code>{context.target_key}</code> — resolved {context.resolved_count}, missing{" "}
            {context.missing_count}
          </p>
          <ul style={{ margin: "8px 0", paddingLeft: 0, listStyle: "none", fontSize: 12 }}>
            {(context.required ?? []).map((row) => (
              <li key={row.name} style={{ marginBottom: 10, padding: 8, borderRadius: 8, background: "rgba(255,255,255,0.03)" }}>
                <div style={{ fontWeight: 600 }}>
                  {row.name}{" "}
                  <span style={{ color: row.resolved ? "var(--aethos-ok)" : "var(--aethos-warn)" }}>
                    {row.resolved ? "resolved" : "missing"}
                  </span>
                  {row.resolution_source_label ? (
                    <span style={{ color: mcColors.textMuted, fontWeight: 400 }}> — {row.resolution_source_label}</span>
                  ) : null}
                </div>
                <div style={{ color: mcColors.textMuted, marginTop: 2 }}>{row.purpose}</div>
                {!row.resolved ? (
                  <input
                    type="password"
                    value={values[row.name] ?? ""}
                    onChange={(e) => setValues((prev) => ({ ...prev, [row.name]: e.target.value }))}
                    placeholder="Paste value (encrypted on save)"
                    style={{
                      width: "100%",
                      marginTop: 6,
                      padding: 6,
                      borderRadius: 6,
                      border: "1px solid rgba(255,255,255,0.12)",
                    }}
                  />
                ) : null}
              </li>
            ))}
          </ul>
          {context.missing_count > 0 ? (
            <button
              type="button"
              disabled={saving}
              onClick={() => void onSave()}
              style={{
                fontSize: 12,
                padding: "8px 12px",
                borderRadius: 8,
                border: "none",
                background: "var(--aethos-accent)",
                color: "#041016",
                fontWeight: 600,
                cursor: saving ? "wait" : "pointer",
              }}
            >
              {saving ? "Saving…" : "Save encrypted values"}
            </button>
          ) : (
            <p style={{ fontSize: 12, color: "var(--aethos-ok)" }}>All listed variables are resolved. Re-run deploy in chat.</p>
          )}
        </div>
      ) : null}

      {message ? (
        <p style={{ marginTop: 10, fontSize: 12, color: mcColors.textMuted }} role="status">{message}</p>
      ) : null}
    </div>
  );
}
