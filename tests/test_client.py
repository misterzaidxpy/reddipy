"""Tests for RedditClient (HTTP, rate limiting, pagination, proxies)."""

import tempfile
import time
from unittest.mock import MagicMock, patch, call

import pytest
import requests

from redminer.client import RedditClient
from redminer.exceptions import (
    NetworkError,
    ProxyError,
    RateLimitError,
    SubredditNotFoundError,
    PostNotFoundError,
    UserNotFoundError,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_response(status_code=200, json_data=None, raise_for_status=None):
    """Build a mock requests.Response."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    if raise_for_status:
        resp.raise_for_status.side_effect = raise_for_status
    return resp


def _page_json(children_data, after=None):
    """Build a Reddit-style listing JSON page."""
    children = [{"kind": "t3", "data": d} for d in children_data]
    return {"data": {"children": children, "after": after}}


# ---------------------------------------------------------------------------
# 1. fetch basics
# ---------------------------------------------------------------------------

class TestFetchBasics:
    @patch("redminer.client.requests.get")
    def test_fetch_returns_json(self, mock_get):
        payload = {"data": {"children": []}}
        mock_get.return_value = _mock_response(200, payload)

        client = RedditClient(delay=0)
        result = client.fetch("https://www.reddit.com/r/python.json")

        assert result == payload
        mock_get.assert_called_once()

    @patch("redminer.client.requests.get")
    def test_fetch_sends_correct_headers_and_params(self, mock_get):
        mock_get.return_value = _mock_response(200, {"ok": True})

        client = RedditClient(delay=0, user_agent="TestAgent/1.0")
        client.fetch("https://www.reddit.com/r/python.json", params={"limit": 10})

        _, kwargs = mock_get.call_args
        assert kwargs["headers"]["User-Agent"] == "TestAgent/1.0"
        assert kwargs["params"]["limit"] == 10


# ---------------------------------------------------------------------------
# 2. rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_rate_limiting_sleeps_between_requests(self, mock_get, mock_sleep):
        mock_get.return_value = _mock_response(200, {"ok": True})

        client = RedditClient(delay=1.0)
        client.fetch("https://www.reddit.com/r/python.json")
        client.fetch("https://www.reddit.com/r/python.json")

        # sleep should have been called at least once for rate limiting
        assert mock_sleep.called


# ---------------------------------------------------------------------------
# 3. retry on 429
# ---------------------------------------------------------------------------

class TestRetryOn429:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_retries_on_429_then_succeeds(self, mock_get, mock_sleep):
        resp_429 = _mock_response(429)
        resp_200 = _mock_response(200, {"ok": True})
        mock_get.side_effect = [resp_429, resp_200]

        client = RedditClient(delay=0)
        result = client.fetch("https://www.reddit.com/r/python.json")

        assert result == {"ok": True}
        assert mock_get.call_count == 2
        # backoff sleep should have been called
        mock_sleep.assert_any_call(2)


# ---------------------------------------------------------------------------
# 4. retry exhaustion (429)
# ---------------------------------------------------------------------------

class TestRetryExhaustion429:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_raises_rate_limit_error_after_3_retries(self, mock_get, mock_sleep):
        mock_get.return_value = _mock_response(429)

        client = RedditClient(delay=0)
        with pytest.raises(RateLimitError):
            client.fetch("https://www.reddit.com/r/python.json")

        # initial attempt + 3 retries = 4 calls
        assert mock_get.call_count == 4


# ---------------------------------------------------------------------------
# 5. 5xx retry
# ---------------------------------------------------------------------------

class TestRetry5xx:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_retries_on_500_then_succeeds(self, mock_get, mock_sleep):
        resp_500 = _mock_response(500)
        resp_200 = _mock_response(200, {"ok": True})
        mock_get.side_effect = [resp_500, resp_200]

        client = RedditClient(delay=0)
        result = client.fetch("https://www.reddit.com/r/python.json")

        assert result == {"ok": True}
        assert mock_get.call_count == 2

    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_raises_network_error_after_5xx_exhaustion(self, mock_get, mock_sleep):
        mock_get.return_value = _mock_response(502)

        client = RedditClient(delay=0)
        with pytest.raises(NetworkError):
            client.fetch("https://www.reddit.com/r/python.json")

        assert mock_get.call_count == 4


# ---------------------------------------------------------------------------
# 6. 404 error
# ---------------------------------------------------------------------------

class TestNotFoundErrors:
    @patch("redminer.client.requests.get")
    def test_404_subreddit_raises_subreddit_not_found(self, mock_get):
        mock_get.return_value = _mock_response(404)

        client = RedditClient(delay=0)
        with pytest.raises(SubredditNotFoundError):
            client.fetch("https://www.reddit.com/r/nonexistent.json")

    @patch("redminer.client.requests.get")
    def test_404_post_raises_post_not_found(self, mock_get):
        mock_get.return_value = _mock_response(404)

        client = RedditClient(delay=0)
        with pytest.raises(PostNotFoundError):
            client.fetch("https://www.reddit.com/r/python/comments/abc123/some_post.json")

    @patch("redminer.client.requests.get")
    def test_404_user_raises_user_not_found(self, mock_get):
        mock_get.return_value = _mock_response(404)

        client = RedditClient(delay=0)
        with pytest.raises(UserNotFoundError):
            client.fetch("https://www.reddit.com/user/nonexistent.json")

    @patch("redminer.client.requests.get")
    def test_403_without_cookie_raises_network_error(self, mock_get):
        mock_get.return_value = _mock_response(403)

        client = RedditClient(delay=0)
        with pytest.raises(NetworkError, match="authenticate"):
            client.fetch("https://www.reddit.com/r/privateSub.json")

    @patch("redminer.client.requests.get")
    def test_403_with_cookie_raises_subreddit_not_found(self, mock_get):
        mock_get.return_value = _mock_response(403)

        client = RedditClient(delay=0, cookie="fake_session")
        with pytest.raises(SubredditNotFoundError):
            client.fetch("https://www.reddit.com/r/privateSub.json")


# ---------------------------------------------------------------------------
# 7. connection error
# ---------------------------------------------------------------------------

class TestConnectionError:
    @patch("redminer.client.requests.get")
    def test_connection_error_raises_network_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        client = RedditClient(delay=0)
        with pytest.raises(NetworkError):
            client.fetch("https://www.reddit.com/r/python.json")

    @patch("redminer.client.requests.get")
    def test_timeout_raises_network_error(self, mock_get):
        mock_get.side_effect = requests.Timeout("Timed out")

        client = RedditClient(delay=0)
        with pytest.raises(NetworkError):
            client.fetch("https://www.reddit.com/r/python.json")


# ---------------------------------------------------------------------------
# 8. fetch_all pagination
# ---------------------------------------------------------------------------

class TestFetchAllPagination:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_fetch_all_paginates_correctly(self, mock_get, mock_sleep):
        page1_items = [{"id": f"p1_{i}"} for i in range(3)]
        page2_items = [{"id": f"p2_{i}"} for i in range(2)]

        page1 = _mock_response(200, _page_json(page1_items, after="t3_abc"))
        page2 = _mock_response(200, _page_json(page2_items, after=None))
        mock_get.side_effect = [page1, page2]

        client = RedditClient(delay=0)
        items = client.fetch_all("https://www.reddit.com/r/python.json", limit=5)

        assert len(items) == 5
        assert items[0]["id"] == "p1_0"
        assert items[3]["id"] == "p2_0"


# ---------------------------------------------------------------------------
# 9. fetch_all respects limit
# ---------------------------------------------------------------------------

class TestFetchAllRespectsLimit:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_fetch_all_trims_to_limit(self, mock_get, mock_sleep):
        page_items = [{"id": f"item_{i}"} for i in range(100)]
        page = _mock_response(200, _page_json(page_items, after="t3_next"))
        mock_get.return_value = page

        client = RedditClient(delay=0)
        items = client.fetch_all("https://www.reddit.com/r/python.json", limit=50)

        assert len(items) == 50


# ---------------------------------------------------------------------------
# 10. fetch_all stops on no more pages
# ---------------------------------------------------------------------------

class TestFetchAllStopsOnNoMore:
    @patch("redminer.client.time.sleep")
    @patch("redminer.client.requests.get")
    def test_stops_when_after_is_none(self, mock_get, mock_sleep):
        page_items = [{"id": f"item_{i}"} for i in range(3)]
        page = _mock_response(200, _page_json(page_items, after=None))
        mock_get.return_value = page

        client = RedditClient(delay=0)
        items = client.fetch_all("https://www.reddit.com/r/python.json", limit=25)

        assert len(items) == 3
        assert mock_get.call_count == 1


# ---------------------------------------------------------------------------
# 11. single proxy
# ---------------------------------------------------------------------------

class TestSingleProxy:
    @patch("redminer.client.requests.get")
    def test_proxy_passed_to_requests(self, mock_get):
        mock_get.return_value = _mock_response(200, {"ok": True})

        client = RedditClient(delay=0, proxy="http://1.2.3.4:8080")
        client.fetch("https://www.reddit.com/r/python.json")

        _, kwargs = mock_get.call_args
        assert kwargs["proxies"] == {
            "http": "http://1.2.3.4:8080",
            "https": "http://1.2.3.4:8080",
        }


# ---------------------------------------------------------------------------
# 12. proxy rotation
# ---------------------------------------------------------------------------

class TestProxyRotation:
    @patch("redminer.client.requests.get")
    def test_proxy_file_loads_and_rotates(self, mock_get):
        mock_get.return_value = _mock_response(200, {"ok": True})

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("http://proxy1:8080\nhttp://proxy2:8080\nhttp://proxy3:8080\n")
            f.flush()
            proxy_file = f.name

        client = RedditClient(delay=0, proxy_file=proxy_file)
        assert len(client._proxies) == 3

        # Make several requests and verify proxies param is always set
        for _ in range(6):
            client.fetch("https://www.reddit.com/r/python.json")

        for c in mock_get.call_args_list:
            _, kwargs = c
            assert "proxies" in kwargs
            proxy_url = kwargs["proxies"]["http"]
            assert proxy_url in [
                "http://proxy1:8080",
                "http://proxy2:8080",
                "http://proxy3:8080",
            ]


# ---------------------------------------------------------------------------
# 13. dead proxy cooldown
# ---------------------------------------------------------------------------

class TestDeadProxyCooldown:
    def test_dead_proxy_is_skipped(self):
        client = RedditClient(delay=0, proxy="http://dead:8080")
        # Mark proxy as dead just now
        client._dead_proxies["http://dead:8080"] = time.time()

        with pytest.raises(ProxyError):
            client._select_proxy()

    def test_dead_proxy_revives_after_cooldown(self):
        client = RedditClient(delay=0, proxy="http://dead:8080")
        # Mark proxy as dead 61 seconds ago
        client._dead_proxies["http://dead:8080"] = time.time() - 61

        result = client._select_proxy()
        assert result == {
            "http": "http://dead:8080",
            "https": "http://dead:8080",
        }

    @patch("redminer.client.requests.get")
    def test_connection_error_marks_proxy_dead(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("Connection refused")

        client = RedditClient(delay=0, proxy="http://flaky:8080")
        with pytest.raises(NetworkError):
            client.fetch("https://www.reddit.com/r/python.json")

        assert "http://flaky:8080" in client._dead_proxies
