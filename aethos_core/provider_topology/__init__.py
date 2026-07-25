# SPDX-License-Identifier: Apache-2.0
"""Provider source binding intelligence — unified operational topology."""

from aethos_core.provider_topology.ambiguity_detection import BindingAmbiguity, detect_binding_ambiguity
from aethos_core.provider_topology.binding_verifier import BindingVerificationResult, compose_binding_mismatch_reply, verify_source_binding
from aethos_core.provider_topology.followup_lock import (
    compose_thread_continuation_reply,
    get_locked_thread_context,
    has_explicit_provider_switch,
    is_thread_continuation_followup,
    should_block_unrelated_preflight,
)
from aethos_core.provider_topology.provider_relationships import extract_github_repo_references
from aethos_core.provider_topology.repair_loop import compose_repair_proposal, execute_topology_repair
from aethos_core.provider_topology.source_binding import SourceBinding, binding_key
from aethos_core.provider_topology.topology_graph import ProviderTopologyGraph
from aethos_core.provider_topology.topology_memory import clear_topology_for_tests, get_binding, save_binding
from aethos_core.provider_topology.repo_reference_parser import parse_repo_reference
from aethos_core.provider_topology.source_binding_resolver import (
    SourceBindingResolution,
    attach_resolved_binding_to_params,
    check_stale_binding_regression,
    compose_stale_binding_regression_reply,
    refresh_params_source_binding,
    resolve_source_binding_for_service,
)
from aethos_core.provider_topology.repo_reconciliation import (
    ReconciliationResult,
    RepoRedirectResult,
    RepoRemoteInfo,
    compose_reconciliation_reply,
    detect_repo_redirect,
    read_local_git_remote,
    reconcile_source_binding,
    refresh_binding_from_remote,
)
from aethos_core.provider_topology.source_binding_chat import compose_source_binding_correction_reply
from aethos_core.provider_topology.topology_refresh import refresh_service_topology, refresh_topology_on_failure

__all__ = [
    "BindingAmbiguity",
    "BindingVerificationResult",
    "ProviderTopologyGraph",
    "SourceBinding",
    "binding_key",
    "clear_topology_for_tests",
    "compose_binding_mismatch_reply",
    "compose_repair_proposal",
    "compose_thread_continuation_reply",
    "detect_binding_ambiguity",
    "execute_topology_repair",
    "extract_github_repo_references",
    "get_binding",
    "get_locked_thread_context",
    "has_explicit_provider_switch",
    "is_thread_continuation_followup",
    "compose_source_binding_correction_reply",
    "RepoRemoteInfo",
    "RepoRedirectResult",
    "ReconciliationResult",
    "read_local_git_remote",
    "detect_repo_redirect",
    "reconcile_source_binding",
    "refresh_binding_from_remote",
    "compose_reconciliation_reply",
    "SourceBindingResolution",
    "resolve_source_binding_for_service",
    "refresh_params_source_binding",
    "check_stale_binding_regression",
    "compose_stale_binding_regression_reply",
    "attach_resolved_binding_to_params",
    "refresh_service_topology",
    "refresh_topology_on_failure",
    "save_binding",
    "should_block_unrelated_preflight",
    "verify_source_binding",
    "parse_repo_reference",
]
