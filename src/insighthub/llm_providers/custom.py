import os
from typing import Any, Dict, List, Optional

import httpx

from insighthub.errors import LLMProcessingError
from insighthub.llm_providers.base import BaseLLMProvider

ALLOWED_PARAMS = {"temperature", "top_p", "max_tokens", "stop", "stream"}


def _sanitize_params(params: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    clean: Dict[str, Any] = {}
    if not params:
        return clean
    for key, value in params.items():
        if key not in ALLOWED_PARAMS:
            continue
        if key == "stream":
            # Custom providers are intentionally non-streaming in current design.
            if bool(value):
                continue
            clean[key] = False
            continue
        clean[key] = value
    return clean


class CustomOpenAIProvider(BaseLLMProvider):
    """
    Generic OpenAI-compatible provider with user-supplied base_url/model.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        self.api_key = api_key or os.getenv("CUSTOM_OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("Missing API key for custom_openai. Set CUSTOM_OPENAI_API_KEY or llm.*.api_key.")

        self.model = model or os.getenv("LLM_MODEL")
        if not self.model:
            raise ValueError("Missing model for custom_openai.")

        self.base_url = (base_url or os.getenv("CUSTOM_OPENAI_BASE_URL") or "").strip()
        if not self.base_url:
            raise ValueError("Missing base_url for custom_openai.")

        self.params = _sanitize_params(params)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.client = httpx.AsyncClient(headers=headers, timeout=60.0)

    async def _chat(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            **self.params,
            "stream": False,
        }
        resp = await self.client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"custom_openai API error: {e.response.status_code} {e.response.text}") from e
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(f"Invalid custom_openai response format: {data}") from e

    async def summarize(self, content: str, prompt_template: str) -> str:
        prompt = prompt_template.format(content=content)
        try:
            return await self._chat(prompt)
        except Exception as e:
            raise LLMProcessingError(f"custom_openai summarization failed: {e}") from e

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        prompt = prompt_template.format(content=content, categories=", ".join(categories))
        try:
            result = await self._chat(prompt)
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            raise LLMProcessingError(f"custom_openai classification failed: {e}") from e


class CustomAnthropicProvider(BaseLLMProvider):
    """
    Generic Anthropic-compatible provider with user-supplied base_url/model.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        self.api_key = api_key or os.getenv("CUSTOM_ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Missing API key for custom_anthropic. Set CUSTOM_ANTHROPIC_API_KEY or llm.*.api_key.")

        self.model = model or os.getenv("LLM_MODEL")
        if not self.model:
            raise ValueError("Missing model for custom_anthropic.")

        self.base_url = (base_url or os.getenv("CUSTOM_ANTHROPIC_BASE_URL") or "").strip()
        if not self.base_url:
            raise ValueError("Missing base_url for custom_anthropic.")

        self.params = _sanitize_params(params)
        self.anthropic_version = os.getenv("CUSTOM_ANTHROPIC_VERSION", "2023-06-01")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.anthropic_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.client = httpx.AsyncClient(headers=headers, timeout=60.0)

    async def _chat(self, prompt: str) -> str:
        url = f"{self.base_url.rstrip('/')}/messages"
        stop_value = self.params.get("stop")
        stop_sequences: Optional[List[str]] = None
        if isinstance(stop_value, str):
            stop_sequences = [stop_value]
        elif isinstance(stop_value, list):
            stop_sequences = [str(x) for x in stop_value]

        max_tokens = int(self.params.get("max_tokens", 4096))
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "stream": False,
        }
        if "temperature" in self.params:
            payload["temperature"] = self.params["temperature"]
        if "top_p" in self.params:
            payload["top_p"] = self.params["top_p"]
        if stop_sequences:
            payload["stop_sequences"] = stop_sequences

        resp = await self.client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"custom_anthropic API error: {e.response.status_code} {e.response.text}") from e
        data = resp.json()
        try:
            content_blocks = data.get("content", [])
            text_parts = [b.get("text", "") for b in content_blocks if isinstance(b, dict) and b.get("type") == "text"]
            text = "".join(text_parts).strip()
            if text:
                return text
            raise ValueError("empty content")
        except Exception as e:
            raise RuntimeError(f"Invalid custom_anthropic response format: {data}") from e

    async def summarize(self, content: str, prompt_template: str) -> str:
        prompt = prompt_template.format(content=content)
        try:
            return await self._chat(prompt)
        except Exception as e:
            raise LLMProcessingError(f"custom_anthropic summarization failed: {e}") from e

    async def classify(self, content: str, categories: List[str], prompt_template: str) -> str:
        prompt = prompt_template.format(content=content, categories=", ".join(categories))
        try:
            result = await self._chat(prompt)
            for category in categories:
                if category.lower() in result.lower():
                    return category
            return "Uncategorized"
        except Exception as e:
            raise LLMProcessingError(f"custom_anthropic classification failed: {e}") from e
