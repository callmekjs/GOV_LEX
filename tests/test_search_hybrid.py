from __future__ import annotations

import json
from pathlib import Path

from govlexops.search import indexer


def test_hybrid_search_ai_expands_to_korean_synonym(tmp_path: Path, monkeypatch):
    docs_path = tmp_path / "docs.jsonl"
    docs = [
        {
            "source_id": "kr_1",
            "jurisdiction": "KR",
            "source_type": "law",
            "language": "ko",
            "title": "인공지능 기본법",
            "issued_date": "2024-01-01",
            "source_url": "https://example.kr",
            "content_hash": "h1",
            "metadata": {},
        },
        {
            "source_id": "us_1",
            "jurisdiction": "US",
            "source_type": "bill",
            "language": "en",
            "title": "Tax Reform Act",
            "issued_date": "2024-01-01",
            "source_url": "https://example.us",
            "content_hash": "h2",
            "metadata": {},
        },
    ]
    docs_path.write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in docs) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(indexer, "DOCS_PATH", docs_path)

    results = indexer.search(query="AI", top_k=5, jurisdiction="전체", mode="hybrid")
    assert results
    assert results[0]["source_id"] == "kr_1"


def test_bm25_mode_respects_jurisdiction_filter(tmp_path: Path, monkeypatch):
    docs_path = tmp_path / "docs.jsonl"
    docs = [
        {
            "source_id": "kr_1",
            "jurisdiction": "KR",
            "source_type": "law",
            "language": "ko",
            "title": "데이터 기본법",
            "issued_date": "2024-01-01",
            "source_url": "https://example.kr",
            "content_hash": "h1",
            "metadata": {},
        },
        {
            "source_id": "us_1",
            "jurisdiction": "US",
            "source_type": "bill",
            "language": "en",
            "title": "Data Governance Act",
            "issued_date": "2024-01-01",
            "source_url": "https://example.us",
            "content_hash": "h2",
            "metadata": {},
        },
    ]
    docs_path.write_text(
        "\n".join(json.dumps(d, ensure_ascii=False) for d in docs) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(indexer, "DOCS_PATH", docs_path)

    results = indexer.search(query="Data", top_k=5, jurisdiction="US", mode="bm25")
    assert len(results) == 1
    assert results[0]["jurisdiction"] == "US"
