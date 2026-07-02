"""Search scraper for Reddit's search endpoint."""

from redminer.models import Post
from redminer.scrapers.base import BaseScraper


class SearchScraper(BaseScraper):
    """Scrapes Reddit search results."""

    def scrape(
        self,
        query: str,
        sort: str = "relevance",
        time_filter: str = "all",
        limit: int = 25,
        subreddit: str | None = None,
    ) -> list[Post]:
        """Search Reddit and return matching posts.

        If *subreddit* is provided the search is scoped to that subreddit,
        otherwise all of Reddit is searched.
        """
        params: dict = {
            "q": query,
            "sort": sort,
            "t": time_filter,
        }

        if subreddit:
            url = f"{self.client.BASE_URL}/r/{subreddit}/search.json"
            params["restrict_sr"] = "on"
        else:
            url = f"{self.client.BASE_URL}/search.json"

        raw_items = self.client.fetch_all(url, params, limit)
        return [Post.from_raw(item) for item in raw_items]
