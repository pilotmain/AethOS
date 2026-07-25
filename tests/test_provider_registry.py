# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.providers.base.provider_registry import ProviderRegistry
from aethos_core.providers.vercel.provider import register_vercel_provider


def test_provider_registry_lists_vercel():
    ProviderRegistry.clear_for_tests()
    try:
        register_vercel_provider()
        assert ProviderRegistry.get("vercel") is not None
        assert "vercel" in ProviderRegistry.list_names()
        catalog = ProviderRegistry.public_catalog()
        assert any(p["name"] == "vercel" for p in catalog)
    finally:
        ProviderRegistry.clear_for_tests()
        import aethos_core.providers as providers_pkg

        providers_pkg  # keep import
        from aethos_core.providers.vercel.provider import ensure_vercel_registered

        ensure_vercel_registered()
