# Week 02 — Structured output classifier

Force JSON with official structured outputs / JSON Schema, not "please return JSON".
Low confidence (`< 0.7`) always sets `needs_human=true`, even if the model disagrees.

**Pass bar:** 10 sample tickets parse into `{intent, priority, entities, confidence, reason, needs_human}`.

## Run the 10 tickets

```powershell
cd E:\AI-application
uv run python -m weeks.week02_classifier.run
```

Expect `PASS  10 tickets parsed`. Results go to `weeks/week02_classifier/output/results.jsonl` (gitignored).

## API

```powershell
uv run uvicorn weeks.week02_classifier.app.main:app --reload --port 8011
```

```bash
curl http://127.0.0.1:8011/health

curl -X POST http://127.0.0.1:8011/classify \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"t-001","subject":"无法登录","body":"昨天还能登录，今天提示密码错误"}'
```

PowerShell:

```powershell
curl.exe -X POST http://127.0.0.1:8011/classify -H "Content-Type: application/json" --data-raw '{"ticket_id":"t-001","subject":"cannot login","body":"password error since this morning"}'
```

## What this week teaches

- `response_format.json_schema` is the contract; Pydantic validates it
- If the provider rejects `json_schema`, the client retries `json_object` once
- Policy lives in code: `apply_policy()` is not a prompt

Docs:
- OpenAI Structured Outputs: https://platform.openai.com/docs/guides/structured-outputs
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
