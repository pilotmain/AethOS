# SPDX-License-Identifier: Apache-2.0
"""Conversational realism — anti-generic-AI conversational shaping."""

from aethos_core.conversation.realism.anti_generic import is_generic_ai_response, reshape_generic_response
from aethos_core.conversation.realism.realism_runtime import assess_conversational_realism

__all__ = ["is_generic_ai_response", "reshape_generic_response", "assess_conversational_realism"]
