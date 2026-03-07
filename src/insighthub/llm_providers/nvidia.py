import os
from typing import List, Optional

import httpx

from insighthub.errors import LLMProcessingError
from insighthub.llm_providers.base import BaseLLMProvider


class NvidiaProvider(BaseLLMProvider):
    """
    LLM provider for NVIDIA Integrate API (OpenAI-compatible chat endpoint).
    """

    DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not api_key:
            raise ValueError("NVIDIA API key not provided. Set llm.primary.api_key or NVIDIA_API_KEY.")

        self.model = model or os.getenv("LLM_MODEL") or os.getenv("NVIDIA_MODEL")
        if not self.model:
            raise ValueError("NVIDIA model not provided. Set llm.primary.model, LLM_MODEL, or NVIDIA_MODEL.")

        self.base_url = base_url or os.getenv("NVIDIA_API_URL") or self.DEFAULT_BASE_URL
        self.temperature = float(os.getenv("NVIDIA_TEMPERATURE", "0.7"))
        self.top_p = float(os.getenv("NVIDIA_TOP_P", "0.95"))
        self.max_tokens = int(os.getenv("NVIDIA_MAX_TOKENS", "8192"))

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.client = httpx.AsyncClient(headers=headers, timeout=60.0)

    async def _call_chat(self, messages: List[dict]) -> dict:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        resp = await self.client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"NVIDIA API error: {e.response.status_code} {e.response.text}") from e
        return resp.json()

    @staticmethod
    def _extract_text_from_response(response: dict) -> str:
        try:
            return response["choices"][0]["message"]["content"].strip()
        except Exception:
            raise AttributeError("Unable to extract text from NVIDIA response")

    async def summarize(self, content: str, prompt_template: str) -> str:
        prompt = self.render_prompt(prompt_template, content=content)
        try:
            raw = await self._call_chat([{"role": "user", "content": prompt}])
            return self._extract_text_from_response(raw)
        except Exception as e:
            raise LLMProcessingError(f"NVIDIA summarization failed: {e}") from e

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        prompt = self.render_prompt(prompt_template, content=content, categories=", ".join(categories))
        try:
            raw = await self._call_chat([{"role": "user", "content": prompt}])
            result = self._extract_text_from_response(raw)
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            raise LLMProcessingError(f"NVIDIA classification failed: {e}") from e
