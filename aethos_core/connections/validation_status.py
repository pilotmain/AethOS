# SPDX-License-Identifier: Apache-2.0
"""Canonical provider credential validation states."""

from __future__ import annotations

CONFIGURED = "configured"
VALIDATED = "validated"
EXPIRED = "expired"
INSUFFICIENT_SCOPE = "insufficient_scope"
INVALID = "invalid"
MISSING = "missing"
SECRET_MISSING = "secret_missing"
RECONNECT_REQUIRED = "reconnect_required"
PERSISTENCE_FAILED = "persistence_failed"
