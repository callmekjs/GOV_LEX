"""KR 하위법령(decree) 수집기(mock HTTP)."""

from unittest.mock import patch

import pytest
import responses

from govlexops.core.http import HTTPError
from govlexops.etl.ingest import kr_decree


@pytest.fixture
def kr_oc(monkeypatch):
    monkeypatch.setenv("LAW_GO_KR_OC", "test-oc")


@responses.activate
def test_fetch_decrees_normal(kr_oc):
    responses.add(
        responses.GET,
        kr_decree.BASE_URL,
        json={
            "LawSearch": {
                "law": [
                    {
                        "법령ID": "100",
                        "법령명한글": "개인정보 보호법 시행령",
                        "공포일자": "20240201",
                        "법령일련번호": "300001",
                    }
                ]
            }
        },
        status=200,
    )
    docs = kr_decree.fetch_decrees(query="시행령", max_count=10)
    assert len(docs) == 1
    assert docs[0].source_id == "kr_decree_100"
    assert docs[0].source_type == "decree"


@responses.activate
def test_fetch_decrees_empty_list(kr_oc):
    responses.add(
        responses.GET,
        kr_decree.BASE_URL,
        json={"LawSearch": {"law": []}},
        status=200,
    )
    assert kr_decree.fetch_decrees(max_count=10) == []


@responses.activate
def test_fetch_decrees_single_dict_normalized(kr_oc):
    responses.add(
        responses.GET,
        kr_decree.BASE_URL,
        json={
            "LawSearch": {
                "law": {
                    "법령ID": "101",
                    "법령명한글": "전자정부법 시행령",
                    "공포일자": "20250101",
                    "법령일련번호": "300002",
                }
            }
        },
        status=200,
    )
    docs = kr_decree.fetch_decrees(max_count=5)
    assert len(docs) == 1
    assert docs[0].title == "전자정부법 시행령"


@responses.activate
@patch("govlexops.core.http.time.sleep")
def test_fetch_decrees_429_then_fail(_, kr_oc):
    responses.add(responses.GET, kr_decree.BASE_URL, status=429)
    responses.add(responses.GET, kr_decree.BASE_URL, status=429)
    responses.add(responses.GET, kr_decree.BASE_URL, status=429)

    with pytest.raises(HTTPError, match="Rate limited"):
        kr_decree.fetch_decrees(max_count=10)


@responses.activate
def test_fetch_decrees_invalid_json_body(kr_oc):
    responses.add(
        responses.GET,
        kr_decree.BASE_URL,
        body="not-json",
        status=200,
    )
    with pytest.raises(HTTPError, match="Invalid JSON"):
        kr_decree.fetch_decrees(max_count=10)
