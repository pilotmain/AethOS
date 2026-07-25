import type { ProviderCapability } from "@/lib/missionControl/providerCatalog";

type Props = {
  capabilities: Record<string, ProviderCapability>;
};

function capLabel(op: string): string {
  return op.replace(/_/g, " ");
}

function capBadge(cap: ProviderCapability): string {
  if (cap.mutation) return cap.enabled ? "Mutation" : "Unsupported";
  if (cap.read_only && cap.enabled) return "Read-only";
  return "Coming soon";
}

export function ProviderCapabilityGrid({ capabilities }: Props) {
  const entries = Object.entries(capabilities);
  if (entries.length === 0) {
    return <p style={{ margin: 0, fontSize: 12, color: "var(--aethos-text-dim)" }}>No capabilities registered.</p>;
  }
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
        gap: 8,
        marginTop: 8,
      }}
    >
      {entries.map(([op, cap]) => (
        <div
          key={op}
          style={{
            padding: "8px 10px",
            borderRadius: 8,
            border: "1px solid rgba(255,255,255,0.08)",
            background: "rgba(255,255,255,0.03)",
            fontSize: 11,
          }}
        >
          <div style={{ fontWeight: 600, color: "var(--aethos-text)", textTransform: "capitalize" }}>
            {capLabel(op)}
          </div>
          <div style={{ color: "var(--aethos-text-muted)", marginTop: 4 }}>{capBadge(cap)}</div>
        </div>
      ))}
    </div>
  );
}
