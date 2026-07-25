import {
  formatChecklistLine,
  providerCardHeadline,
  providerStatusColor,
  type ProviderSettingsViewModel,
} from "@/lib/settings/providerSettings";

type Props = {
  viewModel: ProviderSettingsViewModel;
};

export function ProviderSettingsCard({ viewModel: vm }: Props) {
  return (
    <section
      style={{
        padding: 16,
        borderRadius: 14,
        border: `1px solid ${
          vm.unavailable
            ? "rgba(255,255,255,0.12)"
            : vm.ready
              ? "rgba(34,211,238,0.25)"
              : "rgba(251,191,36,0.25)"
        }`,
        background: vm.unavailable
          ? "rgba(255,255,255,0.03)"
          : vm.ready
            ? "rgba(34,211,238,0.06)"
            : "rgba(251,191,36,0.06)",
        marginBottom: 16,
      }}
    >
      <h2 style={{ margin: "0 0 8px", fontSize: 16, fontWeight: 600 }}>{providerCardHeadline(vm)}</h2>
      <p style={{ margin: "0 0 12px", fontSize: 14, color: providerStatusColor(vm) }}>
        Status: {vm.statusLabel}
      </p>

      {!vm.unavailable && (
        <dl style={{ margin: 0, fontSize: 13, lineHeight: 1.7 }}>
          <dt style={{ color: "var(--aethos-text-muted)" }}>Provider</dt>
          <dd style={{ margin: "0 0 8px" }}>{vm.provider}</dd>
          <dt style={{ color: "var(--aethos-text-muted)" }}>Model</dt>
          <dd style={{ margin: "0 0 8px" }}>{vm.model}</dd>
          <dt style={{ color: "var(--aethos-text-muted)" }}>Real LLM</dt>
          <dd style={{ margin: "0 0 8px" }}>{vm.realLlm ? "Enabled" : "Disabled"}</dd>
          <dt style={{ color: "var(--aethos-text-muted)" }}>Anthropic key</dt>
          <dd style={{ margin: "0 0 8px" }}>{vm.anthropicKeyPresent ? "Present" : "Missing"}</dd>
        </dl>
      )}

      <p style={{ margin: "12px 0", fontSize: 13, lineHeight: 1.6 }}>{vm.userMessage}</p>

      {vm.showTemplateNotes && (
        <>
          <p style={{ margin: "0 0 8px", fontSize: 13, color: "var(--aethos-text-muted)" }}>{vm.deterministicNote}</p>
          <p style={{ margin: "0 0 12px", fontSize: 13, color: "var(--aethos-text-muted)" }}>{vm.templateFallbackNote}</p>
        </>
      )}

      {vm.checklist.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <p style={{ margin: "0 0 6px", fontSize: 12, fontWeight: 600, color: "var(--aethos-text)" }}>Required</p>
          <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, lineHeight: 1.7 }}>
            {vm.checklist.map((item) => (
              <li key={item.label}>{formatChecklistLine(item)}</li>
            ))}
          </ul>
        </div>
      )}

      {vm.restartRequired && !vm.unavailable && (
        <p style={{ margin: "12px 0 0", fontSize: 12, color: "var(--aethos-warn)" }}>
          Restart the API after updating `.env`.
        </p>
      )}
    </section>
  );
}
