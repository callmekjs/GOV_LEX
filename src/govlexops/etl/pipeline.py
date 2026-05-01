"""GovLex-Ops 파이프라인. Day 6: 다중 쿼리 수집 + 영구 중복 저장."""

import argparse
import json
import logging
import time
from datetime import date, datetime
from pathlib import Path

from govlexops.core.config import load_pipeline_config
from govlexops.core.event_log import log_event
from govlexops.core.logging import setup_logging
from govlexops.core.run_context import create_run_context
from govlexops.core.seen_store import count_seen
from govlexops.etl.extract import write_extracted_graph
from govlexops.etl.ingest.assembly_bills import fetch_assembly_bills
from govlexops.etl.ingest.kr_decree import fetch_decrees_bulk
from govlexops.etl.ingest.kr_law import fetch_laws_bulk
from govlexops.etl.ingest.us_congress import fetch_bills
from govlexops.integrations.store.factory import create_document_store
from govlexops.qa.report import generate_quality_report
from govlexops.qa.rules import QARuleEngine

log = logging.getLogger(__name__)


def _log_catalog_warnings() -> None:
    patterns_path = Path("docs/failure_patterns.md")
    if not patterns_path.exists():
        return
    text = patterns_path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.strip().startswith("| R") and "|" in line:
            # Rule frequency 표를 간단 경고로 표시
            log.info("[CATALOG] %s", line)


def _ensure_data_layout() -> None:
    """ETL 5단계 + 품질 디렉터리를 보장한다."""
    for path in (
        "data_index/raw",
        "data_index/normalized",
        "data_index/extracted",
        "data_index/chunks",
        "data_index/embeddings",
        "data_index/quality",
    ):
        Path(path).mkdir(parents=True, exist_ok=True)


def _write_metrics(
    run_dir,
    *,
    started_at: datetime,
    started_monotonic: float,
    all_docs_count: int,
    passed_count: int,
    saved_count: int,
    committed_count: int,
    qa_summary: dict,
    by_source: dict,
) -> dict:
    """실행 메트릭을 runs/<run_id>/metrics.json으로 저장하고 payload를 반환한다."""
    metrics = {
        "run_id": run_dir.name,
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "duration_seconds": round(time.perf_counter() - started_monotonic, 3),
        "ingested": all_docs_count,
        "passed": passed_count,
        "saved": saved_count,
        "committed_seen": committed_count,
        "rejected": qa_summary,
        "by_source": by_source,
        "pass_rate": round(passed_count / max(all_docs_count, 1), 4),
    }
    metrics_path = run_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return metrics


