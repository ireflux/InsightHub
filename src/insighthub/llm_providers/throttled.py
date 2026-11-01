from insighthub.core.rate_limit import AsyncRateLimiter
from insighthub.llm_providers.base import BaseLLMProvider


class ThrottledLLMProvider(BaseLLMProvider):
    """Apply a shared requests-per-minute limit to a wrapped provider.

    The limiter lives at the provider boundary rather than in the engine, so
    scoring, editorial briefs and summarization all consume the same quota.
    """

    def __init__(self, provider: BaseLLMProvider, requests_per_minute: int):
        self.provider = provider
        self.rate_limiter = AsyncRateLimiter(requests_per_minute=requests_per_minute)

    async def summarize(self, content: str, prompt_template: str) -> str:
        await self.rate_limiter.acquire()
        return await self.provider.summarize(content, prompt_template)

    async def score(self, content: str, prompt_template: str) -> str:
        await self.rate_limiter.acquire()
        return await self.provider.score(content, prompt_template)

    async def aclose(self) -> None:
        await self.provider.aclose()

    def __getattr__(self, name):
        # Keep provider attributes (model, base_url, ...) visible to callers
        # that log or introspect the effective provider.
        return getattr(self.provider, name)
