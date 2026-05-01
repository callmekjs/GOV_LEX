"""Replay utilities for re-validating past runs."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from govlexops.core.storage import load_documents
from govlexops.qa.report import generate_quality_report
from govlexops.qa.rules import QARuleEngine
from govlexops.schemas.legal_document import LegalDocument


def _read_failure_source_ids(run_dir: Path) -> set[str]:
    failures_path = run_dir / "quality_failures.jsonl"
    if not failures_path.exists():
        return set()

    source_ids: set[str] = set()
    for line in failures_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        source_id = str(row.get("source_id", "")).strip()
        if source_id:
            source_ids.add(source_id)
    return source_ids


def replay_run(
    run_path: str,
    *,
    only_failures: bool = False,
    regenerate_report: bool = False,
) -> Path:
    """과거 run 경로 기준으로 문서를 다시 QA 검증한다.

    현재 구현은 저장된 normalized 문서에서 재검증한다.
    (source별 재수집은 Phase 2-2 확장 범위)
    """
    run_dir = Path(run_path)
    if not run_dir.exists():
        raise FileNotFoundError(f"Run path not found: {run_dir}")

    docs = load_documents()
    mode = "all"

    if only_failures:
        mode = "only_failures"
        source_ids = _read_failure_source_ids(run_dir)
        docs = [d for d in docs if d.get("source_id") in source_ids]

    engine = QARuleEngine(use_persistent_store=False)
    total_input = 0
    total_passed = 0

    for row in docs:
        try:
            doc = LegalDocument.model_validate(row)
        except Exception:
            # 스키마 파싱 자체가 불가능한 문서는 replay 대상에서 제외.
            continue
        total_input += 1
        if engine.validate(doc):
            total_passed += 1

    summary = engine.get_summary()
    report_path = run_dir / "replay_report.md"
    lines = [
        f"# Replay Report - {run_dir.name}",
        "",
        f"- 생성 시각: `{datetime.now().isoformat(timespec='seconds')}`",
        f"- 모드: `{mode}`",
        f"- replay 입력 문서: `{total_input}`",
        f"- replay 통과 문서: `{total_passed}`",
        f"- replay 통과율: `{(total_passed / max(total_input, 1)):.2%}`",
        "",
        "## Rule Summary",
        "",
        f"- R01: `{summary.get('R01', 0)}`",
        f"- R02: `{summary.get('R02', 0)}`",
        f"- R07: `{summary.get('R07', 0)}`",
        f"- R05: `{summary.get('R05', 0)}`",
        "",
    ]
    report_path.write_text("\n".join(lines), encoding="utf-8")

    if regenerate_report:
        replay_dir = run_dir / "replay_latest"
        replay_dir.mkdir(parents=True, exist_ok=True)
        generate_quality_report(
            run_dir=replay_dir,
            engine=engine,
            total_input=total_input,
            total_passed=total_passed,
        )

    return report_path
