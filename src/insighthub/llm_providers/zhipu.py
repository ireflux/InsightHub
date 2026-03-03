import os
import asyncio
import logging
from typing import List
from zhipuai import ZhipuAI
from tenacity import retry, stop_after_attempt, wait_exponential
from insighthub.llm_providers.base import BaseLLMProvider

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

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def summarize(self, content: str, prompt_template: str) -> str:
        """
        Summarizes content using the specified ZhipuAI model.
        """
        prompt = prompt_template.format(content=content)
        try:
            return await asyncio.to_thread(self._sync_chat, prompt)
        except Exception as e:
            logger.error(f"Error calling ZhipuAI API: {e}", exc_info=True)
            raise

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        """
        Classifies content into categories using the specified ZhipuAI model.
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
            raise
