/** @deprecated Use flatNavigation — re-exports for legacy imports. */

import type { MissionControlView } from "@/lib/missionControl/views";
import {
  FLAT_NAV_GROUPS,
  flatNavDescription,
  flatNavLabel,
  flatNavRedirectForView,
  isMainNavView,
  MAIN_NAV_VIEW_IDS,
  MERGED_INTO_PRIMARY,
} from "@/lib/missionControl/flatNavigation";

export type SimpleNavItem = {
  id: MissionControlView;
  label: string;
  description: string;
};

const workGroup = FLAT_NAV_GROUPS.find((g) => g.id === "work");
const buildGroup = FLAT_NAV_GROUPS.find((g) => g.id === "build");
const connectGroup = FLAT_NAV_GROUPS.find((g) => g.id === "connect");
const systemGroup = FLAT_NAV_GROUPS.find((g) => g.id === "system");

export const SIMPLE_NAV_ITEMS: SimpleNavItem[] = [
  ...(workGroup?.items.filter((i) => !i.href && i.id !== "theme") ?? []),
  ...(connectGroup?.items.filter((i) => !i.href) ?? []),
  ...(systemGroup?.items.filter((i) => i.id === "settings") ?? []),
].map((item) => ({
  id: item.id as MissionControlView,
  label: item.label,
  description: item.description,
}));

export const SIMPLE_NAV_TOOL_ITEMS: SimpleNavItem[] = (buildGroup?.items.filter((i) => !i.href && i.id !== "canvas") ?? []).map(
  (item) => ({
    id: item.id as MissionControlView,
    label: item.label,
    description: item.description,
  }),
);

export const SIMPLE_NAV_VIEW_IDS = MAIN_NAV_VIEW_IDS;
export const SIMPLE_NAV_TOOL_VIEWS = new Set<MissionControlView>(
  SIMPLE_NAV_TOOL_ITEMS.map((item) => item.id),
);

export const SIMPLE_NAV_APPROVAL_REDIRECT_VIEWS = new Set<MissionControlView>(
  Object.keys(MERGED_INTO_PRIMARY).filter((k) => MERGED_INTO_PRIMARY[k] === "approval-inbox") as MissionControlView[],
);

export function isSimpleNavView(view: MissionControlView): boolean {
  return isMainNavView(view);
}

export function simpleNavLabel(view: MissionControlView): string {
  return flatNavLabel(view);
}

export function simpleNavDescription(view: MissionControlView): string {
  return flatNavDescription(view);
}

export function simpleNavRedirectForView(view: MissionControlView): MissionControlView {
  return flatNavRedirectForView(view);
}
