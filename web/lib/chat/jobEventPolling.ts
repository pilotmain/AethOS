/** Best-effort backoff for background job event polling — not chat failures. */

export const LIVE_UPDATES_DELAYED_MESSAGE =
  "Live updates delayed — open Mission Control for latest status.";

export function recordPollOutcome(
  consecutiveFailures: number,
  ok: boolean,
): { consecutiveFailures: number; showStatus: boolean } {
  if (ok) {
    return { consecutiveFailures: 0, showStatus: false };
  }
  const next = consecutiveFailures + 1;
  return { consecutiveFailures: next, showStatus: next >= 3 };
}

export function liveUpdatesDelayedMessage(): string {
  return LIVE_UPDATES_DELAYED_MESSAGE;
}
