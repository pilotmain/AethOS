# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.vercel_operation_capabilities import (
    VERCEL_OPERATION_CAPABILITIES,
    browser_runtime_required,
    is_api_capable,
    preflight_capability_metadata,
)


def test_operation_capability_matrix_api_domains():
    cap = VERCEL_OPERATION_CAPABILITIES["list_domains"]
    assert cap["api"] is True
    assert cap["browser_required"] is False
    assert is_api_capable("list_domains") is True


def test_logs_partial_api_does_not_require_browser_when_token_present():
    assert is_api_capable("check_logs") is True
    assert browser_runtime_required("check_logs", api_token_available=True) is False
    assert browser_runtime_required("check_logs", api_token_available=False) is True


def test_preflight_capability_metadata_shape():
    meta = preflight_capability_metadata("list_deployments")
    assert "auth_method" in meta
    assert "api_capable" in meta
    assert "browser_runtime_required" in meta
