/** Chat scroll helpers — auto-pin to latest unless user scrolled up. */

export const NEAR_BOTTOM_THRESHOLD_PX = 120;

export const CHAT_PINNED_BOTTOM_KEY = "aethos_chat_pinned_bottom";

export function isNearBottom(
  el: HTMLElement,
  threshold: number = NEAR_BOTTOM_THRESHOLD_PX,
): boolean {
  return el.scrollHeight - el.scrollTop - el.clientHeight < threshold;
}

/** Auto-scroll when the user is already at or near the bottom. */
export function shouldAutoScroll(el: HTMLElement | null, awayFromBottom: boolean): boolean {
  if (awayFromBottom) return false;
  if (!el) return true;
  return isNearBottom(el);
}

export function shouldShowJumpToLatest(
  el: HTMLElement | null,
  awayFromBottom: boolean,
  hasNewWhileAway: boolean,
): boolean {
  if (!hasNewWhileAway) return false;
  if (awayFromBottom) return true;
  if (!el) return false;
  return !isNearBottom(el);
}

export function readPinnedToBottom(): boolean {
  if (typeof window === "undefined") return true;
  try {
    return sessionStorage.getItem(CHAT_PINNED_BOTTOM_KEY) !== "0";
  } catch {
    return true;
  }
}

export function writePinnedToBottom(pinned: boolean): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(CHAT_PINNED_BOTTOM_KEY, pinned ? "1" : "0");
  } catch {
    /* quota */
  }
}
