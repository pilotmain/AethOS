# SPDX-License-Identifier: Apache-2.0

from aethos_core.providers.base.auth_adapter import AuthAdapter
from aethos_core.providers.vercel.auth import VercelAuthAdapter


def test_auth_adapter_contract_methods():
    required = {
        "connection_status",
        "list_credentials",
        "resolve_best_auth_method",
        "test_credential",
        "revoke_credential",
    }
    assert required.issubset(set(AuthAdapter.__abstractmethods__))


def test_vercel_auth_exposes_contract_methods():
    adapter = VercelAuthAdapter()
    for name in (
        "connection_status",
        "list_credentials",
        "resolve_best_auth_method",
        "test_credential",
        "revoke_credential",
    ):
        assert callable(getattr(adapter, name))
