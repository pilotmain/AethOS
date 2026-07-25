# SPDX-License-Identifier: Apache-2.0
"""Operational memory & reliability history."""

__all__ = ["assess_reliability_memory"]


def __getattr__(name: str):
    if name == "assess_reliability_memory":
        from aethos_core.reliability_memory.runtime import assess_reliability_memory

        return assess_reliability_memory
    raise AttributeError(name)
