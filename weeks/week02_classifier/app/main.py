from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from ai_application.config import settings
from weeks.week02_classifier.classify import classify_ticket
from weeks.week02_classifier.schemas import TicketClassification, TicketInput

app = FastAPI(
    title="Week 02 Ticket Classifier",
    description="Structured-output ticket classifier. Low confidence always goes to a human.",
    version="0.2.0",
)


class ClassifyResponse(BaseModel):
    ticket_id: str
    classification: TicketClassification
    response_format: str
    latency_s: float
    usage: dict[str, int] = Field(default_factory=dict)
    threshold: float


@app.get("/health")
async def health() -> dict[str, str | float]:
    return {
        "status": "ok",
        "model": settings.llm_model,
        "base_url": settings.llm_base_url,
        "threshold": settings.classify_confidence_threshold,
    }


@app.post("/classify", response_model=ClassifyResponse)
async def classify(ticket: TicketInput) -> ClassifyResponse:
    if not settings.llm_api_key and "localhost" not in settings.llm_base_url:
        raise HTTPException(status_code=500, detail="LLM_API_KEY is empty.")
    classification, parsed, latency_s = await classify_ticket(ticket)
    return ClassifyResponse(
        ticket_id=ticket.ticket_id,
        classification=classification,
        response_format=parsed.response_format,
        latency_s=round(latency_s, 3),
        usage=parsed.usage,
        threshold=settings.classify_confidence_threshold,
    )
