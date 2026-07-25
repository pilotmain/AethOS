import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  applyAuthSessionAfterLogin,
  applyAuthSessionOnLoad,
  clearUserScopedClientState,
} from "@/lib/auth/clientState";
import { getActiveUserScope, setActiveUserScope } from "@/lib/auth/userScope";
import {
  createChatThread,
  listChatThreads,
} from "@/lib/chat/chatThreads";
import type { AuthSessionState } from "@/lib/onboarding/tenantSetup";

function mockBrowserStorage() {
  const store: Record<string, string> = {};
  vi.stubGlobal("localStorage", {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    key: (index: number) => Object.keys(store)[index] ?? null,
    get length() {
      return Object.keys(store).length;
    },
  });
  vi.stubGlobal("sessionStorage", {
    getItem: (key: string) => store[`ss:${key}`] ?? null,
    setItem: (key: string, value: string) => {
      store[`ss:${key}`] = value;
    },
    removeItem: (key: string) => {
      delete store[`ss:${key}`];
    },
    key: (index: number) => {
      const keys = Object.keys(store).filter((k) => k.startsWith("ss:"));
      return keys[index]?.slice(3) ?? null;
    },
    get length() {
      return Object.keys(store).filter((k) => k.startsWith("ss:")).length;
    },
  });
  return store;
}

const userA: AuthSessionState = {
  authenticated: true,
  auth_enabled: true,
  self_signup_enabled: true,
  multi_tenant_enabled: true,
  user: { email: "user-a@example.com", roles: ["operator"] },
};

const userB: AuthSessionState = {
  authenticated: true,
  auth_enabled: true,
  self_signup_enabled: true,
  multi_tenant_enabled: true,
  user: { email: "user-b@example.com", roles: ["operator"] },
};

describe("client auth isolation", () => {
  beforeEach(() => {
    vi.stubGlobal("window", globalThis);
    mockBrowserStorage();
    setActiveUserScope("anonymous");
  });

  it("clears scoped chat threads when switching users", () => {
    applyAuthSessionAfterLogin(userA);
    createChatThread("User A secret thread");
    expect(listChatThreads().some((t) => t.title.includes("User A"))).toBe(true);

    applyAuthSessionAfterLogin(userB);
    const titles = listChatThreads().map((t) => t.title);
    expect(titles.some((t) => t.includes("User A"))).toBe(false);
    expect(getActiveUserScope()).toBe("user-b@example.com");
  });

  it("clearUserScopedClientState removes aethos keys", () => {
    localStorage.setItem("aethos_chat_threads_v1:legacy", "[]");
    localStorage.setItem("aethos.mc.nav.mode", "operator");
    sessionStorage.setItem("aethos_tracked_jobs", "[]");
    clearUserScopedClientState();
    expect(localStorage.getItem("aethos_chat_threads_v1:legacy")).toBeNull();
    expect(localStorage.getItem("aethos.mc.nav.mode")).toBeNull();
    expect(sessionStorage.getItem("aethos_tracked_jobs")).toBeNull();
  });

  it("applyAuthSessionOnLoad clears when stored scope differs", () => {
    applyAuthSessionAfterLogin(userA);
    createChatThread("Only A");
    sessionStorage.setItem("aethos_active_user_scope", "user-a@example.com");

    applyAuthSessionOnLoad(userB);
    expect(listChatThreads().some((t) => t.title.includes("Only A"))).toBe(false);
  });
});
