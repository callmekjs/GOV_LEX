"""content_hash 기반 영구 중복 기억 저장소. QA R01에서 사용.

[pipline_upgrade 0-6] 원자적 쓰기:
  mark_seen / mark_seen_many는 atomic_append_jsonl을 통해 staging → rename
  패턴으로 기록한다. 도중에 죽어도 seen_hashes.jsonl은 이전 상태 유지.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from govlexops.core.atomic import atomic_append_jsonl

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


def mark_seen_many(records: Iterable[dict]) -> int:
    """여러 record를 한 번의 atomic write로 기록한다.

    각 record는 최소 다음 키를 가진다:
      content_hash (필수), source_id, jurisdiction

    Returns:
        실제로 새로 기록된 건수. 이미 _seen에 있던 해시는 건너뛴다.

    원자성:
      atomic_append_jsonl을 사용. 도중 실패 시 SEEN_PATH는 변경되지 않고,
      메모리 캐시(_seen)도 갱신되지 않는다.
    """
    global _seen
    _ensure_loaded()
    assert _seen is not None

    new_records: list[dict] = []
    seen_in_batch: set[str] = set()
    for r in records:
        h = r.get("content_hash")
        if not h:
            continue
        if h in _seen or h in seen_in_batch:
            continue
        new_records.append(r)
        seen_in_batch.add(h)

    if not new_records:
        return 0

    SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [json.dumps(r, ensure_ascii=False) for r in new_records]

    written = atomic_append_jsonl(SEEN_PATH, lines)
    # atomic write가 성공한 후에만 메모리 캐시 갱신.
    # 실패 시엔 예외가 위로 올라가 여기 도달하지 않는다.
    for r in new_records:
        _seen.add(r["content_hash"])
    return written


def mark_seen(content_hash: str, source_id: str, jurisdiction: str) -> None:
    """단건 호환 wrapper.

    신규 코드는 mark_seen_many를 권장 (배치 atomic write로 비용 1/N).
    """
    mark_seen_many(
        [
            {
                "content_hash": content_hash,
                "source_id": source_id,
                "jurisdiction": jurisdiction,
            }
        ]
    )


def count_seen() -> int:
    _ensure_loaded()
    assert _seen is not None
    return len(_seen)
