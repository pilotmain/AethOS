/** Mission Control sidebar views — maps navigation to panel content. */

export const MISSION_CONTROL_VIEWS = [
  "overview",
  "cross-lane-operations",
  "pilot-validation-trust-board",
  "dogfood-pilot-chain",
  "multi-repo-pilot-program",
  "approval-inbox",
  "mission-job-replay",
  "workflow-workspaces",
  "workflow-operations",
  "workflow-infrastructure",
  "workflow-intelligence",
  "workflow-settings",
  "observability",
  "activity-feed",
  "runtime-actions",
  "tracked-work",
  "operation-preflights",
  "mutation-audit",
  "agent-orchestration",
  "deep-research",
  "evidence-gallery",
  "research-library",
  "blind-model-eval",
  "arbiter-panel",
  "monitors",
  "daily-digest",
  "memory-viewer",
  "proactive-suggestions",
  "agent-comms",
  "channel-tool-policy",
  "cron-governed-jobs",
  "proactive-automation",
  "governed-sandbox",
  "active-agents",
  "agent-timelines",
  "coordination-graph",
  "evidence-merge",
  "operational-replay",
  "evidence-graph",
  "agent-evidence",
  "operational-intelligence",
  "engineering-proposals",
  "engineering-execution",
  "sandbox-executions",
  "validation-center",
  "diff-explorer",
  "pr-drafts-center",
  "rollback-snapshots",
  "engineering-audit",
  "operational-reality",
  "operational-anomalies",
  "operational-drift",
  "deployment-stability",
  "cross-provider-correlation",
  "workflow-health",
  "dependency-risk",
  "recommendation-queue",
  "telemetry-freshness",
  "intelligence-replay",
  "runtime-tunnel",
  "mcp-bridge",
  "research-config",
  "agent-policies",
  "delegated-tasks",
  "subagent-sessions",
  "credential-center",
  "provider-inventory",
  "integrations",
  "browser-evidence",
  "web-intelligence",
  "research-intelligence",
  "browser-profiles",
  "audit-logs",
  "system-health",
  "settings",
  "tenant-onboarding",
  "identity-access-hardening",
  "users-roles",
  "platform-owner",
  "provider-connections",
  "channel-integration",
  "billing-entitlements",
  "customer-administration",
  "customer-audit-portal",
  "payment-integration-readiness",
  "saas-launch-readiness",
  "customer-support-success",
  "public-product-experience",
  "public-capability-explorer",
  "public-trust-explorer",
  "public-product-tour",
  "public-customer-journey",
  "public-education-center",
  "beta-launch-program",
  "beta-cohorts",
  "beta-feedback",
  "beta-success-metrics",
  "beta-operations-dashboard",
  "launch-operations-center",
  "launch-dashboard",
  "launch-risks",
  "launch-blockers",
  "launch-evidence",
  "launch-beta-operations",
  "launch-customer-operations",
  "launch-readiness-freeze",
  "launch-baseline",
  "launch-evidence-freeze",
  "launch-recommendation-freeze",
  "launch-freeze-blockers",
  "launch-freeze-risks",
  "launch-decision-package",
  "launch-executive-summary",
  "launch-recommendation-package",
  "launch-decision-dashboard",
  "launch-decision-history",
  "post-launch-operations",
  "post-launch-platform-health",
  "post-launch-customer-health",
  "post-launch-governance-health",
  "post-launch-incident-health",
  "post-launch-commercial-health",
  "post-launch-operations-dashboard",
  "local-workspaces",
  "repo-diagnostics",
  "architecture-maps",
  "git-activity",
  "dependency-health",
  "test-intelligence",
  "pr-proposals",
  "workspace-active",
  "workspace-desktop",
  "workspace-terminal",
  "workspace-evidence",
  "workspace-replay",
  "workspace-files",
  "workspace-sandbox",
  "workspace-memory",
  "presence-feed",
  "presence-attention",
  "presence-timeline",
  "presence-focus",
  "presence-collaboration",
  "presence-recommendations",
  "presence-watch",
  "presence-memory",
  "trust-authority",
  "trust-replay",
  "trust-governance",
  "trust-confidence",
  "trust-signal-quality",
  "trust-correlation",
  "trust-metrics",
  "trust-recovery",
  "truth-capability-matrix",
  "truth-provider-readiness",
  "truth-verification-coverage",
  "truth-mutation-reliability",
  "truth-operational-honesty",
  "truth-runtime-validation",
  "truth-reality-harness",
  "truth-production-readiness",
  "reliability-providers",
  "reliability-deployment-verification",
  "reliability-recovery-runtime",
  "reliability-mutation-reconciliation",
  "reliability-rollback-integrity",
  "reliability-runtime-stabilization",
  "reliability-operational-confidence",
  "reliability-reality-validation",
  "infra-container-intelligence",
  "infra-kubernetes-runtime",
  "infra-runtime-topology",
  "infra-infrastructure-health",
  "infra-resource-pressure",
  "infra-drift-detection",
  "infra-cluster-recovery",
  "infra-infrastructure-truth",
  "reliability-continuous-verification",
  "reliability-recovery-orchestration",
  "reliability-drift-intelligence",
  "reliability-predictive-operations",
  "reliability-production-confidence",
  "reliability-reliability-memory",
  "reliability-operational-trajectory",
  "reliability-confidence-forecasting",
  "synthesis-quality",
  "synthesis-recommendations",
  "synthesis-conversational-trust",
  "synthesis-presentation-safety",
  "synthesis-response-elegance",
  "synthesis-human-trust",
  "synthesis-recommendation-replay",
  "synthesis-conversational-recovery",
  "conv-reliability",
  "conv-recommendation-quality",
  "conv-trust-calibration",
  "conv-presentation-integrity",
  "conv-interaction-elegance",
  "conv-conversational-replay",
  "conv-recommendation-intelligence",
  "conv-human-trust-signals",
  "conv-convergence",
  "conv-interaction-layers",
  "conv-trust-maturity",
  "conv-synthesis-consistency",
  "conv-production-interaction",
  "conv-maturity-profile",
  "conv-surface-integrity",
  "conv-trust-threshold",
  "prod-deployment-truth",
  "prod-rollback-integrity",
  "prod-runtime-stabilization",
  "prod-topology-recovery",
  "prod-operational-decay",
  "prod-production-qualification",
  "prod-sustained-verification",
  "prod-recovery-confidence",
  "rt-reconciliation",
  "rt-operational-patience",
  "rt-runtime-decay",
  "rt-sustained-verification",
  "rt-recovery-truth",
  "rt-replay-stability",
  "rt-topology-alignment",
  "rt-operational-windows",
  "rtc-runtime-truth",
  "rtc-stability-windows",
  "rtc-replay-convergence",
  "rtc-dependency-stability",
  "rtc-topology-truth",
  "rtc-operational-decay",
  "rtc-sustained-confidence",
  "rtc-recovery-continuity",
  "ccg-convergence-cognition",
  "ccg-infrastructure-intuition",
  "ccg-temporal-confidence",
  "ccg-kubernetes-convergence",
  "ccg-replay-continuity",
  "ccg-long-tail-stability",
  "ccg-operational-memory",
  "ccg-runtime-trajectories",
  "rci-recovery-continuity",
  "rci-temporal-trust",
  "rci-infrastructure-convergence",
  "rci-replay-persistence",
  "rci-adaptive-verification",
  "rci-long-tail-stability",
  "rci-topology-resilience",
  "rci-recovery-memory",
  "rsc-operational-resilience",
  "rsc-infrastructure-fragility",
  "rsc-temporal-trust-evolution",
  "rsc-kubernetes-resilience",
  "rsc-replay-resilience",
  "rsc-long-tail-stability",
  "rsc-recovery-durability",
  "rsc-operational-trajectories",
  "ors-operational-resilience",
  "ors-runtime-fragility",
  "ors-sustained-trust",
  "ors-kubernetes-durability",
  "ors-replay-resilience",
  "ors-long-tail-stability",
  "ors-recovery-durability",
  "ors-operational-trajectories",
  "poc-predictive-stability",
  "poc-fragility-acceleration",
  "poc-replay-forecasting",
  "poc-topology-forecasting",
  "poc-operational-fatigue",
  "poc-stability-projection",
  "poc-recovery-forecasting",
  "poc-predictive-memory",
  "rfi-runtime-fragility",
  "rfi-degradation-acceleration",
  "rfi-replay-erosion",
  "rfi-topology-fragility",
  "rfi-operational-fatigue",
  "rfi-predictive-stability",
  "rfi-recovery-fragility",
  "rfi-fragility-memory",
  "ltf-long-tail-forecasting",
  "ltf-operational-survivability",
  "ltf-replay-longevity",
  "ltf-topology-sustainability",
  "ltf-resilience-exhaustion",
  "ltf-stability-endurance",
  "ltf-autonomous-stability",
  "ltf-forecasting-trajectories",
  "ltf-forecasting-memory",
  "ltr-long-tail-cognition",
  "ltr-runtime-survivability",
  "ltr-operational-endurance",
  "ltr-replay-continuity",
  "ltr-topology-endurance",
  "ltr-resilience-exhaustion",
  "ltr-runtime-persistence",
  "ltr-cognition-memory",
  "cog-operational-grounding",
  "cog-continuity-reconstruction",
  "cog-operational-context",
  "cog-governance-restraint",
  "cog-conversational-realism",
  "cog-telegram-persistence",
  "cog-partner-presence",
  "cog-cross-surface-convergence",
  "cog-live-operational-grounding",
  "cog-durable-jobs",
  "cog-durable-jobs-active",
  "cog-durable-jobs-artifacts",
  "cog-grounding-memory",
  "enterprise-doctor",
  "enterprise-setup-wizard",
  "enterprise-config",
  "enterprise-health",
  "enterprise-demo",
  "production-deployment",
  "production-cluster",
  "production-orgs",
  "production-plugins",
  "production-observability",
  "production-metering",
  "production-upgrade",
  "production-security",
  "human-overview",
  "human-relational",
  "human-voice",
  "human-channels",
  "human-life",
  "human-actions",
  "human-ambient",
  "human-collaboration",
  "human-trust",
  "human-marketplace",
  "human-mobile",
  "human-living",
  "human-live-presence",
  "human-conversation",
  "human-copilot",
  "human-personal",
  "human-explainability",
  "human-thinking",
  "human-multimodal-voice",
  "human-continuity",
  "human-trust-controls",
  "integrity-routes",
  "integrity-features",
  "integrity-ui-alignment",
  "integrity-orphans",
  "integrity-diagnostics",
  "presence-attention-quality",
  "presence-interruption-budget",
  "presence-continuity-accuracy",
  "presence-operational-narrative",
  "presence-calm-intelligence",
  "presence-trust-signals",
  "presence-collaboration-quality",
  "companion-operational-reasoning",
  "companion-investigation",
  "companion-replay-intelligence",
  "companion-emotional-realism",
  "companion-attention-awareness",
  "companion-narrative-evolution",
  "companion-trust-retention",
] as const;

