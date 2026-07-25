# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_E2 — intelligence runtime optimization program."""

from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_contract import (
    INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID,
)
from aethos_core.workstreams.intelligence_runtime_optimization_program.intelligence_runtime_optimization_program_service import (
    build_intelligence_runtime_optimization_program,
)

__all__ = [
    "INTELLIGENCE_RUNTIME_OPTIMIZATION_PROGRAM_ID",
    "build_intelligence_runtime_optimization_program",
]
