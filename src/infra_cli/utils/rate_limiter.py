"""
Token‑bucket rate limiter.

This module implements a simple token‑bucket rate limiter. A
``RateLimiter`` instance enforces a maximum number of acquisitions per
second, with a configurable burst capacity. When no tokens are
available the calling thread will sleep until a token becomes
available. The limiter is thread‑safe.
"""

from __future__ import annotations

import threading
import time
from typing import Optional


class RateLimiter:
    """A token‑bucket rate limiter.

    Parameters
    ----------
    rate_per_sec:
        The steady‑state rate in tokens per second.
    capacity:
        Maximum burst capacity (number of tokens that can be saved). If
        omitted the capacity defaults to ``rate_per_sec``.
    """

    def __init__(self, rate_per_sec: float, capacity: Optional[float] = None) -> None:
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec must be positive")
        self.rate = float(rate_per_sec)
        self.capacity = float(capacity) if capacity is not None else float(rate_per_sec)
        self._tokens = self.capacity
        self._last_checked = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Acquire a token from the bucket, sleeping if necessary.

        This method blocks until a token is available. Tokens are
        replenished over time at the configured rate. When no tokens
        remain the calling thread sleeps until the next token arrives.
        """

        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_checked
            # Refill tokens proportional to time elapsed.
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
            self._last_checked = now
            if self._tokens < 1.0:
                # Need to wait for the next token.
                sleep_time = (1.0 - self._tokens) / self.rate
                # Release lock while sleeping to allow other threads to refill concurrently.
                self._lock.release()
                try:
                    time.sleep(sleep_time)
                finally:
                    # Re‑acquire lock and recalculate tokens after sleep.
                    self._lock.acquire()
                    now = time.monotonic()
                    elapsed = now - self._last_checked
                    self._tokens = min(self.capacity, self._tokens + elapsed * self.rate)
                    self._last_checked = now
            # Consume one token.
            self._tokens -= 1.0
