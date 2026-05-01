"""runs/*/metrics.json을 집계해 docs/dashboard.md를 생성한다."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path


RUNS_DIR = Path("runs")
OUTPUT_PATH = Path("docs/dashboard.md")


def _load_metrics() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(RUNS_DIR.glob("run_*/metrics.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        payload["_path"] = str(path)
        rows.append(payload)
    rows.sort(key=lambda x: x.get("started_at", ""))
    return rows


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _within_30_days(row: dict, now: datetime) -> bool:
    started = row.get("started_at")
    if not isinstance(started, str):
        return False
    try:
        dt = datetime.fromisoformat(started)
    except ValueError:
        return False
    return dt >= now - timedelta(days=30)


def build_dashboard() -> Path:
    now = datetime.now()
    rows = _load_metrics()
    recent = [r for r in rows if _within_30_days(r, now)]

    total_runs = len(rows)
    recent_runs = len(recent)
    recent_ingested = sum(_to_int(r.get("ingested")) for r in recent)
    recent_passed = sum(_to_int(r.get("passed")) for r in recent)
    recent_pass_rate = recent_passed / max(recent_ingested, 1)
    avg_duration = (
        sum(_to_float(r.get("duration_seconds")) for r in recent) / max(recent_runs, 1)
    )

    lines: list[str] = [
        "# GovLex 운영 대시보드",
        "",
        f"- 생성 시각: `{now.strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- 전체 집계 run 수: `{total_runs}`",
        f"- 최근 30일 run 수: `{recent_runs}`",
        "",
        "## 최근 30일 요약",
        "",
        f"- 수집 건수 합계: `{recent_ingested}`",
        f"- 통과 건수 합계: `{recent_passed}`",
        f"- 통과율: `{recent_pass_rate:.2%}`",
        f"- 평균 실행 시간: `{avg_duration:.2f}s`",
        "",
        "## 최근 run (최신 20개)",
        "",
        "| run_id | started_at | ingested | passed | pass_rate | duration_s | R01 | R02 | R07 | R05 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in rows[-20:][::-1]:
        rejected = row.get("rejected") or {}
        lines.append(
            "| {run_id} | {started_at} | {ingested} | {passed} | {pass_rate} | {duration} | {r01} | {r02} | {r07} | {r05} |".format(
                run_id=row.get("run_id", "-"),
                started_at=row.get("started_at", "-"),
                ingested=_to_int(row.get("ingested")),
                passed=_to_int(row.get("passed")),
                pass_rate=f"{_to_float(row.get('pass_rate')):.2%}",
                duration=f"{_to_float(row.get('duration_seconds')):.2f}",
                r01=_to_int(rejected.get("R01")),
                r02=_to_int(rejected.get("R02")),
                r07=_to_int(rejected.get("R07")),
                r05=_to_int(rejected.get("R05")),
            )
        )

    lines.extend(
        [
            "",
            "## 메모",
            "",
            "- 이 문서는 `python scripts/build_dashboard.py` 실행 시 자동 갱신됩니다.",
            "- 데이터 소스: `runs/run_*/metrics.json`",
        ]
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return OUTPUT_PATH


if __name__ == "__main__":
    out = build_dashboard()
    print(f"dashboard generated: {out}")
