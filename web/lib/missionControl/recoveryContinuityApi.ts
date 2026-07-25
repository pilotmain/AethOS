import { mcFetch } from "@/lib/missionControl/fetch";

export type RecoveryContinuityIntelligenceState = {
  ok: boolean;
  phase: string;
  converged?: boolean;
  summary?: string;
  narrative?: string;
  recovery_continuity?: {
    summary?: string;
    continuity_held?: boolean;
    replay_continuity?: { summary?: string };
    dependency_continuity?: { summary?: string };
    topology_continuity?: { summary?: string };
  };
  temporal_operational_trust?: { summary?: string; temporally_trusted?: boolean };
  infrastructure_convergence?: { summary?: string; converging?: boolean; topology_resilience?: { summary?: string } };
  replay_persistence?: { summary?: string; persistent?: boolean };
  adaptive_runtime_verification?: { summary?: string; adaptively_qualified?: boolean };
  long_tail_stability?: { summary?: string; long_tail_stable?: boolean };
  harness?: {
    harness_version: string;
    scenario_count: number;
    verified_count: number;
    average_coverage_pct: number;
    scenarios?: { id: string; name: string; status: string; coverage_pct: number }[];
  };
  strategic_position?: Record<string, string>;
  principles?: Record<string, string>;
};

export const fetchRecoveryContinuityIntelligenceState = () =>
  mcFetch<RecoveryContinuityIntelligenceState>("/api/v1/recovery-continuity-intelligence/state");

export const fetchTemporalOperationalTrust = () =>
  mcFetch<RecoveryContinuityIntelligenceState["temporal_operational_trust"]>(
    "/api/v1/recovery-continuity-intelligence/temporal-trust",
  );

export const fetchInfrastructureConvergence = () =>
  mcFetch<RecoveryContinuityIntelligenceState["infrastructure_convergence"]>(
    "/api/v1/recovery-continuity-intelligence/infrastructure-convergence",
  );

export const fetchReplayPersistence = () =>
  mcFetch<RecoveryContinuityIntelligenceState["replay_persistence"]>(
    "/api/v1/recovery-continuity-intelligence/replay-persistence",
  );

export const fetchAdaptiveRuntimeVerification = () =>
  mcFetch<RecoveryContinuityIntelligenceState["adaptive_runtime_verification"]>(
    "/api/v1/recovery-continuity-intelligence/adaptive-verification",
  );

export const fetchLongTailStability = () =>
  mcFetch<RecoveryContinuityIntelligenceState["long_tail_stability"]>(
    "/api/v1/recovery-continuity-intelligence/long-tail-stability",
  );

export const fetchTopologyResilience = () =>
  mcFetch<{ summary?: string; resilient?: boolean }>(
    "/api/v1/recovery-continuity-intelligence/topology-resilience",
  );

export const fetchRecoveryMemory = () =>
  mcFetch<{ ok: boolean; history_count?: number }>(
    "/api/v1/recovery-continuity-intelligence/recovery-memory",
  );

export const fetchRealityHarnessV42Recovery = () =>
  mcFetch<RecoveryContinuityIntelligenceState["harness"]>("/api/v1/reality-harness-v42/scenarios");
