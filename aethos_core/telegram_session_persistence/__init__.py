# SPDX-License-Identifier: Apache-2.0
"""Telegram session persistence — persistent Telegram operational continuity."""

from aethos_core.telegram_session_persistence.session_bridge import hydrate_telegram_session, persist_telegram_continuity

__all__ = ["hydrate_telegram_session", "persist_telegram_continuity"]
