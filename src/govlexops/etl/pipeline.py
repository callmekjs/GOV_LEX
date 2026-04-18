"""GovLex-Ops 파이프라인. Day 3: QA 룰 + 품질 리포트 추가."""
from datetime import date
from govlexops.core.run_context import create_run_context
from govlexops.core.event_log import log_event
from govlexops.schemas.legal_document import LegalDocument, make_content_hash
from govlexops.qa.rules import QARuleEngine
from govlexops.qa.report import generate_quality_report


def run() -> None:
    run_dir = create_run_context()
    print(f"✓ Run started at: {run_dir}")
    log_event(run_dir, "pipeline_started")

    # ── 샘플 문서 5개 (정상 3 + 중복 1 + 날짜충돌 1) ──
    sample_docs = [
        # 1. 정상 KR
        LegalDocument(
            source_id="kr_assembly_20240717_foreign",
            jurisdiction="KR",
            source_type="minutes",
            language="ko",
            title="제22대 제416회 1차 외교통일위원회",
            issued_date=date(2024, 7, 17),
            source_url="https://likms.assembly.go.kr/record/example1",
            content_hash=make_content_hash("외교통일위 회의 내용 본문"),
            metadata={"committee": "외교통일위원회"},
        ),
        # 2. 정상 US
        LegalDocument(
            source_id="us_congress_118_hr4763",
            jurisdiction="US",
            source_type="bill",
            language="en",
            title="AI Accountability Act",
            issued_date=date(2024, 3, 15),
            source_url="https://congress.gov/bill/118/hr/4763",
            content_hash=make_content_hash("Section 1. Short title."),
            metadata={"congress": 118, "bill_type": "HR"},
        ),
        # 3. 정상 KR (다른 회의)
        LegalDocument(
            source_id="kr_assembly_20240320_defense",
            jurisdiction="KR",
            source_type="minutes",
            language="ko",
            title="제22대 제414회 2차 국방위원회",
            issued_date=date(2024, 3, 20),
            source_url="https://likms.assembly.go.kr/record/example2",
            content_hash=make_content_hash("국방위 회의 내용 본문"),
            metadata={"committee": "국방위원회"},
        ),
        # 4. 중복 (1번과 같은 content_hash) → R01에 걸려야 함
        LegalDocument(
            source_id="kr_assembly_20240717_foreign_dup",
            jurisdiction="KR",
            source_type="minutes",
            language="ko",
            title="제22대 제416회 1차 외교통일위원회 (복사본)",
            issued_date=date(2024, 7, 17),
            source_url="https://likms.assembly.go.kr/record/example1_dup",
            content_hash=make_content_hash("외교통일위 회의 내용 본문"),  # 1번과 동일
        ),
        # 5. 날짜 충돌 (2번과 같은 제목, 다른 날짜) → R05에 걸려야 함
        LegalDocument(
            source_id="us_congress_118_hr4763_v2",
            jurisdiction="US",
            source_type="bill",
            language="en",
            title="AI Accountability Act",  # 2번과 동일
            issued_date=date(2024, 6, 20),  # 날짜만 다름
            source_url="https://congress.gov/bill/118/hr/4763/v2",
            content_hash=make_content_hash("Section 1. Short title. (amended)"),
            metadata={"congress": 118, "bill_type": "HR"},
        ),
    ]

    # ── QA 실행 ──
    engine = QARuleEngine()
    passed_docs = []

    for doc in sample_docs:
        ok = engine.validate(doc)
        if ok:
            passed_docs.append(doc)
            log_event(run_dir, "document_passed", source_id=doc.source_id)
            print(f"  ✅ PASS: {doc.source_id}")
        else:
            log_event(run_dir, "document_failed", source_id=doc.source_id)
            print(f"  ❌ FAIL: {doc.source_id}")

    # ── 품질 리포트 생성 ──
    report_path = generate_quality_report(
        run_dir=run_dir,
        engine=engine,
        total_input=len(sample_docs),
        total_passed=len(passed_docs),
    )
    log_event(run_dir, "quality_report_generated", path=str(report_path))
    print(f"\n📋 Quality report: {report_path}")

    log_event(
        run_dir, "pipeline_finished",
        status="ok",
        total_input=len(sample_docs),
        total_passed=len(passed_docs),
        total_failed=len(sample_docs) - len(passed_docs),
    )
    print(f"✓ Run finished. {len(passed_docs)}/{len(sample_docs)} passed.")


if __name__ == "__main__":
    run()