from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from typing import Any


class RateLimiterService:
    def __init__(self) -> None:
        self.enabled = str(os.environ.get("RATE_LIMIT_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}
        self.default_limit = int(os.environ.get("RATE_LIMIT_PER_MINUTE", "60") or "60")
        self._requests: dict[tuple[str, str], deque[float]] = defaultdict(deque)

    def record_request(self, ip_address: str | None, route: str) -> None:
        key = (ip_address or "unknown", route or "/")
        self._requests[key].append(time.time())

    def check_rate_limit(
        self,
        ip_address: str | None,
        route: str,
        limit: int | None = None,
        window_seconds: int = 60,
    ) -> dict[str, Any]:
        if not self.enabled:
            return {
                "allowed": True,
                "limited": False,
                "enabled": False,
                "remaining": None,
                "reset_seconds": window_seconds,
            }

        now = time.time()
        actual_limit = max(1, int(limit or self.default_limit))
        key = (ip_address or "unknown", route or "/")
        bucket = self._requests[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        bucket.append(now)
        limited = len(bucket) > actual_limit
        retry_after = max(1, int(window_seconds - (now - bucket[0]))) if bucket else window_seconds
        return {
            "allowed": not limited,
            "limited": limited,
            "enabled": True,
            "ip_address": ip_address,
            "route": route,
            "limit": actual_limit,
            "window_seconds": window_seconds,
            "count": len(bucket),
            "remaining": max(0, actual_limit - len(bucket)),
            "retry_after_seconds": retry_after,
            "warnings": [
                "In-memory rate limits reset on Cloud Run restart.",
                "Future production upgrades should use Firestore-backed limits, Redis/Memorystore, Cloud Armor, API Gateway, and admin authentication.",
            ],
        }

    def get_rate_limit_status(self) -> dict[str, Any]:
        active_buckets = []
        now = time.time()
        for (ip_address, route), bucket in self._requests.items():
            recent = [item for item in bucket if now - item <= 60]
            if recent:
                active_buckets.append({"ip_address": ip_address, "route": route, "recent_count": len(recent)})
        return {
            "enabled": self.enabled,
            "default_limit_per_minute": self.default_limit,
            "active_buckets": sorted(active_buckets, key=lambda item: item["recent_count"], reverse=True)[:20],
            "warnings": [
                "This is a foundation in-memory limiter.",
                "It does not replace Cloud Armor, API Gateway, authentication, or a persistent distributed limiter.",
            ],
            "future_upgrades": [
                "Firestore-backed request counters",
                "Redis or Memorystore",
                "Cloud Armor WAF and rate limiting",
                "API Gateway quotas",
                "Admin authentication and audit logs",
            ],
        }


_DEFAULT_RATE_LIMITER = RateLimiterService()


def check_rate_limit(ip_address: str | None, route: str, limit: int = 60, window_seconds: int = 60) -> dict[str, Any]:
    return _DEFAULT_RATE_LIMITER.check_rate_limit(ip_address, route, limit, window_seconds)


def record_request(ip_address: str | None, route: str) -> None:
    _DEFAULT_RATE_LIMITER.record_request(ip_address, route)


def get_rate_limit_status() -> dict[str, Any]:
    return _DEFAULT_RATE_LIMITER.get_rate_limit_status()
