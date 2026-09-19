# Stack lock (2026)

| Layer | Use | Do not start with |
|---|---|---|
| Language | Python 3.11+, FastAPI, Pydantic | Java/Go for the lab |
| Models | OpenAI-compatible HTTP + structured output | LangChain 0.x tutorials |
| Agents | `langchain.agents.create_agent`, then LangGraph | `AgentExecutor`, `create_react_agent` |
| Data | LlamaIndex + pgvector, then hybrid/rerank | Vector-only RAG as the end state |
| Tools | MCP | Homegrown plugin protocol |
| Product | Dify | Building your own workflow studio first |
| Automation | n8n | Temporal/Airflow first |
| Observability | Langfuse | print-only debugging |

Official docs only. Prefer changelogs over 2023–2024 blog posts.
