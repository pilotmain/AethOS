# SPDX-License-Identifier: Apache-2.0
"""Operational preflight — intent → target → read-only plan (no mutations in Phase 9.2)."""

from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.target_resolution import resolve_vercel_target

__all__ = [
    "OperationPreflight",
    "infer_operation_preflight_intent",
    "resolve_vercel_target",
]
