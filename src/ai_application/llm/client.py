"""OpenAI-compatible chat client. Point LLM_BASE_URL at any compatible server."""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from ai_application.config import settings
from ai_application.llm.schema import strict_json_schema
from ai_application.llm.types import ChatMessage

T = TypeVar("T", bound=BaseModel)
_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


@dataclass(frozen=True)
class ParsedResult(Generic[T]):
    value: T
    raw_text: str
    model: str
    usage: dict[str, int]
    response_format: str


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
        response_format: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": [m.model_dump() for m in messages],
            "temperature": temperature,
            "stream": stream,
            "max_tokens": max_tokens or settings.max_tokens,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        return payload

    async def _post(self, payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}/chat/completions"
        async with httpx.AsyncClient(timeout=self.timeout_s) as client:
            response = await client.post(url, headers=self._headers(), json=payload)
            response.raise_for_status()
            return response.json()

    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str | None = None,
        temperature: float = 0.2,
    ) -> str:
        data = await self._post(
            self._payload(messages, model=model, temperature=temperature, stream=False)
        )
        return data["choices"][0]["message"]["content"] or ""

    async def chat_parsed(
        self,
        messages: list[ChatMessage],
        response_model: type[T],
        *,
        model: str | None = None,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> ParsedResult[T]:
        """Parse a response into `response_model` via json_schema, not prompt-only JSON."""
        schema = strict_json_schema(response_model)
        json_schema_format = {
            "type": "json_schema",
            "json_schema": {
                "name": response_model.__name__,
                "strict": True,
                "schema": schema,
            },
        }
        token_budget = max_tokens if max_tokens is not None else max(settings.max_tokens, 4096)
        payload = self._payload(
            messages,
            model=model,
            temperature=temperature,
            stream=False,
            max_tokens=token_budget,
            response_format=json_schema_format,
        )
        used_format = "json_schema"
        try:
            data = await self._post(payload)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in {400, 422}:
                raise
            used_format = "json_object"
            payload["response_format"] = {"type": "json_object"}
            data = await self._post(payload)

        raw = _message_text(data)
        value = _validate_model(response_model, raw)
        return ParsedResult(
            value=value,
            raw_text=raw,
            model=data.get("model") or (model or self.model),
            usage=_usage(data),
            response_format=used_format,
        )

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


def _usage(data: dict[str, Any]) -> dict[str, int]:
    usage = data.get("usage") or {}
    return {
        "prompt_tokens": int(usage.get("prompt_tokens") or 0),
        "completion_tokens": int(usage.get("completion_tokens") or 0),
        "total_tokens": int(usage.get("total_tokens") or 0),
    }


def _message_text(data: dict[str, Any]) -> str:
    message = data["choices"][0]["message"]
    for key in ("content", "reasoning_content"):
        text = _coerce_text(message.get(key))
        if text:
            return text
    raise ValueError("model returned empty content")


def _coerce_text(content: Any) -> str:
    if isinstance(content, str) and content.strip():
        return content
    if isinstance(content, list):
        parts = [
            part.get("text", "")
            for part in content
            if isinstance(part, dict) and part.get("type") in {"text", "output_text"}
        ]
        return "".join(parts).strip()
    return ""


def _validate_model(response_model: type[T], raw: str) -> T:
    text = _FENCE_RE.sub("", raw.strip())
    try:
        return response_model.model_validate_json(text)
    except (ValidationError, json.JSONDecodeError):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return response_model.model_validate_json(match.group(0))
        raise
