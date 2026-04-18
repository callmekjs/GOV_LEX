"""
품질 리포트를 자동 생성하는 모듈.
실행할 때마다 runs/<run_id>/quality_report.md 파일이 만들어집니다.
"""
import json
from pathlib import Path
from datetime import datetime
from govlexops.qa.rules import QARuleEngine


def generate_quality_report(
    run_dir: Path,
    engine: QARuleEngine,
    total_input: int,
    total_passed: int,
) -> Path:
    """품질 리포트 md 파일을 생성하고 경로를 반환합니다."""

    summary = engine.get_summary()
    failures = engine.get_failures()
    report_path = run_dir / "quality_report.md"

    lines = []
    lines.append(f"# 품질 리포트 - {run_dir.name}")
    lines.append("")
    lines.append(f"생성 시각: {datetime.now().isoformat()}")
    lines.append("")

    # ── 수집 요약 ──
    lines.append("## 수집 요약")
    lines.append("")
    lines.append(f"- 입력 문서: **{total_input}건**")
    lines.append(f"- 중복 거부 (R01): **{summary['R01']}건**")
    lines.append(f"- 결측 격리 (R02): **{summary['R02']}건**")
    lines.append(f"- 날짜 충돌 경고 (R05): **{summary['R05']}건**")
    lines.append(f"- 최종 저장: **{total_passed}건**")
    lines.append("")

    # ── 통과율 ──
    if total_input > 0:
        pass_rate = (total_passed / total_input) * 100
        lines.append(f"- 통과율: **{pass_rate:.1f}%**")
    lines.append("")

    # ── 실패 상세 ──
    if failures:
        lines.append("## 실패 상세")
        lines.append("")
        for f in failures:
            lines.append(
                f"- **[{f['rule_id']}]** {f['source_id']}: "
                f"{f['observed']}"
            )
        lines.append("")
    else:
        lines.append("## 실패 상세")
        lines.append("")
        lines.append("실패 건 없음.")
        lines.append("")

    # 파일 쓰기
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # ── 이번 run 전용 실패 파일 ──
    failures_path = run_dir / "quality_failures.jsonl"
    with open(failures_path, "w", encoding="utf-8") as f:
        for failure in failures:
            f.write(json.dumps(failure, ensure_ascii=False) + "\n")

    # ── 전역 누적 실패 파일 (운영 대시보드용) ──
    _append_to_global_failure_log(run_dir=run_dir, failures=failures)

    return report_path


def _append_to_global_failure_log(run_dir: Path, failures: list[dict]) -> Path:
    """
    모든 실행의 품질 실패를 한 파일에 누적 기록합니다.
    경로: data_index/quality/failures.jsonl
    각 줄에 run_id와 written_at을 덧붙여 추적 가능하게 합니다.
    """
    global_dir = Path("data_index/quality")
    global_dir.mkdir(parents=True, exist_ok=True)
    global_path = global_dir / "failures.jsonl"

    run_id = run_dir.name
    written_at = datetime.now().isoformat()

    with open(global_path, "a", encoding="utf-8") as f:
        for failure in failures:
            record = {
                **failure,
                "run_id": run_id,
                "written_at": written_at,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return global_path