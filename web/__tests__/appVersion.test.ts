import { describe, expect, it } from "vitest";

import {
  isClientBelowMinSupported,
  shouldPromptVersionReload,
} from "@/lib/pwa/appVersion";

describe("appVersion gate", () => {
  it("does not block git SHAs when min_supported is unset", () => {
    expect(isClientBelowMinSupported("f7952ea", "")).toBe(false);
    expect(isClientBelowMinSupported("83edde2", "")).toBe(false);
  });

  it("blocks leading-letter SHAs only when min_supported is explicitly set", () => {
    expect(isClientBelowMinSupported("f7952ea", "9fc0553")).toBe(true);
    expect(isClientBelowMinSupported("f7952ea", "f7952ea")).toBe(false);
  });

  it("does not nag dev builds against legacy server default", () => {
    expect(shouldPromptVersionReload("dev", "0.2.0")).toBe(false);
  });

  it("prompts when client and server builds differ", () => {
    expect(shouldPromptVersionReload("abc1234", "def5678")).toBe(true);
    expect(shouldPromptVersionReload("abc1234", "abc1234")).toBe(false);
  });
});
