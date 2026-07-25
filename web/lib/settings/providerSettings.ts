/** Normalize provider readiness API payloads — never crash on partial/legacy data. */

export type ProviderSettingsViewModel = {
  ready: boolean;
  statusLabel: string;
  provider: string;
  model: string;
  realLlm: boolean;
  anthropicKeyPresent: boolean;
  checklist: Array<{ label: string; ok: boolean }>;
  userMessage: string;
  deterministicNote: string;
  templateFallbackNote: string;
  restartRequired: boolean;
  showTemplateNotes: boolean;
  unavailable: boolean;
  raw: unknown;
};

const DEFAULT_MODEL = "claude-sonnet-4-6";

function unavailableViewModel(raw: unknown): ProviderSettingsViewModel {
  return {
    ready: false,
    statusLabel: "Unknown",
    provider: "—",
    model: "—",
    realLlm: false,
    anthropicKeyPresent: false,
    checklist: [],
    userMessage: "Provider settings are unavailable right now. Chat still works.",
    deterministicNote: "",
    templateFallbackNote: "",
    restartRequired: false,
    showTemplateNotes: false,
    unavailable: true,
    raw,
  };
}

function asRecord(input: unknown): Record<string, unknown> | null {
  if (!input || typeof input !== "object" || Array.isArray(input)) return null;
  return input as Record<string, unknown>;
}

function normalizeRequirements(
  reqs: unknown,
): Array<{ label: string; ok: boolean }> {
  if (!Array.isArray(reqs)) return [];
  return reqs
    .map((item) => {
      const r = asRecord(item);
      if (!r) return null;
      const key = String(r.key ?? "");
      const value = String(r.value ?? "");
      const ok = Boolean(r.met ?? r.ok);
      return { label: value ? `${key} — ${value}` : key, ok };
    })
    .filter((x): x is { label: string; ok: boolean } => Boolean(x?.label));
}

function fromFullReasoningShape(o: Record<string, unknown>): ProviderSettingsViewModel {
  const fr = asRecord(o.full_reasoning) ?? {};
  const flags = asRecord(o.flags) ?? {};
  const ready = Boolean(fr.ready ?? o.configured);
  const statusLabel = String(fr.status ?? (ready ? "Ready" : "Not configured"));
  const checklist = normalizeRequirements(o.requirements);
  const deterministicNote = String(
    o.deterministic_note ?? "AethOS will still answer deterministic capability and setup questions.",
  );
  const templateFallbackNote = String(
    o.template_fallback_note ??
      "Open-ended reasoning uses a helpful template fallback until the provider is enabled.",
  );

  return {
    ready,
    statusLabel,
    provider: String(fr.provider ?? o.active_provider ?? "Anthropic"),
    model: String(fr.model ?? o.model ?? DEFAULT_MODEL),
    realLlm: Boolean(flags.use_real_llm ?? o.use_real_llm),
    anthropicKeyPresent: Boolean(flags.anthropic_key_set ?? o.anthropic_key_set),
    checklist:
      checklist.length > 0
        ? checklist
        : [
            { label: "USE_REAL_LLM — true", ok: Boolean(flags.use_real_llm ?? o.use_real_llm) },
            {
              label: "ANTHROPIC_API_KEY — set in .env",
              ok: Boolean(flags.anthropic_key_set ?? o.anthropic_key_set),
            },
            { label: "API restart — after .env changes", ok: ready },
          ],
    userMessage: String(
      o.user_message ??
        (ready
          ? "Full reasoning is enabled. Provider-backed tracked jobs use the configured model."
          : "Full reasoning is not enabled. Capability questions still work without a provider."),
    ),
    deterministicNote,
    templateFallbackNote,
    restartRequired: Boolean(o.restart_required ?? !ready),
    showTemplateNotes: !ready,
    unavailable: false,
    raw: o,
  };
}

function fromLegacyProviderShape(o: Record<string, unknown>): ProviderSettingsViewModel {
  const ready = Boolean(o.configured);
  return {
    ready,
    statusLabel: ready ? "Ready" : "Not configured",
    provider: String(o.active_provider === "anthropic" || o.active_provider === "none" ? "Anthropic" : o.active_provider ?? "Anthropic"),
    model: String(o.model ?? DEFAULT_MODEL),
    realLlm: Boolean(o.use_real_llm),
    anthropicKeyPresent: Boolean(o.anthropic_key_set),
    checklist: [
      { label: "USE_REAL_LLM — true", ok: Boolean(o.use_real_llm) },
      { label: "ANTHROPIC_API_KEY — set in .env", ok: Boolean(o.anthropic_key_set) },
      { label: "API restart — after .env changes", ok: ready },
    ],
    userMessage: ready
      ? "Full reasoning is enabled."
      : "Full reasoning is not enabled. Capability and project-direction questions still work without a provider.",
    deterministicNote: "AethOS will still answer deterministic capability and setup questions.",
    templateFallbackNote:
      "Open-ended reasoning uses a helpful template fallback until the provider is enabled.",
    restartRequired: !ready,
    showTemplateNotes: !ready,
    unavailable: false,
    raw: o,
  };
}

function fromDeploymentSettings(o: Record<string, unknown>): ProviderSettingsViewModel {
  const ready = Boolean(o.provider_ready);
  return {
    ready,
    statusLabel: ready ? "Ready" : "Not configured",
    provider: String(o.active_provider ?? "Anthropic"),
    model: String(o.model ?? DEFAULT_MODEL),
    realLlm: Boolean(o.use_real_llm),
    anthropicKeyPresent: false,
    checklist: [
      { label: "USE_REAL_LLM — true", ok: Boolean(o.use_real_llm) },
      { label: "ANTHROPIC_API_KEY — set in .env", ok: false },
      { label: "API restart — after .env changes", ok: ready },
    ],
    userMessage:
      "Deployment settings were shown instead of provider readiness. Refresh or restart the API if this persists.",
    deterministicNote: "AethOS will still answer deterministic capability and setup questions.",
    templateFallbackNote:
      "Open-ended reasoning uses a helpful template fallback until the provider is enabled.",
    restartRequired: !ready,
    showTemplateNotes: !ready,
    unavailable: true,
    raw: o,
  };
}

/** Safe normalization for `/api/v1/settings/provider` and legacy/partial payloads. */
export function normalizeProviderSettings(input: unknown): ProviderSettingsViewModel {
  const o = asRecord(input);
  if (!o) return unavailableViewModel(input);

  if (o.full_reasoning != null) {
    return fromFullReasoningShape(o);
  }

  if ("configured" in o || ("use_real_llm" in o && !("response_mode" in o))) {
    return fromLegacyProviderShape(o);
  }

  if ("response_mode" in o && "provider_ready" in o) {
    return fromDeploymentSettings(o);
  }

  return unavailableViewModel(input);
}

export function providerCardHeadline(vm: ProviderSettingsViewModel): string {
  return `Full reasoning — ${vm.statusLabel}`;
}

export function providerStatusColor(vm: ProviderSettingsViewModel): string {
  if (vm.unavailable) return "#a1a1aa";
  return vm.ready ? "#86efac" : "#fbbf24";
}

export function formatChecklistLine(item: { label: string; ok: boolean }): string {
  return `${item.ok ? "✓" : "○"} ${item.label}`;
}
