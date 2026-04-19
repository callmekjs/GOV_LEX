"""
미국 Congress.gov API v3 수집기.
법안(bill) 데이터를 가져와 LegalDocument로 변환합니다.
"""
import requests
import os
from datetime import date
from dotenv import load_dotenv
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

load_dotenv()

BASE_URL = "https://api.congress.gov/v3"


def fetch_bills(query: str = "artificial intelligence", max_count: int = 10) -> list[LegalDocument]:
    """
    Congress.gov API에서 법안을 검색해서 LegalDocument 목록을 반환합니다.
    """
    api_key = os.getenv("CONGRESS_GOV_API_KEY")
    if not api_key:
        raise ValueError(".env에 CONGRESS_GOV_API_KEY가 없습니다.")

    params = {
        "api_key": api_key,
        "query": query,
        "limit": max_count,
        "sort": "updateDate+desc",
        "format": "json",
    }

    print(f"  → 미국 Congress.gov API 호출 중... (query: {query})")
    response = requests.get(f"{BASE_URL}/bill", params=params)
    response.raise_for_status()

    data = response.json()
    raw_bills = data.get("bills", [])

    docs = []
    for bill in raw_bills:
        try:
            doc = _convert_to_document(bill)
            docs.append(doc)
        except Exception as e:
            print(f"  ⚠️ 변환 실패: {bill.get('title', '?')} — {e}")

    print(f"  ✅ 미국 법안 {len(docs)}건 변환 완료")
    return docs


def _convert_to_document(bill: dict) -> LegalDocument:
    """Congress.gov API 응답 1건을 LegalDocument로 변환합니다."""

    # 고유 ID
    congress = bill.get("congress", "")
    bill_type = bill.get("type", "").lower()
    bill_number = bill.get("number", "")
    source_id = f"us_congress_{congress}_{bill_type}{bill_number}"

    # 제목
    title = bill.get("title", "").strip()

    # 발의일 → date로 변환
    raw_date = bill.get("introducedDate", "")
    try:
        parts = raw_date.split("-")
        issued_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        issued_date = date(2000, 1, 1)

    # 원문 링크
    source_url = bill.get("url", "https://congress.gov")

    # content_hash
    content_hash = make_content_hash(f"{title}_{raw_date}_{bill_number}")

    # 최신 진행 상태
    latest_action = bill.get("latestAction", {})

    return LegalDocument(
        source_id=source_id,
        jurisdiction="US",
        source_type="bill",
        language="en",
        title=title,
        issued_date=issued_date,
        source_url=source_url,
        content_hash=content_hash,
        metadata={
            "congress": congress,
            "bill_type": bill.get("type", ""),
            "bill_number": bill_number,
            "origin_chamber": bill.get("originChamber", ""),
            "latest_action": latest_action.get("text", ""),
            "latest_action_date": latest_action.get("actionDate", ""),
        },
    )