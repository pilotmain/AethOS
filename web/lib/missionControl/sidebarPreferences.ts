/** Persisted Mission Control sidebar preferences — Phase 10.1.5. */

import type { MissionControlMode } from "@/lib/missionControl/sidebarNavigation";
import type { NavigationDomainId } from "@/lib/missionControl/sidebarNavigation";

const MODE_KEY = "aethos.mc.nav.mode";
const ADVANCED_NAV_KEY = "aethos.mc.nav.advanced";
const EXPANDED_DOMAIN_KEY = "aethos.mc.nav.expandedDomain";
const QUIET_MODE_KEY = "aethos.mc.nav.quietMode";
const FOCUS_MODE_KEY = "aethos.mc.nav.focusMode";

export function loadNavMode(): MissionControlMode {
  if (typeof window === "undefined") return "operator";
  const raw = window.localStorage.getItem(MODE_KEY);
  if (raw === "executive" || raw === "operator" || raw === "deep-engineering") return raw;
  return "operator";
}

export function saveNavMode(mode: MissionControlMode): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(MODE_KEY, mode);
}

/** Full workflow sidebar (legacy). Default is simple flat nav. */
export function loadAdvancedNav(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(ADVANCED_NAV_KEY) === "true";
}

export function saveAdvancedNav(advanced: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ADVANCED_NAV_KEY, advanced ? "true" : "false");
}

export function loadExpandedDomain(): NavigationDomainId | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(EXPANDED_DOMAIN_KEY);
  const migrated =
    raw === "engineering"
      ? "workspaces"
      : raw === "human-intelligence"
        ? "intelligence"
        : raw === "enterprise"
          ? "settings"
          : raw;
  if (
    migrated === "workspaces" ||
    migrated === "operations" ||
    migrated === "intelligence" ||
    migrated === "infrastructure" ||
    migrated === "settings"
  ) {
    return migrated;
  }
  return null;
}

export function saveExpandedDomain(domain: NavigationDomainId | null): void {
  if (typeof window === "undefined") return;
  if (domain) window.localStorage.setItem(EXPANDED_DOMAIN_KEY, domain);
  else window.localStorage.removeItem(EXPANDED_DOMAIN_KEY);
}

export function loadQuietMode(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(QUIET_MODE_KEY) === "true";
}

export function saveQuietMode(quiet: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(QUIET_MODE_KEY, quiet ? "true" : "false");
}

export function loadFocusMode(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(FOCUS_MODE_KEY) === "true";
}

export function saveFocusMode(focus: boolean): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(FOCUS_MODE_KEY, focus ? "true" : "false");
}
