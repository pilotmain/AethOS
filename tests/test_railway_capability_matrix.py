# SPDX-License-Identifier: Apache-2.0

import aethos_core.providers  # noqa: F401
from aethos_core.providers.base.capability_matrix import is_api_capable
from aethos_core.providers.railway.provider import ensure_railway_registered


def test_railway_readonly_capabilities_enabled():
    spec = ensure_railway_registered()
    enabled_readonly = {
        op
        for op, cap in spec.capabilities.items()
        if cap.enabled and not cap.mutation and is_api_capable(cap)
    }
    assert "list_deployments" in enabled_readonly
    assert "project_details" in enabled_readonly
    assert "check_logs" in enabled_readonly
    assert "why_down" in enabled_readonly


def test_railway_mutations_declared_api_supported():
    spec = ensure_railway_registered()
    for op in ("redeploy", "restart"):
        cap = spec.capabilities[op]
        assert cap.mutation is True
        assert cap.enabled is True
    # set_env_var is now hardened on Railway — execute_railway_set_env_var does a
    # real governed stage+commit (mutations.py), so enabled=True is honest.
    cap = spec.capabilities["set_env_var"]
    assert cap.mutation is True
    assert cap.enabled is True
    assert cap.api_supported is True
