# SPDX-License-Identifier: Apache-2.0
"""PHASE_J2 — real-world comparative performance program."""

from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_contract import (
    REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID,
)
from aethos_core.workstreams.real_world_comparative_performance_program.real_world_comparative_performance_program_service import (
    build_real_world_comparative_performance_program,
)

__all__ = [
    "REAL_WORLD_COMPARATIVE_PERFORMANCE_PROGRAM_ID",
    "build_real_world_comparative_performance_program",
]
