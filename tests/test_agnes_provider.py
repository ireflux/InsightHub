import json
import os
import sys

import httpx
import pytest


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from insighthub.llm_providers.agnes import AgnesProvider


@pytest.mark.asyncio
async def test_agnes_summarize_sends_non_streaming_text_request_with_thinking():
    captured = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["payload"] = request.read()
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": " summary ",
                        }
                    }
                ]
            },
        )

    provider = AgnesProvider(
        api_key="test-key",
        model="agnes-2.0-flash",
        params={"temperature": 0.3, "stream": True, "enable_thinking": True},
    )
    await provider.client.aclose()
    provider.client = httpx.AsyncClient(
        headers={"Authorization": "Bearer test-key"},
        transport=httpx.MockTransport(handler),
    )

    try:
        result = await provider.summarize("input", "Summarize: {content}")
    finally:
        await provider.aclose()

    assert result == "summary"
    assert captured["url"] == "https://apihub.agnes-ai.com/v1/chat/completions"
    payload = json.loads(captured["payload"])
    assert payload["model"] == "agnes-2.0-flash"
    assert payload["messages"] == [{"role": "user", "content": "Summarize: input"}]
    assert payload["stream"] is False
    assert payload["temperature"] == 0.3
    assert payload["chat_template_kwargs"] == {"enable_thinking": True}


@pytest.mark.asyncio
async def test_agnes_sanitizes_unsupported_params_and_disables_streaming():
    provider = AgnesProvider(
        api_key="test-key",
        model="agnes-2.0-flash",
        params={"temperature": 0.7, "unknown": "ignored", "stream": True},
    )
    try:
        assert provider.params == {"temperature": 0.7}
    finally:
        await provider.aclose()
