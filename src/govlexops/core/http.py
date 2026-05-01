"""GovLex-Ops 공통 HTTP 클라이언트.

[pipline_upgrade 0-3]
세 수집기(kr_law, us_congress, assembly_bills)가 각자 다른 방식으로
requests.get()을 호출하던 것을 하나의 함수로 통일한다.

이전 상태의 문제:
  - kr_law.py: timeout 없음 → API가 느려지면 영원히 안 끝남
  - us_congress.py: timeout은 있으나 retry 없음 → 일시 장애에 약함
  - assembly_bills.py: 자체 retry/timeout/sleep 구현 → 다른 수집기와 중복 코드

이후 통일된 정책:
  - 모든 호출에 timeout 강제 (기본 30초)
  - 429 (Too Many Requests): exponential backoff × 2 후 재시도
  - 5xx 서버 에러: exponential backoff 후 재시도
  - 4xx (429 제외): 즉시 실패 (재시도 무의미)
  - timeout / connection error: exponential backoff 후 재시도
  - User-Agent 헤더 통일
  - 구조화 로그 (logging.getLogger("govlex.http"))
"""

from __future__ import annotations

import logging
import time
from typing import Any, Mapping, Optional

import requests
from requests import Session

log = logging.getLogger("govlex.http")

DEFAULT_USER_AGENT = "govlex-ops/0.1 (+https://github.com/Gov_Lex)"
DEFAULT_TIMEOUT = 30
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF = 1.5


class HTTPError(Exception):
    """공통 HTTP 클라이언트가 모든 재시도 후 실패했거나, 4xx 응답을 받았을 때 발생."""


def get_json(
    url: str,
    params: Optional[Mapping[str, Any]] = None,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff: float = DEFAULT_BACKOFF,
    session: Optional[Session] = None,
    headers: Optional[Mapping[str, str]] = None,
) -> dict:
    """GET 요청을 보내고 응답을 JSON으로 파싱해 반환한다.

    재시도 정책:
      - 429 (Too Many Requests): (backoff^attempt) × 2 초 대기 후 재시도
      - 5xx (서버 에러):          backoff^attempt 초 대기 후 재시도
      - timeout / 연결 실패:      backoff^attempt 초 대기 후 재시도
      - 4xx (429 제외):           즉시 HTTPError raise (재시도 무의미)
      - JSON 파싱 실패:           즉시 HTTPError raise

    Args:
        url: 호출 URL
        params: 쿼리 파라미터 dict
        timeout: 호출당 타임아웃 (초). 기본 30.
        max_retries: 재시도를 포함한 최대 시도 횟수. 기본 3.
        backoff: exponential backoff의 밑. 기본 1.5 → 1.5, 2.25, 3.375 초.
        session: 재사용할 requests.Session. 같은 호스트 다회 호출 시 권장.
        headers: 추가 헤더. User-Agent는 자동으로 주입됨.

    Returns:
        파싱된 JSON dict.

    Raises:
        HTTPError: 모든 재시도 실패, 4xx 응답, 또는 JSON 파싱 실패 시.
    """
    sess = session if session is not None else requests
    final_headers: dict[str, str] = {"User-Agent": DEFAULT_USER_AGENT}
    if headers:
        final_headers.update(headers)

    last_exc: Optional[Exception] = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = sess.get(url, params=params, timeout=timeout, headers=final_headers)
        except (requests.Timeout, requests.ConnectionError) as e:
            last_exc = e
            wait = backoff**attempt
            log.warning(
                "http_network_retry attempt=%d url=%s err=%s wait=%.2fs",
                attempt,
                url,
                type(e).__name__,
                wait,
            )
            if attempt < max_retries:
                time.sleep(wait)
                continue
            break

        # 429 → 대기 후 재시도
        if resp.status_code == 429:
            wait = (backoff**attempt) * 2
            log.warning(
                "http_rate_limited attempt=%d url=%s wait=%.2fs",
                attempt,
                url,
                wait,
            )
            if attempt < max_retries:
                time.sleep(wait)
                continue
            raise HTTPError(f"Rate limited after {max_retries} retries: {url}")

        # 5xx → 대기 후 재시도
        if 500 <= resp.status_code < 600:
            wait = backoff**attempt
            log.warning(
                "http_server_error_retry attempt=%d status=%d url=%s wait=%.2fs",
                attempt,
                resp.status_code,
                url,
                wait,
            )
            if attempt < max_retries:
                time.sleep(wait)
                continue
            raise HTTPError(
                f"Server error {resp.status_code} after {max_retries} retries: {url}"
            )

        # 기타 4xx → 즉시 실패 (재시도해도 결과 동일)
        if 400 <= resp.status_code < 500:
            raise HTTPError(f"Client error {resp.status_code}: {url}")

        # 2xx → JSON 파싱
        try:
            return resp.json()
        except ValueError as e:
            raise HTTPError(f"Invalid JSON response from {url}: {e}") from e

    raise HTTPError(f"Network failure after {max_retries} retries: {url}") from last_exc


def make_session() -> Session:
    """User-Agent가 사전 주입된 requests.Session을 만든다.

    같은 호스트로 여러 번 호출하는 수집기(예: assembly_bills)에서
    연결 재사용으로 성능을 개선한다.
    """
    s = Session()
    s.headers.update({"User-Agent": DEFAULT_USER_AGENT})
    return s
