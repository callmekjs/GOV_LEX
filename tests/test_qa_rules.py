"""QA Rule Engine 테스트."""
import pytest
from datetime import date
from govlexops.schemas.legal_document import LegalDocument, make_content_hash
from govlexops.qa.rules import QARuleEngine


def _make_doc(source_id="test_doc", title="Test", content="hello", issued_date=date(2024, 1, 1)):
    """테스트용 문서를 간편하게 만드는 헬퍼."""
    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title=title,
        issued_date=issued_date,
        source_url="https://example.com",
        content_hash=make_content_hash(content),
    )


def test_r01_allows_unique():
    """R01: 서로 다른 문서는 통과."""
    engine = QARuleEngine()
    doc1 = _make_doc(source_id="doc1", content="본문A")
    doc2 = _make_doc(source_id="doc2", content="본문B")
    assert engine.validate(doc1) is True
    assert engine.validate(doc2) is True
    assert engine.get_summary()["R01"] == 0


def test_r01_blocks_duplicate():
    """R01: 같은 content_hash면 두 번째를 거부."""
    engine = QARuleEngine()
    doc1 = _make_doc(source_id="doc1", content="동일 본문")
    doc2 = _make_doc(source_id="doc2", content="동일 본문")  # 같은 내용
    assert engine.validate(doc1) is True
    assert engine.validate(doc2) is False
    assert engine.get_summary()["R01"] == 1


def test_r05_warns_date_conflict():
    """R05: 같은 제목 + 다른 날짜면 경고."""
    engine = QARuleEngine()
    doc1 = _make_doc(title="AI법", content="내용1", issued_date=date(2024, 3, 1))
    doc2 = _make_doc(title="AI법", content="내용2", issued_date=date(2024, 6, 1))
    engine.validate(doc1)
    engine.validate(doc2)
    assert engine.get_summary()["R05"] == 1


def test_summary_counts():
    """전체 요약이 정확한지."""
    engine = QARuleEngine()
    # 정상 1개
    engine.validate(_make_doc(source_id="ok", content="유니크"))
    # 중복 1개
    engine.validate(_make_doc(source_id="dup", content="유니크"))
    assert engine.get_summary() == {"R01": 1, "R02": 0, "R05": 0}


def test_failures_list():
    """실패 목록이 dict로 나오는지."""
    engine = QARuleEngine()
    engine.validate(_make_doc(source_id="a", content="same"))
    engine.validate(_make_doc(source_id="b", content="same"))
    failures = engine.get_failures()
    assert len(failures) == 1
    assert failures[0]["rule_id"] == "R01"
    assert failures[0]["source_id"] == "b"