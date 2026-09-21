from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Intent = Literal[
    "bug",
    "billing",
    "feature",
    "account",
    "question",
    "complaint",
    "other",
]
Priority = Literal["low", "medium", "high", "critical"]
EntityType = Literal["order_id", "email", "product", "url", "account_id", "other"]


class Entity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: EntityType
    value: str = Field(min_length=1)


class TicketClassification(BaseModel):
    """Forced structured result. Do not rely on free-form JSON in the prompt."""

    model_config = ConfigDict(extra="forbid")

    intent: Intent
    priority: Priority
    entities: list[Entity]
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1)
    needs_human: bool


class TicketInput(BaseModel):
    ticket_id: str
    subject: str
    body: str
    channel: str = "email"
