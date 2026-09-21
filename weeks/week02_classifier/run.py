"""Classify the 10 sample tickets and fail if any result is not valid JSON."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from weeks.week02_classifier.classify import classify_ticket, load_samples
from weeks.week02_classifier.schemas import TicketClassification

REQUIRED_FIELDS = (
    "intent",
    "priority",
    "entities",
    "confidence",
    "reason",
    "needs_human",
)


async def run(sample_path: Path | None = None) -> int:
    tickets = load_samples(sample_path)
    if len(tickets) < 10:
        raise SystemExit(f"need 10 sample tickets, got {len(tickets)}")

    rows: list[dict] = []
    failures: list[str] = []
    for ticket in tickets:
        classification, parsed, latency_s = await classify_ticket(ticket)
        missing = [name for name in REQUIRED_FIELDS if name not in classification.model_dump()]
        if missing:
            failures.append(f"{ticket.ticket_id}: missing {missing}")
        if classification.confidence < 0.7 and not classification.needs_human:
            failures.append(f"{ticket.ticket_id}: low confidence but needs_human is false")
        TicketClassification.model_validate(classification.model_dump())
        row = {
            "ticket_id": ticket.ticket_id,
            "subject": ticket.subject,
            "latency_s": round(latency_s, 3),
            "response_format": parsed.response_format,
            "usage": parsed.usage,
            "classification": classification.model_dump(),
        }
        rows.append(row)
        flag = "HUMAN" if classification.needs_human else "auto"
        print(
            f"{ticket.ticket_id}  {classification.intent:<10}  "
            f"{classification.priority:<8}  conf={classification.confidence:.2f}  "
            f"{flag}  {parsed.response_format}  {latency_s:.2f}s"
        )

    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "results.jsonl"
    out_path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {out_path}")
    if failures:
        print("FAIL")
        for item in failures:
            print(f"  - {item}")
        return 1
    print(f"PASS  {len(rows)} tickets parsed")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=Path, default=None)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run(args.samples)))


if __name__ == "__main__":
    main()
