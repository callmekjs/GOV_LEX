"""GovLex-Ops 파이프라인. Day 4: 진짜 데이터 연결."""
from govlexops.core.run_context import create_run_context
from govlexops.core.event_log import log_event
from govlexops.core.storage import save_documents, count_documents
from govlexops.qa.rules import QARuleEngine
from govlexops.qa.report import generate_quality_report
from govlexops.etl.ingest.kr_law import fetch_laws
from govlexops.etl.ingest.us_congress import fetch_bills


def run(kr_query: str = "인공지능", us_query: str = "artificial intelligence") -> None:
    run_dir = create_run_context()
    print(f"✓ Run started: {run_dir}")
    log_event(run_dir, "pipeline_started")

    # ── 1. 수집 ──
    all_docs = []

    try:
        kr_docs = fetch_laws(query=kr_query, max_count=10)
        all_docs.extend(kr_docs)
        log_event(run_dir, "ingest_done", source="kr_law", count=len(kr_docs))
    except Exception as e:
        print(f"  ❌ KR 수집 실패: {e}")
        log_event(run_dir, "ingest_failed", source="kr_law", error=str(e))

    try:
        us_docs = fetch_bills(query=us_query, max_count=10)
        all_docs.extend(us_docs)
        log_event(run_dir, "ingest_done", source="us_congress", count=len(us_docs))
    except Exception as e:
        print(f"  ❌ US 수집 실패: {e}")
        log_event(run_dir, "ingest_failed", source="us_congress", error=str(e))

    print(f"\n  총 수집: {len(all_docs)}건 (KR + US)")

    # ── 2. QA ──
    engine = QARuleEngine()
    passed_docs = []

    for doc in all_docs:
        ok = engine.validate(doc)
        if ok:
            passed_docs.append(doc)
            print(f"  ✅ PASS [{doc.jurisdiction}]: {doc.title[:40]}")
        else:
            print(f"  ❌ FAIL [{doc.jurisdiction}]: {doc.title[:40]}")

    # ── 3. 저장 ──
    saved = save_documents(passed_docs)
    log_event(run_dir, "documents_saved", count=saved)
    print(f"\n  💾 저장 완료: {saved}건 → data_index/normalized/docs.jsonl")

    # ── 4. 품질 리포트 ──
    report_path = generate_quality_report(
        run_dir=run_dir,
        engine=engine,
        total_input=len(all_docs),
        total_passed=len(passed_docs),
    )
    print(f"  📋 품질 리포트: {report_path}")

    # ── 5. 현재까지 누적 통계 ──
    stats = count_documents()
    print(f"\n📊 전체 누적: KR {stats['KR']}건 / US {stats['US']}건 / 합계 {stats['total']}건")

    log_event(run_dir, "pipeline_finished", status="ok", **stats)
    print(f"\n✓ Run finished: {run_dir}")


if __name__ == "__main__":
    run()