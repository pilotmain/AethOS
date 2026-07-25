# SPDX-License-Identifier: Apache-2.0
"""Queue backend — durable job queue abstraction."""

from __future__ import annotations

import json
import queue
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from time import time
from typing import Any
from uuid import uuid4

_persist_path = Path(__file__).resolve().parents[3] / "data" / "distributed" / "queue.jsonl"


class QueueBackend(ABC):
    backend_name: str = "abstract"

    @abstractmethod
    def enqueue(self, job_id: str, *, domain: str = "default") -> None: ...

    @abstractmethod
    def dequeue(self, *, timeout: float = 1.0) -> str | None: ...

    @abstractmethod
    def depth(self) -> int: ...

    @abstractmethod
    def snapshot(self) -> dict[str, Any]: ...


class InMemoryQueueBackend(QueueBackend):
    backend_name = "in_memory"

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._lock = threading.Lock()
        self._enqueued = 0
        self._dequeued = 0

    def enqueue(self, job_id: str, *, domain: str = "default") -> None:
        self._queue.put(job_id)
        with self._lock:
            self._enqueued += 1

    def dequeue(self, *, timeout: float = 1.0) -> str | None:
        try:
            job_id = self._queue.get(timeout=timeout)
            with self._lock:
                self._dequeued += 1
            return job_id
        except queue.Empty:
            return None

    def depth(self) -> int:
        return self._queue.qsize()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "backend": self.backend_name,
                "depth": self.depth(),
                "enqueued_total": self._enqueued,
                "dequeued_total": self._dequeued,
            }


class DurableFileQueueBackend(QueueBackend):
    """Crash-recoverable file-backed queue for team/enterprise modes."""

    backend_name = "durable_file"

    def __init__(self) -> None:
        _persist_path.parent.mkdir(parents=True, exist_ok=True)
        self._memory = InMemoryQueueBackend()
        self._recover()

    def enqueue(self, job_id: str, *, domain: str = "default") -> None:
        record = {"job_id": job_id, "domain": domain, "at": time(), "status": "pending"}
        with _persist_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        self._memory.enqueue(job_id, domain=domain)

    def dequeue(self, *, timeout: float = 1.0) -> str | None:
        return self._memory.dequeue(timeout=timeout)

    def depth(self) -> int:
        return self._memory.depth()

    def snapshot(self) -> dict[str, Any]:
        snap = self._memory.snapshot()
        snap["persist_path"] = str(_persist_path)
        snap["persisted_lines"] = self._count_lines()
        return snap

    def _recover(self) -> None:
        if not _persist_path.is_file():
            return
        for line in _persist_path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
                if row.get("status") == "pending":
                    self._memory.enqueue(str(row["job_id"]))
            except json.JSONDecodeError:
                continue

    def _count_lines(self) -> int:
        if not _persist_path.is_file():
            return 0
        return len(_persist_path.read_text(encoding="utf-8").splitlines())


_backend: QueueBackend | None = None


def get_queue_backend() -> QueueBackend:
    global _backend
    if _backend is None:
        from aethos_core.config import get_settings

        mode = getattr(get_settings(), "worker_mode", "embedded") or "embedded"
        deploy = getattr(get_settings(), "deployment_mode", "local") or "local"
        if mode == "standalone" or deploy in ("team", "enterprise", "hosted"):
            _backend = DurableFileQueueBackend()
        else:
            _backend = InMemoryQueueBackend()
    return _backend


def reset_queue_backend_for_tests() -> None:
    global _backend
    _backend = InMemoryQueueBackend()
    if _persist_path.is_file():
        _persist_path.unlink()
