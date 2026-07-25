"use client";

import { useEffect, useState } from "react";

import { apiBase } from "@/lib/api";

type GovernanceDiagnostics = {
  local_fast_path_active?: boolean;
  aethos_solo_execution_mode?: boolean;
  aethos_solo_auto_approve?: boolean;
  aethos_solo_auto_approve_phases?: boolean;
  aethos_local_env_trusted?: boolean;
  mutation_execution_enabled?: boolean;
  railway_greenfield_mutation_kill_switch?: boolean;
};

export function GovernanceFastPathBanner() {
  const [diag, setDiag] = useState<GovernanceDiagnostics | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${apiBase()}/api/v1/runtime/snapshot`)
      .then((r) => (r.ok ? r.json() : null))
      .then((payload) => {
        if (!cancelled && payload?.governance_diagnostics) {
          setDiag(payload.governance_diagnostics as GovernanceDiagnostics);
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  if (!diag?.local_fast_path_active) {
    return null;
  }

  const flags = [
    diag.aethos_solo_execution_mode ? "solo" : null,
    diag.aethos_solo_auto_approve ? "auto-approve" : null,
    diag.aethos_solo_auto_approve_phases ? "phase-bundle" : null,
    diag.aethos_local_env_trusted ? "local-env-trusted" : null,
    diag.mutation_execution_enabled ? "mutations-on" : null,
    diag.railway_greenfield_mutation_kill_switch ? "kill-switch" : null,
  ].filter(Boolean);

  return (
    <div
      role="status"
      style={{
        margin: "0 0 12px",
        padding: "10px 14px",
        borderRadius: 10,
        border: "1px solid rgba(255, 180, 80, 0.45)",
        background: "rgba(255, 180, 80, 0.12)",
        color: "var(--aethos-warn)",
        fontSize: 13,
        lineHeight: 1.45,
      }}
    >
      <strong>LOCAL FAST PATH ACTIVE</strong>
      {flags.length ? ` — ${flags.join(" · ")}` : null}
    </div>
  );
}
