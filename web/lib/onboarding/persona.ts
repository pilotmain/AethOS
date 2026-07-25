import { apiBase } from "@/lib/api";

export type OperatorPersona = {
  name: string;
  timezone: string;
  work_start_hour: number | null;
  work_end_hour: number | null;
  tone: string;
  goals: string[];
  first_run_complete: boolean;
  updated_at: number | null;
};

export type PersonaState = {
  ok: boolean;
  login_enabled: boolean;
  login_required: boolean;
  onboarding_enabled: boolean;
  first_run: boolean;
  persona: OperatorPersona;
};

export const OPERATOR_TOKEN_KEY = "aethos_operator_token";

export async function fetchPersonaState(): Promise<PersonaState | null> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/onboarding/persona-state`, {
      headers: { Accept: "application/json" },
    });
    if (!res.ok) return null;
    return (await res.json()) as PersonaState;
  } catch {
    return null;
  }
}

export async function submitOperatorLogin(passphrase: string): Promise<{ ok: boolean; token?: string; error?: string }> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/onboarding/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({ passphrase }),
    });
    return (await res.json()) as { ok: boolean; token?: string; error?: string };
  } catch {
    return { ok: false, error: "network_error" };
  }
}

export async function saveOperatorPersona(
  persona: Partial<OperatorPersona>,
): Promise<{ ok: boolean; persona?: OperatorPersona }> {
  try {
    const res = await fetch(`${apiBase()}/api/v1/runtime/onboarding/persona`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(persona),
    });
    if (!res.ok) return { ok: false };
    return (await res.json()) as { ok: boolean; persona?: OperatorPersona };
  } catch {
    return { ok: false };
  }
}

export function readOperatorToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(OPERATOR_TOKEN_KEY);
}

export function writeOperatorToken(token: string | null): void {
  if (typeof window === "undefined") return;
  if (!token) {
    localStorage.removeItem(OPERATOR_TOKEN_KEY);
    return;
  }
  localStorage.setItem(OPERATOR_TOKEN_KEY, token);
}
