# Week 07 — Bare agent loop

Write a 50–80 line tool-calling loop. No agent framework.

Tools (only three): `search_kb`, `get_ticket`, `draft_reply`.
Hard limits: 8 steps, 30s timeout, unknown tools rejected.

**Pass bar:** On KB failure the agent retries or escalates, and does not spin forever.

Do not use `initialize_agent`, `AgentExecutor`, or `create_react_agent`.
