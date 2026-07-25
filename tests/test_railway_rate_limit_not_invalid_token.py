# SPDX-License-Identifier: Apache-2.0
"""Regression: a transient Railway/Vercel rate-limit (HTTP 429) must never be
classified as RAILWAY_TOKEN_INVALID / VERCEL_TOKEN_INVALID.

Reproduces the reported greenfield deploy bug where Railway returned
"Rate limit exceeded, please try again in 1460.28 seconds." but the flow blocked
with `RAILWAY_TOKEN_INVALID`, even though the token was valid and present.
"""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.provider_e2e_readiness.blocker_mapping import (
    is_auth_rejection_detail,
    is_rate_limited_detail,
    map_plain_text_blocker,
    map_railway_blockers,
    map_vercel_blockers,
)

_RATE_LIMIT_DETAIL = "Rate limit exceeded, please try again in 1460.28 seconds."


def test_rate_limit_detail_is_not_auth_rejection():
    assert is_rate_limited_detail(_RATE_LIMIT_DETAIL) is True
    assert is_auth_rejection_detail(_RATE_LIMIT_DETAIL) is False
    # 429 by status code is also transient regardless of text.
    assert is_rate_limited_detail("anything", status_code=429) is True
    assert is_auth_rejection_detail("anything", status_code=429) is False


def test_auth_rejection_still_detected():
    assert is_auth_rejection_detail("Not Authorized") is True
    assert is_auth_rejection_detail("HTTP 401 unauthorized") is True
    assert is_auth_rejection_detail("forbidden", status_code=403) is True
    assert is_rate_limited_detail("Not Authorized") is False


def test_map_railway_blockers_rate_limit_not_token_invalid():
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": False,
        "railway_api_connection_detail": _RATE_LIMIT_DETAIL,
        "railway_api_connection_status_code": 429,
    }
    blockers = map_railway_blockers(checks, settings=object(), include_mutation_gates=False)
    codes = [b.code for b in blockers]
    assert "RAILWAY_RATE_LIMITED" in codes
    assert "RAILWAY_TOKEN_INVALID" not in codes


def test_map_railway_blockers_auth_failure_still_token_invalid():
    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": False,
        "railway_api_connection_detail": "Not Authorized",
    }
    blockers = map_railway_blockers(checks, settings=object(), include_mutation_gates=False)
    assert blockers[0].code == "RAILWAY_TOKEN_INVALID"


def test_map_vercel_blockers_rate_limit_not_token_invalid():
    blockers = map_vercel_blockers(
        credential_ok=True,
        connection_ok=False,
        connection_detail=_RATE_LIMIT_DETAIL,
        include_mutation_gates=False,
    )
    codes = [b.code for b in blockers]
    assert "VERCEL_RATE_LIMITED" in codes
    assert "VERCEL_TOKEN_INVALID" not in codes


def test_plain_text_blocker_rate_limit():
    for provider in ("railway", "vercel"):
        blocker = map_plain_text_blocker(_RATE_LIMIT_DETAIL, provider=provider)
        assert blocker.code == f"{provider.upper()}_RATE_LIMITED"


def test_greenfield_flow_rate_limit_blocks_as_transient_not_invalid():
    from aethos_core.providers.railway.greenfield_deployment import greenfield_flow

    rate_limited_checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": False,
        "railway_api_connection_rate_limited": True,
        "railway_api_connection_status_code": 429,
        "railway_api_connection_detail": _RATE_LIMIT_DETAIL,
    }
    with patch.object(
        greenfield_flow,
        "_run_railway_greenfield_deployment_flow_impl",
        wraps=greenfield_flow._run_railway_greenfield_deployment_flow_impl,
    ), patch(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        return_value=rate_limited_checks,
    ):
        result = greenfield_flow.run_railway_greenfield_deployment_flow(
            "deploy killit from github repo to railway",
            session_id="rate-limit-regression",
        )
    assert result.blocked is True
    assert result.blocker_code == "RAILWAY_RATE_LIMITED"
    assert "RAILWAY_TOKEN_INVALID" not in result.reply
    assert "token is valid" in result.reply.lower()


def test_validate_railway_api_connection_marks_rate_limited():
    from aethos_core.providers.railway import credential_truth

    with patch.object(
        credential_truth,
        "list_services_with_status",
        return_value={"ok": False, "services": [], "error": _RATE_LIMIT_DETAIL, "status_code": 429},
    ):
        validation = credential_truth.validate_railway_api_connection("some-token")
    assert validation.ok is False
    assert validation.rate_limited is True
    assert validation.http_status == 429
    fields = validation.to_checks_fields()
    assert fields["railway_api_connection_rate_limited"] is True
    assert fields["railway_api_connection_status_code"] == 429


def test_soft_pass_unblocks_when_credential_validated():
    from aethos_core.providers.railway.deployment_readiness import deployment_readiness_checks as drc

    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": False,
        "railway_api_connection_rate_limited": True,
        "railway_api_connection_status_code": 429,
        "railway_api_connection_detail": _RATE_LIMIT_DETAIL,
        "railway_credential_source": "validated_vault",
    }
    drc._soft_pass_rate_limited_connection(checks, {"ok": False})
    assert checks["railway_api_connection_ok"] is True
    assert checks["railway_api_connection_soft_passed"] is True
    assert checks["railway_api_connection_soft_pass_reason"] == "rate_limited"


def test_soft_pass_does_not_unblock_on_auth_failure():
    from aethos_core.providers.railway.deployment_readiness import deployment_readiness_checks as drc

    checks = {
        "railway_credential_ok": True,
        "railway_api_connection_ok": False,
        "railway_api_connection_detail": "Not Authorized",
        "railway_credential_source": "validated_vault",
    }
    drc._soft_pass_rate_limited_connection(checks, {"ok": False})
    assert checks["railway_api_connection_ok"] is False
    assert "railway_api_connection_soft_passed" not in checks
