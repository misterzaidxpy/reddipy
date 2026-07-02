"""Tests for ConsoleExporter."""

from datetime import datetime, timezone

import pytest

from redminer.models import Post, Comment, UserActivity
from redminer.exporters.console import ConsoleExporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_post(
    id="p1",
    title="Sample Post Title",
    author="alice",
    subreddit="python",
    score=150,
    upvote_ratio=0.90,
    num_comments=20,
    selftext="This is the body of the post.",
    url="https://reddit.com",
    permalink="/r/python/comments/p1",
    flair=None,
    created_utc=None,
) -> Post:
    if created_utc is None:
        created_utc = datetime(2024, 5, 1, 8, 0, 0, tzinfo=timezone.utc)
    return Post(
        id=id,
        title=title,
        author=author,
        subreddit=subreddit,
        score=score,
        upvote_ratio=upvote_ratio,
        num_comments=num_comments,
        created_utc=created_utc,
        selftext=selftext,
        url=url,
        permalink=permalink,
        flair=flair,
    )


def make_comment(
    id="c1",
    author="bob",
    body="A simple comment body",
    score=8,
    parent_id="t3_p1",
    depth=0,
    is_submitter=False,
    replies=None,
    created_utc=None,
) -> Comment:
    if created_utc is None:
        created_utc = datetime(2024, 5, 1, 9, 0, 0, tzinfo=timezone.utc)
    if replies is None:
        replies = []
    return Comment(
        id=id,
        author=author,
        body=body,
        score=score,
        created_utc=created_utc,
        parent_id=parent_id,
        depth=depth,
        is_submitter=is_submitter,
        replies=replies,
    )


def make_user_activity(
    activity_type="post",
    id="ua1",
    author="carol",
    subreddit="learnpython",
    score=77,
    title="Activity Post Title",
    body=None,
    permalink="/r/learnpython/comments/ua1",
    created_utc=None,
) -> UserActivity:
    if created_utc is None:
        created_utc = datetime(2024, 5, 2, 10, 0, 0, tzinfo=timezone.utc)
    return UserActivity(
        type=activity_type,
        id=id,
        author=author,
        subreddit=subreddit,
        score=score,
        created_utc=created_utc,
        title=title,
        body=body,
        permalink=permalink,
    )


# ---------------------------------------------------------------------------
# Post table tests
# ---------------------------------------------------------------------------

class TestConsoleExporterPosts:
    def test_headers_present_for_posts(self, capsys):
        post = make_post()
        ConsoleExporter().export([post])
        out = capsys.readouterr().out
        assert "id" in out
        assert "title" in out
        assert "author" in out
        assert "subreddit" in out
        assert "score" in out
        assert "num_comments" in out

    def test_separator_line_printed(self, capsys):
        post = make_post()
        ConsoleExporter().export([post])
        out = capsys.readouterr().out
        lines = out.splitlines()
        # Second line should be a separator made of dashes
        assert any(set(line.strip()).issubset({"-", " "}) and "-" in line for line in lines)

    def test_post_data_row_printed(self, capsys):
        post = make_post(id="post42", author="alice", subreddit="python", score=500)
        ConsoleExporter().export([post])
        out = capsys.readouterr().out
        assert "post42" in out
        assert "alice" in out
        assert "python" in out
        assert "500" in out

    def test_multiple_post_rows_printed(self, capsys):
        posts = [make_post(id=f"p{i}", title=f"Title {i}") for i in range(3)]
        ConsoleExporter().export(posts)
        out = capsys.readouterr().out
        assert "p0" in out
        assert "p1" in out
        assert "p2" in out

    def test_long_title_truncated_to_60_chars(self, capsys):
        long_title = "A" * 80
        post = make_post(title=long_title)
        ConsoleExporter().export([post])
        out = capsys.readouterr().out
        # The full 80-char title should NOT appear; truncated version should
        assert long_title not in out
        assert "A" * 60 + "..." in out

    def test_short_title_not_truncated(self, capsys):
        short_title = "Short Title"
        post = make_post(title=short_title)
        ConsoleExporter().export([post])
        out = capsys.readouterr().out
        assert short_title in out


# ---------------------------------------------------------------------------
# Comment table tests
# ---------------------------------------------------------------------------

