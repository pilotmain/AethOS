import { apiBase } from "@/lib/api";
import type { TrackedJobRecord } from "@/lib/missionControl/trackedJobs";

export type ProviderInventoryService = {
  name: string;
  id: string;
  status?: string;
  domain?: string | null;
  type?: string;
};

export type ProviderInventoryEnvironment = {
  name: string;
  id: string;
  services: ProviderInventoryService[];
};

export type ProviderInventoryProject = {
  name: string;
  id: string;
  environments: ProviderInventoryEnvironment[];
};

export type ProviderInventoryPayload = {
  provider: string;
  workspace?: string | null;
  projects: ProviderInventoryProject[];
  freshness?: string;
  last_refreshed_at?: string | null;
  error?: string | null;
};

export type ProviderTopologyGroup = {
  project: string;
  environment: string;
  services: ProviderInventoryService[];
};

export type ProviderTopology = {
  provider: string;
  groups: ProviderTopologyGroup[];
  freshness: string;
};

export type ProviderServicePickerOption = {
  label: string;
  value: string;
  serviceName: string;
  projectName: string;
  environment: string;
};

export function providerTopologyFromInventory(
  inventory: ProviderInventoryPayload | null | undefined,
): ProviderTopology | null {
  if (!inventory?.projects?.length) return null;
  const groups: ProviderTopologyGroup[] = [];
  for (const project of inventory.projects) {
    for (const environment of project.environments ?? []) {
      groups.push({
        project: project.name,
        environment: environment.name,
        services: environment.services ?? [],
      });
    }
  }
  return {
    provider: inventory.provider,
    groups,
    freshness: inventory.freshness ?? "unknown",
  };
}

export function providerTopologyLabel(topology: ProviderTopology): string {
  return topology.groups
    .map((group) => `${group.project} / ${group.environment}: ${group.services.map((s) => s.name).join(", ")}`)
    .join(" · ");
}

export function providerServicePickerOptions(
  inventory: ProviderInventoryPayload | null | undefined,
): ProviderServicePickerOption[] {
  const topology = providerTopologyFromInventory(inventory);
  if (!topology) return [];
  const options: ProviderServicePickerOption[] = [];
  for (const group of topology.groups) {
    for (const service of group.services) {
      options.push({
        label: `${group.project} / ${group.environment} / ${service.name}`,
        value: service.id,
        serviceName: service.name,
        projectName: group.project,
        environment: group.environment,
      });
    }
  }
  return options;
}

export async function fetchRailwayInventory(): Promise<ProviderInventoryPayload | null> {
  const response = await fetch(`${apiBase()}/api/v1/providers/railway/inventory`);
  if (!response.ok) return null;
  const body = (await response.json()) as { inventory?: ProviderInventoryPayload };
  return body.inventory ?? null;
}

export function resolvedTargetPathFromJob(job: TrackedJobRecord): string | null {
  const target = (job.params?.target ?? {}) as Record<string, unknown>;
  const service = String(target.service_name ?? job.params?.target_name ?? "");
  const project = String(target.project_name ?? "");
  const environment = String(target.environment ?? "production");
  if (!service) return null;
  if (project) return `${project} / ${environment} / ${service}`;
  return service;
}
