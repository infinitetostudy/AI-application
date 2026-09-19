# Week 02 — Structured output classifier

Force JSON with official structured outputs / JSON Schema, not "please return JSON".

**Pass bar:** 10 sample tickets parse into `{intent, priority, entities, confidence, reason, needs_human}`. Low confidence must set `needs_human=true`.

Docs:
- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
