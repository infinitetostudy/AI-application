from ai_application.config import settings
from ai_application.llm.schema import strict_json_schema
from weeks.week02_classifier.classify import apply_policy
from weeks.week02_classifier.schemas import TicketClassification


def _sample(**overrides: object) -> TicketClassification:
    payload = {
        "intent": "question",
        "priority": "low",
        "entities": [],
        "confidence": 0.9,
        "reason": "clear how-to question",
        "needs_human": False,
    }
    payload.update(overrides)
    return TicketClassification.model_validate(payload)


def test_low_confidence_forces_human() -> None:
    result = apply_policy(_sample(confidence=0.4, needs_human=False), threshold=0.7)
    assert result.needs_human is True


def test_high_confidence_keeps_auto() -> None:
    result = apply_policy(_sample(confidence=0.91, needs_human=False), threshold=0.7)
    assert result.needs_human is False


def test_already_human_stays_human() -> None:
    result = apply_policy(_sample(confidence=0.95, needs_human=True), threshold=0.7)
    assert result.needs_human is True


def test_strict_schema_forbids_extra_fields() -> None:
    schema = strict_json_schema(TicketClassification)
    assert schema["additionalProperties"] is False
    assert set(schema["required"]) == {
        "intent",
        "priority",
        "entities",
        "confidence",
        "reason",
        "needs_human",
    }


def test_default_threshold_matches_week02() -> None:
    assert settings.classify_confidence_threshold == 0.7
