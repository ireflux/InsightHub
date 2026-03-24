import os
import logging
from typing import Any, Dict, List, Optional

import httpx

from insighthub.core.registry import registry
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.errors import LLMProcessingError

logger = logging.getLogger(__name__)

@registry.register_llm("zhipuai")
class ZhipuAIProvider(BaseLLMProvider):
    """
    LLM Provider for ZhipuAI.
    
    API key is read from the `ZHIPUAI_API_KEY` environment variable.
    """

    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

    ALLOWED_PARAMS = {"temperature", "top_p", "max_tokens", "stop", "stream"}
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        api_key = api_key or os.getenv("ZHIPUAI_API_KEY")
        if not api_key:
            raise ValueError("ZhipuAI API key not provided or found in environment variables.")

        if not model:
            raise ValueError("ZhipuAI model not provided. Set llm.primary.model.")

        self.model = model
        self.base_url = base_url or os.getenv("ZHIPUAI_API_URL") or self.DEFAULT_BASE_URL
        self.params = self._sanitize_params(params)
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=120.0,
        )

    @classmethod
    def _sanitize_params(cls, params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        clean: Dict[str, Any] = {}
        if not params:
            return clean
        for key, value in params.items():
            if key not in cls.ALLOWED_PARAMS:
                continue
            if key == "stream":
                if bool(value):
                    continue
                clean[key] = False
                continue
            clean[key] = value
        clean.pop("stream", None)
        return clean

    async def _chat(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.params,
            "stream": False,
        }
        payload.pop("stream", None)

        resp = await self.client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"ZhipuAI API error: {e.response.status_code} {e.response.text}") from e

        data = resp.json()
        try:
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                text_parts = [
                    str(part.get("text", ""))
                    for part in content
                    if isinstance(part, dict) and part.get("type") == "text"
                ]
                text = "".join(text_parts).strip()
                if text:
                    return text
            raise ValueError("empty content")
        except Exception as e:
            raise RuntimeError(f"Invalid ZhipuAI response format: {data}") from e

    async def summarize(self, content: str, prompt_template: str) -> str:
        """
        Summarizes content using the specified ZhipuAI model.
        
        Note: Retry logic is handled by the engine layer (with_retry).
        Do not add retry decorators here to avoid nested retry loops.
        """
        prompt = self.render_prompt(prompt_template, content=content)
        try:
            return await self._chat(prompt)
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
        prompt = self.render_prompt(prompt_template, content=content, categories=", ".join(categories))
        try:
            result = await self._chat(prompt)
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            logger.error(f"Error calling ZhipuAI API: {e}", exc_info=True)
            # Wrap in LLMProcessingError which is marked as retryable
            raise LLMProcessingError(f"ZhipuAI classification failed: {e}") from e

    async def aclose(self) -> None:
        await self.client.aclose()
