# Week 09 — MCP server + LangGraph when needed

Expose `search_kb` / `get_ticket` as an MCP server. Connect it to the agent and to Cursor.
Use LangGraph `StateGraph` only if you need explicit branch / resume / approval flow.

Docs:
- https://modelcontextprotocol.io/specification/2026-07-28
- https://docs.langchain.com/oss/python/langchain/mcp
- https://pydantic.dev/docs/ai/mcp/overview/
