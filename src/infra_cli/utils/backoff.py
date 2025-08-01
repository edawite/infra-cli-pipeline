"""
Exponential backoff helper.

This module provides a decorator and functional interface for retrying
operations with exponential backoff and jitter. It is used in the
pipeline to handle transient errors when parsing documents or calling
external services.
"""

from __future__ import annotations

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Iterable, Optional, Tuple, Type


def retry(
    func: Callable[..., Any],
    retries: int = 3,
    base_delay: float = 0.2,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    logger: Optional[logging.Logger] = None,
) -> Callable[..., Any]:
    """Return a wrapper that retries ``func`` with exponential backoff.

    Parameters
    ----------
    func:
        The function to execute. It may be synchronous and return any value.
    retries:
        The maximum number of retry attempts. A value of 0 disables
        retries entirely.
    base_delay:
        The initial delay in seconds before the first retry. Each
        subsequent retry doubles this delay (plus jitter).
    exceptions:
        A tuple of exception classes that trigger a retry. Other
        exceptions propagate immediately.
    logger:
        Optional logger to emit warning messages when retries occur.

    Returns
    -------
    Callable
        A function with the same signature as ``func`` that performs
        retries on failure. If all retries are exhausted the last
        exception is re‑raised.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        attempts = 0
        while True:
            try:
                return func(*args, **kwargs)
            except exceptions as exc:
                if attempts >= retries:
                    raise
                delay = base_delay * (2 ** attempts)
                # Add jitter up to 100 ms to avoid thundering herd.
                jitter = random.uniform(0, min(0.1, delay))
                wait_time = delay + jitter
                if logger:
                    logger.warning(
                        "Retrying after error: %s (attempt %s/%s, sleeping %.2f s)",
                        exc,
                        attempts + 1,
                        retries,
                        wait_time,
                    )
                time.sleep(wait_time)
                attempts += 1
                continue
    return wrapper
