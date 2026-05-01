"""
한국 국가법령정보 Open API 수집기 (decree).
법제처 API(target=ordin/admrul)에서 하위법령을 가져와 LegalDocument로 변환합니다.
"""

import logging
import os
from datetime import date

from dotenv import load_dotenv

from govlexops.core.http import get_json
from govlexops.core.raw_store import save_raw_response
from govlexops.schemas.legal_document import LegalDocument, make_content_hash

load_dotenv()
log = logging.getLogger(__name__)

BASE_URL = "http://www.law.go.kr/DRF/lawSearch.do"
_ISSUED_SINCE_YEAR = date.today().year - 3
_DATE_PARSE_FAILED_SENTINEL = date(1900, 1, 1)


def _issued_in_window(doc: LegalDocument, issued_since_year: int) -> bool:
    if doc.metadata.get("date_parse_failed") is True:
        return True
    return doc.issued_date.year >= issued_since_year


def fetch_decrees(
    query: str = "시행령",
    max_count: int = 50,
    *,
    target: str = "ordin",
    save_raw: bool = False,
) -> list[LegalDocument]:
    oc = os.getenv("LAW_GO_KR_OC")
    if not oc:
        raise ValueError(".env에 LAW_GO_KR_OC가 없습니다.")

    params = {
        "OC": oc,
        "target": target,
        "type": "JSON",
        "query": query,
        "display": max_count,
    }

    log.info(
        "→ KR decree API request: target=%s query=%s max_count=%d",
        target,
        query,
        max_count,
    )
    data = get_json(BASE_URL, params=params, timeout=30)
    if save_raw:
        save_raw_response(data, source="kr_decree", key=f"{target}_{query}")

    raw_items = data.get("LawSearch", {}).get("law", [])
    if isinstance(raw_items, dict):
        raw_items = [raw_items]

    docs: list[LegalDocument] = []
    for item in raw_items:
        try:
            docs.append(_convert_to_document(item))
        except Exception as e:
            log.warning(
                "⚠️ KR decree convert failed: title=%s err=%s",
                item.get("법령명한글", "?"),
                e,
            )

    log.info("✅ KR decree converted: %d docs (query=%s)", len(docs), query)
    return docs


def fetch_decrees_bulk(
    queries: list[str] | None = None,
    max_per_query: int = 80,
    issued_since_year: int | None = None,
    *,
    target: str = "ordin",
    save_raw: bool = False,
) -> list[LegalDocument]:
    if queries is None:
        queries = [
            "시행령",
            "대통령령",
            "총리령",
            "부령",
        ]

    all_docs: list[LegalDocument] = []
    seen_ids: set[str] = set()

    for query in queries:
        try:
            docs = fetch_decrees(
                query=query,
                max_count=max_per_query,
                target=target,
                save_raw=save_raw,
            )
            for doc in docs:
                if doc.source_id not in seen_ids:
                    seen_ids.add(doc.source_id)
                    all_docs.append(doc)
        except Exception as e:
            log.warning("⚠️ KR decree query failed: query=%s err=%s", query, e)

    min_year = (
        issued_since_year if issued_since_year is not None else _ISSUED_SINCE_YEAR
    )
    before = len(all_docs)
    all_docs = [d for d in all_docs if _issued_in_window(d, min_year)]
    log.info(
        "✅ KR decree year filter (>=%d): %d docs (before filter: %d)",
        min_year,
        len(all_docs),
        before,
    )
    return all_docs


def _convert_to_document(item: dict) -> LegalDocument:
    law_id = item.get("법령ID", item.get("id", "unknown"))
    source_id = f"kr_decree_{law_id}"
    title = item.get("법령명한글", "").strip()
    raw_date = item.get("공포일자", "")

    metadata: dict = {
        "law_serial": item.get("법령일련번호", ""),
        "law_type": item.get("법령구분명", ""),
        "ministry": item.get("소관부처명", ""),
        "enforcement_date": item.get("시행일자", ""),
    }
    try:
        issued_date = date(
            int(raw_date[:4]),
            int(raw_date[4:6]),
            int(raw_date[6:8]),
        )
    except Exception:
        issued_date = _DATE_PARSE_FAILED_SENTINEL
        metadata["date_parse_failed"] = True
        metadata["raw_issued_date"] = raw_date

    law_serial = item.get("법령일련번호", "")
    source_url = (
        f"https://www.law.go.kr/lsInfoP.do?lsiSeq={law_serial}"
        if law_serial
        else "https://www.law.go.kr"
    )
    content_hash = make_content_hash(f"{title}_{raw_date}")

    return LegalDocument(
        source_id=source_id,
        jurisdiction="KR",
        source_type="decree",
        language="ko",
        title=title,
        issued_date=issued_date,
        source_url=source_url,
        content_hash=content_hash,
        metadata=metadata,
    )
