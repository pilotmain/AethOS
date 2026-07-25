# SPDX-License-Identifier: Apache-2.0
"""Runtime drift intelligence."""

__all__ = ["assess_drift_intelligence"]


def __getattr__(name: str):
    if name == "assess_drift_intelligence":
        from aethos_core.drift_intelligence.runtime import assess_drift_intelligence

        return assess_drift_intelligence
    raise AttributeError(name)
