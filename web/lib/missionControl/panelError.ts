/** MC panel errors — must never use chat-degraded copy. */

export function formatMcPanelError(message: string): string {
  const m = (message || "").trim();
  if (/panel degraded/i.test(m)) {
    return "This panel could not load. Chat is unaffected — try again.";
  }
  return m || "Panel request failed.";
}

/** MC endpoint failure must not block chat send. */
export function mcFailureAffectsChat(_mcError: string | null): boolean {
  return false;
}
