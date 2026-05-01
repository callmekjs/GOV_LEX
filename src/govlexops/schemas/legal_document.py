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
    """2개국 법·입법 문서의 공통 양식 (9개 필수 필드 + metadata).

    content_hash 정책 (v1.x):
      이 필드는 '본문 텍스트' 해시가 아니라 '정규화된 식별 메타데이터' 해시이다.
      각 수집기는 다음 형식의 문자열을 make_content_hash()의 입력으로 넘긴다:
        - KR 법령 (law):  f"{title}_{공포일자YYYYMMDD}"
        - KR 법안 (bill): f"{title}_{PPSL_DT_digits}_{BILL_NO}"
        - US 법안 (bill): f"{title}_{introducedDate}_{bill_number}"

      본문 해시가 아닌 이유:
        1) 공개 API가 본문(full text)을 일관되게 제공하지 않는다.
        2) 본문 적재 부담(법안 1건당 수십~수백 KB)이 MVP 일정에 맞지 않는다.
        3) 본문 변경 감지는 R05(제목 동일·날짜 다름) 룰로 부분 보완한다.

      한계: 같은 (title, date)면 본문이 바뀌어도 같은 해시 → 변경 추적 불가.
      승격 계획: Phase 2-2에서 source_type별 본문 기반 해시로 분리(schema v2).

      상세 정의·한계·승격 계획: docs/schema_v1.md §6.
    """

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

    # 8. 식별 메타데이터 해시 (중복 감지용)
    content_hash: str = Field(
        ...,
        description=(
            "정규화된 식별 메타데이터(제목·발행일·소스 식별자)의 SHA-256 해시. "
            "본문 해시 아님. 정의·한계·승격계획은 docs/schema_v1.md §6 참고."
        ),
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
    """정규화된 텍스트를 SHA-256으로 해시한다.

    정규화: NFC 통일 → 연속 공백을 단일 공백으로 → 앞뒤 공백 제거.

    호출자 약속(LegalDocument 정책):
      각 수집기의 _convert_to_document는 '본문' 대신
      '제목·발행일·소스 식별자'를 구분자(_)로 결합한 문자열을 넘긴다.
      따라서 이 함수의 결과는 '본문 해시'가 아니라
      '정규화된 식별 메타데이터 해시'이다.

    상세: docs/schema_v1.md §6.
    """
    normalized = _normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
