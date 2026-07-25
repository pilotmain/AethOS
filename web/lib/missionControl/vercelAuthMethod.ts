/** Auth method labels for Vercel inventory jobs — matches backend copy. */

export type VercelJobParams = {
  auth_method?: string;
  auth_method_label?: string;
  credential_id?: string;
  profile_id?: string | null;
  browser_used?: boolean;
  provider_used?: string;
  project_count?: number;
};

export function vercelAuthMethodLabel(params: VercelJobParams | undefined): string {
  if (!params) return "Unknown";
  if (params.auth_method_label?.trim()) return params.auth_method_label.trim();
  const method = (params.auth_method || "").toLowerCase();
  if (method === "api_token") return "Vercel API token";
  if (method === "browser" || method === "browser_session") return "Saved browser session";
  if (method === "cli") return "Vercel CLI authentication";
  return params.auth_method || "Unknown";
}

export function vercelAuthRef(params: VercelJobParams | undefined): string | null {
  if (!params) return null;
  const method = (params.auth_method || "").toLowerCase();
  if (method === "api_token" && params.credential_id) return params.credential_id;
  if (params.profile_id) return String(params.profile_id);
  if (params.credential_id) return params.credential_id;
  return null;
}

export function vercelInspectionCompletionCopy(authMethod: string | undefined): string {
  const method = (authMethod || "").toLowerCase();
  if (method === "api_token") {
    return "Inspection used your saved Vercel API token (not browser automation or generative access).";
  }
  if (method === "browser" || method === "browser_session") {
    return "Inspection used your saved browser session (not generative access).";
  }
  if (method === "cli") {
    return "Inspection used Vercel CLI authentication (not generative access).";
  }
  return "Inspection completed (not generative access).";
}
