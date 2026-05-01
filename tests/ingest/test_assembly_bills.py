"""국회 열린국회정보 수집기(mock HTTP)."""

from unittest.mock import patch

import pytest
import responses

from govlexops.core.http import HTTPError
from govlexops.etl.ingest import assembly_bills


@pytest.fixture
def assembly_key(monkeypatch):
    """모듈 로드 시점에 고정된 API_KEY를 테스트마다 덮어쓴다."""
    monkeypatch.setattr(assembly_bills, "API_KEY", "assembly-test-key")


@pytest.fixture
def narrow_window(monkeypatch):
    """한 대수·한 연도만 순회하도록 줄여 HTTP 스텁 개수를 제한."""
    monkeypatch.setattr(assembly_bills, "ASSEMBLIES", ["제22대"])
    monkeypatch.setattr(assembly_bills, "START_DATE", "2024-01-01")
    monkeypatch.setattr(assembly_bills, "END_DATE", "2024-12-31")


def _list_json_page_with_one_bill():
    row = {
        "BILL_NO": "PRC_R20240009999999",
        "BILL_NM": "모의 법률안",
        "PPSL_DT": "2024-06-15",
        "BILL_KND": "법률안",
        "LINK_URL": "https://open.assembly.go.kr/portal/bill/mock",
        "ERACO": "제22대",
        "BILL_ID": "b1",
        "PPSR_NM": "홍길동",
        "PPSR_KND": "대표발의",
        "JRCMIT_NM": "소관위",
        "RGS_CONF_RSLT": "",
    }
    return {"nested": {"block": {"items": [row]}}}


@pytest.fixture(autouse=True)
def no_sleep():
    with patch.object(assembly_bills.time, "sleep"):
        yield


@responses.activate
def test_fetch_assembly_bills_normal(assembly_key, narrow_window):
    list_url = assembly_bills.BASE_URL + "ALLBILLV2"
    summary_url = assembly_bills.BASE_URL + "BPMBILLSUMMARY"

    responses.add(responses.GET, list_url, json=_list_json_page_with_one_bill(), status=200)
    responses.add(responses.GET, list_url, json={}, status=200)
    responses.add(
        responses.GET,
        summary_url,
        json={
            "data": [
                {
                    "BILL_NO": "PRC_R20240009999999",
                    "SUMMARY": "요약 본문 일부",
                    "AGE": "제22대",
                }
            ]
        },
        status=200,
    )

    docs = assembly_bills.fetch_assembly_bills(test_limit=5)
    assert len(docs) == 1
    assert docs[0].source_id == "kr_assembly_PRC_R20240009999999"
    assert docs[0].metadata.get("summary") == "요약 본문 일부"


@responses.activate
def test_fetch_assembly_bills_empty_list(assembly_key, narrow_window):
    list_url = assembly_bills.BASE_URL + "ALLBILLV2"
    responses.add(responses.GET, list_url, json={"empty": True}, status=200)

    assert assembly_bills.fetch_assembly_bills(test_limit=5) == []


def _list_params_stub():
    return {
        "KEY": "assembly-test-key",
        "Type": "json",
        "pIndex": 1,
        "pSize": assembly_bills.PAGE_SIZE,
        "ERACO": "제22대",
        "BILL_KND": "법률안",
        "PPSL_DT": "2024",
    }


@responses.activate
@patch("govlexops.core.http.time.sleep")
def test_request_json_429_then_raises(_, assembly_key):
    """열린국회 API도 공통 클라이언트를 쓰므로 429 재시도 후 실패 시 HTTPError."""
    url = assembly_bills.BASE_URL + "ALLBILLV2"
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=429)

    with pytest.raises(HTTPError, match="Rate limited"):
        assembly_bills.request_json("ALLBILLV2", _list_params_stub())


@responses.activate
def test_request_json_invalid_body_raises(assembly_key):
    url = assembly_bills.BASE_URL + "ALLBILLV2"
    responses.add(responses.GET, url, body="<html>not json</html>", status=200)

    with pytest.raises(HTTPError, match="Invalid JSON"):
        assembly_bills.request_json("ALLBILLV2", _list_params_stub())


@responses.activate
def test_fetch_assembly_bills_swallows_list_http_error(assembly_key, narrow_window):
    """상위 루프가 예외를 잡아 빈 목록으로 진행하는 경로(운영 시 로그만 남김)."""
    list_url = assembly_bills.BASE_URL + "ALLBILLV2"
    responses.add(responses.GET, list_url, body="not-json", status=200)

    assert assembly_bills.fetch_assembly_bills(test_limit=5) == []
