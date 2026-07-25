# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.providers.base.evidence_adapter import EvidenceItem
from aethos_core.providers.base.inventory_adapter import InventoryAdapter
from aethos_core.providers.base.mutation_adapter import MutationAdapter, MutationNotEnabledError
from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter


def test_provider_base_contract_modules_expose_abcs():
    assert AuthAdapter.__abstractmethods__
    assert InventoryAdapter.__abstractmethods__
    assert ReadonlyExecutionAdapter.__abstractmethods__
    assert MutationAdapter.__abstractmethods__


def test_evidence_item_round_trip():
    item = EvidenceItem(
        source="provider_api",
        type="domain_record",
        confidence="confirmed",
        message="example.com",
        tier="primary",
    )
    restored = EvidenceItem.from_dict(item.to_dict())
    assert restored.source == "provider_api"
    assert restored.type == "domain_record"
    assert restored.tier == "primary"


def test_mutation_adapter_disabled_by_default():
    from aethos_core.providers.vercel.provider import VercelMutationAdapter

    adapter = VercelMutationAdapter()
    assert adapter.enabled is False
    try:
        adapter.execute(operation="redeploy", params={})
        assert False, "expected MutationNotEnabledError"
    except MutationNotEnabledError:
        pass
