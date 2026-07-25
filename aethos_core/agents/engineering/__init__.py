# SPDX-License-Identifier: Apache-2.0
"""Engineering agent substrate — deep readonly intelligence."""

from aethos_core.agents.engineering.architecture_reasoning import run_architecture_reasoning
from aethos_core.agents.engineering.ci_reasoning import run_ci_reasoning
from aethos_core.agents.engineering.dependency_reasoning import run_dependency_reasoning
from aethos_core.agents.engineering.git_hotspots import run_git_hotspot_analysis
from aethos_core.agents.engineering.pr_proposal_engine import build_dependency_modernization_proposal
from aethos_core.agents.engineering.risk_scoring import classify_severity

__all__ = [
    "run_architecture_reasoning",
    "run_ci_reasoning",
    "run_dependency_reasoning",
    "run_git_hotspot_analysis",
    "build_dependency_modernization_proposal",
    "classify_severity",
]
