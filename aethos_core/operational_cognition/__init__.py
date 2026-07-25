# SPDX-License-Identifier: Apache-2.0
"""Unified operational cognition runtime."""

from aethos_core.operational_cognition.cognition_graph import resolve_operational_cognition
from aethos_core.operational_cognition.types import OperationalCognitionDecision

__all__ = ["OperationalCognitionDecision", "resolve_operational_cognition"]
