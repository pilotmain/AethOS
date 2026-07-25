import { describe, expect, it } from "vitest";

import {
  credentialManageableProviders,
  providerHasStoredCredentials,
  type ConnectionsCatalogResponse,
} from "@/lib/missionControl/connectionsCatalog";

function entry(
  name: string,
  label: string,
  opts: Partial<{
    manage: boolean;
    credentials_count: number;
    connection_state: string;
  }> = {},
): ConnectionsCatalogResponse["connected_providers"][number] {
  return {
    name,
    label,
    connected: (opts.credentials_count ?? 0) > 0,
    capabilities: {},
    mutations_enabled: false,
    credentials_count: opts.credentials_count ?? 0,
    connection_state: opts.connection_state ?? "setup_needed",
    credential_ui: opts.manage
      ? {
          manage_credentials: true,
          label,
          default_cred_label: `${label} account`,
          token_field_label: `${label} API key`,
          description: "",
          security_note: "",
          supports_preferred_auth: false,
          token_placeholder: "Paste key",
        }
      : undefined,
  };
}

describe("setup_provider_parity", () => {
  it("lists every credential-manageable provider from the connections catalog", () => {
    const catalog: ConnectionsCatalogResponse = {
      connected_providers: [
        entry("anthropic", "Anthropic", { manage: true }),
        entry("openai", "OpenAI", { manage: true }),
        entry("gemini", "Google Gemini", { manage: true }),
        entry("railway", "Railway", { manage: true }),
        entry("nokeys", "No Keys", { manage: false }),
      ],
      available_providers: [entry("mistral", "Mistral", { manage: true })],
      backend_ready_providers: [],
      connected_channels: [],
      available_channels: [],
    };
    const names = credentialManageableProviders(catalog).map((p) => p.name);
    expect(names).toEqual(["anthropic", "gemini", "mistral", "openai", "railway"]);
    expect(names).not.toContain("nokeys");
  });

  it("detects providers with stored vault credentials", () => {
    const configured = entry("openai", "OpenAI", { manage: true, credentials_count: 1 });
    const empty = entry("anthropic", "Anthropic", { manage: true });
    expect(providerHasStoredCredentials(configured)).toBe(true);
    expect(providerHasStoredCredentials(empty)).toBe(false);
  });
});
