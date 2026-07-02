"""Comprehensive tests for redminer.models (Post, Comment, UserActivity)."""

from datetime import datetime, timezone

import pytest

from redminer.models import Comment, Post, UserActivity


# ---------------------------------------------------------------------------
# Helpers: realistic raw dicts
# ---------------------------------------------------------------------------

def _raw_post(**overrides):
    """Return a realistic raw Reddit post dict (the inner 'data' dict)."""
    base = {
        "id": "abc123",
        "title": "Test Post Title",
        "author": "test_user",
        "subreddit": "python",
        "score": 42,
        "upvote_ratio": 0.95,
        "num_comments": 7,
        "created_utc": 1719000000.0,
        "selftext": "Hello world",
        "url": "https://reddit.com/r/python/comments/abc123/test/",
        "permalink": "/r/python/comments/abc123/test/",
        "link_flair_text": "Discussion",
        # Extra fields that should be ignored by from_raw
        "distinguished": None,
        "is_original_content": False,
        "over_18": False,
        "spoiler": False,
        "locked": False,
        "author_fullname": "t2_xyz",
        "total_awards_received": 0,
        "subreddit_id": "t5_2qh0y",
    }
    base.update(overrides)
    return base


def _raw_comment(*, replies="", **overrides):
    """Return a realistic raw Reddit comment dict (the inner 'data' dict)."""
    base = {
        "id": "cmt001",
        "author": "commenter",
        "body": "Nice post!",
        "score": 10,
        "created_utc": 1719000100.0,
        "parent_id": "t3_abc123",
        "depth": 0,
        "is_submitter": False,
        "replies": replies,
        # Extra fields
        "distinguished": None,
        "collapsed": False,
        "author_fullname": "t2_aaa",
    }
    base.update(overrides)
    return base


def _wrap_comment_children(comment_dicts):
    """Wrap comment data dicts into Reddit listing structure."""
    children = []
    for d in comment_dicts:
        children.append({"kind": "t1", "data": d})
    return {"kind": "Listing", "data": {"children": children}}


# ===========================================================================
# Post tests
# ===========================================================================

class TestPostFromRaw:
    def test_basic_from_raw(self):
        raw = _raw_post()
        post = Post.from_raw(raw)

        assert post.id == "abc123"
        assert post.title == "Test Post Title"
        assert post.author == "test_user"
        assert post.subreddit == "python"
        assert post.score == 42
        assert post.upvote_ratio == 0.95
        assert post.num_comments == 7
        assert post.selftext == "Hello world"
        assert post.url == "https://reddit.com/r/python/comments/abc123/test/"
        assert post.permalink == "/r/python/comments/abc123/test/"
        assert post.flair == "Discussion"

    def test_created_utc_converted_to_datetime(self):
        raw = _raw_post(created_utc=1719000000.0)
        post = Post.from_raw(raw)
        expected = datetime.fromtimestamp(1719000000.0, tz=timezone.utc)
        assert post.created_utc == expected

    def test_flair_none_when_missing(self):
        raw = _raw_post(link_flair_text=None)
        post = Post.from_raw(raw)
        assert post.flair is None

    def test_extra_fields_ignored(self):
        raw = _raw_post()
        post = Post.from_raw(raw)
        assert not hasattr(post, "distinguished")
        assert not hasattr(post, "over_18")

    def test_empty_selftext(self):
        raw = _raw_post(selftext="")
        post = Post.from_raw(raw)
        assert post.selftext == ""

    def test_deleted_author(self):
        raw = _raw_post(author="[deleted]")
        post = Post.from_raw(raw)
        assert post.author == "[deleted]"


class TestPostToDict:
    def test_to_dict_returns_dict(self):
        post = Post.from_raw(_raw_post())
        d = post.to_dict()
        assert isinstance(d, dict)

    def test_datetime_becomes_iso_string(self):
        post = Post.from_raw(_raw_post(created_utc=1719000000.0))
        d = post.to_dict()
        expected_dt = datetime.fromtimestamp(1719000000.0, tz=timezone.utc)
        assert d["created_utc"] == expected_dt.isoformat()

    def test_round_trip_fields(self):
        raw = _raw_post()
        post = Post.from_raw(raw)
        d = post.to_dict()
        assert d["id"] == "abc123"
        assert d["title"] == "Test Post Title"
        assert d["flair"] == "Discussion"
        assert d["score"] == 42
        assert d["upvote_ratio"] == 0.95


# ===========================================================================
# Comment tests
# ===========================================================================

