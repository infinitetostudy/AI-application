# AI Application Lab

一条龙学习 **AI 产品 + 自动化**：模型 API → RAG → Agent/MCP → Dify → n8n → 可上线。

远程仓库：https://github.com/infinitetostudy/AI-application

## 当前进度

- [x] 第 1 周骨架：流式 Chat API（可换模型地址）
- [x] 第 2 周：结构化工单分类（JSON Schema + 低置信度转人工）
- [ ] 第 3–16 周按 `weeks/` 目录推进，详见 [ROADMAP.md](ROADMAP.md)

## 目录

```
src/ai_application/     共享库（配置、LLM 客户端）
weeks/week01_chat_api/  第 1 周：流式 API
weeks/week02_* … 16     之后每周一个目录
evals/golden/           检索/应用黄金集
data/                   示例与本地数据（raw 不入库）
automations/n8n         n8n 工作流导出
automations/dify        Dify 应用导出
infra/                  自托管说明
```

## 快速开始（第 1 周）

需要：Python 3.11+、[uv](https://docs.astral.sh/uv/)

```powershell
cd E:\AI-application
copy .env.example .env
uv sync
uv run python scripts/check_env.py
uv run uvicorn weeks.week01_chat_api.app.main:app --reload --port 8010
```

打开 http://127.0.0.1:8010/health

## 第 2 周

```powershell
uv run python -m weeks.week02_classifier.run
```

API：`uv run uvicorn weeks.week02_classifier.app.main:app --reload --port 8011`

换模型只改 `.env` 里的 `LLM_BASE_URL` / `LLM_MODEL`，例如 Ollama：

```
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.1
```

## 技术栈约定（2026）

用：官方 SDK / 结构化输出、`create_agent`、LangGraph、LlamaIndex、MCP、Dify、n8n、Langfuse。

不用：`LLMChain`、`AgentExecutor`、`initialize_agent`、`create_react_agent`、AutoGPT 式无边界循环。
