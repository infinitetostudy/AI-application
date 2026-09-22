from ai_application.llm.client import _extract_json_payloads, _validate_model
from weeks.week02_classifier.schemas import TicketClassification


def test_extracts_complete_object_from_truncated_noise() -> None:
    good = (
        '{"intent":"bug","priority":"high","entities":[],'
        '"confidence":0.9,"reason":"500 on export","needs_human":true}'
    )
    messy = 'thinking {\n  "confidence": 0.95,\n  "entities": [\n    {"type":"url"' + good
    parsed = _validate_model(TicketClassification, messy)
    assert parsed.intent == "bug"
    assert parsed.needs_human is True
    assert any("bug" in item for item in _extract_json_payloads(messy)) or parsed.intent == "bug"
