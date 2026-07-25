import { methodLabel } from "@/lib/missionControl/connectionsApi";
import { mcColors } from "@/lib/missionControl/layout";

type Props = {
  preferredMethod?: string;
  connectedMethods?: Record<string, string>;
};

function chipColor(status: string): { color: string; bg: string; border: string } {
  const s = status.toLowerCase();
  if (s === "validated" || s === "configured" || s === "connected" || s === "detected" || s === "saved") {
    return { color: mcColors.green, bg: "rgba(74,222,128,0.1)", border: "rgba(74,222,128,0.25)" };
  }
  if (s === "missing" || s === "reconnect_required") {
    return { color: mcColors.amber, bg: "rgba(251,191,36,0.1)", border: "rgba(251,191,36,0.25)" };
  }
  if (s === "invalid" || s === "expired" || s === "failed") {
    return { color: mcColors.red, bg: "rgba(248,113,113,0.1)", border: "rgba(248,113,113,0.25)" };
  }
  return { color: mcColors.textMuted, bg: "rgba(255,255,255,0.04)", border: mcColors.borderSubtle };
}

function StatusChip({ label, status }: { label: string; status: string }) {
  const colors = chipColor(status);
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "4px 10px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        color: colors.color,
        background: colors.bg,
        border: `1px solid ${colors.border}`,
      }}
    >
      {label}: {methodLabel(status)}
    </span>
  );
}

export function ProviderAuthMethods({ preferredMethod, connectedMethods }: Props) {
  if (!connectedMethods) return null;
  const rows = [
    ["api_token", "API token"],
    ["browser_session", "Browser session"],
    ["cli_auth", "CLI auth"],
  ] as const;
  return (
    <div style={{ marginTop: 12, display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center" }}>
      {rows.map(([key, label]) => (
        <StatusChip key={key} label={label} status={connectedMethods[key] ?? "missing"} />
      ))}
      {preferredMethod ? (
        <span style={{ fontSize: 12, color: mcColors.textMuted, marginLeft: 4 }}>
          Preferred: <strong style={{ color: mcColors.text }}>{preferredMethod.replace(/_/g, " ")}</strong>
        </span>
      ) : null}
    </div>
  );
}
