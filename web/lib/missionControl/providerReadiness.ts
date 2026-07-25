/** Provider readiness card — pure helpers for Mission Control Settings. */

export type ProviderRequirement = {
  key: string;
  value: string;
  met: boolean;
};

export type ProviderReadiness = {
  full_reasoning: {
    status: string;
    ready: boolean;
    provider: string;
    model: string;
  };
  flags: {
    use_real_llm: boolean;
    anthropic_key_set: boolean;
    active_provider: string;
  };
  requirements: ProviderRequirement[];
  restart_required: boolean;
  deterministic_note: string;
  template_fallback_note: string;
  user_message: string;
  setup_steps: string[];
  configured: boolean;
};

export function providerStatusLabel(ready: boolean): string {
  return ready ? "Ready" : "Not configured";
}

export function providerStatusColor(ready: boolean): string {
  return ready ? "#86efac" : "#fbbf24";
}

export function formatRequirementLine(req: ProviderRequirement): string {
  const mark = req.met ? "✓" : "○";
  return `${mark} ${req.key} — ${req.value}`;
}

export function shouldShowTemplateFallbackNote(data: ProviderReadiness): boolean {
  return !data.full_reasoning.ready;
}

export function providerCardHeadline(data: ProviderReadiness): string {
  return `Full reasoning — ${providerStatusLabel(data.full_reasoning.ready)}`;
}
