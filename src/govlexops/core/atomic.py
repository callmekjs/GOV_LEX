"""원자적 파일 쓰기 헬퍼.

[pipline_upgrade 0-6]
이전엔 `open(path, "a")`로 직접 append했다. 단점:
  - 100건 중 50건째에서 프로세스가 죽으면 반쪽 파일이 영구히 남는다.
  - 다음 실행 때 부분 데이터와 새 데이터가 섞여 디버깅 불가.
  - 사용자가 Ctrl+C로 중단해도 데이터가 깨진다.

이후엔 staging → atomic rename 패턴을 쓴다:
  1. target_dir에 임시 staging 파일 생성
  2. 기존 target이 있으면 staging에 복사
  3. staging에 새 줄을 append (이건 staging 내부에서 일어나므로 target은 무사)
  4. os.replace(staging, target)  ← 여기가 atomic. POSIX/Windows 모두 보장.

어떤 단계에서 죽어도 target은 "이전 상태" 또는 "완전한 새 상태" 둘 중 하나다.
즉 docs.jsonl이 반쪽이 되는 일은 없다.

비용:
  매 호출마다 기존 파일 전체를 staging으로 복사하므로
  파일이 커질수록 O(file_size). 포트폴리오 규모(수만 줄)에선 문제없음.
  대규모(GB+)로 가면 SQLite/RDB로 이전 (Phase 2-6 어댑터 패턴 참조).
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Iterable


def atomic_append_jsonl(target: Path, lines: Iterable[str]) -> int:
    """target JSONL 파일에 새 줄들을 atomic하게 append한다.

    Args:
        target: 대상 파일 경로 (없으면 새로 생성).
        lines: 추가할 줄들. 각 줄 끝의 개행 문자는 자동으로 보정.

    Returns:
        실제로 추가된 줄 수.

    Raises:
        OSError: 디스크 가득참, 권한 부족 등. target은 변경되지 않는다.

    동시성:
        같은 target에 대해 여러 프로세스가 동시 호출하면 마지막 replace가 이긴다.
        파이프라인은 단일 run을 가정하므로 PID 기반 staging 이름으로
        같은 머신 내 우발적 충돌만 회피한다.
    """
    materialized = [
        line if line.endswith("\n") else line + "\n"
        for line in lines
    ]
    if not materialized:
        return 0

    target.parent.mkdir(parents=True, exist_ok=True)

    # PID로 staging 충돌 회피.
    staging = target.with_suffix(target.suffix + f".staging.{os.getpid()}")

    try:
        # 기존 target이 있으면 staging으로 복사.
        # 없으면 staging을 빈 파일로 시작.
        if target.exists():
            shutil.copyfile(target, staging)
        else:
            staging.touch()

        # staging에 새 줄들 append.
        with open(staging, "a", encoding="utf-8") as f:
            for line in materialized:
                f.write(line)
            f.flush()

        # atomic rename. Windows/Linux 모두 os.replace는 같은 파일시스템에서
        # 단일 inode 갱신으로 atomic을 보장한다.
        os.replace(staging, target)
        return len(materialized)
    except Exception:
        # 실패 시 staging만 정리. target은 호출 전 상태 그대로.
        if staging.exists():
            try:
                staging.unlink()
            except OSError:
                pass
        raise
