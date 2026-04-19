"""
미국 Congress.gov API v3 수집기.
AI·데이터·규제 관련 실제 법안을 직접 지정해서 가져옵니다.
"""
import requests
import os
from datetime import date
from dotenv import load_dotenv
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

load_dotenv()

BASE_URL = "https://api.congress.gov/v3"

# ── 실제 AI·데이터·규제 관련 법안 목록 (직접 지정) ──
KNOWN_AI_BILLS = [
    {"congress": 118, "type": "hr",  "number": "4763"},  # AI Accountability Act
    {"congress": 118, "type": "s",   "number": "2892"},  # AI Act
    {"congress": 118, "type": "hr",  "number": "6936"},  # CREATE AI Act
    {"congress": 118, "type": "s",   "number": "3312"},  # Future of AI Act
    {"congress": 119, "type": "hr",  "number": "1"},     # 119대 첫 법안
    {"congress": 118, "type": "hr",  "number": "5403"},  # Digital Asset Market Structure
    {"congress": 118, "type": "s",   "number": "2045"},  # Data Privacy Act
    {"congress": 118, "type": "hr",  "number": "3369"},  # American Data Privacy Act
    {"congress": 118, "type": "s",   "number": "1289"},  # AI Research Act
    {"congress": 118, "type": "hr",  "number": "6395"},  # National AI Commission Act
]


def fetch_bills(query: str = "artificial intelligence", max_count: int = 10) -> list[LegalDocument]:
    """
    실제 AI·데이터·규제 관련 법안을 직접 가져옵니다.
    """
    api_key = os.getenv("CONGRESS_GOV_API_KEY")
    if not api_key:
        raise ValueError(".env에 CONGRESS_GOV_API_KEY가 없습니다.")

    print(f"  → 미국 Congress.gov API 호출 중... (AI 관련 법안 직접 수집)")

    docs = []
    for bill_info in KNOWN_AI_BILLS[:max_count]:
        try:
            url = (
                f"{BASE_URL}/bill/"
                f"{bill_info['congress']}/"
                f"{bill_info['type']}/"
                f"{bill_info['number']}"
            )
            params = {"api_key": api_key, "format": "json"}
            response = requests.get(url, params=params)

            if response.status_code == 404:
                continue

            response.raise_for_status()
            data = response.json()
            bill = data.get("bill", {})

            if bill:
                doc = _convert_to_document(bill)
                docs.append(doc)

        except Exception as e:
            print(f"  ⚠️ 법안 수집 실패 ({bill_info}): {e}")

    print(f"  ✅ 미국 법안 {len(docs)}건 변환 완료")
    return docs


def _convert_to_document(bill: dict) -> LegalDocument:
    """Congress.gov API 응답 1건을 LegalDocument로 변환합니다."""

    congress = bill.get("congress", "")
    bill_type = bill.get("type", "").lower()
    bill_number = bill.get("number", "")
    source_id = f"us_congress_{congress}_{bill_type}{bill_number}"

    title = bill.get("title", "").strip()

    raw_date = bill.get("introducedDate", "")
    try:
        parts = raw_date.split("-")
        issued_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        issued_date = date(2000, 1, 1)

    source_url = (
        f"https://congress.gov/bill/{congress}th-congress/"
        f"{'house' if bill_type == 'hr' else 'senate'}-bill/{bill_number}"
    )

    content_hash = make_content_hash(f"{title}_{raw_date}_{bill_number}")

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
            "policy_area": bill.get("policyArea", {}).get("name", ""),
        },
    )