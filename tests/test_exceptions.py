"""Tests for reddipy.exceptions."""

import pytest

from reddipy.exceptions import (
    NetworkError,
    PostNotFoundError,
    ProxyError,
    RateLimitError,
    RedMinerError,
    SubredditNotFoundError,
    UserNotFoundError,
)

# ---------------------------------------------------------------------------
# Inheritance checks
# ---------------------------------------------------------------------------

class TestInheritance:
    def test_reddipy_error_inherits_from_exception(self):
        assert issubclass(RedMinerError, Exception)

    def test_subreddit_not_found_error_inherits_from_reddipy_error(self):
        assert issubclass(SubredditNotFoundError, RedMinerError)

    def test_post_not_found_error_inherits_from_reddipy_error(self):
        assert issubclass(PostNotFoundError, RedMinerError)

    def test_user_not_found_error_inherits_from_reddipy_error(self):
        assert issubclass(UserNotFoundError, RedMinerError)

    def test_rate_limit_error_inherits_from_reddipy_error(self):
        assert issubclass(RateLimitError, RedMinerError)

    def test_network_error_inherits_from_reddipy_error(self):
        assert issubclass(NetworkError, RedMinerError)

    def test_proxy_error_inherits_from_reddipy_error(self):
        assert issubclass(ProxyError, RedMinerError)


# ---------------------------------------------------------------------------
# Message propagation checks
# ---------------------------------------------------------------------------

class TestMessages:
    @pytest.mark.parametrize("exc_class, message", [
        (RedMinerError, "base error"),
        (SubredditNotFoundError, "r/secret is private"),
        (PostNotFoundError, "post has been deleted"),
        (UserNotFoundError, "user is suspended"),
        (RateLimitError, "too many requests, retries exhausted"),
        (NetworkError, "connection timed out"),
        (ProxyError, "all proxies are dead"),
    ])
    def test_exception_carries_message(self, exc_class, message):
        exc = exc_class(message)
        assert str(exc) == message

    @pytest.mark.parametrize("exc_class, message", [
        (SubredditNotFoundError, "r/secret is private"),
        (PostNotFoundError, "post has been deleted"),
        (UserNotFoundError, "user is suspended"),
        (RateLimitError, "too many requests, retries exhausted"),
        (NetworkError, "connection timed out"),
        (ProxyError, "all proxies are dead"),
    ])
    def test_exception_is_catchable_as_reddipy_error(self, exc_class, message):
        with pytest.raises(RedMinerError, match=message):
            raise exc_class(message)

    @pytest.mark.parametrize("exc_class, message", [
        (SubredditNotFoundError, "r/secret is private"),
        (PostNotFoundError, "post has been deleted"),
        (UserNotFoundError, "user is suspended"),
        (RateLimitError, "too many requests, retries exhausted"),
        (NetworkError, "connection timed out"),
        (ProxyError, "all proxies are dead"),
    ])
    def test_exception_is_catchable_as_base_exception(self, exc_class, message):
        with pytest.raises(Exception):
            raise exc_class(message)
