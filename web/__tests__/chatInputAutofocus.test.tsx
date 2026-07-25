import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it, vi } from "vitest";

import {
  focusChatInput,
  isChatHomeRoute,
  isEditableElement,
  shouldAutoFocusChatInput,
} from "@/lib/chat/focus";

describe("chatInputAutofocus", () => {
  it("ChatShell defines pathname from usePathname", () => {
    const src = readFileSync(join(__dirname, "../components/ChatShell.tsx"), "utf8");
    expect(src).toContain('import { usePathname } from "next/navigation"');
    expect(src).toMatch(/const pathname = usePathname\(\)/);
  });

  it("focuses on Chat home route", () => {
    expect(isChatHomeRoute("/")).toBe(true);
    expect(isChatHomeRoute(null)).toBe(true);
    expect(isChatHomeRoute(undefined)).toBe(true);
  });

  it("does not autofocus on Mission Control routes", () => {
    expect(isChatHomeRoute("/mission-control")).toBe(false);
    expect(isChatHomeRoute("/mission-control/jobs")).toBe(false);
  });

  it("focuses when active element is body-like", () => {
    expect(shouldAutoFocusChatInput({ tagName: "BODY" } as Element)).toBe(true);
  });

  it("does not steal focus from another textarea", () => {
    const el = { tagName: "TEXTAREA", isContentEditable: false } as HTMLTextAreaElement;
    expect(isEditableElement(el)).toBe(true);
    expect(shouldAutoFocusChatInput(el)).toBe(false);
  });

  it("focusChatInput schedules focus on textarea", () => {
    const calls: string[] = [];
    const input = {
      tagName: "TEXTAREA",
      isContentEditable: false,
      focus: () => calls.push("focus"),
    } as unknown as HTMLTextAreaElement;
    vi.stubGlobal(
      "requestAnimationFrame",
      (cb: FrameRequestCallback) => {
        cb(0);
        return 0;
      },
    );
    focusChatInput(input);
    expect(calls).toContain("focus");
  });
});
