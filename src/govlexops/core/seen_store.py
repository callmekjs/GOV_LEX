"""content_hash 기반 영구 중복 기억 저장소. QA R01에서 사용."""
from __future__ import annotations

import json
from pathlib import Path

SEEN_PATH = Path("data_index/normalized/seen_hashes.jsonl")

_seen: set[str] | None = None


def _ensure_loaded() -> None:
    global _seen
    if _seen is not None:
        return
    _seen = set()
    if not SEEN_PATH.exists():
        return
    with open(SEEN_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                h = obj.get("content_hash")
                if h:
                    _seen.add(h)
            except json.JSONDecodeError:
                continue


def is_seen(content_hash: str) -> bool:
    _ensure_loaded()
    assert _seen is not None
    return content_hash in _seen


def mark_seen(content_hash: str, source_id: str, jurisdiction: str) -> None:
    global _seen
    _ensure_loaded()
    assert _seen is not None
    if content_hash in _seen:
        return
    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "content_hash": content_hash,
        "source_id": source_id,
        "jurisdiction": jurisdiction,
    }
    with open(SEEN_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    _seen.add(content_hash)


def count_seen() -> int:
    _ensure_loaded()
    assert _seen is not None
    return len(_seen)