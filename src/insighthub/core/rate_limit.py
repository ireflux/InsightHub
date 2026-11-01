import asyncio
import logging
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Optional

logger = logging.getLogger(__name__)


class AsyncRateLimiter:
    """Pace async requests evenly to stay within a per-minute quota.

    A single limiter instance is shared by every request made through one LLM
    provider, so scoring and editorial calls draw from the same budget. Slots
    are reserved under a lock and the caller sleeps outside it, which prevents
    a burst of concurrent tasks from all hitting the API at once.
    """

    def __init__(self, requests_per_minute: int, window_seconds: float = 60.0):
        if requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be > 0")
        if window_seconds <= 0:
            raise ValueError("window_seconds must be > 0")

        self.requests_per_minute = requests_per_minute
        self.window_seconds = window_seconds
        self.min_interval_seconds = window_seconds / requests_per_minute
        self._next_allowed_at = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            scheduled_at = max(now, self._next_allowed_at)
            self._next_allowed_at = scheduled_at + self.min_interval_seconds
            delay = scheduled_at - now

        if delay > 0:
            logger.debug(
                "Waiting for LLM rate limit slot.",
                extra={
                    "event": "llm.rate_limit.wait",
                    "requests_per_minute": self.requests_per_minute,
                    "delay_seconds": round(delay, 3),
                },
            )
            await asyncio.sleep(delay)


def parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse a Retry-After header value expressed as seconds or an HTTP date."""
    if not value:
        return None

    try:
        return max(0.0, float(value))
    except (TypeError, ValueError):
        pass

    try:
        retry_at = parsedate_to_datetime(value)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())
    except (TypeError, ValueError, OverflowError):
        return None
