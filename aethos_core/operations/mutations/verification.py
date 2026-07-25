# SPDX-License-Identifier: Apache-2.0
"""Post-mutation readonly verification — re-export canonical orchestration."""

from aethos_core.verification.orchestration.enqueue import (
    enqueue_mutation_verification,
    verification_operation_for_mutation,
)

__all__ = ["enqueue_mutation_verification", "verification_operation_for_mutation"]
