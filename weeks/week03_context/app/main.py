from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_application.config import settings
from ai_application.idempotency import SqliteIdempotencyStore
from weeks.week02_classifier.schemas import TicketClassification, TicketInput
from weeks.week03_context.classify import classify_ticket
from weeks.week03_context.prompts import VERSIONS

STORE = SqliteIdempotencyStore(Path(__file__).resolve().parents[1] / "output" / "idempotency.sqlite")

app = FastAPI(
    title="Week 03 Context Classifier",
    description="Prompt versions + trimmed context + request_id idempotency.",
    version="0.3.0",
)


class ClassifyRequest(TicketInput):
    request_id: str | None = None
    version: str = "baseline"


class ClassifyResponse(BaseModel):
    ticket_id: str
    request_id: str
    prompt_version: str
    cache_hit: bool
    trimmed: bool
    classification: TicketClassification
    prompt_tokens: int = 0
    total_tokens: int = 0
    latency_s: float = 0.0
    threshold: float = Field(default_factory=lambda: settings.classify_confidence_threshold)


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "model": settings.llm_model,
        "versions": list(VERSIONS),
        "max_body_chars": settings.context_max_body_chars,
    }


@app.post("/classify", response_model=ClassifyResponse)
async def classify(req: ClassifyRequest) -> ClassifyResponse:
    if req.version not in VERSIONS:
        raise HTTPException(status_code=400, detail=f"unknown version: {req.version}")
    if not settings.llm_api_key and "localhost" not in settings.llm_base_url:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is empty.")
    outcome = await classify_ticket(
        TicketInput(
            ticket_id=req.ticket_id,
            subject=req.subject,
            body=req.body,
            channel=req.channel,
        ),
        version=req.version,
        request_id=req.request_id,
        store=STORE,
    )
    return ClassifyResponse(
        ticket_id=req.ticket_id,
        request_id=outcome.request_id,
        prompt_version=outcome.prompt_version,
        cache_hit=outcome.cache_hit,
        trimmed=outcome.trimmed,
        classification=outcome.classification,
        prompt_tokens=outcome.prompt_tokens,
        total_tokens=outcome.total_tokens,
        latency_s=round(outcome.latency_s, 3),
    )
