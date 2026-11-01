import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

from insighthub.errors import InsightHubError

T = TypeVar("T")


async def with_retry(
    operation: Callable[[], Awaitable[T]],
    *,
    logger: logging.Logger,
    operation_name: str,
    max_attempts: int = 3,
    base_delay_seconds: float = 1.0,
    backoff_multiplier: float = 2.0,
    max_delay_seconds: float = 30.0,
) -> T:
    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await operation()
        except Exception as exc:
            last_error = exc
            retryable = isinstance(exc, InsightHubError) and exc.retryable
            if not retryable or attempt >= max_attempts:
                raise
            delay = min(base_delay_seconds * (backoff_multiplier ** (attempt - 1)), max_delay_seconds)
            retry_after = getattr(exc, "retry_after_seconds", None)
            if retry_after is not None:
                # A provider-supplied Retry-After is more authoritative than
                # our own backoff and should not be capped by max_delay_seconds.
                delay = max(delay, float(retry_after))
            logger.warning(
                "Retrying operation after failure.",
                extra={
                    "operation": operation_name,
                    "attempt": attempt,
                    "next_delay_seconds": delay,
                    "backoff_multiplier": backoff_multiplier,
                    "retry_after_seconds": retry_after,
                    "error": str(exc),
                },
            )
            await asyncio.sleep(delay)
    raise RuntimeError(f"Unreachable retry state for {operation_name}") from last_error
