"""Subreddit scraper for fetching posts from a subreddit listing."""

from reddipy.models import Post
from reddipy.scrapers.base import BaseScraper


class SubredditScraper(BaseScraper):
    """Scrapes posts from a subreddit."""

    def scrape(
        self,
        subreddit: str,
        sort: str = "hot",
        time_filter: str = "all",
        limit: int = 25,
    ) -> list[Post]:
        """Fetch posts from a subreddit sorted by *sort*.

        The *time_filter* parameter is only sent when *sort* is ``top`` or
        ``controversial`` (for other sorts it has no effect on the API).
        """
        url = f"{self.client.BASE_URL}/r/{subreddit}/{sort}.json"

        params: dict = {}
        if sort in ("top", "controversial"):
            params["t"] = time_filter

        raw_items = self.client.fetch_all(url, params, limit)
        return [Post.from_raw(item) for item in raw_items]
