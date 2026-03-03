import os
import asyncio
import logging
from typing import List
from zhipuai import ZhipuAI
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.errors import LLMProcessingError

logger = logging.getLogger(__name__)

class ZhipuAIProvider(BaseLLMProvider):
    """
    LLM Provider for ZhipuAI.
    
    API key is read from the `ZHIPUAI_API_KEY` environment variable.
    """
    
    def __init__(self, api_key: str = None, model: str = None):
        api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("ZhipuAI API key not provided or found in environment variables.")

        model = model or os.getenv("LLM_MODEL")
        if not model:
            raise ValueError("ZhipuAI model not provided. Set llm.primary.model or LLM_MODEL.")

        self.client = ZhipuAI(api_key=api_key)
        self.model = model

    def _sync_chat(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    async def summarize(self, content: str, prompt_template: str) -> str:
        """
        Summarizes content using the specified ZhipuAI model.
        
        Note: Retry logic is handled by the engine layer (with_retry).
        Do not add retry decorators here to avoid nested retry loops.
        """
        prompt = prompt_template.format(content=content)
        try:
            return await asyncio.to_thread(self._sync_chat, prompt)
        except Exception as e:
            logger.error(f"Error calling ZhipuAI API: {e}", exc_info=True)
            # Wrap in LLMProcessingError which is marked as retryable
            raise LLMProcessingError(f"ZhipuAI summarization failed: {e}") from e

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        """
        Classifies content into categories using the specified ZhipuAI model.
        
        Note: Retry logic is handled by the engine layer (with_retry).
        Do not add retry decorators here to avoid nested retry loops.
        """
        prompt = prompt_template.format(content=content, categories=", ".join(categories))
        try:
            result = await asyncio.to_thread(self._sync_chat, prompt)
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            logger.error(f"Error calling ZhipuAI API: {e}", exc_info=True)
            # Wrap in LLMProcessingError which is marked as retryable
            raise LLMProcessingError(f"ZhipuAI classification failed: {e}") from e
