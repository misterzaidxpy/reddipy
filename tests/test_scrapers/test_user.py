"""Tests for UserScraper."""

from unittest.mock import MagicMock

from redminer.models import UserActivity
from redminer.scrapers.user import UserScraper


def _make_user_response(children):
    """Build a Reddit-style listing response with the given children."""
    return {
        "data": {
            "children": children,
            "after": None,
        }
    }


def _make_post_child(post_id="p1"):
    return {
        "kind": "t3",
        "data": {
            "id": post_id,
            "title": "My Post",
            "author": "someuser",
            "subreddit": "python",
            "score": 10,
            "created_utc": 1700000000.0,
            "permalink": f"/r/python/comments/{post_id}/my_post/",
        },
    }


def _make_comment_child(comment_id="c1"):
    return {
        "kind": "t1",
        "data": {
            "id": comment_id,
            "body": "Nice post!",
            "author": "someuser",
            "subreddit": "python",
            "score": 5,
            "created_utc": 1700001000.0,
            "permalink": f"/r/python/comments/xyz/some_post/{comment_id}/",
        },
    }


class TestUserScraper:
    def test_scrape_returns_user_activities(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_user_response(
            [_make_post_child(), _make_comment_child()]
        )

        scraper = UserScraper(client)
        results = scraper.scrape("someuser")

        assert len(results) == 2
        assert all(isinstance(a, UserActivity) for a in results)

    def test_activity_type_posts_filters_to_t3(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_user_response(
            [_make_post_child("p1"), _make_comment_child("c1"), _make_post_child("p2")]
        )

        scraper = UserScraper(client)
        results = scraper.scrape("someuser", activity_type="posts")

        assert len(results) == 2
        assert all(a.type == "post" for a in results)

    def test_activity_type_comments_filters_to_t1(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_user_response(
            [_make_post_child("p1"), _make_comment_child("c1"), _make_comment_child("c2")]
        )

        scraper = UserScraper(client)
        results = scraper.scrape("someuser", activity_type="comments")

        assert len(results) == 2
        assert all(a.type == "comment" for a in results)

    def test_activity_type_all_includes_both(self):
        client = MagicMock()
        client.BASE_URL = "https://www.reddit.com"
        client.fetch.return_value = _make_user_response(
            [_make_post_child("p1"), _make_comment_child("c1")]
        )

        scraper = UserScraper(client)
        results = scraper.scrape("someuser", activity_type="all")

        assert len(results) == 2
        types = {a.type for a in results}
        assert types == {"post", "comment"}
