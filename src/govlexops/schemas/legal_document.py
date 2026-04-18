"""
GovLex-Ops 표준 데이터 양식 (Canonical Schema).
모든 문서는 이 양식을 통과해야 저장됩니다.
"""
from datetime import datetime, date
from typing import Any
from pydantic import BaseModel, Field
import hashlib
import re
import unicodedata


class LegalDocument(BaseModel):
    """2개국 법·입법 문서의 공통 양식 (9개 필수 필드 + metadata)"""

    # 1. 문서 고유 ID
    source_id: str = Field(
        ...,
        description="문서를 유일하게 구별하는 ID",
        examples=["kr_assembly_20240717_foreign", "us_congress_118_hr4763"],
    )

    # 2. 어느 나라
    jurisdiction: str = Field(
        ...,
        description="국가 코드",
        pattern="^(KR|US)$",
    )

    # 3. 문서 종류
    source_type: str = Field(
        ...,
        description="문서 유형",
        examples=["minutes", "bill", "law"],
    )

    # 4. 언어
    language: str = Field(
        ...,
        description="문서 언어",
        pattern="^(ko|en)$",
    )

    # 5. 제목
    title: str = Field(
        ...,
        min_length=1,
        description="문서 제목",
    )

    # 6. 발행일
    issued_date: date = Field(
        ...,
        description="문서 발행일 (YYYY-MM-DD)",
    )

    # 7. 원문 링크
    source_url: str = Field(
        ...,
        min_length=1,
        description="원문 접근 URL",
    )

    # 8. 본문 지문 (중복 감지용)
    content_hash: str = Field(
        ...,
        description="본문 기반 SHA-256 해시",
    )

    # 9. 수집 시각
    ingested_at: datetime = Field(
        default_factory=datetime.now,
        description="이 문서를 수집한 시각",
    )

    # 국가별 추가 정보 (자유 형식)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="국가별 보조 정보 (위원회명, bill_type, sponsor 등)",
    )


def _normalize_text(text: str) -> str:
    """해시 계산 전, 텍스트를 표준 형태로 청소합니다."""
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def make_content_hash(text: str) -> str:
    """본문 텍스트를 정규화한 뒤 SHA-256 해시를 만듭니다."""
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()