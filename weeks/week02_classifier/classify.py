from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter

from ai_application.config import settings
from ai_application.llm.client import LLMClient, ParsedResult
from ai_application.llm.types import ChatMessage
from weeks.week02_classifier.schemas import TicketClassification, TicketInput

SYSTEM_PROMPT = """You classify inbound support tickets.
Fill every schema field. Use only evidence in the ticket.
confidence is 0 to 1. If the ticket is vague, mixed, or missing key facts, use a low confidence.
needs_human is true when a person must review before action: legal/refund risk, outage, abuse, or low confidence.
Extract entities actually present (order ids, emails, product names, URLs). Do not invent them.
HTTP 5xx, site-down, and production outages are intent=bug with high or critical priority, not feature.
Billing, invoices, duplicate charges, and refunds are intent=billing."""


def apply_policy(
    result: TicketClassification,
    *,
    threshold: float | None = None,
) -> TicketClassification:
    cutoff = settings.classify_confidence_threshold if threshold is None else threshold
    if result.confidence < cutoff and not result.needs_human:
        return result.model_copy(update={"needs_human": True})
    return result


def _user_prompt(ticket: TicketInput) -> str:
    return (
        f"ticket_id: {ticket.ticket_id}\n"
        f"channel: {ticket.channel}\n"
        f"subject: {ticket.subject}\n"
        f"body:\n{ticket.body}"
    )


async def classify_ticket(
    ticket: TicketInput,
    *,
    client: LLMClient | None = None,
) -> tuple[TicketClassification, ParsedResult[TicketClassification], float]:
    llm = client or LLMClient()
    messages = [
        ChatMessage(role="system", content=SYSTEM_PROMPT),
        ChatMessage(role="user", content=_user_prompt(ticket)),
    ]
    started = perf_counter()
    parsed = await llm.chat_parsed(messages, TicketClassification, temperature=0.0)
    latency_s = perf_counter() - started
    return apply_policy(parsed.value), parsed, latency_s


def load_samples(path: Path | None = None) -> list[TicketInput]:
    sample_path = path or Path(__file__).parent / "samples" / "tickets.json"
    payload = json.loads(sample_path.read_text(encoding="utf-8"))
    return [TicketInput.model_validate(item) for item in payload]
