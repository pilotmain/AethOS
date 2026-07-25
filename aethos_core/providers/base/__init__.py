# SPDX-License-Identifier: Apache-2.0
"""Provider-neutral contracts — orchestration stays generic; adapters stay provider-specific."""

from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.providers.base.capability_matrix import (
    OperationCapability,
    is_api_capable,
    is_api_only,
    normalize_legacy_capability,
)
from aethos_core.providers.base.evidence_adapter import EvidenceItem
from aethos_core.providers.base.inventory_adapter import InventoryAdapter
from aethos_core.providers.base.mutation_adapter import MutationAdapter
from aethos_core.providers.base.provider_registry import ProviderRegistry, ProviderSpec
from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter

__all__ = [
    "AuthAdapter",
    "EvidenceItem",
    "InventoryAdapter",
    "MutationAdapter",
    "OperationCapability",
    "ProviderRegistry",
    "ProviderSpec",
    "ReadonlyExecutionAdapter",
    "is_api_capable",
    "is_api_only",
    "normalize_legacy_capability",
]
