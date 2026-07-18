"""RedMiner SDK - Clean Python interface for scraping Reddit."""

from __future__ import annotations

from redminer.client import RedditClient
from redminer.config import get_cookie, set_cookie, clear_config
from redminer.models import Comment, Post, UserActivity
from redminer.scrapers import PostScraper, SearchScraper, SubredditScraper, UserScraper


class Reddit:
    """Main SDK entry point for RedMiner.

    Usage::

        from redminer import Reddit

        reddit = Reddit()
        reddit.configure(cookie="your_reddit_session_cookie")

        posts = reddit.search("python", limit=10)
        for post in posts:
            print(post.title, post.score)
    """

    def __init__(
        self,
        cookie: str | None = None,
        cookie_file: str | None = None,
        delay: float = 2.0,
        proxy: str | None = None,
        proxy_file: str | None = None,
        user_agent: str | None = None,
        verbose: bool = False,
    ):
        resolved_cookie = cookie or get_cookie()
        self._client = RedditClient(
            delay=delay,
            proxy=proxy,
            proxy_file=proxy_file,
            user_agent=user_agent,
            verbose=verbose,
            cookie=resolved_cookie,
            cookie_file=cookie_file,
        )

    @staticmethod
    def configure(cookie: str) -> None:
        """Save Reddit session cookie for persistent use.

        Only needs to be called once. The cookie is stored at
        ``~/.redminer/config.json`` and loaded automatically on future runs.

        Args:
            cookie: Your ``reddit_session`` cookie value from the browser.
        """
        set_cookie(cookie)

    @staticmethod
    def logout() -> None:
        """Remove stored authentication."""
        clear_config()

    @staticmethod
    def is_configured() -> bool:
        """Check if a Reddit session cookie is stored."""
        return get_cookie() is not None

    def search(
        self,
        query: str,
        sort: str = "relevance",
        time_filter: str = "all",
        limit: int = 25,
        subreddit: str | None = None,
    ) -> list[Post]:
        """Search Reddit for posts matching a query.

        Args:
            query: Search keywords.
            sort: Sort order (relevance, hot, new, top, comments).
            time_filter: Time range (day, week, month, year, all).
            limit: Max number of results (up to ~1000).
            subreddit: Optional subreddit to scope the search to.

        Returns:
            List of Post objects.
        """
        scraper = SearchScraper(self._client)
        return scraper.scrape(query, sort=sort, time_filter=time_filter,
                              limit=limit, subreddit=subreddit)

    def post(self, url: str) -> tuple[Post, list[Comment]]:
        """Scrape a single Reddit post and its comments.

        Args:
            url: Full Reddit post URL or permalink.

        Returns:
            Tuple of (Post, list of Comments).
        """
        scraper = PostScraper(self._client)
        return scraper.scrape(url)

    def subreddit(
        self,
        name: str,
        sort: str = "hot",
        time_filter: str = "all",
        limit: int = 25,
    ) -> list[Post]:
        """Fetch posts from a subreddit.

        Args:
            name: Subreddit name (without r/ prefix).
            sort: Sort order (hot, new, top, rising, controversial).
            time_filter: Time range for top/controversial (day, week, month, year, all).
            limit: Max number of posts.

        Returns:
            List of Post objects.
        """
        scraper = SubredditScraper(self._client)
        return scraper.scrape(name, sort=sort, time_filter=time_filter, limit=limit)

    def user(
        self,
        username: str,
        limit: int = 25,
        sort: str = "new",
        activity_type: str = "all",
    ) -> list[UserActivity]:
        """Fetch a user's recent activity.

        Args:
            username: Reddit username (without u/ prefix).
            limit: Max number of items.
            sort: Sort order (new, hot, top).
            activity_type: Filter by type (posts, comments, all).

        Returns:
            List of UserActivity objects.
        """
        scraper = UserScraper(self._client)
        return scraper.scrape(username, limit=limit, sort=sort,
                              activity_type=activity_type)
