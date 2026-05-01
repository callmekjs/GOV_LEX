from __future__ import annotations

from datetime import date
from pathlib import Path

from govlexops.integrations.store.factory import create_document_store
from govlexops.integrations.store.jsonl_store import JsonlDocumentStore
from govlexops.schemas.legal_document import LegalDocument, make_content_hash


def _doc(source_id: str, jurisdiction: str = "KR") -> LegalDocument:
    return LegalDocument(
        source_id=source_id,
        jurisdiction=jurisdiction,
        source_type="law" if jurisdiction == "KR" else "bill",
        language="ko" if jurisdiction == "KR" else "en",
        title=f"title-{source_id}",
        issued_date=date(2025, 1, 1),
        source_url=f"https://example.com/{source_id}",
        content_hash=make_content_hash(f"{source_id}_20250101"),
        metadata={},
    )


def test_jsonl_store_append_count_query(tmp_path: Path):
    store = JsonlDocumentStore(docs_path=tmp_path / "docs.jsonl")

    store.append([_doc("kr_1", "KR"), _doc("us_1", "US")])
    stats = store.count()
    assert stats["total"] == 2
    assert stats["KR"] == 1
    assert len(store.query(jurisdiction="US")) == 1


def test_sqlite_store_append_count_query(tmp_path: Path):
    db_path = tmp_path / "docs.sqlite"
    store = create_document_store("sqlite", sqlite_path=str(db_path))

    store.append([_doc("kr_2", "KR"), _doc("us_2", "US"), _doc("us_3", "US")])
    stats = store.count()
    assert stats == {"KR": 1, "US": 2, "total": 3}
    us_docs = store.query(jurisdiction="US")
    assert len(us_docs) == 2
