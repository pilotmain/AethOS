# SPDX-License-Identifier: Apache-2.0
"""Transport serialization guard tests."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

from aethos_core.chat.cognition_exception_boundary import sanitize_chat_result_for_transport
from aethos_core.chat.service import ChatTurnResult


class Status(Enum):
    FAILED = "failed"


@dataclass
class TargetState:
    service: str
    project: str


def test_datetime_metadata_serializes():
    result = sanitize_chat_result_for_transport(
        ChatTurnResult(
            reply="ok",
            intent="world_model_investigation_recap",
            meta={"created_at": datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc)},
        )
    )
    payload = json.dumps({"meta": result.meta})
    assert "2026-05-20" in payload


def test_exception_metadata_serializes():
    result = sanitize_chat_result_for_transport(
        ChatTurnResult(
            reply="ok",
            intent="world_model_investigation_recap",
            meta={"error": RuntimeError("bad metadata")},
        )
    )
    payload = json.dumps({"meta": result.meta})
    assert "RuntimeError" in payload


def test_dataclass_metadata_serializes():
    result = sanitize_chat_result_for_transport(
        ChatTurnResult(
            reply="ok",
            intent="world_model_investigation_recap",
            meta={"target": TargetState(service="MongoDB", project="pilotcore-sales-engine")},
        )
    )
    payload = json.dumps({"meta": result.meta})
    assert "MongoDB" in payload


def test_set_metadata_serializes():
    result = sanitize_chat_result_for_transport(
        ChatTurnResult(
            reply="ok",
            intent="world_model_investigation_recap",
            meta={"tags": {"wiredtiger", "failed_runtime_status"}, "path": Path("/tmp/state.json")},
        )
    )
    payload = json.dumps({"meta": result.meta})
    assert "wiredtiger" in payload
    assert "/tmp/state.json" in payload
    assert isinstance(result.meta["tags"], list)
