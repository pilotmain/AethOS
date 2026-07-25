/** Runtime configuration API — UI-writable, allowlisted settings (no .env needed). */

import { mcFetch } from "@/lib/missionControl/fetch";

export type RuntimeSettingKind = "bool" | "str" | "enum" | "float" | "int";

export type RuntimeSetting = {
  key: string;
  label: string;
  description: string;
  kind: RuntimeSettingKind;
  options: string[];
  value: unknown;
  source: "runtime_store" | "env_default" | "settings";
  restart_required: boolean;
};

export type RuntimeSettingsGroup = {
  group: string;
  settings: RuntimeSetting[];
};

export type RuntimeSettingsResponse = {
  ok: boolean;
  groups: RuntimeSettingsGroup[];
};

export type RuntimeConfigWriteResponse = {
  ok: boolean;
  key: string;
  value: unknown;
  source: string;
  restart_required: boolean;
};

export const fetchRuntimeConfig = () => mcFetch<RuntimeSettingsResponse>("/api/v1/config");

export const setRuntimeConfig = (key: string, value: unknown) =>
  mcFetch<RuntimeConfigWriteResponse>(`/api/v1/config/${encodeURIComponent(key)}`, {
    method: "POST",
    body: JSON.stringify({ value }),
  });

export const revertRuntimeConfig = (key: string) =>
  mcFetch<{ ok: boolean; key: string; reverted: boolean }>(
    `/api/v1/config/${encodeURIComponent(key)}`,
    { method: "DELETE" },
  );
