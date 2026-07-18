"""RedditClient: HTTP layer with rate limiting, pagination, and proxy support."""

import random
import sys
import time

import requests

from redminer.exceptions import (
    NetworkError,
    PostNotFoundError,
    ProxyError,
    RateLimitError,
    SubredditNotFoundError,
    UserNotFoundError,
)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/149.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {
    "User-Agent": DEFAULT_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Sec-CH-UA": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    "Sec-CH-UA-Mobile": "?0",
    "Sec-CH-UA-Platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Connection": "keep-alive",
}

MAX_RETRIES = 3
BACKOFF_SCHEDULE = [2, 4, 8]
DEAD_PROXY_COOLDOWN = 60  # seconds


class RedditClient:
    """HTTP client for Reddit's public JSON endpoints."""

    BASE_URL = "https://www.reddit.com"

    def __init__(
        self,
        delay: float = 2.0,
        proxy: str | None = None,
        proxy_file: str | None = None,
        user_agent: str | None = None,
        verbose: bool = False,
        cookie: str | None = None,
        cookie_file: str | None = None,
    ):
        self.delay = delay
        self.verbose = verbose
        self._headers = dict(DEFAULT_HEADERS)
        if user_agent:
            self._headers["User-Agent"] = user_agent
        self._last_request_time: float = 0.0
        self._dead_proxies: dict[str, float] = {}

        # Build proxy pool
        self._proxies: list[str] = []
        if proxy:
            self._proxies = [proxy]
        elif proxy_file:
            self._proxies = self._load_proxy_file(proxy_file)

        # Build cookie jar
        self._cookies: dict[str, str] = {}
        if cookie:
            self._cookies["reddit_session"] = cookie
        elif cookie_file:
            self._cookies = self._load_cookie_file(cookie_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch(self, url: str, params: dict | None = None) -> dict:
        """Single HTTP GET with rate limiting, retries, and proxy support."""
        self._rate_limit()

        proxy_dict = self._select_proxy()

        for attempt in range(MAX_RETRIES + 1):
            try:
                resp = requests.get(
                    url,
                    headers=self._headers,
                    params=params or {},
                    proxies=proxy_dict,
                    cookies=self._cookies or None,
                    timeout=30,
                )
            except (requests.ConnectionError, requests.Timeout) as exc:
                # Mark the proxy dead if one was used
                if proxy_dict:
                    proxy_url = proxy_dict.get("http")
                    if proxy_url:
                        self._dead_proxies[proxy_url] = time.time()
                raise NetworkError(str(exc)) from exc

            status = resp.status_code

            # 403 without cookies = auth issue, not "not found"
            if status == 403 and not self._cookies:
                raise NetworkError(
                    "Reddit returned 403 Forbidden. You likely need to authenticate. "
                    "Run: Reddit.configure(cookie='your_reddit_session') or use --cookie"
                )

            # Permanent errors (not retryable)
            if status in (403, 404):
                self._raise_not_found(url, status)

            # Rate limited
            if status == 429:
                if attempt < MAX_RETRIES:
                    wait = BACKOFF_SCHEDULE[attempt]
                    self._log(f"Rate limited (429). Cooling down {wait}s before retry {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(wait)
                    continue
                raise RateLimitError(
                    f"Rate limited after {MAX_RETRIES} retries: {url}"
                )

            # Server errors
            if status >= 500:
                if attempt < MAX_RETRIES:
                    wait = BACKOFF_SCHEDULE[attempt]
                    self._log(f"Server error ({status}). Cooling down {wait}s before retry {attempt + 1}/{MAX_RETRIES}...")
                    time.sleep(BACKOFF_SCHEDULE[attempt])
                    continue
                raise NetworkError(
                    f"Server error {status} after {MAX_RETRIES} retries: {url}"
                )

            # Success
            return resp.json()

        # Should not be reachable, but just in case
        raise NetworkError(f"Unexpected state after retries: {url}")  # pragma: no cover

    def fetch_all(
        self, url: str, params: dict | None = None, limit: int = 25
    ) -> list[dict]:
        """Paginated fetch that collects items across multiple pages."""
        collected: list[dict] = []
        after: str | None = None
        params = dict(params) if params else {}

        while len(collected) < limit:
            remaining = limit - len(collected)
            page_params = {**params, "limit": min(100, remaining)}
            if after:
                page_params["after"] = after

            data = self.fetch(url, params=page_params)
            children = data.get("data", {}).get("children", [])

            for child in children:
                if len(collected) >= limit:
                    break
                collected.append(child.get("data", {}))

            after = data.get("data", {}).get("after")
            if not after:
                break

        return collected

    # ------------------------------------------------------------------
    # Proxy management
    # ------------------------------------------------------------------

    def _select_proxy(self) -> dict | None:
        """Pick a live proxy from the pool, or None if no proxies configured."""
        if not self._proxies:
            return None

        now = time.time()
        alive = [
            p
            for p in self._proxies
            if p not in self._dead_proxies
            or (now - self._dead_proxies[p]) >= DEAD_PROXY_COOLDOWN
        ]

        if not alive:
            raise ProxyError("All proxies are dead")

        chosen = random.choice(alive)
        return {"http": chosen, "https": chosen}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rate_limit(self) -> None:
        """Sleep if needed to enforce minimum delay between requests."""
        if self._last_request_time > 0 and self.delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def _raise_not_found(self, url: str, status: int) -> None:
        """Raise the appropriate not-found exception based on URL pattern."""
        if "/comments/" in url:
            raise PostNotFoundError(f"Post not found ({status}): {url}")
        if "/user/" in url or "/u/" in url:
            raise UserNotFoundError(f"User not found ({status}): {url}")
        # Default to subreddit
        raise SubredditNotFoundError(f"Subreddit not found ({status}): {url}")

    def _log(self, message: str) -> None:
        """Print to stderr if verbose mode is on."""
        if self.verbose:
            print(message, file=sys.stderr)

    @staticmethod
    def _load_proxy_file(path: str) -> list[str]:
        """Load proxy URLs from a file, one per line."""
        with open(path, "r", encoding="utf-8") as f:
            proxies = [line.strip() for line in f if line.strip()]
        return proxies

    @staticmethod
    def _load_cookie_file(path: str) -> dict[str, str]:
        """Load cookies from a JSON file.

        Expects either:
        - A JSON object: {"reddit_session": "value", ...}
        - A JSON array (browser export): [{"name": "reddit_session", "value": "..."}, ...]
        """
        import json as _json

        with open(path, "r", encoding="utf-8") as f:
            data = _json.load(f)

        if isinstance(data, dict):
            return data
        if isinstance(data, list):
            return {item["name"]: item["value"] for item in data if "name" in item and "value" in item}
        return {}
