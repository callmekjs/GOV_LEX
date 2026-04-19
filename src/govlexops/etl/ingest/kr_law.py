"""
한국 국가법령정보 Open API 수집기.
법제처 API에서 법령 데이터를 가져와 LegalDocument로 변환합니다.
"""
import requests
import os
from datetime import date
from dotenv import load_dotenv
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

load_dotenv()

BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"


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

    print(f"  → 한국 법령 API 호출 중... (query: {query})")
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()

    data = response.json()

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
            print(f"  ⚠️ 변환 실패: {law.get('법령명한글', '?')} — {e}")

    print(f"  ✅ 한국 법령 {len(docs)}건 변환 완료")
    return docs

def fetch_laws_bulk(
    queries: list[str] = None,
    max_per_query: int = 10,
) -> list[LegalDocument]:
    """
    여러 쿼리로 법령을 수집하고 중복을 제거해서 반환합니다.
    """
    if queries is None:
        queries = [
            "인공지능",
            "데이터",
            "개인정보",
            "정보통신",
            "규제",
            "디지털",
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
            print(f"  ⚠️ 쿼리 실패 ({query}): {e}")

    print(f"  ✅ KR 법령 총 {len(all_docs)}건 (중복 제거 후)")
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
    try:
        issued_date = date(
            int(raw_date[:4]),
            int(raw_date[4:6]),
            int(raw_date[6:8]),
        )
    except Exception:
        issued_date = date(2000, 1, 1)

    # 원문 링크
    law_serial = law.get("법령일련번호", "")
    source_url = (
        f"https://www.law.go.kr/lsInfoP.do?lsiSeq={law_serial}"
        if law_serial else "https://www.law.go.kr"
    )

    # content_hash: 제목 + 공포일자 기반
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
        metadata={
            "law_serial": law_serial,
            "law_type": law.get("법령구분명", ""),
            "ministry": law.get("소관부처명", ""),
            "enforcement_date": law.get("시행일자", ""),
        },
    )