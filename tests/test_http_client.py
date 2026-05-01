"""[pipline_upgrade 0-3] 공통 HTTP 클라이언트 테스트.

3개 수집기가 공유하는 govlexops.core.http.get_json의
재시도/타임아웃/429 분기/4xx 즉시실패/UA 정책을 잠근다.
"""
from unittest.mock import MagicMock, patch

import pytest
import requests

from govlexops.core.http import HTTPError, get_json, make_session


def _mock_response(status_code: int, json_data=None, raise_on_json: bool = False):
    m = MagicMock()
    m.status_code = status_code
    if raise_on_json:
        m.json.side_effect = ValueError("not json")
    else:
        m.json.return_value = json_data if json_data is not None else {}
    return m


# ── 정상 케이스 ──────────────────────────────────────────────────────

@patch("govlexops.core.http.requests.get")
def test_normal_200_returns_json(mock_get):
    """200 응답 + JSON → 한 번 호출되고 dict 반환."""
    mock_get.return_value = _mock_response(200, {"hello": "world"})
    result = get_json("http://example.com")
    assert result == {"hello": "world"}
    assert mock_get.call_count == 1


@patch("govlexops.core.http.requests.get")
def test_user_agent_header_attached(mock_get):
    """모든 호출에 govlex-ops User-Agent가 자동 주입된다."""
    mock_get.return_value = _mock_response(200, {})
    get_json("http://example.com")
    headers = mock_get.call_args.kwargs["headers"]
    assert "User-Agent" in headers
    assert "govlex-ops" in headers["User-Agent"]


@patch("govlexops.core.http.requests.get")
def test_custom_headers_merge_with_user_agent(mock_get):
    """호출자가 추가 헤더를 줘도 UA는 유지되고 추가 헤더가 합쳐진다."""
    mock_get.return_value = _mock_response(200, {})
    get_json("http://example.com", headers={"X-Custom": "hello"})
    headers = mock_get.call_args.kwargs["headers"]
    assert headers["X-Custom"] == "hello"
    assert "govlex-ops" in headers["User-Agent"]


# ── 재시도 케이스 ────────────────────────────────────────────────────

@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_429_retries_then_succeeds(mock_get, mock_sleep):
    """429 한 번 받고 두 번째에 200 → 최종 성공."""
    mock_get.side_effect = [
        _mock_response(429),
        _mock_response(200, {"ok": True}),
    ]
    result = get_json("http://example.com", max_retries=3)
    assert result == {"ok": True}
    assert mock_get.call_count == 2
    assert mock_sleep.called


@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_429_uses_double_backoff(mock_get, mock_sleep):
    """429는 일반 backoff의 2배 대기 시간을 적용한다."""
    mock_get.side_effect = [
        _mock_response(429),
        _mock_response(200, {}),
    ]
    get_json("http://example.com", max_retries=3, backoff=2.0)
    # 첫 번째 sleep: backoff^1 × 2 = 2.0 × 2 = 4.0
    sleep_arg = mock_sleep.call_args_list[0].args[0]
    assert sleep_arg == 4.0


@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_500_retries_then_fails(mock_get, mock_sleep):
    """5xx는 재시도하다가 결국 실패하면 HTTPError."""
    mock_get.return_value = _mock_response(500)
    with pytest.raises(HTTPError, match="Server error 500"):
        get_json("http://example.com", max_retries=3)
    assert mock_get.call_count == 3


@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_timeout_retries_then_succeeds(mock_get, mock_sleep):
    """timeout 발생 후 다음 시도에 성공."""
    mock_get.side_effect = [
        requests.Timeout("read timeout"),
        _mock_response(200, {"recovered": True}),
    ]
    result = get_json("http://example.com", max_retries=3)
    assert result == {"recovered": True}


@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_connection_error_retries_then_fails(mock_get, mock_sleep):
    """ConnectionError가 모든 재시도에서 발생하면 HTTPError."""
    mock_get.side_effect = requests.ConnectionError("conn refused")
    with pytest.raises(HTTPError, match="Network failure"):
        get_json("http://example.com", max_retries=2)
    assert mock_get.call_count == 2


# ── 즉시 실패 케이스 ─────────────────────────────────────────────────

@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_404_fails_immediately(mock_get, mock_sleep):
    """404 같은 4xx는 재시도 없이 즉시 실패한다."""
    mock_get.return_value = _mock_response(404)
    with pytest.raises(HTTPError, match="Client error 404"):
        get_json("http://example.com", max_retries=3)
    assert mock_get.call_count == 1
    assert not mock_sleep.called


@patch("govlexops.core.http.time.sleep")
@patch("govlexops.core.http.requests.get")
def test_401_fails_immediately(mock_get, mock_sleep):
    """401 (인증 실패) 도 재시도해봤자 동일하므로 즉시 실패."""
    mock_get.return_value = _mock_response(401)
    with pytest.raises(HTTPError, match="Client error 401"):
        get_json("http://example.com", max_retries=3)
    assert mock_get.call_count == 1


@patch("govlexops.core.http.requests.get")
def test_invalid_json_raises_immediately(mock_get):
    """200 OK지만 JSON 파싱 실패 → 재시도 없이 HTTPError."""
    mock_get.return_value = _mock_response(200, raise_on_json=True)
    with pytest.raises(HTTPError, match="Invalid JSON"):
        get_json("http://example.com")
    assert mock_get.call_count == 1


# ── 타임아웃 파라미터 전달 ───────────────────────────────────────────

@patch("govlexops.core.http.requests.get")
def test_timeout_parameter_propagated(mock_get):
    """호출자가 지정한 timeout이 requests.get에 그대로 전달된다."""
    mock_get.return_value = _mock_response(200, {})
    get_json("http://example.com", timeout=60)
    assert mock_get.call_args.kwargs["timeout"] == 60


# ── 세션 재사용 ──────────────────────────────────────────────────────

def test_make_session_attaches_user_agent():
    """make_session()이 만든 Session에는 govlex UA가 사전 주입된다."""
    s = make_session()
    assert "User-Agent" in s.headers
    assert "govlex-ops" in s.headers["User-Agent"]


def test_session_used_when_provided():
    """session 인자가 주어지면 requests.get 대신 session.get이 호출된다."""
    fake_session = MagicMock()
    fake_session.get.return_value = _mock_response(200, {"via": "session"})

    result = get_json("http://example.com", session=fake_session)
    assert result == {"via": "session"}
    fake_session.get.assert_called_once()
