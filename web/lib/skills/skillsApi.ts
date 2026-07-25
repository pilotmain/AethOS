/** Operator skills catalog API. */

import { apiBase } from "@/lib/api";

export type OperatorSkillSummary = {
  id: string;
  path?: string;
  name?: string;
  description?: string;
  loaded?: boolean;
};

export type OperatorSkillsCatalog = {
  ok: boolean;
  root?: string;
  count?: number;
  skills: OperatorSkillSummary[];
};

export type OperatorSkillDetail = OperatorSkillSummary & {
  content?: string;
};

export async function fetchOperatorSkillsCatalog(): Promise<OperatorSkillsCatalog> {
  const res = await fetch(`${apiBase()}/api/v1/runtime/skills/local`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) {
    return { ok: false, skills: [] };
  }
  return res.json() as Promise<OperatorSkillsCatalog>;
}

export async function fetchOperatorSkillDetail(skillId: string): Promise<OperatorSkillDetail | null> {
  const id = encodeURIComponent(skillId);
  const res = await fetch(`${apiBase()}/api/v1/runtime/skills/local/${id}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });
  if (!res.ok) return null;
  const data = (await res.json()) as { skill?: OperatorSkillDetail };
  return data.skill ?? null;
}
