# Week 01 — Chat API

Streaming FastAPI service. Model provider is swapped by `LLM_BASE_URL`, not by rewriting business code.

## Pass bar

- Client sees token-by-token output
- Changing `LLM_BASE_URL` does not require code changes

## Run

```powershell
cd E:\AI-application
copy .env.example .env
uv sync
uv run uvicorn weeks.week01_chat_api.app.main:app --reload --port 8000
```

Health check: http://127.0.0.1:8000/health

```powershell
curl.exe -N -X POST http://127.0.0.1:8000/chat -H "Content-Type: application/json" -d "{\"messages\":[{\"role\":\"user\",\"content\":\"hello in one sentence\"}]}"
```

Ollama example in `.env`:

```
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.1
```
