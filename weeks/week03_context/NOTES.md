# Week 03 notes — what extra tokens bought

Live eval on 10 labeled tickets (`evals/golden/week03_tickets.json`).

| version | intent | needs_human | both | avg prompt tokens | avg total tokens |
|---|---|---|---|---|---|
| compact | 80% | 80% | 60% | 79 | 274 |
| baseline | 60% | 100% | 60% | 189 | 788 |
| few_shot | 100% | 100% | 100% | 429 | 832 |

## Pass bar

**few_shot vs compact: +350 prompt tokens, +40 percentage points both-correct.**

Those tokens paid for examples that compact kept getting wrong:

- t-009 plan comparison: compact said `feature`, few_shot said `question`
- t-010 vague grey-button: compact said `bug`, few_shot said `other` + human
- t-001 / t-002: intent was already right, but compact missed the human/auto policy; few_shot matched both

**baseline vs compact: +110 prompt tokens, +0 both-correct.**  
Longer field rules without examples spent tokens and did not raise joint accuracy. More text is not automatically better.

## Trim

A 1402-char forwarded email was cut to the last 400 chars plus extracted ids. The model still saw `502` / `acct-2201` and returned `bug` + `critical`.

## Idempotency

`request_id=idem-demo:t-001` twice: first call 298 tokens, second `cache_hit=true` and **0 tokens**. Same intent. SQLite store is `output/idempotency.sqlite`.
