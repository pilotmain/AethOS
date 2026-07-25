# SPDX-License-Identifier: Apache-2.0
"""Provider-neutral operation capability matrix."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OperationCapability:
    operation: str
    read_only: bool = True
    mutation: bool = False
    api_supported: bool | str = False
    browser_fallback: bool | str = False
    browser_required: bool = False
    requires_approval: bool = True
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation": self.operation,
            "read_only": self.read_only,
            "mutation": self.mutation,
            "api_supported": self.api_supported,
            "browser_fallback": self.browser_fallback,
            "browser_required": self.browser_required,
            "requires_approval": self.requires_approval,
            "enabled": self.enabled,
        }


def normalize_legacy_capability(operation: str, raw: dict[str, Any]) -> OperationCapability:
    """Convert legacy provider capability dicts to the neutral contract."""
    api = raw.get("api", False)
    browser = raw.get("browser", False)
    mutation = bool(raw.get("mutation"))
    return OperationCapability(
        operation=operation,
        read_only=not mutation,
        mutation=mutation,
        api_supported=api if isinstance(api, (bool, str)) else bool(api),
        browser_fallback=browser if isinstance(browser, (bool, str)) else bool(browser),
        browser_required=bool(raw.get("browser_required", False)),
        requires_approval=True,
        enabled=bool(raw.get("enabled", True)),
    )


def is_api_capable(cap: OperationCapability) -> bool:
    api = cap.api_supported
    return api is True or api == "partial"


def is_api_only(cap: OperationCapability) -> bool:
    return cap.api_supported is True and cap.browser_fallback is False
