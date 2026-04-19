"""GovLex-Ops 파이프라인. Day 6: 다중 쿼리 수집 + 영구 중복 저장."""
from govlexops.core.run_context import create_run_context
from govlexops.core.event_log import log_event
from govlexops.core.storage import save_documents, count_documents
from govlexops.core.seen_store import count_seen
from govlexops.qa.rules import QARuleEngine
from govlexops.qa.report import generate_quality_report
from govlexops.etl.ingest.kr_law import fetch_laws_bulk
from govlexops.etl.ingest.us_congress import fetch_bills


def run(us_query: str = "artificial intelligence") -> None:
    run_dir = create_run_context()
    print(f"✓ Run started: {run_dir}")
    log_event(run_dir, "pipeline_started")

    # ── 영구 저장소 현황 ──
    print(f"  📚 기존 수집 기억: {count_seen()}건")

    all_docs = []

    # ── 1. KR 수집 (여러 쿼리) ──
    try:
        kr_docs = fetch_laws_bulk(max_per_query=10)
        all_docs.extend(kr_docs)
        log_event(run_dir, "ingest_done", source="kr_law", count=len(kr_docs))
    except Exception as e:
        print(f"  ❌ KR 수집 실패: {e}")
        log_event(run_dir, "ingest_failed", source="kr_law", error=str(e))

    # ── 2. US 수집 ──
    try:
        us_docs = fetch_bills(query="artificial intelligence regulation", max_count=10)
        all_docs.extend(us_docs)
        log_event(run_dir, "ingest_done", source="us_congress", count=len(us_docs))
    except Exception as e:
        print(f"  ❌ US 수집 실패: {e}")
        log_event(run_dir, "ingest_failed", source="us_congress", error=str(e))

    print(f"\n  총 수집 시도: {len(all_docs)}건")

    # ── 3. QA (영구 저장소 사용) ──
    engine = QARuleEngine(use_persistent_store=True)
    passed_docs = []

    for doc in all_docs:
        ok = engine.validate(doc)
        if ok:
            passed_docs.append(doc)
            print(f"  ✅ [{doc.jurisdiction}] {doc.title[:45]}")
        else:
            print(f"  ❌ [{doc.jurisdiction}] {doc.title[:45]}")

    # ── 4. 저장 ──
    saved = save_documents(passed_docs)
    log_event(run_dir, "documents_saved", count=saved)
    print(f"\n  💾 신규 저장: {saved}건")

    # ── 5. 품질 리포트 ──
    report_path = generate_quality_report(
        run_dir=run_dir,
        engine=engine,
        total_input=len(all_docs),
        total_passed=len(passed_docs),
    )
    log_event(run_dir, "quality_report_generated", path=str(report_path))
    print(f"  📋 품질 리포트: {report_path}")

    # ── 6. 누적 통계 ──
    stats = count_documents()
    print(f"\n📊 전체 누적: KR {stats['KR']}건 / US {stats['US']}건 / 합계 {stats['total']}건")
    print(f"📚 중복 감지 기억: {count_seen()}건")

    log_event(run_dir, "pipeline_finished", status="ok", **stats)
    print(f"\n✓ Run finished: {run_dir}")


if __name__ == "__main__":
    run()