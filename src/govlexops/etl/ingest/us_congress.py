"""
미국 Congress.gov API v3 수집기.
회기별 bill 목록 API로 대량 수집하거나, 지정 법안을 개별 조회합니다.
"""
import logging
import os
from datetime import date

from dotenv import load_dotenv

from govlexops.core.http import HTTPError, get_json
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

log = logging.getLogger(__name__)

load_dotenv()

BASE_URL = "https://api.congress.gov/v3"

# 발의일 기준 최근 N년만 유지
_MIN_INTRO_YEAR = date.today().year - 3

# [pipline_upgrade 0-4] 발의일 파싱 실패 시 명시적 sentinel.
# 1948 미만이라 QA의 R07이 자동 격리한다.
_DATE_PARSE_FAILED_SENTINEL = date(1900, 1, 1)

# ── 보조: AI·데이터 관련 지정 법안 (목록 API 실패 시 등) ──
KNOWN_AI_BILLS = [
    {"congress": 118, "type": "hr", "number": "4763"},
    {"congress": 118, "type": "s", "number": "2892"},
    {"congress": 118, "type": "hr", "number": "6936"},
    {"congress": 118, "type": "s", "number": "3312"},
    {"congress": 119, "type": "hr", "number": "1"},
    {"congress": 118, "type": "hr", "number": "5403"},
    {"congress": 118, "type": "s", "number": "2045"},
    {"congress": 118, "type": "hr", "number": "3369"},
    {"congress": 118, "type": "s", "number": "1289"},
    {"congress": 118, "type": "hr", "number": "6395"},
]


def _introduced_in_window(doc: LegalDocument) -> bool:
    """연도 정책 필터. 단, 파싱 실패 표지가 있는 문서는 통과시켜
    QA의 R07이 명시적으로 격리하도록 한다 [0-4]."""
    if doc.metadata.get("date_parse_failed") is True:
        return True
    return doc.issued_date.year >= _MIN_INTRO_YEAR


def _fetch_bills_from_congress_list(congress: int, max_count: int) -> list[LegalDocument]:
    """GET /v3/bill/{congress} 목록으로 페이지네이션 수집."""
    api_key = os.getenv("CONGRESS_GOV_API_KEY")
    if not api_key:
        raise ValueError(".env에 CONGRESS_GOV_API_KEY가 없습니다.")

    docs: list[LegalDocument] = []
    offset = 0
    page_size = min(250, max(1, max_count))

    while len(docs) < max_count:
        need = min(page_size, max_count - len(docs))
        params = {
            "api_key": api_key,
            "format": "json",
            "limit": need,
            "offset": offset,
            "sort": "updateDate+desc",
        }
        # [pipline_upgrade 0-3] 공통 HTTP 클라이언트 사용:
        #   목록 API는 응답이 무거워 timeout=90 유지.
        data = get_json(
            f"{BASE_URL}/bill/{congress}",
            params=params,
            timeout=90,
        )
        bills = data.get("bills", [])
        if not bills:
            break

        for item in bills:
            raw = item.get("bill") if isinstance(item.get("bill"), dict) else item
            if not isinstance(raw, dict):
                continue
            try:
                doc = _convert_to_document(raw)
                if _introduced_in_window(doc):
                    docs.append(doc)
            except Exception as e:
                log.warning("⚠️ US list item convert failed: err=%s", e)
            if len(docs) >= max_count:
                break

        pagination = data.get("pagination") or {}
        n = pagination.get("count", len(bills))
        try:
            offset += int(n)
        except (TypeError, ValueError):
            offset += len(bills)

        if len(bills) < need or not pagination.get("next"):
            break

    return docs[:max_count]


