"""Tests for SubredditScraper."""

from unittest.mock import MagicMock

from redminer.models import Post
from redminer.scrapers.subreddit import SubredditScraper


def _make_raw_post(post_id="abc123"):
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


class TestSubredditScraper:
    def test_scrape_returns_list_of_posts(self):
        client = MagicMock()
        client.fetch_all.return_value = [_make_raw_post("p1"), _make_raw_post("p2")]

        scraper = SubredditScraper(client)
        results = scraper.scrape("python")

        assert len(results) == 2
        assert all(isinstance(p, Post) for p in results)

    def test_url_contains_subreddit_and_sort(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SubredditScraper(client)
        scraper.scrape("python", sort="new")

        call_args = client.fetch_all.call_args
        url = call_args[0][0]
        assert url == "https://www.reddit.com/r/python/new.json"

    def test_time_filter_sent_for_top(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SubredditScraper(client)
        scraper.scrape("python", sort="top", time_filter="week")

        params = client.fetch_all.call_args[0][1]
        assert params["t"] == "week"

    def test_time_filter_sent_for_controversial(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SubredditScraper(client)
        scraper.scrape("python", sort="controversial", time_filter="month")

        params = client.fetch_all.call_args[0][1]
        assert params["t"] == "month"

    def test_time_filter_not_sent_for_hot(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SubredditScraper(client)
        scraper.scrape("python", sort="hot", time_filter="week")

        params = client.fetch_all.call_args[0][1]
        assert "t" not in params

    def test_time_filter_not_sent_for_new(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch_all.return_value = []

        scraper = SubredditScraper(client)
        scraper.scrape("python", sort="new", time_filter="all")

        params = client.fetch_all.call_args[0][1]
        assert "t" not in params
