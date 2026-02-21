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
            delay = base_delay_seconds * (2 ** (attempt - 1))
            logger.warning(
                "Retrying operation after failure.",
                extra={
                    "operation": operation_name,
                    "attempt": attempt,
                    "next_delay_seconds": delay,
                    "error": str(exc),
                },
            )
            await asyncio.sleep(delay)
    raise RuntimeError(f"Unreachable retry state for {operation_name}") from last_error
