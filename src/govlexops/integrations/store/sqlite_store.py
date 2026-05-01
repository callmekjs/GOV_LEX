from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from govlexops.schemas.legal_document import LegalDocument


class SqliteDocumentStore:
    def __init__(self, db_path: Path | str = "data_index/normalized/docs.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    source_id TEXT PRIMARY KEY,
                    jurisdiction TEXT,
                    source_type TEXT,
                    issued_date TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_jurisdiction ON documents(jurisdiction)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_source_type ON documents(source_type)"
            )
            conn.commit()

    def append(self, docs: list[LegalDocument]) -> int:
        if not docs:
            return 0
        rows = [
            (
                d.source_id,
                d.jurisdiction,
                d.source_type,
                d.issued_date.isoformat(),
                json.dumps(d.model_dump(mode="json"), ensure_ascii=False),
            )
            for d in docs
        ]
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO documents
                (source_id, jurisdiction, source_type, issued_date, payload_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                rows,
            )
            conn.commit()
        return len(rows)

    def load_all(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT payload_json FROM documents").fetchall()
        return [json.loads(r[0]) for r in rows]

    def query(self, **filters) -> list[dict]:
        where = []
        params: list[str] = []
        allowed = {"jurisdiction", "source_type", "source_id"}
        for k, v in filters.items():
            if k not in allowed:
                continue
            where.append(f"{k} = ?")
            params.append(str(v))
        sql = "SELECT payload_json FROM documents"
        if where:
            sql += " WHERE " + " AND ".join(where)
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [json.loads(r[0]) for r in rows]

    def count(self) -> dict:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
            kr = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE jurisdiction = 'KR'"
            ).fetchone()[0]
            us = conn.execute(
                "SELECT COUNT(*) FROM documents WHERE jurisdiction = 'US'"
            ).fetchone()[0]
        return {"KR": int(kr), "US": int(us), "total": int(total)}
