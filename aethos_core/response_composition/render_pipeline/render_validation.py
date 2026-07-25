# SPDX-License-Identifier: Apache-2.0
"""Render-time validation errors."""

from __future__ import annotations


class RenderValidationError(RuntimeError):
    """Raised when rendered output would violate integrity constraints."""
