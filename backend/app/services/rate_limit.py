"""In-memory fixed-window rate limiter for authentication endpoints (SEC-004)."""
from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request, status


class FixedWindowLimiter:
    """Fixed-window in-memory rate limiter keyed by an arbitrary string.

    Adequate for a single-process prototype. Not shared across workers or
    restarts: if the app is scaled horizontally, replace with a shared store
    (Redis or the database) keeping the same interface.
    """

    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._hits: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        """Register one attempt for the key; return True if still allowed."""
        now = time.monotonic()
        with self._lock:
            count, window_start = self._hits.get(key, (0, now))
            if now - window_start >= self.window_seconds:
                count, window_start = 0, now
            count += 1
            self._hits[key] = (count, window_start)
            return count <= self.limit


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce(limiter: FixedWindowLimiter, request: Request, action: str) -> None:
    """Raise HTTP 429 when the limiter has exhausted the key's budget."""
    if not limiter.check(client_ip(request)):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Demasiados intentos de {action}. Inténtalo más tarde.",
        )