class TestCommentFromRaw:
    def test_basic_from_raw(self):
        raw = _raw_comment()
        comment = Comment.from_raw(raw)

        assert comment.id == "cmt001"
        assert comment.author == "commenter"
        assert comment.body == "Nice post!"
        assert comment.score == 10
        assert comment.parent_id == "t3_abc123"
        assert comment.depth == 0
        assert comment.is_submitter is False
        assert comment.replies == []

    def test_replies_empty_string(self):
        raw = _raw_comment(replies="")
        comment = Comment.from_raw(raw)
        assert comment.replies == []

    def test_nested_replies(self):
        child_data = _raw_comment(
            id="cmt002",
            author="replier",
            body="Thanks!",
            depth=1,
            parent_id="t1_cmt001",
            replies="",
        )
        replies_listing = _wrap_comment_children([child_data])
        raw = _raw_comment(replies=replies_listing)
        comment = Comment.from_raw(raw)

        assert len(comment.replies) == 1
        assert comment.replies[0].id == "cmt002"
        assert comment.replies[0].depth == 1
        assert comment.replies[0].replies == []

    def test_more_stubs_skipped(self):
        child_data = _raw_comment(
            id="cmt002", body="Real reply", depth=1, replies=""
        )
        children = [
            {"kind": "t1", "data": child_data},
            {"kind": "more", "data": {"id": "more001", "count": 5, "children": ["x", "y"]}},
        ]
        replies_listing = {"kind": "Listing", "data": {"children": children}}
        raw = _raw_comment(replies=replies_listing)
        comment = Comment.from_raw(raw)

        assert len(comment.replies) == 1
        assert comment.replies[0].id == "cmt002"

    def test_depth_defaults_to_zero(self):
        raw = _raw_comment()
        del raw["depth"]
        comment = Comment.from_raw(raw)
        assert comment.depth == 0

    def test_created_utc_converted(self):
        raw = _raw_comment(created_utc=1719000100.0)
        comment = Comment.from_raw(raw)
        expected = datetime.fromtimestamp(1719000100.0, tz=timezone.utc)
        assert comment.created_utc == expected

    def test_deleted_author(self):
        raw = _raw_comment(author="[deleted]")
        comment = Comment.from_raw(raw)
        assert comment.author == "[deleted]"

    def test_deeply_nested_replies(self):
        """Three levels deep: comment -> reply -> reply."""
        grandchild = _raw_comment(id="gc", depth=2, replies="")
        child = _raw_comment(
            id="child", depth=1,
            replies=_wrap_comment_children([grandchild]),
        )
        root = _raw_comment(
            id="root", depth=0,
            replies=_wrap_comment_children([child]),
        )
        comment = Comment.from_raw(root)
        assert comment.id == "root"
        assert len(comment.replies) == 1
        assert comment.replies[0].id == "child"
        assert len(comment.replies[0].replies) == 1
        assert comment.replies[0].replies[0].id == "gc"


class TestCommentToDict:
    def test_to_dict_datetime_iso(self):
        comment = Comment.from_raw(_raw_comment())
        d = comment.to_dict()
        expected_dt = datetime.fromtimestamp(1719000100.0, tz=timezone.utc)
        assert d["created_utc"] == expected_dt.isoformat()

    def test_to_dict_nested_replies_serialized(self):
        child_data = _raw_comment(id="cmt002", depth=1, replies="")
        replies_listing = _wrap_comment_children([child_data])
        raw = _raw_comment(replies=replies_listing)
        comment = Comment.from_raw(raw)
        d = comment.to_dict()

        assert isinstance(d["replies"], list)
        assert len(d["replies"]) == 1
        assert d["replies"][0]["id"] == "cmt002"
        assert isinstance(d["replies"][0]["created_utc"], str)


# ===========================================================================
# UserActivity tests
# ===========================================================================

def _raw_user_post():
    return {
        "kind": "t3",
        "data": {
            "id": "upost1",
            "author": "active_user",
            "subreddit": "learnpython",
            "score": 15,
            "created_utc": 1719001000.0,
            "title": "How do I use dataclasses?",
            "permalink": "/r/learnpython/comments/upost1/how/",
            # Extra
            "num_comments": 3,
            "selftext": "body text",
        },
    }


def _raw_user_comment():
    return {
        "kind": "t1",
        "data": {
            "id": "ucmt1",
            "author": "active_user",
            "subreddit": "python",
            "score": 5,
            "created_utc": 1719002000.0,
            "body": "Great question!",
            "permalink": "/r/python/comments/abc/great/ucmt1/",
            # Extra
            "depth": 1,
            "is_submitter": False,
        },
    }


class TestUserActivityFromRaw:
    def test_post_type(self):
        raw = _raw_user_post()
        ua = UserActivity.from_raw(raw)

        assert ua.type == "post"
        assert ua.id == "upost1"
        assert ua.author == "active_user"
        assert ua.subreddit == "learnpython"
        assert ua.score == 15
        assert ua.title == "How do I use dataclasses?"
        assert ua.body is None
        assert ua.permalink == "/r/learnpython/comments/upost1/how/"

    def test_comment_type(self):
        raw = _raw_user_comment()
        ua = UserActivity.from_raw(raw)

        assert ua.type == "comment"
        assert ua.id == "ucmt1"
        assert ua.author == "active_user"
        assert ua.subreddit == "python"
        assert ua.score == 5
        assert ua.body == "Great question!"
        assert ua.title is None
        assert ua.permalink == "/r/python/comments/abc/great/ucmt1/"

    def test_created_utc_converted(self):
        raw = _raw_user_post()
        ua = UserActivity.from_raw(raw)
        expected = datetime.fromtimestamp(1719001000.0, tz=timezone.utc)
        assert ua.created_utc == expected

    def test_deleted_author(self):
        raw = _raw_user_comment()
        raw["data"]["author"] = "[deleted]"
        ua = UserActivity.from_raw(raw)
        assert ua.author == "[deleted]"


class TestUserActivityToDict:
    def test_to_dict_post(self):
        ua = UserActivity.from_raw(_raw_user_post())
        d = ua.to_dict()
        assert d["type"] == "post"
        assert d["title"] == "How do I use dataclasses?"
        assert d["body"] is None
        expected_dt = datetime.fromtimestamp(1719001000.0, tz=timezone.utc)
        assert d["created_utc"] == expected_dt.isoformat()

    def test_to_dict_comment(self):
        ua = UserActivity.from_raw(_raw_user_comment())
        d = ua.to_dict()
        assert d["type"] == "comment"
        assert d["body"] == "Great question!"
        assert d["title"] is None