def fetch_bills(
    # ── 수집 상한 정책 ──────────────────────────────────────────────
    # max_count: Congress.gov 목록 API 한 번에 가져올 법안 수.
    #
    # 근거:
    #   - Congress.gov API 시간당 한도: 5,000건
    #   - 페이지네이션 기본: 250건/호출 (API 권장 상한)
    #   - 최근 3년 필터 적용 후 실제 반환: 통상 30~100건 수준
    #   - 250건 요청은 한도의 5%, 네트워크 안정성 확보
    #
    # 조정 지침:
    #   - 빠른 검증용: max_count=20
    #   - 기본 배치용: max_count=250 (기본값)
    #   - 대량 수집:   페이지네이션 + offset 활용
    max_count: int = 250,
    congress: int = 118,
) -> list[LegalDocument]:
    """
    회기별 bill 목록으로 대량 수집. 발의일이 최근 `_MIN_INTRO_YEAR` 이후인 것만 유지.
    """
    api_key = os.getenv("CONGRESS_GOV_API_KEY")
    if not api_key:
        raise ValueError(".env에 CONGRESS_GOV_API_KEY가 없습니다.")

    log.info(
        "→ US Congress bill list fetch: congress=%d max=%d",
        congress, max_count,
    )

    docs = _fetch_bills_from_congress_list(congress=congress, max_count=max_count)

    # 목록이 비면 지정 법안으로 폴백
    if not docs:
        log.warning("→ US list empty, falling back to KNOWN_AI_BILLS")
        for bill_info in KNOWN_AI_BILLS[: min(10, max_count)]:
            url = (
                f"{BASE_URL}/bill/"
                f"{bill_info['congress']}/"
                f"{bill_info['type']}/"
                f"{bill_info['number']}"
            )
            try:
                # [pipline_upgrade 0-3] 공통 HTTP 클라이언트.
                #   404는 HTTPError로 올라오므로 except에서 스킵 처리.
                payload = get_json(
                    url,
                    params={"api_key": api_key, "format": "json"},
                    timeout=60,
                )
                bill = payload.get("bill", {})
                if bill:
                    doc = _convert_to_document(bill)
                    if _introduced_in_window(doc):
                        docs.append(doc)
            except HTTPError as e:
                # 404 (해당 의안 없음) 등은 정상적으로 다음 후보로 넘어감.
                log.warning("⚠️ US bill fetch failed: bill=%s err=%s", bill_info, e)
            except Exception as e:
                log.warning("⚠️ US bill convert failed: bill=%s err=%s", bill_info, e)

    before = len(docs)
    docs = [d for d in docs if _introduced_in_window(d)]
    log.info(
        "✅ US bill year filter (>=%d): %d docs (before filter: %d)",
        _MIN_INTRO_YEAR, len(docs), before,
    )
    return docs


def _convert_to_document(bill: dict) -> LegalDocument:
    """Congress.gov API 응답 1건을 LegalDocument로 변환합니다."""

    congress = bill.get("congress", "")
    bill_type = str(bill.get("type", "")).lower()
    bill_number = str(bill.get("number", ""))
    source_id = f"us_congress_{congress}_{bill_type}{bill_number}"

    title = (bill.get("title") or "").strip()

    raw_date = bill.get("introducedDate", "") or ""

    latest_action = bill.get("latestAction") or {}
    if not isinstance(latest_action, dict):
        latest_action = {}

    pa = bill.get("policyArea")
    policy_name = ""
    if isinstance(pa, dict):
        policy_name = (pa.get("name") or "").strip()

    metadata: dict = {
        "congress": congress,
        "bill_type": bill.get("type", ""),
        "bill_number": bill_number,
        "origin_chamber": bill.get("originChamber", ""),
        "latest_action": latest_action.get("text", ""),
        "latest_action_date": latest_action.get("actionDate", ""),
        "policy_area": policy_name,
    }

    try:
        parts = raw_date.split("-")
        issued_date = date(int(parts[0]), int(parts[1]), int(parts[2]))
    except Exception:
        # [0-4] 폴백 + R07 격리 표지.
        issued_date = _DATE_PARSE_FAILED_SENTINEL
        metadata["date_parse_failed"] = True
        metadata["raw_issued_date"] = raw_date

    chamber = "house" if bill_type in ("hr", "hres", "hjres", "hconres", "hjr") else "senate"
    source_url = (
        f"https://congress.gov/bill/{congress}th-congress/{chamber}-bill/{bill_number}"
    )

    content_hash = make_content_hash(f"{title}_{raw_date}_{bill_number}")

    return LegalDocument(
        source_id=source_id,
        jurisdiction="US",
        source_type="bill",
        language="en",
        title=title or "(no title)",
        issued_date=issued_date,
        source_url=source_url,
        content_hash=content_hash,
        metadata=metadata,
    )
