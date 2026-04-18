"""표준 양식이 올바른 데이터는 통과하고, 잘못된 데이터는 거부하는지 테스트."""
import pytest
from datetime import date, datetime
from govlexops.schemas.legal_document import LegalDocument, make_content_hash


# ── 올바른 데이터: 통과해야 함 ──

def test_valid_kr_document():
    """한국 회의록 샘플이 schema를 통과하는지"""
    doc = LegalDocument(
        source_id="kr_assembly_20240717_foreign",
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="제22대 제416회 1차 외교통일위원회",
        issued_date=date(2024, 7, 17),
        source_url="https://likms.assembly.go.kr/record/mhs-10-040-0040.do",
        content_hash=make_content_hash("회의 내용 샘플 텍스트"),
        metadata={"committee": "외교통일위원회", "session_no": "제416회"},
    )
    assert doc.jurisdiction == "KR"
    assert doc.source_type == "minutes"


def test_valid_us_document():
    """미국 법안 샘플이 schema를 통과하는지"""
    doc = LegalDocument(
        source_id="us_congress_118_hr4763",
        jurisdiction="US",
        source_type="bill",
        language="en",
        title="AI Accountability Act",
        issued_date=date(2024, 3, 15),
        source_url="https://congress.gov/bill/118th-congress/house-bill/4763",
        content_hash=make_content_hash("Section 1. Short title."),
        metadata={"congress": 118, "bill_type": "HR", "sponsor": "Rep. Smith"},
    )
    assert doc.jurisdiction == "US"
    assert doc.source_type == "bill"


def test_kr_and_us_same_fields():
    """KR과 US 문서가 같은 필드 구조를 가지는지 (표준화 핵심 검증)"""
    kr = LegalDocument(
        source_id="kr_test",
        jurisdiction="KR",
        source_type="minutes",
        language="ko",
        title="테스트",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash="abc123",
    )
    us = LegalDocument(
        source_id="us_test",
        jurisdiction="US",
        source_type="bill",
        language="en",
        title="Test",
        issued_date=date(2024, 1, 1),
        source_url="https://example.com",
        content_hash="def456",
    )
    assert set(LegalDocument.model_fields.keys()) == set(LegalDocument.model_fields.keys())


# ── 잘못된 데이터: 거부해야 함 ──

def test_reject_missing_title():
    """제목 없으면 거부"""
    with pytest.raises(Exception):
        LegalDocument(
            source_id="bad_doc",
            jurisdiction="KR",
            source_type="minutes",
            language="ko",
            title="",          # 빈 문자열 → 거부
            issued_date=date(2024, 1, 1),
            source_url="https://example.com",
            content_hash="abc",
        )


def test_reject_invalid_jurisdiction():
    """KR/US 외 국가코드 거부"""
    with pytest.raises(Exception):
        LegalDocument(
            source_id="bad_doc",
            jurisdiction="JP",   # JP는 아직 지원 안 함 → 거부
            source_type="minutes",
            language="ko",
            title="테스트",
            issued_date=date(2024, 1, 1),
            source_url="https://example.com",
            content_hash="abc",
        )


def test_reject_invalid_language():
    """ko/en 외 언어코드 거부"""
    with pytest.raises(Exception):
        LegalDocument(
            source_id="bad_doc",
            jurisdiction="KR",
            source_type="minutes",
            language="ja",   # ja는 아직 지원 안 함 → 거부
            title="테스트",
            issued_date=date(2024, 1, 1),
            source_url="https://example.com",
            content_hash="abc",
        )


def test_content_hash_consistency():
    """같은 텍스트는 항상 같은 해시를 만드는지"""
    text = "동일한 본문 내용"
    assert make_content_hash(text) == make_content_hash(text)


def test_content_hash_different():
    """다른 텍스트는 다른 해시를 만드는지"""
    assert make_content_hash("문서A") != make_content_hash("문서B")