export type MissionControlView = (typeof MISSION_CONTROL_VIEWS)[number];

export type SidebarSection = {
  title: string;
  items: { id: MissionControlView; label: string }[];
};

export const SIDEBAR_SECTIONS: SidebarSection[] = [
  {
    title: "Overview",
    items: [
      { id: "overview", label: "Mission Control" },
      { id: "cross-lane-operations", label: "Cross-Lane Control" },
      { id: "pilot-validation-trust-board", label: "Pilot Validation Trust" },
      { id: "dogfood-pilot-chain", label: "Dogfood Pilot Chain" },
      { id: "multi-repo-pilot-program", label: "Multi-Repo Pilot Program" },
      { id: "approval-inbox", label: "Approval Inbox" },
      { id: "mission-job-replay", label: "Job Replay" },
      { id: "observability", label: "Observability" },
      { id: "activity-feed", label: "Activity Feed" },
    ],
  },
  {
    title: "Runtime",
    items: [
      { id: "runtime-actions", label: "Runtime Actions" },
      { id: "tracked-work", label: "Tracked Work" },
      { id: "operation-preflights", label: "Operation Preflights" },
      { id: "mutation-audit", label: "Mutation Audit" },
    ],
  },
  {
    title: "Multi-Agent Runtime",
    items: [
      { id: "agent-orchestration", label: "Orchestration" },
      { id: "agent-comms", label: "Multi-Agent Live" },
      { id: "agent-evidence", label: "Evidence" },
      { id: "engineering-proposals", label: "Proposals" },
      { id: "engineering-execution", label: "Pending Preflights" },
    ],
  },
  {
    title: "Multi-Agent (Advanced)",
    items: [
      // §4 — Active Agents / Agent Timelines / Coordination Graph were redundant
      // standalone boards that overlapped the single Orchestration board (which
      // now shows distinct agent lanes + inline coordination). Watch agents there.
      { id: "evidence-merge", label: "Evidence Merge" },
      { id: "operational-intelligence", label: "Operational Intelligence" },
      { id: "operational-replay", label: "Replay Center" },
      { id: "evidence-graph", label: "Evidence Graph" },
      { id: "sandbox-executions", label: "Sandbox Executions" },
      { id: "validation-center", label: "Validation Center" },
      { id: "diff-explorer", label: "Diff Explorer" },
      { id: "pr-drafts-center", label: "PR Drafts" },
      { id: "rollback-snapshots", label: "Rollback Snapshots" },
      { id: "engineering-audit", label: "Engineering Audit" },
      { id: "operational-reality", label: "Operational Reality" },
      { id: "agent-policies", label: "Agent Policies" },
      { id: "delegated-tasks", label: "Delegated Tasks" },
      { id: "subagent-sessions", label: "Session Archive" },
    ],
  },
  {
    title: "Operational Intelligence",
    items: [
      { id: "monitors", label: "Monitors" },
      { id: "daily-digest", label: "Daily Digest" },
      { id: "memory-viewer", label: "Memory" },
      { id: "proactive-suggestions", label: "Proactive Suggestions" },
      { id: "operational-anomalies", label: "Active Anomalies" },
      { id: "operational-drift", label: "Drift Detection" },
      { id: "deployment-stability", label: "Deployment Stability" },
      { id: "cross-provider-correlation", label: "Cross-Provider Correlation" },
      { id: "workflow-health", label: "Workflow Health" },
      { id: "dependency-risk", label: "Dependency Risk" },
      { id: "recommendation-queue", label: "Recommendation Queue" },
      { id: "telemetry-freshness", label: "Telemetry Freshness" },
      { id: "intelligence-replay", label: "Operational Replay" },
    ],
  },
  {
    title: "Providers",
    items: [
      { id: "credential-center", label: "Credential Center" },
      { id: "provider-inventory", label: "Provider Inventory" },
      { id: "integrations", label: "Integrations" },
    ],
  },
  {
    title: "Browser",
    items: [
      { id: "browser-evidence", label: "Browser Evidence" },
      { id: "web-intelligence", label: "Web Intelligence" },
      { id: "research-intelligence", label: "Research Intelligence" },
      { id: "browser-profiles", label: "Browser Profiles" },
    ],
  },
  {
    title: "Engineering",
    items: [
      { id: "local-workspaces", label: "Code workspaces" },
      { id: "repo-diagnostics", label: "Repo Diagnostics" },
      { id: "architecture-maps", label: "Architecture Maps" },
      { id: "git-activity", label: "Git Activity" },
      { id: "dependency-health", label: "Dependency Health" },
      { id: "test-intelligence", label: "Test Intelligence" },
      { id: "pr-proposals", label: "PR Proposals" },
    ],
  },
  {
    title: "Workspace Operations",
    items: [
      { id: "workspace-active", label: "Active Workspaces" },
      { id: "workspace-desktop", label: "Desktop Awareness" },
      { id: "workspace-terminal", label: "Terminal Sessions" },
      { id: "workspace-evidence", label: "Workspace Evidence" },
      { id: "workspace-replay", label: "Runtime Replay" },
      { id: "workspace-files", label: "File Intelligence" },
      { id: "workspace-sandbox", label: "Sandbox Sessions" },
      { id: "workspace-memory", label: "Workspace Memory" },
    ],
  },
  {
    title: "Operational Presence",
    items: [
      { id: "presence-feed", label: "Live Feed" },
      { id: "presence-attention", label: "Attention Center" },
      { id: "presence-timeline", label: "Presence Timeline" },
      { id: "presence-focus", label: "Active Focus" },
      { id: "presence-collaboration", label: "Collaboration Sessions" },
      { id: "presence-recommendations", label: "Recommendation Queue" },
      { id: "presence-watch", label: "Watch Mode" },
      { id: "presence-memory", label: "Operational Memory" },
    ],
  },
  {
    title: "Production Reliability",
    items: [
      { id: "reliability-providers", label: "Provider Reliability" },
      { id: "reliability-deployment-verification", label: "Deployment Verification" },
      { id: "reliability-recovery-runtime", label: "Recovery Runtime" },
      { id: "reliability-mutation-reconciliation", label: "Mutation Reconciliation" },
      { id: "reliability-rollback-integrity", label: "Rollback Integrity" },
      { id: "reliability-runtime-stabilization", label: "Runtime Stabilization" },
      { id: "reliability-operational-confidence", label: "Operational Confidence" },
      { id: "reliability-reality-validation", label: "Reality Validation" },
    ],
  },
  {
    title: "Infrastructure Intelligence",
    items: [
      { id: "infra-container-intelligence", label: "Container Intelligence" },
      { id: "infra-kubernetes-runtime", label: "Kubernetes Runtime" },
      { id: "infra-runtime-topology", label: "Runtime Topology" },
      { id: "infra-infrastructure-health", label: "Infrastructure Health" },
      { id: "infra-resource-pressure", label: "Resource Pressure" },
      { id: "infra-drift-detection", label: "Drift Detection" },
      { id: "infra-cluster-recovery", label: "Cluster Recovery" },
      { id: "infra-infrastructure-truth", label: "Infrastructure Truth" },
    ],
  },
  {
    title: "Operational Reliability",
    items: [
      { id: "reliability-continuous-verification", label: "Continuous Verification" },
      { id: "reliability-recovery-orchestration", label: "Recovery Orchestration" },
      { id: "reliability-drift-intelligence", label: "Drift Intelligence" },
      { id: "reliability-predictive-operations", label: "Predictive Operations" },
      { id: "reliability-production-confidence", label: "Production Confidence" },
      { id: "reliability-reliability-memory", label: "Reliability Memory" },
      { id: "reliability-operational-trajectory", label: "Operational Trajectory" },
      { id: "reliability-confidence-forecasting", label: "Confidence Forecasting" },
    ],
  },
  {
    title: "Operational Truth",
    items: [
      { id: "truth-production-readiness", label: "Production Readiness" },
      { id: "truth-capability-matrix", label: "Capability Matrix" },
      { id: "truth-provider-readiness", label: "Provider Readiness" },
      { id: "truth-verification-coverage", label: "Verification Coverage" },
      { id: "truth-mutation-reliability", label: "Mutation Reliability" },
      { id: "truth-operational-honesty", label: "Operational Honesty" },
      { id: "truth-runtime-validation", label: "Runtime Validation" },
      { id: "truth-reality-harness", label: "Reality Harness" },
    ],
  },
  {
    title: "Operational Trust",
    items: [
      { id: "trust-authority", label: "Reliability Authority" },
      { id: "trust-replay", label: "Replay Intelligence" },
      { id: "trust-governance", label: "Governance Drift" },
      { id: "trust-confidence", label: "Confidence Center" },
      { id: "trust-signal-quality", label: "Signal Quality" },
      { id: "trust-correlation", label: "Correlation Graph" },
      { id: "trust-metrics", label: "Trust Metrics" },
      { id: "trust-recovery", label: "Recovery Runtime" },
    ],
  },
  {
    title: "Production Infrastructure",
    items: [
      { id: "production-deployment", label: "Deployment Topology" },
      { id: "production-cluster", label: "Runtime Cluster" },
      { id: "production-orgs", label: "Organizations" },
      { id: "production-plugins", label: "Plugin Center" },
      { id: "production-observability", label: "Observability" },
      { id: "production-metering", label: "Usage & Metering" },
      { id: "production-upgrade", label: "Upgrade Center" },
      { id: "production-security", label: "Enterprise Security" },
    ],
  },
  {
    title: "Synthesis Intelligence",
    items: [
      { id: "synthesis-quality", label: "Synthesis Quality" },
      { id: "synthesis-recommendations", label: "Recommendation Intelligence" },
      { id: "synthesis-conversational-trust", label: "Conversational Trust" },
      { id: "synthesis-presentation-safety", label: "Presentation Safety" },
      { id: "synthesis-response-elegance", label: "Response Elegance" },
      { id: "synthesis-human-trust", label: "Human Trust Signals" },
      { id: "synthesis-recommendation-replay", label: "Recommendation Replay" },
      { id: "synthesis-conversational-recovery", label: "Conversational Recovery" },
    ],
  },
  {
    title: "Conversational Reliability",
    items: [
      { id: "conv-reliability", label: "Conversational Reliability" },
      { id: "conv-recommendation-quality", label: "Recommendation Quality" },
      { id: "conv-trust-calibration", label: "Trust Calibration" },
      { id: "conv-presentation-integrity", label: "Presentation Integrity" },
      { id: "conv-interaction-elegance", label: "Interaction Elegance" },
      { id: "conv-conversational-replay", label: "Conversational Replay" },
      { id: "conv-recommendation-intelligence", label: "Recommendation Intelligence" },
      { id: "conv-human-trust-signals", label: "Human Trust Signals" },
    ],
  },
  {
    title: "Interaction Convergence",
    items: [
      { id: "conv-convergence", label: "Interaction Convergence" },
      { id: "conv-interaction-layers", label: "Interaction Layers" },
      { id: "conv-trust-maturity", label: "Trust Maturity" },
      { id: "conv-synthesis-consistency", label: "Synthesis Consistency" },
      { id: "conv-production-interaction", label: "Production Interaction" },
      { id: "conv-maturity-profile", label: "Maturity Profile" },
      { id: "conv-surface-integrity", label: "Surface Integrity" },
      { id: "conv-trust-threshold", label: "Trust Threshold" },
    ],
  },
  {
    title: "Production Reality",
    items: [
      { id: "prod-deployment-truth", label: "Deployment Truth" },
      { id: "prod-rollback-integrity", label: "Rollback Integrity" },
      { id: "prod-runtime-stabilization", label: "Runtime Stabilization" },
      { id: "prod-topology-recovery", label: "Topology Recovery" },
      { id: "prod-operational-decay", label: "Operational Decay" },
      { id: "prod-production-qualification", label: "Production Qualification" },
      { id: "prod-sustained-verification", label: "Sustained Verification" },
      { id: "prod-recovery-confidence", label: "Recovery Confidence" },
    ],
  },
  {
    title: "Runtime Truth",
    items: [
      { id: "rt-reconciliation", label: "Runtime Reconciliation" },
      { id: "rt-operational-patience", label: "Operational Patience" },
      { id: "rt-runtime-decay", label: "Runtime Decay" },
      { id: "rt-sustained-verification", label: "Sustained Verification" },
      { id: "rt-recovery-truth", label: "Recovery Truth" },
      { id: "rt-replay-stability", label: "Replay Stability" },
      { id: "rt-topology-alignment", label: "Topology Alignment" },
      { id: "rt-operational-windows", label: "Operational Windows" },
    ],
  },
  {
    title: "Runtime Truth Evolution",
    items: [
      { id: "rtc-runtime-truth", label: "Runtime Truth" },
      { id: "rtc-stability-windows", label: "Stability Windows" },
      { id: "rtc-replay-convergence", label: "Replay Convergence" },
      { id: "rtc-dependency-stability", label: "Dependency Stability" },
      { id: "rtc-topology-truth", label: "Topology Truth" },
      { id: "rtc-operational-decay", label: "Operational Decay" },
      { id: "rtc-sustained-confidence", label: "Sustained Confidence" },
      { id: "rtc-recovery-continuity", label: "Recovery Continuity" },
    ],
  },
  {
    title: "Convergence Cognition",
    items: [
      { id: "ccg-convergence-cognition", label: "Convergence Cognition" },
      { id: "ccg-infrastructure-intuition", label: "Infrastructure Intuition" },
      { id: "ccg-temporal-confidence", label: "Temporal Confidence" },
      { id: "ccg-kubernetes-convergence", label: "Kubernetes Convergence" },
      { id: "ccg-replay-continuity", label: "Replay Continuity" },
      { id: "ccg-long-tail-stability", label: "Long-Tail Stability" },
      { id: "ccg-operational-memory", label: "Operational Memory" },
      { id: "ccg-runtime-trajectories", label: "Runtime Trajectories" },
    ],
  },
  {
    title: "Recovery Continuity",
    items: [
      { id: "rci-recovery-continuity", label: "Recovery Continuity" },
      { id: "rci-temporal-trust", label: "Temporal Trust" },
      { id: "rci-infrastructure-convergence", label: "Infrastructure Convergence" },
      { id: "rci-replay-persistence", label: "Replay Persistence" },
      { id: "rci-adaptive-verification", label: "Adaptive Verification" },
      { id: "rci-long-tail-stability", label: "Long-Tail Stability" },
      { id: "rci-topology-resilience", label: "Topology Resilience" },
      { id: "rci-recovery-memory", label: "Recovery Memory" },
    ],
  },
  {
    title: "Resilience Cognition",
    items: [
      { id: "rsc-operational-resilience", label: "Operational Resilience" },
      { id: "rsc-infrastructure-fragility", label: "Infrastructure Fragility" },
      { id: "rsc-temporal-trust-evolution", label: "Temporal Trust Evolution" },
      { id: "rsc-kubernetes-resilience", label: "Kubernetes Resilience" },
      { id: "rsc-replay-resilience", label: "Replay Resilience" },
      { id: "rsc-long-tail-stability", label: "Long-Tail Stability" },
      { id: "rsc-recovery-durability", label: "Recovery Durability" },
      { id: "rsc-operational-trajectories", label: "Operational Trajectories" },
    ],
  },
  {
    title: "Operational Resilience (11.6.3)",
    items: [
      { id: "ors-operational-resilience", label: "Operational Resilience" },
      { id: "ors-runtime-fragility", label: "Runtime Fragility" },
      { id: "ors-sustained-trust", label: "Sustained Trust" },
      { id: "ors-kubernetes-durability", label: "Kubernetes Durability" },
      { id: "ors-replay-resilience", label: "Replay Resilience" },
      { id: "ors-long-tail-stability", label: "Long-Tail Stability" },
      { id: "ors-recovery-durability", label: "Recovery Durability" },
      { id: "ors-operational-trajectories", label: "Operational Trajectories" },
    ],
  },
  {
    title: "Predictive Cognition",
    items: [
      { id: "poc-predictive-stability", label: "Predictive Stability" },
      { id: "poc-fragility-acceleration", label: "Fragility Acceleration" },
      { id: "poc-replay-forecasting", label: "Replay Forecasting" },
      { id: "poc-topology-forecasting", label: "Topology Forecasting" },
      { id: "poc-operational-fatigue", label: "Operational Fatigue" },
      { id: "poc-stability-projection", label: "Stability Projection" },
      { id: "poc-recovery-forecasting", label: "Recovery Forecasting" },
      { id: "poc-predictive-memory", label: "Predictive Operational Memory" },
    ],
  },
  {
    title: "Runtime Fragility (11.6.4)",
    items: [
      { id: "rfi-runtime-fragility", label: "Runtime Fragility" },
      { id: "rfi-degradation-acceleration", label: "Degradation Acceleration" },
      { id: "rfi-replay-erosion", label: "Replay Erosion" },
      { id: "rfi-topology-fragility", label: "Topology Fragility" },
      { id: "rfi-operational-fatigue", label: "Operational Fatigue" },
      { id: "rfi-predictive-stability", label: "Predictive Stability" },
      { id: "rfi-recovery-fragility", label: "Recovery Fragility" },
      { id: "rfi-fragility-memory", label: "Fragility Memory" },
    ],
  },
  {
    title: "Long-Tail Forecasting (11.4.7)",
    items: [
      { id: "ltf-long-tail-forecasting", label: "Long-Tail Forecasting" },
      { id: "ltf-operational-survivability", label: "Operational Survivability" },
      { id: "ltf-replay-longevity", label: "Replay Longevity" },
      { id: "ltf-topology-sustainability", label: "Topology Sustainability" },
      { id: "ltf-resilience-exhaustion", label: "Resilience Exhaustion" },
      { id: "ltf-stability-endurance", label: "Stability Endurance" },
      { id: "ltf-autonomous-stability", label: "Autonomous Stability" },
      { id: "ltf-forecasting-trajectories", label: "Forecasting Trajectories" },
      { id: "ltf-forecasting-memory", label: "Long-Tail Operational Memory" },
    ],
  },
  {
    title: "Long-Tail Runtime Cognition (11.6.5)",
    items: [
      { id: "ltr-long-tail-cognition", label: "Long-Tail Cognition" },
      { id: "ltr-runtime-survivability", label: "Runtime Survivability" },
      { id: "ltr-operational-endurance", label: "Operational Endurance" },
      { id: "ltr-replay-continuity", label: "Replay Continuity" },
      { id: "ltr-topology-endurance", label: "Topology Endurance" },
      { id: "ltr-resilience-exhaustion", label: "Resilience Exhaustion" },
      { id: "ltr-runtime-persistence", label: "Runtime Persistence" },
      { id: "ltr-cognition-memory", label: "Cognition Memory" },
    ],
  },
  {
    title: "Conversational Grounding (11.7)",
    items: [
      { id: "cog-operational-grounding", label: "Operational Grounding" },
      { id: "cog-continuity-reconstruction", label: "Continuity Reconstruction" },
      { id: "cog-operational-context", label: "Operational Context" },
      { id: "cog-governance-restraint", label: "Governance Restraint" },
      { id: "cog-conversational-realism", label: "Conversational Realism" },
      { id: "cog-telegram-persistence", label: "Telegram Persistence" },
      { id: "cog-partner-presence", label: "Partner Presence" },
      { id: "cog-cross-surface-convergence", label: "Cross-Surface Convergence" },
      { id: "cog-live-operational-grounding", label: "Live Operational Grounding" },
      { id: "cog-durable-jobs", label: "Durable Agent Jobs" },
      { id: "cog-durable-jobs-active", label: "Active Jobs" },
      { id: "cog-durable-jobs-artifacts", label: "Job Artifacts" },
      { id: "cog-grounding-memory", label: "Grounding Memory" },
    ],
  },
  {
    title: "Enterprise Readiness",
    items: [
      { id: "enterprise-doctor", label: "Environment Doctor" },
      { id: "enterprise-setup-wizard", label: "Setup Wizard" },
      { id: "enterprise-config", label: "Configuration Center" },
      { id: "enterprise-health", label: "Operational Health" },
      { id: "enterprise-demo", label: "Demo Mode" },
    ],
  },
  {
    title: "Human-Centered OS",
    items: [
      { id: "human-overview", label: "Convergence Overview" },
      { id: "human-relational", label: "Relational Intelligence" },
      { id: "human-voice", label: "Voice & Presence" },
      { id: "human-channels", label: "Universal Channels" },
      { id: "proactive-automation", label: "Proactive Automation" },
      { id: "human-life", label: "LifeOS" },
      { id: "human-actions", label: "Action Runtime" },
      { id: "human-ambient", label: "Ambient Presence" },
      { id: "human-collaboration", label: "Collaboration Sessions" },
      { id: "human-trust", label: "Trust Center" },
      { id: "human-marketplace", label: "Marketplace" },
      { id: "human-mobile", label: "Mobile & Edge" },
    ],
  },
  {
    title: "Living Intelligence",
    items: [
      { id: "human-living", label: "Living Companion" },
      { id: "human-live-presence", label: "Live Presence" },
      { id: "human-conversation", label: "Conversation Continuity" },
      { id: "human-copilot", label: "Operational Co-Pilot" },
      { id: "human-personal", label: "Personal Intelligence" },
      { id: "human-explainability", label: "World-Class Explainability" },
      { id: "human-thinking", label: "Thinking Boundaries" },
      { id: "human-multimodal-voice", label: "Multimodal Voice" },
      { id: "human-continuity", label: "Continuity Memory" },
      { id: "human-trust-controls", label: "Trust Controls" },
    ],
  },
  {
    title: "Presence Quality",
    items: [
      { id: "presence-attention-quality", label: "Attention Quality" },
      { id: "presence-interruption-budget", label: "Interruption Budget" },
      { id: "presence-continuity-accuracy", label: "Continuity Accuracy" },
      { id: "presence-operational-narrative", label: "Operational Narrative" },
      { id: "presence-calm-intelligence", label: "Calm Intelligence" },
      { id: "presence-trust-signals", label: "Trust Signals" },
      { id: "presence-collaboration-quality", label: "Collaboration Quality" },
    ],
  },
  {
    title: "Companion Intelligence",
    items: [
      { id: "companion-operational-reasoning", label: "Operational Reasoning" },
      { id: "companion-investigation", label: "Investigation Companion" },
      { id: "companion-replay-intelligence", label: "Replay Intelligence" },
      { id: "companion-emotional-realism", label: "Emotional Realism" },
      { id: "companion-attention-awareness", label: "Attention Awareness" },
      { id: "companion-narrative-evolution", label: "Narrative Evolution" },
      { id: "companion-trust-retention", label: "Trust Retention" },
    ],
  },
  {
    title: "Runtime Integrity",
    items: [
      { id: "integrity-routes", label: "Route Health" },
      { id: "integrity-features", label: "Feature Wiring" },
      { id: "integrity-ui-alignment", label: "UI ↔ API Alignment" },
      { id: "integrity-orphans", label: "Orphan Systems" },
      { id: "integrity-diagnostics", label: "Runtime Diagnostics" },
    ],
  },
  {
    title: "Public Experience",
    items: [
      { id: "public-product-experience", label: "Public Experience" },
      { id: "public-capability-explorer", label: "Capability Explorer" },
      { id: "public-trust-explorer", label: "Trust Explorer" },
      { id: "public-product-tour", label: "Product Tour" },
      { id: "public-customer-journey", label: "Customer Journey" },
      { id: "public-education-center", label: "Education Center" },
    ],
  },
  {
    title: "System",
    items: [
      { id: "audit-logs", label: "Audit Logs" },
      { id: "system-health", label: "System Health" },
      { id: "tenant-onboarding", label: "Tenant Onboarding" },
      { id: "identity-access-hardening", label: "Identity & Access" },
      { id: "users-roles", label: "Users & Roles" },
      { id: "platform-owner", label: "Owner console" },
      { id: "provider-connections", label: "Provider Connections" },
      { id: "channel-integration", label: "Channel Integration" },
      { id: "billing-entitlements", label: "Billing & Entitlements" },
      { id: "customer-administration", label: "Administration Console" },
      { id: "customer-audit-portal", label: "Usage & Audit Portal" },
      { id: "payment-integration-readiness", label: "Payment Readiness" },
      { id: "saas-launch-readiness", label: "Launch Readiness" },
      { id: "customer-support-success", label: "Customer Support" },
      { id: "beta-launch-program", label: "Beta Launch Program" },
      { id: "beta-cohorts", label: "Beta Cohorts" },
      { id: "beta-feedback", label: "Beta Feedback" },
      { id: "beta-success-metrics", label: "Beta Success Metrics" },
      { id: "beta-operations-dashboard", label: "Beta Operations Dashboard" },
      { id: "launch-operations-center", label: "Launch Operations Center" },
      { id: "launch-dashboard", label: "Launch Dashboard" },
      { id: "launch-risks", label: "Launch Risks" },
      { id: "launch-blockers", label: "Launch Blockers" },
      { id: "launch-evidence", label: "Launch Evidence" },
      { id: "launch-beta-operations", label: "Beta Operations" },
      { id: "launch-customer-operations", label: "Customer Operations" },
      { id: "launch-readiness-freeze", label: "Launch Readiness Freeze" },
      { id: "launch-baseline", label: "Launch Baseline" },
      { id: "launch-evidence-freeze", label: "Launch Evidence Freeze" },
      { id: "launch-recommendation-freeze", label: "Launch Recommendation Freeze" },
      { id: "launch-freeze-blockers", label: "Launch Freeze Blockers" },
      { id: "launch-freeze-risks", label: "Launch Freeze Risks" },
      { id: "launch-decision-package", label: "Launch Decision Package" },
      { id: "launch-executive-summary", label: "Executive Summary" },
      { id: "launch-recommendation-package", label: "Launch Recommendation" },
      { id: "launch-decision-dashboard", label: "Decision Dashboard" },
      { id: "launch-decision-history", label: "Decision History" },
      { id: "post-launch-operations", label: "Post Launch Operations" },
      { id: "post-launch-platform-health", label: "Platform Health" },
      { id: "post-launch-customer-health", label: "Customer Health" },
      { id: "post-launch-governance-health", label: "Governance Health" },
      { id: "post-launch-incident-health", label: "Incident Health" },
      { id: "post-launch-commercial-health", label: "Commercial Health" },
      { id: "post-launch-operations-dashboard", label: "Operations Dashboard" },
      { id: "settings", label: "Settings" },
      { id: "runtime-tunnel", label: "Runtime Tunnel" },
      { id: "mcp-bridge", label: "MCP Bridge" },
      { id: "research-config", label: "Research" },
    ],
  },
];

