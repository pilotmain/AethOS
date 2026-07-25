# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.operation_models import OperationPreflight


def test_preflight_to_dict_keeps_debug_fields_separately_addressable():
    pf = OperationPreflight(
        provider="vercel",
        operation_type="list_domains",
        target_name="invoicepilot",
        target_status="resolved",
        current_state={
            "api_capable": True,
            "credential_id": "cred-1",
            "resolution_source": "provider_api",
            "production_url": "invoicepilot.vercel.app",
        },
    )
    d = pf.to_dict()
    assert d["current_state"]["api_capable"] is True
    assert d["current_state"]["production_url"] == "invoicepilot.vercel.app"
