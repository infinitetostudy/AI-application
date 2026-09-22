import asyncio

from ai_application.context import extract_metadata, trim_body
from ai_application.idempotency import MemoryIdempotencyStore
from weeks.week02_classifier.schemas import TicketClassification, TicketInput
from weeks.week03_context.classify import classify_ticket
from weeks.week03_context.prompts import COMPACT, FEW_SHOT, VERSIONS
from weeks.week03_context.run import load_golden, load_long_ticket


def test_trim_keeps_tail_and_ids() -> None:
    prefix = "无关会议纪要。" * 200
    tail = "最后：https://app.example.com 502，账号 acct-2201，订单 ORD-88421。"
    trimmed, changed = trim_body(prefix + tail, max_body_chars=120)
    assert changed is True
    assert "502" in trimmed
    assert "acct-2201" in trimmed
    meta = extract_metadata(prefix + tail)
    assert "ORD-88421" in meta
    assert "acct-2201" in meta


def test_short_body_not_trimmed() -> None:
    text, changed = trim_body("密码错误无法登录")
    assert changed is False
    assert text == "密码错误无法登录"


def test_few_shot_is_longer_than_compact() -> None:
    assert len(FEW_SHOT.system) - len(COMPACT.system) >= 200
    assert set(VERSIONS) == {"compact", "baseline", "few_shot"}


def test_golden_covers_ten_tickets() -> None:
    golden = load_golden()
    assert len(golden) == 10
    assert golden["t-003"]["intent"] == "bug"
    assert golden["t-008"]["intent"] == "bug"
    assert golden["t-009"]["intent"] == "question"


def test_long_ticket_is_over_budget() -> None:
    ticket = load_long_ticket()
    assert len(ticket.body) > 800
    assert "502" in ticket.body


class _FakeParsed:
    def __init__(self) -> None:
        self.value = TicketClassification(
            intent="account",
            priority="medium",
            entities=[],
            confidence=0.9,
            reason="cached-path test",
            needs_human=False,
        )
        self.usage = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
        self.raw_text = "{}"
        self.model = "fake"
        self.response_format = "json_schema"


class _FakeClient:
    def __init__(self) -> None:
        self.calls = 0

    async def chat_parsed(self, *args, **kwargs):
        self.calls += 1
        return _FakeParsed()


def test_same_request_id_is_idempotent() -> None:
    asyncio.run(_same_request_id_is_idempotent())


async def _same_request_id_is_idempotent() -> None:
    store = MemoryIdempotencyStore()
    client = _FakeClient()
    ticket = TicketInput(ticket_id="t-001", subject="login", body="cannot login")
    first = await classify_ticket(
        ticket, version="compact", request_id="rid-1", store=store, client=client
    )
    second = await classify_ticket(
        ticket, version="compact", request_id="rid-1", store=store, client=client
    )
    assert client.calls == 1
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert second.classification.intent == first.classification.intent
    assert second.total_tokens == 0
