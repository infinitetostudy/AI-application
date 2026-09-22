"""Compare prompt versions: accuracy vs tokens. Prove request_id is idempotent."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
from collections import defaultdict
from pathlib import Path

from ai_application.idempotency import SqliteIdempotencyStore
from weeks.week02_classifier.classify import load_samples
from weeks.week02_classifier.schemas import TicketInput
from weeks.week03_context.classify import classify_ticket
from weeks.week03_context.prompts import VERSIONS

ROOT = Path(__file__).resolve().parents[2]
GOLDEN_PATH = ROOT / "evals" / "golden" / "week03_tickets.json"
OUT_DIR = Path(__file__).parent / "output"
LONG_PATH = Path(__file__).parent / "samples" / "long_ticket.json"


def load_golden() -> dict[str, dict]:
    rows = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    return {row["ticket_id"]: row for row in rows}


def load_long_ticket() -> TicketInput:
    raw = json.loads(LONG_PATH.read_text(encoding="utf-8"))
    noise = ("会议纪要填充，与故障无关。" * 80) + "\n"
    incident = (
        "请看最后这段：https://app.example.com 从 21:40 起全部 502。"
        "账号 acct-2201。这是 P0，请马上升级值班。"
    )
    return TicketInput.model_validate({**raw, "body": raw["body"] + noise + incident})


def _score(pred_intent: str, pred_human: bool, gold: dict) -> dict[str, int]:
    return {
        "intent_ok": int(pred_intent == gold["intent"]),
        "human_ok": int(pred_human == gold["needs_human"]),
        "both_ok": int(pred_intent == gold["intent"] and pred_human == gold["needs_human"]),
    }


async def run_eval() -> dict:
    tickets = load_samples()
    golden = load_golden()
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / "eval.csv"
    rows = _read_csv(csv_path)
    done = {(row["version"], row["ticket_id"]) for row in rows}
    for version in VERSIONS:
        for ticket in tickets:
            key = (version, ticket.ticket_id)
            if key in done:
                print(f"{version:<9} {ticket.ticket_id}  skip (checkpoint)")
                continue
            gold = golden[ticket.ticket_id]
            try:
                outcome = await classify_ticket(
                    ticket,
                    version=version,
                    request_id=f"eval:{version}:{ticket.ticket_id}",
                )
            except Exception as exc:  # noqa: BLE001 — keep the rest of the eval running
                print(f"{version:<9} {ticket.ticket_id}  ERROR {type(exc).__name__}: {exc}")
                row = {
                    "ticket_id": ticket.ticket_id,
                    "version": version,
                    "pred_intent": "",
                    "gold_intent": gold["intent"],
                    "pred_needs_human": "",
                    "gold_needs_human": gold["needs_human"],
                    "confidence": "",
                    "prompt_tokens": 0,
                    "total_tokens": 0,
                    "latency_s": 0,
                    "cache_hit": False,
                    "trimmed": False,
                    "intent_ok": 0,
                    "human_ok": 0,
                    "both_ok": 0,
                    "error": str(exc),
                }
                rows.append(row)
                write_csv(csv_path, rows)
                continue
            marks = _score(
                outcome.classification.intent,
                outcome.classification.needs_human,
                gold,
            )
            row = {
                "ticket_id": ticket.ticket_id,
                "version": version,
                "pred_intent": outcome.classification.intent,
                "gold_intent": gold["intent"],
                "pred_needs_human": outcome.classification.needs_human,
                "gold_needs_human": gold["needs_human"],
                "confidence": outcome.classification.confidence,
                "prompt_tokens": outcome.prompt_tokens,
                "total_tokens": outcome.total_tokens,
                "latency_s": round(outcome.latency_s, 3),
                "cache_hit": outcome.cache_hit,
                "trimmed": outcome.trimmed,
                "error": "",
                **marks,
            }
            rows.append(row)
            write_csv(csv_path, rows)
            print(
                f"{version:<9} {ticket.ticket_id}  "
                f"pred={outcome.classification.intent:<10} gold={gold['intent']:<10} "
                f"tok={outcome.total_tokens:<5} "
                f"{'OK' if marks['both_ok'] else 'MISS'}"
            )
    return {"rows": rows}


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


async def run_trim_demo() -> dict:
    ticket = load_long_ticket()
    outcome = await classify_ticket(
        ticket,
        version="few_shot",
        request_id="eval:trim:t-long-001",
        max_body_chars=400,
    )
    print(
        f"long ticket trimmed={outcome.trimmed} intent={outcome.classification.intent} "
        f"priority={outcome.classification.priority} tokens={outcome.total_tokens}"
    )
    return {
        "ticket_id": ticket.ticket_id,
        "body_chars": len(ticket.body),
        "trimmed": outcome.trimmed,
        "intent": outcome.classification.intent,
        "priority": outcome.classification.priority,
        "needs_human": outcome.classification.needs_human,
        "prompt_tokens": outcome.prompt_tokens,
    }


async def run_idempotency_demo(store: SqliteIdempotencyStore) -> dict:
    ticket = load_samples()[0]
    first = await classify_ticket(
        ticket,
        version="compact",
        request_id="idem-demo:t-001",
        store=store,
    )
    second = await classify_ticket(
        ticket,
        version="compact",
        request_id="idem-demo:t-001",
        store=store,
    )
    print(
        f"idempotency first_hit={first.cache_hit} second_hit={second.cache_hit} "
        f"same_intent={first.classification.intent == second.classification.intent}"
    )
    return {
        "first_cache_hit": first.cache_hit,
        "second_cache_hit": second.cache_hit,
        "same_intent": first.classification.intent == second.classification.intent,
        "first_tokens": first.total_tokens,
        "second_tokens": second.total_tokens,
    }


def summarize(rows: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        grouped[row["version"]].append(row)
    summary = []
    for version, items in grouped.items():
        n = len(items)
        summary.append(
            {
                "version": version,
                "n": n,
                "intent_acc": round(sum(_as_number(i["intent_ok"]) for i in items) / n, 3),
                "human_acc": round(sum(_as_number(i["human_ok"]) for i in items) / n, 3),
                "both_acc": round(sum(_as_number(i["both_ok"]) for i in items) / n, 3),
                "avg_prompt_tokens": round(sum(_as_number(i["prompt_tokens"]) for i in items) / n, 1),
                "avg_total_tokens": round(sum(_as_number(i["total_tokens"]) for i in items) / n, 1),
            }
        )
    return summary


def _as_number(value: object) -> float:
    if value in ("", None):
        return 0.0
    if isinstance(value, bool):
        return float(value)
    return float(value)


def write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


async def main_async() -> int:
    OUT_DIR.mkdir(exist_ok=True)
    store = SqliteIdempotencyStore(OUT_DIR / "idempotency.sqlite")
    eval_result = await run_eval()
    rows = eval_result["rows"]
    summary = summarize(rows)
    trim_demo = await run_trim_demo()
    idem = await run_idempotency_demo(store)

    write_csv(OUT_DIR / "eval.csv", rows)
    write_csv(OUT_DIR / "summary.csv", summary)
    (OUT_DIR / "extras.json").write_text(
        json.dumps({"trim": trim_demo, "idempotency": idem}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n=== summary ===")
    for item in summary:
        print(
            f"{item['version']:<9} intent={item['intent_acc']:.0%}  "
            f"human={item['human_acc']:.0%}  both={item['both_acc']:.0%}  "
            f"prompt_tok={item['avg_prompt_tokens']}  total_tok={item['avg_total_tokens']}"
        )
    compact = next(item for item in summary if item["version"] == "compact")
    few = next(item for item in summary if item["version"] == "few_shot")
    delta_tok = few["avg_prompt_tokens"] - compact["avg_prompt_tokens"]
    delta_acc = few["both_acc"] - compact["both_acc"]
    print(
        f"few_shot vs compact: +{delta_tok:.0f} prompt tokens, "
        f"{delta_acc:+.0%} both-correct"
    )
    if not idem["second_cache_hit"] or idem["second_tokens"] != 0:
        print("FAIL idempotency")
        return 1
    print("PASS idempotency (same request_id did not call the model again)")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    raise SystemExit(asyncio.run(main_async()))


if __name__ == "__main__":
    main()
