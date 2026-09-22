from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from ai_application.config import settings
from ai_application.context import trim_body
from ai_application.idempotency import IdempotencyStore
from ai_application.llm.client import LLMClient, ParsedResult
from ai_application.llm.types import ChatMessage
from weeks.week02_classifier.classify import apply_policy
from weeks.week02_classifier.schemas import TicketClassification, TicketInput
from weeks.week03_context.prompts import VERSIONS, PromptVersion


@dataclass(frozen=True)
class ClassifyOutcome:
    classification: TicketClassification
    parsed: ParsedResult[TicketClassification] | None
    latency_s: float
    cache_hit: bool
    prompt_version: str
    trimmed: bool
    request_id: str

    @property
    def prompt_tokens(self) -> int:
        if self.parsed is None:
            return 0
        return self.parsed.usage.get("prompt_tokens", 0)

    @property
    def total_tokens(self) -> int:
        if self.parsed is None:
            return 0
        return self.parsed.usage.get("total_tokens", 0)


def prepare_ticket(ticket: TicketInput, *, max_body_chars: int | None = None) -> tuple[TicketInput, bool]:
    cutoff = settings.context_max_body_chars if max_body_chars is None else max_body_chars
    body, trimmed = trim_body(ticket.body, max_body_chars=cutoff)
    if not trimmed:
        return ticket, False
    return ticket.model_copy(update={"body": body}), True


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
    version: str | PromptVersion = "baseline",
    request_id: str | None = None,
    store: IdempotencyStore | None = None,
    client: LLMClient | None = None,
    max_body_chars: int | None = None,
) -> ClassifyOutcome:
    prompt = version if isinstance(version, PromptVersion) else VERSIONS[version]
    prepared, trimmed = prepare_ticket(ticket, max_body_chars=max_body_chars)
    rid = request_id or f"{prompt.name}:{prepared.ticket_id}"

    if store is not None:
        cached = store.get(rid)
        if cached is not None:
            return ClassifyOutcome(
                classification=TicketClassification.model_validate(cached["classification"]),
                parsed=None,
                latency_s=0.0,
                cache_hit=True,
                prompt_version=prompt.name,
                trimmed=bool(cached.get("trimmed", trimmed)),
                request_id=rid,
            )

    llm = client or LLMClient()
    messages = [
        ChatMessage(role="system", content=prompt.system),
        ChatMessage(role="user", content=_user_prompt(prepared)),
    ]
    started = perf_counter()
    parsed = await llm.chat_parsed(messages, TicketClassification, temperature=0.0)
    latency_s = perf_counter() - started
    classification = apply_policy(parsed.value)
    outcome = ClassifyOutcome(
        classification=classification,
        parsed=parsed,
        latency_s=latency_s,
        cache_hit=False,
        prompt_version=prompt.name,
        trimmed=trimmed,
        request_id=rid,
    )
    if store is not None:
        store.put(
            rid,
            {
                "classification": classification.model_dump(),
                "trimmed": trimmed,
                "usage": parsed.usage,
            },
        )
    return outcome
