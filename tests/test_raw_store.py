from __future__ import annotations

import gzip
import json
from pathlib import Path

from govlexops.core import raw_store
from govlexops.etl import pipeline


def test_save_raw_response_writes_gzip_json(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(raw_store, "RAW_BASE_DIR", tmp_path / "raw")
    payload = {"hello": "world", "n": 1}

    out = raw_store.save_raw_response(payload, source="kr_law", key="query_인공지능")
    assert out.exists()
    assert out.suffix == ".gz"
    assert "kr_law" in str(out)

    with gzip.open(out, "rt", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == payload


def test_ensure_data_layout_creates_stage_dirs(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pipeline._ensure_data_layout()

    for path in (
        "data_index/raw",
        "data_index/normalized",
        "data_index/extracted",
        "data_index/chunks",
        "data_index/embeddings",
        "data_index/quality",
    ):
        assert (tmp_path / path).exists()
