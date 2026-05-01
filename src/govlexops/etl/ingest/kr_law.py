"""
한국 국가법령정보 Open API 수집기.
법제처 API에서 법령 데이터를 가져와 LegalDocument로 변환합니다.
"""
import logging
import os
from datetime import date

from dotenv import load_dotenv

from govlexops.core.http import get_json
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

load_dotenv()
log = logging.getLogger(__name__)

BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"

# 올해 기준 -3년 이후 공포분만 유지 (검색 결과에 대한 연도 필터)
_ISSUED_SINCE_YEAR = date.today().year - 3

# [pipline_upgrade 0-4] 발행일 파싱 실패 시 명시적 sentinel.
# 1948 미만이라 QA의 R07이 자동 격리한다.
_DATE_PARSE_FAILED_SENTINEL = date(1900, 1, 1)


def _issued_in_window(doc: LegalDocument) -> bool:
    """연도 정책 필터. 단, 파싱 실패 표지가 있는 문서는 통과시켜
    QA의 R07이 명시적으로 격리하도록 한다 (silently 사라지지 않게)."""
    if doc.metadata.get("date_parse_failed") is True:
        return True
    return doc.issued_date.year >= _ISSUED_SINCE_YEAR


def fetch_laws(query: str = "인공지능", max_count: int = 10) -> list[LegalDocument]:
    """
    법령 검색 API를 호출해서 LegalDocument 목록을 반환합니다.
    """
    oc = os.getenv("LAW_GO_KR_OC")
    if not oc:
        raise ValueError(".env에 LAW_GO_KR_OC가 없습니다.")

    params = {
        "OC": oc,
        "target": "law",
        "type": "JSON",
        "query": query,
        "display": max_count,
    }

    log.info("→ KR law API request: query=%s max_count=%d", query, max_count)
    # [pipline_upgrade 0-3] 공통 HTTP 클라이언트 사용:
    #   timeout 30s + 재시도 3회 + 429/5xx 자동 처리.
    data = get_json(BASE_URL, params=params, timeout=30)

    # 결과 파싱
    raw_laws = data.get("LawSearch", {}).get("law", [])

    # 결과가 딕셔너리 1개(단건)일 수도 있음 → 리스트로 통일
    if isinstance(raw_laws, dict):
        raw_laws = [raw_laws]

    docs = []
    for law in raw_laws:
        try:
            doc = _convert_to_document(law)
            docs.append(doc)
        except Exception as e:
            log.warning(
                "⚠️ KR law convert failed: title=%s err=%s",
                law.get("법령명한글", "?"), e,
            )

    log.info("✅ KR law converted: %d docs (query=%s)", len(docs), query)
    return docs

def fetch_laws_bulk(
    queries: list[str] | None = None,
    max_per_query: int = 80,
) -> list[LegalDocument]:
    """
    여러 쿼리로 법령을 수집하고 중복을 제거해서 반환합니다.
    """
    # ── 수집 상한 정책 ──────────────────────────────────────────────
    # max_per_query: 쿼리당 법령 조회 건수 상한.
    #
    # 근거:
    #   - 국가법령정보 API 일일 호출 한도: 10,000건 (개발계정)
    #   - 현재 쿼리 수: 5개 (인공지능·데이터·개인정보·정보통신·디지털)
    #   - 5 쿼리 × 80건 = 400건 (일일 한도의 4%)
    #   - API 페이지 상한: 100건/호출, 80건은 안정적 마진
    #
    # 조정 지침:
    #   - 빠른 검증용: max_per_query=10
    #   - 일일 배치용: max_per_query=80 (기본값)
    #   - 최대 수집:   max_per_query=100 (API 상한)
    if queries is None:
        queries = [
            "인공지능",
            "데이터",
            "개인정보",
            "정보통신",
            "규제",
            "디지털",
            "클라우드",
            "사이버",
            "네트워크",
            "전자정부",
            "플랫폼",
            "알고리즘",
            "자동화",
            "반도체",
            "소프트웨어",
            "온라인",
            "전자문서",
            "전자서명",
            "블록체인",
            "메타버스",
            "빅데이터",
            "오픈데이터",
            "정보보호",
            "정보유출",
            "해킹",
            "스팸",
            "전기통신",
            "방송",
            "저작권",
            "특허",
            "표준",
            "산업안전",
            "소비자",
            "금융",
            "핀테크",
            "전자상거래",
        ]

    all_docs = []
    seen_ids = set()

    for query in queries:
        try:
            docs = fetch_laws(query=query, max_count=max_per_query)
            for doc in docs:
                if doc.source_id not in seen_ids:
                    seen_ids.add(doc.source_id)
                    all_docs.append(doc)
        except Exception as e:
            log.warning("⚠️ KR law query failed: query=%s err=%s", query, e)

    before = len(all_docs)
    all_docs = [d for d in all_docs if _issued_in_window(d)]
    log.info(
        "✅ KR law year filter (>=%d): %d docs (before filter: %d)",
        _ISSUED_SINCE_YEAR, len(all_docs), before,
    )
    return all_docs


def _convert_to_document(law: dict) -> LegalDocument:
    """법령 API 응답 1건을 LegalDocument로 변환합니다."""

    # 법령 ID (고유 식별자)
    law_id = law.get("법령ID", law.get("id", "unknown"))
    source_id = f"kr_law_{law_id}"

    # 제목
    title = law.get("법령명한글", "").strip()

    # 공포일자 → date로 변환 (형식: YYYYMMDD)
    raw_date = law.get("공포일자", "")
    metadata: dict = {
        "law_serial": law.get("법령일련번호", ""),
        "law_type": law.get("법령구분명", ""),
        "ministry": law.get("소관부처명", ""),
        "enforcement_date": law.get("시행일자", ""),
    }
    try:
        issued_date = date(
            int(raw_date[:4]),
            int(raw_date[4:6]),
            int(raw_date[6:8]),
        )
    except Exception:
        # [0-4] 폴백 + R07 격리 표지. silently 통과시키지 않는다.
        issued_date = _DATE_PARSE_FAILED_SENTINEL
        metadata["date_parse_failed"] = True
        metadata["raw_issued_date"] = raw_date

    # 원문 링크
    law_serial = law.get("법령일련번호", "")
    source_url = (
        f"https://www.law.go.kr/lsInfoP.do?lsiSeq={law_serial}"
        if law_serial else "https://www.law.go.kr"
    )

    # content_hash: 제목 + 공포일자 기반 (메타데이터 ID 해시; docs/schema_v1.md §6)
    content_hash = make_content_hash(f"{title}_{raw_date}")

    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="law",
        language="ko",
        title=title,
        issued_date=issued_date,
        source_url=source_url,
        content_hash=content_hash,
        metadata=metadata,
    )