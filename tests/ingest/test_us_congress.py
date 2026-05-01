"""US Congress.gov 수집기(mock HTTP)."""

from unittest.mock import patch

import pytest
import responses

from govlexops.core.http import HTTPError
from govlexops.etl.ingest import us_congress


@pytest.fixture
def congress_key(monkeypatch):
    monkeypatch.setenv("CONGRESS_GOV_API_KEY", "test-key")


def _bill_payload(
    *,
    congress: int = 118,
    bill_type: str = "HR",
    number: str = "4763",
    introduced: str = "2024-06-01",
    title: str = "Sample Artificial Intelligence Bill",
):
    return {
        "bills": [
            {
                "bill": {
                    "congress": congress,
                    "type": bill_type,
                    "number": number,
                    "title": title,
                    "introducedDate": introduced,
                    "latestAction": {"text": "Introduced", "actionDate": introduced},
                    "policyArea": {"name": "Technology"},
                }
            }
        ],
        "pagination": {"count": 1},
    }


@responses.activate
def test_fetch_bills_normal(congress_key):
    url = f"{us_congress.BASE_URL}/bill/118"
    responses.add(responses.GET, url, json=_bill_payload(), status=200)

    docs = us_congress.fetch_bills(max_count=5, congress=118)
    assert len(docs) == 1
    assert docs[0].jurisdiction == "US"
    assert docs[0].source_type == "bill"
    assert "Sample Artificial Intelligence" in docs[0].title


@responses.activate
def test_fetch_bills_empty_list_no_fallback(congress_key, monkeypatch):
    monkeypatch.setattr(us_congress, "KNOWN_AI_BILLS", [])
    url = f"{us_congress.BASE_URL}/bill/118"
    responses.add(
        responses.GET,
        url,
        json={"bills": [], "pagination": {"count": 0}},
        status=200,
    )

    assert us_congress.fetch_bills(max_count=10, congress=118) == []


@responses.activate
@patch("govlexops.core.http.time.sleep")
def test_fetch_bills_list_429_then_fail(_, congress_key, monkeypatch):
    monkeypatch.setattr(us_congress, "KNOWN_AI_BILLS", [])
    url = f"{us_congress.BASE_URL}/bill/118"
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=429)
    responses.add(responses.GET, url, status=429)

    with pytest.raises(HTTPError, match="Rate limited"):
        us_congress.fetch_bills(max_count=3, congress=118)


@responses.activate
def test_fetch_bills_invalid_json(congress_key, monkeypatch):
    monkeypatch.setattr(us_congress, "KNOWN_AI_BILLS", [])
    url = f"{us_congress.BASE_URL}/bill/118"
    responses.add(responses.GET, url, body="{broken", status=200)

    with pytest.raises(HTTPError, match="Invalid JSON"):
        us_congress.fetch_bills(max_count=3, congress=118)
