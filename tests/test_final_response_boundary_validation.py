# SPDX-License-Identifier: Apache-2.0
"""Final response boundary validation tests."""

from __future__ import annotations

import json

from aethos_core.chat.service import ChatTurnResult, _finalize_result
from aethos_core.response_composition.final_response_validator import (
    JSON_VALIDATION_FAILURE,
    finalize_operational_response,
    validate_final_response,
    validate_json_final_response,
)


def test_broken_json_fence_blocked():
    broken = "header\n\n```json\n{\"summary\": {}}\n"
    result = validate_json_final_response(broken)
    assert result.ok is False


def test_truncated_json_blocked():
    broken = "header\n\n```json\n{\n  \"summary\": {\"failed\": 3},\n  \"failures\": [\n```"
    result = validate_json_final_response(broken)
    assert result.ok is False


def test_unclosed_markdown_fence_blocked():
    broken = "header\n\n```json\n{\"summary\": {\"failed\": 1}}\n"
    result = validate_final_response(broken, output_format="json")
    assert result.ok is False


def test_valid_json_passes_after_wrapper():
    payload = {"summary": {"total": 1}, "services": [{"service": "api"}], "metadata": {"filter": "none"}}
    body = f"Re-render.\n\n```json\n{json.dumps(payload, indent=2)}\n```"
    result = validate_json_final_response(body)
    assert result.ok is True
    assert result.parsed_json["services"][0]["service"] == "api"


def test_finalize_replaces_invalid_json_with_safe_error():
    broken = "Re-render.\n\n```json\n{\"failures\": [\n```"
    final = finalize_operational_response(broken, output_format="json")
    assert final == JSON_VALIDATION_FAILURE


def test_finalizer_cannot_corrupt_operational_json():
    payload = {"summary": {"total": 2, "failed": 1}, "services": [{"service": "worker"}], "metadata": {"filter": "failed_only"}}
    body = f"Using cached report.\n\n```json\n{json.dumps(payload, indent=2)}\n```"

    result = ChatTurnResult(
        reply=body,
        intent="operational_response_json",
        meta={"output_format": "json"},
    )
    finalized = _finalize_result(result, emotional_context={"session_id": "test", "channel": "chat"})
    assert finalized.reply == body
    assert validate_json_final_response(finalized.reply).ok is True
