# SPDX-License-Identifier: Apache-2.0
"""Request-scoped memoization for the Mission Control build_* cascade.

Many Mission Control ``build_*`` services form a diamond dependency: a top-level
builder transitively invokes shared lower builders many times, each of which
re-runs the entire stack beneath it. With no caching this is exponential — a
single top-level build (e.g. the pilot-arc orchestrator) can take minutes, which
in turn pushes the full test suite past the CI time budget.

These builders are pure, read-only compositions: for a given ``session_id`` (and
the persisted state on disk, which does not change during a single logical build)
they return an equivalent value every time. This module provides a
context-scoped cache so that within one logical build each ``(builder, args)`` is
computed once. Nested re-requests return a ``deepcopy`` of the cached value, so
every caller still receives an independent object — behavior is identical to the
un-memoized version, only without the exponential recomputation. The cache lives
only for the duration of the outermost decorated call and is discarded on return,
so no state leaks across calls, requests, or tests.
"""

from __future__ import annotations

import contextvars
import copy
import functools
from typing import Any, Callable, TypeVar

_CACHE: contextvars.ContextVar[dict[Any, Any] | None] = contextvars.ContextVar(
    "mission_control_build_cache", default=None
)

F = TypeVar("F", bound=Callable[..., Any])

_SCALAR = (str, int, float, bool)


def _cache_key(fn: Callable[..., Any], kwargs: dict[str, Any]) -> tuple[Any, ...]:
    scalar_kwargs = tuple(
        sorted((k, v) for k, v in kwargs.items() if v is None or isinstance(v, _SCALAR))
    )
    return (fn.__module__, fn.__qualname__, scalar_kwargs)


def scoped_build(fn: F) -> F:
    """Memoize a pure ``build_*`` service within one logical build tree.

    Only the canonical keyword-only call shape (no positional args) is cached; any
    other call shape falls through to the wrapped function unchanged, so this can
    never silently mis-key a call.
    """

    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if args:
            return fn(*args, **kwargs)
        key = _cache_key(fn, kwargs)
        store = _CACHE.get()
        if store is not None:
            if key in store:
                return copy.deepcopy(store[key])
            result = fn(**kwargs)
            store[key] = result
            return copy.deepcopy(result)
        store = {}
        token = _CACHE.set(store)
        try:
            result = fn(**kwargs)
            store[key] = result
            return result
        finally:
            _CACHE.reset(token)

    return wrapper  # type: ignore[return-value]
