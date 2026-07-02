"""Domain-specific exceptions for RedMiner."""


class RedMinerError(Exception):
    """Base exception for all RedMiner errors."""


class SubredditNotFoundError(RedMinerError):
    """Raised when a subreddit is private, banned, or nonexistent (403/404)."""


class PostNotFoundError(RedMinerError):
    """Raised when a post URL is deleted or invalid."""


class UserNotFoundError(RedMinerError):
    """Raised when a user is suspended, shadow-banned, or nonexistent."""


class RateLimitError(RedMinerError):
    """Raised when all retries are exhausted after repeated 429 responses."""


class NetworkError(RedMinerError):
    """Raised on connection failures or timeouts."""


class ProxyError(RedMinerError):
    """Raised when all proxies are exhausted or dead."""
