"""GovLex-Ops 통일 logging 설정.

[pipline_upgrade 0-5]
이전엔 모든 진행상황을 print()로 출력했다. 단점:
  - 로그 레벨(INFO/WARNING/ERROR) 구분 불가
  - 파일 저장 안 됨 → 운영 환경에서 사후 추적 불가
  - 외부 라이브러리 로그와 섞여 grep 불편

이후엔 표준 logging으로 일원화한다:
  - 콘솔(stdout) + runs/<run_id>/pipeline.log 동시 출력
  - 레벨별 필터링 가능 (운영 시 WARNING 이상만 등)
  - 모듈별 logger 트리 (govlexops.etl.ingest.kr_law 등) → 모듈별 grep 가능
  - urllib3·requests 같은 noisy 외부 라이브러리는 WARNING으로 다운그레이드

사용:
  from govlexops.core.logging import setup_logging
  setup_logging(run_dir=run_dir)        # 파이프라인 시작 시 1회
  log = logging.getLogger(__name__)     # 각 모듈 상단
  log.info("KR law collected: %d docs", n)
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional

_LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    run_dir: Optional[Path] = None,
    level: int = logging.INFO,
) -> None:
    """루트 로거를 govlex 표준 형식으로 (재)설정한다.

    멱등성:
      매 호출 시 기존 핸들러를 모두 제거 후 재부착한다.
      이렇게 해야 새 run마다 새 pipeline.log 파일에 쓰이게 된다.

    Args:
        run_dir: 지정하면 run_dir/pipeline.log에 파일 핸들러 추가.
        level: 기본 로그 레벨 (INFO).
    """
    root = logging.getLogger()

    # 기존 핸들러 정리 (이전 run의 file handler가 남아있지 않도록)
    for h in list(root.handlers):
        root.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass

    root.setLevel(level)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # 콘솔 핸들러
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # 파일 핸들러 (run_dir 지정 시)
    if run_dir is not None:
        run_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            run_dir / "pipeline.log",
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    # 외부 라이브러리 노이즈 다운그레이드
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
