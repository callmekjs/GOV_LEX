"""[pipline_upgrade 0-5] core/logging.py 테스트.

요구사항:
  - setup_logging(run_dir=...) 호출 시 run_dir/pipeline.log 생성
  - 로그가 콘솔 + 파일 양쪽으로 흘러간다
  - 두 번 호출해도 핸들러가 누적되지 않는다(idempotent)
  - run_dir이 없으면 콘솔만 부착되고 파일 핸들러는 0개
"""
import logging
from pathlib import Path

from govlexops.core.logging import setup_logging


def _flush_root_handlers() -> None:
    """파일 핸들러가 즉시 디스크에 반영되도록 강제 flush."""
    for h in logging.getLogger().handlers:
        try:
            h.flush()
        except Exception:
            pass


def _file_handler_count(root: logging.Logger) -> int:
    return sum(
        1 for h in root.handlers
        if isinstance(h, logging.FileHandler)
    )


def _stream_handler_count(root: logging.Logger) -> int:
    # FileHandler는 StreamHandler의 서브클래스이므로 제외해야 한다.
    return sum(
        1 for h in root.handlers
        if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
    )


def test_setup_logging_creates_pipeline_log(tmp_path: Path) -> None:
    """run_dir/pipeline.log 파일이 생성되고 로그가 기록된다."""
    setup_logging(run_dir=tmp_path)

    log = logging.getLogger("govlexops.test_setup")
    log.info("hello world")
    _flush_root_handlers()

    log_file = tmp_path / "pipeline.log"
    assert log_file.exists(), "pipeline.log가 생성되지 않았습니다"

    content = log_file.read_text(encoding="utf-8")
    assert "hello world" in content
    assert "INFO" in content
    assert "govlexops.test_setup" in content


def test_setup_logging_without_run_dir_attaches_only_console(tmp_path: Path) -> None:
    """run_dir 미지정 시 콘솔 핸들러만 부착되고 파일 핸들러는 없다."""
    setup_logging(run_dir=None)
    root = logging.getLogger()

    assert _stream_handler_count(root) == 1
    assert _file_handler_count(root) == 0


def test_setup_logging_idempotent(tmp_path: Path) -> None:
    """두 번 호출해도 핸들러가 1+1=2를 넘지 않는다.

    매 호출마다 기존 핸들러를 제거 후 재부착하므로
    호출 횟수와 무관하게 콘솔 1개 + 파일 1개로 일정해야 한다.
    """
    setup_logging(run_dir=tmp_path)
    setup_logging(run_dir=tmp_path)
    setup_logging(run_dir=tmp_path)

    root = logging.getLogger()
    assert _stream_handler_count(root) == 1
    assert _file_handler_count(root) == 1


def test_setup_logging_switches_log_file_per_run(tmp_path: Path) -> None:
    """매 run마다 새 run_dir에 새 pipeline.log를 쓴다.

    이전 run의 로그가 다음 run 파일에 누락 또는 누적되면 안 된다.
    """
    run1 = tmp_path / "run1"
    run2 = tmp_path / "run2"

    setup_logging(run_dir=run1)
    logging.getLogger("govlexops.test").info("first run only")
    _flush_root_handlers()

    setup_logging(run_dir=run2)
    logging.getLogger("govlexops.test").info("second run only")
    _flush_root_handlers()

    log1 = (run1 / "pipeline.log").read_text(encoding="utf-8")
    log2 = (run2 / "pipeline.log").read_text(encoding="utf-8")

    assert "first run only" in log1
    assert "second run only" not in log1, (
        "첫 run 로그에 두 번째 run의 메시지가 섞여있습니다 — "
        "setup_logging가 핸들러를 정리하지 않고 추가만 하고 있습니다."
    )
    assert "second run only" in log2
    assert "first run only" not in log2


def test_setup_logging_downgrades_noisy_loggers(tmp_path: Path) -> None:
    """urllib3·requests 같은 외부 라이브러리는 WARNING 이상만 흘리도록 다운그레이드."""
    setup_logging(run_dir=tmp_path)

    assert logging.getLogger("urllib3").level == logging.WARNING
    assert logging.getLogger("requests").level == logging.WARNING
