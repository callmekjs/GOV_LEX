"""KR 법령 수집기(mock HTTP)."""

from unittest.mock import patch

import pytest
import responses

from govlexops.core.http import HTTPError
from govlexops.etl.ingest import kr_law


@pytest.fixture
def kr_oc(monkeypatch):
    monkeypatch.setenv("LAW_GO_KR_OC", "test-oc")


@responses.activate
def test_fetch_laws_normal(kr_oc):
    responses.add(
        responses.GET,
        kr_law.BASE_URL,
        json={
            "LawSearch": {
                "law": [
                    {
                        "법령ID": "1",
                        "법령명한글": "AI기본법",
                        "공포일자": "20240315",
                        "법령일련번호": "999",
                    }
                ]
            }
        },
        status=200,
    )
    docs = kr_law.fetch_laws(query="인공지능", max_count=10)
    assert len(docs) == 1
    assert docs[0].title == "AI기본법"
    assert docs[0].source_id == "kr_law_1"


@responses.activate
def test_fetch_laws_empty_list(kr_oc):
    responses.add(
        responses.GET,
        kr_law.BASE_URL,
        json={"LawSearch": {"law": []}},
        status=200,
    )
    assert kr_law.fetch_laws(max_count=10) == []


@responses.activate
def test_fetch_laws_single_dict_normalized(kr_oc):
    """API가 단건 dict만 줄 때 리스트로 통일되는 경로."""
    responses.add(
        responses.GET,
        kr_law.BASE_URL,
        json={
            "LawSearch": {
                "law": {
                    "법령ID": "9",
                    "법령명한글": "단건테스트법",
                    "공포일자": "20250101",
                    "법령일련번호": "100",
                }
            }
        },
        status=200,
    )
    docs = kr_law.fetch_laws(max_count=5)
    assert len(docs) == 1
    assert docs[0].title == "단건테스트법"


@responses.activate
@patch("govlexops.core.http.time.sleep")
def test_fetch_laws_429_then_fail(_, kr_oc):
    responses.add(responses.GET, kr_law.BASE_URL, status=429)
    responses.add(responses.GET, kr_law.BASE_URL, status=429)
    responses.add(responses.GET, kr_law.BASE_URL, status=429)

    with pytest.raises(HTTPError, match="Rate limited"):
        kr_law.fetch_laws(max_count=10)


@responses.activate
def test_fetch_laws_invalid_json_body(kr_oc):
    responses.add(
        responses.GET,
        kr_law.BASE_URL,
        body="not-json",
        status=200,
    )
    with pytest.raises(HTTPError, match="Invalid JSON"):
        kr_law.fetch_laws(max_count=10)
