"""Tests for PostScraper."""

from unittest.mock import MagicMock

from redminer.models import Post, Comment
from redminer.scrapers.post import PostScraper


def _make_reddit_post_response():
    """Return a mock Reddit two-element response for a post page."""
    post_data = {
        "id": "abc123",
        "title": "Test Post",
        "author": "testuser",
        "subreddit": "python",
        "score": 42,
        "upvote_ratio": 0.95,
        "num_comments": 2,
        "created_utc": 1700000000.0,
        "selftext": "Hello world",
        "url": "https://reddit.com/r/python/comments/abc123/test_post/",
        "permalink": "/r/python/comments/abc123/test_post/",
        "link_flair_text": None,
    }

    comment_data_1 = {
        "id": "cmt1",
        "author": "commenter1",
        "body": "Great post!",
        "score": 5,
        "created_utc": 1700001000.0,
        "parent_id": "t3_abc123",
        "depth": 0,
        "is_submitter": False,
        "replies": "",
    }

    comment_data_2 = {
        "id": "cmt2",
        "author": "commenter2",
        "body": "I agree.",
        "score": 3,
        "created_utc": 1700002000.0,
        "parent_id": "t3_abc123",
        "depth": 0,
        "is_submitter": False,
        "replies": "",
    }

    return [
        {"data": {"children": [{"kind": "t3", "data": post_data}]}},
        {
            "data": {
                "children": [
                    {"kind": "t1", "data": comment_data_1},
                    {"kind": "t1", "data": comment_data_2},
                    {"kind": "more", "data": {"id": "more1", "children": ["x", "y"]}},
                ]
            }
        },
    ]


class TestPostScraper:
    def test_scrape_returns_post_and_comments(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_reddit_post_response()

        scraper = PostScraper(client)
        post, comments = scraper.scrape(
            "https://www.reddit.com/r/python/comments/abc123/test_post/"
        )

        assert isinstance(post, Post)
        assert post.id == "abc123"
        assert len(comments) == 2
        assert all(isinstance(c, Comment) for c in comments)

    def test_more_kind_entries_are_skipped(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_reddit_post_response()

        scraper = PostScraper(client)
        _, comments = scraper.scrape(
            "https://www.reddit.com/r/python/comments/abc123/test_post/"
        )

        # The response has 2 t1 comments and 1 "more" entry; only 2 should be returned
        assert len(comments) == 2
        assert all(c.id.startswith("cmt") for c in comments)

    def test_scrape_with_full_url(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_reddit_post_response()

        scraper = PostScraper(client)
        scraper.scrape("https://www.reddit.com/r/python/comments/abc123/test_post/")

        call_url = client.fetch.call_args[0][0]
        assert "/r/python/comments/abc123.json" in call_url

    def test_scrape_with_permalink(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_reddit_post_response()

        scraper = PostScraper(client)
        scraper.scrape("/r/python/comments/abc123/test_post/")

        call_url = client.fetch.call_args[0][0]
        assert "/r/python/comments/abc123.json" in call_url
