"""Database tool.

MEMORY.md checklist: MCP Server tools -> database.

A tiny SQLite-backed "records" store. It demonstrates the three operations you
need to understand a database tool over MCP: create the table, insert a row, and
query rows back.

Safety & offline notes
-----------------------
* Defaults to an **in-memory** SQLite database (``:memory:``) so tests and demos
  leave nothing on disk and need no setup. A file path can be passed to persist.
* All queries are **parameterised** (``?`` placeholders) -- never string
  formatting -- so the store is not vulnerable to SQL injection.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional


class RecordsDB:
    """A minimal records store backed by SQLite.

    Each record has an auto-increment ``id``, a ``category`` and a ``content``.
    Keeping the schema tiny keeps the focus on the MCP mechanics rather than SQL.
    """

    def __init__(self, path: str = ":memory:") -> None:
        # check_same_thread=False keeps the in-memory DB usable if the async MCP
        # server touches it from a worker thread. For this small tool that is safe
        # because we never share a single connection across concurrent writers.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._create_table()

    def _create_table(self) -> None:
        """Create the records table if it does not already exist."""
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content  TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def insert(self, category: str, content: str) -> int:
        """Insert a record and return its new id. Uses a bound parameter."""
        if not category or not content:
            raise ValueError("category and content are required")
        cur = self._conn.execute(
            "INSERT INTO records (category, content) VALUES (?, ?)",
            (category, content),
        )
        self._conn.commit()
        return int(cur.lastrowid)

    def query(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all records, optionally filtered by ``category``.

        The category is passed as a bound parameter, so a value like
        ``"'; DROP TABLE records; --"`` is treated as a literal string, not SQL.
        """
        if category is None:
            cur = self._conn.execute("SELECT id, category, content FROM records ORDER BY id")
        else:
            cur = self._conn.execute(
                "SELECT id, category, content FROM records WHERE category = ? ORDER BY id",
                (category,),
            )
        return [dict(row) for row in cur.fetchall()]

    def count(self) -> int:
        """Return the total number of records."""
        cur = self._conn.execute("SELECT COUNT(*) AS n FROM records")
        return int(cur.fetchone()["n"])

    def close(self) -> None:
        self._conn.close()


def register(mcp) -> None:
    """Expose the records store as MCP tools on the given FastMCP server.

    The tools share a single process-lifetime in-memory database instance so the
    server keeps state between calls within a session.
    """
    db = RecordsDB()  # in-memory for the running server

    @mcp.tool()
    def db_insert(category: str, content: str) -> Dict[str, Any]:
        """Insert a record into the database. Returns the new record id."""
        record_id = db.insert(category, content)
        return {"id": record_id, "category": category, "content": content}

    @mcp.tool()
    def db_query(category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Query records, optionally filtered by category."""
        return db.query(category)
