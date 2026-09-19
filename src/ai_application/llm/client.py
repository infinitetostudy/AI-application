"""OpenAI-compatible chat client. Point LLM_BASE_URL at any compatible server."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

import httpx

from ai_application.config import settings
from ai_application.llm.types import ChatMessage


class LLMClient:
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout_s: float | None = None,
    ) -> None:
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.llm_api_key
        self.model = model or settings.llm_model
        self.timeout_s = timeout_s or settings.request_timeout_s

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _payload(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None,
        temperature: float,
        stream: bool,
        max_tokens: int | None = None,
    ) -> dict:
        return {
            "model": model or self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "stream": stream,
            "max_tokens": max_tokens or settings.max_tokens,
        }

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            response = await client.post(
                url,
                headers=self._headers(),
                json=self._payload(messages, model=model, temperature=temperature, stream=False),
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"] or ""

    async def stream_chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> AsyncIterator[str]:
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._headers(),
                json=self._payload(messages, model=model, temperature=temperature, stream=True),
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    payload = line[6:].strip()
                    if payload == "[DONE]":
                        break
                    chunk = json.loads(payload)
                    delta = chunk["choices"][0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        yield text
