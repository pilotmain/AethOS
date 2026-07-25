# SPDX-License-Identifier: Apache-2.0
"""Solo execution mode for local trusted developer sessions."""

from aethos_core.solo_execution.solo_execution_mode import (
    SoloEligibilityResult,
    SoloExecutionConfig,
    build_solo_railway_execution_policy,
    compose_solo_greenfield_intro,
    is_solo_execution_mode_enabled,
    load_solo_execution_config,
    validate_solo_greenfield_eligibility,
)
from aethos_core.solo_execution.solo_final_report import (
    build_solo_final_report_payload,
    compose_solo_greenfield_final_report,
)
from aethos_core.solo_execution.solo_greenfield_executor import (
    maybe_run_solo_greenfield_execution,
    run_solo_greenfield_execution,
)

__all__ = [
    "SoloEligibilityResult",
    "SoloExecutionConfig",
    "build_solo_final_report_payload",
    "build_solo_railway_execution_policy",
    "compose_solo_greenfield_final_report",
    "compose_solo_greenfield_intro",
    "is_solo_execution_mode_enabled",
    "load_solo_execution_config",
    "maybe_run_solo_greenfield_execution",
    "run_solo_greenfield_execution",
    "validate_solo_greenfield_eligibility",
]
