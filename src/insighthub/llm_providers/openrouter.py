import os
from typing import List, Optional
import httpx
from insighthub.llm_providers.base import BaseLLMProvider
from insighthub.errors import LLMProcessingError


class OpenRouterProvider(BaseLLMProvider):
    """
    LLM Provider for OpenRouter using direct HTTP calls to the OpenRouter REST API.

    - Reads API key from `OPENROUTER_API_KEY` (or from `api_key` argument).
    - Optional `OPENROUTER_API_URL` env var to override the base API URL.
    """

    # Use the official domain/path from OpenRouter quickstart examples
    DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OpenRouter API key not provided or found in environment variables.")

        self.model = model or os.getenv("LLM_MODEL") or os.getenv("OPENROUTER_MODEL")
        if not self.model:
            raise ValueError("OpenRouter model not provided. Set llm.primary.model or LLM_MODEL.")
        self.base_url = base_url or os.getenv("OPENROUTER_API_URL") or self.DEFAULT_BASE_URL

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Optional headers recommended in the official example for site attribution
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        title = os.getenv("OPENROUTER_X_TITLE")
        if referer:
            headers["HTTP-Referer"] = referer
        if title:
            headers["X-Title"] = title

        # Reusable async HTTP client
        self.client = httpx.AsyncClient(headers=headers, timeout=30.0)

    async def _call_chat(self, messages: List[dict]) -> dict:
        """
        Call the OpenRouter chat completions endpoint via HTTP.
        """
        # Official endpoint: /chat/completions under /api/v1
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
        }

        resp = await self.client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # Include body for easier debugging
            raise RuntimeError(f"OpenRouter API error: {e.response.status_code} {e.response.text}") from e

        return resp.json()

    def _extract_text_from_response(self, response: dict) -> str:
        # Common OpenAI-like response shape
        try:
            return response["choices"][0]["message"]["content"].strip()
        except Exception:
            pass

        # Fallbacks for other shapes
        try:
            if "choices" in response and isinstance(response["choices"], list):
                first = response["choices"][0]
                for key in ("text", "content", "message"):
                    if isinstance(first, dict) and key in first and isinstance(first[key], str):
                        return first[key].strip()
        except Exception:
            pass

        raise AttributeError("Unable to extract text from OpenRouter response")

    async def summarize(self, content: str, prompt_template: str) -> str:
        """
        Summarizes content using the OpenRouter API.
        
        Note: Retry logic is handled by the engine layer (with_retry).
        Do not add retry decorators here to avoid nested retry loops.
        """
        prompt = prompt_template.format(content=content)
        try:
            raw = await self._call_chat([{"role": "user", "content": prompt}])
            return self._extract_text_from_response(raw)
        except Exception as e:
            # Wrap in LLMProcessingError which is marked as retryable
            raise LLMProcessingError(f"OpenRouter summarization failed: {e}") from e

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        """
        Classifies content using the OpenRouter API.
        
        Note: Retry logic is handled by the engine layer (with_retry).
        Do not add retry decorators here to avoid nested retry loops.
        """
        prompt = prompt_template.format(content=content, categories=", ".join(categories))
        try:
            raw = await self._call_chat([{"role": "user", "content": prompt}])
            result = self._extract_text_from_response(raw)
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            # Wrap in LLMProcessingError which is marked as retryable
            raise LLMProcessingError(f"OpenRouter classification failed: {e}") from e
