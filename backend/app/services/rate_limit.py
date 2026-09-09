"""In-memory fixed-window rate limiter for authentication endpoints (SEC-004).

RATE-001: by default the limiter keys on the direct peer IP
(``request.client.host``) and ignores ``X-Forwarded-For``. Honoring the proxy
header without a trusted proxy would let a client spoof it and bypass the
per-IP budget, so it is opt-in: set ``RATE_LIMIT_TRUST_PROXY=true`` only when
the app is reachable exclusively through a trusted reverse proxy that
overwrites ``X-Forwarded-For`` (see ``app.config.Settings.rate_limit_trust_proxy``).
"""
from __future__ import annotations

import threading
import time

from fastapi import HTTPException, Request, status

from app.config import settings


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
    """Return the client key used for rate limiting.

    Uses the direct peer IP (``request.client.host``); when
    ``RATE_LIMIT_TRUST_PROXY`` is enabled, the first hop of
    ``X-Forwarded-For`` is used instead (see the module docstring for when that
    is safe). Falls back to the literal key ``\"unknown\"`` only when no peer
    information is available.
    """
    if settings.rate_limit_trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def enforce(limiter: FixedWindowLimiter, request: Request, action: str) -> None:
    """Raise HTTP 429 when the limiter has exhausted the key's budget."""
    if not limiter.check(client_ip(request)):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Demasiados intentos de {action}. Inténtalo más tarde.",
        )