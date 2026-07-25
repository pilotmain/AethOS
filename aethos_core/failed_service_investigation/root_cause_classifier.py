# SPDX-License-Identifier: Apache-2.0
"""Deep root-cause classification for failed-service diagnosis."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal

Confidence = Literal["low", "medium", "high"]

Category = Literal[
    "database_storage_issue",
    "database_startup_failure",
    "database_startup_or_storage_activity",
    "storage_permission_issue",
    "authentication_or_secret_issue",
    "network_dependency_issue",
    "resource_pressure",
    "crash_loop",
    "build_failure",
    "missing_env_variable",
    "port_binding_issue",
    "start_command_error",
    "unknown_runtime_failure",
    "insufficient_evidence",
]


@dataclass
class RootCauseClassification:
    category: str
    label: str
    confidence: Confidence
    summary: str
    interpretation: list[str] = field(default_factory=list)
    next_checks: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)
    log_signals: list[str] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)
    suggests_mutation: bool = False
    suggested_operation: str | None = None
    bounded_diagnosis: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "label": self.label,
            "confidence": self.confidence,
            "summary": self.summary,
            "interpretation": list(self.interpretation),
            "next_checks": list(self.next_checks),
            "recommended_actions": list(self.recommended_actions),
            "log_signals": list(self.log_signals),
            "evidence_gaps": list(self.evidence_gaps),
            "suggests_mutation": self.suggests_mutation,
            "suggested_operation": self.suggested_operation,
            "bounded_diagnosis": self.bounded_diagnosis,
        }


_RULES: list[tuple[str, str, Confidence, re.Pattern[str], list[str], list[str], str | None, bool]] = [
    (
        "missing_env_variable",
        "Missing environment variable",
        "high",
        re.compile(r"(?i)(missing|required|undefined).*(env|environment|variable)|ENV\s+.*not\s+set"),
        [
            "Startup failed because required configuration is absent.",
            "This is usually fixable by setting the missing variable and redeploying.",
        ],
        [
            "Confirm which env var is missing in Railway service settings",
            "Compare against project documentation or sibling services",
        ],
        "redeploy",
        True,
    ),
    (
        "port_binding_issue",
        "Port binding issue",
        "high",
        re.compile(r"(?i)(EADDRINUSE|address already in use|bind.*port|listen EACCES|failed to bind)"),
        ["The process could not bind to the configured port."],
        ["Verify PORT env and start command listen address", "Check for duplicate services on the same port"],
        "restart",
        True,
    ),
    (
        "network_dependency_issue",
        "Network or dependency connectivity issue",
        "high",
        re.compile(
            r"(?i)(ECONNREFUSED|connection refused|could not connect|database.*unreachable|redis.*unreachable|ENOTFOUND|getaddrinfo)"
        ),
        ["The service cannot reach a required dependency over the network."],
        ["Verify dependency URL/host credentials", "Check private networking and firewall rules"],
        "redeploy",
        True,
    ),
    (
        "authentication_or_secret_issue",
        "Authentication or secret issue",
        "high",
        re.compile(r"(?i)(authentication failed|auth failed|invalid credentials|access denied|wrong password|unauthorized|bad auth)"),
        ["Credentials or secrets appear invalid or missing for a protected dependency."],
        ["Verify DATABASE_URL / API keys / secret references", "Rotate credentials if recently changed"],
        "redeploy",
        True,
    ),
    (
        "resource_pressure",
        "Resource pressure",
        "high",
        re.compile(r"(?i)(out of memory|OOM|memory limit|heap out of memory|not enough disk|no space left|disk quota)"),
        ["The service hit memory or disk limits during startup or runtime."],
        ["Review Railway resource limits and volume size", "Inspect memory/disk usage trends around failure time"],
        "redeploy",
        True,
    ),
    (
        "storage_permission_issue",
        "Storage permission issue",
        "high",
        re.compile(r"(?i)(permission denied|EACCES|read-only file system|cannot open.*data directory)"),
        ["The process lacks permission to read or write its data directory or storage files."],
        ["Check volume mount permissions and data path ownership", "Verify Railway volume configuration"],
        None,
        False,
    ),
    (
        "database_storage_issue",
        "Database storage issue",
        "high",
        re.compile(r"(?i)(corruption|corrupt|fatal assertion|data directory|lock file|storage engine error)"),
        ["Database storage files or recovery state may be damaged or misconfigured."],
        [
            "Inspect full database logs around the failure timestamp",
            "Check volume/disk/storage configuration",
            "Review whether data path changed across restarts",
        ],
        None,
        False,
    ),
    (
        "build_failure",
        "Build failure",
        "high",
        re.compile(r"(?i)(build failed|npm ERR!|pnpm ERR!|compile error|docker build)"),
        ["The deployment failed during build, before or instead of healthy runtime."],
        ["Open build logs for the failed deployment", "Fix source/build config before redeploying"],
        "deploy",
        True,
    ),
    (
        "start_command_error",
        "Start command or module error",
        "high",
        re.compile(r"(?i)(command not found|ENOENT.*start|cannot find module|module not found|failed to start)"),
        ["The configured start command or entry module is invalid."],
        ["Verify start command, package entrypoint, and build output", "Confirm dependencies are installed in the image"],
        "deploy",
        True,
    ),
    (
        "crash_loop",
        "Crash loop",
        "medium",
        re.compile(r"(?i)(crash|exited with code|SIGTERM|SIGKILL|process exited|container restart|exit code [1-9])"),
        ["The process started but exited repeatedly or crashed during startup."],
        [
            "Fetch logs immediately before each exit",
            "Check Railway service events / exit code",
            "Identify whether crash is config, dependency, or runtime code",
        ],
        "restart",
        False,
    ),
]

_FATAL_DB_RX = re.compile(
    r"(?i)(corruption|corrupt|permission denied|EACCES|out of memory|OOM|not enough disk|exit code|fatal|assertion|panic|error)"
)
_WIREDTIGER_RX = re.compile(r"(?i)wiredtiger")
_DB_ACTIVITY_RX = re.compile(r"(?i)(wiredtiger|recovery|checkpoint|lock file|data directory|storage engine)")


def _is_database_service(service_name: str) -> bool:
    name = (service_name or "").lower()
    return "mongo" in name or name in {"postgres", "postgresql", "mysql", "redis", "database", "db"}


def _log_corpus(logs: list[dict[str, Any]], *, health_summary: str = "") -> str:
    parts = [health_summary]
    for row in logs:
        if isinstance(row, dict):
            parts.append(str(row.get("message") or row.get("msg") or ""))
    return "\n".join(parts)


def _extract_signals(corpus: str, pattern: re.Pattern[str], limit: int = 3) -> list[str]:
    return [m.group(0)[:160] for m in pattern.finditer(corpus)][:limit]


def classify_root_cause(
    *,
    logs: list[dict[str, Any]],
    service_name: str = "",
    deployment_state: str = "",
    health_summary: str = "",
) -> RootCauseClassification:
    corpus = _log_corpus(logs, health_summary=health_summary)
    is_db = _is_database_service(service_name)

    if not logs:
        return RootCauseClassification(
            category="insufficient_evidence",
            label="Insufficient evidence",
            confidence="low",
            summary="Not enough log evidence to classify root cause.",
            interpretation=["No runtime/deployment logs were available for classification."],
            next_checks=[
                "Fetch Railway deployment/runtime logs near the failure timestamp",
                "Inspect Railway service events and exit code",
                "Verify env/config and dependency connectivity",
            ],
            recommended_actions=[f"show {service_name} error logs" if service_name else "fetch service error logs"],
            evidence_gaps=["No log lines available"],
            bounded_diagnosis=True,
        )

    for category, label, confidence, pattern, interpretation, next_checks, suggested_op, suggests_mutation in _RULES:
        if pattern.search(corpus):
            return RootCauseClassification(
                category=category,
                label=label,
                confidence=confidence,
                summary=label,
                interpretation=list(interpretation),
                next_checks=list(next_checks),
                recommended_actions=_recommended_for(category, service_name),
                log_signals=_extract_signals(corpus, pattern),
                suggests_mutation=suggests_mutation and confidence == "high",
                suggested_operation=suggested_op,
            )

    if is_db and _DB_ACTIVITY_RX.search(corpus) and not _FATAL_DB_RX.search(corpus):
        signals = _extract_signals(corpus, _WIREDTIGER_RX) or _extract_signals(corpus, _DB_ACTIVITY_RX)
        return RootCauseClassification(
            category="database_startup_or_storage_activity",
            label="Database startup or storage activity",
            confidence="medium" if _WIREDTIGER_RX.search(corpus) else "low",
            summary="Database startup/storage activity without a clear fatal error",
            interpretation=[
                "WiredTiger and similar messages usually come from MongoDB storage engine startup or recovery.",
                "The current excerpt does not show the exact fatal error.",
                "This could be normal startup noise unless paired with crash, exit, disk, or permission errors.",
            ],
            next_checks=[
                "Fetch surrounding database logs near the failure timestamp",
                "Check Railway service events / exit code",
                "Check volume/disk/storage configuration",
                "Check whether the database restarted with an incompatible storage or data path",
                "Avoid redeploy until the failure reason is confirmed",
            ],
            recommended_actions=[
                f"show {service_name} error logs" if service_name else "show error logs",
                f"inspect {service_name} service events" if service_name else "inspect service events",
            ],
            log_signals=signals,
            evidence_gaps=[
                "Available logs only show startup/storage activity, not a definitive fatal error line",
            ],
            suggests_mutation=False,
            suggested_operation=None,
            bounded_diagnosis=True,
        )

    if is_db and _DB_ACTIVITY_RX.search(corpus):
        return RootCauseClassification(
            category="database_startup_failure",
            label="Database startup failure",
            confidence="medium",
            summary="Database failed during startup or recovery",
            interpretation=[
                "Database logs show startup/recovery activity together with error indicators.",
                "Inspect the lines immediately before exit or crash for the root trigger.",
            ],
            next_checks=[
                "Fetch full MongoDB logs around failure timestamp",
                "Check disk/volume and permission state",
                "Review recent config or version changes",
            ],
            recommended_actions=[f"show {service_name} error logs" if service_name else "show error logs"],
            log_signals=_extract_signals(corpus, _DB_ACTIVITY_RX),
            suggests_mutation=False,
            bounded_diagnosis=True,
        )

    if str(deployment_state or "").lower() in {"failed", "crashed", "error"}:
        last_signal = str(logs[-1].get("message") or logs[-1].get("msg") or "")[:160]
        return RootCauseClassification(
            category="unknown_runtime_failure",
            label="Unknown runtime failure",
            confidence="low",
            summary="Service is failed but logs do not match a known failure class",
            interpretation=[
                "The service is marked failed, but available logs do not map to a confident root-cause category.",
                "More surrounding log lines and service events are needed before proposing a fix.",
            ],
            next_checks=[
                "Fetch more log lines around the failure timestamp",
                "Inspect Railway deployment/build events",
                "Compare env/config against last known good deployment",
            ],
            recommended_actions=[f"show {service_name} error logs" if service_name else "show error logs"],
            log_signals=[last_signal] if last_signal else [],
            evidence_gaps=["Log excerpt too generic for confident classification"],
            suggests_mutation=False,
            bounded_diagnosis=True,
        )

    return RootCauseClassification(
        category="unknown_runtime_failure",
        label="Unknown runtime failure",
        confidence="low",
        summary="Runtime failure with limited classifiable evidence",
        interpretation=["Available evidence is insufficient for a specific root-cause category."],
        next_checks=["Fetch additional logs and service events before mutation"],
        recommended_actions=[f"inspect {service_name} service events" if service_name else "inspect service events"],
        log_signals=[str(logs[-1].get("message") or "")[:160]] if logs else [],
        suggests_mutation=False,
        bounded_diagnosis=True,
    )


def _recommended_for(category: str, service_name: str) -> list[str]:
    name = service_name or "service"
    if category == "crash_loop":
        return [f"show {name} error logs", f"inspect {name} service events"]
    if category in {"missing_env_variable", "authentication_or_secret_issue"}:
        return [f"inspect {name} env/config", f"show {name} deployment logs"]
    if category.startswith("database") or category == "storage_permission_issue":
        return [f"show {name} error logs", f"inspect {name} service events"]
    return [f"show {name} error logs"]
