from collections.abc import AsyncIterator

from fastapi import FastAPI, HTTPException
from sse_starlette.sse import EventSourceResponse

from ai_application.config import settings
from ai_application.llm.client import LLMClient
from ai_application.llm.types import ChatRequest

app = FastAPI(
    title="Week 01 Chat API",
    description="Streaming OpenAI-compatible chat. Swap LLM_BASE_URL to change providers.",
    version="0.1.0",
)
client = LLMClient()


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "ok",
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
    }


@app.post("/chat")
async def chat(req: ChatRequest) -> EventSourceResponse:
    if not settings.llm_api_key and "localhost" not in settings.llm_base_url:
        raise HTTPException(
            status_code=500,
            detail="LLM_API_KEY is empty. Copy .env.example to .env and fill it in.",
        )

    async def events() -> AsyncIterator[dict[str, str]]:
        try:
            async for token in client.stream_chat(
                req.messages,
                model=req.model,
                temperature=req.temperature,
            ):
                yield {"event": "token", "data": token}
            yield {"event": "done", "data": req.request_id or ""}
        except Exception as exc:  # noqa: BLE001 — surface provider errors to the client
            yield {"event": "error", "data": str(exc)}

    return EventSourceResponse(events())
