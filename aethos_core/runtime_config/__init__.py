# SPDX-License-Identifier: Apache-2.0
"""Runtime configuration — UI-writable settings store with precedence over .env.

Deployed end users have no .env access, so every user-controllable capability must
be settable from Mission Control, persisted in a runtime store (SQLite, canonical),
and read by the code with .env as the operator default/fallback.

Precedence (effective_setting): runtime store -> .env / Settings -> field default.
Secrets never live here (vault only); dangerous/governance flags stay operator-only.
"""

from __future__ import annotations

from aethos_core.runtime_config.effective_settings import (
    apply_runtime_overrides,
    effective_attr,
    effective_bool,
    effective_setting,
    effective_str,
    list_effective_settings,
    revert_effective_setting,
    set_effective_setting,
)

__all__ = [
    "apply_runtime_overrides",
    "effective_attr",
    "effective_bool",
    "effective_setting",
    "effective_str",
    "list_effective_settings",
    "revert_effective_setting",
    "set_effective_setting",
]
