from ai_application.llm.types import ChatMessage, ChatRequest


def test_chat_request_roundtrip() -> None:
    req = ChatRequest(messages=[ChatMessage(role="user", content="hello")], request_id="t-1")
    assert req.model_dump()["messages"][0]["content"] == "hello"
    assert req.request_id == "t-1"
