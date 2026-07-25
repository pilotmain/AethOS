"use client";

import { useCallback, useEffect, useState } from "react";

import { mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";
import type { MissionControlView } from "@/lib/missionControl/views";
import {
  checkRbac,
  fetchConfigMigration,
  fetchObservabilityDashboard,
  fetchObservabilityMetering,
  fetchOrgsCurrent,
  fetchPlugins,
  fetchProductionCluster,
  fetchProductionEdge,
  fetchProductionTopology,
  fetchUpgradeStatus,
  rollbackUpgrade,
  runUpgrade,
} from "@/lib/missionControl/productionApi";

type Props = { view: MissionControlView };

const cardStyle = {
  padding: "12px 14px",
  marginBottom: 10,
  borderRadius: 10,
  border: `1px solid ${mcColors.borderSubtle}`,
  background: "rgba(0,0,0,0.2)",
  fontSize: 13,
} as const;

const titles: Record<string, string> = {
  "production-deployment": "Deployment Topology",
  "production-cluster": "Runtime Cluster",
  "production-orgs": "Organizations",
  "production-plugins": "Plugin Center",
  "production-observability": "Observability",
  "production-metering": "Usage & Metering",
  "production-upgrade": "Upgrade Center",
  "production-security": "Enterprise Security",
};

export function ProductionInfrastructurePanel({ view }: Props) {
  const [data, setData] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      setError(null);
      if (view === "production-deployment") setData(await fetchProductionTopology());
      else if (view === "production-cluster") setData(await fetchProductionCluster());
      else if (view === "production-orgs") setData(await fetchOrgsCurrent());
      else if (view === "production-plugins") setData(await fetchPlugins());
      else if (view === "production-observability") setData(await fetchObservabilityDashboard());
      else if (view === "production-metering") setData(await fetchObservabilityMetering());
      else if (view === "production-upgrade") setData(await fetchUpgradeStatus());
      else if (view === "production-security") {
        const [org, rbac] = await Promise.all([fetchOrgsCurrent(), checkRbac("approve_e3")]);
        setData({ org, rbac_check: rbac });
      } else {
        const [topo, edge] = await Promise.all([fetchProductionTopology(), fetchProductionEdge()]);
        setData({ topology: topo, edge });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load production state");
    }
  }, [view]);

  useEffect(() => {
    load();
  }, [load]);

  const onUpgrade = async () => {
    setBusy(true);
    try {
      await runUpgrade();
      await load();
    } finally {
      setBusy(false);
    }
  };

  const onRollback = async () => {
    setBusy(true);
    try {
      await rollbackUpgrade();
      await load();
    } finally {
      setBusy(false);
    }
  };

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 12 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 600 }}>{titles[view] ?? "Production Infrastructure"}</h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Deployable enterprise infrastructure — durable, isolated, observable.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {view === "production-upgrade" ? (
            <>
              <button type="button" disabled={busy} onClick={onUpgrade} style={mcButtonSecondaryStyle}>
                Run upgrade
              </button>
              <button type="button" disabled={busy} onClick={onRollback} style={mcButtonSecondaryStyle}>
                Rollback
              </button>
            </>
          ) : null}
          <button type="button" onClick={load} style={mcButtonSecondaryStyle}>
            Refresh
          </button>
        </div>
      </div>

      {error ? <p style={{ color: mcColors.amber, marginTop: 12, fontSize: 13 }}>{error}</p> : null}

      {data ? (
        <div style={{ marginTop: 16 }}>
          {view === "production-deployment" && (
            <div style={cardStyle}>
              <div style={{ fontWeight: 600 }}>
                Mode: {String(data.deployment_mode)} · Worker: {String(data.worker_mode)}
              </div>
              <div style={{ fontSize: 11, color: mcColors.textDim, marginTop: 6 }}>
                Services: {Object.keys((data.services as object) || {}).join(", ")}
              </div>
            </div>
          )}
          {view === "production-cluster" && (
            <div style={cardStyle}>
              Queue: {JSON.stringify((data.queue as object) || {})}
              <div style={{ marginTop: 6, fontSize: 11, color: mcColors.textMuted }}>
                Domains: {((data.scaling_domains as string[]) || []).join(", ")}
              </div>
            </div>
          )}
          {view === "production-orgs" && (
            <div style={cardStyle}>
              Org: {String((data.organization as { name?: string })?.name || "—")} · Role: {String(data.current_role)}
            </div>
          )}
          {view === "production-security" && (
            <div style={cardStyle}>
              RBAC E3 approve: {String((data.rbac_check as { allowed?: boolean })?.allowed)}
            </div>
          )}
          <pre style={{ ...cardStyle, whiteSpace: "pre-wrap", fontSize: 11, color: mcColors.textMuted, maxHeight: 480, overflow: "auto" }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      ) : null}

      {view === "production-upgrade" && !data ? null : view === "production-upgrade" ? (
        <button
          type="button"
          style={{ ...mcButtonSecondaryStyle, marginTop: 8, fontSize: 11 }}
          onClick={async () => setData(await fetchConfigMigration())}
        >
          Check .env migration
        </button>
      ) : null}
    </section>
  );
}
