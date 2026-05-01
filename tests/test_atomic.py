"""[pipline_upgrade 0-6] atomic_append_jsonl 단위 테스트.

검증 포인트:
  - 신규 target에 정상 기록
  - 기존 줄 보존 (append 의미)
  - 빈 입력은 no-op
  - 줄 끝 개행 자동 보정
  - 성공 시 staging 파일 잔존 안 함
  - 중간 실패 시 target은 호출 전 상태 그대로 (atomicity)
  - 실패 시 staging 정리
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from govlexops.core.atomic import atomic_append_jsonl


def test_creates_target_when_not_exists(tmp_path: Path) -> None:
    target = tmp_path / "out.jsonl"
    written = atomic_append_jsonl(target, ['{"a": 1}', '{"a": 2}'])

    assert written == 2
    assert target.exists()
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines == ['{"a": 1}', '{"a": 2}']


def test_preserves_existing_lines(tmp_path: Path) -> None:
    target = tmp_path / "out.jsonl"
    target.write_text('{"a": 1}\n{"a": 2}\n', encoding="utf-8")

    written = atomic_append_jsonl(target, ['{"a": 3}'])

    assert written == 1
    content = target.read_text(encoding="utf-8")
    assert content == '{"a": 1}\n{"a": 2}\n{"a": 3}\n'


def test_empty_input_is_noop(tmp_path: Path) -> None:
    target = tmp_path / "out.jsonl"
    target.write_text('{"a": 1}\n', encoding="utf-8")
    mtime_before = target.stat().st_mtime_ns

    written = atomic_append_jsonl(target, [])

    assert written == 0
    # 빈 입력은 파일을 건드리지 않아야 한다.
    assert target.read_text(encoding="utf-8") == '{"a": 1}\n'
    assert target.stat().st_mtime_ns == mtime_before


def test_normalizes_missing_newlines(tmp_path: Path) -> None:
    target = tmp_path / "out.jsonl"
    written = atomic_append_jsonl(target, ['no-newline-1', 'no-newline-2\n'])

    assert written == 2
    lines = target.read_text(encoding="utf-8").splitlines()
    assert lines == ['no-newline-1', 'no-newline-2']


def test_no_staging_left_on_success(tmp_path: Path) -> None:
    target = tmp_path / "out.jsonl"
    atomic_append_jsonl(target, ['{"a": 1}'])

    leftovers = list(tmp_path.glob("out.jsonl.staging.*"))
    assert leftovers == [], f"staging 파일이 정리되지 않음: {leftovers}"


def test_target_unchanged_on_failure(tmp_path: Path) -> None:
    """os.replace가 실패하면 target은 호출 전 상태 그대로여야 한다."""
    target = tmp_path / "out.jsonl"
    target.write_text('{"original": true}\n', encoding="utf-8")
    original_content = target.read_text(encoding="utf-8")

    # os.replace를 강제로 터뜨려 atomic rename 실패를 시뮬레이션.
    with patch("govlexops.core.atomic.os.replace", side_effect=OSError("disk full")):
        with pytest.raises(OSError):
            atomic_append_jsonl(target, ['{"new": true}'])

    # target은 손상되지 않아야 한다.
    assert target.read_text(encoding="utf-8") == original_content


def test_staging_cleaned_up_on_failure(tmp_path: Path) -> None:
    """실패하면 staging 파일은 정리돼야 한다."""
    target = tmp_path / "out.jsonl"
    target.write_text('{"a": 1}\n', encoding="utf-8")

    with patch("govlexops.core.atomic.os.replace", side_effect=OSError("boom")):
        with pytest.raises(OSError):
            atomic_append_jsonl(target, ['{"new": 1}'])

    leftovers = list(tmp_path.glob("out.jsonl.staging.*"))
    assert leftovers == [], f"실패 후 staging 파일이 잔존: {leftovers}"


def test_unicode_content_preserved(tmp_path: Path) -> None:
    """한글·이모지가 ensure_ascii=False로 그대로 들어가는지."""
    target = tmp_path / "out.jsonl"
    atomic_append_jsonl(target, ['{"title": "인공지능 기본법"}', '{"emoji": "📚"}'])

    content = target.read_text(encoding="utf-8")
    assert "인공지능 기본법" in content
    assert "📚" in content


def test_returns_count_of_appended_lines(tmp_path: Path) -> None:
    target = tmp_path / "out.jsonl"
    target.write_text('{"old": 1}\n{"old": 2}\n{"old": 3}\n', encoding="utf-8")

    written = atomic_append_jsonl(target, ['a', 'b', 'c', 'd'])

    # 반환값은 새로 추가된 줄 수만, 누적 총합 아님.
    assert written == 4
    assert len(target.read_text(encoding="utf-8").splitlines()) == 7
