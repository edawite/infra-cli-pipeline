import time

from infra_cli.utils.rate_limiter import RateLimiter


def test_rate_limiter_basic() -> None:
    """The rate limiter should enforce the configured rate."""
    rate = 5  # tokens per second
    limiter = RateLimiter(rate_per_sec=rate, capacity=rate)
    # Acquire more tokens than capacity; expect delay ~ (n - capacity) / rate
    n = 10
    start = time.monotonic()
    for _ in range(n):
        limiter.acquire()
    elapsed = time.monotonic() - start
    expected_min = (n - rate) / rate
    # Allow a small margin for timing variance
    assert elapsed >= expected_min * 0.9
