from __future__ import annotations

from app.workers.queue import internal_queue


def worker_status() -> dict[str, object]:
    return {
        "enabled": internal_queue.worker_enabled(),
        "mode": "external_worker_placeholder" if internal_queue.worker_enabled() else "immediate_processing",
        "message": "External worker execution is a foundation placeholder; immediate backend processing is active when disabled.",
    }
