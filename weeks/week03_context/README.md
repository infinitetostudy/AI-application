# Week 03 — Context engineering

Treat the context window as a budget. Compare prompt versions on accuracy vs tokens.
The same `request_id` must not call the model twice.

**Pass bar:** You can explain what extra tokens bought. Idempotent `request_id`.

## Run

```powershell
cd E:\AI-application
uv run python -m weeks.week03_context
```

Writes `weeks/week03_context/output/eval.csv` and `summary.csv`.

## API

```powershell
uv run uvicorn weeks.week03_context.app.main:app --reload --port 8012
```

Send the same `request_id` twice; the second response has `"cache_hit": true`.

```bash
curl -X POST http://127.0.0.1:8012/classify \
  -H "Content-Type: application/json" \
  -d '{"ticket_id":"t-001","subject":"login","body":"password error","request_id":"req-1","version":"few_shot"}'
```

## Versions

| name | what you pay for |
|---|---|
| `compact` | tiny system prompt |
| `baseline` | week 02 field rules |
| `few_shot` | baseline + paraphrased examples (~+200 tokens) |

Long tickets keep subject + extracted ids + the **last N characters** of the body.

## Live result (this lab)

`few_shot` vs `compact`: **+350 prompt tokens, +40 points both-correct** (60% → 100%).
`baseline` spent extra tokens and stayed at 60%. Details in [NOTES.md](NOTES.md).
