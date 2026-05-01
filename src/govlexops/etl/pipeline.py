"""GovLex-Ops 파이프라인. Day 6: 다중 쿼리 수집 + 영구 중복 저장."""
import logging

from govlexops.core.event_log import log_event
from govlexops.core.logging import setup_logging
from govlexops.core.run_context import create_run_context
from govlexops.core.seen_store import count_seen
from govlexops.core.storage import count_documents, save_documents
from govlexops.etl.ingest.assembly_bills import fetch_assembly_bills
from govlexops.etl.ingest.kr_law import fetch_laws_bulk
from govlexops.etl.ingest.us_congress import fetch_bills
from govlexops.qa.report import generate_quality_report
from govlexops.qa.rules import QARuleEngine

log = logging.getLogger(__name__)


def run(us_query: str = "artificial intelligence") -> None:
    run_dir = create_run_context()
    # [pipline_upgrade 0-5] 매 run마다 콘솔 + run_dir/pipeline.log에 기록.
    setup_logging(run_dir=run_dir)

    log.info("✓ Run started: %s", run_dir)
    log_event(run_dir, "pipeline_started")

    # ── 영구 저장소 현황 ──
    log.info("📚 기존 수집 기억: %d건", count_seen())

    all_docs = []

    # ── 1. KR 수집 (여러 쿼리) ──
    try:
        kr_docs = fetch_laws_bulk(max_per_query=80)
        all_docs.extend(kr_docs)
        log_event(run_dir, "ingest_done", source="kr_law", count=len(kr_docs))
    except Exception as e:
        log.error("❌ KR 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="kr_law", error=str(e))

    # ── 2. US 수집 ──
    try:
        us_docs = fetch_bills(max_count=250)
        all_docs.extend(us_docs)
        log_event(run_dir, "ingest_done", source="us_congress", count=len(us_docs))
    except Exception as e:
        log.error("❌ US 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="us_congress", error=str(e))

    # ── 3. KR 국회 법률안 (열린국회정보 API) ──
    try:
        assembly_docs = fetch_assembly_bills()
        all_docs.extend(assembly_docs)
        log_event(run_dir, "ingest_done", source="kr_assembly", count=len(assembly_docs))
    except Exception as e:
        log.error("❌ 국회 의안 수집 실패: %s", e)
        log_event(run_dir, "ingest_failed", source="kr_assembly", error=str(e))

    log.info("총 수집 시도: %d건", len(all_docs))

    # ── 4. QA (영구 저장소 사용) ──
    engine = QARuleEngine(use_persistent_store=True)
    passed_docs = []

    for doc in all_docs:
        ok = engine.validate(doc)
        if ok:
            passed_docs.append(doc)
            log.info("✅ [%s] %s", doc.jurisdiction, doc.title[:45])
        else:
            log.warning("❌ [%s] %s", doc.jurisdiction, doc.title[:45])

    # ── 5. 저장 ──
    saved = save_documents(passed_docs)
    log_event(run_dir, "documents_saved", count=saved)
    log.info("💾 신규 저장: %d건", saved)

    # ── 5-1. 영구 중복 저장소에 일괄 기록 (0-1 fix) ──
    #   save_documents가 성공한 문서에 한해서만 mark_seen 처리.
    #   이렇게 해야 R02/R05에서 거부됐거나 저장 실패한 문서가
    #   영구 저장소에 잘못 박혀 다음 실행에서 영원히 거부되는
    #   데이터 손실 버그를 막을 수 있다.
    committed = engine.commit_seen_for_passed(passed_docs)
    log_event(run_dir, "seen_committed", count=committed)
    log.info("📌 영구 중복 기억에 추가: %d건", committed)

    # ── 6. 품질 리포트 ──
    report_path = generate_quality_report(
        run_dir=run_dir,
        engine=engine,
        total_input=len(all_docs),
        total_passed=len(passed_docs),
    )
    log_event(run_dir, "quality_report_generated", path=str(report_path))
    log.info("📋 품질 리포트: %s", report_path)

    # ── 7. 누적 통계 ──
    stats = count_documents()
    log.info(
        "📊 전체 누적: KR=%d / US=%d / 합계=%d",
        stats["KR"], stats["US"], stats["total"],
    )
    log.info("📚 중복 감지 기억: %d건", count_seen())

    log_event(run_dir, "pipeline_finished", status="ok", **stats)
    log.info("✓ Run finished: %s", run_dir)


if __name__ == "__main__":
    run()
