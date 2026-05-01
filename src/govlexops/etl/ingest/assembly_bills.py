"""
열린국회정보 Open API — 국회 법률안을 LegalDocument로 수집합니다.
메인 파이프라인에서 `fetch_assembly_bills()`를 호출합니다.
"""
import json
import logging
import os
import re
import time
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

from govlexops.core.http import get_json, make_session
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

load_dotenv()
log = logging.getLogger(__name__)

API_KEY = (
    os.getenv("OPEN_ASSEMBLY_API_KEY")
    or os.getenv("OPEN_ASSAMBLY_API_KEY")
    or ""
).strip()

# 최근 3개 연도(완료 연도 기준): 예) 2026년 실행 → 2023-01-01 ~ 2025-12-31
_END_YEAR = date.today().year - 1
_START_YEAR = date.today().year - 3
START_DATE = f"{_START_YEAR}-01-01"
END_DATE = f"{_END_YEAR}-12-31"

ASSEMBLIES = ["제21대", "제22대"]

# ── 수집 상한 정책 ──────────────────────────────────────────────
# TEST_LIMIT: 목록 API(ALLBILLV2) 필터 통과 후,
#             요약 API(BPMBILLSUMMARY)를 호출할 법안 수 상한.
#
# 근거:
#   - 열린국회정보 API 일일 호출 한도: 10,000건 (운영계정 기준)
#   - 요약 API 호출당 평균 응답 시간: 약 0.3~0.5초
#   - 5,000건 수집 시 예상 소요 시간: 약 25~40분
#   - 일일 한도의 50%를 한 번의 실행에 사용 (여유분 확보)
#
# 조정 지침:
#   - 빠른 검증용: test_limit=100 (약 1분)
#   - 일일 배치용: test_limit=5000 (기본값)
#   - 전체 수집:   test_limit=None (일 한도 초과 위험)
#
# 참고: fetch_assembly_bills(test_limit=...)로 실행 시 덮어쓰기 가능
TEST_LIMIT = 5000

PAGE_SIZE = 100
REQUEST_SLEEP = 0.15
TIMEOUT = 30

BASE_URL = "https://open.assembly.go.kr/portal/openapi/"
# [pipline_upgrade 0-3] 같은 호스트로 수천 번 호출하므로
# 연결 재사용을 위해 govlex 표준 UA가 사전 주입된 세션을 만든다.
session = make_session()


def normalize_date(text: str) -> Optional[str]:
    """날짜를 YYYY-MM-DD로 맞춤."""
    if not text:
        return None

    text = str(text).strip()
    for fmt in ("%Y-%m-%d", "%Y.%m.%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    digits = re.sub(r"[^0-9]", "", text)
    if len(digits) >= 8:
        try:
            return datetime.strptime(digits[:8], "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            return None
    return None


# [pipline_upgrade 0-4] 발의일 파싱 실패 시 명시적 sentinel.
# 1948 미만이라 QA의 R07이 자동 격리한다.
_DATE_PARSE_FAILED_SENTINEL = date(1900, 1, 1)


def _ppsl_to_date(s: str) -> tuple[date, bool]:
    """PPSL_DT 문자열을 date로 변환한다.

    Returns:
        (날짜, 파싱 실패 여부) — 실패 시 sentinel + True.
        호출자는 실패 표지를 metadata.date_parse_failed에 옮겨
        QA의 R07이 격리하도록 한다.
    """
    n = normalize_date(s)
    if not n:
        return _DATE_PARSE_FAILED_SENTINEL, True
    parts = n.split("-")
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2])), False
    except (ValueError, IndexError):
        return _DATE_PARSE_FAILED_SENTINEL, True


def date_in_range(text: str, start_date: str, end_date: str) -> bool:
    norm = normalize_date(text)
    if not norm:
        return False
    return start_date <= norm <= end_date