class TestConsoleExporterComments:
    def test_headers_present_for_comments(self, capsys):
        comment = make_comment()
        ConsoleExporter().export([comment])
        out = capsys.readouterr().out
        assert "id" in out
        assert "author" in out
        assert "body" in out
        assert "score" in out
        assert "depth" in out

    def test_comment_data_row_printed(self, capsys):
        comment = make_comment(id="cmt99", author="dave", score=42, depth=2)
        ConsoleExporter().export([comment])
        out = capsys.readouterr().out
        assert "cmt99" in out
        assert "dave" in out
        assert "42" in out
        assert "2" in out

    def test_long_body_truncated_to_50_chars(self, capsys):
        long_body = "B" * 80
        comment = make_comment(body=long_body)
        ConsoleExporter().export([comment])
        out = capsys.readouterr().out
        assert long_body not in out
        assert "B" * 50 + "..." in out

    def test_short_body_not_truncated(self, capsys):
        short_body = "Short comment body"
        comment = make_comment(body=short_body)
        ConsoleExporter().export([comment])
        out = capsys.readouterr().out
        assert short_body in out

    def test_separator_line_present_for_comments(self, capsys):
        comment = make_comment()
        ConsoleExporter().export([comment])
        out = capsys.readouterr().out
        lines = out.splitlines()
        assert any(set(line.strip()).issubset({"-", " "}) and "-" in line for line in lines)


# ---------------------------------------------------------------------------
# UserActivity table tests
# ---------------------------------------------------------------------------

class TestConsoleExporterUserActivity:
    def test_headers_present_for_user_activity(self, capsys):
        activity = make_user_activity()
        ConsoleExporter().export([activity])
        out = capsys.readouterr().out
        assert "type" in out
        assert "id" in out
        assert "author" in out
        assert "subreddit" in out
        assert "score" in out

    def test_post_type_activity_data_row_printed(self, capsys):
        activity = make_user_activity(
            activity_type="post",
            id="ua10",
            author="eve",
            subreddit="datascience",
            score=300,
            title="Great Post",
        )
        ConsoleExporter().export([activity])
        out = capsys.readouterr().out
        assert "ua10" in out
        assert "eve" in out
        assert "datascience" in out
        assert "300" in out
        assert "post" in out

    def test_comment_type_activity_uses_body(self, capsys):
        activity = make_user_activity(
            activity_type="comment",
            id="ua20",
            title=None,
            body="Here is my comment text",
        )
        ConsoleExporter().export([activity])
        out = capsys.readouterr().out
        assert "Here is my comment text" in out

    def test_long_content_truncated_to_50_chars(self, capsys):
        long_title = "C" * 80
        activity = make_user_activity(title=long_title)
        ConsoleExporter().export([activity])
        out = capsys.readouterr().out
        assert long_title not in out
        assert "C" * 50 + "..." in out

    def test_multiple_activity_rows_printed(self, capsys):
        activities = [
            make_user_activity(activity_type="post", id="ua1", title="Post 1"),
            make_user_activity(
                activity_type="comment", id="ua2", title=None, body="Comment body"
            ),
        ]
        ConsoleExporter().export(activities)
        out = capsys.readouterr().out
        assert "ua1" in out
        assert "ua2" in out
        assert "post" in out
        assert "comment" in out


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestConsoleExporterEdgeCases:
    def test_empty_data_prints_nothing(self, capsys):
        ConsoleExporter().export([])
        out = capsys.readouterr().out
        assert out == ""

    def test_output_path_is_ignored(self, capsys, tmp_path):
        post = make_post()
        out_file = str(tmp_path / "ignored.txt")
        ConsoleExporter().export([post], output_path=out_file)
        # stdout should still have content
        out = capsys.readouterr().out
        assert len(out) > 0
        # File should NOT be created since output_path is ignored
        import os
        assert not os.path.exists(out_file)

    def test_exactly_50_char_body_not_truncated(self, capsys):
        exact_body = "E" * 50
        comment = make_comment(body=exact_body)
        ConsoleExporter().export([comment])
        out = capsys.readouterr().out
        # Should appear without "..." suffix
        assert exact_body in out
        assert exact_body + "..." not in out

    def test_exactly_60_char_title_not_truncated(self, capsys):
        exact_title = "F" * 60
        post = make_post(title=exact_title)
        ConsoleExporter().export([post])
        out = capsys.readouterr().out
        assert exact_title in out
        assert exact_title + "..." not in out
