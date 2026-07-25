# SPDX-License-Identifier: Apache-2.0
"""Post-mutation verification — evidence-based follow-through after governed mutations."""

from aethos_core.post_mutation_verification.verification_followup_router import (
    compose_post_mutation_verification_reply,
    is_post_mutation_verification_intent,
)
from aethos_core.post_mutation_verification.verification_intent_router import (
    classify_verification_intent,
    classify_verification_intent_with_context,
    is_intent_word,
    recent_mutation_lifecycle_exists,
    reset_pending_verification_for_tests,
    route_post_mutation_verification,
)

__all__ = [
    "classify_verification_intent",
    "classify_verification_intent_with_context",
    "compose_post_mutation_verification_reply",
    "is_intent_word",
    "is_post_mutation_verification_intent",
    "recent_mutation_lifecycle_exists",
    "reset_pending_verification_for_tests",
    "route_post_mutation_verification",
]
