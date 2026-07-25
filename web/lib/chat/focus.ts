/** Polite chat input autofocus — only when Chat is active and safe. */

export function isEditableElement(el: Element | null): boolean {
  if (!el) return false;
  if (typeof document !== "undefined" && el === document.body) return false;
  const tag = el.tagName.toLowerCase();
  if (tag === "input" || tag === "textarea" || tag === "select") return true;
  const htmlEl = el as HTMLElement;
  return htmlEl.isContentEditable === true;
}

export function shouldAutoFocusChatInput(
  activeElement: Element | null = typeof document !== "undefined" ? document.activeElement : null,
  options?: { hasOpenDialog?: boolean },
): boolean {
  if (typeof document === "undefined") {
    if (options?.hasOpenDialog) return false;
    if (!activeElement || activeElement === null) return true;
    return !isEditableElement(activeElement);
  }
  if (options?.hasOpenDialog) return false;
  if (document.querySelector("[role='dialog'], dialog[open]")) return false;
  if (!activeElement || activeElement === document.body) return true;
  return !isEditableElement(activeElement);
}

export function isChatHomeRoute(pathname: string | null | undefined): boolean {
  return (pathname ?? "/") === "/";
}

export function focusChatInput(input: HTMLTextAreaElement | HTMLInputElement | null): void {
  if (!input || !shouldAutoFocusChatInput()) return;
  requestAnimationFrame(() => {
    if (shouldAutoFocusChatInput()) {
      input.focus();
    }
  });
}