def request_json(service_name: str, params: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
    """[pipline_upgrade 0-3] 공통 HTTP 클라이언트의 얇은 래퍼.

    - timeout, retry, 429/5xx 처리, UA 헤더는 모두 govlexops.core.http.get_json이 담당.
    - 같은 호스트로 수천 번 호출하므로 모듈 전역 session을 재사용한다.
    - 호출자 측의 time.sleep(REQUEST_SLEEP)는 그대로 유지(쿼터 친화적 페이싱).
    """
    url = BASE_URL + service_name
    return get_json(
        url,
        params=params,
        timeout=TIMEOUT,
        max_retries=max_retries,
        session=session,
    )


def collect_dicts_with_keys(obj: Any, required_keys: set) -> List[Dict[str, Any]]:
    found = []

    def walk(x: Any):
        if isinstance(x, dict):
            if required_keys.issubset(set(x.keys())):
                found.append(x)
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for item in x:
                walk(item)

    walk(obj)

    uniq = {}
    for row in found:
        key = json.dumps(row, ensure_ascii=False, sort_keys=True)
        uniq[key] = row

    return list(uniq.values())


def fetch_bill_list_for_year(eraco: str, year: int) -> List[Dict[str, Any]]:
    all_rows = []
    seen_bill_nos = set()
    page = 1

    while True:
        params = {
            "KEY": API_KEY,
            "Type": "json",
            "pIndex": page,
            "pSize": PAGE_SIZE,
            "ERACO": eraco,
            "BILL_KND": "법률안",
            "PPSL_DT": str(year),
        }

        data = request_json("ALLBILLV2", params)
        rows = collect_dicts_with_keys(data, {"BILL_NO", "BILL_NM", "PPSL_DT"})

        rows = [
            r for r in rows
            if "법률안" in str(r.get("BILL_KND", ""))
            and str(year) in str(r.get("PPSL_DT", ""))
        ]

        new_rows = []
        for row in rows:
            bill_no = str(row.get("BILL_NO", "")).strip()
            if bill_no and bill_no not in seen_bill_nos:
                seen_bill_nos.add(bill_no)
                new_rows.append(row)

        if not new_rows:
            break

        all_rows.extend(new_rows)
        log.info(
            "[bill_list] %s %d page=%d count=%d",
            eraco, year, page, len(new_rows),
        )
        page += 1
        time.sleep(REQUEST_SLEEP)

    return all_rows


def fetch_bill_summary(bill_no: str) -> Optional[Dict[str, Any]]:
    params = {
        "KEY": API_KEY,
        "Type": "json",
        "pIndex": 1,
        "pSize": 100,
        "BILL_NO": bill_no,
    }

    data = request_json("BPMBILLSUMMARY", params)
    rows = collect_dicts_with_keys(data, {"BILL_NO", "SUMMARY"})

    if not rows:
        return None

    for row in rows:
        if str(row.get("BILL_NO", "")).strip() == str(bill_no).strip():
            return row

    return rows[0]


def dedupe_bills(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    uniq = {}
    for row in rows:
        bill_no = str(row.get("BILL_NO", "")).strip()
        if bill_no:
            uniq[bill_no] = row
    return list(uniq.values())


def _bill_to_legal_document(
    bill: Dict[str, Any],
    summary_row: Optional[Dict[str, Any]],
) -> Optional[LegalDocument]:
    bill_no = str(bill.get("BILL_NO", "")).strip()
    title = str(bill.get("BILL_NM", "")).strip()
    url = str(bill.get("LINK_URL", "")).strip()
    if not bill_no or not title or not url:
        return None

    ppsl = str(bill.get("PPSL_DT", "")).strip()
    issued, date_parse_failed = _ppsl_to_date(ppsl)
    raw_date = re.sub(r"[^0-9]", "", ppsl)[:8] if ppsl else ""

    source_id = f"kr_assembly_{bill_no}"
    content_hash = make_content_hash(f"{title}_{raw_date}_{bill_no}")

    metadata: dict = {
        "eraco": str(bill.get("ERACO", "")).strip(),
        "bill_id": str(bill.get("BILL_ID", "")).strip(),
        "bill_knd": str(bill.get("BILL_KND", "")).strip(),
        "ppsr_nm": str(bill.get("PPSR_NM", "")).strip(),
        "ppsr_knd": str(bill.get("PPSR_KND", "")).strip(),
        "jrcmit_nm": str(bill.get("JRCMIT_NM", "")).strip(),
        "rgs_conf_rslt": str(bill.get("RGS_CONF_RSLT", "")).strip(),
    }
    if date_parse_failed:
        # [0-4] 격리 표지. QA의 R07이 잡아낸다.
        metadata["date_parse_failed"] = True
        metadata["raw_issued_date"] = ppsl
    if summary_row:
        if summary_row.get("SUMMARY"):
            metadata["summary"] = str(summary_row.get("SUMMARY", ""))[:20000]
        if summary_row.get("AGE") is not None:
            metadata["summary_age"] = str(summary_row.get("AGE", "")).strip()

    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="bill",
        language="ko",
        title=title,
        issued_date=issued,
        source_url=url,
        content_hash=content_hash,
        metadata=metadata,
    )


def fetch_assembly_bills(
    test_limit: Optional[int] = None,
) -> List[LegalDocument]:
    """
    설정된 기간·대수의 국회 법률안을 API로 수집해 LegalDocument 목록으로 반환합니다.
    test_limit이 None이면 모듈 상수 TEST_LIMIT을 사용합니다. 전체 요약을 받으려면 TEST_LIMIT=None.
    """
    if not API_KEY:
        raise ValueError(".env에 OPEN_ASSEMBLY_API_KEY를 설정해 주세요.")

    limit = test_limit if test_limit is not None else TEST_LIMIT

    start_year = int(START_DATE[:4])
    end_year = int(END_DATE[:4])

    bill_rows: List[Dict[str, Any]] = []
    for eraco in ASSEMBLIES:
        for year in range(start_year, end_year + 1):
            try:
                rows = fetch_bill_list_for_year(eraco, year)
                bill_rows.extend(rows)
            except Exception as e:
                log.warning("[bill_list_err] %s %d err=%s", eraco, year, e)

    bill_rows = dedupe_bills(bill_rows)
    bill_rows = [
        r for r in bill_rows
        if date_in_range(str(r.get("PPSL_DT", "")), START_DATE, END_DATE)
    ]
    bill_rows.sort(
        key=lambda x: (normalize_date(str(x.get("PPSL_DT", ""))) or "", str(x.get("BILL_NO", "")))
    )

    log.info("[bill_list_done] 최종 법률안 수: %d건", len(bill_rows))

    if limit is not None:
        bill_rows = bill_rows[:limit]
        log.info(
            "[summary_limit] 앞에서 %d건만 처리 (TEST_LIMIT=%s)",
            len(bill_rows), limit,
        )

    docs: List[LegalDocument] = []
    total = len(bill_rows)
    for i, bill in enumerate(bill_rows, start=1):
        bill_no = str(bill.get("BILL_NO", "")).strip()
        bill_nm = str(bill.get("BILL_NM", "")).strip()

        try:
            summary_row = fetch_bill_summary(bill_no)
            doc = _bill_to_legal_document(bill, summary_row)
            if doc:
                docs.append(doc)
            log.info("[%d/%d] ok bill_no=%s title=%s", i, total, bill_no, bill_nm[:40])
        except Exception as e:
            log.warning(
                "[%d/%d] skip bill_no=%s title=%s err=%s",
                i, total, bill_no, bill_nm[:40], e,
            )

        time.sleep(REQUEST_SLEEP)

    log.info("[assembly_bills] LegalDocument %d건 변환 완료", len(docs))
    return docs


if __name__ == "__main__":
    # __main__ 단독 실행 시에만 표준 logging을 셋업.
    # 라이브러리로 import될 땐 호출자가 setup_logging을 책임진다.
    from govlexops.core.logging import setup_logging

    setup_logging()
    out = fetch_assembly_bills()
    log.info("샘플 실행: %d건", len(out))