def run(config_path: str = "configs/pipeline.yaml") -> None:
    started_at = datetime.now()
    started_monotonic = time.perf_counter()
    run_dir = create_run_context()
    # [pipline_upgrade 0-5] 매 run마다 콘솔 + run_dir/pipeline.log에 기록.
    setup_logging(run_dir=run_dir)

    log.info("✓ Run started: %s", run_dir)
    log_event(run_dir, "pipeline_started")
    _ensure_data_layout()
    _log_catalog_warnings()

    cfg = load_pipeline_config(config_path)
    log.info("🧩 Loaded config: %s", config_path)
    store = create_document_store(
        cfg.store_backend,
        sqlite_path=cfg.sqlite_path,
    )
    log.info("🗄️ Store backend: %s", cfg.store_backend)

    # ── 영구 저장소 현황 ──
    log.info("📚 기존 수집 기억: %d건", count_seen())

    all_docs = []
    kr_docs = []
    kr_decree_docs = []
    us_docs = []
    assembly_docs = []

    # ── 1. KR 수집 (여러 쿼리) ──
    try:
        kr_docs = fetch_laws_bulk(
            queries=cfg.kr_law.queries,
            max_per_query=cfg.kr_law.max_per_query,
            issued_since_year=date.today().year + cfg.kr_law.issued_since_year_offset,
            save_raw=True,
        )
        all_docs.extend(kr_docs)
        log_event(run_dir, "ingest_done", source="kr_law", count=len(kr_docs))
    except Exception as e:
        log.error("❌ KR 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="kr_law", error=str(e))

    # ── 2. KR 하위법령 수집 (decree) ──
    try:
        kr_decree_docs = fetch_decrees_bulk(
            queries=cfg.kr_decree.queries,
            max_per_query=cfg.kr_decree.max_per_query,
            issued_since_year=date.today().year
            + cfg.kr_decree.issued_since_year_offset,
            target=cfg.kr_decree.target,
            save_raw=True,
        )
        all_docs.extend(kr_decree_docs)
        log_event(
            run_dir,
            "ingest_done",
            source="kr_decree",
            count=len(kr_decree_docs),
        )
    except Exception as e:
        log.error("❌ KR decree 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="kr_decree", error=str(e))

    # ── 3. US 수집 ──
    try:
        us_docs = fetch_bills(
            max_count=cfg.us_congress.max_count,
            congress=cfg.us_congress.congress,
            min_intro_year=date.today().year + cfg.us_congress.min_intro_year_offset,
            save_raw=True,
        )
        all_docs.extend(us_docs)
        log_event(run_dir, "ingest_done", source="us_congress", count=len(us_docs))
    except Exception as e:
        log.error("❌ US 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="us_congress", error=str(e))

    # ── 4. KR 국회 법률안 (열린국회정보 API) ──
    try:
        current_year = date.today().year
        start_year = current_year + cfg.kr_assembly.start_year_offset
        end_year = current_year + cfg.kr_assembly.end_year_offset
        assembly_docs = fetch_assembly_bills(
            test_limit=cfg.kr_assembly.test_limit,
            assemblies=cfg.kr_assembly.assemblies,
            page_size=cfg.kr_assembly.page_size,
            start_date=f"{start_year}-01-01",
            end_date=f"{end_year}-12-31",
            save_raw=True,
        )
        all_docs.extend(assembly_docs)
        log_event(
            run_dir, "ingest_done", source="kr_assembly", count=len(assembly_docs)
        )
    except Exception as e:
        log.error("❌ 국회 의안 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="kr_assembly", error=str(e))

    log.info("총 수집 시도: %d건", len(all_docs))

    # ── 5. QA (영구 저장소 사용) ──
    engine = QARuleEngine(use_persistent_store=True)
    passed_docs = []

    for doc in all_docs:
        ok = engine.validate(doc)
        if ok:
            passed_docs.append(doc)
            log.info("✅ [%s] %s", doc.jurisdiction, doc.title[:45])
        else:
            log.warning("❌ [%s] %s", doc.jurisdiction, doc.title[:45])

    # ── 6. 저장 ──
    saved = store.append(passed_docs)
    log_event(run_dir, "documents_saved", count=saved)
    log.info("💾 신규 저장: %d건", saved)

    # ── 6-1. 영구 중복 저장소에 일괄 기록 (0-1 fix) ──
    #   save_documents가 성공한 문서에 한해서만 mark_seen 처리.
    #   이렇게 해야 R02/R05에서 거부됐거나 저장 실패한 문서가
    #   영구 저장소에 잘못 박혀 다음 실행에서 영원히 거부되는
    #   데이터 손실 버그를 막을 수 있다.
    committed = engine.commit_seen_for_passed(passed_docs)
    log_event(run_dir, "seen_committed", count=committed)
    log.info("📌 영구 중복 기억에 추가: %d건", committed)

    # ── 7. entities/relations 추출 (Phase 3-3) ──
    entities_written, relations_written = write_extracted_graph(passed_docs)
    log_event(
        run_dir,
        "extract_done",
        entities=entities_written,
        relations=relations_written,
    )
    log.info(
        "🕸️ extracted graph: entities=%d, relations=%d",
        entities_written,
        relations_written,
    )

    # ── 8. 품질 리포트 ──
    report_path = generate_quality_report(
        run_dir=run_dir,
        engine=engine,
        total_input=len(all_docs),
        total_passed=len(passed_docs),
    )
    log_event(run_dir, "quality_report_generated", path=str(report_path))
    log.info("📋 품질 리포트: %s", report_path)

    # ── 9. 누적 통계 ──
    stats = store.count()
    log.info(
        "📊 전체 누적: KR=%d / US=%d / 합계=%d",
        stats["KR"],
        stats["US"],
        stats["total"],
    )
    log.info("📚 중복 감지 기억: %d건", count_seen())

    # ── 10. 실행 메트릭 저장 (Phase 1-3) ──
    qa_summary = engine.get_summary()
    metrics = _write_metrics(
        run_dir,
        started_at=started_at,
        started_monotonic=started_monotonic,
        all_docs_count=len(all_docs),
        passed_count=len(passed_docs),
        saved_count=saved,
        committed_count=committed,
        qa_summary=qa_summary,
        by_source={
            "kr_law": len(kr_docs),
            "kr_decree": len(kr_decree_docs),
            "us_congress": len(us_docs),
            "kr_assembly": len(assembly_docs),
        },
    )
    metrics_path = run_dir / "metrics.json"
    log_event(
        run_dir,
        "metrics_written",
        path=str(metrics_path),
        pass_rate=metrics["pass_rate"],
    )
    log.info("📈 실행 메트릭: %s", metrics_path)

    log_event(run_dir, "pipeline_finished", status="ok", **stats)
    log.info("✓ Run finished: %s", run_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run GovLex ETL pipeline")
    parser.add_argument(
        "--config",
        default="configs/pipeline.yaml",
        help="YAML config path (e.g. configs/dev.yaml, configs/prod.yaml)",
    )
    args = parser.parse_args()
    run(config_path=args.config)
