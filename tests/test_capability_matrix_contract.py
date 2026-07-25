# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.vercel_operation_capabilities import (
    VERCEL_OPERATION_CAPABILITIES,
    is_api_capable,
    is_api_only_operation,
    operation_capabilities,
)
from aethos_core.providers.base.capability_matrix import normalize_legacy_capability


def test_capability_matrix_contract_shape():
    cap = normalize_legacy_capability("list_domains", VERCEL_OPERATION_CAPABILITIES["list_domains"])
    d = cap.to_dict()
    assert d["operation"] == "list_domains"
    assert d["read_only"] is True
    assert d["mutation"] is False
    assert d["api_supported"] is True
    assert d["requires_approval"] is True


def test_vercel_operation_capabilities_bridge():
    caps = operation_capabilities("why_down")
    assert caps.get("operation") == "why_down"
    assert caps.get("api_supported") == "partial"
    assert is_api_capable("why_down") is True
    assert is_api_only_operation("list_domains") is True
    assert is_api_only_operation("why_down") is False
