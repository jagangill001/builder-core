from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class QueueDecision:
    queued: bool
    mode: str
    message: str


class InternalQueue:
    def worker_enabled(self) -> bool:
        return os.getenv("WORKER_ENABLED", "").strip().lower() in {"1", "true", "yes"}

    def submit(self, task_id: str) -> QueueDecision:
        if self.worker_enabled():
            return QueueDecision(queued=True, mode="external_worker_placeholder", message=f"Task {task_id} queued for worker.")
        return QueueDecision(queued=False, mode="immediate", message=f"Task {task_id} will process immediately.")


internal_queue = InternalQueue()
