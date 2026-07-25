# SPDX-License-Identifier: Apache-2.0
"""Shared scope limits for governed greenfield live mutations."""

from __future__ import annotations

# Staging-only lanes for FIX 108/109 live mutations (not development/production).
STAGING_ONLY_ENVIRONMENTS = frozenset({"staging", "stage", "preview"})
