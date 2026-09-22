"""Cache LLM completions by request_id so retries do not double-bill."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol


class IdempotencyStore(Protocol):
    def get(self, request_id: str) -> dict[str, Any] | None: ...

    def put(self, request_id: str, payload: dict[str, Any]) -> None: ...


class MemoryIdempotencyStore:
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}

    def get(self, request_id: str) -> dict[str, Any] | None:
        return self._data.get(request_id)

    def put(self, request_id: str, payload: dict[str, Any]) -> None:
        self._data[request_id] = payload


class SqliteIdempotencyStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS completions (
                request_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, request_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT payload FROM completions WHERE request_id = ?",
            (request_id,),
        ).fetchone()
        if row is None:
            return None
        return json.loads(row[0])

    def put(self, request_id: str, payload: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT OR IGNORE INTO completions (request_id, payload, created_at)
            VALUES (?, ?, ?)
            """,
            (
                request_id,
                json.dumps(payload, ensure_ascii=False),
                datetime.now(UTC).isoformat(),
            ),
        )
        self._conn.commit()
