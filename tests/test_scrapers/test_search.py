"""Tests for SearchScraper."""

from unittest.mock import MagicMock

from reddipy.models import Post
from reddipy.scrapers.search import SearchScraper


def _make_raw_post(post_id="abc123"):
    """Return a minimal raw post dict for testing."""
    return {
        "id": post_id,
        "title": "Test Post",
        "author": "testuser",
        "subreddit": "python",
        "score": 42,
        "upvote_ratio": 0.95,
        "num_comments": 10,
        "created_utc": 1700000000.0,
        "selftext": "Hello world",
        "url": f"https://reddit.com/r/python/comments/{post_id}/test_post/",
        "permalink": f"/r/python/comments/{post_id}/test_post/",
        "link_flair_text": None,
    }


class TestSearchScraper:
    def test_scrape_returns_list_of_posts(self):
        client = MagicMock()
        client.fetch_all.return_value = [_make_raw_post("p1"), _make_raw_post("p2")]

        scraper = SearchScraper(client)
        results = scraper.scrape("python tips")

        assert len(results) == 2
        assert all(isinstance(p, Post) for p in results)
        assert results[0].id == "p1"
        assert results[1].id == "p2"

    def test_url_for_global_search(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SearchScraper(client)
        scraper.scrape("test query")

        call_args = client.fetch_all.call_args
        url = call_args[0][0] if call_args[0] else call_args[1]["url"]
        assert url == "https://www.reddit.com/search.json"

    def test_url_for_subreddit_scoped_search(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SearchScraper(client)
        scraper.scrape("test query", subreddit="python")

        call_args = client.fetch_all.call_args
        url = call_args[0][0] if call_args[0] else call_args[1]["url"]
        assert url == "https://www.reddit.com/r/python/search.json"

        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert params.get("restrict_sr") == "on"

    def test_params_include_query_sort_time(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SearchScraper(client)
        scraper.scrape("my query", sort="new", time_filter="week")

        call_args = client.fetch_all.call_args
        params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("params", {})
        assert params["q"] == "my query"
        assert params["sort"] == "new"
        assert params["t"] == "week"
