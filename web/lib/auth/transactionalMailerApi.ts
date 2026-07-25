/** Operator transactional mailer diagnostics (signup verification email). */

import { apiBase } from "@/lib/api";

const creds = { credentials: "include" as const };

export type MailerTestResult = {
  ok: boolean;
  error?: string;
  detail?: string;
  hint?: string;
  provider?: string;
  status?: number;
};

export async function sendMailerTest(to: string): Promise<MailerTestResult> {
  const res = await fetch(`${apiBase()}/api/v1/aethos-identity/mailer-test`, {
    ...creds,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ to: to.trim() }),
  });
  const data = (await res.json()) as MailerTestResult & { error?: string };
  return {
    ok: Boolean(data.ok),
    error: data.error,
    detail: data.detail,
    hint: data.hint,
    provider: data.provider,
    status: data.status,
  };
}
