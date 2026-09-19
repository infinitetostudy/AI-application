# Week 14 — Retry, idempotency, approval

Failed HTTP calls retry with backoff, then Error Workflow.
Idempotency key = `ticket_id`. Low confidence waits for a human.

**Pass bar:** Replaying the same webhook 3 times creates one business record.