export const VIEW_LABELS: Record<MissionControlView, string> = {
  ...Object.fromEntries(
    SIDEBAR_SECTIONS.flatMap((s) => s.items.map((i) => [i.id, i.label])),
  ),
  "workflow-workspaces": "Workspaces",
  "workflow-operations": "Operations",
  "workflow-infrastructure": "Infrastructure",
  "workflow-intelligence": "Intelligence",
  "workflow-settings": "Settings",
  "arbiter-panel": "Multi-model arbiter",
} as Record<MissionControlView, string>;

export type MissionControlDataGroup = "overview" | "browser" | "jobs" | "settings" | "engineering" | "agents";

export function viewDataGroup(view: MissionControlView): MissionControlDataGroup {
  if (
    view === "agent-orchestration" ||
    view === "deep-research" ||
    view === "evidence-gallery" ||
    view === "research-library" ||
    view === "blind-model-eval" ||
    view === "arbiter-panel" ||
    view === "active-agents" ||
    view === "agent-timelines" ||
    view === "coordination-graph" ||
    view === "evidence-merge" ||
    view === "operational-intelligence" ||
    view === "operational-replay" ||
    view === "evidence-graph" ||
    view === "agent-evidence" ||
    view === "engineering-proposals" ||
    view === "agent-policies" ||
    view === "delegated-tasks" ||
    view === "subagent-sessions"
  ) {
    return "agents";
  }
  if (
    view === "local-workspaces" ||
    view === "repo-diagnostics" ||
    view === "architecture-maps" ||
    view === "git-activity" ||
    view === "dependency-health" ||
    view === "test-intelligence" ||
    view === "pr-proposals" ||
    view === "engineering-execution" ||
    view === "sandbox-executions" ||
    view === "validation-center" ||
    view === "diff-explorer" ||
    view === "pr-drafts-center" ||
    view === "rollback-snapshots" ||
    view === "engineering-audit" ||
    view === "operational-reality" ||
    view === "operational-anomalies" ||
    view === "operational-drift" ||
    view === "deployment-stability" ||
    view === "cross-provider-correlation" ||
    view === "workflow-health" ||
    view === "dependency-risk" ||
    view === "recommendation-queue" ||
    view === "telemetry-freshness" ||
    view === "intelligence-replay" ||
    view === "workspace-active" ||
    view === "workspace-desktop" ||
    view === "workspace-terminal" ||
    view === "workspace-evidence" ||
    view === "workspace-replay" ||
    view === "workspace-files" ||
    view === "workspace-sandbox" ||
    view === "workspace-memory" ||
    view === "presence-feed" ||
    view === "presence-attention" ||
    view === "presence-timeline" ||
    view === "presence-focus" ||
    view === "presence-collaboration" ||
    view === "presence-recommendations" ||
    view === "presence-watch" ||
    view === "presence-memory" ||
    view === "trust-authority" ||
    view === "trust-replay" ||
    view === "trust-governance" ||
    view === "trust-confidence" ||
    view === "trust-signal-quality" ||
    view === "trust-correlation" ||
    view === "trust-metrics" ||
    view === "trust-recovery" ||
    view === "truth-capability-matrix" ||
    view === "truth-provider-readiness" ||
    view === "truth-verification-coverage" ||
    view === "truth-mutation-reliability" ||
    view === "truth-operational-honesty" ||
    view === "truth-runtime-validation" ||
    view === "truth-reality-harness" ||
    view === "truth-production-readiness" ||
    view === "reliability-providers" ||
    view === "reliability-deployment-verification" ||
    view === "reliability-recovery-runtime" ||
    view === "reliability-mutation-reconciliation" ||
    view === "reliability-rollback-integrity" ||
    view === "reliability-runtime-stabilization" ||
    view === "reliability-operational-confidence" ||
    view === "reliability-reality-validation" ||
    view === "infra-container-intelligence" ||
    view === "infra-kubernetes-runtime" ||
    view === "infra-runtime-topology" ||
    view === "infra-infrastructure-health" ||
    view === "infra-resource-pressure" ||
    view === "infra-drift-detection" ||
    view === "infra-cluster-recovery" ||
    view === "infra-infrastructure-truth" ||
    view === "reliability-continuous-verification" ||
    view === "reliability-recovery-orchestration" ||
    view === "reliability-drift-intelligence" ||
    view === "reliability-predictive-operations" ||
    view === "reliability-production-confidence" ||
    view === "reliability-reliability-memory" ||
    view === "reliability-operational-trajectory" ||
    view === "reliability-confidence-forecasting" ||
    view === "synthesis-quality" ||
    view === "synthesis-recommendations" ||
    view === "synthesis-conversational-trust" ||
    view === "synthesis-presentation-safety" ||
    view === "synthesis-response-elegance" ||
    view === "synthesis-human-trust" ||
    view === "synthesis-recommendation-replay" ||
    view === "synthesis-conversational-recovery" ||
    view === "conv-reliability" ||
    view === "conv-recommendation-quality" ||
    view === "conv-trust-calibration" ||
    view === "conv-presentation-integrity" ||
    view === "conv-interaction-elegance" ||
    view === "conv-conversational-replay" ||
    view === "conv-recommendation-intelligence" ||
    view === "conv-human-trust-signals" ||
    view === "conv-convergence" ||
    view === "conv-interaction-layers" ||
    view === "conv-trust-maturity" ||
    view === "conv-synthesis-consistency" ||
    view === "conv-production-interaction" ||
    view === "conv-maturity-profile" ||
    view === "conv-surface-integrity" ||
    view === "conv-trust-threshold" ||
    view === "prod-deployment-truth" ||
    view === "prod-rollback-integrity" ||
    view === "prod-runtime-stabilization" ||
    view === "prod-topology-recovery" ||
    view === "prod-operational-decay" ||
    view === "prod-production-qualification" ||
    view === "prod-sustained-verification" ||
    view === "prod-recovery-confidence" ||
    view === "rt-reconciliation" ||
    view === "rt-operational-patience" ||
    view === "rt-runtime-decay" ||
    view === "rt-sustained-verification" ||
    view === "rt-recovery-truth" ||
    view === "rt-replay-stability" ||
    view === "rt-topology-alignment" ||
    view === "rt-operational-windows" ||
    view === "rtc-runtime-truth" ||
    view === "rtc-stability-windows" ||
    view === "rtc-replay-convergence" ||
    view === "rtc-dependency-stability" ||
    view === "rtc-topology-truth" ||
    view === "rtc-operational-decay" ||
    view === "rtc-sustained-confidence" ||
    view === "rtc-recovery-continuity" ||
    view === "ccg-convergence-cognition" ||
    view === "ccg-infrastructure-intuition" ||
    view === "ccg-temporal-confidence" ||
    view === "ccg-kubernetes-convergence" ||
    view === "ccg-replay-continuity" ||
    view === "ccg-long-tail-stability" ||
    view === "ccg-operational-memory" ||
    view === "ccg-runtime-trajectories" ||
    view === "rci-recovery-continuity" ||
    view === "rci-temporal-trust" ||
    view === "rci-infrastructure-convergence" ||
    view === "rci-replay-persistence" ||
    view === "rci-adaptive-verification" ||
    view === "rci-long-tail-stability" ||
    view === "rci-topology-resilience" ||
    view === "rci-recovery-memory" ||
    view === "rsc-operational-resilience" ||
    view === "rsc-infrastructure-fragility" ||
    view === "rsc-temporal-trust-evolution" ||
    view === "rsc-kubernetes-resilience" ||
    view === "rsc-replay-resilience" ||
    view === "rsc-long-tail-stability" ||
    view === "rsc-recovery-durability" ||
    view === "rsc-operational-trajectories" ||
    view === "ors-operational-resilience" ||
    view === "ors-runtime-fragility" ||
    view === "ors-sustained-trust" ||
    view === "ors-kubernetes-durability" ||
    view === "ors-replay-resilience" ||
    view === "ors-long-tail-stability" ||
    view === "ors-recovery-durability" ||
    view === "ors-operational-trajectories" ||
    view === "poc-predictive-stability" ||
    view === "poc-fragility-acceleration" ||
    view === "poc-replay-forecasting" ||
    view === "poc-topology-forecasting" ||
    view === "poc-operational-fatigue" ||
    view === "poc-stability-projection" ||
    view === "poc-recovery-forecasting" ||
    view === "poc-predictive-memory" ||
    view === "rfi-runtime-fragility" ||
    view === "rfi-degradation-acceleration" ||
    view === "rfi-replay-erosion" ||
    view === "rfi-topology-fragility" ||
    view === "rfi-operational-fatigue" ||
    view === "rfi-predictive-stability" ||
    view === "rfi-recovery-fragility" ||
    view === "rfi-fragility-memory" ||
    view === "ltf-long-tail-forecasting" ||
    view === "ltf-operational-survivability" ||
    view === "ltf-replay-longevity" ||
    view === "ltf-topology-sustainability" ||
    view === "ltf-resilience-exhaustion" ||
    view === "ltf-stability-endurance" ||
    view === "ltf-autonomous-stability" ||
    view === "ltf-forecasting-trajectories" ||
    view === "ltf-forecasting-memory" ||
    view === "ltr-long-tail-cognition" ||
    view === "ltr-runtime-survivability" ||
    view === "ltr-operational-endurance" ||
    view === "ltr-replay-continuity" ||
    view === "ltr-topology-endurance" ||
    view === "ltr-resilience-exhaustion" ||
    view === "ltr-runtime-persistence" ||
    view === "ltr-cognition-memory" ||
    view === "cog-operational-grounding" ||
    view === "cog-continuity-reconstruction" ||
    view === "cog-operational-context" ||
    view === "cog-governance-restraint" ||
    view === "cog-conversational-realism" ||
    view === "cog-telegram-persistence" ||
    view === "cog-partner-presence" ||
    view === "cog-cross-surface-convergence" ||
    view === "cog-live-operational-grounding" ||
    view === "cog-durable-jobs" ||
    view === "cog-durable-jobs-active" ||
    view === "cog-durable-jobs-artifacts" ||
    view === "cog-grounding-memory"
  ) {
    return "engineering";
  }
  if (
    view === "runtime-actions" ||
    view === "tracked-work" ||
    view === "operation-preflights" ||
    view === "mutation-audit"
  ) {
    return "jobs";
  }
  if (view === "browser-evidence" || view === "web-intelligence" || view === "research-intelligence" || view === "browser-profiles" || view === "audit-logs") {
    return "browser";
  }
  if (
    view === "credential-center" ||
    view === "provider-inventory" ||
    view === "integrations" ||
    view === "system-health" ||
    view === "tenant-onboarding" ||
    view === "identity-access-hardening" ||
    view === "users-roles" ||
    view === "platform-owner" ||
    view === "provider-connections" ||
    view === "channel-integration" ||
    view === "billing-entitlements" ||
    view === "customer-administration" ||
    view === "customer-audit-portal" ||
    view === "payment-integration-readiness" ||
    view === "saas-launch-readiness" ||
    view === "customer-support-success" ||
    view === "public-product-experience" ||
    view === "public-capability-explorer" ||
    view === "public-trust-explorer" ||
    view === "public-product-tour" ||
    view === "public-customer-journey" ||
    view === "public-education-center" ||
    view === "beta-launch-program" ||
    view === "beta-cohorts" ||
    view === "beta-feedback" ||
    view === "beta-success-metrics" ||
    view === "beta-operations-dashboard" ||
    view === "launch-operations-center" ||
    view === "launch-dashboard" ||
    view === "launch-risks" ||
    view === "launch-blockers" ||
    view === "launch-evidence" ||
    view === "launch-beta-operations" ||
    view === "launch-customer-operations" ||
    view === "launch-readiness-freeze" ||
    view === "launch-baseline" ||
    view === "launch-evidence-freeze" ||
    view === "launch-recommendation-freeze" ||
    view === "launch-freeze-blockers" ||
    view === "launch-freeze-risks" ||
    view === "launch-decision-package" ||
    view === "launch-executive-summary" ||
    view === "launch-recommendation-package" ||
    view === "launch-decision-dashboard" ||
    view === "launch-decision-history" ||
    view === "post-launch-operations" ||
    view === "post-launch-platform-health" ||
    view === "post-launch-customer-health" ||
    view === "post-launch-governance-health" ||
    view === "post-launch-incident-health" ||
    view === "post-launch-commercial-health" ||
    view === "post-launch-operations-dashboard" ||
    view === "settings" ||
    view === "runtime-tunnel" ||
    view === "mcp-bridge" ||
    view === "channel-tool-policy" ||
    view === "cron-governed-jobs" ||
    view === "proactive-automation" ||
    view === "governed-sandbox" ||
    view === "research-config" ||
    view === "enterprise-doctor" ||
    view === "enterprise-setup-wizard" ||
    view === "enterprise-config" ||
    view === "enterprise-health" ||
    view === "enterprise-demo" ||
    view === "production-deployment" ||
    view === "production-cluster" ||
    view === "production-orgs" ||
    view === "production-plugins" ||
    view === "production-observability" ||
    view === "production-metering" ||
    view === "production-upgrade" ||
    view === "production-security" ||
    view === "human-overview" ||
    view === "human-relational" ||
    view === "human-voice" ||
    view === "human-channels" ||
    view === "human-life" ||
    view === "human-actions" ||
    view === "human-ambient" ||
    view === "human-collaboration" ||
    view === "human-trust" ||
    view === "human-marketplace" ||
    view === "human-mobile" ||
    view === "human-living" ||
    view === "human-live-presence" ||
    view === "human-conversation" ||
    view === "human-copilot" ||
    view === "human-personal" ||
    view === "human-explainability" ||
    view === "human-thinking" ||
    view === "human-multimodal-voice" ||
    view === "human-continuity" ||
    view === "human-trust-controls" ||
    view === "integrity-routes" ||
    view === "integrity-features" ||
    view === "integrity-ui-alignment" ||
    view === "integrity-orphans" ||
    view === "integrity-diagnostics" ||
    view === "presence-attention-quality" ||
    view === "presence-interruption-budget" ||
    view === "presence-continuity-accuracy" ||
    view === "presence-operational-narrative" ||
    view === "presence-calm-intelligence" ||
    view === "presence-trust-signals" ||
    view === "presence-collaboration-quality" ||
    view === "companion-operational-reasoning" ||
    view === "companion-investigation" ||
    view === "companion-replay-intelligence" ||
    view === "companion-emotional-realism" ||
    view === "companion-attention-awareness" ||
    view === "companion-narrative-evolution" ||
    view === "companion-trust-retention"
  ) {
    return "settings";
  }
  return "overview";
}

export function isMissionControlView(value: string): value is MissionControlView {
  return (MISSION_CONTROL_VIEWS as readonly string[]).includes(value);
}

/** @deprecated Use MissionControlView — kept for tests referencing legacy tabs. */
export const MISSION_CONTROL_TABS = ["overview", "browser", "jobs", "settings"] as const;
export type MissionControlTab = (typeof MISSION_CONTROL_TABS)[number];
export const TAB_LABELS: Record<MissionControlTab, string> = {
  overview: "Overview",
  browser: "Browser Sessions",
  jobs: "Jobs",
  settings: "Settings",
};
export function isMissionControlTab(value: string): value is MissionControlTab {
  return (MISSION_CONTROL_TABS as readonly string[]).includes(value);
}
