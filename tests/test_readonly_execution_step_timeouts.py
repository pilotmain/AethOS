# SPDX-License-Identifier: Apache-2.0

import time

import pytest

from aethos_core.operations.execution.execution_step_timeouts import ExecutionStepTimeoutError, run_with_timeout


def test_run_with_timeout_returns_result():
    assert run_with_timeout(lambda: 42, timeout_sec=2.0, step="fast") == 42


def test_run_with_timeout_raises():
    def slow():
        time.sleep(2)
        return 1

    with pytest.raises(ExecutionStepTimeoutError) as exc:
        run_with_timeout(slow, timeout_sec=0.1, step="slow_step")
    assert exc.value.step == "slow_step"
