# SPDX-License-Identifier: Apache-2.0
"""Namespace resilience — namespace durability."""

from __future__ import annotations

from typing import Any

from aethos_core.kubernetes_resilience.namespace_resilience import assess_namespace_resilience


def assess_namespace_durability() -> dict[str, Any]:
    return assess_namespace_resilience()
