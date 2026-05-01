from __future__ import annotations

from govlexops.integrations.store.base import DocumentStore
from govlexops.integrations.store.jsonl_store import JsonlDocumentStore
from govlexops.integrations.store.sqlite_store import SqliteDocumentStore


def create_document_store(
    backend: str = "jsonl",
    *,
    sqlite_path: str = "data_index/normalized/docs.sqlite",
) -> DocumentStore:
    normalized = backend.strip().lower()
    if normalized == "jsonl":
        return JsonlDocumentStore()
    if normalized == "sqlite":
        return SqliteDocumentStore(db_path=sqlite_path)
    if normalized == "pgvector":
        raise NotImplementedError("pgvector backend is reserved for Phase 4.")
    raise ValueError(f"Unsupported store backend: {backend}")
