import logging
from typing import List

from insighthub.errors import LLMProcessingError
from insighthub.llm_providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class FailoverLLMProvider(BaseLLMProvider):
    """
    Tries the configured primary provider first, then fallbacks in order.
    """

    def __init__(self, providers: List[BaseLLMProvider], provider_labels: List[str]):
        if not providers:
            raise ValueError("At least one LLM provider is required.")
        if len(providers) != len(provider_labels):
            raise ValueError("providers and provider_labels must have the same length.")
        self.providers = providers
        self.provider_labels = provider_labels

    async def summarize(self, content: str, prompt_template: str) -> str:
        last_error: Exception | None = None
        for provider, label in zip(self.providers, self.provider_labels):
            try:
                return await provider.summarize(content, prompt_template)
            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM summarize failed on provider, trying next if available.",
                    extra={"event": "llm.failover.summarize_failed", "provider": label, "error": str(e)},
                )
        raise LLMProcessingError(f"All LLM summarize providers failed. Last error: {last_error}")

    async def score(self, content: str, prompt_template: str) -> str:
        last_error: Exception | None = None
        for provider, label in zip(self.providers, self.provider_labels):
            try:
                return await provider.score(content, prompt_template)
            except Exception as e:
                last_error = e
                logger.warning(
                    "LLM score failed on provider, trying next if available.",
                    extra={"event": "llm.failover.score_failed", "provider": label, "error": str(e)},
                )
        raise LLMProcessingError(f"All LLM score providers failed. Last error: {last_error}")

    async def aclose(self) -> None:
        for provider in self.providers:
            close_fn = getattr(provider, "aclose", None)
            if callable(close_fn):
                await close_fn()
