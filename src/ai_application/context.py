"""Trim long ticket bodies so the context window is a budget, not a dump."""

from __future__ import annotations

import re

_ORDER = re.compile(r"\b(?:ORD|ORDER)[-_]?\d+\b", re.IGNORECASE)
_ACCT = re.compile(r"\b(?:acct|account)[-_]?\d+\b", re.IGNORECASE)
_EMAIL = re.compile(r"[A-Za-z0-9.\u4e00-\u9fff_+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_URL = re.compile(r"https?://[^\s]+")
_PATH = re.compile(r"(?<![A-Za-z])(/[\w./-]+)")
_HTTP = re.compile(r"\b(?:HTTP\s*)?[45]\d{2}\b", re.IGNORECASE)


def extract_metadata(text: str) -> list[str]:
    found: list[str] = []
    seen: set[str] = set()
    for pattern in (_ORDER, _ACCT, _EMAIL, _HTTP, _URL, _PATH):
        for match in pattern.findall(text):
            value = match.strip().rstrip(".,;，。")
            if value and value not in seen:
                seen.add(value)
                found.append(value)
    return found[:12]


def trim_body(body: str, *, max_body_chars: int = 800) -> tuple[str, bool]:
    text = body.strip()
    if len(text) <= max_body_chars:
        return text, False
    extracted = extract_metadata(text)
    tail = text[-max_body_chars:]
    header = (
        f"[trimmed body {len(text)} -> last {max_body_chars} chars]\n"
        f"extracted: {', '.join(extracted) if extracted else '(none)'}\n---\n"
    )
    return header + tail, True
