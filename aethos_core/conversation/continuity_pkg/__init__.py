# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — conversation continuity and topic persistence."""

from aethos_core.conversation.continuity_pkg.conversation_continuity_contract import (
    CONVERSATION_CONTINUITY_DOMAINS,
    CONVERSATION_CONTINUITY_FIX,
    CONVERSATION_CONTINUITY_ROUTE_ID,
)
from aethos_core.conversation.continuity_pkg.conversation_continuity_service import build_conversation_continuity

__all__ = [
    "CONVERSATION_CONTINUITY_DOMAINS",
    "CONVERSATION_CONTINUITY_FIX",
    "CONVERSATION_CONTINUITY_ROUTE_ID",
    "build_conversation_continuity",
]
