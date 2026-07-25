import { connectionStateLabel } from "@/lib/missionControl/connectionsCatalog";
import { mcAlpha } from "@/lib/missionControl/layout";

type Props = {
  state?: string;
};

export function ProviderHealthBadge({ state }: Props) {
  const label = connectionStateLabel(state);
  const color =
    state === "connected"
      ? "var(--aethos-ok)"
      : state === "partially_configured" || state === "setup_needed" || state === "ready"
        ? "var(--aethos-warn)"
        : state === "coming_soon" || state === "unavailable_on_this_host"
          ? "var(--aethos-text-dim)"
          : "var(--aethos-text-muted)";
  return (
    <span
      style={{
        display: "inline-block",
        padding: "2px 8px",
        borderRadius: 999,
        fontSize: 11,
        fontWeight: 600,
        color,
        border: `1px solid ${mcAlpha(color, 35)}`,
        background: mcAlpha(color, 12),
      }}
    >
      {label}
    </span>
  );
}
