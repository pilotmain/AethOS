# SPDX-License-Identifier: Apache-2.0
"""Active task frame runtime — operational task state."""

from aethos_core.task_frame.clarification_state import store_target_selection_task
from aethos_core.task_frame.task_continuation import compose_task_continuation_reply, has_active_task_frame
from aethos_core.task_frame.task_memory import clear_task_frames_for_tests, get_active_task_frame

__all__ = [
    "clear_task_frames_for_tests",
    "compose_task_continuation_reply",
    "get_active_task_frame",
    "has_active_task_frame",
    "store_target_selection_task",
]
