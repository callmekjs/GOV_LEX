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

def test_hash_ignores_whitespace_differences():
    """공백/줄바꿈이 달라도 같은 해시가 나와야 한다."""
    a = "안녕  세상"
    b = "안녕\n세상"
    c = " 안녕 세상 "
    assert make_content_hash(a) == make_content_hash(b) == make_content_hash(c)
def test_hash_ignores_unicode_form_differences():
    """같은 한글인데 조합형/완성형 차이여도 같은 해시가 나와야 한다."""
    composed = "가"                       # NFC 완성형
    decomposed = "\u1100\u1161"           # NFD 자모 분리 (ㄱ + ㅏ)
    assert make_content_hash(composed) == make_content_hash(decomposed)
def test_hash_differs_for_different_content():
    """내용 자체가 다르면 해시도 달라야 한다."""
    assert make_content_hash("서울") != make_content_hash("부산")

def test_r02_blocks_empty_source_id():
    """R02: source_id가 비어 있으면 실패."""
    doc = LegalDocument(
        source_id="",                 # 결측
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="제목 있음",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash=make_content_hash("내용"),
    )
    engine = QARuleEngine()
    assert engine.validate(doc) is False
    assert engine.get_summary()["R02"] == 1


def test_r02_blocks_empty_content_hash():
    """R02: content_hash가 비어 있으면 실패."""
    doc = LegalDocument(
        source_id="doc1",
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="제목 있음",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash="",              # 결측
    )
    engine = QARuleEngine()
    assert engine.validate(doc) is False
    assert engine.get_summary()["R02"] == 1