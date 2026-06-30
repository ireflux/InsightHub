import os
from typing import Any, Dict, List, Optional

import httpx

from insighthub.core.registry import registry
from insighthub.errors import LLMProcessingError
from insighthub.llm_providers.base import BaseLLMProvider


@registry.register_llm("agnes")
class AgnesProvider(BaseLLMProvider):
    """
    LLM provider for Agnes API using its OpenAI-compatible chat completions endpoint.
    """

    DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
    DEFAULT_MODEL = "agnes-2.0-flash"

    ALLOWED_PARAMS = {"temperature", "top_p", "max_tokens", "stop", "stream", "enable_thinking"}

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        api_key = api_key or os.getenv("AGNES_API_KEY")
        if not api_key:
            raise ValueError("Agnes API key not provided. Set AGNES_API_KEY.")

        self.model = model or os.getenv("AGNES_MODEL") or self.DEFAULT_MODEL
        self.base_url = base_url or os.getenv("AGNES_API_URL") or self.DEFAULT_BASE_URL
        self.params = self._sanitize_params(params)

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        self.client = httpx.AsyncClient(headers=headers, timeout=120.0)

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

    async def _call_chat(self, messages: List[dict]) -> dict:
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload_params = dict(self.params)
        enable_thinking = bool(payload_params.pop("enable_thinking", False))
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            **payload_params,
            "stream": False,
        }
        if enable_thinking:
            payload["chat_template_kwargs"] = {"enable_thinking": True}

        resp = await self.client.post(url, json=payload)
        try:
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Agnes API error: {e.response.status_code} {e.response.text}") from e
        return resp.json()

    @staticmethod
    def _extract_text_from_response(response: dict) -> str:
        try:
            content = response["choices"][0]["message"]["content"]
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
            raise RuntimeError(f"Invalid Agnes response format: {response}") from e

    async def summarize(self, content: str, prompt_template: str) -> str:
        prompt = self.render_prompt(prompt_template, content=content)
        try:
            raw = await self._call_chat([{"role": "user", "content": prompt}])
            return self._extract_text_from_response(raw)
        except Exception as e:
            raise LLMProcessingError(f"Agnes summarization failed: {e}") from e

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
            raise LLMProcessingError(f"Agnes classification failed: {e}") from e

    async def score(self, content: str, prompt_template: str) -> str:
        prompt = self.render_prompt(prompt_template, content=content)
        try:
            raw = await self._call_chat([{"role": "user", "content": prompt}])
            return self._extract_text_from_response(raw)
        except Exception as e:
            raise LLMProcessingError(f"Agnes scoring failed: {e}") from e

    async def aclose(self) -> None:
        await self.client.aclose()
