"use client";

import { useCallback, useEffect, useState } from "react";

import { fetchDeliveryStatus, fetchSandboxStatus, proposeSandboxProbe } from "@/lib/missionControl/phase4Api";
import { mcButtonPrimaryStyle, mcButtonSecondaryStyle, mcColors, mcPanelSectionStyle } from "@/lib/missionControl/layout";

export function GovernedSandboxPanel() {
  const [sandbox, setSandbox] = useState<Awaited<ReturnType<typeof fetchSandboxStatus>>>(null);
  const [delivery, setDelivery] = useState<Awaited<ReturnType<typeof fetchDeliveryStatus>>>(null);
  const [command, setCommand] = useState("");
  const [probeResult, setProbeResult] = useState<Record<string, unknown> | null>(null);

  const load = useCallback(async () => {
    setSandbox(await fetchSandboxStatus());
    setDelivery(await fetchDeliveryStatus());
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const probes = (sandbox?.allowed_readonly_probes as string[]) ?? [];

  return (
    <section style={mcPanelSectionStyle}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>Governed sandbox & delivery</h2>
          <p style={{ margin: "8px 0 0", fontSize: 13, color: mcColors.textMuted }}>
            Governed sandbox probes via terminal preflight · Phase 5 delivery lane status.
          </p>
        </div>
        <button type="button" onClick={() => void load()} style={mcButtonSecondaryStyle}>
          Refresh
        </button>
      </div>
      <div style={{ marginTop: 16, padding: 12, borderRadius: 12, border: `1px solid ${mcColors.borderSubtle}`, background: "rgba(0,0,0,0.2)" }}>
        <div style={{ fontWeight: 600, fontSize: 14 }}>Sandbox</div>
        <p style={{ fontSize: 12, color: mcColors.textMuted, margin: "6px 0" }}>
          {sandbox?.hint as string}
        </p>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 8 }}>
          {probes.map((cmd) => (
            <button key={cmd} type="button" style={mcButtonSecondaryStyle} onClick={() => setCommand(cmd)}>
              {cmd.slice(0, 40)}…
            </button>
          ))}
        </div>
        <input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          style={{ width: "100%", boxSizing: "border-box", padding: 8, borderRadius: 8, marginBottom: 8, fontSize: 12 }}
        />
        <button
          type="button"
          style={mcButtonPrimaryStyle}
          onClick={() => void proposeSandboxProbe(command).then(setProbeResult)}
        >
          Propose sandbox probe
        </button>
        {probeResult ? (
          <pre style={{ marginTop: 8, fontSize: 10, color: mcColors.textDim, overflow: "auto" }}>
            {JSON.stringify(probeResult, null, 2)}
          </pre>
        ) : null}
      </div>
      <div style={{ marginTop: 12, padding: 12, borderRadius: 12, border: `1px solid ${mcColors.borderSubtle}`, background: "rgba(0,0,0,0.2)" }}>
        <div style={{ fontWeight: 600, fontSize: 14 }}>Delivery lane (FIX 125+)</div>
        <p style={{ fontSize: 12, color: mcColors.textMuted, margin: "6px 0" }}>
          {(delivery?.hint as string) ?? "Load delivery status from API."}
        </p>
        <p style={{ fontSize: 11, color: mcColors.textDim }}>
          Enabled: {String((delivery?.config as { enabled?: boolean })?.enabled ?? "—")}
        </p>
      </div>
    </section>
  );
}
