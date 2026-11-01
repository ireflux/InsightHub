import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.core.rate_limit import AsyncRateLimiter, parse_retry_after
from insighthub.core.retry import with_retry
from insighthub.errors import RateLimitError
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.llm_providers.throttled import ThrottledLLMProvider


def test_rate_limiter_uses_even_spacing():
    limiter = AsyncRateLimiter(requests_per_minute=10)
    assert limiter.min_interval_seconds == 6.0


@pytest.mark.asyncio
async def test_rate_limiter_serializes_concurrent_acquires():
    limiter = AsyncRateLimiter(requests_per_minute=10, window_seconds=0.2)

    started_at = time.monotonic()
    await asyncio.gather(*(limiter.acquire() for _ in range(4)))
    elapsed = time.monotonic() - started_at

    # Four slots require three intervals: 3 * (0.2 / 10) = 0.06s.
    assert elapsed >= 0.05


@pytest.mark.asyncio
async def test_throttled_provider_applies_limiter():
    class CountingProvider(BaseLLMProvider):
        def __init__(self):
            self.calls = 0

        async def summarize(self, content: str, prompt_template: str) -> str:
            self.calls += 1
            return "summary"

        async def score(self, content: str, prompt_template: str) -> str:
            self.calls += 1
            return "{}"

    inner = CountingProvider()
    provider = ThrottledLLMProvider(inner, requests_per_minute=600)
    provider.rate_limiter.min_interval_seconds = 0.01

    started_at = time.monotonic()
    await provider.summarize("input", "{content}")
    await provider.score("input", "{content}")
    elapsed = time.monotonic() - started_at

    assert inner.calls == 2
    assert elapsed >= 0.008


@pytest.mark.asyncio
async def test_with_retry_honors_retry_after():
    attempts = 0

    async def operation() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RateLimitError("429", retry_after_seconds=0.05)
        return "ok"

    started_at = time.monotonic()
    result = await with_retry(
        operation,
        logger=logging.getLogger("test.rate_limit"),
        operation_name="test.retry_after",
        max_attempts=2,
        base_delay_seconds=0.001,
    )
    elapsed = time.monotonic() - started_at

    assert result == "ok"
    assert elapsed >= 0.04


def test_parse_retry_after_accepts_seconds_and_http_dates():
    assert parse_retry_after("7") == 7.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("not-a-date") is None

    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    parsed = parse_retry_after(format_datetime(future, usegmt=True))
    assert parsed is not None
    assert 25 <= parsed <= 35
