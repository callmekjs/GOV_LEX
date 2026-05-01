"""[pipline_upgrade 0-6] seen_store의 atomic 동작 + 배치 API 테스트.

검증:
  - mark_seen_many 정상 기록
  - 빈 입력 no-op
  - 이미 본 해시는 스킵 (idempotent)
  - 배치 내부 중복 해시도 한 번만 기록
  - 단건 mark_seen 호환성 유지
  - 도중 실패 시 SEEN_PATH 미손상 + 메모리 캐시 미갱신
"""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from govlexops.core import seen_store


@pytest.fixture(autouse=True)
def isolated_seen_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """SEEN_PATH를 임시 경로로, 메모리 캐시를 None으로 초기화."""
    target = tmp_path / "seen.jsonl"
    monkeypatch.setattr(seen_store, "SEEN_PATH", target)
    monkeypatch.setattr(seen_store, "_seen", None)
    return target


def _records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_mark_seen_many_writes_records(isolated_seen_path: Path) -> None:
    written = seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
        {"content_hash": "h2", "source_id": "s2", "jurisdiction": "US"},
    ])

    assert written == 2
    assert seen_store.count_seen() == 2
    records = _records(isolated_seen_path)
    hashes = {r["content_hash"] for r in records}
    assert hashes == {"h1", "h2"}


def test_mark_seen_many_skips_already_seen(isolated_seen_path: Path) -> None:
    seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
    ])
    written = seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1-dup", "jurisdiction": "KR"},
        {"content_hash": "h2", "source_id": "s2", "jurisdiction": "US"},
    ])

    # h1은 스킵, h2만 새로 기록
    assert written == 1
    assert seen_store.count_seen() == 2
    # 디스크에도 h1은 한 번만 있다.
    records = _records(isolated_seen_path)
    h1_count = sum(1 for r in records if r["content_hash"] == "h1")
    assert h1_count == 1


def test_mark_seen_many_dedups_within_batch(isolated_seen_path: Path) -> None:
    """같은 배치에 중복 해시가 있어도 한 번만 기록한다."""
    written = seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
        {"content_hash": "h1", "source_id": "s1-again", "jurisdiction": "KR"},
        {"content_hash": "h2", "source_id": "s2", "jurisdiction": "US"},
    ])

    assert written == 2
    assert seen_store.count_seen() == 2


def test_mark_seen_many_empty_is_noop(isolated_seen_path: Path) -> None:
    written = seen_store.mark_seen_many([])
    assert written == 0
    assert not isolated_seen_path.exists()


def test_mark_seen_many_skips_missing_hash(isolated_seen_path: Path) -> None:
    """content_hash가 없는 record는 무시."""
    written = seen_store.mark_seen_many([
        {"content_hash": "", "source_id": "s0", "jurisdiction": "KR"},
        {"source_id": "s1", "jurisdiction": "KR"},  # hash 키 없음
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
    ])
    assert written == 1
    assert seen_store.is_seen("h1")


def test_mark_seen_compat(isolated_seen_path: Path) -> None:
    """단건 mark_seen 호환 wrapper가 mark_seen_many와 동일하게 작동."""
    seen_store.mark_seen("h1", "s1", "KR")
    seen_store.mark_seen("h1", "s1", "KR")  # 중복 호출

    assert seen_store.is_seen("h1")
    assert seen_store.count_seen() == 1
    records = _records(isolated_seen_path)
    assert len(records) == 1


def test_mark_seen_failure_preserves_file_and_cache(
    isolated_seen_path: Path,
) -> None:
    """atomic rename 실패 시 파일·메모리 캐시 모두 변경되면 안 된다."""
    seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
    ])
    original = isolated_seen_path.read_text(encoding="utf-8")
    cache_before = seen_store.count_seen()

    with patch("govlexops.core.atomic.os.replace", side_effect=OSError("boom")):
        with pytest.raises(OSError):
            seen_store.mark_seen_many([
                {"content_hash": "h2", "source_id": "s2", "jurisdiction": "US"},
            ])

    # 파일 보존
    assert isolated_seen_path.read_text(encoding="utf-8") == original
    # 메모리 캐시도 갱신 안 됨 (atomic write 후에만 갱신하도록 구현했으므로)
    assert seen_store.count_seen() == cache_before
    assert not seen_store.is_seen("h2")


def test_mark_seen_many_returns_zero_when_all_already_seen(
    isolated_seen_path: Path,
) -> None:
    seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
    ])
    written = seen_store.mark_seen_many([
        {"content_hash": "h1", "source_id": "s1", "jurisdiction": "KR"},
    ])

    assert written == 0
    # 빈 effective batch는 파일도 안 건드린다.
    records = _records(isolated_seen_path)
    assert len(records) == 1
