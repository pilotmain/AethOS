/** Provider credential onboarding copy and UI flags (Mission Control → Connections). */

export type ApiCredentialUi = {
  manage_credentials: boolean;
  label: string;
  default_cred_label: string;
  token_field_label: string;
  description: string;
  security_note: string;
  supports_preferred_auth: boolean;
  token_placeholder: string;
};

export type ProviderCredentialConfig = {
  label: string;
  defaultCredLabel: string;
  tokenFieldLabel: string;
  description: string;
  securityNote: string;
  supportsPreferredAuth: boolean;
  tokenPlaceholder: string;
};

export const PROVIDER_CREDENTIAL_CONFIG: Record<string, ProviderCredentialConfig> = {
  vercel: {
    label: "Vercel",
    defaultCredLabel: "Vercel primary account",
    tokenFieldLabel: "Vercel API token",
    description:
      "Connect Vercel with an API token or saved browser session for read-only inventory and operational checks.",
    securityNote: "Paste your Vercel API token here. It is stored in the encrypted vault and never shown again.",
    supportsPreferredAuth: true,
    tokenPlaceholder: "Paste token here",
  },
  railway: {
    label: "Railway",
    defaultCredLabel: "Railway primary account",
    tokenFieldLabel: "Railway API token",
    description:
      "Connect Railway with an API token so AethOS can run read-only inventory, deployment, logs, and diagnostics checks.",
    securityNote:
      "AethOS never displays saved tokens after storage. Token is stored in the encrypted credential vault.",
    supportsPreferredAuth: false,
    tokenPlaceholder: "Paste token here",
  },
  github: {
    label: "GitHub",
    defaultCredLabel: "GitHub primary account",
    tokenFieldLabel: "GitHub API token",
    description:
      "Connect GitHub with a personal access token for read-only repository and Actions diagnostics (when enabled).",
    securityNote:
      "AethOS never displays saved tokens after storage. Token is stored in the encrypted credential vault.",
    supportsPreferredAuth: false,
    tokenPlaceholder: "Paste token here",
  },
  anthropic: {
    label: "Anthropic",
    defaultCredLabel: "Anthropic account",
    tokenFieldLabel: "Anthropic API key",
    description: "Connect Anthropic for Claude model access — billed to your account.",
    securityNote: "Stored in the encrypted vault — never shown again after save.",
    supportsPreferredAuth: false,
    tokenPlaceholder: "sk-ant-…",
  },
  openai: {
    label: "OpenAI",
    defaultCredLabel: "OpenAI account",
    tokenFieldLabel: "OpenAI API key",
    description: "Connect OpenAI for GPT model access — billed to your account.",
    securityNote: "Stored in the encrypted vault — never shown again after save.",
    supportsPreferredAuth: false,
    tokenPlaceholder: "sk-…",
  },
  openrouter: {
    label: "OpenRouter",
    defaultCredLabel: "OpenRouter account",
    tokenFieldLabel: "OpenRouter API key",
    description: "Connect OpenRouter to route many models through one key.",
    securityNote: "Stored in the encrypted vault — never shown again after save.",
    supportsPreferredAuth: false,
    tokenPlaceholder: "sk-or-…",
  },
};

export function apiCredentialUiToConfig(ui: ApiCredentialUi): ProviderCredentialConfig {
  return {
    label: ui.label,
    defaultCredLabel: ui.default_cred_label,
    tokenFieldLabel: ui.token_field_label,
    description: ui.description,
    securityNote: ui.security_note,
    supportsPreferredAuth: ui.supports_preferred_auth,
    tokenPlaceholder: ui.token_placeholder,
  };
}

export function resolveCredentialConfig(
  provider: string,
  credentialUi?: ApiCredentialUi | null,
): ProviderCredentialConfig | null {
  if (credentialUi?.manage_credentials) {
    return apiCredentialUiToConfig(credentialUi);
  }
  return PROVIDER_CREDENTIAL_CONFIG[provider] ?? null;
}

export function providerSupportsCredentialManagement(credentialUi?: ApiCredentialUi | null): boolean {
  return Boolean(credentialUi?.manage_credentials);
}

/** @deprecated Prefer catalog `credential_ui.manage_credentials` from the backend registry. */
export const MANAGE_CREDENTIAL_PROVIDERS = Object.keys(PROVIDER_CREDENTIAL_CONFIG);

export function providerCredentialConfig(provider: string): ProviderCredentialConfig | null {
  return PROVIDER_CREDENTIAL_CONFIG[provider] ?? null;
}
