"""Tests for JSONExporter."""

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from redminer.models import Post, Comment, UserActivity
from redminer.exporters.json_exporter import JSONExporter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_post(
    id="abc123",
    title="Test Post Title",
    author="testuser",
    subreddit="python",
    score=100,
    upvote_ratio=0.95,
    num_comments=42,
    selftext="Some self text here",
    url="https://reddit.com",
    permalink="/r/python/comments/abc123",
    flair="Discussion",
    created_utc=None,
) -> Post:
    if created_utc is None:
        created_utc = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
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
    author="commenter",
    body="This is a comment body",
    score=10,
    parent_id="t3_abc123",
    depth=0,
    is_submitter=False,
    replies=None,
    created_utc=None,
) -> Comment:
    if created_utc is None:
        created_utc = datetime(2024, 1, 15, 13, 0, 0, tzinfo=timezone.utc)
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
    author="activityuser",
    subreddit="learnpython",
    score=55,
    title="My Post Title",
    body=None,
    permalink="/r/learnpython/comments/ua1",
    created_utc=None,
) -> UserActivity:
    if created_utc is None:
        created_utc = datetime(2024, 2, 1, 9, 0, 0, tzinfo=timezone.utc)
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
# Tests
# ---------------------------------------------------------------------------

class TestJSONExporterToFile:
    def test_export_posts_to_file_creates_valid_json(self, tmp_path):
        posts = [make_post(id="p1", title="Hello World"), make_post(id="p2", title="Goodbye World")]
        exporter = JSONExporter()
        out = str(tmp_path / "out.json")
        exporter.export(posts, output_path=out)

        assert os.path.exists(out)
        with open(out, encoding="utf-8") as f:
            result = json.load(f)

        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["id"] == "p1"
        assert result[0]["title"] == "Hello World"
        assert result[1]["id"] == "p2"

    def test_export_posts_file_contains_all_expected_keys(self, tmp_path):
        post = make_post()
        exporter = JSONExporter()
        out = str(tmp_path / "post.json")
        exporter.export([post], output_path=out)

        with open(out, encoding="utf-8") as f:
            result = json.load(f)

        expected_keys = {
            "id", "title", "author", "subreddit", "score", "upvote_ratio",
            "num_comments", "created_utc", "selftext", "url", "permalink", "flair",
        }
        assert set(result[0].keys()) == expected_keys

    def test_export_comments_to_file(self, tmp_path):
        child = make_comment(id="c2", depth=1, parent_id="t1_c1")
        parent = make_comment(id="c1", replies=[child])
        exporter = JSONExporter()
        out = str(tmp_path / "comments.json")
        exporter.export([parent], output_path=out)

        with open(out, encoding="utf-8") as f:
            result = json.load(f)

        assert len(result) == 1
        assert result[0]["id"] == "c1"
        assert len(result[0]["replies"]) == 1
        assert result[0]["replies"][0]["id"] == "c2"

    def test_export_user_activity_to_file(self, tmp_path):
        activity = make_user_activity()
        exporter = JSONExporter()
        out = str(tmp_path / "activity.json")
        exporter.export([activity], output_path=out)

        with open(out, encoding="utf-8") as f:
            result = json.load(f)

        assert result[0]["type"] == "post"
        assert result[0]["author"] == "activityuser"

    def test_datetime_serialized_as_iso_string(self, tmp_path):
        dt = datetime(2024, 6, 15, 8, 30, 0, tzinfo=timezone.utc)
        post = make_post(created_utc=dt)
        exporter = JSONExporter()
        out = str(tmp_path / "dt.json")
        exporter.export([post], output_path=out)

        with open(out, encoding="utf-8") as f:
            result = json.load(f)

        assert result[0]["created_utc"] == "2024-06-15T08:30:00+00:00"


class TestJSONExporterToStdout:
    def test_export_to_stdout_when_no_path(self, capsys):
        post = make_post(id="stdout_test", title="Stdout Title")
        exporter = JSONExporter()
        exporter.export([post])

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, list)
        assert result[0]["id"] == "stdout_test"
        assert result[0]["title"] == "Stdout Title"

    def test_stdout_output_has_indent_formatting(self, capsys):
        post = make_post()
        exporter = JSONExporter()
        exporter.export([post])

        captured = capsys.readouterr()
        # indent=2 means lines start with "  " for nested fields
        assert "\n  " in captured.out

    def test_export_multiple_items_to_stdout(self, capsys):
        posts = [make_post(id=f"p{i}") for i in range(3)]
        exporter = JSONExporter()
        exporter.export(posts)

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert len(result) == 3
        assert result[2]["id"] == "p2"


class TestJSONExporterIndentFormatting:
    def test_indent_is_two_spaces(self, tmp_path):
        post = make_post()
        exporter = JSONExporter()
        out = str(tmp_path / "indent.json")
        exporter.export([post], output_path=out)

        with open(out, encoding="utf-8") as f:
            raw = f.read()

        # With indent=2 the opening bracket should be followed by a newline
        # and next line should start with 2 spaces (the object open brace).
        lines = raw.splitlines()
        assert lines[0] == "["
        assert lines[1].startswith("  {")

    def test_output_is_valid_json_with_indent(self, tmp_path):
        posts = [make_post(id="x"), make_post(id="y")]
        exporter = JSONExporter()
        out = str(tmp_path / "valid.json")
        exporter.export(posts, output_path=out)

        with open(out, encoding="utf-8") as f:
            parsed = json.load(f)
        assert len(parsed) == 2
